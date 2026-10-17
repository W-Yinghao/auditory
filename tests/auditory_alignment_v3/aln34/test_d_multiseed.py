"""R34_D_PANEL synthetic checks of auditory_alignment_v3.aln34.d_multiseed: panel restriction of the ADDENDUM_12 families,
per-seed paired effects, identity mean over the seeds in which the pair exists (pairs never cross seeds, missing pairs never
filled), between-seed range and its comparison with the per-seed widths, coverage, pairing QC, sign handling of lower-is-better
readouts, the seed-3401 reproduction plumbing, the Monte-Carlo stability table, the card-contrast families, the support / query
sizes, the determinism and version comparison helpers, the document splice and the report renderer (rank unit, table cells).
No unit record or EEG is read."""
import copy
import re

import numpy as np
import pytest

from auditory_alignment_v3 import bc_interim as BI
from auditory_alignment_v3 import d_lag_interim as DL
from auditory_alignment_v3.aln34 import d_multiseed as DM
from auditory_alignment_v3.sci_r1 import stats as S

PIDS = {"fau": [f"F{j:02d}" for j in range(6)], "dtu": [f"D{j:02d}" for j in range(8)]}
GROUPS = {"fau": ("th", "ha", "ci"), "dtu": ("nh", "hi")}
TASK_EFF = {3401: 0.03, 3407: -0.01, 3413: 0.01}   # alignment_plus_selection - attended_alignment (unified mean_score accuracy)
AD_EFF = {3401: 0.20, 3407: 0.21, 3413: 0.22}      # input_spatial - none, support 0.3 (unified gain_bits); support 0.1: AD_EFF - 0.1
WIN = {5: 0.0, 10: 0.02, 20: 0.04}
ATT_TASKS_3401_EXTRA = [("attended_alignment", "CS_SINGLE"), ("selection_only", "SELECTION_CE")]
MC_K_TEST = 3


def _noise(*k):
    return 0.0005 * np.random.default_rng(abs(hash(k)) % (2 ** 32)).standard_normal()


def _att_rec(s, ds, test, t, cf, integ, twin=None):
    pp = {}
    for p in test:
        j = PIDS[ds].index(p)
        cell = {}
        for w in DL.WINS:
            acc = 0.6 + 0.01 * j + 0.004 * cf + WIN[w] + (TASK_EFF[s] if t == "alignment_plus_selection" else 0.0) + _noise(s, p, t, w)
            for rd in ("unified", "native"):
                a = acc + (0.05 if rd == "native" else 0.0)
                cell[f"{w}s|{rd}"] = {"mean_score_accuracy": a, "learned_temporal_accuracy": a - 0.01, "mean_margin": 0.1 + 0.001 * j, "n_windows": 12}
        pp[p] = {"group": GROUPS[ds][j % len(GROUPS[ds])], **cell}
    return {"status": "complete", "code_hash": "h_att", "target_contract": "dense20ms_v1", "shared_model_with": twin,
            "chosen_sel_weight": 0.1 if t == "alignment_plus_selection" else None, "eval": {"attention_windows": {"per_participant": pp}}}


def _ad_rec(s, ds, test, a, base):
    pp = {}
    for p in test:
        j = PIDS[ds].index(p); g0 = 0.5 + 0.01 * j
        x = {}
        for sf in DL.SUPPORTS:
            e = 0.0 if a == "none" else (AD_EFF[s] if sf == "0.3" else AD_EFF[s] - 0.1) + _noise(s, p, a, sf)
            if a == "output_low_rank":
                e = 0.03
            x[f"support_{sf}"] = {"unified": {"gain_bits": g0 + e, "rank_pct": 0.30 - (0.05 if a != "none" else 0.0), "top1": 0.10 + (0.02 if a != "none" else 0.0), "n_query": 7},
                                  "native": {"gain_bits": g0 + (0.3 if a != "none" else 0.0), "rank_pct": 0.3, "top1": 0.1, "n_query": 7}, "n_support": 1 if sf == "0.1" else 3}
        pp[p] = {"group": GROUPS[ds][j % len(GROUPS[ds])], "n_segments": 10, **x}
    return {"status": "complete", "code_hash": "h_ad", "target_contract": "dense20ms_v1",
            "dependency": {"base_same_fold": base, "base_checkpoint": "private/none/does_not_exist.pt"},
            "eval": {"per_participant": pp, "steps": {"chosen": 50, "scores": {}}}}


