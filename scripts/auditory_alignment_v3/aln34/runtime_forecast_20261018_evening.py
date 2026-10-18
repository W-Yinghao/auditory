"""Operational runtime scenarios from saved timings; Slurm CPU only, no fitting."""
import json
import os
from collections import defaultdict
from datetime import datetime
from pathlib import Path

assert os.environ.get('SLURM_JOB_ID')
BASE = Path('private/auditory_alignment_v3/aln34')
read = lambda p: json.loads(p.read_text())
a = read(BASE/'runtime_audit_20261018_evening.json')
old = read(BASE/'runtime_audit_20261017.json')
previous = read(BASE/'runtime_forecast_20261017.json')
H = a['historical_sources']['groups']
aliases = {'private_current_time_v2':'private_current_time_v1',
           'private_episode_v2':'private_episode_v1'}


def historical(ds, arch):
    key = f'{ds}|{arch}|||'
    return H.get(key, old['historical_sources']['groups'].get(key, {}))


def base_time(ds, arch):
    return historical(ds, arch).get('times', {}).get('mean_s',
        {'lag_local_tokens':150., 'cbramod':1200., 'reve':2500.}.get(arch, 1200.))


def rate(lane, key, group):
    t = group['times']
    if t['n']:
        return t['mean_s'], 'current same-workload full production', t['n']
    prior = old['lanes'].get(aliases.get(lane, lane), {}).get('groups', {}).get(key, {})
    if prior.get('times', {}).get('n'):
        return prior['times']['mean_s'], 'previous full production of same workload', prior['times']['n']
    ds, arch, kind, axis, fraction = key.split('|')
    if lane == 'breadth_inner_v1':
        ref = a['lanes']['data_inner_v1']['groups'].get(f'dtu|{arch}|{kind}|{axis}|{fraction}', {})
        if ref.get('times', {}).get('n'):
            return ref['times']['mean_s']*base_time(ds,arch)/base_time('dtu',arch), 'DTU workload scaled by historical cohort runtime', 0
    if lane in ('learning_budget_v2','breadth_budget_v1'):
        h = historical(ds,arch); total = base_time(ds,arch)
        train = h.get('train',{}).get('mean_s',total*0.8)
        return 2*train+4*max(0,total-train), 'historical train x2 plus evaluation overhead x4', 0
    if lane in ('adaptation_policy_v1','breadth_policy_v1'):
        per = {'lag_local_tokens':301.,'cbramod':1597.,'reve':1597.*316.1/93.}[arch]
        if lane.startswith('breadth'):
            per *= {'lag_local_tokens':70./58.4,'cbramod':90.2/93.,'reve':185.9/316.1}[arch]
        return per, 'full local/CB reference and declared architecture/cohort probe ratio', 0
    if lane in ('strong_fusion_v1','breadth_fusion_v1'):
        return 1150.7, 'historical full fusion bundle', 0
    if lane in ('episode_training_v1','breadth_episode_v1','private_episode_v2','cs_episode_v1'):
        if lane == 'private_episode_v2':
            per = {'lag_local_tokens':350.,'cbramod':1293.1,'reve':4000.}[arch]
        elif lane == 'cs_episode_v1':
            per = 400. if ds == 'dtu' else 1000.
        else:
            per = {'lag_local_tokens':375.,'cbramod':862.2,'reve':862.2*786.1/178.2}[arch]
            if ds == 'fau':
                per *= {'lag_local_tokens':2.,'cbramod':242.5/178.2,'reve':556.2/786.1}[arch]
        return per, 'full reference with explicit architecture/cohort fallback', 0
    if lane in ('cb_auditory_v1','private_cb_factorial_v1'):
        return (787.6 if kind == 'donor' else base_time(ds,arch)), 'CB donor/historical target reference', 0
    if lane == 'attention_transfer_v1':
        return {'lag_local_tokens':53.,'cbramod':177.5,'reve':834.8}[arch], 'architecture-specific frozen evaluation reference', 0
    if lane == 'prior_private_loo_v1':
        return 32.6, 'completed prior LOO median', 0
    if lane == 'prior_science_v1':
        return (60. if ds == 'private_bdf' else 30.), 'cohort-specific prior evaluation reference', 0
    if lane in ('content_time_v1','private_current_time_v2'):
        return {'lag_local_tokens':45.,'cbramod':48.,'reve':200.,'?':40.}[arch], 'frozen evaluation reference', 0
    raise ValueError(('unresolved runtime group', lane, key))


