# First returned ordinary/episode continuation bundle

2026-10-17T18:47:13.317464+02:00; CPU job1044405; `ALN34E_9258613073b62a3b`.

Source: dtu, cbramod, pretrained_full, seed3401, person fold0, content fold0.

Chosen by completion order, not efficacy. One fold/content/seed only, without population intervals. Equal-person risks in bits/query. Source/ordinary/episode share identities and query counts; native/unified stay separate. Every fixed candidate and both inner/outer ledgers are in the JSON. No frozen design or schedule is changed.

| Source stage | Regime | Updates | Source people | Support steps | Query anchors | Relative parameter change | Seconds |
|---|---|---:|---:|---:|---:|---:|---:|
| inner | episode | 100 | 24 | 300 | 6400 | 0.005772 | 27.4 |
| inner | ordinary | 100 | 24 | 300 | 6400 | 0.005772 | 27.5 |
| outer | episode | 100 | 34 | 300 | 6400 | 0.005022 | 27.3 |
| outer | ordinary | 100 | 34 | 300 | 6400 | 0.005021 | 27.3 |

## Whole-pipeline inner-person selected policies, applied to outer people

| Support | Readout | n | Ordinary choice | Episode choice | Ordinary R | Episode R | Benefit episode−ordinary |
|---|---|---:|---|---|---:|---:|---:|
| 0.1 | native | 10 | ordinary/5 | episode/5 | 6.47736 | 6.47745 | -9.009854e-05 |
| 0.1 | unified | 10 | ordinary/5 | episode/5 | 6.88130 | 6.88130 | -2.950224e-06 |
| 0.3 | native | 10 | ordinary/20 | episode/20 | 6.47012 | 6.47020 | -7.642570e-05 |
| 0.3 | unified | 10 | ordinary/20 | episode/20 | 6.87294 | 6.87297 | -2.223228e-05 |

Positive benefit means ordinary R minus episode R; it is not the sign of the loss difference. Both selected policies include the original source/0updates and support0steps.

## Fixed outer candidates (no test selection)

| Support | Steps | Readout | n | Source R | Ordinary100 R | Episode100 R | Risk benefit | Mismatch-gain change |
|---|---:|---|---:|---:|---:|---:|---:|---:|
| 0.1 | 0 | native | 10 | 6.45389 | 6.47879 | 6.47889 | -9.583492e-05 | -4.780769e-05 |
| 0.1 | 0 | unified | 10 | 6.86638 | 6.88162 | 6.88163 | -8.519400e-06 | -3.977278e-06 |
| 0.1 | 5 | native | 10 | 6.45287 | 6.47736 | 6.47745 | -9.009854e-05 | -5.237760e-05 |
| 0.1 | 5 | unified | 10 | 6.86615 | 6.88130 | 6.88130 | -2.950224e-06 | +1.145914e-06 |
| 0.1 | 20 | native | 10 | 6.47593 | 6.48871 | 6.48872 | -1.158245e-05 | -3.023283e-05 |
| 0.1 | 20 | unified | 10 | 6.87943 | 6.89191 | 6.89187 | +3.674263e-05 | +4.457299e-05 |
| 0.3 | 0 | native | 10 | 6.45389 | 6.47879 | 6.47889 | -9.583492e-05 | -4.780769e-05 |
| 0.3 | 0 | unified | 10 | 6.86638 | 6.88162 | 6.88163 | -8.519400e-06 | -3.977278e-06 |
| 0.3 | 5 | native | 10 | 6.45153 | 6.47603 | 6.47612 | -9.386395e-05 | -5.084026e-05 |
| 0.3 | 5 | unified | 10 | 6.86485 | 6.88003 | 6.88004 | -8.236347e-06 | -4.003688e-06 |
| 0.3 | 20 | native | 10 | 6.45231 | 6.47012 | 6.47020 | -7.642570e-05 | -1.419586e-04 |
| 0.3 | 20 | unified | 10 | 6.85913 | 6.87294 | 6.87297 | -2.223228e-05 | -2.236631e-05 |

The full panel and direct group-by-adaptation inference remain pending. Historical filtering and repeated use of the same cohort remain limitations.

Display precision updated by CPU job1044410: tiny differences use scientific notation. Numerical JSON unchanged (SHA256 `ab0ffc35b46594079ddeae9a2c13d1835c86dd94a4172e1a741361b874a34bb4`). Original rendering retained. [Weight-space diagnostic](FIRST_EPISODE_WEIGHT_DIAGNOSTIC.md).
