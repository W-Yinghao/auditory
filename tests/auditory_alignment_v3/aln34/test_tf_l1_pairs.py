"""Synthetic checks of auditory_alignment_v3.aln34.tf_l1_pairs (no real record is read).

Design: one dataset (dtu), 2 subject folds x 2 content folds, 4 test identities per subject fold (each identity is tested in
both content-fold cells), seeds 3401 / 3407 / 3413, roles L0, L1 and TF (cbramod; warm-up for 3401 only, as registered).
Known per-identity risks let the per-seed effects, the seed mean, the between-seed range and the pairing statuses be checked.
"""
import hashlib
import json
import os
import stat

import numpy as np
import pytest

from auditory_alignment_v3.aln34 import tf_l1_pairs as T

SEEDS = T.SEEDS
CELLS = [(0, 0), (0, 1), (1, 0), (1, 1)]
PIDS = {0: [f"S{j}" for j in range(4)], 1: [f"S{j}" for j in range(4, 8)]}
CODE = {"A_LOCAL": "hL0", "ALN32_LOCAL_SUPPORT": "hL1", "ALN32_TRUE_FULL": "hTF"}
GROUP = {"A_LOCAL": "local", "ALN32_LOCAL_SUPPORT": "local_support", "ALN32_TRUE_FULL": "aligned32"}
EFFECT = {  # unified risk shift relative to L1 (negative = lower risk = positive dR); native adds 0.05
    ("random_full", 1e-05): +0.10, ("random_full", 3e-04): +0.02, ("pretrained_full", 1e-05): -0.20, ("pretrained_full", 3e-04): -0.25}
SEED_SHIFT = {3401: 0.0, 3407: -0.03, 3413: +0.04}  # pretrained-only seed variation


def base_risk(pid, cell, sd):
    j = int(pid[1:])
    return 4.0 + 0.1 * j + 0.01 * cell[1] + 0.001 * (sd - 3400)


def tf_shift(ad, lr, rc, sd):
    e = EFFECT[(ad, lr)] + (SEED_SHIFT[sd] if ad == "pretrained_full" else 0.0)
    return e + (0.01 if rc == T.WARMUP else 0.0)


def jitter(*key):
    """deterministic identity x configuration noise in [-0.05, 0.05) so that paired differences vary across identities (non-degenerate intervals)."""
    h = hashlib.sha256(repr(key).encode()).digest()
    return (int.from_bytes(h[:4], "little") / 2 ** 32 - 0.5) * 0.1


def risk(kind, pid, cell, sd, cfg=None, readout="unified"):
    r = base_risk(pid, cell, sd) + jitter(kind, pid, cell, sd, cfg, readout)
    if kind == "L0":
        r += 0.03
    elif kind == "TF":
        ad, rc, lr = cfg
        r += tf_shift(ad, lr, rc, sd)
    return r + (0.05 if readout == "native" else 0.0)


def _m(ll, n_q=20, n_c=40):
    return {"top1": 0.3, "top5": 0.6, "mrr": 0.4, "rank_pct": 0.2, "logloss_bits": ll, "n_candidates": n_c, "n_queries": n_q}


def make_row(kind, sd, cell, cfg=None):
    sf, cf = cell
    if kind == "L0":
        fam, spec = "A_LOCAL", {"architecture": "lag_local_tokens", "objective": "NCE", "projection_dim": 32, "target": "local", "window": "full"}
    elif kind == "L1":
        fam, spec = "ALN32_LOCAL_SUPPORT", {"architecture": "lag_local_tokens", "objective": "NCE", "projection_dim": 32, "target": "local", "window": "full",
                                            "variant": "local_aligned1000", "input_support": "aligned1000"}
    else:
        ad, rc, lr = cfg
        fam, spec = "ALN32_TRUE_FULL", {"adaptation": ad, "architecture": "cbramod", "objective": "NCE", "projection_dim": 32, "target": "local",
                                        "recipe": rc, "lr_backbone": lr, "readout": "aligned_patch_linear"}
    eid = f"{kind}_{sd}_{sf}{cf}" + ("" if cfg is None else f"_{cfg[0][:4]}_{T.RTAG[cfg[1]]}_{cfg[2]:g}")
    return {"experiment_id": eid, "family_id": fam, "dataset": "dtu", "subject_fold": sf, "content_fold": cf, "seed": sd,
            "seed_scope": "breadth" if sd == 3401 else "panel", "spec": spec, "logical_dependencies": []}


