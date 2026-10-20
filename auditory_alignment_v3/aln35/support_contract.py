"""ALN3.5 support sampling: no query labels/scores are accepted by selectors."""
from __future__ import annotations

import hashlib
import json
import math
from collections import Counter

import numpy as np
from scipy.special import expit, logsumexp, softmax

SAMPLING_SEEDS = tuple(range(351410, 351415))
TEMPERATURES = (1.0, .5, 2.0)  # first entry wins an exact tie
METHODS = ('zero_step', 'probability_only', 'rank4_fixed20')


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                    allow_nan=False).encode()).hexdigest()


def stable_key(identity, row):
    return digest(['S35_SUPPORT_COVERAGE_v1', identity, int(row)])


def histogram(values):
    return {str(k): int(v) for k, v in sorted(Counter(map(str, values)).items())}


def private_split(kid, fit_only=False):
    """Common physical-block pool and full-epoch sample guard for both encoders.

    The inherited support[:-1], query[1:] rule is applied before the guard.
    Whole-record offline filtering/standardisation is explicitly not re-labelled
    as causally isolated preprocessing by this direct sample-access check.
    """
    n = len(kid['y'])
    times = np.asarray(kid['_s35_onset_seconds'], dtype=float)
    assert len(times) == n and np.isfinite(times).all() and np.all(np.diff(times) >= 0)
    available = np.flatnonzero(~kid['es_mask'] if fit_only else np.ones(n, bool))
    blocks = list(dict.fromkeys(kid['block'][available].tolist()))
    q0 = min(len(blocks), max(1, int(math.ceil(.3 * len(blocks))))) if blocks else 0
    p0 = available[np.isin(kid['block'][available], blocks[:q0])]
    q0rows = available[np.isin(kid['block'][available], blocks[q0:])]
    p, q = p0[:-1], q0rows[1:]
    before = p.copy()
    if len(q):
        boundary = times[q].min() - .2
        p = p[times[p] + .6 <= boundary + 1e-12]
    if len(p) and len(q):
        assert times[p].max() + .6 <= times[q].min() - .2 + 1e-12
    assert not set(kid['block'][p]) & set(kid['block'][q])
    # n10 is a trial count of the original eligible trial population, not blocks.
    n10 = min(int(math.floor(.1 * len(available))), len(p))
    return {'pool': p, 'query': q, 'n10': n10, 'n30': len(p), 'original_n': len(available),
            'original_block_n': len(blocks), 'guard_excluded': before[~np.isin(before, p)],
            'boundary_removed_support': p0[-1:].tolist(), 'boundary_removed_query': q0rows[:1].tolist(),
            'query_identical_private_episode_v2': True,
            'query_identical_native_science': len(q0rows) == 0,
            'guard': 'common full epoch [-0.2,+0.6) seconds; support end <= first query start',
            'preprocessing': 'inherited offline interval filtering and per-record normalisation use the full record; '
                             'no causal or raw-preprocessing-isolation claim',
            'fit_only': fit_only}


def dtu_split(items, fs, seg_len, grid, post, fit_only=False):
    """Existing available five-second segments, ordered by actual EEG-bank start."""
    starts = np.asarray([s['e0'] for s in items], dtype=np.int64)
    assert np.all(np.diff(starts) > 0)
    n = len(items); cut = int(round(.3 * n))
    p0, q = np.arange(cut), np.arange(cut, n)
    # Every registered evaluation anchor is included in the guard, not just the
    # sparse training anchor. Aligned local/FM zero before its segment boundary.
    final_offset = int(np.arange(0, seg_len, grid)[-1])
    p = p0[starts[p0] + final_offset + post <= starts[q[0]]] if len(q) else p0
    if len(p) and len(q):
        assert max(starts[p] + final_offset + post) <= starts[q[0]]
    return {'pool': p, 'query': q, 'n10': min(int(math.floor(.1*n)), len(p)),
            'n30': len(p), 'original_n': n, 'original_block_n': len({s['code'] for s in items}),
            'guard_excluded': p0[~np.isin(p0, p)], 'boundary_removed_support': [],
            'boundary_removed_query': [], 'query_identical_adaptation_policy_v1': True,
            'guard': 'all grid-anchor context ends <= first query segment start; segment-start masking retained',
            'fs': float(fs), 'seg_len': int(seg_len), 'grid': int(grid), 'post': int(post),
            'preprocessing': 'inherited offline filtering and per-person standardisation across available trials; '
                             'no causal or raw-preprocessing-isolation claim', 'fit_only': fit_only}


