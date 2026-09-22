"""auditory_gx unit tests: models, training loop, data splits, staging config parsing, and a
CPU-only end-to-end mini training run on a synthetic staged lane.

CPU only: no CUDA is required or exercised. train.fit/predict use
torch.autocast(device_type="cuda", enabled=xb.is_cuda), which is a no-op (disabled) whenever
the tensors live on CPU, so nothing here needs a GPU or an explicit autocast toggle.
"""
from __future__ import annotations

import csv
import math
from types import SimpleNamespace

import numpy as np
import pytest
import torch
from sklearn.metrics import roc_auc_score

from auditory_gx import data as gxd
from auditory_gx import models
from auditory_gx import stage as gx_stage
from auditory_gx import train as gxt
from auditory_gx.runtime import load_config

CONFIG = load_config()


# ----------------------------------------------------------------------------- models.EEGNet

@pytest.mark.parametrize("n_channels", [20, 128])
@pytest.mark.parametrize("n_classes", [2, 3])
def test_eegnet_forward_shared_spatial_shapes(n_channels, n_classes):
    torch.manual_seed(0)
    model = models.EEGNet(n_channels, 200, n_classes)
    x = torch.randn(5, n_channels, 200)
    logits = model(x)
    assert logits.shape == (5, n_classes)
    assert torch.isfinite(logits).all()
    emb = model.embed(x)
    assert emb.shape == (5, model.feature_dim)


@pytest.mark.parametrize("n_channels", [20, 128])
def test_eegnet_forward_with_per_child_spatial_and_fallback_index(n_channels):
    torch.manual_seed(0)
    n_children = 4
    model = models.EEGNet(n_channels, 200, 2, n_children=n_children)
    # includes every trained child plus the fallback index (n_children) used for unseen children
    child = torch.tensor([0, 1, 2, 3, n_children, n_children], dtype=torch.long)
    B = child.shape[0]
    x = torch.randn(B, n_channels, 200)
    logits = model(x, child=child)
    assert logits.shape == (B, 2)
    assert torch.isfinite(logits).all()
    emb = model.embed(x, child=child)
    assert emb.shape == (B, model.feature_dim)

    # child=None falls back to the shared (fallback-index) filter for every sample
    logits_default = model(x, child=None)
    assert logits_default.shape == (B, 2)


@pytest.mark.parametrize("n_channels", [20, 128])
def test_eegnet_forward_with_film_conditioning(n_channels):
    torch.manual_seed(0)
    model = models.EEGNet(n_channels, 200, 3, cond_dim=1)
    B = 6
    x = torch.randn(B, n_channels, 200)
    cond = torch.randn(B, 1)
    logits = model(x, cond=cond)
    assert logits.shape == (B, 3)
    assert torch.isfinite(logits).all()
    emb = model.embed(x, cond=cond)
    assert emb.shape == (B, model.feature_dim)


# ----------------------------------------------------------------------------- models.MaskedReconstructor

def test_masked_reconstructor_forward_shape_roundtrip():
    torch.manual_seed(0)
    model = models.MaskedReconstructor(n_channels=8, width=16)
    x = torch.randn(3, 8, 1000)
    out = model(x)
    assert out.shape == x.shape
    assert torch.isfinite(out).all()


def test_patch_mask_shape_fraction_and_contiguity():
    gen = torch.Generator(device="cpu")
    gen.manual_seed(0)
    batch, length, patch, fraction = 6, 1000, 50, 0.4
    mask = models.patch_mask(batch, length, patch, fraction, gen, torch.device("cpu"))
    assert mask.shape == (batch, length)
    assert mask.dtype == torch.bool

    n_patches = length // patch
    blocks = mask.view(batch, n_patches, patch)
    # every patch-sized block is either fully hidden or fully visible: masking is patch-contiguous
    fully_masked_or_visible = blocks.all(dim=2) | (~blocks).all(dim=2)
    assert torch.all(fully_masked_or_visible)

    expected_n_masked_patches = max(1, round(fraction * n_patches))
    n_masked_patches = blocks.any(dim=2).sum(dim=1)
    assert torch.all(n_masked_patches == expected_n_masked_patches)


def test_patch_mask_handles_a_length_not_a_multiple_of_patch():
    gen = torch.Generator(device="cpu")
    gen.manual_seed(1)
    batch, length, patch, fraction = 4, 205, 50, 0.5
    mask = models.patch_mask(batch, length, patch, fraction, gen, torch.device("cpu"))
    assert mask.shape == (batch, length)
    # the trailing remainder (205 - 4*50 = 5 samples) is never masked
    assert not mask[:, 200:].any()


