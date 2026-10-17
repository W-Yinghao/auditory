"""Read-only pairing of normalized metadata. Does not inspect outcome values."""
from __future__ import annotations
from typing import Any, Iterable

DEFAULT_FIELDS = ("dataset", "subject_fold", "content_fold", "seed", "split_hash", "target_hash", "access_contract", "evaluation_version")

def audit_pairs(records: Iterable[dict[str, Any]], reference_role: str, candidate_role: str,
                fields: tuple[str, ...] = DEFAULT_FIELDS) -> dict[str, Any]:
    if not reference_role or not candidate_role or reference_role == candidate_role:
        raise ValueError("two distinct nonempty roles are required")
    if not fields or "seed" not in fields or "dataset" not in fields:
        raise ValueError("pairing fields must include seed and dataset")
    selected: dict[str, dict[tuple[Any, ...], dict[str, Any]]] = {reference_role: {}, candidate_role: {}}
    ignored_status = 0
    for rec in records:
        role = rec.get("role")
        if role not in selected:
            continue
        if rec.get("status") != "complete":
            ignored_status += 1
            continue
        if not rec.get("record_id"):
            raise ValueError("complete rows require a record_id")
        missing = [f for f in fields if f not in rec]
        if missing:
            raise ValueError(f"{rec['record_id']}: missing {missing}")
        key = tuple(rec[f] for f in fields)
        if key in selected[role]:
            raise ValueError(f"ambiguous duplicate for role {role} at key {key}; deduplicate by provenance, not score")
        selected[role][key] = rec
    left, right = selected[reference_role], selected[candidate_role]
    all_keys = sorted(set(left) | set(right), key=repr)
    paired, missing = [], []
    for key in all_keys:
        common = dict(zip(fields, key))
        if key in left and key in right:
            paired.append({"key": common,"reference_id":left[key]["record_id"],"candidate_id":right[key]["record_id"],
                           "reference_seed_scope":left[key].get("seed_scope","unspecified"),
                           "candidate_seed_scope":right[key].get("seed_scope","unspecified")})
        else:
            missing.append({"key": common,"missing_role":candidate_role if key in left else reference_role})
    return {"pairs": paired,"missing":missing,"n_pairs":len(paired),"n_missing":len(missing),
            "incomplete_rows_ignored":ignored_status,"outcomes_used_for_selection":False,
            "scope":"metadata equality only; full dependency and leakage checks remain server responsibility"}
