"""Federici normalized-table summaries. Identities must be supplied from metadata.

ALN3.1: HC-v is an independent cohort; the one phantom has multiple sessions.
This module never infers identity from file number, demographics, or EEG values.
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
        if (df[col].astype(str).str.strip().str.len() == 0).any():
            raise ValueError(f"Empty values in {col}")
    if not set(df.entity_type).issubset(ALLOWED):
        raise ValueError("entity_type must be explicitly human, phantom or unknown")
    if not np.isfinite(pd.to_numeric(df.value, errors="raise")).all():
        raise ValueError("Metrics must be finite; failures belong in the status ledger")
    if ((df.condition == "Artifact") & (df.entity_type == "human")).any():
        raise ValueError("Artifact rows cannot enter the human panel")
    if df.duplicated(["dataset", "config_id", "seed", "unit_id", "record_uid", "metric"]).any():
        raise ValueError("Duplicate record/metric within one unit")
    if (df.groupby(["dataset", "subject_uid"]).entity_type.nunique() > 1).any():
        raise ValueError("A supplied identity has conflicting entity types")
    for (dataset, _), block in df[df.entity_type == "human"].groupby(["dataset", "subject_uid"]):
        conditions = set(block.condition)
        if "CI" in conditions and ({"HC", "HC-v"} & conditions):
            raise ValueError("CI and HC identity spaces were incorrectly merged")
        if dataset == "federici" and {"HC", "HC-v"}.issubset(conditions):
            raise ValueError("ALN3.1: HC and HC-v must not be paired by matching file numbers")
        if block.subject_fold.nunique() > 1:
            raise ValueError("One person has conflicting folds; export distinct split contracts separately")
    phantom = df[(df.dataset == "federici") & (df.condition == "Artifact")]
    if len(phantom) and (set(phantom.entity_type) != {"phantom"} or phantom.subject_uid.nunique() != 1):
        raise ValueError("Verified Federici Artifact sessions belong to one phantom")

def identity_condition_values(df: pd.DataFrame) -> pd.DataFrame:
    validate_rows(df)
    cols = ["dataset", "config_id", "seed", "subject_uid", "condition", "entity_type", "metric"]
    records = df.groupby(cols + ["record_uid"], as_index=False).value.mean()
    return records.groupby(cols, as_index=False).value.mean()

def bootstrap_mean(values, n_boot: int = 4000, seed: int = 0):
    x = np.asarray(values, float)
    if x.ndim != 1 or not len(x) or not np.isfinite(x).all() or n_boot < 1:
        raise ValueError("Need nonempty finite identity-level values")
    out = {"n_identities": int(len(x)), "mean": float(x.mean())}
    if len(x) == 1:
        return {**out, "ci_low": None, "ci_high": None, "uncertainty": "single_identity_descriptive_only"}
    rng = np.random.default_rng(seed)
    draws = x[rng.integers(0, len(x), size=(n_boot, len(x)))].mean(1)
    return {**out, "ci_low": float(np.quantile(draws, .025)), "ci_high": float(np.quantile(draws, .975)),
            "uncertainty": "identity_bootstrap_conditional_on_fitted_models"}

def _native_dict(keys, key):
    return {k: (v.item() if isinstance(v, np.generic) else v) for k, v in zip(keys, key)}

def summarize_conditions(df: pd.DataFrame, n_boot: int = 4000, seed: int = 0):
    unit = identity_condition_values(df)
    keys = ["dataset", "config_id", "seed", "condition", "entity_type", "metric"]
    out = []
    for key, block in unit.groupby(keys, sort=True):
        row = _native_dict(keys, key)
        if row["entity_type"] == "human":
            row.update(bootstrap_mean(block.value, n_boot, seed)); row["panel"] = "human_condition"
        else:
            row.update(n_identities=int(len(block)), mean=float(block.value.mean()), ci_low=None, ci_high=None,
                       uncertainty="nonhuman_or_unknown_descriptive_only", panel="separate_nonhuman_or_unknown")
        out.append(row)
    return out

def independent_group_contrasts(df: pd.DataFrame, contrasts=(("HC", "HC-v"), ("CI", "HC")),
                                n_boot: int = 4000, seed: int = 0):
    if n_boot < 1: raise ValueError("n_boot must be positive")
    unit = identity_condition_values(df)
    unit = unit[unit.entity_type == "human"]
    keys = ["dataset", "config_id", "seed", "metric"]; out = []
    for key, block in unit.groupby(keys, sort=True):
        for first, second in contrasts:
            a = block[block.condition == first].set_index("subject_uid").value
            b = block[block.condition == second].set_index("subject_uid").value
            if len(a.index.intersection(b.index)):
                raise ValueError("Independent contrast has overlapping source identities")
            row = _native_dict(keys, key)
            row.update(contrast=f"{first} - {second}", design="independent_groups", n_first=len(a), n_second=len(b))
            if not len(a) or not len(b):
                row.update(mean=None, ci_low=None, ci_high=None, status="missing_group")
            else:
                row.update(mean=float(a.mean()-b.mean()), ci_low=None, ci_high=None, status="ok")
                if min(len(a),len(b)) > 1:
                    rng=np.random.default_rng(seed); x=a.to_numpy(); y=b.to_numpy()
                    ds=x[rng.integers(len(x),size=(n_boot,len(x)))].mean(1)-y[rng.integers(len(y),size=(n_boot,len(y)))].mean(1)
                    row.update(ci_low=float(np.quantile(ds,.025)),ci_high=float(np.quantile(ds,.975)),
                               uncertainty="independent_identity_bootstrap_conditional_on_fitted_models")
                else:
                    row["uncertainty"]="one_group_has_single_identity_descriptive_only"
            out.append(row)
    return out

def phantom_sessions(df: pd.DataFrame):
    validate_rows(df)
    d=df[df.entity_type=="phantom"]
    if d.empty: return []
    keys=["dataset","config_id","seed","subject_uid","condition","metric"]
    records=d.groupby(keys+["record_uid"],as_index=False).value.mean()
    out=[]
    for key,block in records.groupby(keys,sort=True):
        row=_native_dict(keys,key)
        row.update(n_identities=1,n_sessions=len(block),mean=float(block.value.mean()),
                   session_min=float(block.value.min()),session_max=float(block.value.max()),
                   ci_low=None,ci_high=None,uncertainty="one_phantom_sessions_descriptive_not_population",
                   sessions=[{"record_uid":str(r.record_uid),"value":float(r.value)} for r in block.itertuples()])
        out.append(row)
    return out

def paired_conditions(*args, **kwargs):
    """Reject the obsolete default; model-versus-model pairing is a different task."""
    raise ValueError("The old default HC/HC-v same-child contrast is withdrawn in ALN3.1. Use independent_group_contrasts.")
