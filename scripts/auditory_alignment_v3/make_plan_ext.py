"""ALN3 registered extension rows (private/auditory_alignment_v3/plan_ext.jsonl), each block written before any of its rows runs.
  rows 0-299   item-3 addendum 01 (docs/auditory_alignment_v2/ITEM3_ADDENDUM_01.md): original-recipe control and learning-rate
               panel for B_DENSE. Representative configurations (not chosen on results): readout dense_query, objective NCE, all
               three public cohorts, all folds, seed 3401; adaptations pretrained_peft and pretrained_full for both architectures.
                 B_CTRL_ONESTEP  recipe aln2_onestep (no warm-up, no unfreezing schedule, no layer-wise decay, validation every E/20 epochs)
                 B_LR_PANEL      recipe aln3 with backbone lr x0.3 and x3 around the fixed value (head lr unchanged)
               Unchanged since 2026-10-10 (ids ALN3X_*); appending below keeps their queue indices (>= 100000) valid.
  rows 300+    ALN3.1 seed-confirmation panel (docs/auditory_alignment_v3/ADDENDUM_03_ALN3_1_SEED_PANEL.md, 2026-10-11): for every
               role of AUDITORY_ALN3_SERVER_PACKAGE_v3_1_20261011/configs/seed_confirmation_pairs.yaml, the seed-3407/3413 rows
               that the frozen v3.0 plan does not already contain. Each row copies its seed-3401 reference row (same spec, folds,
               job kind, logical dependencies) with the seed changed; its id follows the package's own signature rule
               (scripts/expand_plan.py), so it equals what plans/units.jsonl would have contained had the row been planned.
Also written: governance/deferred_redundant_v30_panel.json — the v3.0 panel rows (seeds 3407/3413) that no v3.1 role requires
(docs/12 §3: 'deferred_redundant', reason kept, nothing deleted). make_queue.py leaves them out unless the switch file
PANEL_V30_RESUME exists; governance/seed_panel_v31_registry.json records every role requirement -> experiment id."""
import hashlib, json, os, sys
from collections import Counter

import yaml

sys.path.insert(0, "/home/infres/yinwang/EEG_auditory")
from auditory_alignment_v3 import core

REPO = "/home/infres/yinwang/EEG_auditory"
PKG31 = os.path.join(REPO, "AUDITORY_ALN3_SERVER_PACKAGE_v3_1_20261011")
GOV = os.path.join(core.OUT, "governance")
os.makedirs(GOV, exist_ok=True)
rows = core.load_rows(); out = []

# ---------------------------------------------------------------- block 1: item-3 addendum 01 (unchanged)
for r in rows:
    s = r["spec"]
    if r["family_id"] != "B_DENSE" or r["seed"] != 3401 or s["readout"] != "dense_query" or s["objective"] != "NCE" or s["adaptation"] not in ("pretrained_peft", "pretrained_full"):
        continue
    for fam, extra in (("B_CTRL_ONESTEP", {"recipe": "aln2_onestep"}), ("B_LR_PANEL", {"recipe": "aln3", "lr_multiplier": 0.3}), ("B_LR_PANEL", {"recipe": "aln3", "lr_multiplier": 3.0})):
        sp = {**s, **extra}
        h = hashlib.sha256((fam + json.dumps(sp, sort_keys=True) + r["experiment_id"]).encode()).hexdigest()[:16]
        out.append({**{k: r[k] for k in ("dataset", "subject_fold", "content_fold", "seed", "seed_scope")}, "experiment_id": f"ALN3X_{h}", "family_id": fam,
                    "job_kind": "train", "spec": sp, "base_plan_row": r["experiment_id"], "registered": "item-3 addendum 01 (docs/auditory_alignment_v2/ITEM3_ADDENDUM_01.md)",
                    "logical_dependencies": [], "status": "registered_extension"})
assert len(out) == 300, len(out)
BLOCK1_SHA = hashlib.sha256("".join(json.dumps(x) + "\n" for x in out).encode()).hexdigest()
assert BLOCK1_SHA.startswith("bbc96cd30c40b27c"), BLOCK1_SHA  # ADDENDUM_02 §1 (the 300-row file of 2026-10-10)

# ---------------------------------------------------------------- block 2: ALN3.1 seed-confirmation panel
rules = yaml.safe_load(open(os.path.join(PKG31, "configs", "seed_confirmation_pairs.yaml")))
SEEDS = rules["seeds"]
assert SEEDS == [3401, 3407, 3413] and rules["version"] == "ALN3.1"
SIG_KEYS = ("family_id", "dataset", "job_kind", "base_commit", "seed", "subject_fold", "content_fold", "spec", "logical_dependencies", "status", "seed_scope")


