#!/bin/bash
# ALN3: rebuild both queues every 10 min (dependency-gated rows enter as bases complete) and release claims of non-running workers
cd /home/infres/yinwang/EEG_auditory
while true; do
  PYTHONPATH=$PWD /home/infres/yinwang/anaconda3/envs/eeg2025/bin/python private/auditory_alignment_v3/make_queue.py 2>&1 | tr '\n' ' ' | sed "s/^/$(date +%T) /"; echo
  live=$(squeue -u $USER -h -t RUNNING,CONFIGURING,COMPLETING -o "%i") && [ -n "$live" ] && for d in private/auditory_alignment_v3/pool/*/*.claim; do
    [ -d "$d" ] && [ -n "$(find "$d" -maxdepth 0 -mmin +2)" ] || continue
    o=$(cat "$d/job" 2>/dev/null); [ -n "$o" ] && ! grep -qx "$o" <<< "$live" && { rm -rf "$d"; echo "$(date +%T) released claim $(basename $d .claim) of non-running job $o"; }
  done
  sleep 600
done
