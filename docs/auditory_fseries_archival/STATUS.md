> Publication copy: the researcher subsequently requested this curated release. Earlier no-push, not-trained and intermediate states are historical. Current completion: [corrected-cohort retraining](../../docs/auditory_retrain/STATUS.md). Participant data and weights remain private; see [publication scope](../../PUBLICATION.md).

# Archival F-series status

The user requested continued testing after strict F1–F4 clinical qualification found insufficient support. A weaker, explicitly exploratory archival-score estimand was frozen and executed; unresolved clinical timing/version/device information was not silently filled in.

The executed screen covers 56 HA candidate identity groups, one earliest recording per group, three tasks, eight models and complete 5×3 nested validation. Correct worksheet-row linkage is used. The two primary questions and the parallel MUSS question all have `NO_CONTROLLED_ARCHIVAL_GAIN_ESTABLISHED` status. No model expansion, CI clinical pooling, paired-task model or longitudinal predictor was launched after viewing these outcomes.

| Task | Clinical MAE | Clinical + EEG MAE | Gain [95% fixed-OOF interval] |
|---|---:|---:|---|
| A given C | 3.838 | 4.087 | −0.249 [−0.700, 0.217] |
| V given C | 5.916 | 5.944 | −0.027 [−0.170, 0.107] |
| V given C and observed A | 5.281 | 5.233 | 0.048 [−0.189, 0.289] |

All quality-adjusted gains were negative. EEG alone was close to the mean-only baseline. The small positive point gain for V conditional on A did not clear uncertainty or the content/quality controls. This screen does not establish functional EEG decoding, and does not prove absence of all possible functional information.

Authoritative fitted result: `results/auditory_fseries_archival/screen_recovery_001/summary.json`. Production models are from `screen_001`; only its final JSON receipt required recovery. Final verification/report run: `verification_003`. All 5,399 attempted heads, tests and failures remain in the private ledger; no fits were repeated for recovery or verification.

The historical PTA mismatch discovered during this work is a separate material correction, not an explanation inferred from the current negative result. Read `LEGACY_PTA_LINEAGE_AMENDMENT.md`. Earlier PTA-adjusted conclusions and indirect downstream split effects need dedicated correction before manuscript reliance. This round does not close that historical reanalysis task.

The current screen should be retained as a bounded negative exploratory result. The next project priority is correcting historical PTA provenance and assessing the effect on earlier results, rather than expanding this screen's model search. Strict F1–F4/CI clinical support limits remain unchanged. Nothing was automatically pushed to GitHub.
