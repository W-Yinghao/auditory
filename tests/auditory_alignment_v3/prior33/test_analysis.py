"""PUBLIC_PRIOR_DESIGN.md §5.8 / §7.1 item 14: synthetic checks of the M11 analysis (auditory_alignment_v3/prior33/analysis.py).

Synthetic records only (plan rows and unit-record JSON files in temporary directories, read back through load_records); CPU,
B = 4,000 as frozen. Covered: identity aggregation over cells and content folds (FAU, Federici records -> subjects with HC /
HC-v separate and the phantom excluded), donor reuse and repeated evaluations never adding n, missing / failed / unregistered
sides and planted pairing-key mismatches (listed separately, excluded with a reason, never zero-filled), family max-t (reproduced
from sci_r1.stats; pointwise on each member's own identities, simultaneous on the family set, members in the max-t), no p-values,
private metrics (positive-affine NLL / AUC directions, secondaries, the three-seed panel, the E_LOCAL reference), endpoint
directions and percentile columns, access modes kept separate, the pool check against the mode-T units, donor and target seeds
kept separate, execution versions from the donor-group rows (continuations, INIT on the primary S rows, labels), the two
selection rules, the donor-side selection table and the J* member check, selection levels, the B_uni_cal sensitivity coverage,
the two target_contract keys, the unit_rows fallback, privacy, and the §5.1 freeze gate (dry run, live reads, frozen run)."""
import json
import os
import re
import stat
import zlib

import numpy as np
import pytest

from auditory_alignment.aggregate import unit_rows
from auditory_alignment_v3.prior33 import analysis as A
from auditory_alignment_v3.sci_r1 import stats as S

PREFIX = A.SEL.PREFIX
MAN_SHA = "a" * 64
TC_SPEC, TC_REC = "tc-spec-1", "tc-rec-1"
LEVEL = {k: v[0] for k, v in A.SELECTION_LEVEL.items()}
IDS = {"fau": {0: [f"P{i:02d}" for i in range(6)] + ["P99"], 1: [f"P{i:02d}" for i in range(6, 12)] + ["P99"]},
       "federici": {0: ["HC:1001", "HC-v:1001", "CI:0002", "HC:1003", "Artifact:0306_bi"],
                    1: ["HC:1004", "HC-v:1004", "CI:0005", "HC:1006", "Artifact:0306_dx_2"]},
       "private_bdf": {0: [f"kid{i:02d}" for i in range(5)], 1: [f"kid{i:02d}" for i in range(5, 10)]}}
CELLS = {"fau": [(0, 0), (0, 1), (1, 0), (1, 1)], "federici": [(0, 0), (1, 0)], "private_bdf": [(0, None), (1, None)]}
MANIFEST = {**{r: (r, r.split(":")[0], "human") for f in IDS["federici"].values() for r in f if not r.startswith("Artifact")},
            "Artifact:0306_bi": ("Artifact", "Artifact", "phantom"), "Artifact:0306_dx_2": ("Artifact", "Artifact", "phantom")}
SLOT_BLOCK = {"APR": "rich", "APC": "csx", "XPC": "csx"}
GROUP_FAMILY = {"core": PREFIX + "DONOR", "panel": PREFIX + "DONOR", "rich": PREFIX + "RICH_DONOR", "csx": PREFIX + "CSX_DONOR"}
COMMON = {"logical_family": "ALN32_PUBLIC_AUDIO_PRIOR", "card": "E34_PUBLIC_PRIOR", "execution_contract": "aln33_env64_125ms_v1",
          "manifest_sha256": MAN_SHA, "architecture": "lag_local_tokens"}


def _z(*key):
    return float(np.random.default_rng(zlib.crc32(repr(key).encode())).standard_normal())


def _idx(p):
    return int(re.sub(r"\D", "", p)) % 1000


def _group(ds, p):
    if ds == "fau":
        return "th" if p == "P99" else ("th", "ha", "ci")[_idx(p) % 3]
    if ds == "federici":
        return p.split(":")[0]
    return "NH" if _idx(p) % 5 == 0 else "HA"


def r_value(ds, p, cf, key, effect, noise):
    """Synthetic true-query risk R (bits): identity base + content-fold offset - the arm's effect + deterministic noise."""
    return 3.0 + 0.1 * _idx(p) + 0.2 * (cf or 0) - effect + noise * _z(p, cf, key)


def _m(ll, nc, nq, rank=0.3):
    return {"top1": 0.2, "top5": 0.5, "mrr": 0.3, "rank_pct": rank, "logloss_bits": ll, "n_candidates": nc, "n_queries": nq}


def cont_eval(ds, sf, cf, key, effect, noise, nc=40, nq=20, kcs=False):
    pp, att = {}, {}
    for p in IDS[ds][sf]:
        r = r_value(ds, p, cf, key, effect, noise)
        pp[p] = {"group": _group(ds, p), "n_segments": nq, "unified/regular": _m(r, nc, nq, 0.3 - 0.01 * effect),
                 "unified/mismatched_eeg": _m(r + 1.0, nc, nq, 0.5), "unified/hard": _m(2.5 - effect, 9, nq),
                 "native/regular": _m(r + 0.1, nc, nq), "native/mismatched_eeg": _m(r + 1.1, nc, nq, 0.5), "native/hard": _m(2.6, 9, nq)}
        if kcs:
            pp[p]["kernel_dependence"] = {"cs_true_nats": 0.02, "cs_mismatched_nats": 0.02 - effect / 10,
                                          "cs_true_minus_mismatched": effect / 10, "n_rows": 256, "draws": 4}
        att[p] = {"unified": {"accuracy": 0.5 + effect / 4, "mean_margin": 0.01, "n": 10}, "native": {"accuracy": 0.5, "mean_margin": 0.0, "n": 10}}
    ev = {"per_participant": pp, "readout": {"alpha_unified": 1.0, "tau": {"unified": 0.1, "native": 0.1}, "n_test_candidates": nc}}
    if ds == "fau":
        ev["attention_2afc"] = att
    return ev


def priv_values(c, key, effect, noise):
    return (0.9 + 0.01 * _idx(c) - effect + noise * _z(c, key, "nll"), 0.6 + effect / 2 + noise * _z(c, key, "auc"),
            0.05 + effect + noise * _z(c, key, "hist"))


def priv_eval(sf, key, effect, noise):
    pp, nc = {}, {}
    for c in IDS["private_bdf"][sf]:
        nll, auc, hg = priv_values(c, key, effect, noise)
        pp[c] = {"group": _group("private_bdf", c), "n": 40, "head_auc": auc, "hist_gain_bits": hg, "hist_gain_twin_bits": 0.01,
                 "kernel_dependence": {"cs_true_nats": 0.0, "cs_mismatched_nats": 0.0, "cs_true_minus_mismatched": 0.0}}
        nc[c] = {"temperature": {"auc_score": auc, "nll_bits": nll + 0.01, "brier": 0.2, "gain_vs_base_bits": 0.0, "n": 40},
                 "positive_affine": {"auc_score": auc, "nll_bits": nll, "brier": 0.2, "gain_vs_base_bits": 0.0, "n": 40}}
    return {"per_participant": pp, "readout": {}, "native_calibration": {"per_participant": nc, "methods": {}, "calibration_set": "es",
                                                                         "n_calibration_trials": 100, "base_rate": 0.5}}


