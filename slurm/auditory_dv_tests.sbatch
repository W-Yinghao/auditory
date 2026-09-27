#!/bin/bash
#SBATCH --job-name=dv_tests
#SBATCH --partition=CPU
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=01:00:00
#SBATCH --output=private/auditory_dv/logs/%x-%j.log
set -euo pipefail
umask 077
cd "$SLURM_SUBMIT_DIR"
export OMP_NUM_THREADS=2 PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=0
PY=/home/infres/yinwang/anaconda3/envs/eeg2025/bin/python
$PY -m py_compile auditory_dv/*.py
$PY -m pytest -q -p no:cacheprovider tests/auditory_dv
