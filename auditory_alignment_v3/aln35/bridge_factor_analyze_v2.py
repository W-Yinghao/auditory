"""Version 2: separate same-cache score parity from archived encoder replay.

The version-1 pilot required exact archival ranks. Its small across-execution
drift is retained. Here each real target score matrix is independently checked
against the original formula on this cache; archival metrics remain diagnostics,
never replacements for any newly calculated B/T cell.
"""
from __future__ import annotations
from collections import defaultdict
from datetime import datetime
import json
import math
import os
from pathlib import Path
import numpy as np
from auditory_alignment_v3.prior33 import bridge as BR, contract as C, views as V
from . import bridge_factor as F
from . import science_binding as B


METRICS = ('logloss_bits', 'top1', 'mrr', 'rank_pct', 'mean_true_rank_1based', 'entropy_bits', 'score_std', 'mean_within_query_score_std', 'mean_own_score')


def validate_same_cache_score(new_score, original_formula_score):
    assert new_score.shape == original_formula_score.shape
    assert np.isfinite(new_score).all() and np.isfinite(original_formula_score).all()
    assert np.allclose(new_score, original_formula_score, rtol=1e-10, atol=1e-12), 'same-cache original score formula mismatch'
    return float(np.max(np.abs(new_score - original_formula_score)))


def unified_scores(matrix, U, A, mu, sd):
    """Same unified correlation as ev1, using BLAS for its flattened inner product."""
    pred = BR.ev1._apply(matrix, U.reshape(-1, U.shape[-1])).reshape(U.shape[0], U.shape[1], -1)
    pp = BR.ev1._zt(pred).reshape(len(pred), -1)
    aa = BR.ev1._zt((A - mu) / sd).reshape(len(A), -1)
    return (pp @ aa.T) / pp.shape[1]


def fixed_alpha_folds(X, Y, fold, alpha):
    """Reproduce both original bridge-cal listener-fold ridge fits, no reselection."""
    X = BR._design(X); Y = np.asarray(Y, dtype=np.float64); fold = np.asarray(fold)
    assert set(fold) == {0, 1} and alpha > 0
    full = BR._solve(X.T @ X, X.T @ Y, alpha)
    by_fold = []
    for f in (0, 1):
        a = X[fold == f]; y = Y[fold == f]
        by_fold.append(BR._solve(a.T @ a, a.T @ y, alpha))
    return full, by_fold


