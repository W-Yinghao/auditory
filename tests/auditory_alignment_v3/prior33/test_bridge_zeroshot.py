"""M6 bridge and zero-shot tests (PUBLIC_PRIOR_DESIGN.md §2.11, §2.13, §6.6 M6, §7.1 item 9): the bridge is fitted on donor data
only (no file, row or participant of the target cohort; identical rows for every member), its ridges and temperatures follow ev1
(ev1._ridge, ev1.Readouts.calibrate), B_uni_cal is fitted on its fixed bridge_cal pool rows (not the queries), the npz round trip
(allow_pickle=False), FrozenBridge defines what ev1 reads and refuses any fit, the frozen evaluation equals the reference ev1
path given the same readout, the zero-shot pool equals the adapted rows' pool (also a real M7 unit's), only the fold's test rows
are read (NaN poisoning), the access modes A / B / C / C_partial, the private cohort gets no speech zero-shot, the pool entry
points write records with the M11 fields and the accounting (parsed by prior33.analysis), a bridge of another checkpoint is
refused, failures are records (also when core.bind raises), the zero-shot path imports only its code group, and a target
participant's statistics reach neither the bridge nor the mode-C input. The last block runs the REAL M9 rows
(make_plan_ext_prior33.build_primary on the synthetic manifest) for every slot (AP, XP, J*, XM, APR, APC, XPC; J* resolved to
J025 and, on a tie, J1), both objectives, and recomputes the temperatures independently in an interior (noisy) case.
Synthetic data only (fixtures.py, scale 1); CPU; about 3-4 minutes and < 1.5 GB RSS on an idle node."""
import ast
import contextlib
import copy
import hashlib
import importlib.util
import json
import math
import os
import shutil
import sys

import numpy as np
import pytest
import torch

from auditory_alignment import evaluate as ev1
from auditory_alignment_v2 import evaluate as ev2
from auditory_alignment_v3 import core
from auditory_alignment_v3.prior33 import bridge as BR
from auditory_alignment_v3.prior33 import contract as C
from auditory_alignment_v3.prior33 import deps as D
from auditory_alignment_v3.prior33 import model as M
from auditory_alignment_v3.prior33 import run_bridge as RB
from auditory_alignment_v3.prior33 import run_zeroshot as RZ
from auditory_alignment_v3.prior33 import sampler as SM
from auditory_alignment_v3.prior33 import select as SEL
from auditory_alignment_v3.prior33 import views as V
from auditory_alignment_v3.prior33 import zeroshot as ZS

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from fixtures import make_synthetic_manifest  # noqa: E402

PKG = os.path.normpath(os.path.join(HERE, "..", "..", "..", "auditory_alignment_v3", "prior33"))
_P33 = lambda *fs: [("auditory_alignment_v3", "core.py"), ("auditory_alignment_v3", "local_train.py")] + \
    [("auditory_alignment_v3/prior33", f) for f in fs]   # noqa: E731 (design §6.3 registry snippet)
DESIGN_CODE = {"prior33_bridge": _P33("contract.py", "views.py", "model.py", "losses.py", "sampler.py", "select.py", "bridge.py",
                                      "run_bridge.py"),
               "prior33_zeroshot": _P33("contract.py", "views.py", "model.py", "select.py", "bridge.py", "zeroshot.py", "run_zeroshot.py")}
SK = C.MONTAGES["sparrkulee"]

# ---------------------------------------------------------------------------------------------------------- open-file audit hook
_OPENED = None


def _audit(event, args):
    if _OPENED is not None and event == "open" and args and isinstance(args[0], (str, bytes, os.PathLike)):
        _OPENED.append(os.path.abspath(os.fsdecode(args[0])))


sys.addaudithook(_audit)


@contextlib.contextmanager
def opened_files():
    global _OPENED
    _OPENED = []
    try:
        yield _OPENED
    finally:
        _OPENED = None


# ---------------------------------------------------------------------------------------------------------- fixtures
@pytest.fixture(scope="module", autouse=True)
def small_chunks():
    old = BR.CHUNK
    BR.CHUNK = 8                       # 2,000 windows per encoder pass on the CPU (memory)
    yield
    BR.CHUNK = old


@pytest.fixture(scope="module")
def fx(tmp_path_factory):
    return make_synthetic_manifest(tmp_path_factory.mktemp("m6_fx1"))


@pytest.fixture(scope="module")
def man(fx):
    return V.open_manifest(fx["manifest_path"], fx["manifest_sha256"])


def donor_state(man, target, seed=3401, sigma=True):
    """A donor member checkpoint: a SharedEncoder trained on the leave-target-out donor union (random weights)."""
    enc = M.build_shared(SK, man["seen"][target], seed)
    return {"enc": enc.state_dict(), **({"sigma_u": 0.9, "sigma_v": 1.1} if sigma else {})}


def m5_ckpt(man, target, gid, member, seed, objective="NCE"):
    """A member checkpoint in donor_train.py's format prior33_donor_member_v1 (bandwidths under "sigma", the fixed head)."""
    enc = M.build_shared(SK, man["seen"][target], seed, rich=member == "APR")
    head = M.fixed_heads(man, man.root)["env"]
    return {"format": BR.CKPT_FORMAT, "group": gid, "member": member, "kind": "best", "enc": enc.state_dict(), "head": head.state_dict(),
            "sigma": {"sigma_u": 0.8, "sigma_v": 1.2, "multiplier": 1.0, "rule": "synthetic", "strata": {}}, "objective": objective,
            "loss": "audio_pair", "lambda": 0.0, "validation": {"ce_dev": 5.0}, "layout": list(SK), "seen": enc.seen_names(),
            "rich_heads": member == "APR", "manifest_sha256": man.sha256, "donor_seed": 3401, "contract": C.CONTRACT}


@pytest.fixture(scope="module")
def states(man):
    return {t: donor_state(man, t) for t in ("fau", "dtu", "federici", "private_bdf")}


def fit(man, state, target, objective="NCE", slot="AP", bid="ALN3X_" + "b" * 16, gid="ALN3X_" + "a" * 16):
    enc, _ = BR.donor_encoder(state, man, target, "cpu")
    return BR.fit_bridge(enc, man, target, objective, slot=slot, member=slot if slot != "J*" else "J1", bridge_id=bid, donor_group=gid,
                         sigma=BR.donor_bandwidths(state), device="cpu", root=man.root)


@pytest.fixture(scope="module")
def bridges(man, states):
    return {(t, o): fit(man, states[t], t, o) for t, o in (("fau", "NCE"), ("fau", "CS_SINGLE"), ("dtu", "NCE"), ("federici", "NCE"))}


def zs_row(man, ds, sf, cf, mode="A", objective="NCE", member="AP", **kw):
    cell = V.manifest_cell(man, ds, sf, cf)
    spec = {"stage": "zero_shot", "objective": objective, "mode": mode, "member": member, "architecture": "lag_local_tokens",
            "window": "full", "target": "envelope", "view": ZS.VIEW_RULE, "split_hash": cell["split_hash"],
            "manifest_sha256": man.sha256, "target_contract": man["target_contract"], **kw}
    return {"experiment_id": "ALN3X_" + "c" * 16, "family_id": SEL.ZEROSHOT, "dataset": ds, "subject_fold": sf, "content_fold": cf,
            "seed": 3401, "spec": spec}


def reference_eval(man, state, ds, sf, cf, objective="NCE"):
    """The reference ev1 path of an adapted row of the cell: all participants, the fold's training participants (TickBatcher
    default), ev1.Readouts fitted on them, ev1.Reps = TickReps; the same donor encoder as the zero-shot path. -> (out, readout)."""
    coh = V.target_view(ds, cf, man, "A")
    b = core.bind(BR.bindable(zs_row(man, ds, sf, cf, objective=objective)))
    bt = V.TickBatcher(coh, b["spec"], b, "cpu", man)
    enc, _ = BR.donor_encoder(state, man, ds, "cpu", layout=coh.layout)
    head = M.fixed_heads(man, man.root)["env"].eval()
    got = {}

    class Capture(ev1.Readouts):
        def __init__(self, *a, **k):
            super().__init__(*a, **k)
            got["ro"] = self

    orig = (ev1.Reps, ev1.Readouts)
    ev1.Reps, ev1.Readouts = V.TickReps, Capture
    try:
        out = ev2.evaluate_continuous(b, enc, head, bt, coh, {"sigma_u": 0.9, "sigma_v": 1.1}, None)
    finally:
        ev1.Reps, ev1.Readouts = orig
    return out, got["ro"], coh


def bridge_from_readout(ro, objective, sigma=(0.9, 1.1)):
    """A BridgeData holding exactly the parameters of a fitted ev1.Readouts (tau constant over the pool table)."""
    n = len(BR.POOL_SIZES)
    tu, tn = np.full(n, ro.tau["unified"]), np.full(n, ro.tau["native"])
    cs = objective == "CS_SINGLE"
    return BR.BridgeData(objective=objective, B_uni=ro.B_uni, alpha_uni=ro.alpha_uni, a_mu=ro.a_mu, a_sd=ro.a_sd,
                         B_nat=ro.B_nat if cs else None, alpha_nat=ro.alpha_nat if cs else None,
                         pool_sizes=np.asarray(BR.POOL_SIZES), pool_realised=np.asarray(BR.POOL_SIZES), tau_unified=tu, tau_native=tn,
                         B_uni_cal=ro.B_uni, alpha_uni_cal=ro.alpha_uni, tau_cal=tu, tau_cal_folds=np.ones((2, n)), sigma_u=sigma[0],
                         sigma_v=sigma[1], native="ridge" if cs else "cosine", native_applicable=True, meta={"bridge_id": "ref"})


def _table(fx, c):
    info = fx["manifest"]["cohorts"][c]
    with open(os.path.join(fx["root"], info["dir"], info["table"])) as f:
        t = json.load(f)
    return t, t[info["items"]]


def _rows_to_pieces(items, rows):
    cached = sorted((int(it["row_offset"]), i) for i, it in enumerate(items) if it["row_offset"] is not None)
    starts = np.array([a for a, _ in cached])
    return np.array([cached[k][1] for k in np.searchsorted(starts, rows, side="right") - 1])


# ---------------------------------------------------------------------------------------------------------- donor data only
def test_bridge_is_fitted_on_donor_data_only(fx, man, states, bridges):
    """§2.11 / §3.1 / inherited contract source_sound_bridge (fit donor_fit_only, calibrate donor_development_only): no file of the
    target cohort is opened, every fit row is a donor-fit row of a donor cohort of the target's donor set (no target id), the
    calibration rows are SparrKULee bridge_cal, nothing of a restricted participant is opened; the rows equal the manifest's and are
    identical for every member (two encoders, two objectives)."""
    root = os.path.abspath(fx["root"])
    for target in ("fau", "dtu", "federici", "private_bdf"):
        with opened_files() as seen:
            b = fit(man, states[target], target, "NCE", "XP")
        tdir = os.path.join(root, man["cohorts"][target]["dir"]) + os.sep if target in man["cohorts"] else None
        assert seen and (tdir is None or not [p for p in seen if p.startswith(tdir)]), target
        assert not [p for p in seen if os.sep + "raw" + os.sep in p and "sparrkulee" in p]          # restricted decoy never opened
        strata = man["donor_sets"][target]["core"]["strata"]
        assert target not in b.meta["fit_cohorts"] and set(b.meta["fit_cohorts"]) <= {SM.coh_of(s) for s in strata}
        assert target not in b.meta["fit_participants"] and "private_bdf" not in b.meta["fit_participants"]
        br = SM.bridge_rows(man, target)
        S = {c: man["segments"][c] for c in man["segments"]}
        for s, sset in br["fit"].items():
            c = SM.coh_of(s)
            t, _ = _table(fx, c)
            donors = {str(p["participant"]) for p in t["participants"] if p.get("donor", True) and not p.get("test_only")}
            assert set(map(str, sset.participant)) <= donors and set(map(str, sset.participant)) <= set(b.meta["fit_participants"][c])
            assert all(S[c]["role"][r] == "fit" for r in sset.rows)
        assert sorted(b.meta["fit_participants"]) == sorted({SM.coh_of(s) for s in br["fit"]})
        assert b.meta["cal_participants"] == sorted({"061", "062"}) and not set(V.RESTRICTED) & set(b.meta["fit_participants"].get("sparrkulee", []))
        assert b.meta["fit_rows_sha256"] == BR.sha_json({"target": target, "order": br["order"]})
        assert b.info["counts"]["fit_rows"] == len(br["order"]) * C.SEG_TICKS
        assert b.info["counts"]["cal_rows"] == len(man["bridge"]["cal_queries"]) * C.SEG_TICKS
        uc = BR.uni_cal_sample(man)                                     # B_uni_cal rows: SparrKULee bridge_cal, the cal_split listeners
        assert all(S["sparrkulee"]["role"][r] == "bridge_cal" for r in uc["set"].rows) and set(uc["set"].rows) <= set(man["pools"]["bridge_cal"]["sparrkulee"])
        assert b.meta["uni_cal_participants"] == sorted({"061", "062"}) and b.meta["uni_cal_rows_sha256"] == uc["rows_sha256"]
        assert b.info["counts"]["uni_cal_rows"] == len(uc["set"]) * C.SEG_TICKS == b.info["counts"]["n_audio_eeg_pairs_uni_cal"]
        assert b.info["counts"]["n_audio_eeg_pairs"] == (len(br["order"]) + len(man["bridge"]["cal_queries"])) * C.SEG_TICKS
    other = fit(man, donor_state(man, "fau", seed=7), "fau", "CS_SINGLE", "J*")
    for k in ("fit_rows_sha256", "cal_rows_sha256", "uni_cal_rows_sha256", "tau_draws_sha256"):
        assert other.meta[k] == bridges[("fau", "NCE")].meta[k]
    assert np.array_equal(other.pool_realised, bridges[("fau", "NCE")].pool_realised)
    assert not np.allclose(other.B_uni, bridges[("fau", "NCE")].B_uni)                          # a different member, same rows


