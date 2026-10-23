#!/bin/bash
#SBATCH --job-name=c3_s35pmmdk
#SBATCH --qos=runfill
#SBATCH --partition=A100,A30,A40,L40S
#SBATCH --exclude=node51,node52
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=48G
#SBATCH --nice=30
#SBATCH --output=private/auditory_alignment_v3/logs/%x-%j.log
# Paper line: dropout-key / shared-input shortcut audit of the complete released MindMix system (released + fine-tuned DTU / FAU
# units; zero optimiser updates). Usage: sbatch slurm/aln35_paper_mmdropkey.sbatch --smoke | --worker
set -euo pipefail
umask 077
cd "$SLURM_SUBMIT_DIR"
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_HUB_CACHE=/projects/EEG-foundation-model/auditory_public/derived/hf_cache/hub
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TQDM_DISABLE=1
export PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=0 PYTHONPATH=$PWD MNE_USE_NUMBA=false HF_HUB_DISABLE_PROGRESS_BARS=1
export _MNE_FAKE_HOME_DIR=$(mktemp -d)
/home/infres/yinwang/anaconda3/envs/eeg2025/bin/python -B -u -m auditory_alignment_v3.paper.mindmix_dropkey_audit "$@"
