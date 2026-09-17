"""Synthetic reader/geometry contracts; execute only through Slurm."""

import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import mne
import numpy as np
from mne._fiff.constants import FIFF

from auditory5.adapters import mff
from auditory5.preprocessing import HA_CHANNELS


class SyntheticMFF:
    """Mock calibrated lazy MNE surface, never allocates a full signal array."""

    def __init__(self):
        self.ch_names = ["E1", "E2", "VREF", "Cz", "E129", "stad"]
        self.info = mne.create_info(self.ch_names, 1000, ["eeg"] * 5 + ["stim"])
        positions = [(-.03, .04, .08), (.03, .04, .08), (0, 0, .1),
                     (0, -.03, .09), (0, -.05, .08)]
        for i, xyz in enumerate(positions):
            self.info["chs"][i]["loc"][:3] = xyz
            self.info["chs"][i]["loc"][3:6] = (0, 0, .1)
            self.info["chs"][i]["coord_frame"] = FIFF.FIFFV_COORD_HEAD
        self._cals = np.array([2e-6, 3e-6, 1e-6, 4e-6, 5e-6, 1.0])
        self._raw_extras = [dict(
            first_samps=np.array([0, 20]), last_samps=np.array([10, 32]),
            samples_block=np.array([10, 12]), event_codes=["stad", "devt", "sync", "TREV"],
        )]
        self.annotations = SimpleNamespace(
            onset=np.array([.002, .0095, .011, .021, .031]),
            duration=np.array([0, .010, 0, 0, 0]),
            description=np.array(["sync", "BAD_ACQ_SKIP", "TREV", "stad", "devt"]),
        )
        self.preload = False
        self.first_samp = 0
        self.n_times = 32
        self.closed = False
        self.requests = []

    def get_data(self, *, picks, start, stop):
        if not any(start >= lo and stop <= hi for lo, hi in ((0, 10), (20, 32))):
            raise AssertionError("test reader forbids reads spanning a real storage gap")
        self.requests.append((tuple(picks), start, stop))
        stored_units = np.asarray(picks)[:, None] + np.arange(start, stop)[None, :] / 100
        return stored_units * self._cals[np.asarray(picks), None]

    def close(self):
        self.closed = True