# ----------------------------------------------------------------------------- train: weights, CE, metrics, augment

def test_class_weights_are_inverse_frequency():
    y = torch.tensor([0, 0, 0, 1])
    w = gxt.class_weights(y, 2)
    expected = torch.tensor([4 / (2 * 3), 4 / (2 * 1)])
    assert torch.allclose(w, expected, atol=1e-5)


@pytest.mark.parametrize("k", [2, 3, 5])
def test_balanced_ce_bits_is_chance_level_for_uniform_logits(k):
    n_per_class = 10
    y = np.repeat(np.arange(k), n_per_class)
    logits = np.zeros((len(y), k))
    value = gxt.balanced_ce_bits(logits, y, k)
    assert math.isclose(value, math.log2(k), rel_tol=1e-6)


def test_child_metrics_binary_perfect_separation():
    y = np.array([0, 0, 1, 1])
    logits = np.array([[1.0, 0.0], [1.0, 0.0], [0.0, 1.0], [0.0, 1.0]])
    out = gxt.child_metrics(logits, y, 2)
    assert out["n"] == 4 and out["n_class1"] == 2
    assert math.isclose(out["auc"], 1.0)
    assert math.isclose(out["bacc"], 1.0)
    assert math.isfinite(out["ce_bal_bits"]) and out["ce_bal_bits"] >= 0
    assert "auc_pitch_direction" not in out


def test_child_metrics_binary_single_class_is_nan():
    y = np.zeros(5, dtype=int)
    logits = np.random.default_rng(0).standard_normal((5, 2))
    out = gxt.child_metrics(logits, y, 2)
    assert out["n"] == 5 and out["n_class1"] == 0
    assert math.isnan(out["auc"]) and math.isnan(out["bacc"])
    assert math.isnan(out["ce_bal_bits"]) and math.isnan(out["j_bits"])


def test_child_metrics_three_class_includes_pitch_direction_auc():
    y = np.array([0, 0, 1, 1, 2, 2])
    logits = np.array([[5.0, 0.0, 0.0]] * 2 + [[0.0, 5.0, 0.0]] * 2 + [[0.0, 0.0, 5.0]] * 2)
    out = gxt.child_metrics(logits, y, 3)
    assert math.isclose(out["auc"], 1.0, abs_tol=1e-6)
    assert math.isclose(out["bacc"], 1.0)
    assert "auc_pitch_direction" in out
    assert math.isclose(out["auc_pitch_direction"], 1.0)


def test_augment_preserves_shape_and_dtype_on_cpu():
    gen = torch.Generator(device="cpu")
    gen.manual_seed(0)
    xb = torch.randn(6, 4, 64, dtype=torch.float32)
    out = gxt.augment(xb, CONFIG, gen)
    assert out.shape == xb.shape
    assert out.dtype == torch.float32
    assert out.device.type == "cpu"
    assert torch.isfinite(out).all()

    # deterministic given a generator seeded the same way
    gen_a = torch.Generator(device="cpu"); gen_a.manual_seed(7)
    gen_b = torch.Generator(device="cpu"); gen_b.manual_seed(7)
    out_a = gxt.augment(xb, CONFIG, gen_a)
    out_b = gxt.augment(xb, CONFIG, gen_b)
    assert torch.equal(out_a, out_b)


# ----------------------------------------------------------------------------- data: folds and splits

def test_child_folds_partition_all_children_disjoint_and_balanced():
    n_children, n_folds, seed = 23, 5, 7
    folds = gxd.child_folds(n_children, n_folds, seed)
    assert len(folds) == n_folds
    sizes = [len(f) for f in folds]
    assert max(sizes) - min(sizes) <= 1

    all_ids = np.concatenate(folds)
    assert sorted(all_ids.tolist()) == list(range(n_children))

    seen: set = set()
    for f in folds:
        s = set(f.tolist())
        assert not (s & seen), "folds must be disjoint"
        seen |= s


def test_split_inner_returns_a_disjoint_partition():
    train_children = np.array([2, 5, 9, 11, 14, 20, 21, 30, 31, 42])
    tr, val = gxd.split_inner(train_children, fraction=0.3, seed=1)
    assert len(val) == max(1, round(0.3 * len(train_children)))
    assert len(tr) + len(val) == len(train_children)
    assert not (set(tr.tolist()) & set(val.tolist()))
    assert set(tr.tolist()) | set(val.tolist()) == set(train_children.tolist())


