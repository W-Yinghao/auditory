"""One fleet authority plus a five-minute efficiency loop; Slurm only."""
import fcntl
import importlib
import json
import os
from pathlib import Path
import subprocess
import time

from private.auditory_alignment_v3.aln34 import maintain_fleet_v14 as Previous
from private.auditory_alignment_v3.aln35 import priority_schedule as Priority
from private.auditory_alignment_v3.aln34 import efficiency_loop_v2 as E

ROOT, OUT, BASE = E.ROOT, E.OUT, E.BASE
CONFIG = dict(Previous.CONFIG)
CONFIG['private'] = ('c3_privscience', 'private_current_time_v2', None, 1, ())
# Process-local configuration only; the old coordinator and source files remain intact.
for key in ('inner', 'cb_auditory'):
    value = list(CONFIG[key]); value[3] = 2; CONFIG[key] = tuple(value)
Previous.CONFIG.update(CONFIG)
Previous.Priority = Priority
NEWBASE = OUT / 'aln35'
PLUGIN_PATH = NEWBASE / 'fleet_plugins.json'
read, log, sha = Previous.read, Previous.log, Previous.sha
JOURNAL = BASE / 'efficiency_jobs.json'


def submit(command):
    jid = subprocess.check_output(['sbatch', '--parsable', *command], text=True, timeout=60).strip().split(';')[0]
    if not jid.isdigit():
        raise RuntimeError('non-numeric sbatch receipt: ' + jid)
    with (OUT / 'logs/operations.log').open('a') as handle:
        handle.write(f'{E.stamp()} fleet ALN35 {os.environ["SLURM_JOB_ID"]} submitted {jid}: {command}\n')
    log(f'SUBMIT {jid}: {command}')
    return jid


def cancel(command):
    subprocess.run(command, check=True, timeout=40)


def base_command(item):
    if item['name'] == 'c3_aln3fm':
        return item['submit']
    return ['--nice=' + str(Priority.nice(item['lane'])), *item['submit']]


def renew_services(jobs, monitor):
    # The existing offload handoff is preserved, with proper array accounting.
    if E.normal_slots(jobs) > 27:
        return
    Previous.renew_offload(jobs)
    current = os.environ['SLURM_JOB_ID']
    own = next((j for j in jobs if j['id'] == current), None)
    if not own:
        return
    left = Previous.seconds_left(own['left'])
    renewal = monitor.state.get('renewal', {})
    if left is not None and 0 < left <= 3600 and renewal.get('parent') != current:
        jid = submit(['--dependency=afterany:' + current, 'slurm/aln35_maintain_fleet.sbatch'])
        monitor.state['renewal'] = {'parent': current, 'job': jid}
        E.write(E.STATE, monitor.state)
        monitor.event('renew_loop', parent=current, job=jid)
        return  # one CPU submission per pass; recheck the shared quota next time
    receipt = BASE / 'efficiency_prior_keeper.json'
    if receipt.exists() and not (BASE / 'STOP_keeper_prior_v2').exists():
        prior = read(receipt)
        keeper = next((j for j in jobs if j['id']==prior['job'] and j['state']=='RUNNING'), None)
        if keeper:
            left = Previous.seconds_left(keeper['left'])
            previous = monitor.state.get('prior_keeper_renewal', {})
            if left is not None and 0 < left <= 3600 and previous.get('parent') != keeper['id']:
                jid = submit(['--dependency=afterany:' + keeper['id'], 'slurm/aln34_prior_keeper_v2.sbatch'])
                monitor.state['prior_keeper_renewal'] = {'parent': keeper['id'], 'job': jid}
                E.write(E.STATE, monitor.state)
                monitor.event('renew_prior_keeper', parent=keeper['id'], job=jid)


def launch(item, monitor, journal, force_broad=False, replaces=None):
    lane = item.get('lane', 'legacy_fm')
    decision = E.route(lane, monitor.state, force_broad=force_broad)
    command = base_command(item)
    jid = submit([*E.route_args(decision), *command])
    journal[jid] = {'id': jid, 'name': item['name'], 'lane': lane, 'decision': decision,
                    'base_command': command, 'submitted_epoch': time.time(),
                    'fallback': force_broad, 'eligible_since': None, 'replaces': replaces}
    E.write(JOURNAL, journal)
    monitor.event('submit_routed', **journal[jid])
    return jid


