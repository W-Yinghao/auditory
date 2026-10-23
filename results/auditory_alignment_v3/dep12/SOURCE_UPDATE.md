# SOURCE_UPDATE — DEP12 intake (2026-10-23)

Package v1.2 baseline: 063bef5. Intake (`private/auditory_alignment_v3/dep12/work/intake.json`, git fetch at 2026-10-22 22:10 UTC) shows that the remote HEAD is still 063bef5.

Everything below was produced locally after publish_036 and has not been pushed. It is the current state of the server. Each item says whether it can be reused this round, and how. No item here was re-run because of an old gap.

## 1. Old gaps named in the package: current status

| Package item (status at 063bef5) | Current status | Action this round |
|---|---|---|
| ALN4.1 R2 private CE full FT, 29/30 (TCS seed3413 outer4 missing) | **Complete, 30/30.** B0, TCS and TNCE × seeds 3407/3413 × 5 folds, plus R1 | Reuse; no retraining |
| R2 full scientific families, support, cross-stimulus | **Complete:** all 13 families in `results/auditory_alignment_v3/aln41/r2/contrasts.json` (see §2) | Reuse as existing evidence |
| MindMix complete route A, 8/10, plus audit 8/10 | **Complete:** DTU 10/10 (`aln42/external_mindmix.py`, scored by `external_eval_v2.py`); FAU 10/10 (`paper/mindmix_fau.py`); mechanism audit v1 + appendum 20 + 20 units | Reuse; EXTERNAL_COMPARISON.md |
| MindMix missing folds cf1/sf3, sf4 | Complete (part of the 10/10 above) | — |

## 2. R2 families (3 seeds; simultaneous 95%; person = unit)

**Content** (frozen PCA64, q0 mixture, history-residual envelope r):

| Cohort | TCS−B0 | TCS−TNCE | TCS−GCS | TCS−WRONG |
|---|---|---|---|---|
| DTU | −0.0022 [−0.0096, 0.0051] | −0.0366 [−0.0479, −0.0252] | +0.0244 [0.0148, 0.0339] | +0.0025 [−0.0031, 0.0082] |
| FAU | **+0.0116 [0.0031, 0.0200]** | −0.0213 [−0.0300, −0.0125] | +0.0262 | +0.0116 [0.0062, 0.0169] |
| Private | +0.0013 [−0.0007, 0.0032] | — | — | — |

- DTU's TCS−WRONG (+0.0025) is no longer resolved at 3 seeds. At R1 it was +0.036, so the R1 gap shrank substantially at 3 seeds.

**Attention (utility, 20 s):**
- DTU: TCS−B0 −0.0143 [−0.036, 0.007]; TCS−TNCE +0.0065.
- FAU: TCS−B0 −0.0005; TCS−TNCE −0.0123.
- Nothing is resolved.

**Time:** TNCE loses more than TCS on the fixed W0→W2 readout in DTU (+0.0198 [0.0056, 0.0339]) and in the private data (+0.0145 [0.0004, 0.0287]). Refit recovery is not resolved.

**Private full FT AUC:**
- TCS−TNCE −0.0068 [−0.0133, −0.0002].
- TCS−B0 −0.0042 (not resolved).

**Age MAE improvement:** RAW−B0 +7.32 [1.30, 13.34]; RAW−TCS +5.51 [−0.03, 11.06]; B0−TCS −1.81 (not resolved).

**Personal support (δ and calibration, U10/U30):** every gain is about 0, in the 1e-4 to 1e-5 bits range.

**Cross-stimulus (BAPA, 24 children):** syllable AUC transfer and refit are both near 0.5 and unresolved for every arm.

## 3. Work done after publish_036 (local; reusable as existing evidence, labelled post hoc where it is)

All of this was done for manuscript v2. Details are in `docs/auditory_alignment_v3/paper/MANUSCRIPT_V2_EXPERIMENTS.md` and `results/auditory_alignment_v3/paper/manuscript_v2/TABLES.md`.

### External decoders, DTU/FAU, 20 s, 2 × 5 folds

