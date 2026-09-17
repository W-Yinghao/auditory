"""Clarify the clinical baseline in HA figure labels; no statistics changed."""
import json,os,shutil
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
BASE=Path(__file__).resolve().parents[1]
assert os.getenv('SLURM_JOB_ID');os.umask(0o077)
out=BASE/'figures/phase3_final';out.mkdir(exist_ok=False)
a=json.loads((BASE/'results/phase3_ha_science_001/summary.json').read_text());b=json.loads((BASE/'results/phase3_ha_sensitivity_001/summary.json').read_text())
rows=[(r['model'],r['MAE']) for r in a['targets_models'] if r['target']=='MUSS']+[(r['model'],r['MAE']) for r in b['models'] if r['model'] in ['clinical_age_duration','post_separate_penalty','pre_separate_penalty']]
labels=['Clinical: age + log(use) + PTA','Clinical + fixed EEG amplitude','Clinical + poststimulus EEG: shared penalty','Clinical + prestimulus EEG: shared penalty','Age + log(use) only','Clinical + poststimulus EEG: separate penalties','Clinical + prestimulus EEG: separate penalties']
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42})
fig,ax=plt.subplots(figsize=(9,4.7),layout='constrained');ax.barh(labels,[v for k,v in rows],color=['#355c7d','#6b8eab','#aa4b4b','#c69797','#355c7d','#568b72','#9fb8aa']);ax.invert_yaxis()
for i,(k,v) in enumerate(rows):ax.text(v+.12,i,f'{v:.2f}',va='center')
ax.set(xlabel='MUSS mean absolute error (lower is better)',xlim=(0,16),title='HA: same 50 candidates, repeated nested validation\nSeparate penalties: sensitivity analysis after observing v1')
fig.savefig(out/'ha_clinical_increment.pdf');fig.savefig(out/'ha_clinical_increment.png',dpi=180);plt.close(fig);shutil.copy2(Path(__file__),out/Path(__file__).name)
print(json.dumps(dict(job_id=os.environ['SLURM_JOB_ID'],status='rendered_from_existing_statistics')))
