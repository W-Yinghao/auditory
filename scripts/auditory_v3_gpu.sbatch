#!/bin/bash
#SBATCH --partition=A100
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=00:30:00
#SBATCH --output=private/auditory_v3/logs/gpu-%A_%a.log
set -euo pipefail
umask 077
export OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4 NUMEXPR_NUM_THREADS=4
export CUBLAS_WORKSPACE_CONFIG=:4096:8 PYTHONDONTWRITEBYTECODE=1
export AUDITORY_ROOT=/home/infres/yinwang/EEG_auditory
cd "${AUDITORY_V3_CODE:-$AUDITORY_ROOT}"
export PYTHONPATH="$PWD"
exec /home/infres/yinwang/anaconda3/envs/eeg2025/bin/python -m auditory_v3.cli "$@"