def make_data():
    rows, recs = [], {}
    for s in DM.SEEDS:
        for ds in ("fau", "dtu"):
            for sf in (0, 1):
                test = [p for k, p in enumerate(PIDS[ds]) if k % 2 == sf]
                for cf in (0, 1):
                    base = f"BASE|{s}|{ds}|{sf}|{cf}"
                    rows.append({"experiment_id": base, "family_id": "A_LOCAL", "dataset": ds, "subject_fold": sf, "content_fold": cf, "seed": s,
                                 "spec": {"architecture": "lag_local_tokens", "objective": "NCE", "window": "full"}})
                    tasks = [(t, "NCE") for t in DM.TASKS] + (ATT_TASKS_3401_EXTRA if s == 3401 else [])
                    for t, o in tasks:
                        for integ in ("mean_score", "learned_temporal"):
                            e = f"ATT|{s}|{ds}|{sf}|{cf}|{t}|{o}|{integ}"
                            spec = {"architecture": "lag_local_tokens", "integrator": integ, "training_task": t, "objective": o}
                            rows.append({"experiment_id": e, "family_id": "D_ATTENTION", "dataset": ds, "subject_fold": sf, "content_fold": cf, "seed": s, "spec": spec,
                                         "reference_3401_id": f"ATT|3401|{ds}|{sf}|{cf}|{t}|{o}|{integ}"})
                            twin = f"ATT|{s}|{ds}|{sf}|{cf}|{t}|{o}|mean_score" if integ == "learned_temporal" else None
                            recs[e] = _att_rec(s, ds, test, t, cf, integ, twin)
                    adapters = list(DM.ADAPTERS) + (["output_low_rank"] if s == 3401 else [])
                    for a in adapters:
                        e = f"AD|{s}|{ds}|{sf}|{cf}|{a}"
                        spec = {"architecture": "lag_local_tokens", "objective": "NCE", "adapter": a}
                        rows.append({"experiment_id": e, "family_id": "D_ADAPT", "dataset": ds, "subject_fold": sf, "content_fold": cf, "seed": s, "spec": spec,
                                     "reference_3401_id": f"AD|3401|{ds}|{sf}|{cf}|{a}"})
                        recs[e] = _ad_rec(s, ds, test, a, base)
    return rows, recs


def _published(rows, recs):
    """what d_lag_interim.main would have published for seed 3401 on these records (attention + adapt blocks)."""
    import json
    DM.setup()
    vals, grp, _ = DM.collect_seed(rows, recs.get, 3401)
    att = DL.run_fams(DL.att_families(), vals, grp, DM.ATT_METRICS, DM.ATT_PRIMARY, [])
    ad = DL.run_fams(DL.ad_families(), vals, grp, DM.AD_METRICS, DM.AD_PRIMARY, [])
    return json.loads(json.dumps(BI.jl({"attention": att, "adapt": ad})))


def _m(out, label, name, seed=None):
    blk = out["seed_mean"] if seed is None else out["per_seed"][str(seed)]
    return blk["families"][label]["members"][name]


META = {"generated": "now", "host": "h", "slurm_job": "0", "code_sha256": {"x": "0" * 64}, "plan_sha256": {"units.jsonl": "0" * 64, "plan_ext.jsonl": "0" * 64},
        "record_digest": "0" * 64, "n_records_read": 1, "note_sha256": "0" * 64, "note_mtime": "t", "runtime_seconds": 1.0,
        "records_by_role": {"panel_3407_3413": 0, "panel_3401": 0, "other_3401": 0}}


