# ALN4.1 R1 report (seed 3401, 2026-10-21)

Package `AUDITORY_ALN4_SERVER_PACKAGE_v4_1_20261021` (zip SHA256 `eb9b343b…971b2c`), researcher instruction "这个包也启动，
这个包里的有优先级". Single seed, therefore exploratory. People are the unit; public values are averaged over the two content
folds within each person. Full family tables: `results/auditory_alignment_v3/aln41/r1/FAMILY_TABLES.md`; per-person values:
`person_results.csv`; contrasts, coverage and F_ASSOC: `contrasts.json`. Binding: `private/auditory_alignment_v3/aln41/bindings/BINDING.json`
(status BOUND). Intake: `private/auditory_alignment_v3/aln41/intake/INTAKE.md`.

## Research answer so far

**Which stimulus relations transfer?** Correct audio pairing in Stage2 matters, and time-tagged CS does better than pooled CS.
Time-tagged CS is not the best objective, though: matched temporal InfoNCE (TNCE) gives the strongest frozen content
representation. Results by comparison (history-conditional envelope r, frozen, PCA64 readout, q0 mixture):
- **TCS vs TCS_WRONG** (same EEG, audio rows permuted across families): TCS higher by DTU +0.036 [+0.021, +0.052] and FAU
  +0.040 [+0.029, +0.050]. Wrong pairing drops the content readout far below B0 (DTU 0.017 vs 0.051, FAU 0.015 vs 0.037).
  So part of this gap is damage done by wrong pairing, not benefit from TCS (decision table row "TCS only beats wrong").
- **TCS vs B0**: FAU +0.018 [+0.009, +0.027] (TCS also beats wrong, and the history-residual target is the content control);
  DTU +0.003 [−0.006, +0.012], not resolved.
- **TCS vs TNCE**: TCS is worse. DTU −0.034 [−0.044, −0.023], FAU −0.012 [−0.022, −0.003]. Private children −0.0003, not
  resolved. CS is a feasible objective here; CS necessity is not supported, and TNCE is the better tool in this R1.
- **TCS vs GCS**: FAU +0.034 [+0.022, +0.047]; DTU +0.016 [−0.001, +0.033], not resolved. Building the dependence on the
  time-tagged distribution beats pooling first, in FAU.

**Which time readouts transfer or recover after refitting?** W0→W2 fixed-readout loss and refit recovery, history-conditional r:
- Refit recovery is larger for TCS than for TNCE (DTU +0.022 [+0.006, +0.039], FAU +0.016 [+0.005, +0.027]) and than for GCS in
  FAU (+0.021 [+0.003, +0.040]). TCS readouts depend more on the specific window; this is not a timing advantage.
- Fixed-loss differences are resolved only against TCS_WRONG. Wrong pairing loses less when transferred (DTU −0.049
  [−0.074, −0.024], FAU −0.018 [−0.035, −0.001]), consistent with its weaker, flatter representation.
- Private children: TNCE loses more AUC across W0→W2 than TCS (+0.022 [+0.005, +0.040]); all other private time contrasts are
  not resolved.

**What is supported in the private children?**
- Frozen current-sound AUC (q0 mixture): TNCE 0.535, TCS 0.525, GCS 0.515, TCS_WRONG 0.512, B0 0.511. History-conditional
  increments are near 0 and every F_CONTENT:PRIVATE contrast is unresolved (e.g. TCS−B0 +0.0016 [−0.0003, +0.0036] bits/trial).
  The strict-twin difference (EEG − same-history other-block twin) is positive in every arm but small (TCS +0.0019,
  TNCE +0.0026 bits/trial descriptively).
- **Private CE full fine-tuning** (15 fits): mean test AUC B0 0.535, TCS 0.537, TNCE 0.538. TCS−B0 +0.0024
  [−0.0052, +0.0099], TCS−TNCE −0.0014 [−0.0093, +0.0064]. Source Stage2 does not change the fine-tuned event task.
  Early stopping selected epochs 10–37, all within the 100-epoch budget.
- **Frozen age** (64 children, unseen-child nested ridge). Every core arm predicts age clearly better than the raw-EEG
  log-variance ridge and the training mean:

  | Arm | MAE (months) | R² |
  |---|---:|---:|
  | B0 | 25.05 | 0.39 |
  | TCS | 25.37 | 0.37 |
  | TNCE | 24.90 | 0.38 |
  | raw-EEG ridge | 32.38 | −0.02 |
  | training mean | 32.02 | — |

  Paired absolute-error gains: raw−B0 +7.3 [+1.4, +13.3] months, raw−TNCE +7.5 [+0.3, +14.6]. The TCS versus raw and mean
  intervals touch 0. TCS adds nothing beyond B0 (B0−TCS −0.32 [−5.3, +4.7]). This shows developmental information in the
  shared Stage1 tokens of this cohort, not a contribution of Stage2.
- **F_ASSOC**: none of the 24 private age / HA / device-duration coefficients on the TCS−B0 and TCS−TNCE differences
  excludes 0 (simultaneous critical 3.32). Of 24 public group contrasts, only FAU TCS−TNCE content HA−CI is pointwise
  negative (−0.023 [−0.041, −0.006]); it is not a family-wise finding.

**Public attention** (20 s mean integrator, double order, ties = 0.5). DTU: B0 0.626 and TCS 0.626 are equal; TCS−TNCE
+0.029 [+0.002, +0.055]; GCS 0.531 and TCS_WRONG 0.564 are lower. FAU: all arms are near chance (0.51–0.53), and both
contrasts are unresolved.

