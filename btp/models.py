"""Lightweight mixed-data generators for the Adult table.

All fitted state is ordinary Python/numpy/sklearn state and is pickleable. The
public API is ``fit_model(name, frame, seed, settings=None)``; returned objects
implement ``sample(n, seed)`` and ``log_prob(frame)``. Numeric columns are the
six Adult measurements; every other column (including income) is categorical.

The independent and Chow--Liu models operate on train-fitted numeric bins and
have normalized exact_discretized likelihoods (numeric values are rounded to
integer bin representatives on sampling). The Gaussian copula uses a Gaussian
latent correlation with empirical marginals; categorical labels receive a
deterministic sorted order for latent threshold construction, so dependence
can reflect arbitrary nominal ordering. Its score is approximate, not an exact
categorical copula likelihood. The mixed GMM uses standardized inputs and
optional log1p transforms, but returns rounded/clipped numeric draws; its
transformed continuous density is evaluated before rounding, so it too is
approximate and is not a mass over the rounded output table.
"""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from scipy.special import logsumexp
from scipy.stats import norm, rankdata
from sklearn.mixture import GaussianMixture

NUMERIC_COLUMNS = ("age", "fnlwgt", "education-num", "capital-gain", "capital-loss", "hours-per-week")
UNKNOWN = "__UNKNOWN__"


def _is_numeric(col: str, frame: pd.DataFrame) -> bool:
    return col in NUMERIC_COLUMNS or pd.api.types.is_numeric_dtype(frame[col].dtype)


def _key(v: Any) -> str:
    if pd.isna(v):
        return UNKNOWN
    return str(v)


class _Base:
    def __init__(self, columns, numeric, categories, edges, likelihood_kind, numeric_bounds=None):
        self.columns = list(columns)
        self.numeric = list(numeric)
        self.categorical = [c for c in columns if c not in numeric]
        self.categories = categories
        self.edges = edges
        self.numeric_bounds = numeric_bounds or {}
        self.likelihood_kind = likelihood_kind

    def _encode(self, frame):
        out = {}
        for c in self.columns:
            if c in self.numeric:
                x = pd.to_numeric(frame[c], errors="coerce").fillna(self.numeric_medians[c]).to_numpy(float)
                idx = np.searchsorted(self.edges[c], x, side="right") - 1
                idx = np.where((x >= self.edges[c][0]) & (x <= self.edges[c][-1]), idx, -1)
                out[c] = np.where(np.isfinite(x), idx, -1).astype(int)
            else:
                lookup = {v: i for i, v in enumerate(self.categories[c])}
                out[c] = np.array([lookup.get(_key(v), -1) for v in frame[c]], dtype=int)
        return out

    def _decode_numeric(self, c, ids, rng):
        edges = self.edges[c]
        lo = edges[np.asarray(ids)]
        hi = edges[np.asarray(ids) + 1]
        # Choose integer representatives that remain in the selected bin,
        # keeping sampling consistent with the discretized likelihood.
        ilo, ihi = np.ceil(lo).astype(np.int64), (np.ceil(hi) - 1).astype(np.int64)
        return np.array([rng.integers(a, b + 1) for a, b in zip(ilo, ihi)], dtype=np.int64)

    def _numeric_log_correction(self, c, idx):
        left, right = self.edges[c][:-1], self.edges[c][1:]
        counts = np.ceil(right).astype(np.int64) - np.ceil(left).astype(np.int64)
        return -np.log(counts[np.maximum(idx, 0)])

    def _valid_rows(self, frame, enc):
        valid = np.ones(len(frame), dtype=bool)
        for c in self.columns:
            valid &= enc[c] >= 0
        return valid

    def _frame(self, encoded, rng):
        data = {}
        for c in self.columns:
            ids = np.asarray(encoded[c], dtype=int)
            data[c] = self._decode_numeric(c, ids, rng) if c in self.numeric else np.asarray(self.categories[c], dtype=object)[ids]
        return pd.DataFrame(data, columns=self.columns)


class IndependentMixed(_Base):
    def __init__(self, *args, probs, **kwargs):
        super().__init__(*args, **kwargs)
        self.probs = probs

    def sample(self, n: int, seed: int) -> pd.DataFrame:
        rng = np.random.default_rng(seed)
        return self._frame({c: rng.choice(len(p), size=n, p=p) for c, p in self.probs.items()}, rng)

    def log_prob(self, frame: pd.DataFrame) -> np.ndarray:
        enc = self._encode(frame)
        result = np.zeros(len(frame))
        for c, p in self.probs.items():
            idx = enc[c]
            result += np.log(p[np.maximum(idx, 0)])
            if c in self.numeric:
                result += self._numeric_log_correction(c, idx)
        result[~self._valid_rows(frame, enc)] = -np.inf
        return result


