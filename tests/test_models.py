import numpy as np
import pandas as pd
import pytest
import os
import subprocess
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from btp.models import fit_model


@pytest.fixture
def adult_frame():
    rng = np.random.default_rng(7)
    n = 160
    age = rng.integers(18, 70, n)
    return pd.DataFrame({
        "age": age,
        "fnlwgt": rng.integers(10000, 250000, n),
        "education-num": rng.integers(1, 17, n),
        "capital-gain": np.where(age > 40, rng.choice([0, 0, 500, 1000], n), 0),
        "capital-loss": rng.choice([0, 0, 0, 200, 500], n),
        "hours-per-week": rng.integers(20, 61, n),
        "workclass": rng.choice(["Private", "State", "Self"], n),
        "income": np.where(age + rng.integers(-25, 25, n) > 50, ">50K", "<=50K"),
    })


@pytest.mark.parametrize("name,kind", [
    ("independent", "exact_discretized"),
    ("chow_liu", "exact_discretized"),
    ("copula", "approximate"),
    ("mixed_gmm", "approximate"),
    ("prototype_kde", "approximate"),
    ("latent_class", "exact_discretized"),
])
def test_models_sample_and_score(adult_frame, name, kind):
    model = fit_model(name, adult_frame, seed=13, settings={"bins": 8, "components": 3})
    draws = model.sample(40, seed=29)
    assert list(draws.columns) == list(adult_frame.columns)
    assert len(draws) == 40
    assert all(pd.api.types.is_integer_dtype(draws[c]) for c in adult_frame.columns[:6])
    assert set(draws.income).issubset(set(adult_frame.income))
    scores = model.log_prob(adult_frame.iloc[:12])
    assert scores.shape == (12,)
    assert np.isfinite(scores).all()
    assert model.likelihood_kind == kind
    assert draws.equals(model.sample(40, seed=29))


def test_independent_histogram_has_train_only_finite_support(adult_frame):
    model = fit_model("independent", adult_frame, seed=1, settings={"bins": 5})
    altered = adult_frame.iloc[:2].copy()
    altered["age"] = [100000, -100000]
    scores = model.log_prob(altered)
    assert np.isneginf(scores).all()
    draws = model.sample(500, seed=10)
    assert draws.age.min() >= adult_frame.age.min() - 1
    assert draws.age.max() <= adult_frame.age.max() + 1


def test_unknown_categories_have_zero_probability(adult_frame):
    model = fit_model("chow_liu", adult_frame, seed=1)
    row = adult_frame.iloc[:1].copy()
    row["workclass"] = "not-seen-at-fit"
    assert np.isneginf(model.log_prob(row)).all()


def test_chow_liu_sampling_seed_is_independent_of_process_hash_seed():
    root = Path(__file__).resolve().parents[1]
    script = (
        "import hashlib, numpy as np, pandas as pd; "
        "from btp.models import fit_model; "
        "n=80; d=pd.DataFrame({"
        "'age':np.arange(n)%5,'workclass':np.where(np.arange(n)%2,'A','B'),"
        "'education':np.where(np.arange(n)%3,'C','D'),"
        "'race':np.where(np.arange(n)%4,'E','F'),"
        "'sex':np.where(np.arange(n)%5,'G','H'),"
        "'income':np.where(np.arange(n)%7,'<=50K','>50K')}); "
        "m=fit_model('chow_liu',d,13,{'bins':3}); "
        "print(hashlib.sha256(m.sample(100,29).to_csv(index=False).encode()).hexdigest())"
    )
    outputs = []
    for hash_seed in ("1", "777"):
        result = subprocess.run(
            [sys.executable, "-c", script], cwd=root, check=True,
            capture_output=True, text=True,
            env={**os.environ, "PYTHONHASHSEED": hash_seed,
                 "OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1"},
        )
        outputs.append(result.stdout.strip())
    assert outputs[0] == outputs[1]


@pytest.mark.parametrize("name", ["independent", "chow_liu", "latent_class"])
def test_exact_models_normalize_over_toy_integer_support(name):
    train = pd.DataFrame({"age": [0, 0, 1, 2, 2], "label": ["a", "b", "a", "b", "b"]})
    model = fit_model(name, train, seed=3, settings={"bins": 2, "numeric_bounds": {"age": [0, 2]}, "category_vocab": {"label": ["a", "b"]}})
    support = pd.DataFrame([(v, c) for v in range(3) for c in ("a", "b")], columns=train.columns)
    assert np.isclose(np.exp(model.log_prob(support)).sum(), 1.0)
    invalid = support.iloc[:1].copy()
    invalid["label"] = "c"
    assert np.isneginf(model.log_prob(invalid)[0])


def test_constant_and_tiny_numeric_domains_have_no_empty_bins():
    train = pd.DataFrame({"age": [7, 7, 7], "income": ["<=50K", ">50K", ">50K"]})
    model = fit_model("independent", train, seed=1, settings={"bins": 12, "numeric_bounds": {"age": [7, 7]}, "category_vocab": {"income": ["<=50K", ">50K"]}})
    assert model.sample(25, 5).age.eq(7).all()
    support = pd.DataFrame({"age": [7, 7], "income": ["<=50K", ">50K"]})
    assert np.isclose(np.exp(model.log_prob(support)).sum(), 1.0)


def test_mixed_gmm_standardized_reinitialization_and_numeric_bounds(adult_frame):
    settings = {"components": 2, "n_init": 2, "reg_covar": 1e-4}
    first = fit_model("mixed_gmm", adult_frame, seed=23, settings=settings)
    second = fit_model("mixed_gmm", adult_frame, seed=23, settings=settings)
    assert first.gmm.n_init == 2
    assert first.transform["fnlwgt"]["log1p"]
    assert first.transform["capital-gain"]["log1p"]
    assert np.allclose(first.gmm.means_, second.gmm.means_)
    assert first.sample(30, 9).equals(second.sample(30, 9))
    draws = first.sample(200, 12)
    for c in adult_frame.columns[:6]:
        assert draws[c].between(adult_frame[c].min(), adult_frame[c].max()).all()
    assert np.isfinite(first.log_prob(adult_frame.iloc[:10])).all()


def test_prototype_kde_releases_aggregated_centers_only(adult_frame):
    model = fit_model("prototype_kde", adult_frame, seed=11,
                      settings={"centers": 12, "minimum_center_support": 8,
                                "bandwidth_multiplier": 1.0})
    assert len(model.centers) <= 12
    assert len(model.centers) < len(adult_frame)
    assert model.component_counts.min() >= 8
    assert model.component_counts.sum() == len(adult_frame)
    assert model.centers.shape[1] == 6
    assert not any(isinstance(v, pd.DataFrame) for v in vars(model).values())
    draws = model.sample(200, seed=4)
    assert draws.income.isin(["<=50K", ">50K"]).all()
    assert np.isfinite(model.log_prob(draws.iloc[:20])).all()


def test_latent_class_records_convergence_and_normalized_components(adult_frame):
    model = fit_model("latent_class", adult_frame, seed=7,
                      settings={"bins": 8, "components": 3, "max_iter": 200,
                                "n_init": 2, "tol": 1e-4})
    assert model.iterations <= 200
    assert np.isfinite(model.lower_bound)
    assert model.mixture_weights.sum() == pytest.approx(1.)
    for probabilities in model.component_probs.values():
        np.testing.assert_allclose(probabilities.sum(axis=1), 1., atol=1e-10)
