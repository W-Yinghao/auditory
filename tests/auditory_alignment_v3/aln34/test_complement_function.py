"""R34_FUSION_FUNCTION (auditory_alignment_v3.aln34.complement_function + complement_function_eval): synthetic checks only.

- per-row residual layers == the package reference residual_diagnostics; D34 radial / orthogonal / alpha <= -1 cases;
- per-query ranks / log-losses == auditory_alignment.evaluate._metrics;
- per_query_eval == auditory_alignment.evaluate.evaluate_continuous on a fake cohort (NCE and CS_SINGLE), two views;
- run_family == bc_interim.run_family (same label -> identical intervals);
- same-contract families on synthetic records: known effects, native-only effect, pairing exclusion, access labels;
- SplitReps: u = normalise(u_base + r) == the trained forward; zero last layer -> u == u_base;
- record layers (epoch-0 identity, L4), checkpoint layer and the merge of per-unit outputs with coverage of every configuration;
- v2 provenance: code hashes and loaded-source snapshots; v1 vs v2 comparison; evaluator math identical to the v1 copy;
- assets: checkpoint inventory, file kinds, npz contents, FM-weight hashes vs a receipt;
- GPU plan: unit list (pending only, full interpreter path, offline flags), sbatch template, claim-based worker (claims, shards, tries);
- SC cross-backbone copies and de-duplicated tallies; Federici manifest identities; regression checks; budgets; report rendering.
No EEG is read."""
import ast
import json
import math
import os
import time

import numpy as np
import pytest
import torch
import torch.nn as nn
import torch.nn.functional as F

from auditory_alignment_v3.aln34 import complement_function as CF
from auditory_alignment_v3.aln34 import complement_function_eval as EV


# ------------------------------------------------------------------------------------------------ reference math
def test_residual_rows_match_reference():
    ref = CF.reference_residuals()
    rng = np.random.default_rng(0)
    u = rng.normal(size=(50, 8)); r = 0.3 * rng.normal(size=(50, 8))
    u[3] = 0.0  # a zero-base row is reported, not averaged
    mine = CF.residual_summary(CF.residual_rows(u, r))
    theirs = ref.residual_diagnostics(u, r)
    for k, v in theirs.items():
        assert mine[k] == pytest.approx(v, rel=1e-12, abs=1e-12), k
    assert mine["n_zero_or_tiny_base_rows"] == 1


def test_d34_cases():
    rng = np.random.default_rng(1)
    u = rng.normal(size=(20, 6))
    rad = CF.residual_rows(u, 2 * u)  # alpha = 2 > -1: no functional change
    assert np.allclose(rad["post_change"], 0, atol=1e-12) and np.allclose(rad["angle_deg"], 0, atol=1e-5)
    assert np.allclose(rad["rel_par"], 2) and np.allclose(rad["rel_orth"], 0, atol=1e-12) and np.allclose(rad["coef"], 2)
    flip = CF.residual_rows(u, -2 * u)  # alpha <= -1 flips the direction
    assert np.allclose(flip["post_change"], 2) and np.allclose(flip["angle_deg"], 180)
    o = rng.normal(size=(20, 6)); o -= (np.sum(o * u, 1) / np.sum(u * u, 1))[:, None] * u
    o *= (0.5 * np.linalg.norm(u, axis=1) / np.linalg.norm(o, axis=1))[:, None]  # orthogonal, ||r|| = 0.5 ||u||
    orth = CF.residual_rows(u, o)
    assert np.allclose(orth["rel_orth"], 0.5) and np.allclose(orth["rel_par"], 0, atol=1e-12)
    assert np.allclose(orth["angle_deg"], math.degrees(math.atan(0.5)))
    with pytest.raises(ValueError):
        CF.residual_rows(u, u[:, :3])


# ------------------------------------------------------------------------------------------------ per-query scoring
def test_query_metrics_equal_ev1():
    from auditory_alignment import evaluate as ev1
    rng = np.random.default_rng(2)
    for _ in range(5):
        Sc = rng.normal(size=(17, 23)); Sc[:, 5] = Sc[:, 6]  # ties resolved as ev1 does
        own = rng.integers(0, 23, 17); tau = float(rng.uniform(0.05, 2))
        a = CF.metrics_from_queries(CF.query_ranks(Sc, own), CF.query_logloss_bits(Sc, own, tau), Sc.shape[1])
        b = ev1._metrics(Sc, own, tau)
        for k in CF.QMETRICS:
            assert a[k] == pytest.approx(b[k], abs=1e-12), k


def test_rank_change():
    rb, rc = np.array([0, 3, 1, 5]), np.array([1, 0, 1, 2])
    d = CF.rank_change(rb, rc, [1, 2, 3, 4], [1, 1, 3, 3], [0, 0, 0, 0], [1, 1, 1, 1], [0] * 4, [0.5] * 4)
    assert d["frac_rank_changed"] == 0.75 and d["top1_gain"] == 0.25 and d["top1_loss"] == 0.25
    assert d["mean_drank"] == pytest.approx(-1.25) and d["mean_abs_drank"] == pytest.approx(1.75)
    assert d["d_logloss"] == pytest.approx(0.5) and d["d_true_score"] == 1.0 and d["d_true_z"] == 0.5


class _Enc(nn.Module):
    def __init__(self, C, L, d, seed):
        super().__init__(); torch.manual_seed(seed); self.lin = nn.Linear(C * L, d)

    def forward(self, patches):
        return F.normalize(self.lin(patches[0].flatten(1)), dim=1)


class _BT:
    """minimal ALN2 batcher interface over synthetic banks"""

    def __init__(self, E, Sx, segs, train_p, seg_len, W=(0, 8)):
        self.E, self.S, self.coh_segments, self.train_p, self.seg_len, self.W = E, Sx, segs, train_p, seg_len, [W]
        self.kind, self.dev = "ss", torch.device("cpu")

    def patches(self, e_idx):
        e_idx = torch.as_tensor(e_idx)
        return [self.E[:, (e_idx[:, None] + torch.arange(a, b)[None])].permute(1, 0, 2).float() for a, b in self.W]

    def audio(self, s_idx):
        s_idx = torch.as_tensor(s_idx)
        return self.S[:, (s_idx[:, None] + torch.arange(8)[None])].permute(1, 0, 2).flatten(1)


def _fake_cohort(seed=3):
    rng = np.random.default_rng(seed)
    seg_len, C, D = 40, 3, 2
    stims = [f"f{i}" for i in range(6)] + [f"e{i}" for i in range(4)] + [f"t{i}" for i in range(10)]
    s0 = {u: k * (seg_len + 16) for k, u in enumerate(stims)}
    Sx = torch.tensor(rng.normal(size=(D, len(stims) * (seg_len + 16))), dtype=torch.float32)
    parts = [{"id": f"P{i}", "group": "nh" if i % 2 else "hi", "fold": [0, 0, 1, 2, 3][i]} for i in range(5)]
    segs, e0 = [], 0
    for p in range(5):
        for u in stims:
            role = "fit" if u[0] == "f" else ("es" if u[0] == "e" else "test")
            segs.append({"p": p, "e0": e0, "s0": s0[u], "s0_ign": None, "role": role, "kind": "ss", "uid": u, "hard_key": "x",
                         "part": u, "feat": rng.normal(size=4)})
            e0 += seg_len + 16
    E = torch.tensor(rng.normal(size=(C, e0 + 64)), dtype=torch.float32)
    # make EEG partly predictable from the audio so the readouts are non-degenerate
    for s in segs:
        E[:2, s["e0"]:s["e0"] + seg_len] += 0.8 * Sx[:, s["s0"]:s["s0"] + seg_len]

    class Coh:
        pass
    coh = Coh(); coh.segments, coh.participants = segs, parts
    return coh, _BT(E, Sx, segs, {2, 3, 4}, seg_len), C


