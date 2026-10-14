"""ADDENDUM_05 §9 E3: synthetic checks of the interim B / C aggregation (no real data). Known paired effects and signs are
recovered, simultaneous intervals contain the pointwise ones, mismatched pairs are excluded, the mismatched-only flag and the
wording rule follow §4 / §7, Federici records map to subjects with the phantom excluded, private records parse, and the privacy
scan catches a planted child id."""
import numpy as np

from auditory_alignment_v3 import bc_interim as BI

IDS = [f"P{i:02d}" for i in range(16)]  # fold 0: P00-P07, fold 1: P08-P15


def _metrics(ll, rank=0.2, top1=0.3, nc=40, nq=20):
    return {"top1": top1, "top5": 0.6, "mrr": 0.4, "rank_pct": rank, "logloss_bits": ll, "n_candidates": nc, "n_queries": nq}


def _rec(effect, gain=1.0, fold=0, pids=None, nc=40, eff_mm=0.0):
    rng = np.random.default_rng(abs(hash((effect, gain, fold))) % 2 ** 32)
    pp = {}
    for j, p in enumerate(pids if pids is not None else IDS[8 * fold:8 * fold + 8]):
        base = 4.0 + 0.1 * j
        reg = base - effect + 0.005 * rng.standard_normal()
        pp[p] = {"group": "ha" if j % 2 else "th", "n_segments": 20,
                 "unified/regular": _metrics(reg, nc=nc), "unified/mismatched_eeg": _metrics(reg + gain + eff_mm, nc=nc), "unified/hard": _metrics(2.5, nc=nc),
                 "native/regular": _metrics(reg + 0.1, nc=nc), "native/mismatched_eeg": _metrics(reg + 1.1, nc=nc), "native/hard": _metrics(2.6, nc=nc)}
    return {"status": "complete", "eval": {"per_participant": pp}}


def _design(effects, mm=None, bad_count=None, ds="fau"):
    """effects: cfg -> true risk reduction vs a common baseline; returns rows and a loader."""
    rows, recs = [], {}
    tgt = BI.TARGET[ds]
    def add(fam, spec, cfg):
        for fold in (0, 1):
            e = f"{fam}_{len(rows):04d}"
            rows.append({"experiment_id": e, "family_id": fam, "dataset": ds, "subject_fold": fold, "content_fold": 0, "seed": 3401, "spec": {**spec, "target": tgt}})
            recs[e] = _rec(effects.get(cfg, 0.0), fold=fold, nc=(39 if bad_count == cfg and fold == 1 else 40), eff_mm=(mm or {}).get(cfg, 0.0))
    for o in BI.OBJ:
        add("A_LOCAL", {"objective": o, "architecture": "lag_local_tokens", "window": "full", "projection_dim": 32}, ("L", ds, o))
        for a in BI.ARCH:
            for ad in BI.ADAPT:
                for ro in BI.READOUT:
                    add("B_DENSE", {"objective": o, "architecture": a, "adaptation": ad, "readout": ro}, ("B", ds, o, a, ad, ro))
            for v in BI.VARIANTS:
                add("C_COMPLEMENT", {"objective": o, "architecture": a, "variant": v}, ("C", ds, o, a, v))
        add("C_CAPACITY_CONTROL", {"objective": o, "architecture": "small_capacity_branch", "variant": BI.CAP}, ("C", ds, o, "-", BI.CAP))
    return rows, recs.get


def _agg(effects, **kw):
    rows, load = _design(effects, **kw)
    return BI.aggregate_continuous(BI.load_continuous(rows, load, {}))


