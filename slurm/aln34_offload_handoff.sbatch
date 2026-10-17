#!/bin/bash
# Start the replacement allocation FIRST, then ask the old daemon to stop through
# its documented STOP file. The new daemon starts only after both job and lock exit.
# This gives an actual allocation instead of relying on sbatch's conservative ETA.
#SBATCH --job-name=c3_ckptoff
#SBATCH --partition=CPU
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=2-00:00:00
#SBATCH --open-mode=append
#SBATCH --signal=B:TERM@120
#SBATCH --output=private/auditory_alignment_v3/logs/%x-%j.log
set -euo pipefail
umask 077
cd "$SLURM_SUBMIT_DIR"
old=${1:?exact old offload job id required}
[[ "$old" =~ ^[0-9]+$ ]] || exit 2
out=private/auditory_alignment_v3
stop=$out/STOP_ckpt_offload
test ! -e "$stop"
line=$(squeue -j "$old" -h -o '%j' 2>/dev/null)
test "$line" = c3_ckptoff
echo "HANDOFF allocated $(date -Is) job=$SLURM_JOB_ID old=$old"
touch "$stop"
free=0
for attempt in $(seq 1 120); do
  state=$(squeue -j "$old" -h -o '%T' 2>/dev/null) || exit 3
  if [ -z "$state" ] && flock -n "$out/.ckpt_offload.lock" true; then free=1; break; fi
  sleep 5
done
test "$free" = 1
mv "$stop" "$out/aln34/STOP_ckpt_offload.handoff_${old}_${SLURM_JOB_ID}"
echo "$(date -Is) offload handoff old=$old exited; lock free; replacement=$SLURM_JOB_ID" >> "$out/logs/operations.log"
echo "HANDOFF complete $(date -Is); starting patched daemon"
exec bash slurm/aln3_ckpt_offload.sbatch
