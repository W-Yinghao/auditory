"""DEP12 public lanes v5 (Agent M; public_features_v5 / perturb_v4, encoders_v4 registry incl. ext3 ssl_continue; M21).

Lane F  c3_s35dMfeat  s35_dep12_pub_features  GPU feature exporter (public_features_v5.py; DTU / FAU / Federici, ext1-ext3 rows).
Lane P  c3_s35dMpert  s35_dep12_pub_perturb   400 ms perturbation panel (perturb_v4.py; DTU / FAU, ext1-ext3 rows).
"""
from __future__ import annotations

from . import perturb_v4 as PT
from . import public_features_v5 as PF

LANES = {'F': (PF.NAME, PF.LANE, PF.SBATCH), 'P': (PT.NAME, PT.LANE, PT.SBATCH)}


def fleet_status(lane='F'):
    assert lane in LANES, lane
    return PF.fleet_status() if lane == 'F' else PT.fleet_status()
