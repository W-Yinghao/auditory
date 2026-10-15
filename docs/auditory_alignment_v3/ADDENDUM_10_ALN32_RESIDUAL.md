# ALN3 Addendum 10 — ALN3.2 wave 2b: trained residual with an epoch-0 candidate and cross-person selection (ALN32_RESIDUAL), 2026-10-14

**Status**: written before any of these rows, their probe or any ALN3.2 test value. Frozen (0444) with the code; sha256 in
`ALN32_IMPLEMENTATION_RECEIPT.md`.

**Basis**:
- ALN3.2 package docs/04 ("第二组"), docs/03 §4, and `configs/experiments.yaml` (ALN32_RESIDUAL).
- User instruction 2026-10-14: "能做的都做了".

## 0. What has been seen

- As ADDENDUM_09 §0.
- The old C residual: selected on the training participants' own held-out content, epoch 0 never a candidate, and every
  FAU/DTU variant worse than local.

## 1. Question

With the local map frozen and its untrained state kept as a candidate, does a trained residual from query-aligned FM
features lower true-query risk? Is that specific to pretrained weights and beyond a small branch with the same EEG access?

## 2. Rows (`plan_ext.jsonl` block 6)

- Per A_LOCAL `lag_local_tokens` full seed-3401 cell (25) × objective {NCE, CS_SINGLE} (base L0 of the same objective).
- Variants:
  - `residual_aligned_pretrained` × {cbramod, reve};
  - `residual_aligned_random` × {cbramod, reve};
  - `residual_small_capacity` (no FM).
- That is **250 rows**.
- `local_only_epoch0` is the base unit itself; it needs no new row and is the reference.

## 3. Model and training

- **Prediction**: u = normalise(u_base + r([base tokens, c])), where `ZeroResidualPrediction` (package reference, hidden 64)
  has a zero last layer. The base encoder and its fixed audio head are frozen; only r and the context branch c are trained.
  At initialisation u equals u_base exactly (checked in the probe).
- **Context branch** (input = the B_ALIGNED window [t − 0.4 s, t + 0.6 s), zero before the segment start):
  - aligned FM: frozen backbone (pretrained, or random initialisation with seed 3401), last-layer channel tokens →
    LayerNorm(E) → Linear(C·E → 64);
  - small capacity: a 2-layer temporal conv over the raw window (C → 32 → 32, kernel 5) → time mean → Linear(32 → 64).
- **Training data**: the training participants are split into the 5 fixed groups of ADDENDUM_09 (seed 20261014). Group 0 is
  the **inner development group**, fixed in advance; groups 1–4 train r.
- **Recipe**: AdamW, lr 1e-3, weight decay 1e-4. 32 segments × 8 anchors per step, the base objective (NCE or CS_SINGLE,
  temperature 0.1). 30 epochs. Resume every epoch.
- **Selection** (training side, cross-person). At epoch 0 (untrained) and after every epoch:
  - **dev risk**: the candidate cross-entropy of the development group's queries among the development pool. Score = the
    mean over 8 fixed grid anchors of u·v. The temperature is fitted on the training groups' early-stopping queries.
  - The checkpoint with the lowest dev risk is kept; ties go to the earlier epoch. Epoch 0 is a legal choice, meaning "no
    correction adopted".
  - Dev rank is recorded alongside. Test participants are never used.

## 4. Engineering probe (no performance gate)

FAU cell, NCE, `residual_aligned_pretrained` reve, 3 epochs. Checks:
- epoch-0 u = base u (max |Δ| ≤ 1e-6);
- the dev group is disjoint from the training groups;
- dev risk is recorded for epochs 0–3;
- training-path and evaluation-path u agree;
- the unit completes; GPU memory and time are recorded.

## 5. Analysis (`aln32_residual_interim.py`, written and synthetically tested before any result)

Per dataset × objective (× backbone where applicable). Positive = candidate lower true-query risk:

| Family | Reference → candidate |
|---|---|
| RS-VALUE | base L0 → each residual configuration (5) |
| RS-ATTRIB | `residual_aligned_random` → `residual_aligned_pretrained`; `residual_small_capacity` → `residual_aligned_pretrained` |

- The fraction of units whose selected epoch is 0 is reported per configuration. This is descriptive, not a result.
- "Complement from the pretrained representation" requires RS-VALUE pretrained I > 0 and both RS-ATTRIB members I > 0.
- RS-VALUE ≈ 0 with a high epoch-0 fraction reads as "no correction adopted". It is not complementarity and not a failure of
  local.
- Base L0 reads post-only EEG. The small-capacity branch has the same aligned access as the FM branch, so it is the access
  control.
