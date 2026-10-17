# Doubled-budget v2: trajectory observation repair

2026-10-17, before any production run of either budget version. The scientific design is unchanged from RESEARCH_DECISION_20261017.md and the 150-row learning_budget_v1 plan (SHA256 109cb9807bbb5bd4e4674e88387851fce2e09a70110d8550a85572fc3e90ac0e). Both remain preserved.

GPU smoke 1043931 completed the CBraMod two-epoch fit, then the local fit reached evaluation without its trajectory_e0002.pt. The old observation hook relied on resume saves. Local saves resume only every 20 epochs and never at the final epoch; therefore it cannot provide the registered 50/100/200/400 trajectory states. The failure occurred before production. The two waiting v1 workers cannot run because their smoke dependency failed.

Version 2 copies only the unchanged local fit function into budget_local_v2.py and adds a read-only observation callback at the end of every epoch, before reloading the selected best checkpoint. It records the current encoder/head state at the registered trajectory epochs. An AST test removes that callback and checks equality with the original fit function; original optimizer, updates, selection and resume are unchanged. FM already saves at every validation epoch under this recipe and retains its original observation hook. No legacy trainer file is edited.

Register new ALN34B2 IDs, code hashes, output root and checkpoint storage. The v1 smoke and plan remain historical evidence and are not counted as completed production. The same 150 matched DTU baselines are reused; all folds/seeds/configurations, doubled cosine horizon, fixed trajectory times and no test-driven selection remain unchanged. This is a repair of measurement, not a change selected to improve scientific performance.
