"""Manuscript v2 Tables 2-6 from whatever results exist (CPU; re-run as systems complete). Pending cells print '—'.

Sources
- ALN4.1 arms B0 / TCS / TNCE / GCS / TCS_WRONG: R1 (seed 3401) + R2 (3407, 3413) frozen readouts, private CE fine-tuning,
  age, cross-stimulus and support records (B0 frozen endpoints and B0 age are seed-free -> R1 only; B0 CE is seed-specific).
- Paper arms (paper/arms.py: THSIC, SV_*): arms_v1/<arm>/seed<S>/{frozen_v1,readout_v1}.
- External systems / encoders (mTRF, VLAAI, TCLIP, MINDMIX, REVE, MMB, CALRA): read from their result files when present
  (hooks below); absent -> '—'.
Per person: content folds averaged (both required), then seeds averaged (all expected seeds required, else the person is
missing for that system). Cell = person mean with a percentile person-bootstrap 95% interval (B = 4000). Families are the
frozen manuscript families (paper/manuscript_families.py, FAMILIES_v1.json) computed with aln41.analysis.family once every
member system is complete; until then their members print as pending.
Writes results/auditory_alignment_v3/paper/manuscript_v2/{TABLES.md, tables.json}.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np

from .. import core
from ..aln41 import analysis as AN, analysis_r2 as AR, r2 as R2, source as SRC
from . import arms as PA, manuscript_families as MF

OUT = Path(core.REPO) / 'results/auditory_alignment_v3/paper/manuscript_v2'
ALN41 = ('B0', 'TCS', 'TNCE', 'GCS', 'TCS_WRONG')
SEEDS = (3401, 3407, 3413)
GROUPS = {'dtu': ('NH', 'HI'), 'fau': ('TH', 'HA', 'CI')}
read = SRC.read


# ----------------------------------------------------------------------------------------------- readout records
def readout_dirs():
    """{system: [(seed, readout units dir)]}."""
    out = {a: [(3401, SRC.OUT / 'readout_v1' / 'units')] for a in ALN41}
    for s in SEEDS[1:]:
        for a in ALN41[1:]:
            out[a].append((s, R2.ROOT / f'seed{s}' / 'readout_v1' / 'units'))
    for a in PA.ARMS:
        out[a] = [(s, PA.OUT / a / f'seed{s}' / 'readout_v1' / 'units') for s in SEEDS]
    calra = Path(core.OUT) / 'paper' / 'calra_v1' / 'CALRA'          # paper/calra_cbramod.py (MindMix recipe on the common backbone)
    out['CALRA'] = [(s, calra / f'seed{s}' / 'readout_v1' / 'units') for s in SEEDS]
    for enc in ('REVE', 'MMB'):                                       # paper/encoders.py: seed-free frozen units (as B0)
        out[enc] = [(3401, ENC / 'readout_v1' / 'units')]
    return out


ENC = Path(core.OUT) / 'paper' / 'encoders_v1'
ALIAS = {'MINDMIX': 'MMB'}                                            # encoders.py arm name -> table system key


def expected_seeds(system):
    return (3401,) if system in ('B0', 'REVE', 'MMB') else SEEDS


def collect_readouts():
    """pub[(cohort, system)][person] = endpoints; priv[system][child] = endpoints; groups[(cohort, person)]."""
    per_pub, per_priv, groups = {}, {}, {}
    for system, dirs in readout_dirs().items():
        for seed, d in dirs:
            for p in sorted(d.glob('*.json')) if d.is_dir() else []:
                if 'FAILED' in p.name:
                    continue
                u = read(p); row = u['row']
                if ALIAS.get(row['arm'], row['arm']) != system:
                    continue
                for pid, r in u['people'].items():
                    if row['dataset'] == 'private_bdf':
                        groups[('private_bdf', pid)] = r.get('group')
                        per_priv.setdefault(system, {}).setdefault(pid, {})[seed] = {
                            'content_hist_bits': r['history_increment_bits_q0'], 'time_fixed_loss': r['W0_to_W2_fixed_loss_auc'],
                            'current_auc': r['current_auc_mixture_q0'], 'twin_bits': r['strict_twin'].get('EEG_minus_twin_bits_q0')}
                        continue
                    groups[(row['dataset'], pid)] = r.get('group')
                    h, dr = r.get('env/history_conditional'), r.get('env/direct')
                    att = r.get('attention', {}).get('q0', {}).get('20')
                    per_pub.setdefault((row['dataset'], system), {}).setdefault(pid, {}).setdefault(seed, {})[row['content_fold']] = {
                        'content_r': h and h['mixture_q0_r'], 'content_direct_r': dr and dr['mixture_q0_r'],
                        'time_fixed_loss': h and h['W0_to_W2_fixed_loss'], 'time_refit_recovery': h and h['W0_to_W2_refit_recovery'],
                        'attention20_acc': att and att['accuracy'], 'attention20_nll_bits': att and att.get('nll_bits')}
    pub = {}
    for key, people in per_pub.items():
        need = expected_seeds(key[1])
        for pid, by_seed in people.items():
            seeds = [s for s in need if s in by_seed and sorted(by_seed[s]) == [0, 1]]
            if len(seeds) != len(need):
                continue
            ends = by_seed[seeds[0]][0].keys()
            pub.setdefault(key, {})[pid] = {e: mean([np.mean([by_seed[s][c][e] for c in (0, 1)]) if all(by_seed[s][c][e] is not None for c in (0, 1))
                                                     else None for s in seeds]) for e in ends}
    priv = {}
    for system, kids in per_priv.items():
        need = expected_seeds(system)
        for cid, by_seed in kids.items():
            if all(s in by_seed for s in need):
                priv.setdefault(system, {})[cid] = {e: mean([by_seed[s][e] for s in need]) for e in by_seed[need[0]]}
    return pub, priv, groups


def mean(vals):
    return None if any(v is None for v in vals) else float(np.mean(vals))


def collect_ft(priv):
    dirs = [(3401, SRC.OUT / 'private_ft_v1' / 'units')] + [(s, R2.ROOT / f'seed{s}' / 'private_ft_v1' / 'units') for s in SEEDS[1:]]
    units = [(seed, p) for seed, d in dirs for p in sorted(d.glob('*.json'))]
    ft = ENC / 'private_ft_v1'                                        # paper/encoders.py: selected candidate per encoder x fold only
    units += [(None, p) for p in (sorted((ft / 'units').glob('*.json')) if (ft / 'units').is_dir() else [])]
    per = {}
    for seed, p in units:
        if 'FAILED' in p.name:
            continue
        u = read(p); row = u['row']
        if seed is None:                                              # seed 3401 calibration unit of the chosen candidate + 3407/3413
            sel = ft / 'selection' / f"{row['encoder']}_fold{row['outer_fold']}.json"
            if u.get('probe') or not sel.exists() or read(sel)['choice'] != row['candidate']:
                continue
            seed = row['seed']
        for cid, r in u['test']['selected'].items():
            per.setdefault(ALIAS.get(row['arm'], row['arm']), {}).setdefault(cid, {})[seed] = (r['mixture']['auc'], r['mixture']['nll_bits'])
    for arm, kids in per.items():
        for cid, by_seed in kids.items():
            if all(s in by_seed for s in SEEDS):
                d = priv.setdefault(arm, {}).setdefault(cid, {})
                d['ft_auc'] = float(np.mean([by_seed[s][0] for s in SEEDS])); d['ft_nll_bits'] = float(np.mean([by_seed[s][1] for s in SEEDS]))


def collect_age(priv):
    files = {3401: SRC.OUT / 'age_v1' / 'age_results.json', **{s: R2.ROOT / f'seed{s}' / 'age_v1' / 'age_results.json' for s in SEEDS[1:]}}
    per = {}
    for seed, f in files.items():
        if not f.exists():
            continue
        a = read(f)
        for arm, res in list(a['arms'].items()) + ([('RAW', a['raw_eeg_logvar'])] if seed == 3401 else []):
            for c in res.get('children', []):
                per.setdefault(arm, {}).setdefault(c['id'], {})[seed] = c['model_absolute_error_months']
                if seed == 3401 and arm == 'B0':
                    per.setdefault('MEAN', {}).setdefault(c['id'], {})[seed] = c['train_mean_absolute_error_months']
    f = ENC / 'age_v1' / 'age_results.json'                           # REVE / MindMix branch (seed-free frozen tokens)
    if f.exists():
        for arm, res in read(f)['encoders'].items():
            for c in res.get('children', []):
                per.setdefault(ALIAS.get(arm, arm), {}).setdefault(c['id'], {})[3401] = c['model_absolute_error_months']
    for arm, kids in per.items():
        need = SEEDS if arm in ('TCS', 'TNCE') else (3401,)
        for cid, by_seed in kids.items():
            if all(s in by_seed for s in need):
                priv.setdefault(arm, {}).setdefault(cid, {})['age_abs_err'] = float(np.mean([by_seed[s] for s in need]))


def encoder_support_values():
    """AR.support_values() over paper/encoders.py support units (same aln41/support runner), keys aliased."""
    d = ENC / 'support_v1'
    if not (d / 'units').is_dir():
        return {}
    old = AR.SU.OUT
    try:
        AR.SU.OUT = d; v = AR.support_values()
    finally:
        AR.SU.OUT = old
    return {ALIAS.get(k, k): x for k, x in v.items()}


# ----------------------------------------------------------------------------------------------- formatting
def cell(values, B=4000, seed=20261022, digits=3):
    v = np.array([x for x in values if x is not None], float)
    if not len(v):
        return '—', None
    rng = np.random.default_rng(seed); idx = rng.integers(0, len(v), (B, len(v)))
    lo, hi = np.percentile(v[idx].mean(1), [2.5, 97.5])
    f = f'{{:.{digits}f}}'
    return f'{f.format(v.mean())} [{f.format(lo)}, {f.format(hi)}] (n{len(v)})', {'mean': float(v.mean()), 'ci95': [float(lo), float(hi)], 'n': int(len(v))}


def table(header, rows):
    out = ['| ' + ' | '.join(header) + ' |', '|' + '---|' * len(header)]
    out += ['| ' + ' | '.join(r) + ' |' for r in rows]
    return '\n'.join(out)


def external_public():
    """Hook: {(cohort, system): {person: {'attention20_acc', 'attention20_nll_bits'}}} from the external-decoder results."""
    out = {}
    base = Path(core.REPO) / 'results/auditory_alignment_v3/paper/external_decoders'
    for sub, system in (('mtrf', 'mTRF'), ('vlaai_v2', 'VLAAI'), ('clip', 'TCLIP'), ('mmfau', 'MINDMIX')):   # vlaai: v2 (swap-check correction); mmfau: FAU only (ext_score_v2), DTU from aln42 below
        for f in sorted((base / sub).glob('TABLE2_*.json')) if (base / sub).is_dir() else []:
            for cohort, d in read(f)['datasets'].items():
                people = d['per_person_by_window_s']['20']
                out[(cohort, system)] = {p: {'attention20_acc': v['accuracy'], 'attention20_nll_bits': v['nll_bits']} for p, v in people.items()}
    sens = base / 'sensitivity'                          # post-hoc training-data sensitivity rows (PROTOCOL.json, post_hoc: true)
    for f in sorted(sens.glob('TABLE2_*.json')) if sens.is_dir() else []:
        system = {'TABLE2_MTRF_SS': 'mTRF[ss-trained,post-hoc]'}.get(f.stem, f.stem.replace('TABLE2_READOUT_CS_', '') + '[cs-trained readout,post-hoc]')
        for cohort, d in read(f)['datasets'].items():
            out[(cohort, system)] = {p: {'attention20_acc': v['accuracy'], 'attention20_nll_bits': v['nll_bits']}
                                     for p, v in d['per_person_by_window_s']['20'].items()}
    ctx = base / 'context_matched'                       # post-hoc context-matched rows (context_matched/PROTOCOL.json, post_hoc: true)
    for f in sorted(ctx.glob('TABLE2_*_CTX.json')) if ctx.is_dir() else []:
        system = {'MTRF': 'mTRF', 'VLAAI': 'VLAAI', 'CLIP': 'TCLIP'}[f.stem[len('TABLE2_'):-len('_CTX')]] + '[context-matched,post-hoc]'
        for cohort, d in read(f)['datasets'].items():
            out[(cohort, system)] = {p: {'attention20_acc': v['accuracy'], 'attention20_nll_bits': v['nll_bits']}
                                     for p, v in d['per_person_by_window_s']['20'].items()}
    f = ctx / 'TABLE2_MTRF_CTX_ANCHOR16.json'               # appendum 01 (post hoc): mTRF scored at the proposed system's 16 anchors
    if f.exists():
        a = read(f)
        for label, ds in (('mTRF[ctx, 16-anchor scoring, post-hoc]', a['datasets']),
                          ('mTRF[16-anchor scoring, post-hoc]', a['secondary_mtrf_main_anchor16']['datasets'])):
            for cohort, d in ds.items():
                out[(cohort, label)] = {p: {'attention20_acc': v['accuracy'], 'attention20_nll_bits': v['nll_bits']}
                                        for p, v in d['per_person_by_window_s']['20'].items()}
    f = Path(core.REPO) / 'results/auditory_alignment_v3/aln42/external/EXTERNAL_COMPARISON.json'
    if f.exists():
        ext = read(f).get('per_person', {}).get('external', {})
        if ext:
            out[('dtu', 'MINDMIX')] = {p: {'attention20_acc': v['accuracy'], 'attention20_nll_bits': v['nll_bits']} for p, v in ext.items()}
    return out


def build():
    pub, priv, groups = collect_readouts(); collect_ft(priv); collect_age(priv)
    pub.update(external_public())
    md, js = ['# Manuscript v2 tables (auto-generated; pending cells "—")', '',
              'Person means with percentile person-bootstrap 95% intervals; seeds averaged within person first. '
              'Families (frozen, FAMILIES_v1.json) appear once every member system is complete.', ''], {}

    # Table 2
    systems2 = ('mTRF', 'VLAAI', 'TCLIP', 'MINDMIX', 'TCS', 'B0', 'TNCE', 'mTRF[ss-trained,post-hoc]',
                'B0[cs-trained readout,post-hoc]', 'TCS[cs-trained readout,post-hoc]', 'TNCE[cs-trained readout,post-hoc]',
                'mTRF[context-matched,post-hoc]', 'VLAAI[context-matched,post-hoc]',
                'mTRF[ctx, 16-anchor scoring, post-hoc]', 'mTRF[16-anchor scoring, post-hoc]')
    hdr = ['System'] + [f'{c.upper()} {g}' for c in ('dtu', 'fau') for g in GROUPS[c]] + ['DTU all', 'FAU all']
    rows = []
    for s in systems2:
        r = [s]
        for c in ('dtu', 'fau'):
            for g in GROUPS[c]:
                people = {p: v for p, v in pub.get((c, s), {}).items() if str(groups.get((c, p))).upper() == g}
                a, _ = cell([v['attention20_acc'] for v in people.values()]); n, _ = cell([v.get('attention20_nll_bits') for v in people.values()])
                r.append(f'{a.split(" (")[0]} / {n.split(" [")[0]}' if a != '—' else '—')
        for c in ('dtu', 'fau'):
            vals = pub.get((c, s), {})
            a, ja = cell([v['attention20_acc'] for v in vals.values()]); n, jn = cell([v.get('attention20_nll_bits') for v in vals.values()])
            r.append(f'{a} / {n.split(" [")[0]}' if a != '—' else '—'); js[f'T2:{c}:{s}'] = {'acc': ja, 'nll_bits': jn}
        rows.append(r)
    md += ['## Table 2 — external auditory decoding, 20-s queries (accuracy [95% CI] / NLL bits per decision)', '', table(hdr, rows), '']

    # Table 3
    rows = []
    for s, label in (('B0', 'CBraMod'), ('REVE', 'REVE'), ('MMB', 'MindMix aligned EEG branch'), ('TCS', 'Proposed temporal CS'), ('TNCE', '(matched InfoNCE)')):
        vals = priv.get(s, {}); r = [label]
        for e, d in (('current_auc', 3), ('content_hist_bits', 4), ('ft_auc', 3), ('ft_nll_bits', 4)):
            t, j = cell([v.get(e) for v in vals.values()], digits=d); r.append(t); js[f'T3:{s}:{e}'] = j
        rows.append(r)
    md += ['## Table 3 — EEG-only transfer to private pediatric events (64 children)', '',
           table(['Representation', 'Frozen event AUC', 'Frozen conditional gain (bits/trial)', 'Full FT AUC', 'Full FT NLL (bits/trial)'], rows), '']

    # Table 4
    cv = AR.cross_values() if (AR.XS.OUT / 'plan.json').exists() else {}
    for f in sorted((ENC / 'cross_readout_v1' / 'units').glob('*.json')) if (ENC / 'cross_readout_v1' / 'units').is_dir() else []:
        u = read(f); sysk = ALIAS.get(u['row']['arm'], u['row']['arm'])          # seed-free frozen encoders
        for kind in ('transfer', 'refit'):
            for i, v in u['children'][kind].items():
                cv.setdefault(sysk, {}).setdefault(i, {})[kind] = v['auc_q0']
    rows = []
    for s, label in (('B0', 'CBraMod'), ('REVE', 'REVE'), ('MMB', 'MindMix aligned EEG branch'), ('TCS', 'Proposed temporal CS'),
                     ('TNCE', '(matched InfoNCE)'), ('MEAN', 'Training-child mean age'), ('RAW', 'Raw-EEG log variance')):
        r = [label]
        for k in ('transfer', 'refit'):
            if s in ('MEAN', 'RAW'):
                r.append('N/A'); continue
            t, j = cell([v.get(k) for v in cv.get(s, {}).values()]); r.append(t); js[f'T4:{s}:{k}'] = j
        t, j = cell([v.get('age_abs_err') for v in priv.get(s, {}).values()], digits=2); r.append(t); js[f'T4:{s}:age_mae'] = j
        rows.append(r)
    md += ['## Table 4 — readout reuse and developmental information', '',
           table(['Representation', 'Transferred syllable AUC', 'Refitted syllable AUC', 'Age MAE (months)'], rows), '']

    # Table 5
    sv = AR.support_values() if (AR.SU.OUT / 'units').exists() else {}
    sv.update(encoder_support_values())
    rows = []
    for s, label in (('B0', 'CBraMod'), ('REVE', 'REVE'), ('MMB', 'MindMix aligned EEG branch'), ('TCS', 'Proposed temporal CS'),
                     ('TNCE', 'Matched multi-positive InfoNCE')):
        kids = {c: v for c, v in sv.get(s, {}).items() if v}
        d = [v.get('delta_U30') for v in kids.values()]; c_ = [v.get('cal_U30') for v in kids.values()]
        diffs = [(a - b) if a is not None and b is not None else None for a, b in zip(d, c_)]
        r = [label]
        for name, vals in (('temporal', d), ('calibration', c_), ('difference', diffs)):
            t, j = cell(vals, digits=5); r.append(t); js[f'T5:{s}:{name}'] = j
        rows.append(r)
    md += ['## Table 5 — personal adaptation with the full early support pool (U30), NLL reduction in bits/trial', '',
           table(['Representation', 'Temporal gain', 'Calibration gain', 'Temporal − calibration'], rows), '']

    # Table 6
    rows = []
    for s, label in (('B0', 'EEG-only initialization'), ('CALRA', 'MindMix alignment recipe (common backbone)'),
                     ('TNCE', 'Matched multi-positive InfoNCE'), ('THSIC', 'Temporal HSIC with mass correction'),
                     ('GCS', 'CS after temporal pooling'), ('TCS', 'Proposed temporal CS'), ('TCS_WRONG', 'Proposed CS, shuffled sound pairs'),
                     ('SV_env', '(W4) TCS, envelope view only'), ('SV_ss', '(W4) TCS, spectral-structure view only'), ('SV_sc', '(W4) TCS, spectral-change view only')):
        r = [label]
        for c in ('dtu', 'fau'):
            vals = pub.get((c, s), {})
            for e in ('content_direct_r', 'content_r', 'time_fixed_loss'):
                t, j = cell([v.get(e) for v in vals.values()], digits=4); r.append(t); js[f'T6:{c}:{s}:{e}'] = j
        t, j = cell([v.get('content_hist_bits') for v in priv.get(s, {}).values()], digits=4); r.append(t); js[f'T6:private:{s}:content_hist_bits'] = j
        rows.append(r)
    md += ['## Table 6 — matched alignment (common CBraMod backbone, common frozen readouts)', '',
           table(['Alignment method', 'DTU envelope r', 'DTU history-residual r', 'DTU W0→W2 fixed loss', 'FAU envelope r',
                  'FAU history-residual r', 'FAU W0→W2 fixed loss', 'Child conditional gain (bits/trial)'], rows), '']

    # Frozen families (computed only when complete)
    fams = read(MF.OUT)['families']; done = []
    pubsys = lambda c: {s for (cc, s) in pub if cc == c}
    for f in fams:
        if f['table'] == 6 and f['id'].startswith('T6_') and ':' in f['id'] and f['id'].split(':')[1] in ('dtu', 'fau'):
            c = f['id'].split(':')[1]; e = f['endpoint']; T = pub.get((c, 'TCS'), {})
            others = [m.split('-', 1)[1] if m.startswith('TCS-') else m.split('-')[0] for m in f['members']]
            if not all((c, o) in pub for o in others):
                continue
            sign = -1 if e == 'time_fixed_loss' else 1
            members = [(m, AN.diff(T, pub[(c, o)], e, sign)) for m, o in zip(f['members'], others)]
            done.append(AN.family(f['id'], f['unit'], members, sorted(T)))
        elif f['id'] == 'T6_CHILD:private':
            others = [m.split('-', 1)[1] for m in f['members']]
            if all(o in priv for o in others):
                T = priv['TCS']; done.append(AN.family(f['id'], f['unit'], [(m, AN.diff(T, priv[o], 'content_hist_bits')) for m, o in zip(f['members'], others)], sorted(T)))
    # Table 2 families (frozen T2_ACC / T2_NLL per cohort; computed once all four external systems are present)
    for f in fams:
        if f['table'] == 2:
            c = f['id'].split(':')[1]; T = pub.get((c, 'TCS'), {})
            ext = [m.split('-', 1)[1] if m.startswith('TCS-') else m.split('-')[0] for m in f['members']]
            if not T or not all((c, x) in pub for x in ext):
                continue
            key, sign = ('attention20_acc', 1) if f['id'].startswith('T2_ACC') else ('attention20_nll_bits', -1)
            done.append(AN.family(f['id'], f['unit'], [(m, AN.diff(T, pub[(c, x)], key, sign)) for m, x in zip(f['members'], ext)], sorted(T)))
    # Tables 3-5 families (computed once every member system is present for the family)
    sub = lambda A, Bd, key, sign=1: AN.diff(A, Bd, key, sign)
    for f in fams:
        fid = f['id']
        if fid == 'T3_FROZEN:private' and all(x in priv for x in ('TCS', 'B0', 'REVE', 'MMB')):
            T = priv['TCS']; done.append(AN.family(fid, f['unit'], [(m, sub(T, priv[m.split('-')[1]], m.split(':')[0])) for m in f['members']], sorted(T)))
        elif fid == 'T3_FT:private' and all(all(v.get('ft_auc') is not None for v in priv.get(x, {}).values()) and priv.get(x)
                                             and any('ft_auc' in v for v in priv[x].values()) for x in ('TCS', 'B0', 'REVE', 'MMB')):
            T = priv['TCS']; mem = []
            for m in f['members']:
                e, pair = m.split(':'); l, r = pair.split('-')
                mem.append((m, sub(T, priv[r], e) if l == 'TCS' else sub(T, priv[l], e, -1)))
            done.append(AN.family(fid, f['unit'], mem, sorted(T)))
        elif fid == 'T4_XS:bapa' and all(x in cv for x in ('TCS', 'B0', 'REVE', 'MMB')):
            T = cv['TCS']; kids = sorted(i for i, v in T.items() if v.get('transfer') is not None or v.get('refit') is not None)
            done.append(AN.family(fid, f['unit'], [(m, {i: (T[i][m.split(':')[0]] - cv[m.split('-')[1]].get(i, {}).get(m.split(':')[0]))
                                                         if T[i].get(m.split(':')[0]) is not None and cv[m.split('-')[1]].get(i, {}).get(m.split(':')[0]) is not None else None
                                                         for i in kids}) for m in f['members']], kids))
        elif fid == 'T5_SUPPORT:private' and all(sv.get(x) and set(sv[x]) == set(sv['TCS']) and all(v is not None for v in sv[x].values())
                                                      for x in ('B0', 'REVE', 'MMB', 'TCS', 'TNCE')):
            kids = sorted(sv['TCS']); mem = []
            for m in f['members']:
                x, k = m.split(':'); g = lambda key: {c: (sv[x].get(c) or {}).get(key) for c in kids}
                if k == 'delta_U30-cal_U30':
                    a, b = g('delta_U30'), g('cal_U30'); mem.append((m, {c: (a[c] - b[c]) if a[c] is not None and b[c] is not None else None for c in kids}))
                else:
                    mem.append((m, g(k.split('-')[0])))
            done.append(AN.family(fid, f['unit'], mem, kids))
        elif fid == 'T4_AGE:private' and all(x in priv for x in ('TCS', 'B0', 'REVE', 'MMB', 'MEAN', 'RAW')):
            T = priv['TCS']; done.append(AN.family(fid, f['unit'], [(m, sub(T, priv[m.split('-')[0]], 'age_abs_err', -1)) for m in f['members']], sorted(T)))
    md += ['## Frozen manuscript families computed so far', '']
    if not done:
        md += ['None complete yet (each needs every member system).', '']
    for f in done:
        md += [f"**{f['family_id']}** — {f['status']}, n {f.get('complete_n')}/{f.get('expected_n')}", '',
               table(['member', 'estimate', 'simultaneous 95%'],
                     [[m['name'], f"{m['estimate']:+.4f}" if m.get('estimate') is not None else '—',
                       (f"[{m['simultaneous_95'][0]:+.4f}, {m['simultaneous_95'][1]:+.4f}]" if m.get('simultaneous_95') else '—')] for m in f['members']]), '']
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'TABLES.md').write_text('\n'.join(md) + '\n')
    (OUT / 'tables.json').write_text(json.dumps({'cells': js, 'families': done}, indent=1) + '\n')
    print('written', OUT / 'TABLES.md')


if __name__ == '__main__':
    assert os.environ.get('SLURM_JOB_ID'); os.umask(0o022)
    build()