**What did not work as designed.**
- The learned group time gate stayed uniform in every arm (final q ≈ [0.333, 0.333, 0.334]; TNCE [0.334, 0.346, 0.320]).
  q0 and the uniform reset are therefore identical, and the "source time prior" question cannot be answered in R1.
- The TNCE query loss sat at chance (ln 32) from about update 200 to 10 000. TCS/GCS dependence scores rose only slightly
  (TCS −0.0186 → −0.0210; GCS −0.029 → −0.046). The within-person 32-anchor source signal is weak, as in the earlier CBAUD
  donors (paired dev NCE 4.076–4.078 vs wrong 4.081).
- Even so, TNCE gives the best frozen representation. Its effect works through the backbone, not through a learned
  within-person discrimination.

## Identity and completion

- **Stage1**: CBraMod `pretrained_full` (SHA256 `0792cb80…7178`). The MindMix EEG-only asset gate did not pass: the
  200×24-dim, 20-head, 109-position, 128-time-step student matches no public code, and its channel→position map cannot be
  recovered (`intake/STAGE1_GATE.json`). No ALN4.0 existed on this server.
- **Source**: SparrKULee fit 81,732 segments / 64 people / 48 families; dev 6,332 / 10 / 9; overlap presentations 4, 5, 19
  excluded. All 64 people were eligible.
- **Stream**: 10 000 pre-generated episodes shared by every arm (`b51945d5…`), with S/Q physical guard checks on every
  episode.
- **Units**: 6/6 calibration + selection (lr 1e-4 for all; TCS_WRONG inherits TCS); 4/4 production at 10 000 updates;
  15/15 private CE; 25/25 frozen extractions; 25/25 readouts; age 1/1. Coverage: DTU 44/44, FAU 67/67, children 64/64
  (age available for all 64). Families: 9/9 complete.
- **Compute (actual)**: source 3.6 GPU-h (A100; production 37–53 min per arm), frozen 1.7 GPU-h, private CE 16.6 GPU-h
  (53–71 min per fit). Each source update = 2 people × 64 anchors × 3 crops plus 5 inner support steps.

## Optimization and correctness

- **Full backbone update**: every backbone tensor received a gradient at the first update. The one exception is CBraMod's
  masked-pretraining token, which is unused without a mask and exempted by exact name. Relative backbone change at update
  10 000: 8.9–10.7%.
- **Fixed-final transfer** at update 10 000 (no per-arm "best" epoch). Checkpoints kept at 0 / 2 500 / 5 000 / 10 000.
- **Inputs**: crop-only resampling equals `scipy.signal.resample` to 2e-15 on every crop length. 20/31/64-channel
  three-crop forwards are finite; save → strict reload diff is 0.
- **Bandwidths** (frozen at the initial state on the source-fit panel): σ_u 1.06–1.14, σ_a 1.41, pooled GCS σ 0.80–0.90.
- **Selection probe (limitation)**: dev NMSE was 1.53–1.91 at calibration and 2.0–2.7 at production, i.e. worse than the fit
  mean. The fixed ridge λ = 1e-3·trace/n overfits the 38 400-dim token vectors. It only ranked the two LRs (lower wins) and
  did not choose a model.
- **Wrong pairing**: cross-family bijection per support and query, shared by all three views (asserted for every episode).
- **Private**: test children took no part in training or selection; ES = training children's last ~20% physical blocks.
- **Reference harness bug**: the package `verify_temporal_torch.py` crashed in its own harness; a server copy with one detach
  passes 28/28.

## Decision for R2 within the fixed budget

Keep the original core replication unchanged: seeds 3407 and 3413, the four source arms (8 fits, LR not re-selected),
3 × 5 private CE (30 fits), and the same frozen endpoints. TNCE's strength and TCS's weakness are not reasons to drop or
retune an arm.
- **Personal support (U0 / U10 / U30, δ vs affine calibration)**: asset-ready. The private CE checkpoints exist, and the
  support contract is reused from aln35.
- **Cross-stimulus question**: still requires the asset-semantics decision (MFF pure-tone vs bapa, 9 candidate same-day
  children; the 7-vs-8 completeness discrepancy is recorded). It must be fixed before any new result is seen.
- **Optional ablation slot**: not used. If invoked in R2, it would target the one unresolved mechanism, i.e. whether the
  learned time gate stays uniform because of the 0.01 KL to uniform. It would be one change (gate KL 0), compared with TCS,
  capped at 3 source and 15 private fits, and must be registered before its results exist. Nothing is registered now.
- **External slot (R3)**: full MindMix on DTU auditory attention decoding; fallback Transformer-CLIP. Fixed in
  `intake/EXTERNAL_SLOT_DECISION.json` before these results.

## Legacy reuse and retention

- D2/GX/NEXTMAP originals were read from `archive/`; they are byte-identical to the package blob OIDs.
- MFF 12.50 vs 19.07 months is confirmed, with caveats: 12.50 is the single-seed linear or the 4-seed RBF value; the 4-seed
  linear is 12.97.
- The GX R2 erratum is not on GitHub. The NEXTMAP `gpu_age.train_age` bug is undocumented in the G1/H reports and was never
  rerun.
- D1 arrays were deleted on 2026-10-11, so D2 features cannot be rebuilt without re-export.
- No old result was recomputed. No deletion was performed. A3b/A3c/A3d/D_FM are still only registered; this round adds no
  dependency to them.
