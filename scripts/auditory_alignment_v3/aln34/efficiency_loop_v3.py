"""Operational monitoring and GPU placement; never changes a scientific row.

Runs inside the single Slurm fleet coordinator. New allocations may prefer fast
partitions; existing work is never killed. Timing comparisons are observational,
matched by workload, and exclude known resumes/probes/reused records.
"""
from collections import defaultdict, Counter
from datetime import datetime
import argparse
import json
import os
from pathlib import Path
import re
from statistics import median
import subprocess
import time

ROOT = Path('/home/infres/yinwang/EEG_auditory')
OUT = ROOT / 'private/auditory_alignment_v3'
BASE = OUT / 'aln34'
STATE = BASE / 'efficiency_state.json'
SHORT = {'science', 'private', 'prior_loo', 'prior_science'}
FAST = ('A100', 'L40S')
BROAD = ('A100', 'L40S', 'A40', 'A30', 'V100')
V100_POLICY = OUT / 'aln35/v100_20261019/compatibility.json'
FIELDS = ('id', 'name', 'qos', 'state', 'elapsed', 'left', 'partition',
          'node', 'reason', 'submitted', 'start', 'gres')


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    path = Path(path)
    tmp = path.with_name(path.name + '.tmp.' + str(os.getpid()))
    tmp.write_text(json.dumps(value, indent=2) + '\n')
    os.replace(tmp, path)


def stamp():
    return datetime.now().astimezone().isoformat()


def query_jobs():
    raw = subprocess.check_output(['squeue', '-u', os.environ['USER'], '-h', '-o',
        '%i|%j|%q|%T|%M|%L|%P|%N|%r|%V|%S|%b'], text=True, timeout=40)
    rows = [dict(zip(FIELDS, line.split('|'))) for line in raw.splitlines() if line]
    if any(len(line.split('|')) != len(FIELDS) for line in raw.splitlines() if line):
        raise ValueError('incomplete squeue response')
    return rows


def gpu_count(jobs):
    total = 0
    for j in jobs:
        if j['qos'] != 'runfill' or not j['name'].startswith('c3_'):
            continue
        if j['state'] not in ('RUNNING', 'CONFIGURING', 'COMPLETING'):
            continue
        counts = re.findall(r'(?:gres/)?gpu(?::[A-Za-z][A-Za-z0-9_-]*)?:(\d+)', j.get('gres', ''))
        if not counts:
            raise ValueError('cannot verify GPU request for ' + j['id'])
        total += sum(map(int, counts))
    return total


def hardware():
    raw = subprocess.check_output(['sinfo', '-N', '-h', '-p', ','.join(BROAD),
        '-o', '%N|%P|%t|%C|%m|%G'], text=True, timeout=40)
    rows = []
    for line in raw.splitlines():
        node, partition, state, cpus, mem, gres = line.split('|')
        rows.append(dict(node=node, partition=partition.rstrip('*'), state=state,
                         cpus=cpus, memory_mb=int(mem), gres=gres))
    # Mixed nodes are not counted as free GPUs. An idle node is only an
    # availability hint, not a reservation or a promised Slurm start time.
    idle = sorted({r['partition'] for r in rows if r['node'] != 'node52'
                   and r['state'] == 'idle' and r['memory_mb'] >= 65536
                   and int(r['cpus'].split('/')[1]) >= 12})
    return {'nodes': rows, 'idle_partitions': idle}


def device_class(name):
    for part in BROAD:
        if part in str(name):
            return part
    return str(name or 'unknown')


def source(row):
    if isinstance(row, dict):
        if 'spec' in row:
            return row
        for key in ('source', 'row', 'outer', 'inner', 'inner_source'):
            if isinstance(row.get(key), dict):
                return source(row[key])
    return row


