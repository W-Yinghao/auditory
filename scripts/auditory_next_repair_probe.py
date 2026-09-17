"""Inspect the exact E0 adapter comparison, stopping before any transform fit."""
import json,os,sys
from pathlib import Path
import yaml
from auditory_next import repair
from auditory_next.provenance import ROOT,require_slurm
require_slurm();os.umask(0o077)
dest=ROOT/'private/auditory_next_v2/adapter_probe_002';dest.mkdir(mode=0o700)
registry=yaml.safe_load((ROOT/'configs/auditory_next_sources_v2.yaml').read_text())
inventory={r['path']:r['sha256'] for r in json.loads((ROOT/'private/auditory_next_v2/S0_001/legacy_input_hashes.json').read_text())}
class ProbeDone(Exception):pass
def trace(frame,event,arg):
    if event=='line' and frame.f_code.co_name=='_prepare_e' and 'original' in frame.f_locals:
        a=frame.f_locals;old=a['original'];new=a['scope']
        result=dict(record=a['rid'],fold=a['fold'],old_scope=vars(old['scope']),new_scope=vars(new),
                    old_hash=old['scope'].hash,new_hash=new.hash,within_type=str(type(old['within_record_only'])),
                    within_value=str(old['within_record_only']),within_is_true=old['within_record_only'] is True)
        (dest/'probe.json').write_text(json.dumps(result,indent=2,default=str))
        sys.settrace(None);raise ProbeDone()
    return trace
sys.settrace(trace)
try:repair._prepare_e(dest/'cases',registry,inventory,{})
except ProbeDone:print(json.dumps(dict(status='PASS',head_fits=0,stopped_before_transforms=True,job_id=os.environ['SLURM_JOB_ID'])))
