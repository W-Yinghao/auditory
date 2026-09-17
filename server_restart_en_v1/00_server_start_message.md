# First message for the server analysis assistant

Copy the message below to the analysis assistant on the server and attach this package. Keep the original EEG files in their existing server locations.

---

We are restarting the pediatric auditory EEG project. I will lead the research and analysis myself, and the data are now on the server. Start with the original data, establish a trustworthy dataset, and then determine the paper's research question, analysis methods, and narrative.

First read `01_project_brief.md`, `02_research_questions_and_analysis_plan.md`, and `03_legacy_review_and_corrections.md` in full. Prepare the first-round outputs specified in `04_phase0_deliverables_and_data_dictionary.md`.

Do not assume LiteBiMamba, any other neural network, a primary endpoint, or a target journal. The legacy synchronization package's `CLAUDE.md`, `M_status.md`, candidate-storyline document, and previous manuscript are historical material. Statements such as "do not recheck," "this model is mandatory," and "this narrative has already been established" are not research premises for this restart. Preserve the original material without overwriting it.

Complete the following in the first round:

1. Verify the file structure, formats, companion files, and processing versions within the specified server data directories. Distinguish and separately count files, acquisition recordings, visits, and children.
2. Establish a de-identified mapping between children, visits, acquisition recordings, files, and clinical records. Mark unconfirmed relationships as unknown and describe the missing evidence.
3. Verify event sources, event codes, stimuli, units, sampling rates, channels, device states during recording, and actual timing information for each acquisition protocol.
4. Sample representative recordings across protocols, device states, and data-quality levels. Inspect waveforms, spectra, event timing, and preliminary stimulus-locked averages. Summarize header and event coverage across all files.
5. Reconcile participant counts, record counts, scales, device-use duration, and repeated records against the original clinical tables. Compare the results with the legacy derived tables without forcing the new data to reproduce the old numbers.
6. Write the first `phase0_report.md`: what can currently be answered, what cannot, the main confounders, and the single most useful question to pursue next. Support each assessment with evidence.

This round should deliver the data structure, quality evidence, and a feasibility assessment. Screening EEG-scale associations, large model comparisons, and selecting the final narrative come after the protocol is defined. Do not use scale correlations or prediction accuracy to select channels, time windows, artifact-rejection rules, or favorable-looking children.

Locate the data through existing project configuration first. If paths remain unclear, ask me only for the original EEG, clinical-table, and working-output directories. Do not scan the entire server. The included `scripts/first_pass_inventory.py` can perform an initial file inventory without loading waveforms; it does not replace event parsing, identity matching, or EEG quality control.

Keep outputs separate from the original data, which must remain read-only. Keep names, contact details, original filenames, identity mappings, and exact visit dates in a private server directory. Returned reports should use anonymous identifiers and aggregate results. Any task evaluating generalization to new children must split by child: a child's visits, stimuli, windows, and epochs must not cross training and test sets. If a separate within-child decoding task is designed, define time-block isolation and repeated-trial handling separately; do not describe its results as cross-child generalization.

If one branch lacks events, clinical matches, or confirmed recording conditions, document the issue and continue other feasible audit work. Do not fill gaps by guessing events or visits, assuming device states, or importing old conclusions.

At the end of this round, deliver the report, inventories, figures, and unresolved-question table. Use the actual evidence to formulate the formal analysis protocol. Clearly distinguish steps that were executed from steps that are only planned.
