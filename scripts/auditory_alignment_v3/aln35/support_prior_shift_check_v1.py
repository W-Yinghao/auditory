"""Why private C10/H10 probability-only calibration loses NLL (Slurm only; reads existing records).

Aggregates, per support condition, the support deviant fraction and the selected temperature of the
probability-only method across all private support units and children. No refit; no identities written.
"""
import collections
import glob
import hashlib
import json
import os
from pathlib import Path

ROOT = Path('/home/infres/yinwang/EEG_auditory')
UNITS = ROOT / 'private/auditory_alignment_v3/aln35/support_coverage_v1/units'
OUT = ROOT / 'results/auditory_alignment_v3/aln35/support_prior_shift_check_v1'


def main():
    assert os.environ.get('SLURM_JOB_ID'), 'run under Slurm'
    stats = collections.defaultdict(lambda: collections.defaultdict(list))
    units = 0
    for path in sorted(glob.glob(str(UNITS / '*.json'))):
        if path.endswith('.FAILED.json'):
            continue
        rec = json.loads(Path(path).read_text())
        people = rec.get('per_participant', {})
        if rec.get('status') != 'complete' or rec.get('probe') or not people:
            continue
        if 'H10' not in next(iter(people.values()))['conditions']:
            continue  # DTU units have no H10; this check targets the private cohort
        units += 1
        arch = rec['unit'].get('architecture') or rec['unit'].get('configuration') or 'unknown'
        for person in people.values():
            for cond, c in person.get('conditions', {}).items():
                key = 'U10' if cond.startswith('U10') else cond
                counts = c['support']['class_counts']
                n0, n1 = counts.get('0', 0), counts.get('1', 0)
                m = c['methods']['probability_only']['metrics']
                for readout in ('linear', 'native'):
                    r = m.get(readout)
                    if not r:
                        continue
                    s = stats[(key, readout)]
                    s['deviant_fraction'].append(n1 / max(1, n0 + n1))
                    s['temperature'].append(r['temperature'])
                    s['nll_bits'].append(r['nll_bits'])
                    s['entropy_bits'].append(r['entropy_bits'])
                    s['gain_vs_base_bits'].append(r['gain_vs_base_bits'])
                    s['arch'].append(arch)
    summary = {}
    for (cond, readout), s in sorted(stats.items()):
        n = len(s['temperature'])
        summary[f'{cond}/{readout}'] = {
            'person_condition_records': n,
            'mean_support_deviant_fraction': sum(s['deviant_fraction']) / n,
            'temperature_share': {str(t): s['temperature'].count(t) / n for t in sorted(set(s['temperature']))},
            'mean_query_nll_bits': sum(s['nll_bits']) / n,
            'mean_query_entropy_bits': sum(s['entropy_bits']) / n,
            'mean_gain_vs_base_bits': sum(s['gain_vs_base_bits']) / n,
        }
    OUT.mkdir(parents=True, exist_ok=True)
    receipt = {'job': os.environ['SLURM_JOB_ID'], 'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               'private_units': units, 'note': 'records are person×condition×unit (seed/fold), not independent n',
               'summary': summary}
    (OUT / 'summary.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
