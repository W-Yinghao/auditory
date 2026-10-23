# EXTERNAL_COMPARISON — DEP12 (v0, 2026-10-23; existing results, before the DEP12 common query)

**Status:**
- Everything here is an existing result, retrospective relative to DEP12.
- Each result was obtained on the ext_common partition: DTU 44 / FAU 67 people, 2 content folds × 5 person folds, 20 s decision = mean of 4 consecutive 5 s segment margins, ties 0.5.
- The DEP12 common query has 152 dense anchors per 20 s and is frozen by Agent M. Once it exists, F_EXTERNAL is recomputed on it wherever predictions can be paired. Otherwise both the full-sample and intersection tables will be given (package 05 §3).

## 1. Systems, protocols and data access

| System | Model source | Target attention labels used? | Target parameter update | Protocol |
|---|---|---|---|---|
| MindMix complete (official code 98445f36, released fusion checkpoint, 509/511 tensors + mechanical wav2vec2 key rename) | released; official MultimodalRealTrainer, 50 epochs on target training people's attended cs segments | yes (training people) | full fine-tune per unit | unified blind order-symmetrised scorer (primary); official target-slot scorer reported separately (audit, KUL) |
| MindMix EEG branch (`eeg_model.*` of the released checkpoint, strict load) | released | used in Tables 3–5 (private) only; the public attention branch is to be served via `dep12/encoders.py` | frozen | common representation + readout (DEP12) |
| mTRF (backward, 0–500 ms lags) | fitted on target | yes: attended envelope of training people's cs segments | fitted | common integration |
| VLAAI (official TF model ported to PyTorch, parity 3.3e-6; released weights) | released, fine-tuned per unit | yes | fine-tune | common integration |
| Transformer-CLIP (official code; released weights unavailable (404), so re-trained on public SparrKULee, 71 listeners) | source re-train (no attention labels) + native envelope readout on target training people | yes (readout) | readout (+ FAU 31→64 adapter) | common integration |
| Proposed TCS / B0 / TNCE (ALN4.1 R1+R2) | source single-speaker (no attention labels) | no (readout fitted on training people's single-speaker data) | frozen + ridge readout | common integration, 16 anchors per 5 s |

## 2. Results (20 s; person mean; accuracy / NLL bits)

| System | DTU (n44) | FAU (n67) | FAU TH / HA / CI accuracy |
|---|---|---|---|
| VLAAI | 0.830 / 0.548 | 0.679 / 0.887 | 0.738 / 0.709 / 0.609 |
| mTRF | 0.818 / 0.566 | 0.636 / 0.930 | 0.701 / 0.680 / 0.546 |
| Transformer-CLIP | 0.803 / 0.618 | 0.636 / 0.949 | 0.692 / 0.664 / 0.569 |
| B0 (frozen + ridge) | 0.626 / 0.938 | 0.516 / 0.999 | 0.559 / 0.505 / 0.503 |
| TCS | 0.612 / 0.942 | 0.515 / 1.000 | 0.542 / 0.519 / 0.495 |
| TNCE | 0.605 / 0.955 | 0.528 / 0.997 | 0.542 / 0.544 / 0.499 |
| MindMix complete | 0.531 / 1.000 | 0.491 / 1.015 | 0.494 / 0.489 / 0.491 |

Frozen T2 families (simultaneous 95%, TCS minus system):

| TCS minus | DTU accuracy | FAU accuracy |
|---|---|---|
| mTRF | −0.206 | −0.121 |
| VLAAI | −0.218 | −0.164 |
| Transformer-CLIP | −0.191 | −0.121 |
| MindMix | +0.081 [+0.045, +0.117] | +0.025 [−0.002, +0.051] |

On NLL, TCS is better than MindMix on DTU (+0.058) and FAU (+0.016), and worse than the three decoders.

## 3. Sensitivities that bear on the DEP12 attention protocol (post hoc, frozen before computation)

- **Training data swapped between systems:** each moves by 1–4 points.
- **Context-matched span [0.203, 4.75] s:**

  | System | DTU | FAU |
  |---|---|---|
  | mTRF | 0.818 → 0.803 | 0.636 → 0.624 |
  | VLAAI | 0.830 → 0.816 | 0.679 → 0.664 |

- **mTRF scored only at the proposed system's 16 anchors:** DTU 0.701, FAU 0.570. This removes about half of the gap to TCS. Sparse scoring at 4 Hz is a major factor, which is why DEP12 uses dense 152-anchor scoring.

## 4. MindMix mechanism, audit (not a performance result)

Complete released system, DTU/FAU × released / fine-tuned × train / test side, all 16 cells agree:
- Eval-mode ClipLoss is about 0.002 × ln B.
- Retrieval follows a transplanted audio 1.0 and a transplanted EEG 0.
- CALRA dropout is neither necessary nor sufficient. The coupling that is necessary is the audio branch's realisation (wav2vec2, mainly SpecAugment).
- KUL (W6): the official target-slot scorer gives 0.9987, unchanged with the unattended stream as target and with noise EEG. The blind symmetric scorer gives 0.50.
- **Interpretation, per package 00 §5:** for this asset and scoring path, fusion lets the candidate audio bypass EEG. This is not a claim about all CALRA models. An EEG-only ablation alone would not show it; the transplant and split tests do.

## 5. Pending for v1

- F_EXTERNAL on the DEP12 common query:
  - cs_pair versus the MindMix complete route;
  - versus the MindMix EEG branch;
  - versus the linear envelope readout (fitted on training people);
  - versus local / CB / REVE wherever `dep12/encoders.py` can serve them.
- Same-query recomputation, or full-sample plus intersection tables.
- MindMix candidate-swap, wrong-trial, same-stimulus cross-listener and noise sensitivities on the common query, each interpreted separately.
