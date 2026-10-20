#!/bin/bash
#SBATCH --job-name=c3_aln35science
#SBATCH --partition=CPU
#SBATCH --qos=normal
#SBATCH --cpus-per-task=2
#SBATCH --mem=20G
#SBATCH --time=01:00:00
#SBATCH --output=/home/infres/yinwang/EEG_auditory/private/auditory_alignment_v3/aln35/science/science-%j.log
set -euo pipefail
cd /home/infres/yinwang/EEG_auditory
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2 PYTHONDONTWRITEBYTECODE=1
/home/infres/yinwang/anaconda3/envs/eeg2025/bin/python -B -m pytest -q tests/auditory_alignment_v3/aln35/test_science_binding.py
/home/infres/yinwang/anaconda3/envs/eeg2025/bin/python -B -u -m auditory_alignment_v3.aln35.science_run
