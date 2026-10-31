import numpy as np
import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from btp.weights import solve_weights


def test_query_minimax_known_exact_solution():
    H = np.array([[0., 1.], [1., 0.]])
    result = solve_weights("query_minimax", H, np.array([.25, .75]), [1, 1])
    assert result["success"]
    np.testing.assert_allclose(result["weights"], [.75, .25], atol=1e-7)
    assert result["objective"] < 1e-7


@pytest.mark.parametrize("method,settings", [
    ("uniform", {}),
    ("size", {"sizes": [1, 3, 2]}),
    ("moment_l2", {}),
    ("kernel_mean_matching", {}),
    ("query_minimax", {}),
    ("robust_query_calibration", {"model_var": [[.01, .02, .01], [.02, .01, .03]], "target_var": [.01, .02], "radius": 1.}),
    ("entropy_calibration", {"penalty": 2.}),
    ("uncertainty_gls", {"covariance": [[2., .2], [.2, 1.]]}),
    ("stacking_logscore", {}),
    ("pseudo_bma_logscore", {}),
    ("predictive_evidence_bma", {}),
    ("oracle_query_minimax", {}),
])
def test_all_methods_return_simplex(method, settings):
    H, b = np.array([[0., 1., .4], [1., 0., .6]]), np.array([.4, .7])
    ll = np.array([[-1., -2., -1.4], [-2., -1., -1.3]])
    result = solve_weights(method, H, b, [1, 2, 1], settings=settings, log_likelihood=ll)
    w = result["weights"]
    assert w.shape == (3,)
    assert np.all(w >= 0)
    assert w.sum() == pytest.approx(1.)
    assert isinstance(result["details"], dict)


def test_stacking_and_pseudo_bma_are_explicitly_privileged():
    H, b = np.eye(2), np.array([.5, .5])
    ll = np.array([[-.1, -2.], [-.1, -2.]])
    stack = solve_weights("stacking_logscore", H, b, [1, 1], log_likelihood=ll)
    pseudo = solve_weights("pseudo_bma_logscore", H, b, [1, 1], log_likelihood=ll)
    assert stack["details"]["privileged"]
    assert pseudo["details"]["interpretation"].startswith("softmax")
    score = ll.sum(axis=0)
    expected = np.exp(score - np.logaddexp.reduce(score))
    np.testing.assert_allclose(pseudo["weights"], expected)


@pytest.mark.parametrize("temperature", [.1, 2.])
def test_pseudo_bma_temperature_softmax_is_normalized(temperature):
    ll = np.array([[-1., -4.], [-2., -3.]])
    scores = ll.sum(axis=0)
    expected = np.exp(temperature * scores - np.logaddexp.reduce(temperature * scores))
    result = solve_weights("pseudo_bma_logscore", np.eye(2), [.5, .5], [1, 1],
                           settings={"temperature": temperature}, log_likelihood=ll)
    np.testing.assert_allclose(result["weights"], expected)


def test_predictive_evidence_bma_matches_uniform_pseudo_bma_at_temperature_one():
    ll = np.array([[-.5, -2.], [-1.2, -1.5], [-.9, -2.1]])
    args = (np.eye(2), [.5, .5], [1, 1])
    bma = solve_weights("predictive_evidence_bma", *args, log_likelihood=ll)
    pseudo = solve_weights("pseudo_bma_logscore", *args, settings={"temperature": 1.}, log_likelihood=ll)
    np.testing.assert_allclose(bma["weights"], pseudo["weights"])


def test_weighted_predictive_scores_use_per_reference_weights_summing_to_n():
    ll = np.array([[-.1, -2.], [-1.4, -.2], [-.7, -1.1]])
    observation_weights = np.array([1.5, .5, 1.])
    settings = {"sample_weights": observation_weights}
    prior = np.array([.8, .2])
    score = observation_weights @ ll
    expected_bma = np.exp(score + np.log(prior) - np.logaddexp.reduce(score + np.log(prior)))
    expected_pseudo = np.exp(score - np.logaddexp.reduce(score))
    bma = solve_weights("predictive_evidence_bma", np.eye(2), [.5, .5], [1, 1],
                        settings={**settings, "model_prior": prior}, log_likelihood=ll)
    pseudo = solve_weights("pseudo_bma_logscore", np.eye(2), [.5, .5], [1, 1],
                           settings=settings, log_likelihood=ll)
    np.testing.assert_allclose(bma["weights"], expected_bma)
    np.testing.assert_allclose(pseudo["weights"], expected_pseudo)
    assert bma["weights"].sum() == pytest.approx(1.)
    assert bma["details"]["sample_weighted_scores"]
    with pytest.raises(ValueError, match="sum to n"):
        solve_weights("stacking_logscore", np.eye(2), [.5, .5], [1, 1],
                      settings={"sample_weights": [2., 1., 1.]}, log_likelihood=ll)


