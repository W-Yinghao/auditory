#!/bin/bash
#SBATCH --job-name=c3_a35sciverify
#SBATCH --partition=CPU
#SBATCH --qos=normal
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G
#SBATCH --time=00:20:00
#SBATCH --output=/home/infres/yinwang/EEG_auditory/private/auditory_alignment_v3/aln35/science/verify-%j.log
set -euo pipefail
cd /home/infres/yinwang/EEG_auditory
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
/home/infres/yinwang/anaconda3/envs/eeg2025/bin/python -B -u -m auditory_alignment_v3.aln35.science_verify
