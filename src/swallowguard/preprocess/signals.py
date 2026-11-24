"""Causal, reproducible DSP primitives. Thresholds are bench assumptions."""
from fractions import Fraction
import numpy as np
from scipy import signal


def finite_matrix(x):
    x = np.asarray(x, dtype=np.float64)
    if x.ndim != 2 or len(x) < 2 or not np.isfinite(x).all():
        raise ValueError("Require finite samples x channels; no missing-data filling")
    return x


def bandpass(x, fs, low, high, order=4):
    x = finite_matrix(x)
    if not np.isfinite(fs) or not 0 < low < high < fs / 2:
        raise ValueError("Cutoffs must lie below Nyquist")
    sos = signal.butter(order, [low, high], fs=fs, btype="bandpass", output="sos")
    # Production streaming must preserve zi between chunks; this resets per recording.
    return signal.sosfilt(sos, x, axis=0)


def resample(x, fs_in, fs_out):
    x = finite_matrix(x)
    if not np.isfinite([fs_in, fs_out]).all() or min(fs_in, fs_out) <= 0:
        raise ValueError("Invalid sample rates")
    ratio = Fraction(str(fs_out)) / Fraction(str(fs_in))
    ratio = ratio.limit_denominator(10000)
    # polyphase FIR includes antialias filtering; preserve and measure group delay
    # separately for the eventual causal embedded implementation.
    return signal.resample_poly(x, ratio.numerator, ratio.denominator, axis=0)


def emg_envelope(x, fs=2000, output_fs=200):
    y = np.abs(bandpass(x, fs, 20, 450))
    sos = signal.butter(4, 10, fs=fs, output="sos")
    return resample(signal.sosfilt(sos, y, axis=0), fs, output_fs)


def optical_features(delta_counts, fs, um_per_count):
    x = finite_matrix(delta_counts)
    if x.shape[1] != 2 or not np.isfinite([fs, um_per_count]).all() or min(fs, um_per_count) <= 0:
        raise ValueError("Two calibrated optical channels required")
    displacement_mm = np.cumsum(x * um_per_count / 1000, axis=0)
    displacement_mm -= displacement_mm[0]
    velocity_mm_s = x * um_per_count / 1000 * fs
    return np.column_stack((displacement_mm, velocity_mm_s))


class TrainStandardizer:
    """Fit once on training data only; persist mean/scale with model artifact."""
    def fit(self, x, *, partition):
        if partition != "train":
            raise ValueError("Normalization fit is restricted to training partition")
        x = finite_matrix(x)
        self.mean = x.mean(axis=0)
        self.scale = np.maximum(x.std(axis=0), 1e-8)
        return self

    def transform(self, x):
        if not hasattr(self, "mean"):
            raise ValueError("Normalizer not fitted")
        return (finite_matrix(x) - self.mean) / self.scale


def window_features(x):
    x = finite_matrix(x)
    return np.concatenate((x.mean(0), x.std(0), np.sqrt(np.mean(x*x, axis=0)),
                           np.ptp(x, axis=0), np.mean(np.abs(np.diff(x, axis=0)), axis=0)))
