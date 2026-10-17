# ALN3.4 publication snapshot — publish_030, 2026-10-18

This release is an ongoing-research snapshot. The main code, documents and results were copied during 00:59–01:01 CEST; additional frozen plans and engineering evidence were copied later in the same publication run. Each generated report retains its own analysis timestamp and actual coverage. Publication does not declare unfinished training complete.

## Reading order

1. [ALN3.4 package](../../AUDITORY_ALN3_SERVER_PACKAGE_v3_4_20261016/README.md), including the inherited public-prior contract. Its zip and extracted files are unchanged.
2. [Project review](../PROJECT_PROGRESS_REVIEW_20261017_v2.md), with the date and limitations retained; [true-full evidence](TRUE_FULL_PAIRED_EVIDENCE.md) and [public-prior results](PUBLIC_PRIOR_RESULTS.md) carry later interim updates.
3. [Design and analysis notes](aln34/), including [M13](aln34/E34_PUBLIC_PRIOR_EXECUTION_RECORD.md), [FIXC items](aln34/prior33_FIXC_items.md), [D analysis note](aln34/D_MULTI_SEED_NOTE.md) and [E analysis note](aln34/E_MULTI_SEED_NOTE.md).
4. [Unit-record archives](../../results/auditory_alignment_v3/unit_records/README.md), their SHA256 manifests, the aggregate JSON files and query-score outputs under `results/auditory_alignment_v3/`.

## Server paths and publication copies

Scientific modules and tests retain their executed locations under `auditory_alignment_v3/` and `tests/auditory_alignment_v3/`. Server orchestration lives under `private/auditory_alignment_v3/`; its source copies and frozen experiment plans are published under `scripts/auditory_alignment_v3/` with the same relative layout. They are reference copies, not an invitation to submit all historical scripts. The current fleet entry points are v15 and the evidence monitor is v10; older versions remain provenance.

Server design notes from `private/auditory_alignment_v3/aln34/` are published under `docs/auditory_alignment_v3/aln34/`. A historical source path in a frozen note or code-hash table still identifies the original execution location. The server-only handoff, operational completion ledger, claims, queues and logs are not GitHub files. Some historical documents link to these server locations; the published design and result counterparts are indexed above.

To prepare an authorized local deployment, copy the orchestration sources from `scripts/auditory_alignment_v3/` into the corresponding private runtime directory, configure storage and datasets, and follow the frozen contract and relevant Slurm entry point. Runtime claims, queues, private input tables and checkpoints are not supplied. Tests and computation on the research server must run through Slurm; GPU jobs use runfill and share a ten-GPU project cap. No scontrol command is used.

## Public-prior artifacts

The [public core/rich manifests](../../results/auditory_alignment_v3/prior33/manifests/) describe public cache files, exclusions, splits and provenance. The core file is the builder's public redaction, with private child split membership removed. Its hash differs intentionally from the full server manifest used by production rows; both hashes are recorded in M13. Raw EEG/audio, derived signal caches and the full private manifest are not redistributed. The published [M12 receipt](../../results/auditory_alignment_v3/prior33/M12_receipt.json) is engineering evidence, not a production efficacy result.

M13 and the immutable package remain frozen records. Where a publication copy needs a private storage path placeholder, the publication kit records both source and published hashes; numeric results and execution identities are unchanged. Source hashes quoted in frozen records refer to server bytes, not a redacted publication copy.

## Coverage and authorization

The four main archives contain 8,229 records: DTU 3,223; FAU 3,165; Federici 1,130; private cohort 711. They include completed units available to the main runner, not every pending plan row. The separate ALN3.4 lane supplement lists its own members and snapshot. Records and per-identity analysis outputs retain authorized pseudonyms and model scores; seeds, folds, repeated evaluations and bundles do not enlarge independent n. Probe and historical execution identities remain distinct from production evidence.

Query-score NPZ files in the attention and complement analyses contain prediction/risk outputs for public datasets. The release scan opens them without pickle and checks string fields. No private raw EEG/audio, file/event ledgers, clinical source tables, identity maps, names, contact details, checkpoints or cleanup lists are included. The workspace archive relocation is not applied to the GitHub layout.

The user requested this push on 2026-10-18. The release follows the established authorization for individual model outputs without reopening that decision. The final content commit and Slurm verification jobs are recorded in [the publication receipt](../GITHUB_PUBLICATION_ALN3.md).
