import numpy as np

from btp.data import prepare_splits
from scripts.report_adult_confirmation_secondary import fit, predict, metrics


def test_frozen_utility_fit_uses_separate_development_roles(tmp_path):
    splits = prepare_splits(__import__('pathlib').Path(__file__).resolve().parents[1] / 'data/raw', 101)
    train = splits['train'].iloc[:1200]
    tune = splits['tune'].iloc[:400]
    calibration = splits['calibration'].iloc[:400]
    for learner in ('logistic', 'extra_trees'):
        base, platt, record = fit(learner, train, tune, calibration, 7)
        p = predict(base, platt, tune)
        assert np.isfinite(p).all()
        assert np.all((p > 0) & (p < 1))
        assert record['train_rows'] == len(train)
        assert metrics((tune.income == '>50K').astype(int).to_numpy(), p,
                       np.ones(len(tune))/len(tune))['brier'] >= 0
