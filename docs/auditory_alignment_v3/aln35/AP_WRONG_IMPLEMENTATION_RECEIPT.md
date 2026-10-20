# ALN3.5 APwrong implementation and engineering receipt

The bounded implementation is executable; production completion is tracked by
unit records, not by this engineering receipt. The training plan SHA is
`07db579e0bbbf5e767641090044a3df0f4a66de8c67a41667f0dfc3ede3e4765`.
All original frozen/running prior33 source and valid prior results remain intact.

CPU1047280 proved exact original-stream reuse impossible at the first canonical
group collision: FAU lineage update1872, DTU update3226, private1880. The revised
common sampler preserves stratum choice and redraws only an impossible whole
batch for both arms. CPU1047302 passed11 contract tests and audited every one of
236,622 accepted metadata batches before sealing the plan. All3 lineages use the
same78,874-update h30 schedule in AP and APwrong, with30 true-paired source-dev
candidates and no independent wrong-arm extension trigger.

Root submitted runfill A100 probes1047335(DTU),1047336(FAU),1047337(private).
All passed8 updates per donor arm and one actual APwrong target epoch, including
real adaptation and evaluation. These probe values are engineering data, not
scientific results or performance entry gates. The read-only fleet plugin is
`auditory_alignment_v3.aln35.ap_wrong.fleet_status`; root owns all GPU routing.

Production scope is3 donor-pair units(6 models), followed by50 target units:
AP/APwrong ×(10 DTU +10 FAU +5 private cells). Compatible25 S outputs are reused.
The longer original AP trajectory stays a distinct historical endpoint.
Checkpoints, exact per-step correspondence ledgers, exposure histograms, resume
state and probes are under the private project-storage `aln35_apwrong_v1` root.
Do not delete that root, original donor/target dependencies or public prior caches.

Analysis v1 was found during review to incorrectly inherit old bootstrap-t and
partial-cell pairing. Its sealed code/registration and empty0/50 report remain
unchanged. The separate v2 correction uses the ALN3.5 reference implementation,
fixed-original-SE max-|z*|, and complete-family people over all required cells;
see `AP_WRONG_ANALYSIS_V2.md` and its separate registration/receipt. Training is
not changed by this analysis-only correction. Actual query/candidate identifiers
are reconstructed from frozen evaluator metadata and checked against each record;
legacy S records are not falsely labeled as having captured runtime IDs.

CPU1047384 passed5 v2 statistical/provenance tests and validated all25 original S
cells against the reconstructed evaluator metadata. The v2 registration SHA is
`0bcfa48b60c51b0690f03ef6615fe50f2d2368dc5c8d24ebe708fc7d601c587f`;
the expected manifest rosters are DTU44, FAU67 and private64. CPU1047374/1047378
are preserved failed audit attempts: private query pool hashes matched exactly,
but recomputing numerical filter coefficients on the CPU produced a different
view hash. Binding to the original frozen manifest filter hashes reproduces the
actual S/A100 view exactly. This metadata correction changes neither filters nor
EEG nor target training.

Use the v2 analyzer for future summaries:

```bash
sbatch slurm/aln35_apwrong_cpu.sbatch -m auditory_alignment_v3.aln35.ap_wrong_analysis_v2 run
```

The production training command remains the plan-bound fleet command:

```bash
sbatch slurm/aln35_apwrong_gpu.sbatch worker --max-units 1
```

Only root/the project fleet submits GPU work under the global cap. Summaries
write `paired_v2.json` and `AP_WRONG_RESULTS_V2.md`; v1 artifacts stay unchanged.
