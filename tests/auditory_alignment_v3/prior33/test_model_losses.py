"""M4 synthetic tests (PUBLIC_PRIOR_DESIGN.md §7.1 items 3c for the head and the losses, 4b / 4f / 4g on the loss side, 5, 6, 7a-d and
the masking / scale part of 12; §2.3-§2.5, §2.7-§2.9, §2.12, §2.15): SharedEncoder shapes, geometry and the exact zero contribution
of unseen channels, seeded construction, strict donor loading and the tensor map, the fixed head in the shared coordinates and the
contract provenance of the stored projections, the contract NCE (multi-positive log-sum-exp, the +-2 s neighbour mask on the family
clock, unknown clocks as a required input, no self pairs, participant ids required in cross_person), the full kernel CS against a
direct numpy evaluation (gradients; the log n limit of narrow kernels), ContractObjective (rolled keys) and the rich block (missing
targets masked, never zero-filled; the donor-side readout against ev1). CPU only; synthetic tensors and the shared fixture
(fixtures.py). The canonical P is embedded below as bytes (sha256 = the design count): design §2.3 never regenerates P because QR
results may depend on the BLAS code path, so no test here depends on the fixture's test-time regeneration of P."""
import base64
import copy
import hashlib
import inspect
import math
import os
import shutil
import sys
import types

import numpy as np
import pytest
import torch
import torch.nn as nn
import torch.nn.functional as F

from auditory_alignment.losses import deduplicated_infonce, prototype_nce
from auditory_alignment.losses_reference import cs_qmi, symmetric_infonce
from auditory_alignment.train import Objective, _offdiag_median_dist
from auditory_alignment_v2.audio_targets import FixedFeatureHead, semi_orthogonal
from auditory_alignment_v2.temporal import TokenEncoder, build_encoder
from auditory_alignment_v3.prior33 import contract as C
from auditory_alignment_v3.prior33 import losses as L
from auditory_alignment_v3.prior33 import model as M
from auditory_alignment_v3.prior33 import rich as R

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fixtures import make_synthetic_manifest  # noqa: E402

FAU, BIO, PRIV = C.MONTAGES["fau"], C.BIOSEMI64, C.PRIVATE_LAYOUT
SD_KEYS = ["branches.0.local.1.bias", "branches.0.local.1.weight", "branches.0.local.2.ln.bias", "branches.0.local.2.ln.weight",
           "branches.0.pos", "branches.0.tok.bias", "branches.0.tok.weight", "proj.0.bias", "proj.0.weight", "proj.1.bias",
           "proj.1.weight", "spatial.W", "spatial.b", "spatial.seen"]
SIB = C.tick(np.arange(0, 250, C.ANCHOR_STEP)[:C.N_ANCHORS])          # the 8 training anchors of a segment (phase 0): 0.62 s apart
# P = audio_targets.semi_orthogonal(32, 8, 20261016) as stored once (§2.3): its float32 C-order bytes, base64; sha256 of the bytes
P_CANON_SHA256 = "706c4ff4441f4940460e8e57cf71a42b07ecd9bdac57d2205a535692ad4733b5"
P_CANON_B64 = ("9yVLvtHAQD4Yck67WkarPtV2jb4XqwW+osGkPYaDL76r1v69ETWCvvC1KL6yXYi+uBPJOghoRbwUFQI+iVajvjIM1b4Q6pu9IdvKvd9IPr5ijeW9"
               "aK5gvjfrUDrCcpI+91O2vazx1bwzDGq9hw0tvedcy70+YAY+U5FXPlUz2j0eRTk9Zz0kPeoaa75E0I09JXWLvTl6db6Woum9WLgOPTx6yLzGsio+"
               "stJavndbHr7bGxm9hsqMvvoRcj4y5pS+v3fjO26oxz73ZE0+w3OXveLeZz4wZ+O94mPKvC2scz01vgA9fZKjO//uzDwOTqu9CZxHPlBV4D5vFCy9"
               "kESLPUp2zjz5vZo9ch8JPTpleT6xgsC9uneXu5SLxT4/1RE5tVj9PRfyMr4uM1m+Kc2fvmef8T2JrKU9vVnsPZXWmj1XFL49pzZUPUjM6709KOE8"
               "gBUbvuuJkj3xfp4+76HnPKCtWT3ooAG+xeBSvVfleLxHfkM+HU8FPofImL1BWhI+El+Ove+l4D3wh526Kcp+PdUrXL7owha+Yj1mPZBGf7vkUuU7"
               "r/IcPfqKhj4Ihak9V5Sbvt6Ohj4yHCs++4yuPgDPNj6hAFG+GIdivnnvPT6worS+QGlgPnS9Gz0hhIe+TcP3PTy8kr3uF5i+fLLGPa5Bq70MnCS+"
               "GGLOvQYVrT6lhvc9fraSPuvDRj6Mjw6+mmjZvbbxkbyVMWO9Wul4viuvjj7sZSk9OKKWPt/ejL32xQY+MklRvojw5j7pgPA9AYztPvdKi77osVo+"
               "dVyQPfD9Ar5m1Pm9iG2OvLRikb2ayqA9en18PlusO76Mbc8+bQeKPk/crD3PktQ9ny9QuwcWJ77gNYS+dLq+O3Gj3T3FoDQ+p9RwPlq7jD6iWe+9"
               "7doGPQNrI71eLpe9nBgPvvVllL5R/zG+C7CdPVR4mD4psiO+kQ5ivu6uhT06PXA+1rKYPg0zYL4iJss9YNEGvQX06b0xFIS+CtJ5PekqlT53qv69"
               "kIGRPfOQOr0xHrO92WD3PVGMyT25QRS+Euy/PVgZVD7aOri9U+YfPmk4Ar7Q/IS+N/kLPkc9BT7Lble+xse1vcN1jD73f5E+kQJcvG+jiTpYbU2+"
               "wFC4PglgC70z4MC9BUMavrPgdD29Oww9cGtHvk89Ub7nW9Y9RJltPswaZT5jEDK+EJ/nPd8rVD5tkkO+9Fwuvghxcj7NC3w9timmvKVo1b2nHBa+"
               "y/QHvl5iZr7D/5O8qvptPoIoz72bxdm8IbB9vRE2m72SAJC+M+YOvmvvYT73Doc9N0JPPoacmr1xxDk+82eDvgEznz3GS4w+sUKgvTEpUz6G9Wu7"
               "A3ILvDrSkrwsKjG+bW02vQ==")
JOB = {"objective": "NCE", "config": {"temperature": 0.1, "bandwidth_multiplier": 1.0, "fmca_relative_ridge": 1e-3}}


@pytest.fixture(scope="module")
def fx(tmp_path_factory):
    return make_synthetic_manifest(tmp_path_factory.mktemp("prior33_m4"))


def _p_canon():
    return np.frombuffer(base64.b64decode(P_CANON_B64), dtype="<f4").reshape(C.P_SHAPE).astype(np.float32)


@pytest.fixture(scope="module")
def canon(fx, tmp_path_factory):
    """The fixture manifest with the stored-once canonical P (the embedded bytes) in place of the P regenerated at test time; the
    rich projections are the fixture's files (the contract pins their file names and seeds, not their sha)."""
    root = str(tmp_path_factory.mktemp("prior33_m4_canon"))
    P = _p_canon()
    np.save(os.path.join(root, C.P_FILE), P)
    for k in ("ss", "sc"):
        shutil.copyfile(os.path.join(fx["root"], C.RICH_P_FILE[k]), os.path.join(root, C.RICH_P_FILE[k]))
    man = copy.deepcopy(fx["manifest"])
    man["projection"]["sha256"] = P_CANON_SHA256
    return {"root": root, "manifest": man, "P": P}


def _g(seed):
    return torch.Generator().manual_seed(seed)


def _x(n, c, seed=0):
    return torch.randn(n, c, C.L_IN, generator=_g(seed))


def _r(n, d, seed, grad=False):
    return torch.randn(n, d, generator=_g(seed), dtype=torch.float64).requires_grad_(grad)


def _keys(fam, pres, s):
    return torch.as_tensor(C.pack_key(np.asarray(fam, dtype=np.int64), np.asarray(pres, dtype=np.int64), np.asarray(s, dtype=np.int64)))


def _row(ds, init, seed=3401, **spec):
    return {"dataset": ds, "seed": seed, "spec": {"stage": "target", "init": init, "target_seed": seed, "architecture": "lag_local_tokens",
                                                  "channel_map": "name_indexed_signed_v1", "fs": 64, "projection_dim": 32,
                                                  "input_samples": [0, 38], "window": "full", **spec}}


