"""Pre-specified Route A controls using frozen representations and fit scopes.

The module has two independent controls.  ``reset_filter_epochs`` rebuilds
epochs from a raw HA source with a new causal filter state at every A block;
``balanced_control_indices`` makes a fixed, outcome-blind history/position
balanced trial subset.  The driver only loads already-fitted representation
checkpoints and never fits an encoder or alters the primary Route A outputs.
"""
from __future__ import annotations

import argparse
import json
import os
import traceback
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import pyedflib

from auditory5.preprocessing import (CausalPreprocessor, HA_CHANNELS,
                                     effective_impulse_support, extract_epoch)
from auditory5.provenance import ROOT, digest, object_hash, require_slurm, write_json
from auditory5.probes import bin_20ms
from auditory5.routes.a_matching import bootstrap_match
from auditory5.routes.route_a import (fit_transforms,
                                      mean_matching_matrices, summary_features,
                                      transform_summaries)
from auditory5.training import FittedEncoder


CONTROL_VERSION = "auditory5_A_controls_v1"
KNOWN_HISTORY = {0, 1}
KNOWN_MODES = ("L0", "R_SUP", "R_RAND", "R_SIM")


def block_ranges(n_samples: int, original_fs: float, block_seconds: float) -> list[tuple[int, int, int]]:
    """Return independent half-open raw blocks on the original sample grid."""
    n = int(n_samples)
    fs = float(original_fs)
    seconds = float(block_seconds)
    if n < 1 or n != n_samples or not np.isfinite(fs) or fs <= 0:
        raise ValueError("A_CONTROL_BLOCK_SCHEMA: invalid sample axis")
    width = int(round(seconds * fs))
    if width < 1 or not np.isclose(width, seconds * fs, atol=1e-9, rtol=0):
        raise ValueError("A_CONTROL_BLOCK_GRID: block width is not an integer sample count")
    return [(i, start, min(start + width, n))
            for i, start in enumerate(range(0, n, width))]


def _epoch_bounds(onset: int, original_fs: float, tmin: float = -.2,
                  tmax: float = .5) -> tuple[int, int]:
    def offset(seconds: float) -> int:
        value = seconds * original_fs
        nearest = round(value)
        return nearest if abs(value - nearest) < 1e-9 else int(np.ceil(value))
    return onset + offset(tmin), onset + offset(tmax)


def reset_block_mask(onsets, n_samples: int, original_fs: float, block_seconds: float,
                     startup_guard_seconds: float, end_embargo_seconds: float,
                     tmin: float = -.2,
                     tmax: float = .5) -> pd.DataFrame:
    """Compute block/reset eligibility without reading signal values.

    Epochs must be entirely inside one independent block and outside its startup
    guard.  The mask is additive: callers must retain the original QC/rejection
    mask and store this as a separate control eligibility column.
    """
    blocks = block_ranges(n_samples, original_fs, block_seconds)
    startup_guard = int(np.ceil(float(startup_guard_seconds) * float(original_fs)))
    end_embargo = int(np.ceil(float(end_embargo_seconds) * float(original_fs)))
    output = []
    for trial_id, value in enumerate(np.asarray(onsets)):
        onset = int(value)
        found = [b for b in blocks if b[1] <= onset < b[2]]
        if len(found) != 1:
            output.append(dict(event_index=trial_id, reset_eligible=False,
                               reset_block_id=-1, reset_reject_reason="onset_outside_blocks"))
            continue
        bid, start, stop = found[0]
        low, high = _epoch_bounds(onset, original_fs, tmin, tmax)
        eligible = low >= start + startup_guard and high <= stop - end_embargo
        output.append(dict(event_index=trial_id, reset_eligible=bool(eligible),
                           reset_block_id=bid,
                           reset_reject_reason="" if eligible else "reset_guard_or_block_boundary"))
    return pd.DataFrame(output)


@dataclass
class ResetEpochs:
    ledger: pd.DataFrame
    trial_ids: np.ndarray
    pre: np.ndarray
    post: np.ndarray


def reset_filter_epochs(raw: np.ndarray, original_fs: float,
                        channel_names: list[str] | tuple[str, ...],
                        events: pd.DataFrame, block_seconds: float,
                        support=None, *, end_embargo_seconds: float) -> ResetEpochs:
    """Filter each raw block with a fresh state and extract aligned epochs.

    No block is concatenated before filtering.  The returned ledger includes
    every input event and keeps any original ``accepted``/``reject_reason``
    columns untouched.  Only target events with complete reset-safe epochs have
    arrays in ``pre`` and ``post``.
    """
    x = np.asarray(raw, dtype=np.float64)
    raw_names = tuple(channel_names)
    if x.ndim != 2 or x.shape[0] != len(raw_names) or not np.isfinite(x).all():
        raise ValueError("A_CONTROL_RAW_SCHEMA: finite [channels,samples] required")
    names, channel_ix = _select_ha_channels(raw_names)
    x = x[channel_ix]
    if not events.trial_id.is_unique:
        raise ValueError("A_CONTROL_TRIAL_ID: input trial_id must be unique")
    if support is None:
        support = effective_impulse_support(float(original_fs))
    blocks = block_ranges(x.shape[1], original_fs, block_seconds)
    return _reset_filter_blocks(events, names, original_fs, blocks, support,
                                float(end_embargo_seconds),
                                lambda start, stop: x[:, start:stop])


