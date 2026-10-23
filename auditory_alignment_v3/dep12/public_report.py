"""DEP12 public per-person rows, families and descriptive tables (Agent M; package v1.2 05 §2-§4; DECISIONS M9).

Inputs: measure.py cells (results/.../dep12/measurement/public/<ds>/<encoder>/cells.jsonl.gz) and attention.py people files.
Person values: content folds averaged within person (both required; missing stays missing, never zero).
Families (aln41.analysis.family with B_REP = 10,000 set at run time; identity bootstrap-t, family max-|T*|; one person set per
family, so families are bound per cohort):
  F_MEASURE:<DS>:<seed|merged>     main-condition excess, cs_pair - {B0, info_nce, sigmoid} for env, spec, Lz (9 members)
  F_ATTENTION:<DS>:<seed|merged>   20 s accuracy of the dependence decision (a), cs_pair - {B0, info_nce, sigmoid}
  F_ATTENTION_READOUT:<DS>:...     the same for the linear readout decision (b)
  F_MECHANISM:<DS>:seed3401        single-seed diagnostics cs_pair - raw_cs, cs_pair - cs_pair_wrong (measurement env/spec/Lz and
                                   both attention decisions), reported separately from the main families
merged = person mean over seeds 3401 / 3407 / 3413 of each arm (all three required); B0 is one checkpoint, measured once.
Reused encoders (input-support / access flags from encoders.py) get descriptive person-bootstrap means and paired differences to
B0, labelled 'descriptive_different_support_or_access' and never placed in a family with the new-round arms.
Outputs: results/auditory_alignment_v3/dep12/{per_person_public.jsonl, contrasts_public.json, contrasts_public.md}
CLI (Slurm only): python -m auditory_alignment_v3.dep12.public_report
"""
from __future__ import annotations

from datetime import datetime
import gzip
import hashlib
import json
import os
from pathlib import Path

import numpy as np

from .. import core
from . import attention as AT
from . import measure_v5 as M
from . import panels as PN
from . import public_features_v5 as PF

SCHEMA = 'dep12_person_row_v1'
SEEDS = (3401, 3407, 3413)
OTHERS = ('B0', 'info_nce', 'sigmoid')
B_FAMILY = 10000
ATT_EPS = ('attention20_acc_dependence', 'attention20_acc_dependence_z', 'attention20_acc_readout', 'foreign_eeg_acc_dependence',
           'foreign_eeg_acc_readout', 'mean_dep_margin', 'mean_read_margin', 'mean_foreign_dep_margin', 'mean_foreign_read_margin',
           'attention20_acc_dependence_debiased', 'attention20_acc_readout_debiased')
sha, write, read = PN.sha, PN.write, PN.read


def code_commit():
    """Not a git checkout: the digest of the DEP12 public sources stands in for a commit id."""
    src = {**AT.sources(), **PF.sources()}
    return 'local-sha256:' + hashlib.sha256(json.dumps(src, sort_keys=True).encode()).hexdigest()[:16]


def family(fid, unit, members, people):
    from ..aln41 import analysis as A41
    old = A41.B_REP; A41.B_REP = B_FAMILY
    try:
        res = A41.family(fid, unit, members, people)
    finally:
        A41.B_REP = old
    res['method'] = (f'aln41.analysis.family unchanged (sci_r1 identity bootstrap-t, family max-|T*|) with its module constant '
                     f'B_REP = {B_FAMILY} set at run time; people resampled jointly within the cohort')
    return res


def cells(ds, name):
    p = M.MEAS / ds / name / 'cells.jsonl.gz'
    if not p.exists():
        return []
    with gzip.open(p, 'rt') as f:
        return [json.loads(x) for x in f]


def measurement_people(ds, name, condition='main'):
    """{descriptor: {person: excess (cf mean) or None}} and per-cf values."""
    by = {}
    for c in cells(ds, name):
        if c['condition'] != condition or c.get('status', '').startswith('completed') is False:
            continue
        by.setdefault(c['descriptor'], {}).setdefault(c['participant_id'], {})[c['content_fold']] = c['excess_cs_nats']
    return {d: {p: (float(np.mean([v[cf] for cf in PN.CFS])) if all(cf in v for cf in PN.CFS) else None) for p, v in pp.items()}
            for d, pp in by.items()}


