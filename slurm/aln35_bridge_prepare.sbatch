#!/bin/bash
#SBATCH --job-name=c3_s35bridgeprep
#SBATCH --partition=CPU
#SBATCH --qos=normal
#SBATCH --cpus-per-task=2
#SBATCH --mem=12G
#SBATCH --time=00:30:00
#SBATCH --output=/home/infres/yinwang/EEG_auditory/private/auditory_alignment_v3/aln35/bridge-prepare-%j.log
set -euo pipefail
cd /home/infres/yinwang/EEG_auditory
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2 PYTHONDONTWRITEBYTECODE=1
/home/infres/yinwang/anaconda3/envs/eeg2025/bin/python -B -m pytest -q tests/auditory_alignment_v3/aln35/test_bridge_factor.py
/home/infres/yinwang/anaconda3/envs/eeg2025/bin/python -B -u -m auditory_alignment_v3.aln35.bridge_factor