def _donor(fx, target, seed=3401, rich=False, step=True):
    """A donor member as a donor group builds it (the donor-union seen set, SparrKULee row order), after one AdamW step."""
    enc = M.build_shared(BIO, fx["manifest"]["seen"][target], seed, rich=rich)
    if step:
        opt = torch.optim.AdamW(enc.parameters(), lr=1e-2, weight_decay=1e-4)
        z = enc.trunk(_x(8, 64, seed))
        loss = (enc.project(z) * torch.randn(8, 32, generator=_g(seed))).sum()
        if rich:
            loss = loss + sum((h * torch.randn(8, 32, generator=_g(seed + 1))).sum() for h in enc.rich(z).values())
        loss.backward()
        opt.step()
    return enc


def _hand_nce(S, E):
    """Diagonal positives, excluded set E: (mean_q l(S) + mean_q l(S^T)) / 2 written out query by query."""
    n = len(S)
    a = torch.stack([-S[q, q] + torch.logsumexp(S[q][~E[q]], 0) for q in range(n)]).mean()
    b = torch.stack([-S[q, q] + torch.logsumexp(S.T[q][~E.T[q]], 0) for q in range(n)]).mean()
    return (a + b) / 2


def _cos(a, b, tau=0.1):
    return F.normalize(a.detach().double(), dim=1) @ F.normalize(b.detach().double(), dim=1).T / tau


# ---------------------------------------------------------------------------------------------------------- encoder
def test_shapes_parameters_and_state_keys():
    enc = M.build_shared(FAU, FAU, 3401)
    x = _x(5, 31)
    u, tok, z = enc(x), enc.forward_tokens(x), enc.trunk(x)
    assert u.shape == (5, 32) and tok.shape == (5, 36, 32) and z.shape == (5, 1152)
    assert torch.allclose(u.norm(dim=1), torch.ones(5), atol=1e-6)
    assert torch.equal(enc([x]), u) and torch.equal(z, tok.flatten(1)) and torch.equal(enc.project(z), u)
    npar = {k: p.numel() for k, p in enc.named_parameters()}
    assert sum(npar.values()) == M.N_PARAMS == 44_176 and npar["proj.1.weight"] + npar["proj.1.bias"] == 36_896
    sd = enc.state_dict()
    assert sorted(sd) == SD_KEYS and sd["spatial.W"].shape == (70, 16) and sd["spatial.seen"].dtype == torch.bool
    assert isinstance(enc.branches[0].local[0], nn.Identity) and enc.branches[0].w == 3 and enc.n_tokens == 36
    assert torch.equal(enc.branches[0].offs, torch.arange(36))           # token step 1 sample (15.6 ms) at 64 Hz
    d = M.describe(enc)
    assert (d["n_params"], d["n_tokens"], d["tokens_per_branch"], d["layout_total"], d["fs"]) == (44_176, 36, [36], 31, 64)
    shapes = {k: v.shape for k, v in sd.items()}                          # identical in every cohort: every tensor transfers
    for lay in (BIO, C.MONTAGES["federici"], PRIV):
        e = M.build_shared(lay, lay, 1)
        assert {k: v.shape for k, v in e.state_dict().items()} == shapes and e(_x(2, len(lay))).shape == (2, 32)
    for bad in (_x(2, 30), torch.randn(2, 31, 40), [x, x]):
        with pytest.raises(ValueError):
            enc(bad)
    with pytest.raises(KeyError):
        M.build_shared(FAU + ("X1",), FAU, 1)                             # every name must map into the vocabulary
    with pytest.raises(ValueError):
        M.names_of(("T3", "T7"))                                          # an alias and its target are one electrode


def test_spatial_map_equals_conv1d_and_the_token_encoder():
    """§7.1 7a: the name-indexed map equals a per-cohort Conv1d, and the composition equals TokenEncoder with that Conv1d."""
    enc = M.build_shared(FAU, FAU, 7)
    x = _x(6, 31, 1)
    idx = torch.tensor([C.VOCAB_INDEX[n] for n in FAU])
    conv = nn.Conv1d(31, 16, 1)
    with torch.no_grad():
        conv.weight.copy_(enc.spatial.W[idx].T[..., None])
        conv.bias.copy_(enc.spatial.b)
    assert (enc.spatial(x) - conv(x)).abs().max() <= 1e-6
    ref = TokenEncoder("lag_local_tokens", 31, 32, [(0, 38)], 64)
    own = ref.state_dict()
    for k in own:
        own[k] = conv.state_dict()[k.rsplit(".", 1)[1]] if k.startswith("branches.0.local.0.") else enc.state_dict()[k]
    ref.load_state_dict(own)
    with torch.no_grad():
        assert (ref.forward_tokens([x]) - enc.forward_tokens(x)).abs().max() <= 1e-6
        assert (ref([x]) - enc(x)).abs().max() <= 1e-6
    perm = FAU[::-1]                                                      # name-indexed: the row order is irrelevant
    assert (enc(x.flip(1), layout=perm) - enc(x)).abs().max() <= 1e-6


def test_unseen_channels_contribute_exactly_zero():
    """§7.1 7b: unseen names hold zero rows, never change the output (whatever their values) and get zero gradient."""
    train = [n for n in FAU if n not in ("F9", "F10", "TP9")]
    enc = M.build_shared(FAU, train, 11)
    W, seen = enc.spatial.W.detach(), enc.spatial.seen
    unseen = [i for i, n in enumerate(C.VOCAB) if n not in train]
    assert not seen[unseen].any() and (W[unseen] == 0).all() and int(seen.sum()) == len(train)
    x = _x(4, 31, 2)
    u0, t0 = enc(x), enc.forward_tokens(x)
    cols = [FAU.index(n) for n in ("F9", "F10", "TP9")]
    for val in (1e6, -3.0, float("inf"), float("nan")):
        xp = x.clone()
        xp[:, cols] = val
        assert torch.equal(enc(xp), u0) and torch.equal(enc.forward_tokens(xp), t0)
    xs = x.clone()
    xs[:, FAU.index("Cz")] += 1.0
    assert not torch.allclose(enc(xs), u0)
    xg = x.clone().requires_grad_(True)
    (enc(xg) * torch.randn(4, 32, generator=_g(3))).sum().backward()
    g = enc.spatial.W.grad
    assert (g[unseen] == 0).all() and (g[[C.VOCAB_INDEX[n] for n in train]].abs().sum(1) > 0).all()
    assert (xg.grad[:, cols] == 0).all() and (xg.grad[:, FAU.index("Cz")] != 0).any()
    cz = FAU.index("Cz")                                                  # per-sample channel mask: never read, as if unseen
    m = torch.ones(31, dtype=torch.bool)
    m[cz] = False
    xn, xz = x.clone(), x.clone()
    xn[:, cz], xz[:, cz] = float("nan"), 0.0
    assert torch.equal(enc(xn, mask=m), enc(xz))
    mb = torch.ones(4, 31, dtype=torch.bool)                              # a [B, C] mask: one cell of row 0
    mb[0, cz] = False
    out = enc(x, mask=mb)
    assert torch.allclose(out[0], enc(xz)[0], atol=1e-6) and torch.allclose(out[1:], u0[1:], atol=1e-6)
    xn0 = x.clone()
    xn0[0, cz] = float("nan")
    assert torch.equal(enc(xn0, mask=mb), out)
    xd = _x(3, 64, 4)                                                     # a batch in another row order (layout override)
    keep = [BIO.index(n) for n in train if n in BIO]
    xd2 = torch.zeros_like(xd)
    xd2[:, keep] = xd[:, keep]
    assert torch.equal(enc(xd, layout=BIO), enc(xd2, layout=BIO))


def test_build_shared_is_seeded_and_leaves_the_rng_alone():
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(123)
        st = torch.get_rng_state()
        a, b = M.build_shared(FAU, FAU, 3401), M.build_shared(FAU, FAU, 3401)
        assert torch.equal(torch.get_rng_state(), st)
    sa, sb = a.state_dict(), b.state_dict()
    assert all(torch.equal(sa[k], sb[k]) for k in sa)
    c = M.build_shared(FAU, FAU, 3407).state_dict()
    assert not torch.equal(sa["spatial.W"], c["spatial.W"]) and not torch.equal(sa["proj.1.weight"], c["proj.1.weight"])
    for names in (FAU, BIO[:20], C.VOCAB):                                # U(+-1/sqrt(n_c)), n_c = the names the unit trains
        e = M.build_shared(BIO, names, 5)
        Wn, rows = e.spatial.W.detach(), [C.VOCAB_INDEX[n] for n in names]
        bound = 1 / math.sqrt(len(names))
        assert bound / 2 < Wn[rows].abs().max() <= bound and e.spatial.b.abs().max() <= bound
        assert (Wn[[i for i in range(70) if i not in rows]] == 0).all() and sorted(e.seen_names()) == sorted(names)
    r = M.build_shared(FAU, FAU, 3401, rich=True)
    sr = r.state_dict()
    assert all(torch.equal(sr[k], sa[k]) for k in sa)                     # the APR trunk and proj start exactly as AP's
    assert sorted(k for k in sr if k.startswith("rich.")) == sorted(f"rich.proj_{h}.{i}.{p}" for h in ("ss", "sc") for i in (0, 1)
                                                                      for p in ("weight", "bias"))
    hs = r.rich(r.trunk(_x(3, 31)))
    assert hs["ss"].shape == hs["sc"].shape == (3, 32) and torch.allclose(hs["ss"].norm(dim=1), torch.ones(3), atol=1e-6)


