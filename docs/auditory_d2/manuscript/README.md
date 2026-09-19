# Manuscript draft

| File | Section |
|---|---|
| `00_ABSTRACT_AND_INTRO.md` | Title, abstract, introduction |
| `01_METHODS.md` | Cohorts, export contract, features, readouts, validation |
| `02_RESULTS.md` | Sections 3.1-3.8, all numbers |
| `03_DISCUSSION.md` | Related work, discussion, limitations |
| `04_REFERENCES.md` | Reference list with DOIs, grouped by role |
| `05_SUPPLEMENTARY_RUNS.md` | Scheduler job identifier for every published aggregate |

Figures: `figures/auditory_d2/fig{1,2,3}_*.{png,pdf}`.
Underlying numbers: `../D2_MANUSCRIPT_SKELETON.md`, `../D2_ROUND{1,2,3,5,6}_RESULTS.md`
and `../D2_ROUND4_CORRECTION.md`.

## Remaining before submission

1. **Verify every reference.** The entries in `04_REFERENCES.md` come from a web search
   run for this project. Each must be opened and checked - author list, exact title,
   volume and pages, and that the DOI resolves. Entries without a full author list are
   the ones most likely to need correction. This is a blocker.
2. IEEE two-column formatting and a figure-caption pass.
3. The clinical branch cannot host the electrode-selection experiment (it has only 20
   electrodes); the text says so, but a reviewer will ask, so consider whether an
   external high-density paediatric corpus can replicate Section 3.3.

## Things deliberately not claimed

Age accuracy is not presented as a contribution; normalised by target dispersion it sits
below the published paediatric frontier, and the introduction and related-work sections
both say so. No causal claim is made about cortical maturation. The two-minute row is
reported as no worse than the full session, not better. The 16-electrode parity with 128
is attributed partly to regularisation at this sample size. No fixed reduced montage is
offered: between-fold selection overlap is 0.245.
