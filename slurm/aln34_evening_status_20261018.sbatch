#!/bin/bash
#SBATCH --job-name=c3_eveningstatus
#SBATCH --partition=CPU
#SBATCH --qos=normal
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=00:20:00
#SBATCH --output=private/auditory_alignment_v3/logs/aln34_eveningstatus-%j.log
set -euo pipefail
umask 077
cd "$SLURM_SUBMIT_DIR"
export PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$PWD"
export OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2
PY=/home/infres/yinwang/anaconda3/envs/eeg2025/bin/python
$PY -B - <<'PY'
import ast, json, os
from datetime import datetime
from pathlib import Path
from auditory_alignment_v3.aln34 import prior_private_loo as P
base = Path('private/auditory_alignment_v3/aln34')
original = (base/'replay_prior_loo_20261018.py').read_text()
expected = original.replace('ALN3X_5e2403355822478f','ALN3X_642554812e473fee').replace('Tesla V100-PCIE-16GB','Tesla V100S-PCIE-32GB').replace('device_replay_20261018','device_replay_20261018_evening').replace('matched V100 replay','matched V100S replay')
assert (base/'replay_prior_loo_v100s_20261018.py').read_text() == expected
ast.parse(expected)
plan = P.read(P.PLAN)
P.verify(plan)
eid = 'ALN3X_642554812e473fee'
row = next(r for r in plan['rows'] if r['experiment_id'] == eid)
source = P.read(P.SOURCE/'units'/f'{eid}.json')
failed = P.read(P.BASE/'units'/f'{eid}.json')
assert P.ready(row) and source['device'] == 'Tesla V100S-PCIE-32GB'
assert failed['status'] == 'reproduction_failed' and not failed['same_recorded_device']
assert (P.BASE/'units'/f'{eid}.FAILED.json').is_file()
for name in ('runtime_audit', 'runtime_forecast'):
    original = (base/f'{name}_20261018.py').read_text()
    expected = original.replace('runtime_audit_20261018.json','runtime_audit_20261018_evening.json').replace('runtime_forecast_20261018.json','runtime_forecast_20261018_evening.json')
    assert (base/f'{name}_20261018_evening.py').read_text() == expected
    ast.parse(expected)
pending_devices = {}
for r in plan['rows']:
    path=P.BASE/'units'/f"{r['experiment_id']}.json"
    if path.exists() and P.read(path).get('status')=='complete':
        continue
    dev=P.read(P.SOURCE/'units'/f"{r['experiment_id']}.json")['device']
    pending_devices[dev]=pending_devices.get(dev,0)+1
receipt={'status':'PASS','job':os.environ['SLURM_JOB_ID'],'time':datetime.now().astimezone().isoformat(),'unit':eid,'plan_sha256':P.sha(P.PLAN),'driver_sha256':P.sha(base/'replay_prior_loo_v100s_20261018.py'),'source_device':source['device'],'prior_failed_device':failed['device'],'unchanged_tolerance':P.L.REPRO_TOL,'remaining_by_source_device':pending_devices}
P.write(base/'evening_replay_preflight_20261018.json',receipt)
print(json.dumps(receipt),flush=True)
PY
bash -n slurm/aln34_prior_loo_replay_v100s_20261018.sbatch
$PY -B -u private/auditory_alignment_v3/aln34/runtime_audit_20261018_evening.py
$PY -B -u private/auditory_alignment_v3/aln34/runtime_forecast_20261018_evening.py