def fit_temperatures(item, cache, bridge):
    meta = B.read(cache / 'source_metadata.json')
    assert meta == item['source_metadata']
    with np.load(cache / 'source.npz', allow_pickle=False) as z:
        Uq, Uu, Yu, A = z['Uq'], z['Uu'], z['Yu'], z['Ac']
        fq, fu = z['fold_q'], z['fold_uc']
    assert fq.tolist() == meta['query_fold'] and fu.tolist() == meta['bridgecal_fit_fold']
    X = Uu.reshape(-1, Uu.shape[-1]); Y = (Yu.reshape(-1, Yu.shape[-1]) - bridge.a_mu) / bridge.a_sd
    full, folds = fixed_alpha_folds(X, Y, np.repeat(fu, C.SEG_TICKS), bridge.alpha_uni_cal)
    relative = float(np.linalg.norm(full - bridge.B_uni_cal) / max(1e-12, np.linalg.norm(bridge.B_uni_cal)))
    assert relative < 1e-3, ('fixed original B_bridgecal replay drift', item['key'], relative)
    own = np.asarray(meta['own'], dtype=np.int64)
    draws = BR.pool_draws(own, len(A))
    result = {}; fold_parameters = {}
    for label in ('B_donor', 'B_bridgecal'):
        taus = np.empty((2, len(BR.POOL_SIZES))); records = []
        for query_fold in (0, 1):
            mask = np.flatnonzero(fq == query_fold)
            matrix = bridge.B_uni if label == 'B_donor' else folds[1 - query_fold]
            S = unified_scores(matrix, Uq[mask], A, bridge.a_mu, bridge.a_sd)
            # Independent check against the original method on a real, small subset.
            ref = BR.FrozenBridge('NCE', matrix, bridge.a_mu, bridge.a_sd,
                                  alpha_uni=bridge.alpha_uni if label == 'B_donor' else bridge.alpha_uni_cal)
            expected = ref.scores(Uq[mask[:2]], np.empty((0,)), A[:7], 'unified')
            assert np.allclose(S[:2, :7], expected, rtol=1e-10, atol=1e-12)
            fit_parts = set(meta['bridgecal_fit_participants'][i] for i in range(len(fu)) if fu[i] == 1 - query_fold)
            query_parts = set(meta['query_participants'][i] for i in mask)
            assert not fit_parts & query_parts
            rec = {'query_fold': query_fold, 'n_queries': len(mask),
                   'query_ids_sha256': B.digest([meta['query_ids'][i] for i in mask]),
                   'query_participants': sorted(query_parts),
                   'bridgecal_fit_participants': sorted(fit_parts) if label == 'B_bridgecal' else None,
                   'no_query_listener_in_B_fit': True, 'by_pool_size': {}}
            for j, nominal in enumerate(BR.POOL_SIZES):
                cols = draws[nominal][mask]
                sub = S[np.arange(len(mask))[:, None], cols]
                tau = BR.calibrate_tau({'unified': sub})['unified']; taus[query_fold, j] = tau
                rec['by_pool_size'][str(nominal)] = {'temperature': tau, 'grid_edge': BR.grid_edge(sub, tau),
                     'candidate_draw_hash': B.digest(cols.tolist()), 'n_candidates': cols.shape[1],
                     'source_fit_metrics': F.query_metrics(sub, np.zeros(len(mask), dtype=int), tau)}
            records.append(rec)
        temperatures = np.sqrt(taus[0] * taus[1])
        result[label] = {'temperature_by_pool_size': dict(zip(map(str, BR.POOL_SIZES), temperatures.tolist())),
                         'folds': records, 'aggregation': 'geometric mean of the two source query-fold temperatures',
                         'alpha_frozen': bridge.alpha_uni if label == 'B_donor' else bridge.alpha_uni_cal}
        fold_parameters[label] = {'tau_folds': taus.tolist()}
    return result, {'relative_B_bridgecal_replay_difference': relative, 'recomputed_full_B_used_on_target': False,
                    'original_full_B_matrices_preserved': True,
                    'frozen_alpha_not_nested_in_temperature_folds': True}, folds


