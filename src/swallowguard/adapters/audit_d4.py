"""Audit authorized local D4 clips without exporting per-participant data."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
from collections import Counter
import numpy as np
from swallowguard.adapters.d4 import load_clip


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('root',type=Path);p.add_argument('manifest',type=Path);p.add_argument('output',type=Path)
    a=p.parse_args();root=a.root.resolve()
    with a.manifest.open() as h:rows=list(csv.DictReader(h))
    if not rows:raise ValueError('Empty manifest')
    hashes={};dups=Counter();flat=Counter();counts=Counter()
    for row in rows:
        path=(root/row['relative_path']).resolve()
        if not path.is_relative_to(root):raise ValueError('Manifest path escapes root')
        r,y=load_clip(path,row);h=hashlib.sha256(r.values.tobytes()).hexdigest()
        if h in hashes:
            subject,label=hashes[h]
            dups['across_subjects' if subject!=r.subject_id else 'within_subject']+=1
            if label!=y:raise ValueError('Identical waveforms have conflicting task labels')
        hashes[h]=(r.subject_id,y)
        for i,name in enumerate(r.channels):
            if np.std(r.values[:,i])<=1e-12:flat[name]+=1
        counts[row['activity']]+=1
    result={'dataset':'D4_v2','clips_checked':len(rows),
            'manifest_sha256':hashlib.sha256(a.manifest.read_bytes()).hexdigest(),
            'checks':['Shape, embedded rate, participant, session and activity match manifest','All values finite'],
            'class_counts':dict(counts),'flatline_channels_at_std_1e-12':dict(flat),
            'identical_waveform_duplicates':dict(dups),'full_scale_clipping_assessed':False,
            'raw_QC_reproduced':False,'clinical_labels':False}
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__':main()
