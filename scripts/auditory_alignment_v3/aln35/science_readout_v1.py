"""Readable readout of completed S34 science_v2 and prior_science aggregates (Slurm only).

Reads the frozen aggregate JSONs; recomputes nothing. Every cell of every family goes to
long CSVs; the markdown shows declared views without test-side peak selection.
Inference marks use each family's simultaneous band ("band_*" or developmental sim_*).
"""
import csv
import hashlib
import json
import os
from pathlib import Path

ROOT = Path('/home/infres/yinwang/EEG_auditory')
SCI = ROOT / 'results/auditory_alignment_v3/aln34/science_v2/science.json'
PRIOR = ROOT / 'results/auditory_alignment_v3/aln34/prior_science/science.json'
OUT = ROOT / 'results/auditory_alignment_v3/aln35/science_readout_v1'
DOCS = ROOT / 'docs/auditory_alignment_v3/aln35'
CENTERS = ['-200', '0', '200', '400', '600']
WINDOWS = ['full', 'pre', '0_200', '200_400', '400_600']
MASKS = ['pre', '0_200', '200_400', '400_600']
PUBLIC_MODELS = [('local', 'local/NCE/ALN32_LOCAL_SUPPORT/model'), ('raw20', 'local/NCE/ALN32_LOCAL_SUPPORT/raw'),
                 ('CBpre', 'cbramod/pretrained_full/NCE/ALN32_TRUE_FULL/model'),
                 ('CBrand', 'cbramod/random_full/NCE/ALN32_TRUE_FULL/model'),
                 ('REVEpre', 'reve/pretrained_full/NCE/ALN32_TRUE_FULL/model')]
TARGETS = [('env', 'direct'), ('onset', 'direct'), ('spec', 'direct'), ('flux', 'direct'), ('Ac', 'direct'),
           ('Lz', 'direct'), ('onset', 'conditional'), ('spec', 'conditional'), ('flux', 'conditional'),
           ('Ac', 'conditional'), ('Lz', 'conditional'), ('env', 'history_conditional')]
PRIVATE_CFGS = ['E_LOCAL|NCE|lag_local_tokens|full', 'E_LOCAL|CS_SINGLE|lag_local_tokens|full',
                'E_PUBLIC_TRANSFER|NCE|lag_local_tokens|task_partial',
                'E_PUBLIC_TRANSFER|CS_SINGLE|lag_local_tokens|task_partial',
                'E_GENERIC|NCE|cbramod|pretrained_full', 'E_GENERIC|CS_SINGLE|cbramod|pretrained_full',
                'E_GENERIC|NCE|cbramod|random_full', 'E_GENERIC|CS_SINGLE|cbramod|random_full',
                'E_GENERIC|NCE|reve|pretrained_full', 'E_GENERIC|CS_SINGLE|reve|pretrained_full']
# CORRECTION_PRIVATE_PRE_ACCESS: native local / E_PUBLIC_TRANSFER pre input was all zeros.
PRE_INVALID = ('E_LOCAL|', 'E_PUBLIC_TRANSFER|')
ARMS = ['AP', 'XP', 'J*', 'XM']
FIELDS = ['source', 'dataset', 'scope', 'metric', 'seed_scope', 'group', 'label', 'est', 'se',
          'band_low', 'band_high', 'ci_low', 'ci_high', 'n', 'crit']


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def mark(lo, hi, ref=0.0):
    if lo is None or hi is None:
        return '?'
    return '+' if lo > ref else ('−' if hi < ref else '')


def cell(g, i, ref=0.0, digits=3):
    est = g['est'][i]
    if est is None:
        return 'NA'
    return f"{est:+.{digits}f}{mark(g['band_low'][i], g['band_high'][i], ref)}"


def auc_cell(g, i):
    est = g['est'][i]
    return 'NA' if est is None else f"{est:.3f}{mark(g['band_low'][i], g['band_high'][i], 0.5)}"


