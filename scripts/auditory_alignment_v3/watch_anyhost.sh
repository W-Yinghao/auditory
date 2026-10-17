#!/bin/bash
# Host-independent fleet watcher (the orchestrators may run on another host, invisible to ps). Exits, printing EVENT ..., on the
# first condition needing attention; polls every 60 s. v2 (2026-10-11): also watches the checkpoint offload daemon and the
# B/C breadth milestone that gates the D policy arms. v3 (2026-10-14 13:35): no keeper strike while the keeper log is < 3 min old
# (the 13:32 ramp-up after the B_ALIGNED release was a false alarm). v4 (ALN3.4 E34_PUBLIC_PRIOR, PUBLIC_PRIOR_DESIGN.md §6.5):
# spec "queue_v3_prior c3_aln3pr 4 120 9" (optional fields 4-5: keeper-log age in s before a strike, strikes for the EVENT; fm and
# small keep 180 and 10). keeper_prior.sh writes a heartbeat line every 60 s, so the prior EVENT comes about 10 min after its last
# heartbeat while workers are missing and rows are unclaimed; a spec without a queue file is skipped. Two more prior EVENTs: the
# keeper is alive but its last 10 heartbeats all report 'sbatch refused' or 'squeue failed', and queue_v3_prior.remaining has held
# a non-integer other than 'held' (make_queue.py's prior-queue error marker 'unknown', or no file) for 20 consecutive minutes.
cd /home/infres/yinwang/EEG_auditory
OUT=private/auditory_alignment_v3
PY=/home/infres/yinwang/anaconda3/envs/eeg2025/bin/python
F="$OUT/pool/*/*.failed private/auditory_alignment_v2/pool/queue_fm/*.failed private/auditory_alignment_v2/pool/queue_small/*.failed"
nf0=$(ls $F 2>/dev/null | xargs -r grep -L DESCOPED 2>/dev/null | wc -l)
err0=$(grep -c ERROR $OUT/logs/ckpt_offload.log 2>/dev/null); err0=${err0:-0}  # grep -c prints 0 and exits 1 on no match
declare -A strikes
tick=0; offmiss=0
unclaimed() {  # same count as keeper.sh
  local Q=$1 C=$OUT/pool/$(basename $1 .txt) left=0
  while IFS='|' read -r eid idx; do
    [ -z "$eid" ] && continue; [ -e "$OUT/units/$eid.json" ] && continue; [ -e "$C/$eid.failed" ] && continue; [ -d "$C/$eid.claim" ] && continue
    left=$((left+1))
  done < "$Q"
  echo $left
}
bc_done() {  # prints 'yes' once every seed-3401 B_DENSE and C_COMPLEMENT row has a unit record
  PYTHONPATH=$PWD PYTHONDONTWRITEBYTECODE=1 $PY -c "
import os, json
from auditory_alignment_v3 import core
rows = core.load_rows()
need = [r['experiment_id'] for r in rows if r['family_id'] in ('B_DENSE', 'C_COMPLEMENT') and r['seed'] == 3401]
print('yes' if need and all(os.path.exists(f'$OUT/units/{e}.json') for e in need) else 'no')" 2>/dev/null
}
bc_reported=$( [ "$(bc_done)" = yes ] && echo 1 || echo 0 )
while true; do
  tick=$((tick+1))
  jobs=$(squeue -u $USER -h -o "%j" 2>/dev/null) || jobs=SQUEUE_FAIL
  for spec in "queue_v3_fm c3_aln3fm 10" "queue_v3_small c3_aln3sm 4" "queue_v3_prior c3_aln3pr 4 120 9"; do
    set -- $spec; q=$1; name=$2; maxg=$3; stale=${4:-180}; need=${5:-10}
    [ -e "$OUT/STOP_$q" ] || [ "$jobs" = SQUEUE_FAIL ] && continue
    [ -e "$OUT/$q.txt" ] || continue  # e.g. the prior queue before make_queue.py writes it
    g=$(grep -cx "$name" <<< "$jobs"); n=$(squeue -u $USER -h -t PENDING -o "%j" | grep -cx "$name")
    klog=$OUT/logs/keeper_${q#queue_v3_}.log; kage=$(( $(date +%s) - $(stat -c %Y $klog 2>/dev/null || echo 0) ))  # keeper submitted within 3 min = alive (ramp-up from 0 takes ~10 min at 1 worker/min)
    if [ $g -lt $maxg ] && [ $n -lt 3 ] && [ $kage -gt $stale ] && [ "$(unclaimed $OUT/$q.txt)" -gt 0 ]; then strikes[$q]=$(( ${strikes[$q]:-0} + 1 )); else strikes[$q]=0; fi
    [ ${strikes[$q]} -ge $need ] && { echo "EVENT keeper for $q seems dead: $g/$maxg workers, $n pending, unclaimed rows, for 10 min"; exit 0; }
  done
  # v4: a prior keeper that is alive but cannot act, and a prior queue stuck in make_queue.py's error state
  pk=$OUT/logs/keeper_prior.log
  if [ -e $OUT/queue_v3_prior.txt ] && [ ! -e $OUT/STOP_queue_v3_prior ]; then
    if [ -e $pk ] && [ $(( $(date +%s) - $(stat -c %Y $pk 2>/dev/null || echo 0) )) -le 300 ] && tail -n 1 $pk | grep -qE ' heartbeat .*(sbatch refused|squeue failed)' \
       && [ "$(tail -n 400 $pk | grep ' heartbeat ' | tail -n 10 | grep -cE 'sbatch refused|squeue failed')" -ge 10 ]; then
      echo "EVENT keeper for queue_v3_prior cannot act: its last 10 heartbeats report sbatch refused / squeue failed"; tail -n 2 $pk; exit 0
    fi
    rem=$(head -c 64 $OUT/queue_v3_prior.remaining 2>/dev/null | tr -d '[:space:]')
    if [[ "$rem" =~ ^[0-9]+$ ]] || [ "$rem" = held ]; then prerr=0; else prerr=$(( ${prerr:-0} + 1 )); fi
    [ $prerr -ge 20 ] && { echo "EVENT prior queue in make_queue.py's error state for 20 min (queue_v3_prior.remaining '${rem:-missing}')"; grep -o 'prior queue error.*' $OUT/logs/refresh.log 2>/dev/null | tail -n 1 | cut -c1-300; exit 0; }
  else prerr=0; fi
  age=$(( $(date +%s) - $(stat -c %Y $OUT/logs/refresh.log) ))
  [ $age -gt 1500 ] && { echo "EVENT refresher silent for ${age}s"; exit 0; }
  nf=$(ls $F 2>/dev/null | xargs -r grep -L DESCOPED 2>/dev/null | wc -l)
  [ "$nf" -gt "$nf0" ] && { echo "EVENT new failed markers: $nf (was $nf0)"; ls -t $F 2>/dev/null | xargs -r grep -L DESCOPED | head -5; exit 0; }
  grep -lE "Disk quota exceeded|No space left" $(ls -t $OUT/logs/c3_*.log 2>/dev/null | head -20) >/dev/null 2>&1 && { echo "EVENT disk problem"; exit 0; }
  # checkpoint offload daemon: must run while ALN3 workers run (unless stopped on purpose)
  if [ "$jobs" != SQUEUE_FAIL ] && [ ! -e $OUT/STOP_ckpt_offload ] && grep -q '^c3_aln3' <<< "$jobs" && ! grep -qx c3_ckptoff <<< "$jobs"; then
    offmiss=$((offmiss+1)); [ $offmiss -ge 3 ] && { echo "EVENT checkpoint offload daemon (c3_ckptoff) not in squeue while ALN3 runs"; exit 0; }
  else offmiss=0; fi
  err=$(grep -c ERROR $OUT/logs/ckpt_offload.log 2>/dev/null); err=${err:-0}
  [ "$err" -gt "$err0" ] && { echo "EVENT offload log has new ERROR lines ($err0 -> $err)"; grep ERROR $OUT/logs/ckpt_offload.log | tail -3; exit 0; }
  if [ $((tick % 10)) -eq 0 ]; then
    kb=$(du -sk $OUT/ckpt 2>/dev/null | cut -f1)
    [ "${kb:-0}" -gt 41943040 ] && { echo "EVENT home ALN3 ckpt holds $((kb/1048576)) GiB of real files (offload falling behind?)"; exit 0; }
    if [ "$bc_reported" = 0 ] && [ "$(bc_done)" = yes ]; then echo "EVENT B/C breadth (seed 3401 B_DENSE + C_COMPLEMENT) complete: D policy arms can now be bound"; exit 0; fi
  fi
  sleep 60
done
