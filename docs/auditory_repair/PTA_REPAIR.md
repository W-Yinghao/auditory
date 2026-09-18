> Publication copy: the researcher subsequently requested this curated release. Earlier no-push, not-trained and intermediate states are historical. Current completion: [corrected-cohort retraining](../../docs/auditory_retrain/STATUS.md). Participant data and weights remain private; see [publication scope](../../PUBLICATION.md).

# PTA lineage repair audit

This versioned repair addresses the historical HA PTA linkage error in the
Phase 3 covariate table. The old reader assigned `C####` from a sequential
count of nonempty workbook rows. The registered clinical table and the
corrected reader resolve `C####` to the actual worksheet row. Existing Phase 3
and auditory5 artifacts remain unchanged.

The repair produces a full 57-row covariate table with the original clinical
fields preserved and all four-frequency PTA fields read from the actual source
row. Before using a source row, it checks the source workbook against the
registered clinical audit for name, age, device duration, MUSS and IT-MAIS/MAIS
values. Row-level source names, identifiers and raw values are retained only in
the restricted repair evidence.

The old auditory5 support table is reused exactly, including its support-count
columns. Clinical completeness is recalculated with the corrected unaided PTA,
then only the D flag is rebuilt. The frozen seed and component-balancing
procedure are replayed for the old support table and for the corrected D
counterfactual. The audit records whether the historical fold file can be
reconstructed exactly, changed D membership, changed eligible-group counts and
changed fold counts. It does not replace the historical split or refit any
model.

The directly affected downstream inputs are the old HA covariate table, the
auditory5 clinical index derived from it, and the auditory5 support/fold
construction where D completeness contributes to eligibility and balancing.
The PTA-adjusted Phase 3 HA model and sensitivity inputs also consume the old
covariate table. EEG representations and historical model outputs are retained
as historical evidence and require separately versioned reruns if corrected
PTA adjustment is to be evaluated.

All computation, source reads, hashing and tests for this audit run under
Slurm. No raw source or historical output is modified.
