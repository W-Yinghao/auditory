# docs/13 science round 2 (SCI_R2) — preregistration, 2026-10-14

**Status**: frozen (0444) before any SCI_R2 computation on real data (synthetic tests only); sha256 in
`ALN32_IMPLEMENTATION_RECEIPT.md`.

**Basis**:
- ALN3.2 package docs/06 (common time panel, explicit sound features S2, groups) and `configs/experiments.yaml`
  (ALN32_SCIENCE_R2).
- SCI_R1_PREREG §1: S2 deferred; its core was fixed then as "lags −200…600 ms, held-out EEG prediction risk, training-side
  regularisation, nested feature families".
- User instruction 2026-10-14: "能做的都做了".

## 0. What has been seen

- Everything in SCI_R1_PREREG §0 and SCI_R1 results: lag curves, temporal generalisation, spatial patterns, S4 associations.
- The B/C, probe, D-lag and ALN3.2 wave results listed in their addenda.
- Never computed: any forward (stimulus → EEG) model, any nested feature increment, any common-ms-grid curve.

## 1. Questions

- **Q1 (S2, forward)**: in held-out participants, how much does each nested stimulus feature family add to the prediction of
  EEG, beyond the previous families?
- **Q2 (S1c, common time panel)**: on one absolute lag grid in ms with equal-width windows and a common envelope target, how
  does strict-local raw-EEG readability change with lag in FAU, DTU and Federici, and in their groups?
- **Q3 (band sensitivity)**: does Q2 for FAU/DTU change when their EEG is restricted to Federici's 2–8 Hz band?

## 2. Data, identities, folds

- **Cohorts**:
  - FAU: content folds 0/1 × subject folds 0–4;
  - DTU: content folds 0/1 × subject folds 0–4;
  - Federici: content fold 0 × subject folds 0–4.
  - Single-speaker segments only; the cohort loaders, folds, roles and segments are unchanged.
- **Identities** as SCI_R1 §2: Federici record → `subject_uid`, phantom excluded.
- Per identity: mean over its test units (content folds; TH-heldout identities are tested in every subject fold).
- Training uses the training participants of the subject fold (`train_participants`). Fit and early-stopping segments are
  pooled. Regularisation is chosen by grouped cross-validation over 5 participant groups (seed 20261014).
- Test participants are used only for the reported scores.

## 3. Q1 — nested forward models (S2)

- **Feature banks** (128 Hz, already aligned to the EEG in the cohort banks; all band-passed 1–8 Hz as in `prep_targets`):

  | Family | Features | Dims |
  |---|---|---|
  | env | broadband envelope (`Local` dimension 5) | 1 |
  | onset | half-wave rectified first difference of env | 1 |
  | spec | log-mel PCA-5 (`Local` dimensions 0–4) | 5 |
  | flux | L2 norm of the first difference of spec (spectral change in the PCA space) | 1 |
  | Ac | Whisper layers 1–2 PCA-5 (contextual, early) | 5 |
  | Lz | Whisper layer 27 PCA-5 (contextual, late) | 5 |

  F0 / voicing need a waveform-to-bank alignment check and are **pending**, not computed.
- **Models**: M1 = env; M2 = M1 + onset; M3 = M2 + spec; M4 = M3 + flux; M5 = M4 + Ac; M6 = M5 + Lz. Federici: M1 only (its
  cache holds a 2–8 Hz envelope only).
- **Forward ridge**: EEG(t), all channels, predicted from features at t − ℓ for ℓ ∈ [−200, +600] ms in samples
  (128 Hz: −26 … +77; 100 Hz: −20 … +60). Only time points whose whole lag range lies inside the segment are used.
  Features are z-scored on the training rows. α is chosen per model by grouped CV (mean channel Pearson r) on the grid
  {1e-3 … 1e4} × trace / p. Training rows: every 2nd sample.
- **Endpoint** per test identity: r = the mean over channels of Pearson(predicted, actual EEG) over the identity's test time
  points. Increments Δr_k = r(M_k) − r(M_{k−1}).
- **Labelling**: Ac / Lz increments are "contextual (Whisper) feature increments". They are never subtracted across
  separately trained models, and no language claim is made from them. No TRF peak criterion is used.

## 4. Q2 — common time panel (S1c)

- **Lag grid**: L ∈ {−200, −180, …, 560} ms, step 20 ms. Window [L, L + 40 ms): samples [round(L·fs/1000), + w), with
  w = 5 at 128 Hz (39.1 ms) and w = 4 at 100 Hz. Negative lags are controls; their readability can come from envelope
  autocorrelation or filtering and is not called leakage.
- **Target**: the envelope at t (FAU/DTU: `Local` dimension 5, 1–8 Hz; Federici: the 2–8 Hz cached envelope).
- **Readout**: ridge from the raw EEG window at t + L (C × w) to the envelope, α by grouped CV.
- **Endpoint**: per identity Pearson r on its test points. Only points whose window lies inside the segment are used.

## 5. Q3 — band-matched sensitivity

FAU/DTU EEG is band-passed 2–8 Hz (zero-phase FIR, `scipy.signal.firwin`, 129 taps at 128 Hz) and Q2 is repeated. The filter
is applied per segment with odd padding (`filtfilt`), because the bank concatenates recordings; only windows inside the
segment are scored. The original
1–20 Hz result stays primary. Window, target and band changes are recorded separately.

## 6. Statistics and reporting

- `sci_r1.stats` unchanged: identity-level bootstrap-t (B = 4,000), max-t bands for curves, family max-t for the nested
  increments within a cohort.
- **Groups**:
  - per-group levels and curves;
  - independent-group contrasts as in SCI_R1: FAU HA − TH, CI − TH, CI − HA; DTU HI − NH; Federici CI − HC, HC-v − HC.
  - Group contrasts are computed for M1 r, every Δr, and the Q2 curve (max-t band over lags).
- No group or method is selected by these results. Weak, null and reversed cells are reported. n is given per cell; cells
  with n < 5 report n only.
- **Interpretation**: an increment I > 0 means the feature family adds held-out EEG predictability beyond the earlier
  families for these stimuli, cohorts and preprocessing. It is not a claim about the neural code or about language. Curve
  shapes are readability under a fixed linear readout, not latencies of a mechanism.

## 7. Outputs

- `docs/auditory_alignment_v3/SCI_R2_RESULTS.md` (cohort and group tables, curve tables);
- `results/auditory_alignment_v3/sci_r2/` (aggregates);
- per-identity tables private.
- Code: `auditory_alignment_v3/sci_r2.py` (tasks) and `sci_r2_aggregate.py`, synthetically tested before the run.
- 25 CPU tasks, one per dataset × subject fold × content fold.
