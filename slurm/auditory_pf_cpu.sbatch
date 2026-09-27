#!/bin/bash
#SBATCH --job-name=pf_cpu
#SBATCH --partition=CPU
#SBATCH --cpus-per-task=2
#SBATCH --mem=16G
#SBATCH --time=23:00:00
#SBATCH --requeue
#SBATCH --open-mode=append
#SBATCH --output=private/auditory_pf/logs/%x-%A_%a.log
set -euo pipefail
umask 077
cd "$SLURM_SUBMIT_DIR"
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2 PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=0 MNE_USE_NUMBA=false
echo "start $(date -Is) node=${SLURMD_NODENAME:-?} restart=${SLURM_RESTART_COUNT:-0}"
exec /home/infres/yinwang/anaconda3/envs/eeg2025/bin/python -m auditory_pf.cli "$@"
