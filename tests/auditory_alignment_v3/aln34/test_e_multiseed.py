"""Synthetic checks of auditory_alignment_v3.aln34.e_multiseed (no unit record, no EEG and no private value is read).

Design: 12 synthetic children in 2 subject folds (content fold 0), groups alternating HA / NH; seeds 3401 / 3407 / 3413; the 17 panel
configurations at every seed plus, at seed 3401 only, non-panel E_GENERIC (pretrained_frozen, pretrained_partial) and E_PUBLIC_TRANSFER
(task_full) configurations; A_LOCAL FAU donor rows for the transfer records. Known per-child effects let the panel restriction of the
frozen families, the per-seed paired effects and their signs, the identity mean over seeds (never across seeds), the between-seed
range and SD, the levels, the frozen-label reproduction plumbing, the coverage / missing-pair handling, the QC checks, the Monte-Carlo
table, the privacy of the aggregate outputs, the document renderer and splice, and the scope helpers be checked."""
import copy
import hashlib
import json
import os

import numpy as np
import pytest

from auditory_alignment_v3 import bc_interim as BI
from auditory_alignment_v3.aln34 import e_multiseed as EM
from auditory_alignment_v3.sci_r1 import stats as S

SEEDS = EM.SEEDS
KIDS = {0: [f"child{100 + j}" for j in range(6)], 1: [f"child{100 + j}" for j in range(6, 12)]}
ALL_KIDS = KIDS[0] + KIDS[1]
GROUP = {k: ("HA" if j % 2 == 0 else "NH") for j, k in enumerate(ALL_KIDS)}
PEFT = {3401: 0.01, 3407: -0.01, 3413: 0.01}  # pretrained_peft - random_full, AUC (seed-dependent sign)
EXTRA_3401 = [("E_GENERIC", o, a, ad) for o in BI.OBJ for a in BI.ARCH for ad in ("pretrained_frozen", "pretrained_partial")] + \
             [("E_PUBLIC_TRANSFER", o, "lag_local_tokens", "task_full") for o in BI.OBJ]


def noise(*key, sd=1.0):
    h = hashlib.sha256(repr(key).encode()).digest()
    u1, u2 = (int.from_bytes(h[:4], "little") + 1) / 2 ** 32, (int.from_bytes(h[4:8], "little") + 1) / 2 ** 32
    return sd * float(np.sqrt(-2 * np.log(u1)) * np.cos(2 * np.pi * u2))


def effects(c, s):
    """(AUC shift, NLL shift, history-increment shift) of a configuration relative to E_LOCAL lag_local_tokens full."""
    f = c[0]
    if f == "E_LOCAL":
        return 0.0, 0.0, 0.0
    if f == "E_GX":
        return 0.03, -0.001, 0.0
    if f == "E_PUBLIC_TRANSFER":
        return (0.005, -0.0005, 0.0) if c[3] == "task_partial" else (0.0, 0.0, 0.0)
    ad = c[3]
    if ad == "random_full":
        return -0.01, 0.002, 0.0
    if ad == "pretrained_full":
        return 0.01, 0.001, 0.001
    if ad == "pretrained_peft":
        return -0.01 + PEFT[s], 0.002, 0.0
    return -0.005, 0.002, 0.0


def values(c, s, kid):
    j = ALL_KIDS.index(kid)
    da, dn, dh = effects(c, s)
    auc = 0.52 + 0.002 * j + da + noise("auc", c, s, kid, sd=0.002)
    nll = 0.72 + 0.0005 * j + dn + noise("nll", c, s, kid, sd=0.0002)
    hg = -0.002 + dh + noise("hg", c, s, kid, sd=0.0002)
    return auc, nll, hg, hg - 0.0005


def spec_of(c):
    f, o, a, w = c
    if f == "E_LOCAL":
        return {"objective": o, "architecture": a, "window": w, "projection_dim": 32, "target": "current_class"}
    if f == "E_GX":
        return {"objective": o, "architecture": "GX", "window": w, "target": "current_class"}
    if f == "E_GENERIC":
        return {"objective": o, "architecture": a, "adaptation": w, "projection_dim": 32, "target": "current_class"}
    return {"objective": o, "source_architecture": a, "adaptation": w, "projection_dim": 32, "target": "current_class"}


STRATUM = {"E_LOCAL": "local_only", "E_GX": "local_only", "E_GENERIC": "padded_private_epoch_no_extra_EEG", "E_PUBLIC_TRANSFER": "private_task_declared_input"}
# synthetic recipe descriptors (v3): (backbone lr, head lr) per objective, architecture and adaptation; epochs and parameter counts per architecture
LRS = {("NCE", "cbramod"): {"random_full": (3e-4, 3e-4), "pretrained_peft": (1e-3, 1e-3), "pretrained_full": (1e-4, 1e-4)},
       ("NCE", "reve"): {"random_full": (3e-4, 3e-4), "pretrained_peft": (1e-3, 1e-4), "pretrained_full": (3e-5, 1e-4)},
       ("CS_SINGLE", "cbramod"): {"random_full": (1e-4, 1e-4), "pretrained_peft": (3e-4, 1e-3), "pretrained_full": (1e-5, 1e-3)},
       ("CS_SINGLE", "reve"): {"random_full": (1e-3, 1e-3), "pretrained_peft": (3e-4, 1e-4), "pretrained_full": (1e-5, 1e-3)}}
EPOCHS = {"cbramod": 100, "reve": 50}
NPARAM = {"cbramod": (4883800, 4960600, 76800), "reve": (69189632, 69730304, 540672)}  # full, PEFT total, PEFT trainable


