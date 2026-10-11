#!/bin/bash
# keeps <= MAXG ALN2 pool workers (job name given by NAME), at most 3 of them pending; persistent (queue refreshed elsewhere)
cd /home/infres/yinwang/EEG_auditory
Q=$1; MAXG=${2:-10}; PAR=${3:-8}; NAME=${4:-c3_aln3}
OUT=private/auditory_alignment_v3; C=$OUT/pool/$(basename $Q .txt)
while true; do
  left=0
  while IFS='|' read -r eid idx; do
    [ -z "$eid" ] && continue; [ -e "$OUT/units/$eid.json" ] && continue; [ -e "$C/$eid.failed" ] && continue; [ -d "$C/$eid.claim" ] && continue
    left=$((left+1))
  done < "$Q"
  [ -e "$OUT/STOP_$(basename $Q .txt)" ] && { echo "$(date +%T) stop file"; break; }
  [ $left -eq 0 ] && { sleep 300; continue; }  # persistent: the queue file is refreshed as dependencies resolve
  # user 2026-10-07: the self-imposed 10-job limit is lifted. The runfill QOS itself allows 10 GPUs per user, so keep up to
  # MAXG workers (running + pending) with at most 3 pending, so a preempted/finished worker is replaced at once.
  g=$(squeue -u $USER -h -o "%j" | grep -cx "$NAME"); n=$(squeue -u $USER -h -t PENDING -o "%j" | grep -cx "$NAME")
  if [ $g -lt $MAXG ] && [ $n -lt 3 ]; then jid=$(sbatch --parsable --job-name=$NAME slurm/aln3_gpu_pool.sbatch $Q $PAR 1) && echo "$(date +%T) worker $jid (workers before: $g, pending: $n, unclaimed: $left)"; fi
  sleep 60
done
