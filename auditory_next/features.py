"""Explicit legacy-feature routing and fit-scope auditing for v2."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
from auditory5.provenance import require_slurm


def _hash(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _groups(value):
    return tuple(str(x) for x in value)


def audit_inner_scope(scope, requested_validation_groups, actual_encoder_train, outer_train_groups):
    """Pure audit: validation groups must be declared and absent from encoder fit."""
    declared = set(_groups(scope.get("validation_groups", [])))
    requested = set(_groups(requested_validation_groups))
    train = set(_groups(actual_encoder_train))
    outer = set(_groups(outer_train_groups))
    if not requested.issubset(declared):
        raise ValueError("UNRECORDED_VALIDATION_GROUP")
    if train & requested:
        raise ValueError("INNER_VALIDATION_IN_ENCODER_TRAIN")
    if not requested.issubset(outer):
        raise ValueError("VALIDATION_OUTSIDE_OUTER_TRAIN")
    return {"valid": True, "covered_groups": sorted(requested),
            "missing_groups": sorted(declared - requested),
            "coverage_n": len(requested), "declared_n": len(declared)}


def validate_feature_alignment(feature_arrays, feature_rows):
    """Check exact trial/group/label alignment and hide clinical columns."""
    rows = feature_rows.to_dict('records') if isinstance(feature_rows,pd.DataFrame) else list(feature_rows)
    if not rows:
        raise ValueError("EMPTY_FEATURE_ROWS")
    forbidden = {"clinical", "muss", "age", "device_duration", "outcome", "name", "path"}
    if isinstance(rows[0], dict) and forbidden.intersection(str(k).lower() for k in rows[0]):
        raise ValueError("CLINICAL_COLUMN_EXPOSED")
    for key in ("trial_ids", "groups", "labels"):
        if key not in feature_arrays:
            raise ValueError("MISSING_FEATURE_KEY_" + key)
    ids = np.asarray(feature_arrays["trial_ids"]).astype(str)
    groups = np.asarray(feature_arrays["groups"]).astype(str)
    labels = np.asarray(feature_arrays["labels"])
    if len(ids) != len(rows) or len(groups) != len(rows) or len(labels) != len(rows):
        raise ValueError("FEATURE_ROW_LENGTH_MISMATCH")
    row_ids = np.asarray([str(r["trial_id"]) for r in rows])
    row_groups = np.asarray([str(r["split_group_id"]) for r in rows])
    row_labels = np.asarray([r["stimulus_local_id"] for r in rows])
    if len(np.unique(ids)) != len(ids) or not np.array_equal(ids, row_ids):
        raise ValueError("FEATURE_TRIAL_ALIGNMENT")
    if not np.array_equal(groups, row_groups) or not np.array_equal(labels, row_labels):
        raise ValueError("FEATURE_METADATA_ALIGNMENT")
    if not np.isin(labels,[0,1]).all(): raise ValueError('FEATURE_BINARY_LABELS')
    for name in ('pre','post'):
        if name in feature_arrays:
            x=np.asarray(feature_arrays[name])
            if x.ndim!=2 or len(x)!=len(rows) or not np.isfinite(x).all(): raise ValueError('FEATURE_NONFINITE_OR_SHAPE')
    return {"n_rows": len(rows), "trial_ids": ids.tolist(), "groups": groups.tolist(), "labels": labels.tolist()}


class LegacyFeatureRegistry:
    """Resolve only explicit plan tasks; never infer names from fold records."""

    def __init__(self, plan, scope_registry):
        self.plan = plan
        self.scopes = {str(x.get("task", x.get("name"))): x for x in scope_registry}
        self.tasks = list(plan.get("tasks", []))

    @classmethod
    def from_dicts(cls, plan, scope_registry):
        return cls(plan, scope_registry)

    @classmethod
    def from_files(cls, plan_path, scope_registry_path):
        require_slurm()
        plan = json.loads(Path(plan_path).read_text())
        scopes = json.loads(Path(scope_registry_path).read_text())
        return cls(plan, scopes)

    def resolve_task(self, *, stage, mode, branch, outer_fold, inner_fold=None):
        matches = [t for t in self.tasks if t.get("stage") == stage and t.get("mode") == mode
                   and t.get("branch") == branch and t.get("outer_fold") == outer_fold
                   and t.get("inner_fold") == inner_fold]
        if len(matches) != 1:
            raise KeyError("EXPLICIT_TASK_NOT_UNIQUE")
        return dict(matches[0])

    def scope_for(self, task):
        name = task.get("name")
        if name not in self.scopes:
            raise KeyError("MISSING_FEATURE_SCOPE")
        return dict(self.scopes[name])

    def load_features(self, task, feature_root):
        """Load one explicit task's arrays; caller supplies private row loading."""
        require_slurm()
        task = self.resolve_task(stage=task["stage"], mode=task["mode"], branch=task["branch"],
                                 outer_fold=task["outer_fold"], inner_fold=task.get("inner_fold"))
        folder = Path(feature_root) / task["name"]
        with np.load(folder / "features.npz", allow_pickle=False) as z:
            arrays = {k: z[k] for k in z.files}
        arrays['labels']=arrays['y']
        rows_path = folder / "feature_rows.parquet"
        if not rows_path.exists():
            raise FileNotFoundError("MISSING_FEATURE_ROWS")
        columns=['trial_id','record_id','candidate_id','split_group_id','stimulus_local_id']
        rows = pd.read_parquet(rows_path,columns=columns).to_dict('records')
        aligned = validate_feature_alignment(arrays, rows)
        scope = self.scope_for(task)
        scope_id = str(scope.get("feature_scope_id", scope.get("scope_hash", "")))
        if not scope_id:
            scope_id = _hash({"task": task["name"], "fit_groups": task.get("fit_groups", []),
                              "validation_groups": task.get("validation_groups", []),
                              "test_groups": task.get("test_groups", [])})
        return {"zpre": arrays.get("pre"), "zpost": arrays.get("post"), "rows": rows,
                "actual_fit_groups": list(scope.get("fit_groups", task.get("fit_groups", []))),
                "validation_groups": list(scope.get("validation_groups", task.get("validation_groups", []))),
                "test_groups": list(scope.get("test_groups", task.get("test_groups", []))),
                "feature_scope_id": scope_id, "feature_scope_hash": _hash(scope), "alignment": aligned}


def final_head_scope(outer_train_groups, qualified_groups):
    """Return the explicit final head fit scope; never expand to unrecorded groups."""
    outer, qualified = set(_groups(outer_train_groups)), set(_groups(qualified_groups))
    if not qualified.issubset(outer):
        raise ValueError("HEAD_GROUP_OUTSIDE_OUTER_TRAIN")
    return {"fit_groups": sorted(qualified), "outer_train_groups": sorted(outer),
            "scope": "outer_train_qualified_groups"}