groups=[]; lanes=defaultdict(lambda: {'planned':0,'complete':0,'remaining':0,'gpu_hours':0.,'estimated_only_gpu_hours':0.})
for dirname, inventory in a['lanes'].items():
    for key,g in inventory['groups'].items():
        lane = dirname
        if dirname in ('data_inner_v1','breadth_inner_v1'):
            lane = ('breadth_' if dirname.startswith('breadth') else '') + ('inner' if key.split('|')[3]=='inner_person' else 'curves')
        v=lanes[lane]
        for k in ('complete','remaining'):v[k]+=g[k]
        v['planned']+=g['total']
        if not g['remaining']:continue
        seconds,basis,n=rate(dirname,key,g)
        hours=g['remaining']*seconds/3600
        v['gpu_hours']+=hours
        if n==0:v['estimated_only_gpu_hours']+=hours
        groups.append({'lane':lane,'group':key,'remaining':g['remaining'],'seconds_per_unit':round(seconds,1),
                       'gpu_hours':round(hours,3),'production_n':n,'basis':basis})

# Current fleet gives most lanes one worker, so total/10 is only a lower bound.
# Scenarios deliberately do not pretend to predict cluster queue availability.
fleet=read(BASE/'fleet_status.json')
short={'content_time_v1','private_current_time_v2','prior_private_loo_v1','prior_science_v1'}
for lane,v in lanes.items():
    v['gpu_hours']=round(v['gpu_hours'],2)
    v['estimated_only_gpu_hours']=round(v['estimated_only_gpu_hours'],2)
    v['one_worker_compute_days']=round(v['gpu_hours']/24,2)
    v['scenario_gpu_hours']=[round(v['gpu_hours']*0.7,2),round(v['gpu_hours']*1.6,2)]
    # A nominal 2 minutes/rotation covers launch + coordinator polling, not queue waits.
    batch=8 if lane in short else (1 if lane=='cb_auditory_v1' else 2)
    v['nominal_launch_overhead_hours']=round(v['remaining']/batch*120/3600,2)

total=sum(v['gpu_hours'] for v in lanes.values())
longest=max(v['gpu_hours'] for v in lanes.values())
result={'created':datetime.now().astimezone().isoformat(),'job':os.environ['SLURM_JOB_ID'],
        'audit_snapshot':a['time'],'fleet_snapshot':fleet['time'],'lanes':dict(lanes),'groups':groups,
        'remaining_units':sum(v['remaining'] for v in lanes.values()),
        'total_gpu_hours':round(total,1),'scenario_gpu_hours':[round(total*.7,1),round(total*1.6,1)],
        'ideal_days_10_gpus':round(total/240,2),'longest_serial_lane_days':round(longest/24,2),
        'current_policy_lower_bound_days':round(max(total/10,longest)/24,2),
        'limitations':['Operational scenarios, not confidence intervals or a promised completion time.',
                       'Actual completed timings mix GPU types; no assumed blanket A100 speedup.',
                       'Slow unobserved groups use explicit historical/probe extrapolations.',
                       'Running partial units count as full remaining units; no progress within a unit is credited.',
                       'Queue waits, dependencies, technical retries and CPU aggregation add calendar time.',
                       'Existing lane caps matter; ideal total/10 is not the current-schedule ETA.',
                       'Only registered active extensions; no new future experiments or historical holds included.']}
(BASE/'runtime_forecast_20261018_evening.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='groups'},indent=2),flush=True)
