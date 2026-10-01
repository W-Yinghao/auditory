#!/bin/bash
#SBATCH --job-name=nm_cpu
# runfill authorised by the user for NEXTMAP (2026-10-01); preemptible (REQUEUE): every unit is atomic + done-marked.
#SBATCH --qos=runfill
#SBATCH --partition=CPU
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=23:00:00
#SBATCH --requeue
#SBATCH --open-mode=append
#SBATCH --output=private/auditory_nextmap/logs/%x-%j.log
set -euo pipefail
umask 077
cd "$SLURM_SUBMIT_DIR"
export OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4 PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=0 MNE_USE_NUMBA=false
echo "start $(date -Is) node=${SLURMD_NODENAME:-?} restart=${SLURM_RESTART_COUNT:-0} qos=${SLURM_JOB_QOS:-?}"
exec /home/infres/yinwang/anaconda3/envs/eeg2025/bin/python -m auditory_nextmap.cli "$@"
