#!/usr/bin/env bash
#SBATCH --job-name=auditory5_gpu
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=04:00:00
#SBATCH --output=private/auditory5_v1/logs/%x-%j.log
set -euo pipefail
umask 077
cd "${AUDITORY5_ROOT:-/home/infres/yinwang/EEG_auditory}"
export OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4
"${AUDITORY5_PYTHON:-/home/infres/yinwang/anaconda3/envs/eeg2025/bin/python}" -m auditory5.cli --config "${AUDITORY5_CONFIG:-configs/auditory5_v1.yaml}" "$@"
