#!/usr/bin/env bash
#SBATCH --job-name=auditory5_export
#SBATCH --partition=CPU
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=04:00:00
#SBATCH --array=0-3%2
#SBATCH --output=private/auditory5_v1/logs/%x-%A_%a.log
set -euo pipefail
umask 077
cd /home/infres/yinwang/EEG_auditory
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2
/home/infres/yinwang/anaconda3/envs/eeg2025/bin/python -m auditory5.cli --config configs/auditory5_v1.yaml export-eeg --run "$1" --bank "$2" --shard "$SLURM_ARRAY_TASK_ID" --shards 4 --contract-run contracts_005