class ChowLiuMixed(_Base):
    def __init__(self, *args, root, parent, cpt, **kwargs):
        super().__init__(*args, **kwargs)
        self.root, self.parent, self.cpt = root, parent, cpt

    def _draw(self, n, rng):
        z = {}
        z[self.root] = rng.choice(self.cpt[self.root].shape[0], n, p=self.cpt[self.root])
        # Preserve declared schema order. Iterating a set here made a fixed
        # sample seed depend on the process's PYTHONHASHSEED.
        pending = [c for c in self.columns if c != self.root]
        while pending:
            ready = [c for c in pending if self.parent[c] in z]
            for c in ready:
                p = self.parent[c]
                mat = self.cpt[c]
                z[c] = np.array([rng.choice(mat.shape[1], p=mat[zp]) for zp in z[p]])
                pending.remove(c)
        return z

    def sample(self, n: int, seed: int) -> pd.DataFrame:
        rng = np.random.default_rng(seed)
        return self._frame(self._draw(n, rng), rng)

    def log_prob(self, frame: pd.DataFrame) -> np.ndarray:
        z = self._encode(frame)
        out = np.log(self.cpt[self.root][z[self.root]])
        for c in self.columns:
            if c == self.root:
                continue
            out += np.log(self.cpt[c][z[self.parent[c]], z[c]])
        out[~self._valid_rows(frame, z)] = -np.inf
        for c in self.numeric:
            out += self._numeric_log_correction(c, z[c])
        return out


class GaussianCopulaMixed(_Base):
    def __init__(self, *args, corr, ranks, marginal_probs, **kwargs):
        super().__init__(*args, **kwargs)
        self.corr, self.ranks, self.marginal_probs = corr, ranks, marginal_probs
        self._chol = np.linalg.cholesky(corr)
        self._inv = np.linalg.inv(corr)
        self._logdet = np.linalg.slogdet(corr)[1]

    def _to_latent(self, frame):
        cols = []
        for c in self.columns:
            x = pd.to_numeric(frame[c], errors="coerce").fillna(self.numeric_medians[c]).to_numpy(float) if c in self.numeric else np.array([_key(v) for v in frame[c]], object)
            vals = self.ranks[c]
            if c in self.numeric:
                q = np.interp(x, vals[0], vals[1], left=vals[1][0], right=vals[1][-1])
            else:
                q = np.array([vals[1].get(v, .5) for v in x])
            cols.append(norm.ppf(np.clip(q, 1e-5, 1 - 1e-5)))
        return np.column_stack(cols)

    def _sample_latent(self, n, rng):
        return rng.standard_normal((n, len(self.columns))) @ self._chol.T

    def _decode_latent(self, z, rng):
        data = {}
        for j, c in enumerate(self.columns):
            q = norm.cdf(z[:, j]); x, y = self.ranks[c]
            if c in self.numeric:
                data[c] = np.rint(np.interp(q, y, x, left=x[0], right=x[-1])).astype(np.int64)
                if c in self.numeric_bounds:
                    data[c] = np.clip(data[c], *self.numeric_bounds[c])
            else:
                cats = self.categories[c]
                probs = self.marginal_probs[c]
                cuts = np.cumsum(probs)
                data[c] = np.asarray(cats, object)[np.searchsorted(cuts, q, side="left").clip(0, len(cats)-1)]
        return pd.DataFrame(data, columns=self.columns)

    def sample(self, n, seed):
        rng = np.random.default_rng(seed)
        return self._decode_latent(self._sample_latent(n, rng), rng)

    def log_prob(self, frame):
        z = self._to_latent(frame)
        d = z.shape[1]
        # Gaussian-copula dependence contribution plus marginal empirical-bin
        # log masses / densities. This is a deliberately approximate score.
        dep = -.5 * (np.einsum('ij,jk,ik->i', z, self._inv - np.eye(d), z)) - .5 * self._logdet
        out = dep.copy()
        for j, c in enumerate(self.columns):
            q = norm.cdf(z[:, j]); x, marginal = self.ranks[c]
            if c in self.numeric:
                edges = self.edges[c]
                idx = np.clip(np.searchsorted(edges, pd.to_numeric(frame[c], errors="coerce").fillna(self.numeric_medians[c]).to_numpy(float), side="right")-1, 0, len(edges)-2)
                out += np.log(self.marginal_probs[c][idx]) - np.log(np.diff(edges)[idx])
            else:
                lookup = {v:i for i,v in enumerate(self.categories[c])}
                ids = np.array([lookup.get(_key(v), -1) for v in frame[c]])
                out += np.log(self.marginal_probs[c][np.maximum(ids, 0)])
                out[ids < 0] = -np.inf
        for c in self.numeric:
            lo, hi = self.numeric_bounds[c]
            x = pd.to_numeric(frame[c], errors="coerce").to_numpy(float)
            out[(x < lo) | (x > hi) | ~np.isfinite(x)] = -np.inf
        return out


