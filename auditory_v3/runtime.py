"""Immutable per-run execution and private failure records."""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import time

ROOT=Path(os.environ.get('AUDITORY_ROOT','/home/infres/yinwang/EEG_auditory'))

def require_slurm():
    if not os.environ.get('SLURM_JOB_ID'):raise RuntimeError('SLURM_REQUIRED')

def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()

def write_json(path,obj):
    Path(path).write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    Path(path).chmod(0o600)

def safe_run(run):
    if not run or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-' for c in run):raise ValueError('UNSAFE_RUN')
    return run

def create(args):
    import yaml
    require_slurm();os.umask(0o077)
    run=safe_run(args.run)
    private=ROOT/'private/auditory_v3'/run
    if any((ROOT/base/'auditory_v3'/run).exists() for base in ('private','results','reports')):raise FileExistsError('RUN_OCCUPIED')
    private.mkdir(mode=0o700)
    public=ROOT/'results/auditory_v3'/run;public.mkdir(mode=0o700)
    report=ROOT/'reports/auditory_v3'/run;report.mkdir(mode=0o700)
    config=yaml.safe_load((ROOT/args.config).read_text())
    source=private/'source';source.mkdir(mode=0o700)
    code_root=Path(__file__).resolve().parents[1]
    paths=[]
    for folder in ('auditory_v3','tests/auditory_v3','auditory5','auditory_next','auditory_v21'):
        paths += [(p,p.relative_to(code_root)) for p in (code_root/folder).rglob('*.py') if '__pycache__' not in p.parts]
    paths += [(ROOT/args.config,Path(args.config)),(ROOT/'AUDITORY_V3_DESIGN_AND_EXECUTION_PLAN_eb24106.md',Path('AUDITORY_V3_DESIGN_AND_EXECUTION_PLAN_eb24106.md'))]
    hashes={}
    for p,rel in sorted(paths):
        target=source/rel
        target.parent.mkdir(parents=True,exist_ok=True,mode=0o700);shutil.copyfile(p,target);hashes[str(rel)]=digest(target)
    write_json(private/'config.json',config)
    write_json(private/'args.json',vars(args))
    write_json(private/'start.json',dict(job_id=os.environ['SLURM_JOB_ID'],run=run,command=args.command,
        start_unix=time.time(),config_sha256=digest(ROOT/args.config),source_hashes=hashes,
        cpu_allocation=os.environ.get('SLURM_CPUS_PER_TASK'),gpu_allocation=os.environ.get('SLURM_GPUS'),
        automatic_push=False))
    return private,public,report

class Ledger:
    """Atomic round-wide reservation BEFORE each model/optimizer attempt."""
    def __init__(self,private,kind='head'):
        self.private=Path(private);self.kind=kind
    def __call__(self,event):
        require_slurm()
        event=dict(event)
        status=event.get('event',event.get('status','start'))
        is_start=status in ('start','attempt','fit_start','started','logistic_fit_attempt')
        global_path=ROOT/'private/auditory_v3/fit_events.jsonl'
        with global_path.open('a+') as f:
            fcntl.flock(f,fcntl.LOCK_EX);f.seek(0)
            old=[json.loads(line) for line in f if line.strip()]
            if event.get('recovery_of') and any(r['details'].get('recovery_of')==event['recovery_of'] for r in old):raise RuntimeError('RECOVERY_ALREADY_RESERVED')
            if is_start:
                n=sum(r['kind']==self.kind and r['is_start'] for r in old)
                maximum={'head':3000,'encoder':30,'synthetic_encoder':3}[self.kind]
                if n>=maximum:raise RuntimeError('ROUND_FIT_BUDGET_EXCEEDED')
            item=dict(run=self.private.name,kind=self.kind,is_start=is_start,time_unix=time.time(),details=event)
            f.seek(0,2);f.write(json.dumps(item,allow_nan=False)+'\n');f.flush();os.fsync(f.fileno())
        with (self.private/'fit_events.jsonl').open('a') as f:f.write(json.dumps(item,allow_nan=False)+'\n')


def finish(private,public,summary):
    start=json.loads((private/'start.json').read_text())
    summary=dict(summary);aggregate=summary.pop('public_summary',None)
    runtime=dict(job_id=os.environ['SLURM_JOB_ID'],elapsed_seconds=time.time()-start['start_unix'],config_sha256=start['config_sha256'])
    obj=dict(summary,**runtime)
    write_json(private/'completion.json',obj);write_json(public/'summary.json',dict(aggregate,**runtime) if aggregate is not None else obj)
    print(json.dumps(dict(status=obj.get('status'),packet=obj.get('packet'),**runtime),ensure_ascii=False),flush=True)
