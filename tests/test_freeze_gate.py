import hashlib
import json

import pytest

from scripts.freeze_gate import REQUIRED, canonical_bytes, validate_freeze
from btp.run import run_cell


def valid_fixture(tmp_path):
    source = tmp_path / "validation_selection.csv"
    source.write_text("generator,loss\nchow_liu,0.1\n")
    record = {key: "registered" for key in REQUIRED}
    record.update({
        "candidate_families": ["copula", "chow_liu", "mixed_gmm"],
        "selected_generator": "chow_liu", "confirmation_seeds": [404, 505],
        "main_weight_rule": {"name": "size", "formula": "w=alpha"},
        "challenger": {"delta_l1": 0.25, "floor_ratio": 0.5},
        "synthetic_draws": {"rows": 10000, "repeats": 5, "allocation": "largest_remainder"},
        "metrics": {"practical_improvement_margin": 0.005},
        "software": {"code_hash": "installed-code-hash"},
        "inputs": {"selection_table": {"path": source.name,
            "sha256": hashlib.sha256(source.read_bytes()).hexdigest()}},
        "global_freeze_complete": True, "test_used_for_selection": False,
        "confirmation_seeds_used_for_selection": False,
        "assessment_informed_design": True, "main_pipeline_private": False,
    })
    freeze = tmp_path / "SELECTION_FROZEN.json"
    freeze.write_bytes(canonical_bytes(record))
    freeze.with_suffix(".json.sha256").write_text(hashlib.sha256(freeze.read_bytes()).hexdigest() + "\n")
    return freeze, record


def test_valid_complete_freeze(tmp_path):
    freeze, record = valid_fixture(tmp_path)
    assert validate_freeze(freeze, tmp_path, "installed-code-hash") == record


def test_missing_freeze_fails_closed(tmp_path):
    with pytest.raises(ValueError, match="missing"):
        validate_freeze(tmp_path / "SELECTION_FROZEN.json", tmp_path, "installed-code-hash")


def test_incomplete_freeze_fails_closed(tmp_path):
    freeze, record = valid_fixture(tmp_path)
    del record["conditional_policy"]
    freeze.write_bytes(canonical_bytes(record))
    freeze.with_suffix(".json.sha256").write_text(hashlib.sha256(freeze.read_bytes()).hexdigest() + "\n")
    with pytest.raises(ValueError, match="Incomplete"):
        validate_freeze(freeze, tmp_path, "installed-code-hash")


def test_hash_mismatch_fails_closed(tmp_path):
    freeze, _ = valid_fixture(tmp_path)
    (tmp_path / "validation_selection.csv").write_text("changed\n")
    with pytest.raises(ValueError, match="hash-mismatched"):
        validate_freeze(freeze, tmp_path, "installed-code-hash")


def test_sidecar_and_source_mismatch_fail_closed(tmp_path):
    freeze, _ = valid_fixture(tmp_path)
    with pytest.raises(ValueError, match="source hash"):
        validate_freeze(freeze, tmp_path, "other-code-hash")
    freeze.with_suffix(".json.sha256").write_text("0" * 64 + "\n")
    with pytest.raises(ValueError, match="sidecar"):
        validate_freeze(freeze, tmp_path, "installed-code-hash")


def test_legacy_official_route_fails_before_data_read(tmp_path):
    with pytest.raises(ValueError, match="disabled"):
        run_cell(tmp_path, "smoke", {}, "chow_liu", "age", 5, 404, (1,),
                 tmp_path / "results", 1, official_test=True,
                 selection_file=tmp_path / "SELECTION_FROZEN.json")