class Synth:
    """Plan rows + unit-record files of a synthetic E34_PUBLIC_PRIOR fleet: donor-group rows and records (pinned select.py
    layout), target / zero-shot rows (spec fields as design §4.3, slots as prior33.select) and E_LOCAL reference rows."""

    def __init__(self, tmp):
        self.dir = tmp / "units"
        self.dir.mkdir(parents=True, exist_ok=True)
        self.rows, self.n, self.groups = [], 0, {}

    def eid(self):
        self.n += 1
        return f"ALN3X_{self.n:016x}"

    def write(self, eid, rec, failed=False):
        (self.dir / (f"{eid}.FAILED.json" if failed else f"{eid}.json")).write_text(json.dumps(rec))

    def group(self, ds, obj="NCE", donor_seed=3401, block="core", ce=None, continuation_of=None, horizon_from=None, joint="rule",
              record=True, mutate=None):
        """A donor-group row and its complete record (CE_dev favours J1 unless `ce` says otherwise); returns its id."""
        key = (ds, obj, donor_seed, block, continuation_of, horizon_from)
        if key in self.groups:
            return self.groups[key]
        fam = GROUP_FAMILY[block]
        members = A.SEL.GROUP_MEMBERS[fam]
        if block in ("rich", "csx") and horizon_from is None:
            horizon_from = self.group(ds, obj, donor_seed, "core" if donor_seed == 3401 else "panel")
        gid = self.eid()
        spec = {**COMMON, "stage": "donor_group", "block": block, "seed_scope": "breadth" if donor_seed == 3401 else "panel",
                "objective": obj, "donor_seed": donor_seed, "sampler_seed": donor_seed, "target_seed": None, "members": list(members),
                "lambda_rule": A.SEL.LAMBDA_RULE,
                "budget": {"epoch_equivalents": 30, "continuation": f"group_wsd_any_last3_ext10_limit{60 if continuation_of is None else 90}_v1"}}
        if continuation_of:
            spec["continuation_of"] = continuation_of
        if horizon_from:
            spec["horizon_from"] = horizon_from
        row = {"experiment_id": gid, "family_id": fam, "dataset": ds, "subject_fold": None, "content_fold": None, "seed": donor_seed,
               "logical_dependencies": [x for x in (continuation_of, horizon_from) if x], "spec": spec}
        self.rows.append(row)
        if record:
            ce = {**{m: 7.5 for m in members}, **({"J1": 7.10, "J025": 7.30} if "J1" in members else {}), **(ce or {})}
            rec = {"experiment_id": gid, "row": row, "status": "complete", "code_hash": "d" * 16, "selection_level": LEVEL["donor_group"],
                   "members": {m: {"best": {"ce_dev": ce[m], "gain": 0.02, "ep_eq": 28.0}, "h30": {"ce_dev": ce[m] + 0.01, "gain": 0.019, "ep_eq": 30.0},
                                   "gainsel": {"ce_dev": ce[m] + 0.05, "gain": 0.025, "ep_eq": 25.0}, "steps": 80893, "nonfinite_steps": 0}
                               for m in members},
                   "horizon_ep_eq": 30, "ceiling_reached_while_improving": False}
            if "J1" in members:
                choice = A.SEL.lambda_choice(ce["J1"], ce["J025"])
                rec["joint_choice"] = {"rule": A.SEL.LAMBDA_RULE, "member": choice if joint == "rule" else joint,
                                       "ce_dev": {"J1": ce["J1"], "J025": ce["J025"]}, "tie_bits": 1e-4}
                rec["gain_rule"] = {"member": "J025"}
            if mutate is not None:
                mutate(row, rec)
            self.write(gid, rec)
        self.groups[key] = gid
        return gid

    def _spec(self, stage, ds, sf, cf, slot, obj, mode, seed, block, donor_seed, gid):
        s = {**COMMON, "block": block, "seed_scope": "breadth" if seed == 3401 else "panel", "objective": obj,
             "target": "current_class" if ds == "private_bdf" else "envelope", "target_contract": TC_SPEC, "split_hash": f"split-{ds}-{sf}-{cf}"}
        if stage == "target":
            s.update(stage="target", variant=slot, member=slot, init="random" if slot == "S" else "donor",
                     donor_seed=None if slot == "S" else donor_seed, sampler_seed=None if slot == "S" else donor_seed, target_seed=seed,
                     donor_group=gid)
        else:
            s.update(stage="zero_shot", variant=slot, member=slot, mode=mode, donor_seed=donor_seed, sampler_seed=donor_seed, target_seed=None,
                     donor_group=gid, bridge=f"B-{gid}-{slot}", job_kind="eval")
        return s

    def unit(self, stage, ds, slot, obj="NCE", mode="T", seed=3401, effect=0.0, noise=0.02, skip=(), fail=(), mutate=None,
             gainsel=None, unical=None, block=None, donor_seed=None, cells=None, group=None, level=None, member="auto"):
        """One configuration over its cells. level: None = the stage's declared text, False = not recorded, else that text.
        member: 'auto' = J* units record J1, None = nothing recorded, else that tag."""
        if stage == "zero_shot" and mode == "T":
            mode = "A"
        d_seed = donor_seed if donor_seed is not None else seed
        gid = None
        if stage in ("target", "zero_shot") and slot != "S":
            gid = group or self.group(ds, obj, d_seed, SLOT_BLOCK.get(slot) or ("core" if d_seed == 3401 else "panel"))
        rblock = block or SLOT_BLOCK.get(slot) or ("panel" if seed != 3401 else ("core" if mode in ("T", "A") else "access"))
        eids = []
        for sf, cf in cells or CELLS[ds]:
            eid = self.eid()
            if stage == "reference":
                row = {"experiment_id": eid, "family_id": "E_LOCAL", "dataset": ds, "subject_fold": sf, "content_fold": 0, "seed": seed,
                       "spec": {"architecture": "lag_local_tokens", "window": "full", "objective": obj, "projection_dim": 32,
                                "target": "current_class", "target_contract": "dense20ms_v1_pending_source_binding",
                                "information_stratum": "local_only"}}
            else:
                row = {"experiment_id": eid, "family_id": PREFIX + ("TARGET" if stage == "target" else "ZEROSHOT"), "dataset": ds,
                       "subject_fold": sf, "content_fold": cf, "seed": seed if stage == "target" else d_seed,
                       "logical_dependencies": [gid] if gid else [],
                       "spec": self._spec(stage, ds, sf, cf, slot, obj, mode, seed, rblock, d_seed, gid)}
            self.rows.append(row)
            eids.append(eid)
            if (sf, cf) in skip:
                continue
            key = (stage, slot, obj, mode, seed)
            if ds == "private_bdf":
                mk = lambda e, k=key, sf=sf: priv_eval(sf, k, e, noise)  # noqa: E731
            else:
                mk = lambda e, k=key, sf=sf, cf=cf: cont_eval(ds, sf, cf, k, e, noise, kcs=obj == "CS_SINGLE")  # noqa: E731
            rec = {"experiment_id": eid, "row": row, "status": "technical_failed" if (sf, cf) in fail else "complete",
                   "code_hash": "e" * 16 if stage == "reference" else "c" * 16,
                   "target_contract": "current_class" if stage == "reference" else TC_REC}
            if stage != "reference" and level is not False:
                default = LEVEL["zero_shot"] if stage == "zero_shot" else LEVEL["target_private" if ds == "private_bdf" else "target"]
                rec["selection_level"] = default if level is None else level
            if (sf, cf) in fail:
                rec["error"] = "synthetic failure"
            else:
                rec["eval"] = mk(effect)
                if member == "auto":
                    if slot == "J*":
                        rec["member_resolved"] = "J1"
                elif member is not None:
                    rec["member_resolved"] = member
                if gainsel == "identical":
                    rec["gainsel"] = "identical"
                elif gainsel is not None:
                    rec["eval_gainsel"] = mk(effect + gainsel)
                if unical is not None:
                    rec["eval_uni_cal"] = mk(effect + unical)
            if mutate is not None:
                mutate(sf, cf, row, rec)
            self.write(eid, rec, failed=(sf, cf) in fail)
        return eids

    def load(self):
        return A.load_records(self.rows, str(self.dir))


T_EFF = {"S": 0.0, "AP": 0.3, "XP": 0.1, "J*": 0.4, "XM": 0.0}
A_EFF = {"AP": 0.2, "XP": 0.1, "J*": 0.25, "XM": 0.0}


def core_fau(sy, obj="NCE", **kw):
    for slot, e in T_EFF.items():
        sy.unit("target", "fau", slot, obj=obj, effect=e, **kw.get(slot, {}))
    for slot, e in A_EFF.items():
        sy.unit("zero_shot", "fau", slot, obj=obj, mode="A", effect=e, unical=0.01, **kw.get("A" + slot, {}))


def run(sy, tmp, units=None, manifest=None):
    out = A.run_families(units if units is not None else sy.load(), manifest, out_json=str(tmp / "res" / A.JSON_NAME),
                         out_md=str(tmp / "docs" / A.MD_NAME), out_private=str(tmp / "priv" / A.PRIV_NAME))
    priv = json.loads((tmp / "priv" / A.PRIV_NAME).read_text())
    return out, priv


def md_of(tmp):
    return (tmp / "docs" / A.MD_NAME).read_text()


def expected_diff(ds, p, cells, ref, cand, mode="T", obj="NCE", seed=3401, stage="target", noise=0.02):
    """Hand computation: the identity's mean over the given cells of R(reference) - R(candidate)."""
    d = [r_value(ds, p, cf, (stage, ref[0], obj, mode, seed), ref[1], noise) - r_value(ds, p, cf, (stage, cand[0], obj, mode, seed), cand[1], noise)
         for sf, cf in cells if p in IDS[ds][sf]]
    return float(np.mean(d))


# ------------------------------------------------------------------------------------------------ identities
def test_probe_budget_is_parsed_but_excluded_from_production_summaries(tmp_path):
    sy = Synth(tmp_path)
    sy.unit("target", "fau", "S", noise=0.0,
            mutate=lambda sf, cf, row, rec: rec.update(truncated={"epochs": 2}, epochs_override=2))
    units = sy.load()
    assert units and all(u["status"] == "probe_truncated" for u in units)
    assert all(u["views"]["primary"]["rows"] for u in units)
    values = A.identity_values(units)
    assert values == {}


def test_identity_aggregation_over_cells_and_content_folds(tmp_path):
    sy = Synth(tmp_path)
    sy.unit("target", "fau", "S", noise=0.0)
    sy.unit("target", "federici", "S", noise=0.0)
    units = sy.load()
    assert len(units) == 6 and all(u["status"] == "complete" for u in units)
    iv = A.identity_values(units, MANIFEST)
    fau = iv[A.cfg("fau", "NCE", "T", "S", 3401)]
    ids = fau["identities"]
    assert len(ids) == 13  # 6 + 6 test identities + P99, tested in both subject folds, counted once
    for p, d in ids.items():
        # mean over the identity's units: content folds 0 (+0) and 1 (+0.2); P99's four units (2 outer x 2 content folds)
        assert d["values"][A.PRIMARY] == pytest.approx(3.0 + 0.1 * _idx(p) + 0.1, abs=1e-12)
        assert d["n_units"] == (4 if p == "P99" else 2)
    assert {ids[p]["group"] for p in ids} == {"TH", "HA", "CI"} and fau["info"]["units"] == 4
    fed = iv[A.cfg("federici", "NCE", "T", "S", 3401)]
    assert set(fed["identities"]) == {"HC:1001", "HC-v:1001", "CI:0002", "HC:1003", "HC:1004", "HC-v:1004", "CI:0005", "HC:1006"}
    assert fed["identities"]["HC-v:1001"]["group"] == "HC-v" and fed["identities"]["HC:1001"]["group"] == "HC"  # independent identities
    assert fed["info"]["phantom_records"] == 2 and fed["info"]["phantom_entities"] == {"Artifact"}  # excluded, counted
    with pytest.raises(KeyError):  # a Federici record outside the entity manifest is an error, never a guess
        A.identity_values(units, {k: v for k, v in MANIFEST.items() if k != "CI:0005"})