class MixedGaussianMixture(_Base):
    def __init__(self, *args, gmm, cat_probs, transform, **kwargs):
        super().__init__(*args, **kwargs)
        self.gmm, self.cat_probs, self.transform = gmm, cat_probs, transform

    def _forward_numeric(self, x):
        z = np.asarray(x, dtype=float).copy()
        log_jacobian = np.zeros(len(z))
        for j, c in enumerate(self.numeric):
            spec = self.transform[c]
            if spec["log1p"]:
                if np.any(z[:, j] < 0):
                    raise ValueError(f"{c} must be nonnegative for log1p transform")
                log_jacobian += np.log1p(z[:, j])
                z[:, j] = np.log1p(z[:, j])
            z[:, j] = (z[:, j] - spec["mean"]) / spec["scale"]
            log_jacobian += np.log(spec["scale"])
        return z, log_jacobian

    def _inverse_numeric(self, z):
        x = np.asarray(z, dtype=float).copy()
        for j, c in enumerate(self.numeric):
            spec = self.transform[c]
            x[:, j] = x[:, j] * spec["scale"] + spec["mean"]
            if spec["log1p"]:
                x[:, j] = np.expm1(x[:, j])
        return x

    def sample(self, n, seed):
        rng = np.random.default_rng(seed)
        # Draw components and normals explicitly so the supplied seed controls
        # every part of the sample across sklearn versions.
        labels = rng.choice(self.gmm.n_components, size=n, p=self.gmm.weights_)
        z = np.empty((n, len(self.numeric)))
        for k in range(self.gmm.n_components):
            mask = labels == k
            if mask.any():
                z[mask] = rng.multivariate_normal(self.gmm.means_[k], self.gmm.covariances_[k], size=int(mask.sum()))
        x = self._inverse_numeric(z)
        data = {}
        for j, c in enumerate(self.numeric):
            data[c] = np.rint(x[:, j]).astype(np.int64)
            if c in self.numeric_bounds:
                data[c] = np.clip(data[c], *self.numeric_bounds[c])
        for c in self.categorical:
            vals = self.categories[c]
            data[c] = np.array([rng.choice(vals, p=self.cat_probs[c][k]) for k in labels], object)
        return pd.DataFrame(data, columns=self.columns)

    def log_prob(self, frame):
        raw_x = frame[self.numeric].apply(pd.to_numeric, errors="coerce").fillna(pd.Series(self.numeric_medians)).to_numpy(float)
        x, log_jacobian = self._forward_numeric(raw_x)
        weighted = self.gmm._estimate_weighted_log_prob(x) - log_jacobian[:, None]
        cat_terms = np.zeros_like(weighted)
        for c in self.categorical:
            lookup = {v: i for i, v in enumerate(self.categories[c])}
            ids = np.array([lookup.get(_key(v), -1) for v in frame[c]])
            ids = np.maximum(ids, 0)
            cat_terms += np.log(self.cat_probs[c][:, ids].T)
        score = logsumexp(weighted + cat_terms, axis=1)
        for c in self.categorical:
            vocab = set(self.categories[c])
            score[np.array([_key(v) not in vocab for v in frame[c]])] = -np.inf
        for c in self.numeric:
            lo, hi = self.numeric_bounds[c]
            values = pd.to_numeric(frame[c], errors="coerce").to_numpy(float)
            score[(values < lo) | (values > hi) | ~np.isfinite(values)] = -np.inf
        return score