def perturb_people(ds, name):
    """Optional 400 ms input-perturbation panel: {window: {descriptor: {person: excess (cf mean)}}}."""
    from . import perturb_v4 as PT
    p = PT.MEAS / ds / name / 'cells.jsonl.gz'
    if not p.exists():
        return {}
    by = {}
    with gzip.open(p, 'rt') as f:
        for line in f:
            c = json.loads(line)
            if c.get('status') == 'completed':
                by.setdefault(c['support'][5:], {}).setdefault(c['descriptor'], {}).setdefault(c['participant_id'], {})[c['content_fold']] = c['excess_cs_nats']
    return {w: {d: {p: float(np.mean([v[cf] for cf in PN.CFS])) for p, v in pp.items() if all(cf in v for cf in PN.CFS)}
                for d, pp in dd.items()} for w, dd in by.items()}


def attention_people(ds, name):
    p = AT.PRED / ds / f'{name}.people.json'
    if not p.exists():
        return {}
    people = {k: dict(v) for k, v in read(p)['people'].items()}
    q = AT.PRED / ds / f'{name}.debiased.people.json'          # post-hoc debiased score (DECISIONS 07:55 / M18), merged in
    if q.exists():
        for k, v in read(q)['people'].items():
            people.setdefault(k, {}).update(v)
    return people


def registry():
    from . import encoders_v4 as ENC
    return ENC.refresh()


def unitize(ds, d):
    """Federici (M20): person unit = identity; the recordings of one identity (HC and HC-v of a child) are averaged."""
    if ds != 'federici' or not d:
        return d
    ident = {q['id']: q['identity'] for q in read(PN.DEFS / ds / 'scan.json')['people']}
    by = {}
    for rec, v in d.items():
        if v is not None:
            by.setdefault(ident[rec], []).append(v)
    return {k: float(np.mean(v)) for k, v in by.items()}


def arm_values(ds, names):
    """Person values of one logical arm (fold-model groups combine their fold models; each person comes from its own folds)."""
    meas, att = {}, {}
    for n in names:
        for d, pp in measurement_people(ds, n).items():
            for p, v in pp.items():
                if v is not None:
                    meas.setdefault(d, {})[p] = v
        for p, v in attention_people(ds, n).items():
            for ep in ATT_EPS:
                if v.get(ep) is not None:
                    att.setdefault(ep, {})[p] = v[ep]
    return {k: unitize(ds, v) for k, v in meas.items()}, {k: unitize(ds, v) for k, v in att.items()}


def fold_model_values(ds, names):
    """aln34 fold models: a person's two content folds come from two different fold models -> combine per-cf cells first."""
    meas, att = {}, {}
    for cond in ('main',):
        byd = {}
        for n in names:
            for c in cells(ds, n):
                if c['condition'] == cond and str(c.get('status', '')).startswith('completed'):
                    byd.setdefault(c['descriptor'], {}).setdefault(c['participant_id'], {})[c['content_fold']] = c['excess_cs_nats']
        for d, pp in byd.items():
            meas[d] = {p: float(np.mean([v[cf] for cf in PN.CFS])) for p, v in pp.items() if all(cf in v for cf in PN.CFS)}
    by = {}
    for n in names:
        for p, v in attention_people(ds, n).items():
            for ep in ATT_EPS:
                for cf, x in v.get(ep + '_by_cf', {}).items():
                    by.setdefault(ep, {}).setdefault(p, {})[int(cf)] = x
    for ep, pp in by.items():
        att[ep] = {p: float(np.mean([v[cf] for cf in PN.CFS])) for p, v in pp.items() if all(cf in v for cf in PN.CFS)}
    return meas, att


def diff(a, b):
    return {p: (a[p] - b[p]) if (p in a and p in b and a[p] is not None and b[p] is not None) else None for p in set(a) | set(b)}


def merged(vals):
    """Person mean over the three seeds (all required)."""
    people = set().union(*[set(v) for v in vals]) if vals else set()
    return {p: (float(np.mean([v[p] for v in vals])) if all(v.get(p) is not None for v in vals) else None) for p in people}


