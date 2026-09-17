> Publication copy: aggregate research evidence only; participant-level inputs and outputs remain on the server. Historical running/queued statements are superseded by S4_final_001. See [publication scope](../PUBLICATION.md).

# Auditory5 D controls v1

This module extends the completed frozen D cores without overwriting them or
changing their endpoint, cohort, projections, penalty grids or primary criteria.
The endpoint remains the same HA source-percentage MUSS. Core results have
already been viewed; the specific low-dimensional count/QC convention below is
a subsequent implementation of the prespecified sensitivity, not an untouched
confirmatory analysis. No encoder is trained by this module.

API: `run(config, split_run, representation_plan, modes, core_runs, output_dir)`.
`representation_plan` is the immutable plan JSON path. `core_runs` maps each of
L0/R_SUP/R_SIM to its completed private D core directory. Required inputs are
`clinical_oof.parquet`, `aggregate.json`, each saved outer/inner projection,
and the matching representation task/completion/features/head files. Learned
inner encoders must exclude both inner clinical validation and every outer-test
identity. Missing dependencies remain pending; incompatible scopes/hashes fail
the affected control. All source artifacts remain read-only and are hashed.

The original 40 trials/class, 20 resampling summaries remain the reference. The
all-trial sensitivity uses every accepted trial in each class, retaining the
same 40/class eligibility floor and the exact saved training-fitted center,
visible basis, null/full/pre PCA and 20 random null bases. It reruns the original
D0--D7 clinical models, including all 20 random controls, using the same grouped
ridge grids and independent inner coordinate systems. Only probabilities or
candidate predictions are pooled across outer folds, never feature coordinates.

Count/QC adds exactly two nuisance columns to the C penalty group:
`log1p(min(n_accepted_class0,n_accepted_class1))` and the rejected fraction of
all original literal-class-1/2 target events from the represented records.
The rejection fraction includes the original boundary/startup/QC rejection
reasons; it is not called an artifact-only fraction. No new channel or trial
exclusion is introduced. These columns share the existing alpha_C grid; the
group's scaling is recomputed only in the relevant clinical training partition.
The private source audit retains the exporter keys `offline_record_qc` and
`persistent_raw_flat_max_fraction`, native/processed sampling rates and guards;
these are provenance fields, not extra nuisance predictors. The original event
parquet hash must match the frozen exporter summary's `output_sha256` entry.
Both original-budget and all-trial count/QC variants rerun D1_C, D2_CV and D3_CVN
on the same candidate set. Thus D1_C in those variants means C plus the fixed
nuisance columns. No nuisance feature uses the clinical target.

Clinical targets and original C columns are read from the core's private OOF
and projection artifacts, not joined to a new clinical source. Each saved
projection's IDs and FitScope must exactly match the frozen clinical train/test
partition; saved PCA fit groups must be precisely that clinical training set.
All new ridge scaling, penalty selection and fitting reuse the core's strict
inner/outer split definitions. All-trial summaries introduce no fitted basis.

For every outer stimulus head and each inner stimulus head, the fixed-head
float32 check computes both original and visible-only probabilities with
float32 inputs, weights, biases, centers and matrix operations. It reports the
maximum over all actual stored feature rows and a fixed 128-point synthetic
input set, with a <=1e-6 threshold, separately from the existing float64 test.
The checked probabilities are the raw fixed linear head used to define D's
geometry; this is not a new temperature fit or a recalibrated clinical feature.
Projection rank and rowspace are checked against the saved core geometry.
L0 inner heads were not saved, so they are deterministically refitted with the
original seed 11, C grid, PCA<=32 and the original nonvalidation training groups;
their row/null projectors must match the saved geometry before the FP32 check.
These are CPU head refits, not new encoders. A failed numerical check is retained
and does not suppress clinical sensitivity results.

The new null stimulus probe is the existing candidate-balanced linear probe
with train-only scaling/PCA<=32, its original C grid and inner-OOF temperature.
It receives the entire fixed-head null projection, then evaluates only held-out
clinical candidates. No test label selects a direction or parameter. This is
a property diagnostic conditional on the fixed outer encoder/head/null basis;
its internal readout CV does not refit that upstream definition. Positive
held-out decoding demonstrates that fixed-head invisibility can retain stimulus
information. A negative linear probe cannot establish stimulus independence.
D.6 requires a new stimulus probe but does not require a nonlinear family;
nonlinear null decoding is explicitly untested and is not claimed complete.
The diagnostic's status is separate so a probe solver failure cannot invalidate
or erase other completed controls.

Private outputs retain candidate-level sensitivity predictions/errors, tuning,
null-probe probabilities and fitted probes, per-candidate null losses, numerical
checks and input hashes. Public tables contain same-candidate 2,000 fixed-OOF
cluster intervals, aggregate numerical errors and independent control statuses.
Original candidate errors, ceiling fractions and leave-one-out ranges are
preserved from the core; they never trigger deletion. These controls do not
automatically issue a full D positive screen or resolve scale concurrence,
identity uncertainty, nonlinear null properties or independent replication.
Every execution and test requires Slurm.
