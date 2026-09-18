"""Zero-refit verification and comprehensive report for the archival repair round.

Executed only through extended.py's Slurm entrypoint. Recomputes published
metrics from durable OOF predictions; never calls a model fitting function.
"""
import ast
import json
import os
import re
import shutil
import stat
from pathlib import Path

import numpy as np
import pandas as pd

from .extended import ROOT, dump, sha

PRIV = ROOT / 'private/auditory_repair'
PUB = ROOT / 'results/auditory_repair'


def read(path):
    return json.loads(Path(path).read_text())


def close(a, b):
    np.testing.assert_allclose(a, b, rtol=1e-10, atol=1e-10)


def interval(d):
    # Independent implementation of the registered fixed-OOF identity bootstrap.
    loss = np.mean(d, axis=0)
    ix = np.random.default_rng(9127).integers(0, len(loss), (2000, len(loss)))
    lo, hi = np.quantile(np.mean(loss[ix], axis=1), [.025, .975])
    loo = (sum(loss) - loss) / (len(loss) - 1)
    return dict(gain_MAE=np.mean(loss), ci_low=lo, ci_high=hi,
                positive_repeats=int(np.sum(np.mean(d, axis=1) > 0)),
                leave_one_identity_min=min(loo), leave_one_identity_max=max(loo))


def check_predictions(run, task_column='task'):
    frame = pd.read_csv(PRIV / run / 'predictions.csv')
    metrics = pd.read_csv(PUB / run / 'metrics.csv')
    expected = {
        'ha_extended_001': (65, {'A','V','V_given_A','CAP','SIR'}),
        'ha_mechanism_001': (18, {'A','V_given_A'}),
        'phase3_replay_002': (27, {'MUSS','age','log_duration'}),
        'mff_archival_001': (28, {'A','V','CAP','SIR'}),
    }
    expected_rows, expected_tasks = expected[run]
    assert len(metrics) == expected_rows and set(metrics[task_column]) == expected_tasks
    assert not frame.duplicated([task_column, 'model', 'repeat', 'group']).any()
    assert np.isfinite(frame[['y', 'prediction']].to_numpy()).all()
    checked, packages = [], {}
    for task, sub in frame.groupby(task_column):
        pack = dict(np.load(PRIV / run / f'{task}_complete_oof.npz', allow_pickle=False))
        packages[task] = pack
        n = len(pack['y'])
        groups = None
        if run in ['ha_extended_001', 'ha_mechanism_001']:
            data = np.load(PRIV / 'ha_prepare_001/data.npz')
            groups = data['groups']
            close(pack['y'], data['V' if task == 'V_given_A' else task])
        elif run == 'phase3_replay_002':
            groups = pd.read_csv(PRIV / run / 'cohort.csv').participant_id.to_numpy(str)
        elif 'groups' in pack:
            groups = pack['groups']
            binding = read(PRIV / run / 'input_binding.json')
            data = np.load(ROOT / 'private/results/auditory_repair' / binding['run'] / 'data.npz')
            mask = data[task + '_valid'].astype(bool) & np.isfinite(data[task])
            np.testing.assert_array_equal(groups, data['groups'][mask])
            close(pack['y'], data[task][mask])
        assert groups is not None and len(set(groups)) == n
        for model, rows in sub.groupby('model'):
            assert len(rows) == n * 5 and set(rows['repeat']) == set(range(5))
            matrix = rows.pivot(index='group', columns='repeat', values='prediction').loc[groups].to_numpy().T
            ys = rows.pivot(index='group', columns='repeat', values='y').loc[groups].to_numpy().T
            close(matrix, pack[model]); close(ys, np.tile(pack['y'], (5, 1)))
            published = metrics[(metrics[task_column] == task) & (metrics.model == model)]
            assert len(published) == 1 and int(published.iloc[0]['n']) == n
            err = matrix - pack['y']
            mae = np.abs(err).mean(); close(mae, published.iloc[0].MAE)
            if 'RMSE' in published:
                close(np.sqrt(np.mean(err**2)), published.iloc[0].RMSE)
            checked.append(dict(run=run, task=task, model=model, n=n, prediction_rows=len(rows), MAE=mae))
    assert len(checked) == len(metrics)
    return checked, packages


def check_effects(run, packages):
    if run == 'ha_extended_001':
        rows = read(PUB / run / 'effects_all_repeats.json')
    else:
        rows = read(PUB / run / 'effects.json')
    ci_pairs = dict(source_technical_increment=('SOURCE_TECH', 'SOURCE_TECH_Z'),
                    content=('SOURCE_TECH_SHUFFLE', 'SOURCE_TECH_Z'),
                    full_quality_increment=('ALL_Q', 'ALL_Q_Z'), EEG_alone=('MEAN', 'Z_ONLY'))
    for row in rows:
        task = row.get('task', row.get('target')); pack = packages[task]
        if run.startswith('mff_'):
            a, b = ci_pairs[row['contrast']]
        else:
            a, b = row['baseline'], row.get('augmented', row.get('model'))
        independently = interval(np.abs(pack[a] - pack['y']) - np.abs(pack[b] - pack['y']))
        for key, value in independently.items():
            close(value, row[key])
    return len(rows)


