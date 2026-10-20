"""Bounded Slurm runtime snapshot; no training, fitting, or checkpoint loading."""
from datetime import datetime
import json
import os
from pathlib import Path
import statistics
import subprocess

ROOT = Path('/home/infres/yinwang/EEG_auditory')
OUT = ROOT / 'private/auditory_alignment_v3'
BASE = OUT / 'aln35/runtime_20261019_evening'


def read(path):
    return json.loads(path.read_text())


def call(args):
    return subprocess.check_output(args, text=True, timeout=45).splitlines()


def compact_families(obj):
    rows = []
    for f in obj.get('families', []):
        rows.append({
            'family': f.get('family_id'), 'status': f.get('status'),
            'coverage': {k: {n: v.get(n) for n in ('common_complete_n', 'expected_n')}
                         for k, v in f.get('coverage', {}).items()},
            'contrasts': [{k: c.get(k) for k in ('id', 'estimate', 'simultaneous_ci', 'status')}
                          for c in f.get('contrasts', [])],
        })
    return rows


def main():
    job = os.environ['SLURM_JOB_ID']
    os.umask(0o077)
    BASE.mkdir(parents=True, exist_ok=True)
    fleet = read(OUT / 'aln35/fleet_status.json')
    milestone = read(OUT / 'aln34/milestone_state.json')
    evidence = read(OUT / 'aln35/evidence/state.json')
    support = read(OUT / 'aln35/support_summary_v1/latest.json')
    timings = {}
    for key, directory in {
        'cb_auditory': 'aln34/cb_auditory_v1',
        'episode35': 'aln35/episode_pressure_v1',
        'matched35': 'aln35/matched_updates_v1',
        'budget': 'aln34/learning_budget_v2',
        'breadth_budget': 'aln34/breadth_budget_v1',
        'curves': 'aln34/data_inner_v1',
        'breadth_curves': 'aln34/breadth_inner_v1',
    }.items():
        root = OUT / directory
        values = []
        schemas = []
        for p in sorted((root / 'units').glob('*.json')):
            if p.name.endswith('.FAILED.json'):
                continue
            r = read(p)
            if r.get('status') != 'complete':
                continue
            if len(schemas) < 1:
                schemas.append({k: r[k] for k in r if any(s in k.lower() for s in ('time', 'second', 'wall', 'duration', 'gpu', 'device'))})
            for field in ('wall_seconds', 'elapsed_seconds', 'seconds', 'runtime_seconds'):
                if isinstance(r.get(field), (int, float)) and r[field] > 0:
                    values.append({'id': p.stem, 'seconds': r[field], 'field': field})
                    break
        timings[key] = {'n': len(values), 'sample_time_fields': schemas,
                        'median_seconds': statistics.median(v['seconds'] for v in values) if values else None,
                        'max_seconds': max((v['seconds'] for v in values), default=None),
                        'slowest': sorted(values, key=lambda v: v['seconds'], reverse=True)[:5]}
    fs = os.statvfs('/projects/EEG-foundation-model')
    result = {
        'status': 'complete', 'job': job, 'time': datetime.now().astimezone().isoformat(),
        'project_jobs': [x for x in call(['squeue', '-u', 'yinwang', '-h', '-o', '%i|%j|%q|%T|%M|%P|%r|%b']) if '|c3_' in x],
        'milestone': milestone,
        'lanes': [{k: l.get(k) for k in ('name', 'lane', 'state', 'ready', 'remaining', 'total', 'failed', 'slots')}
                  for l in fleet['lanes']],
        'evidence': evidence, 'support_analysis_snapshot': support,
        'runtime_samples': timings,
        'projects_available_gib': fs.f_bavail * fs.f_frsize / 2**30,
        'retired_services_stop_marker_present': (OUT / 'STOP_ckpt_offload').exists(),
    }
    path = BASE / f'snapshot_{job}.json'
    path.write_text(json.dumps(result, indent=2) + '\n')
    for name, run in [('fusion', '1047619'), ('attention', '1049394')]:
        source = ROOT / f'results/auditory_alignment_v3/aln35/{name}/run_{run}/contrasts.json'
        obj = read(source)
        (BASE / f'{name}_compact_{job}.json').write_text(json.dumps(compact_families(obj), indent=2) + '\n')
    print(json.dumps({'job': job, 'status': 'complete', 'snapshot': str(path),
                      'projects_available_gib': result['projects_available_gib'],
                      'runtime_samples': timings}, indent=2))


if __name__ == '__main__':
    main()
