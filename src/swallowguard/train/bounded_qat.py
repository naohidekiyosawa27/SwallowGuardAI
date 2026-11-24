"""M0-R3: fixed-budget bounded PTQ/QAT study; CPU-only, train/validation first.

Run in requirements-qat.txt environment with TF_USE_LEGACY_KERAS=1.
All candidate successes/failures are retained. Test means exposed regression,
not a new independent study. M1 and all clinical gates remain unchanged.
"""
import os
os.environ.setdefault('TF_USE_LEGACY_KERAS','1')
import argparse
import hashlib
import json
import random
from pathlib import Path
import numpy as np
from swallowguard.preprocess.bounded import BoundedFeatures,normalized_windows
from swallowguard.evaluate.metrics import binary_metrics
from swallowguard.evaluate.selective import infer_accepted,summarize,select_candidate
from swallowguard.export.int8 import convert,audit
from swallowguard.train.splits import assert_disjoint


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def probabilities(model,x,batch=64):
    return np.concatenate([model(x[start:start+batch],training=False).numpy().ravel() for start in range(0,len(x),batch)])


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('features',type=Path);p.add_argument('waveforms',type=Path)
    p.add_argument('original_evaluation',type=Path);p.add_argument('protocol',type=Path);p.add_argument('output',type=Path)
    a=p.parse_args()
    import tensorflow as tf
    import tf_keras as keras
    import tensorflow_model_optimization as tfmot
    from swallowguard.train.qat_models import bounded_m0,quantization_aware,float_shadow,CUSTOM_OBJECTS
    tf.config.threading.set_inter_op_parallelism_threads(1);tf.config.threading.set_intra_op_parallelism_threads(2)
    random.seed(2026);np.random.seed(2026);tf.random.set_seed(2026);tf.config.experimental.enable_op_determinism()
    protocol=json.loads(a.protocol.read_text())
    if protocol['protocol_id']!='M0-R3-bounded-QAT-v1':raise ValueError('Unknown frozen protocol')
    original=json.loads(a.original_evaluation.read_text());assert_disjoint(original['split'])
    with np.load(a.features,allow_pickle=False) as d:
        if str(d['source'].item())!='replayed_research' or str(d['dataset_id'].item())!='D4_v2':raise ValueError('Expected authorized D4 v2 features')
        features,y,s=d['X'],d['y'],d['subjects']
    with np.load(a.waveforms,allow_pickle=False) as d:
        if not np.array_equal(d['y'],y) or not np.array_equal(d['subjects'],s):raise ValueError('Canonical feature/waveform rows disagree')
    ids={k:np.flatnonzero(np.isin(s,v)) for k,v in original['split'].items()};tr,val=ids['train'],ids['validation']
    if sum(map(len,ids.values()))!=len(y) or set(y[tr])!={0,1}:raise ValueError('Invalid participant/class partition')
    transform=BoundedFeatures().fit(features[tr],partition='train')
    a.output.mkdir(parents=True,exist_ok=True)
    provenance={'protocol_sha256':digest(a.protocol),'feature_sha256':digest(a.features),'waveform_sha256':digest(a.waveforms),
                'source_base_commit':protocol['source_base_commit'],'tensorflow':tf.__version__,'tf_keras':keras.__version__,
                'tfmot':tfmot.__version__,'numpy':np.__version__,'fit_partition':'train','calibration_partition':'train',
                'selection_partition':'validation','original_test_usage':'already exposed regression only',
                'cpu_only':True,'paid_compute':False,'seed':2026}
    (a.output/'manifest_before_training.json').write_text(json.dumps(provenance,indent=2)+'\n')
    reports={};models={};inputs_by_kind={};histories={}
    class_weights={int(label):len(tr)/(2*int(np.sum(y[tr]==label))) for label in [0,1]}

    class ValidationCheckpoint(keras.callbacks.Callback):
        def __init__(self,validation_x,patience):
            super().__init__();self.validation_x=validation_x;self.patience=patience
            self.best=None;self.weights=None;self.wait=0;self.history=[]
        def on_epoch_end(self,epoch,logs=None):
            prob=probabilities(self.model,self.validation_x);score=binary_metrics(y[val],(prob>=.5).astype(int))['f1']
            clipped=np.clip(prob,1e-7,1-1e-7)
            bce=float(np.mean(-y[val]*np.log(clipped)-(1-y[val])*np.log(1-clipped)))
            key=(score,-bce);self.history.append({'epoch':epoch+1,'event_f1':score,'bce':bce})
            if self.best is None or key>self.best:
                self.best=key;self.weights=self.model.get_weights();self.wait=0
            else:self.wait+=1
            print(f'epoch={epoch+1} validation_event_F1={score:.4f} BCE={bce:.4f}',flush=True)
            if self.wait>=self.patience:self.model.stop_training=True
        def on_train_end(self,logs=None):
            if self.weights is not None:self.model.set_weights(self.weights)

    def train(model,x,*,epochs,patience,lr):
        model.compile(optimizer=keras.optimizers.Adam(lr),loss='binary_crossentropy')
        options=tf.data.Options();options.threading.private_threadpool_size=1
        training=tf.data.Dataset.from_tensor_slices((x[tr],y[tr])).shuffle(len(tr),seed=2026).batch(32).with_options(options)
        checkpoint=ValidationCheckpoint(x[val],patience)
        model.fit(training,epochs=epochs,verbose=0,callbacks=[checkpoint],class_weight=class_weights)
        return checkpoint.history

    def evaluate(name,model,shadow,x,kind):
        b=convert(model,[x[tr]],partition='train',representative_indices=np.arange(len(tr),dtype=np.int64))
        metadata=audit(b);prob=probabilities(shadow,x[val]);q=infer_accepted(b,x[val])
        result={'model_bytes':len(b),'calibration_count':len(tr),'manifest':metadata,
                'validation':summarize(y[val],prob,q,s[val]),'parameters':shadow.count_params(),
                'all_validation_shadow_metrics':binary_metrics(y[val],(prob>=.5).astype(int)),
                'kind':kind,'training_epochs':len(histories[name]),'normalization':transform.manifest() if kind=='features' else {'method':'window_center_peak_division','headroom':.9,'amplitude_discarded':True}}
        if name.endswith('QAT'):
            simulated=probabilities(model,x[val]);accepted=np.isfinite(q)
            result['qat_simulation_max_error_vs_int8_accepted']=float(np.max(np.abs(simulated[accepted]-q[accepted]))) if accepted.any() else None
        directory=a.output/name;directory.mkdir(exist_ok=True)
        (directory/'model.int8.tflite').write_bytes(b)
        shadow.save(directory/'shadow.keras')
        if name.endswith('QAT'):
            model.save_weights(directory/'qat.weights.h5')
        models[name]=b
        return result

    for kind in ['features','waveform']:
        random.seed(2026);np.random.seed(2026);tf.random.set_seed(2026)
        if kind=='features':x=transform.transform(features)
        else:
            with np.load(a.waveforms,allow_pickle=False) as d:x=normalized_windows(d['X'])
        inputs_by_kind[kind]=x
        print('Training float warm start:',kind,flush=True)
        base=bounded_m0(kind)
        key=kind+'_PTQ';histories[key]=train(base,x,epochs=protocol['epochs'][kind+'_float_max'],patience=protocol['epochs']['float_patience'],lr=.001)
        try:reports[key]=evaluate(key,base,base,x,kind)
        except Exception as error:reports[key]={'failed':True,'error':type(error).__name__+': '+str(error)}
        print('Training QAT fine tune:',kind,flush=True)
        key=kind+'_QAT'
        try:
            aware=quantization_aware(base)
            histories[key]=train(aware,x,epochs=protocol['epochs']['qat_max'],patience=protocol['epochs']['qat_patience'],lr=.0003)
            reports[key]=evaluate(key,aware,float_shadow(aware,kind),x,kind)
        except Exception as error:reports[key]={'failed':True,'error':type(error).__name__+': '+str(error)}
        (a.output/'interim_validation.json').write_text(json.dumps(reports,indent=2,allow_nan=False)+'\n')

    # First enforce numerical criteria unchanged from R2, then the stricter
    # event-F1 floor. Never select a trivially constant numerical match.
    candidates={k:v for k,v in reports.items() if not v.get('failed')}
    numerically_eligible=[];eligible=[]
    for name,item in candidates.items():
        passed=select_candidate({name:item}) is not None
        item['numerical_criteria_passed']=passed
        if passed:numerically_eligible.append(name)
        metrics=item['validation']['accepted_int8_metrics']
        full_pass=passed and metrics is not None and metrics['f1']>=protocol['accuracy_requirement']['minimum_validation_event_F1_int8']
        item['accuracy_and_numerical_criteria_passed']=full_pass
        if full_pass:eligible.append(name)
    chosen=(min(eligible,key=lambda k:(-candidates[k]['validation']['accepted_int8_metrics']['f1'],
                candidates[k]['validation']['max_probability_error_accepted'],candidates[k]['model_bytes'],k)) if eligible else None)
    selection={'selected':chosen,'eligible':eligible,'numerically_eligible':numerically_eligible,'reports':reports,'provenance':provenance}
    (a.output/'selection_before_regression.json').write_text(json.dumps(selection,indent=2,allow_nan=False)+'\n')
    regression=None
    if chosen is not None:
        kind=candidates[chosen]['kind'];x=inputs_by_kind[kind];test=ids['test']
        shadow=keras.models.load_model(a.output/chosen/'shadow.keras')
        regression=summarize(y[test],probabilities(shadow,x[test]),infer_accepted(models[chosen],x[test]),s[test])
        regression['scope']='previously exposed M01 regression, not external/confirmatory'
        (a.output/'selected.int8.tflite').write_bytes(models[chosen])
    result={**selection,'histories':histories,'regression':regression,'deployment_ready':False,
            'clinical_validation':False,'hardware_latency_measured':False,'M1_unchanged':True,'M01_reference_unchanged':True,
            'limitations':['Custom QAT configuration is experimental; actual flatbuffer audited, physical inference unverified',
                           'Bounded representation does not certify physiological signal quality',
                           'Numerical pass is not independent clinical/event validation',
                           'Existing validation has been reused for model development; external confirmation required']}
    (a.output/'results.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print('Selected:',chosen,'numerically eligible:',numerically_eligible,flush=True)


if __name__=='__main__':main()
