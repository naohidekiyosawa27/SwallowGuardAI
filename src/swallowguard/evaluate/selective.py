"""Numerical abstention accounting. Rejections stay in the reported denominator."""
import numpy as np
from swallowguard.export.int8 import input_range,checked_quantize_input
from swallowguard.evaluate.metrics import binary_metrics,cluster_f1_ci


def range_acceptance(inputs, scale, zero_point):
    x=np.asarray(inputs,dtype=np.float64)
    if x.ndim<2 or not len(x) or not np.prod(x.shape[1:]):
        raise ValueError('Require nonempty batched input')
    lower,upper=input_range(scale,zero_point)
    return np.all(np.isfinite(x)&(x>=lower)&(x<=upper),axis=tuple(range(1,x.ndim)))


def infer_accepted(model_bytes, inputs):
    import tensorflow as tf
    interpreter=tf.lite.Interpreter(model_content=model_bytes,num_threads=1)
    interpreter.allocate_tensors()
    ins,outs=interpreter.get_input_details(),interpreter.get_output_details()
    if len(ins)!=1 or len(outs)!=1 or ins[0]['dtype']!=np.int8 or outs[0]['dtype']!=np.int8:
        raise ValueError('Require a single-input/output INT8 M0 model')
    scale,z=ins[0]['quantization'];os,oz=outs[0]['quantization']
    accepted=range_acceptance(inputs,scale,z);predictions=np.full(len(inputs),np.nan)
    for index in np.flatnonzero(accepted):
        interpreter.set_tensor(ins[0]['index'],checked_quantize_input(inputs[index:index+1],scale,z))
        interpreter.invoke()
        predictions[index]=float((interpreter.get_tensor(outs[0]['index']).astype(float)-oz).ravel()[0]*os)
    return predictions


def summarize(labels, float_probability, selective_probability, subjects, *, bootstrap=1000):
    y,f,q,s=map(np.asarray,(labels,float_probability,selective_probability,subjects))
    if y.ndim!=1 or not len(y) or any(a.shape!=y.shape for a in (f,q,s)) or not np.isin(y,[0,1]).all():
        raise ValueError('Invalid aligned selective-evaluation data')
    if not np.isfinite(f).all() or np.any((f<0)|(f>1)) or np.isinf(q).any() or np.any((q[np.isfinite(q)]<0)|(q[np.isfinite(q)]>1)):
        raise ValueError('Probabilities must be finite [0,1] or NaN for abstention')
    accepted=np.isfinite(q);n=int(accepted.sum());matrix=np.zeros((2,3),dtype=int)
    for label,prob in zip(y,q):matrix[int(label),int(prob>=.5) if np.isfinite(prob) else 2]+=1
    report={'all_windows':len(y),'accepted_windows':n,'abstained_windows':len(y)-n,
            'coverage':n/len(y),'confusion_true_rows_pred_non_swallow_swallow_abstain':matrix.tolist(),
            'abstentions_by_true_class':{'non_swallow':int(matrix[0,2]),'swallow':int(matrix[1,2])},
            'accepted_correct_fraction_of_all_windows':float((matrix[0,0]+matrix[1,1])/len(y)),
            'accepted_int8_metrics':None,'accepted_float_metrics':None,'accepted_f1_ci':None,
            'max_probability_error_accepted':None,'p99_probability_error_accepted':None,
            'threshold_agreement_accepted':None}
    if n:
        error=np.abs(f[accepted]-q[accepted]);fp=(f[accepted]>=.5).astype(int);qp=(q[accepted]>=.5).astype(int)
        report.update(accepted_int8_metrics=binary_metrics(y[accepted],qp),
                      accepted_float_metrics=binary_metrics(y[accepted],fp),
                      accepted_f1_ci=cluster_f1_ci(y[accepted],qp,s[accepted],iterations=bootstrap),
                      max_probability_error_accepted=float(error.max()),
                      p99_probability_error_accepted=float(np.quantile(error,.99)),
                      threshold_agreement_accepted=float(np.mean(fp==qp)))
    return report


def select_candidate(validation_reports, *, minimum_coverage=.95,max_error=.05,
                     minimum_agreement=.99,max_f1_loss=.01,max_bytes=100000):
    eligible=[]
    for name,item in validation_reports.items():
        r=item['validation'];q=r['accepted_int8_metrics'];f=r['accepted_float_metrics']
        if q is None or f is None:continue
        if (r['coverage']>=minimum_coverage and r['max_probability_error_accepted']<=max_error
            and r['threshold_agreement_accepted']>=minimum_agreement and f['f1']-q['f1']<=max_f1_loss
            and item['model_bytes']<max_bytes):
            eligible.append(name)
    if not eligible:return None
    return min(eligible,key=lambda name:(-validation_reports[name]['validation']['coverage'],
        validation_reports[name]['validation']['p99_probability_error_accepted'],
        validation_reports[name]['calibration_count'],name))
