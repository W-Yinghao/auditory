#!/bin/bash
#SBATCH --job-name=d1_export
#SBATCH --partition=CPU
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=12:00:00
#SBATCH --array=0-28%20
#SBATCH --output=private/auditory_d1/export-%A_%a.log
set -euo pipefail
umask 077
cd "$SLURM_SUBMIT_DIR"
chmod 600 "private/auditory_d1/export-${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID}.log" 2>/dev/null || true
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=0
export MNE_USE_NUMBA=false
exec /home/infres/yinwang/anaconda3/envs/eeg2025/bin/python -m auditory_d1.cli export "$@"