def fit_model(name: str, frame: pd.DataFrame, seed: int, settings: dict | None = None):
    """Fit one model; names: independent, copula, chow_liu, mixed_gmm.

    Settings may include ``bins`` (default 12), ``alpha`` (default 1),
    ``components`` (default 4), ``max_iter`` (default 150),
    ``numeric_bounds`` mapping names to inclusive integer (min, max), and
    ``category_vocab`` mapping categorical names to public allowed labels.
    GMM settings include ``numeric_transform`` (default
    ``log1p_standardized``), ``log1p_columns``, ``n_init`` (default 2), and
    ``reg_covar`` (default 1e-4 in transformed standardized units).
    """
    settings = settings or {}
    if frame.empty or len(frame.columns) == 0:
        raise ValueError("frame must contain at least one row and one column")
    columns = list(frame.columns)
    numeric = [c for c in columns if _is_numeric(c, frame)]
    cats = [c for c in columns if c not in numeric]
    bins, alpha = max(2, int(settings.get("bins", 12))), float(settings.get("alpha", 1.0))
    numeric_bounds = {c: tuple(map(int, bound)) for c, bound in settings.get("numeric_bounds", {}).items() if c in numeric}
    category_vocab = settings.get("category_vocab", {})
    edges, medians, categories, encoded = {}, {}, {}, {}
    for c in numeric:
        vals = pd.to_numeric(frame[c], errors="coerce")
        medians[c] = float(vals.median()) if vals.notna().any() else 0.0
        vals = vals.fillna(medians[c]).to_numpy(float)
        if c in numeric_bounds:
            low, high = numeric_bounds[c]
            if low > high:
                raise ValueError(f"invalid numeric bounds for {c}: {numeric_bounds[c]}")
            if np.any(vals < low) or np.any(vals > high):
                raise ValueError(f"training values for {c} fall outside configured numeric_bounds")
        else:
            low, high = int(np.floor(vals.min())), int(np.ceil(vals.max()))
            numeric_bounds[c] = (low, high)
        # Integer half-boundaries guarantee every bin contains at least one
        # integer, even for constant columns and tiny configured domains.
        n_bins = min(bins, high - low + 1)
        cuts = np.unique(np.floor(np.quantile(vals, np.linspace(0, 1, n_bins + 1))[1:-1]).astype(int))
        cuts = cuts[(cuts >= low) & (cuts < high)]
        quant = np.r_[low - .5, cuts + .5, high + .5]
        edges[c] = quant
        encoded[c] = np.searchsorted(quant, vals, side="right") - 1
    for c in cats:
        observed = sorted({_key(v) for v in frame[c]})
        allowed = category_vocab.get(c)
        categories[c] = list(dict.fromkeys(_key(v) for v in allowed)) if allowed is not None else observed
        if not categories[c]:
            categories[c] = [UNKNOWN]
        invalid = set(observed) - set(categories[c])
        if invalid:
            raise ValueError(f"training categories for {c} are outside configured category_vocab: {sorted(invalid)}")
        lookup = {v:i for i,v in enumerate(categories[c])}
        encoded[c] = np.array([lookup[_key(v)] for v in frame[c]], int)
    base = dict(columns=columns, numeric=numeric, categories=categories, edges=edges, likelihood_kind="exact_discretized", numeric_bounds=numeric_bounds)
    common = _Base(**base)
    common.numeric_medians = medians
    k = {c: (len(edges[c])-1 if c in numeric else len(categories[c])) for c in columns}
    if name in ("independent", "independent_mixed"):
        probs = {c: (np.bincount(encoded[c], minlength=k[c]) + alpha) / (len(frame) + alpha*k[c]) for c in columns}
        obj = IndependentMixed(**{**base, "probs": probs}); obj.numeric_medians = medians; return obj
    if name in ("chow_liu", "chow-liu"):
        # Maximum-weight spanning tree over smoothed pairwise mutual information.
        mi = np.zeros((len(columns), len(columns)))
        pair = {}
        for i, a in enumerate(columns):
            for j in range(i):
                b = columns[j]
                tab = np.full((k[a], k[b]), alpha)
                np.add.at(tab, (encoded[a], encoded[b]), 1)
                pxy = tab / tab.sum(); pa, pb = pxy.sum(1), pxy.sum(0)
                value = np.sum(pxy * np.log(pxy / (pa[:,None]*pb[None,:])))
                mi[i,j] = mi[j,i] = value
                pair[(a,b)] = tab
        root = columns[0]; visited = {root}; parent = {root: None}; order = [root]
        while len(visited) < len(columns):
            edges_best = [(mi[columns.index(a), columns.index(b)], a, b) for a in visited for b in columns if b not in visited]
            _, a, b = max(edges_best); parent[b] = a; visited.add(b); order.append(b)
        cpt = {}
        counts = np.bincount(encoded[root], minlength=k[root]) + alpha
        cpt[root] = counts/counts.sum()
        for c in order[1:]:
            p = parent[c]
            if (p,c) in pair:
                tab = pair[(p,c)].copy()
            else:
                tab = pair[(c,p)].T.copy()
            cpt[c] = tab / tab.sum(axis=1, keepdims=True)
        obj = ChowLiuMixed(**{**base, "root":root, "parent":parent, "cpt":cpt}); obj.numeric_medians=medians; return obj
    if name in ("copula", "gaussian_copula"):
        ranks = {}; latent=[]
        for c in columns:
            if c in numeric:
                x = pd.to_numeric(frame[c], errors="coerce").fillna(medians[c]).to_numpy(float)
                sx = np.sort(x); q = (np.arange(len(sx)) + .5)/len(sx)
                ranks[c] = (sx, q)
                latent.append(norm.ppf(np.clip((rankdata(x, method="average")-.5)/len(x),1e-4,1-1e-4)))
            else:
                counts=np.bincount(encoded[c], minlength=k[c]); p=(counts+alpha)/(len(frame)+alpha*k[c])
                qmap={v:float(p[i]) for i,v in enumerate(categories[c])}
                # use midrank CDF locations for category values
                cumul=np.cumsum(p)-p/2
                qmap={v:float(cumul[i]) for i,v in enumerate(categories[c])}
                ranks[c]=(np.array([]),qmap)
                latent.append(np.array([norm.ppf(np.clip(cumul[i],1e-4,1-1e-4)) for i in encoded[c]]))
        corr=np.corrcoef(np.column_stack(latent), rowvar=False)
        corr=np.atleast_2d(corr); corr=np.nan_to_num(corr); corr=.98*corr+.02*np.eye(len(columns))
        # Project to a positive definite correlation matrix under collinearity.
        eigval, eigvec = np.linalg.eigh((corr + corr.T) / 2)
        corr = (eigvec * np.maximum(eigval, 1e-6)) @ eigvec.T
        scale = np.sqrt(np.diag(corr))
        corr = corr / np.outer(scale, scale)
        np.fill_diagonal(corr, 1.0)
        marginal_probs={c:(np.bincount(encoded[c], minlength=k[c])+alpha)/(len(frame)+alpha*k[c]) for c in columns}
        obj=GaussianCopulaMixed(**{**base,"likelihood_kind":"approximate","corr":corr,"ranks":ranks,"marginal_probs":marginal_probs}); obj.numeric_medians=medians; return obj
    if name in ("mixed_gmm", "gmm", "mixed_gaussian_mixture"):
        if not numeric: raise ValueError("mixed_gmm requires at least one numeric column")
        raw_x=frame[numeric].apply(pd.to_numeric, errors="coerce").fillna(pd.Series(medians)).to_numpy(float)
        transform_name = settings.get("numeric_transform", "log1p_standardized")
        if transform_name not in ("standardized", "log1p_standardized"):
            raise ValueError("numeric_transform must be 'standardized' or 'log1p_standardized'")
        log_columns = set(settings.get("log1p_columns", ("fnlwgt", "capital-gain", "capital-loss"))) if transform_name == "log1p_standardized" else set()
        transform = {}
        x = raw_x.copy()
        for j, c in enumerate(numeric):
            do_log = c in log_columns
            if do_log:
                if np.any(x[:, j] < 0):
                    raise ValueError(f"{c} must be nonnegative for log1p transform")
                x[:, j] = np.log1p(x[:, j])
            mean = float(np.mean(x[:, j]))
            scale = float(np.std(x[:, j]))
            if not np.isfinite(scale) or scale < 1e-12:
                scale = 1.0
            transform[c] = {"log1p":do_log, "mean":mean, "scale":scale}
            x[:, j] = (x[:, j] - mean) / scale
        comps=min(max(1,int(settings.get("components",4))),len(frame))
        gmm=GaussianMixture(n_components=comps, covariance_type="full",
                            reg_covar=float(settings.get("reg_covar",1e-4)),
                            n_init=int(settings.get("n_init",2)), random_state=seed,
                            max_iter=int(settings.get("max_iter",150))).fit(x)
        cat_probs={}
        for c in cats:
            cat_probs[c]=np.empty((comps,k[c]))
            for z in range(comps):
                w=gmm.predict_proba(x)[:,z]
                counts=np.bincount(encoded[c], weights=w, minlength=k[c])+alpha
                cat_probs[c][z]=counts/counts.sum()
        obj=MixedGaussianMixture(**{**base,"likelihood_kind":"approximate","gmm":gmm,"cat_probs":cat_probs,"transform":transform}); obj.numeric_medians=medians; return obj
    if name in ("prototype_kde", "kde", "latent_class", "mixture_independent"):
        from .models_extra import fit_extra_model
        return fit_extra_model(name, frame, seed, settings, base, numeric, cats,
                               encoded, k, medians, alpha)
    raise ValueError(f"unknown model {name!r}; choose independent, chow_liu, copula, mixed_gmm, prototype_kde, or latent_class")