# ---------------------------------------------------------------------------------------------------------- fixed head
def test_fixed_head_keys_projection_and_scale_invariance(fx, canon):
    """§7.1 7c (keys of FixedFeatureHead, P sha / orthonormality / rank) and 3c on the head and every loss."""
    heads = M.fixed_heads(canon["manifest"], canon["root"])
    h = heads["env"]
    ref = FixedFeatureHead(8, 32, np.zeros(8), np.ones(8), "fau")
    assert list(h.state_dict()) == list(ref.state_dict()) == ["P", "std.mu", "std.sd"] and not list(h.parameters())
    assert (h.std.mu == 0).all() and np.allclose(h.std.sd.numpy(), fx["manifest"]["standardiser"]["sigma"], rtol=1e-6)
    P = h.P.numpy()
    assert np.array_equal(P, canon["P"]) and hashlib.sha256(P.tobytes()).hexdigest() == P_CANON_SHA256
    assert P_CANON_SHA256.startswith(C.P_SHA16) and np.abs(P.T @ P - np.eye(8)).max() < 1e-6 and np.linalg.matrix_rank(P) == 8
    assert np.abs(np.abs(fx["P"]) - np.abs(P)).max() < 1e-6              # the fixture's test-time QR of the seed, up to the BLAS path
    ref.load_state_dict(h.state_dict())
    y = torch.randn(10, 8, generator=_g(5))
    v = h(y)
    assert torch.equal(v, ref(y)) and torch.allclose(v.norm(dim=1), torch.ones(10), atol=1e-6)
    for c in (0.1, 10.0):
        assert (h(c * y) - v).abs().max() <= 1e-6
    h64 = M.SharedFixedHead(fx["manifest"]["standardiser"]["sigma"], canon["P"]).double()
    y64 = y.double()
    v64 = h64(y64)
    u1, u2 = F.normalize(_r(10, 32, 6), dim=1), F.normalize(_r(10, 32, 7), dim=1)
    k = _keys(np.zeros(10), np.zeros(10), C.tick(np.arange(0, 250, 25)))   # one stream, anchors 0.5 s apart: masks present

    def losses(vv):
        sv = L.calibrate_sigma(vv)
        return [float(L.nce_audio_pair(u1, u2, vv, k, unknown_clock=())[0]), float(L.nce_single_view(u1, vv, k, unknown_clock=())[0]),
                float(L.cs_audio_pair(u1, u2, vv, 0.5, sv)[0]), float(L.cs_cross_person(u1, u2, 0.5)[0]),
                float(cs_qmi(u1, vv, sigma_u=0.5, sigma_v=sv)[0]), float((u1 * vv).sum(1).mean())]
    base = losses(v64)
    for c in (0.1, 10.0):
        assert (h64(c * y64) - v64).abs().max() < 1e-12
        assert np.allclose(losses(h64(c * y64)), base, rtol=0, atol=1e-6)
    for kk, n_in in (("ss", 32), ("sc", 8)):                              # the rich audio heads share the class
        hk = heads[kk]
        assert hk.P.shape == (32, n_in) and hk.std.sd.shape == (n_in,) and (hk.std.mu == 0).all()
        assert np.array_equal(hk.P.numpy(), fx["P_rich"][kk]) and hk(torch.randn(4, n_in)).shape == (4, 32)
    with pytest.raises(ValueError):
        M.load_projection(os.path.join(canon["root"], C.P_FILE), "0" * 64)    # a P whose sha does not match is refused
    with pytest.raises(ValueError):
        M.SharedFixedHead(np.ones(8), np.zeros((32, 7), np.float32))
    with pytest.raises(ValueError):
        M.SharedFixedHead(np.r_[np.ones(7), 0.0], canon["P"])
    assert fx["manifest"]["rich"]["loss_weights"] == [R.RICH_WEIGHTS[x] for x in R.HEADS]


def test_fixed_heads_refuse_a_projection_that_is_not_the_contract_one(canon, tmp_path):
    """§2.3 / inherited §3 (one projection from the fixed seed 20261016, shared by every cohort): the manifest's own sha256 is not
    enough. A P of another seed (ALN2's FAU cohort seed 20261006) stored under the contract name with its own, self-consistent
    sha256 is refused, and so are a wrong file name or seed of the envelope P or of a rich projection."""
    man, root = canon["manifest"], canon["root"]
    assert sorted(M.fixed_heads(man, root)) == ["env", "sc", "ss"]
    for f in os.listdir(root):
        shutil.copyfile(os.path.join(root, f), tmp_path / f)
    other = semi_orthogonal(32, 8, 20261006).numpy()
    np.save(tmp_path / C.P_FILE, other)
    forged = copy.deepcopy(man)
    forged["projection"]["sha256"] = hashlib.sha256(other.tobytes()).hexdigest()
    assert M.load_projection(str(tmp_path / C.P_FILE), forged["projection"]["sha256"], C.P_SHAPE).shape == (32, 8)   # self-consistent
    with pytest.raises(ValueError, match="not the contract's P_32x8_seed20261016_f32.npy"):
        M.fixed_heads(forged, str(tmp_path))
    for path, kw in ((("projection",), {"file": "P_32x8_seed20261006_f32.npy"}), (("projection",), {"seed": 20261006}),
                     (("projection",), {"seed": None}), (("rich", "P_ss"), {"seed": C.RICH_SEEDS["sc"]}),
                     (("rich", "P_sc"), {"file": C.RICH_P_FILE["ss"]})):
        bad = copy.deepcopy(man)
        e = bad
        for p in path:
            e = e[p]
        e.update(kw)
        with pytest.raises(ValueError, match="not the contract's"):
            M.fixed_heads(bad, root)


# ---------------------------------------------------------------------------------------------------------- donor loading
def test_strict_donor_loading_and_tensor_map(fx):
    """§7.1 7d and §2.4: strict load into the target layout, unseen target names opened at W = 0, a complete tensor map."""
    man = fx["manifest"]
    donor = _donor(fx, "fau")
    state = donor.state_dict()
    opened = [C.VOCAB_INDEX[n] for n in ("F9", "F10")]
    assert (state["spatial.W"][opened] == 0).all() and not state["spatial.seen"][opened].any()   # zero under AdamW
    enc = M.build_target_encoder(_row("fau", "donor"), FAU, man, {"enc": state})
    tm = enc.tensor_map
    assert tm["new"] == tm["missing"] == tm["mismatched"] == tm["dropped"] == [] and tm["strict"]
    assert tm["terms"] == M.TENSOR_MAP_TERMS and "missing_keys" in tm["terms"]["new"] and "unexpected_keys" in tm["terms"]["missing"]
    assert tm["loaded"] == sorted(enc.state_dict()) == SD_KEYS
    assert tm["opened_rows"] == man["coverage"]["fau"]["unseen"] == ["F9", "F10"] and tm["closed_unseen"] == []
    assert tm["coverage"] == {"n_seen": 29, "n_total": 31, "unseen": ["F9", "F10"]} and tm["layout"] == list(FAU)
    assert (tm["n_params"], tm["n_params_opened"], tm["n_params_loaded"]) == (44_176, 32, 44_144)
    assert abs(tm["loaded_param_fraction"] - (1 - 32 / 44_176)) < 1e-12 and tm["loaded_param_fraction"] > 0.999
    assert abs(tm["opened_param_fraction"] - 32 / 44_176) < 1e-12
    sd = enc.state_dict()
    for k, v in state.items():
        exp = v.clone()
        if k == "spatial.seen":
            exp[opened] = True
        assert torch.equal(sd[k], exp), k
    assert enc.layout == FAU and sorted(enc.seen_names()) == sorted(set(man["seen"]["fau"]) | {"F9", "F10"})
    x = _x(6, 31, 8)
    assert torch.allclose(enc(x), donor(x, layout=FAU), atol=1e-6)      # opened at W = 0: the loaded function is unchanged
    (enc(x) * torch.randn(6, 32, generator=_g(9))).sum().backward()
    assert (enc.spatial.W.grad[opened].abs().sum(1) > 0).all()            # and the opened rows train
    d = M.describe(enc)
    assert d["tensor_map"] is tm and d["layout_seen"] == 31 and d["n_params"] == 44_176
    zs = M.build_shared(FAU, FAU, 1)                                      # zero-shot: unseen names stay closed
    tz = M.load_donor(zs, state, FAU, open_new=False)
    assert tz["opened_rows"] == [] and tz["closed_unseen"] == ["F9", "F10"] and tz["n_params_loaded"] == 44_176
    xp = x.clone()
    xp[:, [FAU.index("F9"), FAU.index("F10")]] = 1e3
    assert torch.equal(zs(xp), zs(x)) and torch.allclose(zs(x), donor(x, layout=FAU), atol=1e-6)


