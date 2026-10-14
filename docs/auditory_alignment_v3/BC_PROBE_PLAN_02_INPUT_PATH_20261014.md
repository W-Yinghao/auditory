# B / C localisation probes — plan 02: FM input path (2026-10-14)

**Status**: written and frozen (0444) before the run. The sha256 is in `private/auditory_alignment_v3/probe_bc/code_sha256_at_freeze_02.txt`.
User instruction 2026-10-14: "go" (the input-path probe proposed after `BC_PROBE_RESULTS.md`).

This probe asks whether the stimulus-locked information that the local model reads is still present in the tensor the
foundation models receive. That tensor is the output of `foundation_adapter.Backbone.forward` before the network:
- FFT resampling of the whole 5.6 s context to 200 Hz;
- CBraMod: end zero-padding of 51 native samples, then × 0.15;
- REVE: clipping at ±15.

No model is trained. The probe adds no plan rows and sets no performance threshold. Data: training participants only; FAU
and DTU, subject fold 0, content fold 0, target `local` (the B cell of P1–P4 plus its DTU twin). Fixed rng 20261014: 300 fit
segments (every 4th grid query) and 160 early-stopping segments (every 2nd grid query).

Already seen: everything in `BC_PROBE_PLAN_20261014.md`, plus `BC_PROBE_RESULTS.md`.

## P5a · Linear readability of three input views (ridge → standardised target A(t))

| view | features for a query at t |
|---|---|
| F0 native | the cohort EEG (z-scored, 128 Hz) in [t, t + 0.6 s), i.e. the union of the `lag_local_tokens` lag windows (C × 77) |
| F1 CBraMod input | the 200 Hz adapter tensor (padded, resampled, × 0.15) in the same window (C × 120) |
| F2 REVE input | the 200 Hz adapter tensor (resampled, clipped) in the same window (C × 120) |

- **Fit**: ridge on the fit rows; λ = a · tr(XᵀX) / p with a from 1e-4 … 1e2 chosen on early-stopping half A.
- **Reported**: mean Pearson r over target dimensions on half B, at Δ = −3 … +3 grid steps.
- **Floor**: half B with targets from another segment (roll 1).
- **Position breakdown**: r on half B for queries in the first 0.5 s, the middle and the last 0.5 s of the segment. This
  shows edge effects of the FFT resampling and of the CBraMod padding.

## P5b · Input statistics

- Per-channel SD of the native view.
- Fraction of samples with |z| > 15 (REVE clipping).
- Relative RMS difference between the FFT-resampled tensor and a linear-interpolation resampling of the same context, by
  position (first 0.5 s, middle, last 0.5 s).

## P5c · Channel order

- FAU: each participant file's `channels` attribute, compared in order with `foundation_adapter.CHANNELS["fau"]` (the names
  REVE positions are drawn from).
- DTU: the channel names stored in the files, if any, compared with `CHANNELS["dtu"]`. If none are stored, this is reported.

## Reading (fixed now)

- **r(F1), r(F2) ≥ 0.9 · r(F0)** at Δ = 0, and above the floor: the adapter input preserves the information, and the loss
  happens inside the backbones (patch embedding / transformer / optimisation).
- **< 0.5 · r(F0)**: the input preparation loses it, a bug candidate. The position breakdown and the clip fraction indicate
  which step.
- **In between**: partial loss; reported as such.
- **Any FAU file whose channel order differs** from `CHANNELS["fau"]`: REVE positions are misassigned for those
  participants. This is a bug whatever r shows.
- A peak at Δ ≠ 0 for F1/F2 but not F0 would indicate a resampling time shift.

## Outputs

- `private/auditory_alignment_v3/probe_bc/probe_input.json` + log;
- a section appended to `docs/auditory_alignment_v3/BC_PROBE_RESULTS.md`.
