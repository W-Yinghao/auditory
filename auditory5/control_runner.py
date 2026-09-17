"""Slurm-only frozen-source entry point for prespecified sensitivity modules."""
import argparse,json,os,shutil,sys
from pathlib import Path
from auditory5.cli import read_config
from auditory5.provenance import ROOT,require_slurm,digest,write_json


def main():
    require_slurm();p=argparse.ArgumentParser()
    p.add_argument('--route',choices=['A','B','D'],required=True);p.add_argument('--run',required=True)
    p.add_argument('--modes',nargs='+',required=True);p.add_argument('--contracts',required=True)
    p.add_argument('--split-run',default='splits_001');p.add_argument('--plan',default='private/auditory5_v1/jobs/plan_001/plan.json')
    p.add_argument('--core',nargs='*',default=[]);p.add_argument('--outer-folds',nargs='+',type=int);a=p.parse_args()
    if a.outer_folds is not None and a.route!='A':raise ValueError('Partial-fold smoke is specific to A controls')
    config=read_config('configs/auditory5_v1.yaml');base=ROOT/config['paths']['private_relative'];dest=base/'routes'/a.run
    snap=base/'jobs'/('control_'+a.run)/'source'
    if Path(__file__).resolve()!=snap/'auditory5/control_runner.py':
        snap.parent.mkdir(parents=True,exist_ok=False)
        shutil.copytree(ROOT/'auditory5',snap/'auditory5',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
        env=dict(os.environ,AUDITORY5_ROOT=str(ROOT),PYTHONPATH=str(snap));os.chdir(snap)
        os.execve(sys.executable,[sys.executable,'-m','auditory5.control_runner',*sys.argv[1:]],env)
    gate=json.loads((ROOT/config['paths']['aggregates_relative']/a.contracts/'validation.json').read_text())
    module='auditory5/routes/route_'+a.route.lower()+'_controls.py'
    dependencies=[module,'auditory5/routes/route_'+a.route.lower()+'.py','auditory5/probes.py','auditory5/training.py']
    dependencies+=['auditory5/routes/route_b_learned.py'] if a.route=='B' else []
    if gate['status']!='PASS' or any(digest(snap/m)!=gate['code_hashes'].get(m) for m in dependencies):
        raise ValueError('Sensitivity module has not passed the specified contract gate')
    plan=Path(a.plan);plan=plan if plan.is_absolute() else ROOT/plan
    core={}
    for item in a.core:
        mode,run=item.split('=',1)
        if mode in core:raise ValueError('Duplicate core representation mapping')
        path=Path(run);core[mode]=path if path.is_absolute() else base/'routes'/run
    if a.route=='A':
        from auditory5.routes.route_a_controls import run
        summary=run(config,plan_path=str(plan),split_run=a.split_run,output_run=a.run,modes=tuple(a.modes),
            processing_spec_path='private/auditory5_v1/validation/'+a.contracts+'/processing_spec.json',
            outer_folds=None if a.outer_folds is None else tuple(a.outer_folds))
    else:
        if set(a.modes)!=set(core):raise ValueError('Each representation requires an explicit completed primary run')
        if a.route=='B':from auditory5.routes.route_b_controls import run
        else:from auditory5.routes.route_d_controls import run
        summary=run(config,a.split_run,plan,a.modes,core,dest)
    public=ROOT/config['paths']['aggregates_relative']/a.run;public.mkdir(parents=True,exist_ok=True)
    if not (public/'summary.json').exists():write_json(public/'summary.json',summary)
    write_json(snap.parent/'completion.json',{'status':'PASS','scientific_status':summary['status'],
        'route':a.route,'run':a.run,'job_id':os.environ['SLURM_JOB_ID'],
        'code_hashes':{m:digest(snap/m) for m in dependencies}})
    print(json.dumps({'route':a.route,'run':a.run,'scientific_status':summary['status']}),flush=True)

if __name__=='__main__':main()
