#!/bin/bash
# E34_PUBLIC_PRIOR keeper (ALN3.4; PUBLIC_PRIOR_DESIGN.md §6.5, §8; adapted from keeper.sh). Every 60 s it counts the ready
# unclaimed rows of queue_v3_prior.txt with the pool worker's own three-field test (not done, not .failed, not listed in
# queue_v3_prior.blocked, not claimed, every upstream with a complete record units/<up>.json). When a row has been ready and
# unclaimed on this pass and the previous one (a row that has just turned ready is left to the running workers, which poll every
# 30 s), there are fewer than MAXG (at most 4) c3_aln3pr jobs and fewer than 2 of them pending, it submits one
# slurm/aln33_prior_pool.sbatch worker at nice 0; when every such row has run out of memory before (<eid>.oomtries, left to cards
# >= 20 GB by the worker), that worker is restricted to --partition=A30,A40,L40S, and only while no restricted worker is pending
# (those partitions can take a day to start one; the second pending slot stays free for a worker that rows on any card need).
# It writes a heartbeat line every loop (watch_anyhost.sh reads the age of logs/keeper_prior.log and its last heartbeats).
# It stops on STOP_queue_v3_prior, or when queue_v3_prior.remaining reads 0 on two consecutive loops: the lane is complete (every
# row in scope done, failed or blocked, and no open row held). Anything else keeps it running: 'held' (make_queue.py: nothing left
# in scope while prior rows are held or unbound, i.e. paused), 'unknown' (make_queue.py's prior-queue error), a missing file.
# An squeue failure submits nothing.
# One instance only: it holds an exclusive flock on private/auditory_alignment_v3/.keeper_prior.lock (NFS with local_lock=none, so
# the lock is taken on the server and holds across hosts). The Slurm keeper job and the session fallback may both be started;
# whichever comes second exits with a log line naming the holder (at once while the holder looks alive). sleep and sbatch run
# without the lock's descriptor (only the brief flock, squeue, queue-scan, touch and stat calls inherit it). The lock is taken
# with flock -n -E 75: 75 means held; any other failure (a lock-manager error such as ENOLCK, util-linux flock exit 71) is
# logged as 'cannot lock' and ends the keeper with exit 1, never read as held.
# NFSv3 caveat (/home is NFS vers=3): the flock is an NLM lock that the server holds for the client host. A keeper that ends or
# is killed releases it at once, but if its NODE crashes the server keeps the lock until that node reboots and its statd notifies
# the server (hours, or never while the node stays down), and every later keeper, a requeued job or the session fallback, is
# refused. Hence the holder record and the stale-lock check: the holder appends "holder host=H pid=P job=J started=T" to the
# lock file through the locked descriptor (the file is never opened a second time while it is held), refreshes the file's mtime
# on every loop (touch -c, which opens nothing; this mtime is the lock heartbeat) and appends "released ..." when it ends. J is
# $SLURM_JOB_ID, or 'session' outside Slurm. A session fallback started inside a Slurm allocation (a Claude session that runs in
# one, for instance) inherits the allocation's SLURM_JOB_ID and records that number: squeue lists the allocation as running while
# it lasts, and the allocation's end kills the fallback, which frees the lock.
# A keeper refused the lock reads the last record and the mtime and calls the lock stale when the recorded host is this host and
# the pid is gone or does not hold this lock file (its /proc/<pid>/fd/9 is not the file: a reused pid), when the heartbeat is
# older than 10 min, or, for a holder on another host (whose pid cannot be checked from here), when the recorded job is this
# keeper's own job (an earlier run of a requeued job) or a job squeue does not list as running. A keeper that has just taken the
# lock writes its record and first heartbeat a moment after its flock, and another host may see the record only once the
# holder host's NFS client has written it back (at the latest about 35 s later: dirty_expire 30 s plus the 5-s writeback
# interval). So a refused keeper that finds the lock stale says so, re-checks it (flock, record, mtime) after 2 s and then every
# 4 s up to 38 s, exits 0 as soon as the holder looks alive and takes the lock if it has been freed meanwhile. A lock still
# stale after that is never taken over: the keeper logs the holder, the reason and the recovery and exits 3 (no
# heartbeat follows, so the watcher's dead-keeper EVENT still fires). Recovery, once no keeper_prior.sh runs on the recorded host
# and no c3_p33keeper job runs:
#   mv private/auditory_alignment_v3/.keeper_prior.lock private/auditory_alignment_v3/.keeper_prior.lock.stale_<date>
# then start the keeper again (it locks a new file). A keeper whose lock file has been moved or replaced ends at its next loop
# (exit 4), so a recovery made while the old holder still lived cannot leave two keepers running.
# Claims of dead workers: a worker that hits its partition time limit is not requeued and its claims stay behind; a new worker's
# start-up sweep and private/auditory_alignment_v3/refresh.sh (the remote refresher, every 10 min, every pool/*/*.claim of a job
# that no longer runs) release them. Until then the row is neither run nor counted as ready here.
# Runs as slurm/aln33_prior_keeper.sbatch (CPU partition, 1 CPU, 1 GB). If sbatch is refused from compute nodes (the probe checks
# sbatch --test-only) or the CPU partition cannot start that job soon, run it in the session instead, like the existing keepers:
#   nohup bash private/auditory_alignment_v3/keeper_prior.sh >> private/auditory_alignment_v3/logs/keeper_prior.log 2>&1 &
# Usage: keeper_prior.sh [MAXG (default 4, capped at 4) [PAR (default 8)]]
# Test hooks, set only by tests/auditory_alignment_v3/prior33/infra/run_harness.sh: ALN33_ROOT (repo root), ALN33_KEEPER_POLL (s).
# The keeper job unsets them, and every worker submission drops them and the pool's own hooks (ALN33_POOL_*).
cd "${ALN33_ROOT:-/home/infres/yinwang/EEG_auditory}" || exit 1
OUT=private/auditory_alignment_v3; QN=queue_v3_prior; Q=$OUT/$QN.txt; C=$OUT/pool/$QN; LOCK=$OUT/.keeper_prior.lock
MAXG=${1:-4}; PAR=${2:-8}; NAME=c3_aln3pr; MAXP=2; POLL=${ALN33_KEEPER_POLL:-60}; STALE=600  # lock heartbeat older: stale (10 min)
RECHECK=40  # s: a held lock that looks stale is re-checked this long before it is called so (a new holder's record: header)
[[ "$MAXG" =~ ^[0-9]+$ ]] || MAXG=4; [ "$MAXG" -gt 4 ] && MAXG=4  # project rule: up to 4 c3_aln3pr workers
[[ "$PAR" =~ ^[1-9][0-9]*$ ]] || PAR=8
[[ "$POLL" =~ ^[0-9]+([.][0-9]+)?$ ]] || POLL=60
NOHOOK=(env -u ALN33_ROOT -u ALN33_KEEPER_POLL -u ALN33_POOL_PY -u ALN33_POOL_POLL -u ALN33_POOL_IDLE -u ALN33_POOL_STAGGER)
HOST=$(hostname); ME="host=$HOST pid=$$ job=${SLURM_JOB_ID:-session}"
command -v flock > /dev/null || { echo "$(date +%FT%T) keeper_prior: flock (util-linux) not found on $HOST; exiting"; exit 1; }
exec 9>> "$LOCK" || { echo "$(date +%FT%T) keeper_prior: cannot open $LOCK; exiting"; exit 1; }
judge() {  # the lock is held: who holds it ($who, from the last record) and why it looks stale ($why; empty: the holder looks
  # alive, or nothing says otherwise)
  local re lk pk sq
  rec=$(grep -E '^(holder|released) ' "$LOCK" 2>/dev/null | tail -n 1 | cut -c1-300); h=""; p=""; j=""; why=""; alive=unknown
  if [[ "$rec" == "holder "* ]]; then
    re=' host=([^ ]+)'; [[ "$rec" =~ $re ]] && h=${BASH_REMATCH[1]}
    re=' pid=([0-9]+)'; [[ "$rec" =~ $re ]] && p=${BASH_REMATCH[1]}
    re=' job=([^ ]+)'; [[ "$rec" =~ $re ]] && j=${BASH_REMATCH[1]}
  fi
  case "$rec" in "holder "*) who=${rec#holder };; "released "*) who="no record of the holder yet; last: $rec";; *) who="no holder record";; esac
  now=$(date +%s); mt=$(stat -c %Y "$LOCK" 2>/dev/null); age=$(( now - ${mt:-$now} ))
  if [ -n "$h" ] && [ "$h" = "$HOST" ] && [ -n "$p" ]; then  # a holder on this host: does pid p hold this lock file (fd 9)?
    lk=$(stat -c %d:%i "$LOCK" 2>/dev/null); pk=$(stat -L -c %d:%i "/proc/$p/fd/9" 2>/dev/null)
    if [ "$p" != "$$" ] && [ -n "$lk" ] && [ "$pk" = "$lk" ]; then alive=yes; else alive=no; fi
  fi
  if [ "$alive" = no ]; then why="its pid $p is gone from $h or does not hold this lock file"
  elif [ "$age" -gt "$STALE" ]; then
    why="its lock file was last touched ${age}s ago (the holder touches it every loop), more than ${STALE}s"
    [ "$alive" = yes ] && why+=" (pid $p still holds it on $h: hung?)"
  elif [ "$alive" = unknown ] && [[ "$j" =~ ^[0-9]+$ ]]; then  # a holder on another host: its Slurm job
    if [ "$j" = "${SLURM_JOB_ID:-}" ]; then why="its job $j is this job: an earlier run of this requeued keeper job"
    elif sq=$(squeue -u "$USER" -h -o '%i|%T' 2>/dev/null) && ! grep -qE "^$j[|](RUNNING|COMPLETING|CONFIGURING|SUSPENDED)\$" <<< "$sq"; then
      why="its Slurm job $j is not running (squeue)"
    fi
  fi
}
flock -n -E 75 9; fl=$?; waited=0  # 0: taken; 75: held; anything else: an error (cannot lock)
if [ "$fl" = 75 ]; then  # held: name the holder; exit 0 while it looks alive, 3 when it still looks stale after the re-checks
  # (never taken over). These log lines never contain ' heartbeat ', which watch_anyhost.sh reads as this keeper's loop lines
  judge
  if [ -n "$why" ]; then  # a keeper that has just taken the lock writes its record a moment later (header): re-check first
    echo "$(date +%FT%T) keeper_prior: $LOCK is held and looks stale: $why ($who); re-checking it for up to ${RECHECK}s" \
         "before calling it stale (a keeper that has just taken the lock writes its record a moment later)"
    d=2
    while [ -n "$why" ] && [ $((waited + d)) -le "$RECHECK" ]; do  # after 2, 6, ..., 38 s
      sleep $d 9>&-; waited=$((waited + d)); d=4
      flock -n -E 75 9; fl=$?; [ "$fl" = 75 ] || break  # 0: freed meanwhile, taken below; anything else: an error (below)
      judge
    done
  fi
