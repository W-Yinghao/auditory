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
}
FAMILY_GROUP = {"A_LOCAL": "local", "A_TARGETS": "local", "A_DIMENSION": "local", "E_LOCAL": "private", "E_GX": "private", "E_GENERIC": "private",
                "B_DENSE": "dense", "A_LOCAL_FACTORS": "local_factors", "C_COMPLEMENT": "complement", "C_CAPACITY_CONTROL": "complement", "B_CTRL_ONESTEP": "dense_ext", "B_LR_PANEL": "dense_ext", "D_ADAPT": "adapt", "D_COVERAGE": "coverage", "D_ATTENTION": "attention", "E_COMPLEMENT": "e_complement", "E_DISTILL": "distill", "B_LAYER_PROBE": "layer_probe", "E_PUBLIC_TRANSFER": "transfer"}
