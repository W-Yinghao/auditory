"""Training-side-only diagnosis; never writes a scientific result or cache."""
import json
import os
from pathlib import Path
import traceback

import numpy as np
from sklearn.linear_model import LogisticRegression
from scipy.optimize import minimize
from scipy.special import expit

from auditory_alignment import data
from auditory_alignment_v3.aln34 import private_current_time as P
from auditory_alignment_v3.aln3_reference.calibration import AffineLogitCalibrator

assert os.environ.get('SLURM_JOB_ID')
os.umask(0o077)
eid = 'ALN34P_5551c74e7a9b79f8'
plan = json.loads(P.PLAN.read_text())
P.verify(plan)
unit = next(u for u in plan['rows'] if u['id'] == eid)
kids = data.load_private()
fd = P.P.Fold(kids, unit['source']['subject_fold'])
cache = P.STORE / 'cache' / eid
meta = json.loads((cache / 'meta.json').read_text())
assert meta['unit'] == unit and meta['array_sha256'] == P.B.sha(cache / 'arrays.npz')
result = {'job': os.environ['SLURM_JOB_ID'], 'unit': eid, 'plan_sha256': P.B.sha(P.PLAN),
          'cache_sha256': meta['array_sha256'], 'scope': 'training ES calibration only', 'windows': {}}
with np.load(cache / 'arrays.npz', allow_pickle=False) as z:
    for window in P.WINDOWS:
        features = {i: z[f'{window}_{i}'] for i in fd.tr}
        x = fd.es_rows(features)
        mu, sd = x.mean(0), x.std(0) + 1e-8
        lr = LogisticRegression(C=1.0, max_iter=2000).fit((x-mu)/sd, fd.y_es)
        score = lr.decision_function((x-mu)/sd)
        entry = {}
        try:
            entry['original'] = AffineLogitCalibrator.fit(score, fd.y_es).to_dict()
        except Exception:
            entry['original_error'] = traceback.format_exc()
        y = np.asarray(fd.y_es, dtype=float)
        w = np.ones_like(score) / len(score)
        center = float(w @ score)
        scale = float(np.sqrt(w @ ((score-center)**2)))
        zz = (score-center)/scale
        l2 = 1e-6
        def objective(ab):
            a, b = ab
            logits = a*zz+b
            residual = expit(logits)-y
            return (float(w@(np.logaddexp(0, logits)-y*logits)+0.5*l2*(a*a+b*b)),
                    np.array([w@(residual*zz)+l2*a, w@residual+l2*b]))
        prior = float(w@y)
        for maxls in (20, 100):
            fit = minimize(objective, [1., np.log(prior/(1-prior))], jac=True, method='L-BFGS-B',
                           bounds=[(1e-8, None), (None, None)],
                           options={'maxiter': 3000, 'ftol': 1e-12, 'gtol': 1e-8, 'maxls': maxls})
            grad = objective(fit.x)[1]
            if fit.x[0] <= 1.0001e-8: grad[0] = min(grad[0], 0.)
            entry[f'maxls_{maxls}'] = {'success': bool(fit.success), 'message': str(fit.message),
                'objective': float(fit.fun), 'x': fit.x.tolist(), 'projected_gradient_inf': float(abs(grad).max()),
                'iterations': int(fit.nit)}
        result['windows'][window] = entry
        print(window, json.dumps(entry), flush=True)
dest = P.BASE.parent / 'runtime_check_20261018'
dest.mkdir(exist_ok=True)
(dest / 'calibration_diagnosis.json').write_text(json.dumps(result, indent=2)+'\n')
