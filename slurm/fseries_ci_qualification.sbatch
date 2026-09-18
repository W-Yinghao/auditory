#!/bin/bash
#SBATCH --job-name=fseries_ci_qual
#SBATCH --partition=CPU
#SBATCH --cpus-per-task=2
#SBATCH --mem=4G
#SBATCH --time=00:10:00
#SBATCH --output=private/slurm-%j.log
set -euo pipefail
umask 077
cd /home/infres/yinwang/EEG_auditory
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
PYTHON=/home/infres/yinwang/anaconda3/envs/eeg2025/bin/python
$PYTHON -m py_compile scripts/fseries_ci_qualification.py
$PYTHON scripts/fseries_ci_qualification.py
