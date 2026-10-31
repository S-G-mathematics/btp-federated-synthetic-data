import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]
from public_atom_histogram import declared_schema, fit_histogram


def adult_fixture(n=200):
    schema = declared_schema(n, bins=8)
    data = {}
    for column in schema["columns"]:
        if column in schema["numeric_ranges"]:
            data[column] = np.full(n, schema["numeric_ranges"][column][0], int)
        else:
            data[column] = [schema["categories"][column][0]] * n
    data["education"] = ["Bachelors"] * n
    data["education-num"] = np.full(n, 13)
    data["income"] = ["<=50K", ">50K"] * (n//2)
    data["capital-gain"] = np.array([0, 1000] * (n//2))
    data["capital-loss"] = np.array([0, 100] * (n//2))
    return schema, pd.DataFrame(data, columns=schema["columns"])


def test_public_zero_atoms_and_projected_joint_score():
    schema, frame = adult_fixture()
    model = fit_histogram(frame, schema, epsilon=None)
    draws = model.sample(10000, seed=123)
    assert abs(draws["capital-gain"].eq(0).mean() - .5) < .03
    assert abs(draws["capital-loss"].eq(0).mean() - .5) < .03
    assert (draws["capital-gain"] >= 0).all() and (draws["capital-loss"] >= 0).all()
    assert draws["education-num"].eq(13).all()
    assert np.isfinite(model.log_prob(draws)).all()
    bad = draws.iloc[:1].copy()
    bad["education-num"] = 12
    assert model.log_prob(bad)[0] == -np.inf


def test_fresh_noise_ledger_and_exact_fixed_bins():
    schema, frame = adult_fixture()
    model = fit_histogram(frame, schema, epsilon=4.)
    assert model.privacy_ledger["formal_dp_eligible"]
    assert model.privacy_ledger["laplace_scale"] == 7.5
    assert model.privacy_ledger["noise_seed_mode"] == "fresh_os_entropy"
    assert "seed" not in model.privacy_ledger
    assert len(model.probabilities["capital-gain"]) == 8
    assert len(model.probabilities["capital-loss"]) == 8
    assert set(model.sample(1000, 4)["income"]) <= {"<=50K", ">50K"}