class MFFReaderTests(unittest.TestCase):
    def test_open_keeps_all_literals_and_never_preloads(self):
        with patch.object(mne.io, "read_raw_egi", return_value="reader") as mocked:
            self.assertEqual(mff._open_raw("synthetic.mff"), "reader")
        mocked.assert_called_once_with("synthetic.mff", preload=False, exclude=[],
                                       events_as_annotations=True, verbose="ERROR")

    def test_inspection_preserves_intervals_literals_and_privacy(self):
        raw = SyntheticMFF()
        with patch.object(mff, "_open_raw", return_value=raw):
            metadata = mff.inspect_source("synthetic-private-locator.mff")
        self.assertTrue(raw.closed)
        self.assertEqual(raw.requests, [])
        self.assertEqual(metadata["stored_samples"], 22)
        self.assertEqual(metadata["full_axis_samples"], 32)
        self.assertEqual(metadata["interval_stop_convention"], "exclusive")
        self.assertEqual([(row["start_sample"], row["stop_sample"]) for row in metadata["intervals"]],
                         [(0, 10), (20, 32)])
        self.assertEqual(metadata["intervals"][1]["gap_before_samples"], 10)
        self.assertEqual(metadata["physical_channel_names"], ["E1", "E2", "Cz", "E129"])
        self.assertEqual(metadata["excluded_reference_channel_names"], ["VREF"])
        annotations = metadata["annotations"]
        self.assertEqual([row["event_literal"] for row in annotations],
                         ["sync", "BAD_ACQ_SKIP", "TREV", "stad", "devt"])
        self.assertEqual(annotations[1]["onset_sample_fractional"], 9.5)
        self.assertEqual(annotations[1]["sample_alignment_residual"], -.5)
        self.assertFalse(annotations[2]["in_stored_interval"])
        self.assertIsNone(annotations[2]["segment_id"])
        self.assertEqual(annotations[3]["onset_sample"], 21)
        self.assertEqual(annotations[3]["segment_id"], "segment_0001")
        self.assertNotIn("synthetic-private-locator", json.dumps(metadata))
        self.assertFalse(any("task" in key or "diagnosis" in key for key in metadata))

    def test_streams_only_stored_samples_with_single_gain_and_unit_conversion(self):
        raw = SyntheticMFF()
        with patch.object(mff, "_open_raw", return_value=raw):
            chunks = list(mff.iter_raw_chunks("synthetic.mff", ["E2", "E1"], chunk_seconds=.006))
        self.assertTrue(raw.closed)
        self.assertEqual([(row["start_sample"], row["stop_sample"]) for row in chunks],
                         [(0, 6), (6, 10), (20, 26), (26, 32)])
        self.assertEqual(sum(row["data_uv"].shape[1] for row in chunks), 22)
        self.assertEqual([row["segment_id"] for row in chunks],
                         ["segment_0000", "segment_0000", "segment_0001", "segment_0001"])
        self.assertTrue(all(stop - start <= 6 for _, start, stop in raw.requests))
        for chunk in chunks:
            samples = np.arange(chunk["start_sample"], chunk["stop_sample"])
            expected = np.vstack([(1 + samples / 100) * 3, (samples / 100) * 2])
            np.testing.assert_allclose(chunk["data_uv"], expected, rtol=0, atol=1e-14)
            self.assertEqual(chunk["channel_names"], ["E2", "E1"])

    def test_interval_subset_keeps_original_clock_and_order(self):
        raw = SyntheticMFF()
        with patch.object(mff, "_open_raw", return_value=raw):
            chunks = list(mff.iter_raw_chunks("synthetic.mff", ["E1"],
                                             interval_subset=["segment_0001"]))
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0]["start_sample"], 20)
        self.assertEqual(chunks[0]["stop_sample"], 32)
        self.assertEqual(chunks[0]["interval_start_sample"], 20)

    def test_reference_channel_requests_rejected(self):
        raw = SyntheticMFF()
        with patch.object(mff, "_open_raw", return_value=raw):
            with self.assertRaises(ValueError):
                list(mff.iter_raw_chunks("synthetic.mff", ["E1", "VREF"]))
        self.assertTrue(raw.closed)
        self.assertEqual(raw.requests, [])

    def test_declared_reference_coordinate_excluded_even_if_name_unrecognized(self):
        raw = SyntheticMFF()
        mne.rename_channels(raw.info, {"VREF": "OTHER_REFERENCE"})
        raw.ch_names = list(raw.info["ch_names"])
        # _physical_channels uses index-based MNE channel kinds and caller names.
        with patch.object(mff, "_open_raw", return_value=raw):
            metadata = mff.inspect_source("synthetic.mff")
        self.assertIn("OTHER_REFERENCE", metadata["excluded_reference_channel_names"])
        self.assertNotIn("OTHER_REFERENCE", metadata["physical_channel_names"])

    def test_generator_close_releases_reader_without_reading_remaining_signal(self):
        raw = SyntheticMFF()
        with patch.object(mff, "_open_raw", return_value=raw):
            stream = mff.iter_raw_chunks("synthetic.mff", ["E1"], chunk_seconds=.004)
            next(stream)
            self.assertFalse(raw.closed)
            stream.close()
        self.assertTrue(raw.closed)
        self.assertEqual(len(raw.requests), 1)

    def test_invalid_stored_sample_accounting_fails_closed(self):
        raw = SyntheticMFF()
        raw._raw_extras[0]["samples_block"] = np.array([10, 13])
        with patch.object(mff, "_open_raw", return_value=raw):
            with self.assertRaises(ValueError):
                mff.inspect_source("synthetic.mff")
        self.assertTrue(raw.closed)

    def test_adjacent_stored_intervals_remain_distinct_segments(self):
        raw = SyntheticMFF()
        raw._raw_extras[0]["first_samps"] = np.array([0, 10])
        raw._raw_extras[0]["last_samps"] = np.array([10, 32])
        raw._raw_extras[0]["samples_block"] = np.array([10, 22])
        with patch.object(mff, "_open_raw", return_value=raw):
            metadata = mff.inspect_source("synthetic.mff")
        self.assertEqual(len(metadata["intervals"]), 2)
        self.assertEqual(metadata["intervals"][1]["gap_before_samples"], 0)

    def test_missing_head_coordinates_preserved_as_unknown(self):
        raw = SyntheticMFF()
        raw.info["chs"][0]["loc"][:3] = np.nan
        with patch.object(mff, "_open_raw", return_value=raw):
            metadata = mff.inspect_source("synthetic.mff")
        self.assertIsNone(metadata["geometry"][0]["xyz_m"])
        self.assertFalse(metadata["geometry"][0]["usable_for_mapping"])
        json.dumps(metadata, allow_nan=False)


