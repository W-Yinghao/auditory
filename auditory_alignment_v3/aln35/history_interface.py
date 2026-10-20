"""Source-only history intercept and strict other-block twin readout sensitivity.

The encoder and feature cache are frozen. All fitted parameters use the declared
source children's ES rows; queried children never select partners or models by
their labels or losses. This module is not part of any old execution signature.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime
import json
import math
import os
from pathlib import Path
import numpy as np
from scipy.optimize import minimize, root_scalar
from scipy.special import expit
from sklearn.metrics import roc_auc_score

from . import science_binding as B

BASE = Path(B.BASE) / 'aln35/history'
RESULTS = B.ROOT / 'results/auditory_alignment_v3/aln35/history'
SEED = 351819
ARMS = ('S', 'AP', 'J*', 'XM')
GRAD_PER_ROW_TOL = 1e-7


def strict_twin_map(history, blocks, allowed, seed):
    """Return -1 when no same-history other-block partner in allowed rows exists.

    No labels or scores are arguments. Restricting both ends to source ES rows
    prevents strict source readouts from silently using encoder-fit-block twins.
    """
    history = np.asarray(history); blocks = np.asarray(blocks)
    allowed = np.asarray(allowed, dtype=int)
    assert len(allowed) == len(np.unique(allowed))
    assert np.all((allowed >= 0) & (allowed < len(history)))
    rng = np.random.default_rng(seed)
    twin = np.full(len(history), -1, dtype=np.int64)
    for i in allowed:
        candidates = allowed[(history[allowed] == history[i]) & (blocks[allowed] != blocks[i]) & (allowed != i)]
        if len(candidates): twin[i] = rng.choice(candidates)
    eligible = allowed[twin[allowed] >= 0]
    assert np.all(history[eligible] == history[twin[eligible]])
    assert np.all(blocks[eligible] != blocks[twin[eligible]])
    assert np.all(eligible != twin[eligible])
    return twin


def objective(w, X, y, offset):
    Xa = np.column_stack([np.ones(len(X)), X])
    z = offset + Xa @ w
    value = float(np.sum(np.logaddexp(0, z) - y * z) + .5 * np.sum(w[1:] ** 2))
    gradient = Xa.T @ (expit(z) - y)
    gradient[1:] += w[1:]
    return value, gradient


def fit_offset(X, y, offset):
    """Original sum-NLL + L2(C=1), stricter recorded numerical execution."""
    X = np.asarray(X, dtype=np.float64); y = np.asarray(y, dtype=np.float64); offset = np.asarray(offset, dtype=np.float64)
    if not len(y) or len(np.unique(y)) != 2: raise ValueError('source ES must have both classes')
    receipts = []
    initial = np.zeros(X.shape[1] + 1)
    for retry, options in enumerate(({'maxiter': 5000, 'ftol': 1e-12, 'gtol': 1e-8, 'maxls': 50},
                                     {'maxiter': 10000, 'ftol': 1e-15, 'gtol': 1e-10, 'maxls': 100})):
        opt = minimize(objective, initial, args=(X, y, offset), jac=True, method='L-BFGS-B', options=options)
        value, gradient = objective(opt.x, X, y, offset)
        perrow = float(np.max(np.abs(gradient)) / len(y))
        receipt = {'optimizer_success': bool(opt.success), 'optimizer_message': str(opt.message),
                   'objective_finite': bool(math.isfinite(value)), 'objective': value,
                   'gradient_norm': float(np.linalg.norm(gradient)), 'gradient_maxabs_per_source_row': perrow,
                   'tolerance': {'gradient_maxabs_per_source_row': GRAD_PER_ROW_TOL, **options},
                   'retry_reason': None if retry == 0 else 'source optimizer status/gradient criterion unmet',
                   'source_rows_unchanged': True, 'iterations': int(opt.nit), 'C': 1.0,
                   'objective_definition': 'sum logistic NLL + 0.5 * squared slopes; intercept unpenalized'}
        receipts.append(receipt)
        if opt.success and math.isfinite(value) and np.isfinite(opt.x).all() and perrow <= GRAD_PER_ROW_TOL:
            return opt.x, receipts
        initial = opt.x if np.isfinite(opt.x).all() else initial
    raise RuntimeError('source readout convergence failed: ' + json.dumps(receipts))


def fit_intercept(y, offset):
    y = np.asarray(y, dtype=np.float64); offset = np.asarray(offset, dtype=np.float64)
    if not len(y) or len(np.unique(y)) != 2: raise ValueError('source ES must have both classes')
    derivative = lambda b: float(np.sum(expit(offset + b) - y))
    root = root_scalar(derivative, bracket=(-80., 80.), method='brentq', xtol=1e-12, rtol=1e-12)
    b = float(root.root)
    value = float(np.sum(np.logaddexp(0, offset + b) - y * (offset + b)))
    grad = abs(derivative(b))
    receipt = {'optimizer_success': bool(root.converged), 'optimizer_message': str(root.flag), 'objective_finite': math.isfinite(value),
               'objective': value, 'gradient_norm': grad, 'gradient_maxabs_per_source_row': grad / len(y),
               'tolerance': {'xtol': 1e-12, 'rtol': 1e-12, 'gradient_maxabs_per_source_row': GRAD_PER_ROW_TOL},
               'retry_reason': None, 'source_rows_unchanged': True, 'iterations': int(root.iterations),
               'objective_definition': 'sum logistic NLL with history offset; one unpenalized intercept'}
    assert root.converged and math.isfinite(value) and grad / len(y) <= GRAD_PER_ROW_TOL
    return b, receipt


def ll(p, y):
    return np.where(y == 1, np.log2(np.clip(p, 1e-12, 1)), np.log2(np.clip(1 - p, 1e-12, 1)))


def metrics(predictions, y):
    out = {'n_trials': len(y), 'n_standard': int(np.sum(y == 0)), 'n_deviant': int(np.sum(y == 1))}
    if not len(y): return dict(out, status='no_eligible_query_trials')
    out['status'] = 'complete'
    for name, p in predictions.items():
        assert len(p) == len(y) and np.isfinite(p).all()
        out[name] = {'auc': float(roc_auc_score(y, p)) if len(np.unique(y)) == 2 else None,
                     'nll_bits': float(-ll(p, y).mean()), 'brier': float(np.mean((p - y) ** 2))}
    for a, b in (('B1', 'B0'), ('EEG', 'B0'), ('EEG', 'B1'), ('EEG', 'strict_twin')):
        key = a + '_minus_' + b + '_logscore_bits'
        out[key] = float((ll(predictions[a], y) - ll(predictions[b], y)).mean()) if a in predictions and b in predictions else None
    return out


def evaluate_source(binding, unit, rec, cache, arm):
    from auditory_alignment_v3.sci_r1.private_task import Fold
    row = unit['source']; fd = Fold(binding.kids, row['subject_fold'])
    with np.load(cache / 'arrays.npz', allow_pickle=False) as z:
        U = {i: z[f'full_{i}'].astype(np.float64) for i in range(len(binding.kids))}
    for i, k in enumerate(binding.kids): assert U[i].shape == (len(k['y']), 32)
    maps, eval_indices, train_indices = {}, {}, {}
    for i, k in enumerate(binding.kids):
        allowed = np.flatnonzero(k['es_mask']) if i in fd.tr else np.arange(len(k['y']))
        person_seed = SEED + int(B.digest(k['id'])[:8], 16)
        maps[i] = strict_twin_map(k['bin'], k['block'], allowed, person_seed)
        if i in fd.tr: train_indices[i] = allowed[maps[i][allowed] >= 0]
        else: eval_indices[i] = allowed[maps[i][allowed] >= 0]
    source_fits = {}; person_results = {}; coefficients = {}
    for scope in ('full_query', 'strict_other_block'):
        indices = {i: np.flatnonzero(binding.kids[i]['es_mask']) if scope == 'full_query' else train_indices[i] for i in fd.tr}
        x = np.concatenate([U[i][indices[i]] for i in fd.tr])
        y = np.concatenate([binding.kids[i]['y'][indices[i]] for i in fd.tr])
        bins = np.concatenate([binding.kids[i]['bin'][indices[i]] for i in fd.tr])
        off = fd.logit(fd.q0[bins])
        source_ids = [binding.private_query[binding.kids[i]['id']][int(j)] for i in fd.tr for j in indices[i]]
        mu, sd = x.mean(0), x.std(0) + 1e-8
        w, fit_receipts = fit_offset((x - mu) / sd, y, off)
        intercept, b1_receipt = fit_intercept(y, off)
        wt = None
        receipts = {'EEG': fit_receipts, 'B1': [b1_receipt]}
        if scope == 'strict_other_block':
            xt = np.concatenate([U[i][maps[i][indices[i]]] for i in fd.tr])
            wt, receipts['strict_twin'] = fit_offset((xt - mu) / sd, y, off)
        source_fits[scope] = {'n_source_ES': len(y), 'source_ES_class_counts': {'standard': int((y == 0).sum()), 'deviant': int((y == 1).sum())},
                             'source_row_hash': B.digest(source_ids), 'source_child_ids': [binding.kids[i]['id'] for i in fd.tr],
                             'n_ES_children_with_rows': sum(bool(len(ix)) for ix in indices.values()),
                             'standardization': 'mean/std on same source ES row set; same scaler for EEG and twin',
                             'standardization_sha256': B.digest({'mu': mu.tolist(), 'sd': sd.tolist()}),
                             'strict_source_partner_pool': 'source ES rows of same child only', 'fits': receipts}
        coefficients[scope] = {'mu': mu.tolist(), 'sd': sd.tolist(), 'EEG': w.tolist(), 'B1_intercept': intercept,
                               'strict_twin': wt.tolist() if wt is not None else None, 'q0': fd.q0.tolist()}
        for i in fd.te:
            k = binding.kids[i]; idx = np.arange(len(k['y'])) if scope == 'full_query' else eval_indices[i]
            q0 = fd.q0[k['bin'][idx]]; offset = fd.logit(q0)
            design = np.column_stack([np.ones(len(idx)), (U[i][idx] - mu) / sd])
            predictions = {'B0': q0, 'B1': expit(offset + intercept), 'EEG': expit(offset + design @ w)}
            if wt is not None:
                twin_design = np.column_stack([np.ones(len(idx)), (U[i][maps[i][idx]] - mu) / sd])
                predictions['strict_twin'] = expit(offset + twin_design @ wt)
            query_ids = [binding.private_query[k['id']][int(j)] for j in idx]
            common = (q0 > .01) & (q0 < .99)
            original_swap = k['swap']; original_all = np.arange(len(k['y']))
            original_self = original_swap == original_all
            original_same_block = k['block'][original_swap] == k['block']
            original_same_history = k['bin'][original_swap] == k['bin']
            person = person_results.setdefault(k['id'], {'group': k['group'], 'n_trials': len(k['y']),
                'n_standard': int((k['y'] == 0).sum()), 'n_deviant': int((k['y'] == 1).sum()), 'n_history_bins': len(np.unique(k['bin'])),
                'n_strict_twin': len(eval_indices[i]), 'strict_fraction': len(eval_indices[i]) / len(k['y']),
                'n_fallback_same_block': int(original_same_block.sum()), 'n_self_twin': int(original_self.sum()),
                'original_twin_same_history_fraction': float(original_same_history.mean()),
                'original_twin_different_block_fraction': float((~original_same_block).mean()),
                'original_twin_self_fraction': float(original_self.mean()),
                'source_ES_class_counts': source_fits[scope]['source_ES_class_counts'], 'query_class_counts': {'standard': int((k['y'] == 0).sum()), 'deviant': int((k['y'] == 1).sum())},
                'scopes': {}})
            per = {'all_queries': metrics(predictions, k['y'][idx]),
                   'q0_common_support': metrics({n: p[common] for n, p in predictions.items()}, k['y'][idx][common]),
                   'n_common_support': int(common.sum()), 'query_row_hash': B.digest(query_ids),
                   'common_query_row_hash': B.digest([q for q, keep in zip(query_ids, common) if keep]),
                   'source_row_hash': source_fits[scope]['source_row_hash'],
                   'twin_map_hash': B.digest([[binding.private_query[k['id']][int(j)], binding.private_query[k['id']][int(maps[i][j])]]
                                             for j in idx]) if wt is not None else None,
                   'original_full_query_gain_bits': rec['per_participant'][k['id']]['windows']['full']['history_gain_bits'],
                   'readout_reexecution': 'new source-convergence-checked fit; original reported values retained separately'}
            if scope == 'full_query':
                per['difference_from_original_history_gain_bits'] = per['all_queries']['EEG_minus_B0_logscore_bits'] - per['original_full_query_gain_bits']
            person['scopes'][scope] = per
    return {'source_unit': unit, 'arm': arm, 'status': 'complete', 'seed': row['seed'], 'subject_fold': row['subject_fold'],
            'source_fits': source_fits, 'per_participant': person_results,
            'source_checkpoint_sha256': rec['unit']['checkpoint_sha256'], 'cache_array_sha256': rec['cache_metadata']['array_sha256'],
            'strict_source_es_twin_map_hash': B.digest({binding.kids[i]['id']: maps[i].tolist() for i in fd.tr}),
            'strict_query_twin_map_hash': B.digest({binding.kids[i]['id']: maps[i].tolist() for i in fd.te}),
            'source_and_query_labels_never_used_for_partner_choice': True}, coefficients


def aggregate(units, expected):
    by_arm = defaultdict(dict)
    for unit in units:
        for identity, person in unit['per_participant'].items():
            assert identity not in by_arm[unit['arm']]
            by_arm[unit['arm']][identity] = person
    output = []
    for arm in ARMS:
        assert set(by_arm[arm]) == set(expected), ('missing original target children', arm)
        for scope in ('full_query', 'strict_other_block'):
            for query in ('all_queries', 'q0_common_support'):
                for group in ('all', 'HA', 'NH'):
                    ids = [i for i in sorted(expected) if group == 'all' or expected[i] == group]
                    people = [by_arm[arm][i]['scopes'][scope][query] for i in ids]
                    names = ('B1_minus_B0_logscore_bits', 'EEG_minus_B0_logscore_bits', 'EEG_minus_B1_logscore_bits', 'EEG_minus_strict_twin_logscore_bits')
                    means = {}; count = {}
                    for name in names:
                        values = [p[name] for p in people if p.get('status') == 'complete' and p.get(name) is not None]
                        means[name] = math.fsum(values) / len(values) if values else None
                        count[name] = len(values)
                    levels = {}
                    for model in ('B0', 'B1', 'EEG', 'strict_twin'):
                        levels[model] = {}
                        for m in ('auc', 'nll_bits', 'brier'):
                            values = [p[model][m] for p in people if model in p and p[model][m] is not None]
                            levels[model][m] = {'mean': math.fsum(values) / len(values) if values else None, 'n': len(values)}
                    output.append({'arm': arm, 'scope': scope, 'query_subset': query, 'group': group, 'expected_n': len(ids),
                                   'n_with_queries': sum(p.get('status') == 'complete' for p in people),
                                   'n_query_trials': sum(p['n_trials'] for p in people), 'mean_gain_bits': means,
                                   'n_each_gain': count, 'levels': levels, 'inference': 'descriptive equal-child mean; no new significance family inferred'})
    return output


def main():
    assert os.environ.get('SLURM_JOB_ID')
    os.umask(0o077); job = os.environ['SLURM_JOB_ID']
    private = BASE / ('run_' + job); result_dir = RESULTS / ('run_' + job)
    private.mkdir(parents=True, exist_ok=False); result_dir.mkdir(parents=True, exist_ok=False)
    binding = B.Binding(); plan = binding.load_lane('prior_science_v1')
    selected = [u for u in plan['rows'] if u['source']['dataset'] == 'private_bdf' and u['config'][1] == 'NCE' and u['config'][0] in ARMS]
    assert len(selected) == 20
    outputs = []
    for unit in selected:
        rec, path = binding.lane_record('prior_science_v1', unit)
        cache, _ = binding.cache('prior_science_v1', plan, rec)
        value, coefficients = evaluate_source(binding, unit, rec, cache, unit['config'][0])
        value.update(source_record_sha256=B.sha(path), source_record=str(path.relative_to(B.ROOT)),
                     plan_sha256=B.sha(B.BASE / 'aln34/prior_science_v1/plan.json'))
        B.write_new(result_dir / 'units' / (unit['id'] + '.json'), value)
        B.write_new(private / 'readout_parameters' / (unit['id'] + '.json'), coefficients)
        outputs.append(value)
        print(unit['id'], unit['config'][0], unit['source']['subject_fold'], 'complete', flush=True)
    summaries = aggregate(outputs, binding.expected['private_bdf'])
    receipt = {'status': 'complete', 'job': job, 'time': datetime.now().astimezone().isoformat(),
               'analysis_origin': 'exploratory_after_2026_10_18_review', 'baseline_commit': B.BASELINE,
               'source_plan_sha256': binding.plan_hashes['prior_science_v1'], 'expected_units': 20, 'complete_units': len(outputs),
               'arms': list(ARMS), 'seed': 3401, 'scope': 'private prior full-window only; fixed frozen representations',
               'expected_identities': binding.expected['private_bdf'], 'summaries': summaries,
               'encoder_forward_or_training': False, 'strict_partner_rule': 'same child, same history, different physical block, nonself; source partners restricted to ES',
               'source_row_role': 'source children ES blocks only; target query labels evaluate once',
               'optimization_acceptance': 'source optimizer success + finite objective + maxabs gradient/n_source <= 1e-7',
               'source_code_sha256': B.sha(__file__), 'binding_code_sha256': B.sha(B.__file__),
               'analysis_note_sha256': B.sha(BASE / 'ANALYSIS_NOTE.md'),
               'limits': ['log-score difference is not exact CMI', 'calibration gain alone is not clinical improvement',
                          'strict-subset and full-query estimands remain separate', 'descriptive means do not assert population uncertainty']}
    B.write_new(result_dir / 'history_interface.json', receipt)
    B.write_new(private / 'provenance.json', {'sources': binding.sources, 'private_trial_bindings': binding.private_trial_bindings,
                                           'source_manifest_sha256': binding.manifest_sha})
    B.write_new(RESULTS / 'INDEX.json', {'status': 'complete', 'job': job, 'path': str(result_dir.relative_to(B.ROOT))})
    lines = ['# ALN3.5 private history 接口与严格异 block twin', '', f"CPU Slurm {job}，{receipt['time']}；20/20 个 frozen source，64 儿童，seed 3401。", '',
             '没有重训或前向运行 encoder；复用 prior_science 的 full 特征。B1 为与 EEG 同一 source-ES 行拟合的单截距 history-only 校准；EEG 与 strict twin 使用原 C=1、有截距的 offset logistic 目标，新数值执行保存优化终止及梯度证据。', '',
             '严格 twin 仅由同儿童、同 history bin、异物理 block 的非自身 trial 组成；source 拟合两端都限制为 source-ES。无合法 twin 的 trial 保留为显式缺项；完整 query 与严格交集、q0 在 (0.01,0.99) 子集分别报告。以下为等儿童描述均值，不补造新的显著性 family。', '',
             '| Arm | 拟合/评价范围 | Query 子集 | 人数 | B1−B0 bits/trial | EEG−B0 | EEG−B1 | EEG−strict twin |',
             '|---|---|---|---:|---:|---:|---:|---:|']
    for s in summaries:
        if s['group'] != 'all': continue
        vals = ['NA' if v is None else f'{v:+.6f}' for v in s['mean_gain_bits'].values()]
        lines.append('| ' + ' | '.join([s['arm'], s['scope'], s['query_subset'], str(s['n_with_queries']), *vals]) + ' |')
    lines += ['', '每儿童完整/严格 trial、standard/deviant、history bin、common-support、原 twin 的同 block/self 回退，以及每 fold 的 source-ES 类别计数、row/twin-map hashes、拟合终止状态均在同目录 unit JSON。旧 full-query 原值和新收敛验证重拟合差额一并保留；外层 query 结果不触发重试或选择。', '',
              '如果 EEG−B0 主要由 B1−B0 吸收，概率背景修正是竞争解释；EEG−B1 与严格 twin 的剩余表现则继续约束表征解释。这里不将 log-score gain 写作精确条件互信息或临床获益。']
    doc = B.ROOT / 'docs/auditory_alignment_v3/aln35/HISTORY_INTERFACE_RESULTS.md'
    with doc.open('x') as f: f.write('\n'.join(lines) + '\n')
    B.write_new(BASE / ('completed_' + job + '.json'), {'status': 'complete', 'job': job, 'results': str(result_dir), 'units': 20})
    print(json.dumps({'status': 'complete', 'units': len(outputs), 'results': str(result_dir)}), flush=True)


if __name__ == '__main__': main()
