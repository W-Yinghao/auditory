"""ADDENDUM_07 §2: append plan_ext.jsonl block 4 (ALN3.2 wave 1, 575 rows) after verifying the existing 1,500 rows (blocks 1-3;
sha256 8de864ab..., 2026-10-14 after block 3). ids ALN3X_ + sha256(family + spec + base id)[:16]. Idempotent: refuses to run twice.
  ALN32_LOCAL_SUPPORT  per A_LOCAL lag_local_tokens full NCE seed-3401 row (25): variants local_aligned1000, raw_aligned1000_ridge,
                       raw_post600_ridge
  ALN32_POSTONLY_FM    per B_ALIGNED pretrained_frozen / pretrained_peft row (100): input_support post600_zero_left
  ALN32_TRUE_FULL      per B_ALIGNED random_full / pretrained_full row (100) x recipe {full_onestep_v1, warmup_then_all_v1} x
                       backbone lr {1e-5, 3e-4} (head lr 1e-3, LLRD 1)"""
import hashlib, json, os, sys
from collections import Counter
sys.path.insert(0, "/home/infres/yinwang/EEG_auditory")
from auditory_alignment_v3 import core

P = os.path.join(core.OUT, "plan_ext.jsonl")
raw = open(P, "rb").read(); lines = raw.decode().splitlines(keepends=True)
assert len(lines) == 1500 and hashlib.sha256(raw).hexdigest().startswith("8de864abed844c72"), (len(lines), hashlib.sha256(raw).hexdigest())
ext = [json.loads(l) for l in lines]; rows = core.load_rows(); out = []


def add(fam, base, spec):
    h = hashlib.sha256((fam + json.dumps(spec, sort_keys=True) + base["experiment_id"]).encode()).hexdigest()[:16]
    out.append({**{k: base[k] for k in ("dataset", "subject_fold", "content_fold", "seed", "seed_scope")}, "experiment_id": f"ALN3X_{h}", "family_id": fam,
                "job_kind": "train", "spec": spec, "base_plan_row": base["experiment_id"],
                "registered": "ADDENDUM_07 (docs/auditory_alignment_v3/ADDENDUM_07_ALN32_SUPPORT_AND_TRUE_FULL.md)", "logical_dependencies": [],
                "status": "registered_extension"})


for r in rows:
    s = r["spec"]
    if r["family_id"] == "A_LOCAL" and r["seed"] == 3401 and s.get("architecture") == "lag_local_tokens" and s.get("window") == "full" and s["objective"] == "NCE" \
            and s.get("projection_dim", 32) == 32:
        for v in ("local_aligned1000", "raw_aligned1000_ridge", "raw_post600_ridge"):
            add("ALN32_LOCAL_SUPPORT", r, {**s, "variant": v, "input_support": "post600" if v == "raw_post600_ridge" else "aligned1000"})
for r in ext:
    if r["family_id"] != "B_ALIGNED":
        continue
    s = r["spec"]
    if s["adaptation"] in ("pretrained_frozen", "pretrained_peft"):
        add("ALN32_POSTONLY_FM", r, {**s, "input_support": "post600_zero_left"})
    else:
        for rec in ("full_onestep_v1", "warmup_then_all_v1"):
            for lr in (1e-5, 3e-4):
                if s["adaptation"] in ("random_full", "pretrained_full"):
                    add("ALN32_TRUE_FULL", r, {**s, "recipe": rec, "lr_backbone": lr, "lr_head": 1e-3, "llrd": 1.0})
c = Counter(x["family_id"] for x in out)
assert c == {"ALN32_LOCAL_SUPPORT": 75, "ALN32_POSTONLY_FM": 100, "ALN32_TRUE_FULL": 400}, c
ids = {x["experiment_id"] for x in ext}
assert len({x["experiment_id"] for x in out}) == 575 and not ids & {x["experiment_id"] for x in out}
tmp = P + ".tmp"; open(tmp, "w").write("".join(lines) + "".join(json.dumps(x) + "\n" for x in out)); os.replace(tmp, P)
print("appended", dict(c), "| new file sha256", hashlib.sha256(open(P, "rb").read()).hexdigest())