@pytest.fixture(scope="module")
def clean():
    rows, recs = make_data()
    pub = _published(rows, recs)
    out, per_identity, census = DM.analyse(rows, recs.get, pub, mc_k=MC_K_TEST)
    return rows, recs, pub, out, per_identity


def _table_cells(line):
    return len(re.findall(r"(?<!\\)\|", line)) - 1


def test_panel_families_restriction():
    fams = DM.panel_families()
    assert len(fams) == 24 and sum(len(f["members"]) for f in fams) == 44
    c = {}
    for f in fams:
        c[f["family"]] = c.get(f["family"], 0) + len(f["members"])
    assert c == {"AT-LEVEL": 12, "AT-INTEGRATOR": 12, "AT-LENGTH": 8, "AT-TASK": 6, "AD-GAIN": 4, "AD-SUPPORT": 2}
    by = {f["label"]: [m[0] for m in f["members"]] for f in fams}
    assert by["AT-TASK|fau|5s"] == ["align->align+sel NCE"] and by["AD-GAIN|dtu|NCE|0.3"] == ["input_spatial"]
    assert by["AD-SUPPORT|fau|NCE"] == ["input_spatial"] and "AT-LEVEL|fau|selection_only|SELECTION_CE" not in by
    assert not any("CS_SINGLE" in lab for lab in by)
    assert all(f["n_members_addendum12"] >= len(f["members"]) for f in fams)
    full = DM.full_families_with_panel_members()
    assert {f["label"] for f in full} == set(by) and all(set(f["panel_members"]) == set(by[f["label"]]) for f in full)


