#!/bin/bash
#SBATCH --job-name=c3_aln34keep16
#SBATCH --partition=CPU
#SBATCH --qos=normal
#SBATCH --cpus-per-task=2
#SBATCH --mem=4G
#SBATCH --time=4-00:00:00
#SBATCH --output=private/auditory_alignment_v3/logs/aln34_fleet_v16.log
#SBATCH --open-mode=append
set -euo pipefail
umask 077
cd "$SLURM_SUBMIT_DIR"
export PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=$PWD
/home/infres/yinwang/anaconda3/envs/eeg2025/bin/python -B -u private/auditory_alignment_v3/aln34/maintain_fleet_v16.py
