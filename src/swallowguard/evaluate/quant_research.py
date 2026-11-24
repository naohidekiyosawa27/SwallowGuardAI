"""Frozen-model quantization study: train calibration, validation selection,
then explicitly exposed regression testing. No retraining or clinical endpoints.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from swallowguard.export.calibration import representative_indices
from swallowguard.export.int8 import convert,audit,parity
from swallowguard.evaluate.selective import infer_accepted,summarize,select_candidate
from swallowguard.train.splits import assert_disjoint


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('waveforms',type=Path);p.add_argument('model_dir',type=Path)
    p.add_argument('protocol',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
    import tensorflow as tf
    tf.config.threading.set_inter_op_parallelism_threads(1)
    tf.config.threading.set_intra_op_parallelism_threads(2)
    tf.keras.utils.set_random_seed(2026)
    protocol=json.loads(a.protocol.read_text())
    if protocol['protocol_id']!='M0-R2-quantization-abstention-v1':raise ValueError('Unknown frozen protocol')
    meta=json.loads((a.model_dir/'evaluation.json').read_text());assert_disjoint(meta['split'])
    with np.load(a.waveforms,allow_pickle=False) as d:
        raw,y,s=d['X'],d['y'],d['subjects']
        if str(d['source'].item())!='replayed_research' or str(d['dataset_id'].item())!='D4_v2':
            raise ValueError('Expected authorized D4 v2 research data')
    if raw.ndim!=3 or y.shape!=(len(raw),) or s.shape!=y.shape or not np.isfinite(raw).all() or not np.isin(y,[0,1]).all():
        raise ValueError('Invalid canonical waveform table')
    x=((raw-np.asarray(meta['normalization']['mean']))/np.asarray(meta['normalization']['scale'])).astype(np.float32)
    del raw
    ids={k:np.flatnonzero(np.isin(s,v)) for k,v in meta['split'].items()}
    if sum(map(len,ids.values()))!=len(x):raise ValueError('Partition does not cover every clip')
    a.output.mkdir(parents=True,exist_ok=True)
    manifest={'protocol_sha256':sha(a.protocol),'input_sha256':sha(a.waveforms),
              'float_model_sha256':sha(a.model_dir/'m0.keras'),'source_base_commit':protocol['source_base_commit'],
              'normalizer':'unchanged_M01_training_only','seed':2026,'tensorflow':tf.__version__,
              'calibration_partition':'train','selection_partition':'validation','test_usage':'exposed_regression_only'}
    (a.output/'manifest_before_evaluation.json').write_text(json.dumps(manifest,indent=2)+'\n')
    model=tf.keras.models.load_model(a.model_dir/'m0.keras')
    tr=ids['train'];val=ids['validation']
    selections={'existing_random256':None,
                'subject_class_extrema512':representative_indices(x[tr],s[tr],y[tr],partition='train'),
                'all_training':np.arange(len(tr),dtype=np.int64)}
    reports={};models={};float_val=model(x[val],training=False).numpy().ravel()
    for name,selected in selections.items():
        print('Evaluating validation candidate',name,flush=True)
        b=(a.model_dir/'m0.int8.tflite').read_bytes() if selected is None else convert(model,[x[tr]],partition='train',representative_indices=selected)
        audit_result=audit(b);models[name]=b
        q=infer_accepted(b,x[val])
        reports[name]={'model_bytes':len(b),'calibration_count':256 if selected is None else len(selected),
                       'manifest':audit_result,'validation':summarize(y[val],float_val,q,s[val]),
                       'ungated_validation_diagnostic':parity(model,b,x[val])}
        (a.output/(name+'.int8.tflite')).write_bytes(b)
    limits=protocol['validation_acceptance']
    chosen=select_candidate(reports,minimum_coverage=limits['minimum_coverage'],
        max_error=limits['maximum_absolute_probability_error_on_accepted'],
        minimum_agreement=limits['minimum_threshold_agreement_on_accepted'],
        max_f1_loss=limits['maximum_f1_loss_accepted_int8_vs_accepted_float'],
        max_bytes=limits['maximum_model_bytes_exclusive'])
    selection={'selected_by_validation':chosen,'candidate_reports':reports,'protocol_sha256':manifest['protocol_sha256']}
    # This durable local record is written BEFORE touching regression predictions.
    (a.output/'selection_before_regression.json').write_text(json.dumps(selection,indent=2,allow_nan=False)+'\n')
    regression=None
    if chosen is not None:
        test=ids['test'];float_test=model(x[test],training=False).numpy().ravel()
        regression=summarize(y[test],float_test,infer_accepted(models[chosen],x[test]),s[test])
        regression['usage']='previously_exposed_M01_test; not_external_or_confirmatory'
        (a.output/'selected_candidate.int8.tflite').write_bytes(models[chosen])
    result={'mode':'RESEARCH MODE','stage':'M0','manifest':manifest,'validation':reports,
            'selected_by_validation':chosen,'regression':regression,'deployment_ready':False,
            'external_validation':False,'hardware_latency_measured':False,
            'limitations':['Fixed previously trained CNN; no claim of improved physiological event recognition',
                           'Numerical abstention only; physical artifacts and clinical safety not adjudicated',
                           'Accepted-only F1 must be read with coverage and 2x3 confusion',
                           'Old test already exposed; independent confirmation required',
                           'CNN is not selected over the random forest event reference']}
    (a.output/'results.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print('Selected by validation:',chosen,flush=True)


if __name__=='__main__':main()
