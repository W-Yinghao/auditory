#!/bin/bash
# Cohort-breadth modules; every GPU phase uses runfill.
#SBATCH --job-name=c3_breadth
#SBATCH --qos=runfill
#SBATCH --partition=A30,A40,L40S
#SBATCH --exclude=node52
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=12
#SBATCH --mem=64G
#SBATCH --nice=80
#SBATCH --open-mode=append
#SBATCH --output=private/auditory_alignment_v3/logs/%x-%j.log
set -euo pipefail
umask 077
cd "$SLURM_SUBMIT_DIR"
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 OMP_NUM_THREADS=12 MKL_NUM_THREADS=12 OPENBLAS_NUM_THREADS=12
export PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=0 PYTHONPATH=$PWD MNE_USE_NUMBA=false
export _MNE_FAKE_HOME_DIR=$(mktemp -d)
module=$1
shift
case "$module" in breadth_budget|breadth_inner|breadth_policy|breadth_fusion|breadth_episode) ;; *) exit 2 ;; esac
/home/infres/yinwang/anaconda3/envs/eeg2025/bin/python -B -u -m "auditory_alignment_v3.aln34.$module" "$@"
