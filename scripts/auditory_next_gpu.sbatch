#!/bin/bash
#SBATCH --partition=A100
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=2
#SBATCH --mem=64G
#SBATCH --time=06:00:00
#SBATCH --output=private/auditory_next_v2/logs/gpu-%j.log
set -euo pipefail
umask 077
# The user's hardware floor also applies to explicit sbatch overrides.
if [[ "${SLURM_JOB_PARTITION:-}" == "P100" ]]; then
    echo "P100 is disabled by project GPU policy." >&2
    exit 2
fi
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2 NUMEXPR_NUM_THREADS=2
export AUDITORY5_ROOT=/home/infres/yinwang/EEG_auditory
export AUDITORY_NEXT_ROOT="$AUDITORY5_ROOT"
export PYTHONDONTWRITEBYTECODE=1
cd "$AUDITORY_NEXT_ROOT"
if [[ -f "private/auditory_next_v2/logs/gpu-${SLURM_JOB_ID}.log" && ! -L "private/auditory_next_v2/logs/gpu-${SLURM_JOB_ID}.log" ]]; then
    chmod 600 "private/auditory_next_v2/logs/gpu-${SLURM_JOB_ID}.log"
fi
exec /home/infres/yinwang/anaconda3/envs/eeg2025/bin/python -m auditory_next.cli --config configs/auditory_next_v2.yaml "$@"