| System | DTU accuracy | DTU NLL (bits) | FAU accuracy | FAU NLL (bits) |
|---|---|---|---|---|
| mTRF | 0.818 | 0.566 | 0.636 | 0.930 |
| VLAAI (PyTorch port, TF parity 3.3e-6) | 0.830 | 0.548 | 0.679 | 0.887 |
| Transformer-CLIP (official code re-trained on public SparrKULee, 71 listeners; released weights 404) | 0.803 | 0.618 | 0.636 | 0.949 |
| MindMix, complete system | 0.531 | 1.000 | 0.491 | 1.015 |

All four T2 families are complete, with members TCS−external.

### Post-hoc Table 2 sensitivities
- Training data swapped: about 1–4 percentage points.
- Context-matched EEG span [0.203, 4.75] s: mTRF −0.015, VLAAI −0.015.
- Scoring mTRF only at the 16 anchor times: removes about half of the gap to TCS (DTU 0.803 → 0.701; FAU 0.624 → 0.570).
- So **sparse 4 Hz scoring is a major part of the TCS-versus-decoder gap.** This anticipates the package's 152-anchor dense attention scoring.

### Encoders, Tables 3–5
- REVE and the MindMix EEG branch: frozen (event AUC, age, cross-stim) complete; full FT nearly complete (REVE 4/20 left at intake).
- The MindMix branch FT is complete.
- Personal support for these encoders is pending, until the REVE FT finishes.

### Table 6 matched alignment on the common backbone (3 seeds each)

| Arm | DTU envelope r | FAU history-residual r |
|---|---|---|
| THSIC (temporal HSIC) | 0.069 | 0.038 |
| W4 single-view, env | 0.089 | 0.042 |
| W4 single-view, ss | — | 0.026 |
| W4 single-view, sc | — | 0.034 |
| TCS (3 views) | 0.079 | 0.049 |
| CALRA recipe on CBraMod (W5) | — | — |

- CALRA recipe on CBraMod: frozen readout comparable to TCS on envelope, but it loses more on the fixed W0→W2 readout.

### MindMix mechanism
- **W5, CALRA on CBraMod:** train-mode ClipLoss is about 0.001 for real EEG, noise EEG and wrong audio alike. The cause is the dropout pattern shared within one CALRA call. In eval mode the representation is constant.
- **Complete released system, audit v1 + appendum, all 16 cells:**
  - CALRA dropout is neither necessary nor sufficient.
  - The deterministic key is the candidate audio passed through CALRA into the "EEG" output: retrieval follows the audio 1.0 and the EEG 0.
  - In train mode, wav2vec2 SpecAugment adds a further shared key.
- **W6, KUL AAD v2 (16 subjects):**
  - The official scorer gives 0.9987 accuracy, and also 0.9986 with the unattended stream as target and 0.9987 with noise EEG.
  - Blind symmetric scoring gives 0.50.

The package's §5 caution applies: "fusion permits an audio bypass" is a mechanism finding for this asset, not a claim about all CALRA.

### W7: fusion-free CS-dependence alignment
- Pre-registered and frozen 2026-10-22 19:48, after Tables 2–6 had been seen.
- **R, CS-dependence decision rule** on 16-anchor frozen features: at or below chance; R < ridge in every family.
- **Audit A:** for TCS and TNCE, real pairs sit only slightly above the permutation null, and noise EEG and wrong audio sit at the null. This means there is no EEG-independent dependence source.
- **Four GPU arms (RES / PRES / RES_PRES / CCS) and D v2:** running at intake.
- **Relation to DEP12:** W7 shares DEP12's measurement philosophy but uses the older 3-crop / 16-anchor geometry. It stays a separate pre-registered line; its results are context, not DEP12 confirmations.

## 4. What DEP12 reuses vs runs new

- **Reused** (each with its original protocol / commit / retrospective flag):
  - R1/R2 arms and families;
  - the CS atlas;
  - MindMix complete-system DTU/FAU results and the audit;
  - external decoders;
  - REVE and MindMix-branch encoders;
  - ALN3.4 local / CB / REVE assets, where `dep12/encoders.py` can serve them faithfully.
- **New** (package 02 §4–7):
  - E0;
  - 9 main and 2 diagnostic source models;
  - common measurement with 128-anchor panels and 199 nulls;
  - 152-anchor dense 20 s attention scoring;
  - private U0 G (history B1 versus history + EEG) and U10 four-policy selection;
  - the families F_MEASURE, F_ATTENTION, F_PRIVATE, F_SELECTION and F_EXTERNAL.
