# ALN3 Addendum 06 — query-aligned foundation-model readout (B_ALIGNED), 2026-10-14

**Status**: written before any B_ALIGNED unit or probe ran. Frozen (0444) together with the code; sha256 values in
`IMPLEMENTATION_RECEIPT.md` §11. User instruction 2026-10-14: "做你觉得所有该做的，并push". The registration follows the
pre-written reading of `BC_PROBE_PLAN_03_ALIGNED_TOKENS_20261014.md`: aligned patching recovers the information, so the
next step is a registered query-aligned B variant.

## 0. What has been seen

- Everything listed in ADDENDUM_05 §0.
- The B/C interim results (`B_DENSE_READOUT_RESULTS.md`, `C_COMPLEMENT_RESULTS.md`) and the QC notes.
- Probe results P0–P6 (`BC_PROBE_RESULTS.md`). In particular, on DTU training participants, frozen query-aligned tokens keep
  0.75–0.97 of the raw same-window linear readability; FAU was underpowered.
- No B_ALIGNED test value exists.

## 1. Why a new variant, not a fix

B_DENSE reads tokens of a fixed patch grid over the 5.6 s context; a query at t uses the patches around t. P6 showed that
these unaligned tokens carry essentially no linear stimulus information at the 20 ms grid, while a patch aligned with the
query does. B_ALIGNED changes only that interface. The B_DENSE units stay as registered; they are not re-run or replaced.

## 2. Model (code group `aligned`: `fm_aligned.py`, `run_aligned.py`)

- **Input per query t** (in samples from the segment start): the cohort EEG in [t − 0.4 s, t + 0.6 s), zero where it lies
  before the segment start. That is 128 native samples at 128 Hz (FAU, DTU) and 100 at 100 Hz (Federici). The adapter
  (`foundation_adapter.Backbone`, unchanged) resamples it to 200 Hz, i.e. one 1 s patch.
  - The window ends at the local models' lag-access limit (t + 0.6 s ≤ segment end + 0.6 s).
  - It starts at or after the segment start, so the information stratum stays `foundation_context`, as in B_DENSE.
- **Readout `aligned_patch_linear`**: channel tokens of the single patch [C, E] → LayerNorm(E) → flatten → Linear(C·E → d = 32)
  → L2-normalised, in the same fixed target space as B_DENSE and A_LOCAL.
- **Recipe**: the B_DENSE recipe unchanged:
  - learning rates `fm_dense.LR`, epochs `fm_dense.EPOCHS`;
  - head warm-up, top-down unfreezing, layer-wise decay 0.75, AdamW with weight decay 1e-4;
  - `DenseBatcher` rows (32 segments × 8 queries);
  - the same early-stopping content, checkpoint rule min(own − mismatched), and resume.
- **Evaluation**: `ev2.evaluate_continuous` with representations computed per grid query from its own aligned patch
  (`AlignedReps`); same candidate pools, readouts (unified, native), risks and attention 2AFC as B_DENSE.

## 3. Rows (`plan_ext.jsonl` block 3, ids `ALN3X_<sha16>`)

- For every seed-3401 B_DENSE row with objective NCE and readout `channel_phase_linear` (its interface twin): one
  B_ALIGNED row with the same dataset, folds, seed, backbone, adaptation and target, and readout `aligned_patch_linear`.
- That is 2 backbones × 5 adaptations × 25 cells (FAU 10, DTU 10, Federici 5) = **250 rows**.
- Each id is sha256("B_ALIGNED" + spec + base id)[:16], as for block 1. `base_plan_row` points to the twin.
- CS_SINGLE and the seed panel are not registered now. Per docs/12 the FM readout comparisons fix NCE first; CS or seeds are
  added only if a CS-specific or stability claim is made.

## 4. Engineering probe before the fleet (no performance gate)

One FAU unit (reve `pretrained_frozen`) and one Federici unit (cbramod `random_full`), each with 2 epochs, in the scratch
directory. Checks:
- the unit completes and its record carries the B_DENSE fields plus `readout = aligned_patch_linear`;
- the training-path and evaluation-path representations agree (max |Δu| ≤ 1e-4) on the same queries;
- the aligned window equals the cohort EEG slice and is zero before the segment start;
- peak GPU memory fits a V100-16 GB;
- seconds per epoch and per evaluation are recorded.

## 5. Analysis (seed 3401, NCE; identical machinery to ADDENDUM_05)

Endpoints, identities, statistics and sign convention as ADDENDUM_05 §2–§3 and §6. Families are per dataset × backbone:

| Family | Members | Reference → candidate |
|---|---|---|
| AL-LOCAL | 5 | A_LOCAL `lag_local_tokens` full → B_ALIGNED at each adaptation |
| AL-INTERFACE | 5 | B_DENSE `channel_phase_linear` (same backbone, adaptation, NCE) → B_ALIGNED |
| AL-INIT | 4 | B_ALIGNED `random_full` → `pretrained_{frozen, peft, partial, full}` (full = initialization contrast, others recipe) |
| AL-ADAPT | 3 | B_ALIGNED `pretrained_frozen` → `pretrained_{peft, partial, full}` |

**Interpretation grid** (simultaneous interval I):
- AL-INTERFACE I > 0: the aligned interface lowers true-query risk vs the fixed-grid interface.
- AL-LOCAL I > 0: this FM configuration beats the local model; I < 0: the local model is better.
- AL-INIT `pretrained_full − random_full` I > 0: pretraining-prior benefit under matched full update.
- Contains 0: not resolved.

The same forbidden-claims list as ADDENDUM_05 §7 applies. In addition: no statement about C or D from B_ALIGNED alone.

The analysis code is `auditory_alignment_v3/aligned_interim.py`, reusing the `bc_interim` functions. It is written and
tested on synthetic data before any B_ALIGNED aggregate is computed. The analysis runs once every row is complete.

## 6. What follows (not registered here)

- Whether to re-register the C complement with an aligned context branch, and the D FM/complement arms on aligned
  configurations, is decided after the B_ALIGNED results, in a separate addendum.
- The families on hold stay on hold until then.

## 7. Engineering

- New files only; no hashed file is edited.
- `registry.py`: group `aligned`, family `B_ALIGNED`.
- `run.py`: runner `run_aligned`.
- `make_queue.py`: B_ALIGNED on the FM queue (weight 1000).
- `ckpt_offload.py`: B_ALIGNED in `NO_DEPS`; the daemon is restarted.
- `plan_ext.jsonl`: block 3 appended by `private/auditory_alignment_v3/make_plan_ext_block3.py`. It verifies that the first
  1,250 rows are byte-identical before appending.