def test_donor_reuse_and_repeated_evaluations_do_not_add_n(tmp_path):
    sy = Synth(tmp_path)
    core_fau(sy)
    units = sy.load()
    ap = [u for u in units if u["stage"] == "target" and u["slot"] == "AP"]
    assert len(ap) == 4 and len({u["donor_group"] for u in ap}) == 1  # one donor member serves every cell of its target
    zs = [u for u in units if u["stage"] == "zero_shot" and u["slot"] == "AP"]
    assert len({(u["donor_group"], u["bridge"]) for u in zs}) == 1  # one donor + bridge across the content folds
    out, priv = run(sy, tmp_path, units)
    lab, metric = "INIT|fau|NCE|T|s3401", A.PRIMARY
    m = out["families"][f"{lab}|R"]["members"]["S->AP"]
    assert m["n"] == 13 and m["n_paired"] == 13 and m["pairing"]["cells_matched"] == 4  # 4 cells x 7 records -> 13 identities
    assert m["family_set"]["n"] == 13 and out["families"][f"{lab}|R"]["maxt"]["n"] == 13
    # the interval is the identity bootstrap over these 13 values (not 28 unit rows, not 4 cells)
    d = priv["paired_differences"][f"{lab}|{metric}"]["S->AP"]
    assert len(d) == 13 and d["P99"]["n_units"] == 4 and d["P00"]["n_units"] == 2
    y = np.array([d[i]["diff"] for i in sorted(d)])
    s = S.summary(y, idx=S.draws(len(y), S.NB, S.group_seed(lab, metric)))
    assert m["est"] == pytest.approx(float(s["est"]), abs=1e-12) and m["ci_low"] == pytest.approx(float(s["ci_low"]), abs=1e-12)
    assert m["family_set"]["ci_low"] == pytest.approx(m["ci_low"], abs=1e-12)  # own identities = the family set: same draws
    z = out["families"]["SUPERVISION|fau|NCE|A|s3401|R"]["members"]["AP->J*"]
    assert z["n"] == 13 and z["pairing"]["cells_matched"] == 4
    zd = priv["paired_differences"][f"SUPERVISION|fau|NCE|A|s3401|{metric}"]["AP->J*"]["P03"]
    want = expected_diff("fau", "P03", CELLS["fau"], ("AP", 0.2), ("J*", 0.25), mode="A", stage="zero_shot")
    assert zd["n_units"] == 2 and zd["diff"] == pytest.approx(want, abs=1e-12)  # zero-shot content folds averaged into one value
    assert out["meta"]["bootstrap_scope"] == "conditional_on_available_fitted_models_not_full_training_population"
    assert any("not independent samples" in s for s in out["meta"]["statements"])


# ------------------------------------------------------------------------------------------------ effects and max-t
def test_known_effects_signs_and_family_maxt(tmp_path):
    sy = Synth(tmp_path)
    core_fau(sy)
    out, priv = run(sy, tmp_path)
    F = out["families"]
    init = F["INIT|fau|NCE|T|s3401|R"]["members"]
    assert init["S->AP"]["est"] == pytest.approx(0.3, abs=0.03) and init["S->AP"]["family_set"]["sim_position"] == "above 0"
    assert init["S->J*"]["est"] == pytest.approx(0.4, abs=0.03) and abs(init["S->XM"]["est"]) < 0.03
    sup = F["SUPERVISION|fau|NCE|T|s3401|R"]["members"]
    assert sup["AP->XP"]["est"] == pytest.approx(-0.2, abs=0.03) and sup["AP->XP"]["family_set"]["sim_position"] == "below 0"
    assert sup["XP->J*"]["est"] == pytest.approx(0.3, abs=0.03)
    assert F["CONTROL|fau|NCE|T|s3401|R"]["members"]["XM->J*"]["est"] == pytest.approx(0.4, abs=0.03)
    assert F["SUPERVISION|fau|NCE|A|s3401|R"]["members"]["AP->XP"]["est"] == pytest.approx(-0.1, abs=0.03)
    n_checked = 0
    for f in F.values():
        for m in f["members"].values():
            fs = m.get("family_set")
            if fs:
                n_checked += 1
                assert fs["sim_low"] <= fs["ci_low"] + 1e-12 and fs["sim_high"] >= fs["ci_high"] - 1e-12  # family ⊇ pointwise
                assert f["maxt"]["crit"] * fs["se"] >= (fs["ci_high"] - fs["est"]) - 1e-12
                assert fs["pct_low"] <= fs["est"] <= fs["pct_high"]
    assert n_checked >= 10
    # the family max-t is reproduced from sci_r1.stats with shared replicate indices on the common identities
    lab, metric = "INIT|fau|NCE|T|s3401", A.PRIMARY
    D = priv["paired_differences"][f"{lab}|{metric}"]
    common = sorted(set.intersection(*(set(v) for v in D.values())))
    idx = S.draws(len(common), S.NB, S.group_seed(lab, metric))
    items = {}
    for name, v in D.items():
        s = S.summary(np.array([v[i]["diff"] for i in common]), idx=idx)
        items[name] = (s["est"], s["se"], s["T"])
    fm = S.family_maxt(items)
    mx = F[f"{lab}|R"]["maxt"]
    assert mx["crit"] == pytest.approx(fm["crit"], abs=1e-12) and mx["n_members"] == 4 == mx["n_declared"]
    assert mx["members"] == ["S->AP", "S->XP", "S->J*", "S->XM"] and mx["n"] == 13
    for name, iv in fm["intervals"].items():
        assert F[f"{lab}|R"]["members"][name]["family_set"]["sim_low"] == pytest.approx(iv["sim_low"], abs=1e-12)
    # pointwise-only sections carry no simultaneous interval
    assert all("family_set" not in m for f in out["secondary"].values() for e in f["endpoints"].values() for m in e["members"].values())
    sec = out["secondary"]["INIT|fau|NCE|T|s3401"]["endpoints"]
    assert sec["att_acc"]["members"]["S->AP"]["est"] == pytest.approx(0.075, abs=1e-9)  # accuracy: candidate - reference
    assert sec["gain"]["members"]["S->AP"]["est"] == pytest.approx(0.0, abs=1e-9)
    assert sec["hard_gain"]["members"]["S->AP"]["est"] == pytest.approx(0.3, abs=1e-9)
    # R_mm is a risk: Δ = R_mm(reference) − R_mm(candidate); here R_mm = R + 1 bit, so ΔR_mm equals ΔR exactly
    assert sec["R_mm"]["direction_text"] == "ref − cand"
    assert sec["R_mm"]["members"]["S->AP"]["est"] == pytest.approx(init["S->AP"]["est"], abs=1e-12)
    assert sec["R_mm"]["members"]["S->AP"]["est"] > 0
    assert "kernel_cs_diff" not in sec  # CS_SINGLE only


# ------------------------------------------------------------------------------------------------ missing pairs
def test_missing_pairs_listed_never_zero_filled(tmp_path):
    def wrong_split(sf, cf, row, rec):
        if (sf, cf) == (0, 0):
            row["spec"]["split_hash"] = "planted-mismatch"

    def count_mismatch(sf, cf, row, rec):
        if (sf, cf) == (0, 1):
            rec["eval"]["per_participant"]["P02"]["unified/regular"]["n_candidates"] = 39

    sy = Synth(tmp_path)
    core_fau(sy, AP={"skip": [(1, 1)]}, XP={"fail": [(1, 0)]}, XM={"mutate": wrong_split}, **{"J*": {"mutate": count_mismatch}})
    units = sy.load()
    st = {(u["slot"], u["subject_fold"], u["content_fold"]): u["status"] for u in units if u["stage"] == "target"}
    assert st[("AP", 1, 1)] == "missing" and st[("XP", 1, 0)] == "technical_failed"
    out, priv = run(sy, tmp_path, units)
    fam = out["families"]["INIT|fau|NCE|T|s3401|R"]
    m = fam["members"]
    assert m["S->AP"]["pairing"]["cells_missing"] == [{"cell": [1, 1], "reference": "complete", "candidate": "missing"}]
    assert m["S->AP"]["pairing"]["cells_unregistered"] == []
    assert m["S->AP"]["n_paired"] == 13 and m["S->AP"]["pairing"]["identities_partial"] == 7  # outer fold 1 + P99 on 1 of their units
    assert m["S->XP"]["pairing"]["cells_missing"] == [{"cell": [1, 0], "reference": "complete", "candidate": "technical_failed"}]
    assert m["S->XM"]["pairing"]["cells_excluded"] == [{"cell": [0, 0], "reason": "split_hash differs"}]
    assert m["S->J*"]["pairing"]["cells_excluded"] == [{"cell": [0, 1], "reason": "candidate / query counts differ (1 participants)"}]
    # the identity values are the means over the matched units only: hand-computed, never a zero for the missing unit
    D = priv["paired_differences"]["INIT|fau|NCE|T|s3401|" + A.PRIMARY]["S->AP"]
    matched = [(0, 0), (0, 1), (1, 0)]
    for p, v in D.items():
        assert v["diff"] == pytest.approx(expected_diff("fau", p, matched, ("S", 0.0), ("AP", 0.3)), abs=1e-12)
        assert v["n_units"] == sum(p in IDS["fau"][sf] for sf, _ in matched)
    nc = {(x["slot"], tuple(x["cell"])): x["status"] for x in out["coverage"]["not_complete"]}
    assert nc == {("AP", (1, 1)): "missing", ("XP", (1, 0)): "technical_failed"}
    ex = {(e["member"], tuple(e["cell"]), e["reason"]) for e in out["pairing"]["cell_pairs_excluded"]}
    assert ("S->XM", (0, 0), "split_hash differs") in ex
    assert any(e["member"] == "S->AP" and e["cell"] == [1, 1] for e in out["pairing"]["cell_pairs_missing"])
    # the J* unit of cell (0, 1) disagrees with the cell's other mode-T units: the pool check cannot verify that cell's
    # zero-shot units, which leave every zero-shot family with the reason
    q = out["pairing"]["pool_check"]
    assert [d["cell"] for d in q["cells_t_disagree"]] == [[0, 1]] and q["cells_t_disagree"][0]["differs_in"] == ["candidate / query counts"]
    assert len(q["zero_shot_units_excluded"]) == 4 and {e["cell"][1] for e in q["zero_shot_units_excluded"]} == {1}
    za = out["families"]["SUPERVISION|fau|NCE|A|s3401|R"]["members"]["AP->XP"]["pairing"]
    assert za["cells_matched"] == 3 and "mode-T units disagree" in za["cells_excluded"][0]["reason"]

    # both outer-fold-1 AP units missing: those identities leave the AP members (no zero-fill); pointwise n stays each
    # member's own, the family set (and so the simultaneous intervals) shrinks to the identities common to all members
    sy2 = Synth(tmp_path / "b")
    core_fau(sy2, AP={"skip": [(1, 0), (1, 1)]})
    out2, priv2 = run(sy2, tmp_path / "b")
    f2 = out2["families"]["INIT|fau|NCE|T|s3401|R"]
    m2 = f2["members"]
    assert m2["S->AP"]["n_paired"] == 7 and m2["S->AP"]["pairing"]["identities_unpaired"] == 6
    assert m2["S->XP"]["n"] == 13 and m2["S->XP"]["family_set"]["n"] == 7 and f2["maxt"]["n"] == 7
    D2 = priv2["paired_differences"]["INIT|fau|NCE|T|s3401|" + A.PRIMARY]["S->AP"]
    assert set(D2) == set(IDS["fau"][0]) and not set(D2) & set(IDS["fau"][1][:-1])
    want = np.mean([expected_diff("fau", p, [(0, 0), (0, 1)], ("S", 0.0), ("AP", 0.3)) for p in sorted(D2)])
    assert m2["S->AP"]["est"] == pytest.approx(want, abs=1e-12)


