from pathlib import Path
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from btp.privacy import (fit_nonprivate_public_histogram, fit_private_histogram,
                         public_schema, release_query_summary)


def fixture(n=8):
    schema = public_schema(n_public=n, bins=4)
    rows = {}
    for c in schema["columns"]:
        if c in schema["numeric_ranges"]:
            lo, hi = schema["numeric_ranges"][c]
            rows[c] = np.linspace(lo, hi, n)
        elif c == "income":
            rows[c] = ["<=50K", ">50K"] * (n // 2)
        else:
            rows[c] = [schema["categories"][c][0]] * n
    return schema, pd.DataFrame(rows, columns=schema["columns"])


def test_public_schema_has_full_fixed_columns_and_unknowns():
    schema = public_schema(4)
    assert len(schema["columns"]) == 15
    assert schema["categories"]["income"] == ["<=50K", ">50K"]
    assert "__UNKNOWN__" in schema["categories"]["native-country"]


def test_histogram_noise_scale_ledger_clipping_and_sampler_score():
    schema, frame = fixture()
    model = fit_private_histogram(frame, epsilon=2., seed=5, schema=schema)
    assert model.privacy_ledger["epsilon_spent"] == 2.
    assert not model.privacy_ledger["formal_dp_eligible"]
    assert model.privacy_ledger["noise_seed_mode"] == "deterministic_research_seed"
    assert model.privacy_ledger["releases"][0]["sensitivity_l1"] == 30
    assert model.privacy_ledger["releases"][0]["scale"] == 15
    for p in model.probabilities.values():
        assert np.all(p > 0)
        assert p.sum() == pytest.approx(1.)
    draws = model.sample(20, seed=8)
    assert list(draws.columns) == schema["columns"]
    assert np.all(np.isfinite(model.log_prob(draws)))


def test_unknown_and_out_of_range_inputs_are_bounded_to_public_schema():
    schema, frame = fixture()
    frame.loc[0, "age"] = -1000
    frame.loc[1, "age"] = 10000
    frame.loc[0, "workclass"] = "unseen private category"
    model = fit_private_histogram(frame, 1., 4, schema)
    assert model.probabilities["workclass"][-1] > 0
    assert np.all((model.sample(100, 2)["age"] >= 0) & (model.sample(100, 2)["age"] <= 100))


def test_integer_bins_have_nonempty_support_and_income_domain_is_strict():
    schema, frame = fixture()
    schema["bins"] = 64  # education-num has only 17 public integer values
    frame.loc[0, "education-num"] = 16
    model = fit_private_histogram(frame, 1., 9, schema)
    sample = model.sample(200, 10)
    assert set(sample["education-num"]) <= set(range(17))
    assert np.all(np.isfinite(model.log_prob(sample)))
    frame.loc[0, "income"] = "?"
    with pytest.raises(ValueError, match="outside public categorical domain"):
        fit_private_histogram(frame, 1., 9, schema)


def test_fixed_public_n_required_and_sequential_composition_adds_epsilon():
    schema, frame = fixture()
    with pytest.raises(ValueError, match="fixed public n_public"):
        fit_private_histogram(frame.iloc[:-1], 1., 4, schema)
    model = fit_private_histogram(frame, 1.5, 4, schema)
    vals, ledger = release_query_summary(frame, lambda f: np.column_stack([
        f["age"].to_numpy(float) / 100., np.ones(len(f))]), .5, 6,
        model.privacy_ledger, n_public=len(frame))
    assert vals.shape == (2,)
    assert ledger["epsilon_spent"] == 2.
    assert not ledger["formal_dp_eligible"]
    assert len(ledger["releases"]) == 2
    assert ledger["releases"][1]["sensitivity_l1"] == pytest.approx(2/len(frame))


def test_query_summary_rejects_unbounded_transform():
    schema, frame = fixture()
    model = fit_private_histogram(frame, 1., 4, schema)
    with pytest.raises(ValueError, match=r"bounded in \[0,1\]"):
        release_query_summary(frame, lambda f: np.full((len(f), 1), 4.), .5, 7,
                              model.privacy_ledger, len(frame))


def test_fresh_os_entropy_is_formally_dp_eligible_without_storing_seed():
    schema, frame = fixture()
    model = fit_private_histogram(frame, epsilon=1., schema=schema)
    assert model.privacy_ledger["formal_dp_eligible"]
    assert model.privacy_ledger["noise_seed_mode"] == "fresh_os_entropy"
    assert "seed" not in model.privacy_ledger
    released, ledger = release_query_summary(frame, lambda f: np.ones((len(f), 1)), .5,
                                              privacy_ledger=model.privacy_ledger,
                                              n_public=len(frame))
    assert released.shape == (1,)
    assert ledger["formal_dp_eligible"]
    assert ledger["noise_seed_mode"] == "fresh_os_entropy"


def test_nonprivate_histogram_uses_public_counts_and_valid_generated_labels():
    schema, frame = fixture()
    model = fit_nonprivate_public_histogram(frame, schema)
    record = model.privacy_ledger["releases"][0]
    assert not model.privacy_ledger["formal_dp_eligible"]
    assert model.privacy_ledger["epsilon_spent"] is None
    assert record["epsilon"] is None
    assert record["mechanism"] == "none"
    # The two income bins have four observations each, followed by only the
    # documented tiny pseudocount; no noisy count was added.
    counts = np.asarray(record["expected_counts"]["income"])
    np.testing.assert_array_equal(counts, [4., 4.])
    np.testing.assert_allclose(model.probabilities["income"], (counts + 1e-12) / (8 + 2e-12))
    draws = model.sample(500, seed=22)
    assert set(draws["income"]) <= {"<=50K", ">50K"}
    assert np.all(np.isfinite(model.log_prob(draws)))


def test_nonprivate_histogram_matches_dp_public_bin_schema():
    schema, frame = fixture()
    private_model = fit_private_histogram(frame, 1., seed=13, schema=schema)
    reference = fit_nonprivate_public_histogram(frame, schema)
    assert private_model.schema == reference.schema
    assert private_model.probabilities["income"].shape == reference.probabilities["income"].shape
    assert reference.probabilities["age"].shape == private_model.probabilities["age"].shape
    assert np.all(np.asarray(reference.privacy_ledger["releases"][0]["expected_counts"]["age"]) >= 0)