def test_effects_signs_and_simultaneous_cover(tmp_path):
    eff = {("B", "fau", "NCE", "reve", ad, "dense_query"): 0.2 for ad in BI.ADAPT}
    eff[("B", "fau", "NCE", "cbramod", "pretrained_full", "channel_phase_linear")] = -0.1  # worse than random_full
    eff[("C", "fau", "NCE", "reve", "residual_pretrained_full")] = 0.3
    out = _agg(eff)
    m = out["families"]["B-READOUT|fau|NCE|reve"]["members"]["pretrained_peft"]
    assert abs(m["est"] - 0.2) < 0.02 and m["class"] == "I>0" and m["n"] == 16
    m = out["families"]["B-INIT|fau|NCE|cbramod"]["members"]["channel_phase_linear/pretrained_full"]
    assert abs(m["est"] + 0.1) < 0.02 and m["class"] == "I<0" and m["tag"].startswith("initialization")
    m = out["families"]["C-LOCAL|fau|NCE"]["members"]["reve/residual_pretrained_full"]
    assert abs(m["est"] - 0.3) < 0.02 and m["class"] == "I>0"
    for f in out["families"].values():
        for m in f["members"].values():
            if "sim_low" in m:
                assert m["sim_low"] <= m["ci_low"] + 1e-12 and m["sim_high"] >= m["ci_high"] - 1e-12
    # secondary: top1 identical everywhere -> zero difference; native logloss follows the same effect (lower is better)
    sec = out["secondary"]["B-READOUT|fau|NCE|reve"]
    assert abs(sec["unified/regular/top1"]["members"]["pretrained_peft"]["est"]) < 1e-12
    assert abs(sec["native/regular/logloss_bits"]["members"]["pretrained_peft"]["est"] - 0.2) < 0.02
    assert not [x for x in out["excluded_pairs"] if "|fau|" in x]  # only the absent datasets are unpaired
    from auditory_alignment_v3 import bc_interim_report as REP
    meta = {"addendum": "ADDENDUM_05_BC_INTERIM_AGGREGATION.md", "code_sha256": {"bc_interim.py": "0" * 64}, "n_boot": 4000}
    paths = REP.write_continuous(out, None, meta, str(tmp_path))
    assert len(paths) == 2 and all("Interim, seed 3401 only" in open(q).read() for q in paths)


def test_count_mismatch_excludes_pair():
    bad = ("C", "fau", "NCE", "reve", "residual_pretrained_peft")
    out = _agg({}, bad_count=bad)
    assert "reve/residual_pretrained_peft" not in out["families"]["C-LOCAL|fau|NCE"]["members"]
    assert any("C-LOCAL|fau|NCE/reve/residual_pretrained_peft" in x and "counts differ" in x for x in out["excluded_pairs"])


def test_mismatched_only_flag_and_wording():
    C = lambda a, v: ("C", "fau", "NCE", a, v)
    eff = {C("reve", "residual_pretrained_full"): 0.3, C("reve", "residual_pretrained_peft"): 0.3}  # random / capacity stay at 0
    mm = {C("cbramod", "concat_pretrained"): 0.5}  # only the mismatched loss rises
    out = _agg(eff, mm=mm)
    f = out["mismatched_only"]["C-LOCAL|fau|NCE|cbramod/concat_pretrained"]
    assert f["mismatched_only"] and f["dR_class"] == "contains 0"
    assert not out["mismatched_only"]["C-LOCAL|fau|NCE|reve/residual_pretrained_full"]["mismatched_only"]
    w = out["complement_wording"]
    assert w["fau|NCE|reve|residual_pretrained_full"]["wording"] == "complement from the pretrained representation"
    assert w["fau|NCE|reve|residual_pretrained_peft"]["wording"].startswith("added branch lowers risk")  # no matched init member
    assert w["fau|NCE|cbramod|concat_pretrained"]["wording"] == "no complement resolved"


def test_federici_identity_and_phantom():
    rows = [{"experiment_id": "L0", "family_id": "A_LOCAL", "dataset": "federici", "subject_fold": 0, "content_fold": 0, "seed": 3401,
             "spec": {"objective": "NCE", "architecture": "lag_local_tokens", "window": "full", "projection_dim": 32, "target": "envelope"}}]
    rec = _rec(0.0, pids=["HC:1", "HC:1b", "CI:2", "ART:9"])
    man = {"HC:1": ("HC:1", "HC", "human"), "HC:1b": ("HC:1", "HC", "human"), "CI:2": ("CI:2", "CI", "human"), "ART:9": ("ART", "Artifact", "phantom")}
    d = BI.load_continuous(rows, {"L0": rec}.get, man)
    v = d["vals"][("L", "federici", "NCE")]
    assert set(v) == {"HC:1", "CI:2"} and d["n_phantom_entities"]["federici"] == 1
    a, b = rec["eval"]["per_participant"]["HC:1"]["unified/regular"]["logloss_bits"], rec["eval"]["per_participant"]["HC:1b"]["unified/regular"]["logloss_bits"]
    assert abs(v["HC:1"][BI.PRIMARY] - (a + b) / 2) < 1e-12


