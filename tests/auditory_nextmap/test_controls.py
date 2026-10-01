"""T6 and the A1 input definitions: non-aligned windows, staging rebuild, draw0 mapping."""
import numpy as np
import pandas as pd
import pytest

from auditory_nextmap import controls as ct
from auditory_nextmap import representations as rp
from auditory_nextmap.runtime import ProvenanceError

GX = {"qc": {"ptp_max_uv": 150.0, "ptp_channel_fraction_max": 0.10, "flat_ptp_uv": 0.5, "flat_channel_fraction_max": 0.10},
      "epoch": {"interval_edge_guard_seconds": 2.0}}
CONFIG = {"controls": {"nonaligned": {"physical_block_seconds": 60, "source_epoch_seconds": 0.8, "pre_seconds": 0.2,
                                      "interval_guard_seconds": 2.0, "anchor_exclusion_seconds": 0.08,
                                      "exclusion_event_kinds": ["target", "unknown_sound"], "seed": 27092703}}}


def test_t6_candidates_stay_inside_interval_and_away_from_events():
    iv = {"interval_index": 0, "start": 1000, "stop": 6000, "original_start_sample": 0}
    ev = np.array([1700, 3000, 3021, 5999])
    a = rp.candidate_anchors(iv, ev, pre=50, post=150, guard=500, exclusion=20)
    assert a.min() - 50 >= 1000 + 500 and a.max() + 150 <= 6000 - 500          # guard on both sides, no wrap-around
    d = rp.nearest_event_distance(a, ev)
    assert d.min() > 20
    assert not np.any((a >= 2980) & (a <= 3041))                                # both close events excluded
    assert rp.candidate_anchors({"interval_index": 0, "start": 0, "stop": 900, "original_start_sample": 0},
                                ev, pre=50, post=150, guard=500, exclusion=20).size == 0


def test_t6_block_uses_original_time_axis():
    iv = {"interval_index": 1, "start": 20000, "stop": 60000, "original_start_sample": 120000}
    # exported 20000 -> original 120000 samples at 1000 Hz = 120 s -> block 2 (60 s blocks)
    assert rp.block_of_anchor(20000, iv, stride=4, original_fs=1000.0, block_seconds=60.0) == 2
    assert rp.block_of_anchor(20000 + 15000, iv, stride=4, original_fs=1000.0, block_seconds=60.0) == 3


def test_block_selection_is_seeded_and_qc_aware():
    cand = np.arange(100, 400)
    sel1, t1 = rp.select_block_windows(cand, 5, np.random.default_rng(7), lambda a: a % 2 == 0)
    sel2, _ = rp.select_block_windows(cand, 5, np.random.default_rng(7), lambda a: a % 2 == 0)
    assert sel1 == sel2 and len(sel1) == 5 and all(a % 2 == 0 for a in sel1) and t1 >= 5
    few, _ = rp.select_block_windows(np.array([1, 3]), 5, np.random.default_rng(0), lambda a: True)
    assert few == [1, 3]                                                        # shortfall is reported, never padded


def _synthetic_record(seed=0):
    rng = np.random.default_rng(seed)
    n = 250 * 200                                                              # 200 s at 250 Hz, one interval
    data = (rng.normal(size=(20, n)) * 10).astype(np.float32)
    on = np.arange(800, n - 800, 195)
    lit = np.where(np.arange(on.size) % 5 == 4, "2", "1")
    events = pd.DataFrame({"event_kind": "target", "exported_index": on, "exported_interval_index": 0,
                           "onset_seconds": on / 250.0, "event_literal": lit})
    meta = {"rate_hz": 250.0, "stride": 4, "original_fs": 1000.0,
            "intervals": [{"interval_index": 0, "start": 0, "stop": n, "original_start_sample": 0}]}
    keep = (on - 50 >= 500) & (on + 150 <= n - 500)
    on_k = on[keep]
    ep = np.stack([data[:, e - 50:e + 150] for e in on_k])
    qc = ct._qc_fn(GX)
    acc = np.array([qc(e)[0] for e in ep])
    scale = float(np.median(np.abs(ep[acc])))
    stage = {"x": rp.stage_transform(ep, scale), "accepted": acc, "onset_seconds": on_k / 250.0,
             "record_scale": np.float64(scale), "y": (lit[keep] == "2").astype(np.int64),
             "block_id": (on_k / 250.0 // 60).astype(np.int64)}
    return data, events, meta, stage


def test_rebuild_check_is_bit_exact_and_detects_changes():
    data, events, meta, stage = _synthetic_record()
    chk = ct.rebuild_check(CONFIG, GX, "r", stage, events, meta, data)
    assert chk["x_bit_exact"] and chk["accepted_equal"] and chk["onsets_equal"]
    bad = dict(stage, x=stage["x"].copy())
    bad["x"][3, 2, 7] += np.float16(0.5)
    assert not ct.rebuild_check(CONFIG, GX, "r", bad, events, meta, data)["x_bit_exact"]


def test_nonaligned_windows_match_block_quota_and_staging():
    data, events, meta, stage = _synthetic_record(1)
    d0 = {0: np.flatnonzero(stage["y"] == 0)[:30], 1: np.flatnonzero(stage["y"] == 1)[:10]}
    na = ct.nonaligned_windows(CONFIG, GX, "r", stage, d0, events, meta, data)
    quota = pd.Series(stage["block_id"][np.concatenate([d0[0], d0[1]])]).value_counts().to_dict()
    got = pd.Series(na["blocks"]).value_counts().to_dict()
    assert got == {int(k): int(v) for k, v in quota.items()} and not na["shortfall"]
    assert na["nearest_event"].min() > 20
    a = int(na["anchors"][0])
    assert np.array_equal(na["x"][0], rp.stage_transform(data[None, :, a - 50:a + 150], float(stage["record_scale"]))[0])
    assert na["x"].dtype == np.float16 and na["x"].shape[1:] == (20, 200)


def test_draw0_mapping_rejects_wrong_class():
    class Co:
        draw_row = {5: 0}
        draw_std = np.array([[[0, 1]]])
        draw_dev = np.array([[[2, 3]]])
    src = object.__new__(ct.AgeSource)
    src.co = Co()
    src.primary = lambda c: 5
    stage = {"accepted": np.array([1, 0, 1, 1, 1, 1], bool), "y": np.array([0, 0, 0, 1, 1, 1])}
    out = ct.draw0_indices(src, 0, stage)
    assert out[0].tolist() == [0, 2] and out[1].tolist() == [3, 4]
    stage["y"] = np.array([0, 0, 1, 1, 1, 1])
    with pytest.raises(ProvenanceError):
        ct.draw0_indices(src, 0, stage)
