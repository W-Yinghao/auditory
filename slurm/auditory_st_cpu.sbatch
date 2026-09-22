#!/bin/bash
#SBATCH --job-name=auditory_st
#SBATCH --partition=CPU
#SBATCH --cpus-per-task=8
#SBATCH --mem=48G
#SBATCH --time=12:00:00
#SBATCH --output=private/auditory_st/slurm-%j.log
set -euo pipefail
umask 077
cd "$SLURM_SUBMIT_DIR"
mkdir -p private/auditory_st
chmod 700 private/auditory_st || true
find private/auditory_st -maxdepth 1 -type f -name "slurm-${SLURM_JOB_ID}.log" -exec chmod 600 {} + 2>/dev/null || true
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=0 MNE_USE_NUMBA=false
exec /home/infres/yinwang/anaconda3/envs/eeg2025/bin/python -m auditory_st.cli "$@"
