#!/bin/bash
# CPU coordinator: only exact authorized project queues; no scontrol/cancellation.
#SBATCH --job-name=c3_aln34keep
#SBATCH --partition=CPU
#SBATCH --cpus-per-task=2
#SBATCH --mem=4G
#SBATCH --time=4-00:00:00
#SBATCH --open-mode=append
#SBATCH --output=private/auditory_alignment_v3/logs/aln34_fleet.log
set -euo pipefail
umask 077
cd "$SLURM_SUBMIT_DIR"
export PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=$PWD
exec /home/infres/yinwang/anaconda3/envs/eeg2025/bin/python -B -u private/auditory_alignment_v3/aln34/maintain_fleet.py
