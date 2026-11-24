"""Manual optional check: untrained model on noise, no performance claims."""
import numpy as np
from swallowguard.train.models import m0_model,m1_candidate
from swallowguard.export.int8 import convert,audit,parity

if __name__=='__main__':
    import tensorflow as tf
    tf.keras.utils.set_random_seed(2026)
    assert m1_candidate().count_params()==4137
    rng=np.random.default_rng(2026)
    representative=rng.normal(size=(8,800,1)).astype(np.float32)
    heldout=rng.normal(size=(3,800,1)).astype(np.float32)
    model=m0_model();b=convert(model,[representative],partition='train')
    print({'source':'synthetic','untrained':True,'audit':audit(b),'parity':parity(model,b,heldout)})
