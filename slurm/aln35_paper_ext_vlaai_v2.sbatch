#!/bin/bash
#SBATCH --job-name=c3_s35pxvla
#SBATCH --qos=runfill
#SBATCH --partition=A100,A30,A40,L40S
#SBATCH --exclude=node51,node52
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=48G
#SBATCH --nice=30
#SBATCH --output=private/auditory_alignment_v3/logs/%x-%j.log
# Paper line Table 2 VLAAI v2 (paper/ext_vlaai_v2.py): v1 recipe and code, corrected status-gating swap check; adopts validated v1 units.
# Usage: sbatch slurm/aln35_paper_ext_vlaai_v2.sbatch worker --system vlaai_v2 --max-units N   (smoke-inherit is a CPU step)
set -euo pipefail
umask 077
cd "$SLURM_SUBMIT_DIR"
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_HUB_CACHE=/projects/EEG-foundation-model/auditory_public/derived/hf_cache/hub
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TQDM_DISABLE=1
export PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=0 PYTHONPATH=$PWD MNE_USE_NUMBA=false HF_HUB_DISABLE_PROGRESS_BARS=1
export _MNE_FAKE_HOME_DIR=$(mktemp -d)
/home/infres/yinwang/anaconda3/envs/eeg2025/bin/python -B -u -m auditory_alignment_v3.paper.ext_vlaai_v2 "$@"
