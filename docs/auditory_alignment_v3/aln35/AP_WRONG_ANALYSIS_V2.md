# ALN3.5 APwrong: analysis-only correction v2

This correction is made before any new APwrong/AP production target output.
The sealed v1 analysis and its empty 0/50 report are preserved. They incorrectly
inherited the old bootstrap-t/max-t method and allowed each contrast its own
partial content cells. Those choices conflict with package docs/06 §6.5.
Training code, source audit, donor and target plans are unchanged.

Use the supplied `src/aln35_reference/contrasts.py` without modification. For each
dataset and endpoint, define one family of AP−S, APwrong−S and AP−APwrong. Public
endpoint: mode-T unified regular NLL in bits/query. Private endpoints: original
positive-affine native NLL in bits/trial and AUC, separate families. Risk weights
are reference minus candidate; AUC weights are candidate minus reference.

Expected identities come from the frozen manifest target cells, before checking
new outputs: DTU44, FAU67, private64. Require both public content folds0/1 for
every public person, and the single private evaluation cell. The subject-fold
is outer exclusion membership, not a repeated fold. Each family uses people
complete for all three arms and all required cells at seed3401. Missing people,
conditions and nonfinite values remain listed; there is no imputation, score
threshold, favorable-subset choice or performance-dependent stopping.

Within-person condition differences are averaged equally across their required
content cells. Then compute the equal-person mean. Resample whole people4,000
times independently within the existing hearing-group strata, preserving that
observed composition and sharing draws across all three contrasts. The package
reference uses the original sample's fixed standard errors and max-|z*| intervals;
it does not re-estimate standard errors in each replicate. Report seeds, original
SE, critical value, complete/expected n, nonregular diagnostics and actual family
membership. Less than3 complete people, zero empirical stratum contrast variance
or other nonregularity retains a point estimate when defined and no interval.

Queries/candidates are identified from actual evaluator metadata, not inferred
from equal counts. Public queries use the exact physical-order EEG segment IDs;
candidates preserve the evaluator's ordered unique audio pool. Private queries
use exact staged epoch indices after accepted/history-known filtering; their IDs
bind to full staged-file hashes. Store sensitive trial indices only in the
project-private /projects query ledger. Check result view/cell/code bindings and
ordered IDs across arms. Include actual fit/selection identity lists and outer
membership in normalized provenance; no personal support is used by this panel.

Historical S records lack runtime-captured query IDs. The v2 ledger therefore
labels those IDs as deterministic reconstruction under the same immutable
evaluator and stored input-view hashes; it does not pretend to have historical
runtime capture. All current private source hashes are sealed and rechecked.
If an input or view cannot be reconciled, fail that analysis rather than use
counts as a substitute. The existing cross-cohort identity/short-private-sound
overlap assumptions in the original prior contract are not strengthened here.

Intervals condition on these fitted models and declared content/seed scope;
neither sample-size inflation nor a new training-population uncertainty claim is
introduced. Preserve original AP/S/XP/J*/XM results. AP beating wrong alone does
not establish improvement over S, and weak/reversed results do not close the
underlying research question.