def test_clean_panel_effects_range_and_qc(clean):
    rows, recs, pub, out, per_identity = clean
    assert BI.SEED == 3401  # seed scope restored
    # per-seed effects equal the constructed ones; identity mean over seeds = mean of the seeds; range = spread of the seeds
    for s in DM.SEEDS:
        assert abs(_m(out, "AT-TASK|dtu|10s", "align->align+sel NCE", s)["est"] - TASK_EFF[s]) < 0.003
        assert abs(_m(out, "AD-GAIN|fau|NCE|0.3", "input_spatial", s)["est"] - AD_EFF[s]) < 0.003
        assert abs(_m(out, "AD-GAIN|fau|NCE|0.1", "input_spatial", s)["est"] - (AD_EFF[s] - 0.1)) < 0.003
    assert abs(_m(out, "AT-TASK|dtu|10s", "align->align+sel NCE")["est"] - np.mean(list(TASK_EFF.values()))) < 0.003
    assert abs(_m(out, "AD-GAIN|fau|NCE|0.3", "input_spatial")["est"] - 0.21) < 0.003
    b = out["between_seed"]["AT-TASK|dtu|10s|align->align+sel NCE|acc"]
    assert abs(b["spread"] - 0.04) < 0.006 and b["n_seeds"] == 3 and set(b["classes"]) == {"3401", "3407", "3413"}
    # seed mean = mean of the per-seed estimates when every identity has every seed
    est = [_m(out, "AD-SUPPORT|dtu|NCE", "input_spatial", s)["est"] for s in DM.SEEDS]
    assert abs(_m(out, "AD-SUPPORT|dtu|NCE", "input_spatial")["est"] - np.mean(est)) < 1e-12
    # lower-is-better secondary (rank proportion): reference - candidate, positive = better, also in the seed mean
    r = out["seed_mean"]["secondary"]["AD-GAIN|fau|NCE|0.3"]["rank_pct_q"]["members"]["input_spatial"]
    assert abs(r["est"] - 0.05) < 1e-9 and r["ref"] == "AD|fau|NCE|none|0.3" and r["cand"] == "AD|fau|NCE|input_spatial|0.3"
    assert abs(out["seed_mean"]["secondary"]["AD-GAIN|fau|NCE|0.3"]["gain_bits_native"]["members"]["input_spatial"]["est"] - 0.3) < 1e-9
    # level vs chance, integrator, length
    assert abs(_m(out, "AT-INTEGRATOR|fau|attended_alignment|NCE", "20s")["est"] + 0.01) < 1e-9
    assert _m(out, "AT-LEVEL|dtu|alignment_plus_selection|NCE", "5s")["class"] == "I>0"
    assert abs(_m(out, "AT-LENGTH|fau|attended_alignment|NCE", "5s->20s")["est"] - 0.04) < 0.003
    # single-member family: simultaneous interval = pointwise bootstrap-t interval
    m = _m(out, "AD-GAIN|dtu|NCE|0.3", "input_spatial", 3407)
    assert abs(m["sim_low"] - m["ci_low"]) < 1e-12 and abs(m["sim_high"] - m["ci_high"]) < 1e-12
    # identities: n counts identities only; identity value = mean over its content-fold units
    assert _m(out, "AD-GAIN|dtu|NCE|0.3", "input_spatial")["n"] == 8 and _m(out, "AT-TASK|fau|5s", "align->align+sel NCE")["n"] == 6
    v = per_identity["per_seed_values"]["3407"]["ATT|fau|attended_alignment|NCE|ms|5"]["F02"]["acc"]
    assert abs(v - (0.6 + 0.02 + 0.002 + _noise(3407, "F02", "attended_alignment", 5))) < 1e-12
    assert _m(out, "AD-GAIN|dtu|NCE|0.3", "input_spatial")["identities_by_n_seeds"] == {"3": 8}
    # coverage and QC
    cov = out["coverage"]
    assert not cov["any_incomplete"] and cov["missing_pairs"] == [] and out["seed_mean_complete_case"] is None
    assert cov["families"]["AD-GAIN|fau|NCE|0.1"] == {"expected_identities": 6, "per_seed_common": {"3401": 6, "3407": 6, "3413": 6},
                                                      "seed_mean_common": 6, "all_three_seeds": 6, "n_missing_pairs": 0}
    u = cov["units"]["D_ATTENTION|dtu|attended_alignment|learned_temporal|3413"]
    assert u == {"registered": 4, "complete": 4, "identities": 8, "units_per_identity": {"2": 8}}
    q = out["qc"]
    assert q["failures"] == {} and q["counts"] == {"adapt_fold_pairs": 24, "attention_fold_pairs": 24, "learned_temporal_twins": 48}
    assert all(v["identical"] for v in q["adapter_none_identical_across_support"].values())
    assert q["group_label_consistent_across_seeds"] and q["code_hash_single_per_family"]
    assert q["panel_rows_spec_equal_to_reference_3401"] == {"checked": 96, "failures": []}
    assert out["status"]["D_ATTENTION|3407|complete"] == 32 and out["status"]["D_ADAPT|3413|complete"] == 16
    assert out["training_choices"]["D_ADAPT|fau|input_spatial|adaptation_steps|3407"] == {"50": 4}
    assert out["base_checkpoints"]["3401"] == {"distinct_bases": 8, "checkpoint_present": 0}
    # reproduction plumbing: identical on the same records; pointwise panel values equal the full-family ones
    rep = out["reproduction_3401"]
    for k in ("attention", "adapt"):
        assert rep["full_families_vs_published"][k]["mismatches"] == [] and rep["full_families_vs_published"][k]["n_numbers"] > 100
        assert "n_added" not in rep["full_families_vs_published"][k]
    assert rep["panel_members_pointwise_vs_published"]["mismatches"] == [] and rep["panel_members_pointwise_vs_published"]["n_members"] > 0
    assert rep["published_full_family_simultaneous"]["AD-GAIN|fau|NCE|0.3|input_spatial"]["n_members_addendum12"] == 2
    bad = copy.deepcopy(pub)
    bad["adapt"]["families"]["AD-GAIN|fau|NCE|0.3"]["members"]["input_spatial"]["est"] += 1e-6
    assert DM.compare_tree(bad["adapt"], pub["adapt"])["mismatches"]
    # report renders
    txt = DM.render(out, META)
    assert "### 1.1 Personal supervised adaptation" in txt and "Not in the panel" in txt and "Missing pairs: none" in txt
    assert "class differences between the published full family and the panel family" in txt


