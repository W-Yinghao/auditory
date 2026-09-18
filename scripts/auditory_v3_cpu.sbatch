#!/bin/bash
#SBATCH --partition=CPU
#SBATCH --cpus-per-task=2
#SBATCH --mem=16G
#SBATCH --time=00:15:00
#SBATCH --output=private/auditory_v3/logs/cpu-%j.log
set -euo pipefail
umask 077
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2 NUMEXPR_NUM_THREADS=2
export PYTHONDONTWRITEBYTECODE=1
# Verified configs/auditory_next_site.local.yaml; no environment changes.
export AUDITORY_ROOT=/home/infres/yinwang/EEG_auditory
cd "${AUDITORY_V3_CODE:-$AUDITORY_ROOT}"
export PYTHONPATH="$PWD"
exec /home/infres/yinwang/anaconda3/envs/eeg2025/bin/python -m auditory_v3.cli "$@"
