#!/bin/bash
#SBATCH --job-name=c3_s35dMcpuU
#SBATCH --partition=CPU
#SBATCH --qos=normal
#SBATCH --cpus-per-task=48
#SBATCH --mem=48G
#SBATCH --time=2-00:00:00
#SBATCH --output=private/auditory_alignment_v3/logs/%x-%j.log
# DEP12 public feature units on CPU (Agent M), used while the GPU partitions are saturated: unit --id ID for each argument,
# device recorded as 'cpu' in the unit receipt (same code path as the GPU lane; the GPU worker skips completed units).
set -euo pipefail
umask 077
cd "$SLURM_SUBMIT_DIR"
export OMP_NUM_THREADS=48 MKL_NUM_THREADS=48 OPENBLAS_NUM_THREADS=48 PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=0 PYTHONPATH=$PWD
export DEP12_DEVICE=cpu HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 MNE_USE_NUMBA=false
for uid in "$@"; do
  /home/infres/yinwang/anaconda3/envs/eeg2025/bin/python -B -u -m auditory_alignment_v3.dep12.public_features claim-unit --id "$uid"
done
