#!/bin/bash
#SBATCH --job-name=c3_s35pkA
#SBATCH --qos=runfill
#SBATCH --partition=A100,A40,L40S
#SBATCH --exclude=node51,node52
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=48G
#SBATCH --nice=30
#SBATCH --output=private/auditory_alignment_v3/logs/%x-%j.log
# Paper line W6: MindMix (official code, released fusion checkpoint) on KUL AAD v2.0 + shortcut audit
# (auditory_alignment_v3/paper/kul_mindmix.py), lane A = P1 paper split (KFold over windows).
# Submit args come from kul_mindmix.fleet_status('A')['submit'][1:] (e.g. --worker --lane A --max-units 4; lane A also --smoke).
# Units are ~0.1-0.3 GPU-h; resume state every 10 epochs; host RAM < 8 GB, GPU < 12 GB at batch 32 fp32.
set -euo pipefail
umask 077
cd "$SLURM_SUBMIT_DIR"
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_HUB_CACHE=/projects/EEG-foundation-model/auditory_public/derived/hf_cache/hub
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TQDM_DISABLE=1
export PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=0 PYTHONPATH=$PWD MNE_USE_NUMBA=false HF_HUB_DISABLE_PROGRESS_BARS=1
export _MNE_FAKE_HOME_DIR=$(mktemp -d)
/home/infres/yinwang/anaconda3/envs/eeg2025/bin/python -B -u -m auditory_alignment_v3.paper.kul_mindmix "$@"