fi
case $fl in
  0) [ "$waited" -gt 0 ] && echo "$(date +%FT%T) keeper_prior: $LOCK was freed while this keeper re-checked it (its holder" \
                                 "ended); this keeper takes it";;
  75) if [ -z "$why" ]; then
        echo "$(date +%FT%T) keeper_prior: another instance holds $LOCK ($who; lock touched ${age}s ago); this one ($ME) exits"; exit 0
      fi
      echo "$(date +%FT%T) keeper_prior: STALE LOCK $LOCK: $why ($who; still so after re-checking for ${waited}s). Not taking it" \
           "over: this keeper ($ME) exits 3."
      [ -n "$h" ] || h="the holder host"
      echo "$(date +%FT%T) keeper_prior: recovery: once no keeper_prior.sh runs on $h (ps -fu $USER | grep keeper_prior)" \
           "and no c3_p33keeper job runs (squeue -u $USER -n c3_p33keeper), from the repo root mv $LOCK $LOCK.stale_$(date +%Y%m%dT%H%M%S)" \
           "and start the keeper again (NFSv3 keeps a crashed node's lock until that node reboots; see this script's header)"
      exit 3;;
  *) echo "$(date +%FT%T) keeper_prior: cannot lock $LOCK (flock exit $fl: an error, not a conflict); this keeper ($ME) exits 1"; exit 1;;
