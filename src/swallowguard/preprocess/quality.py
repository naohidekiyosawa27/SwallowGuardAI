"""Reject bad measurements before DSP/inference; no clinical thresholds."""
from dataclasses import dataclass
import numpy as np


@dataclass(frozen=True)
class QualityLimits:
    full_scale: float
    max_gap_periods: float = 1.5
    max_rate_error_fraction: float = 0.02
    min_std: float = 1e-9


def assess(t_us, x, fs, limits: QualityLimits, *, tracking_ok=True,
           sensor_attached=True, motion_ok=True, sequence=None):
    t, x = np.asarray(t_us, float), np.asarray(x, float)
    reasons = []
    if not np.isfinite([fs, limits.full_scale]).all() or min(fs, limits.full_scale) <= 0:
        raise ValueError("Invalid quality configuration")
    if t.ndim != 1 or x.ndim != 2 or len(t) < 2 or len(t) != len(x):
        return {"valid": False, "reasons": ["shape_or_empty"]}
    if not np.isfinite(t).all() or not np.isfinite(x).all():
        reasons.append("nonfinite")
    else:
        dt = np.diff(t)
        if np.any(dt <= 0):
            reasons.append("nonmonotonic")
        if np.any(dt > limits.max_gap_periods*1e6/fs):
            reasons.append("gap")
        if abs(np.median(dt)-1e6/fs)/(1e6/fs) > limits.max_rate_error_fraction:
            reasons.append("rate_error")
        if np.any(np.abs(x) >= limits.full_scale):
            reasons.append("clipping")
        if np.any(np.std(x, axis=0) <= limits.min_std):
            reasons.append("flatline")
    if sequence is not None:
        seq = np.asarray(sequence)
        if seq.shape != t.shape or np.any(np.diff(seq.astype(np.int64)) != 1):
            reasons.append("sequence_gap")
    for ok, reason in [(tracking_ok,"tracking_loss"), (sensor_attached,"detached"), (motion_ok,"motion")]:
        if not ok:
            reasons.append(reason)
    return {"valid": not reasons, "reasons": reasons}