def rows_of(source, fam, groups=None, scope=None, seed=None):
    groups = groups if groups is not None else fam['groups']
    for gname, g in groups.items():
        for i, label in enumerate(fam['labels']):
            yield {'source': source, 'dataset': fam['dataset'], 'scope': scope or fam['scope'],
                   'metric': fam['metric'], 'seed_scope': seed or fam.get('seed_scope', fam.get('seed')),
                   'group': gname, 'label': label, 'est': g['est'][i], 'se': g['se'][i],
                   'band_low': g['band_low'][i], 'band_high': g['band_high'][i], 'ci_low': g['ci_low'][i],
                   'ci_high': g['ci_high'][i],
                   'n': g['n'] if 'n' in g else f"{g.get('n_a')}/{g.get('n_b')}",
                   'crit': g.get('crit')}


def index(families):
    return {(f['dataset'], f['scope'], f['metric'], str(f.get('seed_scope', f.get('seed')))): f for f in families}


def public_seed(ds):
    return 'complete_seed_mean' if ds == 'dtu' else '3401'


def science_markdown(sci):
    idx = index(sci['families'])
    L = ['# S34 science_v2 readout (content/time 180 + private current/time v2 130)', '',
         f"Source `{SCI.relative_to(ROOT)}` (job {sci['job']}, {sci['time']}), sha256 `{sha(SCI)[:16]}…`. "
         'Readout only: no refit, no new bootstrap. Full cell tables: '
         '`results/auditory_alignment_v3/aln35/science_readout_v1/science_v2_cells.csv`.', '',
         'Marks: `+`/`−` = the family\'s simultaneous band (max-t over its cells) excludes 0 '
         '(AUC: excludes 0.5). No mark = band includes the reference. Bands condition on fitted models; '
         'n = people. DTU = 3-seed mean (seeds averaged within person); FAU/Federici seed 3401; REVE 3401.', '',
         'Public windows: EEG access [c−400, c+600) ms around each sound anchor; centers are overlapping 1-s '
         'access windows, not neural latencies. Matched−mismatch r subtracts an EEG-only within-person '
         'segment-roll baseline.', '']
    for ds in ('dtu', 'fau', 'federici'):
        seed = public_seed(ds)
        L += [f'## Public {ds}: matched − mismatch r on the diagonal (train = test center)', '',
              '| Model | Target | ' + ' | '.join(f'{c} ms' for c in CENTERS) + ' |',
              '|---|---|' + '---|' * len(CENTERS)]
        for mname, mscope in PUBLIC_MODELS:
            for target, kind in TARGETS:
                fam = idx.get((ds, f'public/{mscope}/{target}/{kind}', 'matched_minus_mismatch_r', seed))
                if not fam:
                    continue
                g = fam['groups']['all']
                vals = [cell(g, fam['labels'].index(f'{c}/{c}')) for c in CENTERS]
                L.append(f'| {mname} | {target} {kind} | ' + ' | '.join(vals) + f" |")
        L.append('')
        L += [f'### {ds}: temporal generalization, train at 200 ms (env and onset direct)', '',
              '| Model | Target | ' + ' | '.join(f'test {c}' for c in CENTERS) + ' |',
              '|---|---|' + '---|' * len(CENTERS)]
        for mname, mscope in PUBLIC_MODELS:
            for target in ('env', 'onset'):
                fam = idx.get((ds, f'public/{mscope}/{target}/direct', 'matched_minus_mismatch_r', seed))
                if fam:
                    g = fam['groups']['all']
                    L.append(f'| {mname} | {target} | ' + ' | '.join(
                        cell(g, fam['labels'].index(f'200/{c}')) for c in CENTERS) + ' |')
        L.append('')
        groups = [k for k in next(iter(f['groups'] for f in sci['families'] if f['dataset'] == ds)) if k != 'all']
        L += [f'### {ds}: hearing groups, env direct matched − mismatch r (diagonal 0 / 200 ms)', '',
              '| Model | ' + ' | '.join(f'{g} 0 / 200' for g in groups) + ' |', '|---|' + '---|' * len(groups)]
        for mname, mscope in PUBLIC_MODELS:
            fam = idx.get((ds, f'public/{mscope}/env/direct', 'matched_minus_mismatch_r', seed))
            if fam:
                parts = []
                for gname in groups:
                    g = fam['groups'][gname]
                    parts.append(f"{cell(g, fam['labels'].index('0/0'))} / {cell(g, fam['labels'].index('200/200'))}"
                                 f" (n={g['n']})")
                L.append(f'| {mname} | ' + ' | '.join(parts) + ' |')
        L.append('')

    L += ['## Private current sound (64 children: HA 55, NH 9)', '',
          'Common source-ES logistic readout, positive-affine calibration. Seeds averaged within child (REVE 3401). '
          '`pre` for E_LOCAL and E_PUBLIC_TRANSFER had an all-zero input (CORRECTION_PRIVATE_PRE_ACCESS) and is '
          'shown as `invalid`.', '']
    for metric, label, fmt in (('auc', 'AUC by input window', auc_cell),
                               ('history_gain_bits', 'history increment (bits/trial) by window', cell)):
        L += [f'### {label}', '', '| Configuration | Group | ' + ' | '.join(WINDOWS) + ' |',
              '|---|---|' + '---|' * len(WINDOWS)]
        for cfg in PRIVATE_CFGS:
            seed = '3401' if '|reve|' in cfg else 'complete_seed_mean'
            fam = idx.get(('private_bdf', f'private/windows/{cfg}', metric, seed))
            if not fam:
                continue
            for gname in ('all', 'HA', 'NH'):
                g = fam['groups'][gname]
                vals = []
                for w in WINDOWS:
                    v = fmt(g, fam['labels'].index(w)) if metric == 'auc' else fmt(g, fam['labels'].index(w), 0.0, 4)
                    vals.append('invalid' if w == 'pre' and cfg.startswith(PRE_INVALID) else v)
                L.append(f'| {cfg} | {gname} (n={g["n"]}) | ' + ' | '.join(vals) + ' |')
        L.append('')
    L += ['### Input-mask transfer (AUC, source-only destination calibration; rows train mask, cols test mask)', '']
    for cfg in PRIVATE_CFGS:
        seed = '3401' if '|reve|' in cfg else 'complete_seed_mean'
        fam = idx.get(('private_bdf', f'private/tg/{cfg}/source_only_destination_calibration', 'auc', seed))
        if not fam:
            continue
        g = fam['groups']['all']
        L += [f'{cfg}:', '', '| train \\ test | ' + ' | '.join(MASKS) + ' |', '|---|' + '---|' * len(MASKS)]
        for tr in MASKS:
            vals = []
            for te in MASKS:
                v = auc_cell(g, fam['labels'].index(f'{tr}/{te}'))
                vals.append('invalid' if 'pre' in (tr, te) and cfg.startswith(PRE_INVALID) else v)
            L.append(f'| {tr} | ' + ' | '.join(vals) + ' |')
        L.append('')
    L += ['### Personal output adaptation (rank-4 residual; steps 0/5/20; support = first 10% / 30% blocks)', '',
          '| Configuration | Support | AUC 0 / 5 / 20 | NLL bits 0 / 5 / 20 |', '|---|---|---|---|']
    for cfg in PRIVATE_CFGS:
        seed = '3401' if '|reve|' in cfg else 'complete_seed_mean'
        for frac in ('0.1', '0.3'):
            out = []
            for metric in ('auc', 'nll_bits'):
                fam = idx.get(('private_bdf', f'private/adapt/{cfg}/{frac}', metric, seed))
                if not fam:
                    out.append('NA'); continue
                g = fam['groups']['all']
                f = auc_cell if metric == 'auc' else (lambda gg, i: f"{gg['est'][i]:.4f}")
                out.append(' / '.join(f(g, fam['labels'].index(s)) for s in ('0', '5', '20')))
            L.append(f'| {cfg} | {frac} | ' + ' | '.join(out) + ' |')
    L.append('')
    L += developmental_markdown(sci['developmental'], 'science_v2')
    return L


