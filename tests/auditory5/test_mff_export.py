"""Synthetic native export integration checks, Slurm execution only."""

import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd

from auditory5.adapters import mff_export


def fixture(fs=250, duration=125, flat_channels=0):
    n = round(duration * fs)
    channels = [f"native{i}" for i in range(10)]
    onsets = [1., 22., 45., 50., 59.9, 60.1, 61., 82., 105., 110.]
    annotations = [dict(annotation_index=i, event_literal="stad" if i % 2 == 0 else "devt",
                        onset_sample=round(onset * fs), onset_seconds_relative=onset,
                        sample_alignment_residual=0., segment_id="segment_0000",
                        in_stored_interval=True, annotation_origin="source_literal")
                   for i, onset in enumerate(onsets) if onset < duration]
    metadata = dict(sfreq=fs, physical_channel_names=channels,
                    excluded_reference_channel_names=["VREF"], full_axis_samples=n,
                    layout_hash="synthetic_native_geometry", annotations=annotations,
                    intervals=[dict(segment_id="segment_0000", start_sample=0, stop_sample=n,
                                    n_samples=n, interval_index=0, gap_before_samples=0)])
    record = dict(record_id="synthetic_mff", candidate_id="synthetic_candidate", split_group_id="synthetic_group",
                  original_fs=fs, n_samples=n, n_channels=11, paradigm_id="puretone",
                  code_map_hash="synthetic_literal_mapping", device_change_flag=False)
    spec = dict(mff_qc_version="auditory5_mff_qc_v1", mff_qc=dict(mff_export.MFF_QC_V1),
                mff_view="continuous", A_B_embargo_seconds=10.823,
                raw_flat_ptp_min_uv=.5, record_raw_flat_fraction_max=.2, scalp_ptp_max_uv=150.)

    def chunks(path, channel_names, chunk_seconds=60, interval_subset=None):
        for interval in metadata["intervals"]:
            if interval_subset is not None and interval["segment_id"] not in interval_subset:
                continue
            width = max(1, round(chunk_seconds * fs))
            for start in range(interval["start_sample"], interval["stop_sample"], width):
                stop = min(interval["stop_sample"], start + width)
                time = np.arange(start, stop) / fs
                x = np.array([(3 + i / 3) * np.sin(2 * np.pi * (3 + i / 5) * time + i / 3)
                              for i in range(len(channels))])
                x[:flat_channels] = 0
                yield dict(segment_id=interval["segment_id"], start_sample=start,
                           stop_sample=stop, data_uv=x)
    return record, metadata, spec, chunks


