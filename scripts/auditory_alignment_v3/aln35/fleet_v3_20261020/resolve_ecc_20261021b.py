"""Second 2026-10-21 ECC resolution (10:00-10:06): every failing attempt ran on node51 and died at its first GPU allocation with
"CUDA error: uncorrectable ECC error encountered" (squeue -t all: jobs 1053330/1053332/1053334/1053338 FAILED on node51).
node51 is now excluded in the active sbatch files (operations.log). Same checks and preservation as resolve_ecc_20261021.py;
each item also requires that its storage directory holds no file written after the failing job's log was created.
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
ECC = 'uncorrectable ECC error encountered'
# (lane base, active marker or probe dir, failing job log, unit id or None, storage dir that must hold no newer file or None)
ITEMS = [
    ('aln41/r2/seed3407/source_v1', 'units/ALN41P_bd32ffb95947b01c.FAILED.json', 'c3_s35r2a41src-1053330.log', 'ALN41P_bd32ffb95947b01c',
     P3 / 'aln41/r2/seed3407/source_v1/units/ALN41P_bd32ffb95947b01c'),
    ('aln41/cross_stim_v1', 'probes/1053338', 'c3_s35a41xs-1053338.log', None, None),
    ('aln36/r2_s3407/fau_group_v1', 'units/ALN36G_befa0e4a7c5a7475.FAILED.json', 'c3_s35r2a36loc-1053334.log', 'ALN36G_befa0e4a7c5a7475', None),
    ('aln36/r2_s3407/public_features_v1', 'probes/1053320', 'c3_s35r2a36feat-1053320.log', None, None),
    ('aln34/breadth_inner_v1', 'units/ALN34BS_7558e7a1b4856378.FAILED.json', 'c3_br_curves-1053332.log', 'ALN34BS_7558e7a1b4856378', None),
]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    receipt = {'job': os.environ['SLURM_JOB_ID'], 'time': datetime.now().astimezone().isoformat(), 'driver_sha256': sha(__file__),
               'cause': 'CUDA error: ' + ECC + ' (node51)', 'items': []}
    checked = []
    for lane, rel, log, unit, storage in ITEMS:
        base = L3 / lane; path = base / rel
        assert path.exists(), path
        text = (LOGS / log).read_text(errors='replace'); assert ECC in text, log
        t0 = (LOGS / log).stat().st_ctime
        if path.is_file():
            assert json.loads(path.read_text())['job'] == log.rsplit('-', 1)[1][:-4], (path, log)
        else:
            r = json.loads((path / 'receipt.json').read_text()); assert r['status'] == 'failed'
        if unit:
            assert not (base / 'units' / f'{unit}.json').exists(), unit
            with (base / 'claims' / f'{unit}.lock').open('a+') as handle:
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if storage is not None and storage.exists():
            late = [str(p) for p in storage.rglob('*') if p.stat().st_mtime >= t0]
            assert not late, late
        checked.append((base, path, log, unit, [l for l in text.splitlines() if ECC in l or 'Error' in l][-6:]))
    for base, path, log, unit, excerpt in checked:
        dest = base / 'technical_failures' / 'ecc_20261021'; dest.mkdir(parents=True, exist_ok=True, mode=0o700)
        name = path.name + '.resolved_b'
        (dest / f'{path.name}.b.log_excerpt.txt').write_text('\n'.join(excerpt) + '\n')
        digest = sha(path) if path.is_file() else None
        shutil.move(str(path), str(dest / name))
        receipt['items'].append({'lane': str(base.relative_to(L3)), 'moved': str(path.relative_to(L3)), 'sha256': digest,
                                 'preserved': str((dest / name).relative_to(L3)), 'log': log, 'unit': unit})
    out = L3 / 'aln35/fleet_v3_20261020' / f'resolve_ecc_20261021b_{os.environ["SLURM_JOB_ID"]}.json'
    out.write_text(json.dumps(receipt, indent=1) + '\n')
    print(json.dumps({'resolved': [i['moved'] for i in receipt['items']], 'receipt': str(out)}))


if __name__ == '__main__':
    main()