def test_strict_loading_refusals(fx):
    man = fx["manifest"]
    state = _donor(fx, "fau", step=False).state_dict()

    def tgt():
        return M.build_shared(FAU, FAU, 1)

    for change, word in ((lambda s: s.update({"branches.0.pos": torch.zeros(25, 32)}), "mismatched"),   # the 128 Hz lag grid
                         (lambda s: s.update({"extra.weight": torch.zeros(3)}), "missing"),         # torch: unexpected key
                         (lambda s: s.pop("proj.1.bias"), "new"),                                   # torch: missing key
                         (lambda s: s.update({"spatial.seen": s["spatial.seen"].to(torch.uint8)}), "mismatched")):
        bad = dict(state)
        change(bad)
        with pytest.raises(ValueError, match="strict load refused") as ei:
            M.load_donor(tgt(), bad, FAU)
        assert [w for w in ("new", "missing", "mismatched") if f"{w}=[" in str(ei.value)] == [word]
    bad = dict(state)
    bad["spatial.W"] = state["spatial.W"].clone()
    bad["spatial.W"][C.VOCAB_INDEX["F9"]] = 0.1
    with pytest.raises(ValueError, match="not zero"):
        M.load_donor(tgt(), bad, FAU)
    native = build_encoder("lag_local_tokens", 31, 32, [(0, 76)], 128).state_dict()   # the native 128 Hz A_LOCAL geometry
    with pytest.raises(ValueError, match="strict load refused"):
        M.load_donor(tgt(), native, FAU)
    with pytest.raises(ValueError, match="not a SharedEncoder state"):
        M.build_target_encoder(_row("fau", "donor"), FAU, man, {"enc": native})
    e, bad = tgt(), dict(state)
    bad["branches.0.pos"] = torch.zeros(25, 32)
    del bad["proj.1.bias"]
    tm = M.load_donor(e, bad, FAU, strict=False)                          # non-strict: the matching tensors, the rest listed
    assert tm["mismatched"] == ["branches.0.pos"] and tm["new"] == ["proj.1.bias"] and not tm["strict"]
    assert torch.equal(e.state_dict()["proj.1.weight"], state["proj.1.weight"])
    with pytest.raises(ValueError):
        M.build_target_encoder(_row("fau", "donor"), FAU, man, None)
    with pytest.raises(ValueError):
        M.build_target_encoder(_row("fau", "random"), FAU, man, state)
    other = _donor(fx, "dtu", step=False).state_dict()                    # another donor set's union
    with pytest.raises(ValueError, match="seen set"):
        M.build_target_encoder(_row("fau", "donor"), FAU, man, other)
    for k, v in (("fs", 250), ("projection_dim", 16), ("architecture", "density_tokens"), ("input_samples", [0, 76]),
                 ("channel_map", "channel_mean")):
        with pytest.raises(ValueError):
            M.build_target_encoder(_row("fau", "random", **{k: v}), FAU, man, None)
    with pytest.raises(ValueError):
        M.build_target_encoder(_row("fau", "random"), FAU[::-1], man, None)   # not the manifest's FAU layout
    with pytest.raises(ValueError):
        M.build_target_encoder(_row("fau", "random"), FAU, {**man, "contract": "dense20ms_v1"}, None)


def test_rich_heads_are_dropped_and_listed(fx):
    donor = _donor(fx, "dtu", rich=True)
    state = donor.state_dict()
    rich_keys = sorted(k for k in state if k.startswith("rich."))
    enc = M.build_target_encoder(_row("dtu", "donor"), BIO, fx["manifest"], state)
    tm = enc.tensor_map
    assert len(rich_keys) == 8 and tm["dropped"] == rich_keys and tm["n_dropped_params"] == 2 * (2 * 1152 + 1152 * 32 + 32)
    assert tm["new"] == tm["missing"] == tm["opened_rows"] == [] and tm["loaded_param_fraction"] == 1.0
    assert tm["coverage"] == {"n_seen": 64, "n_total": 64, "unseen": []}
    assert not hasattr(enc, "rich") and M.describe(enc)["rich_heads"] is False and M.describe(donor)["rich_heads"] is True
    x, x2 = _x(4, 64, 3), _x(4, 64, 4)
    assert torch.allclose(enc(x), donor(x), atol=1e-6)
    heads = R.eeg_heads(donor, x, x2)
    assert torch.allclose(heads["env"][0], donor(x), atol=1e-6) and torch.allclose(heads["env"][1], donor(x2), atol=1e-6)
    assert all(t.shape == (4, 32) for p in heads.values() for t in p)


def test_private_and_from_scratch_paths(fx):
    """§2.12: the private path builds 36 tokens at 64 Hz on the 20-name layout; the from-scratch arm trains the target montage."""
    man = fx["manifest"]
    donor = _donor(fx, "private_bdf")
    legacy = ("Fp1", "Fp2", "Fz", "F3", "F4", "F7", "F8", "Cz", "C3", "C4", "T3", "T4", "Pz", "P3", "P4", "T5", "T6", "Oz", "O1", "O2")
    enc = M.build_target_encoder(_row("private_bdf", "donor", target="current_class"), legacy, man, donor.state_dict())
    assert enc.layout == PRIV and len(PRIV) == 20 and enc.n_tokens == 36 and enc.proj[1].in_features == 1152
    assert enc.tensor_map["opened_rows"] == [] and enc.tensor_map["coverage"]["n_seen"] == 20
    x = _x(5, 20, 6)
    assert enc([x]).shape == (5, 32) and torch.allclose(enc(x), donor(x, layout=PRIV), atol=1e-6)
    s1 = M.build_target_encoder(_row("fau", "random", seed=3407), FAU, man, None)
    s2 = M.build_target_encoder({"dataset": "fau", "seed": 3407, "spec": {}}, FAU, man, None)   # bound row: no init / target_seed
    assert s1.tensor_map["init"] == "random" and s1.tensor_map["seed"] == 3407 and sorted(s1.seen_names()) == sorted(FAU)
    assert all(torch.equal(a, b) for a, b in zip(s1.state_dict().values(), s2.state_dict().values()))
    s3 = M.build_target_encoder(_row("fau", "random", seed=3413), FAU, man, None)
    assert not torch.equal(s1.spatial.W, s3.spatial.W) and s1.spatial.W.abs().max() <= 1 / math.sqrt(31)


# ---------------------------------------------------------------------------------------------------------- NCE
def test_masked_lse_nce_equivalences_and_validation():
    S = torch.randn(6, 9, generator=_g(10), dtype=torch.float64)
    t = torch.tensor([0, 3, 8, 2, 2, 5])
    pos, none = F.one_hot(t, 9).bool(), torch.zeros(6, 9, dtype=torch.bool)
    assert torch.allclose(L.masked_lse_nce(S, pos, none), F.cross_entropy(S, t, reduction="none"), atol=1e-12, rtol=0)
    excl = none.clone()
    excl[:, 4], excl[0, 1] = True, True
    exp = torch.stack([-S[q, t[q]] + torch.logsumexp(S[q][~excl[q]], 0) for q in range(6)])
    assert torch.allclose(L.masked_lse_nce(S, pos, excl), exp, atol=1e-12, rtol=0)
    pm = pos.clone()
    pm[1, 7], pm[3, 0] = True, True                                       # several positives: -log of their summed probability
    p = torch.softmax(S.masked_fill(excl, float("-inf")), 1)
    assert torch.allclose(L.masked_lse_nce(S, pm, excl), -torch.log((p * pm).sum(1)), atol=1e-12, rtol=0)
    with pytest.raises(ValueError):
        L.masked_lse_nce(S, pos, pos)                                     # P(q) and E(q) overlap
    with pytest.raises(ValueError):
        L.masked_lse_nce(S, none, none)                                   # a query without a positive