def select_support(pool, n10, identity, labels=None, groups=None, history=None, times=None):
    """Selectors receive only P metadata. Integer row IDs are opaque here."""
    pool = np.asarray(pool, dtype=int)
    assert len(np.unique(pool)) == len(pool) and 0 <= n10 <= len(pool)
    order = sorted(range(len(pool)), key=lambda j: stable_key(identity, pool[j]))
    out = {f'U10_{seed}': np.sort(np.random.default_rng(seed).choice(pool, size=n10, replace=False))
           for seed in SAMPLING_SEEDS}
    out['U30'] = np.sort(pool.copy())
    if labels is not None:
        labels = np.asarray(labels)
        assert len(labels) == len(pool) and set(np.unique(labels)) <= {0, 1}
        queues = {label: [j for j in order if labels[j] == label] for label in (0, 1)}
        picked = []
        # Round-robin quotas differ by at most one, with shortages transferred.
        while len(picked) < n10:
            for label in (0, 1):
                if queues[label] and len(picked) < n10: picked.append(queues[label].pop(0))
        out['C10'] = np.sort(pool[picked])
    else:
        groups = np.asarray(groups)
        assert len(groups) == len(pool)
        queues = {g: [j for j in order if groups[j] == g] for g in sorted(set(groups))}
        picked = []
        while len(picked) < n10:
            for g in queues:
                if queues[g] and len(picked) < n10: picked.append(queues[g].pop(0))
        out['C10'] = np.sort(pool[picked])
    if history is not None:
        history, times = np.asarray(history), np.asarray(times, dtype=float)
        assert len(history) == len(times) == len(pool)
        assert np.isfinite(times).all()
        width = float(np.ptp(times)) if len(times) else 0.
        terciles = np.minimum(2, np.floor(3*(times-times.min())/width).astype(int)) if width else np.zeros(len(times), int)
        bins, thirds, cells = Counter(), Counter(), Counter(); available = set(order); picked = []
        while len(picked) < n10:
            j = min(available, key=lambda k: (bins[history[k]] > 0, thirds[terciles[k]] > 0,
                    bins[history[k]], thirds[terciles[k]], cells[(history[k], terciles[k])],
                    stable_key(identity, pool[k])))
            picked.append(j); available.remove(j)
            bins[history[j]] += 1; thirds[terciles[j]] += 1; cells[(history[j], terciles[j])] += 1
        out['H10'] = np.sort(pool[picked])
    for selected in out.values(): assert set(selected) <= set(pool)
    return out


def access_budget(strategy, split, selected, steps, private=False):
    coverage = strategy in ('C10', 'H10')
    return {'selection_pool_size': len(split['pool']),
            'metadata_rows_accessed': len(split['pool']) if coverage else 0,
            'label_rows_accessed': len(split['pool']) if coverage and private else len(selected),
            'fit_rows': len(selected), 'fit_updates': int(steps),
            'label_origin': 'pre-existing experimental stimulus log; not inferred from EEG or query outcomes',
            'deployment_label_budget_equivalence_claimed': False}


def temperature_binary(logits, labels):
    logits, labels = np.asarray(logits, float), np.asarray(labels, int)
    if not len(labels): return 1., {'reason': 'no_legal_support_risk', 'risks': {}}
    assert logits.shape == labels.shape and np.isfinite(logits).all()
    scores = {str(t): float(np.mean(np.logaddexp(0, logits/t) - labels*logits/t)/np.log(2)) for t in TEMPERATURES}
    chosen = min(TEMPERATURES, key=lambda t: scores[str(t)])
    return chosen, {'reason': None, 'risks': scores}


def temperature_retrieval(scores, own, base_tau):
    scores, own = np.asarray(scores, float), np.asarray(own, int)
    if len(own) == 0 or scores.ndim != 2 or scores.shape[1] < 2:
        return 1., {'reason': 'no_legal_support_risk', 'risks': {}}
    assert scores.shape[0] == len(own) and np.isfinite(scores).all() and base_tau > 0
    values = {str(t): float(np.mean(logsumexp(scores/(base_tau*t), axis=1)
                    - scores[np.arange(len(own)), own]/(base_tau*t))/np.log(2)) for t in TEMPERATURES}
    chosen = min(TEMPERATURES, key=lambda t: values[str(t)])
    return chosen, {'reason': None, 'risks': values}


def probability_change(p, base):
    p, base = np.asarray(p, float), np.asarray(base, float)
    if p.ndim == 1: p, base = np.c_[1-p, p], np.c_[1-base, base]
    assert p.shape == base.shape and np.isfinite(p).all() and np.isfinite(base).all()
    return {'probability_tv': float(np.abs(p-base).sum(1).mean()/2),
            'entropy_bits': float(-(p*np.log2(np.clip(p, 1e-300, 1))).sum(1).mean())}


def cosine_or_none(a, b):
    a, b = np.asarray(a, float).reshape(-1), np.asarray(b, float).reshape(-1)
    den = np.linalg.norm(a)*np.linalg.norm(b)
    return float(a@b/den) if den > 0 else None


def support_signal(objective, labels, requested_steps):
    labels = np.asarray(labels)
    reason = ('zero_step_candidate' if requested_steps == 0 else 'no_support' if len(labels) == 0
              else 'zero_signal_single_class_CS' if objective.startswith('CS') and len(np.unique(labels)) < 2 else None)
    return {'requested_adapter_steps': requested_steps, 'effective_adapter_steps': 0 if reason else requested_steps,
            'identity_fallback_reason': reason, 'n_support_classes': len(np.unique(labels)),
            'label_kernel_state': 'constant' if len(labels) and len(np.unique(labels)) == 1 else 'nonconstant' if len(labels) else 'empty'}
