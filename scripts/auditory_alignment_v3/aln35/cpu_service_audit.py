"""Read-only, bounded Slurm audit before retiring legacy CPU services."""
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time

ROOT = Path('/home/infres/yinwang/EEG_auditory')
OUT = ROOT / 'private/auditory_alignment_v3'
BASE = OUT / 'aln35/cpu_services_20261019'
EID = re.compile(r'^(ALN3X?_[0-9a-f]{16})(?:_[A-Za-z0-9]+)*_best\.pt$')


def read(path):
    return json.loads(path.read_text())


def main():
    job = os.environ['SLURM_JOB_ID']
    os.umask(0o077)
    BASE.mkdir(parents=True, exist_ok=True)
    start = datetime.now().astimezone().isoformat()
    units = OUT / 'units'
    completed = {
        p.stem for p in units.glob('ALN3*.json')
        if not p.name.endswith('.FAILED.json') and read(p).get('status') == 'complete'
    }
    # Queue eligibility is separate from historical held rows.
    queues = {}
    for path in sorted(OUT.glob('queue_v3_*.txt')):
        if path.name.endswith('_weights.txt'):
            continue
        ids = [line.split('|')[0] for line in path.read_text().splitlines() if line.strip()]
        queues[path.name] = {
            'rows': len(ids),
            'without_complete_record': [eid for eid in ids if eid not in completed],
        }
    claims = sorted(p.name.removesuffix('.claim') for p in (OUT / 'pool').glob('*/*.claim'))
    files = list((OUT / 'ckpt').iterdir())
    names = {p.name for p in files}
    regular = []
    links = 0
    for path in sorted(files):
        if path.is_symlink():
            links += 1
            continue
        if not path.is_file():
            continue
        stat = path.stat()
        match = EID.fullmatch(path.name)
        eid = match.group(1) if match else None
        complete = eid in completed if eid else False
        running = eid in claims if eid else False
        resume = any(name.startswith(eid) and '_resume.pt' in name for name in names) if eid else False
        young = time.time() - stat.st_mtime < 900
        regular.append({
            'name': path.name, 'bytes': stat.st_size, 'mtime_ns': stat.st_mtime_ns,
            'recognized_offload_file': bool(match), 'experiment_id': eid,
            'complete': complete, 'claimed': running, 'resume_present': resume,
            'younger_than_15m': young,
            # An overestimate: dependency checks could only remove more files.
            'candidate_before_dependency_checks': bool(match and complete and not running and not resume and not young),
        })
    fleet = read(OUT / 'aln35/fleet_status.json')
    evidence = read(OUT / 'aln34/milestone_state.json')
    live = subprocess.check_output(
        ['squeue', '-u', os.environ['USER'], '-h', '-o', '%i|%j|%q|%T|%C|%m|%b|%Z'],
        text=True, timeout=40,
    )
    usage = subprocess.run(
        ['sstat', '-j', '1047289.batch,1044086.batch,1047358.batch,1044070.batch',
         '--noheader', '--parsable2', '--format=JobID,AveCPU,AveRSS,MaxRSS,NTasks'],
        text=True, capture_output=True, timeout=40,
    )
    sources = ['watch_anyhost.sh', 'ckpt_offload.py', 'aln35/maintain_fleet.py',
               'aln35/milestone_monitor_v12.py']
    record = {
        'status': 'complete', 'job': job, 'time': start,
        'scope': 'read-only metadata; no checkpoint payload loaded, copied, removed or hashed',
        'legacy_queues': queues, 'legacy_claims': claims,
        'main_checkpoint_symlinks': links, 'main_checkpoint_regular_files': regular,
        'main_checkpoint_regular_bytes': sum(f['bytes'] for f in regular),
        'eligible_offload_before_dependency_checks': sum(f['candidate_before_dependency_checks'] for f in regular),
        'fleet': {'job': fleet['job'], 'time': fleet['time'],
                  'lanes_with_remaining': [{k: l.get(k) for k in ('name', 'lane', 'remaining', 'state')}
                                           for l in fleet['lanes'] if l.get('remaining')]},
        'evidence': {k: evidence.get(k) for k in ('job', 'time', 'counts', 'errors')},
        'squeue': live.splitlines(), 'sstat': usage.stdout.splitlines(),
        'sstat_returncode': usage.returncode, 'sstat_error': usage.stderr,
        'source_sha256': {name: hashlib.sha256((OUT / name).read_bytes()).hexdigest() for name in sources},
    }
    record['legacy_retirement_supported'] = (
        not claims
        and not any(q['without_complete_record'] for q in queues.values())
        and record['eligible_offload_before_dependency_checks'] == 0
        and evidence['counts']['true_full'] == [800, 800]
        and evidence['counts']['public_prior'] == [1154, 1154]
    )
    target = BASE / f'audit_{job}.json'
    target.write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps({k: record[k] for k in ('status', 'job', 'legacy_retirement_supported',
          'eligible_offload_before_dependency_checks', 'main_checkpoint_regular_bytes')}))
    print(target)


if __name__ == '__main__':
    main()