def analyze_entry(item, run_private, result_dir):
    cache = Path(item['cache']); receipt = B.read(cache / 'complete.json')
    assert receipt['status'] == 'complete' and receipt['key'] == item['key']
    assert receipt['plan_sha256'] == B.sha(F.BASE / 'plan.json')
    for name, digest in receipt['files'].items(): assert B.sha(cache / name) == digest, (cache, name)
    for p, digest in item['source_paths_sha256'].items(): assert B.sha(p) == digest, p
    bridge = BR.load_bridge(item['bridge_file'], expect_id=item['rows'][0]['spec']['bridge'])
    fitted, replay, folds = fit_temperatures(item, cache, bridge)
    B.write_new(run_private / (item['key'] + '_fold_matrices.json'), {'B_bridgecal_folds': [b.tolist() for b in folds]})
    rows = []; legacy = []; max_old_diff = defaultdict(float); expected_by_cf = {}; same_cache_score_max_error = 0.
    manifest = BR.open_row_manifest(item['rows'][0])
    for cf in (0, 1):
        data = np.load(cache / f'target_cf{cf}.npz', allow_pickle=False)
        meta = B.read(cache / f'target_cf{cf}_metadata.json'); A = data['Ac']
        assert len(meta['candidate_ids']) == len(A)
        expected = set()
        for sf in range(5):
            cell = V.manifest_cell(manifest, item['dataset'], sf, cf)
            expected.update(map(str, cell['test'])); expected.update(map(str, cell.get('test_only', [])))
        assert {p['id'] for p in meta['people']} == expected
        expected_by_cf[str(cf)] = sorted(expected)
        old = {}; source_unit = {}
        for source in item['rows']:
            if source['content_fold'] != cf: continue
            path = Path(B.BASE) / 'units' / (source['experiment_id'] + '.json')
            rec = B.read(path)
            for identity in rec['eval']['per_participant']:
                assert identity not in old
                old[identity] = (rec['eval']['per_participant'][identity]['unified/regular'],
                                 rec['eval_uni_cal']['per_participant'][identity]['unified/regular'])
                source_unit[identity] = source['experiment_id']
        assert set(old) == expected
        pool_index, nominal, realised = bridge.entry(len(A))
        for person in meta['people']:
            i = person['array_index']; U, own = data[f'U_{i}'], data[f'own_{i}']
            assert len(U) == len(person['query_ids']) == old[person['id']][0]['n_queries']
            assert person['own_candidate_ids'] == [meta['candidate_ids'][int(k)] for k in own]
            base = {'dataset': item['dataset'], 'arm': item['arm'], 'identity': person['id'], 'group': person['group'],
                    'content_fold': cf, 'subject_fold': person['fold'], 'seed': 3401, 'source_unit_id': source_unit[person['id']],
                    'query_ids_sha256': B.digest(person['query_ids']), 'candidate_ids_sha256': B.digest(meta['candidate_ids']),
                    'true_candidates_sha256': B.digest(person['own_candidate_ids']), 'n_queries': len(U), 'n_candidates': len(A)}
            for j, label in enumerate(('B_donor', 'B_bridgecal')):
                matrix = bridge.B_uni if j == 0 else bridge.B_uni_cal
                score = unified_scores(matrix, U, A, bridge.a_mu, bridge.a_sd)
                reference_readout = BR.FrozenBridge('NCE', matrix, bridge.a_mu, bridge.a_sd,
                    alpha_uni=bridge.alpha_uni if j == 0 else bridge.alpha_uni_cal)
                original_formula = reference_readout.scores(U, np.empty(0), A, 'unified')
                same_cache_score_max_error = max(same_cache_score_max_error, validate_same_cache_score(score, original_formula))
                original_tau = bridge.tau_unified[pool_index] if j == 0 else bridge.tau_cal[pool_index]
                old_replay = F.query_metrics(score, own, original_tau)
                differences = {metric: float(old_replay[metric] - old[person['id']][j][metric])
                               for metric in ('logloss_bits', 'top1', 'mrr', 'rank_pct')}
                for metric, diff in differences.items(): max_old_diff[metric] = max(max_old_diff[metric], abs(diff))
                legacy.append({**base, 'bridge': label, 'original_temperature': float(original_tau),
                               'original_metrics': old[person['id']][j], 'replayed_metrics': old_replay,
                               'replay_minus_original': differences, 'source_path': str(Path(B.BASE) / 'units' / (base['source_unit_id'] + '.json'))})
                previous = None
                for temperature_rule in ('fixed_one', 'source_fold_calibrated'):
                    tau = 1. if temperature_rule == 'fixed_one' else fitted[label]['temperature_by_pool_size'][str(nominal)]
                    metrics = F.query_metrics(score, own, tau)
                    if previous is not None:
                        for metric in ('top1', 'mrr', 'rank_pct', 'mean_true_rank_1based'): assert metrics[metric] == previous[metric]
                    previous = metrics
                    rows.append({**base, 'bridge': label, 'temperature_rule': temperature_rule,
                                 'source_calibration_pool_nominal': nominal, 'source_calibration_pool_realised': realised, 'metrics': metrics})
        data.close()
    # Historical feature arrays were not saved. Quantify their execution drift;
    # do not overwrite those archived endpoints or silently call it exact reuse.
    # The strict checks above instead bind frozen sources, real queries and the
    # original score formula for every new cell on the SAME replay cache.
    result = {'key': item['key'], 'status': 'complete', 'seed': 3401, 'expected_by_content_fold': expected_by_cf,
              'source_units': [r['experiment_id'] for r in item['rows']], 'cache_receipt_sha256': B.sha(cache / 'complete.json'),
              'source_paths_sha256': item['source_paths_sha256'], 'source_metadata_digest': B.digest(item['source_metadata']),
              'B_fit_data': {k: item['source_metadata'][k] for k in ('n_donor_fit_segments', 'n_bridgecal_fit_segments', 'fit_rows_by_stratum', 'fit_rows_sha256', 'uni_cal_rows_sha256', 'cal_rows_sha256')},
              'calibration': fitted, 'readout_replay': replay, 'legacy_replay_max_absolute_difference': dict(max_old_diff),
              'same_cache_original_formula_max_absolute_difference': same_cache_score_max_error,
              'legacy_replay_interpretation': 'archived metrics retained; replay is not bitwise-identical and never replaces the archive; small execution drift inspected and reported separately',
              'query_results': rows, 'original_endpoints': legacy}
    B.write_new(result_dir / 'entries' / (item['key'] + '.json'), result)
    print(json.dumps({'key': item['key'], 'status': 'complete', 'legacy_replay': dict(max_old_diff)}), flush=True)
    return result


