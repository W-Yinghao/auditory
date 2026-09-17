#!/bin/bash
#SBATCH --job-name=auditory_mff
#SBATCH --partition=CPU
#SBATCH --cpus-per-task=2
#SBATCH --mem=10G
#SBATCH --time=00:35:00
#SBATCH --output=private/slurm-%j.log
set -euo pipefail
umask 077
cd /home/infres/yinwang/EEG_auditory
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
/home/infres/yinwang/anaconda3/envs/eeg2025/bin/python scripts/audit_mff.py