def timing_sample(rec, row, lane):
    if (rec.get('status') != 'complete' or rec.get('probe') or rec.get('truncated')
            or rec.get('reused_from') or rec.get('resumed') or rec.get('resume_history')
            or rec.get('resumed_from_epoch')):
        return None
    seconds = rec.get('total_seconds', rec.get('seconds'))
    if not isinstance(seconds, (float, int)) or seconds <= 0:
        return None
    row = source(row)
    spec = row.get('spec', {})
    # Exact declared workload and completed budget. No test metric is read.
    key = [lane, row.get('dataset'), spec.get('architecture'), spec.get('adaptation'),
           spec.get('objective'), spec.get('readout'), spec.get('axis'), spec.get('fraction'),
           spec.get('stage'), spec.get('block'), spec.get('donor_set'),
           row.get('subject_fold'), row.get('content_fold'),
           rec.get('epochs_completed'), rec.get('optimizer_steps'), rec.get('steps_per_epoch')]
    if spec.get('stage') == 'donor_group':
        # Packed MPS concurrency and validation/extension work are not a
        # comparable single-card training-time benchmark.
        comparable = False
    else:
        comparable = rec.get('optimizer_steps') is not None
    return {'lane': lane, 'device': str(rec.get('device', 'unknown')),
            'partition': device_class(rec.get('device')), 'seconds': float(seconds),
            'key': json.dumps(key, sort_keys=True), 'comparable': comparable}


def timing_summary(samples):
    grouped = defaultdict(list)
    cells = defaultdict(lambda: defaultdict(list))
    for s in samples:
        grouped[s['lane'], s['partition']].append(s['seconds'])
        if s['comparable']:
            cells[s['key']][s['partition']].append(s['seconds'])
    comparisons = defaultdict(list)
    for key, by_device in cells.items():
        lane = json.loads(key)[0]
        for fast in FAST:
            for slow in ('A40', 'A30', 'V100'):
                # At least two observations per card in an exact workload cell.
                if len(by_device[fast]) >= 2 and len(by_device[slow]) >= 2:
                    comparisons[lane, fast, slow].append(median(by_device[slow]) / median(by_device[fast]))
    return {
        'by_lane_device': [{'lane': lane, 'partition': part, 'n': len(values),
                            'median_seconds': round(median(values), 1)}
                           for (lane, part), values in sorted(grouped.items())],
        'matched_speedups': [{'lane': lane, 'fast': fast, 'slow': slow,
                              'matched_cells': len(values), 'slow_over_fast': round(median(values), 3)}
                             for (lane, fast, slow), values in sorted(comparisons.items())],
        'limitations': 'Observational workload-matched times, not controlled speed tests; known resumes/reuse/probes excluded. Packed donor groups are descriptive only.'}


def collect_timings(cache):
    from auditory_alignment_v3 import core
    from private.auditory_alignment_v3.aln34.milestone_monitor_v11 import LANES
    wanted = []
    rows = core.load_rows() + [json.loads(line) for line in (OUT / 'plan_ext.jsonl').read_text().splitlines() if line]
    for row in rows:
        if row['family_id'] == 'ALN32_TRUE_FULL':
            wanted.append(('legacy_fm', row, OUT / 'units'))
        elif row.get('spec', {}).get('execution_contract') == 'aln33_env64_125ms_v1':
            wanted.append(('prior', row, OUT / 'units'))
    for dirname in LANES:
        plan = read(BASE / dirname / 'plan.json')
        aliases = {'learning_budget_v2':'budget', 'adaptation_policy_v1':'adapt', 'strong_fusion_v1':'fusion',
                   'episode_training_v1':'episode', 'content_time_v1':'science', 'private_current_time_v2':'private',
                   'breadth_budget_v1':'breadth_budget', 'breadth_policy_v1':'breadth_adapt',
                   'breadth_fusion_v1':'breadth_fusion', 'breadth_episode_v1':'breadth_episode',
                   'private_episode_v2':'private_episode', 'cb_auditory_v1':'cb_auditory',
                   'attention_transfer_v1':'attention', 'private_cb_factorial_v1':'private_factorial',
                   'prior_private_loo_v1':'prior_loo', 'prior_science_v1':'prior_science', 'cs_episode_v1':'cs_episode'}
        for row in plan['rows']:
            if dirname in ('data_inner_v1', 'breadth_inner_v1'):
                lane = ('breadth_' if dirname.startswith('breadth_') else '') + ('inner' if row['spec']['axis']=='inner_person' else 'curves')
            else:
                lane = aliases[dirname]
            wanted.append((lane, row, BASE / dirname / 'units'))
    samples = []
    for lane, row, directory in wanted:
        eid = row.get('experiment_id', row.get('id'))
        path = directory / (eid + '.json')
        if not path.is_file():
            continue
        stat = path.stat(); signature = (stat.st_mtime_ns, stat.st_size)
        old = cache.get(str(path))
        if not old or old[0] != signature:
            cache[str(path)] = (signature, timing_sample(read(path), row, lane))
        if cache[str(path)][1]:
            samples.append(cache[str(path)][1])
    return timing_summary(samples)