def test_bridge_banks_hold_only_donor_rows(man):
    banks = BR.bridge_banks(man, "dtu", "cpu", man.root)
    assert "dtu" not in banks and set(banks) <= {"sparrkulee", "fau", "federici"}
    assert all(b.mode == "segments" for b in banks.values())
    assert set(banks["sparrkulee"].roles) == {"fit", "bridge_cal", "control_artefact"}
    assert all(b.roles == ("fit",) for c, b in banks.items() if c != "sparrkulee")


# ---------------------------------------------------------------------------------------------------------- ev1 semantics
def test_ridges_follow_ev1(man, bridges):
    """ridge_select reproduces ev1._ridge (alpha and B) for the corr and mse criteria; the 2-fold rule is the mean of the two
    directions with ev1's ridge per fold; the fitted bridge's alpha lies on the design grids and its curve is recorded."""
    g = np.random.default_rng(0)
    X, Xv = g.standard_normal((900, 32)), g.standard_normal((400, 32))
    W = g.standard_normal((32, 8))
    Y, Yv = X @ W + 3 * g.standard_normal((900, 8)), Xv @ W + 3 * g.standard_normal((400, 8))
    for crit, alphas, k in (("corr", BR.UNI_ALPHAS, 8), ("mse", BR.NAT_ALPHAS, 8)):
        B, a, curve = BR.ridge_select(X, Y[:, :k], alphas, Xv, Yv[:, :k], crit)
        Be, ae = ev1._ridge(X, Y[:, :k], alphas, Xv, Yv[:, :k], crit=crit)
        assert a == ae and np.array_equal(B, Be) and len(curve) == len(alphas)
    fold = np.r_[np.zeros(450, int), np.ones(450, int)]
    B_all, a2, (B0, B1), curve = BR.ridge_select_2fold(X, Y, fold, BR.UNI_ALPHAS)
    errs = []
    for al in BR.UNI_ALPHAS:
        e = []
        for k in (0, 1):
            Bk = ev1._ridge(X[fold == k], Y[fold == k], [al])[0]
            e.append(BR.ridge_err(np.c_[X[fold != k], np.ones((fold != k).sum())] @ Bk, Y[fold != k], "corr"))
        errs.append(np.mean(e))
    assert a2 == float(BR.UNI_ALPHAS[int(np.argmin(errs))])
    assert np.allclose(B_all, ev1._ridge(X, Y, [a2])[0]) and np.allclose(B0, ev1._ridge(X[fold == 0], Y[fold == 0], [a2])[0])
    for b in bridges.values():
        assert b.alpha_uni in set(BR.UNI_ALPHAS.tolist()) and b.alpha_uni_cal in set(BR.UNI_ALPHAS.tolist())
        assert len(b.info["alpha_curve_unified"]) == 13 and b.info["bridge_cal"]["corr_at_alpha"] == max(
            c["bridge_cal_corr"] for c in b.info["alpha_curve_unified"])
        assert (b.objective == "CS_SINGLE") == (b.B_nat is not None) and (b.alpha_nat in set(BR.NAT_ALPHAS.tolist()) or b.B_nat is None)
        assert np.array_equal(b.a_mu, np.zeros(8)) and np.allclose(b.a_sd, man["standardiser"]["sigma"], rtol=1e-6)


def test_tau_tables_pools_and_lookup(man, bridges):
    """tau(n): per query the own candidate (column 0) plus m - 1 distinct other candidates, m = min(n, n_cand), seed 20261017;
    the temperature is ev1.Readouts.calibrate's; zero-shot takes the entry nearest in log2 to the realised pool sizes (ties: the
    smaller n); tau_cal is the geometric mean of the two cross-fitted temperatures."""
    own = np.array([0, 3, 3, 7, 15, 2])
    d1, d2 = BR.pool_draws(own, 16), BR.pool_draws(own, 16)
    assert all(np.array_equal(d1[n], d2[n]) for n in BR.POOL_SIZES)
    assert not np.array_equal(BR.pool_draws(own, 16, seed=1)[64], d1[64])
    for n, cols in d1.items():
        assert cols.shape == (len(own), min(n, 16)) and np.array_equal(cols[:, 0], own)
        assert all(len(set(r.tolist())) == len(r) and r[0] not in r[1:].tolist() for r in cols) and cols.max() < 16
    big = BR.pool_draws(np.arange(5), 2000)
    assert [big[n].shape[1] for n in BR.POOL_SIZES] == list(BR.POOL_SIZES)
    S = {"unified": np.random.default_rng(1).standard_normal((6, 9)), "native": np.random.default_rng(2).standard_normal((6, 9))}

    class H:
        tau = None
    h = H()
    ev1.Readouts.calibrate(h, S, np.zeros(6, int))
    assert BR.calibrate_tau(S) == h.tau
    b = bridges[("fau", "NCE")]
    n_cand = len(SM.selection_sets(man)["bridge_cal"]["candidates"])
    assert list(b.pool_realised) == [min(n, n_cand) for n in BR.POOL_SIZES]
    assert np.allclose(b.tau_cal, np.sqrt(b.tau_cal_folds[0] * b.tau_cal_folds[1]))
    assert all((t > 0).all() for t in (b.tau_unified, b.tau_native, b.tau_cal))
    by = b.info["bridge_cal"]["by_pool_size"]["64"]
    assert by["realised"] == n_cand and "tau_unified_grid_edge" in by and by["unified"]["n_candidates"] == n_cand
    assert b.entry(3) == (0, 64, n_cand)                                                       # all realised sizes equal: first
    t = copy.copy(b)
    t.pool_realised = np.asarray(BR.POOL_SIZES)
    assert [t.entry(n)[1] for n in (1, 64, 90, 91, 181, 182, 700, 5000)] == [64, 64, 64, 128, 128, 256, 512, 1024]
    t.pool_realised = np.array([64, 128, 128, 512, 1024])                                      # a tie: the smaller n
    assert t.entry(128)[:2] == (1, 128)
    fb = BR.FrozenBridge.from_bridge(b, 8, "uni_cal")
    assert fb.tau == {"unified": float(b.tau_cal[0]), "native": float(b.tau_native[0])} and np.array_equal(fb.B_uni, b.B_uni_cal)


# ---------------------------------------------------------------------------------------------------------- independent recomputation
def _ridge(X, Y, a):
    X1 = np.c_[np.asarray(X, np.float64), np.ones(len(X))]
    R = a * np.eye(X1.shape[1])
    R[-1, -1] = 0
    return np.linalg.solve(X1.T @ X1 + R, X1.T @ np.asarray(Y, np.float64))


def _corr(P, Y):
    Pc, Yc = P - P.mean(0), Y - Y.mean(0)
    return float(np.mean((Pc * Yc).sum(0) / np.sqrt((Pc ** 2).sum(0) * (Yc ** 2).sum(0))))


def _apply(B, X):
    return np.c_[np.asarray(X, np.float64), np.ones(len(X))] @ B


def _unified(B, U, A, sd):
    """ev1's unified score of queries U [nq, T, 32] against candidate envelopes A [nc, T, 8] (mu = 0, scale sd): the mean product
    of the per-(segment, dimension) z-scores of the prediction and of the standardised target."""
    nq, T = U.shape[:2]
    P = _apply(B, U.reshape(-1, U.shape[-1])).reshape(nq, T, -1)
    Z = np.asarray(A, np.float64) / sd
    zt = lambda X: (X - X.mean(1, keepdims=True)) / (X.std(1, keepdims=True) + 1e-12)  # noqa: E731
    return np.einsum("qtd,ctd->qc", zt(P), zt(Z)) / (T * P.shape[2])


def _tau(S, own=None):
    """argmin of the candidate cross-entropy over logspace(-3, 2, 41) x sd(S) (the first minimum), own column 0 by default."""
    own = np.zeros(len(S), int) if own is None else own
    sd, best = S.std() + 1e-12, None
    for t in np.logspace(-3, 2, 41) * sd:
        z = S / t
        z = z - z.max(1, keepdims=True)
        ce = float(np.mean(np.log(np.exp(z).sum(1)) - z[np.arange(len(z)), own]))
        if best is None or ce < best[0]:
            best = (ce, t)
    return float(best[1])


@contextlib.contextmanager
def capture(noise=0.0):
    """Record the inputs and outputs of bridge.py's fitting primitives during fit_bridge / run_bridge (module globals of
    bridge.py): encode_segments (rows, montage flag, U, Y; with noise > 0 seeded Gaussian noise is added to U, so that retrieval
    is imperfect and the temperatures leave the grid edge), segment_targets, pool_draws, ridge_select and ridge_select_2fold."""
    cap = {"enc": [], "targets": [], "draws": [], "ridge": [], "ridge2": []}
    o = {n: getattr(BR, n) for n in ("encode_segments", "segment_targets", "pool_draws", "ridge_select", "ridge_select_2fold")}
    g = np.random.default_rng(7)

    def enc(e, bank, sset, **kw):
        U, Y = o["encode_segments"](e, bank, sset, **kw)
        if noise:
            U = (U + noise * g.standard_normal(U.shape)).astype(np.float32)
        cap["enc"].append({"cohort": bank.cohort, "rows": [int(r) for r in sset.rows], "montage_flag": kw.get("montage"),
                           "montage": None if sset.montage is None else list(sset.montage), "U": U.copy(), "Y": Y.copy(),
                           "participant": [str(p) for p in sset.participant]})
        return U, Y

    def targ(bank, pres, s):
        A = o["segment_targets"](bank, pres, s)
        cap["targets"].append({"pres": [int(p) for p in pres], "s": [int(x) for x in s], "A": A.copy()})
        return A

    def draws(own, n_cand, *a, **k):
        d = o["pool_draws"](own, n_cand, *a, **k)
        cap["draws"].append({n: v.copy() for n, v in d.items()})
        return d

    def ridge(X, Y, alphas, Xv, Yv, crit):
        cap["ridge"].append({"crit": crit, "alphas": [float(a) for a in alphas], "Y": np.array(Y, copy=True), "Yv": np.array(Yv, copy=True)})
        return o["ridge_select"](X, Y, alphas, Xv, Yv, crit)

    def ridge2(X, Y, fold, alphas, crit="corr"):
        cap["ridge2"].append({"crit": crit, "alphas": [float(a) for a in alphas], "n": len(X), "fold": np.array(fold, copy=True)})
        return o["ridge_select_2fold"](X, Y, fold, alphas, crit)

    for n, f in (("encode_segments", enc), ("segment_targets", targ), ("pool_draws", draws), ("ridge_select", ridge),
                 ("ridge_select_2fold", ridge2)):
        setattr(BR, n, f)
    try:
        yield cap
    finally:
        for n, f in o.items():
            setattr(BR, n, f)


def _calls(cap, rows):
    return [c for c in cap["enc"] if c["rows"] == [int(r) for r in rows] and c["montage_flag"] is False]


