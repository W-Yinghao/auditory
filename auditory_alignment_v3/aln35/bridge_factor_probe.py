"""Bounded first-cache CPU compatibility audit, not the final four-donor result."""
import json
import os
from . import bridge_factor as F
from . import bridge_factor_analyze as A
from . import science_binding as B


def main():
    assert os.environ.get('SLURM_JOB_ID')
    os.umask(0o077); job = os.environ['SLURM_JOB_ID']
    contract = B.read(F.BASE / 'analysis_contract.json')
    for path, digest in contract['frozen_analysis_files_sha256'].items(): assert B.sha(B.ROOT / path) == digest
    plan = B.read(F.BASE / 'plan.json'); assert B.sha(F.BASE / 'plan.json') == contract['plan_sha256']
    item = next(e for e in plan['entries'] if e['key'] == 'dtu_AP')
    private = F.BASE / ('probe_' + job); out = F.RESULTS / ('probe_' + job)
    private.mkdir(parents=True, exist_ok=False); out.mkdir(parents=True, exist_ok=False)
    result = A.analyze_entry(item, private, out)
    receipt = {'status': 'PASS', 'job': job, 'key': 'dtu_AP', 'scope': 'first-cache engineering audit; not final four-donor analysis',
               'analysis_contract_sha256': B.sha(F.BASE / 'analysis_contract.json'),
               'readout_replay': result['readout_replay'],
               'legacy_replay_max_absolute_difference': result['legacy_replay_max_absolute_difference'],
               'result_sha256': B.sha(out / 'entries/dtu_AP.json')}
    B.write_new(private / 'receipt.json', receipt)
    print(json.dumps(receipt), flush=True)


if __name__ == '__main__': main()
