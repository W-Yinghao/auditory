"""Auditory FN1-A v1.1: record-level EEG learning from the existing archive only.

Frozen plan: AUDITORY_FN1_ARCHIVAL_PLAN_v1_1_493a076.md.

This package deliberately does NOT import auditory_fn1.clinical. That module implements
the FN1 v1.0 clinical-confirmation gate, which v1.1 section 13.2 removes: unknown scale
version, unknown questionnaire time and unknown device state must be ACCEPTED here and
recorded as limitations. Reusing that gate would silently reintroduce the condition the
revision exists to lift. The pure numerical modules (models, splits, statistics, signal)
carry no gate and are imported rather than copied, and both packages' hashes are
snapshotted into every run receipt.
"""
__all__ = ["runtime", "archive", "signal_export", "fitting", "synthetic", "reporting", "cli"]