def recompute_bridge(man, cap, b):
    """Recompute B_uni, alpha_uni, tau(n) (unified; native for NCE = cosine), B_uni_cal (alpha by the 2-fold participant split on
    its own rows), the cross-fitted tau_cal(n) and bridge_cal_r from the captured inputs, independently of bridge.py; compare."""
    sd = np.asarray(man["standardiser"]["sigma"], dtype=np.float64)
    sel = SM.selection_sets(man)["bridge_cal"]
    q_rows, own = [int(r) for r in sel["queries"].rows], np.asarray(sel["own"])
    uc = BR.uni_cal_sample(man)
    fit_calls = [c for c in cap["enc"] if c["montage_flag"] is True]
    q_call, u_call = _calls(cap, q_rows)[0], _calls(cap, uc["set"].rows)[-1]
    X = np.concatenate([c["U"].reshape(-1, 32) for c in fit_calls]).astype(np.float64)
    Y = np.concatenate([c["Y"].reshape(-1, 8) for c in fit_calls]).astype(np.float64) / sd
    Uq = q_call["U"].astype(np.float64)
    Xv, Yv = Uq.reshape(-1, 32), q_call["Y"].reshape(-1, 8).astype(np.float64) / sd
    alphas = np.logspace(-4, 8, 13)
    crit = [_corr(_apply(_ridge(X, Y, a), Xv), Yv) for a in alphas]
    a_star = float(alphas[int(np.argmax(crit))])
    assert b.alpha_uni == a_star and np.allclose(b.B_uni, _ridge(X, Y, a_star), rtol=1e-7, atol=1e-9)
    A_c = cap["targets"][0]["A"].astype(np.float64)
    assert [(p, s) for p, s in zip(cap["targets"][0]["pres"], cap["targets"][0]["s"])] == \
        [(int(p), int(s)) for p, s in zip(sel["candidates"].presentation, sel["candidates"].s)]
    dr = cap["draws"][0]
    S_u = _unified(b.B_uni, Uq, A_c, sd)
    iq = np.arange(len(own))[:, None]
    for k, n in enumerate(BR.POOL_SIZES):
        assert np.array_equal(dr[n][:, 0], own)
        assert math.isclose(b.tau_unified[k], _tau(S_u[iq, dr[n]]), rel_tol=1e-6), n
    if b.objective == "NCE":                                             # native = cosine u . v (no fit)
        head = M.fixed_heads(man, man.root)["env"].eval()
        with torch.no_grad():
            V_c = head(torch.as_tensor(A_c.reshape(-1, 8), dtype=torch.float32)).numpy().reshape(A_c.shape[0], A_c.shape[1], -1)
        S_n = np.einsum("qtd,ctd->qc", Uq, V_c.astype(np.float64)) / Uq.shape[1]
        for k, n in enumerate(BR.POOL_SIZES):
            assert math.isclose(b.tau_native[k], _tau(S_n[iq, dr[n]]), rel_tol=1e-6), n
    assert math.isclose(b.info["bridge_cal"]["r_own_unified"], float(S_u[np.arange(len(own)), own].mean()), rel_tol=1e-6)
    # B_uni_cal: its own rows (not the queries), folds by bridge.cal_split, alpha by the mean of the two directions
    split = man["bridge"]["cal_split"]
    Xc = u_call["U"].reshape(-1, 32).astype(np.float64)
    Yc = u_call["Y"].reshape(-1, 8).astype(np.float64) / sd
    fold = np.repeat([0 if p in set(split[0]) else 1 for p in u_call["participant"]], C.SEG_TICKS)
    f0, f1 = fold == 0, fold == 1
    errs = [np.mean([_corr(_apply(_ridge(Xc[f0], Yc[f0], a), Xc[f1]), Yc[f1]), _corr(_apply(_ridge(Xc[f1], Yc[f1], a), Xc[f0]), Yc[f0])])
            for a in alphas]
    a_cal = float(alphas[int(np.argmax(errs))])
    assert b.alpha_uni_cal == a_cal and np.allclose(b.B_uni_cal, _ridge(Xc, Yc, a_cal), rtol=1e-7, atol=1e-9)
    fq = np.asarray([0 if str(p) in set(split[0]) else 1 for p in sel["queries"].participant])
    tf = np.empty((2, len(BR.POOL_SIZES)))
    for a in (0, 1):
        Ba = _ridge(Xc[fold == a], Yc[fold == a], a_cal)
        qb = np.flatnonzero(fq == 1 - a)                                 # tau on the OTHER fold's queries
        Sa = _unified(Ba, Uq[qb], A_c, sd)
        for k, n in enumerate(BR.POOL_SIZES):
            tf[a, k] = _tau(Sa[np.arange(len(qb))[:, None], dr[n][qb]])
    assert np.allclose(b.tau_cal_folds, tf, rtol=1e-6) and np.allclose(b.tau_cal, np.sqrt(tf[0] * tf[1]), rtol=1e-6)
    return {"crit": crit, "S_u": S_u}


def _variant_manifest(man):
    """The fixture manifest (same sha256 and root) with bridge.cal_queries = every second bridge_cal pool segment of each listener
    (the fixture lists the whole pool), so that the queries, the pool and B_uni_cal's rows differ."""
    data = copy.deepcopy(dict(man))
    P = data["segments"]["sparrkulee"]["participant"]
    by = {}
    for r in data["pools"]["bridge_cal"]["sparrkulee"]:
        by.setdefault(str(P[int(r)]), []).append(int(r))
    data["bridge"]["cal_queries"] = sorted(r for p in sorted(by) for r in by[p][::2])
    return V.Manifest(data, man.path, man.sha256, man.root)


def test_uni_cal_rows_are_a_fixed_balanced_bridge_cal_sample(man):
    """B_uni_cal's rows (§2.11 "bridge_cal rows"): N_UNI_CAL participant-balanced segments of pools.bridge_cal.sparrkulee, drawn
    exactly as manifest.py draws bridge.cal_queries (same water-filling rule, own generator SeedSequence([20261016, 0x43414C46])),
    deterministic, all rows when the pool is smaller, folds by bridge.cal_split; a split missing a participant is refused."""
    from auditory_alignment_v3.prior33 import manifest as MF
    g = np.random.default_rng(0)
    part = np.array([f"p{i % 6}" for i in range(5000)] + ["p6"] * 30)               # 6 large listeners and a small one
    rows = g.permutation(len(part))[:4200]
    for n in (2000, 301, 7):
        a = BR.balanced_rows(rows, part, n, np.random.default_rng(np.random.SeedSequence([C.BRIDGE_SEED, BR.UNI_CAL_TAG])))
        ref = MF._balanced(rows, part, n, np.random.default_rng(np.random.SeedSequence([C.BRIDGE_SEED, BR.UNI_CAL_TAG])))
        assert a == ref and len(a) == n == len(set(a)) and set(a) <= set(rows.tolist()) and a == sorted(a)
        c = {p: int((part[a] == p).sum()) for p in np.unique(part[rows])}
        big = [v for p, v in c.items() if p != "p6"]
        assert max(big) - min(big) <= 1 and c["p6"] == min(int((part[rows] == "p6").sum()), min(big)), (n, c)
    assert BR.balanced_rows(rows[:50], part, 2000, np.random.default_rng(1)) == sorted(rows[:50].tolist())
    uc, uc2 = BR.uni_cal_sample(man), BR.uni_cal_sample(man)
    pool = sorted(int(r) for r in man["pools"]["bridge_cal"]["sparrkulee"])
    assert uc["rows_sha256"] == uc2["rows_sha256"] and list(uc["set"].rows) == pool          # the fixture pool (32) < 2,000: all
    small = BR.uni_cal_sample(man, n=20)
    assert len(small["set"]) == 20 and small["participants"] == {"061": 10, "062": 10} and set(small["set"].rows) < set(pool)
    assert np.array_equal(small["fold"], [0 if p == "061" else 1 for p in small["set"].participant])
    assert small["rows_sha256"] != uc["rows_sha256"] and BR.uni_cal_sample(man, n=20)["rows_sha256"] == small["rows_sha256"]
    bad = V.Manifest(copy.deepcopy(dict(man)), man.path, man.sha256, man.root)
    bad["bridge"]["cal_split"] = [["061"], ["999"]]
    with pytest.raises(ValueError, match="cal_split"):
        BR.uni_cal_sample(bad)


def test_b_uni_cal_is_fitted_on_its_bridge_cal_rows_not_the_queries(man, states, monkeypatch):
    """With queries (16) != pool (32) != B_uni_cal rows (N_UNI_CAL = 20 here): B_uni is the donor-fit solution at the alpha chosen
    on the queries; B_uni_cal is fitted on its 20 balanced pool rows (full montage) with alpha by the 2-fold participant split on
    those rows; its tau is cross-fitted on the other fold's QUERIES; every value equals an independent recomputation; the counts
    and the accounting name the three row sets."""
    m2 = _variant_manifest(man)
    monkeypatch.setattr(BR, "N_UNI_CAL", 20)
    uc = BR.uni_cal_sample(m2)
    q = sorted(int(r) for r in m2["bridge"]["cal_queries"])
    assert len(q) == 16 and len(uc["set"]) == 20 and set(map(int, uc["set"].rows)) != set(q)
    with capture() as cap:
        b = fit(m2, states["dtu"], "dtu", "NCE", "AP")
    assert len(_calls(cap, q)) == 1 and len(_calls(cap, uc["set"].rows)) == 1
    r2 = cap["ridge2"][0]
    assert r2["n"] == 20 * C.SEG_TICKS and r2["alphas"] == [float(a) for a in np.logspace(-4, 8, 13)] and r2["crit"] == "corr"
    recompute_bridge(m2, cap, b)
    cnt = b.info["counts"]
    assert (cnt["cal_queries"], cnt["uni_cal_segments"], cnt["uni_cal_pool_segments"]) == (16, 20, 32)
    assert cnt["n_audio_eeg_pairs"] == cnt["fit_rows"] + 16 * C.SEG_TICKS and cnt["n_audio_eeg_pairs_uni_cal"] == 20 * C.SEG_TICKS
    assert cnt["n_audio_eeg_pairs_all"] == cnt["fit_rows"] + len(set(q) | set(map(int, uc["set"].rows))) * C.SEG_TICKS
    fr = b.info["uni_cal"]["fit_rows"]
    assert fr["segments"] == 20 and fr["per_participant"] == {"061": 10, "062": 10} and fr["rows_sha256"] == b.meta["uni_cal_rows_sha256"]
    acc = BR.accounting(b)
    assert (acc["n_pairs"], acc["n_pairs_uni_cal"], acc["n_pairs_all"]) == (cnt["n_audio_eeg_pairs"], cnt["n_audio_eeg_pairs_uni_cal"],
                                                                             cnt["n_audio_eeg_pairs_all"]) and acc["bridge_seconds"] >= 0


# ---------------------------------------------------------------------------------------------------------- npz round trip
def test_save_load_round_trip(man, bridges, tmp_path):
    """save_bridge / load_bridge: the §2.11 keys, numeric or unicode arrays only (np.load allow_pickle=False), every field equal
    after the round trip, the frozen readout's scores unchanged; a wrong id, a tampered meta and an object array are refused."""
    design = {"objective", "B_uni", "alpha_uni", "a_mu", "a_sd", "B_nat", "alpha_nat", "tau_unified", "tau_native", "B_uni_cal",
              "tau_cal", "sigma_u", "sigma_v", "fit_rows_sha256", "cal_rows_sha256"}
    g = np.random.default_rng(3)
    Uq, Vc, Ac = g.standard_normal((3, 250, 32)), g.standard_normal((5, 250, 32)), g.standard_normal((5, 250, 8))
    for (t, o), b in bridges.items():
        p = str(tmp_path / f"{t}_{o}_bridge.npz")
        BR.save_bridge(p, b)
        with np.load(p, allow_pickle=False) as z:
            keys = set(z.files)
            assert all(z[k].dtype.kind in "biufU" for k in keys)
        assert design <= keys and {"checkpoint_sha256", "uni_cal_rows_sha256"} <= keys and not os.path.exists(p + ".tmp")
        lb = BR.load_bridge(p, expect_id=b.meta["bridge_id"])
        for f in ("B_uni", "a_mu", "a_sd", "pool_sizes", "pool_realised", "tau_unified", "tau_native", "B_uni_cal", "tau_cal", "tau_cal_folds"):
            assert np.array_equal(getattr(lb, f), getattr(b, f)), f
        for f in ("objective", "alpha_uni", "alpha_nat", "alpha_uni_cal", "sigma_u", "sigma_v", "native", "native_applicable", "meta", "info"):
            assert getattr(lb, f) == getattr(b, f), f
        assert (lb.B_nat is None) == (o == "NCE") and (lb.B_nat is None or np.array_equal(lb.B_nat, b.B_nat))
        for view in BR.VIEWS:
            f0, f1 = b.frozen(8, view), lb.frozen(8, view)
            assert f0.tau == f1.tau and all(np.array_equal(f0.scores(Uq, Vc, Ac, k), f1.scores(Uq, Vc, Ac, k)) for k in ("unified", "native"))
        with pytest.raises(ValueError, match="expected"):
            BR.load_bridge(p, expect_id="ALN3X_" + "0" * 16)
    with np.load(p, allow_pickle=False) as z:
        d = {k: z[k] for k in z.files}
    q = str(tmp_path / "tampered.npz")
    for k, v in (("member", "XM"), ("checkpoint_sha256", "0" * 64), ("uni_cal_rows_sha256", "1" * 64)):
        np.savez(q, **dict(d, **{k: np.asarray(v)}))
        with pytest.raises(ValueError, match=k):
            BR.load_bridge(q)
    np.savez(q, **dict(d, B_uni=np.array([object()], dtype=object)))
    with pytest.raises(ValueError):
        BR.load_bridge(q)


