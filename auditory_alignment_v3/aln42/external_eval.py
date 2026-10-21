"""ALN4.2 R3 external comparison evaluation (CPU; package docs/06 §6.4), after the 10 MindMix units and the core-3 readouts.

The common 20 s protocol is the one of aln41.readout.attention: the same 5 s DTU competing-talker segments, runs of
consecutive segments cut into 20 s windows (aln3 run_attention._runs / _windows), mean-score evidence, tau fitted by
double-order log loss on the training side only (train people's fit and es windows), double candidate order, ties 0.5.
MindMix supplies the blind attended-minus-ignored segment margin (mean of its three 2 s sub-windows, frozen binding);
core-3 supplies the envelope-readout margin. Per person: the content folds are averaged, both required. Core TCS / TNCE are
first averaged over seeds 3401 / 3407 / 3413 within person; B0 is the single seed-free baseline. External: one released
checkpoint, downstream seed 3401 (intervals condition on these models).
Families (separate, 3 members each, person bootstrap-t B = 4000, family max-|T*| via aln41.analysis.family):
  accuracy: external - B0, external - TCS, external - TNCE (higher = better);
  NLL bits: external - B0, external - TCS, external - TNCE (lower = better; negative = external better).
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np

from .. import core
from ..aln41 import analysis as AN, frozen as FZ, r2 as R2, readout as RO, source as SRC
from . import external_mindmix as XM

RESULTS = Path(core.REPO) / 'results/auditory_alignment_v3/aln42/external'
SEEDS = (3401, 3407, 3413)


def integrate(margin, person, role, code, e0, seg_len, train_people, test_people):
    """aln41.readout.attention with a precomputed segment margin; returns {sec: {person: {accuracy, nll_bits, n_windows}}}."""
    from ..run_attention import _runs, _windows
    from ..aln34 import attention_order as AO
    segs = [{'p': p, 'code': c, 'e0': int(e), 'role': r, 'i': i} for i, (p, c, e, r) in enumerate(zip(person, code, e0, role))]
    tr = [s for s in segs if s['p'] in train_people and s['role'] in ('fit', 'es')]
    te = [s for s in segs if s['p'] in test_people and s['role'] == 'test']
    assert all(np.isfinite(margin[s['i']]) for s in tr + te), 'unscored segment inside the common query'
    out = {}
    for sec in (5, 10, 20):
        k = sec // 5
        wt = [w for r in ('es', 'fit') for w in _windows(_runs([s for s in tr if s['role'] == r], seg_len), k)]
        we = _windows(_runs(te, seg_len), k)
        xt = np.array([[margin[s['i']] for s in w] for w in wt]); xe = np.array([[margin[s['i']] for s in w] for w in we])
        rms = AO.train_scale(xt); grid = np.logspace(-3, 2, 41) * (rms if rms > 0 else 1.0)
        loss = [AO.order_logloss_bits(xt.mean(1) / t, -xt.mean(1) / t).mean() for t in grid]; tau = float(grid[int(np.argmin(loss))])
        z = xe.mean(1) / tau; acc = AO.order_credit(z, -z); ll = AO.order_logloss_bits(z, -z)
        per = {}
        for j, w in enumerate(we):
            per.setdefault(w[0]['p'], []).append(j)
        out[str(sec)] = {'tau': tau, 'people': {p: {'accuracy': float(acc[ix].mean()), 'nll_bits': float(ll[ix].mean()), 'n_windows': len(ix)}
                                                for p, ix in per.items()}}
    return out


def external_people():
    plan = XM.read(XM.OUT / 'plan.json'); per = {}
    for row in plan['rows']:
        rec = XM.read(XM.OUT / 'units' / f'{row["id"]}.json'); assert rec['status'] == 'complete' and not rec['probe']
        with np.load(Path(rec['dest']) / 'margins.npz') as z:
            A = {k: z[k] for k in z.files}
        assert XM.sha(Path(rec['dest']) / 'margins.npz') == rec['npz_sha256']
        fz = FZ.read(FZ.BASE / 'plan.json')
        b0 = next(r for r in fz['rows'] if r['arm'] == 'B0' and r['dataset'] == 'dtu' and r['content_fold'] == row['content_fold'])
        meta = FZ.read(Path(FZ.read(FZ.BASE / 'units' / f'{b0["id"]}.json')['dest']) / 'meta.json')
        sf = row['person_fold']; train_people = set(meta['pca'][str(sf)]['train_people'])
        test_people = {p for p in set(A['cs_person'].tolist()) if meta['folds'].get(p) == sf and p not in set(meta['dev_people'])}
        res = integrate(A['margin'], A['cs_person'], A['cs_role'], A['cs_code'], A['cs_e0'], meta['cs']['seg_len'], train_people, test_people)
        for p, v in res['20']['people'].items():
            per.setdefault(p, {})[row['content_fold']] = v
    return {p: {'accuracy': np.mean([d[c]['accuracy'] for c in (0, 1)]), 'nll_bits': np.mean([d[c]['nll_bits'] for c in (0, 1)])}
            for p, d in per.items() if sorted(d) == [0, 1]}


def core_people():
    """{arm: {person: {accuracy, nll_bits}}}: q0 20 s attention from the core readouts, content folds then seeds averaged."""
    by = {}
    for seed in SEEDS:
        ctx = R2.seeded(seed) if seed != SRC.SEED else _null()
        with ctx:
            base = RO.BASE if seed == SRC.SEED else R2.ROOT / f'seed{seed}' / 'readout_v1'
            for row in FZ.read(FZ.BASE / 'plan.json')['rows']:
                p = base / 'units' / f'{row["id"]}.json'
                if row['dataset'] != 'dtu' or row['arm'] not in ('B0', 'TCS', 'TNCE') or not p.exists():
                    continue
                for pid, r in FZ.read(p)['people'].items():
                    v = r.get('attention', {}).get('q0', {}).get('20')
                    if v:
                        by.setdefault(row['arm'], {}).setdefault(pid, {}).setdefault(seed, {})[row['content_fold']] = (v['accuracy'], v['nll_bits'])
    out = {}
    for arm, people in by.items():
        need = (SRC.SEED,) if arm == 'B0' else SEEDS
        for pid, s in people.items():
            if all(x in s and sorted(s[x]) == [0, 1] for x in need):
                out.setdefault(arm, {})[pid] = {k: float(np.mean([np.mean([s[x][c][j] for c in (0, 1)]) for x in need]))
                                                for j, k in enumerate(('accuracy', 'nll_bits'))}
    return out


class _null:
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def main():
    assert os.environ.get('SLURM_JOB_ID'); os.umask(0o022)
    ext, core3 = external_people(), core_people()
    people = sorted(set(ext) | set().union(*[set(v) for v in core3.values()]))
    fams = []
    for metric, direction in (('accuracy', 'higher is better'), ('nll_bits', 'lower is better; negative = external better')):
        members = [(f'external-{arm}', {p: (ext[p][metric] - core3[arm][p][metric]) if p in ext and p in core3.get(arm, {}) else None for p in people})
                   for arm in ('B0', 'TCS', 'TNCE')]
        f = AN.family(f'F_EXTERNAL:{metric}', f'20 s attention {metric} ({direction})', members, people)
        f['method'] = 'sci_r1 identity bootstrap-t B=4000, family max-|T*|; core TCS/TNCE seed-averaged within person; external single released checkpoint, seed 3401'
        fams.append(f)
    RESULTS.mkdir(parents=True, exist_ok=True)
    desc = {name: {m: float(np.mean([v[m] for v in d.values()])) for m in ('accuracy', 'nll_bits')} for name, d in [('external', ext)] + list(core3.items())}
    (RESULTS / 'EXTERNAL_COMPARISON.json').write_text(json.dumps({'families': fams, 'descriptive_means': desc,
        'per_person': {'external': ext, **core3}, 'binding_sha256': XM.sha(XM.BINDING), 'plan_sha256': XM.sha(XM.OUT / 'plan.json'),
        'display_name': 'MindMix released full architecture, common-protocol task adaptation'}, indent=1, default=float) + '\n')
    print(json.dumps({f['family_id']: f['status'] for f in fams}, indent=1), desc)


if __name__ == '__main__':
    main()
