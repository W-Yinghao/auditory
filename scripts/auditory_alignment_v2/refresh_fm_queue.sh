#!/bin/bash
# rebuilds queue_fm.txt every 10 minutes (adds foundation rows whose learning-rate recipe has been chosen); file checks only
cd /home/infres/yinwang/EEG_auditory
while true; do
  /home/infres/yinwang/anaconda3/envs/eeg2025/bin/python private/auditory_alignment_v2/apply_epoch_rule.py 2>/dev/null | sed "s/^/$(date +%T) epoch rule: /"
  PYTHONPATH=$PWD /home/infres/yinwang/anaconda3/envs/eeg2025/bin/python private/auditory_alignment_v2/make_fm_queue.py 2>/dev/null | tail -1 | sed "s/^/$(date +%T) /"
  find private/auditory_alignment_v2/ckpt/ -maxdepth 1 -name "*_last.pt" -mmin +10 -delete  # user 2026-10-07: _last.pt not kept
  # release claims held by workers that are not running (preempted + requeued jobs keep their claims while pending; the
  # units resume from their checkpoints on any worker). Claims younger than 2 min are left alone (claim written before job id).
  live=$(squeue -u $USER -h -t RUNNING,CONFIGURING,COMPLETING -o "%i") && [ -n "$live" ] && for d in private/auditory_alignment_v2/pool/queue_fm/*.claim; do
    [ -d "$d" ] && [ -n "$(find "$d" -maxdepth 0 -mmin +2)" ] || continue
    o=$(cat "$d/job" 2>/dev/null); [ -n "$o" ] && ! grep -qx "$o" <<< "$live" && { rm -rf "$d"; echo "$(date +%T) released claim $(basename $d .claim) of non-running job $o"; }
  done
  sleep 600
done