def recipe_fields(c, recipe_dir=None, open_groups=False):
    """synthetic resolved_config / backbone_contract / curve of a record of configuration c (E_GENERIC: FM recipe; others: AdamW 1e-3)."""
    f, o, a, ad = c
    curve = [{"epoch": 1, "step": 10, **({"open_groups": 3} if open_groups else {})}]
    if f != "E_GENERIC":
        return {"resolved_config": {"d": 32, "epochs": 200, "optimizer": "AdamW", "lr": 1e-3}, "curve": curve} if f != "E_GX" else {"curve": curve}
    lb, lh = LRS[(o, a)].get(ad, (1e-4, 1e-3))
    rf = f"{a}__{ad}__private_bdf__{o}.json"
    full, ptot, ptr = NPARAM[a]
    bc = ({"adaptation": ad, "trainable_layers": ["lora_r8:X.weight", "lora_r8:X.weight", "…all attention projections"], "n_params": ptot, "n_trainable_backbone": ptr}
          if ad == "pretrained_peft" else {"adaptation": ad, "trainable_layers": "all", "n_params": full, "n_trainable_backbone": full})
    return {"resolved_config": {"d": 32, "epochs": EPOCHS[a], "lr_backbone": lb, "lr_head": lh,
                                "recipe_file": os.path.join(recipe_dir, rf) if recipe_dir else f"private/none/fm_recipe/{rf}"},
            "lr_backbone": lb, "lr_head": lh, "backbone_contract": bc, "curve": curve}


def make_design(drop=None, count_change=None, donor_seed_shift=None, spec_change=None, nll_shift=None, recipe_dir=None, open_groups_unit=None):
    """rows, loader, registry triples. drop = (config, seed, child): the child is absent from that record; count_change = (config, seed,
    child): its trial count changes; donor_seed_shift = seed whose transfer records name a donor of another seed; spec_change = (config,
    seed): the panel row's spec differs from its seed-3401 counterpart; nll_shift = {(config, seed, subject fold): added NLL}; recipe_dir:
    E_GENERIC records name recipe files there (absolute paths); open_groups_unit = (config, seed, subject fold) whose curve has open_groups."""
    rows, recs, triples = [], {}, {}
    for s in SEEDS:
        for o in BI.OBJ:
            rows.append({"experiment_id": f"AL_{s}_{o}", "family_id": "A_LOCAL", "dataset": "fau", "subject_fold": 0, "content_fold": 0, "seed": s,
                         "spec": {"objective": o, "architecture": "lag_local_tokens", "window": "full"}})
    for s in SEEDS:
        cfgs = list(EM.PANEL_CONFIGS) + (EXTRA_3401 if s == 3401 else [])
        for c in cfgs:
            for sf in (0, 1):
                eid = f"E_{s}_{'_'.join(c)}_{sf}"
                spec = spec_of(c)
                if spec_change == (c, s):
                    spec = {**spec, "projection_dim": 16}
                row = {"experiment_id": eid, "family_id": c[0], "dataset": "private_bdf", "subject_fold": sf, "content_fold": 0, "seed": s,
                       "seed_scope": "breadth" if s == 3401 else "panel", "spec": spec}
                if s != 3401 and c[0] in ("E_PUBLIC_TRANSFER",):
                    row["reference_3401_id"] = f"E_3401_{'_'.join(c)}_{sf}"
                rows.append(row)
                if c in EM.PANEL_SET:
                    triples.setdefault(f"{'_'.join(c)}_{sf}", {})[s] = eid
                pp, nc = {}, {}
                for kid in KIDS[sf]:
                    if drop == (c, s, kid):
                        continue
                    auc, nll, hg, tw = values(c, s, kid)
                    nll += (nll_shift or {}).get((c, s, sf), 0.0)
                    n = 101 if count_change == (c, s, kid) else 100
                    pp[kid] = {"group": GROUP[kid], "n": n, "hist_gain_bits": hg, "hist_gain_twin_bits": tw}
                    nc[kid] = {"positive_affine": {"nll_bits": nll, "auc_score": auc, "n": n}, "temperature": {"nll_bits": nll + 0.01, "auc_score": auc, "n": n}}
                ds = s if donor_seed_shift != s else (3401 if s != 3401 else 3407)
                recs[eid] = {"status": "complete", "code_hash": "h_transfer" if c[0] == "E_PUBLIC_TRANSFER" else "h_private",
                             "code_group": "transfer" if c[0] == "E_PUBLIC_TRANSFER" else "private", "target_contract": "current_class",
                             "information_stratum": STRATUM[c[0]], "selection_rule": "rule", "row": {"seed": s, "spec": spec}, "bound_row": {"seed": s},
                             "donor": f"private/none/AL_{ds}_{c[1]}_best.pt" if c[0] == "E_PUBLIC_TRANSFER" else None,
                             "eval": {"per_participant": pp, "native_calibration": {"per_participant": nc, "calibration_set": "cal", "n_calibration_trials": 500,
                                                                                     "methods": {"positive_affine": {"slope": 1.0 + 0.1 * sf + 0.001 * (s - 3400), "intercept": -1.0, "mean": 0.0, "scale": 1.0}}},
                                      "readout": {"head_fit": "hf"}, "native_head": {"kind": "k"}},
                             **recipe_fields(c, recipe_dir, open_groups=open_groups_unit == (c, s, sf))}
    return rows, recs.get, triples


@pytest.fixture(scope="module")
def clean():
    rows, load, triples = make_design()
    out, per_identity, census = EM.analyse(rows, load, None, mc_k=0, triples=triples)
    return rows, load, triples, out, per_identity, census


