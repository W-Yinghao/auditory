#!/bin/bash
#SBATCH --job-name=c3_aln2pool
# ALN2 GPU pool (adapted from the kernel-CS pool) (user 2026-10-05: at most 10 c3 Slurm slots). Each worker claims fit units from a queue
# file (atomic mkdir claim; lines "experiment_id|job_index") and runs PAR of them concurrently on one GPU, optionally
# under CUDA MPS. A preempted/requeued worker releases its own claims; the unit then resumes from its epoch checkpoint.
# Stale claims of workers no longer in the queue are released; a unit is tried at most 3 times.
#SBATCH --qos=runfill
#SBATCH --partition=A100,A40,L40S,A30
#SBATCH --gres=gpu:1
#SBATCH --exclude=node52
#SBATCH --cpus-per-task=12
#SBATCH --mem=64G
#SBATCH --time=24:00:00
#SBATCH --requeue
#SBATCH --open-mode=append
#SBATCH --output=private/auditory_alignment_v2/logs/%x-%j.log
set -uo pipefail
umask 077
cd "$SLURM_SUBMIT_DIR"
Q=$1; PAR=${2:-8}; MPS=${3:-1}; MAN=${4:-AUDITORY_ALIGNMENT_NEXT_SERVER_PACKAGE_v2_20261006/plans/planned_comparisons.jsonl}; RUNNER=${5:-auditory_alignment_v2.run}
GPU_MB=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits | head -1)
if [ "${GPU_MB:-0}" -lt 30000 ] && [ "$PAR" -gt 5 ]; then PAR=5; fi  # 24 GB cards: 8 concurrent units can OOM
# foundation queue: weight-based admission. Units that train a foundation model have weight 1000 = one unit per card (user
# 2026-10-07); light units carry a conservative GPU-memory weight in GB (<queue>_weights.txt, written by make_fm_queue.py);
# a unit starts only if the running units' weights plus its own fit in CAP = card memory - 3 GB (a unit always starts on an
# idle card). An out-of-memory failure is not counted as a try; it lowers this worker's CAP by 6 GB (floor 12 GB); a unit
# that runs out of memory 6 times is marked failed.
CAP=100000
if [ "$RUNNER" = "auditory_alignment_v2.dispatch" ]; then CAP=$(( ${GPU_MB:-24000} / 1024 - 3 )); fi
M=$MAN
OUT=private/auditory_alignment_v2
TH=$(( ${SLURM_CPUS_PER_TASK:-12} / PAR )); [ $TH -lt 1 ] && TH=1
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 OMP_NUM_THREADS=$TH OPENBLAS_NUM_THREADS=$TH MKL_NUM_THREADS=$TH PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=0 PYTHONPATH=$PWD
export _MNE_FAKE_HOME_DIR=$(mktemp -d) MNE_USE_NUMBA=false
PY=/home/infres/yinwang/anaconda3/envs/eeg2025/bin/python
C=$OUT/pool/$(basename $Q .txt); mkdir -p $C $OUT/logs/units
ME=$SLURM_JOB_ID
echo "start $(date -Is) node=${SLURMD_NODENAME:-?} gpu=$(nvidia-smi --query-gpu=name --format=csv,noheader) restart=${SLURM_RESTART_COUNT:-0} job=$ME queue=$Q par=$PAR mps=$MPS"
if [ "$MPS" = "1" ]; then
  export CUDA_MPS_PIPE_DIRECTORY=$(mktemp -d) CUDA_MPS_LOG_DIRECTORY=$(mktemp -d)
  nvidia-cuda-mps-control -d && echo "mps on" || { echo "mps failed; plain sharing"; unset CUDA_MPS_PIPE_DIRECTORY CUDA_MPS_LOG_DIRECTORY; }
  if [ -n "${CUDA_MPS_PIPE_DIRECTORY:-}" ] && ! /home/infres/yinwang/anaconda3/envs/eeg2025/bin/python -c "import torch; torch.zeros(1).cuda(); torch.cuda.synchronize()" >/dev/null 2>&1; then
    echo "mps health check failed (CUDA init); disabling MPS, PAR 4"; echo quit | nvidia-cuda-mps-control 2>/dev/null
    unset CUDA_MPS_PIPE_DIRECTORY CUDA_MPS_LOG_DIRECTORY; PAR=4
  fi
  trap 'echo quit | nvidia-cuda-mps-control 2>/dev/null' EXIT
fi
# GPU unusable on this node even without MPS (seen 2026-10-07 on node52): claim nothing, exit; the keeper resubmits elsewhere
if ! $PY -c "import torch; torch.zeros(1).cuda(); torch.cuda.synchronize()" >/dev/null 2>&1; then
  echo "GPU unusable on ${SLURMD_NODENAME:-?} (CUDA init fails without MPS); exiting without claiming"; exit 0