@pytest.mark.parametrize("objective", ["NCE", "CS_SINGLE"])
def test_per_query_eval_equals_evaluator(objective):
    from auditory_alignment import evaluate as ev1
    from auditory_alignment_v2.audio_targets import FixedFeatureHead
    coh, bt, C = _fake_cohort()
    head = FixedFeatureHead(16, 4, np.zeros(16), np.ones(16), "dtu")
    enc_a, enc_b = _Enc(C, 8, 4, 0), _Enc(C, 8, 4, 1)
    seed = 3401
    ref = {k: ev1.evaluate_continuous(objective, e, head, bt, coh, {"subject_fold": 0}, np.random.default_rng(seed + 1000), {"sigma_u": 1.0, "sigma_v": 1.0})
           for k, e in (("a", enc_a), ("b", enc_b))}
    views = {"a": ev1.Reps(enc_a, head, bt), "b": ev1.Reps(enc_b, head, bt)}
    per, ros = CF.per_query_eval(objective, views, views["a"], bt, coh, 0, seed)
    assert set(per) == set(ref["a"]["per_participant"]) == {"P0", "P1"}
    for pid, pr in per.items():
        for k in ("a", "b"):
            for rd in CF.READOUTS:
                sv = ref[k]["per_participant"][pid][f"{rd}/regular"]
                for m in CF.QMETRICS:
                    assert pr[k][rd]["metrics"][m] == pytest.approx(sv[m], abs=1e-9), (pid, k, rd, m)
        assert pr["a"]["P_uni"].shape[:2] == (10, 10)
        if objective == "CS_SINGLE":
            assert "P_nat" in pr["a"]
    for k in ("a", "b"):
        assert ros[k].tau == pytest.approx(ref[k]["readout"]["tau"])
    # identical views -> identical outputs and zero layer-3 change
    same = {"base": views["a"], "rs": ev1.Reps(enc_a, head, bt)}
    per2, _ = CF.per_query_eval(objective, same, views["a"], bt, coh, 0, seed)
    for pr in per2.values():
        for rd in CF.READOUTS:
            a, c = pr["base"][rd], pr["rs"][rd]
            d = CF.rank_change(a["rank"], c["rank"], a["ll"], c["ll"], a["true"], c["true"], a["true_z"], c["true_z"])
            assert d["frac_rank_changed"] == 0 and d["d_logloss"] == 0


# ------------------------------------------------------------------------------------------------ split of u_base and r
def test_split_reps_decomposition():
    from auditory_alignment_v2.audio_targets import FixedFeatureHead
    from auditory_alignment_v2.temporal import build_encoder
    from auditory_alignment_v3 import residual32 as R32
    coh, bt, C = _fake_cohort(4)
    torch.manual_seed(0)
    enc = build_encoder("lag_local_tokens", C, 32, [(0, 8)], 100).eval()
    model = R32.ResidualModel(enc, R32.SmallContext(C), 32).eval()
    head = FixedFeatureHead(16, 32, np.zeros(16), np.ones(16), "dtu")
    rw = R32.Rows(bt, 4, 8)
    e0s = [s["e0"] for s in coh.segments[:5]]
    spl = CF.SplitReps(model, rw, bt, head, stride=4)
    ub, r, u = spl.triplets(e0s)
    assert np.abs(r).max() == 0 and np.abs(u - ub).max() <= 1e-6  # zero-initialised last layer: epoch 0 == base
    assert spl.forward_check <= 1e-6
    with torch.no_grad():
        model.res.residual[2].weight.normal_(0, 0.5); model.res.residual[2].bias.normal_(0, 0.5)
    spl = CF.SplitReps(model, rw, bt, head, stride=4)
    ub2, r2, u2 = spl.triplets(e0s)
    assert np.abs(ub2 - ub).max() <= 1e-6 and np.abs(r2).max() > 0
    assert np.allclose(u2, (ub2 + r2) / np.linalg.norm(ub2 + r2, axis=-1, keepdims=True), atol=1e-5)
    assert spl.forward_check <= 1e-5
    assert np.allclose(np.linalg.norm(ub2, axis=-1), 1, atol=1e-5)  # u_base is unit-norm: ||r||/||u|| = ||r||
    v_b, v_r = spl.view("base").u(e0s), spl.view("rs").u(e0s)
    assert np.array_equal(v_b, ub2) and np.array_equal(v_r, u2)


# ------------------------------------------------------------------------------------------------ synthetic records
def _m(ll, rk=0.2, t1=0.3, nc=40, nq=20):
    return {"top1": t1, "top5": 0.6, "mrr": 0.4, "rank_pct": rk, "logloss_bits": ll, "n_candidates": nc, "n_queries": nq}


def _ev(eff_u, eff_n, fold, n=8, nc=40, salt=0):
    rng = np.random.default_rng(int(1000 * (eff_u + 2 * eff_n)) % 997 + fold + salt)
    pp = {}
    for j in range(n):
        base = 4.0 + 0.1 * j
        ru = base - eff_u + 0.004 * rng.standard_normal(); rn = base - eff_n + 0.004 * rng.standard_normal()
        d = {"group": "hi", "n_segments": 20}
        for rd, reg in (("unified", ru), ("native", rn)):
            d[f"{rd}/regular"] = _m(reg, nc=nc); d[f"{rd}/mismatched_eeg"] = _m(reg + 1.0, nc=nc); d[f"{rd}/hard"] = _m(2.5, nc=9)
        pp[f"P{fold}{j}"] = d
    return {"per_participant": pp, "readout": {"alpha_unified": 1.0, "tau": {"unified": 0.1, "native": 0.1}, "n_test_candidates": nc}}


