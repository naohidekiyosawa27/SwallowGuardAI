"""Five-fold participant CV on original training participants only.

Fixed conventional baselines and actual paired acoustic/EMG feature ablations.
No test/validation subjects enter any fold; this is an exploratory robustness
study, not a fresh external performance estimate or deployment-model selection.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from swallowguard.evaluate.metrics import binary_metrics,cluster_f1_ci


def evaluate(features,labels,subjects,*,folds=5,bootstrap=1000):
    x,y,s=map(np.asarray,(features,labels,subjects))
    if x.ndim!=2 or x.shape[1]!=15 or y.shape!=(len(x),) or s.shape!=y.shape or not np.isfinite(x).all() or not np.isin(y,[0,1]).all():
        raise ValueError('Require documented D4 fifteen-feature layout')
    if len(set(s))<folds or any(not str(subject).strip() for subject in s):raise ValueError('Not enough identified participant groups')
    partitions=list(GroupKFold(n_splits=folds).split(x,y,groups=s))
    reports={}
    for name,columns in {'sound_only':slice(0,5),'emg_only':slice(5,15),'paired_sound_emg':slice(0,15)}.items():
        for baseline in ['logistic_regression','random_forest']:
            oof=np.full(len(y),-1,dtype=int);fold_reports=[]
            for train,test in partitions:
                if set(s[train])&set(s[test]):raise ValueError('Participant leakage')
                model=(make_pipeline(StandardScaler(),LogisticRegression(class_weight='balanced',random_state=2026,max_iter=1000))
                       if baseline=='logistic_regression' else RandomForestClassifier(n_estimators=50,max_depth=5,class_weight='balanced',random_state=2026,n_jobs=1))
                model.fit(x[train,columns],y[train]);oof[test]=model.predict(x[test,columns])
                fold_reports.append({'training_participants':len(set(s[train])),'test_participants':len(set(s[test])),
                                     'test_windows':len(test),**binary_metrics(y[test],oof[test])})
            if np.any(oof<0):raise ValueError('Incomplete out-of-fold predictions')
            reports[name+'/'+baseline]={'folds':fold_reports,'pooled_oof':binary_metrics(y,oof),
                'subject_cluster_f1_ci':cluster_f1_ci(y,oof,s,iterations=bootstrap),
                'fold_f1_min':min(f['f1'] for f in fold_reports),'fold_f1_max':max(f['f1'] for f in fold_reports)}
    return reports


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('features',type=Path);p.add_argument('original_evaluation',type=Path);p.add_argument('output',type=Path)
    a=p.parse_args();original=json.loads(a.original_evaluation.read_text())
    with np.load(a.features,allow_pickle=False) as d:
        if str(d['dataset_id'].item())!='D4_v2' or str(d['source'].item())!='replayed_research':raise ValueError('D4 provenance required')
        mask=np.isin(d['subjects'],original['split']['train']);x,y,s=d['X'][mask],d['y'][mask],d['subjects'][mask]
    report={'mode':'RESEARCH MODE','dataset':'D4_v2','scope':'original 26 training participants only',
            'participants':len(set(s)),'windows':len(y),'folds':5,'clinical_validation':False,
            'feature_sha256':hashlib.sha256(a.features.read_bytes()).hexdigest(),'results':evaluate(x,y,s),
            'limitations':['Prior data/model exploration means these are exploratory estimates',
                           'Publisher event clips only; no continuous false-alarm metrics',
                           'No optical/respiratory/actual-prototype channel is included',
                           'This study does not change the validation-selected M01 reference']}
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
