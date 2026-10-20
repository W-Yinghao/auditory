"""Slurm check for fleet v3: synthetic cap/tier tests plus a live no-submit dry run."""
import hashlib
import itertools
import json
import os
from pathlib import Path
import random

from private.auditory_alignment_v3.aln35 import maintain_fleet_v2 as V2
from private.auditory_alignment_v3.aln35 import maintain_fleet_v3 as V3

OUTDIR = Path(__file__).resolve().parent
V2_SHA = '311bcc8b1f73998ecfe5e926724fa69cd2e9cc0beb32944357cb89979ec75205'


def lane(name, key, slots, ready, initial=()):
    return {'name': name, 'lane': key, 'slots': slots, 'ready': ready, 'state': 'ready', 'initial': list(initial)}


def job(i, name, state='RUNNING'):
    return {'id': str(i), 'name': name, 'qos': 'runfill', 'state': state, 'gres': 'gres/gpu:1'}


def simulate(lanes, jobs, passes=12):
    jobs = list(jobs)
    for p in range(passes):
        for item in V3.select(lanes, jobs):
            jobs.append(job(f'n{p}{item["name"]}{len(jobs)}', item['name'], 'PENDING'))
        assert V3.committed(jobs) <= V3.CAP, 'cap violated'
    return jobs


def count(jobs, name):
    return sum(j['name'] == name for j in jobs)


def synthetic():
    out = {}
    lanes = [lane('c3_aln34budget', 'budget', 6, 54), lane('c3_datacurve34', 'curves', 6, 225, ['1044076']),
             lane('c3_br_budget', 'breadth_budget', 2, 16), lane('c3_br_curves', 'breadth_curves', 2, 102)]
    now = [job(1, 'c3_aln34budget'), job(1044076, 'c3_aln34split'), job(3, 'c3_br_budget'), job(4, 'c3_br_budget'),
           job(5, 'c3_br_curves'), job(6, 'c3_br_curves')]
    end = simulate(lanes, now)
    out['current'] = {n: count(end, n) for n in ('c3_aln34budget', 'c3_datacurve34', 'c3_br_budget', 'c3_br_curves')}
    assert out['current'] == {'c3_aln34budget': 3, 'c3_datacurve34': 2, 'c3_br_budget': 2, 'c3_br_curves': 2}, out
    assert V3.committed(end) == 10
    # Breadth keeps its base slot after a worker exits, although DTU lanes still have extended room.
    gone = [j for j in end if j['id'] != '3']
    assert V3.select(lanes, gone)[0]['name'] == 'c3_br_budget'
    # After breadth work is done, the DTU tails take the capacity.
    done = [dict(item, ready=0) if item['name'].startswith('c3_br_') else item for item in lanes]
    tail = simulate(done, [job(1, 'c3_aln34budget'), job(1044076, 'c3_aln34split')])
    out['after_breadth'] = {n: count(tail, n) for n in ('c3_aln34budget', 'c3_datacurve34')}
    assert out['after_breadth'] == {'c3_aln34budget': 5, 'c3_datacurve34': 4}, out
    assert V3.committed(tail) == 10
    # No more workers than unfinished units.
    few = [lane('c3_aln34budget', 'budget', 6, 2)]
    assert count(simulate(few, []), 'c3_aln34budget') == 2
    # Foreign jobs and other QoS never count; pending project jobs do.
    foreign = [{'id': 'x', 'name': 'v10e_x', 'qos': 'normal', 'state': 'RUNNING', 'gres': 'gres/gpu:1'},
               {'id': 'y', 'name': 'c3_privscience', 'qos': 'runfill', 'state': 'PENDING', 'gres': 'gres/gpu:1'}]
    assert V3.committed(foreign) == 1
    # Randomised invariant: never above the cap from any starting state at or below it.
    rng = random.Random(20261020)
    names = [l['name'] for l in lanes] + ['c3_aln34split']
    for trial in range(2000):
        start = [job(i, rng.choice(names), rng.choice(['RUNNING', 'PENDING'])) for i in range(rng.randint(0, 10))]
        rnd = [dict(item, ready=rng.randint(0, 8)) for item in lanes]
        simulate(rnd, start, passes=4)
    out['random_trials'] = 2000
    return out


def live():
    def refuse(*a, **k):
        raise AssertionError('dry run must not submit')
    V2.submit = refuse
    jobs = V2.E.query_jobs()
    lanes = V3.build_lanes(0)
    chosen = V3.select(lanes, jobs)
    tails = {i['name']: {k: i.get(k) for k in ('lane', 'state', 'ready', 'slots')} for i in lanes
             if i['lane'] in ('budget', 'curves', 'breadth_budget', 'breadth_curves')}
    return {'running_gpus': V2.E.gpu_count(jobs), 'committed_gpus': V3.committed(jobs),
            'first_pass_launches': [i['name'] for i in chosen], 'tail_lanes': tails,
            'not_ready': {i['name']: i['state'] for i in lanes if i['state'] not in ('ready', 'complete')}}


def main():
    assert os.environ.get('SLURM_JOB_ID')
    v2 = hashlib.sha256(Path(V2.__file__).read_bytes()).hexdigest()
    assert v2 == V2_SHA, 'v2 source changed'
    receipt = {'job': os.environ['SLURM_JOB_ID'], 'v2_sha256': v2,
               'v3_sha256': hashlib.sha256(Path(V3.__file__).read_bytes()).hexdigest(),
               'synthetic': synthetic(), 'live_dry_run': live(), 'status': 'pass'}
    (OUTDIR / f'check_{os.environ["SLURM_JOB_ID"]}.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