def make_rec(row, kind, cfg=None, sigma_v=None):
    sd, cell = row["seed"], (row["subject_fold"], row["content_fold"])
    pp = {}
    for pid in PIDS[cell[0]]:
        rec = {"group": "nh", "n_segments": 20}
        for rd in ("unified", "native"):
            r = risk(kind, pid, cell, sd, cfg, rd)
            rec[f"{rd}/regular"] = _m(r); rec[f"{rd}/mismatched_eeg"] = _m(r + 1.0); rec[f"{rd}/hard"] = _m(2.5)
        pp[pid] = rec
    rc = {"d": 32, "grid_samples": 3, "fs": 128}
    out = {"experiment_id": row["experiment_id"], "row": json.loads(json.dumps(row)), "status": "complete", "code_group": GROUP[row["family_id"]],
           "code_hash": CODE[row["family_id"]], "target_contract": "dense20ms_v1",
           "bound_row": {"experiment_id": row["experiment_id"], "family_id": row["family_id"], "dataset": "dtu", "subject_fold": cell[0], "content_fold": cell[1],
                         "seed": sd, "spec": {"audio_head": "fixed_features"}},
           "objective_calibration": {"sigma_v": sigma_v or (1.4 + 0.001 * (sd - 3400) + 0.01 * cell[1]), "ridge_v": 3.1e-5},
           "n_train_participants": 40, "n_fit_segments": 4000 + cell[1], "n_es_segments": 3000, "eval": {"per_participant": pp, "readout": {"n_test_candidates": 40}}}
    if kind == "L1":
        rc.update(support="aligned1000", mask="zero before the anchor's segment start"); out["windows_samples"] = [[-51, 77]]
        out["encoder"] = {"n_params": 50800}
    elif kind == "L0":
        out["windows_samples"] = [[0, 77]]
        out["encoder"] = {"n_params": 48000}
    else:
        rc.update(input_support="aligned1000", window_s=[-0.4, 0.6]); out["window_s"] = [-0.4, 0.6]; out["window_native_samples"] = 128
        out["backbone_contract"] = {"arch": "cbramod", "adaptation": cfg[0], "init_state_loaded": None, "n_params": 4883800}
    out["resolved_config"] = rc
    return out


def build(drop=(), fail=(), held=(), mutate=None):
    """-> rows, records; drop: eids without a record (queued); fail: eids with a technical_failed record; held: eids on hold."""
    rows, recs = [], {}
    for sd in SEEDS:
        for cell in CELLS:
            for kind in ("L0", "L1"):
                r = make_row(kind, sd, cell); rows.append(r); recs[r["experiment_id"]] = make_rec(r, kind)
            for rc in ((T.ONESTEP, T.WARMUP) if sd == 3401 else (T.ONESTEP,)):
                for ad in T.INITS:
                    for lr in T.LRS:
                        r = make_row("TF", sd, cell, (ad, rc, lr)); rows.append(r); recs[r["experiment_id"]] = make_rec(r, "TF", (ad, rc, lr))
    for e in drop:
        recs.pop(e)
    for e in fail:
        recs[e] = {"status": "technical_failed"}
    if mutate:
        mutate(recs)
    live = {"held": set(held), "families_on_hold": set(), "deferred": set(), "running": set(), "queued": {r["experiment_id"] for r in rows}, "failed_marker": set()}
    return rows, recs, live


def run(rows, recs, live):
    return T.compute(rows, recs.get, {}, live, CODE, "evalsha")


def expected(sd, ad, lr, rc=T.ONESTEP, readout="unified", pids=None):
    ids = pids or [p for sf in (0, 1) for p in PIDS[sf]]
    d = []
    for pid in ids:
        sf = 0 if pid in PIDS[0] else 1
        cells = [c for c in CELLS if c[0] == sf]
        ref = np.mean([risk("L1", pid, c, sd, None, readout) for c in cells])
        cand = np.mean([risk("TF", pid, c, sd, (ad, rc, lr), readout) for c in cells])
        d.append(ref - cand)
    return float(np.mean(d))


