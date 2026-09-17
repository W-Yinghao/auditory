"""Restricted native MFF epoch export for continuous and isolated E0 views.

The frozen contract is docs/mff_export_contract.md. The historical API bank
P1_CAUSAL20 selects the causal filter family only: outputs explicitly identify
P1_CAUSAL_NATIVE and retain every physical native channel. The E0 variant
resets reference/filter processing in disjoint 60 s raw blocks, discards a
20 s startup guard and an end embargo >= effective support. Stimulus history
always follows the full original chain, not artificial filter resets or QC.
"""

from collections import Counter
from dataclasses import asdict
import math
import os
from pathlib import Path
import tempfile

import numpy as np
import pandas as pd

from auditory5.adapters.mff import inspect_source, iter_raw_chunks
from auditory5.events import build_event_history
from auditory5.preprocessing import CausalPreprocessor, ProcessedChunk, effective_impulse_support, extract_epoch
from auditory5.provenance import digest, object_hash, write_json


MFF_QC_V1 = dict(epoch_over_ptp_fraction_max=0.10, epoch_raw_flat_fraction_max=0.10,
                 record_flat_channel_fraction_max=0.10)


def source_tree_snapshot(path, *, hash_contents):
    """Deterministic read-only file manifest; caller stores it under private."""
    base = Path(path)
    if not base.is_dir() or base.is_symlink():
        raise ValueError("MFF source must be an ordinary directory")
    rows = []
    for source in sorted(base.rglob("*")):
        if source.is_symlink():
            raise ValueError("MFF source contains an unverified symbolic link")
        if not source.is_file():
            continue
        stat = source.stat()
        row = dict(relative_path=source.relative_to(base).as_posix(),
                   size_bytes=stat.st_size, mtime_ns=stat.st_mtime_ns)
        if hash_contents:
            row["sha256"] = digest(source)
        rows.append(row)
    if not rows:
        raise ValueError("MFF source directory is empty")
    return rows


def _ceil_samples(seconds, fs):
    value = seconds * fs
    nearest = round(value)
    return nearest if abs(value - nearest) < 1e-9 else math.ceil(value)


def processing_regions(intervals, fs, view):
    """Do not merge adjacent storage intervals or fill a real acquisition gap."""
    if view not in ("continuous", "E0_BLOCK_RESET_60S"):
        raise ValueError("unknown MFF processing view")
    block_samples = round(60 * fs)
    if view != "continuous" and not math.isclose(block_samples, 60 * fs, abs_tol=1e-9):
        raise ValueError("60 s E0 blocks must have an exact original-sample definition")
    regions = []
    for interval in intervals:
        start, stop = interval["start_sample"], interval["stop_sample"]
        width = stop - start if view == "continuous" else block_samples
        for ordinal, first in enumerate(range(start, stop, width)):
            regions.append(dict(storage_segment_id=interval["segment_id"],
                                filter_segment_id=f'{interval["segment_id"]}:filter_{ordinal:04d}',
                                filter_block_id=len(regions), start_sample=first,
                                stop_sample=min(first + width, stop)))
    return regions


