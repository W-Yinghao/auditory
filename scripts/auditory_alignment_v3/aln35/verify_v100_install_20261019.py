"""Read-only installation verification inside an existing Slurm allocation."""
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path

assert os.environ.get('SLURM_JOB_ID')
ROOT = Path('/home/infres/yinwang/EEG_auditory')
os.chdir(ROOT)
os.umask(0o077)
BASE = ROOT / 'private/auditory_alignment_v3/aln35'

def read(path):
    return json.loads(Path(path).read_text())

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

from private.auditory_alignment_v3.aln35 import maintain_fleet_v2 as F
from auditory_alignment_v3.aln35 import matched_resume_v2 as M

M.verify()
preflight = read(BASE / 'v100_20261019/routing_check.json')
assert preflight['status'] == 'pass'
assert all(sha(p) == expected for p, expected in preflight['source_sha256'].items())
lanes = F.plugin_lanes()
assert not any(row['state'] == 'technical_error' for row in lanes)
matched = next(row for row in lanes if row['lane'] == 's35_matched')
assert matched['slots'] == 1 and matched['state'] == 'ready'
assert matched['submit'][0] == 'slurm/aln35_matched_resume_v2.sbatch'
assert F.E.v100_allowed('s35_matched')
assert 'V100' in F.E.route('s35_matched', {}, force_broad=True)['partitions']
assert 'P100' not in F.E.BROAD

audit = M.AUDIT
check = read(audit / 'checks/1050192.json')
assert check['status'] == 'pass' and check['continuation_exact']
assert check['source_sha256'] == sha(M.__file__)
eid = 'ALN35MAT_0e790ab87996d266'
recovery = read(audit / 'executions/1050192' / (eid + '.json'))
assert recovery['status'] == 'complete' and recovery['checkpoint_before_sha256']
assert recovery['loader_sha256'] == sha(M.__file__)
assert recovery['result_sha256'] == sha(M.M.BASE / 'units' / (eid + '.json'))
assert 'V100' in recovery['device'] and '16GB' in recovery['device']
assert not (M.M.BASE / 'units' / (eid + '.FAILED.json')).exists()
history = list((audit / 'failure_history').glob(eid + '.*.json'))
assert len(history) == 1 and read(history[0]) == {'job': '1050185', 'returncode': 1}

original = read(M.M.BASE / 'units/ALN35MAT_10e691fc2a9ad197.json')
assert original['status'] == 'complete' and not original['probe']
assert original['job'] == '1050188' and 'V100' in original['device']
holds = ROOT / 'private/auditory_alignment_v3/governance/held_executions.json'
assert sha(holds) == 'c00b0e5ba35c9c6a846abbd53955260c6d4d04005bf5850adb19ddfcb26515c0'
jobs = F.E.query_jobs()
assert F.E.gpu_count(jobs) <= 10
assert not any(row['id'] == '1047289' for row in jobs)
assert any(row['id'] == '1047358' and row['state'] == 'RUNNING' for row in jobs)
assert (BASE / 'STOP_fleet_maintenance').exists()
assert not (BASE / 'STOP_fleet_maintenance_v2').exists()

receipt = {
    'status': 'pass', 'time': datetime.now().astimezone().isoformat(),
    'job': os.environ['SLURM_JOB_ID'], 'step': os.environ.get('SLURM_STEP_ID'),
    'provider': matched, 'gpu_rng_check': check, 'recovery': recovery,
    'preserved_failure': str(history[0]), 'hold_sha256': sha(holds),
    'new_start_on_v100': {k: original[k] for k in ('id', 'job', 'device', 'seconds', 'status')},
    'active_project_gpus': F.E.gpu_count(jobs),
    'project_gpu_jobs': [row for row in jobs if row['qos'] == 'runfill' and row['name'].startswith('c3_')],
    'compatibility': read(F.E.V100_POLICY),
    'source_sha256': {str(p): sha(p) for p in [Path(__file__), Path(M.__file__),
        ROOT / 'slurm/aln35_matched_resume_v2.sbatch', F.PLUGIN_PATH]},
}
target = BASE / 'v100_20261019/install_verification.json'
F.E.write(target, receipt)
print(json.dumps({'status': 'pass', 'receipt': str(target), 'GPU_count': receipt['active_project_gpus'],
                  'new_start': receipt['new_start_on_v100'], 'recovery': recovery['status'],
                  'provider': matched['submit'][0]}, indent=2), flush=True)