def test_unregistered_sides_labelled_separately(tmp_path):
    sy = Synth(tmp_path)
    sy.unit("target", "fau", "S")
    sy.unit("target", "fau", "AP", effect=0.3, skip=[(1, 1)])  # plan row without a record: missing
    sy.unit("target", "fau", "XP", effect=0.1, cells=[(0, 0), (0, 1), (1, 0)])  # no plan row for cell (1, 1): unregistered
    out, _ = run(sy, tmp_path)
    m = out["families"]["INIT|fau|NCE|T|s3401|R"]["members"]
    assert m["S->AP"]["pairing"]["cells_missing"] == [{"cell": [1, 1], "reference": "complete", "candidate": "missing"}]
    assert m["S->XP"]["pairing"]["cells_unregistered"] == [{"cell": [1, 1], "reference": "complete", "candidate": "unregistered"}]
    assert m["S->XP"]["pairing"]["cells_missing"] == [] and m["S->XP"]["n"] == 13
    assert m["S->XM"]["status"] == "not registered (reference 4 units, candidate 0 units)" and "est" not in m["S->XM"]
    assert len(m["S->XM"]["pairing"]["cells_unregistered"]) == 4 and m["S->XM"]["family_note"] == "not in the max-t: no paired identities"
    mx = out["families"]["INIT|fau|NCE|T|s3401|R"]["maxt"]
    assert mx["n_members"] == 2 and mx["n_declared"] == 4 and mx["members"] == ["S->AP", "S->XP"]  # the max-t names who is in it
    assert out["families"]["RICH|dtu|CS_SINGLE|A|s3401|R"]["members"]["AP->APR"]["status"].startswith("not registered")
    P = out["pairing"]
    assert [(e["family"], e["member"], e["cell"]) for e in P["cell_pairs_missing"]] == [("INIT|fau|NCE|T|s3401", "S->AP", [1, 1])]
    assert any(e["member"] == "S->XP" and e["cell"] == [1, 1] for e in P["cell_pairs_unregistered"])
    assert any(e["family"] == "RICH|fau|NCE|T|s3401" and e["candidate"] == "unregistered" for e in P["cell_pairs_unregistered"])
    md = md_of(tmp_path)
    assert "with a missing or incomplete side (a plan row without a complete record or evaluation): 1," in md
    assert f"with an unregistered side (no plan row): {len(P['cell_pairs_unregistered'])}" in md


# ------------------------------------------------------------------------------------------------ no p-values
def test_no_p_values_anywhere(tmp_path):
    sy = Synth(tmp_path)
    core_fau(sy)
    for slot, e in T_EFF.items():
        sy.unit("target", "private_bdf", slot, effect=e / 3)
    out, priv = run(sy, tmp_path)
    keys, lengths = [], []

    def walk(x):
        if isinstance(x, dict):
            for k, v in x.items():
                keys.append(str(k))
                walk(v)
        elif isinstance(x, list):
            lengths.append(len(x))
            for v in x:
                walk(v)
    for obj in (json.loads((tmp_path / "res" / A.JSON_NAME).read_text()), priv):
        walk(obj)
    bad = [k for k in keys if re.fullmatch(r"(?i)p|p[_-]?val(ue)?s?|pval.*|p_.*|.*_p|q[_-]?val(ue)?", k)]
    assert not bad, bad
    assert S.NB not in lengths  # bootstrap replicate arrays never leave the computation
    md = md_of(tmp_path)
    js = (tmp_path / "res" / A.JSON_NAME).read_text()
    for txt in (md, js):
        assert not re.search(r"(?i)\bp\s*[=<>≤≥]\s*[0-9.]", txt)
        assert not re.search(r"(?i)p[-_ ]?value\s*[=:]", txt)
    assert "No p-values are computed or reported" in md and "seed 3401 only" in md


# ------------------------------------------------------------------------------------------------ private metrics and the panel
def test_private_metrics_panel_and_native_reference(tmp_path):
    sy = Synth(tmp_path)
    effects = {"S": 0.0, "AP": 0.12, "XP": 0.06, "J*": 0.15, "XM": 0.0}
    for seed in A.ALL_SEEDS:
        for slot, e in effects.items():
            if slot == "XM" and seed == 3413:
                continue  # no XM at seed 3413: incomplete common seed set
            sy.unit("target", "private_bdf", slot, seed=seed, effect=e + 0.01 * (seed - 3401) / 6, noise=0.01)
        sy.unit("reference", "private_bdf", "E_LOCAL", seed=seed, effect=-0.05, noise=0.01)
    units = sy.load()
    loc = [u for u in units if u["stage"] == "reference"]
    assert len(loc) == 6 and all(u["slot"] == "E_LOCAL" and u["target_seed"] in A.ALL_SEEDS for u in loc)
    out, priv = run(sy, tmp_path, units)
    F = out["families"]
    nll, auc = F["INIT|private_bdf|NCE|T|s3401|NLL"]["members"], F["INIT|private_bdf|NCE|T|s3401|AUC"]["members"]
    assert nll["S->AP"]["n"] == 10 and nll["S->AP"]["est"] == pytest.approx(0.12, abs=0.015)  # NLL(ref) - NLL(cand)
    assert auc["S->AP"]["est"] == pytest.approx(0.06, abs=0.015)  # AUC(cand) - AUC(ref)
    assert nll["S->AP"]["family_set"]["sim_position"] == "above 0" and "sim_low" in auc["S->AP"]["family_set"]
    assert F["SUPERVISION|private_bdf|NCE|T|s3401|NLL"]["members"]["AP->XP"]["est"] == pytest.approx(-0.06, abs=0.015)
    m13 = F["INIT|private_bdf|NCE|T|s3413|NLL"]
    assert m13["maxt"]["n_members"] == 3 and m13["members"]["S->XM"]["family_note"] == "not in the max-t: no paired identities"
    sec = out["secondary"]["INIT|private_bdf|NCE|T|s3401"]["endpoints"]
    assert sec["hist_gain"]["members"]["S->AP"]["est"] == pytest.approx(0.12, abs=0.015) and "family_set" not in sec["hist_gain"]["members"]["S->AP"]
    assert sec["twin_sens"]["members"]["S->AP"]["n"] == 10
    lev = out["levels"]["private_bdf|NCE|T|S|d-|t3401|primary"]["endpoints"]["NLL"]
    assert lev["n"] == 10 and lev["groups"]["HA"]["n"] == 8 and "pct_low" in lev["groups"]["HA"] and lev["groups"]["NH"] == {"n": 2}
    # panel: per-seed families, the three-seed identity means and the incomplete seed set
    p3e = out["panel"]["three_seed"]["PANEL3|INIT|private_bdf|NCE|T|NLL"]
    p3 = p3e["members"]
    ap = p3["S->AP"]
    assert set(ap["per_seed"]) == {"3401", "3407", "3413"} and all(v is not None for v in ap["per_seed"].values())
    ests = [ap["per_seed"][str(s)] for s in A.ALL_SEEDS]
    assert ap["mean"] == pytest.approx(np.mean(ests)) and ap["range"] == [min(ests), max(ests)]
    assert ap["sd"] == pytest.approx(np.std(ests, ddof=1))
    D = {s: priv["paired_differences"][f"INIT|private_bdf|NCE|T|s{s}|NLL"]["S->AP"] for s in A.ALL_SEEDS}
    y3 = [np.mean([D[s][c]["diff"] for s in A.ALL_SEEDS]) for c in sorted(D[3401])]
    assert ap["three_seed"]["n"] == 10 and ap["three_seed"]["est"] == pytest.approx(np.mean(y3), abs=1e-12)
    assert "sim_low" in ap["three_seed"]["family_set"]
    assert p3["S->XM"]["three_seed_status"] == "incomplete common seed set: available [3401, 3407], missing [3413]"
    assert p3["S->XM"]["per_seed"]["3413"] is None and p3["S->XM"]["per_seed"]["3407"] is not None
    # the simultaneous family of the three-seed values covers 3 of the 4 declared members, and says so
    assert p3e["maxt"]["n_members"] == 3 and p3e["maxt"]["n_declared"] == 4 and "S->XM" not in p3e["maxt"]["members"]
    c3 = out["panel"]["three_seed"]["PANEL3|CONTROL|private_bdf|NCE|T|AUC"]["members"]
    assert all(r["three_seed_status"].startswith("incomplete") for r in c3.values())
    assert F["INIT|private_bdf|NCE|T|s3407|NLL"]["block"] == "panel" and F["INIT|private_bdf|NCE|T|s3407|NLL"]["seed_label"] == "panel seed 3407"
    # the E_LOCAL native reference: a different-input-contract reference, descriptive and pointwise
    nr = out["panel"]["native_reference"]["NATIVE_REF|private_bdf|NCE|T|s3401|NLL"]
    # E_LOCAL is 0.05 bits worse than S here, so E_LOCAL -> S = NLL(E_LOCAL) - NLL(S) = +0.05, E_LOCAL -> AP = +0.17
    assert nr["members"]["E_LOCAL->S"]["n"] == 10 and nr["members"]["E_LOCAL->S"]["est"] == pytest.approx(0.05, abs=0.015)
    assert "family_set" not in nr["members"]["E_LOCAL->S"] and nr["members"]["E_LOCAL->AP"]["est"] == pytest.approx(0.17, abs=0.015)
    assert out["panel"]["native_reference_three_seed"]["NATIVE_REF3|private_bdf|NCE|T|NLL"]["members"]["E_LOCAL->S"]["n"] == 10
    md = md_of(tmp_path)
    assert "PANEL3 INIT · NCE · T (NLL, ref − cand): simultaneous over 3 of 4 declared members" in md
    assert "panel · private_bdf (mode T, panel seed 3407) · ΔNLL (ref − cand)" in md
    # privacy: no child id in the public outputs; the per-identity file is private
    for name in (tmp_path / "res" / A.JSON_NAME, tmp_path / "docs" / A.MD_NAME):
        txt = name.read_text()
        assert not any(re.search(rf"\b{c}\b", txt) for f in IDS["private_bdf"].values() for c in f)
    pf = tmp_path / "priv" / A.PRIV_NAME
    assert stat.S_IMODE(os.stat(pf).st_mode) == 0o600 and stat.S_IMODE(os.stat(pf.parent).st_mode) == 0o700
    assert "kid03" in pf.read_text()