def _synthetic(sc_eff, rs_eff, bad_counts=None, reve_salt=()):
    """reve_salt: SC variants whose reve copy gets other noise (a different PCA draw); every other SC copy is identical."""
    rows, recs = [], {}
    for fold in (0, 1, 2):
        for o in CF.OBJS:
            e = f"L0{fold}{o}"
            rows.append({"experiment_id": e, "family_id": "A_LOCAL", "dataset": "dtu", "subject_fold": fold, "content_fold": 0, "seed": 3401,
                         "spec": {"objective": o, "target": "local", "architecture": "lag_local_tokens", "window": "full", "projection_dim": 32}})
            recs[e] = {"status": "complete", "eval": _ev(0, 0, fold), "windows_samples": [[0, 8]], "resolved_config": {"fs": 100}}
            for v, a in CF.RS_CONF:
                e = f"RS{fold}{o}{v}{a}"
                rows.append({"experiment_id": e, "family_id": "ALN32_RESIDUAL", "dataset": "dtu", "subject_fold": fold, "content_fold": 0, "seed": 3401,
                             "spec": {"objective": o, "target": "local", "architecture": a, "variant": v}})
                eu, en = rs_eff.get(v, (0.0, 0.0))
                curve = [{"epoch": k, "dev_risk_bits": 5.0 - 0.01 * k, "dev_rank": 0.3, "tau": 0.01, "train_loss": None} for k in range(4)]
                recs[e] = {"status": "complete", "eval": _ev(eu, en, fold), "epoch0_selected": False, "dependency": {"base": f"L0{fold}{o}"}, "curve": curve,
                           "selected_epoch": 3, "selected_dev_risk_bits": curve[3]["dev_risk_bits"], "epochs": 3, "n_train_segments": 100, "n_dev_segments": 30,
                           "n_cal_segments": 30, "dev_group": 0, "trainable_params": 1000, "window_samples": [-4, 8], "epoch0_max_abs_diff_vs_base": 6e-8,
                           "gpu_peak_allocated_mb": 1000 + (9000 if (a == "small_capacity_branch" and fold == 2) else 0), "device": "card-A", "eval_seconds": 30.0}
        e = f"L1{fold}"
        rows.append({"experiment_id": e, "family_id": "ALN32_LOCAL_SUPPORT", "dataset": "dtu", "subject_fold": fold, "content_fold": 0, "seed": 3401,
                     "spec": {"objective": "NCE", "target": "local", "variant": "local_aligned1000"}})
        recs[e] = {"status": "complete", "eval": _ev(0, 0, fold), "windows_samples": [[-4, 8]], "resolved_config": {"fs": 100}}
        for a in CF.ARCH:
            for base in ("L0", "L1"):
                e = f"SC{fold}{a}{base}"
                rows.append({"experiment_id": e, "family_id": "ALN32_SIMPLE_COMPLEMENT", "dataset": "dtu", "subject_fold": fold, "content_fold": 0, "seed": 3401,
                             "spec": {"objective": "NCE", "target": "local", "base": base, "architecture": a}})
                ev, fit = {}, {}
                for v in CF.SC_VARIANTS:
                    eu, en = sc_eff.get(v, (0.0, 0.0))
                    nc = 41 if bad_counts == (v, fold) else 40
                    salt = 7 if (a == "reve" and v in reve_salt) else 0
                    ev[v] = _ev(eu, en, fold, nc=nc, salt=salt)
                    fit[v] = {"alpha_rel": 0.01 if not salt else 0.1, "curve": []}
                recs[e] = {"status": "complete", "eval_variants": ev, "eval": ev["local_only"], "fit": fit, "n_fit_rows": 800 + fold, "n_train_participants": 6,
                           "n_pca_rows": 800, "k_pca": 64, "groups": 5, "base_trained_on_all_groups": True, "alpha_grid": [1e-5, 1e-3, 1e3],
                           "window_samples": [-4, 8], "dependency": {"base": f"{base}{fold}" + ("NCE" if base == "L0" else "")}}
    return rows, recs.get


def test_run_family_matches_bc_interim():
    from auditory_alignment_v3 import bc_interim as BI
    rows, load = _synthetic({}, {"residual_small_capacity": (0.3, 0.0), "residual_aligned_pretrained": (0.01, 0.0)})
    data = CF.load_values(rows, load, {})
    mem = [(f"{a}/{v}", ("L0", "dtu", "NCE"), ("RS", "dtu", "NCE", a, v), "t") for v, a in CF.RS_CONF]
    mine = CF.run_family("RS-VALUE|dtu|NCE", mem, data["vals"], "unified/regular/logloss_bits", [])
    theirs = BI.run_family("RS-VALUE|dtu|NCE", mem, data["vals"], "unified/regular/logloss_bits", [])
    assert mine["crit"] == pytest.approx(theirs["crit"])
    for k, m in mine["members"].items():
        for f in ("est", "ci_low", "ci_high", "sim_low", "sim_high"):
            assert m[f] == pytest.approx(theirs["members"][k][f], abs=1e-12)
        assert m["class"] == theirs["members"][k]["class"]


def test_same_contract_families():
    rows, load = _synthetic({"concat": (0.4, 0.0), "aligned_random": (0.0, 0.4), "local_only": (-0.3, -0.3)},
                            {"residual_small_capacity": (0.3, 0.0)}, bad_counts=("small_context", 1))
    xrows, xload = CF.expand_rows(rows, load)
    out, data = CF.same_contract(xrows, xload, {})
    f = out["families"]
    fu, fn = f["FN-DIRECT-SC|dtu|cbramod|L0|unified"]["members"], f["FN-DIRECT-SC|dtu|cbramod|L0|native"]["members"]
    assert fu["concat"]["class"] == "I>0" and fn["concat"]["class"] == "contains 0"           # unified-only effect
    assert fn["aligned_random"]["class"] == "I>0" and fu["aligned_random"]["class"] == "contains 0"  # native-only effect
    assert fu["local_only"]["class"] == "I<0" and fu["local_only"]["est"] == pytest.approx(-0.3, abs=0.01)  # remap cost
    assert "small_context" not in fu and any("small_context: candidate / query counts differ" in x for x in out["excluded_pairs"])
    r = f["RS-VALUE|dtu|NCE"]["members"]; rn = f["FN-RS-NATIVE|dtu|NCE"]["members"]
    assert r["small_capacity_branch/residual_small_capacity"]["class"] == "I>0" and rn["small_capacity_branch/residual_small_capacity"]["class"] == "contains 0"
    assert out["levels"]["L0|dtu|NCE"]["n"] == 24 and "unified/regular/logloss_bits" in out["levels"]["SC|dtu|NCE|reve|L1|concat"]
    sec = out["secondary"]["FN-DIRECT-SC|dtu|cbramod|L0|unified"]
    assert set(sec) == {"unified/regular/rank_pct", "unified/regular/top1", "unified/gain_bits"}
    # access labels travel with the members (local_refit_capacity under L0 is access-matched)
    assert fu["local_refit_capacity"]["tag"].startswith("access-matched") and fu["concat"]["tag"].startswith("context-assisted")
    assert all(m["tag"].startswith(("access-matched", "remap only")) for m in f["FN-DIRECT-SC|dtu|reve|L1|unified"]["members"].values())
    assert all(m["tag"].startswith("context-assisted") for m in r.values())


def test_access_tags():
    for base in ("L0", "L1"):
        assert CF.access_tag(("SC", "fau", "NCE", "reve", base, "local_only")).startswith("remap only")
        assert CF.access_tag(("SC", "fau", "NCE", "reve", base, "local_refit_capacity")).startswith("access-matched")
    for v in CF.SC_CONTEXT_VARIANTS:
        assert CF.access_tag(("SC", "dtu", "NCE", "cbramod", "L0", v)).startswith("context-assisted")
        assert CF.access_tag(("SC", "dtu", "NCE", "cbramod", "L1", v)).startswith("access-matched")
    for v, a in CF.RS_CONF:
        assert CF.access_tag(("RS", "dtu", "NCE", a, v)).startswith("context-assisted")
    assert set(CF.SC_CONTEXT_VARIANTS) | {"local_only", "local_refit_capacity"} == set(CF.SC_VARIANTS)


