#!/bin/bash
#SBATCH --job-name=c3_s35bridge
#SBATCH --qos=runfill
#SBATCH --partition=A100,L40S,A40,A30,V100
#SBATCH --exclude=node52
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=02:00:00
#SBATCH --nice=15
#SBATCH --output=private/auditory_alignment_v3/aln35/bridge-fleet-%j.log
set -euo pipefail
umask 077
cd "$SLURM_SUBMIT_DIR"
export PYTHONPATH=$PWD PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 CUBLAS_WORKSPACE_CONFIG=:4096:8
/home/infres/yinwang/anaconda3/envs/eeg2025/bin/python -B -u -m auditory_alignment_v3.aln35.bridge_factor_fleet "$@"
