"""Optional M0 training/export CLI; never run against fabricated clinical labels.

Canonical NPZ: X (N,T,C), y, subjects, source scalar, dataset_id scalar.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from swallowguard.train.splits import subject_split
from swallowguard.preprocess.signals import TrainStandardizer
from swallowguard.train.models import m0_model
from swallowguard.export.int8 import convert,audit,parity
from swallowguard.evaluate.metrics import binary_metrics,cluster_f1_ci


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("input",type=Path);p.add_argument("output",type=Path);p.add_argument("--epochs",type=int,default=20)
    a=p.parse_args()
    if a.epochs < 1: raise ValueError("Positive epochs required")
    import tensorflow as tf
    tf.config.threading.set_inter_op_parallelism_threads(1)
    tf.config.threading.set_intra_op_parallelism_threads(2)
    tf.keras.utils.set_random_seed(2026)
    tf.config.experimental.enable_op_determinism()
    with np.load(a.input,allow_pickle=False) as d:
        x,y,s=d['X'],d['y'],d['subjects'];source=str(d['source'].item());dataset=str(d['dataset_id'].item())
    if source not in {'synthetic','replayed_research','live_bench'} or not dataset:
        raise ValueError("Provenance required")
    if x.ndim!=3 or len(x)!=len(y) or s.shape!=y.shape or y.ndim!=1 or not np.isin(y,[0,1]).all() or not np.isfinite(x).all():
        raise ValueError("Invalid canonical waveforms")
    split=subject_split(s);ids={k:np.flatnonzero(np.isin(s,v)) for k,v in split.items()}
    if set(y[ids['train']])!={0,1}:raise ValueError("Both training classes required")
    norm=TrainStandardizer().fit(x[ids['train']].reshape(-1,x.shape[-1]),partition='train')
    x=norm.transform(x.reshape(-1,x.shape[-1])).reshape(x.shape).astype(np.float32)
    model=m0_model(x.shape[1],x.shape[2]);model.compile(optimizer='adam',loss='binary_crossentropy')
    options=tf.data.Options();options.threading.private_threadpool_size=1
    training=tf.data.Dataset.from_tensor_slices((x[ids['train']],y[ids['train']])).shuffle(len(ids['train']),seed=2026).batch(16).with_options(options)
    validation=tf.data.Dataset.from_tensor_slices((x[ids['validation']],y[ids['validation']])).batch(16).with_options(options)
    model.fit(training,validation_data=validation,
              epochs=a.epochs,verbose=2,
              callbacks=[tf.keras.callbacks.EarlyStopping(patience=3,restore_best_weights=True)])
    b=convert(model,[x[ids['train']]],partition='train');manifest=audit(b)
    test=ids['test'];pred=(model(x[test],training=False).numpy().ravel()>=0.5).astype(int)
    val_pred=(model(x[ids['validation']],training=False).numpy().ravel()>=0.5).astype(int)
    report={'mode':'RESEARCH MODE','stage':'M0','source':source,'dataset_id':dataset,'split':split,
            'input_sha256':hashlib.sha256(a.input.read_bytes()).hexdigest(),'tensorflow_version':tf.__version__,
            'validation_window_metrics':binary_metrics(y[ids['validation']],val_pred),
            'float_window_metrics':binary_metrics(y[test],pred),'f1_ci':cluster_f1_ci(y[test],pred,s[test]),
            'quantization_parity':parity(model,b,x[test],labels=y[test],subjects=s[test]),'int8':manifest,
            'normalization':{'mean':norm.mean.tolist(),'scale':norm.scale.tolist()},
            'parameters':model.count_params(),'clinical_validation':False,'latency_measured':False,
            'epochs_requested':a.epochs,'epochs_ran':len(model.history.history['loss'])}
    a.output.mkdir(parents=True,exist_ok=True)
    model.save(a.output/'m0.keras');(a.output/'m0.int8.tflite').write_bytes(b)
    (a.output/'evaluation.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
