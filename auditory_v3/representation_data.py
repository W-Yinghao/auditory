"""Metadata-only construction of the frozen R3 quartet exposure plan."""
from __future__ import annotations

import math
from typing import Iterable

import numpy as np
import pandas as pd


SUPPORT_SECONDS = 10.823
DEFAULT_SEED = 11
GROUP_COLUMNS = ["split_group_id", "A_half", "record_id", "segment_id",
                 "previous_code", "previous_run_bin"]


class QuartetSupportError(ValueError):
    """Raised when any eligible metadata cell cannot form a quartet."""

    def __init__(self, message: str, support: pd.DataFrame):
        super().__init__(message)
        self.support = support


def _time_column(frame: pd.DataFrame) -> str:
    for name in ("onset_s", "onset_seconds_relative", "event_time_s", "sample_time_s",
                 "time_s", "onset", "event_onset_s", "trigger_time_s"):
        if name in frame:
            return name
    raise ValueError("metadata needs an onset/time column")


def _epoch_bounds(row: pd.Series, time_col: str) -> tuple[float, float]:
    for a, b in (("epoch_start_s", "epoch_end_s"), ("direct_epoch_start_s", "direct_epoch_end_s"),
                 ("direct_epoch_start", "direct_epoch_end")):
        if a in row.index and b in row.index and pd.notna(row[a]) and pd.notna(row[b]):
            return float(row[a]), float(row[b])
    t = float(row[time_col])
    return t - 0.2, t + 0.45


def _valid_pairs(cell: pd.DataFrame, time_col: str, support_s: float) -> dict[int, list[tuple[int, int]]]:
    """Return feasible same-class pairs; no four-way Cartesian expansion."""
    rows = {int(i): r for i, r in cell.iterrows()}
    by_class = {c: list(cell.index[cell["class"] == c]) for c in (0, 1)}
    pairs = {}
    for c in (0, 1):
        vals = by_class[c]
        pairs[c] = [(int(a), int(b)) for pos, a in enumerate(vals) for b in vals[pos + 1:]
                    if rows[int(a)].get("physical_block_id") != rows[int(b)].get("physical_block_id")
                    and abs(float(rows[int(a)][time_col]) - float(rows[int(b)][time_col])) >= support_s]
    return pairs


def _cell_cache(cell: pd.DataFrame, time_col: str, support_s: float) -> dict:
    """Compact immutable metadata cache used by support and exposure sampling."""
    rows = {int(i): r for i, r in cell.iterrows()}
    pairs = _valid_pairs(cell, time_col, support_s)
    bounds = {i: _epoch_bounds(r, time_col) for i, r in rows.items()}
    blocks = {i: r["physical_block_id"] for i, r in rows.items()}
    return {"rows": rows, "pairs": {c: np.asarray(v, dtype=np.int64).reshape(-1, 2)
                                      for c, v in pairs.items()},
            "bounds": bounds, "blocks": blocks}


def _pair_combo_valid(cache: dict, p0: tuple[int, int], p1: tuple[int, int]) -> bool:
    ids = (*p0, *p1)
    if len(set(ids)) != 4:
        return False
    intervals = [cache["bounds"][i] for i in ids]
    return not any(max(intervals[i][0], intervals[j][0]) < min(intervals[i][1], intervals[j][1])
                   for i in range(4) for j in range(i + 1, 4))


def _exact_quartet(cache: dict) -> tuple[int, int, int, int] | None:
    p0, p1 = cache["pairs"][0], cache["pairs"][1]
    if not len(p0) or not len(p1):
        return None
    for a, b in p0:
        for c, d in p1:
            if _pair_combo_valid(cache, (int(a), int(b)), (int(c), int(d))):
                return int(a), int(b), int(c), int(d)
    return None


def _audit_quartet(cell: pd.DataFrame, quartet: tuple[int, int, int, int],
                   time_col: str, support_s: float) -> bool:
    rows = {int(i): r for i, r in cell.iterrows()}
    if len(set(quartet)) != 4 or any(i not in rows for i in quartet):
        return False
    if [int(rows[i]["class"]) for i in quartet].count(0) != 2:
        return False
    if rows[quartet[0]]["physical_block_id"] == rows[quartet[1]]["physical_block_id"]:
        return False
    if rows[quartet[2]]["physical_block_id"] == rows[quartet[3]]["physical_block_id"]:
        return False
    intervals = [_epoch_bounds(rows[i], time_col) for i in quartet]
    return not any(max(intervals[i][0], intervals[j][0]) < min(intervals[i][1], intervals[j][1])
                   for i in range(4) for j in range(i + 1, 4)) and \
        abs(float(rows[quartet[0]][time_col]) - float(rows[quartet[1]][time_col])) >= support_s and \
        abs(float(rows[quartet[2]][time_col]) - float(rows[quartet[3]][time_col])) >= support_s


