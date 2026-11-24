"""Export an audited candidate and synthetic golden INT8 vector for target replay.

No actual participant waveform is emitted. Target equivalence remains unmeasured.
"""
import argparse
import json
from pathlib import Path
import numpy as np
from swallowguard.export.int8 import audit,quantize_input


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('model',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
    import tensorflow as tf
    b=a.model.read_bytes();manifest=audit(b)
    i=tf.lite.Interpreter(model_content=b);i.allocate_tensors()
    inp=i.get_input_details()[0];out=i.get_output_details()[0]
    if len(i.get_input_details())!=1:raise ValueError('M0 single-input export only')
    synthetic=np.random.default_rng(2026).normal(0,.2,size=inp['shape']).astype(np.float32)
    scale,z=inp['quantization'];q=quantize_input(synthetic,scale,z)
    i.set_tensor(inp['index'],q);i.invoke();expected=i.get_tensor(out['index'])
    a.output.mkdir(parents=True,exist_ok=True)
    lines=[]
    for j in range(0,len(b),16):lines.append('  '+','.join(f'0x{x:02x}' for x in b[j:j+16])+',')
    text='#pragma once\n#include <cstddef>\n#include <cstdint>\n// RESEARCH MODE; unvalidated event candidate\n'
    text+='alignas(16) inline constexpr unsigned char sg_model[] = {\n'+'\n'.join(lines)+'\n};\n'
    text+='inline constexpr size_t sg_model_len=sizeof(sg_model);\n'
    (a.output/'model_data.hpp').write_text(text)
    (a.output/'golden_synthetic.json').write_text(json.dumps({
        'source':'synthetic','seed':2026,'model_sha256':manifest['sha256'],
        'shape':inp['shape'].tolist(),'input_int8':q.ravel().tolist(),
        'expected_output_int8':expected.ravel().tolist(),'target_replayed':False})+'\n')
    (a.output/'export_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')


if __name__=='__main__':main()
