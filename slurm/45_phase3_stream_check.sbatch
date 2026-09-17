#!/bin/bash
#SBATCH --job-name=auditory_p3_stream_check
#SBATCH --partition=CPU
#SBATCH --cpus-per-task=1
#SBATCH --mem=8G
#SBATCH --time=00:08:00
#SBATCH --output=private/slurm-%j.log
set -euo pipefail
umask 077
cd /home/infres/yinwang/EEG_auditory
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
/home/infres/yinwang/anaconda3/envs/eeg2025/bin/python scripts/phase3_stream_check.py
