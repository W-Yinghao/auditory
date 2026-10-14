# B / C localisation probes — results (2026-10-14)

Plan: `BC_PROBE_PLAN_20261014.md` (frozen before the runs). Jobs: P0 CPU 1039559; P1–P4 GPU 1039560 (L40S; preempted once,
requeued, completed 11:25). Cell for P1–P4: FAU NCE, subject fold 0, content fold 0, seed 3401. Outputs:
`private/auditory_alignment_v3/probe_bc/` (`probe_layers.json`, `probe_gpu.json`, logs). Each reading below applies the
frozen plan. Where the data do not fit a pre-written reading exactly, this is stated.

## P0 · Frozen-backbone layer probes (B_LAYER_PROBE, seed 3401, identity level)

Unified gain (bits, mismatched − regular logloss; higher = more EEG-specific stimulus information) and R (bits):

| dataset | local NCE | local CS | B1 frozen NCE cbramod / reve | layer probe cbramod: patch_emb / middle / last | layer probe reve: patch_emb / middle / last |
|---|---|---|---|---|---|
| FAU (n 67) | 1.044 (R 6.309) | 0.724 | 0.006 / 0.065 | 0.030 / 0.051 / 0.030 | 0.013 / 0.042 / 0.049 |
| DTU (n 44) | 2.009 (R 6.869) | 1.381 | 0.024 / 0.144 | 0.309 / 0.448 / 0.248 | 0.098 / 0.169 / 0.158 |
| Federici (n 86) | 0.264 (R 8.056) | 0.221 | 0.000 / 0.025 | 0.108 / 0.064 / 0.023 | 0.008 / 0.072 / 0.005 |

- Every layer probe has higher risk than the local model (pointwise, all 18 dataset × backbone × layer cells, against both
  local objectives).
- FAU: every layer, including the patch embedding, carries ≤ 0.05 bits gain, about the level of the trained B readouts.
- Federici: ≤ 0.11 bits.
- DTU: the frozen CBraMod layers reach 0.25–0.45 bits, against 0.024 for the trained CBraMod B1. This is still ≤ 22 % of local.
  In R, the DTU layer probes are **worse** than B1 (R 8.0–8.2). Their probability calibration on test is poor even where
  some signal is present.
- Reading (plan): for FAU and Federici, and REVE on DTU, the result is "the FM input path / backbone features do not carry
  the stimulus at this time resolution". For CBraMod on DTU it is partly "the trained readouts fail to extract what the
  backbone has". The two readings were written as alternatives; the data show a mix.

## P1 · C evaluation path at zero residual vs the A_LOCAL record

The C unit `ALN3_0e76e069d283f384` (reve `residual_pretrained_frozen`) was rebuilt with the residual's last layer zeroed and
evaluated with `evaluate_complement`. It was compared with its local base `ALN3_a101538336184522` on 14 participants, all with
identical candidate counts.

- Max |difference| in every logloss metric (unified / native × regular / mismatched / hard): ≤ 3e-7 bits.
- The largest difference of any metric is `native/mismatched_eeg/rank_pct` = 1.2e-4. That is one rank position of one query
  (rank granularity ≈ 1 / (n_candidates − 1) / n_queries), from a floating-point tie.
- The pre-set tolerance of 1e-4 was written for bits. That single rank step exceeds it by its granularity; all bit-valued
  metrics are 300× inside it.
- Reading: the C path reproduces local. The C-vs-local differences in `C_COMPLEMENT_RESULTS.md` are training effects, not
  evaluation-path effects.

## P2 · Train / evaluation query consistency (B units)

| model | queries on grid | max \|Δu\| training path vs `DenseReps` | audio starts = segment s0 | s0_train = s0_true |
|---|---|---|---|---|
| reve frozen dense_query | yes | 1.8e-7 | yes | yes |
| reve frozen phase_linear | yes | 2.4e-7 | yes | yes |
| reve random_full phase_linear | yes | 2.5e-7 | yes | yes |
| cbramod frozen phase_linear | yes | 3.1e-7 | yes | yes |

Reading: consistent. No train/evaluation mismatch in query times or audio pairing.

## P3 · Lag scan on the training participants (ridge u(t) → A(t + Δ), r on held-out early-stopping half)

Grid step 3 samples (23.4 ms at 128 Hz); Δ = −43 … +43. The floor is Δ = 0 with A from another segment (mean / max over 5
rolls).

