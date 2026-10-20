#!/bin/bash
#SBATCH --job-name=c3_aln35intake
#SBATCH --partition=CPU
#SBATCH --qos=normal
#SBATCH --cpus-per-task=2
#SBATCH --mem=4G
#SBATCH --time=00:20:00
#SBATCH --output=private/auditory_alignment_v3/aln35/bootstrap-%j.log
set -euo pipefail
cd "$SLURM_SUBMIT_DIR"
export PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2
/home/infres/yinwang/anaconda3/envs/eeg2025/bin/python -B -u private/auditory_alignment_v3/aln35/bootstrap_20261019.py
