"""Run existing bounded engineering probes on V100; open lanes as they pass."""
from datetime import datetime
import hashlib
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

import torch

ROOT = Path('/home/infres/yinwang/EEG_auditory')
OUT = ROOT / 'private/auditory_alignment_v3'
BASE = OUT / 'aln35/v100_20261019'
POLICY = BASE / 'compatibility.json'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.tmp.' + str(os.getpid()))
    temporary.write_text(json.dumps(value, indent=2) + '\n')
    os.replace(temporary, path)


def main():
    assert os.environ.get('SLURM_JOB_ID') and torch.cuda.is_available()
    os.umask(0o077)
    job = os.environ['SLURM_JOB_ID']
    qos = subprocess.check_output(['squeue', '-j', job, '-h', '-o', '%q'], text=True).strip()
    assert qos == 'runfill'
    device = torch.cuda.get_device_properties(0)
    assert 'V100' in device.name
    # Exercise the smaller card, rather than infer 16GB safety from a 32GB run.
    assert device.total_memory < 18 * 2**30
    phases = [
        ('matched', 'auditory_alignment_v3.aln35.matched_updates', ['--smoke'], ['s35_matched']),
        ('episode', 'auditory_alignment_v3.aln35.episode_pressure', ['--smoke'], ['s35_episode']),
        ('curves', 'auditory_alignment_v3.aln34.data_inner', ['--smoke'], ['curves']),
        ('adapt', 'auditory_alignment_v3.aln34.adaptation_policy',
         ['--probe-root', str(OUT / 'aln34/data_inner_v1/probes' / job)], ['adapt']),
        ('budget', 'auditory_alignment_v3.aln34.learning_budget_v2', ['--smoke'], ['budget']),
        ('breadth_budget', 'auditory_alignment_v3.aln34.breadth_budget', ['--smoke'], ['breadth_budget']),
        ('breadth_curves', 'auditory_alignment_v3.aln34.breadth_inner', ['--smoke'], ['breadth_curves']),
    ]
    source_paths = [Path(__file__)]
    plans = {}
    for _, name, _, _ in phases:
        module = importlib.import_module(name)
        source_paths.append(Path(module.__file__))
        plans[name] = {'path': str(module.PLAN), 'sha256': sha(module.PLAN)}
    baseline = {str(path): sha(path) for path in source_paths}
    record = {'version': 1, 'status': 'running', 'job': job,
              'created': datetime.now().astimezone().isoformat(),
              'device': device.name, 'memory_bytes': device.total_memory,
              'source_sha256': baseline, 'plans': plans, 'allowed_lanes': {}, 'phases': []}
    write(POLICY, record)
    for label, name, arguments, lanes in phases:
        started = time.time()
        module = importlib.import_module(name)
        path = module.BASE / 'probes' / job / 'receipt.json'
        phase = {'phase': label, 'module': name, 'status': 'running', 'receipt': str(path)}
        record['phases'].append(phase)
        write(POLICY, record)
        print(datetime.now().astimezone().isoformat(), 'START', label, flush=True)
        try:
            subprocess.run([sys.executable, '-B', '-u', '-m', name, *arguments], check=True)
            receipt = json.loads(path.read_text())
            assert receipt['status'] == 'pass'
            assert all(sha(p) == value for p, value in baseline.items()), 'frozen source changed'
            assert all(sha(v['path']) == v['sha256'] for v in plans.values()), 'frozen plan changed'
            phase.update(status='pass', seconds=time.time() - started, receipt_sha256=sha(path),
                         unit_count=len(receipt['units']))
            for lane in lanes:
                record['allowed_lanes'][lane] = {'phase': label, 'receipt': str(path),
                    'receipt_sha256': sha(path), 'module_source': str(Path(module.__file__)),
                    'module_sha256': sha(module.__file__), 'plan': str(module.PLAN), 'plan_sha256': sha(module.PLAN)}
            print('PASS', label, phase['unit_count'], round(phase['seconds'], 1), flush=True)
        except BaseException:
            phase.update(status='failed', seconds=time.time() - started, traceback=traceback.format_exc())
            record['status'] = 'partial_failure'
            write(POLICY, record)
            raise
        write(POLICY, record)
    record['status'] = 'pass'
    record['finished'] = datetime.now().astimezone().isoformat()
    write(POLICY, record)
    print('V100 COMPATIBILITY PASS', sorted(record['allowed_lanes']), flush=True)


if __name__ == '__main__':
    main()