def _select_ha_channels(raw_names) -> tuple[tuple[str, ...], np.ndarray]:
    """Select the fixed P1 scalp contract, excluding ears/status/aux channels."""
    names = tuple(str(x) for x in raw_names)
    if len(set(names)) != len(names) or not set(HA_CHANNELS).issubset(names):
        raise ValueError("A_CONTROL_CHANNEL_CONTRACT")
    return tuple(HA_CHANNELS), np.asarray([names.index(c) for c in HA_CHANNELS], dtype=int)


def _reset_filter_blocks(events: pd.DataFrame, names: tuple[str, ...],
                         original_fs: float, blocks, support,
                         end_embargo_seconds: float, loader) -> ResetEpochs:
    if tuple(names) != tuple(HA_CHANNELS):
        raise ValueError("A_CONTROL_CHANNEL_ORDER")
    end_embargo = int(np.ceil(float(end_embargo_seconds) * float(original_fs)))
    if not events.trial_id.is_unique or "onset_sample" not in events:
        raise ValueError("A_CONTROL_EVENT_SCHEMA: unique trial_id/onset_sample required")
    rows = events.copy().reset_index(drop=True)
    for column, default in (("reset_eligible", False), ("reset_block_id", -1),
                            ("reset_reject_reason", "not_target"),
                            ("reset_filter_segment_id", ""),
                            ("reset_pre_stop_index", -1),
                            ("reset_post_start_index", -1),
                            ("reset_post_stop_index", -1)):
        rows[column] = default
    pre, post, ids = [], [], []
    for bid, start, stop in blocks:
        selected = rows.index[(rows.onset_sample >= start) & (rows.onset_sample < stop)]
        if not len(selected):
            continue
        raw = np.asarray(loader(start, stop), dtype=np.float64)
        if raw.shape != (len(names), stop - start) or not np.isfinite(raw).all():
            raise ValueError("A_CONTROL_RAW_BLOCK_SCHEMA")
        processor = CausalPreprocessor(float(original_fs), names,
                                        bank="P1_CAUSAL20", p1_channels=names,
                                        segment_start_sample=start,
                                        grid_origin_sample=0, support=support)
        processed = processor.process(raw, start_sample=start)
        for index in selected:
            row = rows.loc[index]
            rows.at[index, "reset_block_id"] = bid
            rows.at[index, "reset_filter_segment_id"] = f"reset_block_{bid:04d}"
            if row.get("event_kind", "target") != "target":
                rows.at[index, "reset_reject_reason"] = "not_target"
                continue
            low, high = _epoch_bounds(int(row.onset_sample), float(original_fs))
            if (low < start + support.guard_samples or
                    high > stop - end_embargo):
                rows.at[index, "reset_reject_reason"] = "reset_guard_or_block_boundary"
                continue
            epoch = extract_epoch(processed, int(row.onset_sample))
            if not epoch.eligible:
                rows.at[index, "reset_reject_reason"] = "|".join(epoch.reject_reasons)
                continue
            pre_stop = int(np.searchsorted(epoch.times_s + 1e-10, 0.0))
            post_start = int(np.searchsorted(epoch.times_s + 1e-10, .05))
            post_stop = int(np.searchsorted(epoch.times_s + 1e-10, .45))
            if (epoch.data["all"].shape[-1] != 175 or pre_stop != 50 or
                    post_start not in (62, 63) or post_stop - post_start != 100):
                raise ValueError("A_CONTROL_EPOCH_GRID: frozen 250 Hz epoch changed")
            rows.at[index, "reset_eligible"] = True
            rows.at[index, "reset_reject_reason"] = ""
            rows.at[index, "reset_pre_stop_index"] = pre_stop
            rows.at[index, "reset_post_start_index"] = post_start
            rows.at[index, "reset_post_stop_index"] = post_stop
            ids.append(str(row.trial_id))
            pre.append(epoch.data["all"][:, :pre_stop].astype(np.float32))
            post.append(epoch.data["all"][:, post_start:post_stop].astype(np.float32))
    rows["reset_eligible"] = rows.reset_eligible.astype(bool)
    pre_array = np.stack(pre) if pre else np.empty((0, len(names), 50), dtype=np.float32)
    post_array = (np.stack(post) if post else
                  np.empty((0, len(names), 100), dtype=np.float32))
    return ResetEpochs(rows, np.asarray(ids, dtype=str), pre_array, post_array)


