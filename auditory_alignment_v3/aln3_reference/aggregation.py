"""Federici normalized-long-table aggregation; identities are supplied, never guessed.

Rows describe per-record metrics per completed unit, not raw trials. Human and
phantom summaries are separate. HC-v shares a human identity with HC only when
this has been verified by the source manifest. No raw identities are exported.
"""
from __future__ import annotations
import numpy as np
import pandas as pd

REQUIRED = {"dataset", "config_id", "seed", "subject_uid", "record_uid", "condition", "entity_type",
            "identity_source", "subject_fold", "content_fold", "unit_id", "metric", "value"}
ALLOWED = {"human", "phantom", "unknown"}


def validate_rows(df: pd.DataFrame) -> None:
    missing = REQUIRED - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")
    if df.empty or df[list(REQUIRED)].isna().any().any():
        raise ValueError("Empty table or missing required metadata/value")
    for col in REQUIRED - {"seed", "subject_fold", "content_fold", "value"}:
        if (df[col].astype(str).str.len() == 0).any():
            raise ValueError(f"Empty values in {col}")
    if not set(df.entity_type).issubset(ALLOWED):
        raise ValueError("entity_type must be explicitly human, phantom or unknown")
    if not np.isfinite(pd.to_numeric(df.value, errors="raise")).all():
        raise ValueError("Metrics must be finite; do not silently drop failures")
    if ((df.condition == "Artifact") & (df.entity_type == "human")).any():
        raise ValueError("Artifact rows must not enter the human panel")
    if df.duplicated(["dataset", "config_id", "seed", "unit_id", "record_uid", "metric"]).any():
        raise ValueError("Duplicate record/metric within one unit")
    if (df.groupby(["dataset", "subject_uid"]).entity_type.nunique() > 1).any():
        raise ValueError("A source identity has conflicting entity types")
    human = df[df.entity_type == "human"]
    for _, block in human.groupby(["dataset", "subject_uid"]):
        if "CI" in set(block.condition) and ({"HC", "HC-v"} & set(block.condition)):
            raise ValueError("CI and HC identity spaces were incorrectly merged")
        # Every condition of a person must be held out in the same outer fold.
        if block.subject_fold.nunique() > 1:
            raise ValueError("The same human has conflicting subject folds")


def identity_condition_values(df: pd.DataFrame) -> pd.DataFrame:
    validate_rows(df)
    cols = ["dataset", "config_id", "seed", "subject_uid", "condition", "entity_type", "metric"]
    # First equalize repeated fold evaluations of one record; then equalize records.
    records = df.groupby(cols + ["record_uid"], as_index=False).value.mean()
    return records.groupby(cols, as_index=False).value.mean()


def bootstrap_mean(values, n_boot: int = 4000, seed: int = 0):
    x = np.asarray(values, float)
    if x.ndim != 1 or not len(x) or not np.isfinite(x).all() or n_boot < 1:
        raise ValueError("Need nonempty finite identity-level values")
    rng = np.random.default_rng(seed)
    draws = x[rng.integers(0, len(x), size=(n_boot, len(x)))].mean(1)
    return {"n_identities": int(len(x)), "mean": float(x.mean()),
            "ci_low": float(np.quantile(draws, .025)), "ci_high": float(np.quantile(draws, .975)),
            "uncertainty": "identity_bootstrap_conditional_on_fitted_models"}


def summarize_conditions(df: pd.DataFrame, n_boot: int = 4000, seed: int = 0):
    unit = identity_condition_values(df)
    keys = ["dataset", "config_id", "seed", "condition", "entity_type", "metric"]
    out = []
    for key, block in unit.groupby(keys, sort=True):
        row = {k: (v.item() if isinstance(v, np.generic) else v) for k, v in zip(keys, key)}
        row.update(bootstrap_mean(block.value, n_boot, seed))
        row["panel"] = "human_condition" if row["entity_type"] == "human" else "separate_nonhuman_or_unknown"
        out.append(row)
    return out


def paired_conditions(df: pd.DataFrame, first: str = "HC", second: str = "HC-v",
                      n_boot: int = 4000, seed: int = 0):
    unit = identity_condition_values(df)
    unit = unit[unit.entity_type == "human"]
    keys = ["dataset", "config_id", "seed", "metric"]
    out = []
    for key, block in unit.groupby(keys, sort=True):
        a = block[block.condition == first].set_index("subject_uid").value
        b = block[block.condition == second].set_index("subject_uid").value
        shared = a.index.intersection(b.index).sort_values()
        row = {k: (v.item() if isinstance(v, np.generic) else v) for k, v in zip(keys, key)}
        row.update({"contrast": f"{first} - {second}", "n_first_only": int(len(a.index.difference(b.index))),
                    "n_second_only": int(len(b.index.difference(a.index)))})
        if len(shared):
            row.update(bootstrap_mean((a.loc[shared] - b.loc[shared]).to_numpy(), n_boot, seed))
        else:
            row.update({"n_identities": 0, "mean": None, "ci_low": None, "ci_high": None,
                        "status": "no_verified_pairs"})
        out.append(row)
    return out