def fam(fams, family, scope):
    return next(f for f in fams if f["family"] == family and f["scope"] == scope)


# ------------------------------------------------------------------------------------------------ design
def test_panel_definition_and_family_restriction():
    assert len(EM.PANEL_CONFIGS) == 17 and len(EM.PANEL_SET) == 17
    fams = EM.panel_families()
    names = {(f["family"], f["scope"]): [m[0] for m in f["members"]] for f in fams}
    assert {k[0] for k in names} == {"PE-GENERIC", "PE-LOCAL", "PE-TRANSFER"}  # PE-COMPLEMENT / PE-DISTILL have no panel rows
    for o in BI.OBJ:
        for a in BI.ARCH:
            assert names[("PE-GENERIC", f"{o}|{a}")] == ["pretrained_peft", "pretrained_full"]
        assert names[("PE-LOCAL", o)] == [f"generic/{a}/{ad}" for a in BI.ARCH for ad in EM.PANEL_ADAPT] + ["transfer/lag_local_tokens/task_partial"]
        assert names[("PE-TRANSFER", o)] == ["transfer/lag_local_tokens/task_partial"]
        loc, tr = fam(fams, "PE-LOCAL", o), fam(fams, "PE-TRANSFER", o)
        assert loc["members"][-1][1:3] == tr["members"][0][1:3]  # same paired difference in two frozen families
        assert loc["n_members_frozen"] == 16 and tr["n_members_frozen"] == 6
    g = fam(fams, "PE-GENERIC", "NCE|cbramod")
    tags = {m[0]: m[3] for m in g["members"]}
    assert tags["pretrained_full"] == EM.CORRECTED_TAG and g["frozen_tags"]["pretrained_full"] == EM.FROZEN_FULL_TAG
    assert set(g["non_panel_members"]) == {"pretrained_frozen", "pretrained_partial"}
    assert EM.plabel(g, "AUC") == "PE-GENERIC|NCE|cbramod|AUC" and EM.slabel(g) == "PE-GENERIC|NCE|cbramod|sec"


def test_row_in_panel_and_config_of_keep_global_seed():
    rows, _, _ = make_design()
    before = BI.SEED
    panel = [r for r in rows if EM.row_in_panel(r)]
    assert BI.SEED == before
    assert len(panel) == 17 * 2 * 3  # 17 configurations x 2 folds x 3 seeds (the seed-3401 extras and the A_LOCAL donors are outside)
    assert all(EM.config_of(r) in EM.PANEL_SET for r in panel)


# ------------------------------------------------------------------------------------------------ effects, seed mean, range
def test_per_seed_effects_signs_and_identity_mean(clean):
    rows, load, triples, out, per_identity, census = clean
    fams = EM.panel_families()
    g = fam(fams, "PE-GENERIC", "NCE|cbramod")
    for s in SEEDS:
        res = out["per_seed"][str(s)]
        full_auc = res["families"]["PE-GENERIC|NCE|cbramod|AUC"]["members"]["pretrained_full"]
        assert abs(full_auc["est"] - 0.02) < 0.004 and full_auc["class"] == "I>0" and full_auc["n"] == 12
        peft_auc = res["families"]["PE-GENERIC|NCE|cbramod|AUC"]["members"]["pretrained_peft"]
        assert abs(peft_auc["est"] - PEFT[s]) < 0.004
        full_nll = res["families"]["PE-GENERIC|NCE|cbramod|NLL"]["members"]["pretrained_full"]
        assert abs(full_nll["est"] - 0.001) < 0.0003 and full_nll["class"] == "I>0"  # ΔNLL = reference - candidate: lower NLL is positive
        assert full_nll["tag"] == EM.CORRECTED_TAG and full_nll["frozen_tag"] == EM.FROZEN_FULL_TAG
    for m in EM.METRICS:  # balanced complete panel: identity mean = mean of the per-seed estimates
        for name, *_ in g["members"]:
            ests = [EM.block(out["per_seed"][str(s)], g, m)["members"][name]["est"] for s in SEEDS]
            sm = EM.block(out["seed_mean"], g, m)["members"][name]
            assert abs(sm["est"] - np.mean(ests)) < 1e-12 and sm["n"] == 12
            assert sm["identities_by_n_seeds"] == {"3": 12}
            assert sm["ref"] == "E_GENERIC|NCE|cbramod|random_full" and sm["cand"] == f"E_GENERIC|NCE|cbramod|{name}"
    b = out["between_seed"]["PE-GENERIC|NCE|cbramod|AUC|pretrained_peft"]
    ests = [out["per_seed"][str(s)]["families"]["PE-GENERIC|NCE|cbramod|AUC"]["members"]["pretrained_peft"]["est"] for s in SEEDS]
    assert b["min"] == min(ests) and b["max"] == max(ests) and abs(b["spread"] - (max(ests) - min(ests))) < 1e-15
    assert abs(b["sd"] - np.std(ests, ddof=1)) < 1e-15 and b["n_seeds"] == 3
    assert b["classes"]["3407"] == "I<0" and b["classes"]["3401"] == "I>0"
    assert b["spread_vs_widths"] == "above_every_width"  # a sign change of 0.02 against narrow within-seed intervals
    # per-identity file: per-seed deltas and their mean agree with the family inputs
    d = per_identity["per_seed_deltas"]["PE-GENERIC|NCE|cbramod|AUC|pretrained_full"]
    sm = per_identity["seed_mean_deltas"]["PE-GENERIC|NCE|cbramod|AUC|pretrained_full"]
    for kid in ALL_KIDS:
        assert abs(sm[kid][0] - np.mean([d[str(s)][kid] for s in SEEDS])) < 1e-15 and sm[kid][1] == 3


