"""docs/13 parallel scientific analysis, round 1 (docs/auditory_alignment_v3/SCI_R1_PREREG.md).

Analysis only: reads completed ALN2/ALN3 checkpoints and unit records, never writes into units/ or ckpt/, runs on CPU.
Not registered in registry.FAMILY_CODE, so no ALN3 family code hash depends on these files.
  lags.py        lag grids, protocol windows -> token indices, negative-lag control offsets
  readout.py     relative-alpha ridge with edge extension, unified scores / temperature / metrics, Haufe patterns
  continuous.py  FAU / DTU / Federici per-unit analyses (S1a-S1d, S3) for one (dataset, content fold, subject fold) job
  private_task.py private current-class per-fold analyses
  stats.py       identity bootstrap, max-t simultaneous bands, independent-group contrasts, low-df OLS
  aggregate.py   per-identity curves -> group summaries, figures and the SCI_* documents' tables
"""