def test_epoch0_identity_and_layer4():
    rows, load0 = _synthetic({}, {})
    recs = {}
    for r in rows:
        if r["family_id"] != "ALN32_RESIDUAL":
            continue
        rec = dict(load0(r["experiment_id"]))
        base = f"L0{r['subject_fold']}{r['spec']['objective']}"
        e0 = r["spec"]["variant"] == "residual_small_capacity"
        if e0:
            rec["eval"] = load0(base)["eval"]
        sel = 0 if e0 else 3
        curve = [{"epoch": k, "dev_risk_bits": 5.0 - (0.02 * k if k <= 3 else 0.05), "dev_rank": 0.3, "tau": 0.01, "train_loss": None} for k in range(5)]
        rec.update({"dependency": {"base": base}, "curve": curve, "selected_epoch": sel, "selected_dev_risk_bits": curve[sel]["dev_risk_bits"],
                    "epoch0_selected": e0, "epochs": 4, "epoch0_max_abs_diff_vs_base": 5e-8 if e0 else 7e-8})
        recs[r["experiment_id"]] = rec
    load = lambda e: recs.get(e) or load0(e)
    e0 = CF.epoch0_identity(rows, load)
    assert e0["n"] == 6 and e0["max_abs_diff"] == 0.0
    assert e0["record_field"]["epoch0_units_range"] == [5e-8, 5e-8] and e0["record_field"]["all_units_range"] == [5e-8, 7e-8]
    assert "not measured on the outer test" in e0["record_field"]["where"]
    l4 = CF.dev_test_layer(rows, load)
    pc = l4["per_config"]["RS|dtu|NCE|cbramod|residual_aligned_pretrained"]
    assert pc["n_units"] == 3 and pc["n_epoch0"] == 0 and pc["d_dev_mean"] == pytest.approx(0.06)
    assert l4["per_config"]["RS|dtu|NCE|small_capacity_branch|residual_small_capacity"]["d_dev_mean"] == 0.0
    assert l4["per_config"]["RS|dtu|NCE|small_capacity_branch|residual_small_capacity"]["d_test_R_unified_mean"] == 0.0


def _ckpts(rows, load0, out, zero_variant="residual_small_capacity"):
    (out / "ckpt").mkdir(parents=True, exist_ok=True); recs = {}
    for r in rows:
        if r["family_id"] != "ALN32_RESIDUAL":
            continue
        e0 = r["spec"]["variant"] == zero_variant
        W2 = torch.zeros(4, 3) if e0 else torch.full((4, 3), 0.1)
        torch.save({"model": {"res.residual.0.weight": torch.ones(3, 5), "res.residual.0.bias": torch.zeros(3), "res.residual.2.weight": W2,
                              "res.residual.2.bias": torch.zeros(4)}}, out / "ckpt" / f"{r['experiment_id']}_best.pt")
        rec = dict(load0(r["experiment_id"])); rec["epoch0_selected"] = e0
        if e0:
            rec["selected_epoch"] = 0; rec["selected_dev_risk_bits"] = rec["curve"][0]["dev_risk_bits"]
        recs[r["experiment_id"]] = rec
    return lambda e: recs.get(e) or load0(e)


def _unit_out(rec, ok=True, dv=2e-6):
    per = {pid: {"layers": {k: 0.1 for k in CF.LAYER12}, "layer3": {**{rd: {k: 0.01 for k in CF.LAYER3} for rd in CF.READOUTS},
                                                                     "unified_prediction": {"rel_diff": 0.05, "zcorr": 0.99}, "native_prediction": {"rel_diff": 0.1}}}
           for pid in rec["eval"]["per_participant"]}
    lay = {"relative_residual_norm_mean": 0.1, "angle_deg_mean": 5.0, "normalized_change_mean": 0.08}
    rp = {"base_record": {**{k: 1e-7 for k in CF.REPRO_KEYS}, "unified/top1": 0.04}, "rs_record": {k: (4e-4 if ok else 3e-3) for k in CF.REPRO_KEYS},
          "participants_missing_in_record": {}, "within_tolerance": True}  # the stored flag is not trusted; the rule is re-applied
    return {"per_identity": per, "reproduction": rp, "comparable_to_record": True, "dev_only": False,
            "dev": {"layers": lay, "selected": {"abs_diff": dv if ok else 5e-2}, "epoch0": {"abs_diff": 1e-6}}, "test_layers": lay,
            "code_sha256": {"complement_function_eval.py": "e" * 64}}


def test_checkpoint_layer_and_collect(tmp_path):
    rows, load0 = _synthetic({}, {})
    out = tmp_path / "out"; units = tmp_path / "units"; units.mkdir()
    load = _ckpts(rows, load0, out)
    for r in rows:
        if r["family_id"] == "ALN32_RESIDUAL" and r["spec"]["variant"] == "residual_aligned_pretrained" and r["spec"]["objective"] == "NCE":
            ok = not (r["subject_fold"] == 2 and r["spec"]["architecture"] == "cbramod")  # one re-run fails to reproduce its record
            json.dump(_unit_out(load(r["experiment_id"]), ok), open(units / f"{r['experiment_id']}.json", "w"))
    ck = CF.checkpoint_layer(rows, load, out=str(out))
    assert ck["epoch0_vs_zero_mismatch"] == [] and ck["n_epoch0_units"] == 6 and ck["n_epoch0_with_zero_last_layer"] == 6
    v = ck["per_config"]["RS|dtu|NCE|cbramod|residual_aligned_pretrained"]
    assert v["n_zero_last_layer"] == 0 and v["W2_fro_median"] == pytest.approx(math.sqrt(12 * 0.01))
    assert ck["per_config"]["RS|dtu|CS_SINGLE|small_capacity_branch|residual_small_capacity"]["n_zero_last_layer"] == 3
    col = CF.collect_units(rows, load, {}, out_dir=str(units), ckpt=ck)
    assert len(col["per_config"]) == 10  # every configuration is listed, covered or not
    pc = col["per_config"]["RS|dtu|NCE|cbramod|residual_aligned_pretrained"]
    assert pc["n_units"] == 3 and pc["n_units_covered"] == 2 and pc["coverage"] == "partial" and "L12/rel_norm" not in pc  # no partial summary
    assert col["flagged_units"] == ["RS2NCEresidual_aligned_pretrainedcbramod"]
    pr = col["per_config"]["RS|dtu|NCE|reve|residual_aligned_pretrained"]
    assert pr["complete"] and pr["n_identities"] == 24 and pr["L12/rel_norm"]["est"] == pytest.approx(0.1)
    z = col["per_config"]["RS|dtu|NCE|small_capacity_branch|residual_small_capacity"]
    assert z["L12/rel_norm"]["est"] == 0.0 and z["L3/unified/frac_rank_changed"]["est"] == 0.0 and z["n_identities"] == 24
    assert col["per_config"]["RS|dtu|CS_SINGLE|cbramod|residual_aligned_random"]["coverage"] == "none"
    assert col["configs"] == {"complete": 3, "partial": 1, "none": 6}
    assert col["n_units_zero"] == 6 and col["n_units_run"] == 5 and col["evaluator_sha256_of_merged_runs"] == {"e" * 64: 5}
    assert len(col["pending_units"]) == 3 * 2 + 3 * 4  # 3 folds x (NCE random x 2 backbones + CS 4 FM configs): no outputs yet
    bad = dict(ck); bad["epoch0_vs_zero_mismatch"] = ["RS0NCEresidual_small_capacitysmall_capacity_branch"]
    col2 = CF.collect_units(rows, load, {}, out_dir=str(units), ckpt=bad)
    assert "RS0NCEresidual_small_capacitysmall_capacity_branch" in col2["flagged_units"]
    assert not col2["per_config"]["RS|dtu|NCE|small_capacity_branch|residual_small_capacity"]["complete"]


