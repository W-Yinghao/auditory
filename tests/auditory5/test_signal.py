"""Synthetic signal/history checks. Run these only in a Slurm allocation."""

import copy
import unittest

import numpy as np
from scipy.signal import sosfilt, sosfreqz

from auditory5.events import build_event_history
from auditory5.preprocessing import (
    HA_CHANNELS,
    LEFT_CHANNELS,
    RIGHT_CHANNELS,
    CausalPreprocessor,
    concatenate_chunks,
    effective_impulse_support,
    extract_epoch,
    fixed_sos,
)


def event_rows(codes, *, complete=True):
    rows = [dict(record_id="synthetic", segment_id="s0", trial_id=f"t{i}",
                 onset_sample=i * 700, event_literal=code, event_kind="target",
                 accepted=True)
            for i, code in enumerate(codes)]
    if rows and complete:
        rows[0]["sequence_start_complete"] = True
    return rows


class EventHistoryTests(unittest.TestCase):
    def test_history_before_qc(self):
        raw = event_rows([1, 1, 1, 1, 2, 1, 1])
        reference = build_event_history(raw, 1000)
        raw[1]["accepted"] = False
        raw[2]["accepted"] = False
        raw[2]["reject_reason"] = "synthetic_bad_eeg"
        rejected = build_event_history(raw, 1000)
        keys = ("previous_event_id", "previous_code", "previous_gap_s",
                "previous_run_length", "current_run_length", "history_target")
        self.assertEqual([{k: r[k] for k in keys} for r in reference],
                         [{k: r[k] for k in keys} for r in rejected])
        self.assertEqual([r["previous_run_length"] for r in rejected],
                         [None, 1, 2, 3, 4, 1, 1])
        self.assertEqual([r["history_target"] for r in rejected],
                         [None, 0, None, 1, 1, 0, 0])
        self.assertEqual(len(rejected), len(raw))
        self.assertFalse(rejected[1]["accepted"])

    def test_history_gap_resets_and_does_not_invent_completeness(self):
        rows = event_rows([1, 1, 1, 1, 1, 2, 2])
        rows[3]["storage_gap_before"] = True
        output = build_event_history(rows, 1000)
        self.assertIsNone(output[3]["previous_event_id"])
        self.assertEqual(output[3]["history_reset_reason"], "storage_gap")
        self.assertIsNone(output[4]["previous_run_length"])
        self.assertIsNone(output[5]["history_target"])
        self.assertEqual(output[6]["previous_run_length"], 1)

    def test_segment_and_task_restart(self):
        rows = event_rows([1, 1, 1, 1, 1, 1])
        rows[2]["task_restart_before"] = True
        rows[4]["segment_id"] = "s1"
        rows[5]["segment_id"] = "s1"
        output = build_event_history(rows, 1000)
        self.assertIsNone(output[2]["history_target"])
        self.assertEqual(output[3]["history_target"], 0)
        self.assertIsNone(output[4]["previous_event_id"])
        self.assertIsNone(output[5]["history_target"])

    def test_non_sound_log_preserves_history_unknown_sound_interrupts(self):
        rows = event_rows([1, 99, 1, 98, 1, 1])
        rows[1]["event_kind"] = "non_sound"
        rows[3]["event_kind"] = "unknown_sound"
        output = build_event_history(rows, 1000)
        self.assertEqual(output[2]["previous_event_id"], "t0")
        self.assertAlmostEqual(output[2]["previous_gap_s"], 1.4)
        self.assertEqual(output[2]["previous_run_length"], 1)
        self.assertIsNone(output[4]["previous_event_id"])
        self.assertEqual(output[4]["history_reset_reason"], "unknown_sound")
        self.assertIsNone(output[5]["previous_run_length"])

    def test_gap_seconds_use_original_hz(self):
        rows = event_rows([1, 1])
        self.assertAlmostEqual(build_event_history(rows, 1000)[1]["previous_gap_s"], 0.7)
        self.assertAlmostEqual(build_event_history(rows, 500)[1]["previous_gap_s"], 1.4)

    def test_long_interval_alone_does_not_imply_storage_gap(self):
        rows = event_rows([1, 1])
        rows[1]["onset_sample"] = 100_000
        output = build_event_history(rows, 1000)
        self.assertEqual(output[1]["previous_run_length"], 1)
        self.assertEqual(output[1]["previous_gap_s"], 100.0)

    def test_history_does_not_use_future(self):
        rows = event_rows([1, 1, 1, 2, 1])
        mutated = copy.deepcopy(rows)
        mutated[-1]["event_literal"] = 2
        self.assertEqual(build_event_history(rows, 1000)[:-1],
                         build_event_history(mutated, 1000)[:-1])

    def test_mapping_never_guesses_unmapped_roles(self):
        rows = event_rows([1, 99])
        del rows[0]["event_kind"]
        del rows[1]["event_kind"]
        with self.assertRaises(ValueError):
            build_event_history(rows, 1000, target_codes=[1, 2])
        rows[1]["event_kind"] = "non_sound"
        self.assertEqual(build_event_history(rows, 1000, target_codes=[1, 2])[0]["event_kind"],
                         "target")

    def test_ambiguous_duplicate_sounds_fail(self):
        rows = event_rows([1, 2])
        rows[1]["onset_sample"] = 0
        with self.assertRaises(ValueError):
            build_event_history(rows, 1000)


class CausalSignalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.support = effective_impulse_support(1000)

    def processor(self, **kwargs):
        return CausalPreprocessor(1000, HA_CHANNELS, support=self.support, **kwargs)

    def test_future_perturbation(self):
        rng = np.random.default_rng(12)
        raw = rng.normal(size=(20, 5000))
        changed = raw.copy()
        changed[:, 2001:] += rng.normal(size=(20, 2999)) * 1000
        before = self.processor().process(raw, start_sample=0)
        after = self.processor().process(changed, start_sample=0)
        past = before.source_samples <= 2000
        np.testing.assert_array_equal(before.data["all"][:, past], after.data["all"][:, past])
        self.assertGreater(np.max(np.abs(before.data["all"][:, ~past] -
                                        after.data["all"][:, ~past])), 1.0)

    def test_independent_spatial_branch_both_directions(self):
        rng = np.random.default_rng(22)
        raw = rng.normal(size=(20, 5000))
        reference = self.processor(bank="P2_SPATIAL_SPLIT").process(raw, start_sample=0)
        for changed_names, stable_branch in ((RIGHT_CHANNELS, "left"), (LEFT_CHANNELS, "right")):
            changed = raw.copy()
            indices = [HA_CHANNELS.index(name) for name in changed_names]
            changed[indices] += rng.normal(size=(8, 5000)) * 10_000
            output = self.processor(bank="P2_SPATIAL_SPLIT").process(changed, start_sample=0)
            np.testing.assert_array_equal(output.data[stable_branch], reference.data[stable_branch])
            # The forbidden global-reference implementation fails this same perturbation.
            stable_names = LEFT_CHANNELS if stable_branch == "left" else RIGHT_CHANNELS
            stable = [HA_CHANNELS.index(name) for name in stable_names]
            bad_original = raw[stable] - raw.mean(axis=0)
            bad_changed = changed[stable] - changed.mean(axis=0)
            self.assertGreater(np.max(np.abs(bad_original - bad_changed)), 1.0)

    def test_chunk_state_and_original_grid_equal_full_interval(self):
        raw = np.random.default_rng(2).normal(size=(20, 50_003))
        full = self.processor(segment_start_sample=7).process(raw, start_sample=7)
        streaming = self.processor(segment_start_sample=7)
        boundaries = [0, 1, 514, 3001, 20_003, 50_003]
        chunks = [streaming.process(raw[:, left:right], start_sample=7 + left)
                  for left, right in zip(boundaries[:-1], boundaries[1:])]
        joined = concatenate_chunks(chunks)
        np.testing.assert_array_equal(joined.source_samples, full.source_samples)
        np.testing.assert_array_equal(joined.guard_valid, full.guard_valid)
        np.testing.assert_allclose(joined.data["all"], full.data["all"], rtol=0, atol=1e-12)
        self.assertTrue(np.all(joined.source_samples % 4 == 0))
        self.assertEqual(joined.source_samples[0], 8)

    def test_gap_requires_reset_and_fresh_state(self):
        rng = np.random.default_rng(4)
        processor = self.processor()
        processor.process(rng.normal(size=(20, 3000)), start_sample=0)
        raw = rng.normal(size=(20, 5003))
        with self.assertRaises(ValueError):
            processor.process(raw, start_sample=4001)
        processor.reset_segment(4001)
        output = processor.process(raw, start_sample=4001)
        fresh = self.processor(segment_start_sample=4001).process(raw, start_sample=4001)
        np.testing.assert_array_equal(output.data["all"], fresh.data["all"])
        self.assertEqual(output.source_samples[0], 4004)
        self.assertFalse(output.guard_valid.any())

    def test_cannot_concatenate_independently_reset_adjacent_intervals(self):
        raw = np.zeros((20, 1000))
        first = self.processor().process(raw, start_sample=0)
        second = self.processor(segment_start_sample=1000).process(raw, start_sample=1000)
        with self.assertRaises(ValueError):
            concatenate_chunks([first, second])

    def test_support_is_absolute_tail_not_energy_and_guard_is_separate(self):
        support = self.support
        self.assertEqual(support.tolerance, 1e-6)
        self.assertEqual(support.support_seconds, support.support_samples / 1000)
        self.assertEqual(support.guard_samples, max(20_000, support.support_samples))
        # Independently evaluate twice the reported measurement horizon.
        impulse = np.zeros(2 * support.impulse_length_samples)
        impulse[0] = 1.0
        absolute = np.abs(sosfilt(fixed_sos(1000), impulse))
        ratio = absolute[support.support_samples:].sum() / absolute.sum()
        before = absolute[support.support_samples - 1:].sum() / absolute.sum()
        self.assertLess(ratio, 1e-6)
        self.assertGreaterEqual(before, 1e-6)
        self.assertLess(support.terminal_half_fraction, 1e-9)
        self.assertAlmostEqual(ratio, support.absolute_tail_fraction, places=12)

    def test_filter_frequency_and_antialias_attenuation(self):
        # Fixed engineering gates, chosen before processing any real EEG:
        # 5 Hz gain > .99; both cutoffs -3 dB; 125 Hz stopband below -80 dB.
        frequencies = np.array([0.05, 0.5, 5.0, 30.0, 125.0, 180.0])
        _, h = sosfreqz(fixed_sos(1000), worN=frequencies, fs=1000)
        gain = np.abs(h)
        self.assertLess(gain[0], 1.01e-4)
        self.assertAlmostEqual(gain[1], 2 ** -0.5, places=6)
        self.assertGreater(gain[2], 0.99)
        self.assertAlmostEqual(gain[3], 2 ** -0.5, places=6)
        self.assertLess(gain[4], 1e-4)
        self.assertLess(gain[5], 1e-4)

    def test_alias_tone_suppressed_after_streamed_decimation(self):
        # 180 Hz aliases to 70 Hz on a 250 Hz grid without the causal LP8.
        time = np.arange(50_000) / 1000
        raw = np.zeros((20, len(time)))
        raw[0] = np.sin(2 * np.pi * 180 * time)
        processor = self.processor()
        output = concatenate_chunks([
            processor.process(raw[:, :30003], start_sample=0),
            processor.process(raw[:, 30003:], start_sample=30003),
        ])
        steady = output.data["all"][0, output.source_samples >= 30_000]
        reference_rms = 0.95 / np.sqrt(2)  # average reference for one of 20 channels
        self.assertLess(np.sqrt(np.mean(steady ** 2)) / reference_rms, 1e-4)

    def test_native_rate_fallback_no_unverified_resampling(self):
        processor = CausalPreprocessor(512, HA_CHANNELS)
        output = processor.process(np.zeros((20, 1200)), start_sample=0)
        self.assertEqual(output.processed_fs, 512)
        self.assertEqual(output.decimation_factor, 1)
        np.testing.assert_array_equal(output.source_samples, np.arange(1200))

    def test_epoch_retains_original_phase_half_open_window_and_no_baseline(self):
        time = np.arange(40_000) / 1000
        raw = np.zeros((20, len(time)))
        raw[0] = np.sin(2 * np.pi * 1.1 * time)
        output = self.processor().process(raw, start_sample=0)
        epoch = extract_epoch(output, 30_001)
        self.assertTrue(epoch.eligible)
        self.assertEqual(epoch.source_samples[0], 29_804)
        self.assertEqual(epoch.source_samples[-1], 30_500)
        self.assertEqual(epoch.data["all"].shape[-1], 175)
        self.assertAlmostEqual(epoch.times_s[0], -0.197)
        self.assertAlmostEqual(epoch.times_s[-1], 0.499)
        self.assertFalse(np.any(epoch.times_s == 0))
        np.testing.assert_array_equal(epoch.data["all"],
                                      output.data["all"][:, epoch.source_samples // 4])
        self.assertGreater(abs(epoch.data["all"][0, epoch.times_s < 0].mean()), 1e-3)

    def test_rejected_guard_epochs_are_retained(self):
        output = self.processor().process(np.zeros((20, 21_000)), start_sample=0)
        epoch = extract_epoch(output, 20_000)
        self.assertFalse(epoch.eligible)
        self.assertIn("startup_guard", epoch.reject_reasons)
        self.assertEqual(epoch.data["all"].shape[-1], 175)
        valid = extract_epoch(output, 20_250)
        self.assertTrue(valid.eligible)
        boundary = extract_epoch(output, 20_900)
        self.assertFalse(boundary.eligible)
        self.assertIn("incomplete_epoch", boundary.reject_reasons)


if __name__ == "__main__":
    unittest.main()
