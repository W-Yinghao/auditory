"""Aggregate-only report and final contract verification, executed via Slurm."""
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import shutil


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def recover(root, private, public, config, input_run):
    """Recover only the final JSON receipt after fully persisted fits; no refits."""
    import numpy as np
    import pandas as pd
    ns = 'auditory_fseries_archival'
    source = root / 'private' / ns / input_run
    old_public = root / 'results' / ns / input_run
    failure = json.loads((source / 'failure.json').read_text())
    assert failure['type'] == 'TypeError' and 'Object of type int64 is not JSON serializable' in failure['traceback']
    assert "dump(private / 'completion.json', result)" in failure['traceback']
    old_start = json.loads((source / 'start.json').read_text())
    new_start = json.loads((private / 'start.json').read_text())
    assert old_start['config_sha256'] == new_start['config_sha256']
    for rel in ['auditory_fseries/models.py', 'auditory_fseries/data.py']:
        assert old_start['source_hashes'][rel] == new_start['source_hashes'][rel]
    binding = json.loads((source / 'input_binding.json').read_text())
    prepared = root / 'private' / ns / binding['run']
    assert sha(prepared / 'data.npz') == binding['data_sha256']
    with np.load(prepared / 'data.npz', allow_pickle=False) as arrays:
        n = len(arrays['groups'])
    metrics = pd.read_csv(old_public / 'metrics.csv')
    comparisons = pd.read_csv(old_public / 'paired_effects.csv')
    predictions = pd.read_csv(source / 'predictions.csv')
    assert len(metrics) == len(config['tasks']) * len(config['models'])
    assert len(comparisons) == len(config['tasks']) * 6
    assert len(predictions) == n * len(config['tasks']) * len(config['models'])
    assert np.isfinite(predictions[['y', 'prediction']]).all().all()
    statuses = {}
    for task in config['tasks']:
        e = comparisons[comparisons.task == task].set_index('contrast')
        promising = e.loc['primary', 'ci_low'] > 0 and e.loc['quality_adjusted', 'ci_low'] > 0 and e.loc['content_control', 'gain_MAE'] > 0
        statuses[task] = 'EXPLORATORY_CONTROLLED_GAIN_SCREEN' if promising else 'NO_CONTROLLED_ARCHIVAL_GAIN_ESTABLISHED'
        for model in config['models']:
            frame = predictions[(predictions.task == task) & (predictions.model == model)]
            assert len(frame) == frame.group.nunique() == n
            expected = metrics[(metrics.task == task) & (metrics.model == model)].iloc[0]
            assert np.isclose(np.abs(frame.prediction - frame.y).mean(), expected.MAE, atol=1e-10)
            for fold in range(config['validation']['outer_folds']):
                fit_path = source / f'{task}_fold{fold}_{model}_fit.json'
                json.loads(fit_path.read_text())
                shutil.copyfile(fit_path, private / fit_path.name)
    for filename in ['predictions.csv', 'splits.json', 'input_binding.json']:
        shutil.copyfile(source / filename, private / filename)
    for filename in ['metrics.csv', 'paired_effects.csv', 'fold_metrics.csv', 'selections.json']:
        shutil.copyfile(old_public / filename, public / filename)
    events = [json.loads(line) for line in (root / 'private' / ns / 'fit_events.jsonl').read_text().splitlines()]
    assert sum(event['run'] == input_run for event in events) == failure['fits_this_run']
    (private / 'recovery_binding.json').write_text(json.dumps(dict(original_run=input_run,
        original_failure_sha256=sha(source / 'failure.json'), original_source_snapshot=str(source / 'source'),
        preserved_fit_attempts=failure['fits_this_run'], new_fit_attempts=0), indent=2))
    return dict(status='ARCHIVAL_SCREEN_COMPLETE', identity_groups=n, tasks=statuses, metrics=metrics.to_dict('records'),
        comparisons=comparisons.to_dict('records'), summary_only_recovery_of=input_run,
        head_fit_attempts_this_run=0, head_fit_attempts_round=len(events), original_run_fit_attempts=failure['fits_this_run'],
        exploratory=True, strict_clinical_qualification_unchanged=True, clinical_contemporaneity='unknown',
        target_A='mixed_literal_IT_MAIS_MAIS_header', automatic_push=False)


