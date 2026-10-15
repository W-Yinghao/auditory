"""ADDENDUM_09 §2: append plan_ext.jsonl block 5 (ALN32_SIMPLE_COMPLEMENT, 100 rows) after verifying the existing 2,075 rows
(blocks 1-4; sha256 586a7f0a...). One row per A_LOCAL lag_local_tokens full NCE seed-3401 cell x base {L0, L1} x backbone."""
import hashlib, json, os, sys
from collections import Counter
sys.path.insert(0, "/home/infres/yinwang/EEG_auditory")
from auditory_alignment_v3 import core

P = os.path.join(core.OUT, "plan_ext.jsonl")
raw = open(P, "rb").read(); lines = raw.decode().splitlines(keepends=True)
assert len(lines) == 2075 and hashlib.sha256(raw).hexdigest().startswith("586a7f0af1126ea3"), (len(lines), hashlib.sha256(raw).hexdigest())
ext = [json.loads(l) for l in lines]; out = []
L1 = {(r["dataset"], r["subject_fold"], r["content_fold"]): r for r in ext if r["family_id"] == "ALN32_LOCAL_SUPPORT" and r["spec"]["variant"] == "local_aligned1000"}
for r in core.load_rows():
    s = r["spec"]
    if not (r["family_id"] == "A_LOCAL" and r["seed"] == 3401 and s.get("architecture") == "lag_local_tokens" and s.get("window") == "full"
            and s["objective"] == "NCE" and s.get("projection_dim", 32) == 32):
        continue
    for base in ("L0", "L1"):
        brow = r if base == "L0" else L1[(r["dataset"], r["subject_fold"], r["content_fold"])]
        for arch in ("cbramod", "reve"):
            sp = {"objective": "NCE", "target": s["target"], "target_contract": s.get("target_contract"), "projection_dim": 32, "base": base,
                  "architecture": arch, "information_stratum": "foundation_context", "fusion": "common_prediction_space_grouped_crossfit"}
            h = hashlib.sha256(("ALN32_SIMPLE_COMPLEMENT" + json.dumps(sp, sort_keys=True) + brow["experiment_id"]).encode()).hexdigest()[:16]
            out.append({**{k: r[k] for k in ("dataset", "subject_fold", "content_fold", "seed", "seed_scope")}, "experiment_id": f"ALN3X_{h}",
                        "family_id": "ALN32_SIMPLE_COMPLEMENT", "job_kind": "fit", "spec": sp, "base_plan_row": brow["experiment_id"],
                        "registered": "ADDENDUM_09 (docs/auditory_alignment_v3/ADDENDUM_09_ALN32_SIMPLE_COMPLEMENT.md)",
                        "logical_dependencies": [brow["experiment_id"]], "status": "registered_extension"})
assert len(out) == 100 and len({x["experiment_id"] for x in out}) == 100 and not {x["experiment_id"] for x in ext} & {x["experiment_id"] for x in out}
tmp = P + ".tmp"; open(tmp, "w").write("".join(lines) + "".join(json.dumps(x) + "\n" for x in out)); os.replace(tmp, P)
print("appended", dict(Counter((x["spec"]["base"], x["spec"]["architecture"]) for x in out)), "| sha256", hashlib.sha256(open(P, "rb").read()).hexdigest())
