"""Explicit acquisition provenance and fail-closed data contracts."""
from dataclasses import dataclass
from enum import Enum
import numpy as np


class Source(str, Enum):
    SYNTHETIC = "synthetic"
    REPLAY = "replayed_research"
    BENCH = "live_bench"


@dataclass(frozen=True)
class Recording:
    dataset_id: str
    subject_id: str
    session_id: str
    recording_id: str
    source: Source
    sample_rate_hz: float
    t_us: np.ndarray
    values: np.ndarray
    channels: tuple[str, ...]

    def validate(self):
        if not all((self.dataset_id, self.subject_id, self.session_id, self.recording_id)):
            raise ValueError("Dataset, subject, session and recording identifiers required")
        if not isinstance(self.source, Source):
            raise ValueError("Source must explicitly identify synthetic/replay/bench")
        if not np.isfinite(self.sample_rate_hz) or self.sample_rate_hz <= 0:
            raise ValueError("Invalid sample rate")
        if self.values.ndim != 2 or self.values.shape != (len(self.t_us), len(self.channels)):
            raise ValueError("Expected samples x channels")
        if len(self.t_us) < 2 or not np.isfinite(self.t_us).all() or np.any(np.diff(self.t_us) <= 0):
            raise ValueError("Non-finite, duplicate or non-monotonic timestamps")
        if not np.isfinite(self.values).all():
            raise ValueError("Missing/nonfinite samples: reject, never impute")


def require_paired(recordings):
    """Only one actual acquisition session may contribute to a fusion sample.

    Session identity is necessary but not sufficient: trigger-based alignment is
    separately required. Public datasets must retain their own synchronized channels.
    """
    for recording in recordings:
        recording.validate()
    keys = {(r.dataset_id, r.subject_id, r.session_id, r.recording_id, r.source)
            for r in recordings}
    if len(keys) != 1:
        raise ValueError("Unpaired recordings cannot form a multimodal sample")


def research_output(*, valid: bool, event_probability=None, model_stage="M0"):
    if model_stage not in {"M0", "M1"}:
        raise ValueError("Clinical M2 is disabled")
    if event_probability is not None and (
        not np.isfinite(event_probability) or not 0 <= event_probability <= 1
    ):
        raise ValueError("Invalid event probability")
    return {"mode": "RESEARCH MODE", "stage": model_stage,
            "status": "research_event" if valid else "invalid_measurement",
            "event_probability": event_probability if valid else None,
            "clinical_risk": None, "swallowing_safety_clearance": False,
            "treatment_recommendation": None}
