#!/bin/bash
#SBATCH --job-name=d2_cpu
#SBATCH --partition=CPU
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=02:00:00
#SBATCH --output=private/auditory_d2/cpu-%j.log
set -euo pipefail
umask 077
cd "$SLURM_SUBMIT_DIR"
mkdir -p private/auditory_d2 && chmod 700 private/auditory_d2
chmod 600 "private/auditory_d2/cpu-${SLURM_JOB_ID}.log" 2>/dev/null || true
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=0 MNE_USE_NUMBA=false
exec /home/infres/yinwang/anaconda3/envs/eeg2025/bin/python -m auditory_d2.cli "$@"