def _fake_lane(child: np.ndarray, y: np.ndarray, onset_s: np.ndarray, n_classes: int) -> SimpleNamespace:
    return SimpleNamespace(child=child, y=torch.as_tensor(y, dtype=torch.long), n_classes=n_classes, onset_s=onset_s)


def test_within_child_split_train_val_test_disjoint_and_val_is_latest_by_onset():
    n = 200
    rng = np.random.default_rng(0)
    child = np.zeros(n, dtype=np.int64)
    part = np.arange(n) % 2                       # even index -> block 0, odd index -> block 1
    y = rng.integers(0, 2, size=n)                 # plenty of both classes in both blocks
    onset = np.arange(n, dtype=np.float64)
    lane = _fake_lane(child, y, onset, n_classes=2)

    result = gxd.within_child_split(lane, 0, part, 0, val_fraction=0.2, seed=0, min_per_class=5)
    assert result is not None
    train_idx, val_idx, test_idx = result

    assert not (set(train_idx.tolist()) & set(val_idx.tolist()))
    assert not (set(train_idx.tolist()) & set(test_idx.tolist()))
    assert not (set(val_idx.tolist()) & set(test_idx.tolist()))

    train_block = set(np.flatnonzero((child == 0) & (part == 0)).tolist())
    test_block = set(np.flatnonzero((child == 0) & (part == 1)).tolist())
    assert set(train_idx.tolist()) | set(val_idx.tolist()) == train_block
    assert set(test_idx.tolist()) == test_block

    # validation is the LATEST part of the training block by onset time (no trial-level leakage)
    assert onset[val_idx].min() >= onset[train_idx].max()


def test_within_child_split_returns_none_when_a_class_is_too_rare():
    n = 100
    part = np.arange(n) % 2
    y = np.zeros(n, dtype=np.int64)
    y[1] = 1                                       # a single class-1 trial only, in block 1
    onset = np.arange(n, dtype=np.float64)
    lane = _fake_lane(np.zeros(n, dtype=np.int64), y, onset, n_classes=2)

    result = gxd.within_child_split(lane, 0, part, 0, val_fraction=0.2, seed=0, min_per_class=5)
    assert result is None


# ----------------------------------------------------------------------------- stage.condition_map

def test_condition_map_parses_source_candidate_id_lists(tmp_path, monkeypatch):
    monkeypatch.setattr(gx_stage, "ROOT", tmp_path)

    clues_path = tmp_path / "condition_clues.csv"
    with clues_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["container_id", "condition_clue"])
        writer.writeheader()
        writer.writerow({"container_id": "C1", "condition_clue": "ci_quiet"})
        writer.writerow({"container_id": "C2", "condition_clue": "ci_noise"})
        # C3 has no lineage row below and must not appear in the result

    lineage_path = tmp_path / "mff_lineage.csv"
    with lineage_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["container_id", "source_candidate_ids"])
        writer.writeheader()
        writer.writerow({"container_id": "C1", "source_candidate_ids": "['S1', 'S2']"})
        writer.writerow({"container_id": "C2", "source_candidate_ids": "['S2']"})
        writer.writerow({"container_id": "C4", "source_candidate_ids": "['S9']"})  # C4 not in clues -> skipped

    config = {"sources": {"condition_clues": "condition_clues.csv", "mff_lineage": "mff_lineage.csv"}}
    result = gx_stage.condition_map(config)

    # S1 only ever seen via C1 (ci_quiet); S2 seen via both C1 (ci_quiet) and C2 (ci_noise) -> unioned & sorted
    assert result == {"S1": "ci_quiet", "S2": "ci_noise|ci_quiet"}
    assert "S9" not in result


# ----------------------------------------------------------------------------- end-to-end: synthetic staged lane

