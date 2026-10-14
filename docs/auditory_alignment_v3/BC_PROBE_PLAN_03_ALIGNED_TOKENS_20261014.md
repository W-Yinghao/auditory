# B / C localisation probes — plan 03: query-aligned backbone tokens (2026-10-14)

**Status**: written and frozen (0444) before the run. The sha256 is in `private/auditory_alignment_v3/probe_bc/code_sha256_at_freeze_03.txt`.
User instruction 2026-10-14: "做你觉得所有该做的，并push". This is the cheap check proposed after P5.

## Question

Is the stimulus-locked information lost because a backbone token summarises a fixed 1 s patch that is not aligned with
the query? Or do the backbones discard it even when the patch is aligned with the query time?

No model is trained. The probe adds no plan rows and sets no performance threshold. Data: the same FAU and DTU cells and
training participants as plan 02 (fit / early-stopping split, rng 20261014). Fewer queries: every 8th grid query for fit,
every 4th for early stopping.

## Views (features for a query at t)

| view | features |
|---|---|
| R06 | raw native EEG in [t, t + 0.6 s) (= P5 F0) |
| R10 | raw native EEG in [t − 0.4 s, t + 0.6 s), zero before the segment start |
| ALIGNED arch / init / layer | one backbone patch built from exactly the R10 window (resampled to 200 Hz, adapter scaling), frozen; channel tokens at `patch_embedding` or `last` (C × E) |
| UNALIGNED arch / layer | pretrained, from the full-context forward that B_DENSE uses: the token of the patch containing t + 0.3 s (C × E) |

- arch ∈ {cbramod, reve}; init ∈ {pretrained, random (same architecture, frozen at initialisation)}.
- The aligned patch ends at t + 0.6 s, the local models' lag-access limit. Like B_DENSE, it includes earlier EEG of the
  segment. R10 is its raw counterpart with identical information.

**Readout**:
- linear kernel ridge on standardised features, λ chosen on early-stopping half A;
- mean Pearson r over target dimensions on half B at Δ = 0;
- floor: targets from another segment.

## Reading (fixed now)

- **ALIGNED pretrained** (best layer) r ≥ 0.5 · r(R10) and > UNALIGNED: aligned patching recovers the information.
  Next step: a registered query-aligned B variant.
- **ALIGNED random** ≥ 0.5 · r(R10) while ALIGNED pretrained < 0.5 · r(R10): the pretrained weights discard it.
- **Every ALIGNED view** < 0.5 · r(R10): the backbones discard the 20 ms stimulus detail even when aligned. The FM arms stay
  deferred, and the FM result is reported as negative with this localisation.
- Results between these cases are reported as they are.

## Outputs

- `private/auditory_alignment_v3/probe_bc/probe_aligned.json` + log;
- a section appended to `docs/auditory_alignment_v3/BC_PROBE_RESULTS.md`.
