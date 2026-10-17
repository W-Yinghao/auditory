#!/bin/bash
# FIXC -> core manifest -> eligible-window rich PCA refit -> rich manifest -> M12 preflight.
# Submit only after the synthetic suite passes. No production plan rows are registered here.
#SBATCH --job-name=c3_p33freeze
#SBATCH --qos=normal
#SBATCH --partition=CPU
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=1-00:00:00
#SBATCH --open-mode=append
#SBATCH --output=private/auditory_alignment_v3/logs/%x-%j.log
set -euo pipefail
umask 077
cd "$SLURM_SUBMIT_DIR"
export PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=$PWD PYTHONHASHSEED=0 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 MNE_USE_NUMBA=false
export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK MKL_NUM_THREADS=$SLURM_CPUS_PER_TASK OPENBLAS_NUM_THREADS=$SLURM_CPUS_PER_TASK
export _MNE_FAKE_HOME_DIR=$(mktemp -d)
PY=/home/infres/yinwang/anaconda3/envs/eeg2025/bin/python
CACHE=/projects/EEG-foundation-model/auditory_public/derived/aln33_env64_125ms_v1
echo "start $(date -Is) job=$SLURM_JOB_ID node=$SLURMD_NODENAME"
$PY -B -m auditory_alignment_v3.prior33.manifest --part core --root "$CACHE"
$PY -B -m auditory_alignment_v3.prior33.refit_rich --out "$CACHE"
$PY -B -m auditory_alignment_v3.prior33.manifest --part rich --root "$CACHE"
$PY -B private/auditory_alignment_v3/probe_prior33.py --check-only
$PY -B private/auditory_alignment_v3/make_plan_ext_prior33.py --dry-run
sbatch --test-only slurm/aln33_prior_pool.sbatch
echo "end $(date -Is) rc=0"
