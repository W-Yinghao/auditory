#!/bin/bash
#SBATCH --partition=CPU
#SBATCH --cpus-per-task=2
#SBATCH --mem=16G
#SBATCH --time=00:30:00
#SBATCH --output=private/auditory_v21/logs/cpu-%j.log
set -euo pipefail
umask 077
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2 NUMEXPR_NUM_THREADS=2
export PYTHONDONTWRITEBYTECODE=1
export AUDITORY5_ROOT=/home/infres/yinwang/EEG_auditory
cd "$AUDITORY5_ROOT"
exec /home/infres/yinwang/anaconda3/envs/eeg2025/bin/python -m auditory_v21.cli "$@"
