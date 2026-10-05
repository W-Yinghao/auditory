#!/bin/bash
#SBATCH --job-name=c3_gpool
# C3 v1 job pool (user 2026-10-05: at most 10 Slurm slots; batch several CPU units per submission). Each worker claims
# units from a queue file (atomic mkdir claim) and runs PAR of them concurrently; a requeued worker releases its own
# unfinished claims; stale claims of workers no longer in the queue are released; a unit is tried at most 3 times.
#SBATCH --qos=runfill
#SBATCH --partition=A100,A40,L40S,A30
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=96G
#SBATCH --time=12:00:00
#SBATCH --requeue
#SBATCH --open-mode=append
#SBATCH --output=private/auditory_c3/logs/%x-%j.log
set -uo pipefail
umask 077
cd "$SLURM_SUBMIT_DIR"
Q=$1; PAR=${2:-3}
TH=$(( ${SLURM_CPUS_PER_TASK:-8} / PAR ))
export OMP_NUM_THREADS=$TH OPENBLAS_NUM_THREADS=$TH MKL_NUM_THREADS=$TH PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=0
export _MNE_FAKE_HOME_DIR=$(mktemp -d) MNE_USE_NUMBA=false
PY=/home/infres/yinwang/anaconda3/envs/eeg2025/bin/python
C=private/auditory_c3/pool/$(basename $Q .txt); mkdir -p $C
ME=$SLURM_JOB_ID
echo "start $(date -Is) node=${SLURMD_NODENAME:-?} restart=${SLURM_RESTART_COUNT:-0} job=$ME queue=$Q par=$PAR"
live=$(squeue -u $USER -h -o "%i")
for d in $C/*.claim; do
  [ -d "$d" ] || continue
  owner=$(cat $d/job 2>/dev/null)
  if [ "$owner" = "$ME" ] || ! grep -qx "$owner" <<< "$live"; then rm -rf "$d"; fi
done
run_unit() {  # name out cmd...
  local name=$1 out=$2; shift 2
  local t0=$(date +%s)
  $PY -m auditory_c3.$* > private/auditory_c3/logs/unit_${name}.log 2>&1
  local rc=$?
  if [ $rc -eq 0 ] && [ -e "$out" ]; then echo "$(date +%T) done $name $(( $(date +%s)-t0 ))s"; touch $C/$name.done
  else n=$(( $(cat $C/$name.tries 2>/dev/null || echo 0) + 1 )); echo $n > $C/$name.tries
       echo "$(date +%T) FAIL $name rc=$rc try=$n"; [ $n -ge 3 ] && touch $C/$name.failed; fi
  rm -rf $C/$name.claim
}
while true; do
  claimed=0
  while IFS='|' read -r name out cmd; do
    [ -z "$name" ] && continue
    [ -e "$out" ] && continue
    [ -e "$C/$name.failed" ] && continue
    while [ "$(jobs -rp | wc -l)" -ge "$PAR" ]; do sleep 5; done
    if mkdir $C/$name.claim 2>/dev/null; then
      echo $ME > $C/$name.claim/job
      claimed=1
      run_unit "$name" "$out" $cmd &
    fi
  done < "$Q"
  wait
  [ $claimed -eq 0 ] && break
done
echo "end $(date -Is) job=$ME"
