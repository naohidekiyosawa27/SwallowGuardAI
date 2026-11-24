"""Inspect a local INT8 flatbuffer; logical MACs are not measured latency/RAM."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('model',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
    import tensorflow as tf
    data=a.model.read_bytes()
    interpreter=tf.lite.Interpreter(model_content=data,experimental_preserve_all_tensors=True)
    interpreter.allocate_tensors()
    tensors={int(t['index']):t for t in interpreter.get_tensor_details()}
    ops=[];macs=0
    for op in interpreter._get_ops_details():
        if op['op_name']=='DELEGATE':continue
        output=tensors[int(op['outputs'][0])]
        row={'operator':op['op_name'],'output_shape':output['shape'].tolist()}
        if op['op_name'] in {'CONV_2D','FULLY_CONNECTED'}:
            weights=tensors[int(op['inputs'][1])]
            count=int(np.prod(output['shape'])*np.prod(weights['shape'][1:]))
            row['multiply_accumulate_count']=count;macs+=count
        ops.append(row)
    result={
        'model_sha256':hashlib.sha256(data).hexdigest(),
        'calculation':'logical multiply-accumulates from actual flatbuffer shapes, not measured cycles or ESP-NN work',
        'operators':ops,'total_conv_and_dense_MACs_per_window':macs,
        'input_bytes':int(np.prod(interpreter.get_input_details()[0]['shape'])),
        'largest_single_int8_tensor_bytes':max(int(np.prod(t['shape'])) for t in tensors.values() if t['dtype']==np.int8),
        'arena_bytes':None,'latency_ms':None,'hardware_measured':False,
        'limitations':['Single-tensor size is not tensor arena size; allocator overhead, scratch, lifetime overlap, PSRAM placement and kernel optimizations are unmeasured',
                       'MAC count does not determine hardware latency or energy']}
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__':main()