def audit_quartet(frame: pd.DataFrame, quartet: Iterable[int],
                  support_s: float = SUPPORT_SECONDS) -> bool:
    """Explicitly audit identity/history/record scope and quartet validity."""
    ids = tuple(int(i) for i in quartet)
    if len(ids) != 4 or any(i not in frame.index for i in ids):
        return False
    work = frame.copy()
    class_col = next((c for c in ("class", "class_label", "label", "stimulus_class", "stimulus_local_id") if c in work), None)
    if class_col is None or "physical_block_id" not in work or "trial_id" not in work:
        return False
    if class_col != "class":
        work["class"] = work[class_col]
    rows = work.loc[list(ids)]
    if any(rows[c].nunique(dropna=False) != 1 for c in GROUP_COLUMNS):
        return False
    time_col = _time_column(work)
    if not pd.to_numeric(work[time_col], errors="coerce").notna().all():
        raise ValueError("onset/time values must be finite numeric metadata")
    return _audit_quartet(work, ids, time_col, support_s)


def _sample_quartet(cell: pd.DataFrame, time_col: str, support_s: float,
                    rng: np.random.Generator) -> tuple[int, int, int, int] | None:
    cache = _cell_cache(cell, time_col, support_s)
    pairs = cache["pairs"]
    if not pairs[0] or not pairs[1]:
        return None
    # Randomized bounded rejection avoids materializing class0-pair × class1-pair.
    for _ in range(max(16, len(pairs[0]) + len(pairs[1]))):
        a, b = pairs[0][int(rng.integers(len(pairs[0])))]
        c, d = pairs[1][int(rng.integers(len(pairs[1])))]
        quartet = (a, b, c, d)
        if _pair_combo_valid(cache, (a, b), (c, d)):
            return quartet
    return _exact_quartet(cache)


def _sample_cached(cache: dict, rng: np.random.Generator) -> tuple[tuple[int, int, int, int] | None, int, bool]:
    p0, p1 = cache["pairs"][0], cache["pairs"][1]
    if not len(p0) or not len(p1):
        return None, 0, False
    attempts = max(16, len(p0) + len(p1))
    for retry in range(attempts):
        a, b = p0[int(rng.integers(len(p0)))]
        c, d = p1[int(rng.integers(len(p1)))]
        if _pair_combo_valid(cache, (int(a), int(b)), (int(c), int(d))):
            return (int(a), int(b), int(c), int(d)), retry, False
    quartet = _exact_quartet(cache)
    return quartet, attempts, True


def quartet_support(frame: pd.DataFrame, eligible_only: bool = True,
                     support_s: float = SUPPORT_SECONDS) -> pd.DataFrame:
    """Return one aggregate support row per frozen history cell."""
    work = frame.copy()
    class_col = next((c for c in ("class", "class_label", "label", "stimulus_class", "stimulus_local_id") if c in work), None)
    if class_col is None:
        raise ValueError("metadata needs a binary class column")
    if class_col != "class":
        work["class"] = work[class_col]
    required = set(GROUP_COLUMNS + ["class", "physical_block_id", "trial_id"])
    missing = sorted(required - set(work.columns))
    if missing:
        raise ValueError(f"missing metadata columns: {missing}")
    if not np.isfinite(float(support_s)) or float(support_s) < SUPPORT_SECONDS:
        raise ValueError("support_s must be finite and at least 10.823 seconds")
    if work["trial_id"].isna().any() or work["trial_id"].nunique() != len(work):
        raise ValueError("trial_id must be non-null and unique")
    if work["physical_block_id"].isna().any():
        raise ValueError("physical blocks must be non-null")
    if not work["class"].isin([0, 1]).all():
        raise ValueError("class labels must be binary 0/1")
    time_col = _time_column(work)
    if not pd.to_numeric(work[time_col], errors="coerce").notna().all():
        raise ValueError("onset/time values must be finite numeric metadata")
    if eligible_only and "eligible" in work:
        work = work[work["eligible"].astype(bool)]
    rows = []
    for key, cell in work.groupby(GROUP_COLUMNS, sort=True, dropna=False):
        cache = _cell_cache(cell, time_col, support_s)
        has = _exact_quartet(cache) is not None
        rows.append(dict(zip(GROUP_COLUMNS, key if isinstance(key, tuple) else (key,)),
                            n_trials=int(len(cell)),
                            n_class0=int((cell["class"] == 0).sum()),
                            n_class1=int((cell["class"] == 1).sum()),
                            n_physical_blocks=int(cell["physical_block_id"].nunique()),
                            quartet_count=int(has),
                            quartet_eligible=has))
    return pd.DataFrame(rows, columns=GROUP_COLUMNS + ["n_trials", "n_class0", "n_class1",
                                                        "n_physical_blocks", "quartet_count",
                                                        "quartet_eligible"])


