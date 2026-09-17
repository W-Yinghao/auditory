"""Slurm-only two-source MFF adapter smoke; detailed evidence stays private."""

import argparse
from collections import Counter
import json
import os
from pathlib import Path
import sys
import traceback

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd

from auditory5.adapters.mff import inspect_source, iter_raw_chunks, map_to_standard_1020
from auditory5.provenance import ROOT, require_slurm, write_json


def main():
    require_slurm()
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default="private/auditory5_v1/data/manifest_001")
    parser.add_argument("--output", default="private/auditory5_v1/inputs/mff_probe_001")
    args = parser.parse_args()
    source = (ROOT / args.manifest).resolve()
    destination = (ROOT / args.output).resolve()
    for directory in (source, destination):
        if not directory.is_relative_to(ROOT / "private"):
            raise ValueError("MFF probe inputs and evidence output must remain private")
    destination.mkdir(parents=True, mode=0o700, exist_ok=False)
    pairs = pd.read_parquet(source / "E_existing_pairs.parquet")
    records = pd.read_parquet(source / "records.parquet").set_index("record_id")
    locators = pd.read_parquet(source / "raw_locators.parquet").set_index("record_id")
    required = {"container_a", "container_b", "contrast"}
    if not required <= set(pairs):
        raise ValueError("existing-pair schema changed")
    ids = set(pairs["container_a"]) | set(pairs["container_b"])
    selected = []
    for task in ("puretone", "bapa"):
        candidates = [rid for rid in ids if rid in records.index and
                      records.loc[rid, "paradigm_id"] == task]
        if not candidates:
            raise ValueError("existing E pairs do not contain both required tasks")
        chosen = min(candidates, key=lambda rid: (str(locators.loc[rid, "record_time"]), rid))
        selected.append((task, chosen))
    evidence, errors = [], []
    for task, record_id in selected:
        try:
            path = locators.loc[record_id, "signal_path"]
            metadata = inspect_source(path)
            stream = iter_raw_chunks(path, metadata["physical_channel_names"], chunk_seconds=2,
                                     interval_subset=[0])
            try:
                first = next(stream)
            finally:
                stream.close()
            values = first["data_uv"]
            if not np.isfinite(values).all():
                raise ValueError("first bounded native physical EEG chunk is nonfinite")
            row = dict(task=task, record_id=record_id, metadata=metadata,
                       common_map_diagnostic=map_to_standard_1020(metadata),
                       first_chunk_start_sample=first["start_sample"],
                       first_chunk_stop_sample=first["stop_sample"],
                       first_chunk_shape=list(values.shape),
                       first_chunk_channel_ptp_uv=np.ptp(values, axis=1).tolist(),
                       first_chunk_finite=True)
            evidence.append(row)
        except Exception as exc:
            errors.append(dict(record_id=record_id, task=task,
                               error=repr(exc), traceback=traceback.format_exc()))
    write_json(destination / "reader_evidence.json", evidence)
    write_json(destination / "errors.json", errors)
    counts = Counter()
    for row in evidence:
        counts.update(annotation["event_literal"] for annotation in row["metadata"]["annotations"])
    aggregate = dict(status="PASS" if len(evidence) == 2 and not errors else "IMPLEMENTATION_FAIL",
                     inspected_sources=len(evidence), errors=len(errors),
                     physical_channel_counts=[len(row["metadata"]["physical_channel_names"]) for row in evidence],
                     original_sampling_hz=[row["metadata"]["sfreq"] for row in evidence],
                     stored_interval_counts=[len(row["metadata"]["intervals"]) for row in evidence],
                     annotation_literal_counts=dict(counts),
                     output_unit="uV", full_record_signal_loaded=False,
                     scientific_model_fitted=False, job_id=os.environ["SLURM_JOB_ID"])
    write_json(destination / "summary.json", aggregate)
    print(json.dumps(aggregate), flush=True)
    if errors:
        raise RuntimeError("MFF adapter probe failed; inspect restricted evidence")


if __name__ == "__main__":
    main()
