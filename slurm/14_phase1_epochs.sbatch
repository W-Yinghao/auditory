#!/bin/bash
#SBATCH --job-name=auditory_p1_epochs
#SBATCH --partition=CPU
#SBATCH --cpus-per-task=2
#SBATCH --mem=6G
#SBATCH --time=00:30:00
#SBATCH --array=0-7%4
#SBATCH --output=private/slurm-%A_%a.log
set -euo pipefail
umask 077
cd /home/infres/yinwang/EEG_auditory
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
/home/infres/yinwang/anaconda3/envs/eeg2025/bin/python scripts/phase1_epochs.py --run phase1_epochs_001 --shard "$SLURM_ARRAY_TASK_ID" --shards 8