def test_stacking_uses_reference_weights_in_weighted_log_score():
    ll = np.array([[0., -4.], [-4., 0.]])
    wobs = np.array([1.8, .2])
    result = solve_weights("stacking_logscore", np.eye(2), [.5, .5], [1, 1],
                           settings={"sample_weights": wobs}, log_likelihood=ll)
    assert result["success"]
    assert result["weights"][0] > .8


def test_robust_query_calibration_returns_simplex_and_accounts_for_uncertainty():
    H = np.array([[0., 1.], [1., 0.]])
    result = solve_weights("robust_query_calibration", H, [.2, .8], [1, 1], settings={
        "model_var": [[.01, .02], [.02, .01]], "target_var": [.01, .01], "radius": 1.5})
    assert result["success"]
    assert result["weights"].sum() == pytest.approx(1.)
    assert result["objective"] >= 0
    assert "not a faithful AFL" in result["details"]["interpretation"]


def test_gls_whitens_residual_covariance_and_not_generator_alpha():
    H = np.array([[0., 1.], [1., 0.]])
    b = np.array([.2, .8])
    cov = np.diag([100., .01])
    a = solve_weights("uncertainty_gls", H, b, [1, 1], settings={"covariance": cov})
    bresult = solve_weights("uncertainty_gls", H, b, [1000, 1], settings={"covariance": cov})
    assert a["success"] and bresult["success"]
    np.testing.assert_allclose(a["weights"], bresult["weights"], atol=1e-4)
    assert a["weights"][0] > .7  # high-variance first residual is discounted


def test_missing_logscore_and_bad_size_are_errors():
    with pytest.raises(ValueError, match="requires common-reference"):
        solve_weights("stacking_logscore", np.eye(2), [.5, .5], [1, 1])
    with pytest.raises(ValueError, match="sizes"):
        solve_weights("size", np.eye(2), [.5, .5], [1, 1], settings={"sizes": [0, 0]})


def test_gls_rejects_materially_indefinite_covariance():
    with pytest.raises(ValueError, match="negative eigenvalues"):
        solve_weights("uncertainty_gls", np.eye(2), [.5, .5], [1, 1],
                      settings={"covariance": [[1., 3.], [3., 1.]]})


def test_nonconvergence_is_not_silently_replaced():
    # One iteration is insufficient for the requested nonlinear optimization.
    result = solve_weights("stacking_logscore", np.eye(3), [1, 0, 0], [1, 1, 1],
                           settings={"maxiter": 1, "em_maxiter": 1}, log_likelihood=np.array([[0., -1., -2.]]))
    assert not result["success"]
    assert not result["details"]["simplex_valid"] or result["details"]["message"]



def test_gls_scaled_gradient_handles_small_residual_covariance():
    # A realistic small covariance made finite-difference SLSQP falsely report
    # "Positive directional derivative for linesearch" in the full-data pilot.
    rng = np.random.default_rng(3)
    H = rng.uniform(0, 1, (60, 5))
    truth = np.array([.02, .38, .1, .45, .05])
    b = H @ truth + rng.normal(0, .03, 60)
    prior = np.ones(5) / 5
    result = solve_weights("uncertainty_gls", H, b, prior,
                           settings={"covariance": np.eye(60) * 1e-5})
    assert result["success"]
    np.testing.assert_allclose(result["weights"].sum(), 1., atol=1e-8)
    assert np.all(result["weights"] >= 0)
    prior_objective = np.sum((H @ prior - b)**2) / (1e-5 + 1e-9)
    assert result["objective"] < prior_objective
    assert result["details"]["optimizer"] == "SLSQP_analytic_gradient_scaled"


def test_stacking_certifies_multimodel_weighted_logscore():
    # An independent first-order certificate checks the concave mixture score
    # even when the optimum lies near the simplex boundary.
    rng = np.random.default_rng(42)
    ll = rng.normal(-25., 4., (400, 10))
    ll[:, 0] += 2.
    ll[::2, 1] += 5.
    observation_weights = np.linspace(.5, 1.5, len(ll))
    observation_weights *= len(ll) / observation_weights.sum()
    result = solve_weights("stacking_logscore", np.zeros((1, 10)), [0.],
                           np.ones(10)/10, settings={"sample_weights": observation_weights},
                           log_likelihood=ll)
    assert result["success"]
    assert result["details"]["duality_gap"] <= 1e-5
    np.testing.assert_allclose(result["weights"].sum(), 1., atol=1e-8)
    assert np.all(result["weights"] >= 0)
    from scipy.special import logsumexp
    fitted = observation_weights @ logsumexp(ll + np.log(np.maximum(result["weights"], 1e-300)), axis=1)
    uniform = observation_weights @ logsumexp(ll - np.log(10), axis=1)
    assert fitted >= uniform - 1e-7
