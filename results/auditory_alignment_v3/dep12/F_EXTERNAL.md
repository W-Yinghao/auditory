# DEP12 F_EXTERNAL — CS-pair vs external systems on the same 20 s queries

Positive = CS-pair higher 20 s accuracy. CS-pair = person mean over seeds 3401/3407/3413. B = 10,000, simultaneous 95%.

## F_EXTERNAL:dtu:readout_b — complete, n 44/44

| member | estimate | simultaneous 95% |
|---|---|---|
| cs_pair-mTRF | -0.2083 | [-0.2485, -0.1680] |
| cs_pair-VLAAI | -0.2205 | [-0.2668, -0.1742] |
| cs_pair-TCLIP | -0.1934 | [-0.2330, -0.1539] |
| cs_pair-MindMix_complete | +0.0781 | [+0.0412, +0.1151] |
| cs_pair-MindMix_branch | +0.0216 | [-0.0151, +0.0583] |

## F_EXTERNAL:dtu:dependence_a — complete, n 44/44

| member | estimate | simultaneous 95% |
|---|---|---|
| cs_pair-mTRF | -0.2673 | [-0.3054, -0.2291] |
| cs_pair-VLAAI | -0.2795 | [-0.3232, -0.2357] |
| cs_pair-TCLIP | -0.2524 | [-0.2948, -0.2101] |
| cs_pair-MindMix_complete | +0.0191 | [-0.0130, +0.0512] |
| cs_pair-MindMix_branch | -0.0016 | [-0.0299, +0.0267] |

## F_EXTERNAL:fau:readout_b — complete, n 67/67

| member | estimate | simultaneous 95% |
|---|---|---|
| cs_pair-mTRF | -0.1121 | [-0.1463, -0.0778] |
| cs_pair-VLAAI | -0.1550 | [-0.1859, -0.1241] |
| cs_pair-TCLIP | -0.1119 | [-0.1438, -0.0801] |
| cs_pair-MindMix_complete | +0.0334 | [+0.0060, +0.0608] |
| cs_pair-MindMix_branch | +0.0164 | [-0.0055, +0.0382] |

## F_EXTERNAL:fau:dependence_a — complete, n 67/67

| member | estimate | simultaneous 95% |
|---|---|---|
| cs_pair-mTRF | -0.1204 | [-0.1540, -0.0868] |
| cs_pair-VLAAI | -0.1633 | [-0.1926, -0.1341] |
| cs_pair-TCLIP | -0.1203 | [-0.1516, -0.0889] |
| cs_pair-MindMix_complete | +0.0250 | [-0.0032, +0.0533] |
| cs_pair-MindMix_branch | +0.0054 | [-0.0114, +0.0222] |

## Descriptive means (person mean accuracy, n)

- dtu:readout_b: cs_pair 0.609 (n44), mTRF 0.818 (n44), VLAAI 0.830 (n44), TCLIP 0.803 (n44), MindMix_complete 0.531 (n44), MindMix_branch 0.588 (n44)
- dtu:dependence_a: cs_pair 0.550 (n44), mTRF 0.818 (n44), VLAAI 0.830 (n44), TCLIP 0.803 (n44), MindMix_complete 0.531 (n44), MindMix_branch 0.552 (n44)
- fau:readout_b: cs_pair 0.524 (n67), mTRF 0.636 (n67), VLAAI 0.679 (n67), TCLIP 0.636 (n67), MindMix_complete 0.491 (n67), MindMix_branch 0.508 (n67)
- fau:dependence_a: cs_pair 0.516 (n67), mTRF 0.636 (n67), VLAAI 0.679 (n67), TCLIP 0.636 (n67), MindMix_complete 0.491 (n67), MindMix_branch 0.510 (n67)