def geometry_metadata(positions):
    names = [f"native_{i:02d}" for i in range(len(positions))]
    return dict(physical_channel_names=names, layout_hash="synthetic_layout",
                geometry=[dict(channel_name=name, xyz_m=position.tolist(),
                               coord_frame="head", usable_for_mapping=True)
                          for name, position in zip(names, positions)])


class MFFGeometryTests(unittest.TestCase):
    def test_standard_target_is_head_frame_in_metres(self):
        xyz = mff.standard_1020_head_positions()
        self.assertEqual(xyz.shape, (20, 3))
        self.assertTrue(np.isfinite(xyz).all())
        self.assertLess(np.linalg.norm(xyz, axis=1).max(), .25)
        self.assertLess(xyz[HA_CHANNELS.index("Fp1"), 0], 0)
        self.assertGreater(xyz[HA_CHANNELS.index("Fp2"), 0], 0)
        self.assertGreater(xyz[HA_CHANNELS.index("Fz"), 1], xyz[HA_CHANNELS.index("Oz"), 1])

    def test_exact_map_is_unique_and_in_target_order(self):
        xyz = mff.standard_1020_head_positions()
        metadata = geometry_metadata(xyz)
        metadata["geometry"] = metadata["geometry"][::-1]
        result = mff.map_to_standard_1020(metadata)
        self.assertTrue(result["eligible"])
        self.assertEqual([row["target_channel"] for row in result["mapping"]], list(HA_CHANNELS))
        self.assertEqual([row["native_channel"] for row in result["mapping"]],
                         [f"native_{i:02d}" for i in range(20)])
        self.assertEqual(result["maximum_assigned_distance_m"], 0)

    def test_hungarian_assignment_never_duplicates_nearest_sensor(self):
        xyz = mff.standard_1020_head_positions()
        midpoint = (xyz[0] + xyz[1]) / 2
        xyz[0] = midpoint
        xyz[1] = midpoint + np.array([0, 0, .02])
        result = mff.map_to_standard_1020(geometry_metadata(xyz))
        self.assertTrue(result["eligible"])
        self.assertEqual(len({row["native_channel"] for row in result["mapping"]}), 20)
        self.assertTrue(all(row["distance_m"] <= .04 for row in result["mapping"]))

    def test_distance_and_geometry_failures_are_explicit_holds(self):
        xyz = mff.standard_1020_head_positions()
        far = mff.map_to_standard_1020(geometry_metadata(xyz + 1))
        self.assertFalse(far["eligible"])
        self.assertEqual(far["status"], "hold_distance_exceeds_40mm")
        missing = mff.map_to_standard_1020(geometry_metadata(xyz[:-1]))
        self.assertFalse(missing["eligible"])
        self.assertEqual(missing["status"], "hold_insufficient_physical_geometry")
        metadata = geometry_metadata(xyz)
        metadata["geometry"][0]["coord_frame"] = "unverified"
        self.assertFalse(mff.map_to_standard_1020(metadata)["eligible"])


if __name__ == "__main__":
    unittest.main()
