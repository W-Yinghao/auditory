"""Versioned route entry point. Snapshots code before starting analysis."""
import argparse,json,os,shutil,sys
from pathlib import Path
from auditory5.cli import read_config
from auditory5.provenance import ROOT,require_slurm,digest,write_json


def main():
    require_slurm();p=argparse.ArgumentParser();p.add_argument('--route',choices=list('ABCDE'),required=True);p.add_argument('--run',required=True)
    p.add_argument('--split-run',default='splits_001');p.add_argument('--plan',default='private/auditory5_v1/jobs/plan_001/plan.json')
    p.add_argument('--modes',nargs='+',default=['L0']);p.add_argument('--contracts',default='contracts_008')
    p.add_argument('--c-linear-only',action='store_true');a=p.parse_args()
    if a.c_linear_only and a.route!='C':raise ValueError('Linear-only fallback is specific to C')
    config=read_config('configs/auditory5_v1.yaml');base=ROOT/config['paths']['private_relative'];dest=base/'routes'/a.run
    snap=base/'jobs'/('route_'+a.run)/'source'
    if Path(__file__).resolve()!=snap/'auditory5/route_runner.py':
        snap.parent.mkdir(parents=True,exist_ok=False);shutil.copytree(ROOT/'auditory5',snap/'auditory5',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
        env=dict(os.environ,AUDITORY5_ROOT=str(ROOT),PYTHONPATH=str(snap));os.chdir(snap)
        os.execve(sys.executable,[sys.executable,'-m','auditory5.route_runner',*sys.argv[1:]],env)
    gate=json.loads((ROOT/config['paths']['aggregates_relative']/a.contracts/'validation.json').read_text())
    learned_b=a.route=='B' and a.modes!=['L0']
    if learned_b and 'L0' in a.modes:raise ValueError('Run L0 and learned B representations separately')
    module='auditory5/routes/route_b_learned.py' if learned_b else 'auditory5/routes/route_'+a.route.lower()+'.py'
    checked_modules=[module]+(['auditory5/routes/route_b.py'] if learned_b else [])
    if gate['status']!='PASS' or any(digest(snap/m)!=gate['code_hashes'].get(m) for m in checked_modules):raise ValueError('Route implementation has not passed this contract gate')
    plan=Path(a.plan);plan=plan if plan.is_absolute() else ROOT/plan
    if a.route=='B':
        if learned_b:
            from auditory5.routes.route_b_learned import run
            summary=run(config,a.split_run,plan,a.modes,dest)
        else:
            from auditory5.routes.route_b import run_l0
            summary=run_l0(config,a.split_run,dest)
    elif a.route=='D':
        from auditory5.routes.route_d import run
        summary=run(config,a.split_run,plan,a.modes,dest)
    elif a.route=='A':
        from auditory5.routes.route_a import run
        summary=run(config,a.split_run,plan,a.modes,dest)
    elif a.route=='C':
        from auditory5.routes.route_c import run
        summary=run(config,plan.parent.name,dest,modes=tuple(a.modes),linear_only=a.c_linear_only)
    else:
        from auditory5.routes.route_e import run
        summary=run(config,dest)
    public=ROOT/config['paths']['aggregates_relative']/a.run
    if not (public/'summary.json').exists():public.mkdir(parents=True,exist_ok=True);write_json(public/'summary.json',summary)
    write_json(snap.parent/'completion.json',{'status':'PASS','route':a.route,'run':a.run,'scientific_status':summary['status'],
        'job_id':os.environ['SLURM_JOB_ID'],'module_sha256':digest(snap/module)})
    print(json.dumps({'route':a.route,'run':a.run,'scientific_status':summary['status']}),flush=True)
if __name__=='__main__':main()