class MFFExportTests(unittest.TestCase):
    def export(self, base, record, metadata, spec, chunks, name="export"):
        source = base / "synthetic.mff"
        source.mkdir(exist_ok=True)
        (source / "signal1.bin").write_bytes(b"synthetic read-only signal bytes")
        (source / "info.xml").write_text("<synthetic/>")
        destination = base / name
        with patch.object(mff_export, "inspect_source", return_value=metadata), \
             patch.object(mff_export, "iter_raw_chunks", side_effect=chunks):
            summary = mff_export.export_record(record, {"signal_path": str(source)}, destination,
                                                "P1_CAUSAL20", spec)
        return destination, summary

    def test_native_shape_rejected_epochs_timing_and_reference_are_preserved(self):
        record, metadata, spec, chunks = fixture(flat_channels=1)
        with tempfile.TemporaryDirectory() as directory:
            destination, summary = self.export(Path(directory), record, metadata, spec, chunks)
            array = np.load(destination / "all.npy", mmap_mode="r")
            times = np.load(destination / "times_s.npy")
            ledger = pd.read_parquet(destination / "events.parquet")
            self.assertEqual(array.shape, (10, 10, 175))
            self.assertEqual(summary["preprocessing_id"], "P1_CAUSAL_NATIVE")
            self.assertEqual(summary["physical_channels"], 10)
            self.assertEqual(summary["persistent_raw_flat_channels"], 1)
            self.assertFalse(summary["within_record_filter_state_isolation"])
            self.assertTrue(ledger.iloc[0].stored_epoch_index >= 0)
            self.assertFalse(ledger.iloc[0].accepted)
            self.assertIn("startup_guard", ledger.iloc[0].reject_reason)
            self.assertTrue(ledger[ledger.onset_seconds_relative == 22.].iloc[0].accepted)
            self.assertTrue(all(ledger.raw_flat_channel_count == 1))
            self.assertTrue(np.all(times >= -.2 - 1e-12))
            self.assertTrue(np.all(times < .5))
            # Average reference is fixed across all ten physical channels,
            # including the flat channel; no QC-driven channel removal occurred.
            np.testing.assert_allclose(array.mean(axis=1), 0, atol=3e-7)
            self.assertTrue((destination / "source_manifest.json").is_file())
            self.assertEqual(list(destination.glob("mff_native_*")), [])

    def test_e0_block_resets_and_end_embargo_keep_a_rejected_ledger(self):
        record, metadata, spec, chunks = fixture()
        spec["mff_view"] = "E0_BLOCK_RESET_60S"
        with tempfile.TemporaryDirectory() as directory:
            destination, summary = self.export(Path(directory), record, metadata, spec, chunks)
            ledger = pd.read_parquet(destination / "events.parquet").set_index("onset_seconds_relative")
            self.assertTrue(summary["within_record_filter_state_isolation"])
            self.assertTrue(ledger.loc[22., "accepted"])
            self.assertFalse(ledger.loc[50., "accepted"])
            self.assertIn("E0_block_end_embargo", ledger.loc[50., "reject_reason"])
            self.assertEqual(ledger.loc[59.9, "stored_epoch_index"], -1)
            self.assertEqual(ledger.loc[60.1, "stored_epoch_index"], -1)
            self.assertFalse(ledger.loc[61., "accepted"])
            self.assertIn("startup_guard", ledger.loc[61., "reject_reason"])
            self.assertTrue(ledger.loc[82., "accepted"])
            self.assertNotEqual(ledger.loc[22., "filter_segment_id"], ledger.loc[82., "filter_segment_id"])
            self.assertEqual(ledger.loc[61., "previous_event_id"], "synthetic_mff:annotation_5")

    def test_block_reset_cannot_read_earlier_block_signal(self):
        record, metadata, spec, chunks = fixture()
        spec["mff_view"] = "E0_BLOCK_RESET_60S"

        def changed_chunks(*args, **kwargs):
            for chunk in chunks(*args, **kwargs):
                sample = np.arange(chunk["start_sample"], chunk["stop_sample"])
                before = sample < 60 * record["original_fs"]
                chunk["data_uv"][0, before] += 1000
                yield chunk

        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            first, _ = self.export(base, record, metadata, spec, chunks, name="first")
            second, _ = self.export(base, record, metadata, spec, changed_chunks, name="second")
            ledger = pd.read_parquet(first / "events.parquet")
            index = int(ledger[ledger.onset_seconds_relative == 82.].iloc[0].stored_epoch_index)
            np.testing.assert_array_equal(np.load(first / "all.npy")[index],
                                          np.load(second / "all.npy")[index])

    def test_more_than_ten_percent_persistent_flat_rejects_but_retains_arrays(self):
        record, metadata, spec, chunks = fixture(flat_channels=2)
        with tempfile.TemporaryDirectory() as directory:
            destination, summary = self.export(Path(directory), record, metadata, spec, chunks)
            self.assertEqual(summary["accepted"], 0)
            self.assertEqual(summary["stored_epochs"], 10)
            ledger = pd.read_parquet(destination / "events.parquet")
            self.assertTrue(ledger.reject_reason.str.contains("too_many_persistent_raw_flat_channels").all())

    def test_native_rate_is_retained_without_inventing_250hz_epochs(self):
        record, metadata, spec, chunks = fixture(fs=512, duration=30)
        spec["A_B_embargo_seconds"] = 11.0
        with tempfile.TemporaryDirectory() as directory:
            destination, summary = self.export(Path(directory), record, metadata, spec, chunks)
            self.assertEqual(summary["processed_fs"], 512)
            self.assertEqual(summary["epoch_n_samples"], 358)
            self.assertEqual(np.load(destination / "all.npy").shape, (2, 10, 358))
            times = np.load(destination / "times_s.npy")
            np.testing.assert_allclose(np.diff(times, axis=1), 1 / 512, atol=1e-15)

    def test_true_gaps_keep_distinct_filter_and_history_segments(self):
        record, metadata, spec, chunks = fixture(duration=125)
        metadata["intervals"] = [dict(segment_id="segment_0000", start_sample=0, stop_sample=15000,
                                      n_samples=15000, interval_index=0, gap_before_samples=0),
                                  dict(segment_id="segment_0001", start_sample=17500, stop_sample=31250,
                                       n_samples=13750, interval_index=1, gap_before_samples=2500)]
        for event in metadata["annotations"]:
            sample = event["onset_sample"]
            event["segment_id"] = "segment_0000" if sample < 15000 else "segment_0001" if sample >= 17500 else None
            event["in_stored_interval"] = event["segment_id"] is not None
        with tempfile.TemporaryDirectory() as directory:
            destination, summary = self.export(Path(directory), record, metadata, spec, chunks)
            ledger = pd.read_parquet(destination / "events.parquet").set_index("onset_seconds_relative")
            self.assertFalse(ledger.loc[82., "accepted"])
            self.assertIn("startup_guard", ledger.loc[82., "reject_reason"])
            self.assertTrue(pd.isna(ledger.loc[82., "previous_event_id"]))
            self.assertEqual(ledger.loc[61., "stored_epoch_index"], -1)

    def test_qc_spec_must_be_frozen_and_existing_output_is_not_overwritten(self):
        record, metadata, spec, chunks = fixture(duration=30)
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            changed = copy.deepcopy(spec)
            changed["mff_qc"]["epoch_over_ptp_fraction_max"] = .2
            with self.assertRaisesRegex(ValueError, "MFF_QC_NOT_FROZEN"):
                mff_export.export_record(record, {"signal_path": "unused"}, base / "bad", "P1_CAUSAL20", changed)
            self.export(base, record, metadata, spec, chunks)
            with self.assertRaises(FileExistsError):
                self.export(base, record, metadata, spec, chunks)


if __name__ == "__main__":
    unittest.main()
