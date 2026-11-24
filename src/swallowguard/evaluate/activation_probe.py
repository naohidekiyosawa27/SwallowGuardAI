"""Numerical intervention on the previously exposed M01 regression outlier.

This does not label a physiological artifact and must never authorize accepting
clipped signals. It exports scalar/tensor summaries, never waveform samples.
"""
import argparse
import json
from pathlib import Path
import numpy as np
from swallowguard.export.int8 import quantize_input,input_range


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('waveforms',type=Path);p.add_argument('model_dir',type=Path);p.add_argument('output',type=Path)
    p.add_argument('--allow-exposed-regression-diagnostic',action='store_true');a=p.parse_args()
    if not a.allow_exposed_regression_diagnostic:
        raise ValueError('Explicit acknowledgement of already-exposed regression data required')
    import tensorflow as tf
    meta=json.loads((a.model_dir/'evaluation.json').read_text())
    with np.load(a.waveforms,allow_pickle=False) as d:
        ids=np.flatnonzero(np.isin(d['subjects'],meta['split']['test']))
        x=((d['X'][ids]-np.asarray(meta['normalization']['mean']))/np.asarray(meta['normalization']['scale'])).astype(np.float32)
    if not len(x):raise ValueError('Empty regression partition')
    # Selection identifies the largest-amplitude already known case, without
    # training or selecting model candidates on these data.
    x=x[int(np.argmax(np.max(np.abs(x),axis=(1,2))))][None]
    model=tf.keras.models.load_model(a.model_dir/'m0.keras')
    i=tf.lite.Interpreter(model_path=str(a.model_dir/'m0.int8.tflite'),experimental_preserve_all_tensors=True,
                          experimental_op_resolver_type=tf.lite.experimental.OpResolverType.BUILTIN_WITHOUT_DEFAULT_DELEGATES)
    i.allocate_tensors();inp=i.get_input_details()[0];out=i.get_output_details()[0];scale,z=inp['quantization']
    q=quantize_input(x,scale,z);i.set_tensor(inp['index'],q);i.invoke()
    os,oz=out['quantization'];int8_probability=float((i.get_tensor(out['index']).astype(float)-oz).ravel()[0]*os)
    tensors={t['index']:t for t in i.get_tensor_details()};layers=[];bounds=[]
    for op in i._get_ops_details():
        if op['op_name'] not in {'CONV_2D','MEAN','FULLY_CONNECTED','LOGISTIC'}:continue
        index=int(op['outputs'][0]);tensor=tensors[index];s,zero=tensor['quantization'];lo,hi=input_range(s,zero)
        values=i.get_tensor(index);bounds.append((lo,hi))
        layers.append({'operator':op['op_name'],'range':[lo,hi],
                       'upper_endpoint_fraction':float(np.mean(values==127)),
                       'lower_endpoint_fraction':float(np.mean(values==-128))})
    if [l['operator'] for l in layers]!=['CONV_2D','CONV_2D','MEAN','FULLY_CONNECTED','FULLY_CONNECTED','LOGISTIC']:
        raise ValueError('Probe is restricted to the inspected M01 architecture')
    dequantized=(q.astype(np.float32)-z)*scale
    original=float(model(x,training=False).numpy().ravel()[0])
    rounded_input=float(model(dequantized,training=False).numpy().ravel()[0])
    # Follow the existing sequential M0 architecture with frozen weights.
    # Clamp intermediate floats only as a numerical counterfactual.
    value=model.get_layer('signal_expand')(dequantized)
    counterfactual=[]
    for index,name in enumerate(['signal_conv_a','signal_conv_b','signal_pool','dense']):
        value=model.get_layer(name)(value).numpy()
        counterfactual.append({'layer':name,'float_max_before_clamping':float(value.max()),
                               'fraction_above_int8_range':float(np.mean(value>bounds[index][1]))})
        value=np.clip(value,*bounds[index])
    weights,bias=model.get_layer('event_probability').get_weights()
    logits=np.clip(value@weights+bias,*bounds[4])
    probability=np.clip(1/(1+np.exp(-logits)),*bounds[5]);clamped=float(probability.ravel()[0])
    report={'scope':'previously exposed regression outlier; numerical diagnostic only',
            'original_float_probability':original,'input_quantize_dequantize_float_probability':rounded_input,
            'input_and_activation_clamped_float_probability':clamped,'actual_int8_probability':int8_probability,
            'layers':layers,'counterfactual_intermediates':counterfactual,
            'interpretation':'Input saturation alone does not explain discrepancy. Intermediate activation range clipping is a tested numerical mechanism; no physiological cause or clinical validity is inferred.',
            'deploy_clipped_signals':False,'clinical_claim':False}
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