# ---------------------------------------------------------------------------------------------------------- frozen readout
def _attrs_read(func, name):
    """Attribute names loaded on the variable `name` in the source of `func`."""
    import inspect
    import textwrap
    tree = ast.parse(textwrap.dedent(inspect.getsource(func)))
    return {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and n.value.id == name
            and isinstance(n.ctx, ast.Load)}


def test_frozen_bridge_defines_what_ev1_reads_and_fits_nothing(fx, man, states, bridges, monkeypatch):
    """§2.13 / §7.1 9: FrozenBridge defines every attribute ev1.evaluate_continuous and Readouts.scores read (AST of ev1's source;
    FMCA-only attributes excepted), calibrate raises, a batcher with target training participants is refused, and during the
    evaluation ev1._ridge raises; ev1's globals are restored afterwards, also after a refusal."""
    read = _attrs_read(ev1.evaluate_continuous, "ro") | _attrs_read(ev1.Readouts.scores, "self")
    fmca = {"Wu", "Wv", "rho", "mu_u", "mu_v"}
    need = read - fmca - {"scores", "calibrate"}
    assert {"objective", "B_uni", "alpha_uni", "a_mu", "a_sd", "B_nat", "tau"} <= need
    for o in ("NCE", "CS_SINGLE"):
        fb = bridges[("fau", o)].frozen(8)
        assert all(hasattr(fb, a) for a in need) and (fb.B_nat is not None) == (o == "CS_SINGLE")
        assert isinstance(fb, ev1.Readouts) and type(fb).scores is ev1.Readouts.scores
        with pytest.raises(BR.ZeroShotAccessError):
            fb.calibrate({"unified": np.zeros((2, 2))}, np.zeros(2, int))
    orig = (ev1.Reps, ev1.Readouts, ev1._ridge)
    coh = V.target_view("fau", 0, man, "A")
    b = core.bind(BR.bindable(zs_row(man, "fau", 1, 0)))
    bt = V.TickBatcher(coh, b["spec"], b, "cpu", man)                       # adapted: training participants present
    enc, _ = BR.donor_encoder(states["fau"], man, "fau", "cpu", layout=coh.layout)
    head = M.fixed_heads(man, man.root)["env"]
    with pytest.raises(BR.ZeroShotAccessError, match="training segments"):
        ZS.frozen_evaluate(b, enc, head, bt, coh, bridges[("fau", "NCE")].frozen(8), {"sigma_u": 1.0, "sigma_v": 1.0})
    assert (ev1.Reps, ev1.Readouts, ev1._ridge) == orig
    seen = []
    u0 = V.TickReps.u
    monkeypatch.setattr(V.TickReps, "u", lambda self, e: (seen.append((ev1._ridge, ev1.Readouts)), u0(self, e))[1])
    res = ZS.evaluate_zero_shot(zs_row(man, "fau", 1, 0), man, "cpu", states["fau"], bridges[("fau", "NCE")])
    assert seen and all(r is ZS._ridge_forbidden and r is not orig[2] for r, _ in seen)
    with pytest.raises(BR.ZeroShotAccessError):
        seen[0][0](np.zeros((2, 2)), np.zeros((2, 1)), [1.0])
    assert (ev1.Reps, ev1.Readouts, ev1._ridge) == orig
    z = res["zero_shot"]
    assert z["train_p"] == [] and z["train_segs"] == z["es_queries"] == z["fit_segments"] == z["es_segments"] == 0


@pytest.mark.parametrize("objective", ["NCE", "CS_SINGLE"])
def test_frozen_evaluation_equals_the_reference_ev1_path(man, states, objective):
    """Given the readout parameters that ev1.Readouts fitted on an adapted row (B_uni, a_mu, a_sd, B_nat, alpha, tau), the frozen
    zero-shot path (all participants, train_p empty, FrozenBridge, memoised TickReps, ev1._ridge raising) reproduces the reference
    ev1 evaluation of the same cell exactly: every per-participant metric, the attention 2AFC, kernel dependence and the readout."""
    for ds, sf, cf in (("fau", 1, 0), ("dtu", 0, 1)):
        ref, ro, _ = reference_eval(man, states[ds], ds, sf, cf, objective)
        bridge = bridge_from_readout(ro, objective)
        res = ZS.evaluate_zero_shot(zs_row(man, ds, sf, cf, objective=objective), man, "cpu", states[ds], bridge)
        r = BR.jsonable(ref)
        for ev in (res["eval"], res["eval_uni_cal"]):
            assert ev["per_participant"] == r["per_participant"], (ds, objective)
            assert ev.get("attention_2afc") == r.get("attention_2afc") and r.get("attention_2afc")
            assert {k: ev["readout"][k] for k in r["readout"]} == r["readout"]
        assert res["temperatures_used"]["primary"]["tau"] == ro.tau


# ---------------------------------------------------------------------------------------------------------- pools and rows read
def test_zero_shot_pool_equals_the_adapted_rows(fx, man, states, bridges):
    """§2.13 / F5: the zero-shot view loads every participant, so n_test_candidates, the evaluated participants and their
    candidate / query counts equal the adapted row of the same cell (the reference ev1 path), pool_sha256 equals the adapted view's,
    no target training participant is used, and the queries are the fold's test participants (+ the Federici test_only sessions)."""
    for ds, sf, cf in (("fau", 0, 0), ("fau", 3, 1), ("dtu", 2, 0), ("dtu", 4, 1), ("federici", 1, 0)):
        ref, _, coh_a = reference_eval(man, states[ds], ds, sf, cf)
        res = ZS.evaluate_zero_shot(zs_row(man, ds, sf, cf), man, "cpu", states[ds], bridges[(ds, "NCE")])
        cell = V.manifest_cell(man, ds, sf, cf)
        for ev in (res["eval"], res["eval_uni_cal"]):
            assert ev["readout"]["n_test_candidates"] == ref["readout"]["n_test_candidates"] == res["coverage"]["n_test_candidates"]
            assert sorted(ev["per_participant"]) == sorted(ref["per_participant"])
            for p, rr in ref["per_participant"].items():
                for k in ("unified/regular", "native/regular", "unified/hard", "unified/mismatched_eeg"):
                    assert (ev["per_participant"][p][k]["n_candidates"], ev["per_participant"][p][k]["n_queries"]) == \
                        (rr[k]["n_candidates"], rr[k]["n_queries"])
            assert sorted(ev.get("attention_2afc") or {}) == sorted(ref.get("attention_2afc") or {})
        assert res["pool_sha256"] == coh_a.meta["pool_sha256"] and res["view_sha256"] == coh_a.meta["view_sha256"]
        assert res["coverage"]["participants_loaded"] == len(_table(fx, ds)[0]["participants"])
        q = set(res["eval"]["per_participant"])
        assert q <= set(cell["test"]) | set(cell.get("test_only", ())) and not q & set(cell["train"])
        assert set(cell.get("test_only", ())) <= q and (ds != "federici" or res["coverage"]["test_only_queries"])
        assert res["zero_shot"]["train_participants"] == [] and res["split_hash"] == cell["split_hash"]


def test_zero_shot_reads_only_the_folds_test_rows(fx, man, states, bridges, monkeypatch):
    """Every EEG row the zero-shot evaluation reads is test content of a test participant of the fold (or a test_only session);
    every audio row is a test segment's attended or ignored stream window (the rows actually read, not only the lists)."""
    for ds, sf, cf, mode in (("fau", 2, 1, "A"), ("dtu", 1, 0, "C"), ("federici", 3, 0, "C_partial")):
        cell = V.manifest_cell(man, ds, sf, cf)
        items = _table(fx, ds)[1]
        test_ids, content = set(cell["test"]) | set(cell.get("test_only", ())), cell["content"]
        seen_e, seen_a = [], []
        pe, pa = V.TickBatcher.patches, V.TickBatcher.audio
        monkeypatch.setattr(V.TickBatcher, "patches", lambda self, e: (seen_e.append(e.cpu().numpy().copy()), pe(self, e))[1])
        monkeypatch.setattr(V.TickBatcher, "audio", lambda self, s: (seen_a.append(s.cpu().numpy().copy()), pa(self, s))[1])
        ZS.evaluate_zero_shot(zs_row(man, ds, sf, cf, mode=mode), man, "cpu", states[ds], bridges[(ds, "NCE")])
        monkeypatch.undo()
        v = V.target_view(ds, cf, man, mode)
        allowed = {int(s[k]) + int(o) for s in v.segments if s["role"] == "test" for k in ("s0", "s0_ign")
                   if s.get(k) is not None for o in C.TICK_OFFS}
        assert seen_e and seen_a
        for i in np.unique(_rows_to_pieces(items, np.concatenate(seen_e))):
            it = items[i]
            lists = content[it["kind"]] if ds == "fau" else content
            assert it["participant"] in test_ids and it["stimulus"] in lists["test"], (ds, it["piece_id"])
        assert set(np.concatenate(seen_a).tolist()) <= allowed


# ---------------------------------------------------------------------------------------------------------- modes and private
def test_access_modes_a_b_c(man, states, bridges, monkeypatch):
    """§2.13: modes A (FAU, DTU, Federici), B (FAU), C (FAU, DTU) and C_partial (Federici) read their own caches, share the cell's
    pool, record their access declaration (FAU B / C: the CI artefact caveat; C: the donor-derived scale) and give finite metrics;
    undefined pairs and unknown modes are refused. The zero-shot path imports no prior33 file outside its code group (sampler,
    losses and deps are removed from sys.modules for the run and must not come back)."""
    for name in ("sampler", "losses", "deps", "rich"):
        full = f"auditory_alignment_v3.prior33.{name}"
        if full in sys.modules:
            monkeypatch.delitem(sys.modules, full)
            pkg = sys.modules["auditory_alignment_v3.prior33"]
            if hasattr(pkg, name):
                monkeypatch.delattr(pkg, name)
    out = {}
    for ds, modes, sf, cf in (("fau", ("A", "B", "C"), 4, 1), ("dtu", ("A", "C"), 3, 0), ("federici", ("A", "C_partial"), 0, 0)):
        for mode in modes:
            res = ZS.evaluate_zero_shot(zs_row(man, ds, sf, cf, mode=mode), man, "cpu", states[ds], bridges[(ds, "NCE")])
            out[(ds, mode)] = res
            acc = res["normalisation_access"]
            assert res["mode"] == mode and res["mode_name"] == C.ZS_PREFIX + C.ZS_SUFFIX[mode] and acc["cache"] == C.CACHE_FILE[mode]
            assert res["view"]["cache"] == man["cohorts"][ds]["caches"][mode] and res["view"]["mode"] == mode
            assert ("caveat" in acc) == (ds == "fau" and mode in ("B", "C")) and ("mode_c" in acc) == (mode in ("C", "C_partial"))
            vals = [x["unified/regular"]["logloss_bits"] for x in res["eval"]["per_participant"].values()]
            assert vals and np.isfinite(vals).all()
            assert np.isfinite([x["unified/regular"]["logloss_bits"] for x in res["eval_uni_cal"]["per_participant"].values()]).all()
        pools = {out[(ds, m)]["pool_sha256"] for m in modes}
        views = {out[(ds, m)]["view_sha256"] for m in modes}
        assert len(pools) == 1 and len(views) == len(modes)
    assert not {f"auditory_alignment_v3.prior33.{n}" for n in ("sampler", "losses", "deps", "rich")} & set(sys.modules)
    for ds, mode in (("dtu", "B"), ("federici", "C"), ("fau", "C_partial"), ("federici", "B")):
        with pytest.raises(ValueError, match="defined for"):
            ZS.evaluate_zero_shot(zs_row(man, ds, 0, 0, mode=mode), man, "cpu", states[ds], bridges[(ds, "NCE")])
    with pytest.raises(ValueError, match="not one of"):
        ZS.canonical_mode("D")
    with pytest.raises(ValueError, match="fitted for target"):                               # a bridge of another target
        ZS.evaluate_zero_shot(zs_row(man, "fau", 0, 0), man, "cpu", states["fau"], bridges[("dtu", "NCE")])
    with pytest.raises(ValueError, match="bridge objective"):
        ZS.evaluate_zero_shot(zs_row(man, "fau", 0, 0, objective="CS_SINGLE"), man, "cpu", states["fau"], bridges[("fau", "NCE")])
    for m in ("A", "b", "c_partial", "C-partial", "cpartial", C.ZS_MODE_NAME["C"], "  B "):
        assert ZS.canonical_mode(m) == D.zero_shot_mode({"spec": {"mode": m}})
    assert ZS.canonical_mode(C.ZS_MODE_NAME["C_partial"]) == "C_partial"