def developmental_markdown(dev, tag):
    L = [f'## Development ({tag}): simultaneous intervals over all endpoints × coefficients per model', '',
         'Models: (a) all children, age in years + HA indicator; (b) HA only, age + device-use duration in years. '
         'Associations conditional on fitted models; not maturation or treatment effects. Only coefficient cells '
         'whose simultaneous interval excludes 0 are listed; every cell is in the CSV.', '',
         '| Configuration / seed scope | Model | Endpoint | Coefficient | Estimate [simultaneous 95%] |',
         '|---|---|---|---|---|']
    total = hits = 0
    for key, v in dev.items():
        for model in ('all_age_group', 'HA_age_duration'):
            fam = v.get(model, {}).get('simultaneous_coefficient_family', {})
            for name, iv in fam.get('intervals', {}).items():
                total += 1
                if mark(iv['sim_low'], iv['sim_high']):
                    hits += 1
                    ep, coef = name.rsplit('/', 1)
                    L.append(f"| {key} | {model} | {ep} | {coef} | {iv['est']:+.5f} "
                             f"[{iv['sim_low']:+.5f}, {iv['sim_high']:+.5f}] |")
    L += ['', f'{hits} of {total} coefficient cells exclude 0 under their simultaneous family.', '']
    L += ['### Prespecified stage means (descriptive; seed-mean configurations)', '',
          '| Configuration | Stage | n | full AUC | history gain | history − twin | adapt 0.3/20 ΔNLL |',
          '|---|---|---|---|---|---|---|']
    for key, v in dev.items():
        if not (key.endswith('complete_seed_mean') or '|reve|' in key or key.endswith('/3401') and '/' in key and key.split('/')[0] in ('AP', 'XP', 'J*', 'XM', 'S')):
            continue
        for stage, s in v.get('stages', {}).items():
            m = s.get('means', {})
            def f(k, d=4):
                x = m.get(k)
                return 'NA' if x is None else f'{x:.{d}f}'
            L.append(f"| {key} | {stage} | {s.get('n')} | {f('full/auc', 3)} | {f('full/history_gain_bits')} | "
                     f"{f('full/history_minus_twin_bits')} | {f('adapt/0.3/20')} |")
    L.append('')
    return L


