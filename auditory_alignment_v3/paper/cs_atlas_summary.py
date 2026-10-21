"""Paper line W1 summary: person-level CS dependence atlas tables from cells_<source>.csv.gz (CPU).

Person value: excess dependence D (nats; CS_true − mean of the within-person segment-roll null) and z, averaged over the two
content folds (both required), then over seeds within person (aln41 arms other than B0: seeds 3401 / 3407 / 3413, all required;
B0 and aln34 FAU / Federici: the seeds available). People are the unit.
Descriptive cells: mean D across people with a 95% person-bootstrap percentile interval (B = 2000), mean z, and the share of
people with z > 1.96 (not a test; the null sd comes from at most 20 rolls).
Contrast families (paired, same people), each with the sci_r1 identity bootstrap-t family max-|T*| simultaneous 95% intervals
(aln41.analysis.family):
  aln41, per dataset × target: {TCS, TNCE, GCS, TCS_WRONG} − B0, TCS − TCS_WRONG, TCS − TNCE, TCS − GCS, over slots W0/W1/W2;
  aln34, per dataset × target (centres −200…600): CBpre − CBrand, CBpre − local, local learned − local raw-EEG reference.
Outputs: results/auditory_alignment_v3/paper/cs_atlas/{summary.json, ATLAS.md}.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from ..aln41 import analysis as AN
from . import cs_atlas as CA

B_DESC, DESC_SEED = 2000, 20261022


def load(source):
    path = CA.RESULTS / f'cells_{source}.csv.gz'
    if not path.exists():
        return None
    d = pd.read_csv(path, dtype={'person': str})
    d['group'] = d['group'].fillna('').astype(str)
    return d


def person_table(d, need_seeds):
    """-> DataFrame indexed by (dataset, model, rep, target, person) with excess, z, group."""
    keys = ['dataset', 'model', 'rep', 'target', 'person', 'group', 'seed']
    cf = d.groupby(keys + ['content_fold'])[['excess', 'z']].mean().reset_index()
    nfold = cf.groupby(keys)['content_fold'].nunique()
    cf = cf.groupby(keys)[['excess', 'z']].mean().reset_index().merge(nfold.rename('n_cf').reset_index(), on=keys)
    cf = cf[cf['n_cf'] == 2]
    out = []
    for (ds, model), g in cf.groupby(['dataset', 'model']):
        seeds = need_seeds(ds, model)
        k = keys[:-1]
        cnt = g.groupby(k)['seed'].nunique().rename('n_seed')
        h = g.groupby(k)[['excess', 'z']].mean().join(cnt)
        if seeds:
            h = h[h['n_seed'] == seeds]
        out.append(h.reset_index())
    return pd.concat(out, ignore_index=True)


def boot_ci(y, seed=DESC_SEED):
    y = np.asarray(y, float); rng = np.random.default_rng(seed)
    m = rng.integers(0, len(y), size=(B_DESC, len(y)))
    b = y[m].mean(1); return [float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))]


def describe(P):
    rows = []
    for (ds, model, rep, target), g in P.groupby(['dataset', 'model', 'rep', 'target']):
        rows.append({'dataset': ds, 'model': model, 'rep': rep, 'target': target, 'n': len(g), 'mean_excess': float(g['excess'].mean()),
                     'ci95': boot_ci(g['excess'].to_numpy()), 'mean_z': float(g['z'].mean()), 'share_z_gt_1.96': float((g['z'] > 1.96).mean())})
        for grp, gg in g.groupby('group'):
            if grp and len(gg) >= 3:
                rows.append({'dataset': ds, 'model': model, 'rep': rep, 'target': target, 'group': grp, 'n': len(gg),
                             'mean_excess': float(gg['excess'].mean()), 'ci95': boot_ci(gg['excess'].to_numpy()), 'mean_z': float(gg['z'].mean())})
    return rows


def contrast_families(P, source):
    fams = []
    if source == 'aln41':
        pairs = [(a, 'B0') for a in ('TCS', 'TNCE', 'GCS', 'TCS_WRONG')] + [('TCS', 'TCS_WRONG'), ('TCS', 'TNCE'), ('TCS', 'GCS')]
        reps = ('W0', 'W1', 'W2')
    else:
        pairs = [('cbramod_pretrained_full', 'cbramod_random_full'), ('cbramod_pretrained_full', 'local')]
        reps = tuple(f'model_{c}' for c in CA.CT.CENTERS)
    for (ds, target), g in P.groupby(['dataset', 'target']):
        V = {(m, r): dict(zip(h['person'], h['excess'])) for (m, r), h in g.groupby(['model', 'rep'])}
        people = sorted(set(g['person']))
        members = []
        for a, b in pairs:
            for r in reps:
                if (a, r) in V and (b, r) in V:
                    members.append((f'{a}-{b}/{r}', {p: V[a, r][p] - V[b, r][p] if p in V[a, r] and p in V[b, r] else None for p in people}))
        if source == 'aln34':
            for c in CA.CT.CENTERS:
                if ('local', f'model_{c}') in V and ('local', f'raw_{c}') in V:
                    L, R = V['local', f'model_{c}'], V['local', f'raw_{c}']
                    members.append((f'local learned-raw/{c}', {p: L[p] - R[p] if p in L and p in R else None for p in people}))
        if not members:
            continue
        cover = [p for p in people if all(v.get(p) is not None for _, v in members)]
        f = AN.family(f'CS_ATLAS:{source}:{ds}:{target}', 'excess CS dependence (nats)', members, cover)
        f['method'] = 'sci_r1 identity bootstrap-t B=4000, family max-|T*|; person values averaged over content folds and seeds'
        fams.append(f)
    return fams


def fmt(x, scale=1e4):
    return f'{x * scale:+.2f}'


def ci(c, scale=1e4):
    return f'[{c[0] * scale:+.2f}, {c[1] * scale:+.2f}]' if c else 'n/a'


def markdown(out):
    L = ['# CS dependence atlas (paper line W1; exploratory, designed after ALN4.1 R1 / ALN4.2)', '',
         'Excess dependence D = CS_true − mean(within-person segment-roll null), in 1e-4 nats; person means with 95% person-bootstrap',
         'percentile intervals; z = D / null sd (≤ 20 rolls). Contrast intervals: family max-|T*| simultaneous 95%. People are the unit.', '']
    for source, block in out['sources'].items():
        L += [f'## {source}', '']
        desc = [r for r in block['describe'] if 'group' not in r]
        for ds in sorted({r['dataset'] for r in desc}):
            for target in sorted({r['target'] for r in desc if r['dataset'] == ds}):
                rows = [r for r in desc if r['dataset'] == ds and r['target'] == target]
                reps = sorted({r['rep'] for r in rows}, key=lambda x: (x.split('_')[0], int(x.split('_')[1]) if '_' in x else 0, x))
                L += [f'### {ds} — {target}', '', '| model | ' + ' | '.join(reps) + ' |', '|---|' + '---|' * len(reps)]
                for model in sorted({r['model'] for r in rows}):
                    cells = []
                    for rep in reps:
                        r = next((x for x in rows if x['model'] == model and x['rep'] == rep), None)
                        cells.append(f'{fmt(r["mean_excess"])} {ci(r["ci95"])} z{r["mean_z"]:.1f} (n{r["n"]})' if r else '')
                    L.append(f'| {model} | ' + ' | '.join(cells) + ' |')
                L.append('')
        L += [f'### {source} contrast families', '']
        for f in block['families']:
            L += [f'**{f["family_id"]}** — {f["status"]}, n {f["complete_n"]}/{f["expected_n"]}, critical {f["critical"] if f["critical"] is None else round(f["critical"], 3)}', '',
                  '| member | estimate | simultaneous 95% |', '|---|---:|---|']
            L += [f'| {m["name"]} | {fmt(m["estimate"]) if "estimate" in m else "n/a"} | {ci(m.get("simultaneous_95"))} |' for m in f['members']]
            L.append('')
    return '\n'.join(L) + '\n'


def main():
    out = {'version': 'CS_ATLAS_SUMMARY_v1', 'plan_sha256': CA.B.sha(CA.PLAN_DIR / 'plan.json'),
           'summary_module_sha256': CA.B.sha(Path(__file__)), 'sources': {}}
    for source in ('aln41', 'aln34'):
        d = load(source)
        if d is None:
            continue
        if source == 'aln41':
            need = lambda ds, model: 1 if model == 'B0' else 3
        else:
            need = lambda ds, model: None
        P = person_table(d, need)
        out['sources'][source] = {'receipt': json.loads((CA.RESULTS / f'receipt_{source}.json').read_text()),
                                  'describe': describe(P), 'families': contrast_families(P, source)}
    (CA.RESULTS / 'summary.json').write_text(json.dumps(out, indent=1, default=float) + '\n')
    (CA.RESULTS / 'ATLAS.md').write_text(markdown(out))
    print('written', CA.RESULTS / 'ATLAS.md')
