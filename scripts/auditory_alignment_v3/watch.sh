#!/bin/bash
# exits (printing the reason) on the first event needing attention; polls every 60 s
cd /home/infres/yinwang/EEG_auditory
F="private/auditory_alignment_v3/pool/*/*.failed private/auditory_alignment_v2/pool/queue_fm/*.failed private/auditory_alignment_v2/pool/queue_small/*.failed"
nf0=$(ls $F 2>/dev/null | xargs -r grep -L DESCOPED 2>/dev/null | wc -l)
while true; do
  for k in "auditory_alignment_v3/keeper.sh private/auditory_alignment_v3/queue_v3_fm.txt" "auditory_alignment_v3/keeper.sh private/auditory_alignment_v3/queue_v3_small.txt"; do
    ps -eo args= | grep -F "$k" | grep -vq grep || { echo "EVENT keeper not running: $k"; exit 0; }
  done
  nf=$(ls $F 2>/dev/null | xargs -r grep -L DESCOPED 2>/dev/null | wc -l)
  [ "$nf" -gt "$nf0" ] && { echo "EVENT new failed markers: $nf (was $nf0)"; ls -t $F 2>/dev/null | xargs -r grep -L DESCOPED | head -5; exit 0; }
  grep -lE "Disk quota exceeded|No space left" $(ls -t private/auditory_alignment_v3/logs/c3_*.log 2>/dev/null | head -20) >/dev/null 2>&1 && { echo "EVENT disk problem"; exit 0; }
  sleep 60
done
