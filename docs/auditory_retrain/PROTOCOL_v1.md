> Publication copy: the researcher subsequently requested this curated release. Earlier no-push, not-trained and intermediate states are historical. Current completion: [corrected-cohort retraining](../../docs/auditory_retrain/STATUS.md). Participant data and weights remain private; see [publication scope](../../PUBLICATION.md).

# Corrected-cohort and corrected-fold full encoder retraining

The researcher explicitly requested completion of the previously omitted full
retraining. This is a new exploratory execution, not independent confirmation.
The historical repaired readout on the original 51-person cohort remains intact.

Use corrected original-worksheet PTA, the original earliest-record identity
graph and the unchanged audited EEG/QC definitions. Rebuild clinical completeness
and D support (52 groups) and all outer/inner folds with the original deterministic
balancing algorithm. The outer support universe remains 60 groups; 37 assignments
change. Verify these quantities directly before training. Do not copy original
encoder weights, fitted scalers, stimulus probes, PCA bases or clinical projections
into the new tasks. Nonclinical outer-training identities may contribute EEG as
in the original design; all outer-test and clinical-inner-validation identities
are excluded from encoder fitting, including self-supervised fitting.

Scope: five outer folds, each with three independently fitted clinical inner
folds. Train R_SUP and R_SIM anew in all 20 scopes each (40 learned encoders).
Generate five deterministic L0 outer representations; their inner scaling, PCA
and stimulus probes are newly fitted in their respective training scopes. R_SIM
remains primary and R_SUP parallel. Seed11, the SmallEEGCNN architecture and all
original training/readout hyperparameters are retained to isolate cohort/fold
correction. No new model family or favorable seed selection is introduced.

Scientific continuation is never gated by MAE gain, p-value, interval excluding
zero, rank or the old 0.5-point screening threshold. Every representation and
declared control completes. Supervised checkpoint selection retains the original
training-only stimulus-loss monitor (80-epoch maximum, patience12, numerical
improvement tolerance1e-8), followed by fresh-network/fresh-scaler refitting on all
training identities for the chosen epoch count. This optimization rule does not
view clinical results or decide which scientific analyses run. SimCLR uses its
fixed100 epochs, final checkpoint and no clinical labels.

The old deterministic EEG exports are reused only after checking their frozen
summaries, event ledgers, array hashes and identity assignments. An explicit
read-only-by-convention symlink may expose the unchanged export to the new private
namespace; it is never an output destination. The raw dataset is read-only.
All new execution uses immutable source snapshots and a new namespace. Model
artifacts, identities, exact paths, predictions and verbose logs stay private.

For all three modes, complete all27 core D models (clinical, visible, null,
visible+null, full, prestimulus and20 random-null controls). Rebuild every inner
and outer projection on its new clinical training identities. Also complete the
same-cohort all-trial27-model sensitivity, both count/QC3-model sensitivities,
the newly trained null stimulus probe, and FP32/FP64 invariance checks. Do not
declare a control complete by fitting only its successful folds. Numerical
failures have separate statuses and must be diagnosed rather than reclassified
as scientific negative results.

Report all candidate-level OOF predictions privately, aggregate MAE and paired
fixed-OOF identity bootstrap intervals, random-control distributions, influence,
fold/encoder diagnostic counts and checkpoint epochs. Compare the intersection
with the previous corrected old-fold replay as a descriptive sensitivity;
changed training cohorts/folds prevent attributing its difference solely to the
extra person. Do not merge unrelated fold feature coordinates. The requested
work does not create independent clinical validation or establish real follow-up.

All CPU/GPU computation, probes, hashes, tests and figures run through Slurm.
At most two GPU jobs run concurrently. Prefer H100/A100/L40S; V100 or supported
RTX PRO6000 are allowed, P100 is prohibited. Guard the actual allocated device.
Use finite task lists and suitable wall times, never a statistical advancement
threshold. Preserve completed checkpoints and recover downstream summaries
without repeating completed training merely to fix bookkeeping. No automatic
GitHub push.
