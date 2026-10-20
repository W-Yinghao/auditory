"""Frozen-source bindings and numerical helpers for S35_BRIDGE_FACTOR.

Original B matrices and their source-selected alphas are fixed before this
sensitivity. Both temperature rules use the manifest's same two listener folds
and identical candidates. This is source-side readout cross-fitting, not nested
whole-pipeline validation of either alpha or donor selection.
"""
from __future__ import annotations
from collections import defaultdict
from datetime import datetime
import json
import math
import os
from pathlib import Path
import numpy as np
from scipy.special import logsumexp
from auditory_alignment_v3 import core
from auditory_alignment_v3.prior33 import bridge as BR, select as SEL, sampler as SM
from . import science_binding as B

BASE = Path(core.OUT) / 'aln35/bridge'
RESULTS = B.ROOT / 'results/auditory_alignment_v3/aln35/bridge'
CACHE = Path('<private checkpoint storage>/auditory_alignment_v3/aln35/bridge/cache')
KEYS = ('dtu_AP', 'dtu_XM', 'fau_XP', 'fau_XM')


def load_rows():
    return core.load_rows() + [json.loads(x) for x in (Path(core.OUT) / 'plan_ext.jsonl').read_text().splitlines()]


def selected_rows(rows):
    result = defaultdict(list)
    for row in rows:
        s = row['spec']; key = row['dataset'] + '_' + str(s.get('member'))
        if (row['family_id'] == 'ALN32_PUBLIC_AUDIO_PRIOR_ZEROSHOT' and key in KEYS
                and row['seed'] == 3401 and s.get('objective') == 'NCE'
                and s.get('block') == 'core' and s.get('mode') == 'A'):
            result[key].append(row)
    assert set(result) == set(KEYS)
    for key, rr in result.items():
        assert {(r['subject_fold'], r['content_fold']) for r in rr} == {(sf, cf) for sf in range(5) for cf in range(2)}, key
        assert len(rr) == 10
        result[key] = sorted(rr, key=lambda r: (r['content_fold'], r['subject_fold']))
    return dict(result)


def source_metadata(man, bridge, dataset):
    br = SM.bridge_rows(man, dataset, root=man.root)
    uc = BR.uni_cal_sample(man)
    cq, ca = br['cal']['queries'], br['cal']['candidates']
    own = np.asarray(br['cal']['own'], dtype=np.int64)
    fit_hash = BR.sha_json({'target': dataset, 'order': br['order']})
    cal_hash = BR.sha_json({'queries': cq.rows, 'candidates': [[int(p), int(s)] for p, s in zip(ca.presentation, ca.s)],
                           'own': own, 'split': br['cal']['split']})
    assert fit_hash == bridge.meta['fit_rows_sha256']
    assert cal_hash == bridge.meta['cal_rows_sha256']
    assert uc['rows_sha256'] == bridge.meta['uni_cal_rows_sha256']
    assert uc['split'] == br['cal']['split']
    assert set(uc['split'][0]).isdisjoint(uc['split'][1])
    ids = lambda sset: [f'sparrkulee/{p}/segment_row={int(r)}/presentation={int(v)}/s={int(s)}'
                       for p, r, v, s in zip(sset.participant, sset.rows, sset.presentation, sset.s)]
    meta = {'fit_rows_sha256': fit_hash, 'cal_rows_sha256': cal_hash, 'uni_cal_rows_sha256': uc['rows_sha256'],
            'fit_rows_by_stratum': {s: len(br['fit'][s]) for s in br['strata']},
            'fit_participants': bridge.meta['fit_participants'], 'cal_split': uc['split'],
            'query_ids': ids(cq), 'query_participants': list(map(str, cq.participant)),
            'query_fold': np.asarray(br['cal']['fold'], dtype=int).tolist(),
            'candidate_ids': [f'sparrkulee/presentation={int(p)}/s={int(s)}' for p, s in zip(ca.presentation, ca.s)],
            'own': own.tolist(), 'bridgecal_fit_query_ids': ids(uc['set']),
            'bridgecal_fit_participants': list(map(str, uc['set'].participant)), 'bridgecal_fit_fold': uc['fold'].tolist(),
            'n_donor_fit_segments': sum(len(br['fit'][s]) for s in br['strata']), 'n_bridgecal_fit_segments': len(uc['set']),
            'source_scope': 'original source-selected matrices/alphas fixed; identical bridge.cal_split query folds for both T rules; B_bridgecal fits exclude query listener fold; alpha and donor selection not nested',
            'target_access_for_fit': 'none'}
    assert meta['n_donor_fit_segments'] == meta['n_bridgecal_fit_segments'] == 2000
    assert len(meta['query_ids']) == len(set(meta['query_ids']))
    return br, uc, meta


