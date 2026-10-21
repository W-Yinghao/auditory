# ALN3 per-unit records (snapshot 2026-10-18 20:09 CEST)

One JSON record per completed ALN3 unit, written by the unit runners. Each dataset's records are in one archive, and each archive member is
byte-identical to the server file `private/auditory_alignment_v3/units/<id>.json`. `MANIFEST.tsv` lists every member with its experiment id,
dataset, family, seed, seed scope, status, size and sha256.

| archive | records | content |
|---|---|---|
| `dtu.tar.gz` | 3,353 | DTU (public; NH/HI adults) |
| `fau.tar.gz` | 3,209 | FAU/TUD (public; TH/HA/CI adults) |
| `federici.tar.gz` | 1,286 | Federici (public; CI children, incl. the phantom-head records) |
| `private_bdf.tar.gz` | 871 | private children's HA cohort (E families, R_PRIVATE_CALIBRATION) |

The ALN3 and ALN3.4 fleets are still running. This snapshot contains 8,719 main-runner records; it is not a declaration that the registered experiments are complete. Later authorized pushes may refresh it.

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

## ALN3.4 lane supplement — publish_032

The 4 independently readable `aln34_lanes_032_*.tar.gz` parts contain 1269 completed non-probe records at 2026-10-18T20:10:53.660559+02:00. `ALN34_MANIFEST_032.tsv` maps every member to its archive and SHA256. Every member is byte-identical to the frozen source record, with no omissions or duplicates.

The previous `aln34_lanes.tar.gz` and `ALN34_MANIFEST.tsv` remain the publish_030 historical snapshot. The `aln34_lanes_031_*.tar.gz` parts and `ALN34_MANIFEST_031.tsv` remain the publish_031 snapshot. Do not combine releases as independent observations. A record can bundle several evaluations; reused v1/v2 records and seeds never increase independent participant n.

- `adaptation_policy_v1`: 31
- `attention_transfer_v1`: 51
- `breadth_budget_v1`: 4
- `breadth_episode_v1`: 12
- `breadth_fusion_v1`: 6
- `breadth_inner_v1`: 37
- `breadth_policy_v1`: 15
- `causal_filter_v1`: 10
- `cb_auditory_v1`: 20
- `content_time_v1`: 180
- `cs_episode_v1`: 22
- `data_inner_v1`: 198
- `episode_training_v1`: 20
- `learning_budget_v2`: 27
- `prior_private_loo_v1`: 71
- `prior_science_v1`: 300
- `private_calibration_loo_v1`: 4
- `private_cb_factorial_v1`: 40
- `private_current_time_v1`: 26
- `private_current_time_v2`: 130
- `private_episode_v1`: 1
- `private_episode_v2`: 44
- `strong_fusion_v1`: 20

## Lane supplement — publish_033

The 4 independently readable `lanes_033_*.tar.gz` parts contain 1429 completed non-probe records frozen at 2026-10-20T10:29:35.059006+02:00; `LANES_MANIFEST_033.tsv` maps every member to its part and SHA256. Members are byte-identical to the server records.

- Members without a prefix are ALN3.4 lane records that were **not** already published byte-identically in the publish_030/031/032 lane snapshots (new completions or changed records). The complete ALN3.4 lane set at this snapshot is the publish_032 parts plus these members; where a member name occurs in several releases, the latest release is the current record.
- Members under `aln35/` are ALN3.5 lane records (all completed, non-probe). Server-only support/query geometry bindings are not included; plans publish their hash.

A record can bundle several evaluations; records, releases, seeds and reused results never increase independent participant n.

- `adaptation_policy_v1`: 89
- `aln35/apwrong_v1`: 53
- `aln35/episode_lineage_v2`: 2
- `aln35/episode_pressure_v1`: 58
- `aln35/fusion`: 36
- `aln35/matched_updates_v1`: 120
- `aln35/support_coverage_v1`: 30
- `aln35/true_risk_selection_v1`: 60
- `attention_transfer_v1`: 109
- `breadth_budget_v1`: 56
- `breadth_episode_v1`: 28
- `breadth_fusion_v1`: 9
- `breadth_inner_v1`: 240
- `breadth_policy_v1`: 25
- `cb_auditory_v1`: 124
- `cs_episode_v1`: 18
- `data_inner_v1`: 187
- `episode_training_v1`: 60
- `learning_budget_v2`: 70
- `prior_private_loo_v1`: 19
- `private_cb_factorial_v1`: 20
- `private_episode_v2`: 6
- `strong_fusion_v1`: 10

## Lane supplement — publish_034

The 1 independently readable `lanes_034_*.tar.gz` parts contain 269 completed non-probe records frozen at 2026-10-20T19:58:55.466671+02:00; `LANES_MANIFEST_034.tsv` maps every member to its part and SHA256. Members are byte-identical to the server records.

