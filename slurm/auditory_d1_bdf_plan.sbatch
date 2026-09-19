#!/bin/bash
#SBATCH --job-name=d1_bdf
#SBATCH --partition=CPU
#SBATCH --cpus-per-task=2
#SBATCH --mem=16G
#SBATCH --time=00:20:00
#SBATCH --output=private/auditory_d1/bdf-%j.log
set -euo pipefail
umask 077
cd "$SLURM_SUBMIT_DIR"
mkdir -p private/auditory_d1 && chmod 700 private/auditory_d1
chmod 600 "private/auditory_d1/plan-${SLURM_JOB_ID}.log" 2>/dev/null || true
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=0
exec /home/infres/yinwang/anaconda3/envs/eeg2025/bin/python -m auditory_d1.cli plan-bdf "$@"
