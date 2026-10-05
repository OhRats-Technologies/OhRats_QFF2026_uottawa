"""Chronological eligibility, train-only transforms and classification scores."""
import numpy as np
from sklearn.impute import SimpleImputer
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import average_precision_score, roc_auc_score, brier_score_loss


def split(frame, fold, train_window=(2010,2018)):
    start, end, val_start, val_end = fold
    if not train_window[0] <= start <= end < val_start <= val_end <= train_window[1] <= 2018:
        raise ValueError("Study folds must stay within the declared training window before sealed test")
    train = frame[frame.year.between(start, end)].copy()
    valid = frame[frame.year.between(val_start, val_end)].copy()
    if train.empty or valid.empty or set(train.incident_id) & set(valid.incident_id):
        raise ValueError("Empty fold or overlapping fire identities")
    return train, valid


def transform(train, valid, columns):
    preprocess = make_pipeline(SimpleImputer(strategy="median", keep_empty_features=True), StandardScaler())
    return preprocess.fit_transform(train[columns]), preprocess.transform(valid[columns])


def sample_indices(size, cap, seed):
    return np.sort(np.random.default_rng(seed).choice(size, min(size, cap), replace=False))


def scores(y, prediction, probability=True):
    result = dict(average_precision=float(average_precision_score(y, prediction)),
                  roc_auc=float(roc_auc_score(y, prediction)), prevalence=float(np.mean(y)), rows=len(y))
    if probability:
        result["brier"] = float(brier_score_loss(y, prediction))
    return result
