"""Resolve the four 17:17-17:19 technical failures (uncorrectable GPU ECC error) so fleet v3 resumes the tails.

Slurm only. Researcher 2026-10-20: "没有要提交的GPU任务了吗". All four lanes stopped at once after preemption requeues
landed on faulty GPU memory; each attempt died 10-39 s after START with "CUDA error: uncorrectable ECC error encountered".
For each unit this verifies the marker, the log line, that no unit result exists, that no checkpoint/ledger/claim file was
written after the failing attempt started (the resumable state predates it, from healthy preempted runs), and that no
worker holds the claim lock. The marker is then preserved (copy + rename, as in replay_prior_loo_20261018) under
<lane>/technical_failures/ecc_20261020/ with the log excerpt; no plan, row, trainer, checkpoint or record is changed.
"""
import fcntl
import hashlib
import json
import os
import shutil
from datetime import datetime
from pathlib import Path

assert os.environ.get('SLURM_JOB_ID'), 'Slurm required'
L3 = Path('/home/infres/yinwang/EEG_auditory/private/auditory_alignment_v3')
P3 = Path('<private checkpoint storage>/auditory_alignment_v3')
LOGS = L3 / 'logs'
FAILURES = [  # lane, unit, failing job, worker log, START of the failing attempt
    ('learning_budget_v2', 'ALN34B2_367d96143295a220', '1051935', 'c3_aln34budget-1051935.log', '2026-10-20T17:17:03.302603+02:00'),
    ('data_inner_v1', 'ALN34S_ef9d78b1332eddcc', '1052131', 'c3_datacurve34-1052131.log', '2026-10-20T17:17:40.018531+02:00'),
    ('breadth_budget_v1', 'ALN34BB_1de61568b957192e', '1051061', 'c3_br_budget-1051061.log', '2026-10-20T17:17:55.931029+02:00'),
    ('breadth_inner_v1', 'ALN34BS_40ad746c60534cd0', '1052091', 'c3_br_curves-1052091.log', '2026-10-20T17:18:48.189227+02:00'),
]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    receipt = {'job': os.environ['SLURM_JOB_ID'], 'time': datetime.now().astimezone().isoformat(),
               'driver_sha256': sha(__file__), 'cause': 'CUDA error: uncorrectable ECC error encountered', 'units': []}
    plans = []
    for lane, eid, job, log, start in FAILURES:
        base = L3 / 'aln34' / lane
        marker = base / 'units' / f'{eid}.FAILED.json'
        value = json.loads(marker.read_text())
        assert value == {'job': job, 'rc': 1, 'status': None}, (eid, value)
        assert [p.name for p in (base / 'units').glob('*.FAILED.json')] == [marker.name], lane
        assert not (base / 'units' / f'{eid}.json').exists(), eid
        lines = (LOGS / log).read_text(errors='replace').splitlines()
        i = next(k for k, l in enumerate(lines) if l.startswith(f'{start} START ') and l.endswith(f' {eid}'))
        excerpt = [l for l in lines[i:] if 'not a valid Python identifier' not in l and 'flash_attn' not in l][:16]
        assert any(f'{eid} technical_failed' in l and 'uncorrectable ECC error' in l for l in excerpt), eid
        t0 = datetime.fromisoformat(start).timestamp()
        written = sorted([p for p in (P3 / f'aln34_{lane}').glob(f'{eid}*')] + [base / 'claims' / f'{eid}.lock'],
                         key=lambda p: p.stat().st_mtime if p.exists() else 0)
        late = [str(p) for p in written if p.exists() and p.stat().st_mtime >= t0]
        assert not late, (eid, late)
        with (base / 'claims' / f'{eid}.lock').open('a+') as handle:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)  # raises if a live worker holds the unit
        plans.append((base, eid, marker, excerpt, written))
    for base, eid, marker, excerpt, written in plans:
        dest = base / 'technical_failures' / 'ecc_20261020'
        dest.mkdir(parents=True, exist_ok=True, mode=0o700)
        shutil.copy2(marker, dest / marker.name)
        assert sha(marker) == sha(dest / marker.name)
        (dest / f'{eid}.log_excerpt.txt').write_text('\n'.join(excerpt) + '\n')
        state = {str(p): {'mtime': datetime.fromtimestamp(p.stat().st_mtime).astimezone().isoformat(), 'bytes': p.stat().st_size}
                 for p in written if p.exists()}
        marker.rename(dest / (marker.name + '.resolved_active_marker'))
        receipt['units'].append({'lane': base.name, 'unit': eid, 'marker_sha256': sha(dest / marker.name),
                                 'preserved': str(dest), 'state_before_failure': state})
    out = L3 / 'aln35/fleet_v3_20261020' / f'resolve_ecc_{os.environ["SLURM_JOB_ID"]}.json'
    out.write_text(json.dumps(receipt, indent=1) + '\n')
    print(json.dumps({'resolved': [u['unit'] for u in receipt['units']], 'receipt': str(out)}))


if __name__ == '__main__':
    main()