def describe(y):
    from ..sci_r1 import stats as S
    y = np.array([v for v in y if v is not None], float)
    if len(y) < 3:
        return {'n': int(len(y)), 'mean': float(y.mean()) if len(y) else None}
    s = S.summary(y, B=B_FAMILY, seed=20261023)
    return {'n': int(len(y)), 'mean': float(s['est']), 'se': float(s['se']), 'pointwise_95': [float(s['ci_low']), float(s['ci_high'])],
            'method': 'sci_r1.summary identity bootstrap-t, B = 10000 (descriptive)'}


def person_rows(ds, name, reg, commit):
    """05 §2 rows for one encoder x cohort (cells per content fold, plus cf-mean person rows and attention)."""
    spec = reg.get(name, {}); rows = []
    feat_dir, rec = PF.feature_dir(name, ds)
    meta = read(feat_dir / 'meta.json') if feat_dir else {}
    calp = M.MEAS / ds / name / 'calibration.json'
    cal_sha = sha(calp) if calp.exists() else None
    defs = PN.defs(ds)
    common = {'schema_version': SCHEMA, 'experiment_id': f'DEP12_PUBLIC_{ds.upper()}', 'arm': name, 'backbone': spec.get('arch'),
              'training_mode': spec.get('training_mode'), 'train_seed': spec.get('seed'), 'cohort': ds, 'support_seed': None,
              'support_budget': None, 'feature_layer': (meta.get('meta') or {}).get('layer'),
              'window_support_ms': list(PN.SUPPORT_MS), 'checkpoint_sha256': spec.get('sha256'),
              'split_sha256': defs['panels_sha256'], 'calibration_sha256': cal_sha, 'code_commit': commit,
              'input_support_flag': spec.get('input_support_flag'), 'data_access': spec.get('data_access')}
    for c in cells(ds, name):
        ok = str(c.get('status', '')).startswith('completed')
        rows.append({**common, 'participant_id': c['participant_id'], 'outer_fold': c['person_fold'], 'content_fold': c['content_fold'],
                     'task': 'common_measurement', 'descriptor': c['descriptor'], 'condition': c['condition'],
                     'endpoint': 'excess_cs_nats', 'value': c.get('excess_cs_nats') if ok else None, 'n_trials': None,
                     'n_anchors': c.get('n_anchors'), 'access_level': 'target_train_unlabelled_calibration',
                     'query_sha256': defs['panels_sha256'], 'status': 'completed' if ok else c.get('status'),
                     'missing_reason': c.get('missing_reason'), 'raw_cs': c.get('raw_cs_nats'), 'null_mean': c.get('null_mean_nats'),
                     'null_sd': c.get('null_sd_nats'), 'excess_cs': c.get('excess_cs_nats'), 'z': c.get('z'), 'z_status': c.get('z_status'),
                     'null_design_id': c.get('null_design'), 'actual_null_draws': c.get('n_null_draws'), 'sigma_u': c.get('sigma_u'),
                     'sigma_y': c.get('sigma_y'), 'sigma_multiplier': c.get('sigma_multiplier'),
                     'kernel_diagnostics': {'k': c.get('k_diagnostics'), 'l': c.get('l_diagnostics'),
                                            'A': c.get('joint_square'), 'B': c.get('marginal_product_square'), 'C': c.get('cross_overlap')},
                     'panel_id': c['panel_id'], 'group': c.get('group')})
    for p, v in attention_people(ds, name).items():
        for ep in ATT_EPS:
            for cf, x in v.get(ep + '_by_cf', {}).items():
                rows.append({**common, 'participant_id': p, 'outer_fold': defs['folds'].get(p), 'content_fold': int(cf),
                             'task': 'attention_20s', 'descriptor': 'env', 'endpoint': ep, 'value': x,
                             'n_trials': v['n_windows'].get(str(cf)), 'n_anchors': PN.QUERY_N,
                             'access_level': ('target_train_single_talker_pairs_readout_no_attention_labels' if 'read' in ep else
                                              'target_train_unlabelled_calibration'),
                             'control': 'foreign_eeg_candidate_bias' if 'foreign' in ep else None, 'post_hoc': 'debiased' in ep,
                             'query_sha256': defs['queries_sha256'], 'status': 'completed', 'missing_reason': None, 'group': v.get('group')})
            rows.append({**common, 'participant_id': p, 'outer_fold': defs['folds'].get(p), 'content_fold': 'mean',
                         'task': 'attention_20s', 'descriptor': 'env', 'endpoint': ep, 'value': v.get(ep),
                         'n_trials': sum(v['n_windows'].values()), 'n_anchors': PN.QUERY_N,
                         'access_level': ('target_train_single_talker_pairs_readout_no_attention_labels' if 'read' in ep else
                                          'target_train_unlabelled_calibration'),
                         'control': 'foreign_eeg_candidate_bias' if 'foreign' in ep else None, 'post_hoc': 'debiased' in ep,
                         'query_sha256': defs['queries_sha256'], 'status': 'completed' if v.get(ep) is not None else 'missing',
                         'missing_reason': None if v.get(ep) is not None else 'one content fold missing', 'group': v.get('group')})
    return rows


