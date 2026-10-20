"""Change-triggered, bounded Slurm CPU refresh of the new ALN3.5 analyses."""
from datetime import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

ROOT = Path('/home/infres/yinwang/EEG_auditory')
BASE = ROOT/'private/auditory_alignment_v3/aln35'
CONFIG = BASE/'evidence_tasks.json'
STATE = BASE/'evidence/state.json'


def read(path): return json.loads(Path(path).read_text())
def digest(value): return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()
def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(value, indent=2)+'\n'); os.replace(tmp, path)


def normal_jobs():
    # Reissued immediately before each CPU submission. Unknown array syntax
    # conservatively exhausts admission instead of counting an array as one.
    raw = subprocess.check_output(['squeue','-u','yinwang','-h','-q','normal',
                                   '-o','%i|%j|%T'], text=True, timeout=40)
    return [line.split('|') for line in raw.splitlines() if line.strip()]


def normal_count(jobs):
    count = 0
    for jid, *_ in jobs:
        match = re.fullmatch(r'\d+_\[(\d+)-(\d+)(?:%\d+)?\]', jid)
        if '[' in jid and not match: return 30
        count += int(match[2])-int(match[1])+1 if match else 1
    return count


def signature(task):
    files = []
    for pattern in task['sources']:
        for p in sorted(ROOT.glob(pattern)):
            if not p.is_file() or p.name.endswith('.FAILED.json'): continue
            stat = p.stat()
            files.append([str(p.relative_to(ROOT)), stat.st_size, stat.st_mtime_ns])
    ready = len(files) >= task.get('minimum_files', 1)
    ready &= all((ROOT/p).is_file() for p in task.get('requires', []))
    return digest({'task':task, 'files':files}), ready, len(files)


def validate_task(task):
    args = task['args']
    assert len(args) >= 2 and args[0] == '-m'
    assert args[1].startswith('auditory_alignment_v3.aln35.')
    path = ROOT / (args[1].replace('.', '/')+'.py')
    assert hashlib.sha256(path.read_bytes()).hexdigest() == task['module_sha256']
    assert 1 <= task.get('minimum_files', 1)


def tick():
    assert os.environ.get('SLURM_JOB_ID')
    if not CONFIG.exists(): return
    config = read(CONFIG); assert config['version'] == 1
    state = read(STATE) if STATE.exists() else {'tasks':{}}
    jobs = normal_jobs(); live = {j[0] for j in jobs}; now = time.time()
    for name, task in config['tasks'].items():
        validate_task(task)
        item = state['tasks'].setdefault(name, {})
        pending = item.get('pending')
        if pending:
            receipt = BASE/'evidence/tasks'/name/(pending['job']+'.json')
            if receipt.exists():
                result = read(receipt)
                if result['status'] == 'pass':
                    item.update(last_signature=result['signature'], last_success=now,
                                result_receipt=str(receipt), failure=None)
                else: item['failure'] = result
                item.pop('pending')
            elif pending['job'] not in live and now-pending['submitted'] > 180:
                item['failure'] = {'job':pending['job'], 'reason':'job left queue without success receipt'}
                item.pop('pending')
        sig, ready, n = signature(task)
        item.update(current_signature=sig, source_files=n, ready=ready)
    active = sum('pending' in item for item in state['tasks'].values())
    for name, task in config['tasks'].items():
        item = state['tasks'][name]
        if (active >= 2 or not item['ready'] or item.get('pending') or item.get('failure')
                or item['current_signature'] == item.get('last_signature')
                or now-item.get('last_submitted', 0) < task.get('interval_seconds', 1800)):
            continue
        if normal_count(normal_jobs()) > 27: break
        command = ['sbatch','--parsable','--job-name=c3_s35ev_'+name,
                   'slurm/aln35_evidence_task.sbatch', name]
        jid = subprocess.check_output(command, text=True, cwd=ROOT, timeout=60).strip().split(';')[0]
        assert jid.isdigit()
        item['pending'] = {'job':jid, 'submitted':now, 'signature':item['current_signature']}
        item['last_submitted'] = now; active += 1
        print('S35_EVIDENCE_SUBMIT', name, jid, flush=True)
    state.update(time=datetime.now().astimezone().isoformat(), job=os.environ['SLURM_JOB_ID'])
    own = os.environ['SLURM_JOB_ID']
    left = subprocess.check_output(['squeue','-j',own,'-h','-o','%L'], text=True, timeout=40).strip()
    match = re.fullmatch(r'(?:(\d+)-)?(\d+):(\d+):(\d+)', left)
    seconds = (int(match[1] or 0)*86400+int(match[2])*3600+int(match[3])*60+int(match[4])) if match else None
    if seconds is not None and 0 < seconds <= 3600 and state.get('renewal',{}).get('parent') != own:
        if normal_count(normal_jobs()) <= 27:
            jid = subprocess.check_output(['sbatch','--parsable','--dependency=afterany:'+own,
                     'slurm/aln35_milestones_v12.sbatch'], text=True, cwd=ROOT, timeout=60).strip().split(';')[0]
            assert jid.isdigit(); state['renewal'] = {'parent':own,'job':jid}
    write(STATE, state)


def run_task(name):
    assert os.environ.get('SLURM_JOB_ID')
    task = read(CONFIG)['tasks'][name]; validate_task(task)
    sig, ready, n = signature(task); assert ready
    started = time.time()
    result = {'task':name, 'job':os.environ['SLURM_JOB_ID'], 'signature':sig,
              'source_files':n, 'descriptor':task, 'status':'failed'}
    try:
        subprocess.run([sys.executable,'-B','-u',*task['args']], check=True, cwd=ROOT)
        result['status'] = 'pass'
    except BaseException as exc:
        result['error'] = repr(exc); raise
    finally:
        result['seconds'] = time.time()-started
        write(BASE/'evidence/tasks'/name/(os.environ['SLURM_JOB_ID']+'.json'), result)


if __name__ == '__main__':
    os.umask(0o077)
    if len(sys.argv) > 1: run_task(sys.argv[1])
    else: tick()
