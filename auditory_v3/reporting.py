"""Read-only final aggregation, resource bounds and public artifact checks."""
import json
from pathlib import Path
import re
import subprocess
import numpy as np
import pandas as pd
from .runtime import digest,write_json
from .data import load_support


def _read(path):return json.loads(Path(path).read_text())


def resource_audit(root,private):
    rows=[];scheduler=root/'private/auditory_v3/scheduler_receipts';scheduler.mkdir(exist_ok=True,mode=0o700)
    for start_path in sorted((root/'private/auditory_v3').glob('*/start.json')):
        run=start_path.parent;start=_read(start_path);args=_read(run/'args.json');command=args['command']
        gpu=command=='train-representation' or command=='capability' and args.get('packet')=='R3'
        wall={'inspect':900,'freeze-support':900,'make-plan':300,'test':300,'develop-n2r':1800,'prepare-exposures':1800,'join-r3-capability':300,'run-pca':3600,'run-bags':3600,'train-representation':1800,'select-probes':1800,'evaluate-representations':1800,'finalize':600}.get(command,600 if gpu else 900 if args.get('packet')=='P0' else 1800)
        cpus=4 if gpu else 2;job=str(start['job_id']);saved=scheduler/('job'+job+'.txt')
        if not saved.exists():
            outcome=subprocess.run(['scontrol','show','job',job],capture_output=True,text=True)
            if outcome.returncode==0:saved.write_text(outcome.stdout)
        bound=True;seconds=wall;state='UNKNOWN_RETAIN_RESERVATION'
        if saved.exists():
            text=saved.read_text();match=re.search(r'RunTime=(\S+)',text);state_match=re.search(r'JobState=(\S+)',text)
            if state_match:state=state_match.group(1)
            if match and state in ('COMPLETED','FAILED','CANCELLED','TIMEOUT','OUT_OF_MEMORY'):
                value=match.group(1);days=0
                if '-' in value:day,value=value.split('-');days=int(day)
                h,m,s=map(int,value.split(':'));seconds=days*86400+h*3600+m*60+s;bound=False
        completion=run/'completion.json';failure=run/'failure.json'
        status=_read(completion).get('status') if completion.exists() else 'FAILED' if failure.exists() else 'INCOMPLETE'
        rows.append(dict(run=run.name,job_id=job,command=command,status=status,scheduler_state=state,cpus=cpus,gpus=int(gpu),accounted_seconds=seconds,reservation_upper_bound=bound,cpu_core_hours=seconds*cpus/3600,gpu_hours=seconds*int(gpu)/3600))
    frame=pd.DataFrame(rows);frame.to_csv(private/'job_accounting.csv',index=False)
    events=[json.loads(x) for x in (root/'private/auditory_v3/fit_events.jsonl').read_text().splitlines()]
    counts={kind:sum(e['kind']==kind and e['is_start'] for e in events) for kind in ('head','encoder','synthetic_encoder')}
    recovery=sum(bool(e['details'].get('recovery_of')) for e in events)
    summary=dict(fit_attempts=counts,same_initial_state_recoveries=recovery,cpu_core_hours_upper=float(frame.cpu_core_hours.sum()),gpu_hours_upper=float(frame.gpu_hours.sum()),jobs_with_reservation_fallback=int(frame.reservation_upper_bound.sum()),accounting_scope='completed scheduler runtime where retained, otherwise full requested walltime; includes failures and current finalization reservation',limits=dict(head=3000,encoder=30,synthetic_encoder=3,cpu_core_hours=160,gpu_hours=16))
    summary['within_budget']=counts['head']<=3000 and counts['encoder']<=30 and counts['synthetic_encoder']<=3 and summary['cpu_core_hours_upper']<=160 and summary['gpu_hours_upper']<=16
    return frame,summary


def privacy_audit(root,members,private):
    values=set()
    for column in ('trial_id','bag_id','candidate_id','split_group_id','record_id'):
        values.update(str(v) for v in members[column].dropna().unique() if len(str(v))>=6)
    pattern=re.compile('|'.join(re.escape(s) for s in sorted(values,key=len,reverse=True)))
    violations=[];count=0
    for base in ('results/auditory_v3','reports/auditory_v3','docs/auditory_v3'):
        for path in (root/base).rglob('*'):
            if path.is_file() and path.suffix in ('.json','.csv','.md','.txt'):
                count+=1;body=path.read_text(errors='replace')
                # Explanatory source directory names are allowed in internal docs;
                # exact participant tokens must never appear in shareable outputs.
                match=pattern.search(body)
                if match:violations.append(dict(path=str(path),token=match.group(0)))
    write_json(private/'privacy_violations.json',violations)
    return dict(status='PASS' if not violations else 'FAIL',scanned_text_files=count,exact_known_participant_tokens=len(values),violations=len(violations),clinical_values_read=False,scope='known matched-population identifiers; does not certify every possible free-text identifier')


