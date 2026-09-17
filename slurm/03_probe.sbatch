#!/bin/bash
#SBATCH --job-name=auditory_probe
#SBATCH --partition=CPU
#SBATCH --cpus-per-task=2
#SBATCH --mem=12G
#SBATCH --time=00:25:00
#SBATCH --output=private/slurm-%j.log
set -euo pipefail
umask 077
cd /home/infres/yinwang/EEG_auditory
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
/home/infres/yinwang/anaconda3/envs/eeg2025/bin/python scripts/probe_formats.py
