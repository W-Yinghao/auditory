#!/usr/bin/env bash
#SBATCH --job-name=auditory5_representation
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=04:00:00
#SBATCH --output=private/auditory5_v1/logs/%x-%A_%a.log
set -euo pipefail
umask 077
cd /home/infres/yinwang/EEG_auditory
export OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4
/home/infres/yinwang/anaconda3/envs/eeg2025/bin/python -m auditory5.cli --config configs/auditory5_v1.yaml run-job --plan "$1" --index "$SLURM_ARRAY_TASK_ID"
