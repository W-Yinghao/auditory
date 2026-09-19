#!/bin/bash
#SBATCH --job-name=auditory_fn1
#SBATCH --partition=CPU
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --output=private/auditory_fn1/slurm-%j.log
set -euo pipefail
umask 077
cd "$SLURM_SUBMIT_DIR"
# Private artefacts are created 0700/0600 by the runtime; the Slurm log itself is
# created by the scheduler before this script runs, so tighten it explicitly here
# rather than relying on umask (a known limitation in this repository's older jobs).
mkdir -p private/auditory_fn1
chmod 700 private/auditory_fn1 || true
find private/auditory_fn1 -maxdepth 1 -type f -name "*-${SLURM_JOB_ID}.log" -exec chmod 600 {} + 2>/dev/null || true
# Deterministic numerics: single-threaded BLAS, no bytecode written into snapshots.
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export PYTHONDONTWRITEBYTECODE=1
export PYTHONHASHSEED=0
FN1_PYTHON=/home/infres/yinwang/anaconda3/envs/eeg2025/bin/python
"$FN1_PYTHON" -c "import sys; assert sys.version_info[:2] >= (3, 11), sys.version" 
exec "$FN1_PYTHON" -m auditory_fn1.cli "$@"
