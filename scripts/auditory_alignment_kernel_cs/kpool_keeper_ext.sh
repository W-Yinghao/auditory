#!/bin/bash
# extension queue (E10-E12): starts after the main keeper has exited; <= MAXG c3_kpoolx workers and <= 10 c3 jobs in total
cd /home/infres/yinwang/EEG_auditory
Q=private/auditory_alignment_kernel_cs/queue_ext.txt; MAXG=${1:-8}; PAR=${2:-8}
MAN=private/auditory_alignment_kernel_cs/planned_jobs_ext.jsonl
OUT=private/auditory_alignment_kernel_cs; C=$OUT/pool/$(basename $Q .txt)
echo "$(date +%T) starting extension queue (main queue complete)"
while true; do
  left=0
  while IFS='|' read -r eid idx; do
    [ -z "$eid" ] && continue; [ -e "$OUT/units/$eid.json" ] && continue; [ -e "$C/$eid.failed" ] && continue; [ -d "$C/$eid.claim" ] && continue
    left=$((left+1))
  done < "$Q"
  [ $left -eq 0 ] && { echo "$(date +%T) no unclaimed units left in $Q"; break; }
  g=$(squeue -u $USER -h -o "%j" | grep -c "^c3_kpoolx"); n=$(squeue -u $USER -h -o "%j" | grep -c "^c3")
  if [ $g -lt $MAXG ] && [ $n -lt 10 ]; then jid=$(sbatch --parsable --job-name=c3_kpoolx slurm/auditory_kcs_gpu_pool.sbatch $Q $PAR 1 $MAN run_ext) && echo "$(date +%T) ext worker $jid (c3 jobs before: $n, unclaimed: $left)"; fi
  sleep 60
done
