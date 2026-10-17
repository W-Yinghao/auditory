# First episode continuation: weight-space intervention

2026-10-17T18:50:15.301744+02:00; CPU job1044408; `ALN34E_9258613073b62a3b`.

Post hoc diagnosis following the very small ordinary/episode risk differences in the first returned bundle. No training, test-based policy fallback or source edit. Original and continuation SHA256 checks passed for both inner and outer sources.

| Stage | ‖episode−ordinary‖ / ‖source‖ | ‖episode−ordinary‖ / ‖ordinary−source‖ | Update cosine | Largest weight difference | Largest training-loss difference |
|---|---:|---:|---:|---:|---:|
| inner | 3.424391e-05 | 5.932819e-03 | 0.999982401 | 1.066048e-04 | 7.450114e-04 |
| outer | 3.432591e-05 | 6.836458e-03 | 0.999976641 | 9.975047e-05 | 5.787951e-04 |

Norms alone do not imply functional equivalence. This is one configuration/fold/content/seed; complete the registered panel and assess actual prediction changes before extending the same episode recipe. Small differences here do not establish that episodic training in general is ineffective. The selected outer100-update risks are worse than the original source in this cell, despite inner selection; preserve those outcomes rather than switching back using outer test.
