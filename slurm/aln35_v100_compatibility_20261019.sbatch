#!/bin/bash
#SBATCH --job-name=c3_s35v100probe
#SBATCH --qos=runfill
#SBATCH --partition=V100
#SBATCH --nodelist=node42
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=12
#SBATCH --mem=64G
#SBATCH --time=02:00:00
#SBATCH --nice=5
#SBATCH --output=private/auditory_alignment_v3/logs/%x-%j.log
set -euo pipefail
umask 077
cd "$SLURM_SUBMIT_DIR"
export PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=0 PYTHONPATH=$PWD
export OMP_NUM_THREADS=12 MKL_NUM_THREADS=12 OPENBLAS_NUM_THREADS=12
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 MNE_USE_NUMBA=false HF_HUB_DISABLE_PROGRESS_BARS=1
export _MNE_FAKE_HOME_DIR=$(mktemp -d)
/home/infres/yinwang/anaconda3/envs/eeg2025/bin/python -B -u private/auditory_alignment_v3/aln35/v100_compatibility_20261019.py
