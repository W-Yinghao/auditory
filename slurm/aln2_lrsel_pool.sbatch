#!/bin/bash
#SBATCH --job-name=c3_aln2lr
# ALN2 learning-rate selection pool: lines "<key>|0"; runs run_fm --lr-select <key>; done = fm_recipe/<key>.json (user 2026-10-05: at most 10 c3 Slurm slots). Each worker claims fit units from a queue
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
if ! $PY -c "import torch; torch.zeros(1).cuda(); torch.cuda.synchronize()" >/dev/null 2>&1; then
  echo "GPU unusable on ${SLURMD_NODENAME:-?}; exiting without claiming"; exit 0
fi
live=$(squeue -u $USER -h -o "%i")
for d in $C/*.claim; do
  [ -d "$d" ] || continue
  owner=$(cat $d/job 2>/dev/null)
  if [ "$owner" = "$ME" ] || ! grep -qx "$owner" <<< "$live"; then rm -rf "$d"; fi
done
run_unit() {  # eid index
  local eid=$1 idx=$2 t0=$(date +%s)
  rm -f $OUT/units/$eid.FAILED.json
  $PY -m auditory_alignment_v2.run_fm --lr-select "$(echo $eid | sed 's/__/|/g')" --out $OUT >> $OUT/logs/units/LRSEL_$eid.log 2>&1
  local rc=$?
  if [ $rc -eq 0 ] && [ -e "$OUT/fm_recipe/$eid.json" ]; then echo "$(date +%T) done $eid $(( $(date +%s)-t0 ))s"
  else n=$(( $(cat $C/$eid.tries 2>/dev/null || echo 0) + 1 )); echo $n > $C/$eid.tries
       echo "$(date +%T) FAIL $eid rc=$rc try=$n"; [ $n -ge 3 ] && touch $C/$eid.failed; fi
  rm -rf $C/$eid.claim
}
while true; do
  claimed=0
  while IFS='|' read -r eid idx; do
    [ -z "$eid" ] && continue
    [ -e "$OUT/fm_recipe/$eid.json" ] && continue
    [ -e "$C/$eid.failed" ] && continue
    while [ "$(jobs -rp | wc -l)" -ge "$PAR" ]; do sleep 5; done
    if mkdir $C/$eid.claim 2>/dev/null; then
      echo $ME > $C/$eid.claim/job
      claimed=1
      run_unit "$eid" "$idx" &
    fi
  done < "$Q"
  wait
  [ $claimed -eq 0 ] && break
done
echo "end $(date -Is) job=$ME"
