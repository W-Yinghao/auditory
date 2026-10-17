#!/bin/bash
# Verify the new intervention and freeze its independent 150-unit plan.
#SBATCH --job-name=c3_budregister
#SBATCH --qos=normal
#SBATCH --partition=CPU
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=00:30:00
#SBATCH --output=private/auditory_alignment_v3/logs/%x-%j.log
set -euo pipefail
umask 077
cd "$SLURM_SUBMIT_DIR"
export PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=$PWD PYTHONHASHSEED=0 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 MNE_USE_NUMBA=false
export OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2
export _MNE_FAKE_HOME_DIR=$(mktemp -d)
PY=/home/infres/yinwang/anaconda3/envs/eeg2025/bin/python
echo "start $(date -Is) job=$SLURM_JOB_ID"
$PY -B -m pytest -p no:cacheprovider -q tests/auditory_alignment_v3/aln34/test_learning_budget.py
$PY -B -u -m auditory_alignment_v3.aln34.learning_budget --make-plan
echo "end $(date -Is) rc=0"
