"""Check included official UCI source bytes against saved data manifests."""
from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    adult = json.loads((ROOT / "data/data_manifest.json").read_text())
    for name, expected in adult["raw_sha256"].items():
        source = ROOT / "data/raw" / name
        if digest(source.read_bytes()) != expected:
            raise ValueError(f"Adult source hash differs: {name}")
    bank = json.loads((ROOT / "data/external_bank/data_manifest.json").read_text())
    archive = ROOT / bank["archive_path"]
    if digest(archive.read_bytes()) != bank["archive_sha256"]:
        raise ValueError("Bank official archive hash differs")
    with zipfile.ZipFile(archive) as outer:
        inner = outer.read(bank["nested_member"])
    if digest(inner) != bank["inner_archive_sha256"]:
        raise ValueError("Bank nested archive hash differs")
    from io import BytesIO
    with zipfile.ZipFile(BytesIO(inner)) as nested:
        member = nested.read(bank["csv_member"])
    if digest(member) != bank["csv_member_sha256"]:
        raise ValueError("Bank selected additional-full member hash differs")
    print("Adult official source files and Bank additional-full archive/member hashes verified")


if __name__ == "__main__":
    main()
