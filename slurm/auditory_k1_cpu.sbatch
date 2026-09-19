#!/bin/bash
#SBATCH --job-name=auditory_k1
#SBATCH --partition=CPU
#SBATCH --cpus-per-task=2
#SBATCH --mem=16G
#SBATCH --output=private/auditory_k1/slurm-%j.log
set -euo pipefail
umask 077
cd "$SLURM_SUBMIT_DIR"
mkdir -p private/auditory_k1
chmod 700 private/auditory_k1 || true
find private/auditory_k1 -maxdepth 1 -type f -name "*-${SLURM_JOB_ID}.log" -exec chmod 600 {} + 2>/dev/null || true
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=0
exec /home/infres/yinwang/anaconda3/envs/eeg2025/bin/python -m auditory_k1.cli "$@"
