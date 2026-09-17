"""Read-only streaming MFF adapter using the Phase 3 audited MNE reader.

All calls belong in Slurm jobs. Paths and detailed reader failures must remain
in the caller's private workspace/logs. This module writes no files and returns
no source path, patient metadata, or absolute acquisition dates. Raw EEG stays
lazy; each requested chunk is bounded by a real stored interval.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Iterator, Sequence
from pathlib import Path
from typing import Any

import mne
import numpy as np
from mne._fiff.constants import FIFF
from scipy.optimize import linear_sum_assignment

from auditory5.preprocessing import HA_CHANNELS


REFERENCE_NAMES = frozenset({"VREF", "VERTEX REFERENCE", "REF"})


def _open_raw(path: str | Path):
    # [] explicitly preserves all event literals, including sync and TREV.
    return mne.io.read_raw_egi(
        path, preload=False, exclude=[], events_as_annotations=True, verbose="ERROR"
    )


def _hash(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _integer_vector(value: Any, field: str) -> np.ndarray:
    array = np.asarray(value)
    if array.ndim != 1 or not np.issubdtype(array.dtype, np.integer):
        raise ValueError(f"MFF {field} must be a one-dimensional integer sample array")
    if not len(array) or np.any(array < 0) or np.any(array > np.iinfo(np.int64).max):
        raise ValueError(f"MFF {field} has invalid sample indices")
    return array.astype(np.int64)


def _stored_intervals(raw) -> list[dict[str, Any]]:
    """Use reader extras' exclusive stops, never Raw.last_samp (inclusive)."""
    if raw.preload or int(raw.first_samp) != 0 or len(raw._raw_extras) != 1:
        raise ValueError("MFF adapter requires one fresh uncropped lazy source")
    extra = raw._raw_extras[0]
    if "first_samps" not in extra or "last_samps" not in extra:
        raise ValueError("MFF reader is missing explicit stored interval coordinates")
    starts = _integer_vector(extra["first_samps"], "first_samps")
    stops = _integer_vector(extra["last_samps"], "last_samps")
    if (starts.shape != stops.shape or np.any(stops <= starts)
            or np.any(starts[1:] < stops[:-1]) or np.any(stops > raw.n_times)):
        raise ValueError("MFF stored intervals are invalid or overlapping")
    if "samples_block" in extra:
        blocks = _integer_vector(extra["samples_block"], "samples_block")
        if int(blocks.sum()) != int((stops - starts).sum()):
            raise ValueError("MFF stored intervals disagree with binary block sample counts")
    return [dict(segment_id=f"segment_{i:04d}", interval_index=i,
                 start_sample=int(start), stop_sample=int(stop),
                 n_samples=int(stop - start),
                 gap_before_samples=int(start - (stops[i - 1] if i else 0)))
            for i, (start, stop) in enumerate(zip(starts, stops))]


def _physical_channels(raw) -> tuple[list[int], list[str]]:
    eeg = list(mne.pick_types(raw.info, eeg=True, exclude=[]))
    if not eeg or len(set(raw.ch_names)) != len(raw.ch_names):
        raise ValueError("MFF requires uniquely named EEG channels")
    reference_positions = []
    for index in eeg:
        reference = np.asarray(raw.info["chs"][index]["loc"][3:6], dtype=float)
        if np.isfinite(reference).all() and np.linalg.norm(reference) > 0:
            reference_positions.append(reference)
    physical, excluded = [], []
    for index in eeg:
        channel = raw.info["chs"][index]
        name = raw.ch_names[index]
        position = np.asarray(channel["loc"][:3], dtype=float)
        coincides_with_declared_reference = (
            np.isfinite(position).all() and any(
                np.linalg.norm(position - ref) <= 1e-9 for ref in reference_positions
            )
        )
        if name.strip().upper() in REFERENCE_NAMES or coincides_with_declared_reference:
            excluded.append(name)
            continue
        if channel["unit"] != FIFF.FIFF_UNIT_V:
            raise ValueError("physical EEG must be calibrated by MNE in volts")
        physical.append(index)
    if len(physical) < 2:
        raise ValueError("fewer than two physical nonreference EEG channels")
    cals = np.asarray(raw._cals)[physical]
    if not np.isfinite(cals).all() or np.any(cals <= 0):
        raise ValueError("MNE physical EEG calibration is invalid")
    return physical, excluded


def _geometry(raw, picks: list[int]) -> list[dict[str, Any]]:
    geometry = []
    for index in picks:
        channel = raw.info["chs"][index]
        position = np.asarray(channel["loc"][:3], dtype=float)
        finite = bool(np.isfinite(position).all() and np.linalg.norm(position) > 0)
        head = int(channel["coord_frame"]) == int(FIFF.FIFFV_COORD_HEAD)
        geometry.append(dict(
            channel_name=raw.ch_names[index],
            xyz_m=position.tolist() if finite else None,
            coord_frame="head" if head else "unverified",
            coord_frame_id=int(channel["coord_frame"]),
            usable_for_mapping=finite and head,
        ))
    return geometry


