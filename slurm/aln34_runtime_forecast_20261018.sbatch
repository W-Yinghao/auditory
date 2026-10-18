#!/bin/bash
#SBATCH --job-name=c3_eta18
#SBATCH --partition=CPU
#SBATCH --qos=normal
#SBATCH --cpus-per-task=2
#SBATCH --mem=4G
#SBATCH --time=00:10:00
#SBATCH --output=private/auditory_alignment_v3/logs/c3_eta18-%j.log
set -euo pipefail
umask 077
cd "$SLURM_SUBMIT_DIR"
export PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$PWD" OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2
/home/infres/yinwang/anaconda3/envs/eeg2025/bin/python -B -u private/auditory_alignment_v3/aln34/runtime_audit_20261018.py
/home/infres/yinwang/anaconda3/envs/eeg2025/bin/python -B -u private/auditory_alignment_v3/aln34/runtime_forecast_20261018.py
