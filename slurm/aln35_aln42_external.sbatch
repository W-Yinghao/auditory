#!/bin/bash
#SBATCH --job-name=c3_s35a42ext
#SBATCH --qos=runfill
#SBATCH --partition=A100,A40,L40S
#SBATCH --exclude=node51,node52
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=12
#SBATCH --mem=64G
#SBATCH --nice=30
#SBATCH --output=private/auditory_alignment_v3/logs/%x-%j.log
# ALN4.2 R3 external method (MindMix route A). One unit per --worker job (~1-3 GPU-h, resume state every 5 epochs);
# host RAM: input cache ~6 GB + cohort load ~5 GB + one BDF filter pass ~5 GB; GPU: <= ~12 GB at batch 32 fp32.
set -euo pipefail
umask 077
cd "$SLURM_SUBMIT_DIR"
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_HUB_CACHE=/projects/EEG-foundation-model/auditory_public/derived/hf_cache/hub
export OMP_NUM_THREADS=12 MKL_NUM_THREADS=12 OPENBLAS_NUM_THREADS=12 TQDM_DISABLE=1
export PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=0 PYTHONPATH=$PWD MNE_USE_NUMBA=false HF_HUB_DISABLE_PROGRESS_BARS=1
export _MNE_FAKE_HOME_DIR=$(mktemp -d)
/home/infres/yinwang/anaconda3/envs/eeg2025/bin/python -B -u -m auditory_alignment_v3.aln42.external_mindmix "$@"