def test_target_statistics_reach_neither_the_bridge_nor_the_mode_c_input(tmp_path_factory, fx, man, states, bridges):
    """§7.1 9 (mode C) and §2.11: scaling a FAU participant's first piece (a fit trial) by 5 changes that participant's mode-A input
    (its z-score) in every piece, but not the mode-C scale (donor-derived) nor its other mode-C pieces; the bridge of target fau
    (donor data only) stays bit-identical. Zero-shot: in mode A the participant's own values change (its z-score saw the
    perturbed piece), in mode C they are bit-identical (no target statistic enters); the other participants' values are unchanged
    in both modes."""
    pid = "203"
    fx2 = make_synthetic_manifest(tmp_path_factory.mktemp("m6_fx_perturbed"), perturb={("fau", pid): 5.0})
    man2 = V.open_manifest(fx2["manifest_path"], fx2["manifest_sha256"])
    assert man2.sha256 != man.sha256 and man2["mode_c"]["fau"] == man["mode_c"]["fau"]
    b1, b2 = bridges[("fau", "NCE")], fit(man2, states["fau"], "fau", "NCE")
    for f in ("B_uni", "B_uni_cal", "tau_unified", "tau_native", "tau_cal", "pool_realised"):
        assert np.array_equal(getattr(b1, f), getattr(b2, f)), f
    items = _table(fx, "fau")[1]
    mine = [it for it in items if it["participant"] == pid and it["row_offset"] is not None]
    first = min(mine, key=lambda it: it["trial"])
    others = [it for it in items if it["participant"] != pid and it["row_offset"] is not None][:6]
    sl = lambda it: slice(int(it["row_offset"]), int(it["row_offset"]) + int(it["T_eeg"]))   # noqa: E731
    for mode in ("A", "C"):
        e1, e2 = V.target_view("fau", 0, man, mode).eeg, V.target_view("fau", 0, man2, mode).eeg
        for it in mine:
            same = np.array_equal(e1[:, sl(it)], e2[:, sl(it)])
            assert same == (mode == "C" and it is not first), (mode, it["trial"])
        for it in others:
            assert np.array_equal(e1[:, sl(it)], e2[:, sl(it)]), (mode, it["piece_id"])
    sf = next(q["fold"] for q in _table(fx, "fau")[0]["participants"] if q["participant"] == pid)
    for mode in ("A", "C"):
        r1 = ZS.evaluate_zero_shot(zs_row(man, "fau", sf, 0, mode=mode), man, "cpu", states["fau"], b1)["eval"]["per_participant"]
        r2 = ZS.evaluate_zero_shot(zs_row(man2, "fau", sf, 0, mode=mode), man2, "cpu", states["fau"], b2)["eval"]["per_participant"]
        assert pid in r1 and sorted(r1) == sorted(r2) and (r1[pid] == r2[pid]) == (mode == "C"), mode
        assert all(r1[q] == r2[q] for q in r1 if q != pid), mode


def test_private_cohort_gets_no_speech_zero_shot(man, states, bridges):
    """§2.12 / contract §6: the private cohort is never given speech zero-shot (evaluate_zero_shot refuses it before any data is
    read; views.target_view has no private view)."""
    row = zs_row(man, "fau", 0, 0)
    row["dataset"] = "private_bdf"
    with pytest.raises(ValueError, match="private cohort"):
        ZS.evaluate_zero_shot(row, man, "cpu", states["private_bdf"], bridges[("fau", "NCE")])
    with pytest.raises(ValueError):
        V.target_view("private_bdf", 0, man, "A")
    assert "private_bdf" not in {c for m in C.ZS_COHORTS.values() for c in m}


def test_native_flag_and_bandwidths(man, states):
    """Native readout n/a exactly for NCE XP / XM / XPC; donor bandwidths: checkpoint, nested dicts, the group record; a CS member
    without the donor sigma_u is refused, an NCE member falls back (recorded)."""
    for slot in ("AP", "XP", "J*", "XM", "APR", "APC", "XPC", "J1", "J025"):
        assert BR.native_applicable("NCE", slot) == (slot not in ("XP", "XM", "XPC")) and BR.native_applicable("CS_SINGLE", slot)
    assert BR.donor_bandwidths({"sigma_u": 0.5, "sigma_v": 0.7})["source"] == {"sigma_u": "checkpoint", "sigma_v": "checkpoint"}
    b = BR.donor_bandwidths({"objective_calibration": {"sigma_u": torch.tensor(0.4)}}, {"members": {"AP": {"sigma_v": 2.0}}}, "AP")
    assert (b["sigma_u"], b["sigma_v"]) == (pytest.approx(0.4), 2.0) and b["source"]["sigma_v"] == "group_record.members.AP"
    assert BR.donor_bandwidths({}, {"bandwidths": {"u": 1.5, "v": 0.0}})["sigma_u"] == 1.5
    assert BR.donor_bandwidths({"sigma_u": float("nan")})["sigma_u"] is None
    st = donor_state(man, "dtu", sigma=False)
    enc, _ = BR.donor_encoder(st, man, "dtu", "cpu")
    with pytest.raises(ValueError, match="sigma_u"):
        BR.fit_bridge(enc, man, "dtu", "CS_SINGLE", slot="AP", sigma=BR.donor_bandwidths(st), device="cpu", root=man.root)
    nb = BR.fit_bridge(enc, man, "dtu", "NCE", slot="XM", sigma=BR.donor_bandwidths(st), device="cpu", root=man.root)
    assert nb.meta["sigma_source"]["sigma_u"].startswith("fallback") and nb.sigma_u > 0 and not nb.native_applicable
    with pytest.raises(ValueError, match="seen set"):
        BR.donor_encoder(states["fau"], man, "dtu", "cpu")                                      # a donor of another target


def test_artefact_probe(man, bridges, states):
    """The frozen B_uni on the control_artefact run: r_own against its own envelope, r_other against other segments of its family at
    >= 455 family-clock samples; descriptive."""
    b = bridges[("fau", "NCE")]
    enc, _ = BR.donor_encoder(states["fau"], man, "fau", "cpu")
    pr = BR.artefact_probe(enc, b, man, device="cpu", root=man.root)
    rows = BR.artefact_rows(man)
    assert pr["status"] == "computed" and pr["n_segments"] == len(rows) > 0 and pr["presentations"] == ["audiobook_1_artefact"]
    assert np.isfinite([pr["r_own"], pr["r_other"], pr["r_own_minus_other"]]).all() and pr["n_other_candidates"] > 0
    assert pr["min_separation_samples"] == C.SPAN_ENV + C.NEIGHBOR and "never used" in pr["use"]
    m2 = copy.deepcopy(dict(man))
    m2["segments"]["sparrkulee"]["role"] = ["fit" if r == "control_artefact" else r for r in m2["segments"]["sparrkulee"]["role"]]
    assert BR.artefact_probe(enc, b, m2, device="cpu", root=man.root)["status"] == "absent"


# ---------------------------------------------------------------------------------------------------------- pool entry points
def _mk(fam, ds, spec, deps, sf=None, cf=None, seed=3401):
    e = "ALN3X_" + hashlib.sha256(json.dumps([fam, ds, sf, cf, seed, spec], sort_keys=True).encode()).hexdigest()[:16]
    return {"dataset": ds, "subject_fold": sf, "content_fold": cf, "seed": seed, "seed_scope": "breadth", "experiment_id": e,
            "family_id": fam, "job_kind": "eval" if fam == SEL.ZEROSHOT else "train", "spec": spec, "registered": "synthetic test",
            "logical_dependencies": list(deps), "status": "registered_extension"}


def plan(man, ds="fau", obj="NCE"):
    common = {"manifest_sha256": man.sha256, "target_contract": man["target_contract"], "target": "envelope", "objective": obj,
              "architecture": "lag_local_tokens", "window": "full", "fs": 64, "projection_dim": 32, "donor_seed": 3401}
    g = _mk(SEL.DONOR, ds, {**common, "stage": "donor_group", "block": "core", "queue_tier": 1, "members": list(SEL.GROUP_MEMBERS[SEL.DONOR]),
                            "sampler_seed": 3401, "lambda_rule": SEL.LAMBDA_RULE,
                            "budget": {"epoch_equivalents": 30, "continuation": "group_wsd_any_last3_ext10_limit60_v1"}}, ["frozen_manifest"])
    gid, rows = g["experiment_id"], {"G": g}
    for m, k in (("AP", "BAP"), ("J*", "BJ"), ("XP", "BXP")):
        rows[k] = _mk(SEL.BRIDGE, ds, {**common, "stage": "bridge", "block": "core", "queue_tier": 1, "donor_group": gid, "member": m,
                                       **BR.SPEC_RULES, "artefact_probe": True}, [gid])
    for k, b, m, mode, sf, cf in (("ZAP", "BAP", "AP", "A", 0, 0), ("ZJB", "BJ", "J*", "B", 2, 1), ("ZXP", "BXP", "XP", "C", 1, 0)):
        blk = "core" if mode == "A" else "access"
        cell = V.manifest_cell(man, ds, sf, cf)
        rows[k] = _mk(SEL.ZEROSHOT, ds, {**common, "stage": "zero_shot", "block": blk, "queue_tier": D.BLOCK_TIER[blk], "mode": mode,
                                         "variant": C.ZS_MODE_NAME[mode], "member": m, "donor_group": gid,
                                         "bridge": rows[b]["experiment_id"], "view": ZS.VIEW_RULE, "split_hash": cell["split_hash"]},
                      [gid, rows[b]["experiment_id"]], sf, cf)
    return rows


@pytest.fixture
def pool_env(man, monkeypatch, tmp_path):
    """A pool output directory with a complete donor-group record and its member checkpoints; core bound to the design §6.3
    registry entries (in memory only), CPU device names, and core.load_rows on the synthetic plan."""
    rows = plan(man)
    out = str(tmp_path / "out")
    os.makedirs(os.path.join(out, "units")); os.makedirs(os.path.join(out, "ckpt"))
    g = rows["G"]
    rec = {"experiment_id": g["experiment_id"], "row": g, "status": "complete", "code_hash": "d" * 16,
           "members": {m: {"best": {"ce_dev": 5.0 + 0.1 * i}} for i, m in enumerate(SEL.GROUP_MEMBERS[SEL.DONOR])}}
    rec["members"]["J025"]["best"]["ce_dev"] = 5.3
    rec["joint_choice"] = SEL.joint_choice(rec)
    with open(SEL.record_path(out, g["experiment_id"]), "w") as f:
        json.dump(rec, f)
    for i, m in enumerate(("AP", "J1", "XP")):
        torch.save(m5_ckpt(man, "fau", g["experiment_id"], m, 10 + i), SEL.member_ckpt(out, g["experiment_id"], m))
    for grp, files in DESIGN_CODE.items():
        monkeypatch.setitem(core.FAMILY_CODE, grp, files)
    monkeypatch.setitem(core.FAMILY_GROUP, SEL.BRIDGE, "prior33_bridge")
    monkeypatch.setitem(core.FAMILY_GROUP, SEL.ZEROSHOT, "prior33_zeroshot")
    monkeypatch.setattr(torch.cuda, "get_device_name", lambda *a, **k: "cpu (test)")
    monkeypatch.setattr(core, "load_rows", lambda: list(rows.values()))
    return rows, out


def _run(mod, row, out, man):
    mod.run(row, out, manifest_path=man.path, device="cpu")
    with open(SEL.record_path(out, row["experiment_id"])) as f:
        return json.load(f)


def _failed(mod, row, out, man):
    with pytest.raises(SystemExit):
        mod.run(row, out, manifest_path=man.path, device="cpu")
    with open(SEL.record_path(out, row["experiment_id"]).replace(".json", ".FAILED.json")) as f:
        return json.load(f)


