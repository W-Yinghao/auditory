#!/bin/bash
# exits (printing the reason) on the first event that needs attention; polls every 60 s
cd /home/infres/yinwang/EEG_auditory; O=private/auditory_alignment_v2
nf0=$(grep -L DESCOPED $O/pool/queue_fm/*.failed $O/pool/queue_lrsel/*.failed 2>/dev/null | wc -l)
while true; do
  for s in refresh_fm_queue keeper_persist; do
    ps -eo pid=,args= | awk -v s="$s" '$2=="bash" && $3 ~ s".sh$"' | grep -q . || { echo "EVENT orchestrator $s not running"; exit 0; }
  done
  nf=$(grep -L DESCOPED $O/pool/queue_fm/*.failed $O/pool/queue_lrsel/*.failed 2>/dev/null | wc -l)
  [ "$nf" -gt "$nf0" ] && { echo "EVENT new failed markers: $nf (was $nf0)"; grep -L DESCOPED $O/pool/queue_fm/*.failed $O/pool/queue_lrsel/*.failed 2>/dev/null | tail -5; exit 0; }
  ls $O/fm_recipe/*FAILED* >/dev/null 2>&1 && { echo "EVENT failed recipe"; ls $O/fm_recipe/*FAILED*; exit 0; }
  grep -lE "Disk quota exceeded|No space left" $(ls -t $O/logs/c3_aln2*.log | head -20) >/dev/null 2>&1 && { echo "EVENT disk problem in recent worker logs"; exit 0; }
  n=$(ls $O/fm_recipe | grep -v -e epochs -e FAILED | wc -l)
  grep -q reve $O/fm_recipe/epochs.json 2>/dev/null && [ ! -e $O/repair/.seen_reve_epochs ] && { touch $O/repair/.seen_reve_epochs; echo "EVENT REVE epoch budget set: $(cat $O/fm_recipe/epochs.json)"; exit 0; }
  [ "$n" -ge 80 ] && [ ! -e $O/repair/.seen_lr_done ] && { touch $O/repair/.seen_lr_done; echo "EVENT learning-rate selection complete (80 recipes)"; exit 0; }
  sleep 60
done
