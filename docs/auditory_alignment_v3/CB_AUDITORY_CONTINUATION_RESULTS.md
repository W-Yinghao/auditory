# CBraMod intermediate public auditory training

2026-10-18T19:50:39.061674+02:00, CPU job 1045980, **interim**; 19/144 units, 9/9 donors complete.

Matched donor update counts/data streams; only backbone weights transfer. Target heads, source-only selection and original direct baselines are retained. Donor64Hz preprocessing differs from target preprocessing. All registered target effects and donor costs are in the JSON; neither extra optimization nor a single contrast establishes auditory-specific knowledge.

## dtu / native / 3401

Complete paired identities 10/44.

| Comparison | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| generic_paired versus generic_direct | -0.0207 | [-0.0800,+0.0386] |
| generic_wrong versus generic_direct | -0.4854 | [-0.7198,-0.2509] |
| generic_paired versus generic_wrong | +0.4647 | [+0.2233,+0.7060] |
| random_paired versus random_direct | +0.1357 | [+0.0313,+0.2401] |
| generic_paired versus random_paired | +0.1210 | [-0.0517,+0.2937] |

## dtu / unified / 3401

Complete paired identities 10/44.

| Comparison | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| generic_paired versus generic_direct | -0.0466 | [-0.1159,+0.0228] |
| generic_wrong versus generic_direct | -0.3453 | [-0.4737,-0.2169] |
| generic_paired versus generic_wrong | +0.2987 | [+0.1775,+0.4199] |
| random_paired versus random_direct | -0.1021 | [-0.2032,-0.0010] |
| generic_paired versus random_paired | +0.0930 | [-0.0388,+0.2247] |

