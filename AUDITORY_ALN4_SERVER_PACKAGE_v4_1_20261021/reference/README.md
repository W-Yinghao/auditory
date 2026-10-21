# Reference implementation scope

`temporal_cs_reference.py` and `verify_temporal_cs_numpy.py`: independent NumPy q² formula, expanded time-tagged KDE, analytic/finite-difference gate gradients and support-only adaptation checks.

`temporal_objectives_torch.py` and `verify_temporal_torch.py`: differentiable TCS/TNCE/GCS and first-order support logic. Server Torch verification is mandatory; missing Torch is INCOMPLETE (exit2), never PASS.

`cs_qmi_reference.py` / `verify_cs_math.py`: ordinary classical KDE-CS reference inherited from ALN4.0; provenance retained. They do not implement the ALN4.1 episode/trainer.

`time_access.py`: exact native half-open windows, source border validity, crop-only resampling and padding; not an EEG preprocessing pipeline.

`age_probe.py`: one-person-per-row nested ridge age readout. It neither generates real EEG features nor replaces the fixed private roster/split checks.

No raw/private EEG, patient identities or actual trained checkpoint is included. Production wrappers must log input roles and expected tensor shapes, and validate these references on real server data before committing expensive training.