def prior_markdown(pr):
    A = pr['arm_comparisons']
    L = ['# Public auditory prior science readout (300/300 targets, seed 3401)', '',
         f"Source `{PRIOR.relative_to(ROOT)}` (job {pr['job']}, {pr['time']}), sha256 `{sha(PRIOR)[:16]}…`. "
         'Readout only. Every arm-level and contrast cell: '
         '`results/auditory_alignment_v3/aln35/science_readout_v1/prior_science_cells.csv`.', '',
         'Contrasts are arm minus scratch S (positive = arm better: higher r/AUC/gain, lower loss). Marks use '
         'each family\'s simultaneous band. AP/XP/J*/XM differ in target and supervision, not only in sound '
         'pairing (see AP_WRONG_RESULTS_V2 for the pairing test).', '']
    for ds in ('dtu', 'fau', 'federici'):
        L += [f'## {ds}: arm − S, matched − mismatch r on the diagonal', '',
              '| Objective | Model/raw | Target | Arm | ' + ' | '.join(f'{c}' for c in CENTERS) + ' |',
              '|---|---|---|---|' + '---|' * len(CENTERS)]
        for a in A:
            if a['dataset'] != ds or a['metric'] != 'matched_minus_mismatch_r':
                continue
            _, obj, rep, target, kind = a['scope'].split('/')
            g = a['groups']['all']
            for arm in ARMS:
                vals = []
                for c in CENTERS:
                    lab = f'{arm}/{c}/{c} versus S/{c}/{c}'
                    vals.append(cell(g, a['labels'].index(lab)) if lab in a['labels'] else 'NA')
                L.append(f'| {obj} | {rep} | {target} {kind} | {arm} | ' + ' | '.join(vals) + ' |')
        L.append('')
    L += ['## Hearing-group differences in arm − S effects (cells whose simultaneous band excludes 0)', '']
    total = 0
    hits = []
    for a in A:
        for comp, g in a.get('group_effect_difference', {}).get('comparisons', {}).items():
            for i, lab in enumerate(a['labels']):
                total += 1
                m = mark(g['band_low'][i], g['band_high'][i])
                if m:
                    hits.append(f"| {a['dataset']} | {a['scope']} | {a['metric']} | {comp} | {lab} | "
                                f"{g['est'][i]:+.4f} [{g['band_low'][i]:+.4f}, {g['band_high'][i]:+.4f}] |")
    L += [f'{len(hits)} of {total} group-difference cells exclude 0.', '']
    if hits:
        L += ['| Dataset | Scope | Metric | Comparison | Cell | Estimate [band] |', '|---|---|---|---|---|---|'] + hits
    L.append('')
    L += ['## Private (64 children): arm − S', '',
          '| Scope | Metric | Contrast | all | HA | NH |', '|---|---|---|---|---|---|']
    for a in A:
        if a['dataset'] != 'private_bdf' or a['metric'] not in ('auc', 'nll_bits', 'history_gain_bits'):
            continue
        for i, lab in enumerate(a['labels']):
            parts = []
            for gname in ('all', 'HA', 'NH'):
                g = a['groups'][gname]
                parts.append(cell(g, i, 0.0, 4))
            invalid = '/pre' in lab and False  # prior science has no pre-access defect (correction scope)
            L.append(f"| {a['scope']} | {a['metric']} | {lab} | " + ' | '.join(parts) + ' |')
    L.append('')
    L += developmental_markdown(pr['development'], 'prior_science')
    return L


