"""ADDENDUM_06 (B_ALIGNED) synthetic checks: aligned windows equal the EEG slice [t - pre, t + post) with zeros before the
segment start; the readout is L2-normalised; the model refuses a multi-patch backbone output; registry / runner bound without
changing existing code hashes; plan_ext block 3 rows mirror their B_DENSE interface twins."""
import json
import os

import pytest
import torch

from auditory_alignment_v3 import core, fm_aligned, run


def test_aligned_windows_slice_and_zero_before_start():
    C, N, pre, post = 3, 1000, 5, 7
    E = torch.arange(C * N, dtype=torch.float32).reshape(C, N)
    e0 = torch.tensor([100, 300]); t = torch.tensor([[0, 3, 60], [9, 30, 63]])
    W = fm_aligned.aligned_windows(E, e0, t, pre, post).reshape(2, 3, C, pre + post)
    for i in range(2):
        for j in range(3):
            rel = int(t[i, j]) - pre + torch.arange(pre + post)
            exp = E[:, int(e0[i]) + rel.clamp(min=0)] * (rel >= 0).float()
            assert torch.equal(W[i, j], exp)
    assert (W[0, 0, :, :pre] == 0).all() and (W[0, 1, :, :2] == 0).all() and (W[0, 1, :, 2:] != 0).all()


class _BB(torch.nn.Module):
    channel_names, E = ["a", "b", "c"], 4

    def __init__(self, P=1):
        super().__init__(); self.P = P; self.w = torch.nn.Parameter(torch.ones(1))

    def forward(self, x):
        return x.mean(-1)[:, :, None, None].expand(-1, -1, self.P, 4) * self.w


def test_readout_normalised_and_single_patch():
    m = fm_aligned.AlignedFM(_BB(), 8)
    u = m(torch.randn(5, 3, 12))
    assert u.shape == (5, 8) and torch.allclose(u.norm(dim=-1), torch.ones(5), atol=1e-5)
    with pytest.raises(AssertionError):
        fm_aligned.AlignedFM(_BB(P=2), 8)(torch.randn(2, 3, 12))


def test_registry_binding_keeps_existing_hashes():
    assert core.FAMILY_GROUP["B_ALIGNED"] == "aligned" and run.RUNNER["aligned"] == "run_aligned"
    assert core.code_hash("B_DENSE").startswith("040d71894b35349f")  # recorded in every B_DENSE unit
    src = open(os.path.join(os.path.dirname(fm_aligned.__file__), "fm_aligned.py")).read().split('"""', 2)[2]  # code body (the docstring lists the replacements)
    assert "bt.context" not in src and "DenseFM(" not in src and "def fit_aligned(" in src


def test_plan_ext_block3_rows():
    ext = run.ext_rows(); al = [r for r in ext if r["family_id"] == "B_ALIGNED"]
    assert len(al) == 250 and len({r["experiment_id"] for r in al}) == 250
    base = {r["experiment_id"]: r for r in core.load_rows()}
    for r in al:
        b = base[r["base_plan_row"]]; s, bs = r["spec"], b["spec"]
        assert b["family_id"] == "B_DENSE" and bs["readout"] == "channel_phase_linear" and bs["objective"] == "NCE" and b["seed"] == 3401
        assert s["readout"] == "aligned_patch_linear" and s["patch_window_s"] == [-0.4, 0.6]
        assert {k: v for k, v in s.items() if k not in ("readout", "patch_window_s")} == {k: v for k, v in bs.items() if k != "readout"}
        assert all(r[k] == b[k] for k in ("dataset", "subject_fold", "content_fold", "seed"))
