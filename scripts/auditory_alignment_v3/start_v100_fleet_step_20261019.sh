#!/bin/bash
# Client-side orchestration only; all coordinator work runs inside Slurm1047358.
set -euo pipefail
cd /home/infres/yinwang/EEG_auditory
umask 077
out=private/auditory_alignment_v3/aln35/v100_20261019
test -f "$out/routing_check.json"
test ! -e "$out/step_client_v2.pid"
nohup srun --jobid=1047358 --overlap --exact --nodes=1 --ntasks=1 \
  --cpus-per-task=1 --mem=4G \
  --chdir=/home/infres/yinwang/EEG_auditory \
  --export=ALL,PYTHONDONTWRITEBYTECODE=1,PYTHONPATH=/home/infres/yinwang/EEG_auditory,OMP_NUM_THREADS=1,MKL_NUM_THREADS=1,OPENBLAS_NUM_THREADS=1 \
  /home/infres/yinwang/anaconda3/envs/eeg2025/bin/python -B -u \
  private/auditory_alignment_v3/aln35/start_v100_fleet_step.py \
  > "$out/fleet_step_v2.log" 2>&1 < /dev/null &
task_client_pid=$!
printf '%s\n' "$task_client_pid" > "$out/step_client_v2.pid"
printf 'Started Slurm step client %s; waiting for old scheduler handoff.\n' "$task_client_pid"
