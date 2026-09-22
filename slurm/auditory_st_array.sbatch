#!/bin/bash
#SBATCH --job-name=auditory_st_arr
#SBATCH --partition=CPU
#SBATCH --cpus-per-task=2
#SBATCH --mem=24G
#SBATCH --time=06:00:00
#SBATCH --array=0-7
#SBATCH --output=private/auditory_st/slurm-%A_%a.log
set -euo pipefail
umask 077
cd "$SLURM_SUBMIT_DIR"
mkdir -p private/auditory_st
chmod 700 private/auditory_st || true
find private/auditory_st -maxdepth 1 -type f -name "slurm-${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID}.log" -exec chmod 600 {} + 2>/dev/null || true
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=0 MNE_USE_NUMBA=false
exec /home/infres/yinwang/anaconda3/envs/eeg2025/bin/python -m auditory_st.cli "$@"
