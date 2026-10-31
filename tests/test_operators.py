from pathlib import Path
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from btp.operators import fit_operator, refit_operator_weights


class ToyGenerator:
    def __init__(self, rows, columns=("age", "income")):
        self.rows = pd.DataFrame(rows, columns=columns)

    def sample(self, n, seed):
        rng = np.random.default_rng(seed)
        return self.rows.iloc[rng.integers(0, len(self.rows), n)].reset_index(drop=True)

    def log_prob(self, frame):
        keys = {tuple(r): -np.log(len(self.rows)) for r in self.rows.itertuples(index=False, name=None)}
        return np.array([keys.get(tuple(r), -np.inf) for r in frame.itertuples(index=False, name=None)])


def _fixture():
    return [ToyGenerator([(20, "<=50K"), (40, ">50K")]),
            ToyGenerator([(30, "<=50K"), (60, ">50K")])]


def _fit(name):
    return fit_operator(name, _fixture(), alpha=[.5, .5],
                        query_transform=lambda f: f[["age"]].to_numpy(float),
                        target_summary=[35.], seed=11,
                        settings={"pilot_per_model": 40, "support_size": 8,
                                  "iterations": 80, "regularization": .1})


def test_finite_logpool_normalized_and_off_pool_zero():
    op = _fit("logpool")
    assert op.likelihood_kind == "exact_finite_support"
    assert np.isclose(np.exp(op.log_prob(op.support)).sum(), 1)
    off = pd.DataFrame({"age": [999], "income": [">50K"]})
    assert np.isneginf(op.log_prob(off)[0])
    draw1, draw2 = op.sample(30, 17), op.sample(30, 17)
    assert draw1.equals(draw2)
    assert set(map(tuple, draw1.itertuples(index=False, name=None))).issubset(set(map(tuple, op.support.itertuples(index=False, name=None))))
    assert op.details["support_is_synthetic_only"]


def test_entropic_barycenter_normalized_valid_income_and_posterior():
    op = _fit("entropic_barycenter")
    assert np.isclose(np.exp(op.log_prob(op.support)).sum(), 1)
    draws = op.sample(100, 21)
    assert set(draws.income) == {"<=50K", ">50K"}
    assert np.isfinite(op.posterior(pd.DataFrame({"age": [25, 55]}))).all()
    assert op.details["regularization"] > 0
    assert "not unregularized W2" in op.details["interpretation"]
    assert op.details["converged"]
    assert op.posterior_kind == "kernel_smoothed_approximation"


def test_transport_alias_and_seed_determinism():
    a = _fit("transport_barycenter")
    b = _fit("transport_barycenter")
    assert np.allclose(a.weights, b.weights)
    assert a.sample(12, 1).equals(b.sample(12, 1))


def test_logpool_refit_reuses_identical_pool_and_scores():
    op = _fit("logpool")
    refit = refit_operator_weights(op, [50.], seed=8)
    assert refit.details["refit_on_same_pool"]
    assert refit.details["optimizer_method"] == "SLSQP_epigraph_multistart"
    assert refit.support.equals(op.support)
    assert np.array_equal(refit._logscore, op._logscore)
    assert np.isclose(np.exp(refit.log_prob(refit.support)).sum(), 1)
    assert len(refit.details["refit_attempts"]) >= 2


def test_barycenter_refit_reports_candidate_search_and_convergence():
    op = _fit("entropic_barycenter")
    refit = refit_operator_weights(op, [50.], seed=8, settings={"weight_candidate_draws": 2})
    assert refit.details["refit_on_same_pool"]
    assert refit.details["weight_selection"] == "best_found_candidate_not_global_optimum"
    assert refit.support.equals(op.support)
    assert np.array_equal(refit._cost, op._cost)
    assert len(refit.details["weight_candidate_trials"]) >= 2
    assert refit.details["converged"]