def test_width_category_and_between_seed(clean):
    out = clean[3]
    assert DM.width_category(0.01, [0.02, 0.03, 0.05]) == "below_every_width"
    assert DM.width_category(0.04, [0.02, 0.03, 0.05]) == "between"
    assert DM.width_category(0.06, [0.02, 0.03, 0.05]) == "above_every_width"
    n = 0
    for f in DM.panel_families():
        for name, *_ in f["members"]:
            b = out["between_seed"][f"{f['label']}|{name}|{DM.PRIMARY[f['kind']]}"]
            w = [_m(out, f["label"], name, s)["sim_high"] - _m(out, f["label"], name, s)["sim_low"] for s in DM.SEEDS]
            assert np.allclose([b["sim_widths"][str(s)] for s in DM.SEEDS], w, atol=0, rtol=0)
            assert b["spread_vs_widths"] == DM.width_category(b["spread"], w)
            if min(w) > 0:
                assert abs(b["spread_over_narrowest_width"] - b["spread"] / min(w)) < 1e-12 and abs(b["spread_over_widest_width"] - b["spread"] / max(w)) < 1e-12
            else:  # a constant synthetic difference has a zero-width interval: the category is defined, the ratio is not
                assert b["spread_over_narrowest_width"] is None
            n += 1
    assert n == 44
    # secondary readouts carry no width fields
    assert "sim_widths" not in out["between_seed"]["AD-GAIN|fau|NCE|0.3|input_spatial|rank_pct_q"]


def test_mc_stability(clean):
    out = clean[3]
    mc = out["mc_stability"]
    assert S.SEED == 20261011  # draw scope restored
    assert mc["k"] == MC_K_TEST and mc["alternative_base_seeds"] == [S.SEED + DM.MC_STEP * j for j in range(1, MC_K_TEST + 1)]
    assert set(mc["cells"]) == {"panel", "card", "full_addendum12"}
    assert set(mc["cells"]["panel"]) == {"3401", "3407", "3413", "mean"} and set(mc["cells"]["card"]) == {"3401", "3407", "3413", "mean"}
    assert set(mc["cells"]["full_addendum12"]) == {"3401"}
    assert len(mc["cells"]["panel"]["3407"]) == 44 and len(mc["cells"]["card"]["mean"]) == 10
    # full families: panel members only (e.g. no selection_only or output_low_rank member)
    keys = set(mc["cells"]["full_addendum12"]["3401"])
    assert len(keys) == 44 and not any("selection_only" in k or "output_low_rank" in k or "CS" in k for k in keys)
    # the declared draws reproduce the main results and the published full families exactly
    ch = mc["checks"]
    assert ch["max_abs_diff"] == 0.0 and ch["class_mismatches"] == [] and ch["n_numbers"] == 2 * (4 * 44 + 4 * 10 + 44)
    assert ch["full_family_cells_checked_against_published"] == 44
    changed = 0
    for g, blocks in mc["cells"].items():
        for blk, cs in blocks.items():
            for key, c in cs.items():
                assert c["n_alternatives"] == MC_K_TEST and 0 <= c["n_same_class"] <= MC_K_TEST and sum(c["classes"].values()) == MC_K_TEST
                assert c["sim_low_range"][0] <= c["sim_low_range"][1] and c["crit_range"][0] <= c["crit_range"][1]
                changed += c["sim_low_range"] != [c["declared"]["sim_low"]] * 2
    assert changed > 0  # the alternative draws really differ from the declared draw
    # deterministic: the same table again
    rows, recs, pub = clean[:3]
    out2 = DM.analyse(rows, recs.get, pub, mc_k=MC_K_TEST)[0]
    assert DM.compare_tree(DM._plain(out2["mc_stability"]), DM._plain(mc))["mismatches"] == []