def test_runners_write_records_with_the_m11_fields(man, pool_env):
    """run_bridge / run_zeroshot on a synthetic plan (accepted by deps.check_plan): complete records through core.new_record /
    core.write_record with the M11 fields (bridge: alpha_uni, alpha_nat, tau_cal, bridge_cal_r, artefact_probe; zero-shot: eval,
    eval_uni_cal, selection_level containing "donor dev", target_contract = the registered spec value, member_resolved), the npz
    beside, readiness by deps, and prior33.analysis.normalise parsing every record as declared."""
    from auditory_alignment_v3.prior33 import analysis as AN
    rows, out = pool_env
    allrows = list(rows.values())
    assert [r["experiment_id"] for r in D.check_plan(allrows)]
    assert not D.ready(rows["ZAP"], allrows, out)
    recs = {}
    for k in ("BAP", "BJ", "BXP"):
        r = recs[k] = _run(RB, rows[k], out, man)
        assert r["status"] == "complete" and r["code_group"] == "prior33_bridge" and r["code_hash"] == core.code_hash(SEL.BRIDGE)
        assert r["target_contract"] == man["target_contract"] != core.TARGET_CONTRACT
        assert all(r.get(f) is not None for f in ("alpha_uni", "tau_cal", "bridge_cal_r", "artefact_probe", "view_sha256"))
        assert (r["alpha_nat"] is None) and r["artefact_probe"]["status"] == "computed" and "donor dev" in r["selection_level"]
        assert os.path.exists(SEL.bridge_npz(out, rows[k]["experiment_id"])) and r["coverage"]["target_cohort_rows"] == 0
        assert "fau" not in r["fit_participants"] and r["dependency"]["donor_group"] == rows["G"]["experiment_id"]
        # accounting (inherited contract §6): audio-pair counts and seconds at the top level, and the checkpoint the npz names
        cnt = r["bridge"]["counts"]
        assert r["n_pairs"] == cnt["n_audio_eeg_pairs"] == cnt["fit_rows"] + cnt["cal_rows"] > 0 and r["pairs_rule"] == BR.PAIRS_RULE
        assert r["n_pairs_uni_cal"] == cnt["uni_cal_rows"] > 0 and r["n_pairs_all"] >= r["n_pairs"] and r["bridge_seconds"] >= 0
        assert r["bridge_file"]["checkpoint_sha256"] == r["dependency"]["checkpoint_sha256"] == \
            BR.file_sha256(SEL.member_ckpt(out, rows["G"]["experiment_id"], r["member_resolved"]))
        assert r["bridge_file"]["sha256"] == BR.file_sha256(SEL.bridge_npz(out, rows[k]["experiment_id"]))
    assert recs["BJ"]["member_resolved"] == "J1" and recs["BAP"]["member_resolved"] == "AP"
    assert recs["BAP"]["sigma_source"] == {"sigma_u": "checkpoint.sigma", "sigma_v": "checkpoint.sigma"} and recs["BAP"]["sigma_u"] == 0.8
    assert recs["BAP"]["dependency"]["checkpoint_format"] == BR.CKPT_FORMAT
    assert recs["BXP"]["native_readout"]["applicable"] is False and recs["BAP"]["native_readout"]["applicable"] is True
    assert recs["BAP"]["rows_sha256"] == recs["BJ"]["rows_sha256"] == recs["BXP"]["rows_sha256"]
    assert D.ready(rows["ZAP"], allrows, out) and D.ready(rows["ZJB"], allrows, out)
    for k in ("ZAP", "ZJB", "ZXP"):
        r = recs[k] = _run(RZ, rows[k], out, man)
        assert r["status"] == "complete" and r["code_group"] == "prior33_zeroshot" and r["code_hash"] == core.code_hash(SEL.ZEROSHOT)
        assert r["selection_level"] == ZS.SELECTION_LEVEL == AN.SELECTION_LEVEL["zero_shot"][0] and "donor dev" in r["selection_level"]
        assert r["target_contract"] == rows[k]["spec"]["target_contract"] and r["mode"] == rows[k]["spec"]["mode"]
        assert r["eval"]["readout"]["n_test_candidates"] == r["eval_uni_cal"]["readout"]["n_test_candidates"] > 0
        assert r["dependency"]["bridge"] == rows[k]["spec"]["bridge"] and r["zero_shot"]["train_p"] == []
        br = recs[{"ZAP": "BAP", "ZJB": "BJ", "ZXP": "BXP"}[k]]
        assert r["dependency"]["bridge_checkpoint_sha256"] == r["dependency"]["checkpoint_sha256"] == br["dependency"]["checkpoint_sha256"]
        assert {f: r["bridge"][f] for f in ("n_pairs", "n_pairs_uni_cal", "n_pairs_all", "bridge_seconds")} == \
            {f: br[f] for f in ("n_pairs", "n_pairs_uni_cal", "n_pairs_all", "bridge_seconds")}
    assert recs["ZJB"]["member_resolved"] == "J1" and recs["ZXP"]["native_readout"]["applicable"] is False
    group = (rows["G"], json.load(open(SEL.record_path(out, rows["G"]["experiment_id"]))))
    for k in ("BAP", "BJ", "ZAP", "ZJB", "ZXP"):
        u = AN.normalise(rows[k], recs[k], group=group)
        assert u["status"] == "complete" and u["record_target_contract"] == man["target_contract"]
        assert u["member_check"] in ("agrees",), (k, u["member_check"], u["member_check_detail"])
        if k.startswith("Z"):
            assert u["level_status"] == "as declared" and u["views"]["primary"]["rows"] and u["view_status"]["uni_cal"] == "evaluated"
            assert u["views"]["primary"]["n_test_candidates"] == recs[k]["eval"]["readout"]["n_test_candidates"]
            assert u["views"]["primary"]["native_not_applicable"] == (k == "ZXP")
        else:
            bi = u["bridge_info"]
            assert all(bi.get(f) is not None for f in ("alpha_uni", "tau_cal", "bridge_cal_r", "artefact_probe/r_own", "artefact_probe/r_other"))
            assert u["extra"]["n_pairs"] == recs[k]["n_pairs"] and u["extra"]["n_pairs_all"] == recs[k]["n_pairs_all"]   # bridges table


def test_runner_failures_are_technical_failed_records(man, pool_env):
    """A missing dependency, a foreign target contract, a bridge of another slot and a private row are technical_failed records
    (core.write_record exits 1), never silent returns; the failed record keeps the registered target_contract."""
    rows, out = pool_env
    r = _failed(RZ, rows["ZAP"], out, man)                                                     # the bridge record does not exist
    assert r["status"] == "technical_failed" and "bridge" in r["error"] and r["target_contract"] == man["target_contract"]
    bad = copy.deepcopy(rows["BAP"])
    bad["spec"]["target_contract"] = "0" * 64
    assert "target_contract" in _failed(RB, bad, out, man)["error"]
    gone = copy.deepcopy(rows["BXP"])
    os.remove(SEL.member_ckpt(out, rows["G"]["experiment_id"], "XP"))
    assert "checkpoint" in _failed(RB, gone, out, man)["error"]
    _run(RB, rows["BAP"], out, man)
    wrong = copy.deepcopy(rows["ZJB"])
    wrong["spec"]["bridge"] = rows["BAP"]["experiment_id"]                                     # the AP bridge for a J* row
    assert "does not belong" in _failed(RZ, wrong, out, man)["error"]
    priv = copy.deepcopy(rows["ZAP"])
    priv["dataset"] = "private_bdf"
    r = _failed(RZ, priv, out, man)
    assert "private cohort" in r["error"] and "eval" not in r and "eval_uni_cal" not in r
    meth = copy.deepcopy(rows["BJ"])
    meth["spec"]["alpha"] = "logspace(-2,2,5)|bridge_cal_corr"
    assert "another method" in _failed(RB, meth, out, man)["error"]
    gid = rows["G"]["experiment_id"]
    ck = m5_ckpt(man, "fau", gid, "AP", 21)
    for k, v in (("member", "XM"), ("kind", "h30"), ("group", "ALN3X_" + "e" * 16), ("format", "other"), ("objective", "CS_SINGLE")):
        torch.save({**ck, k: v}, SEL.member_ckpt(out, gid, "AP"))
        assert "does not belong" in _failed(RB, rows["BAP"], out, man)["error"], k
    head = {kk: vv.clone() for kk, vv in ck["head"].items()}
    head["std.sd"] = head["std.sd"] * 2
    torch.save({**ck, "head": head}, SEL.member_ckpt(out, gid, "AP"))
    assert "audio head" in _failed(RB, rows["BAP"], out, man)["error"]
    torch.save({**ck, "note": np.float64(1.0)}, SEL.member_ckpt(out, gid, "AP"))           # not loadable with weights_only=True
    assert "weights_only" in _failed(RB, rows["BAP"], out, man)["error"]
    for mod, k in ((RB, "BJ"), (RZ, "ZJB")):                                                # a concrete joint member as the slot
        j1 = copy.deepcopy(rows[k])
        j1["spec"]["member"] = "J1"
        assert "is not a §2.11 slot" in _failed(mod, j1, out, man)["error"], k
    var = copy.deepcopy(rows["ZAP"])
    var["spec"]["variant"] = C.ZS_MODE_NAME["C"]                                             # mode A row named as mode C
    assert "spec.variant" in _failed(RZ, var, out, man)["error"]
    del var["spec"]["variant"]
    assert "spec.variant" in _failed(RZ, var, out, man)["error"]


def test_runner_failures_before_the_record_exists_are_records(man, pool_env):
    """§6.1 "catches all exceptions into technical_failed": a row that core.bind cannot bind (no spec.objective) and a family that
    FAMILY_GROUP does not list still give a technical_failed record (bridge.fallback_record) with the registered target_contract,
    never an escaping exception."""
    rows, out = pool_env
    for mod, k, stage in ((RB, "BAP", "bridge"), (RZ, "ZAP", "zero_shot")):
        r = copy.deepcopy(rows[k])
        del r["spec"]["objective"]
        rec = _failed(mod, r, out, man)
        assert rec["status"] == "technical_failed" and "objective" in rec["error"] and rec["stage"] == stage
        assert rec["code_group"] == core.FAMILY_GROUP[r["family_id"]] and rec["target_contract"] == man["target_contract"]
        assert rec["row"] == r and rec["bound_row"] is None and "traceback" in rec
        u = copy.deepcopy(rows[k])
        u["family_id"] = "ALN32_PUBLIC_AUDIO_PRIOR_UNREGISTERED"
        rec = _failed(mod, u, out, man)
        assert rec["status"] == "technical_failed" and rec["code_group"] is None and rec["code_hash"] is None and "KeyError" in rec["error"]


def test_zero_shot_refuses_a_bridge_of_another_checkpoint(man, pool_env):
    """Provenance: the npz names the sha256 of the checkpoint it was fitted on. After the member checkpoint is replaced (same
    provenance fields, other weights) the zero-shot unit is refused until the bridge is refitted; an npz that is not the file its
    record names, and a bridge record naming another checkpoint, are refused too."""
    rows, out = pool_env
    gid = rows["G"]["experiment_id"]
    brec = _run(RB, rows["BAP"], out, man)
    npz = SEL.bridge_npz(out, rows["BAP"]["experiment_id"])
    assert BR.load_bridge(npz).meta["checkpoint_sha256"] == brec["dependency"]["checkpoint_sha256"]
    torch.save(m5_ckpt(man, "fau", gid, "AP", 999), SEL.member_ckpt(out, gid, "AP"))         # other weights, same provenance
    r = _failed(RZ, rows["ZAP"], out, man)
    assert "checkpoint_sha256" in r["error"] and "eval" not in r
    brec = _run(RB, rows["BAP"], out, man)                                                   # refitted on the new checkpoint
    z = _run(RZ, rows["ZAP"], out, man)
    assert z["status"] == "complete" and z["dependency"]["checkpoint_sha256"] == brec["dependency"]["checkpoint_sha256"]
    b = BR.load_bridge(npz)
    b.tau_unified = b.tau_unified * 2                                                        # a valid npz that is not the recorded one
    BR.save_bridge(npz, b)
    assert "bridge_file.sha256" in _failed(RZ, rows["ZAP"], out, man)["error"]
    rp = SEL.record_path(out, rows["BAP"]["experiment_id"])
    brec["bridge_file"]["sha256"] = BR.file_sha256(npz)
    brec["dependency"]["checkpoint_sha256"] = "0" * 64
    with open(rp, "w") as f:
        json.dump(brec, f)
    assert "bridge_record.dependency.checkpoint_sha256" in _failed(RZ, rows["ZAP"], out, man)["error"]


def test_artefact_probe_failure_is_recorded_not_fatal(man, pool_env, monkeypatch):
    rows, out = pool_env

    def boom(*a, **k):
        raise RuntimeError("probe exploded")
    monkeypatch.setattr(BR, "artefact_probe", boom)
    r = _run(RB, rows["BAP"], out, man)
    assert r["status"] == "complete" and r["artefact_probe"]["status"] == "technical_failed" and "exploded" in r["artefact_probe"]["error"]
    assert os.path.exists(SEL.bridge_npz(out, rows["BAP"]["experiment_id"]))


