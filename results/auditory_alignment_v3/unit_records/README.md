# ALN3 per-unit records (snapshot 2026-10-16 02:15 CEST)

One JSON record per completed ALN3 unit, written by the unit runners. Each dataset's records are in one archive, and each archive member is
byte-identical to the server file `private/auditory_alignment_v3/units/<id>.json`. `MANIFEST.tsv` lists every member with its experiment id,
dataset, family, seed, seed scope, status, size and sha256.

| archive | records | content |
|---|---|---|
| `dtu.tar.gz` | 2,613 | DTU (public; NH/HI adults) |
| `fau.tar.gz` | 2,466 | FAU/TUD (public; TH/HA/CI adults) |
| `federici.tar.gz` | 826 | Federici (public; CI children, incl. the phantom-head records) |
| `private_bdf.tar.gz` | 547 | private children's HA cohort (E families, R_PRIVATE_CALIBRATION) |

The ALN3 fleet was still running at the snapshot (about 75 % of the active units done). Later pushes replace the archives with newer snapshots.

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

The records contain no names, dates, file paths or raw EEG. The mapping from `child<N>` to persons is not published.

## Loading

```python
import json, tarfile
with tarfile.open('results/auditory_alignment_v3/unit_records/fau.tar.gz') as tar:
    records = [json.load(tar.extractfile(m)) for m in tar.getmembers() if m.isfile()]
```

Group-level results built from these records are in `docs/auditory_alignment_v3/` and `results/auditory_alignment_v3/`.