def _inspect_raw(raw) -> dict[str, Any]:
    sfreq = float(raw.info["sfreq"])
    if not math.isfinite(sfreq) or sfreq <= 0:
        raise ValueError("MFF sampling frequency must be finite positive Hz")
    intervals = _stored_intervals(raw)
    picks, excluded = _physical_channels(raw)
    geometry = _geometry(raw, picks)
    names = [raw.ch_names[index] for index in picks]
    layout = [dict(channel_name=row["channel_name"], coord_frame=row["coord_frame"],
                   coord_frame_id=row["coord_frame_id"],
                   xyz_m=(None if row["xyz_m"] is None else
                          [round(coordinate, 9) for coordinate in row["xyz_m"]]))
              for row in geometry]
    literal_codes = set(str(code) for code in raw._raw_extras[0].get("event_codes", []))
    annotations = []
    starts = np.asarray([row["start_sample"] for row in intervals])
    for ordinal, (onset, duration, literal) in enumerate(zip(
        raw.annotations.onset, raw.annotations.duration, raw.annotations.description
    )):
        onset, duration, literal = float(onset), float(duration), str(literal)
        if not math.isfinite(onset) or not math.isfinite(duration) or duration < 0:
            raise ValueError("MFF annotation has invalid relative timing")
        fractional_sample = onset * sfreq
        sample = int(round(fractional_sample))
        interval_index = int(np.searchsorted(starts, sample, side="right") - 1)
        stored = (interval_index >= 0 and sample < intervals[interval_index]["stop_sample"])
        annotations.append(dict(
            annotation_index=ordinal,
            event_literal=literal,
            onset_sample=sample,
            onset_sample_fractional=fractional_sample,
            sample_alignment_residual=fractional_sample - sample,
            onset_seconds_relative=onset,
            duration_seconds=duration,
            segment_id=intervals[interval_index]["segment_id"] if stored else None,
            in_stored_interval=bool(stored),
            annotation_origin="source_literal" if literal in literal_codes else "reader_annotation",
        ))
    return dict(
        schema_version="auditory5_mff_adapter_v1",
        reader="mne.io.read_raw_egi",
        reader_version=str(mne.__version__),
        sfreq=sfreq,
        physical_channel_names=names,
        excluded_reference_channel_names=excluded,
        intervals=intervals,
        stored_samples=sum(row["n_samples"] for row in intervals),
        full_axis_samples=int(raw.n_times),
        interval_stop_convention="exclusive",
        sample_axis="original_recording_samples_no_gap_compression",
        annotations=annotations,
        annotation_scope="all_reader_source_literals_plus_reader_annotations",
        annotation_clock="MNE audited original sample conversion; no acoustic latency correction",
        geometry=geometry,
        layout_hash=_hash(layout),
        layout_hash_definition="ordered physical names, declared frames, coordinates rounded to 1e-9 m",
        mne_calibration_volts_per_stored_unit=np.asarray(raw._cals)[picks].tolist(),
        output_unit="uV",
        volts_to_output_factor=1e6,
        reference_policy="exclude explicit reference names or exact declared reference positions; no rereference",
        native_layout_preferred=True,
    )


def inspect_source(path: str | Path) -> dict[str, Any]:
    """Inspect source headers/geometry/annotations without loading EEG arrays."""
    raw = _open_raw(path)
    try:
        return _inspect_raw(raw)
    finally:
        raw.close()


def iter_raw_chunks(
    path: str | Path,
    channel_names: Sequence[str],
    chunk_seconds: float = 60.0,
    interval_subset: Sequence[str | int] | None = None,
) -> Iterator[dict[str, Any]]:
    """Yield bounded calibrated EEG chunks, never spanning a storage gap.

    ``interval_subset`` contains explicit segment IDs or interval indices;
    intervals always emit in their original order. Filtering/state reset is
    the caller's responsibility at each new segment_id. ``data_uv`` is
    [selected channels, original-rate samples], preserving requested order.
    Chunk size is capped at 60 s to prevent accidental full-record EEG reads.
    Closing the generator also closes the underlying lazy MNE reader. MNE's
    upstream disk index/event metadata can still scale with recording length.
    """
    if not math.isfinite(chunk_seconds) or not 0 < chunk_seconds <= 60:
        raise ValueError("chunk_seconds must be positive seconds, at most 60")
    names = tuple(channel_names)
    if not names or len(set(names)) != len(names):
        raise ValueError("requested physical channel names must be nonempty and unique")
    raw = _open_raw(path)
    try:
        metadata = _inspect_raw(raw)
        if not set(names).issubset(metadata["physical_channel_names"]):
            raise ValueError("requested channels include absent or virtual/reference channels")
        sfreq = metadata["sfreq"]
        step = max(1, int(math.floor(chunk_seconds * sfreq)))
        picks = [raw.ch_names.index(name) for name in names]
        intervals = metadata["intervals"]
        if interval_subset is not None:
            selected_ids = set()
            for selected in interval_subset:
                matches = [row for row in intervals if selected == row["segment_id"]
                           or (not isinstance(selected, (bool, np.bool_))
                               and isinstance(selected, (int, np.integer))
                               and int(selected) == row["interval_index"])]
                if len(matches) != 1 or matches[0]["segment_id"] in selected_ids:
                    raise ValueError("interval_subset must select distinct existing intervals")
                selected_ids.add(matches[0]["segment_id"])
            intervals = [row for row in intervals if row["segment_id"] in selected_ids]
        for interval in intervals:
            for start in range(interval["start_sample"], interval["stop_sample"], step):
                stop = min(start + step, interval["stop_sample"])
                # MNE get_data applies acquisition gain/calibration and returns V.
                # Apply only the SI conversion here; _cals must not be applied twice.
                data_uv = np.asarray(raw.get_data(picks=picks, start=start, stop=stop),
                                     dtype=np.float64) * 1e6
                if data_uv.shape != (len(names), stop - start):
                    raise ValueError("MFF chunk shape differs from requested original samples")
                yield dict(
                    segment_id=interval["segment_id"],
                    interval_start_sample=interval["start_sample"],
                    interval_stop_sample=interval["stop_sample"],
                    start_sample=start,
                    stop_sample=stop,
                    original_fs=sfreq,
                    channel_names=list(names),
                    data_uv=data_uv,
                )
    finally:
        raw.close()


