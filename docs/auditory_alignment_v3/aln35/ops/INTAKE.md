# ALN3.5 intake — 2026-10-19

The researcher supplied the ALN3.5 ZIP and the ALN3.4 full execution document and authorized direct execution and GPU priority changes. This is continuing experimentation. No new performance, wording or manuscript approval gate is introduced.

CPU Slurm 1047276 verified all 50 package files and passed 28 reference-tool tests. The separately supplied ALN3.4 document is byte-identical to the inherited document (SHA256 `12a7e93c823773721f2a58f2e240ec9d236f931baa90a80ed932afb9a5970430`). The ALN3.5 ZIP SHA256 is `ae48519c2766d01f6e4e78c304a65b696207ef961e1b5f0adeb393caaa6e5a57`.

The live workspace is not a Git checkout. The publication checkout `private/github_publish_032/checkout` has HEAD and freshly fetched origin/main `5ef4a60bf77eeaeab5582c2cb076077c0b15bd11`, identical to the package baseline; all 87 referenced publication files match. Live source/plan/cache binding is a separate inventory and is not inferred from the publication checkout. Original package files and old execution identities are preserved. AGENTS.md now starts with ALN3.5; its pre-merge backup is in this directory.

At the first scheduler check, 10 project GPUs were running on runfill (8 A100, one A40, one A30). Current fleet/evidence jobs are 1045979/1045980; watcher 1044086 and checkpoint offload 1044070 continue. No running worker has been interrupted. CPU admission checks use the shared normal queue and an array-aware limit of 27 before submission; no scontrol is used.

The 03:30 efficiency snapshot already marks private factorial 60/60, private episode v2 50/50 and prior-private LOO 90/90 complete. Existing TRUE_FULL 800/800, public prior 1154/1154, public content/time 180/180, private time v2 130/130 and prior science 300/300 remain complete. These are observed snapshots, not all ALN3.5 tasks completed. Useful remaining dependencies continue; exact new bindings and execution counts will be generated from live plans and assets.

The ALN3.5 package discloses the previously seen positive, negative and uncertain values. New science and mechanism contrasts are exploratory after that review. We retain all original primary statistics, the 1002 scoped historical holds and deferred A3c deletion. No new data download, deletion or automatic GitHub push is part of this intake.

Implementation is proceeding in a new aln35 namespace: (1) exact pre-access correction and 13 finite comparison families, (2) support coverage and episode-pressure comparisons, (3) strictly matched AP wrong-audio, and (4) source-state/selection, probability attribution and readout sensitivities. Their actual compatibility, source roles and readiness will be recorded separately. Reference tests do not establish real-data production success.

## Subsequent execution and storage instruction

The user subsequently requested cleaning unused files generated in `/projects`. The completed bounded cleanup is documented in `storage_cleanup/DELETED_20261019.md`: three abandoned FAU partial arrays, 2.39 GiB logical / 1.74 GiB allocated, CPU1047298. This supersedes the initial intake's statement that deletion was outside scope. Active checkpoints/caches and the existing scoped deletion deferrals remain protected.

Fleet CPU1047289 replaced1045979 through an afterany dependency and graceful stop, using the same singleton lock. CPU1047287 passed11 scheduling tests and confirmed old training source hashes unchanged. Existing GPU jobs were retained. New priorities favor inner-source, CB auditory and strong fusion; bounded ALN3.5 lanes join only after matching engineering receipts. Support/episode GPU probes are1047300/1047304. Exact live readiness is recorded in `fleet_status.json`.

CPU1047290 completed40 paired contrasts in13 families from11,402 real normalized observations, with full declared person/seed/content coverage. Native-private pre/TG correction uses actual input batches. CPU1047303 runs probability-fusion attribution from existing caches; it does not train an encoder. These individual completion statements do not mark the entire ALN3.5 package complete.

CPU1047366 produced the actual16-workpackage `ALN35_BINDINGS.json`. It also corrected an inherited prose-count error: the unchanged held-executions file contains1,602 IDs, all without a main-runner completion record, rather than the1,002 stated in earlier status text. Its SHA remains identical to intake; no hold was changed. New evidence service1047358 succeeded1045980 under the same singleton lock; exact old pending renewal1045986 was cancelled. It has already submitted new analysis refreshes1047361/1047362. The finite bridge analysis is owned separately to avoid duplicate submission.