def reset_filter_bdf(locator: dict, record: dict, events: pd.DataFrame,
                     block_seconds: float, support=None, *, end_embargo_seconds: float) -> ResetEpochs:
    """Read one BDF block at a time and reset filter state at every block."""
    path = Path(locator["signal_path"])
    with pyedflib.EdfReader(str(path)) as reader:
        raw_names = tuple(reader.getSignalLabels())
        fs = np.asarray(reader.getSampleFrequencies(), dtype=float)
        n = np.asarray(reader.getNSamples(), dtype=int)
        names, channel_ix = _select_ha_channels(raw_names)
        if len(set(fs[channel_ix])) != 1 or len(set(n[channel_ix])) != 1:
            raise ValueError("A_CONTROL_SOURCE_CHANNEL_SHAPE")
        expected_fs = float(fs[channel_ix[0]])
        expected_n = int(n[channel_ix[0]])
        if not np.allclose(fs[channel_ix], expected_fs) or not np.all(n[channel_ix] == expected_n):
            raise ValueError("A_CONTROL_SOURCE_SHAPE_CHANGED")
        for key, expected in (("original_fs", expected_fs), ("n_samples", expected_n)):
            if key in record and not np.isclose(float(record[key]), expected):
                raise ValueError("A_CONTROL_MANIFEST_SHAPE_MISMATCH")
        if support is None:
            support = effective_impulse_support(expected_fs)
        blocks = block_ranges(expected_n, expected_fs, block_seconds)
        return _reset_filter_blocks(
            events, names, expected_fs, blocks, support, float(end_embargo_seconds),
            lambda start, stop: np.stack([reader.readSignal(int(i), start=start, n=stop - start)
                                           for i in channel_ix]))


def assert_trial_mask_alignment(reference: pd.DataFrame, control: pd.DataFrame) -> None:
    """Require unchanged trial IDs, labels, groups and original rejection mask."""
    for frame in (reference, control):
        if not frame.trial_id.is_unique:
            raise ValueError("A_CONTROL_ALIGNMENT: duplicate trial_id")
    if set(reference.trial_id) != set(control.trial_id):
        raise ValueError("A_CONTROL_ALIGNMENT: trial_id set changed")
    order = pd.Index(reference.trial_id)
    aligned = control.set_index("trial_id").loc[order].reset_index()
    for column in ("stimulus_local_id", "split_group_id"):
        if column in reference and column in aligned and not reference[column].reset_index(drop=True).equals(aligned[column]):
            raise ValueError(f"A_CONTROL_ALIGNMENT: {column} changed")
    if "accepted" in reference and "accepted" in aligned:
        if not np.array_equal(reference.accepted.to_numpy(bool), aligned.accepted.to_numpy(bool)):
            raise ValueError("A_CONTROL_ALIGNMENT: original rejection mask changed")


def _position_bin(values) -> np.ndarray:
    x = np.asarray(values, dtype=float)
    if not np.isfinite(x).all() or np.any((x < 0) | (x > 1)):
        raise ValueError("A_CONTROL_POSITION: fraction must lie in [0,1]")
    return np.minimum(np.floor(x * 3).astype(int), 2)


def balanced_control_indices(rows: pd.DataFrame, group: str, *, budget: int = 20,
                             half_column: str = "A_half", class_column: str = "stimulus_local_id",
                             eligible_column: str = "A_boundary_eligible",
                             seed: int = 20260917) -> np.ndarray | None:
    """Choose exactly ``budget`` trials per half/class across history×position cells.

    The selection is deterministic, uses no signal values or outcomes, and
    returns ``None`` when the frozen 6-cell support is unavailable.
    """
    needed = {"split_group_id", half_column, class_column, eligible_column,
              "history_target", "segment_position_fraction", "A_block_id", "trial_id"}
    if not needed.issubset(rows.columns):
        raise ValueError("A_CONTROL_BALANCE_SCHEMA: missing history/position columns")
    if budget < 6 or not rows.trial_id.is_unique:
        raise ValueError("A_CONTROL_BALANCE_BUDGET")
    position = _position_bin(rows.segment_position_fraction)
    history = rows.history_target.to_numpy()
    valid_history = np.isin(history, list(KNOWN_HISTORY))
    selected = []
    base, remainder = divmod(int(budget), 6)
    for half, cls in ((h, c) for h in (0, 1) for c in (0, 1)):
        own = ((rows.split_group_id == group).to_numpy() &
               rows[eligible_column].fillna(False).to_numpy(bool) &
               rows[half_column].eq(half).to_numpy() & rows[class_column].eq(cls).to_numpy() & valid_history)
        candidates = {cell: np.flatnonzero(own & (history == hist) & (position == pos))
                      for hist in (0, 1) for pos in (0, 1, 2)
                      for cell in [(hist, pos)]}
        if any(len(candidates[cell]) < base for cell in candidates):
            return None
        # The two remainder quotas are fixed by the frozen cell order, not by
        # observed cell counts; every half/class therefore uses the same
        # history×position allocation.
        order = sorted(candidates)
        quotas = {cell: base for cell in candidates}
        for cell in order[:remainder]:
            quotas[cell] += 1
        if any(len(candidates[cell]) < quotas[cell] for cell in candidates):
            return None
        rng = np.random.default_rng(seed + 1009 * (half + 1) + 17 * (cls + 1) + int(object_hash(group)[:8], 16))
        chosen = []
        for cell in sorted(candidates):
            chosen.extend(rng.choice(candidates[cell], quotas[cell], replace=False).tolist())
        if len(set(rows.iloc[chosen].A_block_id)) < 4:
            return None
        selected.extend(chosen)
    return np.asarray(sorted(selected), dtype=int)


