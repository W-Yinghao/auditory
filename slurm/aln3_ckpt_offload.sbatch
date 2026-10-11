#!/bin/bash
#SBATCH --job-name=c3_ckptoff
# ALN3 checkpoint offload daemon (user approval 2026-10-11): moves *_best.pt of COMPLETED units from
# private/auditory_alignment_v3/ckpt to <private checkpoint storage>/auditory_alignment_v3/ckpt
# (verified copy + atomic per-file symlink), every 10 min until the ALN3 fleet is idle. Stop: touch private/auditory_alignment_v3/STOP_ckpt_offload
#SBATCH --partition=CPU
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G
#SBATCH --time=4-00:00:00
#SBATCH --open-mode=append
#SBATCH --signal=B:TERM@120
#SBATCH --output=private/auditory_alignment_v3/logs/%x-%j.log
set -uo pipefail
umask 077
cd "$SLURM_SUBMIT_DIR"
export PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=$PWD OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
echo "start $(date -Is) node=${SLURMD_NODENAME:-?} job=${SLURM_JOB_ID:-?}"
/home/infres/yinwang/anaconda3/envs/eeg2025/bin/python private/auditory_alignment_v3/ckpt_offload.py --interval 600 &
PID=$!; trap "kill -TERM $PID 2>/dev/null" TERM; wait $PID; rc=$?
if [ $rc -gt 128 ]; then wait $PID 2>/dev/null; rc=$?; fi  # interrupted by the TERM trap: wait for the child to finish
echo "end $(date -Is) rc=$rc"; exit $rc  # capture before $(date) runs (audit 2026-10-11)