def summarize(entries):
    people = defaultdict(list); metadata = {}
    for entry in entries:
        for r in entry['query_results']:
            k = (r['dataset'], r['arm'], r['bridge'], r['temperature_rule'], r['identity'])
            people[k].append(r['metrics']); metadata[k] = r
    paired = {}
    for k, rr in people.items():
        assert len(rr) == 2, ('two content folds per person expected', k)
        paired[k] = {m: math.fsum(r[m] for r in rr) / len(rr) for m in METRICS}
    cells = defaultdict(list)
    for k, metrics in paired.items(): cells[k[:4]].append((k[-1], metrics))
    summaries = []
    for k, rr in sorted(cells.items()):
        summaries.append(dict(zip(('dataset', 'arm', 'bridge', 'temperature_rule'), k), n=len(rr),
                    metrics={m: math.fsum(v[m] for _, v in rr) / len(rr) for m in METRICS}))
    comparisons = []
    # All requested same-temperature arm contrasts; NLL risk benefit = reference - candidate.
    for ds, arm in (('dtu', 'AP'), ('fau', 'XP')):
        for bridge in ('B_donor', 'B_bridgecal'):
            for rule in ('fixed_one', 'source_fold_calibrated'):
                a = dict(cells[(ds, arm, bridge, rule)]); b = dict(cells[(ds, 'XM', bridge, rule)])
                assert set(a) == set(b)
                differences = {p: {m: a[p][m] - b[p][m] for m in METRICS} for p in sorted(a)}
                comparisons.append({'dataset': ds, 'candidate_arm': arm, 'reference_arm': 'XM', 'bridge': bridge, 'temperature_rule': rule,
                    'n': len(a), 'mean_candidate_minus_reference': {m: math.fsum(d[m] for d in differences.values()) / len(a) for m in METRICS},
                    'NLL_benefit_reference_minus_candidate': -math.fsum(d['logloss_bits'] for d in differences.values()) / len(a),
                    'per_identity_differences': differences})
    factor_differences = []
    for ds, arm in (('dtu', 'AP'), ('dtu', 'XM'), ('fau', 'XP'), ('fau', 'XM')):
        specifications = [('mapping_at_T1', ('B_bridgecal', 'fixed_one'), ('B_donor', 'fixed_one')),
                          ('temperature_in_B_donor', ('B_donor', 'source_fold_calibrated'), ('B_donor', 'fixed_one')),
                          ('temperature_in_B_bridgecal', ('B_bridgecal', 'source_fold_calibrated'), ('B_bridgecal', 'fixed_one'))]
        for label, aa, bb in specifications:
            a = dict(cells[(ds, arm, *aa)]); b = dict(cells[(ds, arm, *bb)])
            assert set(a) == set(b)
            factor_differences.append({'dataset': ds, 'arm': arm, 'contrast': label, 'n': len(a),
                                      'mean_first_minus_second': {m: math.fsum(a[p][m] - b[p][m] for p in a) / len(a) for m in METRICS}})
    return summaries, comparisons, factor_differences


