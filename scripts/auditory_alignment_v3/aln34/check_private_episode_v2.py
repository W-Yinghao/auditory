"""Validate immutable repair identities and compatible numerical reuse on Slurm CPU."""
import ast
import copy
import os
from pathlib import Path
from auditory_alignment_v3.aln34 import private_episode as Old, private_episode_v2 as New
from private.auditory_alignment_v3.aln34 import maintain_fleet_v13 as F, milestone_monitor_v10 as M
assert os.environ.get('SLURM_JOB_ID')
Old.verify(Old.read(Old.PLAN));New.verify(New.read(New.PLAN))
receipt=New.read(New.BASE/'compatibility_reuse.json')
assert len(receipt['records'])==1
unit=next(x for x in New.read(New.PLAN)['rows'] if (New.BASE/'units'/f"{x['id']}.json").exists())
record=New.read(New.BASE/'units'/f"{unit['id']}.json")
old=Old.read(record['reused_from']['record'])
assert Old.B.sha(record['reused_from']['record'])==record['reused_from']['record_sha256']
assert record['source_sha256']==old['source_sha256'] and record['job']==old['job']
def metrics(value):
    if isinstance(value,dict):return {k:metrics(v) for k,v in value.items() if k not in ('minimum_support_trials','requested_adapter_steps','effective_adapter_steps','identity_fallback_reason','insufficient_support_identity_fallback')}
    if isinstance(value,list):return [metrics(v) for v in value]
    return value
assert metrics(record['stages'])==old['stages']
assert metrics(record['choices'])==old['choices']
assert 'private_episode_v2' in M.LANES and 'private_episode_v1' not in M.LANES
assert F.CONFIG['private_episode'][1]=='private_episode_v2'
for p in ('private/auditory_alignment_v3/aln34/maintain_fleet_v13.py','private/auditory_alignment_v3/aln34/milestone_monitor_v10.py',
          'auditory_alignment_v3/aln34/private_episode_v2_aggregate.py'):
    ast.parse(Path(p).read_text())
print('PASS frozen identities; exact reused metrics and original execution identity; services and aggregator',flush=True)
from auditory_alignment_v3.aln34.private_episode_v2_aggregate import main
main()