- Members without a prefix are ALN3.4 lane records and members under `aln35/` are ALN3.5 lane records that were **not** already published byte-identically in the publish_030/031/032/033 lane snapshots (new completions or changed records; member name and SHA256 compared). The complete lane set at this snapshot is the earlier parts plus these members; where a member name occurs in several releases, the latest release is the current record. Server-only support/query geometry bindings are not included; plans publish their hash.

A record can bundle several evaluations; records, releases, seeds and reused results never increase independent participant n.

- `aln35/cbaud_people_v1`: 20
- `aln35/episode_pressure_s3407_v1`: 10
- `breadth_budget_v1`: 6
- `breadth_inner_v1`: 24
- `data_inner_v1`: 195
- `learning_budget_v2`: 14

## Lane supplement — publish_035

The 1 independently readable `lanes_035_*.tar.gz` parts contain 398 completed non-probe records frozen at 2026-10-21T11:53:17.929248+02:00; `LANES_MANIFEST_035.tsv` maps every member to its part and SHA256. Members are byte-identical to the server records, except that in publish_035 members the private checkpoint-storage root is replaced by the established placeholder `<private checkpoint storage>` (as in published plans; per-member source/published SHA256 in `results/auditory_alignment_v3/publication_035/LANE_MEMBER_DERIVATIONS.json`).

- Members without a prefix are ALN3.4 lane records; members under `aln35/`, `aln36/` and `aln41/` are ALN3.5, ALN3.6 and ALN4.1 lane records (R2 lanes in progress) that were **not** already published byte-identically in the publish_030-034 lane snapshots (new completions or changed records; member name and SHA256 compared). The complete lane set at this snapshot is the earlier parts plus these members; where a member name occurs in several releases, the latest release is the current record. Server-only support/query geometry bindings are not included; plans publish their hash.

A record can bundle several evaluations; records, releases, seeds and reused results never increase independent participant n.

- `aln36/fau_group_v1`: 12
- `aln36/private_features_v1`: 10
- `aln36/private_readout_v1`: 15
- `aln36/public_features_v1`: 52
- `aln36/public_readout_v1`: 52
- `aln36/r2_s3407/apwrong_v1`: 1
- `aln36/r2_s3407/fau_group_v1`: 12
- `aln36/r2_s3407/public_features_v1`: 51
- `aln41/frozen_v1`: 25
- `aln41/private_ft_v1`: 15
- `aln41/r2/seed3407/private_ft_v1`: 2
- `aln41/r2/seed3407/source_v1`: 2
- `aln41/readout_v1`: 25
- `aln41/source_v1`: 10
- `breadth_budget_v1`: 9
- `breadth_inner_v1`: 56
- `data_inner_v1`: 10
- `learning_budget_v2`: 39

## Lane supplement — publish_036

The 1 independently readable `lanes_036_*.tar.gz` parts contain 194 completed non-probe records frozen at 2026-10-22T00:46:34.659337+02:00; `LANES_MANIFEST_036.tsv` maps every member to its part and SHA256. Members are byte-identical to the server records, except that in publish_036 members the private checkpoint-storage root is replaced by the established placeholder `<private checkpoint storage>` (as in published plans; per-member source/published SHA256 in `results/auditory_alignment_v3/publication_036/LANE_MEMBER_DERIVATIONS.json`).

- Members without a prefix are ALN3.4 lane records; members under `aln35/`, `aln36/`, `aln41/`, `aln42/` and `paper/` are ALN3.5, ALN3.6, ALN4.1, ALN4.2 and paper-line (MindMix audit) lane records (lanes in progress) that were **not** already published byte-identically in the publish_030-035 lane snapshots (new completions or changed records; member name and SHA256 compared). The complete lane set at this snapshot is the earlier parts plus these members; where a member name occurs in several releases, the latest release is the current record. Server-only support/query geometry bindings are not included; plans publish their hash.

A record can bundle several evaluations; records, releases, seeds and reused results never increase independent participant n.

- `aln36/r2_s3407/apwrong_v1`: 10
- `aln36/r2_s3407/private_features_v1`: 10
- `aln36/r2_s3407/private_readout_v1`: 10
- `aln36/r2_s3407/public_features_v1`: 1
- `aln36/r2_s3407/public_readout_v1`: 52
- `aln41/r2/seed3407/frozen_v1`: 20
- `aln41/r2/seed3407/private_ft_v1`: 13
- `aln41/r2/seed3407/source_v1`: 2
- `aln41/r2/seed3413/frozen_v1`: 20
- `aln41/r2/seed3413/private_ft_v1`: 14
- `aln41/r2/seed3413/source_v1`: 4
- `aln42/external_v1`: 8
- `aln42/source_diag_v1`: 4
- `breadth_inner_v1`: 18
- `paper/mindmix_audit_v1`: 8