def check_splits(rows, n):
    for rep in range(5):
        current = [s for s in rows if s['repeat'] == rep]
        assert len(current) == 5
        tests = []
        for row in current:
            tr, te = set(row['train']), set(row['test'])
            assert not tr & te and tr | te == set(range(n))
            seen = []
            for inner in row['inner']:
                a, b = set(inner['train']), set(inner['validation'])
                assert not a & b and a | b == tr and not (a | b) & te
                seen.extend(b)
            assert sorted(seen) == sorted(tr)
            tests.extend(te)
        assert sorted(tests) == list(range(n))


def check_sources(private):
    checks = []
    for start in PRIV.glob('*/start.json'):
        obj = read(start)
        for rel, expected in obj.get('source_hashes', {}).items():
            path = start.parent / 'source' / rel
            assert path.is_file() and sha(path) == expected, 'SNAPSHOT_MISMATCH'
            checks.append(dict(kind='executed_source_snapshot', path=str(path), hash=expected))
    for run, name in [('ha_prepare_001', 'inputs.json'), ('phase3_replay_002', 'input_hashes.json')]:
        for absolute, expected in read(PRIV / run / name).items():
            assert sha(absolute) == expected, 'DATA_INPUT_CHANGED'
            checks.append(dict(kind='data_input', path=absolute, hash=expected))
    prepared = PRIV / 'ha_prepare_001/data.npz'
    assert sha(prepared) == read(PRIV / 'ha_prepare_001/completion.json')['data_sha256']
    assert sha(prepared) == read(PRIV / 'ha_extended_001/input_binding.json')['data_sha256']
    # D's immutable, executed sources and all inner/outer projection inputs.
    manifest = read(PRIV / 'legacy_d_002/source_manifest.json')
    assert not manifest['missing_sources']
    for absolute, value in manifest['sources'].items():
        path = Path(absolute)
        if path.suffix in ['.py', '.yaml']:
            path = PRIV / 'legacy_d_002/source_snapshot' / path.name
        assert sha(path) == value['sha256'], 'LEGACY_D_INPUT_CHANGED'
        checks.append(dict(kind='legacy_D_input', path=str(path), hash=value['sha256']))
    binding = read(PRIV / 'mff_archival_001/input_binding.json')
    ci = ROOT / 'private/results/auditory_repair' / binding['run']
    assert sha(ci / 'data.npz') == binding['data_sha256']
    assert sha(ci / 'cohort.csv') == binding['cohort_sha256']
    from .ci_prepare import INPUTS
    for name, expected in read(ci / 'input_sha256.json').items():
        assert sha(INPUTS[name]) == expected, 'CI_PREPARATION_INPUT_CHANGED'
        checks.append(dict(kind='CI_preparation_input',path=str(INPUTS[name]),hash=expected))
    dump(private / 'verified_sources.json', checks)
    return dict(source_bindings_checked=len(checks), mff_preparation=binding['run'])


def check_legacy_d():
    run = PRIV / 'legacy_d_002'
    saved = pd.read_parquet(run / 'corrected_clinical_oof.parquet')
    assert len(saved) == 51 * 27 * 3
    assert not saved.duplicated(['mode', 'split_group_id', 'model']).any()
    old = read(run / 'old_replay_verification.json')
    assert len(old) == 3 and all(r['status'] == 'PASS' and r['rows_checked'] == 1377 for r in old)
    report = read(PUB / 'legacy_d_002/aggregate.json')
    for mode in report['modes']:
        rows = saved[saved['mode'] == mode['mode']]
        assert rows.split_group_id.nunique() == 51
        for model, score in mode['MAE'].items():
            sub = rows[rows.model == model]
            assert len(sub) == 51
            close(np.abs(sub.target - sub.prediction).mean(), score)
        for label, a, b in [('C_vs_CV','D1_C','D2_CV'), ('CV_vs_CVN','D2_CV','D3_CVN'),
                            ('C_vs_CVN','D1_C','D3_CVN'), ('C_vs_FULL','D1_C','D5_CFULL'), ('C_vs_PRE','D1_C','D7_CPRE')]:
            close(mode['MAE'][a] - mode['MAE'][b], mode['gains'][label]['estimate'])
    return dict(prediction_rows=len(saved), modes=3, models_per_mode=27,
                old_replay_max_difference=max(r['max_abs_prediction_difference'] for r in old))


