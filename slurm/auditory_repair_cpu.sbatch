#!/bin/bash
#SBATCH --partition=CPU
#SBATCH --cpus-per-task=2
#SBATCH --mem=16G
#SBATCH --time=01:30:00
set -euo pipefail
umask 077
cd /home/infres/yinwang/EEG_auditory
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
export MPLCONFIGDIR="$PWD/private/auditory_repair/matplotlib"
exec /home/infres/yinwang/anaconda3/envs/eeg2025/bin/python -m auditory_repair.extended "$@"