def test_nce_single_view_reference_equivalence_and_gradients():
    """§7.1 5: unique keys and no mask -> symmetric_infonce; repeated keys -> multi-positive LSE, not deduplicated_infonce."""
    n = 12
    u, v = _r(n, 32, 11, True), _r(n, 32, 12, True)
    k = _keys(np.arange(n), np.arange(n), np.zeros(n))
    l, st = L.nce_single_view(u, v, k, unknown_clock=())
    assert abs(float(l - symmetric_infonce(u, v, 0.1))) < 1e-12 and st["masked_per_q_uv"] == 0 and st["pos_per_q_vu"] == 1
    assert l.dtype == torch.float64 and st["n_q_uv"] == n and st["nopos_uv"] == 0
    l.backward()
    assert torch.isfinite(u.grad).all() and torch.isfinite(v.grad).all() and u.grad.abs().sum() > 0
    kr = k.clone()
    kr[1], kr[5] = kr[0], kr[4]
    lr_, st = L.nce_single_view(u, v, kr, unknown_clock=())
    assert st["pos_per_q_uv"] == (n + 4) / n and abs(float(lr_ - deduplicated_infonce(u, v, kr, 0.1))) > 1e-3
    S, pos = _cos(u, v), kr[:, None] == kr[None, :]
    none = torch.zeros_like(pos)
    hand = (L.masked_lse_nce(S, pos, none).mean() + L.masked_lse_nce(S.T, pos.T, none).mean()) / 2
    assert abs(float(lr_ - hand)) < 1e-12


def test_neighbour_mask_boundary_and_hand_case():
    """§7.1 5 / 4b: |ds| <= 128 on the family clock is masked (128 inclusive, 129 not), other families never, positives never."""
    s, fam, pres = np.array([0, 100, 228, 229, 500, 0]), np.array([3, 3, 3, 3, 3, 4]), np.array([1, 1, 1, 1, 1, 2])
    k = _keys(fam, pres, s)
    pos, excl = L.nce_masks(k, k, unknown_clock=())
    exp = (fam[:, None] == fam[None]) & (np.abs(s[:, None] - s[None]) <= 128) & ~np.eye(6, dtype=bool)
    assert np.array_equal(excl.numpy(), exp) and np.array_equal(pos.numpy(), np.eye(6, dtype=bool)) and not (pos & excl).any()
    assert excl[1, 2] and excl[2, 1] and not excl[1, 3] and excl[2, 3] and not excl[0, 5]
    u, v = _r(6, 8, 13), _r(6, 8, 14)
    S = _cos(u, v)
    lm = L.nce_single_view(u, v, k, unknown_clock=())[0]
    assert abs(float(lm - _hand_nce(S, torch.as_tensor(exp)))) < 1e-12
    k0 = _keys(np.arange(6) + 10, pres, s)                                # the same rows, each its own family: no mask
    l0 = L.nce_single_view(u, v, k0, unknown_clock=())[0]
    assert abs(float(l0 - _hand_nce(S, torch.zeros(6, 6, dtype=torch.bool)))) < 1e-12 and float(lm) < float(l0)


def test_family_clock_masks_from_the_manifest(fx):
    """§7.1 4b / 4f on the loss side: declared and measured family clocks, scan-merged duplicates and unknown clocks."""
    man, t = fx["manifest"], fx["truth"]
    pres, P = man["presentations"], t["presentation"]

    def key(name, s):                                                     # s: sample of the item's own stream
        q = pres[P[name]]
        return int(C.pack_key(q["family"], q["id"], q["family_offset"] + s))

    def off(name):
        return pres[P[name]]["family_offset"]
    h1, h2, sh = "sparrkulee:audiobook_1_1", "sparrkulee:audiobook_1_2", "sparrkulee:audiobook_1_shifted"
    kk = torch.tensor([key(h1, 640), key(h2, 640), key(sh, 640), key(sh, 640 + 128), key(sh, 640 + 129)])
    pos, excl = L.nce_masks(kk, kk, unknown_clock=())
    assert excl[0, 2] and excl[0, 3] and not excl[0, 4] and not excl[0, 1] and not pos[0, 2] and not (pos & excl).any()
    for a, b, lag in (("federici:N1", "federici:V1", 48), ("dtu:t01", "dtu:t07", 400)):   # measured lag; scan-merged copy
        assert off(b) - off(a) == lag == t["family_offset"][b]
        kf = torch.tensor([key(a, lag + 300), key(b, 300), key(b, 300 + 200), key(a, 300)])   # b[300] is a[300 + lag]
        _, ef = L.nce_masks(kf, kf, unknown_clock=())
        assert ef[0, 1] and not ef[0, 2] and bool(ef[1, 3]) == (lag <= 128)       # the clocks differ by the lag
    uc = L.unknown_clock_families(man)
    assert uc == t["unknown_clock_families"]
    ku = torch.tensor([key("federici:N2", 100), key("federici:V2", 1500), key("federici:N2", 1500), key("federici:N1", 100)])
    pos, e0 = L.nce_masks(ku, ku, unknown_clock=())
    _, e1 = L.nce_masks(ku, ku, unknown_clock=uc)
    assert not e0[0, 1] and e1[0, 1] and e1[1, 0] and e1[1, 2]           # another item of an unknown-clock family: any time
    assert not e1[0, 2] and not e1[0, 3] and not (e1 & pos).any()        # the same item far away, another family: not masked


def test_unknown_clock_is_a_required_input(fx):
    """§2.5: the clock status is not in the packed key, so every NCE entry point must be told the unknown-clock families (() when
    there are none): omission is a TypeError and None a ValueError, also for ContractObjective, whose literal §2.12 substitution
    ContractObjective(obj_job, u0, v0) therefore fails instead of dropping the rule. With the manifest's families another item of an
    unknown-clock family is masked at any time; here its anchors lie 1,000 samples (15.6 s) away on the stored clock (offset 0)."""
    man, t = fx["manifest"], fx["truth"]
    pres, Pn = man["presentations"], t["presentation"]
    uc = L.unknown_clock_families(man)
    n2, v2 = pres[Pn["federici:N2"]], pres[Pn["federici:V2"]]
    assert uc == t["unknown_clock_families"] == [n2["family"]] and v2["family"] == n2["family"]
    assert n2["family_offset"] == v2["family_offset"] == 0 and not v2["offset_known"]
    s = 200 + 31 * np.arange(4)
    k = _keys([n2["family"]] * 8, [n2["id"]] * 4 + [v2["id"]] * 4, np.r_[s, s + 1000])
    _, e0 = L.nce_masks(k, k, unknown_clock=())
    p1, e1 = L.nce_masks(k, k, unknown_clock=uc)
    assert not e0[:4, 4:].any() and e1[:4, 4:].all() and e1[4:, :4].all() and torch.equal(e0[:4, :4], e1[:4, :4])
    assert torch.equal(p1, torch.eye(8, dtype=torch.bool)) and not (p1 & e1).any()
    for same in (np.array(uc), torch.tensor(uc), set(uc)):
        assert torch.equal(L.nce_masks(k, k, unknown_clock=same)[1], e1)
    u, v, pid = _r(8, 32, 140), _r(8, 32, 141), torch.arange(8)
    for f, args in ((L.nce_masks, (k, k)), (L.nce_single_view, (u, v, k)), (L.nce_audio_pair, (u, u, v, k)),
                    (L.nce_cross_person, (u, v, k, pid, pid + 100))):
        prm = inspect.signature(f).parameters["unknown_clock"]
        assert prm.kind is inspect.Parameter.KEYWORD_ONLY and prm.default is inspect.Parameter.empty
        with pytest.raises(TypeError):
            f(*args)
        with pytest.raises(ValueError, match="unknown_clock"):
            f(*args, unknown_clock=None)
        for bad in ([0.5], ["g1"], [-1]):
            with pytest.raises(TypeError):
                f(*args, unknown_clock=bad)
    for job in (JOB, {**JOB, "objective": "CS_SINGLE"}):
        with pytest.raises(TypeError):
            L.ContractObjective(job, u, v)
        with pytest.raises(ValueError, match="unknown_clock"):
            L.ContractObjective(job, u, v, unknown_clock=None)
    o0, o1 = L.ContractObjective(JOB, u, v, unknown_clock=()), L.ContractObjective(JOB, u, v, unknown_clock=uc)
    l0, l1 = float(o0(u, v, keys=k)[0]), float(o1(u, v, keys=k)[0])
    S = _cos(u, v)
    assert abs(l0 - float(_hand_nce(S, e0))) < 1e-12 and abs(l1 - float(_hand_nce(S, e1))) < 1e-12 and l0 != l1
    assert (o0.record()["unknown_clock_families"], o1.record()["unknown_clock_families"]) == ([], uc)
    with pytest.raises(KeyError):
        L.unknown_clock_families({a: b for a, b in man.items() if a != "families"})
    with pytest.raises(ValueError):
        L.unknown_clock_families({"families": [{"id": 0, "clock": "unkown"}]})


