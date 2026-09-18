#!/usr/bin/env bash
#SBATCH --partition=CPU
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=01:00:00
set -euo pipefail
umask 077
cd /home/infres/yinwang/EEG_auditory
export OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4 NUMEXPR_NUM_THREADS=4 PYTHONDONTWRITEBYTECODE=1
export AUDITORY5_ROOT="$PWD"
export MPLCONFIGDIR="$PWD/private/auditory_retrain_v1/matplotlib"
exec /home/infres/yinwang/anaconda3/envs/eeg2025/bin/python -m auditory_retrain.run "$@"
