#!/bin/bash
#SBATCH --job-name=auditory_p3_ci_epochs
#SBATCH --partition=CPU
#SBATCH --array=0-7%3
#SBATCH --cpus-per-task=1
#SBATCH --mem=12G
#SBATCH --time=00:30:00
#SBATCH --output=private/slurm-%A_%a.log
set -euo pipefail
umask 077
cd /home/infres/yinwang/EEG_auditory
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
/home/infres/yinwang/anaconda3/envs/eeg2025/bin/python scripts/phase3_ci_epochs.py "$@"
