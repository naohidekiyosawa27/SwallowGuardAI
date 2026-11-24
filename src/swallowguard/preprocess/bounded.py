"""M0 experimental bounded representations; no signal clipping or imputation.

These transformations are numerical feature representations, not physiological
quality certification. Preserve raw signals and apply physical quality checks
separately. Per-window scaling discards absolute amplitude and must be evaluated.
"""
import numpy as np
from swallowguard.preprocess.signals import TrainStandardizer


def _headroom(value):
    if not np.isscalar(value) or not np.isfinite(value) or not 0<value<1:
        raise ValueError('Headroom must lie strictly between zero and one')


def normalized_windows(values, *, headroom=.9, minimum_peak=1e-12):
    _headroom(headroom)
    if not np.isfinite(minimum_peak) or minimum_peak<=0:raise ValueError('Invalid flatline threshold')
    x=np.asarray(values,dtype=np.float64)
    if x.ndim!=3 or not len(x) or x.shape[1]<2 or not x.shape[2] or not np.isfinite(x).all():
        raise ValueError('Require finite N x T x C waveforms; no missing-data filling')
    centered=x-x.mean(axis=1,keepdims=True)
    if not np.isfinite(centered).all():raise ValueError('Numerical centering overflow')
    peak=np.max(np.abs(centered),axis=1,keepdims=True)
    if np.any(peak<=minimum_peak):raise ValueError('Flat/degenerate channel: invalid measurement')
    # Pure centering and division; all finite samples are retained, with no clip.
    return (headroom*centered/peak).astype(np.float32)


class BoundedFeatures:
    def __init__(self,headroom=.9):
        _headroom(headroom);self.headroom=float(headroom);self.standardizer=TrainStandardizer()
    def fit(self,x,*,partition):
        self.standardizer.fit(x,partition=partition);return self
    def transform(self,x):
        z=self.standardizer.transform(x)
        if not np.isfinite(z).all():raise ValueError('Numerical standardization overflow')
        # Softsign is monotone and invertible within the open interval. This is
        # not replacement of missing or clipped physiological measurements.
        return (self.headroom*z/(1+np.abs(z))).astype(np.float32)
    def manifest(self):
        if not hasattr(self.standardizer,'mean'):raise ValueError('Transform not fitted')
        return {'method':'training_standardization_then_softsign','headroom':self.headroom,
                'mean':self.standardizer.mean.tolist(),'scale':self.standardizer.scale.tolist()}