def test_card_families(clean):
    out = clean[3]
    cf = DM.card_families()
    assert [f["label"] for f in cf] == ["R34-CARD|AT-TASK|fau", "R34-CARD|AD-GAIN|fau|NCE", "R34-CARD|AT-TASK|dtu", "R34-CARD|AD-GAIN|dtu|NCE"]
    assert [len(f["members"]) for f in cf] == [3, 2, 3, 2]
    res = out["card_families"]["results"]
    assert set(res) == {"3401", "3407", "3413", "mean"} and out["card_families"]["notes"] == []
    for f in cf:
        for name, *_ in f["members"]:
            pl, pn = f["panel_counterpart"][name]
            for blk in ("3401", "3407", "3413", "mean"):
                c = res[blk][f["label"]]["members"][name]
                p = out["seed_mean"]["families"][pl]["members"][pn] if blk == "mean" else out["per_seed"][blk]["families"][pl]["members"][pn]
                assert c["est"] == p["est"] and c["se"] == p["se"] and c["n"] == p["n"]  # same estimates and identities
                assert "class" in c and c["sim_low"] <= c["est"] <= c["sim_high"]
            assert res["mean"][f["label"]]["members"][name]["ref"] == BI.ckey(f["members"][[m[0] for m in f["members"]].index(name)][1])
        assert res["3407"][f["label"]]["crit"] > 0
    txt = DM.render(out, META)
    assert "### 1.14 Card contrasts" in txt and "R34-CARD · AT-TASK · fau · 10s" in txt


def test_support_query_sizes(clean):
    rows, recs, pub, out, _ = clean
    sq = out["support_query_sizes"]
    assert sq["equal_across_seeds_adapters_and_readouts"] is True
    assert sq["by_dataset_support"]["dtu|0.1"] == {"blocks": 16, "identities": 8, "n_support": {"min": 1, "median": 1.0, "max": 1},
                                                   "n_query": {"min": 7, "median": 7.0, "max": 7}, "identities_with_unequal_n_support_across_units": 0}
    assert sq["by_dataset_support"]["fau|0.3"]["n_support"] == {"min": 3, "median": 3.0, "max": 3} and sq["by_dataset_support"]["fau|0.3"]["blocks"] == 12
    recs2 = copy.deepcopy(recs)
    recs2["AD|3413|dtu|1|0|input_spatial"]["eval"]["per_participant"]["D03"]["support_0.1"]["n_support"] = 2
    recs2["AD|3413|dtu|1|0|none"]["eval"]["per_participant"]["D03"]["support_0.1"]["n_support"] = 2
    sq2 = DM.analyse(rows, recs2.get, None, mc_k=0)[0]["support_query_sizes"]
    assert sq2["equal_across_seeds_adapters_and_readouts"] is False
    assert sq2["by_dataset_support"]["dtu|0.1"]["n_support"]["max"] == 2 and sq2["by_dataset_support"]["dtu|0.1"]["identities_with_unequal_n_support_across_units"] == 1


def test_render_rank_unit_and_table_cells(clean):
    out = clean[3]
    txt = DM.render(out, META)
    assert "rank-percentile points" not in txt and "rank %" not in txt
    assert DM.RANK_UNIT in txt and "unified Δrank proportion (ref − cand; positive = better)" in txt
    # secondary readouts show per-seed pointwise intervals
    row = next(l for l in txt.split("\n") if l.startswith("| AD-GAIN · dtu · NCE · 0.1 · input_spatial | native gain_bits |"))
    assert len(re.findall(r"\[[+-]\d\.\d{3}, [+-]\d\.\d{3}\]", row)) == 5  # 3 per-seed CIs, the between-seed range, the identity-mean CI
    # every markdown table row has as many cells as its header (no unescaped '|' inside a cell)
    lines, n_tables = txt.split("\n"), 0
    for i, l in enumerate(lines):
        if l.startswith("|") and (i == 0 or not lines[i - 1].startswith("|")):
            n_tables += 1
            j, head = i, _table_cells(l)
            while j < len(lines) and lines[j].startswith("|"):
                assert _table_cells(lines[j]) == head, lines[j]
                j += 1
    assert n_tables >= 15
    cov_rows = [l for l in txt.split("\n") if l.startswith("| D_ATTENTION · ") and ("learned_temporal |" in l or "mean_score |" in l)]
    assert len(cov_rows) == 24 and all(_table_cells(l) == 5 for l in cov_rows)
    # sections and placeholders of the template
    heads = [h for h, _ in DM.sections(txt) if h]
    assert [h.split()[1] for h in heads] == ["1.", "2.", "3.", "4.", "5.", "6.", "Not", "7."]
    assert "Determinism: not checked in this run." in txt and "measured peak resident memory not measured" in txt
    # the Monte-Carlo section lists non-unanimous cells only (or says none differs)
    assert "### 1.13 Monte-Carlo stability" in txt and "alternative draws" in txt


