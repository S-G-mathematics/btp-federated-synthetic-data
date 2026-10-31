import itertools

import numpy as np
import pandas as pd
import pytest

from btp.models import fit_model
from btp.projection import EducationNumberProjection
from btp.privacy import PUBLIC_EDUCATION_NUMBER_MAP, public_schema


@pytest.mark.parametrize("name", ["independent", "chow_liu", "latent_class"])
def test_projected_exact_integer_mass_normalizes_and_matches_sampling(name):
    train = pd.DataFrame({
        "education": ["A", "A", "B", "B", "?", "?", "A", "B"],
        "education-num": [0, 2, 1, 2, 0, 1, 2, 0],
        "income": ["a", "b", "a", "b", "a", "b", "b", "a"],
    })
    settings = {"bins": 2, "components": 2, "numeric_bounds": {"education-num": [0, 2]},
                "category_vocab": {"education": ["A", "B", "?"], "income": ["a", "b"]}}
    raw = fit_model(name, train, seed=4, settings=settings)
    model = EducationNumberProjection(raw, {"A": 1, "B": 2}, (0, 2))
    support = pd.DataFrame(itertools.product(["A", "B", "?"], range(3), ["a", "b"]),
                           columns=train.columns)
    mass = np.exp(model.log_prob(support))
    assert mass.sum() == pytest.approx(1.0, abs=1e-10)
    assert mass[(support.education == "A") & (support["education-num"] != 1)].sum() == 0
    assert mass[(support.education == "B") & (support["education-num"] != 2)].sum() == 0
    off_map = pd.DataFrame({"education": ["A", "B"],
                            "education-num": [2, 1], "income": ["a", "b"]})
    assert np.isneginf(model.log_prob(off_map)).all()
    unknown = support.loc[support.education == "?"].copy()
    np.testing.assert_allclose(model.log_prob(unknown), raw.log_prob(unknown))
    draws = model.sample(10000, 17)
    assert (draws.loc[draws.education == "A", "education-num"] == 1).all()
    assert (draws.loc[draws.education == "B", "education-num"] == 2).all()
    target = support.assign(mass=mass).groupby("education").mass.sum()
    empirical = draws.education.value_counts(normalize=True)
    for category in target.index:
        assert empirical[category] == pytest.approx(target[category], abs=.025)
    assert draws.equals(model.sample(10000, 17))


def test_public_mapping_is_explicit_and_unknown_stays_unmapped():
    schema = public_schema()
    assert schema["education_number_map"] == PUBLIC_EDUCATION_NUMBER_MAP
    assert "?" not in schema["education_number_map"]