| model | r(Δ=0) | peak Δ (steps) | peak r | floor mean / max | above floor mean + 0.02? |
|---|---|---|---|---|---|
| local `lag_local_tokens` (control) | 0.060 | +2 | 0.064 | 0.005 / 0.012 | yes |
| reve frozen dense_query | −0.000 | +3 | 0.016 | 0.001 / 0.003 | no |
| reve frozen phase_linear | 0.024 | +1 | 0.024 | 0.010 / 0.012 | no |
| reve random_full phase_linear | 0.008 | +10 | 0.022 | 0.003 / 0.008 | no |
| cbramod frozen phase_linear | 0.002 | −17 | 0.006 | −0.002 / 0.007 | no |

- The control peaks at +2, outside the pre-set expectation |Δ| ≤ 1. Its curve is a flat top (r = 0.057, 0.060, 0.062, 0.064,
  0.062 at Δ = −1 … +3), which this disclosure records rather than counting it as a failed control.
- No FM model has any Δ above the floor + 0.02. Reading: "no stimulus-locked information extracted" for all four FM models.
  This holds even on held-out content of the training participants.
- No off-lag peak above that threshold either. Reading: no evidence of a time misalignment.

## P4 · Query sensitivity (same early-stopping segments)

| model | within-segment variance fraction | adjacent-query cosine | within-patch fraction |
|---|---|---|---|
| local (control) | 0.974 | 0.973 | 0.895 |
| reve frozen dense_query | 0.989 | 0.904 | 0.940 |
| reve frozen phase_linear | 1.000 | 0.691 | 0.976 |
| reve random_full phase_linear | 0.999 | 0.738 | 0.982 |
| cbramod frozen phase_linear | 1.000 | 0.798 | 0.999 |

Reading: `dense_query` does not ignore query time (fraction ≫ 0.05, adjacent cosine < 0.99). Its output varies across
queries; that variation does not track the stimulus (P3).

## Summary of what is and is not localised

**Excluded**:
- an evaluation-path difference between C and local (P1);
- a train/evaluation query-time or audio-pairing mismatch in the dense FM path (P2);
- a constant time misalignment (P3);
- a query-insensitive `dense_query` readout (P4).

**Remaining**: the FM representations themselves carry almost no stimulus-locked information at the 20 ms grid. This holds
- for trained readouts (B1, B2),
- for a randomly initialised REVE trained end to end,
- for frozen layers including the patch embedding (P0, FAU / Federici; partial exception CBraMod on DTU),
- even on the training participants' held-out content.

The small local encoder extracts it from the same `DenseBatcher` EEG. The open locus is therefore upstream of the readouts:
the FM input preparation (adapter resampling, amplitude scaling, channel mapping) or what the backbones' 1 s patches retain
at this time resolution. These probes do not separate those two.

**Not run** (plan "deferred"): the C variant with a `channel_phase_linear` context branch and an epoch-0 candidate. With
P1 clean and P3 showing no usable FM signal, it would test a branch with no information. It waits on the input-path question.

## P5 · FM input path (plan 02, `BC_PROBE_PLAN_02_INPUT_PATH_20261014.md`; GPU job 1039636, A40)

Training participants only; subject fold 0, content fold 0, target `local`. 300 fit / 160 early-stopping segments. Ridge
r = mean Pearson r over target dimensions on early-stopping half B.

| dataset | view | dims | r(Δ=0) | ratio to F0 | peak Δ (steps) | floor | r first 0.5 s / middle / last 0.5 s |
|---|---|---|---|---|---|---|---|
| FAU | F0 native window (128 Hz) | 2,387 | 0.0207 | 1.00 | +1 | 0.004 | 0.031 / 0.015 / 0.055 |
| FAU | F1 CBraMod input (padded, resampled, × 0.15) | 3,720 | 0.0211 | 1.02 | +1 | 0.005 | 0.030 / 0.016 / 0.057 |
| FAU | F2 REVE input (resampled, clipped) | 3,720 | 0.0221 | 1.07 | +1 | 0.006 | 0.029 / 0.017 / 0.056 |
| DTU | F0 native window | 4,928 | 0.0453 | 1.00 | +2 | 0.002 | 0.032 / 0.046 / 0.051 |
| DTU | F1 CBraMod input | 7,680 | 0.0440 | 0.97 | +2 | 0.003 | 0.032 / 0.045 / 0.051 |
| DTU | F2 REVE input | 7,680 | 0.0443 | 0.98 | +2 | 0.003 | 0.032 / 0.045 / 0.051 |

