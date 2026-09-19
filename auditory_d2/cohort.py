"""Join D1 exports to evidenced identities and clinical variables.

Identity is never re-derived here. The only identities used are the ones an earlier
round already established with evidence (`unique_participant_exact_name_same_day`),
and age is the one that round derived from a single parsed date of birth plus the
selected EEG record time. Nothing is inferred from a filename or a GUID count.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np

CI_PREPARE = "private/results/auditory_repair/ci_prepare_004"
C_NAMES = ("age_months", "ci_duration_months", "ha_duration_months")


def d1_receipts(root: Path, run: str) -> dict[str, dict]:
    directory = root / "private/auditory_d1" / run / "receipts"
    out = {}
    for path in sorted(directory.glob("*.json")):
        payload = json.loads(path.read_text())
        if payload.get("status") == "D1_EXPORTED":
            out[payload["container_id"]] = payload
    return out


def mff_labelled(root: Path, run: str = "D1_mff_001") -> dict:
    """MFF records with an evidenced identity and a derived age."""
    with (root / CI_PREPARE / "cohort.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    with np.load(root / CI_PREPARE / "data.npz", allow_pickle=False) as store:
        clinical = store["C"]
        recordings = store["recordings"]
        groups = store["groups"]
        targets = {name: store[name] for name in ("A", "V", "CAP", "SIR")}
        valid = {name: store[f"{name}_valid"] for name in ("A", "V", "CAP", "SIR")}
    assert len(rows) == len(recordings), "cohort.csv and data.npz disagree on length"
    receipts = d1_receipts(root, run)

    units, dropped = [], {"no_d1_export": 0, "no_age": 0}
    for index, row in enumerate(rows):
        container = str(recordings[index])
        assert container == str(row["recording"]), "row order mismatch"
        if container not in receipts:
            dropped["no_d1_export"] += 1
            continue
        age = float(clinical[index, 0])
        if not np.isfinite(age):
            dropped["no_age"] += 1
            continue
        receipt = receipts[container]
        units.append({
            "container_id": container,
            "identity": str(groups[index]),
            "age_months": age,
            "identity_status": row["identity_status"],
            "age_source_status": row["age_source_status"],
            "protocol_task": row["protocol_task"],
            "source_label": row["source_label"],
            "n_channels": receipt["n_channels"],
            "rate_hz": receipt["rate_hz"],
            "seconds": receipt["seconds"],
            "layout_hash": receipt.get("layout_hash"),
            **{name: (float(targets[name][index]) if bool(valid[name][index]) else float("nan"))
               for name in targets},
        })
    return {"branch": "mff", "run": run, "units": units, "dropped": dropped,
            "n_units": len(units), "n_identities": len({u["identity"] for u in units}),
            "total_hours": round(sum(u["seconds"] for u in units) / 3600.0, 2)}


def summarise(cohort: dict) -> dict:
    units = cohort["units"]
    ages = np.array([u["age_months"] for u in units], dtype=float)
    layouts: dict[str, int] = {}
    channels: dict[str, int] = {}
    for unit in units:
        layouts[str(unit["layout_hash"])] = layouts.get(str(unit["layout_hash"]), 0) + 1
        channels[str(unit["n_channels"])] = channels.get(str(unit["n_channels"]), 0) + 1
    return {"branch": cohort["branch"], "n_units": cohort["n_units"],
            "n_identities": cohort["n_identities"], "total_hours": cohort["total_hours"],
            "dropped": cohort["dropped"], "layouts": layouts, "channels": channels,
            "age_months": {"min": float(ages.min()), "p25": float(np.quantile(ages, .25)),
                           "median": float(np.median(ages)), "p75": float(np.quantile(ages, .75)),
                           "max": float(ages.max()), "mean": float(ages.mean()),
                           "sd": float(ages.std(ddof=1))},
            "endpoint_available": {name: int(np.isfinite([u.get(name, np.nan)
                                                          for u in units]).sum())
                                   for name in ("A", "V", "CAP", "SIR", "duration",
                                                "unaided", "aided")
                                   if any(name in u for u in units)}}


BDF_COHORT_CANDIDATES = (
    "private/results/auditory_repair/ha_prepare_001/cohort.csv",
    "private/auditory_repair/ha_prepare_001/cohort.csv",
    "private/auditory_repair/phase3_replay_002/cohort.csv",
)


BDF_CLINICAL_COLUMNS = ("age", "duration", "A", "V", "CAP", "SIR", "unaided", "aided")


def bdf_labelled(root: Path, run: str = "D1_bdf_001") -> dict:
    """HA/BDF records with an evidenced identity, age, device-use duration and thresholds.

    The clinical table is keyed by this project's own record id; the D1 export is keyed
    by file id. They are joined through the absolute source path that both already
    reference, so no identifier is invented and no name column is ever carried forward.
    """
    import pandas as pd

    rows, source = bdf_clinical(root)
    locators = pd.read_parquet(root / "private/auditory5_v1/data/manifest_001/raw_locators.parquet")
    path_of_record = {str(r.record_id): str(r.signal_path) for r in locators.itertuples()}
    with (root / "private/inventory_001/file_path_map.csv").open(newline="", encoding="utf-8") as h:
        file_of_path = {r["absolute_path"]: r["file_id"] for r in csv.DictReader(h)}
    receipts = d1_receipts(root, run)

    units, dropped = [], {"no_path": 0, "no_file_id": 0, "no_d1_export": 0, "no_age": 0}
    for row in rows:
        record = str(row["recording"])
        path = path_of_record.get(record)
        if path is None:
            dropped["no_path"] += 1
            continue
        file_id = file_of_path.get(path)
        if file_id is None:
            dropped["no_file_id"] += 1
            continue
        if file_id not in receipts:
            dropped["no_d1_export"] += 1
            continue
        try:
            age = float(row["age"])
        except (TypeError, ValueError):
            age = float("nan")
        if not np.isfinite(age):
            dropped["no_age"] += 1
            continue
        receipt = receipts[file_id]

        def number(key):
            try:
                return float(row[key])
            except (TypeError, ValueError):
                return float("nan")

        units.append({"container_id": file_id, "identity": str(row["group"]),
                      "age_months": age, "n_channels": receipt["n_channels"],
                      "rate_hz": receipt["rate_hz"], "seconds": receipt["seconds"],
                      "layout_hash": "bdf_ha20",
                      **{name: number(name) for name in BDF_CLINICAL_COLUMNS}})
    return {"branch": "bdf", "run": run, "source_table": source, "units": units,
            "dropped": dropped, "n_units": len(units),
            "n_identities": len({u["identity"] for u in units}),
            "total_hours": round(sum(u["seconds"] for u in units) / 3600.0, 2)}


def bdf_clinical(root: Path) -> tuple[list[dict], str]:
    """Locate the HA/BDF clinical table an earlier round already assembled."""
    for relative in BDF_COHORT_CANDIDATES:
        path = root / relative
        if path.is_file():
            with path.open(newline="", encoding="utf-8") as handle:
                return list(csv.DictReader(handle)), relative
    raise FileNotFoundError("D2_BDF_CLINICAL_TABLE_NOT_FOUND")
