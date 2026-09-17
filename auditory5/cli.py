"""Slurm-only entry points for the versioned auditory5 experiment stages."""
import argparse, dataclasses, importlib, json, math, os, subprocess, sys, shutil
import xml.etree.ElementTree as ET
from pathlib import Path
import yaml
from auditory5.provenance import ROOT,require_slurm,write_json,digest,object_hash


def read_config(path):
    p=Path(path)
    if not p.is_absolute():p=ROOT/p
    config=yaml.safe_load(p.read_text())
    if config['project']['overwrite'] or config['project']['publish_individual_data']:
        raise ValueError('v1 requires no overwrite and restricted individual outputs')
    return config


def test_contracts(config,run):
    from auditory5.preprocessing import effective_impulse_support
    private=ROOT/config['paths']['private_relative']/'validation'/run
    public=ROOT/config['paths']['aggregates_relative']/run
    private.mkdir(parents=True,exist_ok=False);public.mkdir(parents=True,exist_ok=False)
    snapshot=private/'source_snapshot'
    shutil.copytree(ROOT/'auditory5',snapshot/'auditory5',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    shutil.copytree(ROOT/'tests/auditory5',snapshot/'tests/auditory5',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    environment=dict(os.environ,AUDITORY5_ROOT=str(ROOT),PYTHONPATH=str(snapshot))
    result=subprocess.run([sys.executable,'-m','pytest',str(snapshot/'tests/auditory5'),'-v',
                           '--junitxml='+str(private/'junit.xml')],cwd=snapshot,env=environment)
    xml=ET.parse(private/'junit.xml').getroot()
    cases=xml.findall('.//testcase')
    failures=len(xml.findall('.//failure'));errors=len(xml.findall('.//error'));skipped=len(xml.findall('.//skipped'))
    successful=result.returncode==0 and len(cases)>=35 and not skipped
    supports=[dataclasses.asdict(effective_impulse_support(fs)) for fs in [250.,500.,1000.]]
    embargo=max(10.,max(s['support_seconds'] for s in supports))
    block=30*math.ceil((4*embargo+0.7)/30)
    frozen={'source_plan_sha256':digest(ROOT/'AUDITORY_FIVE_IDEAS_SERVER_PLAN_v1.md'),
        'config_hash':object_hash(config),'impulse_support_by_original_fs':supports,
        'A_block_seconds':block,'A_B_embargo_seconds':embargo,
        'epoch_interval_seconds':[-0.2,0.5],'block_eligibility_rule':'entire_direct_epoch_inside_block_plus_embargo_on_both_sides',
        'A_half_block_minimum':4,'general_block_seconds':30,
        'anti_alias_gate':'fixed test_signal anti-alias/response tests; no outcome-based tuning',
        'QC_version':'auditory5_qc_v1','scalp_ptp_max_uv':150.,'raw_flat_ptp_min_uv':0.5,
        'record_raw_flat_fraction_max':0.2,'offline_record_qc':True,
        'statistical_claim':'IIR effective support at numeric tolerance, not mathematical independence'}
    summary={'stage':'S1_module_contracts','status':'PASS' if successful else 'IMPLEMENTATION_FAIL',
        'job_id':os.environ['SLURM_JOB_ID'],'tests_run':len(cases),
        'failure_count':failures,'error_count':errors,'skipped':skipped,
        'A_block_seconds':block,'A_B_embargo_seconds':embargo,
        'hard_gate_scope':'synthetic module contracts only; export/training integration gates remain required',
        'code_hashes':{str(p.relative_to(snapshot)):digest(p) for p in sorted((snapshot/'auditory5').rglob('*.py'))}}
    write_json(private/'processing_spec.json',frozen)
    write_json(public/'validation.json',summary)
    print(json.dumps({k:v for k,v in summary.items() if k!='code_hashes'},indent=2))
    if not successful:raise RuntimeError('Hard module test failure; inspect private Slurm log')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',default='configs/auditory5_v1.yaml')
    parser.add_argument('--dry-run',action='store_true')
    sub=parser.add_subparsers(dest='command',required=True)
    for name in ['preflight','build-manifest','build-splits','test-contracts','export-eeg','make-job-plan','run-job','aggregate','validate-release']:
        p=sub.add_parser(name)
        p.add_argument('--run',help='new immutable run identifier')
        if name=='export-eeg':
            p.add_argument('--bank',choices=['P1_CAUSAL20','P2_SPATIAL_SPLIT'],required=True)
            p.add_argument('--shard',type=int,default=0);p.add_argument('--shards',type=int,default=1)
            p.add_argument('--record-ids',nargs='*')
            p.add_argument('--limit',type=int)
            p.add_argument('--contract-run',default='contracts_005')
            p.add_argument('--branch',choices=['HA','MFF'],default='HA')
            p.add_argument('--mff-view',choices=['continuous','E0_BLOCK_RESET_60S'],default='continuous')
            p.add_argument('--mff-pairs',action='store_true')
        if name in ['make-job-plan','aggregate']:
            p.add_argument('--stage',default='S3')
            p.add_argument('--split-run',default='splits_001')
        if name=='make-job-plan':
            p.add_argument('--contract-run',default='contracts_007')
            p.add_argument('--synthetic-run',default='synthetic_001')
        if name=='build-splits':
            p.add_argument('--export-run',required=True)
            p.add_argument('--export-validation',required=True)
        if name=='run-job':
            p.add_argument('--plan',required=True);p.add_argument('--index',required=True,type=int)
        if name not in ['preflight','test-contracts']:
            p.add_argument('--manifest',default='manifest_001')
        p.add_argument('--resume',action='store_true')
    args=parser.parse_args()
    require_slurm();config=read_config(args.config)
    if args.dry_run:
        print(json.dumps({'command':args.command,'routes':config['scope']['routes'],'run':args.run,
            'status':'DRY_RUN_NO_COMPUTATION','read_only_raw':True,'restricted_outputs':True}));return
    if args.resume:raise ValueError('Resume requires task-specific checkpoint/hash validation; unavailable for this stage')
    if args.command=='preflight':
        if not args.run:parser.error('--run is required')
        subprocess.run([sys.executable,str(ROOT/'scripts/auditory5_bootstrap.py'),'--run',args.run],check=True)
    elif args.command=='build-manifest':
        from auditory5.manifest import build_manifest
        if not args.run:parser.error('--run is required')
        print(json.dumps(build_manifest(config,args.run),indent=2))
    elif args.command=='test-contracts':
        if not args.run:parser.error('--run is required')
        test_contracts(config,args.run)
    else:
        module={'build-splits':'splitting','export-eeg':'exporting','make-job-plan':'job_plan',
                'run-job':'execution','aggregate':'reporting','validate-release':'reporting'}[args.command]
        implementation=importlib.import_module('auditory5.'+module)
        implementation.run(config,args)


if __name__=='__main__':main()