def check_pairs():
    base = PRIV / 'pairs_003'
    summary = read(PUB / 'pairs_003/summary.json')
    assert summary['status'] == 'COMPLETED' and summary['fit_calls'] == 0
    for row in read(base / 'source_manifest.json'):
        assert sha(ROOT / row['path']) == row['sha256'], 'PAIR_SOURCE_CHANGED'
    f3 = pd.read_csv(base / 'f3_pair_measurements.csv')
    ha = pd.read_csv(base / 'f4_ha_pair_measurements.csv')
    assert len(f3) == summary['f3']['candidate_pairs'] == 9
    assert len(ha) == summary['f4_ha']['candidate_pairs'] == 15
    assert ha.participant_id.nunique() == summary['f4_ha']['candidate_identity_groups'] == 13
    for window in ['main','late']:
        a = f3[f'puretone_{window}_uv'].to_numpy(float)
        b = f3[f'bapa_{window}_uv'].to_numpy(float)
        close(b-a, f3[f'{window}_delta_bapa_minus_puretone_uv'])
        close(np.median(b-a),summary['f3']['metrics'][window]['difference_bapa_minus_puretone_uv']['median'])
        close(np.corrcoef(a,b)[0,1],summary['f3']['metrics'][window]['task_value_correlation']['pearson_r'])
    good = ha[['a_hp01_avg20_code1_uv','b_hp01_avg20_code1_uv']].notna().all(axis=1)
    assert sum(good) == summary['f4_ha']['pairs_with_both_measurements'] == 10
    close(ha.loc[good,'b_hp01_avg20_code1_uv']-ha.loc[good,'a_hp01_avg20_code1_uv'],ha.loc[good,'delta_b_minus_a_uv'])
    close(ha.loc[good,'delta_b_minus_a_uv'].median(),summary['f4_ha']['delta_b_minus_a_uv']['median'])
    return dict(f3_pairs=9,f3_candidate_groups=int(f3.participant_id.nunique()),HA_pairs=15,HA_measured_pairs=10,
                HA_measured_candidate_groups=int(ha.loc[good,'participant_id'].nunique()),MFF_multidate_candidate_groups=2)


def accounting(private, config):
    events = []
    for path in PRIV.glob('*/fit_events.jsonl'):
        count = 0
        with path.open() as handle:
            for line in handle:
                row = json.loads(line); count += 1
                assert row['attempt'] == count
        completion = path.parent / 'completion.json'
        if completion.exists():
            assert read(completion)['fit_attempts'] == count
        events.append(dict(run=path.parent.name, logged_attempts=count, supplemental_attempts=0))
    for name in ['legacy_d_001', 'legacy_d_002']:
        obj = read(PRIV / name / 'fit_attempt_ledger.json')
        assert obj['failures'] == 0
        events.append(dict(run=name, logged_attempts=obj['attempts'], supplemental_attempts=405 if name.endswith('001') else 0))
    for row in events:
        if row['run'] == 'followup_tests_001':
            row['supplemental_attempts'] = 3
    total = sum(r['logged_attempts'] + r['supplemental_attempts'] for r in events)
    assert total <= config['limits']['total_head_fit_attempts'], 'ROUND_BUDGET_EXCEEDED'
    jobs = read(ROOT / 'docs/auditory_repair/JOBS.json')['jobs']
    shutil.copyfile(ROOT / 'docs/auditory_repair/JOBS.json',private/'jobs_snapshot.json')
    assert len({j['job_id'] for j in jobs}) == len(jobs)
    assert os.environ['SLURM_JOB_ID'] in {str(j['job_id']) for j in jobs}, 'CURRENT_JOB_NOT_REGISTERED'
    hours = sum(j['accounted_cpus'] * j['time_limit_minutes'] / 60 for j in jobs)
    assert hours <= config['limits']['cpu_reserved_core_hours']
    result = dict(head_call_attempts=total, head_call_limit=config['limits']['total_head_fit_attempts'],
                  events=events, scheduler_jobs=len(jobs), reserved_core_hours_upper_bound=hours,
                  actual_accounting_available=False, GPU_hours=0,
                  accounting_notes=['Counts include mean-head calls, synthetic tests and failed attempts.',
                    'legacy_d_001 omitted 405 old replay calls; included as supplemental.',
                    'followup_tests_001 omitted 3 kernel solves; included as supplemental.',
                    'legacy_d_002 unnecessarily repeated completed predictions to repair accounting; both runs charged.',
                    'Legacy D synthetic tests have zero fitting calls; PTA/CI preparation/verification fit no heads.',
                    'Reserved core-hour bound uses full job time limits, including failed jobs; not measured CPU use.'])
    dump(private / 'accounting.json', result)
    return result


def table(frame, columns=None, digits=3):
    if columns is not None:
        frame = frame[columns]
    def fmt(x):
        if isinstance(x, (float, np.floating)):
            return f'{x:.{digits}f}'
        return str(x).replace('|', '/')
    lines = ['| ' + ' | '.join(frame.columns) + ' |', '| ' + ' | '.join(['---'] * len(frame.columns)) + ' |']
    lines += ['| ' + ' | '.join(fmt(x) for x in row) + ' |' for row in frame.itertuples(index=False, name=None)]
    return '\n'.join(lines)


def effects_table(rows):
    out = []
    for r in rows:
        out.append(dict(task=r.get('task',r.get('target')), comparison=r.get('contrast',r.get('model')),
                        gain=r['gain_MAE'], interval=f"[{r['ci_low']:.3f}, {r['ci_high']:.3f}]",
                        positive_repeats=f"{r['positive_repeats']}/5",
                        leave_one_out=f"[{r['leave_one_identity_min']:.3f}, {r['leave_one_identity_max']:.3f}]"))
    return table(pd.DataFrame(out))


