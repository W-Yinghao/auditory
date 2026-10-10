#!/bin/bash
# keeps <= MAXG ALN2 pool workers (job name given by NAME) and <= 10 c3 jobs in total, until no unit of Q is unclaimed
cd /home/infres/yinwang/EEG_auditory
Q=$1; MAXG=${2:-8}; PAR=${3:-8}; NAME=${4:-c3_aln2pool}; MAN=${5:-AUDITORY_ALIGNMENT_NEXT_SERVER_PACKAGE_v2_20261006/plans/planned_comparisons.jsonl}; RUNNER=${6:-auditory_alignment_v2.run}
OUT=private/auditory_alignment_v2; C=$OUT/pool/$(basename $Q .txt)
while true; do
  left=0
  while IFS='|' read -r eid idx; do
    [ -z "$eid" ] && continue; [ -e "$OUT/units/$eid.json" ] && continue; [ -e "$C/$eid.failed" ] && continue; [ -d "$C/$eid.claim" ] && continue
    left=$((left+1))
  done < "$Q"
  [ $left -eq 0 ] && { echo "$(date +%T) no unclaimed units left in $Q"; break; }
  g=$(squeue -u $USER -h -o "%j" | grep -cx "$NAME"); n=$(squeue -u $USER -h -o "%j" | grep -c "^c3")
  if [ $g -lt $MAXG ] && [ $n -lt 10 ]; then jid=$(sbatch --parsable --job-name=$NAME slurm/aln2_gpu_pool.sbatch $Q $PAR 1 $MAN $RUNNER) && echo "$(date +%T) worker $jid (c3 jobs before: $n, unclaimed: $left)"; fi
  sleep 60
done
