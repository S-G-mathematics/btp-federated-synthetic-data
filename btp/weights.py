"""Generator-weight baselines for a fixed family of candidate generators.

These are established calibration/ensemble baselines, not novel methods.
References: Yao et al., *Using Stacking to Average Bayesian Predictive
Distributions* (2018), https://doi.org/10.1214/17-BA1091 ; Vehtari et al.,
*Practical Bayesian model evaluation using leave-one-out cross-validation*
(2017), https://doi.org/10.1007/s11222-016-9696-4 . Pseudo-BMA here means a
softmax of common-reference predictive scores; it is not Bayesian evidence.

All outputs are simplex weights over the same fixed generator family.
"""
from __future__ import annotations

import numpy as np
from scipy.optimize import linprog, minimize
from scipy.special import logsumexp


def _simplex(x):
    x = np.asarray(x, dtype=float).reshape(-1)
    if not len(x) or not np.all(np.isfinite(x)) or np.any(x < 0) or x.sum() <= 0:
        raise ValueError("weights must be finite, nonnegative, and have positive sum")
    return x / x.sum()


def solve_weights(method, H, b, alpha, seed=0, settings=None, log_likelihood=None) -> dict:
    """Solve a generator weighting problem.

    ``H`` is L-by-K, ``b`` length L, and ``alpha`` supplies the prior simplex
    (or may be omitted for uniform/size). Optional ``settings`` keys include
    ``sizes`` (K), ``covariance`` (L-by-L residual covariance), ``ridge`` for
    GLS, ``penalty`` for entropy calibration, ``temperature`` for pseudo-BMA,
    and ``privileged`` (default true) to acknowledge validation-score access.
    """
    del seed  # deterministic optimizers; accepted for a uniform runner API
    settings = dict(settings or {})
    names = {"uniform", "size", "moment_l2", "kernel_mean_matching", "query_minimax",
             "robust_query_calibration", "entropy_calibration", "uncertainty_gls",
             "stacking_logscore", "pseudo_bma_logscore", "predictive_evidence_bma",
             "oracle_query_minimax"}
    if method not in names:
        raise ValueError(f"unknown method {method!r}; available methods: {sorted(names)}")
    H = np.asarray(H, dtype=float)
    b = np.asarray(b, dtype=float).reshape(-1)
    if H.ndim != 2 or H.shape[0] != len(b) or not H.shape[1] or not np.all(np.isfinite(H)) or not np.all(np.isfinite(b)):
        raise ValueError("H must be finite L-by-K and b finite length L")
    L, K = H.shape
    prior = _simplex(np.ones(K) if alpha is None else alpha)
    if len(prior) != K:
        raise ValueError("alpha must have K entries")
    method_used = "query_minimax" if method == "oracle_query_minimax" else method
    if method_used == "kernel_mean_matching":
        method_used = "moment_l2"
    details = {"method": method, "family_fixed": True}
    if method == "oracle_query_minimax":
        details.update({"oracle": True, "reference": "REAL validation target; same H,b solver"})

    success, message = True, "optimized"
    if method_used == "uniform":
        w = np.ones(K) / K
    elif method_used == "size":
        sizes = np.asarray(settings.get("sizes", []), dtype=float)
        if sizes.shape != (K,) or np.any(~np.isfinite(sizes)) or np.any(sizes < 0) or sizes.sum() <= 0:
            raise ValueError("size requires settings['sizes'] with K nonnegative counts")
        w = _simplex(sizes)
    elif method_used in ("moment_l2", "uncertainty_gls"):
        if method_used == "uncertainty_gls":
            cov = np.asarray(settings.get("covariance"), dtype=float)
            if cov.shape != (L, L) or not np.all(np.isfinite(cov)):
                raise ValueError("uncertainty_gls requires finite L-by-L settings['covariance']")
            cov = (cov + cov.T) / 2
            ridge = float(settings.get("ridge", 1e-9))
            if not np.isfinite(ridge) or ridge <= 0:
                raise ValueError("ridge must be finite and positive")
            eigval, eigvec = np.linalg.eigh(cov)
            if eigval.min() < -max(1e-10, ridge * 1e-6):
                raise ValueError("covariance has materially negative eigenvalues")
            # Ridge regularizes semidefinite/near-singular estimates. Factor
            # once; optimizer calls only require a matrix-vector product.
            precision = (eigvec / np.maximum(eigval + ridge, ridge)) @ eigvec.T
        def whitened(x):
            d = H @ x - b
            if method_used == "uncertainty_gls":
                return float(d @ precision @ d)
            return float(d @ d)
        # Scale the objective and supply its exact gradient. The estimated
        # residual covariance can be small, so finite-difference SLSQP may
        # report a false line-search failure even for this convex quadratic.
        objective_scale = max(1.0, abs(whitened(prior))) if method_used == "uncertainty_gls" else 1.0
        def gradient(x):
            d = H @ x - b
            return (2 * H.T @ (precision @ d if method_used == "uncertainty_gls" else d)) / objective_scale
        res = minimize(lambda x: whitened(x) / objective_scale, prior, jac=gradient,
                       method="SLSQP", bounds=[(0, 1)]*K,
                       constraints=[{"type": "eq", "fun": lambda x: x.sum()-1,
                                     "jac": lambda x: np.ones(K)}],
                       options={"maxiter": int(settings.get("maxiter", 1000)), "ftol": 1e-12})
        if method_used == "uncertainty_gls":
            details.update({"optimizer": "SLSQP_analytic_gradient_scaled",
                            "objective_scale": objective_scale})
        success, message = bool(res.success), str(res.message)
        w = res.x
        if method == "kernel_mean_matching":
            details.update({"method_family": "KMM-style kernel mean matching",
                            "kernel_embedding_input": True,
                            "implementation": "simplex-constrained squared kernel-mean discrepancy"})
    elif method_used == "robust_query_calibration":
        model_var = np.asarray(settings.get("model_var"), dtype=float)
        target_var = np.asarray(settings.get("target_var"), dtype=float).reshape(-1)
        radius = float(settings.get("radius", 1.0))
        if model_var.shape != (L, K) or target_var.shape != (L,):
            raise ValueError("robust_query_calibration requires model_var (L-by-K) and target_var (L,)")
        if (not np.all(np.isfinite(model_var)) or not np.all(np.isfinite(target_var))
                or np.any(model_var < 0) or np.any(target_var < 0)):
            raise ValueError("model_var and target_var must be finite and nonnegative")
        if not np.isfinite(radius) or radius < 0:
            raise ValueError("radius must be finite and nonnegative")
        def risks(x):
            weights, t = x[:K], x[K]
            spread = np.sqrt(target_var + np.sum(weights[:, None]**2 * model_var.T, axis=0))
            return t - (np.abs(H @ weights - b) + radius * spread)
        def risks_jac(x):
            weights = x[:K]
            residual = H @ weights - b
            spread = np.sqrt(target_var + np.sum(weights[:, None]**2 * model_var.T, axis=0))
            grad = np.sign(residual)[:, None] * H
            grad += radius * (model_var * weights[None, :]) / np.maximum(spread[:, None], 1e-15)
            return np.c_[-grad, np.ones(L)]
        def robust_obj(x): return float(x[K])
        def robust_obj_jac(x): return np.r_[np.zeros(K), 1.]
        start_risk = np.abs(H @ prior - b) + radius * np.sqrt(target_var + np.sum(prior[:, None]**2 * model_var.T, axis=0))
        x0 = np.r_[prior, start_risk.max()]
        res = minimize(robust_obj, x0, jac=robust_obj_jac, method="SLSQP", bounds=[(0, 1)]*K+[(0, None)],
                       constraints=[{"type": "eq", "fun": lambda x: x[:K].sum()-1,
                                     "jac": lambda x: np.r_[np.ones(K), 0.]},
                                    {"type": "ineq", "fun": risks, "jac": risks_jac}],
                       options={"maxiter": int(settings.get("maxiter", 1000)), "ftol": 1e-10})
        success, message = bool(res.success), str(res.message)
        w = res.x[:K]
        details.update({"method_family": "robust query calibration",
                        "interpretation": "uncertainty-set-inspired robust objective; not a faithful AFL implementation",
                        "radius": radius, "robust_epigraph": float(res.x[K])})
    elif method_used in ("query_minimax",):
        # min t subject to -t <= Hw-b <= t and simplex constraints.
        c = np.r_[np.zeros(K), 1.]
        Aub = np.vstack([np.c_[H, -np.ones(L)], np.c_[-H, -np.ones(L)]])
        bub = np.r_[b, -b]
        Aeq = np.array([[*([1.] * K), 0.]])
        res = linprog(c, A_ub=Aub, b_ub=bub, A_eq=Aeq, b_eq=[1.],
                      bounds=[(0, 1)]*K+[(0, None)], method="highs")
        success, message = bool(res.success), str(res.message)
        w = res.x[:K] if res.x is not None else np.full(K, np.nan)
    elif method_used == "entropy_calibration":
        penalty = float(settings.get("penalty", 1.0))
        if penalty < 0 or not np.isfinite(penalty):
            raise ValueError("penalty must be finite and nonnegative")
        def objective(x):
            positive = x > 0
            kl = np.sum(x[positive] * np.log(x[positive] / prior[positive]))
            d = H @ x - b
            return float(kl + penalty * (d @ d))
        bounds = [(1e-12, 1) if prior[k] > 0 else (0, 0) for k in range(K)]
        res = minimize(objective, prior, method="SLSQP", bounds=bounds,
                       constraints=[{"type": "eq", "fun": lambda x: x.sum()-1}],
                       options={"maxiter": int(settings.get("maxiter", 1000)), "ftol": 1e-12})
        success, message = bool(res.success), str(res.message)
        w = res.x
        details["penalty"] = penalty
        details["exact_balance"] = bool(np.linalg.norm(H @ w - b, ord=np.inf) < 1e-8)
    elif method_used in ("stacking_logscore", "pseudo_bma_logscore", "predictive_evidence_bma"):
        if log_likelihood is None:
            raise ValueError(f"{method} requires common-reference log_likelihood (n-by-K)")
        ll = np.asarray(log_likelihood, dtype=float)
        if ll.ndim != 2 or ll.shape[1] != K or not ll.shape[0] or not np.all(np.isfinite(ll)):
            raise ValueError("log_likelihood must be finite n-by-K")
        sample_weights = np.asarray(settings.get("sample_weights", np.ones(ll.shape[0])), dtype=float).reshape(-1)
        if (sample_weights.shape != (ll.shape[0],) or not np.all(np.isfinite(sample_weights))
                or np.any(sample_weights <= 0) or not np.isclose(sample_weights.sum(), ll.shape[0], rtol=1e-8, atol=1e-8)):
            raise ValueError("sample_weights must be finite, strictly positive, length n, and sum to n")
        details["sample_weighted_scores"] = not np.allclose(sample_weights, 1.)
        details.update({"validation_scores": True, "privileged": bool(settings.get("privileged", True))})
        if method_used == "predictive_evidence_bma":
            model_prior = _simplex(settings.get("model_prior", np.ones(K)))
            if len(model_prior) != K:
                raise ValueError("model_prior must have K entries")
            scores = sample_weights @ ll
            logprior = np.full(K, -np.inf)
            logprior[model_prior > 0] = np.log(model_prior[model_prior > 0])
            w = np.exp(scores + logprior - logsumexp(scores + logprior))
            details.update({"method_family": "conditional fixed-model predictive evidence BMA",
                            "model_prior": model_prior.tolist(),
                            "interpretation": "common-reference scores conditional on supplied fitted models; not integrated training-model evidence" if np.allclose(sample_weights, 1.) else "power predictive evidence from normalized per-reference weights, conditional on supplied fitted models; not integrated training-model evidence"})
        elif method_used == "pseudo_bma_logscore":
            temp = float(settings.get("temperature", 1.0))
            if temp <= 0 or not np.isfinite(temp): raise ValueError("temperature must be positive")
            score = sample_weights @ ll
            w = np.exp(temp * score - logsumexp(temp * score))
            details.update({"temperature": temp, "interpretation": "softmax common-reference scores; not Bayesian model evidence"})
        else:
            # The mixture log score is concave in simplex weights. Optimize
            # the mean score with its analytic gradient, then check its
            # Frank-Wolfe/first-order dual gap. Finite-difference SLSQP can
            # falsely fail near zero weights in heterogeneous K=10 cells.
            score_scale = float(sample_weights.sum())
            def score_gradient(x):
                safe = np.maximum(x, 1e-12)
                denominator = logsumexp(ll + np.log(safe)[None, :], axis=1)
                value = -float(sample_weights @ denominator / score_scale)
                gradient = -(sample_weights @ np.exp(ll-denominator[:, None])) / score_scale
                return value, gradient
            def dual_gap(x):
                _, negative_gradient = score_gradient(x)
                derivative = -negative_gradient
                return float(derivative.max()-x @ derivative)
            res = minimize(score_gradient, prior, jac=True, method="SLSQP",
                           bounds=[(1e-12, 1)]*K,
                           constraints=[{"type": "eq", "fun": lambda x: x.sum()-1,
                                         "jac": lambda x: np.ones(K)}],
                           options={"maxiter": int(settings.get("maxiter", 3000)), "ftol": 1e-12})
            w = res.x
            gap = dual_gap(w) if np.all(np.isfinite(w)) else np.inf
            success = bool(res.success and gap <= 1e-5)
            message = str(res.message)
            details.update({"optimizer": "SLSQP_mean_score_analytic_gradient",
                            "iterations": int(res.nit), "duality_gap": gap,
                            "score_scale": score_scale})
            if not success:
                # EM is monotone for fixed candidate densities. Accept a
                # fallback only with the same independently checked gap.
                w = np.maximum(prior, 1e-12); w /= w.sum()
                em_iterations = 0
                for em_iterations in range(1, int(settings.get("em_maxiter", 10000))+1):
                    denominator = logsumexp(ll + np.log(w)[None, :], axis=1)
                    responsibilities = np.exp(ll + np.log(w)[None, :]-denominator[:, None])
                    w = (sample_weights @ responsibilities) / score_scale
                    w = np.maximum(w, 1e-12); w /= w.sum()
                    gap = dual_gap(w)
                    if gap <= 1e-6: break
                success = bool(gap <= 1e-5)
                message = "EM converged with dual gap certificate" if success else "EM did not meet dual gap certificate"
                details.update({"optimizer": "EM_fallback", "iterations": em_iterations,
                                "duality_gap": gap, "slsqp_message": str(res.message)})
    else:
        raise AssertionError("unhandled method")

    # Never conceal optimizer failure or repair an invalid optimizer result.
    w = np.asarray(w, dtype=float).reshape(-1)
    valid = w.shape == (K,) and np.all(np.isfinite(w)) and np.all(w >= -1e-8) and abs(w.sum()-1) < 1e-5
    success = bool(success and valid)
    if valid:
        w = np.maximum(w, 0); w /= w.sum()
    else:
        details["invalid_solution"] = True
    details["message"] = message
    details["simplex_valid"] = bool(valid)
    if method_used in ("moment_l2", "uncertainty_gls", "query_minimax", "entropy_calibration", "robust_query_calibration"):
        discrepancy = H @ w - b if valid else np.full(L, np.nan)
        objective = float(np.linalg.norm(discrepancy, ord=np.inf) if method_used == "query_minimax" else (
            (discrepancy @ discrepancy) if method_used == "moment_l2" else
            (discrepancy @ precision @ discrepancy
             if method_used == "uncertainty_gls" else
             (float(res.fun) if method_used in ("entropy_calibration", "robust_query_calibration") else float("nan"))))) if valid else float("nan")
        details["residual_linf"] = float(np.max(np.abs(discrepancy))) if valid else None
    elif method_used == "stacking_logscore":
        ll = np.asarray(log_likelihood)
        score_weights = np.asarray(settings.get("sample_weights", np.ones(ll.shape[0])), dtype=float)
        objective = float(np.dot(score_weights, logsumexp(ll + np.log(np.maximum(w, 1e-300))[None,:], axis=1))) if valid else float("nan")
    elif method_used == "pseudo_bma_logscore":
        ll = np.asarray(log_likelihood)
        score_weights = np.asarray(settings.get("sample_weights", np.ones(ll.shape[0])), dtype=float)
        objective = float(np.dot(w, score_weights @ ll)) if valid else float("nan")
    elif method_used == "predictive_evidence_bma":
        ll = np.asarray(log_likelihood)
        score_weights = np.asarray(settings.get("sample_weights", np.ones(ll.shape[0])), dtype=float)
        objective = float(logsumexp(score_weights @ ll + np.log(np.maximum(np.asarray(settings.get("model_prior", np.ones(K)), dtype=float), 1e-300)))) if valid else float("nan")
    else:
        objective = 0.0
    return {"weights": w, "success": success, "objective": objective, "details": details}