def figures(folder, extended, followup, mixed, reliability, legacy):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    folder.mkdir()
    plt.rcParams.update({'font.size':9, 'savefig.dpi':180, 'axes.spines.top':False, 'axes.spines.right':False})
    def forest(rows, name, title):
        fig, ax = plt.subplots(figsize=(9,max(3, .34 * len(rows) + 1)))
        y = np.arange(len(rows)); means = np.array([r['gain_MAE'] for r in rows])
        lows = np.array([r['ci_low'] for r in rows]); highs = np.array([r['ci_high'] for r in rows])
        ax.errorbar(means, y, xerr=[means-lows, highs-means], fmt='o', color='#176b87', capsize=3)
        ax.set_yticks(y, [str(r.get('task','')) + ' / ' + str(r['contrast']) for r in rows])
        ax.invert_yaxis(); ax.axvline(0, color='0.4', lw=1)
        ax.set_xlabel('MAE reduction (positive favors augmented model); raw score units')
        ax.set_title(title); fig.tight_layout()
        for ext in ['pdf','png']: fig.savefig(folder / f'{name}.{ext}', bbox_inches='tight')
        plt.close(fig)
    forest([r for r in extended if r['contrast'] in ['joint_selector','quality_adjusted','content_control']],
           'ha_primary_controls', 'HA, 57 candidate identities; fixed-OOF 95% identity bootstrap')
    forest(followup, 'ha_mechanism', 'Subsequent quality decomposition and Gaussian kernel sensitivity')
    forest(mixed, 'mixed_mff', 'Mixed-MFF archival association; not a CI clinical validation')
    fig, axes = plt.subplots(1,2,figsize=(10,4),sharey=True)
    for ax, split in zip(axes,['odd_even','early_late']):
        for bank, rows in reliability[reliability['split']==split].groupby('bank',sort=False):
            ax.plot(rows.budget,rows.median_correlation, marker='o',label=bank)
        ax.set(xlabel='Total sampled trials',title=split,ylim=(-.15,1.05),xticks=[32,64,128,256]);ax.axhline(0,color='0.7',lw=.7)
    axes[0].set_ylabel('Median featurewise cross-identity Pearson r');axes[1].legend(fontsize=8)
    fig.suptitle('Same 43 identities at every trial budget; split-half reliability is not clinical validity')
    fig.tight_layout()
    for ext in ['pdf','png']:fig.savefig(folder/f'matched_reliability.{ext}',bbox_inches='tight')
    plt.close(fig)
    rows=[]
    for m in legacy['modes']:
        for label in ['C_vs_CV','CV_vs_CVN','C_vs_CVN','C_vs_FULL','C_vs_PRE']:
            g=m['gains'][label]
            rows.append(dict(task=m['mode'],contrast=label,gain_MAE=g['estimate'],ci_low=g['ci_lower'],ci_high=g['ci_upper']))
    forest(rows,'legacy_D_repaired','Original 51 identities and original folds; corrected PTA readout')


