#!/bin/bash
#SBATCH --job-name=auditory_r0
#SBATCH --partition=CPU
#SBATCH --cpus-per-task=4
#SBATCH --mem=24G
#SBATCH --time=01:00:00
#SBATCH --output=private/auditory_r0/slurm-%j.log
set -euo pipefail
umask 077
cd "$SLURM_SUBMIT_DIR"
chmod 600 "private/auditory_r0/slurm-${SLURM_JOB_ID}.log" 2>/dev/null || true
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=0
exec /home/infres/yinwang/anaconda3/envs/eeg2025/bin/python -m auditory_r0.cli "$@"