def test_manifest_resolution(fx, man, monkeypatch, tmp_path):
    """open_row_manifest: an explicit path, else <CACHE_ROOT>/manifest.json, else the private copy (cache root CACHE_ROOT unless
    given), always with the row's sha256; spec.target_contract must equal the manifest's; no manifest is a dependency failure."""
    row = zs_row(man, "fau", 0, 0)
    assert BR.open_row_manifest(row, man.path).sha256 == man.sha256
    monkeypatch.setattr(BR, "MANIFEST_PATH", str(tmp_path / "absent.json"))
    monkeypatch.setattr(BR, "PRIVATE_MANIFEST", man.path)
    m2 = BR.open_row_manifest(row, None, fx["root"])
    assert m2.sha256 == man.sha256 and m2.root == os.path.abspath(fx["root"])
    assert BR.open_row_manifest(row).root == os.path.abspath(V.CACHE_ROOT)
    monkeypatch.setattr(BR, "PRIVATE_MANIFEST", str(tmp_path / "absent2.json"))
    with pytest.raises(BR.DependencyError):
        BR.open_row_manifest(row)
    bad = copy.deepcopy(row)
    bad["spec"]["target_contract"] = "f" * 64
    with pytest.raises(ValueError, match="target_contract"):
        BR.open_row_manifest(bad, man.path)
    bad["spec"]["manifest_sha256"] = "0" * 64
    with pytest.raises(ValueError):
        BR.open_row_manifest(bad, man.path)


# ---------------------------------------------------------------------------------------------------------- imports
def _imports(path):
    """{function name or '<module>': set of prior33 module names imported there (relative imports)}."""
    tree = ast.parse(open(path).read())
    out = {}

    def visit(node, where):
        for ch in ast.iter_child_nodes(node):
            w = ch.name if isinstance(ch, (ast.FunctionDef, ast.AsyncFunctionDef)) and where == "<module>" else where
            if isinstance(ch, ast.ImportFrom) and ch.level == 1:
                names = [ch.module] if ch.module else [a.name for a in ch.names]
                out.setdefault(where, set()).update(n.split(".")[0] for n in names)
            visit(ch, w)
    visit(tree, "<module>")
    return out


def test_zero_shot_path_imports_only_its_code_group():
    """Design §6.3: prior33_zeroshot hashes contract, views, model, select, bridge, zeroshot and run_zeroshot. zeroshot.py and
    run_zeroshot.py import nothing else of prior33; bridge.py's module level neither; sampler / losses (prior33_bridge only) are
    imported only inside the bridge-fitting functions, which the zero-shot path never calls."""
    zs_group = {f[:-3] for d, f in DESIGN_CODE["prior33_zeroshot"] if d.endswith("prior33")}
    br_group = {f[:-3] for d, f in DESIGN_CODE["prior33_bridge"] if d.endswith("prior33")}
    for name in ("zeroshot.py", "run_zeroshot.py"):
        imp = _imports(os.path.join(PKG, name))
        assert set().union(*imp.values()) <= zs_group, (name, imp)
    imp = _imports(os.path.join(PKG, "bridge.py"))
    assert imp["<module>"] <= zs_group
    nested = {f: s for f, s in imp.items() if f != "<module>"}
    assert set().union(*nested.values()) <= br_group and \
        set(nested) <= {"bridge_banks", "encode_segments", "fit_bridge", "artefact_probe", "uni_cal_sample"}
    src = open(os.path.join(PKG, "zeroshot.py")).read() + open(os.path.join(PKG, "run_zeroshot.py")).read()
    assert not [f for f in nested if f"BR.{f}(" in src]
    assert set().union(*_imports(os.path.join(PKG, "run_bridge.py")).values()) <= br_group
    from auditory_alignment_v3.prior33 import registry_patch as RP                          # M9's registry block = §6.3 for M6
    assert {g: RP.group_files(g) for g in DESIGN_CODE} == DESIGN_CODE and RP.RUNNERS["prior33_bridge"] == "prior33.run_bridge"
    assert RP.FAMILIES[SEL.BRIDGE] == "prior33_bridge" and RP.FAMILIES[SEL.ZEROSHOT] == "prior33_zeroshot"


# ---------------------------------------------------------------------------------------------------------- the REAL M9 rows
_MP_PATH = os.path.normpath(os.path.join(HERE, "..", "..", "..", "private", "auditory_alignment_v3", "make_plan_ext_prior33.py"))
M9_GROUPS = [  # (family, target, objective, block, CE_dev overrides) of the synthetic donor-group records
    (SEL.DONOR, "dtu", "NCE", "core", {"J1": 5.2, "J025": 5.0}),            # J* -> J025 (lower by more than 1e-4 bits)
    (SEL.DONOR, "dtu", "CS_SINGLE", "core", {"J1": 5.0, "J025": 5.00005}),  # a tie -> J1
    (SEL.RICH_DONOR, "dtu", "NCE", "rich", {}),
    (SEL.CSX_DONOR, "dtu", "NCE", "csx", {}),
    (SEL.DONOR, "fau", "NCE", "core", {}),
    (SEL.DONOR, "federici", "NCE", "core", {}),
]


def pick(plan, fam, ds, **spec):
    return [r for r in plan if r["family_id"] == fam and r["dataset"] == ds and all(r["spec"].get(k) == v for k, v in spec.items())]


@pytest.fixture(scope="module")
def m9(man, tmp_path_factory):
    """The primary block of make_plan_ext_prior33.build_primary on the synthetic manifest (the rows M9 registers), core bound to
    M9's registry block (registry_patch, in memory only), complete synthetic donor-group records (select.joint_choice) and an M5-
    format checkpoint per member of the groups in M9_GROUPS."""
    spec = importlib.util.spec_from_file_location("m6_make_plan_ext_prior33", _MP_PATH)
    MP = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(MP)
    from auditory_alignment_v3.prior33 import registry_patch as RP
    plan = MP.build_primary(MP.manifest_context(man, man.sha256), "synthetic M6 test")
    assert D.check_plan(plan)
    mp = pytest.MonkeyPatch()
    out = str(tmp_path_factory.mktemp("m6_m9_out"))
    os.makedirs(os.path.join(out, "units")); os.makedirs(os.path.join(out, "ckpt"))
    for g in RP.GROUPS:
        mp.setitem(core.FAMILY_CODE, g, RP.group_files(g))
    for f, g in RP.FAMILIES.items():
        mp.setitem(core.FAMILY_GROUP, f, g)
    mp.setattr(torch.cuda, "get_device_name", lambda *a, **k: "cpu (test)")
    mp.setattr(core, "load_rows", lambda: list(plan))
    groups = {}
    for k, (fam, ds, obj, blk, ce) in enumerate(M9_GROUPS):
        g, = pick(plan, fam, ds, objective=obj, block=blk)
        ms = SEL.group_members(g)
        rec = {"experiment_id": g["experiment_id"], "row": g, "status": "complete", "code_hash": "c" * 16,
               "members": {m: {"best": {"ce_dev": float(ce.get(m, 5.5 + 0.01 * i))}} for i, m in enumerate(ms)}}
        if all(m in ms for m in SEL.JOINT_CANDIDATES):
            rec["joint_choice"] = SEL.joint_choice(rec)
        SEL.check_group_record(rec, g)
        with open(SEL.record_path(out, g["experiment_id"]), "w") as f:
            json.dump(rec, f)
        for i, m in enumerate(ms):
            torch.save(m5_ckpt(man, ds, g["experiment_id"], m, 100 * k + i, obj), SEL.member_ckpt(out, g["experiment_id"], m))
        groups[(fam, ds, obj)] = (g, rec)
    yield {"plan": plan, "out": out, "groups": groups}
    mp.undo()


def bridge_rows_of(plan, gid):
    return {r["spec"]["member"]: r for r in plan if r["family_id"] == SEL.BRIDGE and r["spec"]["donor_group"] == gid}


def _ok(run, row, out, *a, **k):
    """run(row, out, ...) of a pool runner -> its complete record; a technical_failed unit fails the test with its error."""
    try:
        run(row, out, *a, **k)
    except SystemExit:
        with open(SEL.record_path(out, row["experiment_id"]).replace(".json", ".FAILED.json")) as f:
            r = json.load(f)
        pytest.fail(f"{row['family_id']} {row['experiment_id']}: {r.get('error')}\n{r.get('traceback', '')[-1500:]}")
    with open(SEL.record_path(out, row["experiment_id"])) as f:
        return json.load(f)


def _run_ok(mod, row, out, man):
    return _ok(mod.run, row, out, manifest_path=man.path, device="cpu")


def _bridge_rec(out, row, man):
    p = SEL.record_path(out, row["experiment_id"])
    return json.load(open(p)) if os.path.exists(p) else _run_ok(RB, row, out, man)


def test_m9_rows_every_slot_same_procedure_same_rows(man, m9):
    """Contract §6 / §2.11 on the real M9 bridge rows of target dtu: every slot (AP, XP, J*, XM for NCE and CS_SINGLE; APR; APC,
    XPC) gets the same procedure on the same rows (fit-row and bridge_cal targets, encode calls with their rows and montage
    subsets, tau pool draws, alpha grids, B_uni_cal rows and folds); only U differs. J* resolves to J025 (NCE) and to J1 on a
    tie (CS_SINGLE); the native readout is n/a exactly for XP / XM / XPC NCE; the records carry the M11 fields and the
    accounting, and prior33.analysis parses them with member_check 'agrees'."""
    from auditory_alignment_v3.prior33 import analysis as AN
    out, plan, G = m9["out"], m9["plan"], m9["groups"]
    runs = {}
    for key in ((SEL.DONOR, "dtu", "NCE"), (SEL.DONOR, "dtu", "CS_SINGLE"), (SEL.RICH_DONOR, "dtu", "NCE"), (SEL.CSX_DONOR, "dtu", "NCE")):
        g, grec = G[key]
        for slot, row in bridge_rows_of(plan, g["experiment_id"]).items():
            with capture() as cap:
                rec = _run_ok(RB, row, out, man)
            runs[(key[2], slot)] = (cap, rec, row, (g, grec))
    assert set(runs) == {("NCE", s) for s in SEL.SLOTS} | {("CS_SINGLE", s) for s in ("AP", "XP", "J*", "XM")}
    ref_cap, ref_rec = runs[("NCE", "AP")][:2]
    sig = lambda cap: [(c["cohort"], c["rows"], c["montage"], c["montage_flag"], hashlib.sha256(c["Y"].tobytes()).hexdigest())  # noqa: E731
                       for c in cap["enc"]]
    for (obj, slot), (cap, rec, row, grp) in runs.items():
        assert sig(cap) == sig(ref_cap), (obj, slot)
        assert [{n: hashlib.sha256(v.tobytes()).hexdigest() for n, v in d.items()} for d in cap["draws"]] == \
            [{n: hashlib.sha256(v.tobytes()).hexdigest() for n, v in d.items()} for d in ref_cap["draws"]]
        assert [t["A"].tobytes() == r["A"].tobytes() for t, r in zip(cap["targets"], ref_cap["targets"])] == [True] * len(ref_cap["targets"])
        uni = cap["ridge"][0]
        assert uni["crit"] == "corr" and uni["alphas"] == [float(a) for a in np.logspace(-4, 8, 13)]
        assert np.array_equal(uni["Y"], ref_cap["ridge"][0]["Y"]) and np.array_equal(uni["Yv"], ref_cap["ridge"][0]["Yv"])
        assert [(c["n"], c["fold"].tobytes()) for c in cap["ridge2"]] == [(c["n"], c["fold"].tobytes()) for c in ref_cap["ridge2"]]
        assert len(cap["ridge"]) == (2 if obj == "CS_SINGLE" else 1)                   # CS: + the native ridge (MSE); NCE: cosine
        if obj == "CS_SINGLE":
            assert cap["ridge"][1]["crit"] == "mse" and cap["ridge"][1]["alphas"] == [float(a) for a in np.logspace(-3, 3, 7)]
        assert rec["rows_sha256"] == ref_rec["rows_sha256"] and rec["method"] == ref_rec["method"]
        for k in ("fit_rows", "cal_rows", "uni_cal_rows", "n_audio_eeg_pairs", "n_audio_eeg_pairs_uni_cal", "n_audio_eeg_pairs_all"):
            assert rec["coverage"][k] == ref_rec["coverage"][k], (obj, slot, k)
        assert rec["n_pairs"] == ref_rec["n_pairs"] and rec["bridge_seconds"] >= 0
        assert rec["native_readout"]["applicable"] == (not (obj == "NCE" and slot in ("XP", "XM", "XPC")))
        assert rec["target_contract"] == row["spec"]["target_contract"] == man["target_contract"]
        assert rec["member_resolved"] == SEL.member_of(row, grp[1])
        u = AN.normalise(row, rec, group=grp)
        assert u["status"] == "complete" and u["member_check"] == "agrees" and u["extra"]["n_pairs"] == rec["n_pairs"]
        assert all(u["bridge_info"].get(f) is not None for f in ("alpha_uni", "tau_cal", "bridge_cal_r", "artefact_probe/r_own"))
    assert runs[("NCE", "J*")][1]["member_resolved"] == "J025" and runs[("CS_SINGLE", "J*")][1]["member_resolved"] == "J1"
    assert len({hashlib.sha256(np.asarray(BR.load_bridge(SEL.bridge_npz(out, r[2]["experiment_id"])).B_uni).tobytes()).hexdigest()
                for r in runs.values()}) == len(runs)                                       # the members really differ
    br = SM.bridge_rows(man, "dtu")
    got = sorted((c["cohort"], r, m) for c in ref_cap["enc"] if c["montage_flag"] is True for r, m in zip(c["rows"], c["montage"]))
    assert got == sorted((SM.coh_of(s), int(r), m) for s, r, m in br["order"])            # the manifest's bridge.fit_rows[dtu]