def write_report(folder, verification, pta, counts, ci_run):
    extended=read(PUB/'ha_extended_001/effects_all_repeats.json')
    followup=read(PUB/'ha_mechanism_001/effects.json')
    mixed=read(PUB/'mff_archival_001/effects.json')
    legacy=read(PUB/'legacy_d_002/aggregate.json')
    reliability=pd.read_csv(PUB/'reliability_matched_001/reliability_matched.csv')
    ci=read(PUB/ci_run/'summary.json')
    support=read(PUB/'mff_archival_001/target_support.json')
    figures(folder/'figures',extended,followup,mixed,reliability,legacy)
    mff_support=pd.DataFrame([dict(task=r['task'],n=r['n'],finite_age=r['finite_age_count'],sources=json.dumps(r['source_labels'],ensure_ascii=False)) for r in support])
    legacy_rows=[]
    for mode in legacy['modes']:
        for label in ['C_vs_CV','CV_vs_CVN','C_vs_CVN','C_vs_FULL','C_vs_PRE']:
            g=mode['gains'][label]
            legacy_rows.append(dict(representation=mode['mode'],contrast=label,gain=g['estimate'],interval=f"[{g['ci_lower']:.3f}, {g['ci_upper']:.3f}]"))
    ha_metrics=pd.read_csv(PUB/'ha_extended_001/metrics.csv')
    rel=reliability.pivot(index='bank',columns=['budget','split'],values='median_correlation')
    rel_table=pd.DataFrame(dict(bank=rel.index,odd_even_32=rel[(32,'odd_even')],odd_even_256=rel[(256,'odd_even')],early_late_32=rel[(32,'early_late')],early_late_256=rel[(256,'early_late')]))
    strata=pd.read_csv(PUB/'ha_extended_001/strata_descriptive.csv')
    full = f'''# 保守停止策略下的 PTA 修正与扩展探索：完整结果

本轮按预先列出的任务完成分析，没有根据显著性、置信区间是否跨零、效应大小或表征排名提前停止。所有结果均为已被反复研究的档案数据上的探索证据，不是独立临床验证。这里保留小的正向结果，也列出改变解释的控制实验。

## 本轮完成了什么

- HA：57 个候选身份，每人一个最早合格记录，5 个固定特征库、5 个任务、13 个模型方案，5 次重复的 5 折外层／3 折内层验证；65 个任务×模型结果全部保留。
- 在相同的两个主要任务上，补齐技术质量、振幅、完整质量和有限高斯核非线性检验。
- 旧 Phase 3：原 50 人、原划分，先复现旧预测，再修正 PTA；所有原任务及单独惩罚敏感性完成。
- 旧 auditory5 D：原 51 人、原划分、原训练范围的缓存表征，L0／监督／自监督三种模式，各 27 个模型全部完成。
- 试次数可靠性：同一批 43 个身份，32／64／128／256 试次、两种分半、五个特征库，40 行结果全部完成。
- CI／MFF：203 个 canonical 记录的来源和测量描述；另完成身份核验后的混合 MFF 档案分数回归，四终点、七个模型方案全部保留。
- 最终独立聚合验证、来源绑定核验、拟合记账、隐私权限与图表生成。最终验证没有重新训练模型。

## 数据、目标与验证方法

A 表示档案 IT-MAIS/MAIS 列；V 表示 MUSS 列；V_given_A 表示已知 A 时预测 V。A/V 的量表版本、EEG 与评估的同期性仍未全部确证，不能写作已确证的同期功能量。HA 使用原表分值，混合 MFF 的 0–40 原始值保留原单位，未擅自乘以 2.5。CAP、SIR 是原始有序分数的探索性误差比较，不产生诊断阈值。

HA 纳入以来源、身份、必要字段和至少每个字面事件码两次可用试次为基础；未沿用早期每条件 40／总数 64／队列 30 的科学推进门槛。五种特征为 HJORTH(60)、POST(320)、CONTRAST(160)、PRE(160)、SPATIAL(210)，每记录最多均匀取 256 个按时间排序的接受 epoch。1/2 未被擅自命名为标准／偏差音；CONTRAST 只是 code2−code1。

标准化、缺失值插补与指示变量、临床线性／二次基、惩罚和联合特征库选择均在训练内部完成。候选身份不跨训练和验证。EEG 联合模型包括退回临床基线的选择；外层最佳特征库不重新充当主要模型。质量控制与非线性补充是在看到首轮结果之后明确追加的探索分析。

表中 gain = 基线 MAE − 加入信息后 MAE，正值代表改善。区间来自 2,000 次候选身份 bootstrap：先对同一人的五次外层误差取平均，再抽取身份。它是固定 OOF 预测的 95% 区间，不包含整条训练流程重抽样的不确定性，也未对多任务／多表征比较作确证性校正。五次重复不是五倍人数。leave-one-out 是从固定误差中删去一个身份的敏感性，不是重训 LOOCV。

## PTA 历史错误与修正边界

旧脚本把非空记录的顺序号作为临床 ID，而注册表的 C 编号指向实际工作表行。57 行中，较好耳未助听 PTA 有 {pta['better_unaided_pta_changed_n']} 行改变，助听 PTA 有 {pta['better_aided_pta_changed_n']} 行改变。实际源行号码改变 {pta['source_row_changed_n']} 行；本次以数值比较修正了 pta_007 汇总中把字符串格式差异算作变更的问题，007 的 PTA 数值表经重新逐表校验一致。

未助听完整数 {pta['old_unaided_complete_n']}→{pta['corrected_unaided_complete_n']}；助听完整数 {pta['old_aided_complete_n']}→{pta['corrected_aided_complete_n']}。旧 D 支持 {pta['old_D_group_n']}→{pta['corrected_D_group_n']}，其中增加 {pta['D_membership_gained_record_n']}、失去 {pta['D_membership_lost_record_n']}。复现旧划分完全一致；仅修正支持后重新运行原平衡算法，会有 {pta['fold_assignment_changed_group_n']}/{pta['old_eligible_group_n']} 个外层组改变。

本轮旧模型的配对修正保留原队列和原划分，不把旧缓存投影用于新划分。新的 52 人 D 队列及新的 encoder 划分尚未整套训练；这与本轮已经完成的 51 人配对修正是不同实验。不能宣称所有下游旧结论已修复，也不能仅因反事实划分改变就宣称旧划分存在身份泄漏。历史原文件保留。

## HA：每个预定任务与特征库均保留

{effects_table(extended)}

主要值得保留的线索是 V_given_A 的联合选择增益约 +0.289 分，固定 OOF 区间约 [0.010, 0.583]，3/5 次重复正向；去掉任何单个身份后，固定误差平均增益仍为正。相较训练内打乱 EEG 的对照也呈正向。它说明当前数据存在一个条件关联线索，不证明听觉与言语功能已被成功分离，更不证明临床效用。

A 的 Hjorth 单库改善约 +0.141 分，区间跨零，4/5 次重复正向；联合选择并未改善。该小效应没有被门槛删去，但事后挑出最好的库不能替代联合选择的泛化结果。临床二次基相对线性基的改善需要单列，避免将欠拟合临床基线造成的差距误归因于 EEG。

### 绝对预测误差

{table(ha_metrics,['task','model','n','MAE','RMSE','R2'])}

### 天花板与预定分层

{table(pd.read_csv(PUB/'ha_prepare_001/target_distribution.csv'))}

{table(strata[strata.model=='BEST_CZ'],['task','stratum','n','MAE','gain_vs_clinical'])}

分层共享全队列训练模型，没有在小亚组内重新调参，也没有选择最有利年龄／时长切点。它们只帮助理解误差来自哪里。A 有 28/57、V 有 18/57 位于字面最大值；CAP/SIR 各 17/57。误差降低的空间并不均匀，不能只报告总体相关系数。

## 条件关联是否受技术因素或非线性影响

{effects_table(followup)}

V_given_A 的技术摘要基线相对临床基线改善约 +0.572 分，5/5 次重复为正，但区间跨零。在技术摘要基线上继续加入 EEG 的增益为约 −0.591 分，5 次重复均不改善。仅控制振幅后也没有保持原来的正向点估计，区间仍宽。因此原线索的脆弱性不能仅解释为“振幅调整把生理信号去掉了”。技术摘要可关联配合度、数据可用性、采集过程和真实个体差异；这里不能从预测结果判定因果解释。

有限高斯核 EEG 在 A 上有小的正向点估计，在 V_given_A 上没有改善。它只覆盖一个明确定义的非线性替代，不等于排除所有非线性，更不构成深度模型一定无效的证据。本轮没有因为原线性结果弱而跳过它。

## 测量可靠性：比较同一批身份

{table(rel_table)}

完整 40 行见 `results/auditory_repair/reliability_matched_001/reliability_matched.csv`。这里的 r 是同一特征在两个半段之间、跨 43 个候选身份的相关，再对特征取中位数；不是单个儿童的可靠性置信区间。奇偶与前后半分开报告，Spearman–Brown 仅作启发性描述。

Hjorth 和空间统计保留较稳定的个体差异；刺激后波形随试次数增加而改善；字面条件差值仍弱。稳定性也可能包含稳定的头部／电极／噪声差异，不能由高 r 直接认定为听觉功能标志物。这个结果支持继续研究可重复的记录表征，以及为什么平均响应与条件差值的误差不同。试次数曲线是回顾性子采样，没有证明缩短实际采集时长具有相同效果。

## 旧 Phase 3：原样复现后修正

{table(pd.read_csv(PUB/'phase3_replay_002/metrics.csv'))}

{effects_table(read(PUB/'phase3_replay_002/effects.json'))}

12 个旧目标×模型预测组合已先复现。MUSS 临床 MAE 由旧 PTA 的约 7.048 变为约 6.693；修正后共享惩罚的高维刺激后模型明显较差，单独惩罚后约 6.705，与临床基线非常接近。这区分了正则化失配和缺乏稳定增量，不能只引用旧共享惩罚模型的坏结果作为 EEG 无效依据。

## 旧 auditory5 D：三种表征及随机方向完整保留

{table(pd.DataFrame(legacy_rows))}

监督表征 C→CVN 的正向点估计约 +0.356，区间跨零；自监督约 +0.136，区间也宽；L0 为负。三种模式各 20 个随机方向控制均已完成，正向个数分别为 1/20、16/20、14/20，说明不能把监督表征中的正向点估计直接解释为功能方向特异性。所有 27 模型绝对误差、随机方向、区间和影响范围见 `results/auditory_repair/legacy_d_002/aggregate.json`。

旧 51 人队列保留两条修正后 PTA 缺失记录，插补仅使用相应训练折；没有借用其他儿童的行或删除不利记录。旧缓存回放三模式各 1,377 行通过，最大绝对差不超过 4.3e−14。

## CI 与混合 MFF：已有内容继续利用，来源仍分开

203 个 canonical MFF 记录中有 20 个字面 CI、18 个 CIHA、3 个 HA、1 个 NH、161 个未明确来源。临床同日设备历史线索加入后，扩展 CI 证据范围为 41 条记录。源标签是证据线索，不是已经确证的诊断或设备开关状态，也不是 41 个独立儿童。

扩展 CI 范围内，已有 primary 的 devt−stad 主窗／晚窗成对记录各 39 条，中位数约 −0.678／−0.345 µV；strict 下各 10 条，约 −0.287／−0.520 µV。它们是记录内描述，不能命名为已确证的 MMN 或康复获益。该范围内有数值临床链接且可测 stad 的记录每终点仅两条，仍给出数值分布，没有因为少而隐去；无法据此训练或验证独立 CI 临床模型。

### 混合来源档案回归

准备版本 `{ci_run}` 已核对原始表头、出生／日期字段、身份冲突和可解释时间来源。保存的完整 10 个 sheet 表头没有可数值提取的植入／开机／验配／使用时长专用列；通用自由文本设备线索不足以补出有定义的时长。71 个候选身份中，66 个可用唯一 DOB 和实际 EEG 时间派生年龄，另 5 个保留缺失。一个 DOB 矛盾身份被暂缓纳入。每个候选身份选最早唯一链接且有 canonical EEG 时间的记录，选择先于终点和特征可用性；这不宣称覆盖所有未链接的更早记录。各终点冲突值保留为无效，不取均值或挑最有利值。来源、范式、技术元数据作为基线；可信且可用的年龄／时长才纳入。完整 preparation 摘要是结果的一部分。

{table(mff_support)}

{table(pd.read_csv(PUB/'mff_archival_001/metrics.csv'))}

{effects_table(mixed)}

混合回归所有目标都有可用年龄；每个终点只有 1 个字面 CI，其他都是未知来源。A/V 的增量分别约 −0.026／−0.048 原分，CAP/SIR 约 −0.020／−0.005。CAP 的真实 EEG 相比打乱对照改善约 +0.036，但仍差于不含 EEG 的基线；不能将“优于打乱”偷换为“具有基线之外的价值”。小的正向内容差异和原始误差都完整保留。

以上是混合 MFF 的档案关联，不是 CI-only，也不是已经调整所有重要临床混杂因素的效用结论。来源及缺失指示有控制不等于解决未知字段；小来源亚组不能承受独立来源外推结论。固定 stad 三值统计包含主窗、晚窗及其差，后者与前两者线性相关，岭惩罚下保留这一预定表达，不把它解释成第三个独立生理维度。

## 小样本任务配对和重复采集也保留描述

原始 F3 是纯音与 bapa 两任务的临床信息互补，F4 是已知基线功能后预测未来功能。既有资格核验发现 9 对同候选同日且都有 stad 测量的任务配对，其中 2 对有一致的档案量表值；HA 有 15 对候选重复采集、涉及 13 个身份；MFF 的多日期档案涉及 2 个身份、8 个身份×终点序列，其中 7 个数值不变、1 个变化。

本轮另对现有配对测量作零拟合描述，完整结果见 `results/auditory_repair/pairs_003/`。9 对的主窗／晚窗跨任务 Pearson r 约为 0.604／0.836；bapa−纯音的差值中位数约为 +0.126／−0.631 µV。HA 的 15 对中 10 对有两次可比固定幅度，后次减前次的中位数约 +0.368 µV；全部 15 对的 vendor 采集间隔中位数约 5.217 月。没有把缺失的 5 对删掉后报告成 15 对完整测量，也没有将这些记录对当作独立人数。

两任务刺激和测量的含义不必相同，相关或差值不是临床互补证据；重复 EEG 的时间顺序也不补出功能量表的真实随访日期。较高的跨任务幅度相关提示共享个体差异值得继续研究，但也可能包括稳定非神经因素。保留这些小规模描述的原因是它们有数据价值；不强行训练临床模型的原因是临床对象尚未成立，并非未达到人为的高效应阈值。

## 对原始科研目的的判断

| 科研目的 | 目前能支持的部分 | 仍不能宣称的部分 |
| --- | --- | --- |
| F1 听觉功能相关表征 | 57 身份的基线、全部固定库、质量和非线性对照；A 上小的 Hjorth／核方法线索 | 稳定且可临床推广的独立 EEG 增量 |
| F2 听觉与言语功能的条件关系 | 已知 A 时预测 V 的小正向关联及控制实验，明确脆弱性 | 两种临床功能已被机制性分离，或模型可替代量表 |
| F3 跨任务临床互补 | 9 对同日任务测量的来源与描述性比较；其中 2 对有一致档案量表 | 用非配对人数充样本、将跨任务相关直接解释为临床互补 |
| F4 基线之外的随访预测 | HA 重复采集及 MFF 多日期档案的支持／变化描述 | 把未确证问卷日期的档案序列称为真实功能随访，或由设备月数构造康复轨迹 |
| CI／跨设备研究 | 明确 CI／CIHA／历史线索／未知来源，CI 波形描述与混合来源回归 | 将未知来源当作 CI、用极少临床交集验证 CI 模型或推断设备获益 |
| 记录表征与测量研究 | 同一身份集合的可靠性曲线、临床天花板、技术摘要与表征增量比较 | 可靠性自动等同临床有效性，或离线子采样等同前瞻缩短采集 |

尚未进行的是新支持／新划分下的整套 encoder 重训、整流程重抽样验证、独立队列复现，以及需确证临床时间／设备／量表版本的临床问题。本轮完成的是以上明确列出的有限实验集合，不是声称穷尽所有模型。后续若扩展，应围绕可重复的测量和条件关联的替代解释提出新的有限假设，不能通过无限增加架构／种子将探索结果伪装为确证结果。停止依据不使用“增益必须很大／区间必须排除零”的门槛。

## 执行、验证与资源

最终核验重算 {verification['metric_rows_checked']} 个模型指标行、{verification['effect_rows_checked']} 个效应行，检查持久化 OOF 完整性、原划分、来源快照与输入哈希，未重新拟合。所有生产、测试、探测、统计和绘图均走 CPU Slurm；GPU 使用为零，也未使用 P100。

本轮累计 {counts['head_call_attempts']:,} 次 head 调用尝试（包含均值头、测试和历史回放，不等于独立模型或独立统计检验）。上限为 {counts['head_call_limit']:,}；这是运行保护，不是科学推进阈值。legacy_D 首次完成后因记账修补而不必要地重跑了一遍，两遍都计费，并将首遍遗漏的 405 次回放计入；首个核测试遗漏的 3 次求解也补计。后续汇总修复均采用零重训方式。

已登记 {counts['scheduler_jobs']} 个 Slurm 任务，按完整申请时限及保守 CPU 数计算的预留上界为 {counts['reserved_core_hours_upper_bound']:.2f} core-hours。调度记账历史不可用，未将该上界说成实际 CPU 消耗。失败／被替代版本均保留，资源和失败原因见 `docs/auditory_repair/JOBS.json`。

原始数据只读。候选身份、姓名、日期、原路径、逐人预测和拟合参数均留在 private 目录；本报告只包含聚合结果。没有自动推送 GitHub。

图表：`figures/ha_primary_controls.pdf`、`ha_mechanism.pdf`、`matched_reliability.pdf`、`legacy_D_repaired.pdf`、`mixed_mff.pdf`，每图另有 PNG。详细机器可读证据见同版本 `results/auditory_repair/{folder.name}/`；若验证需更正，将创建新版本并在 STATUS 中指向最终成功版本。
'''
    (folder/'REPORT.md').write_text(full)
    dump(folder/'ci_preparation_summary.json',ci)


