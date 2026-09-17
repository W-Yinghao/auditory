#!/usr/bin/env bash
#SBATCH --job-name=auditory5_worker
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=04:00:00
#SBATCH --output=private/auditory5_v1/logs/%x-%j.log
set -euo pipefail
umask 077
cd /home/infres/yinwang/EEG_auditory
export OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4
/home/infres/yinwang/anaconda3/envs/eeg2025/bin/python -m scripts.auditory5_worker --plan /home/infres/yinwang/EEG_auditory/private/auditory5_v1/jobs/plan_001/plan.json --resource "$1" --worker "$2"