def balanced_control_view(post: np.ndarray, pre: np.ndarray, rows: pd.DataFrame,
                          groups: list[str], *, budget: int = 20):
    """Apply the same trial selection to pre/post arrays and retain row order."""
    if len(post) != len(rows) or len(pre) != len(rows):
        raise ValueError("A_CONTROL_BALANCE_ALIGNMENT")
    indices = []
    for group in sorted(groups):
        chosen = balanced_control_indices(rows, group, budget=budget)
        if chosen is None:
            continue
        indices.extend(chosen.tolist())
    indices = np.asarray(sorted(set(indices)), dtype=int)
    return post[indices], pre[indices], rows.iloc[indices].reset_index(drop=True), indices


def _frozen_encoder(directory: Path, mode: str):
    if mode == "L0":
        return None
    checkpoint = directory / "encoder.pt"
    if not checkpoint.is_file():
        raise FileNotFoundError(f"A_CONTROL_ENCODER_MISSING:{mode}")
    encoder = FittedEncoder.load(checkpoint, device="cpu")
    if encoder.mode != mode:
        raise ValueError("A_CONTROL_ENCODER_MODE_SCOPE")
    return encoder


def _encode(epochs: np.ndarray, mode: str, encoder) -> np.ndarray:
    if mode == "L0":
        return bin_20ms(epochs)
    return np.asarray(encoder.transform(epochs), dtype=np.float32)


def _same_rows(rows: pd.DataFrame, trial_ids: np.ndarray) -> pd.DataFrame:
    if rows.trial_id.duplicated().any():
        raise ValueError("A_CONTROL_CACHE_TRIAL_ID")
    order = pd.Index(trial_ids, name='trial_id')
    if not set(order).issubset(set(rows.trial_id)):
        raise ValueError("A_CONTROL_CACHE_COVERAGE")
    return rows.set_index("trial_id").loc[order].reset_index()


def _encoder_scope_gate(encoder, task: dict, fold: dict, support_table: pd.DataFrame) -> str:
    """Check the actual checkpoint scope against execution.py's general gate."""
    if encoder is None:
        return "L0:no_encoder"
    general = set(support_table.loc[support_table.general, "split_group_id"].astype(str))
    expected_train = set(map(str, task["fit_groups"])) & general
    actual_train = set(map(str, encoder.scope.train_groups))
    if actual_train != expected_train:
        raise ValueError("A_CONTROL_ENCODER_SCOPE_GENERAL_INTERSECTION")
    if actual_train & set(map(str, encoder.scope.validation_groups + encoder.scope.test_groups)):
        raise ValueError("A_CONTROL_ENCODER_SCOPE_OVERLAP")
    if set(map(str, fold["test_groups"])) & actual_train:
        raise ValueError("A_CONTROL_ENCODER_TEST_TRAIN_OVERLAP")
    return encoder.scope.hash


def _balanced_indices(rows: pd.DataFrame, groups: list[str], budget: int = 20) -> tuple[np.ndarray, list[str]]:
    return _balanced_indices_seeded(rows, groups, budget=budget, seed=20260917)


def _balanced_indices_seeded(rows: pd.DataFrame, groups: list[str], *, budget: int = 20,
                             seed: int = 20260917) -> tuple[np.ndarray, list[str]]:
    picked, unsupported = [], []
    for group in sorted(map(str, groups)):
        chosen = balanced_control_indices(rows, group, budget=budget, seed=seed)
        if chosen is None:
            unsupported.append(group)
        else:
            picked.extend(chosen.tolist())
    return np.asarray(sorted(set(picked)), dtype=int), unsupported


def _balanced_repeated_values(post: np.ndarray, pre: np.ndarray, rows: pd.DataFrame,
                              groups: list[str], eligible_ids, *, budget: int = 20,
                              repetitions: int = 20):
    """Make independent balanced trial draws, then concatenate repetition axes."""
    per_rep, id_sets, diagnostics = [], [], []
    for rep in range(repetitions):
        chosen, unsupported = _balanced_indices_seeded(
            rows, groups, budget=budget, seed=20260917 + 100003 * rep)
        diagnostics.append({"unsupported_groups": len(unsupported),
                            "selected_trials": int(len(chosen))})
        if not len(chosen):
            return [], None, diagnostics
        subrows = rows.iloc[chosen].reset_index(drop=True)
        ids, values = summary_features(post[chosen], pre[chosen], subrows,
                                        sorted(map(str, eligible_ids)), "A_half",
                                        "A_boundary_eligible", repetitions=1,
                                        support_budget=budget)
        if len(ids) < 2:
            return [], None, diagnostics
        per_rep.append((list(map(str, ids)), values))
        id_sets.append(set(map(str, ids)))
    common = sorted(set.intersection(*id_sets)) if id_sets else []
    if len(common) < 2:
        return [], None, diagnostics
    merged = {}
    for key in per_rep[0][1]:
        pieces = []
        for ids, values in per_rep:
            # summary_features preserves the requested id order, but select
            # by explicit mapping so a future implementation cannot reorder.
            # Recompute the ordered ids from the current common intersection.
            # The qualified list is available through the deterministic input
            # order; all common ids are present in every repetition.
            positions = [ids.index(x) for x in common]
            pieces.append(values[key][:, positions])
        merged[key] = np.concatenate(pieces, axis=0)
    return common, merged, diagnostics