def migrate_pending(jobs, lanes, monitor, journal):
    """One-time adoption of an exact recorded list, only while still pending."""
    path = BASE / 'efficiency_adopt_pending.json'
    if not path.exists():
        return False
    adopted = read(path)
    by_name = {item['name']: item for item in lanes}
    done = monitor.state.setdefault('adopted_pending', {})
    for job in jobs:
        if job['id'] not in adopted or job['id'] in done:
            continue
        if adopted[job['id']] != job['name'] or job['state'] != 'PENDING' or job['qos'] != 'runfill':
            continue
        item = by_name.get(job['name'])
        if not item or item['state'] != 'ready' or not item['ready']:
            continue
        if 'A100' in job['partition'].split(','):
            done[job['id']] = 'already eligible for A100'
            continue
        cancel(['scancel', '--state=PENDING', job['id']])
        if any(j['id'] == job['id'] for j in E.query_jobs()):
            monitor.event('pending_race_preserved', job=job['id'])
            return False
        jid = launch(item, monitor, journal, replaces=job['id'])
        done[job['id']] = jid
        E.write(E.STATE, monitor.state)
        return True  # at most one reroute per minute, preserving queue stability
    return False


def fallback_pending(jobs, monitor, journal):
    now = time.time()
    for job in jobs:
        meta = journal.get(job['id'])
        if not meta:
            continue
        eligible = (job['state'] == 'PENDING' and job['reason'] in ('Resources', 'Priority')
                    and E.gpu_count(jobs) < 10)
        if eligible:
            if not meta.get('eligible_since'):
                meta['eligible_since'] = now
        else:
            meta['eligible_since'] = None
        if not E.pending_fallback(job, meta, jobs, now):
            continue
        monitor.state.setdefault('broad_until', {})[meta['lane']] = now + 3600
        E.write(E.STATE, monitor.state)
        result = E.replace_pending(job, meta, jobs, now, E.query_jobs, cancel, submit)
        if result:
            journal[result['id']] = result
            E.write(JOURNAL, journal)
            monitor.event('fast_wait_fallback', old_job=job['id'], **result)
            return True
    E.write(JOURNAL, journal)
    return False


def lane(key, overrides):
    if key != 'private':
        return Previous.lane(key, overrides)
    original = Previous.CONFIG[key]
    Previous.CONFIG[key] = CONFIG[key]
    try:
        item = Previous.lane(key, overrides)
    finally:
        Previous.CONFIG[key] = original
    if item['state'] == 'ready':
        item['submit'] = ['--job-name=c3_privscience', 'slurm/aln34_private_science_v2.sbatch',
                          '--max-units', '8', '--smoke-job', str(overrides[key])]
    return item


def plugin_lanes(path=PLUGIN_PATH):
    """Explicitly registered read-only readiness providers, isolated on failure."""
    if not path.exists():
        return []
    config = read(path)
    assert config['version'] == 1
    result = []
    for entry in config['plugins']:
        module = entry['module']
        assert module.startswith('auditory_alignment_v3.aln35.')
        assert all(part.isidentifier() for part in module.split('.'))
        try:
            provider = importlib.import_module(module)
            assert sha(provider.__file__) == entry['sha256'], 'frozen readiness provider changed'
            value = provider.fleet_status()
            values = value if isinstance(value, list) else [value]
            for item in values:
                assert item['name'].startswith('c3_s35') and item['lane'].startswith('s35_')
                assert 1 <= item['slots'] <= 2 and item['ready'] >= 0
                assert item.get('initial', []) == []
                if item['state'] == 'ready' and item['ready']:
                    command = item['submit']
                    assert isinstance(command,list) and all(isinstance(s,str) for s in command)
                    assert command[0].startswith('slurm/aln35_') and command[0].endswith('.sbatch')
                result.append(item)
        except Exception as exc:
            log('PLUGIN_ERROR ' + module + ': ' + repr(exc))
            result.append(dict(name=entry['name'],lane=entry['lane'],state='technical_error',
                               ready=0,remaining=None,slots=1,initial=[],error=repr(exc)))
    assert len({item['name'] for item in result}) == len(result), 'duplicate plugin lane names'
    return result


