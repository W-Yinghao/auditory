"""ALN3 family registry (not part of any code hash): family -> code group -> code files. Adding a family here never
changes the version of running units."""
FAMILY_CODE = {
    "local": [("auditory_alignment_v3", f) for f in ("core.py", "local_train.py", "run_local.py")],
    "private": [("auditory_alignment_v3", f) for f in ("core.py", "local_train.py", "calib.py", "run_private.py")] + [("auditory_alignment_v3/aln3_reference", "calibration.py")],
    "local_factors": [("auditory_alignment_v3", f) for f in ("core.py", "local_train.py", "run_local.py", "temporal_ext.py", "run_local_factors.py")],
    "complement": [("auditory_alignment_v3", f) for f in ("core.py", "local_train.py", "fm_dense.py", "fm_complement.py", "run_complement.py")] + [("auditory_alignment_v3/aln3_reference", "readouts.py")],
    "dense_ext": [("auditory_alignment_v3", f) for f in ("core.py", "local_train.py", "fm_dense.py", "run_dense_ext.py")] + [("auditory_alignment_v3/aln3_reference", "readouts.py")],
    "adapt": [("auditory_alignment_v3", f) for f in ("core.py", "local_train.py", "run_complement.py", "run_adapt3.py")],
    "coverage": [("auditory_alignment_v3", f) for f in ("core.py", "local_train.py", "coverage_train.py", "run_coverage.py")],
    "attention": [("auditory_alignment_v3", f) for f in ("core.py", "local_train.py", "run_attention.py")],
    "e_complement": [("auditory_alignment_v3", f) for f in ("core.py", "local_train.py", "fm_dense.py", "private_stage.py", "run_e_complement.py")] + [("auditory_alignment_v3/aln3_reference", f) for f in ("readouts.py", "calibration.py")],
    "distill": [("auditory_alignment_v3", f) for f in ("core.py", "local_train.py", "calib.py", "private_stage.py", "distill_train.py", "run_distill.py")] + [("auditory_alignment_v3/aln3_reference", "calibration.py")],
    "layer_probe": [("auditory_alignment_v3", f) for f in ("core.py", "local_train.py", "fm_dense.py", "fm_probe.py", "run_layer_probe.py")] + [("auditory_alignment_v3/aln3_reference", "readouts.py")],
    "transfer": [("auditory_alignment_v3", f) for f in ("core.py", "local_train.py", "calib.py", "run_private.py", "run_transfer.py")],
    "dense": [("auditory_alignment_v3", f) for f in ("core.py", "local_train.py", "fm_dense.py", "run_dense.py")] + [("auditory_alignment_v3/aln3_reference", "readouts.py")],
    # D policy arms (ADDENDUM_04, 2026-10-13): routed by run.py per row (architecture dense_fm_policy / complement_policy)
    "adapt_policy": [("auditory_alignment_v3", f) for f in ("core.py", "local_train.py", "fm_dense.py", "fm_complement.py", "run_adapt3.py", "policy.py",
                                                            "policy_models.py", "run_adapt_policy.py")] + [("auditory_alignment_v3/aln3_reference", "readouts.py")],
    "coverage_policy": [("auditory_alignment_v3", f) for f in ("core.py", "local_train.py", "fm_dense.py", "fm_complement.py", "complement_coverage_train.py",
                                                               "policy.py", "run_coverage_policy.py")] + [("auditory_alignment_v3/aln3_reference", "readouts.py")],
    "attention_policy": [("auditory_alignment_v3", f) for f in ("core.py", "local_train.py", "fm_dense.py", "fm_complement.py", "fm_attention.py", "run_attention.py",
                                                                "policy.py", "run_attention_policy.py")] + [("auditory_alignment_v3/aln3_reference", "readouts.py")],
    # ADDENDUM_06 (2026-10-14): query-aligned foundation-model readout
    "aligned": [("auditory_alignment_v3", f) for f in ("core.py", "local_train.py", "fm_dense.py", "fm_aligned.py", "run_aligned.py")] + [("auditory_alignment_v3/aln3_reference", "readouts.py")],
    # ADDENDUM_07 (2026-10-14, ALN3.2 wave 1)
    "local_support": [("auditory_alignment_v3", f) for f in ("core.py", "local_train.py", "local_support.py")],
    "aligned32": [("auditory_alignment_v3", f) for f in ("core.py", "local_train.py", "fm_dense.py", "fm_aligned.py", "fm_aligned32.py", "run_aligned32.py")] + [("auditory_alignment_v3/aln3_reference", "readouts.py")],
    # ADDENDUM_09 (2026-10-14, ALN3.2 wave 2a)
    "complement32": [("auditory_alignment_v3", f) for f in ("core.py", "local_train.py", "fm_dense.py", "local_support.py", "complement32.py")],
    # ADDENDUM_10 (2026-10-14, ALN3.2 wave 2b)
    "residual32": [("auditory_alignment_v3", f) for f in ("core.py", "local_train.py", "local_support.py", "residual32.py")] + [("auditory_alignment_v3/aln3_reference", "readouts.py")],
}
POLICY_GROUP = {"D_ADAPT": "adapt_policy", "D_COVERAGE": "coverage_policy", "D_ATTENTION": "attention_policy"}  # D family -> code group of its bound policy arms (families not listed stay unbound)
FAMILY_GROUP = {"A_LOCAL": "local", "A_TARGETS": "local", "A_DIMENSION": "local", "E_LOCAL": "private", "E_GX": "private", "E_GENERIC": "private",
                "B_DENSE": "dense", "A_LOCAL_FACTORS": "local_factors", "C_COMPLEMENT": "complement", "C_CAPACITY_CONTROL": "complement", "B_CTRL_ONESTEP": "dense_ext", "B_LR_PANEL": "dense_ext", "D_ADAPT": "adapt", "D_COVERAGE": "coverage", "D_ATTENTION": "attention", "E_COMPLEMENT": "e_complement", "E_DISTILL": "distill", "B_LAYER_PROBE": "layer_probe", "E_PUBLIC_TRANSFER": "transfer", "B_ALIGNED": "aligned",
                "ALN32_LOCAL_SUPPORT": "local_support", "ALN32_POSTONLY_FM": "aligned32", "ALN32_TRUE_FULL": "aligned32",
                "ALN32_SIMPLE_COMPLEMENT": "complement32", "ALN32_RESIDUAL": "residual32"}
