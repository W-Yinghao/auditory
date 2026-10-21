"""CPU reference for source/shared and personal temporal readouts.

This package does not load EEG, fit encoders, or implement server data binding.
"""
from .nested import (
    FitFailure,
    NestedReadoutFit,
    TemporalBasis,
    build_time_basis,
    evaluate_readout,
    fit_nested_readout,
    risk_contrasts,
)

__all__ = [
    "FitFailure", "NestedReadoutFit", "TemporalBasis", "build_time_basis",
    "evaluate_readout", "fit_nested_readout", "risk_contrasts",
]