# ------------------------------------------------------------------------------------------------ modes, pools, seeds
def test_access_modes_kept_separate(tmp_path):
    def few_candidates(sf, cf, row, rec):
        if (sf, cf) == (0, 0):
            rec["eval"]["readout"]["n_test_candidates"] = 39

    sy = Synth(tmp_path)
    core_fau(sy)
    for slot, eb in (("AP", -0.1), ("XP", 0.0), ("J*", 0.1)):
        sy.unit("zero_shot", "fau", slot, mode="B", effect=eb)
        sy.unit("zero_shot", "fau", slot, mode="C", effect=eb - 0.2, mutate=few_candidates if slot == "XP" else None)
    units = sy.load()
    assert {u["mode"] for u in units if u["stage"] == "zero_shot"} == {"A", "B", "C"}
    iv = A.identity_values(units)
    assert {c[2] for c in iv if c[3] == "AP"} == {"T", "A", "B", "C"}  # separate configurations, never pooled
    out, _ = run(sy, tmp_path, units)
    sup = out["families"]["SUPERVISION|fau|NCE|A|s3401|R"]["members"]["AP->XP"]
    assert sup["est"] == pytest.approx(-0.1, abs=0.03)  # mode-A values only
    acc = out["access"]["ACCESS|fau|NCE|A->B|s3401|R"]["members"]
    assert acc["AP"]["est"] == pytest.approx(-0.3, abs=0.03) and acc["J*"]["est"] == pytest.approx(-0.15, abs=0.03)  # R(A) - R(B)
    assert all("family_set" not in m for m in acc.values()) and "maxt" not in out["access"]["ACCESS|fau|NCE|A->B|s3401|R"]
    xc = out["access"]["ACCESS|fau|NCE|A->C|s3401|R"]["members"]["XP"]["pairing"]["cells_excluded"]
    assert len(xc) == 1 and xc[0]["cell"] == [0, 0]
    assert xc[0]["reason"].endswith("excluded: zero-shot pool differs from the cell's mode-T units: n_test_candidates (39 vs 40)")
    q = out["pairing"]["pool_check"]
    assert q["cells_with_t_and_zero_shot"] == 4 and q["zero_shot_units_checked"] == 40 and q["zero_shot_units_verified"] == 39
    assert [(e["configuration"], e["cell"]) for e in q["zero_shot_units_excluded"]] == [("fau|NCE|C|XP|d3401|t-|primary", [0, 0])]
    assert q["cells_t_disagree"] == []
    for f in out["families"].values():  # mode T and zero-shot values are never contrasted
        for m in f["members"].values():
            assert m["reference"].split("|")[2] == m["candidate"].split("|")[2] == f["mode"]
    na = out["secondary"]["SUPERVISION|fau|NCE|A|s3401"]["endpoints"]["R_native"]["members"]
    assert na["AP->XP"]["status"].startswith("not applicable") and na["AP->J*"]["n"] == 13
    assert out["secondary"]["SUPERVISION|fau|NCE|T|s3401"]["endpoints"]["R_native"]["members"]["AP->XP"]["n"] == 13
    sens = out["families"]["SUPERVISION|fau|NCE|A|s3401|R"]["sensitivity_uni_cal"]["members"]["AP->XP"]
    assert sens["est"] == pytest.approx(-0.1, abs=0.03) and "family_set" not in sens


def test_pool_check_uses_the_mode_T_units_as_reference(tmp_path):
    def n39(sf, cf, row, rec):
        if (sf, cf) == (0, 0):
            rec["eval"]["readout"]["n_test_candidates"] = 39

    # the reviewer's case: every zero-shot unit of cell (0, 0) (A 4, B 3, C 3) differs from the five mode-T units
    sy = Synth(tmp_path)
    for slot, e in T_EFF.items():
        sy.unit("target", "fau", slot, effect=e)
    for slot, e in A_EFF.items():
        sy.unit("zero_shot", "fau", slot, mode="A", effect=e, unical=0.01, mutate=n39)
    for slot in ("AP", "XP", "J*"):
        sy.unit("zero_shot", "fau", slot, mode="B", effect=0.0, mutate=n39)
        sy.unit("zero_shot", "fau", slot, mode="C", effect=0.0, mutate=n39)
    out, _ = run(sy, tmp_path)
    q = out["pairing"]["pool_check"]
    assert len(q["zero_shot_units_excluded"]) == 10 and all(e["cell"] == [0, 0] for e in q["zero_shot_units_excluded"])
    assert all(e["reason"] == "zero-shot pool differs from the cell's mode-T units: n_test_candidates (39 vs 40)"
               for e in q["zero_shot_units_excluded"])
    assert q["cells_t_disagree"] == [] and not any(e["configuration"].split("|")[2] == "T" for e in q["zero_shot_units_excluded"])
    for key, name in (("SUPERVISION|fau|NCE|A|s3401|R", "AP->XP"), ("CONTROL|fau|NCE|A|s3401|R", "XM->J*")):
        p = out["families"][key]["members"][name]["pairing"]
        assert p["cells_matched"] == 3 and [e["cell"] for e in p["cells_excluded"]] == [[0, 0]]
        assert "zero-shot pool differs" in p["cells_excluded"][0]["reason"]
        sp = out["families"][key]["sensitivity_uni_cal"]["members"][name]["pairing"]
        assert sp["cells_matched"] == 3 and [e["cell"] for e in sp["cells_excluded"]] == [[0, 0]]
    assert out["access"]["ACCESS|fau|NCE|A->B|s3401|R"]["members"]["AP"]["pairing"]["cells_matched"] == 3
    assert out["families"]["INIT|fau|NCE|T|s3401|R"]["members"]["S->AP"]["pairing"]["cells_matched"] == 4  # mode T untouched
    ident = out["coverage"]["identities"]["fau|NCE|A|AP|d3401|t-|primary"]
    assert ident["units"] == 3 and ident["units_excluded"] == 1 and ident["n"] == 13  # outer fold 0 stays via content fold 1
    row = [r for r in out["coverage"]["by_configuration"] if r["stage"] == "zero_shot" and r["mode"] == "B" and r["slot"] == "AP"][0]
    assert row["complete"] == 4 and row["excluded"] == 1
    assert len(out["pairing"]["units_excluded"]) == 10 and "unit excluded:" in md_of(tmp_path)

    # mode-T units that disagree with each other, and a cell without any mode-T unit
    def n41(sf, cf, row, rec):
        if (sf, cf) == (1, 0):
            rec["eval"]["readout"]["n_test_candidates"] = 41

    sy2 = Synth(tmp_path / "b")
    for slot, e in T_EFF.items():
        sy2.unit("target", "fau", slot, effect=e, skip=[(1, 1)], mutate=n41 if slot == "XM" else None)
    for slot, e in A_EFF.items():
        sy2.unit("zero_shot", "fau", slot, mode="A", effect=e)
    out2, _ = run(sy2, tmp_path / "b")
    q2 = out2["pairing"]["pool_check"]
    assert [d["cell"] for d in q2["cells_t_disagree"]] == [[1, 0]] and q2["cells_t_disagree"][0]["differs_in"] == ["n_test_candidates"]
    assert {e["cell"][0] for e in q2["zero_shot_units_excluded"]} == {1} and len(q2["zero_shot_units_excluded"]) == 4
    assert all("mode-T units disagree" in e["reason"] for e in q2["zero_shot_units_excluded"])
    assert [e["cell"] for e in q2["zero_shot_units_unverified"]] == [[1, 1]] * 4  # listed, kept
    p = out2["families"]["SUPERVISION|fau|NCE|A|s3401|R"]["members"]["AP->XP"]["pairing"]
    assert p["cells_matched"] == 3 and [e["cell"] for e in p["cells_excluded"]] == [[1, 0]]
    ix = out2["families"]["INIT|fau|NCE|T|s3401|R"]["members"]["S->XM"]["pairing"]["cells_excluded"]
    assert ix == [{"cell": [1, 0], "reason": "n_test_candidates differ (40 vs 41)"}]


def test_donor_and_target_seeds_recorded_separately(tmp_path):
    def other_donor(sf, cf, row, rec):
        if (sf, cf) == (0, 0):
            row["spec"]["donor_seed"] = 3407

    sy = Synth(tmp_path)
    core_fau(sy, XP={"mutate": other_donor})
    units = sy.load()
    keys = {A.ckey(A.config_of(u)) for u in units if u["stage"] in ("target", "zero_shot")}
    assert {"fau|NCE|T|S|d-|t3401|primary", "fau|NCE|T|AP|d3401|t3401|primary", "fau|NCE|A|AP|d3401|t-|primary",
            "fau|NCE|T|XP|d3407|t3401|primary"} <= keys
    out, _ = run(sy, tmp_path, units)
    lv = out["levels"]
    assert (lv["fau|NCE|T|S|d-|t3401|primary"]["donor_seed"], lv["fau|NCE|T|S|d-|t3401|primary"]["target_seed"]) == (None, 3401)
    assert (lv["fau|NCE|A|AP|d3401|t-|primary"]["donor_seed"], lv["fau|NCE|A|AP|d3401|t-|primary"]["target_seed"]) == (3401, None)
    assert lv["fau|NCE|T|XP|d3407|t3401|primary"]["n"] == 7  # the odd-seed unit (cell 0/0: 7 records) stays its own configuration
    m = out["families"]["SUPERVISION|fau|NCE|T|s3401|R"]["members"]["AP->XP"]
    assert m["pairing"]["cells_unregistered"] == [{"cell": [0, 0], "reference": "complete", "candidate": "unregistered"}]
    assert out["families"]["INIT|fau|NCE|T|s3401|R"]["allowed_differences"] == ["donor_seed"]