def test_reproduction_rule():
    base = {"comparable_to_record": True, "dev_only": False,
            "reproduction": {"base_record": {k: 1e-7 for k in CF.REPRO_KEYS}, "rs_record": {k: 5e-4 for k in CF.REPRO_KEYS}, "participants_missing_in_record": {}},
            "dev": {"selected": {"abs_diff": 3e-6}, "epoch0": {"abs_diff": 4e-6}}}
    assert CF.reproduces(base)
    flip = json.loads(json.dumps(base)); flip["reproduction"]["rs_record"]["unified/top1"] = 1 / 23  # a near-tie top-1 flip: reported, not bounded
    assert CF.reproduces(flip)
    for path, val in ((("reproduction", "rs_record", "native/logloss_bits"), 2e-3), (("dev", "selected", "abs_diff"), 0.01), (("dev", "epoch0", "abs_diff"), None)):
        bad = json.loads(json.dumps(base)); d = bad
        for k in path[:-1]:
            d = d[k]
        d[path[-1]] = val
        assert not CF.reproduces(bad), path
    assert not CF.reproduces({**base, "comparable_to_record": False}) and not CF.reproduces({**base, "dev_only": True})
    miss = json.loads(json.dumps(base)); miss["reproduction"]["participants_missing_in_record"] = {"rs": ["P1"]}
    assert not CF.reproduces(miss)


def test_limits():
    assert CF.Limits().comparable() and not CF.Limits(tiny=True).comparable() and not CF.Limits(max_queries=3).comparable()
    t = CF.Limits(tiny=True)
    assert t.max_test_participants == 2 and t.max_readout_segs == 24


# ------------------------------------------------------------------------------------------------ v2 provenance
def test_code_versions_and_snapshot(tmp_path):
    cv = EV.code_versions()
    assert cv["complement_function_eval.py"] == EV.sha256(EV.__file__) and cv["complement_function.py"] == CF.MODULE_SHA256 == EV.sha256(CF.__file__)
    assert all(rel in cv for rel in EV.FROZEN_DEPS) and "reference residuals.py" in cv
    snap = EV.snapshot_code(str(tmp_path / "snap"))
    assert set(snap) == {"complement_function_eval.py", "complement_function.py"}
    for name, rel in snap.items():
        p = os.path.join(EV.REPO, rel)
        assert EV.sha256(p) == cv[name] and oct(os.stat(p).st_mode & 0o777) == "0o600"
    assert EV.snapshot_code(str(tmp_path / "snap")) == snap  # idempotent


def test_cli_versions(tmp_path):
    snap = tmp_path / "snap"; out = tmp_path / "units"; out.mkdir()
    EV.snapshot_code(str(snap))
    json.dump({"code_sha256": {"complement_function.py": CF.MODULE_SHA256}}, open(out / "A.json", "w"))
    json.dump({"code_sha256": {"complement_function.py": "f" * 64}}, open(out / "B.json", "w"))
    v = CF.cli_versions(str(out), str(snap))
    assert v[CF.MODULE_SHA256] == {"outputs": 1, "snapshot": True, "main_identical_to_current": True}
    assert v["f" * 64] == {"outputs": 1, "snapshot": False, "main_identical_to_current": False}


def test_evaluator_math_identical_to_v1():
    """The value-producing functions moved to complement_function_eval.py unchanged (v1 copy kept in private/)."""
    v1 = os.path.join(CF.V1_COPY, "complement_function.py")
    if not os.path.exists(v1):
        pytest.skip("v1 copy not present")

    def defs(path):
        src = open(path).read(); t = ast.parse(src); lines = src.splitlines()
        return {n.name: "\n".join(lines[n.lineno - 1:n.end_lineno]) for n in t.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))}
    a, b = defs(v1), defs(EV.__file__)
    for name in ("reproduces", "residual_rows", "residual_summary", "query_ranks", "query_logloss_bits", "metrics_from_queries", "rank_change", "true_scores",
                 "Limits", "build_unit", "SplitReps", "_pool_of", "per_query_eval", "_zcorr", "layer_rows_for", "_jl"):
        assert a[name] == b[name], name


def test_compare_versions(tmp_path):
    a, b = tmp_path / "v1", tmp_path / "v2"; a.mkdir(); b.mkdir()
    u = {"eid": "X", "seconds": 5.0, "per_identity": {"P1": {"layers": {"rel_norm": 0.1}}}, "dev": {"selected": {"risk_bits": 6.0}, "seconds": 3},
         "code_sha256": {"complement_function.py": "a" * 64}}
    w = json.loads(json.dumps(u)); w["seconds"] = 99.0; w["per_identity"]["P1"]["layers"]["rel_norm"] = 0.1 + 2e-7; w["code_sha256"] = {"complement_function_eval.py": "b" * 64}
    json.dump(u, open(a / "X.json", "w")); json.dump(w, open(b / "X.json", "w"))
    np.savez(a / "X_queries.npz", rank_base_unified=np.array([0, 1, 2]), ll_base_unified=np.array([1.0, 2.0, 3.0]))
    np.savez(b / "X_queries.npz", rank_base_unified=np.array([0, 1, 3]), ll_base_unified=np.array([1.0, 2.0, 3.0 + 1e-6]))
    c = CF.compare_versions(str(a), str(b))["X.json"]
    assert c["max_abs_diff"] == pytest.approx(2e-7) and c["worst_leaf"] == "per_identity/P1/layers/rel_norm"  # timing excluded
    assert c["code_sha256_v1"] == "a" * 64 and c["code_sha256_v2_evaluator"] == "b" * 64
    assert c["queries"]["max_abs_diff_float"] == pytest.approx(1e-6) and c["queries"]["max_frac_differing_int"] == pytest.approx(1 / 3)


