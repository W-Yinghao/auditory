> Publication copy: aggregate research evidence only; participant-level inputs and outputs remain on the server. Historical running/queued statements are superseded by S4_final_001. See [publication scope](../PUBLICATION.md).

# Auditory5 native MFF export contract v1

Frozen before examining this round's MFF signal QC support. This is subsequent
exploratory processing and does not alter any Phase 0–3 output or source file.

The `P1_CAUSAL20` API spelling selects the shared filter family. Export metadata
and events instead identify `P1_CAUSAL_NATIVE`: all physical native EEG channels
are used, with VREF and other declared references excluded. All models in a
native-layout comparison receive the same channel set. Channel membership and
the average reference do not change according to QC; there is no interpolation.
Different native layouts must remain separate unless an independently frozen
mapping is used. The adapter already applies acquisition calibration into volts;
the exporter receives microvolts after exactly one conversion by 1e6.

Each actual stored interval is processed separately. Filtering uses the shared
forward HP4 0.5 Hz and LP8 30 Hz at original sampling frequency. Downsampling
keeps the original sample grid. Epochs are [-0.2,0.5), without baseline removal;
exact per-epoch times and original onset samples are retained. At 250 Hz these
contain 175 samples. Unverified native-rate resampling is not performed.

Two separately named views are available. `continuous` resets only at real
stored interval boundaries and does not establish within-record train/test
filter-state isolation. `E0_BLOCK_RESET_60S` partitions each stored interval into
disjoint 60 s raw blocks, anchored at that interval's first sample, and resets
the filter independently in each block. The entire epoch must follow the
max(20 s, measured impulse support) startup guard and precede the frozen
10.823 s block-end embargo (or a separately revised longer embargo if required
by original-rate support). These are separate start/end requirements, not two
durations added at the block start. About 28.5 s of event-onset support remains
per full 60 s block. No train/test split may mix trials from the same block.
Full stimulus history still uses actual storage intervals and the complete
pre-QC event chain; artificial filter blocks do not rewrite that history.

`auditory5_mff_qc_v1` freezes all three fractions at 0.10: reject when more than
10% of physical channels exceed 150 microvolt filtered epoch peak-to-peak,
when more than 10% have raw epoch peak-to-peak below 0.5 microvolt, or when more
than 10% are persistently raw-flat. A channel is persistently flat if at least
20% of its complete nonoverlapping 2 s raw blocks are below 0.5 microvolt.
Equality at the 10% limits is allowed. The reference always includes the fixed
physical set. Channel counts, maxima, median and 95th-percentile filtered
peak-to-peak, raw-flat metrics, and all rejection reasons are retained.
Acquisition digital rails are not established for MFF. Exact repeated extrema
are a descriptive proxy only; BDF rail rules are not transferred or called
confirmed MFF saturation detection. The 10% convention resembles an old MFF
threshold, but processing and reference differ and do not imply identical masks.

All original annotation rows remain in the ledger. Complete epochs inside a
filter region are stored even when rejected; epochs crossing actual or chosen
filter-region boundaries retain a rejected ledger entry. Unknown source event
roles interrupt history conservatively, while reader-generated annotations are
identified separately. Unlocated dynamic device/behavior changes are retained
as a whole-record eligibility hold, without invented timing cuts.

Exports and per-file hashes remain private. Temporary raw/filtered interval
memmaps bound RAM and are removed after each interval; no full EEG array is
loaded into RAM. Source files are opened read-only, with content hashes and
before/after file-tree signatures. Incomplete output directories are retained
for diagnosis and never silently resumed or overwritten.
