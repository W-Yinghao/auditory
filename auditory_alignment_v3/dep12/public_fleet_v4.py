"""DEP12 public lanes v4 (Agent M; public_features_v4 incl. Federici (M20) and ext2; encoders_v3 registry; lane s35_dep12_pub_features).

Lane F  c3_s35dMfeat  s35_dep12_pub_features  GPU feature exporter (public_features_v4.py): smoke, then worker --max-units 2.
The perturbation lane stays on public_fleet_v3 / perturb_v3 (aln35/dep12_pub_pert_fleet_v5.py); Federici has no perturbation panel.
"""
from __future__ import annotations

from . import public_features_v4 as PF

LANES = {'F': (PF.NAME, PF.LANE, PF.SBATCH)}


def fleet_status(lane='F'):
    assert lane == 'F', lane
    return PF.fleet_status()
