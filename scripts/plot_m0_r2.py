"""Plot aggregate R2 results only. Requires optional matplotlib; no waveforms."""
import argparse
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('ablation');p.add_argument('quantization');p.add_argument('linear');p.add_argument('sound');p.add_argument('emg');p.add_argument('output')
    a=p.parse_args();ab=json.load(open(a.ablation));q=json.load(open(a.quantization));linear=json.load(open(a.linear))
    sound=json.load(open(a.sound));emg=json.load(open(a.emg))
    fig,axes=plt.subplots(1,2,figsize=(12.5,4.5),layout='constrained')
    for offset,model,color,label in [(-.08,'logistic_regression','#1967a3','Logistic regression'),(.08,'random_forest','#d47721','Random forest')]:
        values=[ab['results'][name+'/'+model] for name in ['sound_only','emg_only','paired_sound_emg']]
        means=np.array([v['pooled_oof']['f1'] for v in values]);low=np.array([v['subject_cluster_f1_ci']['low'] for v in values]);high=np.array([v['subject_cluster_f1_ci']['high'] for v in values])
        axes[0].errorbar(np.arange(3)+offset,means,yerr=np.vstack((means-low,high-means)),fmt='o',capsize=4,color=color,label=label)
    axes[0].set_xticks(range(3),['Sound','EMG','Paired sound + EMG']);axes[0].set_ylim(.65,1.01)
    axes[0].set_ylabel('Pooled out-of-fold event F1');axes[0].set_title('26 training participants, 5 grouped folds')
    axes[0].legend(loc='lower right',fontsize=8);axes[0].grid(axis='y',alpha=.2)
    names=list(q['validation']);errors=[q['validation'][name]['validation']['max_probability_error_accepted'] for name in names]
    errors.extend(d['validation']['max_probability_error_accepted'] for d in [linear,sound,emg])
    labels=['CNN\n256','CNN\n512','CNN\nall','Linear\npaired','Linear\nsound','Linear\nEMG']
    axes[1].bar(range(6),errors,color=['#b24b3e']*6,width=.65)
    axes[1].axhline(.05,color='#333333',linestyle='--',label='Frozen parity limit: 0.05')
    axes[1].set_xticks(range(6),labels);axes[1].set_ylim(0,1)
    axes[1].set_ylabel('Maximum absolute probability error');axes[1].set_title('Validation: accepted inputs only')
    axes[1].legend(loc='upper right',fontsize=8)
    for j,error in enumerate(errors):axes[1].text(j,error+.02,f'{error:.3f}',ha='center',fontsize=9)
    fig.suptitle('SWALLOWGUARD M0 — exploratory research; no clinical validation',fontsize=12)
    fig.savefig(a.output)


if __name__=='__main__':main()
