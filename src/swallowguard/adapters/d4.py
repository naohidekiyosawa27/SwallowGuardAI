"""D4 v2 processed-clip adapter. MAT schema documented; waveform not yet tested."""
import re
import numpy as np
from scipy.io import loadmat
from swallowguard.contracts import Recording, Source

ACTIVITIES = {"Fluid":1,"Saliva":1,"Solid":1,"Cough":0,"ThroatClearing":0}


def load_clip(path, manifest_row, *, source=Source.REPLAY):
    row = manifest_row
    participant,session = row['participant_id'],row['session_id']
    if not re.fullmatch(r"HSD\d{3}",participant) or not session.startswith(participant+'_S'):
        raise ValueError("Invalid D4 subject/session relationship")
    if row['activity'] not in ACTIVITIES or float(row['sampling_frequency_hz']) != 20000:
        raise ValueError("Unknown D4 class/rate")
    mat=loadmat(path)
    def scalar(value):
        while isinstance(value,np.ndarray):
            if value.size!=1:raise ValueError('Expected scalar MAT metadata')
            value=value.item()
        return value
    if float(scalar(mat['sampling_frequency_hz']))!=20000 or any(
        str(scalar(mat[key]))!=row[key] for key in ('participant_id','session_id','activity')
    ):
        raise ValueError('Embedded MAT metadata disagrees with manifest')
    data = np.asarray(mat['data'],dtype=float)
    if data.shape != (int(row['n_samples']),int(row['n_columns'])) or data.shape[1] != 3:
        raise ValueError("D4 schema differs from manifest; inspect before proceeding")
    r=Recording('D4_v2',participant,session,row['clip_id'],Source(source),20000,
                np.arange(len(data))*50.,data,('throat_sound','upper_emg','lower_emg'))
    r.validate()
    return r,ACTIVITIES[row['activity']]