def finalize(root,private,public,report,config,args):
    members,splits,history,registry,support=load_support(root,args['split_run'])
    runs={'P0':args['p0_run'],'N2R':args['n2r_run'],'R3':args['r3_run']};packets={};rows=[];bindings={}
    for packet,run in runs.items():
        path=root/'private/auditory_v3'/run/'completion.json';result=_read(path)
        capability_path=root/'private/auditory_v3'/result['capability_run']/'completion.json'
        capability=_read(capability_path)
        if capability.get('status')!='PASS' or capability.get('packet')!=packet or capability['config_sha256']!=result['config_sha256'] or capability['split_run']!=result['split_run']:raise ValueError('INVALID_PACKET_CAPABILITY_RECEIPT:'+packet)
        if result.get('execution')!='COMPLETE':raise ValueError('PACKET_EXECUTION_INCOMPLETE:'+packet)
        primary=result['contrasts'][result['primary_contrast']]
        if primary['status']!='PASS':raise ValueError('PRIMARY_NOT_EVALUABLE:'+packet)
        packets[packet]=result;bindings[packet]=dict(run=run,completion_sha256=digest(path),algorithm_hash=result['algorithm_hash'],capability_receipt_sha256=digest(capability_path))
        rows.append(dict(packet=packet,risk_unit=result['risk_unit'],support=result['support'],capability=capability['status'],execution=result['execution'],research=result['research'],contrast=result['primary_contrast'],gain_bits=primary['gain_bits'],ci_low=primary['ci_low'],ci_high=primary['ci_high'],identity_groups=primary['n_groups']))
    table=pd.DataFrame(rows);table.to_csv(public/'primary_results.csv',index=False)
    jobs,resources=resource_audit(root,private)
    jobs.to_csv(public/'execution_jobs.csv',index=False)
    privacy=privacy_audit(root,members,private)
    write_json(public/'resource_audit.json',resources);write_json(public/'privacy_audit.json',privacy)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.ticker import MaxNLocator
    fig,axes=plt.subplots(1,3,figsize=(11,3.6),layout='constrained')
    for axis,row,threshold in zip(axes,rows,[.002,.005,.005]):
        gain=row['gain_bits'];axis.errorbar([gain],[0],xerr=[[gain-row['ci_low']],[row['ci_high']-gain]],fmt='o',color='#24486b',capsize=5)
        axis.axvline(0,color='0.4',lw=1);axis.axvline(threshold,color='#b66b18',ls='--',lw=1)
        titles={'P0':'P0: PC8 − FULL','N2R':'N2R: HQ − HQV','R3':'R3: SUP − MATCH'}
        axis.set_title(titles[row['packet']]);axis.set_yticks([]);axis.set_ylim(-1,1)
        axis.xaxis.set_major_locator(MaxNLocator(nbins=4));axis.tick_params(axis='x',labelsize=9)
        axis.set_xlabel('Paired gain ('+row['risk_unit'].replace('_',' ')+')')
        axis.text(.5,.88,f"{gain:.5f}\n95% CI [{row['ci_low']:.5f}, {row['ci_high']:.5f}]",transform=axis.transAxes,ha='center',fontsize=9)
        axis.spines[['top','left','right']].set_visible(False)
    fig.suptitle('Exploratory fixed-OOF risks; identity-stratified bootstrap (49 groups)',fontsize=11)
    fig.savefig(public/'primary_effects.png',dpi=180);fig.savefig(public/'primary_effects.pdf');plt.close(fig)
    body=['# Auditory v3 executed results','', '三个实验包独立完成；下列结果来自预先冻结的主终点，未用敏感性分析替代主比较。人群为既有49个安全身份组、698个匹配袋、5,584个唯一试次，仍属已探索队列。','', '| 包 | 主增量及95% CI | 单位 | 科学状态 |','|---|---|---|---|']
    for row in rows:body.append(f"| {row['packet']} | {row['gain_bits']:.6f} [{row['ci_low']:.6f}, {row['ci_high']:.6f}] | {row['risk_unit']} | {row['research']} |")
    body+=['','P0比较旧SIM完整表示与PCA8；N2R比较控制历史及二次均值后增加方差；R3比较给定历史的MATCH与SUP完整表示。它们的风险单位和研究问题不同，不能将三个数值混成一个总体效应。图中灰实线为零增量，橙虚线为预设效应阈值；达到阈值仍须满足CI与相应对照条件。', '', 'P0与N2R区间包含零，且上界仍容许各自预设推进阈值附近的正效应；阴性筛查不能证明等价或证明不存在神经信息。完整400维N2R敏感性、pre与历史控制、各外折结果均保留在相应结果表中。', '', 'R3的SUP/MATCH外层区分能力接近机会水平，但CE约2.7，明显差于SIM、历史与随机encoder基线。该现象与过度自信及跨身份泛化失败相容；没有通过额外实验确定原因。主CI跨零，不能以正的点估计宣布目标函数优势。', '', '预刺激窗200ms、刺激后窗400ms，且R3 encoder在post训练，pre仅为诊断。匹配袋由已知类别离线构造；不能宣称在线未知刺激部署。Bootstrap针对固定OOF预测，不包含重训整个流程的变异；无临床量表回归、临床阈值或皮层来源结论。本轮范围为冻结P_MATCH，不能外推到全部CI资料。', '', f"实际头优化尝试：{resources['fit_attempts']['head']}/3000；正式encoder：{resources['fit_attempts']['encoder']}/30；合成encoder初始分配：{resources['fit_attempts']['synthetic_encoder']}/3。资源保守上界：CPU {resources['cpu_core_hours_upper']:.3f}/160 core-hours、GPU {resources['gpu_hours_upper']:.3f}/16 hours。三个首次CUDA反向失败及同初始化恢复均保留，未追加seed或改模型。", '', '本轮没有自动推送GitHub。源码、配置、分折和来源回执均有版本与哈希；逐身份预测、模型权重和原始数据留在private。']
    (report/'V3_RESULTS.md').write_text('\n'.join(body)+'\n')
    result=dict(status='V3_EXECUTION_COMPLETE' if resources['within_budget'] and privacy['status']=='PASS' else 'FINAL_AUDIT_REQUIRES_REVIEW',packet='v3',primaries=rows,resources=resources,privacy=privacy,input_receipts=bindings,automatic_push=False,new_model_fits=0)
    write_json(private/'input_bindings.json',bindings)
    return result
