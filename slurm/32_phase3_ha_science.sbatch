#!/bin/bash
#SBATCH --job-name=phase3_ha_science
#SBATCH --partition=CPU
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G
#SBATCH --time=00:10:00
#SBATCH --output=private/phase3-ha-science-%j.log
set -euo pipefail
cd "$SLURM_SUBMIT_DIR"
umask 077
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
/home/infres/yinwang/anaconda3/envs/eeg2025/bin/python scripts/phase3_ha_science.py "$@"
