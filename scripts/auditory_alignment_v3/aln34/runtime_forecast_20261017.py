"""Operational scenario estimate, not a statistical confidence interval."""
import json
import os
from pathlib import Path
from datetime import datetime

assert os.environ.get('SLURM_JOB_ID')
BASE = Path('private/auditory_alignment_v3/aln34')
a = json.loads((BASE/'runtime_audit_20261017.json').read_text())
H = a['historical_sources']['groups']
result = {'runtime_snapshot':a['time'], 'job':os.environ['SLURM_JOB_ID'],
          'created':datetime.now().astimezone().isoformat(), 'lanes':{}}

def historical(ds, arch):
    return H[f'{ds}|{arch}|||']

def baseline(ds, arch):
    return historical(ds,arch)['times']['mean_s']

def put(lane, values, note, factors=(0.75,1.5)):
    hours = sum(values)/3600
    result['lanes'][lane] = {'central_gpu_h':round(hours,2),
        'scenario_gpu_h':[round(hours*factors[0],2),round(hours*factors[1],2)], 'basis':note}

for lane in ('learning_budget_v2','data_inner_v1'):
    put(lane,[g['remaining']*g['times']['mean_s'] for g in a['lanes'][lane]['groups'].values()],
        'Production mean per dataset/architecture/data fraction; few cells so broad hardware/fold range.')

values=[]
for k,g in a['lanes']['breadth_budget_v1']['groups'].items():
    ds,arch,*_=k.split('|'); h=historical(ds,arch)
    train=h['train']['mean_s']; overhead=h['times']['mean_s']-train
    values.append(g['remaining']*(2*train+4*overhead))
put('breadth_budget_v1',values,'Same-dataset historical training x2 plus nontraining overhead x4 for trajectory evaluations.')

values=[]
for k,g in a['lanes']['breadth_inner_v1']['groups'].items():
    ds,arch,kind,axis,frac=k.split('|')
    reference=a['lanes']['data_inner_v1']['groups'][f'dtu|{arch}|{kind}|{axis}|{frac}']['times']['mean_s']
    estimate=g['times'].get('mean_s',reference*baseline(ds,arch)/baseline('dtu',arch))
    values.append(g['remaining']*estimate)
put('breadth_inner_v1',values,'DTU matched architecture/axis/fraction scaled by historical cohort runtime; production where available.')

# D probes evaluate a reduced grid; use completed full CB/local work and the
# REVE-to-CB probe ratio, rather than treating a short probe as production.
for lane,scale in (('adaptation_policy_v1',1.0),('breadth_policy_v1',1.0)):
    values=[]
    plan=json.loads((BASE/lane/'plan.json').read_text())
    for row in plan['rows']:
        p=BASE/lane/'units'/f"{row['id']}.json"
        if p.exists() and json.loads(p.read_text()).get('status')=='complete':continue
        arch=row['inner_source']['spec']['architecture']
        per={'lag_local_tokens':301.,'cbramod':1597.,'reve':1597.*316.1/93.0}[arch]
        if lane=='breadth_policy_v1':
            per*= {'lag_local_tokens':70./58.4,'cbramod':90.2/93.,'reve':185.9/316.1}[arch]
        values.append(per)
    put(lane,values,'Full-grid CB/local production; REVE and FAU inferred with short-probe runtime ratios.',(0.65,1.8))

for lane in ('strong_fusion_v1','breadth_fusion_v1'):
    put(lane,[g['remaining']*1150.7 for g in a['lanes'][lane]['groups'].values()],
        'First two DTU full fusion bundles; cohort portability uncertain.',(0.7,1.6))

for lane in ('episode_training_v1','breadth_episode_v1','private_episode_v1','cs_episode_v1'):
    values=[]
    for k,g in a['lanes'][lane]['groups'].items():
        ds,arch,*_=k.split('|')
        if lane=='private_episode_v1':
            per={'lag_local_tokens':350.,'cbramod':1293.1,'reve':4000.}[arch]
        elif lane=='cs_episode_v1':
            per=400. if ds=='dtu' else 1000.
        else:
            per={'lag_local_tokens':375.,'cbramod':862.2,'reve':862.2*786.1/178.2}[arch]
            if ds=='fau':per*={'lag_local_tokens':2.,'cbramod':242.5/178.2,'reve':556.2/786.1}[arch]
        per=g['times'].get('mean_s',per)
        values.append(g['remaining']*per)
    put(lane,values,'Full returned bundles where available; architecture probe ratios and explicit fallback for unobserved full bundles.',(0.6,1.8))

for lane in ('cb_auditory_v1','private_cb_factorial_v1'):
    values=[]
    for k,g in a['lanes'][lane]['groups'].items():
        ds,arch,kind,*_=k.split('|')
        per=787.6 if kind=='donor' else baseline(ds,arch)
        values.append(g['remaining']*per)
    put(lane,values,'Completed CB donor and historical same-architecture target training runtimes.')

for lane in ('content_time_v1','private_current_time_v1','attention_transfer_v1','prior_private_loo_v1','prior_science_v1'):
    values=[]
    for k,g in a['lanes'][lane]['groups'].items():
        ds,arch,*_=k.split('|')
        if lane=='attention_transfer_v1':per={'lag_local_tokens':53.,'cbramod':177.5,'reve':834.8}[arch]
        elif lane=='prior_private_loo_v1':per=22.
        elif lane=='prior_science_v1':per=60. if ds=='private_bdf' else 30.
        else:per={'lag_local_tokens':45.,'cbramod':48.,'reve':200.,'?':40.}[arch]
        values.append(g['remaining']*g['times'].get('mean_s',per))
    put(lane,values,'Full frozen evaluation where available; probe-derived approximation otherwise.',(0.7,2.0))

put('true_full',[g['remaining']*g['times']['mean_s'] for g in a['true_full']['groups'].values()],
    'Historical mean per dataset and architecture for actual remaining cells.',(0.85,1.5))
values=[]
for k,g in a['prior']['groups'].items():
    ds,arch,stage,*_=k.split('|')
    per=g['times'].get('mean_s')
    if per is None:
        per=({'fau':250.,'dtu':137.3,'federici':220.,'private_bdf':330.}[ds]
             if stage=='target' else 60.)
    values.append(g['remaining']*per)
put('public_prior',values,'Completed donor/bridge/target means; other targets use cohort historical scales; zero-shot provision60s. Mixed donor member counts are conservatively pooled.',(0.65,1.8))

result['total_gpu_h']=round(sum(v['central_gpu_h'] for v in result['lanes'].values()),1)
result['scenario_gpu_h']=[round(sum(v['scenario_gpu_h'][i] for v in result['lanes'].values()),1) for i in (0,1)]
result['central_ideal_days_at_10_gpus']=round(result['total_gpu_h']/240,2)
result['interpretation']='Current registered work only. Scenarios are judgmental, not confidence intervals. Running partial units count as full remaining; no guaranteed GPU availability. Launch/IO/dependency delays and future scientific expansions are outside the GPU-hour sum.'
(BASE/'runtime_forecast_20261017.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
