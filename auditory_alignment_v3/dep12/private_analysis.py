"""DEP12 Agent P: per-person private rows (05 §2 schema), F_PRIVATE / F_SELECTION families and descriptive tables (CPU).

Inputs: private_use outputs (REC/use_v1/<encoder>) and selection outputs (REC/selection_v1/<set>_s<seed>), both bound to the
frozen binding_v1. Person = child (pseudonymous childN); metrics are computed per child x training seed x support seed, then
averaged within the child; seeds are averaged within the child for the merged contrast; missing people are never zero-filled.
Families (05 §3), aln41.analysis.family with B_REP = 10,000 at run time (identity bootstrap-t, family max-|T*|):
  F_PRIVATE[seed]:   U0 'all_trials' G (bits/trial): cs_pair@s - B0, cs_pair@s - info_nce@s, cs_pair@s - sigmoid@s
  F_PRIVATE[merged]: the same with each child's mean over seeds 3401/3407/3413 (B0 constant)
  F_SELECTION[seed]/[merged]: U10 query log2-score: delta_cs - fixed, delta_cs - support_cv, delta_cs - uniform
  F_SELECTION_EXT[seed]/[merged] (added, DECISIONS P17-P19): delta_train_profile - fixed, delta_cs_pca64 - support_cv,
  delta_cs_pca64 - delta_cs
Descriptive (not registered families; labelled): private δ profile method differences, mechanism controls (raw_cs@3401,
cs_pair_wrong@3401), reused encoders vs B0 (aln41 arms by seed, REVE0, MINDMIX_branch), the exploratory 'aln41' selection set,
and the recovered ALN4.1 R2 cross-stimulus results (pure tone -> bapa) with the 8 same-day pairs.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import datetime
import json
import math
import os
from pathlib import Path

import numpy as np

from . import private_features as PF
from . import private_fleet as FL
from . import private_use as PU
from . import selection as SEL

SCHEMA = 'dep12_private_rows_v1'
SEEDS = (3401, 3407, 3413)
OUT_ROWS = PF.RESULTS / 'per_person_private.jsonl'
OUT_JSON = PF.RESULTS / 'private_contrasts.json'
OUT_MD = PF.RESULTS / 'private_contrasts.md'
B_DRAWS = 10000
WINDOW = 'real [-200, +600) ms at 250 Hz -> 160 samples at 200 Hz + 200 ms leading zeros (1 s container); pad_mask stored'
read, write, sha, digest = PF.read, PF.write, PF.sha, PF.digest


def family(fid, unit, members, people):
    from ..aln41 import analysis as AN
    old = AN.B_REP
    AN.B_REP = B_DRAWS
    try:
        out = AN.family(fid, unit, members, people)
    finally:
        AN.B_REP = old
    out['method'] = (f'aln41.analysis.family (sci_r1 identity bootstrap-t, family max-|T*|) with B = {B_DRAWS} '
                     f'(module constant set at run time); people = children')
    out['bootstrap_draws'] = B_DRAWS
    return out


def code_sha():
    return {k: v for k, v in SEL.sources().items()}


# ----------------------------------------------------------------------------------------------- loading
def use_rows(name):
    odir = PU.BASE / name.replace('@', '_at_')
    if not (odir / 'complete.json').exists():
        return None
    done = read(odir / 'complete.json')
    out = {}
    for f in PF.FOLDS:
        p = odir / f'fold{f}.json'
        assert sha(p) == done['folds_sha256'][str(f)]
        out[f] = read(p)
    return out


def sel_rows(tag):
    d = SEL.BASE / tag
    if not (d / 'complete.json').exists():
        return None
    done = read(d / 'complete.json')
    out = {}
    for f in PF.FOLDS:
        p = d / f'fold{f}.json'
        assert sha(p) == done['folds_sha256'][str(f)]
        out[f] = read(p)
    return out


def encoder_info(name, folds):
    m = folds[0]['encoder_meta']
    seed = m.get('seed')
    return {'arm': name, 'backbone': m.get('arch'), 'training_mode': m.get('mode'), 'train_seed': seed,
            'feature_layer': m.get('layer'), 'access_level': m.get('data_access'), 'checkpoint_sha256': m.get('checkpoint_sha256'),
            'input_support_flag': m.get('input_support_flag')}


# ----------------------------------------------------------------------------------------------- rows
def base_row(info, bind, child, fold, **kw):
    r = {'schema_version': SCHEMA, 'experiment_id': None, **{k: info[k] for k in ('arm', 'backbone', 'training_mode', 'train_seed',
                                                                                    'feature_layer', 'access_level', 'checkpoint_sha256')},
         'cohort': 'private_bdf', 'participant_id': child, 'outer_fold': fold, 'support_seed': None, 'support_budget': None,
         'task': None, 'descriptor': None, 'window_support_ms': WINDOW, 'endpoint': None, 'value': None, 'n_trials': None,
         'n_anchors': None, 'split_sha256': bind.sha256, 'query_sha256': None, 'calibration_sha256': None,
         'code_commit': 'no git; module sha256 in private_contrasts.json:code', 'status': 'complete', 'missing_reason': None,
         'input_support_flag': info['input_support_flag'], 'group': bind.by_id[child]['group'], 'protocol': bind.by_id[child]['protocol']}
    r.update(kw)
    return r


def u0_person_rows(name, folds, bind):
    info = encoder_info(name, folds); rows = []
    for f, fold in folds.items():
        for c, rec in fold['u0'].items():
            for q in ('all_trials', 'contract_query'):
                m = rec[q]
                qsha = digest(np.arange(rec['n_trials']).tolist() if q == 'all_trials' else bind.arr(c, 'query').tolist())
                for ep in ('G_bits', 'auc_EEG_part', 'auc_E', 'auc_B1', 'logscore_E', 'logscore_B1', 'clipped_fraction_E', 'clipped_fraction_B1'):
                    rows.append(base_row(info, bind, c, f, experiment_id='DEP12_PRIVATE_U0', support_budget='U0', task='current_event_beyond_history',
                                         descriptor='current_label', endpoint=f'{q}/{ep}', value=m[ep], n_trials=m['n'], query_sha256=qsha,
                                         status='complete' if m[ep] is not None else 'not_estimable',
                                         missing_reason=None if m[ep] is not None else 'one-class query'))
            st = rec['strict_twin']
            for ep in ('E_minus_B1_bits', 'E_minus_twin_bits', 'twin_minus_B1_bits', 'full_readout_G_on_subset_bits', 'subset_fraction'):
                v = st.get(ep)
                rows.append(base_row(info, bind, c, f, experiment_id='DEP12_PRIVATE_U0_TWIN', support_budget='U0', task='strict_other_block_twin',
                                     descriptor='current_label', endpoint=f'strict_twin/{ep}', value=v, n_trials=st.get('n_subset'),
                                     query_sha256=st.get('twin_pair_sha256'), status='complete' if v is not None else 'missing',
                                     missing_reason=None if v is not None else st.get('status')))
        cal = fold['profile_calibration']
        for c, cells in fold['profile'].items():
            for key, m in cells.items():
                panel, mult = key.split('_x')
                r = base_row(info, bind, c, f, experiment_id='DEP12_PRIVATE_DELTA_PROFILE', task='private_delta_profile',
                             descriptor='current_label_delta_kernel', endpoint=f'excess_cs_nats/{key}', value=m.get('excess_cs_nats'),
                             n_anchors=m.get('n'), calibration_sha256=digest({k: cal.get(k) for k in ('overlap_sigma', 'n_people', 'panel_id')}),
                             status='complete' if m.get('excess_cs_nats') is not None else 'missing', missing_reason=None if m.get('status') == 'measured' else m.get('status'))
                r.update(raw_cs=m.get('raw_cs_nats'), null_mean=m.get('null_mean_nats'), null_sd=m.get('null_sd_nats'), excess_cs=m.get('excess_cs_nats'),
                         z=m.get('z'), z_status=m.get('z_status'), null_design_id=PU.NULL_DESIGN, actual_null_draws=m.get('n_null_draws'),
                         sigma_u=m.get('sigma_u'), sigma_y=None, kernel_diagnostics={'k': m.get('k_diagnostics'), 'l': m.get('l_diagnostics')},
                         panel_id=f'{c}/{panel}', sigma_multiplier=float(mult))
                rows.append(r)
    return rows


def sel_person_rows(tag, folds, bind):
    rows = []
    for f, fold in folds.items():
        order = fold['order']
        for c, ch in fold['children'].items():
            for ss, d in ch['draws'].items():
                for pol, m in d['policies'].items():
                    for ep in ('logscore_bits', 'G_vs_B1cal_bits', 'auc', 'clipped_fraction'):
                        rows.append({'schema_version': SCHEMA, 'experiment_id': 'DEP12_PRIVATE_U10_SELECTION', 'arm': f'policy:{pol}',
                                     'candidate_set': tag, 'chosen': d['decision'].get(pol), 'fallback': d['fallback'].get(pol),
                                     'backbone': 'cbramod_or_candidate', 'training_mode': None, 'train_seed': fold['seed'], 'cohort': 'private_bdf',
                                     'participant_id': c, 'outer_fold': f, 'support_seed': int(ss), 'support_budget': 'U10', 'task': 'u10_selection',
                                     'descriptor': 'current_label', 'feature_layer': None, 'window_support_ms': WINDOW, 'endpoint': ep,
                                     'value': m[ep], 'n_trials': m['n'], 'n_anchors': d['n_support'], 'access_level': 'labelled personal support (U10)',
                                     'checkpoint_sha256': None, 'split_sha256': bind.sha256, 'query_sha256': ch['query_sha256'],
                                     'calibration_sha256': None, 'code_commit': 'no git; see private_contrasts.json:code',
                                     'status': 'complete' if m[ep] is not None else 'not_estimable', 'missing_reason': None,
                                     'group': ch['group'], 'protocol': ch['protocol']})
                for n in order:
                    cr = d['candidates'][n]
                    rows.append({'schema_version': SCHEMA, 'experiment_id': 'DEP12_PRIVATE_U10_CANDIDATE', 'arm': n, 'candidate_set': tag,
                                 'train_seed': fold['seed'], 'cohort': 'private_bdf', 'participant_id': c, 'outer_fold': f, 'support_seed': int(ss),
                                 'support_budget': 'U10', 'task': 'u10_candidate', 'endpoint': 'logscore_bits', 'value': cr['query']['logscore_bits'],
                                 'auc': cr['query']['auc'], 'offset_c': cr['offset_c'], 'cv_risk_bits': cr['cv_risk_bits'],
                                 'delta_excess_cs_nats': cr['delta'].get('excess_cs_nats'), 'delta_status': cr['delta'].get('status'),
                                 'delta_pca64_excess_cs_nats': cr['delta_pca64'].get('excess_cs_nats'),
                                 'n_trials': cr['query']['n'], 'n_anchors': d['n_support'], 'split_sha256': bind.sha256,
                                 'query_sha256': ch['query_sha256'], 'status': 'complete', 'missing_reason': None,
                                 'checkpoint_sha256': fold['candidates'][n]['checkpoint_sha256'], 'group': ch['group'], 'protocol': ch['protocol']})
    return rows


# ----------------------------------------------------------------------------------------------- per-child endpoint maps
def u0_map(folds, query='all_trials', key='G_bits'):
    out = {}
    for fold in folds.values():
        for c, rec in fold['u0'].items():
            out[c] = rec[query][key]
    return out


def twin_map(folds, key):
    return {c: rec['strict_twin'].get(key) for fold in folds.values() for c, rec in fold['u0'].items()}


def profile_map(folds, cell='n128_x1'):
    return {c: cells[cell].get('excess_cs_nats') for fold in folds.values() for c, cells in fold['profile'].items() if cell in cells}


def sel_map(folds, policy, key='logscore_bits'):
    return {c: ch['child_mean_over_support_seeds'][policy][key] for fold in folds.values() for c, ch in fold['children'].items()}


def diff(a, b):
    return {p: (a[p] - b[p]) if p in b and a.get(p) is not None and b.get(p) is not None else None for p in a}


def mean_over(maps):
    """Child mean over seeds; a child enters only when every seed contributes (no partial-seed means)."""
    people = set.intersection(*[set(m) for m in maps]) if maps else set()
    return {p: (float(np.mean([m[p] for m in maps])) if all(m.get(p) is not None for m in maps) else None) for p in people}


def describe(m):
    v = np.array([x for x in m.values() if x is not None], float)
    return {'n': int(len(v)), 'mean': float(v.mean()) if len(v) else None, 'sd': float(v.std(ddof=1)) if len(v) > 1 else None,
            'n_positive': int((v > 0).sum())}


# ----------------------------------------------------------------------------------------------- cross-stimulus recovery
def cross_stim_recovery():
    p = PF.ROOT / 'results/auditory_alignment_v3/aln41/r2/contrasts.json'
    d = read(p)
    fams = {f['family_id']: f for f in d['families'] if f['family_id'].startswith('F_CROSS_STIM')}
    pairs = d.get('cross_stim_same_day_pairs', [])
    desc = {}
    for arm in ('B0', 'TCS', 'TNCE'):
        for route in ('within', 'transfer', 'refit'):
            v = [r[f'{arm}:{route}'] for r in pairs if r.get(f'{arm}:{route}') is not None]
            desc[f'{arm}:{route}'] = {'n_pairs': len(v), 'mean_auc': float(np.mean(v)) if v else None,
                                      'min': float(np.min(v)) if v else None, 'max': float(np.max(v)) if v else None}
    return {'source': str(p.relative_to(PF.ROOT)), 'source_sha256': sha(p), 'original_protocol': 'ALN4.1 R2 F_CROSS_STIM (route A: MFF pure tone -> MFF bapa, deviant vs standard)',
            'original_commit': 'local after publish_036 (not pushed)', 'retrospective_reanalysis': False,
            'families': fams, 'same_day_pairs': pairs, 'same_day_pairs_descriptive': desc,
            'note': ('same-day pairs: 8 identity groups with both lanes on the same day; descriptive only. AUC within = pure-tone '
                     'within-lane (person-disjoint folds), transfer = pure-tone readout on bapa, refit = bapa readout on bapa.'),
            'new_frozen_representations': ('not run: the existing formal path extracts three 400 ms crops through the ALN4.1 time '
                                           'bank and mixes slots with q0; applying it to the DEP12 1 s container would need a new '
                                           'extraction/readout definition (03 §6.2 condition not met)')}


# ----------------------------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(); ap.parse_args()
    assert os.environ.get('SLURM_JOB_ID'), 'compute through Slurm'
    os.umask(0o077)
    bind = PF.Binding()
    names = [s['encoder'] for s in FL.specs()]
    use = {n: use_rows(n) for n in names}
    use = {n: v for n, v in use.items() if v is not None}
    rows = []
    for n, folds in use.items():
        rows += u0_person_rows(n, folds, bind)
    sels = {}
    for cset in ('primary', 'aln41'):
        for s in SEEDS:
            v = sel_rows(f'{cset}_s{s}')
            if v is not None:
                sels[f'{cset}_s{s}'] = v
                rows += sel_person_rows(f'{cset}_s{s}', v, bind)
    kids = bind.ids
    fams, desc = [], {}
    G = {n: u0_map(f) for n, f in use.items()}
    Gc = {n: u0_map(f, 'contract_query') for n, f in use.items()}
    AUC = {n: u0_map(f, key='auc_EEG_part') for n, f in use.items()}
    PROF = {n: profile_map(f) for n, f in use.items()}
    PROFP = {n: profile_map(f, 'pca64_n128_x1') for n, f in use.items()}
    # registered F_PRIVATE
    for s in SEEDS:
        need = ['B0', f'cs_pair@{s}', f'info_nce@{s}', f'sigmoid@{s}']
        if all(n in G for n in need):
            fams.append(family(f'F_PRIVATE[{s}]', 'U0 all-trials G, bits/trial',
                               [(f'cs_pair-{o}', diff(G[f'cs_pair@{s}'], G[n])) for o, n in zip(('B0', 'info_nce', 'sigmoid'), need[:1] + need[2:])], kids))
    if all(f'{a}@{s}' in G for a in ('cs_pair', 'info_nce', 'sigmoid') for s in SEEDS) and 'B0' in G:
        mem = []
        for o in ('B0', 'info_nce', 'sigmoid'):
            mem.append((f'cs_pair-{o}', mean_over([diff(G[f'cs_pair@{s}'], G['B0' if o == 'B0' else f'{o}@{s}']) for s in SEEDS])))
        fams.append(family('F_PRIVATE[merged]', 'U0 all-trials G, bits/trial, child mean over seeds', mem, kids))
    # registered F_SELECTION
    for s in SEEDS:
        tag = f'primary_s{s}'
        if tag in sels:
            d = sel_map(sels[tag], 'delta_cs')
            fams.append(family(f'F_SELECTION[{s}]', 'U10 query log2-score, bits/trial',
                               [(f'delta_cs-{o}', diff(d, sel_map(sels[tag], o))) for o in ('fixed', 'support_cv', 'uniform')], kids))
    if all(f'primary_s{s}' in sels for s in SEEDS):
        mem = [(f'delta_cs-{o}', mean_over([diff(sel_map(sels[f'primary_s{s}'], 'delta_cs'), sel_map(sels[f'primary_s{s}'], o)) for s in SEEDS]))
               for o in ('fixed', 'support_cv', 'uniform')]
        fams.append(family('F_SELECTION[merged]', 'U10 query log2-score, child mean over seeds', mem, kids))
    ext = (('delta_train_profile', 'fixed'), ('delta_cs_pca64', 'support_cv'), ('delta_cs_pca64', 'delta_cs'))
    for s in SEEDS:
        tag = f'primary_s{s}'
        if tag in sels:
            fams.append(family(f'F_SELECTION_EXT[{s}]', 'U10 query log2-score; added policies (DECISIONS P17-P19)',
                               [(f'{a}-{b}', diff(sel_map(sels[tag], a), sel_map(sels[tag], b))) for a, b in ext], kids))
    if all(f'primary_s{s}' in sels for s in SEEDS):
        fams.append(family('F_SELECTION_EXT[merged]', 'U10 query log2-score, child mean over seeds; added policies',
                           [(f'{a}-{b}', mean_over([diff(sel_map(sels[f'primary_s{s}'], a), sel_map(sels[f'primary_s{s}'], b)) for s in SEEDS]))
                            for a, b in ext], kids))
    # descriptive / exploratory
    if 'B0' in G:
        others = [n for n in G if n != 'B0']
        desc['levels'] = {n: {'G_all': describe(G[n]), 'G_contract': describe(Gc[n]), 'auc_EEG_part': describe(AUC[n]),
                              'profile_excess_n128': describe(PROF[n]), 'profile_excess_pca64_n128': describe(PROFP[n]),
                              'twin_E_minus_twin': describe(twin_map(use[n], 'E_minus_twin_bits'))} for n in G}
        proto = {c: bind.by_id[c]['protocol'] for c in kids}
        desc['levels_by_protocol'] = {
            n: {p: {'G_all': describe({c: v for c, v in G[n].items() if proto[c] == p}),
                    'profile_excess_n128': describe({c: v for c, v in PROF[n].items() if proto[c] == p})}
                for p in sorted(set(proto.values()))} for n in G}
        desc['levels_by_group'] = {
            n: {g: {'G_all': describe({c: v for c, v in G[n].items() if bind.by_id[c]['group'] == g}),
                    'profile_excess_n128': describe({c: v for c, v in PROF[n].items() if bind.by_id[c]['group'] == g})}
                for g in ('HA', 'NH')} for n in G}
        for label, M, unit in (('G', G, 'U0 all-trials G difference vs B0, bits/trial'), ('AUC', AUC, 'U0 AUC of the readout EEG part, difference vs B0'),
                               ('delta_profile', PROF, 'n128 δ excess CS difference vs B0, nats'),
                               ('delta_profile_pca64', PROFP, 'n128 δ excess CS on the PCA64 kernel variant vs B0, nats')):
            mem = []
            for arm in ('TCS', 'TNCE', 'GCS', 'WRONG'):
                names_ = [f'aln41_{arm}@{s}' for s in SEEDS]
                if all(n in M for n in names_):
                    mem.append((f'aln41_{arm}[3 seeds]-B0', mean_over([diff(M[n], M['B0']) for n in names_])))
            mem += [(f'{n}-B0', diff(M[n], M['B0'])) for n in ('REVE0', 'MINDMIX_branch') if n in M]
            if mem:
                fams.append(family(f'EXPLORATORY_REUSED_VS_B0:{label}', unit + ' (exploratory; reused encoders carry input-support / access flags)', mem, kids))
        for label, M in (('G', G), ('delta_profile', PROF), ('delta_profile_pca64', PROFP)):
            mem = [(f'cs_pair@3401-{n}', diff(M['cs_pair@3401'], M[n])) for n in ('raw_cs@3401', 'cs_pair_wrong@3401')
                   if 'cs_pair@3401' in M and n in M]
            if mem:
                fams.append(family(f'MECHANISM_CONTROLS[3401]:{label}', 'single-seed mechanism controls (descriptive, not a stability claim)', mem, kids))
        for label, M in (('delta_profile', PROF), ('delta_profile_pca64', PROFP), ('AUC', AUC)):
            for s in SEEDS:
                need = ['B0', f'cs_pair@{s}', f'info_nce@{s}', f'sigmoid@{s}']
                if all(n in M for n in need):
                    fams.append(family(f'DESCRIPTIVE_PRIVATE_{label}[{s}]', 'same members as F_PRIVATE on another endpoint (descriptive)',
                                       [(f'cs_pair-{o}', diff(M[f'cs_pair@{s}'], M[n])) for o, n in zip(('B0', 'info_nce', 'sigmoid'), need[:1] + need[2:])], kids))
    for s in SEEDS:
        tag = f'aln41_s{s}'
        if tag in sels:
            d = sel_map(sels[tag], 'delta_cs')
            fams.append(family(f'EXPLORATORY_SELECTION_ALN41[{s}]', 'U10 query log2-score (exploratory candidate set)',
                               [(f'delta_cs-{o}', diff(d, sel_map(sels[tag], o))) for o in ('fixed', 'support_cv', 'uniform')]
                               + [(f'{a}-{b}', diff(sel_map(sels[tag], a), sel_map(sels[tag], b))) for a, b in ext], kids))
    sens = {}
    for n, folds in use.items():
        if PU.sensitivity_for(n):
            sens[n] = {cell: describe(profile_map(folds, cell)) for cell in ('n32_x1', 'n64_x1', 'n128_x0.5', 'n128_x1', 'n128_x2')}
    choice = {}
    for tag, folds in sels.items():
        cnt = defaultdict(int); fb = defaultdict(int)
        for fold in folds.values():
            for ch in fold['children'].values():
                for d in ch['draws'].values():
                    for k, v in d['decision'].items():
                        cnt[f'{k}:{v}'] += 1
                    for k, v in d['fallback'].items():
                        if v:
                            fb[f'{k}:{v}'] += 1
        choice[tag] = {'decisions': dict(cnt), 'fallbacks': dict(fb), 'fixed_by_fold': {f: fold['fixed']['choice'] for f, fold in folds.items()}}
    body = {'version': 'DEP12_PRIVATE_ANALYSIS_v1', 'time': datetime.now().astimezone().isoformat(), 'job': os.environ.get('SLURM_JOB_ID'),
            'binding_sha256': bind.sha256, 'encoders_with_results': sorted(use), 'selection_sets': sorted(sels), 'families': fams,
            'descriptive': desc, 'profile_sensitivity': sens, 'selection_choices': choice, 'cross_stim': cross_stim_recovery(),
            'code': code_sha(), 'notes': ['families: person = child; per-seed and merged; incomplete people never zero-filled',
                                          'δ profile is a description and selector input, not an F_PRIVATE synonym (05 §3)',
                                          'reused encoders carry their input-support / access flags; not a training-objective ablation']}
    write(OUT_JSON, body)
    PF.RESULTS.mkdir(parents=True, exist_ok=True)
    with open(OUT_ROWS, 'w') as fh:
        for r in rows:
            fh.write(json.dumps(r, sort_keys=True, allow_nan=False) + '\n')
    write_md(body)
    print(json.dumps({'rows': len(rows), 'families': [f['family_id'] for f in fams]}), flush=True)


def fmt(x, nd=5):
    return 'NA' if x is None else f'{x:+.{nd}f}'


def write_md(body):
    L = ['# DEP12 private children: results (Agent P)', '',
         f"Generated {body['time']} (job {body['job']}); binding {body['binding_sha256'][:12]}; encoders with results: {len(body['encoders_with_results'])}.", '',
         'G = mean log2 p_E(y) − log2 p_B1(y) on the outer-test children (bits/trial); B1 = history-only single intercept on the same source-ES rows. '
         'Intervals: person bootstrap-t, B = 10,000, simultaneous = family max-|T*|.', '']
    for f in body['families']:
        L += [f"## {f['family_id']} — {f['unit']}", '', f"status {f['status']}, n = {f['complete_n']}/{f['expected_n']}, critical {fmt(f['critical'], 3)}", '',
              '| member | n | estimate | pointwise 95% | simultaneous 95% |', '|---|---:|---:|---|---|']
        for m in f['members']:
            pw = m.get('pointwise_95'); sm = m.get('simultaneous_95')
            L.append(f"| {m['name']} | {m['n']} | {fmt(m.get('estimate'))} | {('[' + fmt(pw[0]) + ', ' + fmt(pw[1]) + ']') if pw else 'NA'} | "
                     f"{('[' + fmt(sm[0]) + ', ' + fmt(sm[1]) + ']') if sm else 'NA'} |")
        L.append('')
    lv = body['descriptive'].get('levels', {})
    if lv:
        L += ['## Levels per encoder (child means; descriptive)', '', '| encoder | n | G all (bits) | G contract | AUC EEG part | δ excess n128 U (nats) | δ excess n128 PCA64 | E−twin (bits) |', '|---|---:|---:|---:|---:|---:|---:|---:|']
        for n, v in sorted(lv.items()):
            L.append(f"| {n} | {v['G_all']['n']} | {fmt(v['G_all']['mean'])} | {fmt(v['G_contract']['mean'])} | {fmt(v['auc_EEG_part']['mean'], 4)} | "
                     f"{fmt(v['profile_excess_n128']['mean'], 6)} | {fmt(v['profile_excess_pca64_n128']['mean'], 6)} | {fmt(v['twin_E_minus_twin']['mean'])} |")
        L.append('')
    lp = body['descriptive'].get('levels_by_protocol', {})
    if lp:
        L += ['## By protocol (child60 = audited alternative sequence; regular = the other 63)', '',
              '| encoder | regular G | regular δ excess | child60 G | child60 δ excess |', '|---|---:|---:|---:|---:|']
        for n, v in sorted(lp.items()):
            r = v.get('regular', {}); a = v.get('alt_sequence_child60_audited', {})
            L.append(f"| {n} | {fmt(r.get('G_all', {}).get('mean'))} | {fmt(r.get('profile_excess_n128', {}).get('mean'), 6)} | "
                     f"{fmt(a.get('G_all', {}).get('mean'))} | {fmt(a.get('profile_excess_n128', {}).get('mean'), 6)} |")
        L.append('')
    if body['profile_sensitivity']:
        L += ['## δ profile sensitivity (seed 3401 encoders and B0; child means of excess CS, nats)', '',
              '| encoder | n32 ×1 | n64 ×1 | n128 ×0.5 | n128 ×1 | n128 ×2 |', '|---|---:|---:|---:|---:|---:|']
        for n, v in sorted(body['profile_sensitivity'].items()):
            L.append('| ' + n + ' | ' + ' | '.join(fmt(v[c]['mean'], 6) for c in ('n32_x1', 'n64_x1', 'n128_x0.5', 'n128_x1', 'n128_x2')) + ' |')
        L.append('')
    if body['selection_choices']:
        L += ['## U10 decisions and fallbacks (counts over child × support seed)', '']
        for tag, v in body['selection_choices'].items():
            L.append(f"- {tag}: fixed by fold {v['fixed_by_fold']}; decisions {v['decisions']}; fallbacks {v['fallbacks'] or 'none'}")
        L.append('')
    xs = body['cross_stim']
    L += ['## Cross-stimulus (recovered ALN4.1 R2, pure tone → bapa; not re-run)', '', f"Source {xs['source']} (sha256 {xs['source_sha256'][:12]}).", '']
    for fid, f in xs['families'].items():
        L += [f'### {fid}', '', '| member | n | estimate | simultaneous 95% |', '|---|---:|---:|---|']
        for m in f['members']:
            sm = m.get('simultaneous_95')
            L.append(f"| {m['name']} | {m['n']} | {fmt(m.get('estimate'))} | {('[' + fmt(sm[0]) + ', ' + fmt(sm[1]) + ']') if sm else 'NA'} |")
        L.append('')
    L += ['### Same-day pairs (8; descriptive mean AUC [min, max])', '', '| arm:route | n | mean AUC | range |', '|---|---:|---:|---|']
    for k, v in xs['same_day_pairs_descriptive'].items():
        L.append(f"| {k} | {v['n_pairs']} | {fmt(v['mean_auc'], 4)} | [{fmt(v['min'], 3)}, {fmt(v['max'], 3)}] |")
    L += ['', xs['note'], '', 'New frozen representations: ' + xs['new_frozen_representations'], '']
    OUT_MD.write_text('\n'.join(L) + '\n')


if __name__ == '__main__':
    main()
