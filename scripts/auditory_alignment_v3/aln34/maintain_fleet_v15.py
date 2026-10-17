"""One fleet authority plus a five-minute efficiency loop; Slurm only."""
import fcntl
import json
import os
from pathlib import Path
import subprocess
import time

from private.auditory_alignment_v3.aln34 import maintain_fleet_v14 as Previous
from private.auditory_alignment_v3.aln34 import priority_schedule as Priority
from private.auditory_alignment_v3.aln34 import efficiency_loop as E

ROOT, OUT, BASE = E.ROOT, E.OUT, E.BASE
CONFIG = dict(Previous.CONFIG)
read, log, sha = Previous.read, Previous.log, Previous.sha
JOURNAL = BASE / 'efficiency_jobs.json'


def submit(command):
    jid = subprocess.check_output(['sbatch', '--parsable', *command], text=True, timeout=60).strip().split(';')[0]
    if not jid.isdigit():
        raise RuntimeError('non-numeric sbatch receipt: ' + jid)
    with (OUT / 'logs/operations.log').open('a') as handle:
        handle.write(f'{E.stamp()} fleet v15 {os.environ["SLURM_JOB_ID"]} submitted {jid}: {command}\n')
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
        jid = submit(['--dependency=afterany:' + current, 'slurm/aln34_maintain_fleet_v15.sbatch'])
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


def main():
    assert os.environ.get('SLURM_JOB_ID')
    os.chdir(ROOT); os.umask(0o077)
    lock = (BASE / '.fleet_maintenance.lock').open('a+')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    assert (OUT / 'STOP_queue_v3_fm').exists()
    monitor = E.Monitor()
    journal = read(JOURNAL) if JOURNAL.exists() else {}
    turn = 0
    log('START v15: 60s queue / 300s efficiency / 1800s timing / 3600s history; runfill GPU cap10')
    while not (BASE / 'STOP_fleet_maintenance_v15').exists():
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
            lanes = [Previous.lane(k, overrides) for k in sorted(keys, key=lambda k: Priority.rank(k, keys.index(k)))]
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
            log('HEARTBEAT ' + json.dumps({item['name']: {k: item.get(k) for k in ('state', 'ready', 'remaining', 'failed')} for item in lanes}))
        except Exception as exc:
            log('ERROR ' + repr(exc))
        time.sleep(60)
    log('STOP v15')


if __name__ == '__main__':
    main()
