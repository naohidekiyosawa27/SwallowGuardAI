"""Plot aggregate validation decisions; no participant rows or waveforms."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

root=Path(__file__).resolve().parents[1]
r=json.loads((root/'reports/M0_R3_RESULTS.json').read_text())['reports']
names=list(r)
fig,axes=plt.subplots(1,3,figsize=(12,4.4))
colors=['#17816a' if r[n]['accuracy_and_numerical_criteria_passed'] else '#bc493e' for n in names]
measures=[('coverage','Validation coverage',.95),('max_probability_error_accepted','Max |INT8 − float shadow|',.05),('threshold_agreement_accepted','Threshold agreement',.99)]
for ax,(key,title,gate) in zip(axes,measures):
    values=[r[n]['validation'][key] for n in names]
    bars=ax.barh(names[::-1],values[::-1],color=colors[::-1])
    ax.axvline(gate,color='#27354b',ls='--',label=f'Gate {gate:g}')
    for bar,value in zip(bars,values[::-1]):
        ax.text(value+.008 if key!='max_probability_error_accepted' else value+.0006,bar.get_y()+bar.get_height()/2,f'{value:.4f}',va='center',fontsize=9)
    ax.set_title(title,fontsize=11);ax.spines[['top','right']].set_visible(False)
    ax.set_xlim(0,1.22 if key!='max_probability_error_accepted' else .064)
    ax.legend(loc='lower right',fontsize=8)
fig.suptitle('M0-R3: three candidates pass; waveform QAT selected',fontsize=14,fontweight='bold')
fig.text(.5,.025,'602 validation clips / 6 participants • reused development split • numerical gates, no clinical validation',ha='center',fontsize=9)
fig.tight_layout(rect=(0,.08,1,.93))
fig.savefig(root/'reports/M0_R3_summary.svg')
