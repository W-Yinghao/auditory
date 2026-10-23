"""CPU tests for the APPENDUM_04 PRES term of paper/w7_arms_v2.py (synthetic tokens only; no production writes).

Run as a Slurm CPU step: python -m pytest -q auditory_alignment_v3/paper/test_w7_arms_v2.py
"""
from __future__ import annotations

import pytest
import torch
import torch.nn.functional as F

from auditory_alignment_v3.aln41.cs_qmi_reference import cs_qmi
from auditory_alignment_v3.paper import w7_arms_v2 as A2, w7_objectives as OBJ


def setup():
    g = torch.Generator().manual_seed(4)
    z0 = torch.randn(32, 3, 50, generator=g)
    pca = {'mu': z0.reshape(-1, 50).mean(0), 'sd': z0.reshape(-1, 50).std(0), 'components': torch.linalg.qr(torch.randn(50, 8, generator=g))[0].T}
    zn = torch.stack([F.normalize(OBJ.pca_project(z0[:, k], pca), dim=-1) for k in range(3)], 1)
    return g, z0, pca, OBJ.pooled_slot_sigma(zn)


def test_l2_pres_matches_definition_and_is_scale_free():
    g, z0, pca, sig = setup()
    zt = z0.clone().requires_grad_(True)
    v, rep = A2.pres_dependence_l2(zt, z0, pca, sig)
    v.backward()
    ref = sum(float(cs_qmi(F.normalize(OBJ.pca_project(z0[:, k], pca), dim=-1), F.normalize(OBJ.pca_project(z0[:, k], pca), dim=-1),
                           sigma_u=sig, sigma_v=sig)[0]) for k in range(3)) / 3
    assert abs(float(v) - ref) < 1e-10 and torch.isfinite(zt.grad).all() and rep['normalised'] == 'L2 per slot'
    mu = pca['mu']
    scaled, _ = A2.pres_dependence_l2(mu + 1.5 * (z0 - mu), z0, pca, sig)
    assert abs(float(scaled) - float(v)) < 1e-6                     # the scale channel of the v1 term is gone
    with pytest.raises(AssertionError):
        A2.pres_dependence_l2(zt, z0.clone().requires_grad_(True), pca, sig)


def test_v2_paths_and_lanes_are_separate_from_v1():
    assert A2.OUT.name == 'arms_v2' and A2.V1.name == 'arms' and A2.FIXED.parent == A2.V1
    assert all(n.startswith('c3_s35pw7v2') and l.startswith('s35_paper_w7v2') and s.startswith('slurm/aln35_paper_w7v2') for n, l, s in A2.LANES.values())
    assert set(A2.w7_sources()) == {'auditory_alignment_v3/paper/w7_arms_v2.py', 'auditory_alignment_v3/paper/w7_objectives.py'}
