"""Aggregate normalized-input range audit using the unchanged M01 scaler."""
import argparse
import json
from pathlib import Path
import numpy as np
from swallowguard.evaluate.selective import range_acceptance


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('waveforms',type=Path);p.add_argument('model_dir',type=Path);p.add_argument('output',type=Path)
    a=p.parse_args()
    import tensorflow as tf
    meta=json.loads((a.model_dir/'evaluation.json').read_text())
    with np.load(a.waveforms,allow_pickle=False) as d:
        x=((d['X']-np.asarray(meta['normalization']['mean']))/np.asarray(meta['normalization']['scale'])).astype(np.float32)
        subjects=d['subjects']
    interpreter=tf.lite.Interpreter(model_path=str(a.model_dir/'m0.int8.tflite'))
    interpreter.allocate_tensors();scale,z=interpreter.get_input_details()[0]['quantization']
    report={'source':'D4_v2','numerical_analysis_only':True,'source_model_sha256':meta['int8']['sha256'],'partitions':{}}
    for part,groups in meta['split'].items():
        values=x[np.isin(subjects,groups)];peaks=np.max(np.abs(values),axis=1)
        report['partitions'][part]={'clips':len(values),'clips_outside_int8_range':int(np.sum(~range_acceptance(values,scale,z))),
            'per_channel_peak_abs_percentiles':{str(q):np.percentile(peaks,q,axis=0).tolist() for q in [50,95,99,100]}}
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
