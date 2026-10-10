#!/bin/bash
#SBATCH --job-name=c3_aln2gprobe
# ALN2 GPU engineering check: runs the python script given as arguments on one whole GPU (no MPS)
#SBATCH --qos=runfill
#SBATCH --partition=A100,A40,L40S,A30
#SBATCH --exclude=node52
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=12
#SBATCH --mem=64G
#SBATCH --time=4:00:00
#SBATCH --open-mode=append
#SBATCH --output=private/auditory_alignment_v2/logs/%x-%j.log
set -uo pipefail
umask 077
cd "$SLURM_SUBMIT_DIR"
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 OMP_NUM_THREADS=12 MKL_NUM_THREADS=12 PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=0 PYTHONPATH=$PWD _MNE_FAKE_HOME_DIR=$(mktemp -d) MNE_USE_NUMBA=false
echo "start $(date -Is) node=${SLURMD_NODENAME:-?} gpu=$(nvidia-smi --query-gpu=name --format=csv,noheader) args=$*"
/home/infres/yinwang/anaconda3/envs/eeg2025/bin/python "$@"
echo "end $(date -Is) rc=$?"