def test_simultaneous_intervals_cover_pointwise_and_one_member_families(clean):
    out = clean[3]
    for blk in [out["seed_mean"]] + [out["per_seed"][str(s)] for s in SEEDS]:
        for label, f in blk["families"].items():
            for name, m in f["members"].items():
                assert m["sim_low"] <= m["ci_low"] + 1e-12 and m["sim_high"] >= m["ci_high"] - 1e-12
            if label.startswith("PE-TRANSFER"):
                (m,) = f["members"].values()
                assert abs(m["sim_low"] - m["ci_low"]) < 1e-12 and abs(m["sim_high"] - m["ci_high"]) < 1e-12


def test_history_increment_addition_a_keeps_frozen_pointwise(clean):
    out = clean[3]
    for blk in [out["seed_mean"]] + [out["per_seed"][str(s)] for s in SEEDS]:
        for k, sec in blk["secondary"].items():
            a = blk["hist_gain_simultaneous"][k]
            assert set(a["members"]) == set(sec[EM.HG]["members"])
            for name, x in sec[EM.HG]["members"].items():
                for key in ("n", "est", "se", "ci_low", "ci_high", "pct_low", "pct_high"):
                    assert x[key] == a["members"][name][key]
                assert "sim_low" not in x and "sim_low" in a["members"][name]
    x = out["per_seed"]["3407"]["hist_gain_simultaneous"]["PE-GENERIC|CS_SINGLE|reve"]["members"]["pretrained_full"]
    assert abs(x["est"] - 0.001) < 0.0003
    tw = out["seed_mean"]["secondary"]["PE-LOCAL|NCE"]["twin_sens"]["members"]["generic/reve/random_full"]
    assert abs(tw["est"]) < 1e-12  # the twin sensitivity is 0.0005 for every configuration, so every paired difference is 0


def test_levels_per_seed_and_mean(clean):
    out = clean[3]
    gx = BI.ckey(("E_GX", "GX_NATIVE", "GX", "full"))
    for s in SEEDS:
        lv = out["levels"][str(s)][gx]
        exp = np.mean([values(("E_GX", "GX_NATIVE", "GX", "full"), s, k)[0] for k in ALL_KIDS])
        assert abs(lv["AUC"]["est"] - exp) < 1e-12 and lv["n"] == 12
        assert lv["AUC"]["ci_low"] < lv["AUC"]["est"] < lv["AUC"]["ci_high"]
        assert set(lv["AUC"]["groups"]) == {"HA", "NH"}
        h = lv["hist_gain_ci"]
        assert h["ci_low"] < h["est"] < h["ci_high"] and abs(h["est"] - lv["hist_gain"]["est"]) < 1e-15
    m = out["levels"]["mean"][gx]
    exp = np.mean([np.mean([values(("E_GX", "GX_NATIVE", "GX", "full"), s, k)[0] for s in SEEDS]) for k in ALL_KIDS])
    assert abs(m["AUC"]["est"] - exp) < 1e-12 and m["children_by_n_seeds"] == {"3": 12}
    b = out["levels_between_seed"][f"{gx}|AUC"]
    assert b["n_seeds"] == 3 and b["min"] <= b["max"]


# ------------------------------------------------------------------------------------------------ reproduction, coverage, QC
def test_reproduction_plumbing_detects_changes():
    rows, load, triples = make_design()
    with EM.seed_scope(3401):
        published = BI.aggregate_private(BI.load_private(rows, load))
    published = json.loads(json.dumps(BI.jl({"meta": {"seed": 3401}, **published})))
    out, _, _ = EM.analyse(rows, load, published, mc_k=0, triples=triples)
    rep = out["reproduction_3401"]
    assert rep["full_aggregation_vs_published"]["mismatches"] == [] and rep["full_aggregation_vs_published"]["n_numbers"] > 1000
    assert rep["panel_members_pointwise_vs_published"]["mismatches"] == [] and rep["panel_members_pointwise_vs_published"]["max_abs_diff"] == 0.0
    assert rep["panel_members_pointwise_vs_published"]["n_member_blocks"] == 24 * 4 + 24  # 24 members x 4 endpoints + addition A
    assert rep["panel_levels_vs_published"]["mismatches"] == [] and rep["panel_levels_vs_published"]["n_configurations"] == 17
    sim = rep["published_full_family_simultaneous"]["PE-GENERIC|NCE|cbramod|AUC|pretrained_full"]
    assert sim["n_members_frozen"] == 4 and sim["crit"] >= out["per_seed"]["3401"]["families"]["PE-GENERIC|NCE|cbramod|AUC"]["crit"] - 1e-12
    npp = out["non_panel_published_3401"]
    assert "PE-GENERIC|NCE|cbramod|AUC|pretrained_frozen" in npp["members"] and "PE-COMPLEMENT" in npp["whole_families_not_in_panel"]
    bad = copy.deepcopy(published)
    bad["families"]["PE-GENERIC|NCE|cbramod|AUC"]["members"]["pretrained_full"]["est"] += 1e-6
    rep2 = EM.analyse(rows, load, bad, mc_k=0, triples=triples)[0]["reproduction_3401"]
    assert rep2["full_aggregation_vs_published"]["mismatches"] and rep2["panel_members_pointwise_vs_published"]["mismatches"]


