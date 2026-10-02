#!/bin/bash
#SBATCH --job-name=story_tests
#SBATCH --qos=runfill
#SBATCH --partition=CPU
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=00:30:00
#SBATCH --requeue
#SBATCH --output=private/auditory_story/logs/%x-%j.log
set -euo pipefail
umask 077
cd "$SLURM_SUBMIT_DIR"
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2 PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=0
exec /home/infres/yinwang/anaconda3/envs/eeg2025/bin/python -m pytest -q -p no:cacheprovider tests/auditory_story "$@"
