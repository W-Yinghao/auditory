"""Single-worker bridge replay lane; original extractor and plan stay immutable."""
from __future__ import annotations
import argparse
from datetime import datetime
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
from . import bridge_factor as F
from . import science_binding as B

BASE = F.BASE
PLAN = BASE / 'fleet_plan.json'


def fresh_sha(path):
    return F.BR.file_sha256(path)


def source_files():
    paths = ['auditory_alignment_v3/aln35/bridge_factor_fleet.py',
             'auditory_alignment_v3/aln35/bridge_factor.py',
             'auditory_alignment_v3/aln35/bridge_factor_extract.py',
             'slurm/aln35_bridge_fleet.sbatch']
    return {p: fresh_sha(B.ROOT / p) for p in paths}


def register():
    original = B.read(BASE / 'plan.json')
    body = {'schema': 'aln35_bridge_fleet_v1', 'source_plan_sha256': fresh_sha(BASE / 'plan.json'),
            'rows': [{'id': 'ALN35BRIDGE_' + entry['key'], 'key': entry['key'], 'cache': entry['cache'],
                      'source_bundle_sha256': B.digest(entry)} for entry in original['entries']],
            'sources': source_files(), 'bootstrap_key': 'dtu_AP', 'slots': 1,
            'rule': 'first manually submitted dtu_AP receipt must PASS; then fixed remaining key order; one global worker claim; no job submission from this module',
            'CPU_analysis_entry': ['slurm/aln35_bridge_analyze.sbatch'],
            'GPU_extractor_unchanged': True}
    if PLAN.is_file(): assert B.read(PLAN) == body
    else: B.write_new(PLAN, body)
    print(json.dumps({'status': 'registered', 'plan_sha256': fresh_sha(PLAN), 'fleet': fleet_status()}), flush=True)


def verify(plan):
    assert plan['sources'] == source_files(), 'bridge lane source drift'
    assert plan['source_plan_sha256'] == fresh_sha(BASE / 'plan.json'), 'frozen bridge source plan drift'
    original = B.read(BASE / 'plan.json')
    assert len(plan['rows']) == 4 and [u['key'] for u in plan['rows']] == list(F.KEYS)
    for row, entry in zip(plan['rows'], original['entries']):
        assert row['key'] == entry['key'] and row['source_bundle_sha256'] == B.digest(entry)


def complete(unit, plan):
    """Cheap scheduler check; extractor and CPU analyzer verify all array hashes."""
    public_receipt = BASE / 'extract_receipts' / (unit['key'] + '.json')
    cache_receipt = Path(unit['cache']) / 'complete.json'
    if not public_receipt.is_file() or not cache_receipt.is_file(): return False
    rec = B.read(public_receipt)
    return (rec == B.read(cache_receipt) and rec.get('status') == 'complete' and rec.get('key') == unit['key']
            and rec.get('plan_sha256') == plan['source_plan_sha256']
            and rec.get('extract_code_sha256') == plan['sources']['auditory_alignment_v3/aln35/bridge_factor_extract.py'])


def failures(plan):
    return [u['key'] for u in plan['rows'] if (BASE / 'fleet_failures' / (u['key'] + '.json')).exists()]


def fleet_status():
    """Read-only interface used by the single root fleet authority."""
    status = {'name': 'c3_s35bridge', 'lane': 's35_bridge', 'state': 'plan_missing',
              'ready': 0, 'remaining': 4, 'slots': 1, 'initial': [], 'submit': []}
    if not PLAN.is_file(): return status
    plan = B.read(PLAN)
    remaining = [u for u in plan['rows'] if not complete(u, plan)]
    status['remaining'] = len(remaining)
    if not remaining:
        status.update(state='complete', CPU_analysis_ready=True,
                      CPU_analysis_submit=['slurm/aln35_bridge_analyze.sbatch'])
        return status
    if failures(plan):
        status.update(state='failed_unit_requires_review', failed=failures(plan)); return status
    bootstrap = next(u for u in plan['rows'] if u['key'] == plan['bootstrap_key'])
    if not complete(bootstrap, plan):
        status['state'] = 'bootstrap_dtu_AP_receipt_required'; return status
    # A partial directory is preserved for review, not overwritten or retried.
    partial = [u['key'] for u in remaining if Path(u['cache']).exists()]
    if partial:
        status.update(state='partial_cache_or_active_worker', partial=partial); return status
    status.update(state='ready', ready=len(remaining),
                  submit=['slurm/aln35_bridge_fleet.sbatch', '--max-units', '1'])
    return status


def worker(max_units):
    plan = B.read(PLAN); verify(plan)
    bootstrap = next(u for u in plan['rows'] if u['key'] == plan['bootstrap_key'])
    assert complete(bootstrap, plan), 'manual dtu_AP bootstrap has not completed'
    assert not failures(plan), 'failed bridge unit needs scoped review'
    claims = BASE / 'claims'; claims.mkdir(parents=True, exist_ok=True)
    with (claims / 'single_worker.lock').open('a+') as handle:
        try: fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print('another bridge worker owns the single claim', flush=True); return
        n = 0
        for unit in plan['rows']:
            if complete(unit, plan): continue
            assert unit['key'] != plan['bootstrap_key']
            assert not Path(unit['cache']).exists(), ('partial cache preserved; scoped review required', unit['cache'])
            claim = {'key': unit['key'], 'job': os.environ['SLURM_JOB_ID'], 'time': datetime.now().astimezone().isoformat(),
                     'source_plan_sha256': plan['source_plan_sha256'], 'fleet_plan_sha256': fresh_sha(PLAN)}
            B.write_new(claims / (unit['key'] + '_' + os.environ['SLURM_JOB_ID'] + '.json'), claim)
            process = subprocess.run([sys.executable, '-B', '-u', '-m', 'auditory_alignment_v3.aln35.bridge_factor_extract', '--key', unit['key']])
            if process.returncode or not complete(unit, plan):
                B.write_new(BASE / 'fleet_failures' / (unit['key'] + '.json'), {**claim, 'returncode': process.returncode,
                            'status': 'technical_failed', 'partial_cache_preserved': True})
                raise RuntimeError('bridge extraction failed: ' + unit['key'])
            n += 1
            if n >= max_units: break
    print(json.dumps({'status': 'worker_complete', 'completed_here': n, 'fleet': fleet_status()}), flush=True)


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--register', action='store_true'); parser.add_argument('--max-units', type=int, default=1)
    args = parser.parse_args(); assert os.environ.get('SLURM_JOB_ID'); os.umask(0o077)
    if args.register: register()
    else:
        assert 1 <= args.max_units <= 3
        worker(args.max_units)


if __name__ == '__main__': main()
