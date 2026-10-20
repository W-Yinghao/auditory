# ALN3.5 support / episode / matched updates / true-risk selection

Job 1050005; snapshot 2026-10-19T19:49:27.055503+00:00; **interim**.

Only completed production records enter. Engineering probes and old blocked episode execution IDs do not count.

| Work | Complete / expected scientific units |
|---|---:|
| support | 30 / 30 |
| episode | 38 / 60 |
| matched | 87 / 120 |
| selection | 27 / 60 |

Expected independent people: DTU 44; private 64. U10 averages five fixed support draws within each person; DTU then requires both registered content folds. Outer person fold is membership, not a repeated measurement.

The exploratory intervals use 4,000 whole-person hearing-group-stratified draws, fixed original SE and max-|z*|. No aggregate CI subtraction, result selection, performance gate, or seed-by-person sample inflation.

| True-query NLL family | Paired people / expected | Complete units / expected |
|---|---:|---:|
| episode_fixed20__dtu__CBpre__native__pressure100__nll_bits | 44 / 44 | 10 / 10 |
| episode_fixed20__dtu__CBpre__native__pressure20__nll_bits | 44 / 44 | 10 / 10 |
| episode_fixed20__dtu__CBpre__unified__pressure100__nll_bits | 44 / 44 | 10 / 10 |
| episode_fixed20__dtu__CBpre__unified__pressure20__nll_bits | 44 / 44 | 10 / 10 |
| episode_fixed20__dtu__local__native__pressure100__nll_bits | 26 / 44 | 8 / 10 |
| episode_fixed20__dtu__local__native__pressure20__nll_bits | 26 / 44 | 8 / 10 |
| episode_fixed20__dtu__local__unified__pressure100__nll_bits | 26 / 44 | 8 / 10 |
| episode_fixed20__dtu__local__unified__pressure20__nll_bits | 26 / 44 | 8 / 10 |
| episode_fixed20__private_bdf__CBpre__linear__pressure100__nll_bits | 13 / 64 | 1 / 5 |
| episode_fixed20__private_bdf__CBpre__linear__pressure20__nll_bits | 13 / 64 | 1 / 5 |
| episode_fixed20__private_bdf__CBpre__native__pressure100__nll_bits | 13 / 64 | 1 / 5 |
| episode_fixed20__private_bdf__CBpre__native__pressure20__nll_bits | 13 / 64 | 1 / 5 |
| episode_fixed20__private_bdf__local__linear__pressure100__nll_bits | 0 / 64 | 0 / 5 |
| episode_fixed20__private_bdf__local__linear__pressure20__nll_bits | 0 / 64 | 0 / 5 |
| episode_fixed20__private_bdf__local__native__pressure100__nll_bits | 0 / 64 | 0 / 5 |
| episode_fixed20__private_bdf__local__native__pressure20__nll_bits | 0 / 64 | 0 / 5 |
| episode_selected__dtu__CBpre__native__pressure100__nll_bits | 44 / 44 | 10 / 10 |
| episode_selected__dtu__CBpre__native__pressure20__nll_bits | 44 / 44 | 10 / 10 |
| episode_selected__dtu__CBpre__unified__pressure100__nll_bits | 44 / 44 | 10 / 10 |
| episode_selected__dtu__CBpre__unified__pressure20__nll_bits | 44 / 44 | 10 / 10 |
| episode_selected__dtu__local__native__pressure100__nll_bits | 26 / 44 | 8 / 10 |
| episode_selected__dtu__local__native__pressure20__nll_bits | 26 / 44 | 8 / 10 |
| episode_selected__dtu__local__unified__pressure100__nll_bits | 26 / 44 | 8 / 10 |
| episode_selected__dtu__local__unified__pressure20__nll_bits | 26 / 44 | 8 / 10 |
| episode_selected__private_bdf__CBpre__linear__pressure100__nll_bits | 13 / 64 | 1 / 5 |
| episode_selected__private_bdf__CBpre__linear__pressure20__nll_bits | 13 / 64 | 1 / 5 |
| episode_selected__private_bdf__CBpre__native__pressure100__nll_bits | 13 / 64 | 1 / 5 |
| episode_selected__private_bdf__CBpre__native__pressure20__nll_bits | 13 / 64 | 1 / 5 |
| episode_selected__private_bdf__local__linear__pressure100__nll_bits | 0 / 64 | 0 / 5 |
| episode_selected__private_bdf__local__linear__pressure20__nll_bits | 0 / 64 | 0 / 5 |
| episode_selected__private_bdf__local__native__pressure100__nll_bits | 0 / 64 | 0 / 5 |
| episode_selected__private_bdf__local__native__pressure20__nll_bits | 0 / 64 | 0 / 5 |
| matched_U__dtu__CBpre__native__nll_bits | 0 / 44 | 10 / 20 |
| matched_U__dtu__CBpre__unified__nll_bits | 0 / 44 | 10 / 20 |
| matched_U__dtu__CBrand__native__nll_bits | 0 / 44 | 8 / 20 |
| matched_U__dtu__CBrand__unified__nll_bits | 0 / 44 | 8 / 20 |
| matched_U__dtu__local__native__nll_bits | 0 / 44 | 9 / 20 |
| matched_U__dtu__local__unified__nll_bits | 0 / 44 | 9 / 20 |
| support__dtu__CBpre__native__nll_bits | 44 / 44 | 10 / 10 |
| support__dtu__CBpre__unified__nll_bits | 44 / 44 | 10 / 10 |
| support__dtu__local__native__nll_bits | 44 / 44 | 10 / 10 |
| support__dtu__local__unified__nll_bits | 44 / 44 | 10 / 10 |
| support__private_bdf__CBpre__linear__nll_bits | 64 / 64 | 5 / 5 |
| support__private_bdf__CBpre__native__nll_bits | 64 / 64 | 5 / 5 |
| support__private_bdf__local__linear__nll_bits | 64 / 64 | 5 / 5 |
| support__private_bdf__local__native__nll_bits | 64 / 64 | 5 / 5 |
| true_risk_selection__dtu__CBpre__native__EEG100__nll_bits | 44 / 44 | 10 / 10 |
| true_risk_selection__dtu__CBpre__native__EEG50__nll_bits | 0 / 44 | 0 / 10 |
| true_risk_selection__dtu__CBpre__unified__EEG100__nll_bits | 44 / 44 | 10 / 10 |
| true_risk_selection__dtu__CBpre__unified__EEG50__nll_bits | 0 / 44 | 0 / 10 |
| true_risk_selection__dtu__CBrand__native__EEG100__nll_bits | 26 / 44 | 8 / 10 |
| true_risk_selection__dtu__CBrand__native__EEG50__nll_bits | 0 / 44 | 0 / 10 |
| true_risk_selection__dtu__CBrand__unified__EEG100__nll_bits | 26 / 44 | 8 / 10 |
| true_risk_selection__dtu__CBrand__unified__EEG50__nll_bits | 0 / 44 | 0 / 10 |
| true_risk_selection__dtu__local__native__EEG100__nll_bits | 34 / 44 | 9 / 10 |
| true_risk_selection__dtu__local__native__EEG50__nll_bits | 0 / 44 | 0 / 10 |
| true_risk_selection__dtu__local__unified__EEG100__nll_bits | 34 / 44 | 9 / 10 |
| true_risk_selection__dtu__local__unified__EEG50__nll_bits | 0 / 44 | 0 / 10 |

All signed estimates, simultaneous intervals, nonregular reasons and missing cells are in summary.json. Positive NLL/Brier/rank improvement means reference minus candidate; AUC/top1/mismatch-gain use candidate minus reference. Wrong-query risk is a diagnostic with its own signed value, not an automatic criterion of improvement.

Private support rank4 is the output adapter; private episode rank4 is the spatial input adapter. Their effects are separate. The shared direct sample guard inherits whole-record offline preprocessing; it does not establish causal preprocessing isolation. Current task-specific inner sources exclude the selected inner people, using source-ES content.

Validation issues: 0. Any invalid unit/pair is reported and excluded from its dependent inference; other registered work continues. No missing value is replaced by a synthetic result.