fi
live=$(squeue -u $USER -h -t RUNNING,CONFIGURING,COMPLETING -o "%i")  # a requeued (pending) worker runs nothing: its claims are released (2026-10-09)
for d in $C/*.claim; do
  [ -d "$d" ] || continue
  owner=$(cat $d/job 2>/dev/null)
  if [ "$owner" = "$ME" ] || ! grep -qx "$owner" <<< "$live"; then rm -rf "$d"; fi
done
run_unit() {  # eid index
  local eid=$1 idx=$2 t0=$(date +%s)
  rm -f $OUT/units/$eid.FAILED.json
  EXTRA=""; [ "$RUNNER" = "auditory_alignment_v2.dispatch" ] && EXTRA="--eid $eid"
  local thr=$TH; [ "${WT[$eid]:-0}" -ge 1000 ] && thr=${SLURM_CPUS_PER_TASK:-12}  # exclusive (whole-card) units get all CPUs
  OMP_NUM_THREADS=$thr OPENBLAS_NUM_THREADS=$thr MKL_NUM_THREADS=$thr $PY -m $RUNNER --manifest $M --job-index $idx --out $OUT $EXTRA >> $OUT/logs/units/$eid.log 2>&1
  local rc=$?
  if [ $rc -eq 0 ] && [ -e "$OUT/units/$eid.json" ]; then echo "$(date +%T) done $eid $(( $(date +%s)-t0 ))s"
  elif tail -n 30 $OUT/logs/units/$eid.log | grep -qE "CUDA unknown error|CUDA-capable device|cudaErrorDevicesUnavailable|Disk quota exceeded|No space left on device|MPS client failed"; then
       echo "$(date +%T) INFRA $eid rc=$rc (node/disk problem; not counted as a try; worker stops claiming)"; touch $C/.infra_$ME
  elif tail -n 30 $OUT/logs/units/$eid.log | grep -qE "out of memory|OutOfMemoryError|CUSOLVER_STATUS_INTERNAL_ERROR"; then
       n=$(( $(cat $C/$eid.oomtries 2>/dev/null || echo 0) + 1 )); echo $n > $C/$eid.oomtries; touch $C/.oom_$ME
       echo "$(date +%T) OOM $eid rc=$rc oom=$n (GPU memory; not counted as a try; worker lowers its memory budget)"
       [ $n -ge 6 ] && echo "failed: out of GPU memory 6 times" > $C/$eid.failed
  else n=$(( $(cat $C/$eid.tries 2>/dev/null || echo 0) + 1 )); echo $n > $C/$eid.tries
       echo "$(date +%T) FAIL $eid rc=$rc try=$n"; [ $n -ge 3 ] && touch $C/$eid.failed; fi
  rm -f $OUT/ckpt/${eid}_last.pt $OUT/ckpt/${eid}_c[0-9]_last.pt  # user 2026-10-07: final-epoch states are not kept (never read)
  rm -rf $C/$eid.claim
}
declare -A W WT
used() { local s=0 p; for p in $(jobs -rp); do s=$(( s + ${W[$p]:-0} )); done; echo $s; }
echo "memory budget $CAP GB"
while true; do
  claimed=0
  WT=(); WF=$OUT/$(basename $Q .txt)_weights.txt
  [ -e "$WF" ] && while read -r e w; do WT[$e]=$w; done < "$WF"
  while IFS='|' read -r eid idx; do
    [ -z "$eid" ] && continue
    [ -e "$OUT/units/$eid.json" ] && continue
    [ -e "$C/$eid.failed" ] && continue
    [ -d "$C/$eid.claim" ] && continue
    w=${WT[$eid]:-8}
    while true; do
      if [ -e $C/.oom_$ME ]; then rm -f $C/.oom_$ME; CAP=$(( CAP - 6 )); [ $CAP -lt 12 ] && CAP=12; echo "$(date +%T) memory budget now $CAP GB"; fi
      nr=$(jobs -rp | wc -l)
      [ "$nr" -ge "$PAR" ] || { [ "$nr" -gt 0 ] && [ $(( $(used) + w )) -gt $CAP ]; } || break
      sleep 5
    done
    [ -e $C/.infra_$ME ] && break
    [ -e "$OUT/units/$eid.json" ] && continue
    if mkdir $C/$eid.claim 2>/dev/null; then
      echo $ME > $C/$eid.claim/job
      claimed=1
      run_unit "$eid" "$idx" &
      W[$!]=$w
      sleep 20  # stagger data loading: 8 simultaneous loads exceeded the 64G job memory (rc=137, DTU, 2026-10-06/07)
    fi
  done < "$Q"
  wait
  [ -e $C/.infra_$ME ] && { echo "infrastructure failure on ${SLURMD_NODENAME:-?}; worker ends"; break; }
  [ $claimed -eq 0 ] && break
done
echo "end $(date -Is) job=$ME"