def sample_quartets(frame: pd.DataFrame, fit_groups: Iterable | None = None,
                    seed: int = DEFAULT_SEED, epochs: int = 60,
                    batch_original_trials: int = 64,
                    support_s: float = SUPPORT_SECONDS) -> dict:
    """Build the fixed, shared exposure plan for SUP/SIM/MATCH.

    The returned ``pairs`` table is deliberately private-use metadata.  The
    public ``support`` table contains only aggregate counts.
    """
    work = frame.copy()
    class_col = next((c for c in ("class", "class_label", "label", "stimulus_class", "stimulus_local_id") if c in work), None)
    if class_col is None:
        raise ValueError("metadata needs a binary class column")
    if class_col != "class":
        work["class"] = work[class_col]
    if fit_groups is not None:
        allowed = set(fit_groups)
        work = work[work["split_group_id"].isin(allowed)]
    support = quartet_support(work, support_s=support_s)
    bad = support[~support["quartet_eligible"]]
    if not bad.empty:
        raise QuartetSupportError("every eligible cell must support a quartet", support)
    if not np.isfinite(float(support_s)) or float(support_s) < SUPPORT_SECONDS:
        raise ValueError("support_s must be finite and at least 10.823 seconds")
    if "trial_id" not in work or work["trial_id"].isna().any() or work["trial_id"].nunique() != len(work):
        raise ValueError("trial_id must be non-null and unique")
    if not work["class"].isin([0, 1]).all():
        raise ValueError("class labels must be binary 0/1")
    time_col = _time_column(work)
    rng = np.random.default_rng(seed)
    records = []
    quartet_meta = []
    cell_defs = {}
    qid = 0
    for key, cell in work.groupby(GROUP_COLUMNS, sort=True, dropna=False):
        cell_defs[key] = _cell_cache(cell, time_col, support_s)
    if support.empty or (~support["quartet_eligible"]).any():
        raise QuartetSupportError("every eligible cell must support a quartet", support)
    groups = sorted(support["split_group_id"].drop_duplicates().tolist(), key=str)
    if len(groups) < batch_original_trials // 4:
        raise QuartetSupportError("fewer than 16 training groups cannot fill a batch", support)
    group_halves = {g: sorted(support.loc[support.split_group_id == g, "A_half"].drop_duplicates().tolist(), key=str)
                    for g in groups}
    group_half_cells = {(g, h): [tuple(x) for x in support.loc[(support.split_group_id == g) &
                                                               (support.A_half == h), GROUP_COLUMNS].itertuples(index=False, name=None)]
                        for g in groups for h in group_halves[g]}
    if not work.index.is_unique:raise ValueError('metadata row indices must be unique')
    n_unique = int(work['trial_id'].nunique())
    steps = math.ceil(n_unique / batch_original_trials)
    exposure = []
    retry_ledger = []
    batch_indices = np.full((epochs, steps, batch_original_trials), -1, dtype=np.int64)
    for epoch in range(epochs):
        for step in range(steps):
            chosen_groups = rng.choice(groups, size=batch_original_trials // 4, replace=False)
            for slot, g in enumerate(chosen_groups):
                h = group_halves[g][int(rng.integers(len(group_halves[g])))]
                key = group_half_cells[(g, h)][int(rng.integers(len(group_half_cells[(g, h)])))]
                quartet, retries, fallback = _sample_cached(cell_defs[key], rng)
                if quartet is None:
                    raise QuartetSupportError("pair audit could not realize a supported cell", support)
                quartet_meta.append((qid, g, h, key))
                for pos, row_idx in enumerate(quartet):
                    records.append({"quartet_index": qid, "position": pos,
                                    "row_index": int(row_idx), "seed": seed,
                                    "cell_index": len(records)})
                exposure.append({"epoch": epoch, "step": step, "quartet_index": qid,
                                 "split_group_id": g, "A_half": h, "cell_key": key})
                batch_indices[epoch, step, slot * 4:slot * 4 + 4] = quartet
                retry_ledger.append({"epoch": epoch, "step": step, "quartet_index": qid,
                                     "retries": retries, "exact_fallback": fallback})
                qid += 1
    pairs = pd.DataFrame(records)
    qmeta = pd.DataFrame(quartet_meta, columns=["quartet_index", "group_id", "half", "cell_key"])
    return {"support": support, "pairs": pairs, "quartet_metadata": qmeta,
            "exposure": pd.DataFrame(exposure),
            "batch_indices": batch_indices,
            "retry_ledger": pd.DataFrame(retry_ledger),
            "steps_per_epoch": steps, "epochs": epochs, "seed": seed,
            "batch_original_trials": batch_original_trials}
