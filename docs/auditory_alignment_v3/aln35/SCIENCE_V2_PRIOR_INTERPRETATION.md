# Content/time, private current/time and prior science — interpretation

Claude Code, 2026-10-20. First reading of three completed aggregates that had only coverage reports:
S34 content/time (180 units), S34 private current/time v2 (130 units) and prior science (300 targets).
Readouts: `SCIENCE_V2_READOUT.md`, `PRIOR_SCIENCE_READOUT.md` (this folder); every cell is in
`results/auditory_alignment_v3/aln35/science_readout_v1/` (science_v2 116,932 rows, prior 210,392 rows,
development 1,408 rows; Slurm step in 1047358, receipt `receipt.json`). No refit and no new bootstrap.

Marks follow each family's simultaneous band. Public numbers: matched − mismatch r (EEG-only within-person
segment-roll baseline subtracted). DTU = 3-seed mean (44 people); FAU 67 and Federici 86 people, seed 3401.
Window centers are overlapping 1-s access windows [c−400, c+600) ms, not neural latencies.

## 1. Public sound content and time

| Observation | Evidence | Status |
|---|---|---|
| All six sound attributes (env, onset, spec, flux, Ac, Lz) are readable from every trained model | Direct diagonal cells `+` (local/CBpre/CBrand/REVEpre × 6 attributes × 5 centers): DTU 120/120, FAU 101/120, Federici (env only) 15/20; none `−`. E.g. DTU env at 0 ms: local 0.145, CBpre 0.159, CBrand 0.142, REVEpre 0.153 | + |
| Residual attributes after the preceding declared features stay readable | Conditional + history-conditional diagonal cells `+`: DTU 119/120, FAU 82/120, Federici 4/20. DTU at 0 ms: onset 0.10–0.11, flux 0.085–0.098, spec ~0.05, Ac 0.04–0.06, Lz ~0.025; env beyond its own past 0.10–0.11 | + (descriptive residual target, not an independent-source claim) |
| Learned 1-s representations peak at center 0; the strict 20-ms raw reference peaks at center 200 | raw20 env DTU: 0.009 / 0.013 / **0.057** / 0.006 / 0.008 at −200…600; FAU 0.023 at 200 only | + (consistent with ~200 ms-lagged responses in the raw signal; still not a latency estimate) |
| Readout direction is time-specific | Train at 200 → test at 600: env −0.060 … −0.065 for all FMs and local (DTU, `−`); train 200 → test 0/400 positive | + / − |
| Architectures differ little in linear content | DTU env 0 ms: CBpre 0.159 vs local 0.145 vs CBrand 0.142; FAU CBpre 0.080 vs local 0.075 | no contrast family; descriptive |
| FAU and Federici follow DTU at lower levels | FAU env 0 ms 0.066–0.080; Federici env 0.073–0.149 by group | + |

The CB risk advantage (TRUE_FULL +0.14…+0.21 bits/query) is not mirrored by clearly more linearly readable
sound attributes; it may come from other properties of the representation or readout. This is an inference
from descriptive levels, not a tested contrast.

**Hearing groups (descriptive levels, no group-difference family in this aggregate):**
- DTU HI ≥ NH: env 0 ms 0.16–0.18 vs 0.13–0.14 across models.
- FAU CI < HA ≈ TH: 0.04–0.05 vs 0.08–0.10. FAU CI tracking has documented device-artifact limits.
- Federici CI < HC: CBpre 0.119 vs 0.149; HC-v (separate children) 0.148.

## 2. Private children: current sound, time, history (64 children; HA 55, NH 9)

Common source-ES logistic readout with positive-affine calibration (differs from the native readouts that give
0.545–0.553 in E_MULTI_SEED_RESULTS).

- **Full-window AUC 0.510–0.537**, all `+` vs 0.5. CS_SINGLE > NCE in every architecture (CBpre 0.537 vs 0.512;
  local 0.532 vs 0.518).
- **Time:** the FM pre-stimulus window is 0.494–0.501 (sanity check). The 0–200 and 200–400 ms windows carry the
  signal (0.501–0.521); 400–600 ms ≈ 0.50–0.508. Input-mask transfer is diagonal-dominant with weak off-diagonal
  transfer. Local/E_PUBLIC_TRANSFER pre windows are invalid (all-zero input correction).
- **History:** EEG added to the history model *lowers* log-score in every configuration
  (−0.001 … −0.004 bits/trial; several NH and FM cells `−`).
- **Personal output adaptation (rank 4, 0/5/20 steps):** AUC changes ≤ 0.007; 20 steps at 10% support raise NLL
  slightly; 30% support ≈ unchanged. Consistent with 1050758.
- **Development:** **0 of 1,088** coefficient cells (age, HA indicator; HA-only age and device-use duration;
  all endpoints) exclude 0. Stage means (≤2 mo n=14, 2–13 mo n=5, ≥13 mo n=36) show no consistent order.
- **NH vs HA:** NH AUC is descriptively higher in every configuration (e.g. local CS 0.556 vs 0.529) but NH n=9
  and this aggregate has no HA−NH contrast family; earlier direct contrasts were uncertain.

## 3. Public auditory prior (AP, XP, J*, XM vs scratch S; seed 3401)

- **Public content:** 0 of 960 arm − S diagonal cells are positive; 7 are negative (all CS_SINGLE objective,
  DTU/FAU). The prior does not make sound attributes more linearly readable.
- **Group differences in prior effects:** 11 of 45,728 cells exclude 0, scattered across datasets, arms, metrics
  and cells, with no consistent pattern.
- **Private, NCE:** full-window AUC AP +0.021, J* +0.017, XM +0.012 (all children `+`); history gain AP +0.0038.
  The unpaired control XM also helps, matching AP_WRONG_RESULTS_V2: a general-pretraining effect, not
  established as sound-pairing specific. CS: all ≈ 0.
- **Development:** 0 of 320 coefficient cells exclude 0.

## 4. What this changes

1. Sound content is broadly and stably readable in adults and children's public data; residual attributes and
   envelope beyond its own history remain readable. The open question is not *whether* sound is represented but
   which properties explain the CB risk advantage and the group differences.
2. Temporal organisation: learned models integrate across a ~1-s window; the strict local reference localises
   the raw signal around +200 ms; readout directions flip sign ~400 ms away from training.
3. Private current-sound information is small (AUC ≈ 0.51–0.54 common readout), confined to 0–400 ms, adds nothing
   beyond stimulus history in log-score, and shows no detectable association with age, device-use duration or
   stage. These are limits of the present representation/readout and n = 64, not evidence that development has
   no auditory correlate.
4. The public prior acts as general pretraining, not as a carrier of sound-attribute content.

## 5. Implications for next steps

- The CB-auditory × people-fraction experiment remains the most direct test of whether paired auditory
  pretraining can substitute for target people (content readouts do not answer it).
- For the private line, further encoder training is unlikely to move AUC; a different question (e.g. multi-trial
  integration within child, or a different endpoint) needs a design decision by the researcher.
- A direct group-difference family for public content (HI−NH, CI−HA/TH, CI−HC) is missing from science_v2 and
  could be computed from the existing per-identity outputs (CPU only) if the group question is pursued.
