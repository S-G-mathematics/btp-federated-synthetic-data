"""Additional non-neural mixed-data generators.

Prototype KDE stores only aggregated numeric centroids and categorical
probabilities, never the training rows used to fit them. It is not DP and its
continuous score is approximate for rounded/clipped integer samples.
Latent class is an exact declared integer-bin mixture of product models.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.special import logsumexp
from sklearn.cluster import KMeans

from .models import _Base, _key


class PrototypeKDEMixed(_Base):
    def __init__(self, *args, centers, component_weights, bandwidth,
                 cat_probs, transform, component_counts, minimum_center_support,
                 kmeans_iterations, **kwargs):
        super().__init__(*args, **kwargs)
        self.centers = np.asarray(centers, dtype=float)
        self.component_weights = np.asarray(component_weights, dtype=float)
        self.bandwidth = np.asarray(bandwidth, dtype=float)
        self.cat_probs = cat_probs
        self.transform = transform
        self.component_counts = np.asarray(component_counts, dtype=int)
        self.minimum_center_support = int(minimum_center_support)
        self.kmeans_iterations = int(kmeans_iterations)

    def _inverse_numeric(self, z):
        x = np.asarray(z, dtype=float).copy()
        for j, c in enumerate(self.numeric):
            spec = self.transform[c]
            x[:, j] = x[:, j] * spec["scale"] + spec["mean"]
            if spec["log1p"]:
                x[:, j] = np.expm1(np.clip(x[:, j], -30, 30))
        return x

    def _forward_numeric(self, frame):
        raw = frame[self.numeric].apply(pd.to_numeric, errors="coerce").to_numpy(float)
        valid = np.isfinite(raw).all(axis=1)
        z = raw.copy()
        log_jacobian = np.zeros(len(frame))
        for j, c in enumerate(self.numeric):
            lo, hi = self.numeric_bounds[c]
            valid &= (raw[:, j] >= lo) & (raw[:, j] <= hi)
            spec = self.transform[c]
            x = np.where(np.isfinite(raw[:, j]), raw[:, j], self.numeric_medians[c])
            if spec["log1p"]:
                valid &= x >= 0
                x = np.maximum(x, 0)
                log_jacobian += np.log1p(x)
                x = np.log1p(x)
            z[:, j] = (x - spec["mean"]) / spec["scale"]
            log_jacobian += np.log(spec["scale"])
        return z, log_jacobian, valid

    def sample(self, n: int, seed: int) -> pd.DataFrame:
        rng = np.random.default_rng(seed)
        labels = rng.choice(len(self.component_weights), size=n, p=self.component_weights)
        z = self.centers[labels] + rng.normal(size=(n, len(self.numeric))) * self.bandwidth
        x = self._inverse_numeric(z)
        data = {}
        for j, c in enumerate(self.numeric):
            lo, hi = self.numeric_bounds[c]
            data[c] = np.rint(np.clip(x[:, j], lo, hi)).astype(np.int64)
        for c in self.categorical:
            ids = np.empty(n, dtype=int)
            for component in range(len(self.component_weights)):
                mask = labels == component
                if mask.any():
                    ids[mask] = rng.choice(len(self.categories[c]), size=int(mask.sum()),
                                           p=self.cat_probs[c][component])
            data[c] = np.asarray(self.categories[c], dtype=object)[ids]
        return pd.DataFrame(data, columns=self.columns)

    def log_prob(self, frame: pd.DataFrame) -> np.ndarray:
        z, log_jacobian, valid = self._forward_numeric(frame)
        cat_ids = {}
        for c in self.categorical:
            lookup = {v: i for i, v in enumerate(self.categories[c])}
            cat_ids[c] = np.array([lookup.get(_key(v), -1) for v in frame[c]], dtype=int)
            valid &= cat_ids[c] >= 0
        out = np.empty(len(frame), dtype=float)
        base = np.log(self.component_weights)
        normalizer = np.log(self.bandwidth).sum() + len(self.numeric) * np.log(2 * np.pi) / 2
        for start in range(0, len(frame), 1024):
            stop = min(start + 1024, len(frame))
            scaled = (z[start:stop, None, :] - self.centers[None, :, :]) / self.bandwidth
            terms = base[None, :] - .5 * np.sum(scaled * scaled, axis=2) - normalizer
            terms = terms - log_jacobian[start:stop, None]
            for c in self.categorical:
                terms += np.log(self.cat_probs[c][:, np.maximum(cat_ids[c][start:stop], 0)].T)
            out[start:stop] = logsumexp(terms, axis=1)
        out[~valid] = -np.inf
        return out


class LatentClassMixed(_Base):
    def __init__(self, *args, mixture_weights, component_probs, converged,
                 iterations, lower_bound, n_init, **kwargs):
        super().__init__(*args, **kwargs)
        self.mixture_weights = np.asarray(mixture_weights, dtype=float)
        self.component_probs = component_probs
        self.converged = bool(converged)
        self.iterations = int(iterations)
        self.lower_bound = float(lower_bound)
        self.n_init = int(n_init)

    def sample(self, n: int, seed: int) -> pd.DataFrame:
        rng = np.random.default_rng(seed)
        labels = rng.choice(len(self.mixture_weights), size=n, p=self.mixture_weights)
        encoded = {}
        for c in self.columns:
            ids = np.empty(n, dtype=int)
            for component in range(len(self.mixture_weights)):
                mask = labels == component
                if mask.any():
                    ids[mask] = rng.choice(self.component_probs[c].shape[1],
                                           size=int(mask.sum()),
                                           p=self.component_probs[c][component])
            encoded[c] = ids
        return self._frame(encoded, rng)

    def log_prob(self, frame: pd.DataFrame) -> np.ndarray:
        encoded = self._encode(frame)
        terms = np.broadcast_to(np.log(self.mixture_weights),
                                (len(frame), len(self.mixture_weights))).copy()
        for c in self.columns:
            terms += np.log(self.component_probs[c][:, np.maximum(encoded[c], 0)].T)
        out = logsumexp(terms, axis=1)
        for c in self.numeric:
            out += self._numeric_log_correction(c, encoded[c])
        out[~self._valid_rows(frame, encoded)] = -np.inf
        return out


def _fit_prototype_kde(frame, seed, settings, base, numeric, cats, encoded, medians, alpha):
    if not numeric:
        raise ValueError("prototype_kde requires numeric columns")
    if alpha <= 0:
        raise ValueError("prototype_kde alpha must be positive")
    min_support = int(settings.get("minimum_center_support", 10))
    if min_support < 2:
        raise ValueError("minimum_center_support must be at least 2")
    requested = int(settings.get("centers", 32))
    multiplier = float(settings.get("bandwidth_multiplier", 1.0))
    if requested < 1 or not np.isfinite(multiplier) or multiplier <= 0:
        raise ValueError("centers and bandwidth_multiplier must be positive")
    n = len(frame)
    min_support = min(min_support, n)
    center_count = min(requested, max(1, n // min_support))
    transform = {}
    x = frame[numeric].apply(pd.to_numeric, errors="coerce").fillna(pd.Series(medians)).to_numpy(float)
    log_columns = set(settings.get("log1p_columns", ("fnlwgt", "capital-gain", "capital-loss")))
    for j, c in enumerate(numeric):
        do_log = c in log_columns
        if do_log:
            if np.any(x[:, j] < 0):
                raise ValueError(f"{c} must be nonnegative for log1p transform")
            x[:, j] = np.log1p(x[:, j])
        mean = float(x[:, j].mean())
        scale = max(float(x[:, j].std()), 1e-12)
        transform[c] = {"log1p": do_log, "mean": mean, "scale": scale}
        x[:, j] = (x[:, j] - mean) / scale
    km = KMeans(n_clusters=center_count, n_init=int(settings.get("n_init", 2)),
                max_iter=int(settings.get("max_iter", 100)), random_state=seed).fit(x)
    initial_counts = np.bincount(km.labels_, minlength=center_count)
    kept = np.flatnonzero(initial_counts >= min_support)
    if not len(kept):
        kept = np.array([int(np.argmax(initial_counts))])
    dist = np.sum((x[:, None, :] - km.cluster_centers_[kept][None, :, :]) ** 2, axis=2)
    labels = dist.argmin(axis=1)
    counts = np.bincount(labels, minlength=len(kept))
    centers = np.vstack([x[labels == j].mean(axis=0) for j in range(len(kept))])
    residual = x - centers[labels]
    factor = n ** (-1 / (len(numeric) + 4))
    bandwidth = np.maximum(.06, residual.std(axis=0) * factor * multiplier)
    cat_probs = {}
    for c in cats:
        width = len(base["categories"][c])
        probs = np.empty((len(kept), width))
        for j in range(len(kept)):
            hist = np.bincount(encoded[c][labels == j], minlength=width) + alpha
            probs[j] = hist / hist.sum()
        cat_probs[c] = probs
    obj = PrototypeKDEMixed(**{**base, "likelihood_kind": "approximate",
        "centers": centers, "component_weights": counts / n, "bandwidth": bandwidth,
        "cat_probs": cat_probs, "transform": transform, "component_counts": counts,
        "minimum_center_support": min_support, "kmeans_iterations": km.n_iter_})
    obj.numeric_medians = medians
    return obj


def _fit_latent_class(frame, seed, settings, base, encoded, widths, medians, alpha):
    if alpha <= 0:
        raise ValueError("latent_class alpha must be positive")
    components = min(max(1, int(settings.get("components", 4))), len(frame))
    max_iter = int(settings.get("max_iter", 150))
    n_init = int(settings.get("n_init", 2))
    tolerance = float(settings.get("tol", 1e-4))
    if max_iter < 1 or n_init < 1 or tolerance <= 0:
        raise ValueError("max_iter, n_init and tol must be positive")
    n = len(frame)
    rng = np.random.default_rng(seed)
    best = None
    for _ in range(n_init):
        seeds = rng.choice(n, size=components, replace=False)
        probs = {}
        for c in base["columns"]:
            global_p = (np.bincount(encoded[c], minlength=widths[c]) + alpha)
            global_p = global_p / global_p.sum()
            probs[c] = np.empty((components, widths[c]))
            for j in range(components):
                row_p = np.zeros(widths[c]); row_p[encoded[c][seeds[j]]] = 1
                probs[c][j] = .5 * global_p + .5 * row_p
        mix = np.ones(components) / components
        previous = -np.inf
        converged = False
        for iteration in range(1, max_iter + 1):
            terms = np.broadcast_to(np.log(mix), (n, components)).copy()
            for c in base["columns"]:
                terms += np.log(probs[c][:, encoded[c]].T)
            norm = logsumexp(terms, axis=1)
            lower_bound = float(norm.mean())
            if iteration > 1 and abs(lower_bound - previous) < tolerance:
                converged = True
                break
            previous = lower_bound
            responsibilities = np.exp(terms - norm[:, None])
            totals = responsibilities.sum(axis=0)
            mix = (totals + 1e-8) / (n + components * 1e-8)
            for c in base["columns"]:
                for j in range(components):
                    hist = np.bincount(encoded[c], weights=responsibilities[:, j],
                                       minlength=widths[c]) + alpha
                    probs[c][j] = hist / hist.sum()
        candidate = (lower_bound, mix.copy(),
                     {c: p.copy() for c, p in probs.items()}, converged, iteration)
        if best is None or candidate[0] > best[0]:
            best = candidate
    lower_bound, mix, probs, converged, iteration = best
    obj = LatentClassMixed(**{**base, "mixture_weights": mix,
        "component_probs": probs, "converged": converged,
        "iterations": iteration, "lower_bound": lower_bound, "n_init": n_init})
    obj.numeric_medians = medians
    return obj


def fit_extra_model(name, frame, seed, settings, base, numeric, cats,
                    encoded, widths, medians, alpha):
    if name in ("prototype_kde", "kde"):
        return _fit_prototype_kde(frame, seed, settings, base, numeric, cats,
                                  encoded, medians, alpha)
    if name in ("latent_class", "mixture_independent"):
        return _fit_latent_class(frame, seed, settings, base, encoded,
                                 widths, medians, alpha)
    raise ValueError(f"unknown extra model {name}")
