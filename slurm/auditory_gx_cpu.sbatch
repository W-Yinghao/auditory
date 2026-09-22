#!/bin/bash
#SBATCH --job-name=auditory_gx_cpu
#SBATCH --partition=CPU
#SBATCH --cpus-per-task=2
#SBATCH --mem=16G
#SBATCH --time=01:00:00
#SBATCH --output=private/auditory_gx/cpu-%j.log
set -euo pipefail
umask 077
cd "$SLURM_SUBMIT_DIR"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=0
exec /home/infres/yinwang/anaconda3/envs/eeg2025/bin/python -m auditory_gx.cli "$@"
