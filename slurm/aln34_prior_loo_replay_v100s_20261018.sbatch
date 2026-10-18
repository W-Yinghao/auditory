#!/bin/bash
# Exact-device recovery for ALN3X_642554812e473fee after A100 replay1046274.
# Source record: Tesla V100S-PCIE-32GB. Prior M12 receipt and operations log
# identify node08 as this model. Keep evaluator, plan and tolerances unchanged.
#SBATCH --job-name=c3_plreplay08
#SBATCH --qos=runfill
#SBATCH --partition=V100
#SBATCH --nodelist=node08
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
/home/infres/yinwang/anaconda3/envs/eeg2025/bin/python -B -u private/auditory_alignment_v3/aln34/replay_prior_loo_v100s_20261018.py
