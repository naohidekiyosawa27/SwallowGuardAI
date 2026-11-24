"""Common-trigger affine alignment without interpolation over dropouts."""
import numpy as np


def fit_clock(sensor_trigger_us, reference_trigger_us):
    s, r = np.asarray(sensor_trigger_us, float), np.asarray(reference_trigger_us, float)
    if s.ndim != 1 or s.shape != r.shape or len(s) < 3:
        raise ValueError("At least three paired triggers required")
    if not np.isfinite(s).all() or not np.isfinite(r).all() or min(np.diff(s)) <= 0 or min(np.diff(r)) <= 0:
        raise ValueError("Invalid trigger times")
    slope = float(np.dot(s-s.mean(), r-r.mean()) / np.dot(s-s.mean(), s-s.mean()))
    offset = float(r.mean() - slope*s.mean())
    residual = r - (slope*s+offset)
    return {"slope": slope, "offset_us": offset,
            "skew_ppm": (slope-1)*1e6, "max_residual_us": float(np.max(np.abs(residual)))}


def align_timestamps(t_us, clock, *, measured_filter_delay_us=0):
    t = np.asarray(t_us, dtype=float)
    if t.ndim != 1 or len(t) < 2 or not np.isfinite(t).all() or np.any(np.diff(t) <= 0):
        raise ValueError("Invalid timestamps")
    if not np.isfinite([clock['slope'], clock['offset_us'], measured_filter_delay_us]).all() or clock['slope'] <= 0:
        raise ValueError("Invalid clock calibration")
    return clock['slope']*t + clock['offset_us'] - measured_filter_delay_us


def frame_to_sample(frame, *, fs=4000, fps=60, frame_origin, sample_origin=0):
    """Origin is mandatory until HRCA zero/one indexing is independently verified."""
    if frame_origin not in (0, 1) or sample_origin not in (0, 1):
        raise ValueError("Invalid indexing origin")
    if not np.isfinite([frame, fs, fps]).all() or frame < frame_origin or min(fs, fps) <= 0:
        raise ValueError("Invalid frame or rates")
    return int(np.floor((frame-frame_origin)*fs/fps+0.5))+sample_origin
