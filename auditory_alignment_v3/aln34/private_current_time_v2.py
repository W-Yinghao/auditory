"""Successor execution for the private science calibration termination repair."""
import argparse
from contextlib import contextmanager
from datetime import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import traceback
from sklearn.linear_model import LogisticRegression

from . import private_current_time as V1
from . import calibration_retry as C

BASE = V1.BASE.parent/'private_current_time_v2'
PLAN = BASE/'plan.json'
NOTE = BASE.parent/'PRIVATE_TIME_CALIBRATION_CORRECTION_20261018.md'
OLD_BASE, OLD_PLAN = V1.BASE, V1.PLAN
B = V1.B


def sources():
    files = (Path(__file__), Path(C.__file__), NOTE, OLD_PLAN)
    return {str(p.relative_to(V1.core.REPO)): B.sha(p) for p in files}


def register():
    old = json.loads(OLD_PLAN.read_text()); V1.verify(old)
    rows = []
    for original in old['rows']:
        unit = dict(original)
        unit['previous_id'] = original['id']
        unit['calibration_correction_sha256'] = B.sha(NOTE)
        unit['id'] = 'ALN34P2_'+hashlib.sha256(B.dumps(unit).encode()).hexdigest()[:16]
        rows.append(unit)
    plan = {'version': 'ALN34_PRIVATE_CURRENT_TIME_v2', 'rows': rows, 'sources': sources(),
            'created': datetime.now().astimezone().isoformat(), 'v1_sources': old['sources']}
    if PLAN.exists():
        saved = json.loads(PLAN.read_text())
        assert all(saved[k] == v for k, v in plan.items() if k != 'created')
    else:
        B.write(PLAN, plan); PLAN.chmod(0o444)
    reused = 0
    for unit in rows:
        original = OLD_BASE/'units'/f'{unit["previous_id"]}.json'
        dest = BASE/'units'/f'{unit["id"]}.json'
        if not original.exists() or dest.exists(): continue
        rec = json.loads(original.read_text())
        if rec.get('status') != 'complete' or rec.get('probe'): continue
        assert rec['plan_sha256'] == B.sha(OLD_PLAN)
        rec.update(unit=unit, plan_sha256=B.sha(PLAN), execution_version=plan['version'],
                   reused_from={'path': str(original), 'sha256': B.sha(original), 'plan_sha256': B.sha(OLD_PLAN)},
                   calibration_execution='v1_success_exact_reuse')
        B.write(dest, rec); reused += 1
    print(json.dumps({'planned': len(rows), 'reused': reused, 'plan_sha256': B.sha(PLAN)}), flush=True)


def verify(plan):
    assert plan['sources'] == sources(), 'private science v2 source drift'
    old = json.loads(OLD_PLAN.read_text()); V1.verify(old)
    assert plan['v1_sources'] == old['sources']


class Probe(V1.P.Probe):
    def __init__(self, Xtr, ytr, Xcal=None, ycal=None):
        self.mu, self.sd = Xtr.mean(0), Xtr.std(0)+1e-8
        self.lr = LogisticRegression(C=1.0, max_iter=2000).fit((Xtr-self.mu)/self.sd, ytr)
        Xc, yc = (Xtr, ytr) if Xcal is None else (Xcal, ycal)
        self.cal = C.AffineLogitCalibrator.fit(self.score(Xc), yc)


@contextmanager
def bindings(unit):
    original = next(u for u in json.loads(OLD_PLAN.read_text())['rows'] if u['id'] == unit['previous_id'])
    previous = V1.BASE, V1.PLAN, V1.extract, V1.P.Probe, V1.AffineLogitCalibrator
    extract = V1.extract
    V1.BASE, V1.PLAN, V1.P.Probe, V1.AffineLogitCalibrator = BASE, PLAN, Probe, C.AffineLogitCalibrator
    # Extractor and cached metadata retain the original unit/source identity.
    V1.extract = lambda unused, kids, probe=False: extract(original, kids, probe)
    try: yield
    finally: V1.BASE, V1.PLAN, V1.extract, V1.P.Probe, V1.AffineLogitCalibrator = previous


def run_unit(unit):
    out = BASE/'units'/f'{unit["id"]}.json'
    assert not out.exists(), 'never overwrite an execution'
    C.FIT_EVENTS.clear()
    with bindings(unit): V1.run_unit(unit)
    rec = json.loads(out.read_text())
    rec.update(execution_version='ALN34_PRIVATE_CURRENT_TIME_v2', calibration_execution=list(C.FIT_EVENTS))
    B.write(out, rec)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--register', action='store_true'); ap.add_argument('--smoke', action='store_true')
    ap.add_argument('--unit'); ap.add_argument('--smoke-job'); ap.add_argument('--max-units', type=int, default=8)
    a = ap.parse_args(); assert os.environ.get('SLURM_JOB_ID'); os.umask(0o077)
    if a.register: register(); return
    plan = json.loads(PLAN.read_text()); verify(plan)
    if a.unit: run_unit(next(u for u in plan['rows'] if u['id'] == a.unit)); return
    if a.smoke:
        receipt = {'status': 'running', 'plan_sha256': B.sha(PLAN), 'full_failed_case': True}
        try:
            unit = next(u for u in plan['rows'] if u['previous_id'] == 'ALN34P_5551c74e7a9b79f8')
            run_unit(unit)
            rec = json.loads((BASE/'units'/f'{unit["id"]}.json').read_text())
            fallbacks = sum(x['fallback'] for x in rec['calibration_execution'])
            assert fallbacks > 0 and rec['status'] == 'complete' and not rec['probe']
            receipt.update(status='pass', unit=unit['id'], fallbacks=fallbacks)
        except BaseException: receipt.update(status='failed', traceback=traceback.format_exc()); raise
        finally: B.write(BASE/'probes'/os.environ['SLURM_JOB_ID']/'receipt.json', receipt)
        return
    receipt = json.loads((BASE/'probes'/a.smoke_job/'receipt.json').read_text())
    assert receipt['status'] == 'pass' and receipt['plan_sha256'] == B.sha(PLAN)
    assert not list((BASE/'units').glob('*.FAILED.json'))
    done = 0
    for unit in plan['rows']:
        eid = unit['id']; out = BASE/'units'/f'{eid}.json'
        if out.exists():
            assert json.loads(out.read_text())['status'] == 'complete'; continue
        lock = BASE/'claims'/f'{eid}.lock'; lock.parent.mkdir(exist_ok=True)
        with lock.open('a+') as handle:
            try: fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError: continue
            if out.exists(): continue
            rc = subprocess.run([sys.executable, '-B', '-u', '-m', __spec__.name, '--unit', eid]).returncode
            if rc or not out.exists() or json.loads(out.read_text()).get('status') != 'complete':
                B.write(BASE/'units'/f'{eid}.FAILED.json', {'job': os.environ['SLURM_JOB_ID'], 'rc': rc})
                raise RuntimeError('private science v2 failure: '+eid)
            done += 1
        if done >= a.max_units: break


if __name__ == '__main__': main()
