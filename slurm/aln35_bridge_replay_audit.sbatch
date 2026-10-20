#!/bin/bash
#SBATCH --job-name=c3_s35bridgereplay
#SBATCH --partition=CPU
#SBATCH --qos=normal
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=00:30:00
#SBATCH --output=/home/infres/yinwang/EEG_auditory/private/auditory_alignment_v3/aln35/bridge-replay-audit-%j.log
set -euo pipefail
cd /home/infres/yinwang/EEG_auditory
export OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4 PYTHONDONTWRITEBYTECODE=1
/home/infres/yinwang/anaconda3/envs/eeg2025/bin/python -B -u -m auditory_alignment_v3.aln35.bridge_factor_replay_audit
