"""Post-completion rendering only; preserves the frozen numerical aggregate."""
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

assert os.environ.get('SLURM_JOB_ID')
root=Path('/home/infres/yinwang/EEG_auditory')
res=root/'results/auditory_alignment_v3/aln34/causal_filter'
path=res/'efficacy.json';value=json.loads(path.read_text())
assert value['status']=='complete' and value['tasks_complete']==10 and value['complete_paired_people']==44
digest=hashlib.sha256(path.read_bytes()).hexdigest()
doc=root/'docs/auditory_alignment_v3/CAUSAL_FILTER_BOUNDARY_RESULTS.md'
backup=root/'private/auditory_alignment_v3/aln34/CAUSAL_FILTER_BOUNDARY_RESULTS.original_format_20261017.md'
if not backup.exists():shutil.copy2(doc,backup)
labels=value['cells'];r=value['families']['r'];m=value['families']['mse']

fig,ax=plt.subplots(2,2,figsize=(10,6.5),sharex=True,layout='constrained')
for col,guard in enumerate(('0.5','2.0')):
    ix=[i for i,k in enumerate(labels) if k.startswith(guard+'/')]
    x=np.array([int(labels[i].split('/')[1]) for i in ix])
    for variant,label,color in (('zero_phase','Forward/backward','#38598b'),('causal_cascade','Causal cascade','#c44e52')):
        stat=r['all'][variant];y=np.array(stat['est'])[ix]
        ax[0,col].plot(x,y,'o-',color=color,label=label)
        ax[0,col].fill_between(x,np.array(stat['band_low'])[ix],np.array(stat['band_high'])[ix],color=color,alpha=.14)
    stat=r['all']['causal_benefit'];y=np.array(stat['est'])[ix]
    ax[1,col].errorbar(x,y,yerr=[y-np.array(stat['band_low'])[ix],np.array(stat['band_high'])[ix]-y],fmt='o-',color='#555555',capsize=3)
    ax[1,col].axhline(0,color='black',lw=.8,alpha=.5)
    ax[0,col].set_title(f'{guard} s physical-trial guard')
    ax[1,col].set_xlabel('EEG window start relative to sound (ms)')
    for a in ax[:,col]:a.grid(alpha=.2);a.set_xticks(x)
ax[0,0].set_ylabel('Envelope decoding Pearson r')
ax[1,0].set_ylabel('Causal minus forward/backward r')
ax[0,0].legend(frameon=False,fontsize=9)
fig.suptitle('Native DTU filter sensitivity: 44 paired listeners\n3-sample EEG window; offline normalization retained',fontsize=12)
fig.savefig(res/'filter_comparison.png',dpi=180);fig.savefig(res/'filter_comparison.pdf');plt.close(fig)

lines=['# Native DTU filter and boundary sensitivity','',
       f"Complete:10/10fold tasks,44/44 paired listeners. Numerical snapshot {value['time']}; report rendered {datetime.now().astimezone().isoformat()}.",'',
       'The new native-BDF pipelines use two forward Butterworth passes or forward/backward filtering with the same interior magnitude response. No causal filter delay is compensated. Both retain the original sound envelope and offline whole-recording channel normalization. Thus this is a filter/boundary sensitivity, not an online-causal pipeline, a neural latency measurement, or a test of the absence of auditory information. The3-sample EEG window is23.4375ms at128Hz. Five person folds and two content folds do not increase the independent sample size.','',
       'All10guard×lag cells are reported. Means first combine the two content folds within each identity.4000identity bootstrap-t intervals are simultaneous across the10cells within each metric/contrast family; separate model-level bands and difference bands are not interchangeable. Positive r benefit means causal minus forward/backward correlation. Positive MSE benefit means forward/backward minus causal loss, in the original envelope-squared units. No test-selected time, group, model or sign is substituted.','',
       '![Paired filter sensitivity](../../results/auditory_alignment_v3/aln34/causal_filter/filter_comparison.png)','',
       '| Guard / lag(ms) | Forward/backward r | Causal r | Paired difference | Simultaneous95% interval |',
       '|---|---:|---:|---:|---|']
for i,k in enumerate(labels):
    a=r['all']['zero_phase'];b=r['all']['causal_cascade'];d=r['all']['causal_benefit']
    lines.append(f"| {k} | {a['est'][i]:.5f} | {b['est'][i]:.5f} | {d['est'][i]:+.5f} | [{d['band_low'][i]:+.5f}, {d['band_high'][i]:+.5f}] |")
lines+=['','| Guard / lag(ms) | MSE benefit | Simultaneous95% interval |','|---|---:|---|']
d=m['all']['causal_benefit']
for i,k in enumerate(labels):lines.append(f"| {k} | {d['est'][i]:+.4e} | [{d['band_low'][i]:+.4e}, {d['band_high'][i]:+.4e}] |")
lines+=['','| Guard / lag(ms) | HI minus NH difference in r intervention effect | Simultaneous95% interval |','|---|---:|---|']
d=r['hi_minus_nh_effect']
for i,k in enumerate(labels):lines.append(f"| {k} | {d['est'][i]:+.5f} | [{d['band_low'][i]:+.5f}, {d['band_high'][i]:+.5f}] |")
lines+=['','The full JSON also retains each hearing group and both model-level families. A crossing-zero interval is uncertainty about this declared contrast, not equivalence. Changes at fixed lags may reflect the causal filter phase/delay and boundary treatment; they cannot isolate a neural source or turn positive-minus-negative decoding into pure neural information.','',
        'Rendering provenance: the frozen experiment and numerical JSON are unchanged. The first report rounded native MSE differences to five decimals; this version uses scientific notation and adds levels, the direct group interaction and a figure. Original rendering retained under the private ALN3.4 directory.',
        f'Numerical JSON SHA256 `{digest}`; plan SHA256 `{value["plan_sha256"]}`; rendering job `{os.environ["SLURM_JOB_ID"]}`.']
doc.write_text('\n'.join(lines)+'\n')
receipt={'time':datetime.now().astimezone().isoformat(),'job':os.environ['SLURM_JOB_ID'],'status':'complete','numeric_sha256':digest,
         'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'doc_sha256':hashlib.sha256(doc.read_bytes()).hexdigest()}
(res/'render_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
assert hashlib.sha256(path.read_bytes()).hexdigest()==digest
print('Rendered complete causal filter report, unchanged numerical SHA',digest,flush=True)
