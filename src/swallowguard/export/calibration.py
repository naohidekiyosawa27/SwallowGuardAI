"""Training-only deterministic coverage for a single M0 waveform input."""
import numpy as np


def representative_indices(x, subjects, labels, *, partition, limit=512, seed=2026):
    if partition!='train':
        raise ValueError('Calibration selection is restricted to training subjects')
    x,subjects,labels=map(np.asarray,(x,subjects,labels))
    if x.ndim!=3 or not len(x) or subjects.shape!=(len(x),) or labels.shape!=(len(x),) or not np.isfinite(x).all() or not np.isin(labels,[0,1]).all():
        raise ValueError('Invalid M0 waveform calibration data')
    if not isinstance(limit,int) or limit<1 or any(not str(s).strip() for s in subjects):
        raise ValueError('Invalid limit or subject identifiers')
    chosen=set()
    for subject in sorted(set(subjects)):
        ids=np.flatnonzero(subjects==subject)
        for label in sorted(set(labels[ids])):
            chosen.add(int(ids[np.flatnonzero(labels[ids]==label)[0]]))
        # Preserve positive/negative extrema for every channel of each subject.
        for channel in range(x.shape[2]):
            peaks=x[ids,:,channel].max(axis=1);troughs=x[ids,:,channel].min(axis=1)
            chosen.add(int(ids[np.argmax(peaks)]));chosen.add(int(ids[np.argmin(troughs)]))
    if len(chosen)>limit:
        raise ValueError('Calibration budget cannot cover required subjects/classes/extrema')
    for i in np.random.default_rng(seed).permutation(len(x)):
        if len(chosen)>=min(limit,len(x)):break
        chosen.add(int(i))
    return np.asarray(sorted(chosen),dtype=np.int64)
