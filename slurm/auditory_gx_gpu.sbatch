#!/bin/bash
#SBATCH --job-name=auditory_gx
#SBATCH --partition=A100,L40S,A40
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=6
#SBATCH --mem=48G
#SBATCH --time=23:00:00
#SBATCH --output=private/auditory_gx/gpu-%j.log
set -euo pipefail
umask 077
cd "$SLURM_SUBMIT_DIR"
mkdir -p private/auditory_gx && chmod 700 private/auditory_gx || true
export OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4 PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=0 MNE_USE_NUMBA=false
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader || true
exec /home/infres/yinwang/anaconda3/envs/eeg2025/bin/python -m auditory_gx.cli "$@"
