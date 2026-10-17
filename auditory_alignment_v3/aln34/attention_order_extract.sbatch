#!/bin/bash
# R34_ATTENTION_ORDER stage 1 (score extraction), v2 (private/auditory_alignment_v3/aln34/ATTENTION_ORDER_NOTE.md section 11).
# NOT submitted by the writing agent. One job per partition; the partition is given at submission, e.g.
#   sbatch --partition=A40 auditory_alignment_v3/aln34/attention_order_extract.sbatch
#   sbatch --partition=V100-16GB --exclude=node42 auditory_alignment_v3/aln34/attention_order_extract.sbatch
#   sbatch --partition=V100-32GB auditory_alignment_v3/aln34/attention_order_extract.sbatch
#   sbatch --partition=A30 auditory_alignment_v3/aln34/attention_order_extract.sbatch
# Each job runs ONE process over the whole unit list; the script extracts only the units whose unit record names the GPU model of
# this job (the others are skipped and listed), sorted by cohort so each (dataset, content fold) cohort loads once.
# --qos=runfill: the scheduler counts the job against the per-user gres/gpu=10 limit (MaxTRESPU) shared with the pool; while 10 GPUs
# are in use it pends (QOSMaxGRESPerUser). Requeue-safe: existing score files are skipped.
#SBATCH --job-name=c3_aoextract
#SBATCH --qos=runfill
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --requeue
#SBATCH --open-mode=append
#SBATCH --output=private/auditory_alignment_v3/logs/%x-%j.log
set -uo pipefail
umask 077
cd "$SLURM_SUBMIT_DIR"
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4 PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=0 PYTHONPATH=$PWD
export _MNE_FAKE_HOME_DIR=$(mktemp -d) MNE_USE_NUMBA=false
PY=/home/infres/yinwang/anaconda3/envs/eeg2025/bin/python
echo "start $(date -Is) node=${SLURMD_NODENAME:-?} gpu=$(nvidia-smi --query-gpu=name --format=csv,noheader | head -1) restart=${SLURM_RESTART_COUNT:-0} job=${SLURM_JOB_ID:-?}"
$PY -B -m auditory_alignment_v3.aln34.attention_order --unit-list private/auditory_alignment_v3/aln34/attention_order_units.txt --device cuda
rc=$?
echo "end $(date -Is) rc=$rc"
exit $rc