def _restrict_matrices(matrices: dict, ids, common_ids) -> dict:
    """Restrict every identity matrix to one explicitly shared candidate cohort."""
    positions = [list(ids).index(x) for x in common_ids]
    restricted = {}
    for key, value in matrices.items():
        if not isinstance(value, dict):
            continue
        restricted[key] = {}
        for metric in ("cosine", "inner_product", "squared_distance"):
            matrix = value.get(metric)
            if isinstance(matrix, np.ndarray) and matrix.ndim == 2:
                restricted[key][metric] = matrix[np.ix_(positions, positions)]
    return restricted


def _reset_record_cache(base: Path, split: dict, record_id: str, locators: dict,
                        records: pd.DataFrame, block_seconds: float,
                        embargo_seconds: float, support_by_fs: dict,
                        cache: dict, ledger_dir: Path) -> dict:
    """Build one raw reset per record and reuse it for every representation/control."""
    rid = str(record_id)
    if rid in cache:
        return cache[rid]
    export_base = base / "data" / split["export_run"] / "P1_CAUSAL20"
    event_path = export_base / rid / "events.parquet"
    if not event_path.is_file():
        raise FileNotFoundError("A_CONTROL_EVENT_CACHE_MISSING")
    record = records.loc[rid].to_dict()
    fs = float(record["original_fs"])
    support = support_by_fs.get(fs)
    if support is None:
        support = effective_impulse_support(fs)
        support_by_fs[fs] = support
    locator = locators[rid]
    summary_path=export_base/rid/'summary.json'
    if digest(summary_path)!=split['input_hashes']['P1_CAUSAL20/'+rid]:
        raise ValueError('A_CONTROL_EXPORT_CHANGED')
    source_summary=json.loads(summary_path.read_text())
    if digest(event_path)!=source_summary['output_sha256']['events.parquet']:
        raise ValueError('A_CONTROL_EVENT_LEDGER_CHANGED')
    raw_path=Path(locator['signal_path']);source_hash=digest(raw_path);before=raw_path.stat()
    if source_hash!=source_summary['source_sha256']:
        raise ValueError('A_CONTROL_RAW_SOURCE_CHANGED')
    rebuilt = reset_filter_bdf(locator, record, pd.read_parquet(event_path), block_seconds,
                               support, end_embargo_seconds=embargo_seconds)
    after=raw_path.stat()
    if (before.st_size,before.st_mtime_ns)!=(after.st_size,after.st_mtime_ns):
        raise ValueError('A_CONTROL_RAW_SOURCE_MUTATED_DURING_READ')
    rebuilt.ledger.to_parquet(ledger_dir / f"reset_{rid}_ledger.parquet", index=False)
    cache[rid] = {"record": record, "epochs": rebuilt,
                  "source_sha256": source_hash}
    return cache[rid]


