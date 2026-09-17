#!/bin/bash
#SBATCH --job-name=raw_numeric_links
#SBATCH --partition=CPU
#SBATCH --cpus-per-task=1
#SBATCH --mem=8G
#SBATCH --time=00:30:00
#SBATCH --output=private/raw-numeric-links-%j.log
set -euo pipefail
cd "$SLURM_SUBMIT_DIR"
umask 077
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
/home/infres/yinwang/anaconda3/envs/eeg2025/bin/python scripts/phase3_raw_numeric_links.py
