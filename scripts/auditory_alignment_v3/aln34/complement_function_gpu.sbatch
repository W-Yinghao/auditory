#!/bin/bash
# TEMPLATE written by auditory_alignment_v3.aln34.complement_function --write-units. NOT submitted by this lane; submitting it is
# an operational step inside the project's 10-GPU cap (the c3_aln3fm pool shares that cap). Settings follow slurm/aln3_gpu_pool.sbatch.
# One unit at a time per worker; several workers may run on the same list: atomic claims (<out>/claims/<eid>.claim) prevent
# duplicates, a requeued worker releases its own claims, finished units (<out>/<eid>.json) are skipped, a unit is tried at most 3 times.
#SBATCH --job-name=c3_aln34cf
#SBATCH --nice=50
#SBATCH --qos=runfill
#SBATCH --partition=A100,A40,L40S,A30,V100
#SBATCH --gres=gpu:1
#SBATCH --exclude=node52
#SBATCH --cpus-per-task=8
#SBATCH --mem=48G
#SBATCH --time=24:00:00
#SBATCH --requeue
#SBATCH --open-mode=append
#SBATCH --output=private/auditory_alignment_v3/logs/%x-%j.log
set -uo pipefail
umask 077
cd "$SLURM_SUBMIT_DIR"
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 OMP_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 MKL_NUM_THREADS=8 PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=0 PYTHONPATH=$PWD MNE_USE_NUMBA=false
export _MNE_FAKE_HOME_DIR=$(mktemp -d)
PY=/home/infres/yinwang/anaconda3/envs/eeg2025/bin/python
SHARD=${1:-}  # optional K/N (e.g. 0/4); claims alone already prevent duplicate work
$PY -B -m auditory_alignment_v3.aln34.complement_function --units-file private/auditory_alignment_v3/aln34/complement_function_units.txt --device cuda ${SHARD:+--shard $SHARD}