def test_m9_zero_shot_rows_through_the_runners(man, m9):
    """Real M9 zero-shot rows through run_zeroshot: J* (-> J025) mode A, a CS_SINGLE row, the rich APR and CSX XPC slots (native
    n/a), FAU mode B and Federici C_partial: M11 fields, mode_name = spec.variant, the temperatures are the bridge table entries at
    the pool size (tau_cal for eval_uni_cal), the bridge's accounting and checkpoint in the record, analysis 'as declared'."""
    from auditory_alignment_v3.prior33 import analysis as AN
    out, plan, G = m9["out"], m9["plan"], m9["groups"]
    cases = [((SEL.DONOR, "dtu", "NCE"), "J*", "A", (2, 1)), ((SEL.DONOR, "dtu", "CS_SINGLE"), "AP", "A", (0, 0)),
             ((SEL.RICH_DONOR, "dtu", "NCE"), "APR", "A", (1, 0)), ((SEL.CSX_DONOR, "dtu", "NCE"), "XPC", "A", (3, 1)),
             ((SEL.DONOR, "fau", "NCE"), "XP", "B", (4, 0)), ((SEL.DONOR, "federici", "NCE"), "AP", "C_partial", (2, 0))]
    for key, slot, mode, (sf, cf) in cases:
        g, grec = G[key]
        brow = bridge_rows_of(plan, g["experiment_id"])[slot]
        brec = _bridge_rec(out, brow, man)
        z, = [r for r in pick(plan, SEL.ZEROSHOT, key[1], member=slot, mode=mode, donor_group=g["experiment_id"])
              if (r["subject_fold"], r["content_fold"]) == (sf, cf)]
        zrec = _run_ok(RZ, z, out, man)
        assert zrec["mode"] == mode and zrec["mode_name"] == z["spec"]["variant"] == C.ZS_MODE_NAME[mode]
        assert "donor dev" in zrec["selection_level"] and zrec["target_contract"] == z["spec"]["target_contract"]
        assert zrec["member_resolved"] == brec["member_resolved"] == SEL.member_of(z, grec)
        b = BR.load_bridge(SEL.bridge_npz(out, brow["experiment_id"]))
        n = zrec["eval"]["readout"]["n_test_candidates"]
        k = b.entry(n)[0]
        assert zrec["eval"]["readout"]["tau"] == {"unified": float(b.tau_unified[k]), "native": float(b.tau_native[k])}
        assert zrec["eval_uni_cal"]["readout"]["tau"] == {"unified": float(b.tau_cal[k]), "native": float(b.tau_native[k])}
        assert zrec["eval_uni_cal"]["readout"]["n_test_candidates"] == n > 0 and zrec["eval"]["readout"]["frozen"] is True
        assert zrec["kernel_dependence_sigma"] == {"sigma_u": b.sigma_u, "sigma_v": b.sigma_v}
        assert zrec["bridge"]["n_pairs"] == brec["n_pairs"] and zrec["bridge"]["checkpoint_sha256"] == zrec["dependency"]["checkpoint_sha256"]
        na = key[2] == "NCE" and slot in ("XP", "XM", "XPC")
        assert zrec["native_readout"]["applicable"] == (not na)
        u = AN.normalise(z, zrec, group=(g, grec))
        assert u["level_status"] == "as declared" and u["member_check"] == "agrees" and u["view_status"]["uni_cal"] == "evaluated"
        assert u["views"]["primary"]["native_not_applicable"] == na
    gf = G[(SEL.DONOR, "fau", "NCE")][0]["experiment_id"]
    _bridge_rec(out, bridge_rows_of(plan, gf)["AP"], man)
    zc = pick(plan, SEL.ZEROSHOT, "fau", member="AP", mode="C", donor_group=gf)[0]
    acc = _run_ok(RZ, zc, out, man)["normalisation_access"]
    assert "caveat" in acc and "donor-derived scale" in json.dumps(acc) and acc["target_supervised_fit"] == "none"


def test_m9_temperatures_interior_case(man, m9, tmp_path):
    """With seeded noise added to U (retrieval imperfect), the unified, native (NCE cosine) and cross-fitted temperatures leave the
    grid edge, and every bridge value equals the independent recomputation (alpha, B_uni, tau(n), B_uni_cal, tau_cal)."""
    out, plan = m9["out"], m9["plan"]
    g, _ = m9["groups"][(SEL.DONOR, "fau", "NCE")]
    row = bridge_rows_of(plan, g["experiment_id"])["XP"]
    o2 = str(tmp_path / "o2")
    os.makedirs(os.path.join(o2, "units")); os.makedirs(os.path.join(o2, "ckpt"))
    shutil.copy(SEL.record_path(out, g["experiment_id"]), os.path.join(o2, "units"))
    shutil.copy(SEL.member_ckpt(out, g["experiment_id"], "XP"), os.path.join(o2, "ckpt"))
    with capture(noise=0.35) as cap:
        rec = _run_ok(RB, row, o2, man)
    b = BR.load_bridge(SEL.bridge_npz(o2, row["experiment_id"]))
    recompute_bridge(man, cap, b)
    edges = [v for n in BR.POOL_SIZES for v in (rec["bridge"]["bridge_cal"]["by_pool_size"][str(n)]["tau_unified_grid_edge"],
                                                rec["bridge"]["bridge_cal"]["by_pool_size"][str(n)]["tau_native_grid_edge"],
                                                rec["bridge"]["uni_cal"]["by_pool_size"][str(n)]["tau_fold0_grid_edge"],
                                                rec["bridge"]["uni_cal"]["by_pool_size"][str(n)]["tau_fold1_grid_edge"])]
    assert edges.count(None) > 0, "every temperature still on the grid edge"
    g2 = np.random.default_rng(3)
    for _ in range(5):                                                                   # calibrate_tau = the CE argmin
        S = g2.standard_normal((7, 11)) * g2.uniform(0.1, 3)
        assert math.isclose(BR.calibrate_tau({"unified": S})["unified"], _tau(S), rel_tol=1e-12)


def test_m9_zero_shot_pool_equals_a_real_m7_unit(man, m9):
    """The zero-shot units of a cell (modes A and C) have the participants, per-participant candidate / query counts,
    n_test_candidates and pool_sha256 of a real M7 target unit of the same cell (run_target.run, 1 epoch), as prior33.analysis'
    pool check reads them (B_uni and B_uni_cal views)."""
    from auditory_alignment_v3.prior33 import analysis as AN
    from auditory_alignment_v3.prior33 import run_target as RT
    out, plan = m9["out"], m9["plan"]
    g, _ = m9["groups"][(SEL.DONOR, "dtu", "NCE")]
    sf, cf = 1, 1
    _bridge_rec(out, bridge_rows_of(plan, g["experiment_id"])["AP"], man)
    t, = [r for r in pick(plan, SEL.TARGET, "dtu", member="AP", donor_group=g["experiment_id"]) if (r["subject_fold"], r["content_fold"]) == (sf, cf)]
    trec = _ok(RT.run, t, out, 1, device="cpu", manifest_path=man.path, rows=plan)
    ut = AN.normalise(t, trec)
    for mode in ("A", "C"):
        z, = [r for r in pick(plan, SEL.ZEROSHOT, "dtu", member="AP", mode=mode, donor_group=g["experiment_id"])
              if (r["subject_fold"], r["content_fold"]) == (sf, cf)]
        zrec = _run_ok(RZ, z, out, man)
        uz = AN.normalise(z, zrec)
        assert AN._sig(ut["views"]["primary"]) == AN._sig(uz["views"]["primary"]) == AN._sig(uz["views"]["uni_cal"]), mode
        assert zrec["pool_sha256"] == trec["pool_sha256"] and zrec["split_hash"] == trec["split_hash"]
        assert zrec["eval"]["readout"]["n_test_candidates"] == trec["eval"]["readout"]["n_test_candidates"] > 0


def _keep_masks(coh, bt, sf):
    """EEG columns of the fold's test participants' (and test_only sessions') test segments; audio columns of every test segment."""
    segs, parts = coh.segments, coh.participants
    test_p = {s["p"] for s in segs if s["role"] == "test" and (parts[s["p"]]["fold"] == sf or parts[s["p"]].get("test_only"))}
    ke, ka = np.zeros(bt.E.shape[1], dtype=bool), np.zeros(bt.S.shape[1], dtype=bool)
    se, sa = int(C.TICK_OFFS[-1]) + C.L_IN, int(C.TICK_OFFS[-1]) + C.N_TGT
    for s in segs:
        if s["role"] != "test":
            continue
        if s["p"] in test_p:
            ke[s["e0"]:s["e0"] + se] = True
        ka[s["s0"]:s["s0"] + sa] = True
        if s.get("s0_ign") is not None:
            ka[s["s0_ign"]:s["s0_ign"] + sa] = True
    return ke, ka


@pytest.mark.parametrize("ds,mode,sf,cf", [("fau", "B", 3, 1), ("federici", "C_partial", 2, 0)])
def test_zero_shot_reads_nothing_but_the_folds_test_rows_nan_poisoning(man, m9, monkeypatch, ds, mode, sf, cf):
    """With every EEG sample outside the fold's test participants' test segments (training participants, fit / es content),
    every audio sample outside the test segments and every donor-unseen channel set to NaN in the batcher, the zero-shot
    evaluation (both bridges) is bit-identical and finite: nothing else reaches it."""
    out, plan = m9["out"], m9["plan"]
    g, _ = m9["groups"][(SEL.DONOR, ds, "NCE")]
    brow = bridge_rows_of(plan, g["experiment_id"])["AP"]
    _bridge_rec(out, brow, man)
    bridge = BR.load_bridge(SEL.bridge_npz(out, brow["experiment_id"]))
    ck = torch.load(SEL.member_ckpt(out, g["experiment_id"], "AP"), map_location="cpu", weights_only=True)
    z, = [r for r in pick(plan, SEL.ZEROSHOT, ds, member="AP", mode=mode, donor_group=g["experiment_id"])
          if (r["subject_fold"], r["content_fold"]) == (sf, cf)]
    clean = ZS.evaluate_zero_shot(z, man, "cpu", ck, bridge)
    orig, info = V.TickBatcher.__init__, {}
    unseen = man["coverage"][ds]["unseen"]

    def init(self, coh, spec, row, dev, manifest, train_p=None):
        orig(self, coh, spec, row, dev, manifest, train_p=train_p)
        ke, ka = _keep_masks(coh, self, sf)
        E, S_ = self.E.clone(), self.S.clone()
        E[:, torch.as_tensor(~ke)] = float("nan")
        for n in unseen:
            E[list(coh.layout).index(n)] = float("nan")
        S_[:, torch.as_tensor(~ka)] = float("nan")
        self.E, self.S = E, S_
        info.update(eeg=float((~ke).mean()), audio=float((~ka).mean()))
    monkeypatch.setattr(V.TickBatcher, "__init__", init)
    dirty = ZS.evaluate_zero_shot(z, man, "cpu", ck, bridge)
    assert info["eeg"] > 0.3 and info["audio"] > 0.2, info
    for k in ("eval", "eval_uni_cal"):
        assert dirty[k] == clean[k], (ds, mode, k)
        vals = [v["unified/regular"]["logloss_bits"] for v in clean[k]["per_participant"].values()]
        assert vals and np.isfinite(vals).all()
    assert clean["coverage"]["channels"]["closed_unseen"] == unseen
