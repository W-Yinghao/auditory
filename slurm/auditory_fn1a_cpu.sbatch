#!/bin/bash
#SBATCH --job-name=auditory_fn1a
#SBATCH --partition=CPU
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --output=private/auditory_fn1a/slurm-%j.log
set -euo pipefail
umask 077
cd "$SLURM_SUBMIT_DIR"
mkdir -p private/auditory_fn1a
chmod 700 private/auditory_fn1a || true
# Slurm creates the --output file before this script body runs, so umask cannot protect
# it; tighten every log for this job id explicitly.
find private/auditory_fn1a -maxdepth 1 -type f -name "*-${SLURM_JOB_ID}.log" -exec chmod 600 {} + 2>/dev/null || true
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export PYTHONDONTWRITEBYTECODE=1
export PYTHONHASHSEED=0
FN1A_PYTHON=/home/infres/yinwang/anaconda3/envs/eeg2025/bin/python
"$FN1A_PYTHON" -c "import sys; assert sys.version_info[:2] >= (3, 11), sys.version"
exec "$FN1A_PYTHON" -m auditory_fn1a.cli "$@"