def test_audio_pair_structure_and_sibling_anchors():
    """§2.7: E->A 1 positive (2B queries), A->E 2 positives (both views); the mask removes 3-6 of the 7 sibling anchors."""
    B = 3 * 8
    fam = np.repeat([5, 6, 7], 8)
    k = _keys(fam, fam, np.tile(SIB, 3) + 320 * np.repeat([0, 1, 2], 8))
    u1, u2, v = _r(B, 32, 20, True), _r(B, 32, 21, True), _r(B, 32, 22, True)
    l, st = L.nce_audio_pair(u1, u2, v, k, unknown_clock=())
    assert (st["pos_per_q_e2a"], st["pos_per_q_a2e"], st["n_q_e2a"], st["n_q_a2e"]) == (1, 2, 2 * B, B)
    assert st["masked_per_q_e2a"] == st["masked_per_q_a2e"] / 2 == 4.5
    assert L.nce_masks(k, k, unknown_clock=())[1].sum(1).tolist() == [3, 4, 5, 6, 6, 5, 4, 3] * 3
    kU = torch.cat([k, k])
    S = _cos(torch.cat([u1, u2]), v)
    pe, ee = L.nce_masks(kU, k, unknown_clock=())
    hand = (L.masked_lse_nce(S, pe, ee).mean() + L.masked_lse_nce(S.T, pe.T, ee.T).mean()) / 2
    assert abs(float(l - hand)) < 1e-12 and (pe.sum(0) == 2).all() and torch.equal(pe[:B], pe[B:])
    l.backward()
    assert all(torch.isfinite(x.grad).all() and x.grad.abs().sum() > 0 for x in (u1, u2, v))


def test_cross_person_never_pairs_an_observation_with_itself():
    """§2.7 / OBJECTIVES §2: same participant at the same key is masked, so the same physical observation is never its own
    positive; the participant ids are required (without them a self pair would count as a positive); XM masks = XP's."""
    B = 6
    k = _keys(np.arange(B), np.arange(B), np.zeros(B))
    pid1, pid2 = torch.arange(B), torch.arange(B) + 100
    u1, u2 = _r(B, 16, 30), _r(B, 16, 31)
    l, st = L.nce_cross_person(u1, u2, k, pid1, pid2, unknown_clock=())
    assert abs(float(l - symmetric_infonce(u1, u2, 0.1))) < 1e-12 and st["nopos_12"] == st["nopos_21"] == 0
    pself, u2s = pid2.clone(), u2.clone()
    pself[0], u2s[0] = pid1[0], u1[0]                                     # view-2 row 0 is view-1 row 0's own observation
    pos, excl = L.nce_masks(k, k, pid1, pself, unknown_clock=())
    assert not pos[0, 0] and excl[0, 0] and pos.diagonal()[1:].all() and not (pos & excl).any()
    l2, st2 = L.nce_cross_person(u1, u2s, k, pid1, pself, unknown_clock=())
    assert st2["nopos_12"] == st2["nopos_21"] == 1 and st2["n_q_12"] == B and math.isfinite(float(l2))
    S, q = _cos(u1, u2s), torch.arange(1, B)
    hand = (L.masked_lse_nce(S[q], pos[q], excl[q]).mean() + L.masked_lse_nce(S.T[q], pos.T[q], excl.T[q]).mean()) / 2
    assert abs(float(l2 - hand)) < 1e-12
    u1g = u1.clone().requires_grad_(True)
    L.nce_cross_person(u1g, u2s, k, pid1, pself, unknown_clock=())[0].backward()
    assert torch.isfinite(u1g.grad).all() and u1g.grad[1:].abs().sum() > 0
    la, sa = L.nce_cross_person(u1, u1.clone(), k, pid1, pid1, unknown_clock=())   # every view-2 row is the query's own observation
    assert sa["nopos_12"] == sa["nopos_21"] == B and float(la) == 0.0
    for a, b in ((pid1, None), (None, pself), (None, None)):              # ids omitted: refused, never silently unmasked
        with pytest.raises(ValueError, match="participant ids"):
            L.nce_cross_person(u1, u2s, k, a, b, unknown_clock=())
    pi = torch.tensor([1, 2, 0, 4, 5, 3])                                 # XM: X2[pi] with X1's keys
    assert torch.equal(L.nce_masks(k, k, pid1, pid2, unknown_clock=())[1], L.nce_masks(k, k, pid1, pid2[pi], unknown_clock=())[1])
    assert math.isfinite(float(L.nce_cross_person(u1, u2[pi], k, pid1, pid2[pi], unknown_clock=())[0]))
    kx = _keys(np.zeros(B), np.zeros(B), SIB[:B])                          # sibling anchors of one segment: masked, not positive
    px, ex = L.nce_masks(kx, kx, pid1, pid2, unknown_clock=())
    assert torch.equal(px, torch.eye(B, dtype=torch.bool)) and ex.sum() > 0 and not ex.diagonal().any()


# ---------------------------------------------------------------------------------------------------------- CS
def _cs_np(U, V, su, sv):
    """I = log A + log B - 2 log C, written out with the full Gaussian kernels (diagonal kept, uniform weights)."""
    U, V = np.asarray(U, np.float64), np.asarray(V, np.float64)
    K = np.exp(-((U[:, None] - U[None]) ** 2).sum(-1) / (2 * su ** 2))
    Lk = np.exp(-((V[:, None] - V[None]) ** 2).sum(-1) / (2 * sv ** 2))
    n = len(U)
    A, Bv, Cv = (K * Lk).sum() / n ** 2, (K.sum() / n ** 2) * (Lk.sum() / n ** 2), (K.sum(1) * Lk.sum(1)).sum() / n ** 3
    return np.log(A) + np.log(Bv) - 2 * np.log(Cv), (np.log(A), np.log(Bv), np.log(Cv))


def test_cs_full_kernel_equals_direct_numpy_evaluation():
    """§7.1 6: cs_audio_pair = cs_qmi with v duplicated = the numpy formula; cross_person symmetric; no mask argument; gradients."""
    B = 7
    u1, u2, v = _r(B, 4, 40, True), _r(B, 4, 41, True), _r(B, 4, 42, True)
    su, sv = 1.3, 0.9
    l, st = L.cs_audio_pair(u1, u2, v, su, sv)
    I, (la, lb, lc) = _cs_np(torch.cat([u1, u2]).detach(), torch.cat([v, v]).detach(), su, sv)
    assert abs(-float(l) - I) < 1e-10 and st["n_rows"] == 2 * B
    assert max(abs(st["log_joint_square"] - la), abs(st["log_marginal_product_square"] - lb), abs(st["log_cross_overlap"] - lc)) < 1e-10
    assert float(l) == -float(cs_qmi(torch.cat([u1, u2]), torch.cat([v, v]), sigma_u=su, sigma_v=sv)[0])
    lx, _ = L.cs_cross_person(u1, u2, su)
    Ix, _ = _cs_np(torch.cat([u1, u2]).detach(), torch.cat([u2, u1]).detach(), su, su)
    assert abs(-float(lx) - Ix) < 1e-10 and abs(float(L.cs_cross_person(u2, u1, su)[0] - lx)) < 1e-12
    for f, args in ((L.cs_audio_pair, ["u1", "u2", "v", "sigma_u", "sigma_v"]), (L.cs_cross_person, ["u1", "u2", "sigma_u"])):
        assert list(inspect.signature(f).parameters) == args              # no mask (or key) argument exists
    (l + lx).backward()
    assert all(torch.isfinite(x.grad).all() and x.grad.abs().sum() > 0 for x in (u1, u2, v))


def test_cs_narrow_kernel_limit_is_log_n_even_without_dependence():
    """§2.8, documented: as the bandwidths shrink, K and L tend to I and the estimator tends to log n whatever the dependence. With
    2B = 512 rows, cross_person (512 distinct rows) tends to log 512 = 6.24 nats; audio_pair repeats each v twice, so it tends to
    log(n / 2) = log 256 = 5.55 nats. Independent random rows reach both, so training values are not evidence of generalisation."""
    B = 256
    u1, u2, v = _r(B, 32, 50), _r(B, 32, 51), _r(B, 32, 52)              # mutually independent
    med = L.calibrate_sigma(torch.cat([u1, u2]))
    xp = [-float(L.cs_cross_person(u1, u2, med * f)[0]) for f in (1.0, 0.1, 1e-3)]
    ap = [-float(L.cs_audio_pair(u1, u2, v, med * f, med * f)[0]) for f in (1.0, 0.1, 1e-3)]
    assert abs(xp[-1] - math.log(2 * B)) < 1e-9 and abs(ap[-1] - math.log(B)) < 1e-9
    assert round(math.log(2 * B), 2) == 6.24 and round(math.log(B), 2) == 5.55
    assert xp[0] < 0.1 and ap[0] < 0.1                                    # calibrated bandwidth: near 0 for independent rows


