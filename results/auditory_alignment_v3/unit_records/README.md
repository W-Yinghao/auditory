# ALN3 per-unit records (snapshot 2026-10-18 01:00 CEST)

One JSON record per completed ALN3 unit, written by the unit runners. Each dataset's records are in one archive, and each archive member is
byte-identical to the server file `private/auditory_alignment_v3/units/<id>.json`. `MANIFEST.tsv` lists every member with its experiment id,
dataset, family, seed, seed scope, status, size and sha256.

| archive | records | content |
|---|---|---|
| `dtu.tar.gz` | 3,223 | DTU (public; NH/HI adults) |
| `fau.tar.gz` | 3,165 | FAU/TUD (public; TH/HA/CI adults) |
| `federici.tar.gz` | 1,130 | Federici (public; CI children, incl. the phantom-head records) |
| `private_bdf.tar.gz` | 711 | private children's HA cohort (E families, R_PRIVATE_CALIBRATION) |

The ALN3 and ALN3.4 fleets are still running. This snapshot contains 8,229 main-runner records; it is not a declaration that the registered experiments are complete. Later authorized pushes may refresh it.

## What a record contains

- `experiment_id`, `row`: the frozen plan row, with family, dataset, seed, seed scope, folds and `spec`.
- `bound_row`, `dependency`: the resolved bases, donors and twins.
- `code_hash`, `code_group`, `runner`: the code identity.
- `status`, `device`: run outcome and the GPU used.
- Training trace:
  - `curve`;
  - selection fields: `selected_epoch`, `selected_dev_risk_bits`, `epoch0_selected`, `best_selection_score`, …;
  - `update_ledger` (ALN3.2 full-update runs);
  - timing and memory.
- `eval`: test metrics. Aggregates, plus `per_participant` entries keyed by the dataset's participant code: public subject codes for
  DTU / FAU / Federici, internal pseudonyms `child<N>` for the private cohort.

**Private cohort (`private_bdf`).** The researcher decided on 2026-10-16 to publish these records verbatim. Each child entry carries:
- `group` (HA / NH);
- `age_months` and `duration_months` (calendar age and hearing-aid wearing duration in months; not applicable for NH);
- `n` (trials);
- the per-child task scores (AUC, NLL / log-loss, Brier, history increment, calibration variants).

The records contain no names, identity keys or raw EEG/audio. Code, cache and checkpoint provenance paths can occur in execution metadata. The mapping from `child<N>` to persons is not published.

## Loading

```python
import json, tarfile
with tarfile.open('results/auditory_alignment_v3/unit_records/fau.tar.gz') as tar:
    records = [json.load(tar.extractfile(m)) for m in tar.getmembers() if m.isfile()]
```

Group-level results built from these records are in `docs/auditory_alignment_v3/` and `results/auditory_alignment_v3/`.

## ALN3.4 lane supplement

`aln34_lanes.tar.gz` contains 205 completed non-probe lane records at the later supplement snapshot; `ALN34_MANIFEST.tsv` records member hashes. Members are verbatim runner outputs. A lane may bundle several evaluations; these counts must not be added to participant n. Historical plans and corrected v2 plans retain their own identities.

- `adaptation_policy_v1`: 6
- `attention_transfer_v1`: 4
- `breadth_inner_v1`: 4
- `breadth_policy_v1`: 2
- `causal_filter_v1`: 10
- `cb_auditory_v1`: 2
- `content_time_v1`: 26
- `cs_episode_v1`: 2
- `data_inner_v1`: 71
- `episode_training_v1`: 3
- `learning_budget_v2`: 6
- `prior_science_v1`: 24
- `private_calibration_loo_v1`: 4
- `private_cb_factorial_v1`: 6
- `private_current_time_v1`: 26
- `private_episode_v1`: 1
- `private_episode_v2`: 4
- `strong_fusion_v1`: 4
