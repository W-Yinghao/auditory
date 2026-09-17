#!/usr/bin/env bash
#SBATCH --job-name=auditory5_mff_export
#SBATCH --partition=CPU
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=02:00:00
#SBATCH --array=0-1%2
#SBATCH --output=private/auditory5_v1/logs/%x-%A_%a.log
set -euo pipefail
umask 077
cd /home/infres/yinwang/EEG_auditory
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2
/home/infres/yinwang/anaconda3/envs/eeg2025/bin/python -m auditory5.cli export-eeg --run mff_e0_export_001 --bank P1_CAUSAL20 --branch MFF --mff-pairs --mff-view E0_BLOCK_RESET_60S --contract-run contracts_007 --shards 2 --shard "$SLURM_ARRAY_TASK_ID"
