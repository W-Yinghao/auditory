> GitHub 发布副本：仅提供代码、报告、汇总结果和选定图表。逐人、逐记录、逐 epoch 及原始来源资料仍保存在服务器；原文的服务器内保存声明描述审计时状态。发布范围见 [PUBLICATION.md](../PUBLICATION.md)。

# Auditory EEG project: evidence-first plan

Created 2026-09-16. The current research target is IEEE JBHI or a comparable journal, per the researcher. This supersedes the restart packet's earlier decision not to specify a journal. A journal target is not evidence of feasibility or novelty.

Execution update: Phase 0 audit and Phase 1 BDF reconstruction are complete. [Phase 2](phase2_report.md) now adds candidate-index amplitude agreement and a prespecified, explicitly limited archival MUSS feasibility model. Single-feature EEG did not improve the age/use-duration baseline in 53 HA candidates. Concurrent clinical-validation gates remain unmet; this archival experiment does not resolve them. The CI continuous-signal branch and manuscript-level study remain unfinished. Future model development must acknowledge that these HA outcomes have now been viewed.

## Execution rules

- Treat `/projects/EEG-foundation-model/auditory` as read-only. Preserve the restart archive and extracted package.
- Submit every data-analysis, environment-probing, testing, CPU and GPU workload through Slurm. Shell file viewing, editing, and scheduler control are orchestration.
- Inventory before selecting outcomes or fitting models. Do not infer event semantics from frequency, diagnoses from filenames, or visits from modification times.
- Keep original paths, participant identifiers, dates, row-level clinical extracts, and verbose reader errors in `private/` (0700). Review anonymous summaries before sharing.
- Use bounded per-file reads; no full data copy, GPU allocation, or full-file hashing until justified. Reuse existing Python environments when possible.
- Lightweight delegation is limited to independent document/code review. All substantive results must point to reproducible artifacts.

## Stages and acceptance criteria

1. **Repository and full data inventory.** Read all restart documents, inspect archives and references, enumerate every regular file and companions, capture actual reader versions and resources. Separate available, skipped, and failed files.
2. **Formats and provenance.** Inspect headers for every EEG export, internal references, preprocessing history, channel/reference/unit information, continuous versus epoched layouts, and event sources. Detect exact copies using targeted hashes if needed; label acquisition links as candidates until established.
3. **Clinical tables and identities.** Profile every workbook and sheet; preserve instrument versions, repeated rows, units, dates, missingness and source lineage. Build candidate identity links using multiple fields; no filename-only confirmed merges.
4. **Epoch and event audit.** Produce one row per existing epoch with source file, source trial, event code(s), time-zero selection, within-epoch latencies, original event links, condition ambiguity, and provenance status. Inspect all epoch metadata, not just the first epoch. Inspect signal QC in bounded batches; clinical labels remain separate until concurrent linkage is verified.
5. **Representative quality inspection.** Deterministically sample every observed protocol/layout/version stratum, including technically problematic files. Show signals, spectra, event intervals and aligned averages only when their alignment is supported. Report measured scope explicitly.
6. **Phase 0 report and research decision.** Reconcile historical counts, distinguish candidate identities from confirmed children, list blockers, and nominate one primary research question supported by the data. Freeze outcome-blinded preprocessing and measurement definitions before association screening.
7. **Subsequent formal analysis (after the above gates).** Establish within-record reliability and uncertainty; evaluate clinical incremental information with a clinical-only baseline and identical child-level outer folds. Any preprocessing learned from data must be fit within training folds. Repeated records stay in the same fold. Consider complex models only after simple baselines and adequate participant support.

## Initial priorities for a JBHI-oriented study

The provisional question is whether reproducible auditory EEG measurements add information about concurrent auditory/speech function beyond age, device-use duration, and hearing thresholds. This is conditional on trustworthy identity/time matching, interpretable events, and adequate sample support. Clinical incremental utility and honest subject-level validation are more important than a predetermined network. Device artifact, audibility, recording state, protocol/site differences, and outcome ceilings must be evaluated before clinical claims. No acceptance, causal mechanism, or prognosis claim is assumed.

## Resource and token budget strategy

Return compact structured summaries to the assistant; keep detailed tables on disk. Start with a short CPU inventory job, then adaptive header/table jobs, then bounded signal reads. Request memory based on the largest single file and use sequential processing initially. Avoid copying signal payloads, repeated full scans, broad literature searches, and model installation before data feasibility is known. Record job IDs, actual runtime, memory, failures, code hashes, and output checksums.

## Status

Planning and initial source review complete; execution status and findings will be maintained in `docs/phase0_report.md` and `results/` rather than inferred from this plan.