def v100_allowed(lane):
    """Require a V100 probe with measured allocation below the 16GB budget."""
    if lane in ('prior', 'legacy_fm'):
        return True  # Previously allowed and production-verified.
    try:
        import hashlib
        policy = read(V100_POLICY)
        entry = policy['allowed_lanes'][lane]
        phase = next(p for p in policy['phases'] if p['phase'] == entry['phase'])
        if phase['status'] != 'pass' or 'V100' not in policy['device']:
            return False
        for key, expected in (('receipt', 'receipt_sha256'), ('module_source', 'module_sha256'), ('plan', 'plan_sha256')):
            if hashlib.sha256(Path(entry[key]).read_bytes()).hexdigest() != entry[expected]:
                return False
        return read(entry['receipt'])['status'] == 'pass'
    except (OSError, ValueError, KeyError, TypeError, StopIteration):
        return False


def route(lane, status, now=None, force_broad=False, oom_only=False):
    now = time.time() if now is None else now
    broad = [p for p in BROAD if p != 'V100'] + (['V100'] if v100_allowed(lane) and not oom_only else [])
    fast = [part for part in FAST if part in status.get('hardware', {}).get('idle_partitions', [])]
    fresh = 0 <= now - status.get('epoch', 0) <= 900
    blocked = status.get('broad_until', {}).get(lane, 0) > now
    adverse = any(c['lane'] == lane and c['matched_cells'] >= 2 and c['slow_over_fast'] < 0.9
                  for c in status.get('timing', {}).get('matched_speedups', []))
    if fresh and fast and lane not in SHORT and not force_broad and not blocked and not adverse:
        parts, reason = list(FAST), 'fast capacity observed; production placement trial or matched timing support'
    else:
        parts, reason = broad, 'broad eligibility: short work, wait fallback, stale availability or insufficient fast capacity'
    return {'partitions': parts, 'reason': reason, 'time': '24:00:00'}


def route_args(decision):
    assert set(decision['partitions']) <= set(BROAD) | {'V100'}
    return ['--partition=' + ','.join(decision['partitions']), '--time=24:00:00']


def pending_fallback(job, meta, all_jobs, now):
    if not meta or job['state'] != 'PENDING' or job['qos'] != 'runfill':
        return False
    if job['id'] != meta['id'] or job['name'] != meta['name'] or meta.get('fallback'):
        return False
    if set(job['partition'].split(',')) - set(FAST):
        return False
    # A full per-user quota is not a wait for a fast GPU; keep queue age then.
    if job['reason'] not in ('Resources', 'Priority') or gpu_count(all_jobs) >= 10:
        return False
    return now - (meta.get('eligible_since') or now) >= 1200


def replace_pending(job, meta, all_jobs, now, get_jobs, cancel, submit):
    if not pending_fallback(job, meta, all_jobs, now):
        return None
    # Race-safe: state-filtered cancellation, then independent absence check.
    cancel(['scancel', '--state=PENDING', job['id']])
    if any(j['id'] == job['id'] for j in get_jobs()):
        return None
    decision = route(meta['lane'], {}, now, force_broad=True)
    jid = submit([*route_args(decision), *meta['base_command']])
    return dict(meta, id=jid, submitted_epoch=now, fallback=True, decision=decision,
                replaces=job['id'], eligible_since=None)


def normal_slots(jobs):
    count = 0
    for j in jobs:
        if j['qos'] != 'normal':
            continue
        match = re.search(r'_\[(\d+)-(\d+)(?:%\d+)?\]', j['id'])
        if '[' in j['id'] and not match:
            return 30  # unknown compressed-array syntax: do not over-submit
        count += int(match[2]) - int(match[1]) + 1 if match else 1
    return count


