"""Read-only fleet readiness for the ALN4.1 R2 replication, v2 (r2_lanes.py unchanged): the private CE items run the
resumable runner (r2_private_resume.py) under new job names c3_s35r2a41q{b0,tcs,tnc}. Their worker work waits for the
resume validation smoke, which the B0 item submits first. Source and frozen items are r2_lanes' own.
"""
from __future__ import annotations

from . import r2_lanes as L, r2_private_resume as RR

PRIVATE_NAMES = {arm: ('c3_s35r2a41q' + tag, 's35_r2_aln41_private_' + tag, f'slurm/aln35_r2a41_private_resume_{tag}.sbatch')
                 for arm, tag in (('B0', 'b0'), ('TCS', 'tcs'), ('TNCE', 'tnc'))}


def fleet_status():
    out = [L.stage_status('source', *L.NAMES['source'])]
    smoke_ok = RR.smoke_passed()
    for arm, names in PRIVATE_NAMES.items():
        it = L.stage_status('private', *names, arm=arm, smoke_owner=arm == 'B0')
        if it['state'] == 'ready' and '--worker' in it['submit'] and not smoke_ok:
            it = L.item(*names, 'ready', 1, it['remaining'], ['--resume-smoke']) if arm == 'B0' else \
                L.item(*names, 'awaiting_resume_smoke', remaining=it['remaining'])
        out.append(it)
    out.append(L.stage_status('frozen', *L.NAMES['frozen']))
    return out