def main():
    assert os.environ.get('SLURM_JOB_ID'); os.umask(0o022)
    reg = registry(); commit = code_commit(); plan = {'rows': PF.plan_rows()}
    available = {(r['dataset'], n) for r in plan['rows'] if (PF.FEAT / 'units' / f'{r["id"]}.json').exists() for n in r['encoders']}
    rows = []
    for ds, n in sorted(available):
        if AT.done(n, ds):
            rows.extend(person_rows(ds, n, reg, commit))
    out = M.RESULTS / 'per_person_public.jsonl'
    with open(out, 'w') as f:
        for r in rows:
            f.write(json.dumps(r, allow_nan=False, default=float) + '\n')
    fams, desc = [], {}
    for ds in PF.DATASETS:
        DS = ds.upper()
        vals = {}
        for r in plan['rows']:
            if r['dataset'] != ds:
                continue
            if r['group'].startswith('aln34'):
                if all(AT.done(n, ds) for n in r['encoders']):
                    vals[r['group']] = fold_model_values(ds, r['encoders'])
            else:
                for n in r['encoders']:
                    if AT.done(n, ds):
                        vals[n] = arm_values(ds, [n])
        if not vals:
            continue
        people = sorted({p for m, a in vals.values() for d in list(m.values()) + list(a.values()) for p in d})
        # ---------------------------------------------------------------- main families (new-round arms)
        for tag, seeds in [(f'seed{s}', (s,)) for s in SEEDS] + [('merged', SEEDS)]:
            arms = {}
            for arm in ('cs_pair', 'info_nce', 'sigmoid'):
                got = [vals.get(f'{arm}@{s}') for s in seeds]
                if all(g is not None for g in got):
                    arms[arm] = got
            if 'cs_pair' not in arms or 'B0' not in vals:
                fams.append({'family_id': f'F_MEASURE:{DS}:{tag}', 'status': 'not_available_yet',
                             'missing': [a for a in ('cs_pair', 'info_nce', 'sigmoid') if a not in arms] + ([] if 'B0' in vals else ['B0'])})
                continue

            def series(arm, kind, key):
                if arm == 'B0':
                    return vals['B0'][0 if kind == 'm' else 1].get(key, {})
                return merged([g[0 if kind == 'm' else 1].get(key, {}) for g in arms[arm]])
            mem = [(f'{d}:cs_pair-{o}', diff(series('cs_pair', 'm', d), series(o, 'm', d))) for d in M.descriptors_for(ds) for o in OTHERS
                   if o == 'B0' or o in arms]
            fams.append(family(f'F_MEASURE:{DS}:{tag}', 'excess CS (nats), main condition, cf mean', mem, people))
            for fid, ep in (('F_ATTENTION', 'attention20_acc_dependence'), ('F_ATTENTION_READOUT', 'attention20_acc_readout'),
                            ('F_ATTENTION_DEBIASED', 'attention20_acc_dependence_debiased'),
                            ('F_ATTENTION_READOUT_DEBIASED', 'attention20_acc_readout_debiased')):
                mem = [(f'cs_pair-{o}', diff(series('cs_pair', 'a', ep), series(o, 'a', ep))) for o in OTHERS if o == 'B0' or o in arms]
                if not any(v is not None for _, m in mem for v in m.values()):
                    fams.append({'family_id': f'{fid}:{DS}:{tag}', 'status': 'not_available_yet', 'missing': ['debiased scores']}); continue
                f = family(f'{fid}:{DS}:{tag}', '20 s accuracy (person mean, cf mean)', mem, people)
                if 'DEBIASED' in fid:
                    f.update(post_hoc=True, label='POST HOC / secondary (DECISIONS 2026-10-23 07:55, M18)')
                fams.append(f)
        mech_seeds = [s for s in SEEDS if all(vals.get(f'{a}@{s}') for a in ('cs_pair', 'raw_cs', 'cs_pair_wrong'))]
        for tag, ss in [(f'seed{s}', (s,)) for s in mech_seeds] + ([('merged', SEEDS)] if len(mech_seeds) == 3 else []):
            def mv(arm, k, key):
                return merged([vals[f'{arm}@{s}'][k].get(key, {}) for s in ss])
            mem = [(f'{d}:cs_pair-{lab}', diff(mv('cs_pair', 0, d), mv(arm, 0, d))) for d in M.descriptors_for(ds)
                   for lab, arm in (('raw_cs', 'raw_cs'), ('wrong', 'cs_pair_wrong'))]
            mem += [(f'{ep}:cs_pair-{lab}', diff(mv('cs_pair', 1, ep), mv(arm, 1, ep))) for ep in ('attention20_acc_dependence', 'attention20_acc_readout')
                    for lab, arm in (('raw_cs', 'raw_cs'), ('wrong', 'cs_pair_wrong'))]
            fams.append(family(f'F_MECHANISM:{DS}:{tag}', ('single-seed diagnostic contrasts' if tag != 'merged' else
                                                          'mechanism contrasts, person mean over the three seeds'), mem, people))
        # ---------------------------------------------------------------- F_EXT2 / F_EXT3 follow-ups (M19 / M21)
        for EXT, ARM, PRIMARY, LABEL in (('EXT2', 'cs_pair_noise', ('readout_debiased', 'readout'), 'FOLLOW-UP / post hoc (ext2, DECISIONS 2026-10-23 10:55)'),
                                         ('EXT3', 'ssl_continue', ('readout_debiased',), 'FOLLOW-UP / post hoc (ext3, DECISIONS 2026-10-23 11:55 + 12:20)')):
          ext_seeds = [s for s in SEEDS if vals.get(f'{ARM}@{s}') and vals.get(f'cs_pair@{s}')]
          for tag, ss in [(f'seed{s}', (s,)) for s in ext_seeds] + ([('merged', SEEDS)] if len(ext_seeds) == 3 else []):
              def ser(arm, k, key):
                  if arm == 'B0':
                      return vals['B0'][k].get(key, {})
                  return merged([vals[f'{arm}@{s}'][k].get(key, {}) for s in ss])
              for suffix, ep in (('readout_debiased', 'attention20_acc_readout_debiased'), ('readout', 'attention20_acc_readout'),
                                 ('dependence', 'attention20_acc_dependence'), ('dependence_debiased', 'attention20_acc_dependence_debiased')):
                  mem = [(f'{ARM}-B0', diff(ser(ARM, 1, ep), ser('B0', 1, ep))),
                         (f'cs_pair-{ARM}', diff(ser('cs_pair', 1, ep), ser(ARM, 1, ep)))]
                  f = family(f'F_{EXT}:{DS}:{suffix}:{tag}', '20 s accuracy (person mean, cf mean)', mem, people)
                  f.update(post_hoc=True, label=LABEL,
                           role='primary' if (DS == 'DTU' and suffix in PRIMARY) else 'descriptive')
                  fams.append(f)
              mem = [(f'{d}:{lab}', diff(ser(a1, 0, d), ser(a2, 0, d))) for d in M.descriptors_for(ds)
                     for lab, a1, a2 in ((f'{ARM}-B0', ARM, 'B0'), (f'cs_pair-{ARM}', 'cs_pair', ARM))]
              f = family(f'F_{EXT}:{DS}:excess:{tag}', 'excess CS (nats), main condition, cf mean', mem, people)
              f.update(post_hoc=True, label=LABEL, role='descriptive')
              fams.append(f)
        # ---------------------------------------------------------------- descriptive: every available encoder / group
        d = {}
        for name, (m, a) in sorted(vals.items()):
            spec = reg.get(name) or reg.get(next((n for r in plan['rows'] if r['group'] == name for n in r['encoders']), ''), {})
            ent = {'input_support_flag': spec.get('input_support_flag'), 'data_access': spec.get('data_access'), 'kind': spec.get('kind'),
                   'label': ('new_round_same_support' if spec.get('kind') in ('new_round_production',) else
                             'reference_B0' if name == 'B0' else 'descriptive_different_support_or_access')}
            for dn in M.descriptors_for(ds):
                ent[f'excess_{dn}'] = describe(list(m.get(dn, {}).values()))
                if name != 'B0' and 'B0' in vals:
                    ent[f'excess_{dn}_minus_B0'] = describe([v for v in diff(m.get(dn, {}), vals['B0'][0].get(dn, {})).values()])
            for ep in ATT_EPS:
                ent[ep] = describe(list(a.get(ep, {}).values()))
                if name != 'B0' and 'B0' in vals and ep.startswith('attention20'):
                    ent[ep + '_minus_B0'] = describe(list(diff(a.get(ep, {}), vals['B0'][1].get(ep, {})).values()))
            ent['readout_minus_dependence'] = describe(list(diff(a.get('attention20_acc_readout', {}),
                                                                 a.get('attention20_acc_dependence', {})).values()))
            # controls (generic encoders only: cell condition files)
            if not name.startswith('aln34'):
                for cond in ('noise', 'partner', 'own_on_partner_blocks'):
                    cm = {k: unitize(ds, v) for k, v in measurement_people(ds, name, cond).items()}
                    for dn in M.descriptors_for(ds):
                        if cm.get(dn):
                            ent[f'{cond}_excess_{dn}'] = describe(list(cm[dn].values()))
                if ds == 'dtu':
                    for cond in ('sens_n32', 'sens_n64', 'sens_sigma_x0.5', 'sens_sigma_x2'):
                        cm = measurement_people(ds, name, cond)
                        if cm.get('env'):
                            ent[f'{cond}_excess_env'] = describe(list(cm['env'].values()))
            if not name.startswith('aln34'):
                for w, dd in perturb_people(ds, name).items():
                    for dn, pp in dd.items():
                        ent[f'pert_{w}_excess_{dn}'] = describe(list(pp.values()))
                        if name != 'B0':
                            b0 = perturb_people(ds, 'B0').get(w, {}).get(dn, {})
                            if b0:
                                ent[f'pert_{w}_excess_{dn}_minus_B0'] = describe(list(diff(pp, b0).values()))
            d[name] = ent
        desc[ds] = d
    for f in fams:
        if ':FEDERICI:' in f['family_id']:
            lab = 'FOLLOW-UP / descriptive (Federici, DECISIONS M20; 20 s decision = match vs mismatch)'
            f.update(post_hoc=True, role='descriptive', label=(f['label'] + '; ' + lab) if f.get('label') else lab)
    res = {'version': 'DEP12_PUB_REPORT_v1', 'time': datetime.now().astimezone().isoformat(), 'code_commit': commit,
           'families': fams, 'descriptive': desc, 'per_person_sha256': sha(out), 'n_rows': len(rows),
           'notes': ['person = unit; content folds averaged within person (both required); seeds merged as person means',
                     'reused encoders are descriptive and flagged with input support / access; never in the main families',
                     'excess CS in nats (not Shannon MI); attention accuracy with ties 0.5']}
    write(M.RESULTS / 'contrasts_public.json', res)
    (M.RESULTS / 'contrasts_public.md').write_text(markdown(res))
    import shutil
    with open(out, 'rb') as src, gzip.open(str(out) + '.gz.tmp', 'wb', compresslevel=6) as dst:
        shutil.copyfileobj(src, dst, 1 << 24)
    os.replace(str(out) + '.gz.tmp', str(out) + '.gz')
    if any(f['family_id'].startswith('F_EXT2') for f in fams):
        (M.RESULTS / 'EXT2_PUBLIC.md').write_text(ext2_markdown(res))
    if any(f['family_id'].startswith('F_EXT3') for f in fams):
        (M.RESULTS / 'EXT3_PUBLIC.md').write_text(ext3_markdown(res))
    print('rows', len(rows), 'families', len(fams), flush=True)