class Monitor:
    def __init__(self):
        self.state = read(STATE) if STATE.exists() else {}
        self.last = 0
        self.last_timing = 0
        self.last_hour = 0
        self.cache = {}

    def event(self, kind, **values):
        value = {'time': stamp(), 'kind': kind, **values}
        with (BASE / 'efficiency_actions.jsonl').open('a') as handle:
            handle.write(json.dumps(value) + '\n')
        print('EFFICIENCY', json.dumps(value), flush=True)

    def refresh(self, jobs, lanes, force=False):
        now = time.time()
        if not force and now - self.last < 300:
            return self.state
        self.last = now
        hw = hardware()
        if now - self.last_timing >= 1800:
            self.state['timing'] = collect_timings(self.cache)
            self.last_timing = now
        project = [j for j in jobs if j['qos'] == 'runfill' and j['name'].startswith('c3_')]
        alerts = [f"{l['lane']}: {l['state']} ({l.get('failed', 0)} failures)"
                  for l in lanes if l.get('state') in ('technical_failure', 'engineering_plan_mismatch', 'engineering_code_mismatch')]
        milestone = BASE / 'milestone_state.json'
        progress = read(milestone) if milestone.exists() else {}
        for filename, limit in [('milestone_state.json', 7200), ('fleet_status.json', 600)]:
            path = BASE / filename
            if not path.exists() or now - path.stat().st_mtime > limit:
                alerts.append('stale service artifact: ' + filename)
        alerts.extend(str(e) for e in progress.get('errors', []))
        self.state.update(epoch=now, time=stamp(), job=os.environ.get('SLURM_JOB_ID'),
                          hardware=hw, gpu_count=gpu_count(jobs), queue=project,
                          progress=progress.get('counts', {}), alerts=alerts,
                          pending_reasons=dict(Counter(j['reason'] for j in project if j['state'] == 'PENDING')))
        write(STATE, self.state)
        lines = ['# 实验效率监控', '', f"更新时间：{self.state['time']}；Slurm loop：{self.state['job']}", '',
                 f"运行 GPU：{self.state['gpu_count']}/10；待运行：{sum(j['state']=='PENDING' for j in project)}。",
                 f"空闲节点所在分区：{', '.join(hw['idle_partitions']) or '未观察到'}（不保证排队开始时间）。", '',
                 '每分钟维护队列；每 5 分钟检查资源/异常；每 30 分钟刷新运行耗时；每小时保留进展快照。',
                 '长任务优先试用 A100/L40S；通过 V100 实测及 16GB 显存预算检查的队列可回退到 V100。达到 10 卡上限时不反复重排。',
                 '运行中的训练不会被取消。公共先验最多进行一次无中断换卡试运行；继续换卡须有实际匹配吞吐证据。', '',
                 '| 实验 | 已完成/登记 |', '|---|---|']
        lines += [f'| {key} | {value[0]}/{value[1]} |' for key, value in self.state['progress'].items()]
        lines += ['', '异常：' + ('；'.join(alerts) if alerts else '当前未发现已记录的异常'), '',
                  '实际换卡、回退和接续记录：`efficiency_actions.jsonl`。训练结果解释仍以完整配对汇总为准。',
                  '这是 Slurm 上的规则监控循环；不会在聊天会话关闭后自动产生新的模型研究推理。', '']
        (BASE / 'EFFICIENCY_LOOP_STATUS.md').write_text('\n'.join(lines))
        if now - self.last_hour >= 3600:
            with (BASE / 'efficiency_hourly.jsonl').open('a') as handle:
                handle.write(json.dumps({k: self.state[k] for k in ('time', 'job', 'gpu_count', 'progress', 'alerts', 'pending_reasons')}) + '\n')
            self.last_hour = now
        self.event('heartbeat', gpu_count=self.state['gpu_count'], pending=sum(j['state']=='PENDING' for j in project), alerts=alerts)
        return self.state

    def drain_prior_canary(self, jobs):
        """One allocation-boundary trial; no loss, no mid-unit resumption."""
        if self.state.get('prior_canary_drain'):
            return
        if route('prior', self.state)['partitions'] != list(FAST):
            return
        keepers = [j for j in jobs if j['name'] == 'c3_p33keeper' and j['state'] == 'RUNNING']
        # Require the upgraded keeper's verified receipt before draining.
        receipt = BASE / 'efficiency_prior_keeper.json'
        if not receipt.exists() or not any(j['id'] == read(receipt)['job'] for j in keepers):
            return
        prior = [j for j in jobs if j['name'] == 'c3_aln3pr' and j['qos'] == 'runfill']
        if any(j['state'] == 'PENDING' for j in prior):
            return
        candidates = [j for j in prior if j['state'] == 'RUNNING' and j['partition'] in ('V100', 'A30', 'A40')]
        pool = OUT / 'pool/queue_v3_prior'
        candidates = [j for j in candidates if not (pool / ('.infra_' + j['id'])).exists()]
        if not candidates:
            return
        owned = read(receipt).get('adopted_workers', [])
        candidates = [j for j in candidates if j['id'] in owned]
        if not candidates:
            return
        claims = Counter()
        for path in pool.glob('*.claim/job'):
            try:
                claims[path.read_text().strip()] += 1
            except OSError:
                continue
        selected = min(candidates, key=lambda j: (claims[j['id']], int(j['id'])))
        marker = pool / ('.infra_' + selected['id'])
        marker.write_text('Authorized efficiency rotation: finish all current units, then release allocation. Not a scientific failure.\n')
        self.state['prior_canary_drain'] = {'job': selected['id'], 'time': stamp(), 'active_claims': claims[selected['id']]}
        write(STATE, self.state)
        self.event('drain_prior_at_unit_boundary', **self.state['prior_canary_drain'])

    def fallback_prior(self, jobs):
        # The prior keeper owns its submissions. Cancel at most one pending
        # fast-only job and let that same keeper refill it with wider routing.
        # This avoids two submitters racing past the prior's four-worker limit.
        receipt = BASE / 'efficiency_prior_keeper.json'
        if not receipt.exists():
            return False
        info = read(receipt)
        if not any(j['id'] == info['job'] and j['state'] == 'RUNNING' for j in jobs):
            return False
        now = time.time()
        clocks = self.state.setdefault('prior_wait_clocks', {})
        for job in jobs:
            if job['name'] != 'c3_aln3pr' or job['qos'] != 'runfill' or job['state'] != 'PENDING':
                continue
            if job['id'] in info.get('adopted_workers', []):
                continue
            if set(job['partition'].split(',')) - set(FAST):
                continue
            if job['reason'] not in ('Resources', 'Priority') or gpu_count(jobs) >= 10:
                clocks.pop(job['id'], None)
                continue
            clocks.setdefault(job['id'], now)
            if now - clocks[job['id']] < 1200:
                continue
            self.state.setdefault('broad_until', {})['prior'] = now + 3600
            write(STATE, self.state)
            subprocess.run(['scancel', '--state=PENDING', job['id']], check=True, timeout=40)
            absent = not any(j['id'] == job['id'] for j in query_jobs())
            self.event('prior_fast_wait_fallback', job=job['id'], absent=absent,
                       refill='existing prior keeper; running allocations preserved')
            return absent
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--prior-args', action='store_true')
    ap.add_argument('--oom-only', action='store_true')
    ap.add_argument('--keeper-start', action='store_true')
    a = ap.parse_args()
    assert os.environ.get('SLURM_JOB_ID'), 'Slurm required'
    if a.prior_args:
        state = read(STATE) if STATE.exists() else {}
        print('\n'.join(route_args(route('prior', state, oom_only=a.oom_only))))
    if a.keeper_start:
        jobs = query_jobs()
        write(BASE / 'efficiency_prior_keeper.json', {'job': os.environ['SLURM_JOB_ID'], 'time': stamp(),
              'version': 2, 'adopted_workers': [j['id'] for j in jobs if j['qos']=='runfill' and j['name']=='c3_aln3pr']})


if __name__ == '__main__':
    main()
