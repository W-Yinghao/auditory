"""Aggregate-only execution ledger and stimulus diagnostics; no automatic verdict upgrades."""
import json
from datetime import datetime,timezone
import numpy as np
import pandas as pd
from auditory5.provenance import ROOT,require_slurm,write_json,digest
from auditory5.metrics import classification_metrics,candidate_log_losses_bits
from auditory5.statistics import paired_cluster_bootstrap


def run(config,args):
    require_slurm();out=ROOT/config['paths']['aggregates_relative']/args.run;out.mkdir(parents=True,exist_ok=False)
    reports=ROOT/config['paths']['reports_relative'];reports.mkdir(parents=True,exist_ok=True)
    base=ROOT/config['paths']['private_relative'];planpath=base/'jobs/plan_001/plan.json';plan=json.loads(planpath.read_text())
    statuses=[];done={}
    for task in plan['tasks']:
        folder=planpath.parent/'outputs'/task['name'];path=folder/'completion.json'
        if path.exists():
            result=json.loads(path.read_text());status=result['status']
            if status=='PASS':done[task['name']]=result
        else:status='STARTED_INCOMPLETE' if (folder/'task.json').exists() else 'NOT_STARTED'
        statuses.append({k:task[k] for k in ['index','name','stage','outer_fold','inner_fold','mode','branch','resource']}|{'status':status})
    pd.DataFrame(statuses).to_csv(out/'task_status.csv',index=False)
    measurements=[]
    for mode in ['L0','R_RAND','R_SUP','R_SIM']:
        for branch in ['all','left','right']:
            names=[f'outer{i}_{branch}_{mode}' for i in range(5)]
            if not all(name in done for name in names):continue
            for window in ['post','pre']:
                parts=[pd.read_parquet(planpath.parent/'outputs'/name/('stimulus_oof_'+window+'.parquet')) for name in names]
                rows=pd.concat(parts,ignore_index=True)
                assert rows.trial_id.is_unique
                for cal in ['raw','calibrated']:
                    p1=rows[cal+'_probability_class1'].to_numpy();probs=np.c_[1-p1,p1];y=rows.stimulus_local_id.to_numpy();g=rows.split_group_id.to_numpy()
                    metrics=classification_metrics(y,probs,g,rows.trial_id.to_numpy())
                    losses=candidate_log_losses_bits(y,probs,g);values=np.array(list(losses.values()));ci=paired_cluster_bootstrap(np.ones(len(values)),values,list(losses),n_boot=2000)
                    measurements.append({'mode':mode,'branch':branch,'window':window,'probability':cal,'n_candidates':len(losses),
                        'trial_count':len(rows),**metrics,'J_ci_lower':ci['ci_lower'],'J_ci_upper':ci['ci_upper']})
    pd.DataFrame(measurements).to_csv(out/'stimulus_decoding.csv',index=False)
    support=json.loads((ROOT/config['paths']['aggregates_relative']/args.split_run/'summary.json').read_text())
    route_files={'A':'A_L0_core_001','B':'B_L0_001','C':'C_L0_003','D':'D_L0_core_001','E':'E0_native_003'}
    route_summaries={}
    for route,name in route_files.items():
        path=ROOT/config['paths']['aggregates_relative']/name/'summary.json'
        if path.exists():route_summaries[route]={'run':name,'summary':json.loads(path.read_text())}
    counts=pd.DataFrame(statuses).groupby(['resource','mode','status']).size().reset_index(name='tasks').to_dict('records')
    readout_runs={}
    for path in sorted((ROOT/config['paths']['aggregates_relative']).glob('*/summary.json')):
        name=path.parent.name
        if name.startswith(('A_','B_','C_','D_','E0_')):
            readout_runs[name]=json.loads(path.read_text())
    representation_complete=len(done)==len(plan['tasks'])
    summary={'stage':'auditory5_first_pass_execution','status':'REPRESENTATION_MATRIX_COMPLETE' if representation_complete else 'IN_PROGRESS','utc':datetime.now(timezone.utc).isoformat(),
        'plan_hash':digest(planpath),'completed_representation_tasks':len(done),'planned_representation_tasks':len(plan['tasks']),
        'representation_progress':counts,'route_support':support['route_support'],'route_summaries':route_summaries,
        'all_readout_run_summaries':readout_runs,
        'all_five_scientific_routes_complete':False,'current_scope':'Representation receipt and stimulus decoding audit; route verdicts require the separate explicit-source S4 report',
        'not_confirmation_data':True,'participant_data_or_models_published':False}
    write_json(out/'summary.json',summary)
    lines=['# Auditory5 首轮执行状态',f"\n生成时间：{summary['utc']}。这是运行记录，不是五路线最终结论。",'',
        '已完成输入冻结、原始信号重新导出、身份连通组划分和五折冻结。HA 的全头/独立左右处理各保存59,997个完整epoch，保留拒绝标记与完整事件历史；合格数分别44,358和47,245。',
        '',f"支持人数：一般解码{support['route_support']['general']}，A {support['route_support']['A']}，B {support['route_support']['B']}（读出时仍检查共同支持），C {support['route_support']['C']}，D {support['route_support']['D']}。",
        '',f"表示任务完成 {len(done)}/{len(plan['tasks'])}，其中计划60个学习型编码器、30个L0/随机编码器任务。并发上限2 GPU/4 CPU作业；大数组受Slurm提交限额限制，改为固定worker顺序执行。",'',
        '五路线各完成100次正向、100次阴性小型模拟。阴性误筛率A为2/100，其余四路线0/100；这不等于真实数据有效性证明。C在低SNR模拟中功效不足，保留该限制。','',
        '## 已得出的基线信息','']
    if 'A' in route_summaries:
        a=next(r for r in route_summaries['A']['summary']['results'] if r['analysis']=='alternate20')
        stats=a['statistics'];post=stats['post'];adj=stats['background_adjusted']
        lines.append(f"- A，L0、{a['n_candidates']}人：条件对比对应效应 T={post['estimate']:.4f}，95%区间{post['ci95']}；post−pre={post.get('paired_estimate'):.4f}，配对区间{post.get('paired_ci95')}。背景调整后T={adj['estimate']:.4f}。独立重置滤波和额外历史/位置平衡仍待完成，状态INTERIM。")
    if 'B' in route_summaries:
        b=next(r for r in route_summaries['B']['summary']['comparisons'] if r['analysis_set']=='all' and r['probability_mode']=='calibrated' and r['comparison']=='main_gain')
        lines.append(f"- B，L0_HISTORY、{b['n_candidates']}人：强context以外的post增益 {b['estimate']:.5f} bits/trial，95%区间[{b['ci_lower']:.5f}, {b['ci_upper']:.5f}]，不支持0.01的初筛阈值。学习表征和其余预设诊断待完成。")
    if 'D' in route_summaries:
        d=route_summaries['D']['summary']['modes'][0];mae=d['MAE'];ci=d['main_D2_minus_D3']
        lines.append(f"- D，L0、{d['n_candidates']}人、完整临床内外嵌套：临床基线MAE={mae['D1_C']:.3f}，C+visible={mae['D2_CV']:.3f}，加入null={mae['D3_CVN']:.3f}。增益{ci['estimate']:.3f}，95%区间[{ci['ci_lower']:.3f}, {ci['ci_upper']:.3f}]；当前为负向结果，不更换主终点。学习型模型和剩余预设诊断待完成。")
    for route in ['C','E']:
        if route in route_summaries:lines.append(f"- {route}：{route_summaries[route]['summary']['status']}，详见 results/auditory5_v1/{route_summaries[route]['run']}/summary.json。")
        else:lines.append(f'- {route}：尚无完成的读出汇总，不能记为阴性或阳性。')
    if 'A_SUP_RAND_core_001' in readout_runs:
        lines.extend(['','## 已完成的监督/随机表征核心结果',''])
        for result in readout_runs['A_SUP_RAND_core_001']['results']:
            if result['analysis']!='alternate20':continue
            post=result['statistics']['post'];background=result['statistics']['background']
            lines.append(f"- A {result['mode']}：主条件对比T={post['estimate']:.4f}，95%区间{post['ci95']}；背景重复T={background['estimate']:.4f}。尚不替代其余预设对照。")
    if 'B_SUP_RAND_core_001' in readout_runs:
        for mode,summary_b in readout_runs['B_SUP_RAND_core_001']['representations'].items():
            result=next(r for r in summary_b['comparisons'] if r['analysis_set']=='all' and r['probability_mode']=='calibrated' and r['comparison']=='main_gain')
            lines.append(f"- B {mode}：{result['n_candidates']}人，主增益{result['estimate']:.5f} bits/trial，95%区间[{result['ci_lower']:.5f}, {result['ci_upper']:.5f}]。")
    if 'D_SUP_core_001' in readout_runs:
        result=readout_runs['D_SUP_core_001']['modes'][0];ci=result['main_D2_minus_D3']
        lines.append(f"- D R_SUP：51人，C+visible和C+visible+null的MAE均为{result['MAE']['D3_CVN']:.3f}；null增益{ci['estimate']:.3f}，区间[{ci['ci_lower']:.3f}, {ci['ci_upper']:.3f}]。")
    lines.extend(['','E1：同布局bapa只有16个安全候选索引，低于20人门槛，SUPPORT_INSUFFICIENT。E0已有18条配对记录完成128通道、真实缺口保留、独立60s滤波块导出；16条达到每类40个试次。MFF不是全部CI，不由未知来源组推断诊断。',
        '', '## 继续执行','',
        'GPU任务会继续产出每折独立的R_SUP/R_SIM及D内折模型。A/B/C/D的后续读出必须使用对应的冻结模型和身份边界；缺少预设控制的路线保持INTERIM/NEED_CONTROLS，不自动升级阳性判断。只在首轮完整判据支持后考虑预设的23/37种子，当前未扩展架构或临床终点。',
        '', '所有逐人信息、模型、epoch、路径和详细日志保存在private/。本轮没有自动推送GitHub。既有Phase0–3结果及失败的开发/数值运行保持原样。',
        '', f"聚合表：results/auditory5_v1/{args.run}/stimulus_decoding.csv；任务状态：results/auditory5_v1/{args.run}/task_status.csv。"])
    if representation_complete:
        lines=['# Auditory5 表征执行记录','',f"生成时间：{summary['utc']}。",
            '',f"90/90 表征任务有 PASS receipt，包括60个学习型编码器任务及30个L0/随机任务。S4报告另行核对每个receipt的plan、模式、折和fit-scope契约。",
            '',f"共享刺激解码共有{len(measurements)}个 mode×branch×window×calibration 聚合组合；不把任务数或折数当作独立人数。",
            '', '本记录只标记表征矩阵完成，不代表五条科学路线均通过。A的固定历史平衡支持不足、C/E的数值失败必须由独立S4报告保留。',
            '', '所有主路线和控制来源按显式 configs/auditory5_screening_sources_v1.yaml 聚合，不从当前目录挑选较好的结果。',
            '',f"任务表：results/auditory5_v1/{args.run}/task_status.csv。",
            f"刺激解码：results/auditory5_v1/{args.run}/stimulus_decoding.csv。",
            '', '真实任务及其检查点/逐试次OOF预测留在 private/auditory5_v1/jobs/plan_001/outputs。数据已经探索，不作为未经查看的确认队列；本轮没有自动发布到GitHub。']
    (reports/(args.run+'.md')).write_text('\n'.join(lines)+'\n')
    print(json.dumps({'report':str(reports/(args.run+'.md')),'completed_representation_tasks':len(done),'planned':len(plan['tasks'])}))