def _prec(nll_shift, kids, comp=False, distill=False):
    pp, nc = {}, {}
    for j, c in enumerate(kids):
        nll = 0.7 + 0.01 * j - nll_shift
        if comp:
            pp[c] = {"group": "NH" if j < 2 else "HA", "combined": {"auc": 0.6, "nll_bits": nll, "brier": 0.2, "gain_vs_base_bits": 0, "n": 50},
                     "local_only": {"auc": 0.55, "nll_bits": 0.7 + 0.01 * j, "brier": 0.2, "gain_vs_base_bits": 0, "n": 50}}
        else:
            pp[c] = {"group": "NH" if j < 2 else "HA", "hist_gain_bits": 0.01 + nll_shift, "hist_gain_twin_bits": 0.0}
            nc[c] = {"positive_affine": {"auc_score": 0.55 + nll_shift, "nll_bits": nll, "brier": 0.2, "gain_vs_base_bits": 0, "n": 50}}
    ev = {"per_participant": pp} if comp else {"per_participant": pp, "native_calibration": {"per_participant": nc}}
    rec = {"status": "complete", "eval": ev}
    if distill:
        rec["baseline_lambda0_eval"] = _prec(0.0, kids)["eval"]
    return rec


def test_private_parse_contrasts_and_privacy(tmp_path):
    kids = [f"kid{i:02d}" for i in range(12)]
    rows, recs = [], {}
    def add(fam, spec, rec):
        e = f"{fam}_{len(rows)}"; rows.append({"experiment_id": e, "family_id": fam, "dataset": "private_bdf", "subject_fold": 0, "content_fold": 0, "seed": 3401, "spec": spec}); recs[e] = rec
    add("E_LOCAL", {"objective": "NCE", "architecture": "lag_local_tokens", "window": "full"}, _prec(0.0, kids))
    for ad in BI.ADAPT:
        add("E_GENERIC", {"objective": "NCE", "architecture": "reve", "adaptation": ad}, _prec(0.05 if ad == "pretrained_full" else 0.0, kids))
    add("E_COMPLEMENT", {"objective": "NCE", "architecture": "reve", "variant": "residual_pretrained_frozen"}, _prec(0.02, kids, comp=True))
    add("E_DISTILL", {"objective": "NCE", "teacher_policy": "local_teacher", "window": "full"}, _prec(0.03, kids, distill=True))
    p = BI.aggregate_private(BI.load_private(rows, recs.get))
    m = p["families"]["PE-GENERIC|NCE|reve|NLL"]["members"]["pretrained_full"]
    assert abs(m["est"] - 0.05) < 1e-9 and m["n"] == 12
    assert abs(p["families"]["PE-GENERIC|NCE|reve|AUC"]["members"]["pretrained_full"]["est"] - 0.05) < 1e-9
    assert abs(p["families"]["PE-COMPLEMENT|NCE|reve|NLL"]["members"]["residual_pretrained_frozen"]["est"] - 0.02) < 1e-9
    assert abs(p["families"]["PE-DISTILL|NCE|NLL"]["members"]["local_teacher/full"]["est"] - 0.03) < 1e-9
    assert abs(p["families"]["PE-LOCAL|NCE|NLL"]["members"]["generic/reve/pretrained_full"]["est"] - 0.05) < 1e-9
    lv = p["levels"]["E_LOCAL|NCE|lag_local_tokens|full"]["NLL"]["groups"]
    assert lv["NH"] == {"n": 2} and lv["HA"]["n"] == 10  # n < 5 -> n only
    clean, dirty = tmp_path / "a.md", tmp_path / "b.md"
    clean.write_text("no identifiers here"); dirty.write_text("value for kid07 is")
    assert BI.privacy_scan([str(clean), str(dirty)], set(kids)) == [str(dirty)]
    assert not any("child" in n and "<child>" not in n for n in p["notes"])
    from auditory_alignment_v3 import bc_interim_report as REP
    meta = {"addendum": "ADDENDUM_05_BC_INTERIM_AGGREGATION.md", "code_sha256": {"bc_interim.py": "0" * 64}, "n_boot": 4000}
    q = REP.write_private(p, meta, str(tmp_path))
    assert "PRIVATE" in open(q).read() and BI.privacy_scan([q], set(kids)) == []