EXT3_INTRO = ('FOLLOW-UP / post hoc experiment designed after the round results (coordinator DECISIONS 2026-10-23 11:55 + 12:20; public side '
              'M21). `ssl_continue` = the cs_pair LoRA recipe (streams, anchors / windows, optimiser, schedule, 10,000 updates) with an '
              'audio-free CBraMod-style masked-patch reconstruction objective (a domain-adaptation control). Read-outs fixed in advance: '
              'primary = DTU debiased readout attention (b), members ssl_continue − B0 and cs_pair − ssl_continue, per seed and merged, '
              'B = 10,000, simultaneous intervals; FAU and Federici (match vs mismatch, M20) and every other endpoint descriptive. '
              'Interpretation fixed in advance: ssl_continue ≈ cs_pair (> B0) → domain adaptation suffices; ssl_continue ≈ B0 → the '
              'alignment objective matters beyond exposure to source EEG, UNLESS the manipulation check shows ssl_continue moved the '
              'representation by < 25 % of cs_pair_noise (12:20), in which case the control is inconclusive.')


def ext3_markdown(res):
    txt = ext2_markdown(res, 'F_EXT3', 'ssl_continue', title='# DEP12 ext3 (ssl_continue) — public cohorts', intro=EXT3_INTRO)
    mc = M.RESULTS / 'MANIPULATION_CHECK.md'
    if mc.exists():
        txt += '\n' + mc.read_text().replace('# DEP12 manipulation check (ext3)', '## Manipulation check (included; descriptive)', 1)
    return txt


