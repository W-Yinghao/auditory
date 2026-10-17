#!/bin/bash
# Frozen-checkpoint evaluation; no model training. Full original-score reproduction first.
#SBATCH --job-name=c3_privcalloo
#SBATCH --qos=runfill
#SBATCH --partition=V100,A30,A40,L40S
#SBATCH --exclude=node52
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=12
#SBATCH --mem=64G
#SBATCH --nice=65
#SBATCH --open-mode=append
#SBATCH --output=private/auditory_alignment_v3/logs/%x-%j.log
set -euo pipefail
umask 077
cd "$SLURM_SUBMIT_DIR"
export PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=$PWD PYTHONHASHSEED=0 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 MNE_USE_NUMBA=false
export OMP_NUM_THREADS=12 MKL_NUM_THREADS=12 OPENBLAS_NUM_THREADS=12
export _MNE_FAKE_HOME_DIR=$(mktemp -d)
echo "start $(date -Is) job=$SLURM_JOB_ID node=$SLURMD_NODENAME args=$*"
/home/infres/yinwang/anaconda3/envs/eeg2025/bin/python -B -u -m auditory_alignment_v3.aln34.private_calibration_loo "$@"
echo "end $(date -Is) rc=0"
