"""Final completeness / provenance audit of the ALN2 in-scope units (file checks only)."""
import json, os, glob
from collections import Counter
O = "/home/infres/yinwang/EEG_auditory/private/auditory_alignment_v2"
R = [json.loads(l) for l in open("/home/infres/yinwang/EEG_auditory/AUDITORY_ALIGNMENT_NEXT_SERVER_PACKAGE_v2_20261006/plans/planned_comparisons.jsonl")]
SC = json.load(open(O + "/seed_scope.json")); PN = SC["panel"]
inpan = lambda r: r["seed"] in PN["seeds"] and r["family_id"] in PN["families"] and r["spec"].get("objective") == PN["objective"] and r["spec"].get("adaptation") in PN["adaptations"]
scope = [r for r in R if r["seed"] in SC["seeds"] or r["family_id"] in SC["exempt_families"] or inpan(r)]
def fm(r):
    f, a = r["family_id"], r["spec"].get("architecture")
    return f in ("B_FM", "D_FM_GENERIC", "B_AUDITORY_CONTINUE", "D_FM_PUBLIC", "D_LOCAL_DISTILL") or (f in ("C_ATTENTION", "C_COVERAGE", "C_SELECTION", "C_ADAPT") and a == "cbramod")
NEW = {"run_fm": "234202b1e913d385", "run_stage": "6ddfa147a711e286", "run_adapt": "8889ea0390ed872c"}
issues = Counter(); ex = {}; hashes = Counter(); n_fm = n_small = 0
def bad(k, e):
    issues[k] += 1; ex.setdefault(k, e)
for r in scope:
    e = r["experiment_id"]; p = f"{O}/units/{e}.json"
    if not os.path.exists(p): bad("missing", e); continue
    d = json.load(open(p))
    if d.get("status") != "complete": bad("not_complete", e); continue
    src = d
    if d.get("reuse_of"):
        sp = f"{O}/units/{d['reuse_of']}.json"
        if not os.path.exists(sp): bad("reuse_source_missing", e); continue
        src = json.load(open(sp))
        if src.get("status") != "complete": bad("reuse_source_incomplete", e)
        if src.get("code_hash") != d.get("code_hash"): bad("reuse_hash_differs", e)
    runner = (src.get("runner") or "run").split("/")[0]
    hashes[(r["family_id"] if not fm(r) else "FM:" + r["family_id"], runner, src.get("code_hash"))] += 1
    if fm(r):
        n_fm += 1
        if src.get("code_hash") != NEW.get(runner, "?"): bad("fm_old_code_hash", e)
        uses_fm_net = r["family_id"] not in ("D_LOCAL_DISTILL",) and not (r["family_id"] == "C_ADAPT")
        if uses_fm_net and not str(src.get("readout_head", "")).startswith("spatial_signed"): bad("fm_no_repaired_head", e)
        if uses_fm_net and "channel_probe" not in src.get("eval", {}): bad("fm_no_probe", e)
        if "channel_probe_error" in src.get("eval", {}): bad("probe_error", e)
        if r["family_id"] == "D_LOCAL_DISTILL":
            t = src.get("teacher_unit"); tp = f"{O}/units/{t}.json"
            if not t or not os.path.exists(tp) or not str(json.load(open(tp)).get("readout_head", "")).startswith("spatial_signed"): bad("distill_teacher_not_repaired", e)
        if r["family_id"] == "C_ADAPT":
            b = src.get("base_unit"); bp = f"{O}/units/{b}.json"
            bd = json.load(open(bp)) if b and os.path.exists(bp) else None
            if bd and bd.get("reuse_of"): bd = json.load(open(f"{O}/units/{bd['reuse_of']}.json"))
            if not bd or not str(bd.get("readout_head", "")).startswith("spatial_signed"): bad("adapt_base_not_repaired", e)
    else:
        n_small += 1
# legacy records left in units/ (channel-mean head) for FM families
for p in glob.glob(f"{O}/units/ALN2_*.json"):
    d = json.load(open(p))
    if d.get("row") and fm(d["row"]) and not d.get("reuse_of") and d.get("code_hash") in ("60d363ffe7c32f70", "fc5af9f62078e891", "49805706b6bd69a5") and d["row"]["family_id"] != "C_ADAPT":
        bad("legacy_record_in_units", os.path.basename(p))
donors = sorted(os.path.basename(p) for p in glob.glob(f"{O}/donors/*.pt"))
dj = [json.load(open(p)) for p in glob.glob(f"{O}/donors/*.json")]
print("in-scope units:", len(scope), "| FM-dependent:", n_fm, "| other:", n_small)
print("donors:", len(donors), "| donor records with repaired readout:", sum(str(x.get("readout_head", "")).startswith("spatial_signed") for x in dj))
print("issues:", dict(issues) or "none")
for k, v in ex.items(): print("  e.g.", k, v)
print("code hashes by family / runner:")
for k, v in sorted(hashes.items(), key=lambda x: str(x[0])): print("  ", k, v)
