#!/bin/bash
#SBATCH --job-name=c3x_A_word
# Word-level conditional decoding (docs/auditory_c3/WORDLEVEL_REG_v1.md). runfill; never P100/RTX6000PRO/H100.
#SBATCH --qos=runfill
#SBATCH --partition=A100,A40,L40S,A30
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=6
#SBATCH --mem=48G
#SBATCH --time=12:00:00
#SBATCH --requeue
#SBATCH --open-mode=append
#SBATCH --output=private/auditory_c3/wordlevel/%x-%j.log
set -euo pipefail
umask 077
cd "$SLURM_SUBMIT_DIR"
export OMP_NUM_THREADS=6 OPENBLAS_NUM_THREADS=6 MKL_NUM_THREADS=6 PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=0 PYTHONPATH="$SLURM_SUBMIT_DIR"
export _MNE_FAKE_HOME_DIR=$(mktemp -d) MNE_USE_NUMBA=false
echo "start $(date -Is) node=${SLURMD_NODENAME:-?} restart=${SLURM_RESTART_COUNT:-0} args=$*"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader || true
/home/infres/yinwang/anaconda3/envs/eeg2025/bin/python -m auditory_c3.wordlevel.run "$@"
echo "end $(date -Is)"
