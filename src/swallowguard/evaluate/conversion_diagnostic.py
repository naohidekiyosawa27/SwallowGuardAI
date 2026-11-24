"""Validation-only FP32 export control and default/reference INT8 kernel check."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from swallowguard.export.int8 import fixed_converter,quantize_input


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('waveforms',type=Path);p.add_argument('model_dir',type=Path);p.add_argument('output',type=Path)
    a=p.parse_args()
    import tensorflow as tf
    meta=json.loads((a.model_dir/'evaluation.json').read_text())
    with np.load(a.waveforms,allow_pickle=False) as d:
        ids=np.flatnonzero(np.isin(d['subjects'],meta['split']['validation']))
        x=((d['X'][ids]-np.asarray(meta['normalization']['mean']))/np.asarray(meta['normalization']['scale'])).astype(np.float32)
    if not len(x):raise ValueError('Empty validation partition')
    model=tf.keras.models.load_model(a.model_dir/'m0.keras');expected=model(x,training=False).numpy().ravel()
    fp32=fixed_converter(model).convert();int8=(a.model_dir/'m0.int8.tflite').read_bytes()
    report={'scope':'validation only; numerical control, not model selection',
            'float_model_sha256':hashlib.sha256((a.model_dir/'m0.keras').read_bytes()).hexdigest(),
            'comparisons':{}}
    for name,b,reference in [('float32',fp32,False),('original_int8_default',int8,False),('original_int8_reference',int8,True)]:
        extra={'experimental_op_resolver_type':tf.lite.experimental.OpResolverType.BUILTIN_REF} if reference else {}
        i=tf.lite.Interpreter(model_content=b,num_threads=1,**extra);i.allocate_tensors()
        inp=i.get_input_details()[0];out=i.get_output_details()[0];actual=[]
        for xx in x:
            value=xx[None] if inp['dtype']==np.float32 else quantize_input(xx[None],*inp['quantization'])
            i.set_tensor(inp['index'],value);i.invoke();value=i.get_tensor(out['index']).astype(float)
            actual.append(float(value.ravel()[0]) if out['dtype']==np.float32 else float((value-out['quantization'][1]).ravel()[0]*out['quantization'][0]))
        error=np.abs(expected-actual)
        report['comparisons'][name]={'max_probability_error':float(error.max()),'p99_error':float(np.quantile(error,.99)),
                                    'threshold_agreement':float(np.mean((expected>=.5)==(np.asarray(actual)>=.5)))}
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
