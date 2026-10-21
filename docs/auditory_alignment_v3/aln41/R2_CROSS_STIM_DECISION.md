# ALN4.1 R2 cross-stimulus question: decision record (2026-10-21, before any cross-stimulus result)

Package rule (`docs/04` §4.3, `docs/06` F_CROSS_STIM): R2 has exactly one cross-stimulus question. If two stimulus lanes share the
label meaning "current sound identity or deviance relation" after the identity/label audit, a readout trained on the frozen
representation in one lane is tested on the other lane (**transfer**). The same representation is then refitted on the target
lane (**refit**), which separates "the relation is available in the representation" from "the readout is reusable". If the
labels cannot be shared, per-lane readouts compare time/history phenotypes in the same children instead. The route is fixed
here, from asset semantics only.

## Asset audit (read-only; no scores computed)

Audit: `private/auditory_alignment_v3/aln41/checks/mff_crossstim_asset_audit.py`; file hashes in `mff_crossstim_asset_sha256.tsv`.

| | MFF pure-tone | MFF bapa |
|---|---|---|
| Event codes | stad → 0, devt → 1 | stad → 0, devt → 1 (same mapping, `archive/configs/auditory_st_v1.yaml`) |
| Sounds (Events XML CELL labels) | 1000 Hz / 1500 Hz tones (41/41 records) | /ba/ / /pa/ syllables (29/29 records) |
| Standard → deviant (derived containers, no role swap seen) | 1000 Hz → 1500 Hz | ba → pa |
| p(deviant) | 0.150 | 0.151 |
| SOA median (p05) | 0.873 s (0.78) | 1.074 s (0.98) |
| Records / ids staged | 41 / 37 | 29 / 27 |
| Records / ids passing the ST1 gate (≥ 40 accepted per class, ≥ 4 blocks) | 35 / 33 | 25 / 24 |
| History field (since-last-deviant, 6 bins) | 28,162 / 28,416 accepted trials | 19,729 / 19,873 |

- Both lanes use 128 EGI channels (average reference) at 250 Hz with epoch [−200, 600) ms, the same time geometry as the
  private BDF lane. Arrays: `private/auditory_gx/GX_stage_001/epochs/M*.npz` (still on disk; independent of the deleted D1 arrays).
- Identity overlap after the gate: 8 identity groups have both lanes, all recorded on the same day. 16 are bapa-only and 25 are
  pure-tone-only, so person-disjoint transfer is possible. The old "7 complete pairs" counted only the earliest record per
  task; it dropped a group whose second same-day pure-tone record passes the gate. The 9th candidate pair fails the gate (39
  accepted deviants).
- Not verified: the ba/pa contrast is known from file names only; no audio was found. Whether standard/deviant roles are fixed
  for the 70 canonical records is inferred from 99 derived containers, which never swap roles.

## Decision

**Route: deviance-relation transfer (route A).** The two lanes share the *deviance relation*: the same stad/devt codes and
deviant probability, an oddball structure with a since-last-deviant history, and a fixed standard → deviant role. They do
**not** share sound identity: the sounds differ (tones vs syllables), and so does the SOA. The label shared across lanes is
therefore *deviant vs standard*, not *which sound*.

- **Direction (fixed):** source lane = MFF pure-tone, target lane = MFF bapa. Pure-tone is the larger lane (33 vs 24 gated
  ids), and its stimulus class matches the private BDF pure-tone lane. The reverse direction is not run.
- **Representation:** core-3 frozen backbones B0 / TCS / TNCE. TCS and TNCE use all three seeds (3401 R1, 3407 / 3413 R2),
  averaged within each child before contrasts; B0 is seed-free.
  - Three crops [0:100] / [50:150] / [100:200] at 250 Hz with crop-only resampling, as for the private BDF lane in
    `frozen.private_unit`. Each record gets the same per-channel z-score as the BDF loader.
  - CBraMod does not use channel names. Its positional encoding runs over the stored E1–E128 channel order, which is
    disclosed as a limitation.
- **Readout:** the private BDF readout contract, unchanged, used per slot and mixed with q0:
  - features: PCA64 fitted on the readout's own training rows, as in `frozen.pca_fit`;
  - current-sound probe: `private_current_time_v2.Probe`, i.e. standardise, L2 logistic C = 1, then positive-affine calibration;
  - history readout: the 6-bin since-last-deviant base rate, the B1 intercept and the EEG-offset logistic of `history_interface`.
  - Rows: all accepted trials with a known history bin. These trials define every endpoint.
- **Splits:** gated bapa ids go into 5 folds by sha256 rank of the anonymous identity key.
  - **Transfer** for fold f: fit on every gated pure-tone id *not* in bapa fold f (identity-disjoint); test on bapa fold f.
  - **Refit** for fold f: fit on the other bapa folds; test on fold f.
  - A child with several gated records in a lane contributes all of them, pooled within that lane.
- **Endpoints, per bapa child:**
  - primary: AUC (deviant vs standard) of the q0 mixture under transfer and under refit;
  - secondary: the history-conditional increment (bits/trial, EEG + history vs history-only B1) under both routes.
- **F_CROSS_STIM family (fixed now):** bapa children are the unit (n = 24), on the primary AUC endpoint. Inference is the
  sci_r1 identity bootstrap-t, B = 4000, with a family max-|T*|.
  - per arm: transfer − 0.5, refit − 0.5 and refit − transfer (9 members);
  - arm contrasts on transfer and on refit: TCS − B0 and TCS − TNCE (4 members);
  - total: 13 members.
  - The secondary endpoint gets the same 13-member layout as a separate, descriptive family.
- **Same-day pairs (8 children):** a finite-sample description only, with no inference. For each child it tabulates:
  - the child's own pure-tone within-lane AUC, from a 5-fold split over gated pure-tone ids;
  - the child's bapa transfer AUC;
  - the child's bapa refit AUC.
- **Interpretation rules, fixed now:**
  - Refit > 0.5 with transfer ≈ 0.5 means the relation is available in the representation, but the pure-tone readout does
    not carry over.
  - Transfer > 0.5 supports a reusable deviance readout across stimulus classes.
  - None of this is called zero-shot classification of sound identity.
  - Old GX results (cross-paradigm zero-shot 0.485–0.506 with GX encoders) were known when this was written. They do not
    change the route, which the semantics determine.

## Not done

- No route B, and no reverse direction.
- No unknown-task lane (its identity is unconfirmed and it is not bapa-compatible).
- No hdev/ldev pitch lanes.
- No ba1/ba4 single case.
- No new cohort.
- No retraining: frozen forward plus CPU readouts only. The 7 frozen extractions are about 2 GPU-hours on the core-3 backbones.
