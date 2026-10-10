"""Queue of plan rows the runner can execute now; canonical duplicates are placed after every source row."""
import json, sys
sys.path.insert(0, "/home/infres/yinwang/EEG_auditory")
from auditory_alignment_v2.registry import integrated
from auditory_alignment_v2.run import PLAN, canonical
R = [json.loads(l) for l in open(PLAN)]
pri = {"A_TIME": 0, "D_TASK_LOCAL": 1, "S_CONTROLS": 2, "A_TARGET_TIME": 3, "A_ANCHOR": 4, "C_COVERAGE": 5, "C_ATTENTION": 6, "C_SELECTION": 7}
SC = json.load(open("/home/infres/yinwang/EEG_auditory/private/auditory_alignment_v2/seed_scope.json"))
in_scope = lambda r: r["seed"] in SC["seeds"] or r["family_id"] in SC["exempt_families"]  # user 2026-10-07: one seed
rows = [(i, r) for i, r in enumerate(R) if integrated(r) and in_scope(r)]
rows.sort(key=lambda t: (pri.get(t[1]["family_id"], 9), t[1]["seed"], t[1]["subject_fold"], t[1]["content_fold"], t[1]["dataset"]))
seen, first, dup = set(), [], []
for i, r in rows:
    c = canonical(r)
    (dup if c in seen else first).append((i, r)); seen.add(c)
out = sys.argv[1]
import os
with open(out + ".tmp", "w") as f:
    for i, r in first + dup:
        f.write(f"{r['experiment_id']}|{i}\n")
os.replace(out + ".tmp", out)
from collections import Counter
print(len(first) + len(dup), "rows;", len(first), "unique models;", len(dup), "reuse rows", Counter(r["family_id"] for _, r in first + dup))
