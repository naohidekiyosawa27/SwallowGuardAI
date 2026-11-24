"""Exactly map a conventional logistic baseline into an INT8 research comparator.

This does not change M1 architecture or select a clinical/deployment model.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from swallowguard.train.splits import assert_disjoint
from swallowguard.export.int8 import convert,audit
from swallowguard.evaluate.selective import infer_accepted,summarize,select_candidate


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('features',type=Path);p.add_argument('original_evaluation',type=Path)
    p.add_argument('protocol',type=Path);p.add_argument('output',type=Path)
    p.add_argument('--feature-set',choices=['paired','sound','emg'],default='paired');a=p.parse_args()
    import tensorflow as tf
    tf.config.threading.set_inter_op_parallelism_threads(1)
    tf.config.threading.set_intra_op_parallelism_threads(2)
    tf.keras.utils.set_random_seed(2026)
    protocol=json.loads(a.protocol.read_text())
    if protocol['protocol_id'] not in {'M0-R2-linear-reference-v1','M0-R2-modality-linear-v1'}:raise ValueError('Unknown protocol')
    if a.feature_set not in protocol.get('feature_sets',['paired']):raise ValueError('Feature set not authorized by frozen protocol')
    original=json.loads(a.original_evaluation.read_text());assert_disjoint(original['split'])
    with np.load(a.features,allow_pickle=False) as d:
        if str(d['dataset_id'].item())!='D4_v2' or str(d['source'].item())!='replayed_research':raise ValueError('D4 provenance required')
        x,y,s=d['X'],d['y'],d['subjects']
    if x.ndim!=2 or x.shape[1]!=15 or y.shape!=(len(x),) or s.shape!=y.shape or not np.isfinite(x).all() or not np.isin(y,[0,1]).all():raise ValueError('Invalid D4 feature table')
    x=x[:,{'paired':slice(0,15),'sound':slice(0,5),'emg':slice(5,15)}[a.feature_set]]
    ids={part:np.flatnonzero(np.isin(s,v)) for part,v in original['split'].items()};tr,val=ids['train'],ids['validation']
    scaler=StandardScaler().fit(x[tr]);normalized=scaler.transform(x).astype(np.float32)
    classifier=LogisticRegression(class_weight='balanced',C=1,max_iter=1000,random_state=2026).fit(normalized[tr],y[tr])
    inp=tf.keras.Input((x.shape[1],),name=a.feature_set+'_features');out=tf.keras.layers.Dense(1,activation='sigmoid',name='event_probability')(inp)
    model=tf.keras.Model(inp,out,name='M0_linear_comparator')
    model.layers[-1].set_weights([classifier.coef_.T.astype(np.float32),classifier.intercept_.astype(np.float32)])
    a.output.mkdir(parents=True,exist_ok=True)
    provenance={'protocol_sha256':hashlib.sha256(a.protocol.read_bytes()).hexdigest(),
                'features_sha256':hashlib.sha256(a.features.read_bytes()).hexdigest(),
                'fit_partition':'train','normalization_fit_partition':'train','calibration_partition':'train',
                'calibration_count':len(tr),'seed':2026,'tensorflow':tf.__version__,'feature_set':a.feature_set}
    (a.output/'manifest_before_evaluation.json').write_text(json.dumps(provenance,indent=2)+'\n')
    model_bytes=convert(model,[normalized[tr]],partition='train',representative_indices=np.arange(len(tr),dtype=np.int64))
    float_val=model(normalized[val],training=False).numpy().ravel()
    mapping_error=float(np.max(np.abs(float_val-classifier.predict_proba(normalized[val])[:,1])))
    report=summarize(y[val],float_val,infer_accepted(model_bytes,normalized[val]),s[val])
    limits=protocol['acceptance'];name='linear_comparator'
    accepted=select_candidate({name:{'model_bytes':len(model_bytes),'calibration_count':len(tr),'validation':report}},
        minimum_coverage=limits['minimum_coverage'],max_error=limits['maximum_probability_error'],
        minimum_agreement=limits['minimum_threshold_agreement'],max_f1_loss=limits['maximum_f1_loss'],
        max_bytes=limits['maximum_model_bytes_exclusive']) is not None
    (a.output/'selection_before_regression.json').write_text(json.dumps({'validation_numerical_criteria_passed':accepted,'validation':report,'provenance':provenance},indent=2)+'\n')
    regression=None
    if accepted:
        test=ids['test'];fp=model(normalized[test],training=False).numpy().ravel()
        regression=summarize(y[test],fp,infer_accepted(model_bytes,normalized[test]),s[test])
        regression['usage']='previously exposed M01 test; not new confirmatory validation'
    result={'mode':'RESEARCH MODE','stage':'M0 conventional comparator','parameters':model.count_params(),
            'keras_vs_sklearn_validation_max_probability_error':mapping_error,'provenance':provenance,
            'validation':report,'validation_numerical_criteria_passed':accepted,'regression':regression,
            'int8':audit(model_bytes),'deployment_ready':False,'changes_M01_reference':False,
            'clinical_validation':False,'normalization':{'mean':scaler.mean_.tolist(),'scale':scaler.scale_.tolist()},
            'limitations':['Feature extraction CPU/memory and hardware latency not measured',
                           'Cannot compare accepted-only scores without coverage',
                           'No independent external test','M1 architecture and M2 clinical gate unchanged']}
    model.save(a.output/'linear_comparator.keras');(a.output/'linear_comparator.int8.tflite').write_bytes(model_bytes)
    (a.output/'results.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print('Linear validation numerical criteria passed:',accepted,flush=True)


if __name__=='__main__':main()