def mem(fams, key, rd, name):
    return fams[key]["readouts"][rd]["members"][name]


def test_role_filter():
    base = make_row("L0", 3401, (0, 0))
    assert T.role_of(base) == ("L0", "dtu", 3401)
    for change in ({"window": "early"}, {"projection_dim": 16}, {"objective": "CS_SINGLE"}):
        assert T.role_of({**base, "spec": {**base["spec"], **change}}) is None
    l1 = make_row("L1", 3407, (1, 0))
    assert T.role_of(l1) == ("L1", "dtu", 3407)
    assert T.role_of({**l1, "spec": {**l1["spec"], "variant": "raw_aligned1000_ridge"}}) is None
    tf = make_row("TF", 3413, (1, 1), ("pretrained_full", T.ONESTEP, 3e-4))
    assert T.role_of(tf) == ("TF", "dtu", "cbramod", "pretrained_full", T.ONESTEP, 3e-4, 3413)
    assert T.role_of({**tf, "seed": 1234}) is None and T.role_of({**tf, "dataset": "private_bdf"}) is None


def test_effects_seed_mean_range_and_native():
    sc, au, fams, notes, dev = run(*build())
    assert au["n_mismatch"] == 0 and dev < 1e-12
    for sd in SEEDS:
        for ad in T.INITS:
            for lr in T.LRS:
                name = f"L1->{ad}/{T.ONESTEP}/lr{lr:g}"
                m = mem(fams, f"TF-LOCAL|onestep|dtu|cbramod|{sd}", "unified", name)
                assert m["n"] == 8 and m["n_own"] == 8
                assert m["est"] == pytest.approx(expected(sd, ad, lr), abs=1e-12)
                assert m["sim_low"] <= m["est"] <= m["sim_high"]
                mn = mem(fams, f"TF-LOCAL|onestep|dtu|cbramod|{sd}", "native", name)
                assert mn["est"] == pytest.approx(expected(sd, ad, lr, readout="native"), abs=1e-12)
        for lr in T.LRS:  # TF-INIT: random -> pretrained
            m = mem(fams, f"TF-INIT|onestep|dtu|cbramod|{sd}", "unified", f"{T.ONESTEP}/lr{lr:g}")
            assert m["est"] == pytest.approx(expected(sd, "pretrained_full", lr) - expected(sd, "random_full", lr), abs=1e-12)
    sm = fams["TF-LOCAL|onestep|dtu|cbramod|seedmean"]
    name = f"L1->pretrained_full/{T.ONESTEP}/lr0.0003"
    per = [expected(sd, "pretrained_full", 3e-4) for sd in SEEDS]
    assert sm["readouts"]["unified"]["members"][name]["est"] == pytest.approx(np.mean(per), abs=1e-12)
    b = sm["between_seed"]["unified"][name]
    assert b["n"] == 8 and b["min"] == pytest.approx(min(per)) and b["max"] == pytest.approx(max(per))
    assert [b["per_seed"][str(sd)] for sd in SEEDS] == pytest.approx(per)
    assert sm["coverage"][name] == {"3": 8}
    # TF-INIT gets no seed mean; warm-up exists only for the breadth seed
    assert not any(k.startswith("TF-INIT") and k.endswith("seedmean") for k in fams)
    assert "TF-LOCAL|warmup|dtu|cbramod|3401" in fams and "TF-INIT|warmup|dtu|cbramod|3401" in fams
    assert not any(k.startswith(("TF-LOCAL|warmup", "TF-INIT|warmup")) and not k.endswith("3401") for k in fams)
    w = mem(fams, "TF-LOCAL|warmup|dtu|cbramod|3401", "unified", f"L1->pretrained_full/{T.WARMUP}/lr1e-05")
    assert w["est"] == pytest.approx(expected(3401, "pretrained_full", 1e-5, rc=T.WARMUP), abs=1e-12)


def test_warmup_panel_pairs_missing_not_registered():
    sc, au, fams, notes, dev = run(*build())
    m = au["members"][f"TF-LOCAL|warmup|dtu|cbramod|3407|L1->pretrained_full/{T.WARMUP}/lr0.0003"]
    assert not m["registered"] and m["cells"] == {"missing": 4}
    reasons = {p["reason"] for p in au["pairs"] if p["member"].startswith("TF-LOCAL|warmup|dtu|cbramod|3407|")}
    assert reasons == {"candidate not registered"}
    # the other backbone was never registered at all
    assert not au["members"][f"TF-LOCAL|onestep|dtu|reve|3401|L1->pretrained_full/{T.ONESTEP}/lr0.0003"]["registered"]
    assert "TF-LOCAL|onestep|dtu|reve|3401" not in fams


