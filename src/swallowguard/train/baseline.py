"""Runnable M0 baseline comparison on canonical feature tables, split by subject.

NPZ input: X (N,F), y (N), subjects (N), source (scalar), dataset_id (scalar).
Features must be computed per recording AFTER subject assignment by the adapter.
Raw waveforms stay outside this repository. No pickle/object arrays are accepted.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from swallowguard.train.splits import subject_split
from swallowguard.evaluate.metrics import binary_metrics, cluster_f1_ci


def run(x, y, subjects, *, source, dataset_id, seed=2026, return_model=False):
    if source not in {"synthetic", "replayed_research", "live_bench"} or not dataset_id:
        raise ValueError("Explicit dataset provenance required")
    x,y,subjects = np.asarray(x),np.asarray(y),np.asarray(subjects)
    if x.ndim != 2 or len(x) != len(y) or subjects.shape != y.shape or y.ndim != 1 or not np.isfinite(x).all() or not np.isin(y,[0,1]).all():
        raise ValueError("Invalid canonical feature table")
    split = subject_split(subjects,seed=seed)
    ids = {k: np.flatnonzero(np.isin(subjects,v)) for k,v in split.items()}
    if set(y[ids['train']]) != {0,1}:
        raise ValueError("Both event classes required in training")
    candidates = {
        "logistic_regression": make_pipeline(StandardScaler(), LogisticRegression(class_weight="balanced",random_state=seed,max_iter=1000)),
        "random_forest": RandomForestClassifier(n_estimators=50,max_depth=5,class_weight="balanced",random_state=seed,n_jobs=1)}
    scores = {}
    for name, model in candidates.items():
        model.fit(x[ids['train']],y[ids['train']])
        scores[name] = binary_metrics(y[ids['validation']],model.predict(x[ids['validation']]))
    chosen = max(scores, key=lambda name: scores[name]['f1'])
    test = ids['test']
    pred = candidates[chosen].predict(x[test])
    report = {"stage":"M0", "mode":"RESEARCH MODE", "source":source,"dataset_id":dataset_id,
              "synthetic_only":source == "synthetic", "seed":seed, "split":split,
              "validation":scores,"selected":chosen,"test":binary_metrics(y[test],pred),
              "test_subject_cluster_f1_ci":cluster_f1_ci(y[test],pred,subjects[test]),
              "failure_cases":[{"row":int(i),"subject":str(subjects[i]),"truth":int(y[i]),"pred":int(p)}
                               for i,p in zip(test,pred) if y[i] != p],
              "limitations":["Window event classification only", "No continuous event timing or false events/min evaluated",
                             "No clinical endpoint", "Small subject counts yield unstable CIs"]}
    return (report,candidates[chosen]) if return_model else report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("input",type=Path);p.add_argument("output",type=Path)
    p.add_argument("--model-output",type=Path,help="Persist locally generated trusted sklearn reference model")
    args = p.parse_args()
    with np.load(args.input,allow_pickle=False) as d:
        report,model = run(d['X'],d['y'],d['subjects'],source=str(d['source'].item()),dataset_id=str(d['dataset_id'].item()),return_model=True)
    report['input_sha256'] = hashlib.sha256(args.input.read_bytes()).hexdigest()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2)+"\n")
    if args.model_output:
        import joblib
        args.model_output.parent.mkdir(parents=True,exist_ok=True)
        joblib.dump(model,args.model_output)


if __name__ == "__main__":
    main()
