"""Split the operational cost estimate into dependencies, curves and architectures."""
import json
import os
from pathlib import Path
assert os.environ.get('SLURM_JOB_ID')
base=Path('private/auditory_alignment_v3/aln34')
a=json.loads((base/'runtime_audit_20261017.json').read_text())
f=json.loads((base/'runtime_forecast_20261017.json').read_text())
h=a['historical_sources']['groups']
out={'snapshot':a['time'],'job':os.environ['SLURM_JOB_ID'],'data':{},'budget':{}}
for lane in ('data_inner_v1','breadth_inner_v1'):
    for key,g in a['lanes'][lane]['groups'].items():
        ds,arch,kind,axis,frac=key.split('|')
        t=g['times'].get('mean_s')
        if t is None:
            t=a['lanes']['data_inner_v1']['groups'][f'dtu|{arch}|{kind}|{axis}|{frac}']['times']['mean_s']
            t*=h[f'{ds}|{arch}|||']['times']['mean_s']/h[f'dtu|{arch}|||']['times']['mean_s']
        category=('inner_sources' if axis=='inner_person' else 'reduced_data_curves')+'|'+arch
        out['data'][category]=out['data'].get(category,0)+g['remaining']*t/3600
for lane in ('learning_budget_v2','breadth_budget_v1'):
    for key,g in a['lanes'][lane]['groups'].items():
        ds,arch,*_=key.split('|')
        t=g['times'].get('mean_s')
        if t is None:
            hist=h[f'{ds}|{arch}|||'];train=hist['train']['mean_s']
            t=2*train+4*(hist['times']['mean_s']-train)
        out['budget'][arch]=out['budget'].get(arch,0)+g['remaining']*t/3600
for key in ('data','budget'):out[key]={k:round(v,2) for k,v in out[key].items()}
out['total_forecast_gpu_h']=f['total_gpu_h']
(base/'priority_cost_breakdown_20261017.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2),flush=True)