def canonical(r):  # training identity independent of the seed (package scripts/register_seed_pairs.py; same value for plan rows,
    # which carry exactly the signature keys + experiment_id; bookkeeping keys of extension rows are ignored)
    d = {k: r[k] for k in SIG_KEYS if k not in ("seed", "seed_scope", "status")}
    return hashlib.sha256(json.dumps(d, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def matches(row, selector):
    for k, v in selector.items():
        actual = row.get(k, row["spec"].get(k))
        if actual not in (v if isinstance(v, list) else [v]):
            return False
    return True


def plan_id(row):  # package scripts/expand_plan.py signature rule
    sig = json.dumps({k: row[k] for k in SIG_KEYS}, sort_keys=True, separators=(",", ":"))
    return "ALN3_" + hashlib.sha256(sig.encode()).hexdigest()[:16]


assert all(plan_id(r) == r["experiment_id"] for r in rows), "signature rule does not reproduce the frozen plan ids"
registered = {(canonical(r), r["seed"]): r["experiment_id"] for r in rows}
breadth = [r for r in rows if r["seed"] == SEEDS[0]]
need = {}  # (canonical, seed) -> reference row + roles
for panel in rules["panels"]:
    for role in panel["roles"]:
        found = [r for r in breadth if matches(r, role["selector"])]
        assert found, (panel["id"], role["role"])
        for r in found:
            for s in SEEDS:
                d = need.setdefault((canonical(r), s), {"ref": r, "roles": []}); d["roles"].append(f"{panel['id']}/{role['role']}")
new_rows = []
for (c, s), d in need.items():
    if (c, s) in registered:
        continue
    ref = d["ref"]
    row = {k: ref[k] for k in ("family_id", "dataset", "job_kind", "base_commit", "subject_fold", "content_fold", "spec", "logical_dependencies")}
    row.update({"seed": s, "status": "planned_needs_binding", "seed_scope": "panel"})
    row["experiment_id"] = plan_id(row)
    row.update({"reference_3401_id": ref["experiment_id"], "panel_roles": sorted(set(d["roles"])),
                "registered": "ALN3.1 seed_confirmation_pairs.yaml (docs/auditory_alignment_v3/ADDENDUM_03_ALN3_1_SEED_PANEL.md)"})
    new_rows.append(row)
FAM_ORDER = ["A_LOCAL", "E_GENERIC", "B_DENSE", "C_CAPACITY_CONTROL", "C_COMPLEMENT", "D_ADAPT", "D_ATTENTION", "E_PUBLIC_TRANSFER"]
new_rows.sort(key=lambda r: (FAM_ORDER.index(r["family_id"]) if r["family_id"] in FAM_ORDER else 99, r["dataset"], r["subject_fold"] or 0,
                             r["content_fold"] or 0, json.dumps(r["spec"], sort_keys=True), r["seed"]))
ids = {r["experiment_id"] for r in rows} | {r["experiment_id"] for r in out}
for r in new_rows:
    assert r["experiment_id"] not in ids, r["experiment_id"]; ids.add(r["experiment_id"])
out += new_rows

# ---------------------------------------------------------------- deferred_redundant: v3.0 panel rows outside every v3.1 role
deferred = [r for r in rows if r["seed_scope"] == "panel" and (canonical(r), r["seed"]) not in need]
assert not any(os.path.exists(os.path.join(core.OUT, "units", f"{r['experiment_id']}.json")) for r in deferred), "a deferred row already has a unit record"
summary = lambda s: {k: s.get(k) for k in ("architecture", "adaptation", "variant", "objective", "window", "readout", "target") if k in s}
gov = {"version": "ALN3.1", "decided": "2026-10-11 (AUDITORY_ALN3_SERVER_PACKAGE_v3_1_20261011 docs/12 §3: rows not submitted that no longer belong to a core comparison are marked deferred_redundant, reason kept)",
       "reason": "v3.0 panel rows (seeds 3407/3413) that no role of configs/seed_confirmation_pairs.yaml requires: CS_SINGLE dense readouts / complement variants and lag-local CS_SINGLE early/late/joint windows (traditional CS keeps full breadth at seed 3401; a CS-specific FM/time claim would add its matched confirmation controls then, docs/12 §3). Not a judgement on results: none of these rows had started.",
       "resume_switch": os.path.join(core.OUT, "PANEL_V30_RESUME"), "n_rows": len(deferred), "by_family": dict(Counter(r["family_id"] for r in deferred)),
       "by_family_seed": {f"{k[0]}|{k[1]}": v for k, v in sorted(Counter((r["family_id"], r["seed"]) for r in deferred).items())},
       "ids": [r["experiment_id"] for r in deferred],
       "rows": [{"experiment_id": r["experiment_id"], "family_id": r["family_id"], "seed": r["seed"], "dataset": r["dataset"], "subject_fold": r["subject_fold"], "content_fold": r["content_fold"], "spec": summary(r["spec"])} for r in deferred]}
reg = {"version": "ALN3.1", "source_rules": "AUDITORY_ALN3_SERVER_PACKAGE_v3_1_20261011/configs/seed_confirmation_pairs.yaml",
       "n_requirements": len(need), "n_present_in_v30_plan": sum(k in registered for k in need), "n_new_rows": len(new_rows),
       "new_by_family_seed": {f"{k[0]}|{k[1]}": v for k, v in sorted(Counter((r["family_id"], r["seed"]) for r in new_rows).items())},
       "requirements": [{"canonical": c, "seed": s, "experiment_id": registered.get((c, s)) or next(r["experiment_id"] for r in new_rows if canonical(r) == c and r["seed"] == s),
                         "in_v30_plan": (c, s) in registered, "reference_3401_id": d["ref"]["experiment_id"], "family_id": d["ref"]["family_id"], "roles": sorted(set(d["roles"]))}
                        for (c, s), d in sorted(need.items(), key=lambda kv: (kv[1]["ref"]["family_id"], kv[1]["ref"]["experiment_id"], kv[0][1]))]}

p = os.path.join(core.OUT, "plan_ext.jsonl")
open(p + ".tmp", "w").write("".join(json.dumps(x) + "\n" for x in out)); os.replace(p + ".tmp", p)
for name, obj in (("deferred_redundant_v30_panel.json", gov), ("seed_panel_v31_registry.json", reg)):
    q = os.path.join(GOV, name); open(q + ".tmp", "w").write(json.dumps(obj, indent=1) + "\n"); os.replace(q + ".tmp", q)
print("plan_ext rows", len(out), "block1 sha", BLOCK1_SHA[:16], "| new v3.1 panel rows", len(new_rows), dict(Counter((x["family_id"], x["seed"]) for x in new_rows)))
print("requirements", len(need), "present", reg["n_present_in_v30_plan"], "| deferred_redundant", len(deferred), gov["by_family"])