# ------------------------------------------------------------------------------------------------ execution versions
def test_execution_versions_from_donor_groups(tmp_path):
    def row_label(sf, cf, row, rec):
        row["spec"]["continuation_of"] = "ALN3X_" + "f" * 16  # a per-row label written by the plan builder: not a key

    def zs_label(sf, cf, row, rec):
        row["spec"]["version"] = "cont-label"

    sy = Synth(tmp_path)
    core_fau(sy)
    g0 = sy.group("fau")
    g1 = sy.group("fau", continuation_of=g0)  # continuation of the core group: new ids for it and its downstream rows
    for slot in ("AP", "XP", "J*", "XM"):
        sy.unit("target", "fau", slot, effect=T_EFF[slot] + 0.1, group=g1, mutate=row_label)
        sy.unit("zero_shot", "fau", slot, mode="A", effect=A_EFF[slot] + 0.05, group=g1, mutate=zs_label)
    r0 = sy.group("fau", block="rich")  # horizon from g0
    r1 = sy.group("fau", block="rich", continuation_of=r0, horizon_from=g1)
    sy.unit("target", "fau", "APR", effect=0.35)
    sy.unit("target", "fau", "APR", effect=0.45, group=r1)
    units = sy.load()
    ver = {u["eid"]: u["version"] for u in units}
    assert ver[g0] == ver[r0] == "primary" and ver[g1] == ver[r1] == "continuation_1"
    assert {u["version"] for u in units if u["slot"] == "S"} == {"primary"}  # S is never re-registered
    out, priv = run(sy, tmp_path, units)
    F = out["families"]
    assert out["meta"]["versions_order"] == ["primary", "continuation_1"]
    vi = {x["version"]: x for x in out["meta"]["versions"]}
    assert vi["continuation_1"]["donor_groups"] == 2 and vi["continuation_1"]["compute_limits"] == [90]
    assert vi["continuation_1"]["downstream_rows_with_continuation_of"] == 16 and vi["continuation_1"]["explicit_labels"] == {"cont-label": 16}
    assert vi["primary"]["compute_limits"] == [60]
    # INIT at the continuation: continuation arms against the primary S rows (the only allowed version difference)
    ic = F["INIT|fau|NCE|T|s3401|continuation_1|R"]
    assert ic["reference_version"] == "primary" and "version" in ic["allowed_differences"]
    assert ic["members"]["S->AP"]["pairing"]["cells_matched"] == 4 and ic["members"]["S->AP"]["est"] == pytest.approx(0.4, abs=0.03)
    assert ic["members"]["S->AP"]["reference"] == "fau|NCE|T|S|d-|t3401|primary"
    assert F["INIT|fau|NCE|T|s3401|R"]["members"]["S->AP"]["est"] == pytest.approx(0.3, abs=0.03)  # primary unchanged
    assert "version" not in F["INIT|fau|NCE|T|s3401|R"]["allowed_differences"]
    assert F["SUPERVISION|fau|NCE|T|s3401|continuation_1|R"]["members"]["AP->XP"]["est"] == pytest.approx(-0.2, abs=0.03)
    assert F["SUPERVISION|fau|NCE|A|s3401|continuation_1|R"]["members"]["AP->XP"]["est"] == pytest.approx(-0.1, abs=0.03)
    # the rich continuation adopts the continued core horizon: APR - AP at equal updates within each version
    assert F["RICH|fau|NCE|T|s3401|R"]["members"]["AP->APR"]["est"] == pytest.approx(0.05, abs=0.03)
    assert F["RICH|fau|NCE|T|s3401|continuation_1|R"]["members"]["AP->APR"]["est"] == pytest.approx(0.05, abs=0.03)
    assert out["pairing"]["member_check"] == {"agrees": 16, "derived": 56}  # J* units of both versions resolve to J1
    md = md_of(tmp_path)
    assert "### Execution version `continuation_1` (INIT: S from the primary rows)" in md
    cont = md.split("### Execution version `continuation_1` (INIT: S from the primary rows)")[1].split("## 4.")[0]
    assert "| INIT · NCE · T | S → AP | 13 |" in cont and "#### core · fau · NCE" in cont and "dtu" not in cont
    assert "`continuation_1` (2 donor groups" in md
    assert "16 downstream rows carry their own continuation_of (a label)" in md

    # explicit spec.version labels on the primary rows never empty the primary families
    sy2 = Synth(tmp_path / "b")
    core_fau(sy2)
    for r in sy2.rows:
        r["spec"]["version"] = "1"
    out2, _ = run(sy2, tmp_path / "b")
    assert out2["meta"]["versions_order"] == ["primary"]
    assert out2["families"]["INIT|fau|NCE|T|s3401|R"]["members"]["S->AP"]["est"] == pytest.approx(0.3, abs=0.03)
    assert out2["meta"]["versions"][0]["explicit_labels"] == {"1": len(sy2.rows)}
    assert "| INIT · NCE · T | S → AP | 13 |" in md_of(tmp_path / "b")

    # a slot row whose donor group is not a plan row: version primary, with a note
    sy3 = Synth(tmp_path / "c")
    sy3.unit("target", "fau", "S")
    sy3.unit("target", "fau", "AP", effect=0.3)
    sy3.rows = [r for r in sy3.rows if A.SEL.STAGE.get(r["family_id"]) != "donor_group"]
    u3 = [u for u in sy3.load() if u["slot"] == "AP"]
    assert all(u["version"] == "primary" and any("is not a donor-group plan row" in n for n in u["notes"]) for u in u3)
    # a continuation cycle is a plan error
    a, b = {"experiment_id": "ALN3X_" + "1" * 16, "family_id": A.SEL.DONOR, "spec": {"continuation_of": "ALN3X_" + "2" * 16}}, \
        {"experiment_id": "ALN3X_" + "2" * 16, "family_id": A.SEL.DONOR, "spec": {"continuation_of": "ALN3X_" + "1" * 16}}
    with pytest.raises(ValueError, match="cycle"):
        A.execution_versions([a, b])


# ------------------------------------------------------------------------------------------------ selection
def test_selection_rules_descriptive(tmp_path):
    sy = Synth(tmp_path)
    sy.unit("target", "fau", "S")
    sy.unit("target", "fau", "AP", effect=0.3, gainsel="identical")
    sy.unit("target", "fau", "XP", effect=0.1, gainsel=0.05)
    out, _ = run(sy, tmp_path)
    T = out["selection"]["target_side"]
    ap = T["SELECTION|fau|NCE|T|AP|d3401t3401"]
    assert ap["gainsel_status"] == {"identical": 4}
    r = ap["endpoints"]["R"]["members"]["risk->gain"]
    assert r["n"] == 13 and r["est"] == 0.0 and r["ci_low"] == 0.0 and "family_set" not in r
    xp = T["SELECTION|fau|NCE|T|XP|d3401t3401"]["endpoints"]["R"]["members"]["risk->gain"]
    assert xp["est"] == pytest.approx(0.05, abs=0.03)  # gain-selected checkpoint lower risk by 0.05 bits
    s = T["SELECTION|fau|NCE|T|S|d-t3401"]
    assert s["gainsel_status"] == {"absent": 4}
    sm = s["endpoints"]["R"]["members"]["risk->gain"]
    assert sm["n_paired"] == 0 and "est" not in sm and sm["status"] == "no matched cell pair (4 missing, 0 excluded, 0 unregistered)"
    rows = {r["slot"]: r for r in out["coverage"]["by_configuration"] if r["stage"] == "target"}
    assert rows["S"]["sensitivity_views"] == {"gainsel": {"absent": 4}} and rows["AP"]["sensitivity_views"] == {"gainsel": {"identical": 4}}


def test_donor_side_selection_table_and_member_check(tmp_path):
    sy = Synth(tmp_path)
    core_fau(sy)
    gid = sy.group("fau")
    bid = sy.eid()
    brow = {"experiment_id": bid, "family_id": PREFIX + "BRIDGE", "dataset": "fau", "subject_fold": None, "content_fold": None,
            "seed": 3401, "logical_dependencies": [gid], "spec": {**COMMON, "stage": "bridge", "block": "core", "objective": "NCE",
                                                                  "donor_seed": 3401, "donor_group": gid, "member": "J*",
                                                                  "bridge": "ridge_u_to_stdenv8_v1"}}
    sy.rows.append(brow)
    sy.write(bid, {"experiment_id": bid, "row": brow, "status": "complete", "code_hash": "b" * 16, "member_resolved": "J1",
                   "alpha_uni": 100.0, "tau_cal": 0.12, "bridge_cal_r": 0.08, "artefact_probe": {"r_own": 0.05, "r_other": 0.01}})
    out, _ = run(sy, tmp_path)
    g = [x for x in out["selection"]["donor_groups"] if x["eid"] == gid][0]
    assert set(g["members"]) == {"AP", "XP", "J1", "J025", "XM"} and g["compute_limit"] == 60 and g["horizon_ep_eq"] == 30
    j1 = g["members"]["J1"]
    assert (j1["best/ce_dev"], j1["h30/ce_dev"], j1["gainsel/ce_dev"]) == pytest.approx((7.10, 7.11, 7.15))
    assert (j1["best/gain"], j1["gainsel/gain"], j1["best/ep_eq"], j1["nonfinite_steps"]) == (0.02, 0.025, 28.0, 0)
    assert j1["best/bridge_cal_ce"] is None and g["ceiling_reached_while_improving"] is False
    lam = g["lambda"]
    assert lam["choice"] == "J1" and lam["recorded_primary"] == "J1" and lam["check"] == "agrees" and lam["recorded_gain_rule"] == "J025"
    assert lam["ce_dev"] == {"J1": 7.10, "J025": 7.30} and lam["gainsel_gain"] == {"J1": 0.025, "J025": 0.025}
    assert g["values"]["members/J1/best/ce_dev"] == 7.10  # every selection scalar also copied
    J = out["joint_resolution"][gid]
    assert J["downstream"] == {"bridge": {"agrees": 1}, "target": {"agrees": 4}, "zero_shot": {"agrees": 4}}
    assert J["members_used"] == {"J1": 9}
    assert out["pairing"]["member_check"] == {"agrees": 9, "derived": 24}  # J* units and the bridge record J1; the others nothing
    b = out["selection"]["bridges"][0]
    assert (b["slot"], b["member_resolved"], b["member_check"]) == ("J*", "J1", "agrees")
    assert b["fields"]["alpha_uni"] == 100.0 and b["fields"]["bridge_cal_r"] == 0.08 and b["fields"]["artefact_probe/r_own"] == 0.05
    md = md_of(tmp_path)
    assert "| J1 | 7.100 / 7.110 / 7.150 | +0.020 / +0.019 / +0.025 | – / – / – | 28 / 30 / 25 | 80893 | 0 |" in md
    assert "recorded primary choice J1 (agrees); recorded gain-rule choice J025" in md

    # the lambda rule gives J025 but the target J* units record J1: excluded from every family, with the reason;
    # zero-shot J* units that record nothing take J025 from the rule and stay
    sy2 = Synth(tmp_path / "b")
    sy2.group("fau", ce={"J1": 7.3, "J025": 7.0})
    core_fau(sy2, **{"AJ*": {"member": None}})
    out2, _ = run(sy2, tmp_path / "b")
    m2 = out2["families"]["INIT|fau|NCE|T|s3401|R"]["members"]["S->J*"]
    assert m2["status"] == "no matched cell pair (0 missing, 4 excluded, 0 unregistered)"
    assert "member check disagrees: the unit records member J1; the lambda rule on the donor-group record gives J025" in \
        m2["pairing"]["cells_excluded"][0]["reason"]
    assert out2["families"]["SUPERVISION|fau|NCE|A|s3401|R"]["members"]["AP->J*"]["pairing"]["cells_matched"] == 4
    assert out2["pairing"]["member_check"] == {"derived": 28, "disagrees": 4} and len(out2["pairing"]["member_check_failures"]) == 4
    assert len(out2["pairing"]["units_excluded"]) == 4
    J2 = list(out2["joint_resolution"].values())[0]
    assert J2["lambda"]["choice"] == "J025" and J2["members_used"] == {"J025": 4, "J1": 4}
    assert any("used more than one member" in n for n in out2["notes"])

    # a recorded joint choice that contradicts the recorded CE_dev: select refuses it, so the group's J* units are unverifiable
    sy3 = Synth(tmp_path / "c")
    sy3.group("fau", joint="J025")
    core_fau(sy3)
    out3, _ = run(sy3, tmp_path / "c")
    assert out3["pairing"]["member_check"].get("unverifiable") == 8
    assert all("select.member_of raised SelectionError" in f["detail"] for f in out3["pairing"]["member_check_failures"])
    lam3 = list(out3["joint_resolution"].values())[0]["lambda"]
    assert lam3["check"] == "disagrees" and any("recorded joint choice J025 differs from the lambda rule" in n for n in out3["notes"])