# E34_PUBLIC_PRIOR (ALN3.4; PUBLIC_PRIOR_DESIGN.md §6.3, module M9): the five prior33 code groups and the six
# ALN32_PUBLIC_AUDIO_PRIOR_* families, appended after FAMILY_GROUP. Each group hashes core.py, local_train.py and its prior33
# files (and V2_DEPS, like every group). Design delta: prior33_donor and prior33_rich_donor also hash prior33/select.py,
# which run_donor.py / donor_train.py import at run time (joint choice, checkpoint and stable-state names); §6.3 lists it for
# the bridge, target and zero-shot groups only. Runners: RUNNER.update in run.py (run.prior33.patch).
_p33 = lambda *fs: [("auditory_alignment_v3", "core.py"), ("auditory_alignment_v3", "local_train.py")] + \
                   [("auditory_alignment_v3/prior33", f) for f in fs]  # noqa: E731
FAMILY_CODE.update({
    "prior33_donor":      _p33("contract.py", "views.py", "model.py", "losses.py", "sampler.py", "select.py", "donor_train.py", "run_donor.py"),
    "prior33_rich_donor": _p33("contract.py", "views.py", "model.py", "losses.py", "sampler.py", "rich.py", "select.py", "donor_train.py", "run_donor.py"),
    "prior33_bridge":     _p33("contract.py", "views.py", "model.py", "losses.py", "sampler.py", "select.py", "bridge.py", "run_bridge.py"),
    "prior33_target":     _p33("contract.py", "views.py", "model.py", "losses.py", "select.py", "gen_fit_target.py", "fit_target.py", "target_train.py", "run_target.py") + [("auditory_alignment_v3", "calib.py"), ("auditory_alignment_v3/aln3_reference", "calibration.py")],
    "prior33_zeroshot":   _p33("contract.py", "views.py", "model.py", "select.py", "bridge.py", "zeroshot.py", "run_zeroshot.py"),
})
FAMILY_GROUP.update({
    "ALN32_PUBLIC_AUDIO_PRIOR_DONOR":      "prior33_donor",
    "ALN32_PUBLIC_AUDIO_PRIOR_CSX_DONOR":  "prior33_donor",
    "ALN32_PUBLIC_AUDIO_PRIOR_RICH_DONOR": "prior33_rich_donor",
    "ALN32_PUBLIC_AUDIO_PRIOR_BRIDGE":     "prior33_bridge",
    "ALN32_PUBLIC_AUDIO_PRIOR_TARGET":     "prior33_target",
    "ALN32_PUBLIC_AUDIO_PRIOR_ZEROSHOT":   "prior33_zeroshot",
})
