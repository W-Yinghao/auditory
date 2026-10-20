#!/bin/bash
#SBATCH --job-name=c3_apwrongcpu
#SBATCH --partition=CPU
#SBATCH --qos=normal
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=01:30:00
#SBATCH --output=private/auditory_alignment_v3/aln35/apwrong-cpu-%j.log
set -euo pipefail
umask 077
cd "$SLURM_SUBMIT_DIR"
export PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=$PWD
export OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4
/home/infres/yinwang/anaconda3/envs/eeg2025/bin/python -B -u "$@"