def test_selection_levels_per_configuration(tmp_path):
    def drop_level(sf, cf, row, rec):
        if (sf, cf) == (0, 0):
            rec.pop("selection_level")

    sy = Synth(tmp_path)
    sy.unit("target", "fau", "S")
    sy.unit("target", "fau", "AP", effect=0.3, mutate=drop_level)
    sy.unit("target", "fau", "XP", effect=0.1, level="donor dev: new listeners, new content")  # not mode T's level
    sy.unit("zero_shot", "fau", "AP", mode="A", effect=0.2)
    sy.unit("target", "private_bdf", "S")
    out, _ = run(sy, tmp_path)
    rows = {(r["stage"], r["cohort"], r["slot"]): r for r in out["coverage"]["by_configuration"]}
    assert rows[("target", "fau", "S")]["selection_level_status"] == {"as declared": 4}
    assert rows[("target", "fau", "AP")]["selection_level_status"] == {"as declared": 3, "missing": 1}
    assert rows[("target", "fau", "XP")]["selection_level_status"] == {"unexpected": 4}
    assert rows[("zero_shot", "fau", "AP")]["selection_level_status"] == {"as declared": 4}
    assert rows[("target", "private_bdf", "S")]["selection_level_status"] == {"as declared": 2}
    assert rows[("donor_group", "fau", "-")]["selection_level_status"] == {"as declared": 1}
    leg = {x["text"]: x for x in out["coverage"]["selection_levels"]}
    code = leg[LEVEL["target"]]["code"]
    assert leg[LEVEL["target"]]["units"] == 7 and rows[("target", "fau", "AP")]["selection_levels"] == {code: 3, "none": 1}
    # levels are declared and reported, never pooled or used to drop a unit
    assert out["families"]["INIT|fau|NCE|T|s3401|R"]["members"]["S->XP"]["n"] == 13
    md = md_of(tmp_path)
    assert f"- {code} = '{LEVEL['target']}': 7 units (target 7; as declared 7)" in md
    line = [ln for ln in md.splitlines() if ln.startswith("Selection levels (unit records") and "mode A" in ln][0]
    assert "mode T:" in line and "missing 1" in line and "unexpected 4" in line


def test_uni_cal_sensitivity_missing_cells_listed(tmp_path):
    def no_unical(sf, cf, row, rec):
        if (sf, cf) == (0, 0):
            rec.pop("eval_uni_cal")

    sy = Synth(tmp_path)
    core_fau(sy, AXP={"mutate": no_unical})
    out, _ = run(sy, tmp_path)
    fam = out["families"]["SUPERVISION|fau|NCE|A|s3401|R"]
    assert fam["members"]["AP->XP"]["pairing"]["cells_matched"] == 4  # the primary evaluation is complete
    sp = fam["sensitivity_uni_cal"]["members"]["AP->XP"]["pairing"]
    assert sp["cells_matched"] == 3 and sp["cells_missing"] == [{"cell": [0, 0], "reference": "complete", "candidate": "uni_cal evaluation absent"}]
    assert any(e["view"] == "uni_cal" and e["member"] == "AP->XP" and e["cell"] == [0, 0] for e in out["pairing"]["cell_pairs_missing"])
    row = [r for r in out["coverage"]["by_configuration"] if r["stage"] == "zero_shot" and r["slot"] == "XP"][0]
    assert row["sensitivity_views"] == {"uni_cal": {"absent": 1, "evaluated": 3}}
    md = md_of(tmp_path)
    n_uc = sum(1 for e in out["pairing"]["cell_pairs_missing"] if e["view"] == "uni_cal")
    assert n_uc >= 3 and f"of which {n_uc} lack the B_uni_cal sensitivity evaluation" in md and "uni_cal absent 1, evaluated 15" in md


def test_target_contract_keys_compared_separately(tmp_path):
    def spec_tc(sf, cf, row, rec):
        if (sf, cf) == (0, 0):
            row["spec"]["target_contract"] = "tc-spec-OTHER"

    def rec_tc(sf, cf, row, rec):
        if (sf, cf) == (0, 1):
            rec["target_contract"] = "dense20ms_v1"  # core.new_record's constant, not overwritten by the runner

    sy = Synth(tmp_path)
    sy.unit("target", "fau", "S")
    sy.unit("target", "fau", "AP", effect=0.3, mutate=spec_tc)
    sy.unit("target", "fau", "XP", effect=0.1, mutate=rec_tc)
    out, _ = run(sy, tmp_path)
    m = out["families"]["INIT|fau|NCE|T|s3401|R"]["members"]
    assert m["S->AP"]["pairing"]["cells_excluded"] == [{"cell": [0, 0], "reason": "spec target_contract differs (tc-spec-1 vs tc-spec-OTHE…)"}]
    assert m["S->XP"]["pairing"]["cells_excluded"] == [{"cell": [0, 1], "reason": "record target_contract differs (tc-rec-1 vs dense20ms_v1)"}]
    assert m["S->AP"]["pairing"]["cells_matched"] == 3 and m["S->XP"]["pairing"]["cells_matched"] == 3


def test_pointwise_sections_on_own_identities(tmp_path):
    sy = Synth(tmp_path)
    core_fau(sy, XM={"skip": [(1, 0), (1, 1)]})
    for slot, eb in (("AP", -0.1), ("XP", 0.0), ("J*", 0.1)):
        sy.unit("zero_shot", "fau", slot, mode="B", effect=eb, skip=[(1, 0), (1, 1)] if slot == "XP" else ())
    out, priv = run(sy, tmp_path)
    lab = "INIT|fau|NCE|T|s3401"
    init = out["families"][f"{lab}|R"]
    ap, xm = init["members"]["S->AP"], init["members"]["S->XM"]
    assert ap["n"] == 13 and xm["n"] == 7 and init["maxt"]["n"] == 7 == ap["family_set"]["n"] and init["maxt"]["n_members"] == 4
    D = priv["paired_differences"][f"{lab}|{A.PRIMARY}"]["S->AP"]
    y = np.array([D[i]["diff"] for i in sorted(D)])
    s = S.summary(y, idx=S.draws(13, S.NB, S.group_seed(lab, A.PRIMARY)))
    assert (ap["est"], ap["ci_low"], ap["pct_high"]) == pytest.approx((float(s["est"]), float(s["ci_low"]), float(s["pct_high"])), abs=1e-12)
    common = sorted(set(priv["paired_differences"][f"{lab}|{A.PRIMARY}"]["S->XM"]))
    sc = S.summary(np.array([D[i]["diff"] for i in common]), idx=S.draws(7, S.NB, S.group_seed(lab, A.PRIMARY)))
    fs = ap["family_set"]
    assert fs["est"] == pytest.approx(float(sc["est"]), abs=1e-12) and fs["sim_low"] <= fs["ci_low"] and fs["sim_high"] >= fs["ci_high"]
    sec = out["secondary"][lab]["endpoints"]["gain"]["members"]
    assert sec["S->AP"]["n"] == 13 and sec["S->XM"]["n"] == 7  # pointwise sections are never cut by another member
    acc = out["access"]["ACCESS|fau|NCE|A->B|s3401|R"]["members"]
    assert acc["AP"]["n"] == 13 and acc["XP"]["n"] == 7 and acc["J*"]["n"] == 13
    sens = out["families"]["CONTROL|fau|NCE|A|s3401|R"]["sensitivity_uni_cal"]["members"]
    assert sens["XM->AP"]["n"] == 13  # the zero-shot XM units are complete in all cells
    md = md_of(tmp_path)
    assert re.search(r"\| INIT · NCE · T \| S → AP \| 13 \| [^|]+ \| [^|]+ \| 7 \|", md)
    assert "INIT · NCE · T (R, ref − cand): simultaneous over 4 of 4 declared members (S → AP, S → XP, S → J*, S → XM), family n = 7" in md


