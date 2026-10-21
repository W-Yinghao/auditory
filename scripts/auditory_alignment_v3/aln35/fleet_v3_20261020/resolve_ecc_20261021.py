"""Resolve the 2026-10-21 09:50-09:54 technical failures (uncorrectable GPU ECC error) so the fleet retries them.

Same cause and procedure as resolve_ecc_20261020.py. Each attempt died seconds after start while moving data to the GPU with
"CUDA error: uncorrectable ECC error encountered". For each item this checks four things: the marker or receipt, the ECC line
in the log, that no unit result exists, and that no worker holds the claim lock. The marker or receipt is then preserved
under <lane>/technical_failures/ecc_20261021/ and taken out of the active path. No plan, row, trainer, checkpoint or record
is changed.
Items: ALN4.1 R2 source unit (seed 3407 TNCE, job 1053316); the ALN3.6 R2 FAU-group smoke receipt (job 1053319, nothing
trained); breadth_curves unit ALN34BS_7558e7a1b4856378 (job 1053294, after a preemption requeue).
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
LOGS = L3 / 'logs'
ECC = 'uncorrectable ECC error encountered'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def preserve(base, path, log, receipt, unit=None):
    dest = base / 'technical_failures' / 'ecc_20261021'; dest.mkdir(parents=True, exist_ok=True, mode=0o700)
    lines = (LOGS / log).read_text(errors='replace').splitlines()
    excerpt = [l for l in lines if ECC in l or 'Error' in l][-8:]
    assert any(ECC in l for l in excerpt), log
    if unit:
        assert not (base / 'units' / f'{unit}.json').exists(), unit
        with (base / 'claims' / f'{unit}.lock').open('a+') as handle:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)      # raises if a live worker holds the unit
    digest = sha(path) if path.is_file() else None
    (dest / f'{path.name}.log_excerpt.txt').write_text('\n'.join(excerpt) + '\n')
    shutil.move(str(path), str(dest / (path.name + '.resolved')))
    receipt['items'].append({'lane': str(base.relative_to(L3)), 'moved': str(path.relative_to(L3)), 'sha256': digest,
                             'preserved': str((dest / (path.name + '.resolved')).relative_to(L3)), 'log': log, 'unit': unit})


def main():
    receipt = {'job': os.environ['SLURM_JOB_ID'], 'time': datetime.now().astimezone().isoformat(), 'driver_sha256': sha(__file__),
               'cause': 'CUDA error: ' + ECC, 'items': []}
    b = L3 / 'aln41/r2/seed3407/source_v1'; u = 'ALN41P_bd32ffb95947b01c'
    m = b / 'units' / f'{u}.FAILED.json'
    assert json.loads(m.read_text()) == {'job': '1053316', 'returncode': 1, 'seed': 3407}
    preserve(b, m, 'c3_s35r2a41src-1053316.log', receipt, u)
    b = L3 / 'aln36/r2_s3407/fau_group_v1'; p = b / 'probes' / '1053319'
    r = json.loads((p / 'receipt.json').read_text()); assert r['status'] == 'failed' and not list((p / 'units').glob('*.json')) if (p / 'units').exists() else True
    preserve(b, p, 'c3_s35r2a36loc-1053319.log', receipt)
    b = L3 / 'aln34/breadth_inner_v1'; u = 'ALN34BS_7558e7a1b4856378'
    m = b / 'units' / f'{u}.FAILED.json'
    assert json.loads(m.read_text()) == {'job': '1053294', 'rc': 1, 'status': None}
    assert [x.name for x in (b / 'units').glob('*.FAILED.json')] == [m.name]
    preserve(b, m, 'c3_br_curves-1053294.log', receipt, u)
    out = L3 / 'aln35/fleet_v3_20261020' / f'resolve_ecc_20261021_{os.environ["SLURM_JOB_ID"]}.json'
    out.write_text(json.dumps(receipt, indent=1) + '\n')
    print(json.dumps({'resolved': [i['moved'] for i in receipt['items']], 'receipt': str(out)}))


if __name__ == '__main__':
    main()
