#!/bin/bash
# Canonical CI source to clinical candidate linkage; no EEG amplitudes read.
# Usage: sbatch slurm/36_phase3_ci_linkage.sbatch [run_name]
# The run name is passed to the script so completed versions are immutable.
#SBATCH --job-name=auditory_p3_ci_link
#SBATCH --partition=CPU
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G
#SBATCH --time=00:08:00
#SBATCH --output=private/slurm-%j.log
set -euo pipefail
umask 077
cd /home/infres/yinwang/EEG_auditory
export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1
RUN_NAME="${1:-phase3_ci_linkage_001}"
/home/infres/yinwang/anaconda3/envs/eeg2025/bin/python scripts/phase3_ci_linkage.py --run "$RUN_NAME"