def main():
    assert os.environ.get('SLURM_JOB_ID')
    os.chdir(ROOT); os.umask(0o077)
    lock = (BASE / '.fleet_maintenance.lock').open('a+')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    assert (OUT / 'STOP_queue_v3_fm').exists()
    monitor = E.Monitor()
    journal = read(JOURNAL) if JOURNAL.exists() else {}
    turn = 0
    log('START ALN35: inherited monitoring plus new bounded comparisons; dependencies first; runfill GPU cap10')
    while not (NEWBASE / 'STOP_fleet_maintenance').exists():
        try:
            jobs = E.query_jobs()
            assert E.gpu_count(jobs) <= 10, 'GPU cap exceeded'
            renew_services(jobs, monitor)
            overrides = read(BASE / 'fleet_smoke_jobs.json')
            runtime = read(BASE / 'fleet_runtime.json')
            fm_slots = int(runtime.get('legacy_fm_slots', 2)); assert 1 <= fm_slots <= 3
            for key, value in runtime.get('extra_lanes', {}).items():
                assert key.startswith('breadth_') and len(value) == 5
                assert value[0].startswith('c3_') and '/' not in value[1] and 1 <= int(value[3]) <= 2
                CONFIG[key] = Previous.CONFIG[key] = tuple(value)
            keys = list(CONFIG); keys = keys[turn % len(keys):] + keys[:turn % len(keys)]; turn += 1
            lanes = [lane(k, overrides) for k in sorted(keys, key=lambda k: Priority.rank(k, keys.index(k)))]
            lanes.extend(plugin_lanes())
            lanes.sort(key=lambda item: Priority.rank(item['lane'], 0))
            fm = OUT / 'queue_v3_fm.txt'
            ids = [line.split('|')[0] for line in fm.read_text().splitlines() if line.strip()]
            ready = [eid for eid in ids if not (OUT/'units'/f'{eid}.json').exists()
                     and not (OUT/'pool/queue_v3_fm'/f'{eid}.failed').exists()
                     and not (OUT/'pool/queue_v3_fm'/f'{eid}.claim').exists()]
            lanes.insert(0, {'name': 'c3_aln3fm', 'lane': 'legacy_fm', 'state': 'ready', 'ready': len(ready),
                'slots': fm_slots, 'initial': [],
                'submit': ['--job-name=c3_aln3fm', '--nice=0', 'slurm/aln3_gpu_pool.sbatch', str(fm), '1', '1']})
            try:
                monitor.refresh(jobs, lanes)
                monitor.drain_prior_canary(jobs)
            except Exception as exc:
                monitor.event('monitor_error', error=repr(exc))
                # Stale routing data automatically widens; existing work continues.
            if (migrate_pending(jobs, lanes, monitor, journal)
                    or fallback_pending(jobs, monitor, journal) or monitor.fallback_prior(jobs)):
                jobs = E.query_jobs()
            project = [j for j in jobs if j['qos'] == 'runfill' and j['name'].startswith('c3_')]
            pending = sum(j['state'] == 'PENDING' for j in project)
            for item in lanes:
                active = [j for j in jobs if j['name'] == item['name'] or j['id'] in item.get('initial', [])]
                item['jobs'] = active
                if item['state'] == 'ready' and item['ready'] and len(active) < item['slots'] and pending < 12:
                    jid = launch(item, monitor, journal); pending += 1
                    jobs.append({'id': jid, 'name': item['name'], 'qos': 'runfill', 'state': 'PENDING'})
            E.write(BASE / 'fleet_status.json', {'time': E.stamp(), 'job': os.environ['SLURM_JOB_ID'],
                'source_sha256': sha(__file__), 'project_gpu_jobs': project, 'lanes': lanes})
            E.write(NEWBASE / 'fleet_status.json', {'time': E.stamp(), 'job': os.environ['SLURM_JOB_ID'],
                'source_sha256': sha(__file__), 'project_gpu_jobs': project, 'lanes': lanes})
            log('HEARTBEAT ' + json.dumps({item['name']: {k: item.get(k) for k in ('state', 'ready', 'remaining', 'failed')} for item in lanes}))
        except Exception as exc:
            log('ERROR ' + repr(exc))
        time.sleep(60)
    log('STOP ALN35')


if __name__ == '__main__':
    main()
