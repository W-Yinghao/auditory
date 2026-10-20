"""Seal the tested CPU analysis entry point without changing the GPU plan."""
import json
import os
from datetime import datetime
from . import bridge_factor as F
from . import science_binding as B


def main():
    assert os.environ.get('SLURM_JOB_ID')
    files = ['auditory_alignment_v3/aln35/bridge_factor.py',
             'auditory_alignment_v3/aln35/bridge_factor_analyze.py',
             'tests/auditory_alignment_v3/aln35/test_bridge_factor.py',
             'tests/auditory_alignment_v3/aln35/test_bridge_factor_analyze.py',
             'slurm/aln35_bridge_analyze.sbatch',
             'private/auditory_alignment_v3/aln35/bridge/ANALYSIS_NOTE.md']
    receipt = {'status': 'ready', 'job': os.environ['SLURM_JOB_ID'], 'time': datetime.now().astimezone().isoformat(),
               'plan_sha256': B.sha(F.BASE / 'plan.json'),
               'frozen_analysis_files_sha256': {p: B.sha(B.ROOT / p) for p in files},
               'run_after_all_four_GPU_receipts': 'sbatch slurm/aln35_bridge_analyze.sbatch',
               'CPU_submission_rule': 'fresh standalone normal-QOS squeue logical count <=27 before sbatch',
               'calculation': 'CPU only, cached representations; no encoder forward/training'}
    B.write_new(F.BASE / 'analysis_contract.json', receipt)
    print(json.dumps(receipt), flush=True)


if __name__ == '__main__': main()