def _fold_control(config, base: Path, split: dict, fold: dict, mode: str,
                  repdir: Path, locators: dict, records: pd.DataFrame,
                  block_seconds: float, embargo_seconds: float, support_by_fs: dict,
                  reset_cache: dict, output: Path) -> dict:
    fold_id = int(fold["outer_fold"])
    directory = repdir / f"outer{fold_id}_all_{mode}"
    if not (directory / "completion.json").is_file():
        return {"outer_fold": fold_id, "mode": mode, "status": "CACHE_MISSING"}
    completion = json.loads((directory / "completion.json").read_text())
    task = json.loads((directory / "task.json").read_text())
    if completion.get("status") != "PASS" or task.get("fit_groups") != fold["train_groups"]:
        raise ValueError("A_CONTROL_FIT_SCOPE_CACHE")
    with np.load(directory / "features.npz", allow_pickle=False) as arrays:
        original_post, original_pre = arrays["post"].astype(float), arrays["pre"].astype(float)
        cached_trials = arrays["trial_ids"].astype(str)
    cached_rows = pd.read_parquet(directory / "feature_rows.parquet")
    if not np.array_equal(cached_trials, cached_rows.trial_id.to_numpy(str)):
        raise ValueError("A_CONTROL_CACHE_FEATURE_ALIGNMENT")
    support_table = pd.read_parquet(base / "splits" / split["split_run"] / "support.parquet")
    eligible = set(support_table.loc[support_table.A, "split_group_id"].astype(str))
    train_ids, train_values = summary_features(
        original_post, original_pre, cached_rows, sorted(eligible & set(fold["train_groups"])),
        "A_half", "A_boundary_eligible")
    if len(train_ids) < 4:
        return {"outer_fold": fold_id, "mode": mode, "status": "TRAIN_SUPPORT_INSUFFICIENT"}
    encoder = _frozen_encoder(directory, mode)
    transforms = fit_transforms(train_values)
    scope_hash = _encoder_scope_gate(encoder, task, fold, support_table)
    base_rows = cached_rows[cached_rows.split_group_id.astype(str).isin(set(map(str, fold["test_groups"])))].copy()
    base_idx = np.flatnonzero(cached_rows.split_group_id.astype(str).isin(set(map(str, fold["test_groups"]))))
    continuous_post = original_post[base_idx]
    continuous_pre = original_pre[base_idx]

    reset_rows, reset_post, reset_pre = [], [], []
    source_hashes = {}
    for record_id in sorted(base_rows.record_id.astype(str).unique()):
        item = _reset_record_cache(base, split, record_id, locators, records, block_seconds,
                                   embargo_seconds, support_by_fs, reset_cache, output)
        rebuilt = item["epochs"]
        source_hashes[record_id] = item["source_sha256"]
        one = base_rows[base_rows.record_id.astype(str) == record_id].copy()
        assert_trial_mask_alignment(one, _same_rows(rebuilt.ledger, one.trial_id.to_numpy(str)))
        ledger = rebuilt.ledger.set_index("trial_id")
        keep = ledger.loc[one.trial_id, "reset_eligible"].to_numpy(bool)
        position = {trial: i for i, trial in enumerate(rebuilt.trial_ids)}
        available = [i for i, trial in enumerate(one.trial_id) if keep[i] and trial in position]
        if available:
            selected = one.iloc[available]
            reset_rows.append(selected)
            reset_post.append(rebuilt.post[[position[x] for x in selected.trial_id]])
            reset_pre.append(rebuilt.pre[[position[x] for x in selected.trial_id]])
    controls = {}
    if reset_rows:
        controls["reset"] = (pd.concat(reset_rows, ignore_index=True), np.concatenate(reset_post), np.concatenate(reset_pre))
    controls["continuous"] = (base_rows.reset_index(drop=True), continuous_post, continuous_pre)
    if reset_rows:
        reset_trial_ids = set(pd.concat(reset_rows, ignore_index=True).trial_id.astype(str))
        common_reset = base_rows[base_rows.trial_id.astype(str).isin(reset_trial_ids)].copy()
        common_index = np.flatnonzero(base_rows.trial_id.astype(str).isin(reset_trial_ids))
        controls["continuous_on_reset"] = (common_reset.reset_index(drop=True),
                                              continuous_post[common_index], continuous_pre[common_index])
    private_rows = {}
    matrix_files = {}
    balance_diagnostics = {}
    for control_name, (rows, post_raw, pre_raw) in controls.items():
        # The continuous cache already contains the frozen representation;
        # only raw-reset epochs need the encoder/binning pass here.
        if control_name.startswith("continuous"):
            post, pre = post_raw, pre_raw
        else:
            post, pre = _encode(post_raw, mode, encoder), _encode(pre_raw, mode, encoder)
        ids, values = summary_features(post, pre, rows, sorted(eligible & set(map(str, fold["test_groups"]))),
                                        "A_half", "A_boundary_eligible", budget=20, repetitions=20, support_budget=20)
        if len(ids) < 2:
            continue
        transformed = transform_summaries(values, transforms)
        matrices = {key: mean_matching_matrices(value[:, :, 0], value[:, :, 1])
                    for key, value in transformed.items()}
        # Always retain the independent unbalanced support.  Balanced support
        # is an additional subset and must never gate this result.
        matrix_files[f"{control_name}_unbalanced"] = (list(map(str, ids)), matrices)
        bids, bvalues, balance_diagnostics[control_name] = _balanced_repeated_values(
            post, pre, rows, sorted(eligible & set(map(str, fold["test_groups"]))),
            ids, budget=20, repetitions=20)
        if bvalues is None or len(bids) < 2:
            continue
        common_ids = sorted(set(map(str, ids)) & set(map(str, bids)))
        if len(common_ids) < 2:
            continue
        # The unbalanced and balanced estimates are compared on the same
        # candidate cohort; support loss is represented by the control status.
        matrix_files[f"{control_name}_unbalanced_on_balanced"] = (
            common_ids, _restrict_matrices(matrices, ids, common_ids))
        btransformed = transform_summaries(bvalues, transforms)
        balanced_matrices = {key: mean_matching_matrices(value[:, :, 0], value[:, :, 1])
                             for key, value in btransformed.items()}
        matrix_files[f"{control_name}_balanced"] = (
            common_ids, _restrict_matrices(balanced_matrices, bids, common_ids))
        private_rows[control_name] = rows[["trial_id", "record_id", "split_group_id", "stimulus_local_id",
                                           "A_block_id", "A_half", "history_target", "segment_position_fraction"]].copy()
    for name, (ids, values) in matrix_files.items():
        np.savez_compressed(output / f"outer{fold_id}_{mode}_{name}_matrices.npz",
                            ids=np.asarray(ids, dtype=str),
                            **{key: value["cosine"] for key, value in values.items()})
    for name, rows in private_rows.items():
        rows.to_parquet(output / f"outer{fold_id}_{mode}_{name}_control_rows.parquet", index=False)
    write_json(output / f"outer{fold_id}_{mode}_source_hashes.json", source_hashes)
    status = "PASS" if {"continuous_unbalanced", "continuous_balanced", "reset_unbalanced", "reset_balanced"} <= set(matrix_files) else "NEED_CONTROLS"
    return {"outer_fold": fold_id, "mode": mode, "status": status,
            "train_groups": len(train_ids), "control_files": sorted(matrix_files),
            "balance_diagnostics": balance_diagnostics,
            "reset_test_trials": int(sum(len(x) for x in reset_rows)),
            "encoder_scope_hash": scope_hash, "source_hash_count": len(source_hashes)}


