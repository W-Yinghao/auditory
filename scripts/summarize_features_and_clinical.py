import csv,json,os,hashlib,math
from pathlib import Path
from collections import Counter
import numpy as np
from scipy.io import loadmat
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
from audit_mff import dump,table,j
BASE=Path(__file__).resolve().parents[1]
assert os.environ.get('SLURM_JOB_ID')
out=BASE/'results/descriptive_002';out.mkdir(exist_ok=False);figs=BASE/'figures/descriptive_002';figs.mkdir(exist_ok=False)
mapping=list(csv.DictReader((BASE/'private/inventory_001/file_path_map.csv').open()));arrays=[]
for r in mapping:
 p=Path(r['absolute_path'])
 if p.suffix.lower()!='.mat':continue
 for k,x in loadmat(p).items():
  if k.startswith('__'):continue
  z=np.asarray(x);n=int(z.shape[0]);channels=(1+math.isqrt(1+8*n))//2;triangular=channels*(channels-1)//2==n
  arrays.append({'file_id':r['file_id'],'variable':k,'shape':j(z.shape),'dtype':str(z.dtype),'all_finite':bool(np.isfinite(z).all()),'min':float(np.nanmin(z)),'median':float(np.nanmedian(z)),'max':float(np.nanmax(z)),'first_dimension_equals_channel_pairs_for_n':channels if triangular else '', 'interpretation_status':'numeric_array_only_axes_unknown'})
table(out/'legacy_mat_arrays.csv',arrays)
clinical=list(csv.DictReader((BASE/'private/clinical_003/clinical_rows_clean.csv').open()));counts=Counter(r['candidate_key'] for r in clinical);ha=[r for r in clinical if r['group'].lower()!='nh'];nh=[r for r in clinical if r['group'].lower()=='nh']
fig,axs=plt.subplots(1,2,figsize=(10,4))
for rows,label,color in [(ha,'HA records','#277da1')]:
 axs[0].scatter([float(r['duration_months']) for r in rows],[float(r['age_months']) for r in rows],label=f'{label} (n={len(rows)})',s=22,alpha=.7,c=color)
 axs[1].scatter([float(r['duration_months']) for r in rows],[float(r['SIR']) for r in rows],label=label,s=22,alpha=.7,c=color)
axs[0].set(xlabel='Device-use months (source field)',ylabel='Age (months)',title='HA records; repeats retained');axs[0].legend(fontsize=7)
axs[1].set(xlabel='Device-use months (source field)',ylabel='SIR (ordinal)',title='HA clinical description; no EEG association');fig.suptitle('NH device-use duration is not applicable; NH not plotted',fontsize=9);fig.tight_layout();fig.savefig(figs/'age_use_sir.png',dpi=160);plt.close(fig)
# Duplicate references are verified on extracted text, not inferred from filenames.
refs=Counter()
for p in (BASE/'private/supporting_001').glob('file_*.txt'):
 if p.name.endswith(('.archive_listing.txt','.archive_errors.txt')):continue
 refs[hashlib.sha256(p.read_bytes()).hexdigest()]+=1
def strat(rows):return {'records':len(rows),'name_candidates':len(set(r['candidate_key'] for r in rows))}
ha60=[r for r in ha if 0<=float(r['duration_months'])<=60];repeated=[v for v in Counter(r['candidate_key'] for r in ha).values() if v>1]
dump(out/'summary.json',{'job_id':os.environ['SLURM_JOB_ID'],'mat_arrays':len(arrays),'primary':strat(clinical),'HA':strat(ha),'NH':strat(nh),'HA_0_60':strat(ha60),'HA_repeated_name_candidates':len(repeated),'HA_records_in_repeated_name_candidates':sum(repeated),'identical_reference_text_extra_copies':sum(n-1 for n in refs.values() if n>1),'notice':'Leading-name candidate counts are not identity confirmations. Pair-count-shaped MAT axes are a mathematical clue, not an established connectivity definition.'})