def source_freeze(key, selected, all_rows):
    row = selected[0]
    man = BR.open_row_manifest(row)
    dep = BR.load_member(row, all_rows, core.OUT)
    bid = row['spec']['bridge']; bp = Path(SEL.bridge_npz(core.OUT, bid))
    bridge = BR.load_bridge(bp, expect_id=bid)
    brec = SEL.load_record(core.OUT, bid)
    from auditory_alignment_v3.prior33.run_zeroshot import check_bridge
    check_bridge(bridge, row, dep, brec, B.sha(bp))
    sources = {str(Path(dep['ckpt_path'])): dep['ckpt_sha256'], str(bp): B.sha(bp),
               str(Path(core.OUT) / 'units' / (bid + '.json')): B.sha(Path(core.OUT) / 'units' / (bid + '.json')),
               str(Path(core.OUT) / 'units' / (dep['gid'] + '.json')): B.sha(Path(core.OUT) / 'units' / (dep['gid'] + '.json'))}
    for r in selected:
        p = Path(core.OUT) / 'units' / (r['experiment_id'] + '.json')
        rec = B.read(p); assert rec['status'] == 'complete' and rec['row'] == r
        assert rec['dependency']['checkpoint_sha256'] == dep['ckpt_sha256']
        assert rec['dependency']['bridge_npz_sha256'] == B.sha(bp)
        sources[str(p)] = B.sha(p)
    br, uc, source = source_metadata(man, bridge, row['dataset'])
    return {'key': key, 'dataset': row['dataset'], 'arm': row['spec']['member'], 'seed': 3401,
            'rows': selected, 'source_paths_sha256': sources, 'source_rows_sha256': B.digest(selected),
            'manifest_sha256': man.sha256, 'bridge_file': str(bp), 'checkpoint': str(dep['ckpt_path']),
            'source_metadata': source, 'cache': str(CACHE / key),
            'encoder_training': False, 'forward_scope': 'bridge-cal and bridge-cal-fit rows plus original mode-A target queries only; original donor-fit B reused'}


def query_metrics(scores, own, tau):
    scores = np.asarray(scores, dtype=np.float64); own = np.asarray(own, dtype=np.int64)
    assert scores.ndim == 2 and len(own) == len(scores) and len(scores)
    assert np.isfinite(scores).all() and np.isfinite(tau) and tau > 0
    assert own.min() >= 0 and own.max() < scores.shape[1]
    # Exact old argsort tie policy retained; positive temperature must preserve it.
    order = np.argsort(-scores, axis=1)
    scaled_order = np.argsort(-(scores / tau), axis=1)
    assert np.array_equal(order, scaled_order), 'temperature changed ranks'
    rank = np.argmax(order == own[:, None], axis=1)
    z = scores / tau; lse = logsumexp(z, axis=1)
    logp = z - lse[:, None]; p = np.exp(logp)
    nll = (lse - z[np.arange(len(z)), own]) / np.log(2.)
    entropy = -np.sum(p * logp, axis=1) / np.log(2.)
    base = BR.ev1._metrics(scores, own, tau)
    return {**base, 'mean_true_rank_1based': float((rank + 1).mean()), 'entropy_bits': float(entropy.mean()),
            'score_std': float(scores.std()), 'mean_within_query_score_std': float(scores.std(axis=1).mean()),
            'mean_own_score': float(scores[np.arange(len(scores)), own].mean()), 'temperature': float(tau),
            'nll_bits_mean_check': float(nll.mean()), 'rank_invariant_to_temperature': True}


def register():
    assert os.environ.get('SLURM_JOB_ID')
    os.umask(0o077); BASE.mkdir(parents=True, exist_ok=True)
    rows = load_rows(); selected = selected_rows(rows)
    entries = [source_freeze(key, selected[key], rows) for key in KEYS]
    plan = {'schema': 'aln35_bridge_factor_v1', 'time': datetime.now().astimezone().isoformat(),
            'registration_job': os.environ['SLURM_JOB_ID'], 'baseline_commit': B.BASELINE,
            'analysis_origin': 'exploratory_after_known_bridge_sign_changes', 'entries': entries,
            'new_scope': 'two fixed original B matrices x T=1 / common source-listener-fold calibration; four donors only',
            'cache_audit': {'original_bridge_feature_arrays_persisted': False,
                            'original_zero_shot_representations_persisted': False,
                            'evidence': 'bridge.fit_bridge local arrays discarded; zeroshot.MemoTickReps dictionary lives in process only; prior_science cache uses adapted target checkpoints, not these donors'},
            'code_sha256': {str(p.relative_to(B.ROOT)): B.sha(p) for p in [Path(__file__), B.ROOT / 'auditory_alignment_v3/aln35/bridge_factor_extract.py',
                            B.ROOT / 'auditory_alignment_v3/prior33/bridge.py', B.ROOT / 'auditory_alignment_v3/prior33/zeroshot.py',
                            B.ROOT / 'auditory_alignment_v3/prior33/views.py', B.ROOT / 'auditory_alignment_v3/prior33/sampler.py']}}
    B.write_new(BASE / 'plan.json', plan)
    print(json.dumps({'status': 'registered', 'entries': [e['key'] for e in entries], 'source_units': sum(len(e['rows']) for e in entries),
                      'forward_required': True, 'plan_sha256': B.sha(BASE / 'plan.json')}), flush=True)


if __name__ == '__main__': register()
