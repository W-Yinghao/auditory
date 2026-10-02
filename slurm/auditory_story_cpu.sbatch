#!/bin/bash
#SBATCH --job-name=story_cpu
# STORY v1 (AUDITORY_STORY_SERVER_PACKAGE_v1_20261002): runfill as for NEXTMAP; preemptible (REQUEUE). Units are atomic
# with done markers and representation training resumes from 100-step checkpoints; USR1 120 s before the limit
# triggers a checkpoint and exit.
#SBATCH --qos=runfill
#SBATCH --partition=CPU
#SBATCH --cpus-per-task=4
#SBATCH --mem=24G
#SBATCH --time=12:00:00
#SBATCH --requeue
#SBATCH --signal=B:USR1@120
#SBATCH --open-mode=append
#SBATCH --output=private/auditory_story/logs/%x-%j.log
set -euo pipefail
umask 077
cd "$SLURM_SUBMIT_DIR"
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2 PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=0
echo "start $(date -Is) node=${SLURMD_NODENAME:-?} restart=${SLURM_RESTART_COUNT:-0} qos=${SLURM_JOB_QOS:-?} task=${SLURM_ARRAY_TASK_ID:-none}"
exec /home/infres/yinwang/anaconda3/envs/eeg2025/bin/python -m auditory_story.cli "$@"
