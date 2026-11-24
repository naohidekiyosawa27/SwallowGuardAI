"""Reproduce largest held-out quantization discrepancy; emits aggregate data only."""
import argparse
import json
from pathlib import Path
import numpy as np
from swallowguard.export.int8 import quantize_input


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('waveforms',type=Path);p.add_argument('model_dir',type=Path);p.add_argument('output',type=Path)
    a=p.parse_args()
    import tensorflow as tf
    r=json.loads((a.model_dir/'evaluation.json').read_text())
    with np.load(a.waveforms,allow_pickle=False) as d:
        ids=np.flatnonzero(np.isin(d['subjects'],r['split']['test']))
        x=((d['X'][ids]-np.array(r['normalization']['mean']))/np.array(r['normalization']['scale'])).astype(np.float32)
    if not len(x):raise ValueError('No held-out inputs')
    m=tf.keras.models.load_model(a.model_dir/'m0.keras');expected=m(x,training=False).numpy().ravel()
    i=tf.lite.Interpreter(model_path=str(a.model_dir/'m0.int8.tflite'));i.allocate_tensors()
    inp=i.get_input_details()[0];out=i.get_output_details()[0]
    scale,z=inp['quantization'];os,oz=out['quantization'];actual=[]
    for xx in x:
        i.set_tensor(inp['index'],quantize_input(xx[None],scale,z));i.invoke()
        actual.append(float((i.get_tensor(out['index']).astype(float)-oz).ravel()[0]*os))
    errors=np.abs(expected-np.asarray(actual));j=int(np.argmax(errors))
    lower,upper=(-128-z)*scale,(127-z)*scale
    report={'source':r['dataset_id']+' heldout event clips','clinical':False,'n_test':len(x),
            'input_representable_range':[lower,upper],'largest_parity_error':float(errors[j]),
            'float_probability_at_largest_error':float(expected[j]),'int8_probability_at_largest_error':actual[j],
            'input_saturation_fraction_at_largest_error':float(np.mean((x[j]<lower)|(x[j]>upper))),
            'normalized_input_range_at_largest_error':[float(x[j].min()),float(x[j].max())],
            'samples_error_above_0_05':int(np.sum(errors>.05)),
            'interpretation':'Largest discrepancy coincides with input saturation; causal attribution not proven. Deployment blocked pending range gating and independent validation.',
            'deployment_ready':False}
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
