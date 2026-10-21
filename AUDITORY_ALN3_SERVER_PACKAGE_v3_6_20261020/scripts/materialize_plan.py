#!/usr/bin/env python3
"""Expand the scientific specification, without submitting jobs or reading EEG.

IDs here are draft descriptors. The server must bind actual data/code/checkpoint
hashes before producing immutable execution signatures. A person-fold slice does
not enter the whole-group-excluded training descriptor.
"""
import argparse
import hashlib
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def key(prefix, value):
    digest = hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return prefix + digest[:16]


def expand(spec, include_s=False):
    train, evaluations = [], []
    for tool, group, cf in itertools.product(spec["public_tools"], spec["heldout_groups"], spec["content_folds"]):
        unit = {"kind": "fau_whole_group_source", "tool": tool, "excluded_group": group,
                "content_fold": cf, "seed": spec["seed"]}
        unit["draft_id"] = key("S36TRAIN_", unit)
        train.append(unit)
        for pf in spec["person_folds"]:
            ev = {"kind": "fau_group_evaluation", "source_draft_id": unit["draft_id"],
                  "tool": tool, "target_group": group, "content_fold": cf,
                  "person_fold": pf, "seed": spec["seed"]}
            evaluations.append(dict(ev, draft_id=key("S36EVAL_", ev)))
    for dataset in ("dtu", "fau"):
        for tool, cf, pf in itertools.product(spec["public_tools"], spec["content_folds"], spec["person_folds"]):
            ev = {"kind": "existing_pooled_frozen", "dataset": dataset, "tool": tool,
                  "content_fold": cf, "person_fold": pf, "seed": spec["seed"],
                  "parent_binding_required": True}
            evaluations.append(dict(ev, draft_id=key("S36EVAL_", ev)))
    arms = spec["private_arms"] + (["compatible_existing_S"] if include_s else [])
    for arm, pf in itertools.product(arms, spec["person_folds"]):
        ev = {"kind": "private_frozen", "arm": arm, "person_fold": pf,
              "seed": spec["seed"], "parent_binding_required": True}
        evaluations.append(dict(ev, draft_id=key("S36EVAL_", ev)))
    counts = spec["expected_counts"]
    assert len(train) == counts["unique_fau_source_training"]
    assert len(evaluations) == counts["core_evaluation_bundles"] + (counts["optional_S_bundles"] if include_s else 0)
    assert len({u["draft_id"] for u in train + evaluations}) == len(train) + len(evaluations)
    return {"version": spec["version"], "status": "draft_requires_actual_server_binding",
            "baseline_commit": spec["baseline_commit"], "no_jobs_submitted": True,
            "unique_train_count": len(train), "evaluation_bundle_count": len(evaluations),
            "source_training": train, "evaluations": evaluations}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--spec", type=Path, default=ROOT / "plans/round1.json")
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--include-compatible-s", action="store_true")
    args = ap.parse_args()
    result = expand(json.loads(args.spec.read_text()), args.include_compatible_s)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"output": str(args.output.resolve()), "unique_training": result["unique_train_count"],
                      "evaluation_bundles": result["evaluation_bundle_count"], "status": result["status"]}))


if __name__ == "__main__":
    main()
