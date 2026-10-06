"""Extension plan (spec 8.8; registered 2026-10-06 before any extension unit ran). Same record format and id scheme as the
package's make_plan.py; written to private/auditory_alignment_kernel_cs/planned_jobs_ext.jsonl.

E10 ext_combo            : CS_SINGLE+NCE and FMCA+NCE (losses summed at their native scales), FAU and DTU, Local / full.
E11 ext_class_balanced   : private task, class-balanced training batches (natural-distribution selection and evaluation),
                           4 objectives x 4 windows.
E12 ext_target_windows   : Ac and Lz targets in the early / late / joint windows, FAU and DTU, 4 objectives.
All: 5 subject folds x content folds x seeds 1-3, default configuration otherwise.
"""
from __future__ import annotations

import hashlib
import json
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = os.path.join(REPO, "AUDITORY_KERNEL_CS_FULL_EXPERIMENTS_SERVER_v1_20261005", "planned_jobs.jsonl")
OUT = os.path.join(REPO, "private", "auditory_alignment_kernel_cs", "planned_jobs_ext.jsonl")
OBJ = ("NCE", "FMCA", "CS_SINGLE", "CS_MULTI")


def main():
    base = [json.loads(l) for l in open(BASE)]
    proto = {ds: next(j for j in base if j["block"] == "core" and j["dataset"] == ds) for ds in ("fau", "dtu", "private_bdf")}
    jobs = []

    def add(block, ds, objective, target, window, changes=None):
        n_cf = 2 if ds in ("fau", "dtu") else 1
        for sf in range(5):
            for cf in range(n_cf):
                for seed in (1, 2, 3):
                    r = {k: v for k, v in proto[ds].items() if k not in ("experiment_id",)}
                    r = json.loads(json.dumps(r))
                    r.update({"block": block, "objective": objective, "target": target, "window": window, "subject_fold": sf,
                              "content_fold": cf, "seed": seed, "status": "planned", "extension_registered": "2026-10-06"})
                    r["config"].update(changes or {})
                    r["experiment_id"] = f"{block}_{ds}_{objective.replace('+', '_PLUS_')}_" + hashlib.sha256(json.dumps(r, sort_keys=True).encode()).hexdigest()[:16]
                    jobs.append(r)
    for ds in ("fau", "dtu"):
        for o in ("CS_SINGLE+NCE", "FMCA+NCE"):
            add("ext_combo", ds, o, "local", "full")
    for o in OBJ:
        for w in ("full", "early", "late", "joint"):
            add("ext_class_balanced", "private_bdf", o, "current_class", w, {"class_balanced_training": True})
    for ds in ("fau", "dtu"):
        for t in ("Ac", "Lz"):
            for w in ("early", "late", "joint"):
                for o in OBJ:
                    add("ext_target_windows", ds, o, t, w)
    assert len({j["experiment_id"] for j in jobs}) == len(jobs)
    with open(OUT, "w") as f:
        for j in jobs:
            f.write(json.dumps(j, sort_keys=True) + "\n")
    from collections import Counter
    print(len(jobs), Counter(j["block"] for j in jobs))


if __name__ == "__main__":
    main()
