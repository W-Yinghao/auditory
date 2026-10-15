"""ADDENDUM_11 §1: append plan_ext.jsonl block 7 (ALN3.2 paired seed panel, 900 rows) after verifying the existing 2,425 rows
(blocks 1-6; sha256 b53b138c...). Each row = its seed-3401 row with seed 3407 / 3413 (seed_scope panel); id = sha256(family +
spec + seed + base id)[:16]; dependencies re-pointed to the same-seed upstream rows."""
import hashlib, json, os, sys
from collections import Counter
sys.path.insert(0, "/home/infres/yinwang/EEG_auditory")
from auditory_alignment_v3 import core

P = os.path.join(core.OUT, "plan_ext.jsonl")
raw = open(P, "rb").read(); lines = raw.decode().splitlines(keepends=True)
assert len(lines) == 2425 and hashlib.sha256(raw).hexdigest().startswith("b53b138c51dff87c"), (len(lines), hashlib.sha256(raw).hexdigest())
ext = [json.loads(l) for l in lines]; plan = core.load_rows(); out = []
alocal = {(r["dataset"], r["subject_fold"], r["content_fold"], r["seed"], r["spec"]["objective"]): r for r in plan
          if r["family_id"] == "A_LOCAL" and r["spec"].get("architecture") == "lag_local_tokens" and r["spec"].get("window") == "full" and r["spec"].get("projection_dim", 32) == 32}
pan_ext = {(r["dataset"], r["subject_fold"], r["content_fold"], r["seed"], r["spec"]["objective"]): r for r in ext
           if r["family_id"] == "A_LOCAL" and r["spec"].get("architecture") == "lag_local_tokens" and r["spec"].get("window") == "full"}
alocal.update(pan_ext)


def sel(r):
    f, s = r["family_id"], r["spec"]
    if r["seed"] != 3401 or s.get("objective") != "NCE":
        return False
    if f == "ALN32_LOCAL_SUPPORT":
        return s["variant"] == "local_aligned1000"
    if f == "B_ALIGNED":
        return s["adaptation"] in ("pretrained_frozen", "pretrained_peft")
    if f == "ALN32_TRUE_FULL":
        return s["recipe"] == "full_onestep_v1"
    if f == "ALN32_RESIDUAL":
        return True
    return False


for r in ext:
    if not sel(r):
        continue
    for seed in (3407, 3413):
        sp = dict(r["spec"]); deps = list(r.get("logical_dependencies", []))
        if r["family_id"] == "ALN32_RESIDUAL":
            b = alocal.get((r["dataset"], r["subject_fold"], r["content_fold"], seed, "NCE"))
            assert b is not None, ("no same-seed A_LOCAL base", r["dataset"], r["subject_fold"], r["content_fold"], seed)
            deps = [b["experiment_id"]]
        h = hashlib.sha256((r["family_id"] + json.dumps(sp, sort_keys=True) + str(seed) + r["experiment_id"]).encode()).hexdigest()[:16]
        out.append({**{k: r[k] for k in ("dataset", "subject_fold", "content_fold")}, "seed": seed, "seed_scope": "panel", "experiment_id": f"ALN3X_{h}",
                    "family_id": r["family_id"], "job_kind": r.get("job_kind", "train"), "spec": sp, "base_plan_row": r["experiment_id"],
                    "registered": "ADDENDUM_11 (docs/auditory_alignment_v3/ADDENDUM_11_ALN32_SEED_PANEL.md)", "logical_dependencies": deps,
                    "status": "registered_extension"})
c = Counter((x["family_id"], x["seed"]) for x in out)
assert len(out) == 900 and len({x["experiment_id"] for x in out}) == 900 and not {x["experiment_id"] for x in ext} & {x["experiment_id"] for x in out}, (len(out), c)
tmp = P + ".tmp"; open(tmp, "w").write("".join(lines) + "".join(json.dumps(x) + "\n" for x in out)); os.replace(tmp, P)
print("appended", dict(c), "| sha256", hashlib.sha256(open(P, "rb").read()).hexdigest())
