#!/bin/bash
#SBATCH --job-name=nm_garr
# runfill authorised by the user for NEXTMAP (2026-10-01); preemptible (REQUEUE): units are atomic + done-marked.
# bf16 partitions only; never P100, RTX6000PRO or H100 (user 2026-10-01).
#SBATCH --qos=runfill
#SBATCH --partition=A100,A40,L40S,A30
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=48G
#SBATCH --time=23:00:00
#SBATCH --requeue
#SBATCH --open-mode=append
#SBATCH --output=private/auditory_nextmap/logs/%x-%A_%a.log
set -euo pipefail
umask 077
cd "$SLURM_SUBMIT_DIR"
export OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4 PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=0 MNE_USE_NUMBA=false
echo "start $(date -Is) node=${SLURMD_NODENAME:-?} task=${SLURM_ARRAY_TASK_ID:-?} restart=${SLURM_RESTART_COUNT:-0} qos=${SLURM_JOB_QOS:-?}"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader || true
exec /home/infres/yinwang/anaconda3/envs/eeg2025/bin/python -m auditory_nextmap.cli --config "${NM_CONFIG:-configs/auditory_nextmap_gpu_v1.yaml}" "$@"