# ------------------------------------------------------------------------------------------------ assets
def test_ckpt_inventory_and_file_kinds(tmp_path, monkeypatch):
    out = tmp_path / "out"; (out / "ckpt").mkdir(parents=True); store = tmp_path / "store"; store.mkdir()
    e1, e2, e3 = "ALN3X_" + "1" * 16, "ALN3X_" + "2" * 16, "ALN3X_" + "3" * 16
    (store / f"{e1}_best.pt").write_bytes(b"x"); os.symlink(store / f"{e1}_best.pt", out / "ckpt" / f"{e1}_best.pt")
    (out / "ckpt" / f"{e2}_best.pt").write_bytes(b"x"); (out / "ckpt" / f"{e2}_resume.pt").write_bytes(b"x")
    os.symlink(store / "gone.pt", out / "ckpt" / f"{e3}_best.pt")
    inv = CF.ckpt_inventory([e1, e2, e3], out=str(out))
    assert inv["file_patterns"] == {"<eid>_best.pt": 2, "<eid>_best.pt + <eid>_resume.pt": 1}
    assert inv["link_states"] == {"link": 1, "file": 2, "broken_link": 1} and inv["units_without_exactly_one_file"] == [e2]
    assert CF.file_kind("private/auditory_alignment_v3/units", "<eid>.json") == "unit record"
    assert CF.file_kind("private/auditory_alignment_v3/probe_out_r32/ckpt", "<eid>_best.pt") == "engineering probe of the runner"
    assert CF.file_kind("private/auditory_alignment_v3/ckpt", "<eid>_best.pt") == "checkpoint"
    assert CF.file_kind("private/auditory_alignment_v3/sci_r1/continuous", "<eid>__frozen.npz") == "sci_r1 continuous-science output"
    assert CF.file_kind("results/auditory_alignment_v3/aln34/complement_function/units", "<eid>.json") == "this lane's evaluator output"
    assert CF.file_kind("private/auditory_alignment_v3/pool/q", "<eid>.tries") == "scheduler marker"
    assert CF.file_kind("private/auditory_alignment_v3/logs/units", "<eid>.log") == "unit log"


def test_npz_contents_and_search(tmp_path, monkeypatch):
    d = tmp_path / "private" / "sci_r1" / "continuous"; d.mkdir(parents=True)
    e = "ALN3_" + "a" * 16
    np.savez(d / f"{e}__frozen.npz", s1=np.zeros((3, 25, 9)), tg=np.zeros((3, 25, 25, 4)), pooled_lam=np.zeros(3), perq=np.zeros((60, 2)))
    json.dump({"participants": ["a", "b", "c"], "n_queries": [20, 20, 20]}, open(d / f"{e}__frozen.json", "w"))
    monkeypatch.setattr(CF, "REPO", str(tmp_path))
    g = CF.eid_file_search({e: "L0"}, [str(tmp_path / "private")])
    keys = sorted(g)
    assert [k[2] for k in keys] == ["<eid>__frozen.json", "<eid>__frozen.npz"]
    desc = CF.describe_group("L0", "private/sci_r1/continuous", "<eid>__frozen.npz", g[keys[1]])
    c = desc["contents"]
    assert desc["kind"] == "sci_r1 continuous-science output" and c["first_dim_equals_participants"] == {"s1": 1, "tg": 1, "pooled_lam": 1}
    assert c["first_dim_equals_test_queries"] == {"perq": 1} and c["shapes_first_file"]["tg"] == [3, 25, 25, 4]


def test_fm_weights_check(tmp_path, monkeypatch):
    from auditory_alignment_v2 import foundation_adapter as FA
    root = tmp_path / "fm"; rep = root / "repoA"; rep.mkdir(parents=True); code = root / "code" / "models"; code.mkdir(parents=True)
    (rep / "w.bin").write_bytes(b"weights"); (rep / "c.json").write_bytes(b"{}"); (code / "m.py").write_bytes(b"")
    good = CF._sha256_stream(str(rep / "w.bin"))
    json.dump({"org/repoA": {"revision": "abc1234def", "dir": str(rep), "files": {"w.bin": good, "c.json": "0" * 64, "absent.bin": "1" * 64}},
               "github:org/code": {"dir": str(root / "code"), "head": "h", "files": ["m.py", "gone.py"]}}, open(root / "FETCH_RECEIPT.json", "w"))
    for k, v in (("FM_ROOT", str(root)), ("CBRAMOD_W", str(rep / "w.bin")), ("REVE_DIR", str(rep)), ("REVE_POS", str(rep))):
        monkeypatch.setattr(FA, k, v)
    out = CF.fm_weights_check()
    a = out["repos"]["org/repoA"]
    assert a["files"] == {"w.bin": "match", "c.json": "MISMATCH", "absent.bin": "absent"} and a["n_match"] == 1 and not out["all_hashed_files_match"]
    assert out["repos"]["github:org/code"] == {"head": "h", "n_files": 2, "n_present": 1, "hashes_in_receipt": False}


# ------------------------------------------------------------------------------------------------ SC copies, identities, budgets, regression
def test_sc_backbone_copies_and_dedupe():
    rows, load = _synthetic({"concat": (0.4, 0.0)}, {}, reve_salt=("small_context",))
    xrows, xload = CF.expand_rows(rows, load)
    table, data = CF.same_contract(xrows, xload, {})
    cp = CF.sc_backbone_copies(rows, load, data["vals"])
    lo, sm = cp["dtu|L0|local_only"], cp["dtu|L0|small_context"]
    assert lo["unit_pairs"] == 3 and lo["alpha_equal"] == 3 and lo["max_participant_abs_diff_unified"] == 0 and lo["max_identity_abs_diff_native"] == 0
    assert sm["alpha_equal"] == 0 and sm["max_participant_abs_diff_unified"] > 0 and not sm["reads_fm"] and cp["dtu|L1|concat"]["reads_fm"]
    for rd in CF.READOUTS:
        c, _ = CF.class_counts(table, "FN-DIRECT-SC", rd)
        cd, _ = CF.class_counts(table, "FN-DIRECT-SC", rd, dedupe=True)
        assert sum(c.values()) == 24 and sum(cd.values()) == 22  # local_only counted once per base
    agree, n = CF.local_only_copy_classes(table)
    assert n == 4 and agree == 4


def test_manifest_identities():
    man = {"HC:1": ("HC:1", "HC", "human"), "HC:2": ("HC:2", "HC", "human"), "HC-v:1": ("HCv:1vocod", "HC-v", "human"), "CI:1": ("CI:1", "CI", "human"),
           "ph:1": ("phantom:j", "Artifact", "phantom"), "ph:2": ("phantom:j", "Artifact", "phantom")}
    m = CF.manifest_identities(man)
    assert m["human_records"] == 4 and m["human_identities"] == 4 and m["identities_by_condition"] == {"CI": 1, "HC": 2, "HC-v": 1}
    assert m["uids_shared_across_conditions"] == [] and m["non_human_records"] == 2 and m["non_human_entities"] == 1


def test_budgets_and_access():
    rows, load = _synthetic({}, {})
    b = CF.budgets(rows, load)
    sc = b["SC"]["dtu|L0"]
    assert sc["records"] == 6 and sc["n_fit_rows"] == [800, 802] and sc["k_pca"] == [64] and sc["base_trained_on_all_groups"]
    assert b["SC_code"]["anchors_per_training_segment"] == "8" and b["SC_code"]["pca_subsample_rng"] == "GROUP_SEED + 2"
    assert b["RS"]["dtu|residual_small_capacity"]["n_dev_segments"] == [30] and b["RS_code"]["Q_anchors_per_segment"] == 8
    assert "niter = 4" in b["SC_code"]["pca"] and b["RS_code"]["dev_rng"] == "GROUP_SEED + 1"
    assert b["RS_code"]["development"].startswith("<= 300 ") and b["RS_code"]["dev_temperature"].startswith("<= 300 ")
    ev = b["evaluator"]
    assert ev["readout_segments"] == 400 and ev["calibration_queries"] == "300" and ev["unified_alpha_grid"] == "np.logspace(-4, 8, 13)"
    assert ev["native_CS_SINGLE_alpha_grid"] == "np.logspace(-3, 3, 7)"
    ac = CF.access_table(rows, load)
    assert ac["windows"]["L0|dtu"] == ["[[0, 8]]"] and ac["windows"]["L1|dtu"] == ["[[-4, 8]]"] and ac["windows"]["SC|dtu"] == ["[-4, 8]"]
    assert ac["fs"] == {"dtu": 100}