def test_pending_cell_excludes_identities_without_partial_averaging():
    drop = make_row("TF", 3413, (1, 1), ("pretrained_full", T.ONESTEP, 3e-4))["experiment_id"]
    sc, au, fams, notes, dev = run(*build(drop=[drop]))
    name = f"L1->pretrained_full/{T.ONESTEP}/lr0.0003"
    m = au["members"][f"TF-LOCAL|onestep|dtu|cbramod|3413|{name}"]
    assert m["cells"] == {"complete": 3, "pending": 1} and m["identities"] == {"complete": 4, "pending": 4, "missing": 0}
    p = [x for x in au["pairs"] if x["member"] == f"TF-LOCAL|onestep|dtu|cbramod|3413|{name}" and x["cell"] == [1, 1]][0]
    assert p["status"] == "pending" and p["reason"] == "candidate queued"
    f = fams["TF-LOCAL|onestep|dtu|cbramod|3413"]["readouts"]["unified"]["members"]
    assert f[name]["n_own"] == 4 and f[name]["n"] == 4  # family common set shrinks to the complete identities
    other = f"L1->random_full/{T.ONESTEP}/lr1e-05"
    assert f[other]["n_own"] == 8 and f[other]["n"] == 4
    assert f[name]["est"] == pytest.approx(expected(3413, "pretrained_full", 3e-4, pids=PIDS[0]), abs=1e-12)
    # identity_values never averages an identity over the subset of its cells that happens to be complete
    cfg = ("TF", "dtu", "cbramod", "pretrained_full", T.ONESTEP, 3e-4, 3413)
    v = T.identity_values(sc, cfg, {(0, 0), (0, 1), (1, 0)}, PIDS[0] + PIDS[1])
    assert set(v) == set(PIDS[0])
    # seed mean: only identities complete in all seeds; the counts by number of complete seeds are reported
    sm = fams["TF-LOCAL|onestep|dtu|cbramod|seedmean"]
    assert sm["readouts"]["unified"]["members"][name]["n"] == 4
    assert sm["coverage"][name] == {"2": 4, "3": 4}
    assert sm["between_seed"]["unified"][name]["n"] == 4


def test_mismatch_failed_and_held_are_missing():
    e_split = make_row("TF", 3407, (0, 0), ("random_full", T.ONESTEP, 1e-5))["experiment_id"]
    e_tgt = make_row("TF", 3407, (0, 1), ("random_full", T.ONESTEP, 1e-5))["experiment_id"]
    e_fail = make_row("TF", 3413, (0, 0), ("random_full", T.ONESTEP, 3e-4))["experiment_id"]
    e_held = make_row("TF", 3413, (1, 0), ("pretrained_full", T.ONESTEP, 1e-5))["experiment_id"]

    def mutate(recs):
        recs[e_split]["eval"]["per_participant"]["S0"]["unified/regular"]["n_queries"] = 19
        recs[e_tgt]["objective_calibration"]["sigma_v"] *= 1.01

    rows, recs, live = build(fail=[e_fail], mutate=mutate)
    recs.pop(e_held)
    live["held"].add(e_held)
    sc, au, fams, notes, dev = run(rows, recs, live)
    by = {(p["member"], tuple(p["cell"])): p for p in au["pairs"]}
    k = f"TF-LOCAL|onestep|dtu|cbramod|3407|L1->random_full/{T.ONESTEP}/lr1e-05"
    assert by[(k, (0, 0))]["status"] == "missing" and "split" in by[(k, (0, 0))]["reason"]
    assert by[(k, (0, 1))]["status"] == "missing" and "target" in by[(k, (0, 1))]["reason"]
    assert au["members"][k]["identities"]["missing"] == 4
    kf = f"TF-INIT|onestep|dtu|cbramod|3413|{T.ONESTEP}/lr0.0003"
    assert by[(kf, (0, 0))]["status"] == "missing" and "technical_failed" in by[(kf, (0, 0))]["reason"]
    kh = f"TF-LOCAL|onestep|dtu|cbramod|3413|L1->pretrained_full/{T.ONESTEP}/lr1e-05"
    assert by[(kh, (1, 0))]["status"] == "missing" and "held" in by[(kh, (1, 0))]["reason"]
    assert au["n_mismatch"] >= 2
    # the mismatched member uses only the identities of the intact subject fold
    m = fams["TF-LOCAL|onestep|dtu|cbramod|3407"]["readouts"]["unified"]["members"][f"L1->random_full/{T.ONESTEP}/lr1e-05"]
    assert m["n_own"] == 4


