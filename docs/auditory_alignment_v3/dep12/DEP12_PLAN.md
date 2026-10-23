# DEP12: execution plan for the dependence package v1.2 (from 2026-10-23)

- **Package:** `docs/AUDITORY_DEPENDENCE_SERVER_PACKAGE_v1_2_20261022.zip` (sha256 `2c4245e6…a84fe`).
  - Unpacked read-only at `private/auditory_alignment_v3/dep12/package/`.
  - The package is the frozen research contract: docs 00–06, `configs/round.json`, `reference/`.
  - Read the package docs in the order 00 → 01 → 02 → 03 → 04 → 05 before implementing anything.
- **Researcher instruction (2026-10-23):** "看看能不能按这个方向做，完成所有规划的实验，尽可能完善。……只要对这个思路有用的实验，你都自己下判断，不用问我"
  - Any change of protocol or research question beyond the package is recorded in `DECISIONS.md` (this directory), with its reason, before the affected results exist.
- **Verified on the server (Slurm CPU, 1047358):**
  - `reference/verify_measurement.py`: 18/18 NumPy checks passed.
  - `reference/verify_training_objectives.py`: 10/10 Torch checks passed (torch 2.6.0+cu124).
  - Receipts are in `private/auditory_alignment_v3/dep12/work/`.
- **Intake** (`work/intake.json`): remote HEAD = local publish head = 063bef5. Everything after publish_036 is local and unpushed; see SOURCE_UPDATE.md.
- **Logical plan:** `work/round_plan.json` (29 units, 115,000 source updates).

## Ownership and modules

All new code lives in `auditory_alignment_v3/dep12/`. New files only; existing modules are never edited, because running fleet shims byte-check them.

| Owner | Modules | Package scope |
|---|---|---|
| Agent S (source) | `dep12/encoders.py` (shared API, first deliverable); `source_sampler.py`, `objectives.py` (byte copy of the package's `training_objectives_torch.py` plus thin wrappers), `trainer.py`, `devprobe.py`, `source_fleet.py`; shims `aln35/dep12_src_*_fleet.py`; `slurm/dep12_*.sbatch` | 02 §4–5.1, 03 §1–3, E0 selection, 9 main + 2 diagnostic models |
| Agent M (measurement, public) | `dep12/public_features.py`, `measure.py` (wraps the package's `dependence_measure.py`, byte copy), `panels.py`, `attention.py`, `public_fleet.py` | 02 §5.2, §6.1, optional §7.2; 03 §4.1–4.3, §4.5; F_MEASURE, F_ATTENTION |
| Agent P (private) | `dep12/private_features.py`, `private_use.py` (U0 G, strict twin), `selection.py` (U10, four policies), `private_fleet.py` | 02 §6.2, §7.1; 03 §4.4, §5; F_PRIVATE, F_SELECTION, private δ |
| Coordinator (me) | SOURCE_UPDATE.md, EXTERNAL_COMPARISON.md, `work/server_binding.json`, lane registration, aggregation, ROUND_REPORT.md, LIMITATIONS.md | 02 §3, 04, 05 |

## Shared interface: `dep12/encoders.py`

Agent S writes it first and documents it in `docs/auditory_alignment_v3/dep12/INTERFACES.md`. Agents M and P code against it.

- **`REGISTRY`:** encoder name → spec.
  - New-round encoders: `B0`; `cs_pair@<seed>`; `info_nce@<seed>`; `sigmoid@<seed>`; `raw_cs@3401`; `cs_pair_wrong@3401`.
  - Reused encoders, each flagged with a different input support or access: e.g. `aln41_TCS@<seed>`, local / full-CB / REVE assets, `MINDMIX_branch`.
  - Fields per spec: kind, checkpoint path, sha256, training mode, step, input-support description, data-access level.
- **`load(name, device)` returns an object with:**
  - `represent(x, channel_names, pad_mask)` → `U [N, D]`. Input `x [N, C, 200]` is float32: one 1 s container at 200 Hz, already natively cropped, resampled and padded by the caller per 03 §1.
  - What `represent` computes: the frozen backbone's predetermined layer, LayerNorm'd tokens in real channel/time order, flattened, L2-normalised. Never conditioned on candidate audio.
  - `meta`: layer, token shape, checkpoint sha256, mode.
- **Training-only projector:** exposed separately as `project(x, …)` for diagnostics only.
- **`B0`:** the zero-update Stage1 CBraMod snapshot that every new arm starts from; one weight hash for all.

## Paths

- **Records:** `private/auditory_alignment_v3/dep12/{source,public,private,selection,external}/`.
- **Checkpoints and feature caches:** `<private checkpoint storage>/auditory_alignment_v3/dep12/`.
- **Results:** `results/auditory_alignment_v3/dep12/`. Layout follows package 05 §1: `per_person.jsonl`, `contrasts.json/.md`, `predictions/`, `measurement/`, `selection/`, `run_receipts/`.
  - Only de-identified pseudonymous IDs. No raw EEG, no identity maps.
- **Status values per logical unit (04 §6):** `planned`, `reused`, `running`, `completed`, `blocked_technical`, `not_run_optional`.

## Rules (all agents)

- **Coordinator naming convention (hard requirement, checked by `maintain_fleet_v2/v3`):** a shim's `fleet_status()` must return `name` starting `c3_s35`, `lane` starting `s35_`, slots 1..2, `initial == []`, and `submit[0]` = `slurm/aln35_*.sbatch`. The first DEP12 public shims used `dep12_*` names and were rejected (technical_error, 01:25–01:52); fixed by v2 wrappers.

- Compute through Slurm only.
  - CPU: `srun --jobid=1047358 --overlap -n1 -c2 …`; that allocation has 4 CPUs and 16 GB in total and is shared, so run at most one step per agent at a time.
  - GPU: a manual smoke only if `squeue -u yinwang -h -t R,PD -o '%b|%j' | grep gpu | grep -c '|c3_'` ≤ 8. Production lanes go through the coordinator registry; agents return lane specs and the coordinator registers them, last, with ≤ 10 GPUs total.
- `/projects/EEG-foundation-model/auditory` is read-only.
- Never use scontrol. Never touch jobs that are not ours (`csqmi_*`, `v10*`, `n2m*`, `r22_*`, `no-shell`).
- No push, deletion or messages.
- No scientific effect gates. Weak, negative and unresolved results are results.
  - Only implementation, numeric, mapping or leakage errors block a path, and only the affected path.
- Freeze plans and protocol choices (0444) before the outputs they govern exist.
  - Record every deviation from the package in `DECISIONS.md` with its reason.
  - Results must state which choices were made after which results were seen.
