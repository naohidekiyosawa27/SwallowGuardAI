"""Group assignment is performed before segmentation and persisted."""
import numpy as np


def subject_split(subjects, *, seed=2026, fractions=(0.7, 0.15, 0.15)):
    groups = np.asarray(sorted(set(subjects)))
    if len(groups) < 6 or any(not str(g).strip() for g in groups):
        raise ValueError("Require >=6 identified subjects; otherwise use grouped CV")
    if len(fractions) != 3 or any(f <= 0 for f in fractions) or not np.isclose(sum(fractions), 1):
        raise ValueError("Invalid split fractions")
    groups = np.random.default_rng(seed).permutation(groups)
    ntest = max(1, int(round(len(groups)*fractions[2])))
    nval = max(1, int(round(len(groups)*fractions[1])))
    if ntest+nval >= len(groups):
        raise ValueError("No training subjects")
    result = {"train": groups[:len(groups)-nval-ntest].tolist(),
              "validation": groups[len(groups)-nval-ntest:len(groups)-ntest].tolist(),
              "test": groups[len(groups)-ntest:].tolist()}
    assert_disjoint(result)
    return result


def assert_disjoint(split):
    sets = [set(split[k]) for k in ("train", "validation", "test")]
    if any(not s for s in sets) or any(sets[i] & sets[j] for i in range(3) for j in range(i)):
        raise ValueError("Empty partition or subject leakage")