def verify_common_queries(entries):
    """Contrasts bind real per-person/per-fold rosters, not only matching n."""
    coverage = defaultdict(dict)
    for entry in entries:
        for r in entry['query_results']:
            unit = (r['dataset'], r['identity'], r['content_fold'])
            condition = (r['arm'], r['bridge'], r['temperature_rule'])
            assert condition not in coverage[unit]
            coverage[unit][condition] = tuple(r[k] for k in ('query_ids_sha256', 'candidate_ids_sha256', 'true_candidates_sha256', 'n_queries', 'n_candidates'))
        first = entry['calibration']['B_donor']['folds']
        second = entry['calibration']['B_bridgecal']['folds']
        for a, b in zip(first, second):
            assert a['query_fold'] == b['query_fold'] and a['query_ids_sha256'] == b['query_ids_sha256']
            for pool in a['by_pool_size']:
                assert a['by_pool_size'][pool]['candidate_draw_hash'] == b['by_pool_size'][pool]['candidate_draw_hash']
    for unit, conditions in coverage.items():
        assert len(conditions) == 8 and len(set(conditions.values())) == 1, ('unpaired real queries/candidates', unit)
    return {'status': 'PASS', 'person_content_fold_cells': len(coverage),
            'each_cell_has_all_two_arms_two_B_two_T_on_identical_real_queries': True,
            'source_query_folds_and_candidate_draws_identical_across_B': True}


