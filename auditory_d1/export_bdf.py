"""D1 export of the 22-channel clinical BDF branch. Same contract as the MFF branch."""
from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
import pyedflib

from auditory5.preprocessing import HA_CHANNELS

from . import contract
from .export import _chunk_windows

CHUNK_SECONDS = 60.0
PATH_MAP = "private/inventory_001/file_path_map.csv"
BDF_INDEX = "results/other_eeg_001/bdf_index.csv"


def signal_records(root: Path) -> list[dict]:
    """Signal-role BDF files with their audited shape. Event files are not read."""
    with (root / PATH_MAP).open(newline="", encoding="utf-8") as handle:
        paths = {r["file_id"]: r["absolute_path"] for r in csv.DictReader(handle)}
    rows = []
    with (root / BDF_INDEX).open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if "signal" not in str(row["file_role"]).lower() or row["read_status"] != "ok":
                continue
            rows.append({"container_id": row["file_id"], "path": paths[row["file_id"]],
                         "candidate_acquisition_id": row["candidate_acquisition_id"],
                         "duration_s": float(row["duration_s"]), "n_channels": int(row["n_channels"])})
    return sorted(rows, key=lambda r: r["container_id"])


def _read_chunks(reader, picks, n_samples, step):
    for start in range(0, n_samples, step):
        stop = min(n_samples, start + step)
        block = np.stack([reader.readSignal(k, start=start, n=stop - start) for k in picks])
        if not np.isfinite(block).all():
            raise ValueError("D1_NONFINITE_SOURCE")
        yield np.asarray(block, dtype=np.float64)


def export_record(root: Path, entry: dict, destination: Path) -> dict:
    """Export one BDF recording as a single continuous interval."""
    path = Path(entry["path"])
    with pyedflib.EdfReader(str(path)) as reader:
        names = reader.getSignalLabels()
        if len(set(names)) != len(names) or not set(HA_CHANNELS) <= set(names):
            raise ValueError("D1_BDF_CHANNEL_CONTRACT")
        rates = np.asarray(reader.getSampleFrequencies(), dtype=float)
        picks = [names.index(c) for c in HA_CHANNELS]
        if not np.all(rates[picks] == rates[picks][0]):
            raise ValueError("D1_BDF_MIXED_RATES")
        original_fs = float(rates[picks[0]])
        headers = reader.getSignalHeaders()
        if any(headers[k]["dimension"] != "uV" for k in picks):
            raise ValueError("D1_BDF_UNIT_CHANGED")
        n_samples = int(reader.getNSamples()[picks[0]])
        stride = contract.stride_for(original_fs)
        step = int(round(CHUNK_SECONDS * original_fs))
        if step % stride:
            raise ValueError("D1_CHUNK_NOT_STRIDE_ALIGNED")
        if n_samples / original_fs < contract.MIN_INTERVAL_SECONDS:
            return {"container_id": entry["container_id"], "status": "D1_NO_USABLE_INTERVAL"}
        pieces = []
        for block, centre in _chunk_windows(_read_chunks(reader, picks, n_samples, step)):
            filtered = contract.filter_whole(block, original_fs)[:, centre]
            pieces.append(contract.decimate(contract.average_reference(filtered),
                                            stride).astype(np.float32))
    data = np.concatenate(pieces, axis=1)
    rate = original_fs / stride
    quality = contract.qc_blocks(data, rate)
    destination.mkdir(parents=True, exist_ok=True)
    array_path = destination / f"{entry['container_id']}.npy"
    np.save(array_path, data)
    array_path.chmod(0o600)
    payload = {
        "container_id": entry["container_id"], "contract": contract.CONTRACT_VERSION,
        "status": "D1_EXPORTED", "branch": "bdf", "channels": list(HA_CHANNELS),
        "n_channels": len(HA_CHANNELS), "rate_hz": rate, "original_fs": original_fs,
        "stride": stride, "n_samples": int(data.shape[1]), "seconds": round(data.shape[1] / rate, 3),
        "candidate_acquisition_id": entry["candidate_acquisition_id"],
        "intervals": [{"interval_index": 0, "start": 0, "stop": int(data.shape[1]),
                       "original_start_sample": 0}],
        "skipped_intervals": [],
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
        qc_path = destination / f"{entry['container_id']}_qc.npz"
        np.savez_compressed(qc_path, channels_over_threshold=quality["channels_over_threshold"],
                            channels_flat=quality["channels_flat"],
                            block_median_peak_to_peak_uv=quality["block_median_peak_to_peak_uv"])
        qc_path.chmod(0o600)
    meta_path = destination / f"{entry['container_id']}.json"
    meta_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    meta_path.chmod(0o600)
    return payload
