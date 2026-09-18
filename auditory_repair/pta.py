"""Versioned audit and repair of the historical HA PTA linkage.

This module deliberately leaves every historical input untouched.  It reads the
57-row Phase 3 covariate table, resolves each ``C####`` against the registered
clinical table's actual worksheet row, and reads PTA values through the
auditory_fseries source-row reader.  The repair also audits the old auditory5
support table and reconstructs its seeded component folds after changing only
the clinical-completeness-dependent D flag.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import re
from pathlib import Path
from typing import Any, Iterable, Mapping

import numpy as np
import pandas as pd

from auditory_fseries.data import _read_workbook, _text, _number
from auditory5.splitting import balanced_component_folds


ROOT = Path(__file__).resolve().parents[1]
OLD_COV = ROOT / "private/phase3_ha_covariates_004/candidate_covariates.csv"
CLINICAL = ROOT / "private/clinical_003/clinical_rows_clean.csv"
INVENTORY = ROOT / "private/inventory_001/file_path_map.csv"
WORKBOOK_ID = "file_e254c9a75c971ac7d4e76bf6df2b4030"
OLD_MANIFEST = ROOT / "private/auditory5_v1/data/manifest_001/clinical_index.parquet"
OLD_SUPPORT = ROOT / "private/auditory5_v1/splits/splits_001/support.parquet"
OLD_FOLDS = ROOT / "private/auditory5_v1/splits/splits_001/folds.json"
SEED = 20260917


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_row_from_clinical_id(value: Any) -> int:
    match = re.fullmatch(r"C(\d{4})", _text(value))
    if match is None:
        raise ValueError(f"clinical row id must be C####: {value!r}")
    return int(match.group(1))


def pta(values: Iterable[Any]) -> float | None:
    numbers = [_number(value) for value in values]
    if len(numbers) != 4 or any(value is None for value in numbers):
        return None
    return float(sum(numbers) / 4.0)


def _num_equal(left: Any, right: Any) -> bool:
    a, b = _number(left), _number(right)
    return a is None and b is None or a is not None and b is not None and math.isclose(a, b, rel_tol=0.0, abs_tol=1e-9)


def _value_changed(left: Any, right: Any) -> bool:
    """Compare numeric PTA values while treating empty and None as the same missing value."""
    return not _num_equal(left, right)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def workbook_path() -> Path:
    for row in _read_csv(INVENTORY):
        if _text(row.get("file_id")) == WORKBOOK_ID:
            path = Path(_text(row.get("absolute_path")))
            if not path.exists():
                raise FileNotFoundError(path)
            return path
    raise KeyError(WORKBOOK_ID)


def read_registered_rows() -> dict[int, dict[str, str]]:
    return {int(row["source_row"]): row for row in _read_csv(CLINICAL)}


def _complete(row: Mapping[str, Any]) -> bool:
    def finite(key: str) -> float | None:
        try:
            value = float(row[key])
        except (KeyError, TypeError, ValueError):
            return None
        return value if math.isfinite(value) else None

    age, duration, threshold, target = (
        finite("clinical_age_months"), finite("duration_months"),
        finite("better_unaided_pta"), finite("MUSS"),
    )
    return (
        _text(row.get("pta_status")) == "linked_complete_unaided"
        and all(value is not None for value in (age, duration, threshold, target))
        and age >= 0 and duration >= 0 and 0 <= target <= 100
        and _text(row.get("strong_unique_link")).lower() == "true"
        and _text(row.get("eligible_measurement_identity_index")).lower() == "true"
    )


def repair_candidates() -> tuple[list[dict[str, str]], list[dict[str, Any]], dict[str, Any]]:
    """Return repaired rows, private row-level differences, and source evidence."""
    old_rows = _read_csv(OLD_COV)
    if len(old_rows) != 57:
        raise AssertionError(f"expected 57 old candidate rows, got {len(old_rows)}")
    registered = read_registered_rows()
    wb_path = workbook_path()
    workbook, evidence = _read_workbook(wb_path)
    repaired: list[dict[str, str]] = []
    differences: list[dict[str, Any]] = []
    for old in old_rows:
        cid = _text(old.get("clinical_row_id"))
        actual_row = source_row_from_clinical_id(cid)
        reg = registered.get(actual_row)
        sheet = workbook.get(actual_row)
        if reg is None or sheet is None:
            raise AssertionError(f"missing registered/source row for {cid} ({actual_row})")
        # The direct source row and the registered clinical audit must agree on
        # identity and clinical fields before threshold values are consumed.
        checks = {
            "name": _text(reg.get("raw_name")) == _text(sheet.get("name")),
            "age_months": _num_equal(reg.get("age_months"), sheet.get("age_months")),
            "duration_months": _num_equal(reg.get("duration_months"), sheet.get("duration_months")),
            "MUSS": _num_equal(reg.get("MUSS"), sheet.get("MUSS")),
            "IT_MAIS_MAIS": _num_equal(reg.get("IT_MAIS_MAIS"), sheet.get("IT_MAIS_MAIS")),
            "candidate_age_months": _num_equal(old.get("clinical_age_months"), reg.get("age_months")),
            "candidate_duration_months": _num_equal(old.get("duration_months"), reg.get("duration_months")),
            "candidate_MUSS": _num_equal(old.get("MUSS"), reg.get("MUSS")),
        }
        if not all(checks.values()):
            raise AssertionError(f"registered/source mismatch for {cid}: {checks}")

        values = {
            "source_row": str(actual_row),
            "clinical_id_found": "True",
            "better_unaided_pta": "" if sheet["better_unaided_pta"] is None else str(sheet["better_unaided_pta"]),
            "r_unaided_pta": "" if sheet["right_unaided_pta"] is None else str(sheet["right_unaided_pta"]),
            "l_unaided_pta": "" if sheet["left_unaided_pta"] is None else str(sheet["left_unaided_pta"]),
            "better_aided_pta": "" if sheet["better_aided_pta"] is None else str(sheet["better_aided_pta"]),
        }
        values["pta_status"] = "linked_complete_unaided" if sheet["better_unaided_pta"] is not None else "not_available_or_unlinked"
        new = dict(old)
        new.update(values)
        repaired.append(new)

        def raw_or_none(value: Any) -> Any:
            return None if value == "" else value

        differences.append({
            "participant_id": old.get("participant_id", ""),
            "recording_id": old.get("recording_id", ""),
            "clinical_row_id": cid,
            "old_source_row": old.get("source_row", ""),
            "corrected_source_row": actual_row,
            "source_row_changed": not _num_equal(old.get("source_row", ""), actual_row),
            "source_name": sheet.get("name", ""),
            "registered_name": reg.get("raw_name", ""),
            "old_better_unaided_pta": raw_or_none(old.get("better_unaided_pta", "")),
            "corrected_better_unaided_pta": sheet["better_unaided_pta"],
            "old_better_aided_pta": raw_or_none(old.get("better_aided_pta", "")),
            "corrected_better_aided_pta": sheet["better_aided_pta"],
            "old_unaided_missing": not bool(_text(old.get("better_unaided_pta"))),
            "corrected_unaided_missing": sheet["better_unaided_pta"] is None,
            "old_aided_missing": not bool(_text(old.get("better_aided_pta"))),
            "corrected_aided_missing": sheet["better_aided_pta"] is None,
            "registered_source_assertions": checks,
            "source_raw_thresholds": sheet["raw_thresholds"],
        })
    source = {
        "workbook_file_id": WORKBOOK_ID,
        "workbook_path": str(wb_path),
        "workbook_sha256": sha256(wb_path),
        "registered_clinical_sha256": sha256(CLINICAL),
        "old_covariates_sha256": sha256(OLD_COV),
        "workbook_evidence": evidence,
        "candidate_rows": len(repaired),
    }
    return repaired, differences, source


def rebuild_support(repaired: list[dict[str, str]]) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    """Rebuild old clinical completeness and D using the exact old support rows."""
    support = pd.read_parquet(OLD_SUPPORT)
    if list(support.columns) != [
        "record_id", "candidate_id", "split_group_id", "general", "A", "B", "C", "D",
        "accepted_P1", "accepted_P2_joint", "P1_class0", "P1_class1", "P2_class0", "P2_class1",
        "A_half0_blocks", "A_half1_blocks", "B_history0", "B_history1",
    ]:
        raise AssertionError("frozen support columns differ from the expected old contract")
    old_manifest = pd.read_parquet(OLD_MANIFEST)
    repaired_by_record = {row["recording_id"]: row for row in repaired}
    old_by_record = old_manifest.set_index("record_id")
    rows: list[dict[str, Any]] = []
    for record_id in support.record_id:
        # The historical manifest was built from the 57 candidate rows while
        # the old support table contains all 61 metadata indices.  The old
        # splitter treated a record absent from clinical_index as incomplete.
        old_complete = bool(old_by_record.loc[record_id, "clinical_complete"]) if record_id in old_by_record.index else False
        support_row = support.loc[support.record_id == record_id].iloc[0]
        expected_old_d = old_complete and int(support_row["P1_class0"]) >= 40 and int(support_row["P1_class1"]) >= 40
        if bool(support_row["D"]) != bool(expected_old_d):
            raise AssertionError(f"frozen D mismatch for support record {record_id}")
        corrected = repaired_by_record.get(record_id)
        corrected_complete = _complete(corrected) if corrected is not None else old_complete
        rows.append({"record_id": record_id, "old_clinical_complete": old_complete,
                     "corrected_clinical_complete": corrected_complete,
                     "candidate_table_row_present": corrected is not None})
    completeness = pd.DataFrame(rows)
    corrected = support.copy()
    completeness_by_record = completeness.set_index("record_id")
    corrected["D"] = [
        bool(completeness_by_record.loc[rid, "corrected_clinical_complete"])
        and int(support.loc[i, "P1_class0"]) >= 40
        and int(support.loc[i, "P1_class1"]) >= 40
        for i, rid in enumerate(support.record_id)
    ]
    return support, corrected, {
        "old_clinical_complete_n": int(completeness.old_clinical_complete.sum()),
        "corrected_clinical_complete_n": int(completeness.corrected_clinical_complete.sum()),
        "old_D_record_n": int(support.D.sum()),
        "corrected_D_record_n": int(corrected.D.sum()),
        "old_D_group_n": int(support.loc[support.D, "split_group_id"].nunique()),
        "corrected_D_group_n": int(corrected.loc[corrected.D, "split_group_id"].nunique()),
    }


def compare_folds(old_support: pd.DataFrame, corrected_support: pd.DataFrame) -> dict[str, Any]:
    """Reconstruct old and corrected folds with the frozen algorithm and seed."""
    frozen = json.loads(OLD_FOLDS.read_text(encoding="utf-8"))
    old_eligible = old_support[old_support[["general", "A", "B", "C", "D"]].any(axis=1)].copy()
    corrected_eligible = corrected_support[corrected_support[["general", "A", "B", "C", "D"]].any(axis=1)].copy()
    old_rebuilt = balanced_component_folds(old_eligible, 5, SEED)
    corrected = balanced_component_folds(corrected_eligible, 5, SEED)
    frozen_assignments = {str(key): int(value) for key, value in frozen["outer_fold_by_group"].items()}
    old_matches_frozen = old_rebuilt == frozen_assignments
    changed = sorted(set(old_rebuilt) | set(corrected))
    changed = [group for group in changed if old_rebuilt.get(group) != corrected.get(group)]
    return {
        "seed": SEED,
        "old_support_rows": len(old_support),
        "corrected_support_rows": len(corrected_support),
        "old_eligible_rows": len(old_eligible),
        "corrected_eligible_rows": len(corrected_eligible),
        "old_eligible_groups": int(old_eligible.split_group_id.nunique()),
        "corrected_eligible_groups": int(corrected_eligible.split_group_id.nunique()),
        "old_reconstruction_matches_frozen": bool(old_matches_frozen),
        "frozen_fold_counts": {str(k): int(v) for k, v in pd.Series(list(frozen_assignments.values())).value_counts().sort_index().items()},
        "old_rebuilt_fold_counts": {str(k): int(v) for k, v in pd.Series(list(old_rebuilt.values())).value_counts().sort_index().items()},
        "corrected_fold_counts": {str(k): int(v) for k, v in pd.Series(list(corrected.values())).value_counts().sort_index().items()},
        "changed_group_count": len(changed),
        "old_assignment": old_rebuilt,
        "corrected_assignment": corrected,
        "changed_groups": changed,
        "old_folds_sha256": sha256(OLD_FOLDS),
        "old_support_sha256": sha256(OLD_SUPPORT),
        "old_manifest_sha256": sha256(OLD_MANIFEST),
    }


def run(output: Path, public_output: Path | None = None) -> dict[str, Any]:
    if not os.environ.get("SLURM_JOB_ID"):
        raise RuntimeError("PTA repair must run under Slurm")
    output = Path(output)
    private = output
    public = public_output or (ROOT / "results/auditory_repair/pta_001")
    private.mkdir(parents=True, exist_ok=False, mode=0o700)
    public.mkdir(parents=True, exist_ok=False)
    os.chmod(private, 0o700)

    repaired, differences, source = repair_candidates()
    old_support, corrected_support, support_summary = rebuild_support(repaired)
    fold_summary = compare_folds(old_support, corrected_support)

    with (private / "candidate_covariates.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(repaired[0]))
        writer.writeheader()
        writer.writerows(repaired)
    with (private / "row_differences.json").open("w", encoding="utf-8") as handle:
        json.dump(differences, handle, ensure_ascii=False, indent=2)
    pd.DataFrame(differences).drop(columns=["source_raw_thresholds", "registered_source_assertions"]).to_csv(
        private / "row_differences.csv", index=False
    )
    old_support.to_parquet(private / "support_old_copy.parquet", index=False)
    corrected_support.to_parquet(private / "support_corrected.parquet", index=False)
    completeness = pd.DataFrame({
        "record_id": old_support.record_id,
        "old_D": old_support.D.astype(bool),
        "corrected_D": corrected_support.D.astype(bool),
    })
    completeness.to_csv(private / "D_membership.csv", index=False)
    json.dump(fold_summary, (private / "folds_corrected.json").open("w", encoding="utf-8"), indent=2)
    json.dump(source, (private / "source_evidence.json").open("w", encoding="utf-8"), ensure_ascii=False, indent=2)

    summary = {
        "status": "COMPLETED_REPAIR_AUDIT",
        "candidate_rows": len(repaired),
        "old_unaided_complete_n": int(sum(not d["old_unaided_missing"] for d in differences)),
        "corrected_unaided_complete_n": int(sum(not d["corrected_unaided_missing"] for d in differences)),
        "old_aided_complete_n": int(sum(not d["old_aided_missing"] for d in differences)),
        "corrected_aided_complete_n": int(sum(not d["corrected_aided_missing"] for d in differences)),
        "source_row_changed_n": int(sum(d["source_row_changed"] for d in differences)),
        "better_unaided_pta_changed_n": int(sum(_value_changed(d["old_better_unaided_pta"], d["corrected_better_unaided_pta"]) for d in differences)),
        "better_aided_pta_changed_n": int(sum(_value_changed(d["old_better_aided_pta"], d["corrected_better_aided_pta"]) for d in differences)),
        "unaided_missingness_changed_n": int(sum(d["old_unaided_missing"] != d["corrected_unaided_missing"] for d in differences)),
        "aided_missingness_changed_n": int(sum(d["old_aided_missing"] != d["corrected_aided_missing"] for d in differences)),
        **support_summary,
        "old_support_columns_preserved": list(old_support.columns),
        "old_split_reconstruction_matches_frozen": fold_summary["old_reconstruction_matches_frozen"],
        "old_eligible_group_n": fold_summary["old_eligible_groups"],
        "corrected_eligible_group_n": fold_summary["corrected_eligible_groups"],
        "old_fold_counts": fold_summary["old_rebuilt_fold_counts"],
        "frozen_fold_counts": fold_summary["frozen_fold_counts"],
        "corrected_fold_counts": fold_summary["corrected_fold_counts"],
        "D_membership_changed_record_n": int(sum(bool(a) != bool(b) for a, b in zip(old_support.D, corrected_support.D))),
        "D_membership_gained_record_n": int(sum((not bool(a)) and bool(b) for a, b in zip(old_support.D, corrected_support.D))),
        "D_membership_lost_record_n": int(sum(bool(a) and (not bool(b)) for a, b in zip(old_support.D, corrected_support.D))),
        "fold_assignment_changed_group_n": fold_summary["changed_group_count"],
        "downstream_inputs": [
            "private/phase3_ha_covariates_004/candidate_covariates.csv",
            "scripts/phase3_ha_science.py -> phase3_ha_science_001 (all PTA-adjusted HA clinical baselines and EEG increments)",
            "scripts/phase3_ha_sensitivity.py -> phase3_ha_sensitivity_001 (post-v1 PTA penalty sensitivity)",
            "private/auditory5_v1/data/manifest_001/clinical_index.parquet",
            "private/auditory5_v1/splits/splits_001/support.parquet (D and seeded fold balance; all route folds use this file)",
            "private/auditory5_v1/splits/splits_001/folds.json (37 outer-group assignments change in the corrected counterfactual)",
            "auditory5 route D and D controls (clinical index and D support); any route rerun using corrected folds must regenerate fold-scoped representations",
        ],
        "note": "Historical artifacts remain unchanged. This output is a corrected input and downstream support audit; no models were fit.",
    }
    json.dump(summary, (public / "summary.json").open("w", encoding="utf-8"), indent=2)
    return summary


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--public-output", required=True)
    args = parser.parse_args()
    print(json.dumps(run(Path(args.output), Path(args.public_output)), indent=2))
