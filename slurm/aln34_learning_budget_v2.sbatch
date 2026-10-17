#!/bin/bash
# Independent-plan ALN3.4 matched doubled-budget workers; whole GPU, runfill.
# --smoke exercises CBraMod, local and REVE before the production workers start.
#SBATCH --job-name=c3_aln34budget
#SBATCH --qos=runfill
#SBATCH --partition=A30,A40,L40S
#SBATCH --exclude=node52
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=12
#SBATCH --mem=64G
#SBATCH --nice=10
#SBATCH --open-mode=append
#SBATCH --output=private/auditory_alignment_v3/logs/%x-%j.log
set -euo pipefail
umask 077
cd "$SLURM_SUBMIT_DIR"
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 OMP_NUM_THREADS=12 MKL_NUM_THREADS=12 OPENBLAS_NUM_THREADS=12
export PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=0 PYTHONPATH=$PWD MNE_USE_NUMBA=false
export _MNE_FAKE_HOME_DIR=$(mktemp -d)
echo "start $(date -Is) job=$SLURM_JOB_ID node=$SLURMD_NODENAME args=$*"
/home/infres/yinwang/anaconda3/envs/eeg2025/bin/python -B -u -m auditory_alignment_v3.aln34.learning_budget_v2 "$@"
echo "end $(date -Is) rc=0"
