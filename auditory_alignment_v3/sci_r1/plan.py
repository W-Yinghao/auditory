"""Round-1 task plan (SCI_R1_PREREG §2) -> private/auditory_alignment_v3/sci_r1/plan.json.

Built from plan rows and file NAMES only (unit record + checkpoint present); the record status is checked inside each job and a
non-complete unit fails its task with a reason. Continuous jobs = (dataset, content fold, subject fold); private jobs = outer fold.
Panels: P0 ALN3 lag_local full seed 3401 (S1 + TG + MD/SB + channel occlusion + first-layer patterns); P2 random-init twin of
each P0 unit (S1 + TG); P1 ALN2 lag_local full seed 3401 (S1 + TG + MD/SB + first-layer patterns); R raw reference per fold
(S1 + TG + Haufe + negative lags + PCA-32; Ac/Lz: S1 only); P3 seeds 3407/3413, P4 A_TARGETS Ac/Lz, P5 early/late/joint: S1.
"""
from __future__ import annotations

import json
import os

from auditory_alignment_v3 import core
from auditory_alignment_v3 import run as r3
from .continuous import OUT, V2_PLAN


def _have(out, eid):
    return os.path.exists(os.path.join(out, "units", f"{eid}.json")) and os.path.exists(os.path.join(out, "ckpt", f"{eid}_best.pt"))


def build():
    rows3 = r3.all_rows()
    rows2 = [json.loads(l) for l in open(V2_PLAN)]
    jobs, missing = {}, []

    def job(ds, cf, sf):
        name = f"private_sf{sf}" if ds == "private_bdf" else f"{ds}_cf{cf}_sf{sf}"
        return jobs.setdefault(name, {"name": name, "dataset": ds, "content_fold": cf, "subject_fold": sf, "tasks": []})

    def add(src, out, r, panel, **kw):
        if not _have(out, r["experiment_id"]):
            missing.append({"eid": r["experiment_id"], "panel": panel, "reason": "unit record or checkpoint absent"}); return
        s = r["spec"]; ds = r["dataset"]
        tgt = s.get("target") or core.DEFAULT_TARGET[ds]
        key = kw.pop("key", f"{r['experiment_id']}__frozen")
        seed = kw.pop("seed_override", r["seed"])
        t = {"key": key, "kind": "frozen", "source": src, "eid": r["experiment_id"], "panel": panel,
             "objective": "untrained" if kw.get("trained") is False else s["objective"], "window": s.get("window", "full"), "target": tgt,
             "seed": seed, "sf": r["subject_fold"], **kw}
        job(ds, r["content_fold"] if r["content_fold"] is not None else 0, r["subject_fold"])["tasks"].append(t)

    for r in rows3:
        s, fam, ds = r["spec"], r["family_id"], r["dataset"]
        if s.get("architecture") != "lag_local_tokens" or ds not in ("fau", "dtu", "federici", "private_bdf"):
            continue
        win, seed, d = s.get("window", "full"), r["seed"], s.get("projection_dim", 32)
        if fam in ("A_LOCAL", "E_LOCAL") and win == "full" and d == 32:
            if seed == 3401:
                add("aln3", core.OUT, r, "P0", tg=True, mdsb=True, chan=True, filt=True)
                if s["objective"] == "NCE":  # P2: untrained twin = one network per seed (fold / objective free); 3 draws
                    for s2 in (3401, 3407, 3413):
                        cf = r["content_fold"] if r["content_fold"] is not None else 0
                        tag = "private" if ds == "private_bdf" else f"{ds}__cf{cf}"
                        add("aln3", core.OUT, r, "P2", trained=False, tg=s2 == 3401, seed_override=s2,
                            key=f"random__{tag}__sf{r['subject_fold']}__s{s2}")
            elif seed in (3407, 3413):
                add("aln3", core.OUT, r, "P3")
        elif fam == "A_TARGETS" and win == "full" and seed == 3401:
            add("aln3", core.OUT, r, "P4")
        elif fam in ("A_LOCAL", "E_LOCAL") and win in ("early", "late", "joint") and seed == 3401 and d == 32:
            add("aln3", core.OUT, r, "P5", tg=win in ("early", "late"))  # within-window TG (docs/13 l.25 sensitivity)
    for r in rows2:
        s = r["spec"]
        if s.get("architecture") == "lag_local_tokens" and s.get("window") == "full" and r["seed"] == 3401 and \
                ((r["family_id"] == "A_TIME" and r["dataset"] in ("fau", "dtu", "federici")) or (r["family_id"] == "D_TASK_LOCAL" and r["dataset"] == "private_bdf")):
            add("aln2", core.V2_OUT, r, "P1", tg=True, mdsb=True, filt=True)
    for j in jobs.values():  # raw references per fold
        ds, cf, sf = j["dataset"], j["content_fold"], j["subject_fold"]
        if ds == "private_bdf":
            j["tasks"].append({"key": f"raw__private__sf{sf}", "kind": "raw", "panel": "R", "target": "current_class", "tg": True, "haufe": True})
            continue
        j["tasks"].append({"key": f"raw__{ds}__cf{cf}__sf{sf}__{core.DEFAULT_TARGET[ds]}__s3401", "kind": "raw", "panel": "R", "sf": sf,
                           "seed": 3401, "target": core.DEFAULT_TARGET[ds], "tg": True, "haufe": True, "neg": True, "pca": True})
        for tgt in sorted({t["target"] for t in j["tasks"] if t.get("panel") == "P4"}):
            j["tasks"].append({"key": f"raw__{ds}__cf{cf}__sf{sf}__{tgt}__s3401", "kind": "raw", "panel": "R4", "sf": sf, "seed": 3401, "target": tgt})
    for cf in (0, 1):  # CI contamination sensitivity: raw reference on the FAU stage-B copy without ICA (eeg_1_20_noica)
        jobs[f"fau_noica_cf{cf}"] = {"name": f"fau_noica_cf{cf}", "dataset": "fau", "content_fold": cf, "subject_fold": None, "loader": "fau_noica",
                                    "tasks": [{"key": f"rawnoica__fau__cf{cf}__sf{sf}__local__s3401", "kind": "raw", "panel": "RN", "sf": sf, "seed": 3401,
                                               "target": "local", "neg": True} for sf in range(5)]}
    order = {"R": 0, "P0": 1, "P2": 2, "P1": 3, "R4": 4, "P4": 5, "P5": 6, "P3": 7, "RN": 8}
    for j in jobs.values():
        j["tasks"].sort(key=lambda t: (order[t["panel"]], t["key"]))
    plan = {"prereg": "docs/auditory_alignment_v3/SCI_R1_PREREG.md", "jobs": sorted(jobs.values(), key=lambda j: j["name"]), "missing": missing}
    return plan


def main():
    plan = build()
    os.makedirs(OUT, mode=0o700, exist_ok=True)
    json.dump(plan, open(os.path.join(OUT, "plan.json.tmp"), "w"), indent=1); os.replace(os.path.join(OUT, "plan.json.tmp"), os.path.join(OUT, "plan.json"))
    from collections import Counter
    c = Counter((j["dataset"], t["panel"]) for j in plan["jobs"] for t in j["tasks"])
    print(len(plan["jobs"]), "jobs;", sum(c.values()), "tasks;", "missing", len(plan["missing"]))
    for k, v in sorted(c.items()):
        print(" ", k, v)


if __name__ == "__main__":
    main()
