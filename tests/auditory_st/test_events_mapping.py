"""Original-sample -> D1 export mapping, epoch support and history integration."""
from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest

from auditory_st import events as ev
from auditory_st import features as ft
from auditory_st.runtime import load_config

CONFIG = load_config()


def _meta(stride=4, rate=250.0):
    # interval 0 skipped (short); interval 1 exported from original sample 4086; interval 2 later
    return {"rate_hz": rate, "original_fs": rate * stride, "stride": stride, "n_channels": 3,
            "n_samples": 1000 + 500,
            "intervals": [{"interval_index": 1, "start": 0, "stop": 1000, "original_start_sample": 4086},
                          {"interval_index": 2, "start": 1000, "stop": 1500, "original_start_sample": 12000}],
            "skipped_intervals": [{"interval_index": 0, "seconds": 1.7}]}


def test_mapping_formula_and_residual():
    table = ev.d1_interval_table(_meta())
    assert table[0]["original_stop_sample_exclusive"] == 4086 + 1000 * 4
    e, i, r = ev.map_original_to_exported(4086, table)
    assert (e, i, r) == (0, 1, 0.0)
    e, i, r = ev.map_original_to_exported(4086 + 4 * 10 + 3, table)
    assert (e, i, r) == (10, 1, 3.0)
    e, i, r = ev.map_original_to_exported(12000 + 4 * 7, table)
    assert (e, i, r) == (1007, 2, 0.0)
    # inside the skipped interval or in a gap -> unmapped
    assert ev.map_original_to_exported(100, table)[0] == -1
    assert ev.map_original_to_exported(4086 + 4000, table)[0] == -1        # exactly at exclusive stop
    assert ev.map_original_to_exported(11999, table)[0] == -1


def test_epoch_support_guards():
    table = ev.d1_interval_table(_meta())
    pre, post, guard = 50, 200, 100
    ok, reason = ev.epoch_support(600, 1, table, pre_samples=pre, post_samples=post, guard_samples=guard)
    assert ok and reason == ""
    ok, reason = ev.epoch_support(140, 1, table, pre_samples=pre, post_samples=post, guard_samples=guard)
    assert not ok and reason == "epoch_before_interval_guard"
    ok, reason = ev.epoch_support(750, 1, table, pre_samples=pre, post_samples=post, guard_samples=guard)
    assert not ok and reason == "epoch_after_interval_guard"
    ok, reason = ev.epoch_support(-1, -1, table, pre_samples=pre, post_samples=post, guard_samples=guard)
    assert not ok and reason == "onset_not_in_exported_interval"


