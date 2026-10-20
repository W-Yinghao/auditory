"""CPU-only registration of immutable analysis descriptors; no GPU action."""
import ast
import hashlib
import json
import os
from pathlib import Path
from private.auditory_alignment_v3.aln35 import evidence_refresh as E

assert os.environ.get('SLURM_JOB_ID')
tasks = {
    'fusion':dict(args=['-m','auditory_alignment_v3.aln35.fusion_attribution'],
                  sources=['private/auditory_alignment_v3/aln34/strong_fusion_v1/units/ALN*.json']),
    'attention':dict(args=['-m','auditory_alignment_v3.aln35.attention_sensitivity'],
                     sources=['private/auditory_alignment_v3/aln34/attention_transfer_v1/units/ALN*.json']),
    'cbstate':dict(args=['-m','auditory_alignment_v3.aln35.cb_audio_state','report'],
                   sources=['private/auditory_alignment_v3/aln34/cb_auditory_v1/units/ALN*.json'],
                   requires=['private/auditory_alignment_v3/aln35/cb_audio_state_v1/complete.json']),
    'bridge':dict(args=['-m','auditory_alignment_v3.aln35.bridge_factor_analyze'],
                  sources=['private/auditory_alignment_v3/aln35/bridge/extract_receipts/*.json'],minimum_files=4,
                  requires=['private/auditory_alignment_v3/aln35/bridge/analysis_contract.json'])
}
value = E.read(E.CONFIG) if E.CONFIG.exists() else {'version':1, 'tasks':{}}
for name, task in tasks.items():
    path=E.ROOT/(task['args'][1].replace('.','/')+'.py')
    task.update(module_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),interval_seconds=1800)
    if name in value['tasks']: assert value['tasks'][name]==task, 'descriptor changed: '+name
    value['tasks'][name]=task
    E.validate_task(task)
for name in ('evidence_refresh.py','milestone_monitor_v12.py'):
    ast.parse((E.BASE/name).read_text())
E.write(E.CONFIG, value)
receipt={'status':'pass','job':os.environ['SLURM_JOB_ID'],'config':value,
         'legacy_monitor_sha256':hashlib.sha256((E.ROOT/'private/auditory_alignment_v3/aln34/milestone_monitor_v11.py').read_bytes()).hexdigest(),
         'new_monitor_sha256':hashlib.sha256((E.BASE/'milestone_monitor_v12.py').read_bytes()).hexdigest()}
E.write(E.BASE/('evidence_setup_'+os.environ['SLURM_JOB_ID']+'.json'), receipt)
print('PASS: old evidence logic retained, new finite analysis refresh registered', flush=True)
