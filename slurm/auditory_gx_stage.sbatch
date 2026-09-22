#!/bin/bash
#SBATCH --job-name=auditory_gx_stage
#SBATCH --partition=CPU
#SBATCH --cpus-per-task=2
#SBATCH --mem=24G
#SBATCH --time=04:00:00
#SBATCH --array=0-7
#SBATCH --output=private/auditory_gx/stage-%A_%a.log
set -euo pipefail
umask 077
cd "$SLURM_SUBMIT_DIR"
mkdir -p private/auditory_gx && chmod 700 private/auditory_gx || true
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=0 MNE_USE_NUMBA=false
exec /home/infres/yinwang/anaconda3/envs/eeg2025/bin/python -m auditory_gx.cli "$@"