def run(config, *, plan_path: str, split_run: str = "splits_001",
        output_run: str = "A_controls_001", modes: tuple[str, ...] = KNOWN_MODES,
        processing_spec_path: str = "private/auditory5_v1/validation/contracts_012/processing_spec.json",
        outer_folds: tuple[int, ...] | None = None):
    """Run controls with frozen cached encoders; callers must allocate Slurm."""
    require_slurm()
    private = ROOT / config["paths"]["private_relative"] / "routes" / output_run
    public = ROOT / config["paths"]["aggregates_relative"] / output_run
    private.mkdir(parents=True, exist_ok=False, mode=0o700)
    public.mkdir(parents=True, exist_ok=False)
    plan_file = Path(plan_path)
    if not plan_file.is_absolute():
        plan_file = ROOT / plan_file
    plan = json.loads(plan_file.read_text())
    base = ROOT / config["paths"]["private_relative"]
    split_file = base / "splits" / split_run / "folds.json"
    split = json.loads(split_file.read_text())
    if plan['split_run']!=split_run or plan['split_hash']!=digest(split_file) or plan['config_hash']!=object_hash(config):
        raise ValueError('A_CONTROL_PLAN_CONFIG_SPLIT_CHANGED')
    split["split_run"] = split_run
    requested_folds = set(map(int, outer_folds)) if outer_folds is not None else None
    run_folds = [fold for fold in split["folds"]
                 if requested_folds is None or int(fold["outer_fold"]) in requested_folds]
    if not run_folds:
        raise ValueError("A_CONTROL_OUTER_FOLD_SELECTION")
    spec_file = ROOT / processing_spec_path
    spec = json.loads(spec_file.read_text())
    block_seconds = float(spec["A_block_seconds"])
    embargo = float(spec["A_B_embargo_seconds"])
    if block_seconds < 4 * embargo + .7 - 1e-9:
        raise ValueError("A_CONTROL_BLOCK_TOO_SHORT")
    if not set(modes).issubset(KNOWN_MODES):
        raise ValueError("A_CONTROL_MODE")
    records = pd.read_parquet(base / "data" / split["export_run"] / "records.parquet") if (base / "data" / split["export_run"] / "records.parquet").exists() else pd.read_parquet(base / "data" / "manifest_001" / "records.parquet")
    records = records.set_index(records.record_id.astype(str))
    raw_locator_rows = pd.read_parquet(base / "data" / "manifest_001" / "raw_locators.parquet").set_index("record_id").to_dict("index")
    locators = {str(k): v for k, v in raw_locator_rows.items()}
    support_by_fs = {}
    repdir = Path(plan["source_snapshot"]).parent / "outputs"
    reset_cache = {}
    results = []
    for fold in run_folds:
        for mode in modes:
            try:
                results.append(_fold_control(config, base, split, fold, mode, repdir,
                                             locators, records, block_seconds, embargo, support_by_fs,
                                             reset_cache, private))
            except Exception as exc:
                (private / "errors.jsonl").open("a", encoding="utf-8").write(
                    json.dumps({"outer_fold": fold["outer_fold"], "mode": mode, "error": repr(exc),
                                "traceback": traceback.format_exc()}) + "\n")
                results.append({"outer_fold": fold["outer_fold"], "mode": mode, "status": "FAIL"})
    aggregates = {}
    expected_folds = len(run_folds)
    all_controls = ("continuous_unbalanced", "continuous_balanced",
                    "continuous_unbalanced_on_balanced", "reset_unbalanced",
                    "reset_balanced", "reset_unbalanced_on_balanced",
                    "continuous_on_reset_unbalanced")
    for mode in modes:
        for control in all_controls:
            files = [private / f"outer{fold['outer_fold']}_{mode}_{control}_matrices.npz" for fold in run_folds]
            if not all(path.is_file() for path in files):
                aggregates[f"{mode}:{control}"] = {"status": "NEED_CONTROLS", "complete_folds": sum(p.is_file() for p in files),
                                                     "total_folds": expected_folds}
                continue
            matrices, ids_by_fold, pre_matrices = [], [], []
            for path in files:
                with np.load(path, allow_pickle=False) as arrays:
                    if "post" not in arrays or "pre" not in arrays:
                        raise ValueError("A_CONTROL_MATRIX_SCHEMA")
                    matrices.append(arrays["post"])
                    pre_matrices.append(arrays["pre"])
                    ids_by_fold.append(arrays["ids"].astype(str))
            total_candidates = int(sum(len(x) for x in ids_by_fold))
            if (total_candidates < 25 or
                    any(len(ids) < 2 or m.shape != (len(ids), len(ids))
                        for m, ids in zip(matrices, ids_by_fold))):
                aggregates[f"{mode}:{control}"] = {"status": "NEED_CONTROLS", "complete_folds": expected_folds,
                                                     "total_folds": expected_folds,
                                                     "total_candidates": total_candidates,
                                                     "minimum_total_candidates": 25}
                continue
            stats = bootstrap_match(matrices, ids_by_fold, n_boot=2000, seed=20260917,
                                    paired_matrices=pre_matrices)
            stats.update({"status": "PASS", "complete_folds": expected_folds,
                          "total_candidates": total_candidates,
                          "minimum_total_candidates": 25})
            aggregates[f"{mode}:{control}"] = stats
        # Paired sensitivity estimates use the exact same candidate IDs in
        # each fold.  The balance pair is balanced minus its common-support
        # unbalanced estimate; the reset pair is reset minus continuous on
        # the same reset-eligible trial cohort.
        for label, left_name, right_name in (
                ("continuous_balance_minus_unbalanced", "continuous_balanced", "continuous_unbalanced_on_balanced"),
                ("reset_balance_minus_unbalanced", "reset_balanced", "reset_unbalanced_on_balanced"),
                ("reset_minus_continuous_same_reset_trials", "reset_unbalanced", "continuous_on_reset_unbalanced")):
            left_files = [private / f"outer{fold['outer_fold']}_{mode}_{left_name}_matrices.npz" for fold in run_folds]
            right_files = [private / f"outer{fold['outer_fold']}_{mode}_{right_name}_matrices.npz" for fold in run_folds]
            if not all(p.is_file() for p in left_files + right_files):
                aggregates[f"{mode}:{label}"] = {"status": "NEED_CONTROLS"}
                continue
            left, right, pair_ids = [], [], []
            for lp, rp in zip(left_files, right_files):
                with np.load(lp, allow_pickle=False) as la, np.load(rp, allow_pickle=False) as ra:
                    li, ri = la["ids"].astype(str), ra["ids"].astype(str)
                    common = sorted(set(li) & set(ri))
                    if len(common) < 2:
                        break
                    lix = [list(li).index(x) for x in common]
                    rix = [list(ri).index(x) for x in common]
                    left.append(la["post"][np.ix_(lix, lix)])
                    right.append(ra["post"][np.ix_(rix, rix)])
                    pair_ids.append(np.asarray(common, dtype=str))
            if len(pair_ids) != expected_folds:
                aggregates[f"{mode}:{label}"] = {"status": "NEED_CONTROLS"}
            else:
                paired = bootstrap_match(left, pair_ids, n_boot=2000, seed=20260917,
                                          paired_matrices=right)
                paired.update({"status": "PASS", "paired_direction": "left_minus_right",
                               "total_candidates": int(sum(len(x) for x in pair_ids))})
                aggregates[f"{mode}:{label}"] = paired
    smoke_incomplete = requested_folds is not None and len(run_folds) != len(split["folds"])
    if smoke_incomplete:
        aggregates = {key: {"status": "SMOKE_INCOMPLETE", "computed_folds": expected_folds}
                      for key in aggregates}
    implementation_errors = any(r["status"] == "FAIL" for r in results)
    aggregate_complete = all(x.get("status") == "PASS" for x in aggregates.values()) if aggregates else False
    overall_status = ("IMPLEMENTATION_FAIL" if implementation_errors else
                      ("SMOKE_INCOMPLETE" if smoke_incomplete else
                       ("PASS" if aggregate_complete else "NEED_CONTROLS")))
    summary = {"version": CONTROL_VERSION, "status": overall_status,
               "job_id": os.environ["SLURM_JOB_ID"], "output_run": output_run,
               "block_seconds": block_seconds, "embargo_seconds": embargo,
               "modes": list(modes), "outer_folds": [int(f["outer_fold"]) for f in run_folds],
               "results": results, "aggregates": aggregates,
               "primary_outputs_unchanged": True, "encoder_training_jobs": 0,
               "trial_id_and_original_reject_mask_preserved": True,
               "fit_scope_policy": "frozen outer training checkpoints and route-A training summaries only",
               "balanced_comparison_support": "within-fold intersection of unbalanced and balanced candidate IDs; continuous and reset remain separate",
               "input_hashes": {"plan": digest(plan_file), "split": digest(split_file), "processing_spec": digest(spec_file)},
               "code_hash": digest(Path(__file__))}
    write_json(private / "summary.json", summary)
    public_summary = {k: v for k, v in summary.items() if k not in {"results", "input_hashes"}}
    public_summary.update({"fold_mode_status": Counter(r["status"] for r in results),
                           "fold_mode_count": len(results)})
    write_json(public / "summary.json", public_summary)
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", required=True)
    parser.add_argument("--split-run", default="splits_001")
    parser.add_argument("--run", default="A_controls_001")
    parser.add_argument("--modes", nargs="+", default=list(KNOWN_MODES))
    parser.add_argument("--processing-spec", default="private/auditory5_v1/validation/contracts_012/processing_spec.json")
    parser.add_argument("--outer-folds", nargs="*", type=int, default=None)
    args = parser.parse_args()
    from auditory5.cli import read_config
    config = read_config("configs/auditory5_v1.yaml")
    run(config, plan_path=args.plan, split_run=args.split_run, output_run=args.run,
        modes=tuple(args.modes), processing_spec_path=args.processing_spec,
        outer_folds=None if args.outer_folds is None else tuple(args.outer_folds))


if __name__ == "__main__":
    main()