def test_calibrate_sigma_rule():
    a, b = torch.randn(40, 32, generator=_g(60)), 3 * torch.randn(30, 32, generator=_g(61))
    ma, mb = _offdiag_median_dist(a), _offdiag_median_dist(b)
    assert L.calibrate_sigma(a) == ma and abs(L.calibrate_sigma([a, b], [0.75, 0.25]) - (0.75 * ma + 0.25 * mb)) < 1e-12
    assert abs(L.calibrate_sigma([a, b], [3, 1], multiplier=2.0) - 2 * (0.75 * ma + 0.25 * mb)) < 1e-12
    o = Objective({"objective": "CS_SINGLE", "config": {"bandwidth_multiplier": 1.0}}, a, b)
    assert (o.sigma_u, o.sigma_v) == (L.calibrate_sigma(a), L.calibrate_sigma(b))     # the target-stage Objective rule
    for args in (([a, b], [1.0]), ([a, b], [-1, 2]), ([], None), ([a, b], [0, 0]), (torch.zeros(5, 3), None)):
        with pytest.raises(ValueError):
            L.calibrate_sigma(*args)


# ---------------------------------------------------------------------------------------------------------- ContractObjective
def test_contract_objective_interface_and_rolled_keys(fx):
    """§2.5 / §7.1 4g on the loss side: the mask of a rolled early-stopping batch is the rolled audio's mask; labels and CS unchanged."""
    job = JOB
    n_seg, A = 3, 8
    fam, pres = np.repeat([9, 9, 11], A), np.repeat([0, 1, 2], A)       # segments 0 and 1: two presentations of one family
    s = np.tile(SIB, n_seg) + np.repeat([0, 100, 0], A)                   # whose family clocks overlap within 2 s
    k = _keys(fam, pres, s)
    u, v = _r(n_seg * A, 32, 70), _r(n_seg * A, 32, 71)
    obj, ref = L.ContractObjective(job, u, v, unknown_clock=()), Objective(job, u, v)
    assert (obj.sigma_u, obj.sigma_v, obj.ridge_u, obj.ridge_v, obj.temperature) == (ref.sigma_u, ref.sigma_v, ref.ridge_u, ref.ridge_v, 0.1)
    rec = obj.record()
    assert rec["nce"] == "contract_lse_mask2s_v1" and rec["neighbor_samples"] == 128 and {x: rec[x] for x in ref.record()} == ref.record()
    l, st = obj(u, v, keys=k)
    assert float(l) == float(L.nce_single_view(u, v, k, unknown_clock=())[0]) and st["masked_per_q_uv"] > 0
    src = np.roll(np.arange(n_seg), 1)                                    # fit_continuous roll: audio (and keys) of the next segment
    rows = (src[:, None] * A + np.arange(A)[None]).reshape(-1)
    kr, vr, fr, sr = k[rows], v[rows], fam[rows], s[rows]
    E = torch.as_tensor((fr[:, None] == fr[None]) & (np.abs(sr[:, None] - sr[None]) <= 128) & ~np.eye(len(rows), dtype=bool))
    lr_, _ = obj(u, vr, keys=kr)
    assert abs(float(lr_ - _hand_nce(_cos(u, vr), E))) < 1e-12
    assert torch.equal(L.nce_masks(kr, kr, unknown_clock=())[1], E) and not torch.equal(E, L.nce_masks(k, k, unknown_clock=())[1])
    y, protos = torch.tensor([0, 1] * 12), _r(2, 32, 80)
    assert float(obj(u, labels=y, prototypes=protos)[0]) == float(prototype_nce(u, y, protos, 0.1))
    cjob = {**job, "objective": "CS_SINGLE"}
    a, sa = L.ContractObjective(cjob, u, v, unknown_clock=())(u, v, keys=k)
    b, sb = Objective(cjob, u, v)(u, v, keys=k)
    assert float(a) == float(b) and sa == sb
    for name in ("FMCA", "CS_MULTI"):
        with pytest.raises(ValueError):
            L.ContractObjective({**job, "objective": name}, u, v, unknown_clock=())
    with pytest.raises(ValueError):
        obj(u, v)                                                         # the contract NCE needs the packed keys
    uc = L.unknown_clock_families(fx["manifest"])
    ou = L.ContractObjective(job, u, v, unknown_clock=uc)
    assert ou.record()["unknown_clock_families"] == fx["truth"]["unknown_clock_families"]
    ku = _keys(np.full(len(rows), uc[0]), pres + 40, s + 600 * pres)      # one unknown-clock family, items > 2 s apart
    assert float(ou(u, v, keys=ku)[0]) < float(obj(u, v, keys=ku)[0])


def test_target_stage_usage_pattern(fx, canon):
    """The calls of the generated target copy (local_train.fit_continuous with the §2.12 substitutions) on synthetic rows: the
    strictly loaded encoder, the shared fixed head, ContractObjective calibration, one clipped AdamW step and the logged diagnostics."""
    from auditory_alignment.train import _eff_rank, _kernel_stats, cs_diag
    man = fx["manifest"]
    head = M.fixed_heads(canon["manifest"], canon["root"])["env"]
    state = _donor(fx, "fau").state_dict()
    fam = np.repeat(np.arange(4) + 1, 8)
    keys, patches, audio = _keys(fam, fam, np.tile(SIB, 4)), [_x(32, 31, 90)], torch.randn(32, 8, generator=_g(91))
    for name in ("NCE", "CS_SINGLE"):
        enc = M.build_target_encoder(_row("fau", "donor", objective=name), FAU, man, state)
        params = [p for m in (enc, head) for p in m.parameters() if p.requires_grad]
        opt = torch.optim.AdamW(params, lr=1e-3, weight_decay=1e-4)
        job = {**JOB, "objective": name}
        with torch.no_grad():
            obj = L.ContractObjective(job, enc(patches), head(audio), unknown_clock=L.unknown_clock_families(man))
        loss, _ = obj(enc(patches), head(audio), keys=keys)
        opt.zero_grad()
        loss.backward()
        gn = float(torch.nn.utils.clip_grad_norm_(params, 5.0))
        assert math.isfinite(gn) and gn > 0 and bool(torch.isfinite(loss)) and len(params) == 13
        opt.step()
        with torch.no_grad():
            u, v = enc(patches), head(audio)
            st = cs_diag(u, v, sigma_u=obj.sigma_u, sigma_v=obj.sigma_v)
            assert math.isfinite(st["cs_qmi_nats"]) and _eff_rank(u) > 1 and _kernel_stats(u, obj.sigma_u)["k_off_mean"] > 0
        assert obj.record()["sigma_v"] == obj.sigma_v > 0 and M.describe(enc)["tensor_map"]["opened_rows"] == ["F9", "F10"]