def test_regression_checks(tmp_path, monkeypatch):
    rows, load = _synthetic({}, {"residual_small_capacity": (0.3, 0.0)})
    xrows, xload = CF.expand_rows(rows, load)
    table, _ = CF.same_contract(xrows, xload, {})
    fr = {"families": {lab: {"members": {n: {k: m[k] for k in ("est", "ci_low", "ci_high", "sim_low", "sim_high", "class")} for n, m in f["members"].items()}}
                       for lab, f in table["families"].items() if lab.startswith("RS-VALUE|") and f["members"]}}
    lab0 = next(iter(fr["families"])); n0 = next(iter(fr["families"][lab0]["members"]))
    fr["families"][lab0]["members"][n0]["est"] += 1e-3
    json.dump(fr, open(tmp_path / "rs.json", "w"))
    json.dump({"levels": {k: {m: {"est": v[m]["est"]} for m in CF.PRIMARY34.values() if m in v} for k, v in table["levels"].items() if k.startswith("SC|")}},
              open(tmp_path / "sc.json", "w"))
    v1 = {"same_contract": json.loads(json.dumps(CF._jl(table)))}
    for f in v1["same_contract"]["families"].values():
        for m in f["members"].values():
            if m["tag"].startswith("access-matched (the base"):
                m["tag"] = "SC vs original direct base (context-assisted: base L0 reads post-only EEG)" if "L0" in m["ref"] else m["tag"]
    json.dump(v1, open(tmp_path / "v1.json", "w"))
    monkeypatch.setattr(CF, "FROZEN_RS_JSON", str(tmp_path / "rs.json")); monkeypatch.setattr(CF, "FROZEN_SC_JSON", str(tmp_path / "sc.json"))
    monkeypatch.setattr(CF, "REPO", str(tmp_path))
    rg = CF.regression_checks(table, str(tmp_path / "v1.json"))
    assert rg["rs_value_vs_frozen"]["max_abs_diff"] == pytest.approx(1e-3) and rg["rs_value_vs_frozen"]["class_mismatches"] == 0
    assert rg["sc_levels_vs_frozen"]["max_abs_diff_est"] == 0 and rg["sc_levels_vs_frozen"]["values"] > 0
    v = rg["v1_vs_v2"]
    assert v["max_abs_diff"] == 0 and v["class_changes"] == 0 and v["tag_changes"] == 4 and v["v1_refit_capacity_L0_context_tags"] == 4
    assert v["access_class_changes"] == {"context-assisted -> access-matched": 4}
    assert CF.access_class("selected epoch vs epoch 0 (= base L0)") == "no access label" and CF.access_class("remap only") == "remap only"
    assert v["levels_max_abs_diff_est"] == 0


# ------------------------------------------------------------------------------------------------ GPU plan and worker
def test_write_units_file(tmp_path, monkeypatch):
    rows, load0 = _synthetic({}, {})
    out = tmp_path / "out"
    load = _ckpts(rows, load0, out)
    monkeypatch.setattr(CF.core, "OUT", str(out))
    units = tmp_path / "units"; units.mkdir()
    done = next(r for r in rows if r["family_id"] == "ALN32_RESIDUAL" and r["spec"]["variant"] == "residual_aligned_random")
    json.dump(_unit_out(load(done["experiment_id"])), open(units / f"{done['experiment_id']}.json", "w"))
    p, n_need, n_zero, n_pend, est, mem = CF.write_units_file(rows, load, str(tmp_path / "u.txt"), str(units), str(tmp_path / "w.sbatch"))
    assert (n_need, n_zero, n_pend) == (24, 6, 23)
    txt = open(p).read(); sb = open(tmp_path / "w.sbatch").read()
    assert CF.PY in txt and "HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1" in txt and " python -B" not in txt and "--shard" in txt
    assert "no measurement of this evaluator on a GPU exists" in txt and "Pending: 23 units" in txt
    assert txt.count(" pending\n") == 23 and txt.count(" done_v2\n") == 1
    assert est["pending"]["total_gpu_minutes"] < est["all_listed"]["total_gpu_minutes"]
    assert mem["dtu|small_capacity_branch"]["max_mb"] == 10000 and mem["dtu|small_capacity_branch"]["units_above_2x_min"] == 2
    assert "--units-file" in sb and "HF_HUB_OFFLINE=1" in sb and "NOT submitted" in sb and CF.PY in sb
    assert oct(os.stat(p).st_mode & 0o777) == "0o600" and oct(os.stat(tmp_path / "w.sbatch").st_mode & 0o777) == "0o600"


def _units_list(tmp_path, eids):
    p = tmp_path / "list.txt"
    p.write_text("# header\n" + "\n".join(f"{e} x y" for e in eids) + "\n")
    return str(p)


def test_worker_claims_shards_tries(tmp_path, monkeypatch):
    out = tmp_path / "units"; out.mkdir()
    eids = [f"ALN3X_{i:016x}" for i in range(6)]
    calls = []

    def fake_eval(eid, device, limits, dev_only, out_dir, rows, load):
        calls.append(eid)
        if eid == eids[4]:
            raise RuntimeError("boom")
        return EV._write_json(os.path.join(out_dir, f"{eid}.json"), {"eid": eid})
    monkeypatch.setattr(CF, "evaluate_unit", fake_eval)
    monkeypatch.setenv("SLURM_JOB_ID", "111")
    lst = _units_list(tmp_path, eids)
    json.dump({"eid": eids[0]}, open(out / f"{eids[0]}.json", "w"))                       # finished before
    CF.try_claim(str(out / "claims"), eids[1], {"job": "222", "host": "h", "pid": 1})     # a live foreign worker (fresh claim)
    CF.try_claim(str(out / "claims"), eids[2], {"job": "111", "host": "h", "pid": 1})     # our own claim from before a requeue
    t = CF.run_units_file(lst, "cpu", str(out), rows=[], load=lambda e: None, live={"222"})
    assert calls == [eids[2], eids[3], eids[4], eids[5]] and t["skip_done"] == 1 and t["skip_claimed"] == 1 and t["failed"] == 1 and t["done"] == 3
    assert t["released_stale_claims"] == 1 and os.path.isdir(out / "claims" / f"{eids[1]}.claim") and not os.path.exists(out / "claims" / f"{eids[2]}.claim")
    f = json.load(open(out / f"{eids[4]}.FAILED.json"))
    assert f["tries"] == 1 and "boom" in f["error"]
    for k in range(2):  # two more failing passes reach max_tries; then the unit is skipped
        CF.run_units_file(lst, "cpu", str(out), rows=[], load=lambda e: None, live={"222"})
    assert json.load(open(out / f"{eids[4]}.FAILED.json"))["tries"] == 3
    calls.clear()
    t = CF.run_units_file(lst, "cpu", str(out), rows=[], load=lambda e: None, live={"222"})
    assert calls == [] and t["skip_failed"] == 1
    # shards partition the list (claims alone already prevent duplicates)
    assert CF.parse_shard("1/3") == (1, 3) and CF.parse_shard(None) is None
    with pytest.raises(ValueError):
        CF.parse_shard("3/3")
    out2 = tmp_path / "u2"; out2.mkdir(); calls.clear()
    CF.run_units_file(lst, "cpu", str(out2), shard=(1, 3), rows=[], load=lambda e: None, live=set())
    assert calls == [eids[1], eids[4]]


