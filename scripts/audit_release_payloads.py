"""Counted application payload and matched raw/model serialization audit."""
from __future__ import annotations

import argparse
import fcntl
import gzip
import hashlib
import json
import os
import pickle
import shutil
import socket
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from btp.data import ALL_COLUMNS, prepare_splits

SOURCE = ROOT / "results/ec2_projected_v2_deterministic_20261024"
OUT = ROOT / "reports/resources"
SPECS = (("age_education", 5), ("age_education", 10), ("label_skew", 10))
GENERATOR = "copula"
SEED = 101


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def wire_bytes(obj) -> tuple[bytes, float, int]:
    start = time.monotonic()
    uncompressed = pickle.dumps(obj, protocol=5)
    payload = gzip.compress(uncompressed, compresslevel=6, mtime=0)
    return payload, time.monotonic()-start, len(uncompressed)


def socket_transfer(payload: bytes) -> tuple[int, float]:
    """One-process, nonblocking Unix socket pair; application payload only."""
    sender, receiver = socket.socketpair()
    sender.setblocking(False)
    receiver.setblocking(False)
    start = time.monotonic()
    sent = received = 0
    view = memoryview(payload)
    try:
        while received < len(payload):
            if sent < len(payload):
                try:
                    sent += sender.send(view[sent:sent+65536])
                except BlockingIOError:
                    pass
            try:
                chunk = receiver.recv(65536)
                if chunk:
                    received += len(chunk)
            except BlockingIOError:
                pass
        if sent != len(payload) or received != len(payload):
            raise RuntimeError("Application payload transfer incomplete")
    finally:
        sender.close()
        receiver.close()
    return received, time.monotonic()-start


def find_cell(partition: str, k: int) -> Path:
    matches = []
    for cell in SOURCE.iterdir():
        if not cell.is_dir():
            continue
        cfg = json.loads((cell / "configuration.json").read_text())
        if (cfg["generator"], cfg["partition"], cfg["k"], cfg["seed"]) == (GENERATOR, partition, k, SEED):
            matches.append(cell)
    if len(matches) != 1:
        raise ValueError(f"Expected one saved model cell for {(partition, k)}, found {matches}")
    return matches[0]


def reconstruct_training(cell: Path) -> list[pd.DataFrame]:
    cfg = json.loads((cell / "configuration.json").read_text())
    splits = prepare_splits(ROOT / "data/raw", cfg["seed"])
    development = pd.concat([splits[n] for n in ("train", "tune", "calibration", "validation")])
    partition = pd.read_csv(cell / "partition_manifest.csv", dtype={"row_id": str})
    joined = partition.join(development, on="row_id", validate="one_to_one")
    return [joined[(joined.split == "train") & (joined.client == i)][list(ALL_COLUMNS)].copy()
            for i in range(cfg["k"])]


def run() -> None:
    resources = yaml.safe_load((ROOT / "configs/resources.yaml").read_text())
    lane = Path(os.path.expanduser(resources["shared_compute_lease"]))
    OUT.mkdir(parents=True, exist_ok=True)
    rows, messages = [], []
    with lane.open("a+") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        for partition, k in SPECS:
            mem = Path("/proc/meminfo").read_text()
            available = next(int(line.split()[1])*1024 for line in mem.splitlines() if line.startswith("MemAvailable:"))
            if available < resources["minimum_available_ram_gib"]*2**30 or shutil.disk_usage(ROOT).free < resources["minimum_free_disk_gib"]*2**30:
                raise RuntimeError("Shared capacity reserve breached")
            cell = find_cell(partition, k)
            training = reconstruct_training(cell)
            models = [pickle.loads((cell / "releases" / f"client_{i}.pkl").read_bytes())
                      for i in range(k)]
            public_contract = json.loads((cell / "releases/release_contract.json").read_text())
            target = json.loads((cell / "partition.json").read_text())
            for i, (frame, model) in enumerate(zip(training, models)):
                if len(frame) != target["counts"][i]:
                    raise ValueError("Reconstructed client training count differs from released count")
                raw_payload, raw_seconds, raw_uncompressed = wire_bytes(frame)
                model_payload, model_seconds, model_uncompressed = wire_bytes(model)
                metadata = {"client_id": i, "train_count": len(frame),
                            "public_contract": public_contract}
                metadata_payload, meta_seconds, meta_uncompressed = wire_bytes(metadata)
                for object_name, payload, seconds, uncompressed in (
                    ("raw_table_comparison_only", raw_payload, raw_seconds, raw_uncompressed),
                    ("released_client_model", model_payload, model_seconds, model_uncompressed),
                    ("released_client_metadata", metadata_payload, meta_seconds, meta_uncompressed)):
                    counted, transport_seconds = socket_transfer(payload)
                    messages.append({"cell": cell.name, "partition": partition, "k": k,
                                     "client": i, "object": object_name,
                                     "serialization": "pickle5+gzip6", "uncompressed_bytes": uncompressed,
                                     "application_payload_bytes": counted,
                                     "serialization_wall_seconds": seconds,
                                     "loopback_transfer_wall_seconds": transport_seconds,
                                     "payload_sha256": hashlib.sha256(payload).hexdigest(),
                                     "actual_wan_traffic_measured": False})
                rows.append({"cell": cell.name, "partition": partition, "k": k,
                             "client": i, "train_rows": len(frame),
                             "raw_table_bytes": len(raw_payload),
                             "released_model_bytes": len(model_payload),
                             "released_metadata_bytes": len(metadata_payload),
                             "model_plus_metadata_bytes": len(model_payload)+len(metadata_payload),
                             "model_to_raw_ratio": (len(model_payload)+len(metadata_payload))/len(raw_payload)})
            summary_path = cell / "releases/permitted_summary.npz"
            payload, ser_seconds, uncompressed = wire_bytes(summary_path.read_bytes())
            counted, transfer_seconds = socket_transfer(payload)
            messages.append({"cell": cell.name, "partition": partition, "k": k,
                             "client": "aggregate", "object": "released_permitted_summary",
                             "serialization": "pickle5+gzip6", "uncompressed_bytes": uncompressed,
                             "application_payload_bytes": counted,
                             "serialization_wall_seconds": ser_seconds,
                             "loopback_transfer_wall_seconds": transfer_seconds,
                             "payload_sha256": hashlib.sha256(payload).hexdigest(),
                             "actual_wan_traffic_measured": False})
    pd.DataFrame(rows).to_csv(OUT / "matched_raw_vs_model_payloads.csv", index=False)
    pd.DataFrame(messages).to_csv(OUT / "application_messages.csv", index=False)
    totals = pd.DataFrame(messages).groupby(["cell", "object"], as_index=False).agg(
        messages=("object", "count"), payload_bytes=("application_payload_bytes", "sum"),
        serialization_wall_seconds=("serialization_wall_seconds", "sum"),
        loopback_transfer_wall_seconds=("loopback_transfer_wall_seconds", "sum"))
    totals.to_csv(OUT / "message_totals.csv", index=False)
    (OUT / "release_manifest.json").write_text(json.dumps({
        "cells": [find_cell(p, k).name for p, k in SPECS],
        "raw_rows_sent_to_model_only_server": False,
        "transport": "one-process Unix socketpair application payload count only; no WAN/TLS claim",
        "matched_serialization": "pickle protocol 5 plus gzip level 6 for all compared objects",
        "message_table_sha256": sha(OUT / "application_messages.csv"),
        "payload_table_sha256": sha(OUT / "matched_raw_vs_model_payloads.csv"),
    }, indent=2) + "\n")
    print(totals.to_string(index=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="store_true", required=True)
    parser.parse_args()
    run()