def privacy(private, report_folder):
    changed = 0; checked = 0
    roots = [PRIV, ROOT/'private/results/auditory_repair']
    for base in roots:
        for path in [base,*base.rglob('*')]:
            if path.is_symlink():
                assert any(path.resolve().is_relative_to(r) for r in roots), 'PRIVATE_SYMLINK_ESCAPES'
                continue
            checked += 1
            if stat.S_IMODE(path.stat().st_mode) & 0o077:
                path.chmod(0o700 if path.is_dir() else 0o600);changed += 1
    tokens = set()
    for run in ['ha_prepare_001','phase3_replay_002']:
        f=pd.read_csv(PRIV/run/'cohort.csv').fillna('')
        for col in ['name','participant_id','group','recording','recording_id']:
            if col in f:
                tokens.update(str(v) for v in f[col] if len(str(v))>=6 or re.fullmatch(r'[\u4e00-\u9fff]{2,}',str(v)))
                if col == 'name':
                    tokens.update(m.group() for v in f[col] if (m := re.match(r'[\u4e00-\u9fff]{2,}',str(v))))
    binding=read(PRIV/'mff_archival_001/input_binding.json')
    f=pd.read_csv(ROOT/'private/results/auditory_repair'/binding['run']/'cohort.csv').fillna('')
    for col in ['candidate_group','recording','recording_id','source_id','name','raw_name','normalized_name']:
        if col in f: tokens.update(str(v) for v in f[col] if len(str(v))>=6 or re.fullmatch(r'[\u4e00-\u9fff]{2,}',str(v)))
    text_files=[]
    for base in [PUB,report_folder]:
        text_files.extend(p for p in base.rglob('*') if p.suffix in ['.csv','.json','.md','.txt'])
    hits=[]
    for path in text_files:
        txt=path.read_text()
        if '/projects/EEG-foundation-model/auditory/' in txt: hits.append(dict(path=str(path),kind='raw_dataset_path'))
        if any(token in txt for token in tokens):hits.append(dict(path=str(path),kind='known_identity_token'))
    dump(private/'privacy_scan.json',dict(hits=hits,files_scanned=len(text_files),private_paths_checked=checked,permissions_restricted=changed))
    assert not hits, 'PUBLIC_IDENTITY_TOKEN_FOUND'
    return dict(public_text_files_scanned=len(text_files),known_identity_tokens_checked=len(tokens),private_paths_checked=checked,permissions_restricted=changed,
                limitation='Known-token and raw-path scan, not a proof against all possible re-identification.')


