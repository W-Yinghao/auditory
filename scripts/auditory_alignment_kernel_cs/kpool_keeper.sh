#!/bin/bash
# keeps <= MAXG kernel-CS GPU pool workers and <= 10 c3 jobs in total, until no unit is left unclaimed
cd /home/infres/yinwang/EEG_auditory
Q=$1; MAXG=${2:-8}; PAR=${3:-8}; MPS=${4:-1}
OUT=private/auditory_alignment_kernel_cs; C=$OUT/pool/$(basename $Q .txt)
while true; do
  left=0
  while IFS='|' read -r eid idx; do
    [ -z "$eid" ] && continue; [ -e "$OUT/units/$eid.json" ] && continue; [ -e "$C/$eid.failed" ] && continue; [ -d "$C/$eid.claim" ] && continue
    left=$((left+1))
  done < "$Q"
  [ $left -eq 0 ] && { echo "$(date +%T) no unclaimed units left in $Q"; break; }
  g=$(squeue -u $USER -h -o "%j" | grep -c "^c3_kpool"); n=$(squeue -u $USER -h -o "%j" | grep -c "^c3")
  if [ $g -lt $MAXG ] && [ $n -lt 10 ]; then jid=$(sbatch --parsable slurm/auditory_kcs_gpu_pool.sbatch $Q $PAR $MPS) && echo "$(date +%T) kpool worker $jid (c3 jobs before: $n, unclaimed: $left)"; fi
  sleep 60
done
