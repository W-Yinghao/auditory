# Repository working rules

- This repository is a curated research snapshot. Read README.md, PUBLICATION.md, docs/phase3_report.md and the phase artifact guides before making changes.
- Run CPU/GPU analyses, dependency installation, environment probes and tests through Slurm. Reading/editing files and Git/scheduler operations are orchestration.
- Keep original EEG and clinical data read-only. Never commit names, exact subject dates, original subject paths, identity mappings, source-row clinical values, individual predictions or epoch-level signals. Keep these in private/ with restricted permissions. Repository publication does not authorize future participant-data uploads.
- Preserve executed configurations, negative results and historical analysis order. Use new output directories and versioned configurations for methodological changes. Previously analyzed candidates are not an untouched validation set.
- Apply the final Phase 3 metadata addendum alongside v1 outcomes. Source labels are not confirmed diagnoses; device wearing is not proof of power; notes are not epoch-aligned without timing evidence.
- Do not count files, exported versions, event-code pairs or epochs as independent children. Use evidence-supported candidate identities and validation grouped by candidate.
- The repository omits required restricted inputs. Do not fabricate them or claim complete reproduction from aggregate summaries alone. See release/manifest.json for the included files.
