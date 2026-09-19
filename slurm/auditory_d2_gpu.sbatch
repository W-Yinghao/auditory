#!/bin/bash
#SBATCH --job-name=d2_gpu
#SBATCH --partition=A40
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=12:00:00
#SBATCH --output=private/auditory_d2/gpu-%j.log
set -euo pipefail
umask 077
cd "$SLURM_SUBMIT_DIR"
mkdir -p private/auditory_d2 && chmod 700 private/auditory_d2
chmod 600 "private/auditory_d2/gpu-${SLURM_JOB_ID}.log" 2>/dev/null || true
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=0 MNE_USE_NUMBA=false
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
exec /home/infres/yinwang/anaconda3/envs/eeg2025/bin/python -m auditory_d2.cli "$@"
