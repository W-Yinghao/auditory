#!/bin/bash
# Read-only takeover watcher; independent of the interactive session allocation.
# Submit from the repository root after checking for an existing c3_watchcodex job.
# The inherited watcher exits on the first EVENT; inspect watch_codex.out before restarting.
#SBATCH --job-name=c3_watchcodex
#SBATCH --partition=CPU
#SBATCH --qos=normal
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G
#SBATCH --time=4-00:00:00
#SBATCH --open-mode=append
#SBATCH --output=private/auditory_alignment_v3/logs/watch_codex.out
set -uo pipefail
umask 077
cd "$SLURM_SUBMIT_DIR" || exit 1
export PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$PWD"
echo "start $(date -Is) node=${SLURMD_NODENAME:-?} job=${SLURM_JOB_ID:-?} read-only Codex takeover watcher"
bash private/auditory_alignment_v3/watch_anyhost.sh
rc=$?
echo "end $(date -Is) rc=$rc"
exit "$rc"