def test_missing_pair_listed_not_filled_never_cross_seed():
    c = ("E_GENERIC", "NCE", "cbramod", "pretrained_full")
    kid = KIDS[1][2]
    rows, load, triples = make_design(drop=(c, 3407, kid))
    out, per_identity, _ = EM.analyse(rows, load, None, mc_k=0, triples=triples)
    cov = out["coverage"]
    assert cov["any_incomplete"] and cov["n_missing_pairs"] > 0
    miss = per_identity["missing_pairs"]
    assert all(m["child"] == kid and m["seed"] == 3407 for m in miss)
    assert {(m["family"], m["member"]) for m in miss} == {("PE-GENERIC|NCE|cbramod", "pretrained_full"), ("PE-LOCAL|NCE", "generic/cbramod/pretrained_full")}
    assert kid not in json.dumps(out)  # the aggregate output lists counts, not children
    sm = per_identity["seed_mean_deltas"]["PE-GENERIC|NCE|cbramod|AUC|pretrained_full"][kid]
    d = per_identity["per_seed_deltas"]["PE-GENERIC|NCE|cbramod|AUC|pretrained_full"]
    assert sm[1] == 2 and kid not in d["3407"] and abs(sm[0] - np.mean([d["3401"][kid], d["3413"][kid]])) < 1e-15
    fm = out["seed_mean"]["families"]["PE-GENERIC|NCE|cbramod|AUC"]
    assert fm["members"]["pretrained_full"]["identities_by_n_seeds"] == {"2": 1, "3": 11}
    assert out["per_seed"]["3407"]["families"]["PE-GENERIC|NCE|cbramod|AUC"]["members"]["pretrained_full"]["n"] == 11
    cc = out["seed_mean_complete_case"]["families"]["PE-GENERIC|NCE|cbramod|AUC"]["members"]["pretrained_full"]
    assert cc["n"] == 11 and cc["identities_by_n_seeds"] == {"3": 11}
    assert "children_or_trial_counts_differ_across_configurations" in out["qc"]["failures"]


def test_qc_flags_counts_donors_and_specs(clean):
    out = clean[3]
    q = out["qc"]
    assert q["failures"] == {} and q["children_and_trial_counts_equal_across_configurations_and_seeds"]
    assert q["counts"]["registry_cells"] == 34 and q["counts"]["panel_records"] == 102 and q["counts"]["fold_cells"] == 6
    assert q["one_descriptor_set_per_family_across_seeds"] and q["group_label_consistent"] and q["n_children_with_group"] == 12
    assert all(k.endswith("same_seed_same_objective_fau_lag_local_full") or "checkpoint_present" in k for k in q["donors"])
    c = ("E_LOCAL", "CS_SINGLE", "lag_local_tokens", "full")
    rows, load, triples = make_design(count_change=(c, 3413, KIDS[0][0]), donor_seed_shift=3407, spec_change=(("E_GX", "GX_NATIVE", "GX", "full"), 3407))
    q2 = EM.analyse(rows, load, None, mc_k=0, triples=triples)[0]["qc"]
    f = q2["failures"]
    assert "children_or_trial_counts_differ_across_configurations" in f and "children_or_trial_counts_differ_from_3401" in f
    assert len(f["donor_not_the_same_seed_fau_local_unit"]) == 4  # 2 objectives x 2 folds at seed 3407
    assert len(f["spec_or_fold_differs_from_3401"]) == 2 and not q2["children_and_trial_counts_equal_across_configurations_and_seeds"]


def test_mc_stability_declared_cells_match():
    rows, load, triples = make_design()
    out, _, _ = EM.analyse(rows, load, None, mc_k=2, triples=triples)
    mc = out["mc_stability"]
    assert mc["k"] == 2 and set(mc["cells"]) == {"panel", "full_frozen"}
    assert set(mc["cells"]["panel"]) == {"3401", "3407", "3413", "mean"} and len(mc["cells"]["panel"]["mean"]) == 48
    assert len(mc["cells"]["full_frozen"]["3401"]) == 48  # only the panel members of the full frozen families are kept
    ch = mc["checks"]
    assert ch["n_numbers"] == 2 * 48 * 4 and ch["max_abs_diff"] == 0.0 and ch["class_mismatches"] == []
    assert S.SEED == 20261011  # draw scope restored


def test_determinism(clean):
    rows, load, triples, out, per_identity, _ = clean
    out2, pi2, _ = EM.analyse(rows, load, None, mc_k=0, triples=triples)
    a = EM.compare_tree(EM._plain(out), EM._plain(out2)); b = EM.compare_tree(EM._plain(per_identity), EM._plain(pi2))
    assert a["mismatches"] == [] and b["mismatches"] == [] and a["n_numbers"] > 1000


# ------------------------------------------------------------------------------------------------ outputs
def _meta():
    return {"generated": "2026-01-01 00:00 CET", "host": "h", "slurm_job": "0", "code_sha256": {"aln34/e_multiseed.py": "a" * 64, "bc_interim.py": "b" * 64, "sci_r1/stats.py": "c" * 64},
            "code_registration": {"registered": ["a" * 64], "current_sha_registered": True},
            "plan_sha256": {"units.jsonl": "d" * 64, "plan_ext.jsonl": "e" * 64, "seed_panel_v31_registry.json": "f" * 64}, "record_digest": "0" * 64,
            "n_records_read": 114, "records_by_role": {"panel_3407_3413": 68, "panel_3401": 34, "other_3401": 12}, "published_reference": "x.json",
            "published_sha256": "1" * 64, "note_sha256": "2" * 64, "note_mtime": "2026-01-01", "note_before_run": True, "determinism": None,
            "peak_rss_mib": 100.0, "runtime_seconds": 1.0, "privacy_scan": "PASS"}


