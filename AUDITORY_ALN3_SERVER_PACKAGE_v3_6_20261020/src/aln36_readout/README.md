# ALN3.6 CPU readout reference

This is a small, runnable NumPy/SciPy reference for H0/E0/HP/EC/ET. It is **not** an assertion that the server's EEG extraction, source-group exclusion, matched AP/APwrong lineage, or trial bindings have already been integrated. The server adapter must implement and verify those bindings before passing arrays here. No encoder, CUDA, Slurm, data loading, or filesystem write is performed by this module.

Public continuous outcomes use `family="gaussian"`, five source-window scores, and MSE. Private binary outcomes use `family="bernoulli"`, three source-window logits, and log loss in bits/trial. All score and history scaling, the history offset, `a0`, temporal basis, and ridge strengths are fixed using the permitted source population only. See `docs/03_READOUT_CONTRACT.md` for the scientific and data contract.

```python
from aln36_readout import build_time_basis, fit_nested_readout, evaluate_readout

# source arrays are provided by the server adapter, never by an outer target.
basis = build_time_basis(
    a0=a0, source_scores=source_scorebank,
    source_history_design=source_history_design,
)
fit = fit_nested_readout(
    family="bernoulli",
    support_offset=support_offset, support_history=support_history_design,
    support_scores=support_scorebank, support_y=support_y,
    a0=a0, time_basis=basis,
    ridge_history=source_fixed_ridge_history,
    ridge_scale=source_fixed_ridge_scale,
    ridge_time=source_fixed_ridge_time,
)
result = evaluate_readout(
    fit=fit, query_offset=query_offset, query_history=query_history_design,
    query_scores=query_scorebank, query_y=query_y,
)
```

`fit_nested_readout` has no query argument. Query labels appear only in the non-fitting evaluator. This interface separation cannot itself certify that an adapter supplied legal support or excluded the correct source groups.

The temporal transform stores and actually applies the source nuisance projection
and residual whitening: `Z = (scores @ B - [1, history, scores @ a0] @ C) / scale`.
Supply the same history columns when building and applying this transform; it is
never refitted on target support or query. Coefficient orthogonality alone is not
used as a substitute for conditional time features.

Run the seven synthetic checks from the server-package root:

```bash
python -B -m unittest discover -s tests -p test_nested_readout.py -v
```

Required dependencies: Python 3.10+, NumPy, SciPy. The tests use the standard-library `unittest`; pytest is not required. Synthetic checks establish the reference's algebra and optimization behavior, not the validity or scientific result of any EEG experiment.
