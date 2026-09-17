> Publication copy: aggregate research evidence only; participant-level inputs and outputs remain on the server. Historical running/queued statements are superseded by S4_final_001. See [publication scope](../PUBLICATION.md).

# Auditory5 C paired readout v1

This outcome-blinded implementation consumes only independently generated P2
left and right branch features from the frozen representation plan. It never
partitions a full-head hidden state. Trial IDs, labels, identity groups, original
blocks, branch task metadata and encoder fit-scope hashes must agree before
fitting. A missing branch or control yields `NEED_CONTROLS`. Empty/class-deficient
inputs, inconsistent provenance, or any solver convergence failure yield `FAIL`;
no model or regularization candidate is silently omitted. Each candidate must
have at least 20 common trials in each class. No trial cap is applied.

The two separately reported families are logistic linear and one-hidden-layer
32-unit ReLU MLP. Both fit C_L, C_R, C_LR, C_LL and C_RR on the exact same trials.
The MLP family additionally fits 64-unit single-left and single-right heads.
The MLP solver is sklearn `lbfgs`, fixed `max_iter=1000`, `max_fun=50000`,
`tol=1e-6`, `early_stopping=False`. Its alpha grid is [.01,.1,1,10]; linear C
uses the same numeric grid. These choices precede viewing real C readout scores.
The first-pass seed is the frozen split seed. There is no width/seed/solver scan
or fallback after failed convergence. The environment must support MLP sample
weights; an unsupported environment fails instead of using unweighted fitting.

Each branch receives its own newly fitted candidate-weighted tabular scaler.
There is no joint scaler or PCA. Scaling is fitted separately in each of three
group inner-training folds and then in all outer-training groups. Classifier
sample weight is exactly 1/(2 * candidate-class trial count): each candidate has
total weight one and each class half. Scaler weights total one per candidate
without using its label. Duplicate models concatenate the same standardized
branch twice. The regularization and bounded [.25,4] temperature use training
inner OOF predictions only, minimizing natural-log loss and reporting bits.
All heads and all transforms are refitted on the complete outer-training set.

For learned representations, this is explicitly readout-only inner validation
conditional on a frozen outer-training encoder. It does not claim to refit that
encoder without inner-validation candidates. The encoder excludes all outer
test identities; strict nested encoder fitting is a separate requirement for D.

Each reported candidate loss weights its two classes equally; candidate groups
are then equally weighted. All intervals use 2,000 shared fixed-OOF cluster
draws and never refit the workflow. T_C is computed as
`min(mean CE_L, mean CE_R) - mean CE_LR` separately on each bootstrap draw,
never as the mean of per-person minima. Both directional gains, joint gain over
the balanced 1-bit null, duplicate margin, and the margin over expanded single
heads are reported. The MLP capacity margin compares joint loss with the best
mean loss among LL, RR, L64 and R64, reselecting this minimum within every draw.
These quantities are predictive readout contrasts, not PID synergy or brain
information capacity.

Fixed fitted heads for LR, LL and RR receive identical six interventions:
first/second slot set to standardized zero (the training branch mean), or
replaced by a same-candidate same-class / opposite-class donor from another
original record/block. A donor never crosses candidate_id, even inside a shared
identity component. Selection is stable under trial ordering using a fixed seed
and sorted trial IDs. Donor pools contain only that outer test partition. If
even one trial has no legal donor, that intervention is explicitly missing;
it is not evaluated on a selectively reduced subset. Heads, scalers and
temperatures remain fixed, and all resulting probabilities are labelled OOD
model-use diagnostics. LL/RR are perturbed slotwise, preserving the other copy.

The runner checks the archived exact two-direction raw preprocessing isolation
test and performs exact branch-scaler perturbation checks. Production-head
synthetic controls cover copied evidence, left-only evidence and XOR; a linear
XOR failure is expected while the 32-unit joint MLP must recover the signal.
These small controls validate implementation, not a type-I error bound.

The main screening requires R_SIM/MLP32, at least 25 complete candidate groups,
T_C >= .01 bit with positive lower CI, positive joint gain over the 1-bit null,
and positive lower CI for the capacity margin. R_SUP is required in parallel;
L0 alone always leaves `NEED_CONTROLS`. Missing folds, required interventions,
input-isolation evidence or synthetic controls cannot yield a positive verdict.
A calibrated positive screen unsupported by raw probabilities is marked
`MIXED_SCREEN: capacity_or_calibration`; linear/MLP disagreement is reported as
model-class dependence. All screens remain first-pass technical evidence.

Per-trial probabilities, donor IDs, fitted heads, branch input hashes, fit scopes
and per-candidate CE stay under a new private run directory. Prediction parquet
files are partitioned by outer fold, representation mode and intervention to
bound memory. Public outputs contain only aggregate losses, paired gains,
capacity comparisons, intervention summaries, control status and coverage.
Unperturbed model summaries also include candidate-macro balanced accuracy,
AUROC, Brier score and both class trial counts. Metrics use epsilon=1e-7 only
for reported CE; temperature fitting uses untruncated pre-sigmoid logits.
The runner never overwrites an existing run and never loads clinical outcomes.

Numerical repair v2 (before any real C outer-fold score was produced): C_L0_002 failed in the first nested MLP optimization at the 1000-iteration ceiling; its failure.json has an empty completed-fold coverage list. Preserve that failure. Keep the model, objective, alpha/C grid, feature scaling, tolerance, sample weights, folds and seed identical, and uniformly increase all MLP ceilings to max_iter=5000/max_fun=250000. No unconverged grid candidate is discarded. This supersedes only the two numerical ceilings above; it does not select a model using test performance.
# Linear-only partial fallback after documented numerical failure

C_L0_003 stopped in the first inner-fold MLP32 fit (alpha0.01,24649 training trials,160 features) even at the fixed5000-iteration ceiling. No C test score was produced. A separately named linear-only run now computes the original five paired views and every applicable fixed-head intervention with unchanged trials, folds, regularization and calibration. It always records the missing nonlinear/expanded-capacity matrix and cannot issue a full C screen. It neither treats an unconverged MLP as fitted nor selects a subset of successful records/folds. The full nonlinear matrix remains a separate required run; this fallback preserves useful planned linear results without claiming the C question is settled.