def test_history_and_finish_rows_on_a_toy_chain():
    meta = _meta()
    fs = meta["original_fs"]
    rid = "T0001"
    codes = {"stad": 0, "devt": 1}
    literals = ["stad", "stad", "devt", "stad", "stad", "stad", "devt"]
    rows = []
    for k, lit in enumerate(literals):
        rows.append({"record_id": rid, "segment_id": "segment_0001", "trial_id": f"{rid}:a{k:05d}",
                     "onset_sample": 4086 + 3000 + k * 900, "event_literal": lit, "event_kind": "target",
                     "in_stored_interval": True, "source_alignment_residual": 0.0})
    out = ev._finish_rows(rows, fs, codes, meta, CONFIG)
    assert len(out) == 7
    assert out[0]["history_status"] == "no_previous_sound"
    assert out[2]["previous_code"] == "stad" and math.isclose(out[2]["previous_gap_s"], 0.9)
    assert out[2]["stimulus_local_id"] == 1
    # run lengths: first run has unknown true length at a chain start -> None until code change
    assert out[1]["previous_run_length"] is None
    assert out[3]["previous_run_length"] == 1        # previous was the single devt
    assert out[6]["previous_run_length"] == 3 and out[6]["history_target"] == 1
    exported = [r["exported_index"] for r in out]
    assert exported[0] == 750 and exported[1] == 975
    # events 2..5 fall in the original gap between interval 1 (ends at 8086) and interval 2 (starts 12000)
    assert all(e == -1 for e in exported[2:6])
    # event 6 (original 12486) lands in interval 2: 1000 + 486 // 4
    assert exported[6] == 1121 and out[6]["exported_interval_index"] == 2
    # 750 + 200 post samples > 1000 - guard(500): after-guard failure; unmapped ones carry their own reason
    assert out[0]["epoch_supported"] is False and out[0]["epoch_support_reason"] == "epoch_after_interval_guard"
    assert out[3]["epoch_support_reason"] == "onset_not_in_exported_interval"
    assert all(r["block_id"] == int(r["onset_seconds"] // 60) for r in out)


def test_window_grid_and_means():
    rate = 250.0
    starts, length = ft.window_starts(rate, 0.2, 0.8, 0.08, 0.02)
    assert length == 20 and starts[0] == 0 and starts[1] == 5 and len(starts) == 47
    centres = ft.window_centres_s(starts, length, rate, 0.2)
    assert math.isclose(centres[0], -0.16) and math.isclose(centres[-1], 0.76)
    epochs = np.zeros((2, 3, 250), dtype=np.float32)
    epochs[0, 1, 0:20] = 2.0            # window 0 mean on channel 1 = 2
    epochs[1, 2, 5:25] = 1.0            # window 1 mean on channel 2 = 1
    means = ft.window_means(epochs, starts, length)
    assert means.shape == (2, 47, 3)
    assert math.isclose(means[0, 0, 1], 2.0) and math.isclose(means[0, 1, 1], 1.5)
    assert math.isclose(means[1, 1, 2], 1.0) and math.isclose(means[1, 0, 2], 0.75)


def test_epoch_qc_rules():
    good = np.random.default_rng(0).standard_normal((10, 100)) * 5
    ok, reason, over, flat = ft.epoch_qc(good, ptp_max=150, ptp_fraction_max=0.1, flat_ptp=0.5, flat_fraction_max=0.1)
    assert ok and reason == "" and over == 0.0 and flat == 0.0
    bad = good.copy(); bad[:2] *= 100
    ok, reason, over, flat = ft.epoch_qc(bad, ptp_max=150, ptp_fraction_max=0.1, flat_ptp=0.5, flat_fraction_max=0.1)
    assert not ok and reason == "too_many_channels_over_ptp" and math.isclose(over, 0.2)
    flat_bad = good.copy(); flat_bad[:2] = 0.0
    ok, reason, *_ = ft.epoch_qc(flat_bad, ptp_max=150, ptp_fraction_max=0.1, flat_ptp=0.5, flat_fraction_max=0.1)
    assert not ok and reason == "too_many_flat_channels"


def test_extract_record_cuts_at_mapped_index(tmp_path):
    meta = _meta()
    rate = meta["rate_hz"]
    # alternating +-1 uV so no channel is flat, every 20-sample window mean is exactly 0 and |x| median is 1
    data = np.tile(((np.arange(meta["n_samples"]) % 2) * 2 - 1).astype(np.float32), (3, 1))
    data[0, 600] += 10.0                                  # an impulse exactly at the onset of trial A
    path = tmp_path / "T.npy"
    np.save(path, data)
    frame = pd.DataFrame([
        {"event_kind": "target", "exported_index": 600, "exported_interval_index": 1, "trial_id": "a", "stimulus_local_id": 0,
         "onset_seconds": 2.4, "block_id": 0, "previous_code": None, "previous_gap_s": np.nan, "previous_run_length": None,
         "history_status": "no_previous_sound"},
        {"event_kind": "target", "exported_index": 1200, "exported_interval_index": 2, "trial_id": "b", "stimulus_local_id": 1,
         "onset_seconds": 5.6, "block_id": 0, "previous_code": "stad", "previous_gap_s": 3.2, "previous_run_length": 1,
         "history_status": "complete"},
        {"event_kind": "target", "exported_index": 1490, "exported_interval_index": 2, "trial_id": "c", "stimulus_local_id": 0,
         "onset_seconds": 5.96, "block_id": 0, "previous_code": "devt", "previous_gap_s": 0.36, "previous_run_length": 1,
         "history_status": "complete"},
        {"event_kind": "non_sound", "exported_index": 700, "exported_interval_index": 1, "trial_id": "n", "stimulus_local_id": -1,
         "onset_seconds": 2.8, "block_id": 0, "previous_code": None, "previous_gap_s": np.nan, "previous_run_length": None,
         "history_status": "not_target"},
    ])
    cfg = dict(CONFIG)
    cfg["epoch"] = dict(CONFIG["epoch"], interval_edge_guard_seconds=0.4)
    out = ft.extract_record(path, meta, frame, cfg, post_seconds=0.8, codes={"stad": 0, "devt": 1})
    assert out["previous_code"].tolist() == [-1, 0]      # None -> -1, 'stad' -> 0 (literal map, not int cast)
    # trial b fits (1150 >= 1100 and 1400 <= 1400); trial c has no room after the interval end -> excluded; non_sound ignored
    assert list(out["trial_id"]) == ["a", "b"]
    assert out["features"].shape == (2, 47, 3)
    # impulse at sample 600 lands in the window that starts at the onset (pre = 50 samples => window index 10)
    w = int(np.argmax(out["features"][0, :, 0]))
    assert out["window_starts"][w] <= 50 < out["window_starts"][w] + out["window_length"]
    assert out["accepted"].all()
    # record scale = median |x| over accepted epochs = 1.0 by construction
    assert math.isclose(out["record_scale"], 1.0)
    # features are divided by the scale, so the impulse mean is 10 / 20 samples = 0.5 in its window
    assert math.isclose(float(out["features"][0, w, 0]), 0.5, rel_tol=1e-5)
