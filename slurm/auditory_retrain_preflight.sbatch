#!/usr/bin/env bash
#SBATCH --partition=CPU
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=00:15:00
set -euo pipefail
umask 077
cd /home/infres/yinwang/EEG_auditory
export OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4 NUMEXPR_NUM_THREADS=4 PYTHONDONTWRITEBYTECODE=1
export AUDITORY5_ROOT="$PWD"
exec /home/infres/yinwang/anaconda3/envs/eeg2025/bin/python -m auditory_retrain.preflight "$@"
