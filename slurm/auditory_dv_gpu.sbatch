#!/bin/bash
#SBATCH --job-name=dv_gpu
# (runfill was used only for the first PF batch; default QoS from now on, per user 2026-09-27)
#SBATCH --partition=A100,A40,L40S,H100,A30
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=96G
#SBATCH --time=23:00:00
#SBATCH --requeue
#SBATCH --open-mode=append
#SBATCH --output=private/auditory_dv/logs/%x-%A_%a.log
set -euo pipefail
umask 077
cd "$SLURM_SUBMIT_DIR"
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2 PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=0 MNE_USE_NUMBA=false
echo "start $(date -Is) node=${SLURMD_NODENAME:-?} restart=${SLURM_RESTART_COUNT:-0}"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader || true
exec /home/infres/yinwang/anaconda3/envs/eeg2025/bin/python -m auditory_dv.cli "$@"
