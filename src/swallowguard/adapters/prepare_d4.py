"""Build M0 feature table from locally authorized D4 v2 clips (no downloads).

Root is the extracted archive directory containing Processed_2s_Clips/.
Keep its input and output on a secure local research workstation.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import numpy as np
from swallowguard.adapters.d4 import load_clip
from swallowguard.preprocess.signals import bandpass,resample,emg_envelope,window_features
from swallowguard.train.splits import subject_split


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('root',type=Path);p.add_argument('manifest',type=Path);p.add_argument('output',type=Path)
    p.add_argument('--waveforms',type=Path,help='Optional N x 4000 x 3 synchronous 2-kHz waveform table')
    a=p.parse_args();root=a.root.resolve()
    with a.manifest.open() as h:rows=list(csv.DictReader(h))
    if not rows:raise ValueError('Empty clip manifest')
    # Split participants before our preprocessing/feature extraction. Publisher
    # presegmentation is immutable; their QC selection bias remains a limitation.
    split=subject_split([r['participant_id'] for r in rows])
    features=[];labels=[];subjects=[];hashes=[];waveforms=[];seen={};excluded_duplicates=0
    for row in rows:
        path=(root/row['relative_path']).resolve()
        if not path.is_relative_to(root):raise ValueError('Manifest path escapes data root')
        recording,y=load_clip(path,row)
        waveform_hash=hashlib.sha256(recording.values.tobytes()).hexdigest()
        if waveform_hash in seen:
            if seen[waveform_hash]!=(recording.subject_id,y):
                raise ValueError('Identical waveform crosses subjects or conflicts in label')
            excluded_duplicates+=1
            continue
        seen[waveform_hash]=(recording.subject_id,y)
        # Independent per-recording filters, with no learned statistics here.
        # These are candidate bands, not a domain-validated signal transformation.
        sound=resample(bandpass(recording.values[:,:1],20000,100,3000),20000,2000)
        emg=emg_envelope(recording.values[:,1:],fs=20000,output_fs=200)
        if a.waveforms:
            # Retain three physically paired channels at a common 2-kHz rate.
            # Crop the inclusive 2-second endpoint from 4001 to 4000 explicitly.
            emg_raw=resample(bandpass(recording.values[:,1:],20000,20,450),20000,2000)
            waveforms.append(np.column_stack((sound[:4000],emg_raw[:4000])).astype(np.float32))
        features.append(np.concatenate([window_features(sound),window_features(emg)]))
        labels.append(y);subjects.append(recording.subject_id)
        hashes.append({'clip_id':row['clip_id'],'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
        if len(features)%500==0:print(f'Processed {len(features)}/{len(rows)} clips',flush=True)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    np.savez_compressed(a.output,X=np.asarray(features),y=np.asarray(labels),subjects=np.asarray(subjects),
                        source=np.array('replayed_research'),dataset_id=np.array('D4_v2'))
    a.output.with_suffix('.provenance.json').write_text(json.dumps({
        'stage':'M0','split':split,'files':hashes,'excluded_identical_duplicates':excluded_duplicates,
        'retained_clips':len(features),'manifest_sha256':hashlib.sha256(a.manifest.read_bytes()).hexdigest(),
        'preprocess':'candidate-0.3.0','source':'replayed_research',
        'limitations':['Publisher PASS clips only; continuous detection untested',
                       'No physiological full-scale calibration or raw QC reproduction',
                       'Healthy participants only; no clinical endpoint']},indent=2)+'\n')
    if a.waveforms:
        a.waveforms.parent.mkdir(parents=True,exist_ok=True)
        np.savez_compressed(a.waveforms,X=np.asarray(waveforms),y=np.asarray(labels),subjects=np.asarray(subjects),
                            source=np.array('replayed_research'),dataset_id=np.array('D4_v2'))


if __name__=='__main__':main()
