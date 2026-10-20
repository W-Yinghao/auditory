"""ALN3.5 fleet v3: the v2 authority with tiered tail concurrency; Slurm only.

Operational change only. v2, v14, trainers, plans and rows are imported unchanged.
- DTU budget/curves base slots 1 -> 3; breadth lanes keep their runtime slots.
- Base slots of every lane are filled before any lane uses extended slots, so the
  DTU tails absorb capacity only after breadth work stops needing it.
- Hard cap on project runfill GPUs counted running plus pending (v2 counted running).
- A lane never holds more workers than it has unfinished units (no empty rotations).
"""
import fcntl
import json
import os
import re
import time

from private.auditory_alignment_v3.aln35 import maintain_fleet_v2 as V2

E, Previous, Priority = V2.E, V2.Previous, V2.Priority
ROOT, OUT, BASE, NEWBASE = V2.ROOT, V2.OUT, V2.BASE, V2.NEWBASE
read, log, sha = V2.read, V2.log, V2.sha
CAP = 10
MAX_PENDING = 12
BASE_SLOTS = {'budget': 3, 'curves': 3}
EXTENDED_SLOTS = {'budget': 6, 'curves': 6}
SBATCH = 'slurm/aln35_maintain_fleet_v3.sbatch'
STOP = NEWBASE / 'STOP_fleet_maintenance_v3'
GPU_RE = re.compile(r'(?:gres/)?gpu(?::[A-Za-z][A-Za-z0-9_-]*)?:(\d+)')

# Process-local configuration, as in v2.
for _key, _slots in EXTENDED_SLOTS.items():
    _value = list(Previous.CONFIG[_key]); _value[3] = _slots
    V2.CONFIG[_key] = Previous.CONFIG[_key] = tuple(_value)


def project(jobs):
    return [j for j in jobs if j.get('qos') == 'runfill' and j.get('name', '').startswith('c3_')]


def committed(jobs):
    """GPUs held or requested by project runfill jobs; an unparsable request counts as 1."""
    total = 0
    for j in project(jobs):
        counts = GPU_RE.findall(j.get('gres', ''))
        total += sum(map(int, counts)) if counts else 1
    return total


def active(item, jobs):
    return [j for j in jobs if j['name'] == item['name'] or j['id'] in item.get('initial', [])]


def limit(item, tier):
    if tier == 'base':
        return min(item['slots'], BASE_SLOTS.get(item['lane'], item['slots']))
    return item['slots']


def select(lanes, jobs, cap=CAP, max_pending=MAX_PENDING):
    """Lanes to launch this pass, in order; at most one launch per lane per tier."""
    jobs = list(jobs)
    pending = sum(j['state'] == 'PENDING' for j in project(jobs))
    chosen = []
    for tier in ('base', 'extended'):
        for item in lanes:
            if item['state'] != 'ready' or not item['ready']:
                continue
            n = len(active(item, jobs))
            if n >= limit(item, tier) or n >= item['ready']:
                continue
            if pending >= max_pending or committed(jobs) >= cap:
                return chosen
            chosen.append(item); pending += 1
            jobs.append({'id': f'planned-{len(chosen)}', 'name': item['name'], 'qos': 'runfill',
                         'state': 'PENDING', 'gres': 'gres/gpu:1'})
    return chosen


def build_lanes(turn):
    """The v2 lane list for one pass (read-only)."""
    overrides = read(BASE / 'fleet_smoke_jobs.json')
    runtime = read(BASE / 'fleet_runtime.json')
    fm_slots = int(runtime.get('legacy_fm_slots', 2)); assert 1 <= fm_slots <= 3
    for key, value in runtime.get('extra_lanes', {}).items():
        assert key.startswith('breadth_') and len(value) == 5
        assert value[0].startswith('c3_') and '/' not in value[1] and 1 <= int(value[3]) <= 2
        V2.CONFIG[key] = Previous.CONFIG[key] = tuple(value)
    keys = list(V2.CONFIG); keys = keys[turn % len(keys):] + keys[:turn % len(keys)]
    lanes = [V2.lane(k, overrides) for k in sorted(keys, key=lambda k: Priority.rank(k, keys.index(k)))]
    lanes.extend(V2.plugin_lanes())
    lanes.sort(key=lambda item: Priority.rank(item['lane'], 0))
    fm = OUT / 'queue_v3_fm.txt'
    ids = [line.split('|')[0] for line in fm.read_text().splitlines() if line.strip()]
    ready = [eid for eid in ids if not (OUT/'units'/f'{eid}.json').exists()
             and not (OUT/'pool/queue_v3_fm'/f'{eid}.failed').exists()
             and not (OUT/'pool/queue_v3_fm'/f'{eid}.claim').exists()]
    lanes.insert(0, {'name': 'c3_aln3fm', 'lane': 'legacy_fm', 'state': 'ready', 'ready': len(ready),
        'slots': fm_slots, 'initial': [],
        'submit': ['--job-name=c3_aln3fm', '--nice=0', 'slurm/aln3_gpu_pool.sbatch', str(fm), '1', '1']})
    return lanes


