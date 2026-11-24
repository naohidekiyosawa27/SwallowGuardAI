"""Fixed windows; explicit overlap ambiguity policy for M0 sample labels."""
import numpy as np


def labeled_windows(x, labels, *, length, hop, positive=2, negative=(0, 3, 4), purity=0.9):
    x, labels = np.asarray(x), np.asarray(labels)
    if x.ndim != 2 or labels.shape != (len(x),) or not np.isfinite(x).all():
        raise ValueError("Invalid samples/labels")
    if min(length, hop) < 1 or not 0.5 < purity <= 1:
        raise ValueError("Invalid window configuration")
    # Preparation (D2 class 1) and mixed transitions remain unlabelled.
    for start in range(0, len(x)-length+1, hop):
        y = labels[start:start+length]
        if np.mean(y == positive) >= purity:
            yield start, x[start:start+length], 1
        elif np.mean(np.isin(y, negative)) >= purity:
            yield start, x[start:start+length], 0