**Input statistics (P5b)**:
- Native per-channel SD: mean 0.89 for FAU (range 0.008–5.9), 0.97 for DTU (0.11–4.6).
- Samples clipped by REVE (|z| > 15): 5.6e-5 (FAU), 1.4e-6 (DTU).
- FFT resampling vs linear interpolation of the same context, relative RMS for first 0.5 s / middle / last 0.5 s: FAU 3 % /
  5 % / 9 %; DTU 4 % / 6 % / 11 %.
- The larger end difference does not lower readability: the last 0.5 s has the highest r in every view.

**Channel order (P5c)**:
- FAU: 81 / 81 participant files have exactly the order of `foundation_adapter.CHANNELS["fau"]`.
- DTU: the stored channel names equal `CHANNELS["dtu"]`.

**Reading (plan 02)**:
- r(F1) and r(F2) ≥ 0.9 · r(F0) at Δ = 0, above the floor, in both datasets. The adapter input preserves the
  stimulus-locked information that is linearly present in the local lag window.
- The views share the same peak lag, so there is no resampling time shift. Channel order is correct, so there is no
  position misassignment.
- The loss therefore happens inside the backbones: patch embedding, transformer or optimisation. This holds for frozen
  pretrained layers (P0) and for randomly initialised REVE trained end to end (P3).

For scale only (different features and fits, not a contrast): the trained local encoder reaches r = 0.060 on the same FAU
training-side scan (P3). The linear readout of its own 0.6 s input window reaches 0.021 here.

## P6 · Query-aligned backbone tokens (plan 03, `BC_PROBE_PLAN_03_ALIGNED_TOKENS_20261014.md`; GPU job 1039800)

Frozen backbones; no training. Linear kernel ridge → target A(t); r on early-stopping half B. The ratio is r(view) / r(R10),
where R10 is the raw EEG of exactly the aligned patch window [t − 0.4 s, t + 0.6 s).

**DTU** (R06 r = 0.038, R10 r = 0.034, floors ≤ 0.014):

| backbone | layer | ALIGNED pretrained | UNALIGNED pretrained (B_DENSE tokens) | ALIGNED random init |
|---|---|---|---|---|
| CBraMod | patch_embedding | 0.030 (0.87) | 0.005 (0.16) | 0.023 (0.66) |
| CBraMod | last | 0.031 (0.90) | 0.003 (0.07) | 0.020 (0.59) |
| REVE | patch_embedding | 0.026 (0.75) | −0.003 (−0.09) | 0.035 (1.01) |
| REVE | last | 0.034 (0.97) | −0.000 (−0.01) | 0.033 (0.96) |

**FAU** (R06 r = 0.015, R10 r = 0.005, floors −0.012 … +0.003):

| backbone | layer | ALIGNED pretrained | UNALIGNED pretrained | ALIGNED random init |
|---|---|---|---|---|
| CBraMod | patch_embedding | 0.005 | −0.006 | 0.015 |
| CBraMod | last | 0.014 | −0.007 | 0.014 |
| REVE | patch_embedding | −0.004 | 0.005 | 0.008 |
| REVE | last | 0.011 | 0.007 | 0.005 |

**Reading (plan 03)**:
- **DTU**: ALIGNED pretrained ≥ 0.5 · r(R10) for every backbone and layer (0.75–0.97), and above UNALIGNED, which is ≈ 0.
  Reading: aligned patching recovers the information. Next step: a registered query-aligned B variant.
  - The pretrained weights are not consistently better than random initialisation for this linear readability. CBraMod:
    pretrained 0.87–0.90 vs random 0.59–0.66. REVE: pretrained 0.75–0.97 vs random 0.96–1.01.
- **FAU**: not readable as a ratio. R10 itself is barely above the floor (0.005), below R06 (0.015): the wider window
  with fewer queries is underpowered here. Aligned views exceed unaligned in 3 of 4 pairs; REVE patch_embedding is the
  reversal. FAU therefore neither supports nor contradicts the DTU result.

**What this localises**:
- At the 20 ms grid, the backbone tokens of a fixed patch grid that is not aligned with the query carry essentially no
  linear stimulus information, even though the patch content contains it.
- A patch aligned with the query keeps most of it (DTU).
- The B_DENSE failure is therefore consistent with the patch-to-query alignment of the readout interface, not with an
  absence of information in the backbone.
