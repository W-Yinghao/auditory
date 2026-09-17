"""Freeze a bounded dependency plan and a runnable source snapshot."""
import json,os,shutil
import pandas as pd
from auditory5.provenance import ROOT,require_slurm,write_json,digest,object_hash


def run(config,args):
    require_slurm();base=ROOT/config['paths']['private_relative'];dest=base/'jobs'/args.run;dest.mkdir(parents=True,exist_ok=False)
    split=json.loads((base/'splits'/args.split_run/'folds.json').read_text());support=pd.read_parquet(base/'splits'/args.split_run/'support.parquet')
    gate=ROOT/config['paths']['aggregates_relative']/args.contract_run/'validation.json'
    assert json.loads(gate.read_text())['status']=='PASS'
    tasks=[]
    for fold in split['folds']:
        of=fold['outer_fold']
        for branch in ['all','left','right']:
            for mode in ['L0','R_RAND','R_SUP','R_SIM']:
                tasks.append({'name':f'outer{of}_{branch}_{mode}','stage':'outer','outer_fold':of,'inner_fold':None,
                    'branch':branch,'mode':mode,'seed':11,'fit_groups':fold['train_groups'],
                    'validation_groups':[],'test_groups':fold['test_groups'],'resource':'gpu' if mode in ['R_SUP','R_SIM'] else 'cpu'})
        if int(support.D.sum())>=config['route_D']['min_candidates']:
            for inner in range(3):
                val=sorted(g for g,i in fold['D_inner_fold_by_group'].items() if i==inner)
                train=sorted(set(fold['train_groups'])-set(val))
                for mode in ['R_SUP','R_SIM']:
                    tasks.append({'name':f'D_outer{of}_inner{inner}_{mode}','stage':'D_inner','outer_fold':of,'inner_fold':inner,
                        'branch':'all','mode':mode,'seed':11,'fit_groups':train,'validation_groups':val,
                        'test_groups':fold['test_groups'],'resource':'gpu'})
    for i,task in enumerate(tasks):task['index']=i
    learned=sum(t['resource']=='gpu' for t in tasks);assert learned<=config['resources']['max_initial_encoder_jobs']
    snapshot=dest/'source';shutil.copytree(ROOT/'auditory5',snapshot/'auditory5',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    hashes={str(p.relative_to(snapshot)):digest(p) for p in sorted(snapshot.rglob('*.py'))}
    plan={'version':'auditory5_job_plan_v1','tasks':tasks,'config':config,'config_hash':object_hash(config),
        'split_run':args.split_run,'split_hash':digest(base/'splits'/args.split_run/'folds.json'),
        'export_run':split['export_run'],'contract_run':args.contract_run,'contract_hash':digest(gate),
        'synthetic_run':args.synthetic_run,'source_snapshot':str(snapshot),'code_hashes':hashes,
        'learned_encoder_jobs':learned,'CPU_jobs':len(tasks)-learned,
        'pending_routes':'These jobs produce representations and stimulus diagnostics; A-E route readouts and verdicts are separate jobs.'}
    write_json(dest/'plan.json',plan)
    for kind in ['cpu','gpu']:
        write_json(dest/(kind+'_indices.json'),[t['index'] for t in tasks if t['resource']==kind])
    public=ROOT/config['paths']['aggregates_relative']/args.run;public.mkdir(parents=True,exist_ok=False)
    write_json(public/'job_plan.json',{'status':'PREPARED_NOT_SUBMITTED','learned_encoder_jobs':learned,'CPU_jobs':len(tasks)-learned,
        'outer_folds':split['fold_count'],'main_seed':11,'max_concurrent_GPU':2,'max_concurrent_CPU':4,
        'plan_sha256':digest(dest/'plan.json'),'scope':'representation generation; five scientific verdicts pending'})
    print(json.dumps({'plan':str(dest/'plan.json'),'learned_encoder_jobs':learned,'cpu_jobs':len(tasks)-learned}))
