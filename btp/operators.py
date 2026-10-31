"""Finite synthetic-candidate generator pooling operators.

Both operators normalize over a deduplicated pool made only from ``model.sample``
draws. Their returned log scores are exact *finite-pool masses*; off-pool rows
have zero mass. They are not continuous densities or probabilities over the
full table space.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.special import logsumexp


def _simplex(value, k):
    x = np.asarray(value if value is not None else np.ones(k), dtype=float).reshape(-1)
    if x.shape != (k,) or np.any(~np.isfinite(x)) or np.any(x < 0) or x.sum() <= 0:
        raise ValueError("alpha must be a finite nonnegative K-vector with positive sum")
    return x / x.sum()


def _key(row):
    return tuple("__NA__" if pd.isna(v) else v.item() if hasattr(v, "item") else v for v in row)


def _features(frame, transform):
    x = transform(frame) if callable(transform) else frame.select_dtypes(include=[np.number]).to_numpy(float)
    x = np.asarray(x, dtype=float)
    if x.ndim == 1:
        x = x[:, None]
    if x.ndim != 2 or x.shape[0] != len(frame) or np.any(~np.isfinite(x)):
        raise ValueError("query_transform must return a finite row-aligned vector or matrix")
    return x


def _loss(q, feature, target, kind="l2"):
    delta = q @ feature - target
    return float(np.max(np.abs(delta)) if kind == "linf" else delta @ delta)


class FinitePoolOperator:
    def __init__(self, support, probs, weights, details, query_transform=None):
        self.support = support.reset_index(drop=True)
        self.probs = np.asarray(probs, float) / np.sum(probs)
        self.weights = np.asarray(weights, float)
        self.details = details
        self.query_transform = query_transform
        self.likelihood_kind = "exact_finite_support"
        self.posterior_kind = "kernel_smoothed_approximation"
        self._lookup = {_key(row): i for i, row in enumerate(self.support.itertuples(index=False, name=None))}

    def sample(self, n: int, seed: int) -> pd.DataFrame:
        idx = np.random.default_rng(seed).choice(len(self.support), size=n, p=self.probs)
        return self.support.iloc[idx].reset_index(drop=True)

    def log_prob(self, frame: pd.DataFrame) -> np.ndarray:
        out = np.full(len(frame), -np.inf)
        for i, row in enumerate(frame.itertuples(index=False, name=None)):
            j = self._lookup.get(_key(row))
            if j is not None:
                out[i] = np.log(self.probs[j]) if self.probs[j] > 0 else -np.inf
        return out

    def posterior(self, frame: pd.DataFrame) -> np.ndarray:
        """Kernel-smoothed P(income='>50K' | row predictors), when available."""
        if "income" not in self.support or self.query_transform is None:
            raise ValueError("posterior requires an income column and query_transform")
        cols = [c for c in self.support.columns if c != "income"]
        x = _features(frame.loc[:, cols], self.query_transform)
        s = _features(self.support.loc[:, cols], self.query_transform)
        scale = np.maximum(np.std(s, axis=0), 1e-8)
        d2 = np.sum(((x[:, None, :] - s[None, :, :]) / scale) ** 2, axis=2)
        bandwidth = float(self.details.get("posterior_bandwidth", 1.0))
        kernel = np.exp(-.5 * d2 / max(bandwidth**2, 1e-12)) * self.probs[None, :]
        high = (self.support["income"].astype(str).to_numpy() == ">50K").astype(float)
        return (kernel @ high) / np.maximum(kernel.sum(axis=1), 1e-300)


def _pilot_pool(models, seed, settings):
    n = max(1, int(settings.get("pilot_per_model", settings.get("support_size", 128))))
    pieces = []
    for j, model in enumerate(models):
        sample = model.sample(n, seed + 104729 * j)
        if not isinstance(sample, pd.DataFrame):
            raise TypeError("each model.sample must return a DataFrame")
        pieces.append(sample)
    columns = list(pieces[0].columns)
    if any(list(p.columns) != columns for p in pieces):
        raise ValueError("all model samples must have the same ordered columns")
    pool = pd.concat(pieces, ignore_index=True).drop_duplicates(ignore_index=True)
    cap = max(1, int(settings.get("support_size", len(pool))))
    if len(pool) > cap:
        keep = np.sort(np.random.default_rng(seed).choice(len(pool), size=cap, replace=False))
        pool = pool.iloc[keep].reset_index(drop=True)
    return pool, pieces


def _model_log_matrix(models, pool, settings):
    rows, smoothed = [], 0
    floor = float(settings.get("logscore_floor", -60.0))
    for model in models:
        score = np.asarray(model.log_prob(pool), dtype=float).reshape(-1)
        if len(score) != len(pool):
            raise ValueError("model.log_prob must return one score per candidate")
        bad = ~np.isfinite(score)
        smoothed += int(bad.sum())
        score[bad] = floor
        rows.append(score)
    return np.column_stack(rows), smoothed


def _mixed_cost(support, settings):
    nums = list(support.select_dtypes(include=[np.number]).columns)
    cats = [c for c in support.columns if c not in nums]
    n = len(support)
    cost = np.zeros((n, n), float)
    bounds = settings.get("numeric_bounds", {})
    for c in nums:
        x = pd.to_numeric(support[c]).to_numpy(float)
        if c in bounds:
            scale = max(float(bounds[c][1]) - float(bounds[c][0]), 1.0)
        else:
            scale = max(float(np.max(x) - np.min(x)), 1.0)
        d = (x[:, None] - x[None, :]) / scale
        cost += d*d / max(1, len(nums))
    for c in cats:
        x = support[c].astype(str).to_numpy()
        cost += (x[:, None] != x[None, :]).astype(float) / max(1, len(cats))
    return cost


def _row_to_pool_cost(row, support, settings):
    """Vectorized O(S*d) mixed cost from one row to the shared support."""
    nums = list(support.select_dtypes(include=[np.number]).columns)
    cats = [c for c in support.columns if c not in nums]
    cost = np.zeros(len(support), float)
    bounds = settings.get("numeric_bounds", {})
    for c in nums:
        values = pd.to_numeric(support[c]).to_numpy(float)
        scale = max(float(bounds[c][1])-float(bounds[c][0]), 1.0) if c in bounds else max(float(values.max()-values.min()), 1.0)
        cost += ((values-float(row[support.columns.get_loc(c)]))/scale)**2 / max(1,len(nums))
    for c in cats:
        values = support[c].astype(str).to_numpy()
        cost += (values != str(row[support.columns.get_loc(c)])).astype(float) / max(1,len(cats))
    return cost


def _sinkhorn_barycenter(hist, cost, weights, reg, iterations, tol):
    # Entropic Wasserstein barycenter on a shared finite support, via the
    # standard scaling fixed point. Smoothing makes every source histogram >0.
    kernel = np.exp(-np.maximum(cost, 0) / reg) + 1e-300
    u = np.ones_like(hist)
    v = np.ones_like(hist)
    b = np.full(hist.shape[1], 1 / hist.shape[1])
    err = np.inf
    for it in range(iterations):
        kv = np.maximum(kernel @ v.T, 1e-300).T
        u = hist / kv
        ktu = np.maximum(kernel.T @ u.T, 1e-300).T
        log_b = np.sum(weights[:, None] * np.log(ktu), axis=0)
        b_new = np.exp(log_b - logsumexp(log_b))
        err = float(np.sum(np.abs(b_new - b)))
        b = b_new
        v = b[None, :] / ktu
        if err < tol:
            break
    return b / b.sum(), it + 1, err, bool(err < tol)


def fit_operator(name: str, models, alpha, query_transform, target_summary, seed=0, settings=None):
    """Fit ``logpool`` or ``entropic_barycenter`` on synthetic pilot rows.

    ``query_transform`` maps frames to finite numeric query features and
    ``target_summary`` is their requested mean. Barycenter weights default to
    normalized ``alpha``; optional ``weight_candidates`` can select among a
    few deterministic/simplex candidates against the same query loss.
    """
    settings = dict(settings or {})
    models = list(models)
    if not models:
        raise ValueError("models must be nonempty")
    if name not in ("logpool", "entropic_barycenter", "transport_barycenter"):
        raise ValueError("name must be 'logpool' or 'entropic_barycenter'")
    prior = _simplex(alpha, len(models))
    pool, pieces = _pilot_pool(models, seed, settings)
    if not len(pool):
        raise ValueError("synthetic candidate pool is empty")
    feature = _features(pool, query_transform)
    target = np.asarray(target_summary, float).reshape(-1)
    if feature.shape[1] != len(target) or np.any(~np.isfinite(target)):
        raise ValueError("target_summary must be finite and match query feature dimension")
    loss_kind = settings.get("query_loss", "l2")
    ridge = float(settings.get("ridge", 1e-3))
    details = {"operator": name, "candidate_count": len(pool), "pilot_per_model": len(pieces[0]),
               "support_is_synthetic_only": True, "finite_pool_restricted": True,
               "query_loss": loss_kind, "prior_weights": prior.tolist()}
    if name == "logpool":
        logscore, smoothed = _model_log_matrix(models, pool, settings)
        details.update({"logscore_smoothed_count": smoothed, "logscore_floor": float(settings.get("logscore_floor", -60.0)),
                        "interpretation": "normalized geometric pool restricted to finite synthetic candidates"})
        def distribution(w):
            z = logscore @ w
            return np.exp(z - logsumexp(z))
        def objective(w):
            q = distribution(w)
            return _loss(q, feature, target, loss_kind) + ridge * float(np.sum((w-prior)**2))
        res = minimize(objective, prior, method="SLSQP", bounds=[(0, 1)]*len(models),
                       constraints=[{"type":"eq", "fun":lambda w:w.sum()-1}],
                       options={"maxiter":int(settings.get("maxiter",500)), "ftol":1e-11})
        w = _simplex(res.x if res.x is not None else prior, len(models))
        probs = distribution(w)
        details.update({"optimizer_success": bool(res.success), "optimizer_message": str(res.message),
                        "query_loss_value": _loss(probs,feature,target,loss_kind), "ridge":ridge})
    else:
        cost = _mixed_cost(pool, settings)
        lookup = {_key(row):i for i,row in enumerate(pool.itertuples(index=False,name=None))}
        smooth = float(settings.get("histogram_smoothing", 1e-6))
        hist = np.full((len(models),len(pool)), smooth)
        for j, sample in enumerate(pieces):
            for row in sample.itertuples(index=False,name=None):
                key=_key(row)
                if key in lookup: hist[j,lookup[key]] += 1
                else:
                    d = _row_to_pool_cost(row, pool, settings)
                    hist[j,int(np.argmin(d))] += 1
        hist /= hist.sum(axis=1,keepdims=True)
        candidates = [prior, np.full(len(models),1/len(models))]
        for _ in range(max(0,int(settings.get("weight_candidate_draws",0)))):
            candidates.append(np.random.default_rng(seed+_+1).dirichlet(np.maximum(prior*len(models),.05)))
        reg=float(settings.get("regularization",.05))
        iterations=int(settings.get("iterations",500)); tol=float(settings.get("tolerance",1e-9))
        fitted=[]
        for w0 in candidates:
            q,it,err,converged=_sinkhorn_barycenter(hist,cost,w0,reg,iterations,tol)
            fitted.append(( _loss(q,feature,target,loss_kind)+ridge*float(np.sum((w0-prior)**2)), w0, q,it,err,converged))
        _,w,probs,it,err,converged=min(fitted,key=lambda x:x[0])
        details.update({"regularization":reg,"iterations":it,"marginal_error":err,"converged":converged,
                        "weight_candidate_count":len(candidates),
                        "interpretation":"finite-support entropic transport barycenter (regularized W2 analogue); not unregularized W2"})
    details["weights"] = w.tolist()
    details["normalization_error"] = float(abs(probs.sum()-1))
    details["posterior_bandwidth"] = float(settings.get("posterior_bandwidth",1.0))
    details["posterior_kind"] = "kernel_smoothed_approximation"
    op = FinitePoolOperator(pool, probs, w, details, query_transform)
    op._pool_features = feature
    op._logscore = logscore if name == "logpool" else None
    op._hist = hist if name != "logpool" else None
    op._cost = cost if name != "logpool" else None
    op._settings = settings
    op._target_summary = target
    op._weight_candidates = [x[1].copy() for x in fitted] if name != "logpool" else None
    return op


def refit_operator_weights(operator: FinitePoolOperator, target_summary, seed=0, settings=None):
    """Refit weights to a new real calibration summary on the *same* pool.

    No generators are called and no rows are added. Logpool uses multistart
    SLSQP with an epigraph for query L-infinity error. Barycenter reports the
    best among previously saved and newly drawn simplex candidates; this is
    candidate search, not a global optimum claim.
    """
    settings = dict(settings or {})
    if not isinstance(operator, FinitePoolOperator) or not hasattr(operator, "_pool_features"):
        raise TypeError("operator must be the result of fit_operator")
    feature = operator._pool_features
    target = np.asarray(target_summary, float).reshape(-1)
    if target.shape != (feature.shape[1],) or np.any(~np.isfinite(target)):
        raise ValueError("target_summary must be finite and match the saved query feature dimension")
    prior = np.asarray(operator.details["prior_weights"], float)
    ridge = float(settings.get("ridge", operator._settings.get("ridge", 1e-3)))
    details = dict(operator.details)
    details.update({"refit_on_same_pool": True, "validation_target_used": True})
    name = operator.details["operator"]
    if name == "logpool":
        logscore = operator._logscore
        kind = settings.get("query_loss", "linf")
        if kind != "linf":
            kind = "linf"
        def distribution(w):
            z = logscore @ w
            return np.exp(z-logsumexp(z))
        starts = [prior, np.full(len(prior),1/len(prior))]
        starts.extend(np.eye(len(prior)))
        attempts = []
        for start in starts:
            q0 = distribution(start)
            t0 = float(np.max(np.abs(q0 @ feature-target)))
            x0 = np.r_[start,t0]
            def objective(x):
                return x[-1] + ridge*float(np.sum((x[:-1]-prior)**2))
            def epigraph(x):
                delta=x[-1]-(distribution(x[:-1]) @ feature-target)
                return np.r_[delta, x[-1]+(distribution(x[:-1]) @ feature-target)]
            res=minimize(objective,x0,method="SLSQP",bounds=[(0,1)]*len(prior)+[(0,None)],
                         constraints=[{"type":"eq","fun":lambda x:x[:-1].sum()-1},
                                      {"type":"ineq","fun":epigraph}],
                         options={"maxiter":int(settings.get("maxiter",500)),"ftol":1e-11})
            w=_simplex(res.x[:-1] if res.x is not None else start,len(prior))
            q=distribution(w)
            loss=_loss(q,feature,target,"linf")
            attempts.append({"success":bool(res.success),"message":str(res.message),"weights":w.tolist(),"query_loss":loss})
        successful=[a for a in attempts if a["success"]]
        chosen=min(successful or attempts,key=lambda a:a["query_loss"]+ridge*np.sum((np.asarray(a["weights"])-prior)**2))
        w=np.asarray(chosen["weights"]); probs=distribution(w)
        details.update({"optimizer_success":bool(successful),"optimizer_message":chosen["message"],
                        "optimizer_method":"SLSQP_epigraph_multistart","query_loss":"linf",
                        "query_loss_value":chosen["query_loss"],"refit_attempts":attempts,
                        "refit_weight_selection":"best_successful_multistart" if successful else "best_found_failed_starts"})
    else:
        cost, hist = operator._cost, operator._hist
        reg=float(settings.get("regularization",operator._settings.get("regularization",.05)))
        iterations=int(settings.get("iterations",operator._settings.get("iterations",500)))
        tol=float(settings.get("tolerance",operator._settings.get("tolerance",1e-9)))
        candidates=[np.asarray(x,float) for x in (operator._weight_candidates or [prior])]
        count=max(0,int(settings.get("weight_candidate_draws",12)))
        for j in range(count):
            candidates.append(np.random.default_rng(seed+j).dirichlet(np.maximum(prior*len(prior),.05)))
        attempts=[]
        for w0 in candidates:
            q,it,err,converged=_sinkhorn_barycenter(hist,cost,w0,reg,iterations,tol)
            loss=_loss(q,feature,target,settings.get("query_loss","linf"))
            attempts.append({"weights":w0.tolist(),"query_loss":loss,"iterations":it,
                             "marginal_error":err,"converged":converged})
        chosen=min(attempts,key=lambda a:a["query_loss"]+ridge*np.sum((np.asarray(a["weights"])-prior)**2))
        w=np.asarray(chosen["weights"]); probs,_it,_err,converged=_sinkhorn_barycenter(hist,cost,w,reg,iterations,tol)
        details.update({"query_loss":settings.get("query_loss","linf"),"query_loss_value":chosen["query_loss"],
                        "regularization":reg,"iterations":_it,"marginal_error":_err,"converged":converged,
                        "weight_candidate_count":len(candidates),"weight_candidate_trials":attempts,
                        "weight_selection":"best_found_candidate_not_global_optimum"})
    details["weights"]=w.tolist()
    details["normalization_error"]=float(abs(probs.sum()-1))
    result=FinitePoolOperator(operator.support,probs,w,details,operator.query_transform)
    result._pool_features=operator._pool_features
    result._logscore=operator._logscore
    result._hist=operator._hist
    result._cost=operator._cost
    result._settings=operator._settings
    result._target_summary=target
    result._weight_candidates=operator._weight_candidates
    return result
