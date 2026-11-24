"""HRCA array contract; file parser/participant map await archive inspection."""
import numpy as np
from swallowguard.contracts import Recording,Source


def from_verified_array(values, *, subject_id, session_id, recording_id, schema_verified):
    if not schema_verified:
        raise ValueError('Inspect real array storage and participant map first')
    values=np.asarray(values,dtype=float)
    r=Recording('D1',subject_id,session_id,recording_id,Source.REPLAY,4000,
                np.arange(len(values))*250.,values,('microphone','AP','SI','ML'))
    r.validate()
    return r