def ext2_markdown(res, prefix='F_EXT2', arm='cs_pair_noise', title='# DEP12 ext2 (cs_pair_noise) — public cohorts', intro=None):
    L = [title, '', f'Generated {res["time"]}; code {res["code_commit"]}.', '']
    if intro:
        L += [intro, '', 'Units: 20 s person-mean accuracy (ties 0.5), content folds averaged within person; excess CS in nats.', '']
    else:
        L += ['FOLLOW-UP / post hoc experiment designed after the round results (coordinator DECISIONS 2026-10-23 10:55; public side M19). '
             '`cs_pair_noise` = the cs_pair LoRA recipe trained against i.i.d. unit-Gaussian 32-d targets (no acoustic information, no '
             'learnable dependence). Read-outs fixed at 10:55: primary = DTU debiased readout attention (b) and DTU primary (b), members '
             'cs_pair_noise − B0 and cs_pair − cs_pair_noise, per seed and merged, B = 10,000, simultaneous intervals; everything else '
             'descriptive. Interpretation fixed at 10:55: cs_pair_noise ≈ cs_pair (> B0) → gain independent of sound; cs_pair_noise ≈ B0 < '
             'cs_pair → the sound kernel structure contributes; in between → partial.', '',
             'Units: 20 s person-mean accuracy (ties 0.5), content folds averaged within person; excess CS in nats.', '']
    for f in res['families']:
        if not f['family_id'].startswith(prefix):
            continue
        L += [f'## {f["family_id"]} — {f.get("role")} ({f["status"]}, n = {f["complete_n"]}/{f["expected_n"]}, critical {_fmt(f.get("critical"), 3)})', '',
              '| member | estimate | pointwise 95 % | simultaneous 95 % | n |', '|---|---|---|---|---|']
        for m in f['members']:
            pw = m.get('pointwise_95'); sm = m.get('simultaneous_95')
            L.append(f'| {m["name"]} | {_fmt(m.get("estimate"), 5)} | {"—" if not pw else f"[{pw[0]:+.5f}, {pw[1]:+.5f}]"} | '
                     f'{"—" if not sm else f"[{sm[0]:+.5f}, {sm[1]:+.5f}]"} | {m["n"]} |')
        L.append('')
    keys = (('attention20_acc_dependence', '(a)'), ('attention20_acc_readout', '(b)'), ('foreign_eeg_acc_dependence', 'foreign (a)'),
            ('foreign_eeg_acc_readout', 'foreign (b)'), ('attention20_acc_dependence_debiased', 'debiased (a)'),
            ('attention20_acc_readout_debiased', 'debiased (b)'), ('excess_env', 'env'), ('excess_spec', 'spec'), ('excess_Lz', 'Lz'))
    for ds, d in res['descriptive'].items():
        names = ['B0'] + [n for n in d if n.split('@')[0] in ('cs_pair', arm, 'cs_pair_wrong', 'raw_cs')]
        L += [f'## {ds.upper()}: per-encoder means (descriptive; incl. the foreign-EEG control)', '',
              '| encoder | ' + ' | '.join(k[1] for k in keys) + ' |', '|' + '---|' * (len(keys) + 1)]
        for n in names:
            e = d.get(n)
            if not e:
                continue
            L.append(f'| {n} | ' + ' | '.join((f'{e[k]["mean"]:.4f}' if 'acc' in k else f'{e[k]["mean"]:.3g}') if (e.get(k) or {}).get('mean') is not None else '—'
                                               for k, _ in keys) + ' |')
        L.append('')
    return '\n'.join(L) + '\n'


