"""Metadata-only input contract for the v2.1 N2 experiment.

This module consumes the future N2 design bag metadata, the completed
metadata-only input-preflight cases, and the frozen five-fold split.  It never
opens EEG feature payloads and performs no fit.  Its PASS is an execution
input receipt: every outer fold must retain the same role rules and source
scope before a downstream N2 learner may be considered.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

from .runtime import digest, require_slurm


H_BAG_COLUMNS = (
    "previous_code_1_proportion", "previous_code_2_proportion",
    "previous_code_unknown_proportion", "previous_run_run_1_proportion",
    "previous_run_run_2_proportion", "previous_run_run_3_5_proportion",
    "previous_run_run_6_plus_proportion", "previous_run_unknown_proportion",
    "gap_mean", "gap_present", "position_mean", "position_squared",
    "gap_std", "position_std", "block_count", "time_coverage_s",
)
ROLE_MIN_GROUPS = {"A": 12, "B": 3, "C": 4, "D": 4, "E": 3}
ROLES = ("A", "B", "C", "D", "E")
EXPECTED_OUTER_FOLDS = 5
EXPECTED_RAW_FEATURE_DIMENSIONS = {"post": 64, "pre": 64}
EXPECTED_PCA_DIMENSION = 8
REQUIRED_BAG_COLUMNS = {
    "bag_id", "matched_pair_id", "trial_id", "candidate_id", "record_id",
    "segment_id", "split_group_id", "stimulus_local_id", "A_half", "k",
    "A_block_id", "physical_block_id",
}


def _json(path: Path) -> Any:
    return json.loads(path.read_text())


def _safe_path(root: Path, value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else root / path


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
    path.chmod(0o600)


def _write_frame(path: Path, frame: pd.DataFrame) -> None:
    frame.to_parquet(path, index=False)
    path.chmod(0o600)


def _as_groups(values: Iterable[Any]) -> set[str]:
    return {str(value) for value in (values or [])}


def _case_roles(case: dict[str, Any]) -> dict[str, list[str]]:
    raw = case.get("roles") or case.get("role_groups")
    if not isinstance(raw, dict) or set(raw) != set(ROLES):
        raise ValueError("N2_INPUT_ROLE_SCHEMA")
    roles = {role: sorted(_as_groups(raw[role])) for role in ROLES}
    all_groups: list[str] = []
    for role in ROLES:
        if len(roles[role]) < ROLE_MIN_GROUPS[role]:
            raise ValueError("N2_INPUT_ROLE_SUPPORT")
        all_groups.extend(roles[role])
    if len(all_groups) != len(set(all_groups)):
        raise ValueError("N2_INPUT_ROLE_OVERLAP")
    return roles


def _preflight_cases(cases: Any) -> dict[int, dict[str, Any]]:
    if isinstance(cases, dict):
        cases = cases.get("cases", [])
    if not isinstance(cases, list):
        raise ValueError("N2_INPUT_CASES_SCHEMA")
    selected = [case for case in cases
                if isinstance(case, dict) and case.get("packet") == "N1"
                and case.get("mode") == "R_SIM"]
    by_fold: dict[int, dict[str, Any]] = {}
    for case in selected:
        fold = int(case.get("outer_fold", -1))
        if fold in by_fold:
            raise ValueError("N2_INPUT_DUPLICATE_PREFLIGHT_FOLD")
        by_fold[fold] = case
    if set(by_fold) != set(range(EXPECTED_OUTER_FOLDS)):
        raise ValueError("N2_INPUT_FIVE_PREFLIGHT_FOLDS_REQUIRED")
    return by_fold


def _frozen_folds(value: Any) -> dict[int, dict[str, Any]]:
    folds = value.get("folds", []) if isinstance(value, dict) else value
    if not isinstance(folds, list) or len(folds) != EXPECTED_OUTER_FOLDS:
        raise ValueError("N2_INPUT_FIVE_FOLDS_REQUIRED")
    output: dict[int, dict[str, Any]] = {}
    for fold in folds:
        number = int(fold.get("outer_fold", fold.get("fold", -1)))
        if number in output or number not in range(EXPECTED_OUTER_FOLDS):
            raise ValueError("N2_INPUT_FOLD_SCHEMA")
        output[number] = fold
    if set(output) != set(range(EXPECTED_OUTER_FOLDS)):
        raise ValueError("N2_INPUT_FIVE_FOLDS_REQUIRED")
    return output


def validate_h_bag_metadata(metadata: pd.DataFrame) -> dict[str, Any]:
    """Validate the 16-column H_BAG contract without reading EEG features."""
    if not isinstance(metadata, pd.DataFrame):
        raise ValueError("N2_INPUT_H_BAG_TYPE")
    missing = sorted(set(H_BAG_COLUMNS) - set(metadata.columns))
    if missing:
        raise ValueError("N2_INPUT_H_BAG_COLUMNS:" + ",".join(missing))
    numeric = {}
    for column in H_BAG_COLUMNS:
        numeric[column] = bool(pd.to_numeric(metadata[column], errors="coerce").notna().all())
    if not all(numeric.values()):
        raise ValueError("N2_INPUT_H_BAG_NONNUMERIC")
    return {"rows": int(len(metadata)), "columns": list(H_BAG_COLUMNS),
            "column_count": len(H_BAG_COLUMNS), "numeric": numeric}


def eligible_two_half_candidates(bags: pd.DataFrame) -> tuple[set[str], dict[str, Any]]:
    """Return only candidates with at least one bag in both frozen halves."""
    if not isinstance(bags, pd.DataFrame) or not REQUIRED_BAG_COLUMNS.issubset(bags.columns):
        raise ValueError("N2_INPUT_BAG_SCHEMA")
    ids = ["trial_id", "candidate_id", "record_id", "segment_id", "split_group_id",
           "bag_id", "matched_pair_id"]
    if bags[ids].isna().any().any():
        raise ValueError("N2_INPUT_BAG_ID_SCHEMA")
    if bags.trial_id.astype(str).duplicated().any():
        raise ValueError("N2_INPUT_DUPLICATE_MEMBER")
    halves = pd.to_numeric(bags.A_half, errors="coerce")
    labels = pd.to_numeric(bags.stimulus_local_id, errors="coerce")
    if halves.isna().any() or not halves.isin([0, 1]).all() or labels.isna().any() or not labels.isin([0, 1]).all():
        raise ValueError("N2_INPUT_LABEL_HALF_SCHEMA")
    if pd.to_numeric(bags.k, errors="coerce").ne(8).any():
        raise ValueError("N2_INPUT_FIXED_K8")
    for bag_id, part in bags.groupby(bags.bag_id.astype(str), sort=False):
        if len(part) != 8 or part[["candidate_id", "record_id", "segment_id",
                                   "stimulus_local_id", "A_half"]].nunique().max() != 1:
            raise ValueError("N2_INPUT_BAG_STRUCTURE")
        block_counts = part.groupby(part.physical_block_id.astype(str)).size()
        if len(block_counts) < 2 or block_counts.max() > 4:
            raise ValueError("N2_INPUT_BAG_BLOCK_STRUCTURE")
    for pair_id, part in bags.groupby(bags.matched_pair_id.astype(str), sort=False):
        if set(part.stimulus_local_id.astype(int)) != {0, 1}:
            raise ValueError("N2_INPUT_PAIR_CLASS_STRUCTURE")
    by_candidate = bags.assign(_candidate=bags.candidate_id.astype(str)).groupby("_candidate")
    half_counts = {str(candidate): sorted(set(part.A_half.astype(int)))
                   for candidate, part in by_candidate}
    eligible = {candidate for candidate, halves_seen in half_counts.items()
                if halves_seen == [0, 1]}
    detail = {"candidate_denominator": len(half_counts),
              "candidate_both_half_numerator": len(eligible),
              "candidate_unsupported": sorted(set(half_counts) - eligible),
              "half_counts": half_counts}
    return eligible, detail


def _source_scope(case: dict[str, Any], roles: dict[str, list[str]]) -> dict[str, Any]:
    """Require N2 source encoder/scaler groups to exclude B/C/D/E."""
    holdout = set().union(*(set(roles[role]) for role in ("B", "C", "D", "E")))
    a_groups = set(roles["A"])
    receipt = case.get("encoder_receipt") or {}
    encoder = _as_groups(receipt.get("encoder_fit_groups", receipt.get("actual_train_groups", [])))
    scaler = _as_groups(receipt.get("scaler_train_groups", []))
    encoder_bad = sorted(encoder & holdout)
    scaler_bad = sorted(scaler & holdout)
    present = bool(encoder) and bool(scaler)
    return {"status": "PASS" if present and not encoder_bad and not scaler_bad
            else "BLOCKED",
            "encoder_fit_groups": sorted(encoder), "scaler_train_groups": sorted(scaler),
            "encoder_excludes_BCD_E": not encoder_bad,
            "scaler_excludes_BCD_E": not scaler_bad,
            "encoder_fit_subset_A": encoder <= a_groups,
            "scaler_fit_subset_A": scaler <= a_groups,
            "encoder_fit_outside_retained_A": sorted(encoder - a_groups),
            "scaler_fit_outside_retained_A": sorted(scaler - a_groups),
            "missing_scope_receipt": not present,
            "bad_encoder_groups": encoder_bad, "bad_scaler_groups": scaler_bad}


def _feature_hash_status(case: dict[str, Any]) -> dict[str, Any]:
    hashes = case.get("feature_file_hashes") or {}
    required = ("features.npz", "feature_rows.parquet")
    rows = {name: hashes.get(name) for name in required}
    passed = all(isinstance(item, dict) and item.get("exists") and item.get("hash_match")
                 and item.get("sha256") for item in rows.values())
    return {"status": "PASS" if passed else "BLOCKED", "files": rows}


def _dimension_status(case: dict[str, Any]) -> dict[str, Any]:
    dimensions = case.get("dimensions") or {}
    post = dimensions.get("P_header", dimensions.get("post"))
    pre = dimensions.get("B_header", dimensions.get("pre"))
    # A source preflight records the R_SIM payloads as P/B.  N2 downstream
    # preprocessing is fixed to eight PCA components for both payloads.
    passed = post == EXPECTED_RAW_FEATURE_DIMENSIONS["post"] and pre == EXPECTED_RAW_FEATURE_DIMENSIONS["pre"]
    return {"status": "PASS" if passed else "BLOCKED", "post_raw": post,
            "pre_raw": pre, "post_pca": EXPECTED_PCA_DIMENSION,
            "pre_pca": EXPECTED_PCA_DIMENSION}


def _role_counts(bags: pd.DataFrame, roles: dict[str, list[str]], fold: int,
                 eligible_candidates: set[str]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    selected = bags.loc[bags.candidate_id.astype(str).isin(eligible_candidates)].copy()
    selected["_group"] = selected.split_group_id.astype(str)
    records: list[dict[str, Any]] = []
    members: list[dict[str, Any]] = []
    for role in ROLES:
        groups = set(roles[role])
        part = selected.loc[selected._group.isin(groups)].copy()
        class_counts = {str(label): int((part.stimulus_local_id.astype(int) == label).sum())
                        for label in (0, 1)}
        bag_counts = {str(label): int(part.loc[part.stimulus_local_id.astype(int) == label,
                                               "bag_id"].astype(str).nunique()) for label in (0, 1)}
        half_counts = {str(half): int((part.A_half.astype(int) == half).sum()) for half in (0, 1)}
        records.append({"outer_fold": int(fold), "role": role,
                        "group_count": int(part._group.nunique()),
                        "group_min_required": ROLE_MIN_GROUPS[role],
                        "bag_count": int(part.bag_id.astype(str).nunique()),
                        "pair_count": int(part.matched_pair_id.astype(str).nunique()),
                        "member_trial_count": int(part.trial_id.astype(str).nunique()),
                        "candidate_count": int(part.candidate_id.astype(str).nunique()),
                        "class_member_counts": class_counts,
                        "class_bag_counts": bag_counts,
                        "half_member_counts": half_counts,
                        "class_support": all(value > 0 for value in class_counts.values()),
                        "group_support": int(part._group.nunique()) >= ROLE_MIN_GROUPS[role]})
        for row in part.itertuples(index=False):
            members.append({"outer_fold": int(fold), "role": role,
                            "candidate_id": str(row.candidate_id),
                            "bag_id": str(row.bag_id),
                            "matched_pair_id": str(row.matched_pair_id),
                            "trial_id": str(row.trial_id),
                            "split_group_id": str(row.split_group_id),
                            "stimulus_local_id": int(row.stimulus_local_id),
                            "A_half": int(row.A_half)})
    return records, members


def build_fold_support_manifest(bags: pd.DataFrame, cases: Any, folds: Any) -> dict[str, Any]:
    """Build all five fold/role receipts; never select a passing fold subset."""
    preflight = _preflight_cases(cases)
    frozen = _frozen_folds(folds)
    eligible, candidate_detail = eligible_two_half_candidates(bags)
    fold_rows: list[dict[str, Any]] = []
    role_rows: list[dict[str, Any]] = []
    members: list[dict[str, Any]] = []
    for number in range(EXPECTED_OUTER_FOLDS):
        case = preflight[number]
        roles = _case_roles(case)
        frozen_groups = set().union(*(_as_groups(frozen[number].get("train_groups", [])),
                                      _as_groups(frozen[number].get("test_groups", []))))
        role_groups = set().union(*(set(groups) for groups in roles.values()))
        # N1 R_SIM preflight may deliberately restrict its source cohort to a
        # subset of the frozen split groups.  Every role group must still come
        # from that split; requiring equality would mistake that source-scope
        # restriction for a role leak.
        role_alignment = role_groups <= frozen_groups
        source_scope = _source_scope(case, roles)
        feature_hashes = _feature_hash_status(case)
        dimensions = _dimension_status(case)
        role_counts, fold_members = _role_counts(bags, roles, number, eligible)
        role_rows.extend(role_counts)
        members.extend(fold_members)
        role_pass = all(row["group_support"] and row["class_support"] for row in role_counts)
        case_pass = case.get("status") == "PASS"
        status = "PASS" if role_alignment and role_pass and case_pass and source_scope["status"] == "PASS" and feature_hashes["status"] == "PASS" and dimensions["status"] == "PASS" else "BLOCKED"
        reasons = []
        if not role_alignment:
            reasons.append("ROLE_GROUPS_DO_NOT_MATCH_FROZEN_SPLIT")
        if not role_pass:
            reasons.append("ROLE_BAG_OR_CLASS_SUPPORT")
        if not case_pass:
            reasons.append("INPUT_PREFLIGHT_CASE_NOT_PASS")
        if source_scope["status"] != "PASS":
            reasons.append("N2_ENCODER_SCALER_SCOPE")
        if feature_hashes["status"] != "PASS":
            reasons.append("SOURCE_FEATURE_HASH_RECEIPT")
        if dimensions["status"] != "PASS":
            reasons.append("POST_PRE_DIMENSION_OR_PCA")
        fold_rows.append({"outer_fold": number, "status": status,
                          "reasons": reasons, "preflight_case": str(case.get("case", "")),
                          "role_alignment": role_alignment,
                          "role_support": role_pass, "preflight_pass": case_pass,
                          "source_scope": source_scope, "feature_hashes": feature_hashes,
                          "source_feature_file_hashes": {
                              name: item.get("sha256") if isinstance(item, dict) else None
                              for name, item in feature_hashes["files"].items()},
                          "dimensions": dimensions,
                          "candidate_both_half_count": len(eligible),
                          "candidate_denominator": candidate_detail["candidate_denominator"],
                          "role_counts": role_counts})
    return {"status": "PASS" if all(row["status"] == "PASS" for row in fold_rows) else "BLOCKED",
            "folds": fold_rows, "role_counts": role_rows, "members": members,
            "candidate_detail": candidate_detail,
            "all_five_folds_required": True, "passing_fold_subset_selection": False}


def _resolve_paths(root: Path, config: dict[str, Any]) -> dict[str, Path]:
    block = config.get("n2_inputs", config)
    if not isinstance(block, dict):
        block = {}
    design_run = str(block.get("n2_design_run", "n2_design_001"))
    preflight_run = str(block.get("input_preflight_run", "input_preflight_003"))
    design = root / "private/auditory_v21" / design_run
    preflight = root / "private/auditory_v21" / preflight_run
    split = _safe_path(root, block.get("split_path", "private/auditory5_v1/splits/splits_001/folds.json"))
    return {
        "matched_bags": _safe_path(root, block.get("matched_bags_path", design / "matched_bags.parquet")),
        "h_bag": _safe_path(root, block.get("h_bag_metadata_path", design / "matched_h_bag_metadata.parquet")),
        "cases": _safe_path(root, block.get("cases_path", preflight / "cases.json")),
        "split": split,
    }


def run(root: Path, private: Path, public: Path, report: Path, config: dict) -> dict[str, Any]:
    """Run the zero-fit N2 experiment-input receipt under Slurm."""
    require_slurm()
    os.umask(0o077)
    root, private, public, report = map(Path, (root, private, public, report))
    private.mkdir(parents=True, exist_ok=True, mode=0o700)
    public.mkdir(parents=True, exist_ok=True, mode=0o700)
    report.mkdir(parents=True, exist_ok=True, mode=0o700)
    private.chmod(0o700)
    paths = _resolve_paths(root, config)
    missing = [str(path) for path in paths.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError("N2_INPUT_MISSING:" + ",".join(missing))
    input_hashes = {str(path): digest(path) for path in paths.values() if path.is_file()}
    config_hash = hashlib.sha256(json.dumps(config, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    input_hashes["config"] = config_hash
    _write_json(private / "input_hashes.json", input_hashes)
    bags = pd.read_parquet(paths["matched_bags"])
    h_bag = pd.read_parquet(paths["h_bag"])
    h_manifest = validate_h_bag_metadata(h_bag)
    if "bag_id" not in h_bag.columns or h_bag.bag_id.astype(str).duplicated().any():
        raise ValueError("N2_INPUT_H_BAG_BAG_ID_SCHEMA")
    bag_ids = set(bags.bag_id.astype(str))
    h_bag_ids = set(h_bag.bag_id.astype(str))
    if h_bag_ids != bag_ids:
        raise ValueError("N2_INPUT_H_BAG_BAG_COVERAGE")
    h_manifest.update({"bag_id_coverage": "EXACT", "bag_count_matches": True})
    cases = _json(paths["cases"])
    folds = _json(paths["split"])
    manifest = build_fold_support_manifest(bags, cases, folds)
    h_columns = [column for column in ("bag_id", "candidate_id", "record_id", "segment_id",
                                       "split_group_id", "A_half", "stimulus_local_id", *H_BAG_COLUMNS)
                 if column in h_bag.columns]
    _write_frame(private / "h_bag_metadata.parquet", h_bag[h_columns].copy())
    _write_frame(private / "fold_role_counts.parquet", pd.DataFrame(manifest["role_counts"]))
    _write_frame(private / "member_trial_ids.parquet", pd.DataFrame(manifest["members"]))
    _write_json(private / "support_manifest.json", manifest)
    summary = {
        "status": "N2_INPUTS_COMPLETE" if manifest["status"] == "PASS" else "N2_INPUTS_BLOCKED",
        "zero_fit": True, "eeg_arrays_read": False, "effects_read": False,
        "fold_count": EXPECTED_OUTER_FOLDS, "all_five_folds_required": True,
        "passing_fold_subset_selection": False, "support": manifest["status"],
        "candidate_detail": manifest["candidate_detail"],
        "h_bag": h_manifest,
        "post_pre_feature_requirements": {"post_raw": 64, "pre_raw": 64,
                                           "post_pca": 8, "pre_pca": 8,
                                           "post": {"raw_dimension": 64, "pca_components": 8},
                                           "pre": {"raw_dimension": 64, "pca_components": 8}},
        "mu_dimension_required": 8, "var_dimension_required": 8,
        "role_minimum_groups": ROLE_MIN_GROUPS,
        "folds": [{"outer_fold": row["outer_fold"], "status": row["status"],
                   "reasons": row["reasons"],
                   "source_feature_file_hashes": row["source_feature_file_hashes"],
                   "role_counts": row["role_counts"]} for row in manifest["folds"]],
        "input_hashes_recorded": True,
    }
    _write_json(private / "n2_experiment_inputs_summary.json", summary)
    public_summary = dict(summary)
    public_summary["candidate_detail"] = {
        "candidate_denominator": manifest["candidate_detail"]["candidate_denominator"],
        "candidate_both_half_numerator": manifest["candidate_detail"]["candidate_both_half_numerator"],
        "candidate_unsupported_count": len(manifest["candidate_detail"]["candidate_unsupported"]),
    }
    _write_json(public / "N2_INPUT_SUPPORT_SUMMARY.json", public_summary)
    pd.DataFrame(manifest["role_counts"]).to_csv(public / "N2_FOLD_ROLE_SUPPORT.csv", index=False)
    public.joinpath("N2_FOLD_ROLE_SUPPORT.csv").chmod(0o600)
    report.joinpath("N2_EXPERIMENT_INPUTS.md").write_text(
        "# N2 v2.1 experiment input receipt\n\n"
        "This is a metadata-only, zero-fit receipt. It requires all five frozen "
        "R_SIM D_inner0 folds, keeps only candidates supported in both halves, "
        "and requires source encoder/scaler groups to exclude B/C/D/E. "
        "Post/pre source dimensions are 64 with eight PCA components required.\n\n"
        f"Status: {manifest['status']}. All five folds are retained in the receipt; "
        "a passing fold subset is never selected.\n")
    report.joinpath("N2_EXPERIMENT_INPUTS.md").chmod(0o600)
    return public_summary


__all__ = [
    "H_BAG_COLUMNS", "ROLE_MIN_GROUPS", "eligible_two_half_candidates",
    "validate_h_bag_metadata", "build_fold_support_manifest", "run",
]
