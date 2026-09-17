"""One Slurm-only schema diagnosis; no fitting or source mutations."""
import json,pickle,os
from pathlib import Path
import numpy as np
import pandas as pd
from auditory5.provenance import require_slurm,ROOT
from auditory5.contracts import FitScope
from auditory5.routes.route_e import block_folds
require_slurm()
os.umask(0o077)
dest=ROOT/'private/auditory_next_v2/adapter_probe_001';dest.mkdir(mode=0o700)
legacy=ROOT/'private/auditory5_v1/routes/E0_native_003'
support=pd.read_parquet(legacy/'support.parquet');record=support.loc[support.status.eq('PASS'),'record_id'].iloc[0]
events=pd.read_parquet(ROOT/'private/auditory5_v1/data/mff_e0_export_001/P1_CAUSAL20'/record/'events.parquet')
accepted=events[events.accepted].reset_index(drop=True);keep,folds=block_folds(accepted);rows=accepted.loc[keep].reset_index(drop=True)
groups=rows.filter_block_id.to_numpy(str);tr,te=folds[0]
new=FitScope(tuple(np.unique(groups[tr])),test_groups=tuple(np.unique(groups[te])))
with (legacy/f'{record}_linear_fold0.pkl').open('rb') as f:old=pickle.load(f)
result=dict(record=record,dtype=str(rows.filter_block_id.dtype),new_scope=vars(new),old_scope=vars(old['scope']),
            old_hash=old['scope'].hash,new_hash=new.hash,within_record_only=old['within_record_only'],
            model_fields=list(vars(old['model'])),model_scope=old['model'].fit_scopes)
with (dest/'probe.json').open('x') as f:json.dump(result,f,default=str,indent=2)
print(json.dumps(dict(status='PASS',job_id=os.environ['SLURM_JOB_ID'],scope_equal=new.hash==old['scope'].hash,head_fits=0)))