def _fmt(x, k=4):
    return '—' if x is None else f'{x:+.{k}f}' if isinstance(x, float) else str(x)


def markdown(res):
    L = ['# DEP12 public measurement and attention (Agent M)', '', f'Generated {res["time"]}; code {res["code_commit"]}.', '',
         'Units: excess CS in nats (raw − mean of the 199 block-shift nulls; not Shannon MI); 20 s attention accuracy (ties 0.5). '
         'Person = unit; content folds averaged within person. Intervals: person bootstrap-t, B = 10,000.', '']
    for ds, d in res['descriptive'].items():
        L += [f'## {ds.upper()}: every available encoder (descriptive)', '',
              '| encoder | label | env excess | spec excess | Lz excess | att. dep. (a) | att. dep. z (a_z) | att. readout (b) | '
              'foreign-EEG (a) | foreign-EEG (b) | debiased (a), post hoc | debiased (b), post hoc |',
              '|---|---|---|---|---|---|---|---|---|---|---|---|']
        for name, e in d.items():
            def c(k):
                v = e.get(k) or {}
                return f'{v["mean"]:.5f} [{v["pointwise_95"][0]:.5f}, {v["pointwise_95"][1]:.5f}] (n={v["n"]})' if v.get('pointwise_95') else '—'
            L.append(f'| {name} | {e["label"]} | {c("excess_env")} | {c("excess_spec")} | {c("excess_Lz")} | '
                     f'{c("attention20_acc_dependence")} | {c("attention20_acc_dependence_z")} | {c("attention20_acc_readout")} | '
                     f'{c("foreign_eeg_acc_dependence")} | {c("foreign_eeg_acc_readout")} | '
                     f'{c("attention20_acc_dependence_debiased")} | {c("attention20_acc_readout_debiased")} |')
        L.append('')
    L += ['## Families', '']
    for f in res['families']:
        if f.get('status') == 'not_available_yet':
            L.append(f'- {f["family_id"]}: not available yet (missing {", ".join(f["missing"])})'); continue
        L += [f'### {f["family_id"]} ({f["status"]}, n = {f["complete_n"]}/{f["expected_n"]}, critical {_fmt(f.get("critical"), 3)})', '',
              '| member | estimate | pointwise 95 % | simultaneous 95 % | n |', '|---|---|---|---|---|']
        for m in f['members']:
            pw = m.get('pointwise_95'); sm = m.get('simultaneous_95')
            L.append(f'| {m["name"]} | {_fmt(m.get("estimate"), 5)} | {"—" if not pw else f"[{pw[0]:+.5f}, {pw[1]:+.5f}]"} | '
                     f'{"—" if not sm else f"[{sm[0]:+.5f}, {sm[1]:+.5f}]"} | {m["n"]} |')
        L.append('')
    return '\n'.join(L) + '\n'


if __name__ == '__main__':
    main()
