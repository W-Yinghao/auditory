#!/bin/bash
#SBATCH --job-name=c3_caldiag18
#SBATCH --partition=CPU
#SBATCH --qos=normal
#SBATCH --cpus-per-task=12
#SBATCH --mem=16G
#SBATCH --time=00:30:00
#SBATCH --output=private/auditory_alignment_v3/logs/%x-%j.log
set -euo pipefail
umask 077
cd "$SLURM_SUBMIT_DIR"
export PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$PWD" PYTHONHASHSEED=0
export OMP_NUM_THREADS=12 MKL_NUM_THREADS=12 OPENBLAS_NUM_THREADS=12 MNE_USE_NUMBA=false
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_HUB_DISABLE_PROGRESS_BARS=1
/home/infres/yinwang/anaconda3/envs/eeg2025/bin/python -B -u private/auditory_alignment_v3/aln34/diagnose_calibration_20261018.py