def test_l0_pairs_are_declared_access_extensions():
    sc, au, fams, notes, dev = run(*build())
    l0 = [p for p in au["pairs"] if p["member"].startswith("L0-L1 (audit only)")]
    assert l0 and all(p["status"] == "complete" and p["checks"]["access"] == "declared difference" for p in l0)
    same = [p for p in au["pairs"] if p["member"].startswith("TF-LOCAL|onestep") and p["status"] == "complete"]
    assert same and all(p["checks"]["access"] is True for p in same)
    assert not any("L0" in k.split("|")[0] for k in fams)  # L0 enters the audit only
    u = sc["units"][make_row("L1", 3401, (0, 0))["experiment_id"]]["fp"]
    t = sc["units"][make_row("TF", 3401, (0, 0), ("random_full", T.ONESTEP, 1e-5))["experiment_id"]]["fp"]
    assert u["access"] == t["access"] == {"support": "aligned1000", "window_samples": [-51, 77], "mask": "zero_before_segment_start"}


def test_code_hash_not_reproduced_blocks_pair():
    e = make_row("L1", 3407, (1, 1))["experiment_id"]

    def mutate(recs):
        recs[e]["code_hash"] = "old"

    sc, au, fams, notes, dev = run(*build(mutate=mutate))
    p = [x for x in au["pairs"] if x["member"].startswith("TF-LOCAL|onestep|dtu|cbramod|3407|") and x["cell"] == [1, 1]]
    assert p and all(x["status"] == "missing" and "evaluation" in x["reason"] for x in p)


def test_deterministic_and_reproduction_check(tmp_path):
    a = run(*build()); b = run(*build())
    dump = lambda r: json.dumps(T.BI.jl(r[2]), sort_keys=True)
    assert dump(a) == dump(b)
    fams = a[2]
    frozen = {"families": {}, "secondary": {}}
    for key, f in fams.items():
        if f["seed"] != 3401:
            continue
        lab = f"{f['contrast']}|{f['dataset']}|{f['backbone']}"
        for name, m in f["readouts"]["unified"]["members"].items():
            frozen["families"].setdefault(lab, {"members": {}})["members"][name] = {"est": m["est"], "n": m["n"]}
        for name, m in f["readouts"]["native"]["members"].items():
            frozen["secondary"].setdefault(lab, {}).setdefault("native/regular/logloss_bits", {"members": {}})["members"][name] = {"est": m["est"], "n": m["n"]}
    p = tmp_path / "frozen.json"; p.write_text(json.dumps(frozen))
    rc = T.reproduction_check(fams, str(p))
    assert rc["status"] == "pass" and rc["n_compared"] == 24
    frozen["families"]["TF-INIT|dtu|cbramod"]["members"][f"{T.ONESTEP}/lr1e-05"]["est"] += 1e-3
    p.write_text(json.dumps(frozen))
    assert T.reproduction_check(fams, str(p))["status"] == "FAIL"


def test_complete_panel_flags_and_report(tmp_path):
    sc, au, fams, notes, dev = run(*build())
    assert not fams["TF-LOCAL|onestep|dtu|cbramod|3407"]["interim"] and fams["TF-LOCAL|onestep|dtu|cbramod|3407"]["coverage_complete"]
    assert not fams["TF-LOCAL|onestep|dtu|cbramod|seedmean"]["interim"]
    out = {"meta": {"generated": "test", "code_sha256": {"x": "0" * 64}, "code_hash_now": CODE, "reused_records": {"TF": 1}, "runtime_s": 0.0,
                    "json_path": str(tmp_path / "x.json")},
           "coverage": T.coverage(sc), "pair_audit": T.strip_private(au), "families": fams, "max_target_rel_dev": dev, "role_summary": T.role_summary(sc),
           "units": sc["units"], "reproduction_check": {"status": "not compared", "n_compared": 0}, "notes": notes}
    txt = open(T.report(out, str(tmp_path / "R.md"))).read()
    assert "Panel complete" in txt and "— INTERIM\n" not in txt.splitlines()[0] + "\n" and "run it now that the panel is complete" in txt
    assert "Interim coverage" not in txt