def _write_synthetic_lane(tmp_path, *, n_children: int, n_trials: int, n_channels: int, n_samples: int,
                          lane_name: str, seed: int):
    """Write one fake stage.stage_record()-shaped npz per child, with a planted class signal
    (channel 0, samples [80:140)) that is identical across children so a shared model can
    generalise to a held-out child.
    """
    epochs_dir = tmp_path / "epochs"
    epochs_dir.mkdir(parents=True, exist_ok=True)
    sig_channel, sig_lo, sig_hi, amplitude = 0, 80, 140, 4.0

    for c in range(n_children):
        rng = np.random.default_rng(seed * 1000 + c)
        y = rng.integers(0, 2, size=n_trials).astype(np.int64)
        x = rng.standard_normal((n_trials, n_channels, n_samples)).astype(np.float32)
        x[y == 1, sig_channel, sig_lo:sig_hi] += amplitude
        x16 = x.astype(np.float16)

        onset = np.arange(n_trials, dtype=np.float64) * 0.5 + 5.0
        block_id = np.floor(onset / 60.0).astype(np.int64)
        record_id = f"REC{c:02d}"
        trial_id = np.array([f"{record_id}:{k:05d}" for k in range(n_trials)])
        previous_code = rng.integers(-1, 2, size=n_trials).astype(np.int64)
        previous_gap_s = np.where(previous_code >= 0, rng.uniform(0.3, 2.0, size=n_trials), -1.0).astype(np.float64)
        previous_run_length = np.where(previous_code >= 0, rng.integers(1, 5, size=n_trials), -1).astype(np.int64)
        history_status = np.where(previous_code >= 0, "complete", "no_previous_sound")

        payload = dict(
            x=x16, y=y, accepted=np.ones(n_trials, dtype=bool),
            qc_over_fraction=np.zeros(n_trials, dtype=np.float32),
            onset_seconds=onset, block_id=block_id, trial_id=trial_id,
            previous_code=previous_code, previous_gap_s=previous_gap_s,
            previous_run_length=previous_run_length, history_status=history_status,
            record_scale=np.float64(1.0), rate_hz=np.float64(250.0),
            pre_samples=np.int64(50), post_samples=np.int64(150),
            record_id=record_id, lane=lane_name, branch="MFF",
            identity_group=f"CHILD{c:02d}", n_channels=np.int64(n_channels),
            layout_hash="synthetic", age_months=np.float64(24.0 + c),
            device_duration_months=np.float64(3.0), source_cohort_evidence="synthetic",
            candidate_day_id=f"DAY{c:02d}", condition_clue="quiet",
            original_fs=np.float64(1000.0), d1_seconds=np.float64(600.0),
        )
        np.savez(epochs_dir / f"{record_id}.npz", **payload)
    return tmp_path


def test_end_to_end_shared_model_recovers_planted_signal_and_fit_is_deterministic(tmp_path):
    torch.set_num_threads(1)
    n_children, n_trials, n_channels, n_samples = 4, 300, 8, 200
    lane_name = "mff_puretone"
    stage_dir = _write_synthetic_lane(tmp_path, n_children=n_children, n_trials=n_trials,
                                      n_channels=n_channels, n_samples=n_samples,
                                      lane_name=lane_name, seed=0)

    device = torch.device("cpu")
    lane = gxd.load_lane(CONFIG, stage_dir, lane_name, device=device)
    assert lane.n_children == n_children
    assert lane.n_classes == 2
    assert lane.x.shape == (n_children * n_trials, n_channels, n_samples)
    assert lane.x.device.type == "cpu"

    seed = 123
    folds = gxd.child_folds(lane.n_children, lane.n_children, seed)   # one held-out child per fold
    test_children = folds[0]
    train_children = np.setdiff1d(np.arange(lane.n_children), test_children)
    inner_tr, inner_val = gxd.split_inner(train_children, fraction=0.34, seed=seed)

    train_idx = gxd.idx_of_children(lane, inner_tr)
    val_idx = gxd.idx_of_children(lane, inner_val)
    test_idx = gxd.idx_of_children(lane, test_children)
    assert len(train_idx) > 0 and len(val_idx) > 0 and len(test_idx) > 0

    def _fit_and_predict() -> np.ndarray:
        torch.manual_seed(seed)
        model = gxt.build_model(CONFIG, lane)
        info = gxt.fit(model, lane, train_idx, val_idx, CONFIG, seed=seed, max_epochs=20)
        assert info["epochs_run"] >= 1
        return gxt.predict(model, lane, test_idx)

    logits_a = _fit_and_predict()
    logits_b = _fit_and_predict()
    assert logits_a.shape == (len(test_idx), 2)
    assert np.allclose(logits_a, logits_b, atol=1e-6), "fit() must be deterministic for a fixed seed"

    y_test = lane.y.cpu().numpy()[test_idx]
    score = logits_a[:, 1] - logits_a[:, 0]
    auc = roc_auc_score(y_test, score)
    assert auc > 0.7, f"held-out AUC too low: {auc}"