def test_sweep_claims(tmp_path):
    c = tmp_path / "claims"
    me = {"job": "9", "host": "h", "pid": 1}
    for e, owner in (("own", {"job": "9"}), ("dead", {"job": "5"}), ("live", {"job": "6"}), ("young", {"job": "5"}), ("noowner", None)):
        os.makedirs(c / f"{e}.claim")
        if owner:
            json.dump(owner, open(c / f"{e}.claim" / "owner.json", "w"))
    old = time.time() - 3600
    for e in ("own", "dead", "live"):
        os.utime(c / f"{e}.claim", (old, old))
    assert sorted(CF.sweep_claims(str(c), me, {"6"})) == ["dead", "own"]  # 'young' < 2 min and 'noowner' < 10 min are kept
    assert CF.sweep_claims(str(c), me, None) == []  # squeue unavailable: no foreign claim is released
    os.utime(c / "noowner.claim", (old, old))
    assert CF.sweep_claims(str(c), me, None) == ["noowner"]


# ------------------------------------------------------------------------------------------------ report
def test_report_renders(tmp_path):
    rows, load0 = _synthetic({"concat": (0.4, 0.0)}, {"residual_small_capacity": (0.3, 0.0)})
    out_dir = tmp_path / "out"
    load = _ckpts(rows, load0, out_dir, zero_variant="none")
    xrows, xload = CF.expand_rows(rows, load)
    table, data = CF.same_contract(xrows, xload, {})
    ck = CF.checkpoint_layer(rows, load, out=str(out_dir))
    inv = {"units": 30, "file_patterns": {"<eid>_best.pt": 30}, "link_states": {"link": 30}, "link_target_roots": {"/projects": 30}, "units_without_exactly_one_file": []}
    au = {"SC": {"rows": 12, "records_complete": 12, "variant_evaluations": 72, "state(seed,status,ckpt,eval_variants,fit_log)": {}, "ckpt_inventory": inv, "saved": "s", "not_saved": "n"},
          "RS": {"rows": 30, "per_seed": {"3401": {"rows": 30}}, "state(seed,status,best_ckpt,resume_ckpt)": {}, "selected_epoch": {}, "ckpt_inventory(seed 3401)": inv,
                 "saved": "s", "epoch0": "e", "not_saved": "n"},
          "L0 (A_LOCAL lag_local_tokens full)": {"state(dataset,objective,status,ckpt)": {}, "ckpt_inventory": inv},
          "L1 (ALN32_LOCAL_SUPPORT local_aligned1000)": {"state(dataset,objective,status,ckpt)": {}, "ckpt_inventory": inv},
          "dependency_missing": [], "fm_weights": {"repos": {"org/r": {"revision": "abcdef0", "n_files": 2, "n_match": 2, "files": {}}}, "all_hashed_files_match": True},
          "files_by_id": [{"role": "L0", "dir": "d", "pattern": "<eid>__frozen.npz", "files": 3, "kind": "sci_r1 continuous-science output",
                           "contents": {"shapes_first_file": {"s1": [3, 25, 9]}, "first_dim_equals_participants": {"s1": 3}, "first_dim_equals_test_queries": {}}}],
          "files_by_id_search": "x", "per_query_prediction_files_outside_this_lane": []}
    need, zero, pending, est = CF.gpu_units(rows, load, str(tmp_path / "none"))
    units = tmp_path / "units"; units.mkdir()
    for r in rows:  # one fully covered configuration
        if r["family_id"] == "ALN32_RESIDUAL" and r["spec"]["variant"] == "residual_aligned_pretrained" and r["spec"]["architecture"] == "reve" and r["spec"]["objective"] == "NCE":
            json.dump(_unit_out(load(r["experiment_id"])), open(units / f"{r['experiment_id']}.json", "w"))
    out = {"meta": {"generated": "now", "slurm_job": "local", "note": "n", "note_correction": "c", "supersedes": "v1dir", "seed": 3401, "n_boot": 4000,
                    "code_sha256": {"x": "0" * 64}, "code_snapshot": {"a.py": "snap/a.py"}},
           "same_contract": table, "record_counts": CF.record_counts(rows, load), "federici_identities": CF.manifest_identities({"a": ("a", "HC", "human")}),
           "access": CF.access_table(rows, load), "budgets": CF.budgets(rows, load), "sc_backbone_copies": CF.sc_backbone_copies(rows, load, data["vals"]),
           "regression": {}, "epoch0_identity": CF.epoch0_identity(rows, load), "readout_scales": CF.readout_scales(rows, load),
           "layer4_dev_test": CF.dev_test_layer(rows, load), "checkpoint_layer": ck, "asset_audit": au,
           "gpu_plan": {"units_file": "u.txt", "sbatch_template": "s.sbatch", "n_units_listed": len(need), "n_units_pending": len(pending), "n_epoch0_units_exact_zero": len(zero),
                        **est, "gpu_memory_records": CF.gpu_memory_from_records(rows, load)},
           "layers_1_3": CF.collect_units(rows, load, {}, out_dir=str(units), ckpt=ck),
           "engineering_checks": {"v2": CF.engineering_checks(str(tmp_path / "none")), "v1_kept_not_merged": CF.engineering_checks(str(tmp_path / "none"))},
           "v1_vs_v2_unit_outputs": {}}
    p = CF.write_report(out, str(tmp_path / "r.md"))
    txt = open(p).read()
    for s in ("## 0. Version history", "## 1. Level of held-out development", "## 2. Same-contract checks", "## 3. Input access and fit budgets",
              "## 5. SC variants vs the original direct base", "## 6. RS selected epoch vs epoch 0", "## 7. Layer 4", "## 9. Layers 1–3", "## 10. Asset audit",
              "## 11. GPU plan", "### 12.3 Competing explanations", "pending the GPU run", "I>0: dtu·cbramod·L0/concat", "over the 22 distinct contrasts",
              "access-matched (the base's own tokens)", "never measured for this evaluator", "not covered 9", "SC in-sample caveat",
              "RS·dtu·NCE·reve·residual_aligned_pretrained: the selected residual moves the normalised representation", "computed for RS·dtu·NCE·reve"):
        assert s in txt, s
    assert oct(os.stat(p).st_mode & 0o777) == "0o600"
