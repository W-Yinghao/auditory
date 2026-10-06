"""Generate full training-unit manifests. Does NOT launch jobs or read EEG.

Counts are planning arithmetic. Changes to available identities/content require
an updated manifest, not fabricated data to meet a target count.
"""
from __future__ import annotations
import argparse
from collections import Counter
import copy
import hashlib
import itertools
import json
from pathlib import Path


def build_plan(cfg: dict) -> list[dict]:
    jobs: list[dict] = []
    objectives = cfg["objectives"]
    def add(block, ds, objective, target, window="full", changes=None):
        dataset = cfg["datasets"][ds]
        base = copy.deepcopy(cfg["defaults"])
        if "audio_projection" in dataset:
            base["audio_projection"] = dataset["audio_projection"]
        changes = changes or {}
        base.update(changes)
        for sf, cf, seed in itertools.product(range(cfg["subject_folds"]), range(dataset["content_folds"]), cfg["seeds"]):
            r = {
                "family": cfg["experiment_family"], "block": block,
                "dataset": ds, "objective": objective, "target": target, "window": window,
                "subject_fold": sf, "content_fold": cf, "seed": seed,
                "train_population": changes.get("train_population", dataset["train_population"]),
                "config": copy.deepcopy(base),
                "evaluation_protocol": dataset["evaluation_protocol"],
                "reference_sha": cfg["reference_sha"],
                "status": "planned"
            }
            digest = hashlib.sha256(json.dumps(r, sort_keys=True).encode()).hexdigest()[:16]
            r["experiment_id"] = f"{block}_{ds}_{objective}_{digest}"
            jobs.append(r)

    for ds, dataset in cfg["datasets"].items():
        for objective, (target, window) in itertools.product(objectives, dataset["scenarios"]):
            add("core", ds, objective, target, window)

    ex = cfg["extensions"]
    o = ex["optimization"]
    if o["enabled"]:
        for ds in o["datasets"]:
            target = "current_class" if ds == "private_bdf" else "local"
            for objective in objectives:
                for d in o["projection_dims"]:
                    add("optimization", ds, objective, target, changes={"projection_dim": d})
                for n in o["kernel_rows"]:
                    add("optimization", ds, objective, target, changes={"kernel_rows": n})
            for temperature in o["nce_temperatures"]:
                add("optimization", ds, "NCE", target, changes={"temperature": temperature})
            for ridge in o["fmca_relative_ridges"]:
                add("optimization", ds, "FMCA", target, changes={"fmca_relative_ridge": ridge})
            for multiplier in o["cs_single_bandwidth_multipliers"]:
                add("optimization", ds, "CS_SINGLE", target, changes={"bandwidth_multiplier": multiplier})
        for ds in o["frozen_audio_projection_datasets"]:
            for objective in objectives:
                add("optimization", ds, objective, "local", changes={"audio_projection": "frozen_initial_projection"})

    if ex["attention"]["enabled"]:
        for ds, objective, target in itertools.product(ex["attention"]["datasets"], objectives, ex["attention"]["targets"]):
            add("attention", ds, objective, target, changes={"training_task": "competing_speech_attended_alignment"})
    if ex["exclude_CI_training"]["enabled"]:
        c = ex["exclude_CI_training"]
        for objective, target in itertools.product(objectives, c["targets"]):
            add("exclude_CI_training", c["dataset"], objective, target, changes={"train_population": "TH_HA", "test_panel": "same_as_joint_training"})
    if ex["equal_width"]["enabled"]:
        for ds, objective in itertools.product(ex["equal_width"]["datasets"], objectives):
            target = "envelope" if ds == "federici" else "local"
            add("equal_width", ds, objective, target, window="late_equalwidth")
    if ex["wrong_pair_training"]["enabled"]:
        for ds, objective in itertools.product(ex["wrong_pair_training"]["datasets"], objectives):
            target = "current_class" if ds == "private_bdf" else "envelope" if ds == "federici" else "local"
            add("wrong_pair_training", ds, objective, target, changes={"pairing": "training_side_mismatch_preserving_declared_structure"})
    ids = [r["experiment_id"] for r in jobs]
    if len(ids) != len(set(ids)):
        raise RuntimeError("Duplicate experiment IDs")
    return jobs


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--config", type=Path, default=Path("configs/full_experiments.json"))
    p.add_argument("--output", type=Path, default=Path("planned_jobs.jsonl"))
    a=p.parse_args()
    cfg=json.loads(a.config.read_text(encoding="utf-8"))
    jobs=build_plan(cfg)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    with a.output.open("w",encoding="utf-8") as f:
        for job in jobs:
            f.write(json.dumps(job,ensure_ascii=False,sort_keys=True)+"\n")
    summary={
        "total_planned_fits":len(jobs),
        "by_block":dict(Counter(j["block"] for j in jobs)),
        "by_dataset":dict(Counter(j["dataset"] for j in jobs)),
        "by_objective":dict(Counter(j["objective"] for j in jobs)),
        "all_status_planned":all(j["status"]=="planned" for j in jobs),
        "launched":False,
        "content_identity_note":"Resolve actual server splits before dispatch; this script does not inspect data."
    }
    a.output.with_suffix(".summary.json").write_text(json.dumps(summary,indent=2,ensure_ascii=False),encoding="utf-8")
    print(json.dumps(summary,indent=2,ensure_ascii=False))

if __name__=="__main__": main()