def main():
    assert os.environ.get('SLURM_JOB_ID')
    os.umask(0o077); job = os.environ['SLURM_JOB_ID']; plan = B.read(F.BASE / 'plan.json')
    contract = B.read(F.BASE / 'analysis_contract_v2.json')
    for path, digest in contract['frozen_analysis_files_sha256'].items(): assert B.sha(B.ROOT / path) == digest, path
    assert contract['plan_sha256'] == B.sha(F.BASE / 'plan.json')
    private = F.BASE / ('run_' + job); out = F.RESULTS / ('run_' + job)
    private.mkdir(parents=True, exist_ok=False); out.mkdir(parents=True, exist_ok=False)
    entries = [analyze_entry(item, private, out) for item in plan['entries']]
    common_coverage = verify_common_queries(entries)
    summaries, comparisons, factor = summarize(entries)
    report = {'status': 'complete', 'job': job, 'time': datetime.now().astimezone().isoformat(), 'baseline_commit': B.BASELINE,
              'analysis_origin': plan['analysis_origin'], 'plan_sha256': B.sha(F.BASE / 'plan.json'),
              'analysis_code_sha256': B.sha(__file__), 'source_units': 40, 'donors': 4, 'new_B_T_cells': 16,
              'analysis_contract_sha256': B.sha(F.BASE / 'analysis_contract_v2.json'),
              'analysis_note_sha256': B.sha(F.BASE / 'ANALYSIS_NOTE.md'),
              'versioned_replay_note_sha256': B.sha(F.BASE / 'REPLAY_NUMERICS_V2.md'),
              'comparison_version': 'S35_BRIDGE_FACTOR_v2_replayed_features_original_matrices',
              'prior_failed_engineering_job': '1047360',
              'common_coverage': common_coverage,
              'summaries': summaries, 'arm_contrasts': comparisons, 'factor_differences': factor,
              'inference': 'descriptive equal-person means; first average both content folds within identity; no new testing family',
              'selection_level': 'all B/alpha/checkpoint/T selection source-only; source-listener readout folds with frozen alpha, not nested whole-pipeline validation; shared source presentations',
              'all_temperature_ranks_invariant': True, 'encoder_training': False,
              'limits': ['B mapping difference includes fit population/montage change', 'fixed selected alphas are not nested inside T folds',
                         'T calibration uses same source query folds and candidate draws; target queries only evaluated']}
    B.write_new(out / 'bridge_factor.json', report)
    B.write_new(F.RESULTS / 'INDEX.json', {'status': 'complete', 'job': job, 'path': str(out.relative_to(B.ROOT)), 'result_sha256': B.sha(out / 'bridge_factor.json')})
    lines = ['# ALN3.5 bridge 映射与概率温度分解', '', f'CPU Slurm {job}；4 个冻结 donor，40 个原 zero-shot unit，16 个 arm×B×T 条件。', '',
             'NCE seed3401，DTU AP/XM、FAU XP/XM，原 mode A。B_donor 与 B_bridgecal 原完整矩阵和 alpha 不变；两者各 2,000 个 source 拟合 segment。前者保留原 donor-fit 的 montage 混合，后者为 bridge-cal 全 montage；B 差异包含映射拟合人群/采样变化。', '',
             'T=1 与同 source listener 两折的温度规则比较。两 B 共用 query、候选、poolsize、分折；B_bridgecal 的该折 query 只由另一 listener 折拟合的矩阵产生分数，T 取两折几何均值。原 alpha 与 donor 选择未嵌套在 T 折内、source presentations 跨折共享，因此这是固定超参数的 source-side 读出交叉拟合。目标 EEG/标签没有参与参数拟合或选择。', '',
             '每人先平均两个 content fold，再等人求描述均值；没有将 fold 当作新参与者。原已发布两端点及原温度全部保留在 entries JSON，重放误差逐项记录。v1 的跨执行 rank 完全相等断言失败保留（CPU1047360）；v2 对每个真实分数矩阵验证同一新缓存上的原 BR 公式，历史冻结 encoder 重放误差单列，绝不以旧分数替代新四格。', '',
             '| Dataset | Arm | B | T rule | n | NLL bits | top1 | mean true rank | entropy bits | score SD |',
             '|---|---|---|---|---:|---:|---:|---:|---:|---:|']
    for s in summaries:
        m = s['metrics']; lines.append(f"| {s['dataset']} | {s['arm']} | {s['bridge']} | {s['temperature_rule']} | {s['n']} | {m['logloss_bits']:.6f} | {m['top1']:.6f} | {m['mean_true_rank_1based']:.3f} | {m['entropy_bits']:.6f} | {m['score_std']:.6f} |")
    lines += ['', '| Dataset | 对比 | B | T rule | 配对人数 | ΔR (XM NLL − candidate NLL, bits) |', '|---|---|---|---|---:|---:|']
    for s in comparisons: lines.append(f"| {s['dataset']} | {s['candidate_arm']}−XM | {s['bridge']} | {s['temperature_rule']} | {s['n']} | {s['NLL_benefit_reference_minus_candidate']:+.6f} |")
    lines += ['', '正温度下同一 B 的全部 query rank/top1 严格不变，断言已通过。NLL 与熵可以变化；因此不能以 NLL 符号变化自动推断候选排序改变，亦不选更有利 bridge 替换原主结果。16 格、直接配对差与每人 provenance 完整保留，结果为描述性的接口敏感性分析。']
    with (B.ROOT / 'docs/auditory_alignment_v3/aln35/BRIDGE_FACTOR_RESULTS.md').open('x') as f: f.write('\n'.join(lines) + '\n')
    B.write_new(F.BASE / ('completed_' + job + '.json'), {'status': 'complete', 'job': job, 'results': str(out), 'donors': 4})
    print(json.dumps({'status': 'complete', 'result': str(out)}), flush=True)


if __name__ == '__main__': main()
