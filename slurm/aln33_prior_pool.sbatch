#!/bin/bash
#SBATCH --job-name=c3_aln3pr
# E34_PUBLIC_PRIOR GPU pool (ALN3.4, contract aln33_env64_125ms_v1; PUBLIC_PRIOR_DESIGN.md §6.5, §8). A copy of
# slurm/aln3_gpu_pool.sbatch (sha256 ee96fa7eaf4b4ecf...) with the §6.5 changes:
#   - job name c3_aln3pr; no --nice; no --time (user rule: no time limit on V100/A30/A40/L40S; DefaultTime=NONE, so a worker's
#     limit is the partition maximum: L40S 1 day, V100 2 days, A30 and A40 4 days; running units resume from their checkpoints);
#   - partitions V100,A30,A40,L40S (the A100s stay with the FM lane);
#   - the queue is queue_v3_prior.txt (prior33.deps.write_queue via make_queue.py), lines "eid|idx|up1,up2,..." read as three
#     fields (the third may be empty); queue_v3_prior.blocked lists the eids of rows whose upstream failed;
#   - a 30-s polling loop in place of the pass-and-wait loop: every 30 s reap the finished units, re-read the queue, the weights
#     and .blocked, walk the rows in queue order skipping rows that are done (units/<eid>.json), failed (<eid>.failed), blocked,
#     claimed, rows with an upstream that has no complete record (units/<up>.json) and rows that ran out of memory
#     (<eid>.oomtries) when this card has < 20 GB; admit a row when fewer than PAR units run and its weight fits CAP (a row always
#     starts on an idle card), otherwise go on to the next, lighter row; claim by mkdir, launch, keep the 20-s stagger;
#   - exit: STOP_queue_v3_prior or .infra_<jobid> (stop claiming, wait for the running units, exit), or no unit running and no
#     row admissible for 20 consecutive minutes (the GPU returns to the FM lane; keeper_prior.sh resubmits when rows are ready).
# Claims, tries, OOM and INFRA handling, MPS, weights and the _last.pt cleanup are unchanged from the source.
# Beyond §6.5 (recorded deviations, all benign): cd "$SLURM_SUBMIT_DIR" || exit 1; Q defaults to the prior queue and any other
# queue file is refused (exit 2); the test hooks below (the MPS health check runs $PY, by default the source's interpreter);
# malformed queue lines are skipped and logged once; a missing or non-integer weight counts as 8 GB; done / .failed are re-checked
# under a fresh claim; a missing queue file is tolerated (logged once); a last line without a newline is read; blank lines of
# queue_v3_prior_weights.txt and .blocked are skipped (the source aborts the worker on one: an empty associative-array key is
# fatal in non-interactive bash, 'bad array subscript'); log lines for admissions, halts and the idle exit.
# Claims of dead workers: a worker that hits its partition time limit (TIMEOUT) is not requeued and its claims stay behind; the
# start-up sweep below (any later worker) and private/auditory_alignment_v3/refresh.sh (the remote refresher: every 10 min it
# releases every pool/*/*.claim of a job that no longer runs, this pool included) free them. Meanwhile running workers skip the
# row and keeper_prior.sh does not count it as ready.
# Usage (private/auditory_alignment_v3/keeper_prior.sh, from the repo root):
#   sbatch --job-name=c3_aln3pr --nice=0 slurm/aln33_prior_pool.sbatch private/auditory_alignment_v3/queue_v3_prior.txt [PAR [MPS]]
# Test hooks, set only by tests/auditory_alignment_v3/prior33/infra/run_harness.sh (fake runners in a temporary directory):
#   ALN33_POOL_PY (interpreter), ALN33_POOL_POLL, ALN33_POOL_IDLE, ALN33_POOL_STAGGER (seconds; defaults 30, 1200, 20; a
#   non-numeric value falls back to the default). keeper_prior.sh drops them from every submission (sbatch exports the
#   submitter's environment by default), and the log names any hook in effect.
#SBATCH --qos=runfill
#SBATCH --partition=V100,A30,A40,L40S
#SBATCH --gres=gpu:1
#SBATCH --exclude=node52
#SBATCH --cpus-per-task=12
#SBATCH --mem=64G
#SBATCH --requeue
#SBATCH --open-mode=append
#SBATCH --output=private/auditory_alignment_v3/logs/%x-%j.log
set -uo pipefail
umask 077
cd "$SLURM_SUBMIT_DIR" || exit 1
Q=${1:-private/auditory_alignment_v3/queue_v3_prior.txt}; PAR=${2:-8}; MPS=${3:-1}
# only this pool and keeper_prior.sh may serve the prior queue: the source's two-field read would leave "idx|ups" in idx
[ "$(basename "$Q")" = queue_v3_prior.txt ] || { echo "aln33_prior_pool serves queue_v3_prior.txt only (three-field lines), not $Q"; exit 2; }
GPU_MB=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits | head -1)
if [ "${GPU_MB:-0}" -lt 30000 ] && [ "$PAR" -gt 5 ]; then PAR=5; fi  # 24 GB cards: 8 concurrent units can OOM
# weight-based admission (unchanged): every row carries a conservative GPU-memory weight in GB (queue_v3_prior_weights.txt,
# prior33.deps.WEIGHTS: donor groups 8, bridges 6, targets 3, zero-shot 2); a unit starts only if the running units' weights
# plus its own fit in CAP = card memory - 3 GB (a unit always starts on an idle card). An out-of-memory failure is not counted
# as a try; it lowers this worker's CAP by 6 GB (floor 12 GB); a unit that runs out of memory 6 times is marked failed.
CAP=100000
CAP=$(( ${GPU_MB:-24000} / 1024 - 3 ))
OUT=private/auditory_alignment_v3
TH=$(( ${SLURM_CPUS_PER_TASK:-12} / PAR )); [ $TH -lt 1 ] && TH=1
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 OMP_NUM_THREADS=$TH OPENBLAS_NUM_THREADS=$TH MKL_NUM_THREADS=$TH PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=0 PYTHONPATH=$PWD
export _MNE_FAKE_HOME_DIR=$(mktemp -d) MNE_USE_NUMBA=false
PY=${ALN33_POOL_PY:-/home/infres/yinwang/anaconda3/envs/eeg2025/bin/python}
POLL=${ALN33_POOL_POLL:-30}; IDLE=${ALN33_POOL_IDLE:-1200}; STAGGER=${ALN33_POOL_STAGGER:-20}
NUM='^[0-9]+([.][0-9]+)?$'; [[ "$POLL" =~ $NUM ]] || POLL=30; [[ "$IDLE" =~ ^[0-9]+$ ]] || IDLE=1200; [[ "$STAGGER" =~ $NUM ]] || STAGGER=20
HOOKS=$(env | grep -o '^ALN33_POOL_[A-Z]*=' | tr -d '=' | tr '\n' ' ')
QN=$(basename $Q .txt)
C=$OUT/pool/$QN; mkdir -p $C $OUT/logs/units
ME=$SLURM_JOB_ID
echo "start $(date -Is) node=${SLURMD_NODENAME:-?} gpu=$(nvidia-smi --query-gpu=name --format=csv,noheader) restart=${SLURM_RESTART_COUNT:-0} job=$ME queue=$Q par=$PAR mps=$MPS"
if [ "$MPS" = "1" ]; then
  export CUDA_MPS_PIPE_DIRECTORY=$(mktemp -d) CUDA_MPS_LOG_DIRECTORY=$(mktemp -d)
  nvidia-cuda-mps-control -d && echo "mps on" || { echo "mps failed; plain sharing"; unset CUDA_MPS_PIPE_DIRECTORY CUDA_MPS_LOG_DIRECTORY; }
  if [ -n "${CUDA_MPS_PIPE_DIRECTORY:-}" ] && ! $PY -c "import torch; torch.zeros(1).cuda(); torch.cuda.synchronize()" >/dev/null 2>&1; then
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
# 2026-10-11 (offload review): if squeue failed or returned nothing (it always lists this worker itself), sweep nothing but
# our own claims; never sweep a claim whose owner is not written yet (mkdir precedes echo) or another worker's claim < 2 min old
[ $? -eq 0 ] && [ -n "$live" ] || live=SKIP
for d in $C/*.claim; do
  [ -d "$d" ] || continue
  owner=$(cat $d/job 2>/dev/null)
  if [ "$owner" = "$ME" ]; then rm -rf "$d"; continue; fi
  [ "$live" = SKIP ] && continue
  if [ -z "$owner" ]; then [ -n "$(find "$d" -maxdepth 0 -mmin +10)" ] && rm -rf "$d"; continue; fi
  [ -n "$(find "$d" -maxdepth 0 -mmin -2)" ] && continue
  grep -qx "$owner" <<< "$live" || rm -rf "$d"
done
run_unit() {  # eid index
  local eid=$1 idx=$2 t0=$(date +%s)
  rm -f $OUT/units/$eid.FAILED.json
  local thr=$TH; [ "${WT[$eid]:-0}" -ge 1000 ] && thr=${SLURM_CPUS_PER_TASK:-12}  # exclusive (whole-card) units get all CPUs
  OMP_NUM_THREADS=$thr OPENBLAS_NUM_THREADS=$thr MKL_NUM_THREADS=$thr $PY -m auditory_alignment_v3.run --index $idx --eid $eid --out $OUT >> $OUT/logs/units/$eid.log 2>&1
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
declare -A W WT BL
used() { local s=0 p; for p in $(jobs -rp); do s=$(( s + ${W[$p]:-0} )); done; echo $s; }
nrun() { jobs -rp | wc -l; }
reap() {  # forget finished units (their run_unit subshell has already logged done / FAIL / OOM / INFRA and released the claim);
  local p live=" $(jobs -rp | tr '\n' ' ') "  # sets reaped = how many finished since the last poll
  jobs >/dev/null 2>&1  # bash reports, and drops, terminated jobs
  reaped=0
  for p in "${!W[@]}"; do [[ "$live" == *" $p "* ]] || { unset "W[$p]"; reaped=$(( reaped + 1 )); }; done
}
oomcheck() { if [ -e $C/.oom_$ME ]; then rm -f $C/.oom_$ME; CAP=$(( CAP - 6 )); [ $CAP -lt 12 ] && CAP=12; echo "$(date +%T) memory budget now $CAP GB"; fi; }
ups_done() { local u; for u in ${1//,/ }; do [ -e "$OUT/units/$u.json" ] || return 1; done; return 0; }  # every upstream has a complete record
halt() { [ -e "$OUT/STOP_$QN" ] || [ -e $C/.infra_$ME ]; }
WF=$OUT/${QN}_weights.txt; BF=$OUT/$QN.blocked
echo "memory budget $CAP GB; poll ${POLL}s; idle exit after ${IDLE}s"
[ -n "$HOOKS" ] && echo "test hooks in effect: $HOOKS(interpreter $PY, stagger ${STAGGER}s)"
idle0=$(date +%s); badmsg=0; noq=0; reaped=0
while true; do
  reap; oomcheck
  if halt; then
    if [ -e $C/.infra_$ME ]; then why=".infra_$ME"; else why="STOP_$QN"; fi
    echo "$(date +%T) $why present: no more claims; waiting for $(nrun) running unit(s)"
    wait
    if [ -e $C/.infra_$ME ]; then echo "infrastructure failure on ${SLURMD_NODENAME:-?}; worker ends"; else echo "stop file $OUT/STOP_$QN; worker ends"; fi
    break
  fi
  # (an empty key would abort bash with "bad array subscript", so blank lines are skipped)
  WT=(); [ -e "$WF" ] && while read -r e w; do [ -n "$e" ] && WT[$e]=$w; done < "$WF"
  BL=(); [ -e "$BF" ] && while read -r e; do [ -n "$e" ] && BL[$e]=1; done < "$BF"
  admitted=0
  nr=$(nrun); u=$(used)  # once per poll, then kept by hand: no fork per queue line (units ending mid-scan free at the next poll)
  if [ -e "$Q" ]; then
    noq=0
    while IFS='|' read -r eid idx ups || [ -n "$eid" ]; do
      [ -z "$eid" ] && continue
      [ $nr -ge $PAR ] && break
      halt && break
      if ! [[ "$eid" =~ ^ALN3X?_[0-9a-f]{16}$ && "$idx" =~ ^[0-9]+$ && "$ups" =~ ^[A-Za-z0-9_,]*$ ]]; then
        [ $badmsg -eq 0 ] && echo "$(date +%T) skipping malformed queue line(s), e.g. '$eid|$idx|$ups'"; badmsg=1; continue
      fi
      [ -e "$OUT/units/$eid.json" ] && continue
      [ -e "$C/$eid.failed" ] && continue
      [ -n "${BL[$eid]:-}" ] && continue
      [ -d "$C/$eid.claim" ] && continue
      [ -e "$C/$eid.oomtries" ] && [ "${GPU_MB:-0}" -lt 20000 ] && continue  # 2026-10-14: a unit that ran out of memory is left to cards >= 20 GB
      ups_done "$ups" || continue
      w=${WT[$eid]:-8}; [[ "$w" =~ ^[0-9]+$ ]] || w=8  # a missing or non-integer weight counts as 8 GB (bash arithmetic below)
      oomcheck
      [ $nr -gt 0 ] && [ $(( u + w )) -gt $CAP ] && continue  # does not fit beside the running units: try the lighter rows
      if mkdir $C/$eid.claim 2>/dev/null; then
        echo $ME > $C/$eid.claim/job
        # another worker may have finished or failed the row just before its claim was released: re-check under our claim
        if [ -e "$OUT/units/$eid.json" ] || [ -e "$C/$eid.failed" ]; then rm -rf $C/$eid.claim; continue; fi
        echo "$(date +%T) start $eid w=$w running=$nr used=$u/$CAP GB"
        run_unit "$eid" "$idx" &
        W[$!]=$w; nr=$(( nr + 1 )); u=$(( u + w ))
        admitted=$(( admitted + 1 ))
        sleep $STAGGER  # stagger data loading: 8 simultaneous loads exceeded the 64G job memory (rc=137, DTU, 2026-10-06/07)
      fi
    done < "$Q"
  elif [ $noq -eq 0 ]; then echo "$(date +%T) $Q missing; nothing to admit"; noq=1
  fi
  now=$(date +%s)
  # the idle clock restarts while a unit runs, when one was admitted, and at the poll that reaps the last one
  if [ $admitted -gt 0 ] || [ $reaped -gt 0 ] || [ "$(nrun)" -gt 0 ]; then idle0=$now
  elif [ $(( now - idle0 )) -ge $IDLE ]; then
    echo "$(date +%T) no unit running and no row admissible for $(( (now - idle0) / 60 )) min ($(( now - idle0 ))s); worker ends (keeper_prior.sh resubmits when rows are ready)"
    break
  fi
  halt || sleep $POLL
done
echo "end $(date -Is) job=$ME"
