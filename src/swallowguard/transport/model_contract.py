"""Block accidental reuse of a D4 three-channel model on Rev-A two-channel AFE."""
from dataclasses import dataclass

@dataclass(frozen=True)
class InputContract:
    channels:tuple[str,...]
    sample_hz:int
    window_samples:int
    domain:str
    preprocessing_id:str

D4_R3=InputContract(('throat_sound','upper_emg','lower_emg'),2000,4000,'D4_v2','D4_v2_R3_bounded')
REVA_RAW=InputContract(('pvdf','semg'),8000,16000,'prototype_RevA','raw_counts_uncalibrated')

def mismatch_reasons(observed,required=D4_R3):
    if not isinstance(observed,InputContract) or not isinstance(required,InputContract):
        raise ValueError('Explicit input contracts required')
    return tuple(name for name in ('channels','sample_hz','window_samples','domain','preprocessing_id')
                 if getattr(observed,name)!=getattr(required,name))

def require_compatible(observed,required=D4_R3):
    reasons=mismatch_reasons(observed,required)
    if reasons:raise ValueError('Model input contract mismatch: '+', '.join(reasons))
    # Metadata compatibility is necessary only, not model/quality acceptance.
    return True