def test_render_tables_privacy_and_splice(clean, tmp_path):
    rows, load, triples = make_design()
    with EM.seed_scope(3401):
        published = json.loads(json.dumps(BI.jl({"meta": {}, **BI.aggregate_private(BI.load_private(rows, load))})))
    out, per_identity, _ = EM.analyse(rows, load, published, mc_k=2, triples=triples)
    doc = EM.render(out, _meta())
    assert "seed 3407" in doc and "Not in the panel" in doc and "recipe (C01)" in doc
    assert "pretrained_frozen" in doc  # non-panel members are listed with their seed-3401 values
    lines = doc.split("\n")
    i = 0
    while i < len(lines):  # every table row has the header's cell count
        if lines[i].startswith("|") and i + 1 < len(lines) and lines[i + 1].startswith("|---"):
            ncol = lines[i].count("|")
            j = i + 2
            while j < len(lines) and lines[j].startswith("|"):
                assert lines[j].count("|") == ncol, lines[j]
                j += 1
            i = j
        else:
            i += 1
    jp, dp = tmp_path / "e.json", tmp_path / "e.md"
    BI.write_json(str(jp), {"meta": _meta(), **out}, private=True)
    dp.write_text(doc)
    assert BI.privacy_scan([str(jp), str(dp)], set(ALL_KIDS)) == []
    pp = tmp_path / "per_identity.json"
    BI.write_json(str(pp), per_identity, private=True)
    assert BI.privacy_scan([str(pp)], set(ALL_KIDS)) == [str(pp)]  # child pseudonyms only in the private file
    assert oct(os.stat(jp).st_mode & 0o777) == "0o600"
    hand = doc.replace("## 2. 当前工作判断 (working interpretation)\n\n(written after the run)", "## 2. 当前工作判断 (working interpretation)\n\nmy text")
    again = EM.splice(EM.render(out, _meta()), hand)
    assert "my text" in again and again.count("## 2. ") == 1
    with pytest.raises(ValueError):
        EM.splice("# t\n\n## 1. a\n", hand)


def test_scopes_restore_on_error():
    s0, d0 = BI.SEED, S.SEED
    with pytest.raises(RuntimeError):
        with EM.seed_scope(3407):
            assert BI.SEED == 3407
            raise RuntimeError
    with pytest.raises(RuntimeError):
        with EM.draw_scope(1000):
            assert S.SEED == d0 + 1000
            raise RuntimeError
    assert BI.SEED == s0 and S.SEED == d0


def test_compare_tree_and_registered_shas(tmp_path):
    a = {"x": 1.0, "y": [1, 2], "z": "s", "new": 3}
    b = {"x": 1.0 + 1e-9, "y": [1, 2], "z": "t"}
    r = EM.compare_tree(a, b, one_sided=True)
    assert r["n_added"] == 1 and len(r["mismatches"]) == 2 and r["max_abs_diff"] > 0
    note = tmp_path / "n.md"
    h1, h2 = "a" * 64, "b" * 64
    note.write_text(f"# note\n\n`e_multiseed.py` sha256 `{'c' * 64}` (before the section)\n\n## Code registration\n\n- `auditory_alignment_v3/aln34/e_multiseed.py` sha256 `{h1}`\n"
                    f"- `tests/auditory_alignment_v3/aln34/test_e_multiseed.py` sha256 `{'d' * 64}`\n- later: `e_multiseed.py` sha256 `{h2}`\n")
    assert EM.registered_shas(str(note)) == [h1, h2]  # the test file's hash is not taken for the module's
    assert EM.registered_shas(str(tmp_path / "missing.md")) == []


def test_unit_levels_addition_f(clean):
    out, census = clean[3], clean[5]
    ul = out["unit_levels"]
    assert len(ul) == 17 * 3 * 2  # every panel unit: 17 configurations x 3 seeds x 2 folds
    c = ("E_GENERIC", "CS_SINGLE", "reve", "pretrained_peft")
    r = ul[f"{BI.ckey(c)}|3407|1|0"]
    assert r["n"] == 6 and r["fold"] == [1, 0] and r["seed"] == 3407
    assert abs(r["NLL"] - np.mean([values(c, 3407, k)[1] for k in KIDS[1]])) < 1e-12
    assert abs(r["AUC"] - np.mean([values(c, 3407, k)[0] for k in KIDS[1]])) < 1e-12
    assert abs(r["calibrator_slope"] - (1.0 + 0.1 + 0.007)) < 1e-12 and r["calibrator_intercept"] == -1.0
    assert not any(k in json.dumps(ul) for k in ALL_KIDS)  # unit means only, no child pseudonym
    lines = EM.unit_table(out)
    # main unit table: 17 configurations x 3 seeds; addition G summary (v3): the 3 excluded configurations x 3 seeds
    assert sum(1 for x in lines if x.startswith("| E_")) == 17 * 3 + 3 * 3


def test_width_category():
    assert EM.width_category(0.1, [0.2, 0.3, 0.4]) == "below_every_width"
    assert EM.width_category(0.25, [0.2, 0.3]) == "between"
    assert EM.width_category(0.5, [0.2, 0.3]) == "above_every_width"


