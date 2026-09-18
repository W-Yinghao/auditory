#!/bin/bash
#SBATCH --job-name=fseries_archival
#SBATCH --partition=CPU
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=00:20:00
set -euo pipefail
umask 077
cd /home/infres/yinwang/EEG_auditory
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export PYTHONDONTWRITEBYTECODE=1
export MPLCONFIGDIR="$PWD/private/auditory_fseries_archival/matplotlib"
exec /home/infres/yinwang/anaconda3/envs/eeg2025/bin/python -m auditory_fseries.cli "$@"