def standard_1020_head_positions(
    channel_names: Sequence[str] = HA_CHANNELS,
) -> np.ndarray:
    """Return standard montage locations explicitly transformed to head metres."""
    standard = mne.channels.make_standard_montage("standard_1020")
    positions = standard.get_positions()["ch_pos"]
    if any(name not in positions for name in channel_names):
        raise ValueError("requested target is absent from standard_1020")
    transform = mne.channels.compute_native_head_t(standard, verbose="ERROR")
    return np.asarray([mne.transforms.apply_trans(transform, positions[name])
                       for name in channel_names], dtype=np.float64)


def map_to_standard_1020(
    metadata: dict[str, Any], *, maximum_distance_m: float = 0.04,
) -> dict[str, Any]:
    """Diagnose a one-to-one HA-20 map; never duplicate or interpolate sensors.

    Native-layout analysis remains preferred. A Hungarian assignment is
    accepted only if all 20 targets have unique physical sensors within the
    fixed 40 mm limit. A cost penalty first minimizes violations, avoiding an
    unnecessary failed map when a fully admissible assignment exists.
    Missing coordinates or insufficient sensors return a hold diagnosis.
    """
    if maximum_distance_m != 0.04:
        raise ValueError("v1 cross-layout distance threshold is frozen at 0.04 m")
    targets = standard_1020_head_positions()
    geometry = metadata["geometry"]
    physical = set(metadata["physical_channel_names"])
    valid = [row for row in geometry if row["channel_name"] in physical
             and row.get("usable_for_mapping", False) and row.get("coord_frame") == "head"
             and row.get("xyz_m") is not None and np.isfinite(row["xyz_m"]).all()]
    if len({row["channel_name"] for row in valid}) != len(valid):
        raise ValueError("geometry contains duplicate physical electrode names")
    result = dict(
        mapping_schema="auditory5_mff_1020_mapping_v1", target_channel_names=list(HA_CHANNELS),
        target_coord_frame="head", coordinate_unit="m", maximum_distance_m=maximum_distance_m,
        layout_hash=metadata["layout_hash"], native_layout_preferred=True,
        n_available_physical_geometry=len(valid), mapping=[],
        status="hold_insufficient_physical_geometry", eligible=False,
    )
    if len(valid) < len(HA_CHANNELS):
        return result
    positions = np.asarray([row["xyz_m"] for row in valid], dtype=np.float64)
    if positions.shape != (len(valid), 3):
        raise ValueError("physical coordinates must be three-dimensional metres")
    distance = np.linalg.norm(targets[:, None, :] - positions[None, :, :], axis=2)
    penalty = (len(HA_CHANNELS) + 1) * (float(distance.max()) + 1.0)
    cost = distance + (distance > maximum_distance_m) * penalty
    rows, columns = linear_sum_assignment(cost)
    mapping = []
    for row, column in zip(rows, columns):
        mapping.append(dict(
            target_channel=HA_CHANNELS[row], native_channel=valid[column]["channel_name"],
            distance_m=float(distance[row, column]),
            within_threshold=bool(distance[row, column] <= maximum_distance_m),
            target_xyz_m=targets[row].tolist(), native_xyz_m=positions[column].tolist(),
        ))
    accepted = len(mapping) == len(HA_CHANNELS) and all(row["within_threshold"] for row in mapping)
    result.update(mapping=mapping, eligible=accepted,
                  status="eligible" if accepted else "hold_distance_exceeds_40mm",
                  maximum_assigned_distance_m=max(row["distance_m"] for row in mapping),
                  mapping_hash=_hash(mapping))
    return result
