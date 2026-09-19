"""D1 streaming export of continuous MFF recordings. No events are read; no epochs."""
from __future__ import annotations

import json
from collections import deque
from pathlib import Path

import numpy as np

from auditory5.adapters import mff

from . import contract

REGISTRY = "private/mff_001/registry.json"
CHUNK_SECONDS = 60.0


def registry(root: Path) -> dict[str, str]:
    rows = json.loads((root / REGISTRY).read_text())
    return {row["container_id"]: row["path"] for row in rows}


def retained_channels(metadata: dict) -> list[str]:
    """All physical EEG channels, with declared reference sensors excluded."""
    names = [n for n in metadata["physical_channel_names"]
             if n.strip().upper() not in mff.REFERENCE_NAMES]
    if not names:
        raise ValueError("D1_NO_PHYSICAL_CHANNELS")
    return names


def _emit(window: np.ndarray, centre: slice, original_fs: float, stride: int) -> np.ndarray:
    """Zero-phase filter the padded window, keep the centre, reference and decimate."""
    filtered = contract.filter_whole(window, original_fs)[:, centre]
    return contract.decimate(contract.average_reference(filtered), stride).astype(np.float32)


def _chunk_windows(chunks):
    """Yield (padded_block, centre_slice) so every chunk is emitted exactly once.

    A chunk is filtered inside a window holding its neighbours, so each emitted sample
    has a full 60 s chunk of real signal on either side except at the interval's true
    edges, where sosfiltfilt's own edge handling applies exactly as it would when
    filtering the whole interval at once. `d1_stream_agreement` checks this.
    """
    window: list = []
    emitted_first = False
    for chunk in chunks:
        window.append(chunk)
        if len(window) == 2 and not emitted_first:
            block = np.concatenate(window, axis=1)
            yield block, slice(0, window[0].shape[1])
            emitted_first = True
        elif len(window) == 3:
            block = np.concatenate(window, axis=1)
            offset = window[0].shape[1]
            yield block, slice(offset, offset + window[1].shape[1])
            window.pop(0)
    if len(window) == 1:
        yield window[0], slice(0, window[0].shape[1])
    elif len(window) == 2:
        block = np.concatenate(window, axis=1)
        yield block, slice(window[0].shape[1], block.shape[1])


def stream_interval(path: str, names: list[str], interval_index: int,
                    original_fs: float, stride: int):
    """Yield decimated, average-referenced float32 blocks for one stored interval."""
    step = int(round(CHUNK_SECONDS * original_fs))
    if step % stride:
        raise ValueError("D1_CHUNK_NOT_STRIDE_ALIGNED")
    chunks = (chunk["data_uv"] for chunk in
              mff.iter_raw_chunks(path, names, chunk_seconds=CHUNK_SECONDS,
                                  interval_subset=[interval_index]))
    for block, centre in _chunk_windows(chunks):
        yield _emit(block, centre, original_fs, stride)


def d1_stream_agreement(seed: int = 20260919, chunk_count: int = 7,
                        original_fs: float = 1000.0, channels: int = 3) -> dict:
    """The chunked emission must reproduce whole-interval zero-phase filtering.

    Runs the real `_chunk_windows` path against `contract.filter_whole` on the same
    synthetic interval, for every chunk count from 1 up, so the single-chunk, two-chunk
    and general cases are all covered.
    """
    rng = np.random.default_rng(seed)
    step = int(CHUNK_SECONDS * original_fs)
    results = []
    for count in range(1, chunk_count + 1):
        n = count * step
        time = np.arange(n) / original_fs
        signal_uv = (rng.standard_normal((channels, n))
                     + 9.0 * np.sin(2 * np.pi * 9.5 * time)[None, :]
                     + 4.0 * np.sin(2 * np.pi * 0.3 * time)[None, :])
        chunks = [signal_uv[:, i * step:(i + 1) * step] for i in range(count)]
        streamed = np.concatenate(
            [contract.filter_whole(block, original_fs)[:, centre]
             for block, centre in _chunk_windows(iter(chunks))], axis=1)
        whole = contract.filter_whole(signal_uv, original_fs)
        assert streamed.shape == whole.shape, (count, streamed.shape, whole.shape)
        difference = float(np.max(np.abs(streamed - whole)))
        scale = float(np.max(np.abs(whole)))
        results.append({"chunks": count, "max_abs_difference": difference,
                        "relative": difference / scale})
    worst = max(r["relative"] for r in results)
    return {"cases": results, "worst_relative": worst,
            "status": "AGREE" if worst < 1e-6 else "DISAGREE"}