# ------------------------------------------------------------------------------------------------ version 3: G, recipes, numbering, archives
def test_unit_nll_excess_addition_g():
    reve_peft = ("E_GENERIC", "CS_SINGLE", "reve", "pretrained_peft")
    reve_rand = ("E_GENERIC", "CS_SINGLE", "reve", "random_full")
    shift = {(reve_peft, 3407, 0): 0.2, (reve_peft, 3407, 1): 0.15, (reve_rand, 3413, 1): 0.05}
    rows, load, triples = make_design(nll_shift=shift)
    out = EM.analyse(rows, load, None, mc_k=0, triples=triples)[0]
    g, ul = out["unit_nll_excess"], out["unit_levels"]
    assert len(g["reference_configurations"]) == 14 and len(g["excluded_configurations"]) == 3
    assert set(g["excluded_configurations"]) == {BI.ckey(("E_GENERIC", "CS_SINGLE", "reve", ad)) for ad in EM.PANEL_ADAPT}
    assert g["n_reference_units"] == 14 * 3 * 2 and set(g["n_reference_units_by_seed_fold"].values()) == {14}
    ref = set(g["reference_configurations"])
    for k, r in ul.items():  # excess = unit NLL - median of the 14 reference unit NLLs of the same seed and fold
        m = np.median([x["NLL"] for x in ul.values() if x["config"] in ref and x["seed"] == r["seed"] and x["fold"] == r["fold"]])
        assert abs(g["excess"][k] - (r["NLL"] - m)) < 1e-15
    rx = [g["excess"][k] for k, r in ul.items() if r["config"] in ref]
    assert g["reference_excess_range"] == [min(rx), max(rx)]
    b = g["by_configuration_seed"][f"{BI.ckey(reve_peft)}|3407"]
    assert b["n_units"] == 2 and b["n_above_reference_max"] == 2 and not b["reference"]
    assert abs(b["excess_by_subject_fold"]["0"] - 0.2) < 0.003
    hi = g["reference_excess_range"][1]
    for b2 in g["by_configuration_seed"].values():  # the count is the number of units above the largest reference excess
        assert b2["n_above_reference_max"] == sum(v > hi for v in b2["excess_by_subject_fold"].values())
        if b2["reference"]:
            assert b2["n_above_reference_max"] == 0
    rr = g["by_configuration_seed"][f"{BI.ckey(reve_rand)}|3413"]["excess_by_subject_fold"]
    assert rr["1"] > hi + 0.04 and rr["0"] < hi + 0.001  # one raised unit, one unit at the level of the reference units
    # the main statistics do not depend on G: same family results as without the added fields
    assert out["per_seed"]["3407"]["families"]["PE-GENERIC|CS_SINGLE|reve|NLL"]["members"]["pretrained_peft"]["est"] < -0.1
    lines = EM.unit_table(out)
    row = next(x for x in lines if x.startswith(f"| {EM.lab(BI.ckey(reve_peft))} | 3407 |") and "of 2" in x)
    assert row.endswith("| 2 of 2 |")


def test_recipes_block_and_summary(clean):
    out = clean[3]
    rc = out["recipes"]
    assert rc["n_records"] == 17 * 3 * 2 and rc["n_records_with_open_groups"] == 0 and rc["one_descriptor_set_per_configuration"]
    c = rc["configurations"][BI.ckey(("E_GENERIC", "CS_SINGLE", "reve", "pretrained_full"))]
    assert c["units_per_seed"] == {"3401": 2, "3407": 2, "3413": 2} and c["n_descriptor_sets"] == 1
    d = c["descriptor_sets"][0]
    assert d["lr_backbone"] == 1e-5 and d["lr_head"] == 1e-3 and d["epochs"] == 50 and d["n_trainable_backbone"] == d["n_params"] == 69189632
    assert d["lr_equals_recipe_chosen"] is None  # the synthetic records name recipe files that do not exist
    k = rc["pe_generic_contrasts"]
    assert abs(k["PE-GENERIC|NCE|cbramod|pretrained_full"]["backbone_lr_ref_over_cand"] - 3) < 1e-9
    assert abs(k["PE-GENERIC|CS_SINGLE|reve|pretrained_full"]["backbone_lr_ref_over_cand"] - 100) < 1e-9
    assert k["PE-GENERIC|CS_SINGLE|reve|pretrained_full"]["every_backbone_parameter_trained"] == [True, True]
    assert k["PE-GENERIC|CS_SINGLE|reve|pretrained_peft"]["every_backbone_parameter_trained"] == [True, False]
    s = EM.recipe_summary(out)
    assert "3× to 100× lower" in s and "differs in 3 of 4 scopes" in s and "the epochs are the same" in s
    assert "both arms train every backbone parameter from the start" in s and "progressive-prefix" not in s
    lines = EM.recipe_tables(out)
    assert sum(1 for x in lines if x.startswith("| E_GENERIC")) == 12 and any("LoRA r8 adapters (all attention projections)" in x for x in lines)
    assert any("Other panel configurations:" in x and "no `resolved_config` recorded" in x for x in lines)  # E_GX


