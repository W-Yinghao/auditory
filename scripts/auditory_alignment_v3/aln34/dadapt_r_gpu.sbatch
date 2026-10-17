#!/bin/bash
# TEMPLATE written by auditory_alignment_v3.aln34.dadapt_r --write-units (2026-10-17 01:34 CEST); execution R34_DADAPT_R_v1.
# NOT submitted by this lane. Submitting it is an operational step inside the project's 10-GPU cap (shared with the c3_aln3fm pool
# and the other lanes). Each array task is one GPU running PAR concurrent worker loops (default 2) over the unit list: own shard first,
# then the rest; every unit runs in a fresh subprocess; atomic claims (<out>/claims/<eid>.claim) prevent duplicate work; finished units
# (<out>/<eid>.json) are skipped; a unit is tried at most 3 times; a requeued task releases its own claims and redoes its unfinished
# units from scratch (a unit takes about 0.5-8 min). Claims record SLURM_JOB_ID and <array job>_<task>; the sweep checks both squeue
# id forms (%A and %i), and a worker removes only its own claims (note, addendum 2, C2). Per-unit outputs (per-participant values)
# go to private/auditory_alignment_v3/aln34/dadapt_r/units/ (note, addendum 2, C3).
# Partition A40: the device of all 200 source records (TF32 cuDNN convolutions by default), so the numerics stay closest to the records.
# Other cards should also pass the QC tolerance (the CPU FP32 checks matched the A40 records within 2e-4 bits): A30 / L40S / V100 can be
# added if A40 is congested; A100 / H100 would need --time under the slot policy.
# Estimate (assumption-based, from the records' wall times): 228.1 unit-minutes for 200 pending units (range 175.8-367.1); about
# 114 GPU-minutes at PAR 2, i.e. ~29 min wall with the 4 array tasks below once they all run.
# Submit from the repo root: sbatch private/auditory_alignment_v3/aln34/dadapt_r_gpu.sbatch [PAR]
#SBATCH --job-name=c3_aln34dr
#SBATCH --nice=50
#SBATCH --qos=runfill
#SBATCH --partition=A40
#SBATCH --gres=gpu:1
#SBATCH --exclude=node52
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --array=0-3
#SBATCH --requeue
#SBATCH --open-mode=append
#SBATCH --output=private/auditory_alignment_v3/logs/%x-%A_%a.log
set -uo pipefail
umask 077
cd "$SLURM_SUBMIT_DIR"
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2 PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=0 PYTHONPATH=$PWD MNE_USE_NUMBA=false
export _MNE_FAKE_HOME_DIR=$(mktemp -d)
PY=/home/infres/yinwang/anaconda3/envs/eeg2025/bin/python
UNITS=private/auditory_alignment_v3/aln34/dadapt_r_units.txt
K=${SLURM_ARRAY_TASK_ID:-0}; N=${SLURM_ARRAY_TASK_COUNT:-1}; PAR=${1:-2}
echo "start $(date -Is) node=${SLURMD_NODENAME:-?} gpu=$(nvidia-smi --query-gpu=name --format=csv,noheader | head -1) restart=${SLURM_RESTART_COUNT:-0} job=${SLURM_JOB_ID:-?} task=$K/$N par=$PAR"
if ! $PY -c "import torch; torch.zeros(1).cuda(); torch.cuda.synchronize()" >/dev/null 2>&1; then
  echo "GPU unusable on ${SLURMD_NODENAME:-?}; exiting without claiming"; exit 0
fi
for j in $(seq 0 $((PAR-1))); do
  $PY -B -m auditory_alignment_v3.aln34.dadapt_r --units-file $UNITS --shard $((K*PAR+j))/$((N*PAR)) --worker-tag w$j --device cuda &
  sleep 30  # stagger the cohort loads (host memory)
done
wait
echo "end $(date -Is)"
