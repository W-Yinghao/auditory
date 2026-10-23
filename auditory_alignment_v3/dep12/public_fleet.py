"""DEP12 public lanes (Agent M): fleet_status(lane) for the fleet scheduler (via the aln35/dep12_pub_*_fleet.py shims).

Lane F  c3_s35dMfeat  dep12_pub_features  GPU feature exporter (public_features.py): smoke, then worker --max-units 2; units become
                                           ready as encoders.py reports them 'available'; preemption-safe, FAILED marker on rc > 0.
Lane P  c3_s35dMpert  dep12_pub_perturb   optional 400 ms input-perturbation panel (perturb.py), same pattern, one slot.
The CPU steps (measure.py, attention.py, perturb.py measure-all, public_report.py) run as CPU Slurm jobs after GPU units complete.
"""
from __future__ import annotations

from . import perturb as PT
from . import public_features as PF

LANES = {'F': (PF.NAME, PF.LANE, PF.SBATCH), 'P': (PT.NAME, PT.LANE, PT.SBATCH)}


def fleet_status(lane='F'):
    assert lane in LANES, lane
    return PF.fleet_status() if lane == 'F' else PT.fleet_status()
