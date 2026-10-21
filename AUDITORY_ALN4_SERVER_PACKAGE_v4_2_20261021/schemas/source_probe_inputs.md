# Source diagnostic helper input

tools/source_probe_metrics.py reads an NPZ with allow_pickle=False. It is an array reference helper, not a model loader or sampler.

Required arrays:

| Key | Shape | Meaning |
|---|---|---|
| logits | [V,K,N,N] | Finite EEG–audio candidate logits after the production temperature; each last axis pair is one person's one S or Q block |
| positive | [N,N] | Boolean/0–1 positive correspondence mask |
| exclusion | [N,N] | Boolean/0–1 excluded candidate mask; disjoint from positive |
| q_prior | [K] | Nonnegative finite probabilities summing to1 |
| q_support | [K] | Same, after the existing support procedure |
| eeg (optional) | [V,K,N,D] | Diagnostic features at one clearly named raw/projected interface |
| audio (optional) | [V,N,D] | Diagnostic audio features at that interface |

Positive and exclusion masks are shared acrossV/K in this helper. If real masks differ across view/slot, export separate bundles with their true masks; do not collapse them to fit the interface. Each row/column must have a legal positive. All logits, including excluded entries, must be finite; masked-large finite values are legal.

Do not mix people into one Gram matrix. Give each bundle an external receipt recording arm/seed/checkpoint/person/episode/S-or-Q/native-pair-or-correct-pair/slot/head/temperature/masks and array SHA. Keep physical private panel IDs on server; public receipt may use opaque hashes.

Repeated positions or multiple positives change the uniform-score baseline. The helper computes the exact average log(legal_count/positive_count) in both directions. It does not substitute lnN when the actual masks differ.

NCE q-weighted values describe this exported episode and gate, not a new population inference, a redefinition of the production objective or CS information in bits. Native CS potentials and gradients must be exported separately from production functions as described in docs/03.

Example (paths are files produced by the server adapter, not bundled real observations):

~~~bash
python3 -B tools/source_probe_metrics.py --input source_probe_arrays.npz --output source_probe_summary.json
~~~

The output path must not already exist. All scientific arrays, checkpoints and production adapters remain server responsibilities; local tests use synthetic fixtures only.