def main():
    assert os.environ.get('SLURM_JOB_ID'), 'run under Slurm'
    OUT.mkdir(parents=True, exist_ok=True)
    sci = json.loads(SCI.read_text())
    pr = json.loads(PRIOR.read_text())
    n_rows = {}
    with (OUT / 'science_v2_cells.csv').open('w', newline='') as h:
        w = csv.DictWriter(h, FIELDS); w.writeheader(); k = 0
        for fam in sci['families']:
            for r in rows_of('science_v2', fam):
                w.writerow(r); k += 1
        n_rows['science_v2_cells.csv'] = k
    with (OUT / 'prior_science_cells.csv').open('w', newline='') as h:
        w = csv.DictWriter(h, FIELDS); w.writeheader(); k = 0
        for fam in pr['levels']:
            for r in rows_of('prior_level', fam):
                w.writerow(r); k += 1
        for a in pr['arm_comparisons']:
            for r in rows_of('prior_arm_minus_S', a, seed=str(a['seed'])):
                w.writerow(r); k += 1
            for comp, g in a.get('group_effect_difference', {}).get('comparisons', {}).items():
                for r in rows_of('prior_group_difference', a, groups={comp: g}, seed=str(a['seed'])):
                    w.writerow(r); k += 1
        n_rows['prior_science_cells.csv'] = k
    with (OUT / 'development.csv').open('w', newline='') as h:
        w = csv.writer(h); w.writerow(['source', 'configuration', 'model', 'endpoint', 'coefficient', 'est',
                                       'sim_low', 'sim_high', 'n']); k = 0
        for tag, dev in (('science_v2', sci['developmental']), ('prior_science', pr['development'])):
            for key, v in dev.items():
                for model in ('all_age_group', 'HA_age_duration'):
                    m = v.get(model, {})
                    for name, iv in m.get('simultaneous_coefficient_family', {}).get('intervals', {}).items():
                        ep, coef = name.rsplit('/', 1)
                        w.writerow([tag, key, model, ep, coef, iv['est'], iv['sim_low'], iv['sim_high'], m.get('n')])
                        k += 1
        n_rows['development.csv'] = k
    (DOCS / 'SCIENCE_V2_READOUT.md').write_text('\n'.join(science_markdown(sci)) + '\n')
    (DOCS / 'PRIOR_SCIENCE_READOUT.md').write_text('\n'.join(prior_markdown(pr)) + '\n')
    receipt = {'job': os.environ['SLURM_JOB_ID'], 'script_sha256': sha(__file__),
               'inputs': {str(SCI.relative_to(ROOT)): sha(SCI), str(PRIOR.relative_to(ROOT)): sha(PRIOR)},
               'families': {'science_v2': len(sci['families']), 'prior_levels': len(pr['levels']),
                            'prior_arm_comparisons': len(pr['arm_comparisons'])},
               'rows': n_rows, 'status': 'pass'}
    (OUT / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
