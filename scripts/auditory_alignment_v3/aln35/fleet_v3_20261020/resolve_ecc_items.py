"""Release GPU-ECC technical failures named on the command line (same checks as resolve_ecc_20261021b.py).

Usage (Slurm only): resolve_ecc_items.py <tag> <lane>:<marker or probe dir relative to lane>:<log>[:<unit>] ...
Each item needs: the ECC line in its log; a marker whose job equals the log's job, or a failed probe receipt; no unit result; a
free claim lock. The marker is preserved under <lane>/technical_failures/ecc_<tag>/; a receipt is written next to this script.
"""
import fcntl
import hashlib
import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

assert os.environ.get('SLURM_JOB_ID'), 'Slurm required'
L3 = Path('/home/infres/yinwang/EEG_auditory/private/auditory_alignment_v3')
ECC = 'uncorrectable ECC error encountered'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    tag, specs = sys.argv[1], sys.argv[2:]
    receipt = {'job': os.environ['SLURM_JOB_ID'], 'time': datetime.now().astimezone().isoformat(), 'driver_sha256': sha(__file__),
               'cause': 'CUDA error: ' + ECC, 'items': []}
    checked = []
    for spec in specs:
        lane, rel, log, *unit = spec.split(':'); unit = unit[0] if unit else None
        base = L3 / lane; path = base / rel; text = (L3 / 'logs' / log).read_text(errors='replace')
        assert path.exists() and ECC in text, spec
        if path.is_file():
            assert str(json.loads(path.read_text())['job']) == log.rsplit('-', 1)[1][:-4], spec
        else:
            assert json.loads((path / 'receipt.json').read_text())['status'] == 'failed', spec
        if unit:
            assert not (base / 'units' / f'{unit}.json').exists(), unit
            with (base / 'claims' / f'{unit}.lock').open('a+') as handle:
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        checked.append((base, path, log, unit, [l for l in text.splitlines() if ECC in l][-3:]))
    for base, path, log, unit, excerpt in checked:
        dest = base / 'technical_failures' / f'ecc_{tag}'; dest.mkdir(parents=True, exist_ok=True, mode=0o700)
        name = f'{path.name}.{log[:-4]}.resolved'
        (dest / f'{name}.log_excerpt.txt').write_text('\n'.join(excerpt) + '\n')
        digest = sha(path) if path.is_file() else None
        shutil.move(str(path), str(dest / name))
        receipt['items'].append({'lane': str(base.relative_to(L3)), 'moved': str(path.relative_to(L3)), 'sha256': digest,
                                 'preserved': str((dest / name).relative_to(L3)), 'log': log, 'unit': unit})
    out = Path(__file__).with_name(f'resolve_ecc_items_{tag}_{os.environ["SLURM_JOB_ID"]}_{datetime.now():%H%M%S}.json')
    out.write_text(json.dumps(receipt, indent=1) + '\n')
    print(json.dumps({'resolved': [i['moved'] for i in receipt['items']], 'receipt': str(out)}))


if __name__ == '__main__':
    main()
