#!/usr/bin/env python3
"""Expand registered full-experiment families. Does not train, fetch data or submit jobs."""
from __future__ import annotations
import argparse
import hashlib
import itertools
import json
from collections import Counter
from pathlib import Path
from typing import Any


def read_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as stream:
        return json.load(stream)


def digest(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def build_plan(study: dict[str, Any], registry: dict[str, Any]) -> list[dict[str, Any]]:
    policy = study["research_policy"]
    if policy["significance_gates"] or policy["automatic_negative_paper_fallback"]:
        raise ValueError("The study policy must not contain scientific admission gates or automatic negative-paper fallbacks.")
    if not policy["retain_all_valid_results"]:
        raise ValueError("All valid results must be retained.")
    rows: list[dict[str, Any]] = []
    family_ids: set[str] = set()
    for family in registry["families"]:
        if not family.get("enabled", True):
            continue
        fid = family["family_id"]
        if fid in family_ids:
            raise ValueError(f"Duplicate family id: {fid}")
        family_ids.add(fid)
        if family.get("scientific_gate") is not None:
            raise ValueError(f"{fid}: only technical dependencies, not scientific gates, are permitted.")
        axes = family["axes"]
        names = sorted(axes)
        if any(not isinstance(axes[name], list) or not axes[name] for name in names):
            raise ValueError(f"{fid}: each axis must be a non-empty list.")
        if set(names) & set(family.get("fixed", {})):
            raise ValueError(f"{fid}: fixed fields and axes must not overlap.")
        for dataset in family["datasets"]:
            if dataset not in study["cohorts"]:
                raise ValueError(f"Unknown dataset: {dataset}")
            cohort = study["cohorts"][dataset]
            for values in itertools.product(*(axes[name] for name in names)):
                spec = dict(family.get("fixed", {}))
                spec.update(zip(names, values))
                if spec.get("target") == "@cohort_default":
                    spec["target"] = cohort["target_default"]
                if spec.get("adaptation") == "resolve_by_architecture":
                    spec["adaptation"] = "pretrained_peft" if spec["architecture"] in study["foundation_registry"] else "from_scratch"
                if spec.get("context_mode") == "architecture_native":
                    spec["context_mode"] = ("padded_private_epoch_no_extra_EEG" if dataset == "private_bdf" else "foundation_segment") if spec["architecture"] in study["foundation_registry"] else "restricted_window"
                if spec.get("window") == "task_context":
                    spec["window"] = "full_context" if spec["context_mode"] == "foundation_segment" else "full"
                for fold, content, seed in itertools.product(
                    study["repeats"]["subject_folds"],
                    study["repeats"]["content_folds"][dataset],
                    study["repeats"]["seeds"],
                ):
                    signature = {"dataset":dataset, "spec":spec, "subject_fold":fold, "content_fold":content, "seed":seed}
                    row = {
                        "experiment_id": f"ALN2_{fid}_{dataset}_{digest(signature)[:16]}",
                        "family_id":fid, "module":family["module"],
                        "question":family["question"], **signature,
                        "work_type":family["work_type"],
                        "scientific_gate":None,
                        "technical_dependencies":family["technical_dependencies"],
                        "implementation_status":"requires_server_integration",
                        "status":"planned", "evidence_sha":study["evidence_sha"],
                        "reuse_signature":digest(signature),
                        "dependency_resolution":"server_must_resolve_compatible_data_and_checkpoint_ids",
                    }
                    rows.append(row)
    ids = [r["experiment_id"] for r in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("Experiment-id collision; inspect the registry before execution.")
    return rows


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "n_planned_comparison_units":len(rows),
        "unique_reuse_signatures":len({r["reuse_signature"] for r in rows}),
        "by_module":dict(sorted(Counter(r["module"] for r in rows).items())),
        "by_family":dict(sorted(Counter(r["family_id"] for r in rows).items())),
        "by_dataset":dict(sorted(Counter(r["dataset"] for r in rows).items())),
        "by_work_type":dict(sorted(Counter(r["work_type"] for r in rows).items())),
        "warning":"Comparison units are not independent participants, completed fits or a compute estimate. Staged fits and adaptation bundles contain differing amounts of work. Reuse requires server-side provenance verification.",
        "all_status":"planned", "submits_jobs":False,
    }


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    root=Path(__file__).resolve().parents[1]
    parser.add_argument("--study", type=Path, default=root/"configs/study.json")
    parser.add_argument("--families", type=Path, default=root/"configs/experiment_families.json")
    parser.add_argument("--output", type=Path, default=root/"plans/planned_comparisons.jsonl")
    args=parser.parse_args()
    rows=build_plan(read_json(args.study), read_json(args.families))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False)+"\n")
    summary=summarize(rows)
    args.output.with_suffix(".summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(summary,ensure_ascii=False,indent=2))


if __name__ == "__main__":
    main()