def run(private, public, config, input_run):
    assert os.environ.get('SLURM_JOB_ID')
    from . import pta
    pta_summary=pta.run(private/'pta_revalidated',public/'pta_revalidated')
    pd.testing.assert_frame_equal(pd.read_csv(private/'pta_revalidated/candidate_covariates.csv'),
                                  pd.read_csv(PRIV/'pta_007/candidate_covariates.csv'),check_dtype=False)
    assert pta_summary['old_split_reconstruction_matches_frozen']
    check_splits(read(PRIV/'ha_extended_001/splits.json'),57)
    check_splits(read(PRIV/'phase3_replay_002/folds.json'),50)
    all_checks=[];effect_count=0
    for name, task_col in [('ha_extended_001','task'),('ha_mechanism_001','task'),('phase3_replay_002','target'),('mff_archival_001','task')]:
        checked, packs=check_predictions(name,task_col);all_checks.extend(checked)
        effect_count += check_effects(name,packs)
    assert len(all_checks) == 138 and effect_count == 104
    old=read(PUB/'phase3_replay_002/old_reproduction.json')
    assert len(old)==12 and max(r['max_absolute_difference'] for r in old)<1e-7
    legacy=check_legacy_d();pairs=check_pairs();source=check_sources(private)
    for path in (ROOT/'auditory_repair').glob('*.py'):ast.parse(path.read_text())
    counts=accounting(private,config)
    result=dict(status='PASS',metric_rows_checked=len(all_checks),effect_rows_checked=effect_count,
                legacy_D=legacy,pairs=pairs,source=source,all_declared_model_comparisons_complete=True,
                head_refits_in_verification=0,scientific_early_stopping=False)
    pd.DataFrame(all_checks).to_csv(public/'recomputed_metrics.csv',index=False)
    dump(public/'fit_accounting.json',counts)
    folder=ROOT/'reports/auditory_repair'/private.name
    folder.mkdir(parents=True,exist_ok=False)
    write_report(folder,result,pta_summary,counts,source['mff_preparation'])
    result['privacy']=privacy(private,folder)
    dump(public/'verification.json',result)
    dump(private/'output_hashes.json',{str(p):sha(p) for p in [*public.rglob('*'),*folder.rglob('*')] if p.is_file()})
    return result
