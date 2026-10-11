"""Item-3 engineering checks (no performance thresholds): layer-wise lr groups, phase geometry, plan size."""
import json, os
import pytest
import torch

from auditory_alignment_v2.fm_ext import LLRD, PLAN_X, PHASES, llrd_groups, phase_geometry
from auditory_alignment_v2.foundation_adapter import Backbone
from auditory_alignment_v2.train_fm import FMEncoder


@pytest.mark.parametrize("arch", ["cbramod", "reve"])
@pytest.mark.parametrize("adaptation", ["pretrained_full", "pretrained_partial", "pretrained_peft"])
def test_llrd_groups(arch, adaptation):
    enc = FMEncoder(Backbone(arch, "dtu", adaptation, 200))
    groups, params = llrd_groups(enc, 1e-5, 1e-3, LLRD)
    trainable = [p for p in enc.parameters() if p.requires_grad]
    assert sorted(map(id, params)) == sorted(map(id, trainable))           # every trainable parameter exactly once
    assert len(params) == len(set(map(id, params)))
    bb_lrs = sorted(g["lr"] for g in groups[:-1])
    assert groups[-1]["lr"] == 1e-3 and max(bb_lrs) <= 1e-5 + 1e-18        # head lr; top block = backbone lr
    n = len(enc.bb.blocks); top = {id(p) for p in enc.bb.blocks[-1].parameters() if p.requires_grad}
    lr_of = {id(p): g["lr"] for g in groups for p in g["params"]}
    assert all(abs(lr_of[i] - 1e-5) < 1e-18 for i in top)
    low = {id(p) for p in enc.bb.blocks[0].parameters() if p.requires_grad}
    if adaptation != "pretrained_partial":
        assert all(abs(lr_of[i] - 1e-5 * LLRD ** (n - 1)) < 1e-18 for i in low)


class _BT:
    def __init__(self, fs, seg_len):
        self.fs, self.seg_len = fs, seg_len


@pytest.mark.parametrize("arch,expect", [("cbramod", {0.0: 5, 0.25: 4, 0.5: 4, 0.75: 4}), ("reve", {0.0: 5, 0.25: 5, 0.5: 4, 0.75: 4})])
@pytest.mark.parametrize("fs", [64, 128])
def test_phase_geometry(arch, expect, fs):
    bb = Backbone(arch, "dtu", "pretrained_frozen", fs)
    bt = _BT(fs, 5 * fs)
    for o in PHASES:
        off_e, L, offs = phase_geometry(bt, bb, o)
        assert off_e == round(o * fs) and L == 5 * fs - off_e and len(offs) == expect[o]
        starts = bb.patch_starts(int(round(L * 200 / fs)))
        for a, so in zip(starts, offs):
            assert abs(so / fs - (a + o - 0.2)) < 1.0 / fs     # audio window start = patch start + o - lead
            assert so / fs + 1.2 <= 5.0 + 1e-9                  # window ends inside the 5 s segment


def test_plan_matches_prereg():
    rows = [json.loads(l) for l in open(PLAN_X)]
    from collections import Counter
    c = Counter(r["family_id"] for r in rows)
    assert c == {"X_READOUT_DIAG": 500, "X_FT_VAL": 150, "X_FT_REG": 150, "X_PHASE": 100}
    for r in rows:
        assert r["seed"] == 3401 and r["base_unit"].startswith("ALN2_B_FM_")
        if r["family_id"] != "X_READOUT_DIAG":
            assert r["spec"]["objective"] == "NCE"
