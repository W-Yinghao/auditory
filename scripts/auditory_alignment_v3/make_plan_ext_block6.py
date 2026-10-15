"""ADDENDUM_10 §2: append plan_ext.jsonl block 6 (ALN32_RESIDUAL, 250 rows) after verifying the existing 2,175 rows (blocks 1-5;
sha256 09fe8add...). Per A_LOCAL lag_local_tokens full seed-3401 cell x objective {NCE, CS_SINGLE}: residual_aligned_pretrained /
residual_aligned_random x {cbramod, reve} and residual_small_capacity."""
import hashlib, json, os, sys
from collections import Counter
sys.path.insert(0, "/home/infres/yinwang/EEG_auditory")
from auditory_alignment_v3 import core

P = os.path.join(core.OUT, "plan_ext.jsonl")
raw = open(P, "rb").read(); lines = raw.decode().splitlines(keepends=True)
assert len(lines) == 2175 and hashlib.sha256(raw).hexdigest().startswith("09fe8addb505a2e2"), (len(lines), hashlib.sha256(raw).hexdigest())
ext = [json.loads(l) for l in lines]; out = []
for r in core.load_rows():
    s = r["spec"]
    if not (r["family_id"] == "A_LOCAL" and r["seed"] == 3401 and s.get("architecture") == "lag_local_tokens" and s.get("window") == "full"
            and s.get("projection_dim", 32) == 32 and s["objective"] in ("NCE", "CS_SINGLE")):
        continue
    for v, arch in [(v, a) for v in ("residual_aligned_pretrained", "residual_aligned_random") for a in ("cbramod", "reve")] + [("residual_small_capacity", "small_capacity_branch")]:
        sp = {"objective": s["objective"], "target": s["target"], "target_contract": s.get("target_contract"), "projection_dim": 32, "variant": v,
              "architecture": arch, "information_stratum": "foundation_context", "recipe": "freeze_local", "selection": "inner_group_dev_risk_epoch0_candidate"}
        h = hashlib.sha256(("ALN32_RESIDUAL" + json.dumps(sp, sort_keys=True) + r["experiment_id"]).encode()).hexdigest()[:16]
        out.append({**{k: r[k] for k in ("dataset", "subject_fold", "content_fold", "seed", "seed_scope")}, "experiment_id": f"ALN3X_{h}", "family_id": "ALN32_RESIDUAL",
                    "job_kind": "train", "spec": sp, "base_plan_row": r["experiment_id"], "registered": "ADDENDUM_10 (docs/auditory_alignment_v3/ADDENDUM_10_ALN32_RESIDUAL.md)",
                    "logical_dependencies": [r["experiment_id"]], "status": "registered_extension"})
assert len(out) == 250 and len({x["experiment_id"] for x in out}) == 250 and not {x["experiment_id"] for x in ext} & {x["experiment_id"] for x in out}
tmp = P + ".tmp"; open(tmp, "w").write("".join(lines) + "".join(json.dumps(x) + "\n" for x in out)); os.replace(tmp, P)
print("appended", dict(Counter((x["spec"]["objective"], x["spec"]["variant"]) for x in out)), "| sha256", hashlib.sha256(open(P, "rb").read()).hexdigest())
