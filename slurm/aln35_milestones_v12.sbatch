#!/bin/bash
#SBATCH --job-name=c3_aln35evidence12
#SBATCH --partition=CPU
#SBATCH --qos=normal
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=4-00:00:00
#SBATCH --output=private/auditory_alignment_v3/logs/aln35_milestones_v12.log
#SBATCH --open-mode=append
set -euo pipefail
umask 077
cd "$SLURM_SUBMIT_DIR"
export PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=$PWD
export OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4
/home/infres/yinwang/anaconda3/envs/eeg2025/bin/python -B -u private/auditory_alignment_v3/aln35/milestone_monitor_v12.py