def test_splice_keeps_hand_written_sections():
    gen = "# T\n\npre v2\n\n## 1. obs\n\nnew table\n\n## 2. judge\n\n(written after the run)\n\n## 5. reuse\n\nnew run\n\n## 6. open\n\n(written after the run)\n\n## Not in the panel\n\n- x\n\n## 7. history\n\n(written after the run)\n"
    old = "# T\n\npre v1\n\n## 1. obs\n\nold table\n\n## 2. judge\n\nhand text 2\n\n## 5. reuse\n\nold run\n\n## 6. open\n\nhand text 6\n\n## Not in the panel\n\n- y\n"
    s = DM.splice(gen, old)
    assert "pre v2" in s and "new table" in s and "new run" in s and "- x" in s
    assert "hand text 2" in s and "hand text 6" in s and "old table" not in s and "old run" not in s and "- y" not in s
    assert s.count("(written after the run)") == 1  # section 7 has no hand-written version yet
    assert "\n".join((b if h is None else f"{h}\n{b}") for h, b in DM.sections(gen)) == gen  # exact round trip
    assert DM.splice(gen, s) == s  # idempotent
    with pytest.raises(ValueError):
        DM.splice(gen.replace("## 4.", "## 9."), old.replace("## 6. open", "## 4. next"))


def test_determinism_and_version_comparison(clean):
    rows, recs, pub, out, per_identity = clean
    out2, per2, _ = DM.analyse(rows, recs.get, pub, mc_k=0)
    strip = lambda o: DM._plain({k: v for k, v in o.items() if k != "mc_stability"})
    d = DM.compare_tree(strip(out), strip(out2))
    assert d["mismatches"] == [] and d["n_numbers"] > 1000 and d["max_abs_diff"] == 0.0
    assert DM.compare_tree(DM._plain(per_identity), DM._plain(per2))["mismatches"] == []
    a, b = {"x": 1.0, "new": {"y": 2.0}}, {"x": 1.0}
    r = DM.compare_tree(a, b, one_sided=True)
    assert r["mismatches"] == [] and r["n_added"] == 1 and r["n_numbers"] == 1
    assert DM.compare_tree(b, a, one_sided=True)["mismatches"] == ["/new: present on one side only"]
    assert DM.compare_tree(a, b)["mismatches"] == ["/new: present on one side only"]


def test_non_panel_task_classes(clean):
    out = clean[3]
    npc = out["non_panel_task_classes_3401"]
    assert set(npc) == {f"AT-TASK|{ds}|{w}s|align NCE->selection_only" for ds in ("fau", "dtu") for w in DL.WINS}
    assert all(v["class"] in ("I>0", "I<0", "contains 0") for v in npc.values())
    assert DM.non_panel_task_classes(None) == {}


