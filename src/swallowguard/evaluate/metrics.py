"""Window metrics with subject-cluster bootstrap; not clinical performance."""
import numpy as np
from sklearn.metrics import confusion_matrix, precision_recall_fscore_support


def binary_metrics(y, pred):
    y, pred = np.asarray(y), np.asarray(pred)
    if y.ndim != 1 or y.shape != pred.shape or not len(y) or not np.isin(y,[0,1]).all() or not np.isin(pred,[0,1]).all():
        raise ValueError("Require aligned non-empty binary labels")
    p, r, f, _ = precision_recall_fscore_support(y, pred, average="binary", zero_division=0)
    return {"precision": float(p), "recall": float(r), "f1": float(f),
            "confusion_matrix_true_rows_pred_columns": confusion_matrix(y,pred,labels=[0,1]).tolist(),
            "class_order": ["non_swallow_event", "swallow_event"]}


def cluster_f1_ci(y, pred, subjects, *, iterations=1000, seed=2026):
    y, pred, subjects = map(np.asarray, (y, pred, subjects))
    binary_metrics(y, pred)
    if y.shape != subjects.shape or iterations < 2:
        raise ValueError("Invalid cluster bootstrap input")
    groups = np.unique(subjects)
    if len(groups) < 2:
        return {"low": None, "high": None, "reason": "fewer_than_two_test_subjects"}
    rng = np.random.default_rng(seed)
    scores = []
    for _ in range(iterations):
        ids = np.concatenate([np.flatnonzero(subjects == g) for g in rng.choice(groups,len(groups),replace=True)])
        scores.append(binary_metrics(y[ids],pred[ids])["f1"])
    low, high = np.quantile(scores,[0.025,0.975])
    return {"low": float(low), "high": float(high), "method": "subject_cluster_percentile",
            "iterations": iterations, "seed": seed}
