"""Freeze the explicit v2 numerical-replay amendment after independent audit."""
import json
import os
from datetime import datetime
from . import bridge_factor as F
from . import science_binding as B


def main():
    assert os.environ.get('SLURM_JOB_ID')
    audit_path = F.BASE / 'replay_audit_1047375.json'; audit = B.read(audit_path)
    assert audit['status'] == 'complete'
    assert audit['maximum_absolute_differences']['fast_vs_original_score_absolute'] < 1e-12
    for metric in ('top1', 'mrr', 'rank_pct'):
        assert audit['maximum_absolute_differences']['fast_vs_original_formula_' + metric] < 1e-12
    files = ['auditory_alignment_v3/aln35/bridge_factor.py',
             'auditory_alignment_v3/aln35/bridge_factor_analyze_v2.py',
             'tests/auditory_alignment_v3/aln35/test_bridge_factor.py',
             'tests/auditory_alignment_v3/aln35/test_bridge_factor_v2.py',
             'slurm/aln35_bridge_analyze_v2.sbatch',
             'private/auditory_alignment_v3/aln35/bridge/ANALYSIS_NOTE.md',
             'private/auditory_alignment_v3/aln35/bridge/REPLAY_NUMERICS_V2.md',
             'private/auditory_alignment_v3/aln35/bridge/replay_audit_1047375.json']
    receipt = {'status': 'ready', 'version': 2, 'job': os.environ['SLURM_JOB_ID'], 'time': datetime.now().astimezone().isoformat(),
               'plan_sha256': B.sha(F.BASE / 'plan.json'), 'previous_contract_sha256': B.sha(F.BASE / 'analysis_contract.json'),
               'frozen_analysis_files_sha256': {p: B.sha(B.ROOT / p) for p in files},
               'known_v1_failed_probe': '1047360', 'independent_formula_audit': '1047375',
               'run_after_all_four_GPU_receipts': 'sbatch slurm/aln35_bridge_analyze_v2.sbatch',
               'calculation': 'CPU only; original B matrices and frozen re-extracted features; every historical endpoint retained'}
    B.write_new(F.BASE / 'analysis_contract_v2.json', receipt)
    print(json.dumps(receipt), flush=True)


if __name__ == '__main__': main()