def test_markdown_directions_and_percentile_columns(tmp_path):
    sy = Synth(tmp_path)
    core_fau(sy, obj="CS_SINGLE")
    out, _ = run(sy, tmp_path)
    md = md_of(tmp_path)
    sec = out["secondary"]["INIT|fau|CS_SINGLE|T|s3401"]["endpoints"]
    assert sec["R_mm"]["direction"] == "lower" and sec["kernel_cs_diff"]["direction"] == "higher"
    assert sec["R_mm"]["members"]["S->AP"]["est"] == pytest.approx(0.3, abs=0.03)  # the candidate's R_mm is 0.3 bits lower: positive
    assert sec["kernel_cs_diff"]["members"]["S->AP"]["est"] == pytest.approx(0.03, abs=1e-9)  # cand − ref
    assert "R_mm (ref − cand)" in md and "kernel_cs_diff (cand − ref)" in md and "rank_pct (ref − cand)" in md
    assert "R_mm ref − cand" in md  # the direction list under "Reading the tables"
    m = out["families"]["INIT|fau|CS_SINGLE|T|s3401|R"]["members"]["S->AP"]
    assert m["pct_low"] < m["est"] < m["pct_high"] and f"[{m['pct_low']:+.3f}, {m['pct_high']:+.3f}]" in md
    assert "| Δ [95 % bootstrap-t] | [95 % percentile] | family n | Δ on the family set [95 % simultaneous] |" in md
    lev = out["levels"]["fau|CS_SINGLE|T|S|d-|t3401|primary"]["endpoints"]["R"]
    assert lev["pct_low"] < lev["est"] < lev["pct_high"] and f"[{lev['pct_low']:.3f}, {lev['pct_high']:.3f}]" in md
    acc = out["secondary"]["INIT|fau|CS_SINGLE|T|s3401"]["endpoints"]["att_acc"]["members"]["S->AP"]
    assert f"pct [{acc['pct_low']:+.3f}, {acc['pct_high']:+.3f}]" in md


# ------------------------------------------------------------------------------------------------ parsing and guards
def test_unit_rows_fallback_and_parsing(tmp_path):
    ev = cont_eval("fau", 0, 0, ("x",), 0.1, 0.02)
    assert A._tolerant_rows(ev) == unit_rows({"eval": ev})  # same endpoint definitions as auditory_alignment.aggregate
    del ev["per_participant"]["P01"]["native/mismatched_eeg"]
    with pytest.raises(KeyError):
        unit_rows({"eval": ev})
    u = {"mode": "T", "objective": "NCE", "slot": "AP", "notes": []}
    v = A._continuous_view(ev, u)
    assert u["notes"] and A.PRIMARY in v["rows"]["P01"] and "native/gain_bits" not in v["rows"]["P01"]
    assert "native/gain_bits" in v["rows"]["P00"] and v["counts"]["P01"] == (40, 20)
    assert A.canon_mode("zero_shot__no_target_supervised_fit__source_statistics_partial") == "C_partial"
    with pytest.raises(ValueError):
        A.canon_mode("D")
    sy = Synth(tmp_path)
    eid = sy.unit("target", "fau", "S", cells=[(0, 0)])[0]
    rec = json.loads((sy.dir / f"{eid}.json").read_text())
    rec["eval"] = {"readout": {}}
    (sy.dir / f"{eid}.json").write_text(json.dumps(rec))
    u = sy.load()[0]
    assert u["status"] == "complete_unparseable" and u["notes"]


def test_duplicate_units_and_privacy_scan(tmp_path):
    sy = Synth(tmp_path)
    sy.unit("target", "fau", "S", cells=[(0, 0)])
    sy.unit("target", "fau", "S", cells=[(0, 0)])
    with pytest.raises(ValueError, match="ambiguous duplicate"):
        A.run_families(sy.load())
    assert A.privacy_scan({"a": "x kid03 y", "b": "kid030", "c": "child12 here", "d": "64 children"}, {"kid03"}) == ["a", "c"]


# ------------------------------------------------------------------------------------------------ the §5.1 freeze gate
def _live_tree(tmp, monkeypatch):
    """Point the module's live paths at a temporary repository and return them."""
    repo = tmp / "repo"
    out = repo / "private" / "auditory_alignment_v3"
    p = {"REPO": repo, "OUT": out, "UNITS": out / "units", "PLAN": repo / "pkg" / "units.jsonl", "PLAN_EXT": out / "plan_ext.jsonl",
         "RES": repo / "results" / "auditory_alignment_v3" / "public_prior", "DOCS": repo / "docs" / "auditory_alignment_v3",
         "PRIV": out / "prior33" / "agg", "EXEC_RECORD": out / "aln34" / "E34_PUBLIC_PRIOR_EXECUTION_RECORD.md",
         "ENTITY_MANIFEST": out / "reaggregate" / "entity_manifest.csv"}
    for d in (p["UNITS"], p["PLAN"].parent, p["EXEC_RECORD"].parent, p["ENTITY_MANIFEST"].parent):
        d.mkdir(parents=True, exist_ok=True)
    p["ENTITY_MANIFEST"].write_text("dataset,record_uid,subject_uid,condition,entity_type\n")
    for k, v in p.items():
        monkeypatch.setattr(A, k, str(v))
    return p


def _jsonl(path, rows):
    path.write_text("".join(json.dumps(r) + "\n" for r in rows))


def test_freeze_gate_dry_run_and_frozen_run(tmp_path, monkeypatch):
    live = _live_tree(tmp_path, monkeypatch)
    sy = Synth(tmp_path / "scratch")
    sy.unit("target", "fau", "S")
    sy.unit("target", "fau", "AP", effect=0.3)
    plan = tmp_path / "scratch" / "plan.jsonl"
    _jsonl(plan, sy.rows)
    _jsonl(live["PLAN"], [])
    _jsonl(live["PLAN_EXT"], sy.rows)  # the same rows registered in the live plan
    s = tmp_path / "scratch"
    ok = ["--plan", str(plan), "--units", str(sy.dir), "--res", str(s / "res"), "--docs", str(s / "docs"), "--priv", str(s / "priv")]

    def refused(args, match):
        with pytest.raises(SystemExit, match=match):
            A.main(["--allow-unfrozen"] + args)

    refused([], "--units is required")
    refused(["--plan", str(live["PLAN_EXT"])] + ok[2:], "is a live plan file")
    refused(ok[:2] + ["--units", str(live["UNITS"])] + ok[4:], "live units directory")
    refused(ok[:2] + ["--units", str(live["UNITS"] / "copy")] + ok[4:], "live units directory")  # inside it
    refused(ok[:6] + ["--docs", str(live["DOCS"] / "dry")] + ok[8:], "inside docs")  # a subdirectory of a publication path
    refused(ok[:4] + ["--res", str(live["REPO"] / "results" / "x")] + ok[6:], "inside results")
    refused(ok[:8] + ["--priv", str(live["OUT"] / "prior33" / "dry")], "inside private")
    # a dry run on scratch inputs works, is labelled and is not frozen
    A.main(["--allow-unfrozen"] + ok)
    js = json.loads((s / "res" / A.JSON_NAME).read_text())
    assert js["meta"]["dry_run"] is True and js["meta"]["frozen_check"]["ok"] is False
    assert js["families"]["INIT|fau|NCE|T|s3401|R"]["members"]["S->AP"]["n"] == 13
    assert "**Dry run**" in (s / "docs" / A.MD_NAME).read_text() and not os.listdir(live["UNITS"])
    # once a plan row has a live record, a dry run refuses (existence is checked; the record is never opened)
    eid = sy.rows[-1]["experiment_id"]
    (live["UNITS"] / f"{eid}.json").write_text("not json: never read")
    refused(ok, "have a record in the live units directory")
    (live["UNITS"] / f"{eid}.json").unlink()
    # the frozen run refuses without the execution record, and the live units directory is never read unfrozen
    with pytest.raises(SystemExit, match="refusing to run .* is absent"):
        A.main([])
    with pytest.raises(RuntimeError, match="read only by the frozen analysis"):
        A.load_records(sy.rows)
    # an execution record listing every code file (full hashes and 16-digit prefixes) and the manifest freezes the analysis
    shas = A.code_sha256()
    assert set(shas) == set(A.code_files()) >= {"auditory_alignment_v3/prior33/analysis.py", "tests/auditory_alignment_v3/prior33/test_analysis.py",
                                                 "auditory_alignment_v3/prior33/select.py", "auditory_alignment_v3/prior33/contract.py",
                                                 "auditory_alignment_v3/sci_r1/stats.py", "auditory_alignment/aggregate.py"}
    names = sorted(shas)
    partial = "\n".join(f"{k} {shas[k]}" for k in names[1:])
    live["EXEC_RECORD"].write_text(partial + f"\nmanifest {MAN_SHA[:16]}…\n")
    fz = A.frozen_check(sy.rows)
    assert not fz["ok"] and fz["problems"] == [f"{names[0]}: sha256 {shas[names[0]][:16]}… not listed in the record"]
    live["EXEC_RECORD"].write_text(partial + f"\n{names[0]} {shas[names[0]][:16]}…\n")
    fz = A.frozen_check(sy.rows)
    assert not fz["ok"] and fz["problems"] == [f"manifest sha256 {MAN_SHA[:16]}… of {len(sy.rows)} E34 plan rows not listed in the record"]
    live["EXEC_RECORD"].write_text(partial + f"\n{names[0]} {shas[names[0]][:16]}…\nmanifest sha256 {MAN_SHA}\n")
    assert A.frozen_check(sy.rows)["ok"]
    for f in sy.dir.iterdir():  # the fleet's records reach the live units directory
        (live["UNITS"] / f.name).write_text(f.read_text())
    A.main([])
    js = json.loads((live["RES"] / A.JSON_NAME).read_text())
    assert js["meta"]["dry_run"] is False and js["meta"]["frozen_check"]["ok"] is True
    assert js["families"]["INIT|fau|NCE|T|s3401|R"]["members"]["S->AP"]["n"] == 13
    assert stat.S_IMODE(os.stat(live["PRIV"] / A.PRIV_NAME).st_mode) == 0o600
    assert "Frozen check: PASS" in (live["DOCS"] / A.MD_NAME).read_text()
    # a changed manifest (rows built on another manifest) is refused again
    rows2 = [dict(r, spec={**r["spec"], "manifest_sha256": "b" * 64}) if r["family_id"] in A.SEL.STAGE else r for r in sy.rows]
    assert A.frozen_check(rows2)["problems"][0].startswith("manifest sha256 bbbbbbbbbbbbbbbb… of")
