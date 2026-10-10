"""Engineering checks for the repaired foundation-model readout (amendment A1). Technical only - no performance threshold.
Checks: backbone tensor axes [B, C, T, D] for each layout; channel-sensitive output; signed channel contrasts representable
(a zero-channel-mean input that the legacy channel mean cannot distinguish); finite gradients reaching exactly the parameters
each adaptation recipe makes trainable; state-dict round trips (incl. LoRA parametrisation), donor initialisation and
teacher loading."""
import os
import tempfile

import pytest
import torch

from auditory_alignment_v2.fm_readout import HEAD_VERSION, SpatialPatchHead
from auditory_alignment_v2.foundation_adapter import CHANNELS, Backbone, PatchHead
from auditory_alignment_v2.train_fm import EpochEncoder, FMEncoder

ARCHS = ("cbramod", "reve")
OFF_PATH = {"cbramod": {"patch_embedding.mask_encoding"}, "reve": {"cls_query_token"}}


def _x(ds, B=2, fs=200, T=1000, seed=0):
    g = torch.Generator().manual_seed(seed)
    return torch.randn(B, len(CHANNELS[ds]), T, generator=g)


def test_signed_contrast_is_representable():
    torch.manual_seed(0)
    s = torch.randn(1, 1, 3, 8)
    tok = lambda a: torch.cat([a * s, -a * s], 1)  # two channels, H1 = s, H2 = -s: channel mean is 0 for every a
    legacy, new = PatchHead(8, 4).eval(), SpatialPatchHead(8, 2, d=4, K=2, e=4).eval()
    assert torch.allclose(legacy(tok(1.0)), legacy(tok(-1.0)))  # the legacy interface cannot tell the two apart
    assert (new(tok(1.0)) - new(tok(-1.0))).abs().max() > 1e-3  # the signed spatial readout can


@pytest.mark.parametrize("arch", ARCHS)
@pytest.mark.parametrize("ds,fs,T,P", [("fau", 200, 1000, 5), ("dtu", 200, 1000, 5), ("private_bdf", 250, 200, 1)])
def test_axes_and_channel_sensitivity(arch, ds, fs, T, P):
    bb = Backbone(arch, ds, "pretrained_frozen", fs).eval()
    enc = (FMEncoder(bb) if ds != "private_bdf" else EpochEncoder(bb)).eval()
    x = _x(ds, fs=fs, T=T)
    with torch.no_grad():
        tok = bb(x)
        assert tuple(tok.shape) == (2, len(CHANNELS[ds]), P, bb.E), tok.shape  # [B, C, T, D] in the layout's channel order
        u = enc(x if ds != "private_bdf" else [x])
        assert u.shape[-1] == 16 and torch.allclose(u.norm(dim=-1), torch.ones_like(u.norm(dim=-1)), atol=1e-4)
        x2 = x.clone(); x2[:, 3] = x2[:, 3] + 1.0
        u2 = enc(x2 if ds != "private_bdf" else [x2])
        assert (u - u2).abs().max() > 1e-4  # output depends on an individual channel
        x3 = x.clone(); x3[:, [0, 1]] = x3[:, [1, 0]]
        u3 = enc(x3 if ds != "private_bdf" else [x3])
        assert (u - u3).abs().max() > 1e-4  # and on which channel carries which signal


def _trainable_expected(bb, name):
    a = bb.adaptation
    if a in ("random_full", "pretrained_full", "auditory_continued_full", "auditory_pretrained_full"):
        return True
    if a in ("pretrained_peft", "auditory_pretrained_peft"):
        return "parametrizations" in name and not name.endswith(".original")
    if a in ("pretrained_partial", "auditory_continued_partial"):
        k = 3 if bb.arch == "cbramod" else 6
        n = len(bb.blocks); ids = {id(p) for blk in bb.blocks[n - k:] for p in blk.parameters()}
        return id(dict(bb.net.named_parameters())[name]) in ids
    return False


@pytest.mark.parametrize("arch", ARCHS)
@pytest.mark.parametrize("adaptation", ["random_full", "pretrained_frozen", "pretrained_peft", "pretrained_partial", "pretrained_full"])
def test_gradients_reach_exactly_the_intended_parameters(arch, adaptation):
    torch.manual_seed(0)
    bb = Backbone(arch, "fau", adaptation, 200)
    enc = FMEncoder(bb).train()
    enc(_x("fau", T=1000))[..., 0].sum().backward()
    for n, p in enc.head.named_parameters():
        assert p.grad is not None and torch.isfinite(p.grad).all() and p.grad.abs().sum() > 0, n
    assert enc.head.W.grad.abs().sum(0).min() > 0  # every channel receives gradient through the spatial filters
    n_tr, no_grad = 0, set()
    for n, p in bb.net.named_parameters():
        exp = _trainable_expected(bb, n)
        assert p.requires_grad == exp, (n, p.requires_grad, exp)
        if exp:
            n_tr += 1
            if p.grad is None:
                no_grad.add(n)
            else:
                assert torch.isfinite(p.grad).all(), n
        else:
            assert p.grad is None, n
    # trainable but off the forward path by design: CBraMod's masked-pretraining token, REVE's classification-pooling query
    # (the readout uses every channel's patch tokens). Anything else without a gradient is an error.
    assert no_grad <= OFF_PATH[arch], no_grad - OFF_PATH[arch]
    assert (n_tr == 0) == (adaptation == "pretrained_frozen")


@pytest.mark.parametrize("arch", ARCHS)
@pytest.mark.parametrize("adaptation", ["pretrained_peft", "pretrained_full", "random_full"])
def test_state_dict_round_trip(arch, adaptation):
    torch.manual_seed(1)
    enc = FMEncoder(Backbone(arch, "dtu", adaptation, 200)).eval()
    x = _x("dtu", T=1000, seed=3)
    with torch.no_grad():
        u = enc(x)
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "u_best.pt"); torch.save({"enc": enc.state_dict()}, p)
        torch.manual_seed(2)
        enc2 = FMEncoder(Backbone(arch, "dtu", adaptation, 200)).eval()
        enc2.load_state_dict(torch.load(p)["enc"], strict=True)
    with torch.no_grad():
        assert torch.allclose(enc2(x), u, atol=1e-5)


@pytest.mark.parametrize("arch", ARCHS)
def test_donor_initialisation_and_teacher_loading(arch):
    from auditory_alignment_v2.distill import load_teacher
    sd = Backbone(arch, "fau", "pretrained_full", 200).net.state_dict()
    for a in ("auditory_continued_partial", "auditory_continued_full", "auditory_pretrained_peft", "auditory_pretrained_full"):
        bb = Backbone(arch, "dtu", a, 200, init_state=sd)
        assert bb.init_loaded["missing"] == [] and bb.init_loaded["unexpected"] == [] and bb.init_loaded["n_tensors"] == len(sd)
    t = EpochEncoder(Backbone(arch, "private_bdf", "auditory_pretrained_full", 250)).eval()
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "teacher_best.pt"); torch.save({"enc": t.state_dict()}, p)
        lt = load_teacher(arch, p, "cpu")
    x = [_x("private_bdf", fs=250, T=200)]
    with torch.no_grad():
        assert torch.allclose(lt(x), t(x), atol=1e-5)
    assert all(not q.requires_grad for q in lt.parameters())


def test_head_version_recorded():
    assert HEAD_VERSION.startswith("spatial_signed")
