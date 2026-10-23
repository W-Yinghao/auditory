#!/bin/bash
#SBATCH --job-name=c3_s35dPmff
#SBATCH --qos=runfill
#SBATCH --partition=A100,A30,A40,L40S
#SBATCH --exclude=node51,node52
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=96G
#SBATCH --nice=30
#SBATCH --output=private/auditory_alignment_v3/logs/%x-%j.log
# DEP12 Agent P: MFF pure-tone / bapa extension (auditory_alignment_v3/dep12/private_mff.py); --smoke | --worker | --post.
set -euo pipefail
umask 077
cd "$SLURM_SUBMIT_DIR"
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8
export PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=0 PYTHONPATH=$PWD MNE_USE_NUMBA=false HF_HUB_DISABLE_PROGRESS_BARS=1
export _MNE_FAKE_HOME_DIR=$(mktemp -d)
/home/infres/yinwang/anaconda3/envs/eeg2025/bin/python -B -u -m auditory_alignment_v3.dep12.private_mff "$@"