def test_report_and_json_modes(tmp_path):
    sc, au, fams, notes, dev = run(*build(drop=[make_row("TF", 3407, (1, 1), ("random_full", T.ONESTEP, 1e-5))["experiment_id"]]))
    out = {"meta": {"generated": "test", "code_sha256": {"x": "0" * 64}, "code_hash_now": CODE, "reused_records": {"TF": 1}, "runtime_s": 0.0,
                    "json_path": str(tmp_path / "x.json")},
           "coverage": T.coverage(sc), "pair_audit": T.strip_private(au), "families": fams, "max_target_rel_dev": dev, "role_summary": T.role_summary(sc),
           "units": sc["units"], "reproduction_check": {"status": "not compared", "n_compared": 0}, "notes": notes}
    blob = json.dumps(T.BI.jl(out))
    assert "complete_identities" not in blob and '"S0"' not in blob  # identity counts only, no identity lists
    rs = out["role_summary"]
    assert rs["L1|dtu"]["complete"] == 12 and rs["L1|dtu"]["reproduced"] == {"True": 12} and rs["TF|dtu"]["complete"] == 63
    assert rs["L1|dtu"]["initialization"] == {"local encoder": 12} and rs["TF|dtu"]["initialization_consistent"] == 63
    assert sum(rs["TF|dtu"]["initialization"].values()) == 63 and set(rs["TF|dtu"]["initialization"]) == {"cbramod/random_full", "cbramod/pretrained_full"}
    p = T.report(out, str(tmp_path / "doc" / "R.md"))
    txt = open(p).read()
    assert "INTERIM" in txt and "not independent replications" in txt and "## 6." in txt and "Derived fields per role" in txt
    for line in txt.splitlines():  # every table row has the header's column count (no stray '|' inside cells)
        if line.startswith("| "):
            assert line.count("|") == line.count(" | ") + 2
    assert stat.S_IMODE(os.stat(p).st_mode) == 0o600
    assert out["coverage"]["tf_panel"]["complete"] == out["coverage"]["tf_panel"]["registered"] - 1



# ------------------------------------------------------------------------------------------------ Correction 1 of the analysis note
def frozen_like(fams=None):
    """an ADDENDUM_07-style frozen file built independently of tf_l1_pairs: identity values straight from the synthetic risk function,
    the frozen labels and member names, bc_interim.run_family as aln32_interim.aggregate calls it (native readout '<label>|sec', pointwise)."""
    BI = T.BI
    ids = [p for sf in (0, 1) for p in PIDS[sf]]

    def ival(kind, cfg, readout):
        out = {}
        for pid in ids:
            sf = 0 if pid in PIDS[0] else 1
            cells = [c for c in CELLS if c[0] == sf]
            out[pid] = float(np.mean([risk(kind, pid, c, 3401, cfg, readout) for c in cells]))
        return out

    def V(kind, cfg=None):
        u, n = ival(kind, cfg, "unified"), ival(kind, cfg, "native")
        return {pid: {"unified/regular/logloss_bits": u[pid], "native/regular/logloss_bits": n[pid]} for pid in ids}

    vals = {("L0",): V("L0"), ("L1",): V("L1")}
    for ad in T.INITS:
        for rc in T.RECIPES:
            for lr in T.LRS:
                vals[("T", ad, rc, lr)] = V("TF", (ad, rc, lr))
    fam = {"TF-INIT|dtu|cbramod": [(f"{rc}/lr{lr:g}", ("T", "random_full", rc, lr), ("T", "pretrained_full", rc, lr), "init") for rc in T.RECIPES for lr in T.LRS],
           "TF-LOCAL|dtu|cbramod": [(f"{ref}->{ad}/{rc}/lr{lr:g}", (ref,), ("T", ad, rc, lr), "local") for ref in ("L0", "L1") for ad in T.INITS
                                    for rc in T.RECIPES for lr in T.LRS]}
    out = {"families": {}, "secondary": {}}
    for label, members in fam.items():
        out["families"][label] = BI.run_family(label, members, vals, "unified/regular/logloss_bits", [], True)
        out["secondary"][label] = {"native/regular/logloss_bits": BI.run_family(f"{label}|sec", members, vals, "native/regular/logloss_bits", [], False)}
    return json.loads(json.dumps(BI.jl(out)))