esac
echo "holder $ME started=$(date +%FT%T)" >&9; touch -c "$LOCK" 2>/dev/null  # the holder record and the first heartbeat
trap 'echo "released $ME at=$(date +%FT%T)" >&9' EXIT
LOCKID=$(stat -L -c %d:%i "/proc/$$/fd/9" 2>/dev/null)  # the locked file (device:inode), to notice a lock moved aside
declare -A BL PREV NOW
ready_rows() {  # prints "<eid> <0|1>" per ready row (1: <eid>.oomtries exists): the worker's admission test without the card-dependent parts
  local eid idx ups u e ok
  BL=(); [ -e "$OUT/$QN.blocked" ] && while read -r e; do [ -n "$e" ] && BL[$e]=1; done < "$OUT/$QN.blocked"
  [ -e "$Q" ] || return 0
  while IFS='|' read -r eid idx ups || [ -n "$eid" ]; do
    [ -z "$eid" ] && continue
    [[ "$eid" =~ ^ALN3X?_[0-9a-f]{16}$ && "$idx" =~ ^[0-9]+$ && "$ups" =~ ^[A-Za-z0-9_,]*$ ]] || continue
    [ -e "$OUT/units/$eid.json" ] && continue; [ -e "$C/$eid.failed" ] && continue; [ -n "${BL[$eid]:-}" ] && continue; [ -d "$C/$eid.claim" ] && continue
    ok=1; for u in ${ups//,/ }; do [ -e "$OUT/units/$u.json" ] || { ok=0; break; }; done
    [ $ok -eq 1 ] || continue
    if [ -e "$C/$eid.oomtries" ]; then echo "$eid 1"; else echo "$eid 0"; fi
  done < "$Q"
}
echo "$(date +%FT%T) keeper_prior start pid=$$ host=$HOST job=${SLURM_JOB_ID:-session} maxg=$MAXG maxpending=$MAXP par=$PAR poll=${POLL}s queue=$Q lock=${LOCKID:-unidentified}"
zero=0
while true; do
  if [ -n "$LOCKID" ] && [ "$(stat -c %d:%i "$LOCK" 2>/dev/null)" != "$LOCKID" ]; then  # moved aside or replaced: a recovery
    echo "$(date +%FT%T) keeper_prior: $LOCK was moved or replaced (a stale-lock recovery?): this keeper no longer holds the keeper lock and ends"; exit 4
  fi
  touch -c "$LOCK" 2>/dev/null  # the lock heartbeat (mtime); touch -c opens nothing, so the lock's descriptor stays the only one
  [ -e "$OUT/STOP_$QN" ] && { echo "$(date +%FT%T) stop file STOP_$QN; keeper ends"; break; }
  rem=$(head -c 64 "$OUT/$QN.remaining" 2>/dev/null | tr -d '[:space:]')
  if [ "$rem" = 0 ]; then zero=$((zero + 1)); else zero=0; fi
  [ $zero -ge 2 ] && { echo "$(date +%FT%T) $QN.remaining is 0 on two consecutive loops (lane complete); keeper ends"; break; }
  [[ "$rem" =~ ^[0-9]+$ || "$rem" =~ ^[a-z]{1,16}$ ]] || rem=unknown  # 'held' and 'unknown' are shown as written
  # ready now (n, k without an OOM mark) and ready on the previous pass too (np, kp): only the latter trigger a submission
  NOW=(); n=0; k=0; np=0; kp=0
  while read -r e oom; do
    [ -z "$e" ] && continue
    NOW[$e]=1; n=$((n + 1)); [ "$oom" = 0 ] && k=$((k + 1))
    if [ -n "${PREV[$e]:-}" ]; then np=$((np + 1)); [ "$oom" = 0 ] && kp=$((kp + 1)); fi
  done <<< "$(ready_rows)"
  PREV=(); for e in "${!NOW[@]}"; do PREV[$e]=1; done
  act=""
  if sq=$(squeue -u $USER -h -o "%j|%T|%P" 2>/dev/null); then
    g=$(grep -c "^$NAME|" <<< "$sq"); p=$(grep -c "^$NAME|PENDING|" <<< "$sq")
    pr=$(grep "^$NAME|PENDING|" <<< "$sq" | grep -vc 'V100')  # pending workers restricted to the >= 24 GB partitions
    if [ "$np" -gt 0 ] && [ "$g" -lt "$MAXG" ] && [ "$p" -lt "$MAXP" ]; then
      part=(); [ "$kp" -eq 0 ] && part=(--partition=A30,A40,L40S)
      if [ ${#part[@]} -gt 0 ] && [ "$pr" -gt 0 ]; then
        act=" (only out-of-memory rows are ready and an A30,A40,L40S worker is already pending: the other pending slot stays free)"
      elif jid=$("${NOHOOK[@]}" sbatch --parsable --job-name=$NAME --nice=0 "${part[@]}" slurm/aln33_prior_pool.sbatch $Q $PAR 1 9>&-); then
        act=" submitted worker $jid${part[*]:+ (${part[*]}: only out-of-memory rows are ready)}"
      else act=" sbatch refused (rc=$?)"; fi
    fi
  else g="?"; p="?"; act=" squeue failed: nothing submitted"; fi
  echo "$(date +%FT%T) heartbeat ready=$n (no oom mark: $k; also ready last pass: $np) workers=$g pending=$p remaining=$rem$act"
  sleep $POLL 9>&-
done
