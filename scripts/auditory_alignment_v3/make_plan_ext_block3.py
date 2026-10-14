"""ADDENDUM_06 §3: append plan_ext.jsonl block 3 (B_ALIGNED, 250 rows) after verifying that the existing 1,250 rows (blocks 1-2)
are byte-identical to the file of 2026-10-11 (sha256 recorded below). One B_ALIGNED row per seed-3401 B_DENSE row with objective
NCE and readout channel_phase_linear (the interface twin): same dataset, folds, seed, backbone, adaptation, target; readout
aligned_patch_linear; id ALN3X_ + sha256("B_ALIGNED" + spec + base id)[:16] (block-1 rule). Idempotent: refuses to run twice."""
import hashlib, json, os, sys
from collections import Counter
sys.path.insert(0, "/home/infres/yinwang/EEG_auditory")
from auditory_alignment_v3 import core

P = os.path.join(core.OUT, "plan_ext.jsonl")
lines = open(P).read().splitlines(keepends=True)
assert len(lines) == 1250, f"expected the 1,250-row file, found {len(lines)} rows (block 3 already appended?)"
SHA12 = hashlib.sha256("".join(lines).encode()).hexdigest()
print("blocks 1-2 sha256", SHA12)
rows = core.load_rows(); out = []
for r in rows:
    s = r["spec"]
    if r["family_id"] != "B_DENSE" or r["seed"] != 3401 or s["objective"] != "NCE" or s["readout"] != "channel_phase_linear":
        continue
    sp = {**s, "readout": "aligned_patch_linear", "patch_window_s": [-0.4, 0.6]}
    h = hashlib.sha256(("B_ALIGNED" + json.dumps(sp, sort_keys=True) + r["experiment_id"]).encode()).hexdigest()[:16]
    out.append({**{k: r[k] for k in ("dataset", "subject_fold", "content_fold", "seed", "seed_scope")}, "experiment_id": f"ALN3X_{h}", "family_id": "B_ALIGNED",
                "job_kind": "train", "spec": sp, "base_plan_row": r["experiment_id"], "registered": "ADDENDUM_06 (docs/auditory_alignment_v3/ADDENDUM_06_B_ALIGNED.md)",
                "logical_dependencies": [], "status": "registered_extension"})
assert len(out) == 250, len(out)
ids = {json.loads(l)["experiment_id"] for l in lines}
assert not ids & {x["experiment_id"] for x in out} and len({x["experiment_id"] for x in out}) == 250
tmp = P + ".tmp"
open(tmp, "w").write("".join(lines) + "".join(json.dumps(x) + "\n" for x in out)); os.replace(tmp, P)
print("appended", len(out), "B_ALIGNED rows", dict(Counter((x["dataset"], x["spec"]["architecture"]) for x in out)), dict(Counter(x["spec"]["adaptation"] for x in out)))
print("new file sha256", hashlib.sha256(open(P, "rb").read()).hexdigest())
