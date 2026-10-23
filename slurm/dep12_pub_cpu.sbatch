#!/bin/bash
#SBATCH --job-name=c3_s35dMcpu
#SBATCH --partition=CPU
#SBATCH --qos=normal
#SBATCH --cpus-per-task=4
#SBATCH --mem=24G
#SBATCH --time=12:00:00
#SBATCH --output=private/auditory_alignment_v3/logs/%x-%j.log
# DEP12 public CPU steps (Agent M): measure.py run-all -> attention.py run-all -> public_report.py (each step skips completed encoders).
set -euo pipefail
umask 022
cd "$SLURM_SUBMIT_DIR"
export OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=0 PYTHONPATH=$PWD
PY=/home/infres/yinwang/anaconda3/envs/eeg2025/bin/python
$PY -B -u -m auditory_alignment_v3.dep12.measure run-all
$PY -B -u -m auditory_alignment_v3.dep12.attention run-all
$PY -B -u -m auditory_alignment_v3.dep12.public_report
