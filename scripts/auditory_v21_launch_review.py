"""Aggregate the completed launch runs, without any model fitting."""
import hashlib
import json
import os
from pathlib import Path
import shutil

import numpy as np
import pandas as pd


ROOT=Path('/home/infres/yinwang/EEG_auditory')


def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as handle:
        for part in iter(lambda:handle.read(1024*1024),b''):h.update(part)
    return h.hexdigest()


def write(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n')


def main():
    if not os.environ.get('SLURM_JOB_ID'):raise RuntimeError('SLURM_REQUIRED')
    os.umask(0o077)
    run='launch_review_001'
    private,public,report=[ROOT/base/'auditory_v21'/run for base in ('private','results','reports')]
    if any(p.exists() for p in (private,public,report)):raise FileExistsError('IMMUTABLE_RUN_EXISTS')
    for p in (private,public,report):p.mkdir(parents=True,mode=0o700)
    shutil.copyfile(__file__,private/'analysis_source.py')
    hashes={}
    def read_json(path):
        hashes[str(path.relative_to(ROOT))]=digest(path)
        return json.loads(path.read_text())
    def read_csv(path):
        hashes[str(path.relative_to(ROOT))]=digest(path)
        return pd.read_csv(path)
    stage=read_json(ROOT/'private/auditory_v21/stage0_001/completion.json')
    dev=read_json(ROOT/'private/auditory_v21/development_001/completion.json')
    tests=read_json(ROOT/'private/auditory_v21/tests_004/completion.json')
    if stage['status']!='STAGE0_RECORDED' or tests['status']!='PASS':raise ValueError('UPSTREAM_NOT_COMPLETE')
    stage_dir=ROOT/'results/auditory_v21/stage0_001'
    a2=read_csv(stage_dir/'a2_secondary_comparisons.csv')
    fold=read_csv(stage_dir/'a2_secondary_fold_statistics.csv')
    original=read_csv(ROOT/'results/auditory_next_v2/A2_core_001/repeatability_aggregate.csv')
    reproduction=[]
    for (mode,endpoint),rows in fold.groupby(['mode','endpoint']):
        if '_minus_' in mode:continue
        rows=rows.drop_duplicates('fold')
        actual=np.average(rows.statistic,weights=rows.n_candidates)
        frozen=original[(original['mode']==mode)&(original.endpoint==endpoint)&(original.metric=='cosine')]
        if len(frozen)!=1 or not np.isclose(actual,float(frozen.estimate.iloc[0]),rtol=0,atol=1e-12):
            raise ValueError('FROZEN_A2_POINT_ESTIMATE_NOT_REPRODUCED')
        reproduction.append(dict(mode=mode,endpoint=endpoint,status='PASS',absolute_error=float(abs(actual-frozen.estimate.iloc[0]))))
    write(public/'a2_reproduction.json',reproduction)
    development_dir=ROOT/'results/auditory_v21/development_001'
    effects=read_csv(development_dir/'development_effects.csv')
    execution=read_json(development_dir/'development_execution.json')
    rows=[]
    for keys,data in effects.groupby(['packet','world','dimension','first','second'],sort=True):
        rows.append(dict(zip(['packet','world','dimension','first','second'],keys),
            development_worlds=len(data),mean_gain=float(data.estimate.mean()),
            min_gain=float(data.estimate.min()),max_gain=float(data.estimate.max()),
            positive_estimates=int((data.estimate>0).sum()),
            positive_fixed_prediction_intervals=int((data.ci_lower>0).sum()),
            independent_capability_pass=False))
    aggregate=pd.DataFrame(rows);aggregate.to_csv(public/'development_descriptive_summary.csv',index=False)
    optimizer=[]
    for number,item in enumerate(execution):
        if item['status']=='FAILED':continue
        receipts=read_json(ROOT/f'private/auditory_v21/development_001/world_{number:03d}/fit_receipts.json')
        optimizer.extend(receipts)
    optimization=dict(head_receipts=len(optimizer),optimizer_success=sum(r['optimizer_success'] for r in optimizer),
        finite_budget_endpoints_without_optimizer_success=sum(not r['optimizer_success'] for r in optimizer),
        max_gradient_norm=max((r['gradient_norm'] for r in optimizer),default=None))
    write(public/'optimization_diagnostics.json',optimization)
    write(public/'BASELINE_PRESERVATION_TESTS.json',dict(status='PASS',source='tests_004',
        tests=tests['tests'],test_receipt_sha256=digest(ROOT/'private/auditory_v21/tests_004/completion.json'),
        scope='exact calibrated baseline candidates; test label/feature invariance; disjoint encoder scope; source/budget gates',
        formal_capability_status='NOT_EVALUATED'))
    lines=['# v2.1 首批实验结果','',
        '本报告汇总新版本的零拟合审计和合成开发，不是独立能力评估，也未启动新的真实 EEG 读出。',
        '',f"26项模块测试通过。合成开发完成{dev['worlds_complete']}/36世界，失败{dev['worlds_failed']}；"
        f"头调用{dev['fit_counts']['head']['completed']}/244。优化诊断成功{optimization['optimizer_success']}个，"
        f"其余有限预算终点{optimization['finite_budget_endpoints_without_optimizer_success']}个；二者均不自动代表识别能力。",'',
        '## A2：既有49组的事后配对审阅','',
        '原点估计已由保存的折内矩阵复现。下列为同身份、同折配对差值，区间来自固定矩阵的身份bootstrap，无重拟合。原R_SIM主终点保留。','',
        '| 比较 | 终点 | 差值 | 95%区间 |','|---|---|---:|---|']
    for row in a2.itertuples():
        lines.append(f'| {row.comparison} | {row.endpoint} | {row.estimate:.6f} | [{row.ci_lower:.6f}, {row.ci_upper:.6f}] |')
    lines+=['','四个差值区间均跨零，尚不能主张监督表示优于SIM或随机表示。单个表示自身显著不等于表示间差异显著。']
    n2=stage['n2'];history=n2['member_history_audit'];support=n2['common_history_support']
    lines+=['','## N2：元数据和成员关系','',
        f"保存袋数{history['n_bags_denominator']}，成员行数{history['n_member_rows_denominator']}。"
        f"直接前驱也是同袋成员的行数{history['n_members_direct_previous_member']}；"
        f"任意更早祖先包含同袋成员的行数{history['n_members_any_earlier_member']}。这些关系不能自动称为标签泄漏。",
        f"精确历史共同单元存在于{support['candidate_half_design_exact_common_numerator']}/"
        f"{support['candidate_half_design_eligible_denominator']}个满足旧配额的身份×half；"
        f"旧成员同时满足等类别袋数与精确历史配额的计数为{support['candidate_half_construction_feasible_numerator']}。"
        '后者不证明重新构造平衡袋不可能；新的可比装袋设计仍待验证。',
        '', '## 合成开发：不能用作正式通过率','',
        '每行仅两个开发世界，类别率分别0.15/0.20，种子未用于独立评估。仅汇总首要方向；双向增益及噪声/复制控制保存在完整CSV。',
        '', '| 路线 | 机制 | 维数 | 平均增益 bits/trial | 最小值 | 最大值 |', '|---|---|---:|---:|---:|---:|']
    for row in aggregate.itertuples():
        if (row.packet=='N1' and (row.first,row.second)==('HP','HPB')) or (row.packet=='N3' and (row.first,row.second)==('H','HP')):
            lines.append(f'| {row.packet} | {row.world} | {row.dimension} | {row.mean_gain:.6f} | {row.min_gain:.6f} | {row.max_gain:.6f} |')
    lines+=['','下一阶段需核对真实H维数、编码器训练与校准身份范围，冻结独立评估种子、逐情景门槛及精确拟合目录。对应能力通过之前，真实分支保持关闭。',
        '全部任务通过Slurm。新正式编码器为0；没有GPU任务，也没有使用P100。', '']
    (report/'LAUNCH_RESULTS.md').write_text('\n'.join(lines))
    write(private/'input_hashes.json',hashes)
    summary=dict(status='LAUNCH_REVIEW_COMPLETE',new_head_fits=0,new_encoder_fits=0,
        job_id=os.environ['SLURM_JOB_ID'],script_hash=digest(private/'analysis_source.py'),
        source_runs=['tests_004','stage0_001','development_001'],independent_capability_status='NOT_EVALUATED',real_gate_open=False)
    write(private/'completion.json',summary);write(public/'summary.json',summary)
    print(json.dumps(summary),flush=True)


if __name__=='__main__':main()
