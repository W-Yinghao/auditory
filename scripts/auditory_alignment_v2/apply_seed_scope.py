"""Marks out-of-scope plan rows (seed_scope.json) and out-of-scope donors as skipped for pool workers that still read an
older queue snapshot: pool/<queue>/<eid>.failed with content DESCOPED (workers and keepers skip .failed). Rows that are
complete or currently claimed are left alone. Re-enabling = delete markers whose content starts with DESCOPED."""
import glob, json, os, sys
sys.path.insert(0, "/home/infres/yinwang/EEG_auditory")
from auditory_alignment_v2.run import PLAN
O = "/home/infres/yinwang/EEG_auditory/private/auditory_alignment_v2"
SC = json.load(open(f"{O}/seed_scope.json"))
R = [json.loads(l) for l in open(PLAN)]
out = [r["experiment_id"] for r in R if r["seed"] not in SC["seeds"] and r["family_id"] not in SC["exempt_families"]]
from auditory_alignment_v2.donor import donor_id, sources_for
for a in ("cbramod", "reve"):
    for s in (3401, 3407, 3413):
        if s in SC["seeds"]: continue
        for d in ("partial", "full"):
            for t in ("fau", "dtu"):
                out.append(donor_id(a, d, sources_for("B_AUDITORY_CONTINUE", t), s))
        out.append(donor_id(a, "full", sources_for("D_FM_PUBLIC", "private_bdf"), s))
n = skipped = 0
for q in ("queue_small", "queue_fm"):
    C = f"{O}/pool/{q}"
    for e in out:
        if os.path.exists(f"{O}/units/{e}.json") or os.path.exists(f"{O}/donors/{e}.pt") or os.path.isdir(f"{C}/{e}.claim"):
            skipped += 1; continue
        if not os.path.exists(f"{C}/{e}.failed"):
            open(f"{C}/{e}.failed", "w").write("DESCOPED seed_scope.json 2026-10-07\n"); n += 1
print(len(out), "out-of-scope ids;", n, "markers written;", skipped, "left alone (complete or claimed)")