def test_frozen_label_interval_reproduction(tmp_path):
    sc, au, fams, notes, dev = run(*build())
    fz = frozen_like()
    p = tmp_path / "frozen.json"; p.write_text(json.dumps(fz))
    ir = T.frozen_interval_check(sc, str(p))
    assert ir["status"] == "pass" and ir["n_families"] == 4 and ir["n_members_compared"] == 2 * (4 + 16)
    assert max(ir["max_abs_diff"].values()) < 1e-12 and set(ir["max_abs_diff"]) >= {"est", "se", "ci_low", "ci_high", "sim_low", "sim_high", "crit"}
    # the declared families (other labels, other members) reproduce the point estimates but not the intervals: label-seeded replicates
    rp = T.reproduction_check(fams, str(p))
    assert rp["status"] == "pass" and rp["max_abs_diff"] < 1e-12
    du = rp["declared_interval_diff"]["unified"]
    assert du["n_members"] == 12 and du["n_pointwise_differ"] > 0 and du["pointwise_max_abs_diff"] > 0
    assert "group_seed" in rp["declared_interval_diff_cause"]
    # any change to a frozen interval, critical value or member list fails the check
    for mut in (lambda z: z["families"]["TF-INIT|dtu|cbramod"]["members"][f"{T.ONESTEP}/lr1e-05"].__setitem__("sim_low", z["families"]["TF-INIT|dtu|cbramod"]["members"][f"{T.ONESTEP}/lr1e-05"]["sim_low"] + 1e-6),
                lambda z: z["families"]["TF-LOCAL|dtu|cbramod"].__setitem__("crit", z["families"]["TF-LOCAL|dtu|cbramod"]["crit"] * 1.001),
                lambda z: z["secondary"]["TF-INIT|dtu|cbramod"]["native/regular/logloss_bits"]["members"][f"{T.WARMUP}/lr0.0003"].__setitem__("ci_high", 9.0),
                lambda z: z["families"]["TF-LOCAL|dtu|cbramod"]["members"].pop(f"L0->random_full/{T.ONESTEP}/lr1e-05")):
        z = frozen_like(); mut(z); p.write_text(json.dumps(z))
        assert T.frozen_interval_check(sc, str(p))["status"] == "FAIL"


def test_label_seeding_explains_pointwise_differences():
    """the mechanism the report cites: same members + same label -> identical pointwise intervals whatever the family size;
    another label -> same estimates, other pointwise intervals; more members -> a critical value at least as large."""
    BI = T.BI
    rng = np.random.default_rng(0)
    ids = [f"S{j}" for j in range(12)]
    m = "unified/regular/logloss_bits"
    vals = {(k,): {i: {m: float(rng.normal(k, 1.0))} for i in ids} for k in range(5)}
    four = [(f"m{k}", (0,), (k,), "t") for k in range(1, 5)]
    a = BI.run_family("X", four, vals, m, [], True)
    b = BI.run_family("X", four[:2], vals, m, [], True)
    c = BI.run_family("Y", four[:2], vals, m, [], True)
    for name in ("m1", "m2"):
        assert a["members"][name]["ci_low"] == b["members"][name]["ci_low"] and a["members"][name]["ci_high"] == b["members"][name]["ci_high"]
        assert b["members"][name]["est"] == c["members"][name]["est"]
        assert b["members"][name]["ci_low"] != c["members"][name]["ci_low"]
    assert a["crit"] >= b["crit"]


