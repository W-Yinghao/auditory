#!/bin/bash
#SBATCH --job-name=c3_gpu
# C3 v1 GPU entry (stimulus feature extraction with frozen speech models; no EEG, no training).
# runfill per user 2026-10-04; preemptible (REQUEUE): units are atomic + done-marked. Never P100/RTX6000PRO/H100.
#SBATCH --qos=runfill
#SBATCH --partition=A100,A40,L40S,A30
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=48G
#SBATCH --time=12:00:00
#SBATCH --requeue
#SBATCH --open-mode=append
#SBATCH --output=private/auditory_c3/logs/%x-%j.log
set -euo pipefail
umask 022
cd "$SLURM_SUBMIT_DIR"
export OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4 PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=0
# per-job local MNE home: concurrent jobs locking ~/.mne/mne-python.json on NFS fail with "Stale file handle"
export _MNE_FAKE_HOME_DIR=$(mktemp -d) MNE_USE_NUMBA=false
export HF_HOME=/projects/EEG-foundation-model/auditory_public/derived/hf_cache HF_HUB_DISABLE_TELEMETRY=1 TOKENIZERS_PARALLELISM=false
echo "start $(date -Is) node=${SLURMD_NODENAME:-?} restart=${SLURM_RESTART_COUNT:-0} qos=${SLURM_JOB_QOS:-?} args=$*"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader || true
for unit in "$@"; do /home/infres/yinwang/anaconda3/envs/eeg2025/bin/python -m auditory_c3.features "$unit" || echo "UNIT_FAIL $unit rc=$?"; done
echo "end $(date -Is)"