def export_container(root: Path, container_id: str, destination: Path) -> dict:
    """Export every long-enough stored interval of one container."""
    path = registry(root)[container_id]
    metadata = mff.inspect_source(path)
    original_fs = float(metadata["sfreq"])
    stride = contract.stride_for(original_fs)
    names = retained_channels(metadata)
    rate = original_fs / stride

    pieces, boundaries, skipped = [], [], []
    samples = 0
    for interval in metadata["intervals"]:
        length = interval["stop_sample"] - interval["start_sample"]
        seconds = length / original_fs
        if seconds < contract.MIN_INTERVAL_SECONDS:
            skipped.append({"interval_index": int(interval["interval_index"]),
                            "seconds": round(seconds, 3), "reason": "interval_shorter_than_minimum"})
            continue
        produced = 0
        for block in stream_interval(path, names, int(interval["interval_index"]),
                                     original_fs, stride):
            pieces.append(block)
            produced += block.shape[1]
        boundaries.append({"interval_index": int(interval["interval_index"]),
                           "start": samples, "stop": samples + produced,
                           "original_start_sample": int(interval["start_sample"])})
        samples += produced
    if not pieces:
        return {"container_id": container_id, "status": "D1_NO_USABLE_INTERVAL",
                "skipped_intervals": skipped}

    data = np.concatenate(pieces, axis=1)
    assert data.shape == (len(names), samples), "D1 concatenation length mismatch"
    quality = contract.qc_blocks(data, rate)
    destination.mkdir(parents=True, exist_ok=True)
    array_path = destination / f"{container_id}.npy"
    np.save(array_path, data)
    array_path.chmod(0o600)
    payload = {
        "container_id": container_id, "contract": contract.CONTRACT_VERSION,
        "status": "D1_EXPORTED", "channels": names, "n_channels": len(names),
        "rate_hz": rate, "original_fs": original_fs, "stride": stride,
        "n_samples": int(samples), "seconds": round(samples / rate, 3),
        "intervals": boundaries, "skipped_intervals": skipped,
        "sensor_net": metadata.get("sensor_net"), "layout_hash": metadata.get("layout_hash"),
        "qc_n_blocks": int(quality.get("n_blocks", 0)),
        "qc_blocks_with_any_channel_over_threshold":
            int((quality["channels_over_threshold"] > 0).sum()) if quality.get("n_blocks") else 0,
        "qc_blocks_with_any_flat_channel":
            int((quality["channels_flat"] > 0).sum()) if quality.get("n_blocks") else 0,
        "qc_median_block_peak_to_peak_uv":
            float(np.median(quality["block_median_peak_to_peak_uv"])) if quality.get("n_blocks") else None,
        "value_abs_max_uv": float(np.abs(data).max()),
        "nonfinite_samples": int((~np.isfinite(data)).sum()),
    }
    if quality.get("n_blocks"):
        qc_path = destination / f"{container_id}_qc.npz"
        np.savez_compressed(qc_path, channels_over_threshold=quality["channels_over_threshold"],
                            channels_flat=quality["channels_flat"],
                            block_median_peak_to_peak_uv=quality["block_median_peak_to_peak_uv"])
        qc_path.chmod(0o600)
    meta_path = destination / f"{container_id}.json"
    meta_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    meta_path.chmod(0o600)
    return payload