# ---------------------------------------------------------------------------------------------------------- rich
def test_rich_loss_masks_missing_targets_and_keeps_the_scale():
    """§2.15 / §7.1 12: missing targets are masked, never zero-filled; the normalised scale is the same for one head and three."""
    B = 16
    k = _keys(np.arange(B) // 8 + 1, np.arange(B) // 8 + 1, np.tile(SIB, 2))
    U = {h: (F.normalize(_r(B, 32, 100 + i), dim=1).requires_grad_(True), F.normalize(_r(B, 32, 110 + i), dim=1).requires_grad_(True))
         for i, h in enumerate(R.HEADS)}
    V = {h: F.normalize(_r(B, 32, 120 + i), dim=1) for i, h in enumerate(R.HEADS)}
    nce = {"keys": k, "unknown_clock": ()}
    le, ls, lc = (L.nce_audio_pair(*U[h], V[h], k, unknown_clock=())[0] for h in R.HEADS)
    l3, st = R.rich_loss(U, V, {"ss": True, "sc": True}, "NCE", **nce)
    assert abs(float(l3 - (le + 0.5 * ls + 0.5 * lc) / 2.0)) < 1e-12 and st["norm"] == 2.0 and st["rows_ss"] == st["rows_sc"] == B
    l1, st1 = R.rich_loss({"env": U["env"]}, {"env": V["env"], "ss": None, "sc": None}, {"ss": False, "sc": False}, "NCE", **nce)
    assert abs(float(l1 - le)) < 1e-12 and st1["norm"] == 1.0 and st1["rows_ss"] == st1["rows_sc"] == 0       # a Federici batch
    same = R.rich_loss({h: U["env"] for h in R.HEADS}, {h: V["env"] for h in R.HEADS}, {"ss": True, "sc": True}, "NCE", **nce)[0]
    assert abs(float(same - le)) < 1e-12                                  # equal heads: the same scale as the envelope alone
    m = torch.ones(B, dtype=torch.bool)
    m[:3] = False                                                         # rows of a stream without a rich target
    svn, svz = V["ss"].clone(), V["ss"].clone()
    svn[:3], svz[:3] = float("nan"), 0.0
    lm, stm = R.rich_loss(U, {**V, "ss": svn}, {"ss": m, "sc": True}, "NCE", **nce)
    ls_m = L.nce_audio_pair(U["ss"][0][m], U["ss"][1][m], V["ss"][m], k[m], unknown_clock=())[0]
    assert math.isfinite(float(lm)) and stm["rows_ss"] == B - 3 and abs(float(lm - (le + 0.5 * ls_m + 0.5 * lc) / 2.0)) < 1e-12
    assert abs(float(R.rich_loss(U, {**V, "ss": svz}, {"ss": True, "sc": True}, "NCE", **nce)[0] - lm)) > 1e-6   # zero fill differs
    lm.backward()
    g = U["ss"][0].grad
    assert (g[:3] == 0).all() and g[3:].abs().sum() > 0                   # masked rows: no gradient
    for t in (x for p in U.values() for x in p):
        t.grad = None
    lg, _ = R.rich_loss(U, {**V, "sc": None}, {"ss": True}, "NCE", **nce)
    lg.backward()
    assert U["sc"][0].grad is None and U["sc"][1].grad is None and U["ss"][0].grad.abs().sum() > 0      # absent head: no gradient
    sig = {"env": (0.7, 0.8), "ss": (0.6, 0.9), "sc": {"sigma_u": 0.5, "sigma_v": 1.1}}
    lcs, _ = R.rich_loss(U, V, {"ss": True, "sc": True}, types.SimpleNamespace(name="CS_SINGLE"), sig)
    parts = [L.cs_audio_pair(*U[h], V[h], *s_)[0] for h, s_ in (("env", (0.7, 0.8)), ("ss", (0.6, 0.9)), ("sc", (0.5, 1.1)))]
    assert abs(float(lcs - (parts[0] + 0.5 * parts[1] + 0.5 * parts[2]) / 2)) < 1e-12
    for args in ((U, V, {"env": m}), (U, {**V, "ss": svn}, {"ss": True}), (U, {**V, "ss": None}, {"ss": True}),
                 (U, V, {"ss": torch.ones(B - 1, dtype=torch.bool)})):
        with pytest.raises(ValueError):
            R.rich_loss(*args, "NCE", **nce)
    with pytest.raises(ValueError):
        R.rich_loss(U, V, {"ss": True}, "FMCA", **nce)


def test_rich_loss_signature_and_objective_inputs():
    """Design §6.1 rich_loss(u_heads, v_heads, present, objective), with the M4 task's sigmas as an optional fifth argument: each
    objective checks only its own inputs (CS_SINGLE: sigmas; NCE: the keys and the unknown-clock families, keyword-only)."""
    prm = inspect.signature(R.rich_loss).parameters
    assert list(prm)[:5] == ["u_heads", "v_heads", "present", "objective", "sigmas"] and prm["sigmas"].default is None
    assert all(prm[p].kind is inspect.Parameter.KEYWORD_ONLY for p in ("keys", "unknown_clock", "temperature"))
    B = 8
    k = _keys(np.ones(B), np.ones(B), SIB)
    U = {h: (F.normalize(_r(B, 32, 160 + i), dim=1), F.normalize(_r(B, 32, 170 + i), dim=1)) for i, h in enumerate(R.HEADS)}
    V = {h: F.normalize(_r(B, 32, 180 + i), dim=1) for i, h in enumerate(R.HEADS)}
    sig, both = {h: (0.8, 0.9) for h in R.HEADS}, {"ss": True, "sc": True}
    l4 = R.rich_loss(U, V, both, "NCE", keys=k, unknown_clock=())[0]                  # the design's four positional arguments
    assert float(l4) == float(R.rich_loss(U, V, both, "NCE", sig, keys=k, unknown_clock=())[0])   # sigmas unused by NCE
    lc = R.rich_loss(U, V, both, "CS_SINGLE", sig)[0]                                 # the M4 task's five-argument form
    exp = sum(R.RICH_WEIGHTS[h] * L.cs_audio_pair(*U[h], V[h], 0.8, 0.9)[0] for h in R.HEADS) / 2
    assert abs(float(lc - exp)) < 1e-12
    with pytest.raises(ValueError, match="sigmas"):
        R.rich_loss(U, V, both, "CS_SINGLE")
    with pytest.raises(ValueError, match="keys"):
        R.rich_loss(U, V, both, "NCE", unknown_clock=())
    with pytest.raises(ValueError, match="unknown_clock"):
        R.rich_loss(U, V, both, "NCE", keys=k)
    with pytest.raises(TypeError):
        R.rich_loss(U, V, both, "NCE", None, k)                                       # keys are keyword-only


def test_rich_readout_matches_ev1_and_masks_missing_targets():
    """§2.15 Downstream (descriptive): per head, the §2.10 ridge (intercept, penalty 1e-2 mean diag(U^T U), no search) on the fit
    segments and r_bar = mean S(q, own) on the bridge_cal segments, equal to ev1._ridge / ev1._zt; segments without a target (NaN)
    are left out, never zero-filled; a head without any present segment is reported as None."""
    from auditory_alignment.evaluate import _apply, _ridge, _zt
    rng = np.random.default_rng(150)
    nf, nc, T = 10, 6, 50
    yf = {"ss": rng.standard_normal((nf, T, 32)), "sc": rng.standard_normal((nf, T, 8))}
    yc = {"ss": rng.standard_normal((nc, T, 32)), "sc": rng.standard_normal((nc, T, 8))}
    Q = np.linalg.qr(rng.standard_normal((32, 32)))[0]
    Uf, Uc = yf["ss"] @ Q + 0.3 * rng.standard_normal((nf, T, 32)), yc["ss"] @ Q + 0.3 * rng.standard_normal((nc, T, 32))
    out = R.rich_readout(Uf, yf, Uc, yc)
    for h in ("ss", "sc"):
        D = yc[h].shape[2]
        X, Y = Uf.reshape(-1, 32), yf[h].reshape(-1, D)
        alpha = 1e-2 * np.mean(np.diag(X.T @ X))
        B, _ = _ridge(X, Y, [alpha])
        P = _apply(B, Uc.reshape(-1, 32)).reshape(nc, T, D)
        s_own = np.einsum("qtd,qtd->q", _zt(P), _zt(yc[h])) / (T * D)
        o = out[h]
        assert abs(o["r_bar"] - s_own.mean()) < 1e-10 and abs(o["alpha"] - alpha) <= 1e-12 * alpha and len(o["r_dim"]) == D
        assert (o["n_fit"], o["n_fit_missing"], o["n_cal"], o["n_cal_missing"], o["dims"], o["rel_ridge"]) == (nf, 0, nc, 0, D, 1e-2)
    assert out["ss"]["r_bar"] > 0.5 and abs(out["sc"]["r_bar"]) < 0.1    # u carries y_ss, not the independent y_sc
    noise = R.rich_readout(rng.standard_normal(Uf.shape), {"ss": yf["ss"]}, rng.standard_normal(Uc.shape), {"ss": yc["ss"]})
    assert abs(noise["ss"]["r_bar"]) < 0.1                                # an encoder without the target: about 0
    tt = {h: torch.from_numpy(y) for h, y in yf.items()}, {h: torch.from_numpy(y) for h, y in yc.items()}
    assert R.rich_readout(torch.from_numpy(Uf), tt[0], torch.from_numpy(Uc), tt[1]) == out
    yfm, ycm = {h: y.copy() for h, y in yf.items()}, {h: y.copy() for h, y in yc.items()}
    yfm["ss"][2], ycm["ss"][[1, 4]] = np.nan, np.nan                      # streams without a usable waveform: missing, not 0
    om = R.rich_readout(Uf, yfm, Uc, ycm)
    kf, kc = [i for i in range(nf) if i != 2], [0, 2, 3, 5]
    sub = R.rich_readout(Uf[kf], {"ss": yf["ss"][kf]}, Uc[kc], {"ss": yc["ss"][kc]})["ss"]
    assert abs(om["ss"]["r_bar"] - sub["r_bar"]) < 1e-12 and om["sc"] == out["sc"]
    assert (om["ss"]["n_fit"], om["ss"]["n_fit_missing"], om["ss"]["n_cal"], om["ss"]["n_cal_missing"]) == (nf - 1, 1, nc - 2, 2)
    zf, zc = np.nan_to_num(yfm["ss"]), np.nan_to_num(ycm["ss"])
    assert abs(R.rich_readout(Uf, {"ss": zf}, Uc, {"ss": zc})["ss"]["r_bar"] - om["ss"]["r_bar"]) > 1e-3   # zero fill differs
    none = R.rich_readout(Uf, {"ss": yf["ss"]}, Uc, {"ss": np.full_like(yc["ss"], np.nan)})["ss"]
    assert none["r_bar"] is None and none["r_dim"] is None and (none["n_cal"], none["n_cal_missing"]) == (0, nc)
    with pytest.raises(ValueError):
        R.rich_readout(Uf, yf, Uc, {"ss": yc["ss"]})                      # the heads differ between fit and bridge_cal
    with pytest.raises(ValueError):
        R.rich_readout(Uf, {"ss": yf["ss"][:, :40]}, Uc, {"ss": yc["ss"]})   # targets not on u's ticks
    with pytest.raises(ValueError):
        R.rich_readout(Uf[..., :16], yf, Uc, yc)                          # fit and bridge_cal u of different width