def test_initialization_check_blocks_pair():
    e_ad = make_row("TF", 3407, (0, 0), ("pretrained_full", T.ONESTEP, 1e-5))["experiment_id"]
    e_donor = make_row("TF", 3413, (1, 1), ("random_full", T.ONESTEP, 3e-4))["experiment_id"]
    e_l1 = make_row("L1", 3401, (1, 0))["experiment_id"]

    def mutate(recs):
        recs[e_ad]["backbone_contract"]["adaptation"] = "random_full"       # record contradicts the configured initialization
        recs[e_donor]["backbone_contract"]["init_state_loaded"] = {"n_tensors": 3}  # donor weights loaded
        recs[e_l1].pop("encoder")                                         # local side without an encoder record

    sc, au, fams, notes, dev = run(*build(mutate=mutate))
    by = {(p["member"], tuple(p["cell"])): p for p in au["pairs"]}
    k = f"TF-INIT|onestep|dtu|cbramod|3407|{T.ONESTEP}/lr1e-05"
    assert by[(k, (0, 0))]["status"] == "missing" and "initialization" in by[(k, (0, 0))]["reason"]
    k = f"TF-LOCAL|onestep|dtu|cbramod|3413|L1->random_full/{T.ONESTEP}/lr0.0003"
    assert by[(k, (1, 1))]["status"] == "missing" and "initialization" in by[(k, (1, 1))]["reason"]
    k = f"TF-LOCAL|onestep|dtu|cbramod|3401|L1->pretrained_full/{T.ONESTEP}/lr1e-05"
    assert by[(k, (1, 0))]["status"] == "missing" and "initialization" in by[(k, (1, 0))]["reason"]
    ok = [p for p in au["pairs"] if p["status"] == "complete"]
    assert ok and all(p["checks"]["initialization"] is True for p in ok)
    assert not sc["units"][e_ad]["initialization_ok"] and sc["units"][make_row("L1", 3401, (0, 0))["experiment_id"]]["initialization_ok"]


def test_report_tf_init_interim_and_not_judged_across_seeds(tmp_path):
    sc, au, fams, notes, dev = run(*build(drop=[make_row("TF", 3407, (1, 1), ("random_full", T.ONESTEP, 1e-5))["experiment_id"]]))
    fz = frozen_like(); p = tmp_path / "frozen.json"; p.write_text(json.dumps(fz))
    out = {"meta": {"generated": "test", "code_sha256": {"x": "0" * 64}, "code_hash_now": CODE, "reused_records": {"TF": 1}, "runtime_s": 0.0,
                    "json_path": str(tmp_path / "x.json")},
           "coverage": T.coverage(sc), "pair_audit": T.strip_private(au), "families": fams, "max_target_rel_dev": dev, "role_summary": T.role_summary(sc),
           "units": sc["units"], "reproduction_check": T.reproduction_check(fams, str(p)), "interval_reproduction_check": T.frozen_interval_check(sc, str(p)),
           "notes": notes}
    txt = open(T.report(out, str(tmp_path / "R.md"))).read()
    sec = lambda a, b: txt.split(a, 1)[1].split(b, 1)[0]
    s2 = sec("## 2. ", "## 3. ")
    assert "| dtu · cbramod | TF-LOCAL ·" in s2 and "| dtu · cbramod | TF-INIT ·" not in s2 and "TF-INIT is not judged across seeds" in s2
    s14 = sec("### 1.4 ", "Warm-up recipe (seed 3401 only):")
    rows = [l for l in s14.splitlines() if l.startswith("| dtu")]
    assert rows and all(" · interim |" in l for l in rows)
    s15 = sec("TF-INIT one-step (interim):", "TF-LOCAL warm-up (seed 3401 only):")
    assert all(" · interim |" in l for l in s15.splitlines() if l.startswith("| dtu"))
    app = [l for l in sec("## Appendix A.", "## Appendix B.").splitlines() if l.startswith("| TF-INIT · onestep")]
    assert app and all("interim (ADDENDUM_11 role)" in l for l in app)
    assert "seeded by the family label" in sec("### 1.4 ", "### 1.5 ") and "reproduce the frozen intervals exactly" in sec("### 1.3 ", "### 1.4 ")
    assert "On the same identities the seeds still differ" in s2
    s16 = sec("### 1.6 ", "## 2. ")
    assert "**pass**" in s16 and "group_seed" in s16 and "initialization" in s16
    for line in txt.splitlines():
        if line.startswith("| "):
            assert line.count("|") == line.count(" | ") + 2