def renew_services(jobs, monitor):
    """v2 renewal with this version's entry point and its own renewal record."""
    if E.normal_slots(jobs) > 27:
        return
    Previous.renew_offload(jobs)
    current = os.environ['SLURM_JOB_ID']
    own = next((j for j in jobs if j['id'] == current), None)
    if not own:
        return
    left = Previous.seconds_left(own['left'])
    renewal = monitor.state.get('renewal_v3', {})
    if left is not None and 0 < left <= 3600 and renewal.get('parent') != current:
        jid = V2.submit(['--dependency=afterany:' + current, SBATCH])
        monitor.state['renewal_v3'] = {'parent': current, 'job': jid}
        E.write(E.STATE, monitor.state)
        monitor.event('renew_loop', parent=current, job=jid)
        return
    receipt = BASE / 'efficiency_prior_keeper.json'
    if receipt.exists() and not (BASE / 'STOP_keeper_prior_v2').exists():
        prior = read(receipt)
        keeper = next((j for j in jobs if j['id'] == prior['job'] and j['state'] == 'RUNNING'), None)
        if keeper:
            left = Previous.seconds_left(keeper['left'])
            previous = monitor.state.get('prior_keeper_renewal', {})
            if left is not None and 0 < left <= 3600 and previous.get('parent') != keeper['id']:
                jid = V2.submit(['--dependency=afterany:' + keeper['id'], 'slurm/aln34_prior_keeper_v2.sbatch'])
                monitor.state['prior_keeper_renewal'] = {'parent': keeper['id'], 'job': jid}
                E.write(E.STATE, monitor.state)
                monitor.event('renew_prior_keeper', parent=keeper['id'], job=jid)


def main():
    assert os.environ.get('SLURM_JOB_ID')
    os.chdir(ROOT); os.umask(0o077)
    lock = (BASE / '.fleet_maintenance.lock').open('a+')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    assert (OUT / 'STOP_queue_v3_fm').exists()
    monitor = E.Monitor()
    journal = read(V2.JOURNAL) if V2.JOURNAL.exists() else {}
    turn = 0
    log(f'START ALN35 v3: base {BASE_SLOTS}, extended {EXTENDED_SLOTS}, committed runfill GPU cap {CAP}')
    while not STOP.exists():
        try:
            jobs = E.query_jobs()
            assert E.gpu_count(jobs) <= CAP, 'GPU cap exceeded'
            renew_services(jobs, monitor)
            lanes = build_lanes(turn); turn += 1
            try:
                monitor.refresh(jobs, lanes)
                monitor.drain_prior_canary(jobs)
            except Exception as exc:
                monitor.event('monitor_error', error=repr(exc))
            if (V2.migrate_pending(jobs, lanes, monitor, journal)
                    or V2.fallback_pending(jobs, monitor, journal) or monitor.fallback_prior(jobs)):
                jobs = E.query_jobs()
            for item in select(lanes, jobs):
                jid = V2.launch(item, monitor, journal)
                jobs.append({'id': jid, 'name': item['name'], 'qos': 'runfill', 'state': 'PENDING',
                             'gres': 'gres/gpu:1'})
            for item in lanes:
                item['jobs'] = active(item, jobs)
            status = {'time': E.stamp(), 'job': os.environ['SLURM_JOB_ID'], 'version': 'v3',
                      'source_sha256': sha(__file__), 'committed_gpus': committed(jobs),
                      'project_gpu_jobs': project(jobs), 'lanes': lanes}
            E.write(BASE / 'fleet_status.json', status)
            E.write(NEWBASE / 'fleet_status.json', status)
            log('HEARTBEAT ' + json.dumps({item['name']: {k: item.get(k) for k in ('state', 'ready', 'remaining', 'failed')}
                                            for item in lanes}))
        except Exception as exc:
            log('ERROR ' + repr(exc))
        time.sleep(60)
    log('STOP ALN35 v3')


if __name__ == '__main__':
    main()
