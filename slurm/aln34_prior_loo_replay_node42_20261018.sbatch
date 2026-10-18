#!/bin/bash
# Corrected routing only: source job 1044427 recorded Tesla V100-PCIE-16GB on node42.
# Attempt 1045971 selected V100S-PCIE-32GB and stopped before evaluation.
# Keep that wrapper/attempt; use the identical evaluator, plan and tolerances here.
#SBATCH --job-name=c3_plreplay42
#SBATCH --qos=runfill
#SBATCH --partition=V100
#SBATCH --nodelist=node42
#SBATCH --nodes=1
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=12
#SBATCH --mem=64G
#SBATCH --time=00:15:00
#SBATCH --nice=0
#SBATCH --output=private/auditory_alignment_v3/logs/%x-%j.log
set -euo pipefail
umask 077
cd "$SLURM_SUBMIT_DIR"
export PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$PWD" PYTHONHASHSEED=0
export OMP_NUM_THREADS=12 MKL_NUM_THREADS=12 OPENBLAS_NUM_THREADS=12 MNE_USE_NUMBA=false
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_HUB_DISABLE_PROGRESS_BARS=1
/home/infres/yinwang/anaconda3/envs/eeg2025/bin/python -B -u private/auditory_alignment_v3/aln34/replay_prior_loo_20261018.py
