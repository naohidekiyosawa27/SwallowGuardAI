"""Strict D2 CSV adapter from documented six-column schema; real file pending."""
from pathlib import Path
import re
import numpy as np
from swallowguard.contracts import Recording, Source

CHANNELS = ("submental_emg", "intercostal_emg", "diaphragm_emg", "pressure", "contact_microphone")


def load_csv(path, *, source, all_channels_sample_rate_hz, channel_rate_verified):
    # Only EMG 2 kHz is explicitly established; other channels must be inspected.
    if not channel_rate_verified:
        raise ValueError("Verify time base of every selected channel before import")
    path = Path(path)
    match = re.fullmatch(r"P(\d+)_S(\d+)", path.parent.name)
    if not match:
        raise ValueError("Expected P<subject>_S<session> parent; never guess IDs")
    x = np.loadtxt(path, delimiter=",", ndmin=2)
    if x.shape[1] != 6 or not np.isfinite(x).all():
        raise ValueError("Expected six finite columns; header handling requires schema review")
    labels = x[:, 5]
    if not np.isin(labels, [0, 1, 2, 3, 4]).all():
        raise ValueError("Unknown D2 annotation")
    r = Recording("D2", f"P{match[1]}", path.parent.name, path.stem, Source(source),
                  all_channels_sample_rate_hz, np.arange(len(x))*1e6/all_channels_sample_rate_hz,
                  x[:, :5], CHANNELS)
    r.validate()
    return r, labels.astype(np.int8)