def test_recipe_files_checked_and_open_groups_detected(tmp_path):
    for (o, a), v in LRS.items():
        for ad, (lb, lh) in v.items():
            chosen = {"lr_backbone": lb, "lr_head": lh}
            if (o, a, ad) == ("NCE", "reve", "pretrained_full"):
                chosen = {"lr_backbone": 1e-4, "lr_head": lh}  # a recipe file that disagrees with the records
            (tmp_path / f"{a}__{ad}__private_bdf__{o}.json").write_text(json.dumps({"chosen": chosen, "dev_cell": {"subject_fold": 0, "content_fold": 0, "seed": 3401},
                                                                                    "epochs": 20, "candidates": [{}, {}]}))
    c_og = ("E_GENERIC", "CS_SINGLE", "cbramod", "pretrained_full")
    rows, load, triples = make_design(recipe_dir=str(tmp_path), open_groups_unit=(c_og, 3413, 1))
    out = EM.analyse(rows, load, None, mc_k=0, triples=triples)[0]
    rc = out["recipes"]
    ok = rc["configurations"][BI.ckey(("E_GENERIC", "NCE", "cbramod", "pretrained_full"))]["descriptor_sets"][0]
    assert ok["lr_equals_recipe_chosen"] is True and ok["recipe_dev_cell"]["seed"] == 3401 and ok["recipe_search_epochs"] == 20
    bad = rc["configurations"][BI.ckey(("E_GENERIC", "NCE", "reve", "pretrained_full"))]["descriptor_sets"][0]
    assert bad["lr_equals_recipe_chosen"] is False
    assert rc["n_records_with_open_groups"] == 1 and not rc["one_descriptor_set_per_configuration"]
    og = rc["configurations"][BI.ckey(c_og)]
    assert og["n_descriptor_sets"] == 2 and sorted(d["n_units"] for d in og["descriptor_sets"]) == [1, 5]
    assert rc["pe_generic_contrasts"]["PE-GENERIC|CS_SINGLE|cbramod|pretrained_full"] is None  # not one descriptor set: no contrast row
    assert "not recorded for every scope" in EM.recipe_summary(out) or "incomplete" in EM.recipe_summary(out)
    assert any("| NO" in x for x in EM.recipe_tables(out))


def test_section_numbers_and_cross_references(clean):
    out = clean[3]
    doc = EM.render(out, _meta())
    heads = [x.split()[1] for x in doc.split("\n") if x.startswith("### 1.")]
    assert heads == [f"1.{j}" for j in range(1, len(EM.SECTION_ORDER) + 1)]  # sections in order, numbered as SECNO says
    assert f"### {EM.SECNO['mc']} Monte-Carlo stability" in doc and f"§{EM.SECNO['mc']} shows their Monte-Carlo stability" in doc
    assert EM.SECNO["mc"] == "1.14" and EM.SECNO["coverage"] == "1.11" and EM.SECNO["unit"] == "1.15" and EM.SECNO["recipe"] == "1.16"
    assert f"### {EM.SECNO['recipe']} Training-recipe descriptors" in doc
    assert "30×" not in doc and "progressive-prefix schedule" not in doc  # v3: the recipe text comes from the records
    assert "the head learning rate differs in 3 of 4 scopes" in doc


def test_crit_comparison_text(clean):
    rows, load, triples = make_design()
    with EM.seed_scope(3401):
        published = json.loads(json.dumps(BI.jl({"meta": {}, **BI.aggregate_private(BI.load_private(rows, load))})))
    out = EM.analyse(rows, load, published, mc_k=0, triples=triples)[0]
    fams = EM.panel_families()
    txt = " ".join(EM.crit_comparison(out, out["reproduction_3401"], fams))
    assert "PE-GENERIC" in txt and "(2 of 4 members per scope)" in txt and "(7 of 16 members per scope)" in txt and "(1 of 6 members per scope)" in txt
    assert "at or below its full-family value: True" in txt and "PE-TRANSFER panel families have a single member" in txt
    for k, v in out["reproduction_3401"]["published_full_family_simultaneous"].items():
        assert out["per_seed"]["3401"]["families"][k.rsplit("|", 1)[0]]["crit"] <= v["crit"] + 1e-12


def test_compare_with_archives_wording(tmp_path):
    rows, load, triples = make_design()
    out, per_identity, _ = EM.analyse(rows, load, None, mc_k=0, triples=triples)
    a1, a2 = tmp_path / "v1", tmp_path / "v2"
    a1.mkdir(); a2.mkdir()
    old1 = {"meta": {"x": 1}, **{k: v for k, v in EM._plain(out).items() if k not in ("unit_levels", "unit_nll_excess", "recipes")}}
    old2 = {"meta": {}, **{k: v for k, v in EM._plain(out).items() if k not in ("unit_nll_excess", "recipes")}}
    old2["unit_levels"] = copy.deepcopy(old2["unit_levels"])
    first = next(iter(old2["unit_levels"]))
    old2["unit_levels"][first].pop("calibrator_intercept")  # a field that only the current version has
    for d, o in ((a1, old1), (a2, old2)):
        (d / "e_multiseed.json").write_text(json.dumps(o)); (d / "per_identity.json").write_text(json.dumps(EM._plain(per_identity)))
    vc = EM.compare_with_archives(out, per_identity, (("version 1", str(a1)), ("version 2", str(a2))))
    assert vc["version 1"]["new_top_level_keys"] == ["recipes", "unit_levels", "unit_nll_excess"] and vc["version 1"]["json"]["n_added"] == 0
    assert vc["version 2"]["new_top_level_keys"] == ["recipes", "unit_nll_excess"] and vc["version 2"]["json"]["n_added"] == 1
    assert all(v["json"]["mismatches"] == [] and v["per_identity"]["mismatches"] == [] for v in vc.values())
    txt = EM._versions_txt({"version_comparisons": vc})
    assert "0 fields added inside those blocks; new top-level blocks: `recipes`, `unit_levels`, `unit_nll_excess`" in txt
    assert "1 fields added inside those blocks; new top-level blocks: `recipes`, `unit_nll_excess`" in txt
    assert "added fields (" not in txt  # the version-2 wording that read as a contradiction
    old2.pop("coverage")
    (a2 / "e_multiseed.json").write_text(json.dumps(old2))
    vc2 = EM.compare_with_archives(out, per_identity, (("version 2", str(a2)),))
    assert vc2["version 2"]["missing_top_level_keys"] == [] and "coverage" in vc2["version 2"]["new_top_level_keys"]
