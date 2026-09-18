"""Freeze and run the independent saved-output audit/report in Slurm."""
import argparse
import json
import os
import shutil
import sys
from pathlib import Path

from auditory5.provenance import ROOT, digest, require_slurm, write_json


def main():
    require_slurm()
    parser = argparse.ArgumentParser()
    parser.add_argument('--plan', default=str(ROOT / 'private/auditory_retrain_v1/jobs/plan_001/plan.json'))
    parser.add_argument('--run', default='verification_001')
    parser.add_argument('--frozen', action='store_true')
    args = parser.parse_args()
    plan_path = Path(args.plan).resolve()
    plan = json.loads(plan_path.read_text())
    base = ROOT / plan['config']['paths']['private_relative']
    review = base / 'reviews' / args.run
    snapshot = review / 'source'
    if not args.frozen:
        review.mkdir(parents=True, exist_ok=False)
        shutil.copytree(Path(plan['source_snapshot']) / 'auditory5', snapshot / 'auditory5')
        (snapshot / 'auditory_retrain').mkdir()
        for name in ['__init__.py', 'audit.py', 'verify.py', 'report.py']:
            shutil.copyfile(ROOT / 'auditory_retrain' / name, snapshot / 'auditory_retrain' / name)
        write_json(review / 'source_receipt.json', dict(job_id=os.environ['SLURM_JOB_ID'],
                   hashes={str(p.relative_to(snapshot)): digest(p) for p in snapshot.rglob('*.py')},
                   plan_hash=digest(plan_path)))
        env = dict(os.environ, AUDITORY5_ROOT=str(ROOT), PYTHONPATH=str(snapshot))
        os.chdir(snapshot)
        os.execve(sys.executable, [sys.executable, '-m', 'auditory_retrain.audit', '--plan', str(plan_path),
                                  '--run', args.run, '--frozen'], env)
    assert Path(__file__).resolve() == snapshot / 'auditory_retrain/audit.py'
    receipt = json.loads((review / 'source_receipt.json').read_text())
    for path, expected in receipt['hashes'].items():
        assert digest(snapshot / path) == expected
    from auditory_retrain.verify import run as verify
    from auditory_retrain.report import run as report
    summary = verify(plan_path, run_name=args.run)
    report_path = report(plan_path, summary, args.run)
    # Protect only this round's own files; never follow the EEG export alias.
    directories = files = 0
    for directory, children, names in os.walk(base, followlinks=False):
        os.chmod(directory, 0o700)
        directories += 1
        children[:] = [name for name in children if not (Path(directory) / name).is_symlink()]
        for name in names:
            path = Path(directory) / name
            if not path.is_symlink():
                os.chmod(path, 0o600)
                files += 1
    write_json(review / 'completion.json', dict(status='PASS', job_id=os.environ['SLURM_JOB_ID'],
               plan_hash=digest(plan_path), model_refits=0, report_hash=digest(report_path / 'REPORT.md'),
               private_permissions=dict(directories_0700=directories, files_0600=files, followed_symlinks=False)))
    print(json.dumps(dict(status='PASS', stage='independent_verification_and_report',
                         tasks=summary['tasks'], job_id=os.environ['SLURM_JOB_ID'])), flush=True)


if __name__ == '__main__':
    main()