def original_events(record, metadata, *, non_sound_literals=()):
    """Preserve all literal annotations; unknown source roles interrupt history."""
    rid, fs = record["record_id"], metadata["sfreq"]
    intervals = {row["segment_id"]: row for row in metadata["intervals"]}
    target = {"stad": 0, "devt": 1}
    collisions = Counter(row["onset_sample"] for row in metadata["annotations"]
                         if row["event_literal"] in target)
    rows = []
    for annotation in metadata["annotations"]:
        ordinal = int(annotation["annotation_index"])
        segment = annotation["segment_id"]
        literal = annotation["event_literal"]
        mapped = literal in target
        conflict = mapped and collisions[annotation["onset_sample"]] > 1
        if annotation["annotation_origin"] == "reader_annotation" or literal in non_sound_literals:
            kind, evidence = "non_sound", "reader_annotation_or_explicit_frozen_non_sound_map"
        elif mapped and not conflict:
            kind, evidence = "target", "frozen_task_local_literal_mapping"
        else:
            kind, evidence = "unknown_sound", "unresolved_or_colliding_sound_conservative_break"
        interval = intervals.get(segment)
        sample = int(annotation["onset_sample"])
        rows.append(dict(
            record_id=rid, candidate_id=record["candidate_id"], split_group_id=record["split_group_id"],
            segment_id=rid + ":" + (segment or f"unstored_annotation_{ordinal}"),
            storage_segment_id=segment, trial_id=f"{rid}:annotation_{ordinal}",
            annotation_index=ordinal, event_literal=literal, stimulus_local_id=target.get(literal, -1),
            is_target_event=mapped, event_kind=kind, event_role_evidence=evidence,
            target_sample_collision=conflict, onset_sample=sample,
            onset_seconds_relative=sample / fs,
            source_onset_seconds_relative=annotation["onset_seconds_relative"],
            sample_alignment_residual=annotation["sample_alignment_residual"],
            in_stored_interval=annotation["in_stored_interval"], time_block_id=int((sample / fs) // 30),
            segment_position_fraction=((sample - interval["start_sample"]) / interval["n_samples"]
                                       if interval else None),
            paradigm_id=record["paradigm_id"], label_semantics="literal_only",
            code_map_hash=record["code_map_hash"],
            clinical_link_status=record.get("clinical_link_status", "unknown"),
            clinical_assessment_timing_status=record.get("clinical_assessment_timing_status", "unknown"),
            dynamic_condition_unknown=bool(record.get("dynamic_condition_unknown", True)),
            device_change_flag=bool(record.get("device_change_flag", False)),
        ))
    # Reader order is retained for simultaneous annotations; a collision was
    # already converted to an explicit history break rather than invented order.
    return build_event_history(rows, fs, target_codes=target)


def _epoch_array(path, shape, dtype):
    if shape[0] == 0:
        empty = np.empty(shape, dtype=dtype)
        np.save(path, empty)
        return empty
    return np.lib.format.open_memmap(path, mode="w+", dtype=dtype, shape=shape)


def export_record(record, locator, destination, bank, spec):
    """Export one source with bounded RAM and per-interval temporary memmaps.

    bank accepts the historical P1 API spelling or P1_CAUSAL_NATIVE. spec must
    explicitly freeze mff_qc, mff_qc_version and mff_view before signal QC.
    All complete epochs inside the selected filter region are stored even
    when rejected. Every original annotation remains in events.parquet.
    """
    if bank not in ("P1_CAUSAL20", "P1_CAUSAL_NATIVE"):
        raise ValueError("native MFF export supports only the P1 causal filter family")
    if spec.get("mff_qc_version") != "auditory5_mff_qc_v1" or spec.get("mff_qc") != MFF_QC_V1:
        raise ValueError("MFF_QC_NOT_FROZEN: explicit auditory5_mff_qc_v1 fractions are required")
    view = spec.get("mff_view")
    if view not in ("continuous", "E0_BLOCK_RESET_60S"):
        raise ValueError("MFF_VIEW_NOT_FROZEN")
    os.umask(0o077)
    dest = Path(destination)
    dest.mkdir(parents=True, mode=0o700, exist_ok=False)
    raw_path = Path(locator["signal_path"])
    before = source_tree_snapshot(raw_path, hash_contents=True)
    signature = [{key: value for key, value in row.items() if key != "sha256"} for row in before]
    source_hash = object_hash([{key: row[key] for key in ("relative_path", "size_bytes", "sha256")}
                              for row in before])
    metadata = inspect_source(raw_path)
    fs, names = metadata["sfreq"], metadata["physical_channel_names"]
    if fs != float(record["original_fs"]) or metadata["full_axis_samples"] != int(record["n_samples"]):
        raise ValueError("MFF source sampling or time-axis length differs from frozen manifest")
    support = effective_impulse_support(fs)
    embargo = float(spec["A_B_embargo_seconds"])
    if embargo < max(10.0, support.support_seconds) - 1e-12:
        raise ValueError("frozen MFF embargo is shorter than measured filter support")
    regions = processing_regions(metadata["intervals"], fs, view)
    events = original_events(record, metadata, non_sound_literals=spec.get("mff_non_sound_literals", ()))
    processor = CausalPreprocessor(fs, names, bank="P1_CAUSAL20", p1_channels=names, support=support)
    step, processed_fs = processor.decimation_factor, processor.processed_fs
    low_offset, high_offset = _ceil_samples(-.2, fs), _ceil_samples(.5, fs)
    stored_rows = []
    for row in events:
        row.update(preprocessing_id="P1_CAUSAL_NATIVE", processing_view=view,
                   original_fs=fs, processed_fs=processed_fs, qc_version=spec["mff_qc_version"],
                   source_sha256=source_hash, raw_locator_key=record["record_id"],
                   channel_map_hash=metadata["layout_hash"], stored_epoch_index=-1,
                   accepted=False, all_accepted=False, reject_reason="not_target", filter_segment_id=None,
                   saturation_status="unknown_no_audited_MFF_digital_rails")
        if not row["is_target_event"]:
            continue
        row["reject_reason"] = "incomplete_epoch_or_filter_region_boundary"
        low, high = row["onset_sample"] + low_offset, row["onset_sample"] + high_offset
        found = [region for region in regions if region["storage_segment_id"] == row["storage_segment_id"]
                 and low >= region["start_sample"] and high <= region["stop_sample"]]
        if len(found) != 1:
            continue
        region = found[0]
        row.update(stored_epoch_index=len(stored_rows), filter_segment_id=region["filter_segment_id"],
                   filter_block_id=region["filter_block_id"],
                   filter_start_sample=region["start_sample"], filter_stop_sample=region["stop_sample"])
        first_grid = low + (-low) % step
        row["epoch_n_samples"] = (high - 1 - first_grid) // step + 1
        stored_rows.append(row)
    lengths = {row["epoch_n_samples"] for row in stored_rows}
    if len(lengths) > 1:
        raise ValueError("native-rate phase produces variable epoch lengths; no implicit resampling permitted")
    shape_t = next(iter(lengths), (high_offset - low_offset + step - 1) // step)
    arrays = _epoch_array(dest / "all.npy", (len(stored_rows), len(names), shape_t), "float32")
    times = _epoch_array(dest / "times_s.npy", (len(stored_rows), shape_t), "float64")
    flat_count = np.zeros(len(names), dtype=np.int64)
    total_qc_blocks = 0
    raw_min, raw_max = np.full(len(names), np.inf), np.full(len(names), -np.inf)
    interval_events = {interval["segment_id"]: [row for row in stored_rows
                      if row["storage_segment_id"] == interval["segment_id"]]
                       for interval in metadata["intervals"]}
    with tempfile.TemporaryDirectory(prefix="mff_native_", dir=dest) as tmpname:
        temporary = Path(tmpname)
        for interval in metadata["intervals"]:
            first, last = interval["start_sample"], interval["stop_sample"]
            raw_file = temporary / "raw_interval.dat"
            raw = np.memmap(raw_file, mode="w+", dtype="float64", shape=(len(names), last - first))
            expected = first
            for chunk in iter_raw_chunks(raw_path, names, chunk_seconds=60,
                                         interval_subset=[interval["segment_id"]]):
                if chunk["start_sample"] != expected:
                    raise ValueError("MFF adapter emitted a noncontiguous stored interval")
                x = chunk["data_uv"]
                if not np.isfinite(x).all():
                    raise ValueError("nonfinite MFF source: no implicit signal repair")
                raw[:, chunk["start_sample"] - first:chunk["stop_sample"] - first] = x
                raw_min = np.minimum(raw_min, x.min(axis=1))
                raw_max = np.maximum(raw_max, x.max(axis=1))
                expected = chunk["stop_sample"]
            if expected != last:
                raise ValueError("MFF adapter did not cover the complete stored interval")
            raw.flush()
            qc_width = round(2 * fs)
            if not math.isclose(qc_width, 2 * fs, abs_tol=1e-9):
                raise ValueError("native 2 s QC blocks require exact original sample counts")
            for lo in range(0, last - first - qc_width + 1, qc_width):
                flat_count += np.ptp(raw[:, lo:lo + qc_width], axis=1) < spec["raw_flat_ptp_min_uv"]
                total_qc_blocks += 1
            for region in (r for r in regions if r["storage_segment_id"] == interval["segment_id"]):
                begin, end = region["start_sample"], region["stop_sample"]
                processor.reset_segment(begin)
                first_grid = begin + (-begin) % step
                out_count = max(0, (end - 1 - first_grid) // step + 1)
                if out_count == 0:
                    continue
                filtered_file = temporary / "filtered_region.dat"
                filtered = np.memmap(filtered_file, mode="w+", dtype="float64",
                                     shape=(len(names), out_count))
                written = 0
                for start in range(begin, end, max(1, round(60 * fs))):
                    stop = min(end, start + max(1, round(60 * fs)))
                    chunk = processor.process(raw[:, start - first:stop - first], start_sample=start)
                    size = len(chunk.source_samples)
                    filtered[:, written:written + size] = chunk.data["all"]
                    written += size
                if written != out_count:
                    raise ValueError("MFF decimation output count differs from original grid")
                filtered.flush()
                for row in interval_events[interval["segment_id"]]:
                    if row["filter_segment_id"] != region["filter_segment_id"]:
                        continue
                    onset, idx = row["onset_sample"], row["stored_epoch_index"]
                    low, high = onset + low_offset, onset + high_offset
                    first_epoch_grid = low + (-low) % step
                    index = (first_epoch_grid - first_grid) // step
                    samples = first_epoch_grid + np.arange(row["epoch_n_samples"]) * step
                    local = ProcessedChunk(
                        data={"all": filtered[:, index:index + len(samples)]}, source_samples=samples,
                        guard_valid=samples - begin >= support.guard_samples,
                        original_fs=fs, processed_fs=processed_fs, decimation_factor=step,
                        grid_origin_sample=0, segment_start_sample=begin, bank="P1_CAUSAL20")
                    epoch = extract_epoch(local, onset)
                    arrays[idx], times[idx] = epoch.data["all"], epoch.times_s
                    channel_ptp = np.ptp(epoch.data["all"], axis=1)
                    original = raw[:, low - first:high - first]
                    raw_ptp = np.ptp(original, axis=1)
                    over = channel_ptp > spec["scalp_ptp_max_uv"]
                    flat = raw_ptp < spec["raw_flat_ptp_min_uv"]
                    # Exact extrema repetition is descriptive only; MFF rail
                    # limits are unknown and are not borrowed from BDF headers.
                    repeated_extrema = ((original == original.min(axis=1, keepdims=True)) |
                                        (original == original.max(axis=1, keepdims=True))).mean(axis=1)
                    reasons = list(epoch.reject_reasons)
                    if low < begin + support.guard_samples and "startup_guard" not in reasons:
                        reasons.append("startup_guard")
                    if row["target_sample_collision"]:
                        reasons.append("target_sample_collision")
                    if over.mean() > MFF_QC_V1["epoch_over_ptp_fraction_max"]:
                        reasons.append("too_many_channels_over_ptp")
                    if flat.mean() > MFF_QC_V1["epoch_raw_flat_fraction_max"]:
                        reasons.append("too_many_raw_flat_channels")
                    if view == "E0_BLOCK_RESET_60S" and high > end - _ceil_samples(embargo, fs):
                        reasons.append("E0_block_end_embargo")
                    row.update(
                        grid_first_relative_s=float(epoch.times_s[0]),
                        post_start_index=int(np.searchsorted(epoch.times_s + 1e-10, .05)),
                        pre_stop_index=int(np.searchsorted(epoch.times_s + 1e-10, 0)),
                        post_n_samples=int(np.sum((epoch.times_s >= .05 - 1e-10) &
                                                  (epoch.times_s < .45 - 1e-10))),
                        all_ptp_uv=float(channel_ptp.max()), all_ptp_p50_uv=float(np.median(channel_ptp)),
                        all_ptp_p95_uv=float(np.percentile(channel_ptp, 95)),
                        over_ptp_channel_count=int(over.sum()), over_ptp_channel_fraction=float(over.mean()),
                        raw_flat_channel_count=int(flat.sum()), raw_flat_channel_fraction=float(flat.mean()),
                        raw_repeated_extrema_max_fraction=float(repeated_extrema.max()),
                        accepted=not reasons, all_accepted=not reasons, reject_reason="|".join(reasons))
                    del local, epoch, original
                del filtered
                filtered_file.unlink()
            del raw
            raw_file.unlink()
    fractions = flat_count / total_qc_blocks if total_qc_blocks else np.full(len(names), np.nan)
    persistent = fractions >= spec["record_raw_flat_fraction_max"]
    record_reasons = []
    if total_qc_blocks == 0:
        record_reasons.append("record_flat_qc_insufficient_2s_blocks")
    elif persistent.mean() > MFF_QC_V1["record_flat_channel_fraction_max"]:
        record_reasons.append("too_many_persistent_raw_flat_channels")
    if record.get("device_change_flag", False):
        record_reasons.append("unlocated_dynamic_condition_change")
    for row in stored_rows:
        if record_reasons:
            row["accepted"] = row["all_accepted"] = False
            row["reject_reason"] = "|".join(filter(None, [row["reject_reason"], *record_reasons]))
    for array in (arrays, times):
        if hasattr(array, "flush"):
            array.flush()
    after = source_tree_snapshot(raw_path, hash_contents=False)
    if signature != after:
        raise ValueError("MFF source tree changed during read-only export")
    pd.DataFrame(events).to_parquet(dest / "events.parquet", index=False)
    write_json(dest / "source_manifest.json", dict(content_manifest=before,
               signature_before=signature, signature_after=after, source_sha256=source_hash))
    write_json(dest / "processing_contract.json", dict(spec=spec, metadata=metadata,
               support=asdict(support), regions=regions, preprocessing_id="P1_CAUSAL_NATIVE"))
    pd.DataFrame(dict(channel=names, raw_min_uv=raw_min, raw_max_uv=raw_max,
                      raw_flat_2s_fraction=fractions, persistent_raw_flat=persistent,
                      reference_member=True)).to_csv(dest / "channel_qc.csv", index=False)
    summary = dict(
        record_id=record["record_id"], candidate_id=record["candidate_id"], split_group_id=record["split_group_id"],
        bank=bank, preprocessing_id="P1_CAUSAL_NATIVE", processing_view=view,
        native_layout_hash=metadata["layout_hash"], branch_channels={"all": names},
        physical_channels=len(names), excluded_reference_channels=metadata["excluded_reference_channel_names"],
        original_fs=fs, processed_fs=processed_fs, epoch_n_samples=shape_t,
        stored_epochs=len(stored_rows), target_events=sum(row["is_target_event"] for row in events),
        accepted=sum(row["accepted"] for row in events), source_sha256=source_hash,
        accepted_class_counts=dict(Counter(row["event_literal"] for row in events if row["accepted"])),
        code_counts=dict(Counter(row["event_literal"] for row in events)),
        filter_support_seconds=support.support_seconds, startup_guard_seconds=support.guard_seconds,
        E0_end_embargo_seconds=embargo if view != "continuous" else None,
        within_record_filter_state_isolation=view == "E0_BLOCK_RESET_60S",
        offline_record_qc=True, persistent_raw_flat_channels=int(persistent.sum()),
        persistent_raw_flat_channel_fraction=float(persistent.mean()),
        raw_flat_qc_blocks=total_qc_blocks, qc_version=spec["mff_qc_version"],
        raw_saturation_status="unknown_no_audited_MFF_digital_rails",
        comparison_to_legacy="different filter/reference/native channels; masks require explicit comparison",
        output_sha256={path.name: digest(path) for path in dest.iterdir() if path.is_file()})
    write_json(dest / "summary.json", summary)
    return summary