def finalize(root, private, public, report, config, input_run):
    import numpy as np
    import pandas as pd
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    ns = 'auditory_fseries_archival'
    fitted = root / 'private' / ns / input_run
    aggregate = root / 'results' / ns / input_run
    fit_start = json.loads((fitted / 'start.json').read_text())
    fit_receipt = json.loads((fitted / 'completion.json').read_text())
    assert fit_receipt['status'] == 'ARCHIVAL_SCREEN_COMPLETE'
    prepared = root / 'private' / ns / json.loads((fitted / 'input_binding.json').read_text())['run']
    prepared_receipt = json.loads((prepared / 'completion.json').read_text())
    inputs = json.loads((prepared / 'inputs.json').read_text())
    for section in ['paths', 'epoch_packages']:
        for path, info in inputs[section].items():
            assert sha(path) == info['sha256']
    with np.load(prepared / 'data.npz', allow_pickle=False) as a:
        data = {k: a[k] for k in a.files}
    assert sha(prepared / 'data.npz') == prepared_receipt['data_sha256']
    assert sha(prepared / 'data.npz') == json.loads((fitted / 'input_binding.json').read_text())['data_sha256']
    n = len(data['groups'])
    assert n == len(set(data['groups'])) == fit_receipt['identity_groups']
    assert data['Z'].shape == (n, 60) and data['Q'].shape == (n, 4) and data['C'].shape == (n, 4)
    assert all(np.isfinite(data[k]).all() for k in ['Q', 'Z', 'A', 'V'])
    assert np.isfinite(data['C'][:, :2]).all() and not np.isinf(data['C']).any()
    assert all(((data[k] >= 0) & (data[k] <= 100)).all() for k in ['A', 'V'])
    splits = json.loads((fitted / 'splits.json').read_text())
    test_indices = []
    for entry in splits:
        train, test = set(entry['train']), set(entry['test'])
        assert not train & test and train | test == set(range(n))
        assert set(entry['train_groups']).isdisjoint(entry['test_groups'])
        test_indices.extend(entry['test'])
        inner_validation = []
        for inner in entry['inner']:
            a, b = set(inner['train']), set(inner['validation'])
            assert not a & b and a | b == train and not (a | b) & test
            inner_validation.extend(inner['validation'])
        assert sorted(inner_validation) == sorted(train)
    assert sorted(test_indices) == list(range(n))

    predictions = pd.read_csv(fitted / 'predictions.csv')
    metrics = pd.read_csv(aggregate / 'metrics.csv')
    effects = pd.read_csv(aggregate / 'paired_effects.csv')
    assert len(predictions) == n * len(config['tasks']) * len(config['models'])
    assert len(metrics) == len(config['tasks']) * len(config['models'])
    mapping = {str(g): i for i, g in enumerate(data['groups'])}
    checks = 0
    for row in metrics.to_dict('records'):
        frame = predictions[(predictions.task == row['task']) & (predictions.model == row['model'])]
        assert len(frame) == n and frame.group.nunique() == n and set(frame.group) == set(mapping)
        for item in frame.to_dict('records'):
            index = mapping[item['group']]
            target = data['A' if row['task'] == 'A_given_C' else 'V'][index]
            assert item['y'] == target and index in splits[int(item['outer_fold'])]['test']
            assert item['recording'] == data['recordings'][index]
        residual = frame.prediction.to_numpy() - frame.y.to_numpy()
        assert np.isfinite(residual).all()
        assert np.isclose(np.abs(residual).mean(), row['MAE'], atol=1e-10)
        assert np.isclose(np.sqrt(np.mean(residual**2)), row['RMSE'], atol=1e-10)
        checks += 1
    events = (root / 'private' / ns / 'fit_events.jsonl').read_text().splitlines()
    assert len(events) == fit_receipt['head_fit_attempts_round'] <= config['limits']['head_fit_attempts']
    jobs = json.loads((root / 'docs' / ns / 'jobs.json').read_text())
    assert int(os.environ['SLURM_JOB_ID']) in [j['job_id'] for j in jobs], 'RESOURCE_LEDGER_MUST_INCLUDE_CURRENT_JOB'
    reserved = sum(j['cpus'] * j['time_limit_minutes'] / 60 for j in jobs)
    assert reserved <= config['limits']['cpu_reserved_core_hours'] and all(j['gpus'] == 0 for j in jobs)
    accounting = subprocess.run(['sacct', '-j', ','.join(str(j['job_id']) for j in jobs), '-X', '-n', '-P',
        '--format=JobIDRaw,State,AllocCPUS,ElapsedRaw,TimelimitRaw,ReqMem,AllocTRES'], capture_output=True, text=True)
    (private / 'slurm_accounting.txt').write_text(accounting.stdout)
    (private / 'slurm_accounting_stderr.txt').write_text(accounting.stderr)
    accounting_status = 'AVAILABLE' if accounting.returncode == 0 and accounting.stdout.strip() else 'UNAVAILABLE'

    cohort_summary = dict(identity_groups=n, C_missing_per_column=np.isnan(data['C']).sum(axis=0).tolist(),
        A_min_median_max=[float(x) for x in np.quantile(data['A'], [0, .5, 1])],
        V_min_median_max=[float(x) for x in np.quantile(data['V'], [0, .5, 1])])
    (public / 'cohort_summary.json').write_text(json.dumps(cohort_summary, indent=2))
    task_titles = {'A_given_C': 'Auditory archive score | C', 'V_given_C': 'MUSS archive score | C',
                   'V_given_C_and_A': 'MUSS archive score | C + auditory score'}
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.2), sharey=True)
    colors = ['#245b80', '#729aa5', '#b08757']
    for ax, task in zip(axes, config['tasks']):
        rows = effects[effects.task == task].set_index('contrast')
        for i, label in enumerate(['primary', 'quality_adjusted', 'content_control']):
            row = rows.loc[label]
            ax.plot([row.ci_low, row.ci_high], [i, i], color=colors[i], linewidth=2)
            ax.scatter(row.gain_MAE, i, color=colors[i], s=40, zorder=3)
        ax.axvline(0, color='#777777', linewidth=1, linestyle='--')
        ax.set_title(task_titles[task], fontsize=10)
        ax.set_xlabel('MAE gain in archive score points\n(positive favors real EEG)', fontsize=9)
        ax.set_yticks([0, 1, 2], ['Clinical + EEG', 'After quality adjustment', 'Versus shuffled EEG'])
        ax.grid(axis='x', alpha=.15)
    axes[0].invert_yaxis()
    fig.suptitle(f'Exploratory HA archival screen, {n} candidate identity groups', fontsize=12)
    fig.text(.5, .005, '95% intervals resample fixed out-of-fold identity errors within folds; no pipeline refitting.', ha='center', fontsize=8)
    fig.tight_layout(rect=(0, .06, 1, .94))
    for extension in ['png', 'pdf']:
        fig.savefig(report / ('incremental_screen.' + extension), dpi=180, bbox_inches='tight')
    plt.close(fig)

    lines = ['# HA 档案功能分数：固定 EEG 表征探索检验 v1', '',
        f'本轮完成 {n} 个候选身份组、每组最早一条记录的 5 外折×3 内折检验。3 个任务、8 种模型均有完整 OOF 预测。', '',
        '**主要解释范围：预测现存 HA 档案数值。严格 F1–F4 临床资格结论不变。** 量表时点、逐行 IT-MAIS/MAIS 版本及设备采集状态仍有限制；这不是独立外部验证、同期功能解码、未来康复预测或 CI 结论。', '',
        f"来源流程：{prepared_receipt['flow']['linked_rows']} 条 BDF 来源 → {prepared_receipt['flow']['earliest_ha_rows']} 条合格最早 HA 索引 → {prepared_receipt['flow']['metadata_eligible_rows']} 条唯一档案链接 → {n} 条满足 epoch 数量要求的记录。临床四列缺失数依次为 {cohort_summary['C_missing_per_column']}。", '',
        '| 任务 | 均值 MAE | 临床最佳 MAE | 临床＋EEG MAE | EEG 增量（95% 区间） | 质量调整增量（95% 区间） |',
        '|---|---:|---:|---:|---|---|']
    for task in config['tasks']:
        m = metrics[metrics.task == task].set_index('model')
        e = effects[effects.task == task].set_index('contrast')
        def interval(label):
            r = e.loc[label]
            return f'{r.gain_MAE:.3f} [{r.ci_low:.3f}, {r.ci_high:.3f}]'
        lines.append(f"| {task} | {m.loc['MEAN', 'MAE']:.3f} | {m.loc['C_BEST', 'MAE']:.3f} | {m.loc['C_Z', 'MAE']:.3f} | {interval('primary')} | {interval('quality_adjusted')} |")
    lines += ['', '增量为基线 MAE 减 EEG 模型 MAE，正值表示误差下降。A_given_C 与 V_given_C_and_A 是预先固定的两项主要问题；V_given_C 为并行探索。V_given_C_and_A 明确使用真实听觉档案数值作为已知输入。', '',
        '## 筛查结论', '']
    for task, status in fit_receipt['tasks'].items():
        lines.append(f'- {task}: `{status}`。')
    lines += ['', '仅当主增量、质量调整增量的区间下界都为正，且真实 EEG 优于固定种子的训练内打乱对照，才通过本轮推进门槛。一个打乱种子不是置换检验 p 值。失败于此门槛不等于证明 EEG 与功能无关，也不能通过更换目标或增加架构改写本轮结果。', '',
        '## 方法与边界', '',
        '人群选择沿用全量来源的最早身份索引，先于结果和质量筛选，不以更晚记录补位。使用两列目标、年龄和设备月数完整者，PTA 允许训练内插补。身份仍为候选身份；姓名＋标签日期档案链接不证明同期评估。', '',
        '固定表征是主 QC 通过的两种事件码 epoch：20 通道、250 Hz、−0.2 至 +0.5 秒，按时间均匀取至多 256 个。每通道的 log 方差、log Hjorth mobility 与 log complexity 取记录内中位数，共 60 维。没有事件语义、ERP 峰或静息态推断。', '',
        '临床模型在内层选择线性/二次岭；组合模型允许完全不用 EEG，临床与 EEG 分别正则。质量摘要为有效 epoch 数、拒绝率、最大头皮峰峰值和记录时长。它们可能同时含生理信息，不能把质量调整解释成完全剔除伪迹。', '',
        '全部插补、标准化、二次展开及超参数选择仅在相应训练集内完成。区间为 2,000 次固定 OOF 误差的分折内身份 bootstrap，不反映重训/换分折变异，也不是多重比较校正后的确认性结果。此前探索过该队列，本轮结果不属于未经触碰的验证。', '',
        '## 验证与资源', '',
        f'{checks} 组任务×模型的完整 OOF 指标已从私有预测独立重算；身份内外折无交叉，数据哈希匹配。', '',
        f"本轮累计岭拟合尝试 {len(events)} / {config['limits']['head_fit_attempts']}（包含合成测试及失败尝试）；全部通过 Slurm，申请时限累计上界 {reserved:.3f} CPU core·h，0 GPU。逐次作业见 jobs.json；sacct 记账查询状态为 {accounting_status}，查询输出/错误留在 private。若记账服务不可用，不能将申请上界当成实际使用量。", '',
        '逐人数据、标签、分折、预测与系数仅保存在 private。此报告不自动发布 GitHub。']
    if (root / 'results' / ns / 'legacy_lineage_001/mapping_summary.json').exists():
        lines += ['', '## 历史 PTA 对应关系更正', '',
            '本轮原表复核发现旧 phase3_ha_covariates_004 的顺序编号与原表实际行号不一致：57 条旧候选记录中，55 条较好耳裸耳 PTA、47 条助听 PTA 与按原行号读取的值不同。本轮已经使用正确原行号，并逐行核对既有临床审计的姓名、年龄、设备月数及两个目标。', '',
            '旧 PTA 调整结果及其下游使用需要单独更正，不能继续作为可靠的独立支持证据。本轮没有覆盖或替换任何旧结果；也没有因 v3 未直接读取此表就宣称它完全不受间接影响。详见 docs/auditory_fseries_archival/LEGACY_PTA_LINEAGE_AMENDMENT.md。']
    (report / 'REPORT.md').write_text('\n'.join(lines) + '\n')

    # Check this round's entire private tree, including failures and Slurm logs.
    violations = []
    for path in [root / 'private' / ns, *(root / 'private' / ns).rglob('*')]:
        # pytest creates an internal `...current` link to its synthetic fixture
        # directory. Audit the resolved target and its private containment.
        if (path.is_symlink() and not path.resolve().is_relative_to(root / 'private' / ns)) or stat.S_IMODE(path.stat().st_mode) & 0o077:
            violations.append(str(path))
    if violations:
        (private / 'permission_failures.json').write_text(json.dumps(violations))
        raise ValueError('PRIVATE_PERMISSION_AUDIT_FAILED')
    cohort = pd.read_csv(prepared / 'cohort.csv', dtype=str).fillna('')
    tokens = set(map(str, data['groups'])) | set(map(str, data['recordings']))
    for col in ['worksheet_name', 'vendor_exam_time']:
        if col in cohort:
            tokens.update(value for value in cohort[col] if len(value) >= 2)
    published = [p for base in [root / 'results' / ns, root / 'reports' / ns]
                 for p in base.rglob('*') if p.is_file() and p.suffix in ['.json', '.csv', '.md', '.txt']]
    for path in published:
        content = path.read_text()
        if any(token in content for token in tokens if token) or '/projects/EEG-foundation-model/auditory' in content:
            raise ValueError('PUBLIC_CONTENT_AUDIT_FAILED')
    hashes = {str(p.relative_to(root)): sha(p) for p in published}
    (private / 'verified_public_sha256.json').write_text(json.dumps(hashes, indent=2))
    return dict(status='PASS', verification='complete_OOF_identity_isolation_input_binding_budget_and_privacy',
        identity_groups=n, verified_task_model_combinations=checks, head_fit_attempts_round=len(events),
        cpu_reserved_core_hours_upper_bound=reserved, gpu_hours=0, tasks=fit_receipt['tasks'],
        slurm_accounting_status=accounting_status,
        strict_clinical_qualification_unchanged=True, automatic_push=False)
