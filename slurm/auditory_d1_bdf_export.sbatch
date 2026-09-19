#!/bin/bash
#SBATCH --job-name=d1_bdf_export
#SBATCH --partition=CPU
#SBATCH --cpus-per-task=4
#SBATCH --mem=24G
#SBATCH --time=06:00:00
#SBATCH --array=0-7
#SBATCH --output=private/auditory_d1/bdfexport-%A_%a.log
set -euo pipefail
umask 077
cd "$SLURM_SUBMIT_DIR"
chmod 600 "private/auditory_d1/bdfexport-${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID}.log" 2>/dev/null || true
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=0
exec /home/infres/yinwang/anaconda3/envs/eeg2025/bin/python -m auditory_d1.cli export-bdf "$@"