def test_missing_pairs_listed_not_filled_and_never_cross_seed():
    rows, recs = make_data()
    # D03 (dtu, subject fold 1) lacks its input_spatial values in seed 3413 (both content folds)
    for cf in (0, 1):
        del recs[f"AD|3413|dtu|1|{cf}|input_spatial"]["eval"]["per_participant"]["D03"]
    # F05 (fau, subject fold 1): reference 'none' only in seed 3407, candidate 'input_spatial' only in seed 3413 -> no pair anywhere
    for s in DM.SEEDS:
        for cf in (0, 1):
            if s != 3407:
                del recs[f"AD|{s}|fau|1|{cf}|none"]["eval"]["per_participant"]["F05"]
            if s != 3413:
                del recs[f"AD|{s}|fau|1|{cf}|input_spatial"]["eval"]["per_participant"]["F05"]
    # one learned_temporal copy that is not identical to its twin
    recs["ATT|3407|fau|0|0|attended_alignment|NCE|learned_temporal"]["eval"]["attention_windows"]["per_participant"]["F00"]["5s|unified"]["n_windows"] = 11
    out, per_identity, _ = DM.analyse(rows, recs.get, None, mc_k=0)
    assert out["mc_stability"] is None
    cov = out["coverage"]
    assert cov["any_incomplete"]
    miss = {(m["family"], m["member"], m["seed"], m["identity"]) for m in cov["missing_pairs"]}
    assert ("AD-GAIN|dtu|NCE|0.3", "input_spatial", 3413, "D03") in miss and ("AD-SUPPORT|dtu|NCE", "input_spatial", 3413, "D03") in miss
    assert all(("AD-GAIN|fau|NCE|0.1", "input_spatial", s, "F05") in miss for s in DM.SEEDS)
    assert cov["families"]["AD-GAIN|dtu|NCE|0.3"]["per_seed_common"] == {"3401": 8, "3407": 8, "3413": 7}
    assert cov["families"]["AD-GAIN|dtu|NCE|0.3"]["seed_mean_common"] == 8 and cov["families"]["AD-GAIN|dtu|NCE|0.3"]["all_three_seeds"] == 7
    # D03: mean of its two available seeds (not filled with 0); F05: no seed has the pair -> absent, never paired across seeds
    d = per_identity["seed_mean_deltas"]["AD-GAIN|dtu|NCE|0.3|input_spatial|gain_bits"]
    assert d["D03"][1] == 2 and abs(d["D03"][0] - np.mean([AD_EFF[3401] + _noise(3401, "D03", "input_spatial", "0.3"),
                                                           AD_EFF[3407] + _noise(3407, "D03", "input_spatial", "0.3")])) < 1e-12
    assert "F05" not in per_identity["seed_mean_deltas"]["AD-GAIN|fau|NCE|0.1|input_spatial|gain_bits"]
    assert _m(out, "AD-GAIN|fau|NCE|0.3", "input_spatial")["n"] == 5
    assert _m(out, "AD-GAIN|dtu|NCE|0.3", "input_spatial")["identities_by_n_seeds"] == {"2": 1, "3": 7}
    # the card family's identity mean uses the same identity values (D03 with its two seeds)
    assert out["card_families"]["results"]["mean"]["R34-CARD|AD-GAIN|dtu|NCE"]["members"]["0.3"]["identities_by_n_seeds"] == {"2": 1, "3": 7}
    # complete-case sensitivity: identities with all three seeds only
    cc = out["seed_mean_complete_case"]["families"]["AD-GAIN|dtu|NCE|0.3"]["members"]["input_spatial"]
    assert cc["n"] == 7
    # QC flags the unequal participant sets and the non-identical learned_temporal copy
    f = out["qc"]["failures"]
    assert "adapt_participants_or_counts_differ" in f and "learned_temporal_not_identical_copy" in f
    assert len(f["learned_temporal_not_identical_copy"]) == 1
    # the report still renders with missing pairs and without the Monte-Carlo table
    txt = DM.render(out, META)
    assert "Missing pairs (family, member, seed, identity)" in txt and "Not computed in this run." in txt


def test_seed_and_draw_scopes_restore_on_error():
    before, sb = BI.SEED, S.SEED
    h = S.group_seed("a", "b") - sb
    with pytest.raises(RuntimeError):
        with DM.seed_scope(3407):
            assert BI.SEED == 3407
            raise RuntimeError("x")
    assert BI.SEED == before
    with pytest.raises(RuntimeError):
        with DM.draw_scope(5000):
            assert S.SEED == sb + 5000 and S.group_seed("a", "b") == sb + 5000 + h  # every group seed shifts by the offset
            raise RuntimeError("y")
    assert S.SEED == sb
