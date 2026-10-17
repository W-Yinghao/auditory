#!/bin/bash
# M10 infrastructure harness (ALN3.4 E34_PUBLIC_PRIOR; PUBLIC_PRIOR_DESIGN.md §6.5, §7.1 item 15). In a temporary directory, with
# fake squeue / sbatch / nvidia-smi / nvidia-cuda-mps-control and a fake interpreter standing in for the unit runner, it runs
#   - the real slurm/aln33_prior_pool.sbatch: admission order and packing past a heavy row, the skip rules (done, failed, blocked,
#     claimed, unready upstreams, OOM-marked rows on a < 20 GB card simulated by FAKE_GPU_MB), tries / OOM / INFRA handling, the
#     claim sweep and the _last.pt cleanup, queue and .blocked re-reads, three-field parsing, PAR, and the exit rules (STOP,
#     .infra_<jobid>, 20 idle minutes; all time-compressed through the pool's ALN33_POOL_* hooks);
#   - the real private/auditory_alignment_v3/keeper_prior.sh: it submits only for rows ready and unclaimed on two consecutive
#     passes, caps at 4 jobs / 2 pending, runs as one instance only (lock: two keepers cannot exceed the cap), stops on STOP or
#     when .remaining reads 0 twice (not on 'unknown' or 'held', not on a single 0), restricts OOM-only submissions to >= 24 GB
#     partitions, survives squeue and sbatch failures, drops every ALN33_* test hook from its submissions and writes a heartbeat
#     line every loop; the NFSv3 stale-lock rules (holder record and heartbeat; a lock held for a dead pid, a stale heartbeat, a
#     finished or requeued holder job is re-checked, then refused with exit 3 and never taken over; a new holder's record that
#     appears during the re-check, or a lock freed meanwhile, is not called stale; a flock error is 'cannot lock', exit 1, never
#     'held'; a keeper whose lock file is moved aside ends; a helper process holding the lock stands in for the NFS server that
#     keeps a crashed node's lock); slurm/aln33_prior_keeper.sbatch (with a stub keeper) unsets the hooks;
#   - a sandbox copy of private/auditory_alignment_v3/refresh.sh (the remote refresher), which releases a dead worker's claim;
#   - each patch of private/auditory_alignment_v3/aln34/prior33_patches/ applied to a temporary copy of its live file (sha256
#     checked against the patch header), then syntax-, import- and behaviour-tested there (watcher in a sandbox; make_queue and
#     ckpt_offload, including the real one_pass on sandbox trees, through harness_checks.py), and each patch header's apply
#     recipe run verbatim in a sandbox copy of the repo layout.
# Never touches the live pool, queue, units or ckpt files, never calls the real squeue / sbatch, CPU only, about 3-5 minutes.
# Robust under load: the checks wait for events (a trace or log line, a record, a submission count, a number of keeper heartbeats
# or watcher loops, the end of a process; polled every 0.1 s for up to ALN33_HARNESS_WAIT s, default 90), never for a fixed
# number of seconds. Where the harness must act between two keeper loops (k3d, k7) or during a stale-lock re-check (k14*), the
# keeper's sleep is a gate (FAKE_SLEEP_GATE: each sleep waits for the harness's go), so the keeper moves one step at a time; the
# watcher's log-age checks hold the log at its age while they run, and the pool's idle-reset check (s6) gives the late upstream
# a 20-s window. Every time bound a check asserts leaves slack for a loaded node. A wait that runs out is a FAIL of its own;
# after 3 of them the remaining waits are cut to 2 s, so a broken keeper or pool fails fast.
# Patch states, per live file (with ALN33_HARNESS_LIVE=<dir>: the same-named file there; only read, like the live files):
# not deployed (its sha256 is the header's live-sha256: the patch is applied to a copy); deployed (§6.5 live-edit steps 3, 5, 6:
# patched-sha256; the deployed file is tested as it is, and the unpatched file that the comparisons, the line count and the
# recipes use is its reverse patch, pinned by live-sha256); changed after deployment (it carries E34_PUBLIC_PRIOR but matches
# neither sha256: its patch checks are reported 'n/a' and the rest runs; test_infra_harness.py then skips its patch test and
# names the file); neither sha256 and no marker (changed before deployment): FAIL, regenerate the patch.
# Usage: bash tests/auditory_alignment_v3/prior33/infra/run_harness.sh
#   TMPDIR sets the parent of the temporary directory; ALN33_HARNESS_KEEP=1 keeps it after a passing run (always kept on failure).
set -u
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REPO=$(cd "$HERE/../../../.." && pwd)
PYH=${ALN33_HARNESS_PY:-/home/infres/yinwang/anaconda3/envs/eeg2025/bin/python}
POOL=$REPO/slurm/aln33_prior_pool.sbatch
KEEPER=$REPO/private/auditory_alignment_v3/keeper_prior.sh
PATCHES=$REPO/private/auditory_alignment_v3/aln34/prior33_patches
LIVE=$REPO/private/auditory_alignment_v3
PL=${ALN33_HARNESS_LIVE:-$LIVE}   # where the patched live files (make_queue.py, ckpt_offload.py, watch_anyhost.sh) are read from
T=$(mktemp -d "${TMPDIR:-/tmp}/aln33_infra.XXXXXX") || exit 1
case "$T" in "$REPO"|"$REPO"/*) echo "refusing to run inside the repository ($T)"; exit 1;; esac
NPASS=0; NFAIL=0; FAILED=(); NNA=0; NAS=()
ok()  { NPASS=$((NPASS+1)); echo "  ok   $*"; }
bad() { NFAIL=$((NFAIL+1)); FAILED+=("$*"); echo "  FAIL $*"; }
na()  { NNA=$((NNA+1)); NAS+=("$1: $2"); echo "  n/a  $1: $2"; }   # na CHECKS REASON: checks that cannot apply (not run)
chk() { local d=$1; shift; if "$@"; then ok "$d"; else bad "$d"; fi; }
finish() {
  local p; for p in $(jobs -p); do kill "$p" 2>/dev/null; done
  echo; [ $NNA -gt 0 ] && printf '  not applicable: %s\n' "${NAS[@]}"
  echo "M10 infra harness: $NPASS passed, $NFAIL failed, $NNA not applicable (directory $T)"
  if [ $NFAIL -gt 0 ]; then printf '  failed: %s\n' "${FAILED[@]}"; exit 1; fi
  [ "${ALN33_HARNESS_KEEP:-0}" = 1 ] || rm -rf -- "$T"
  exit 0
}
echo "M10 infra harness in $T"
[ "$PL" = "$LIVE" ] || echo "  (the patched live files are read from $PL: ALN33_HARNESS_LIVE)"

# ---------------------------------------------------------------------------------------------------------------- fakes
B=$T/bin; mkdir -p "$B"
cat > "$B/nvidia-smi" <<'EOF'
#!/bin/bash
case "$*" in *memory.total*) echo "${FAKE_GPU_MB:-16384}";; *name*) echo "Fake-GPU-${FAKE_GPU_MB:-16384}MiB";; *) echo fake;; esac
EOF
cat > "$B/squeue" <<'EOF'
#!/bin/bash
# fake squeue over $FAKE_SQ (lines "jobid name STATE [PARTITIONS]", default V100,A30,A40,L40S): -t S1,S2 filters states, -o
# expands %i %j %T %P; FAKE_SQUEUE_FAIL=1 fails
[ "${FAKE_SQUEUE_FAIL:-0}" = 1 ] && { echo "squeue: error: fake failure" >&2; exit 1; }
st=""; fmt="%i"
while [ $# -gt 0 ]; do case "$1" in -t) st=$2; shift 2;; -o) fmt=$2; shift 2;; -u) shift 2;; *) shift;; esac; done
[ -e "${FAKE_SQ:-/nonexistent}" ] || exit 0
while read -r id name s part; do
  [ -z "$id" ] && continue
  [ -n "$st" ] && [[ ",$st," != *",$s,"* ]] && continue
  l=${fmt//%i/$id}; l=${l//%j/$name}; l=${l//%T/$s}; l=${l//%P/${part:-V100,A30,A40,L40S}}; echo "$l"
done < "$FAKE_SQ"
EOF
cat > "$B/sbatch" <<'EOF'
#!/bin/bash
# fake sbatch: logs its arguments to $FAKE_SBATCH_LOG and the ALN33_* variables it inherits to $FAKE_SBATCH_ENV (one line per
# call), adds a PENDING job to $FAKE_SQ, prints the id; FAKE_SBATCH_FAIL=1 refuses
echo "$*" >> "${FAKE_SBATCH_LOG:-/dev/null}"
{ env | grep '^ALN33_' | sort | tr '\n' ' '; echo; } >> "${FAKE_SBATCH_ENV:-/dev/null}"
[ "${FAKE_SBATCH_FAIL:-0}" = 1 ] && { echo "sbatch: error: Batch job submission failed: fake refusal" >&2; exit 1; }
name=fake; part=V100,A30,A40,L40S
for a in "$@"; do case "$a" in --job-name=*) name=${a#--job-name=};; --partition=*) part=${a#--partition=};; esac; done
n=$(( $(cat "$FAKE_SQ.next" 2>/dev/null || echo 5000) + 1 )); echo $n > "$FAKE_SQ.next"
echo "$n $name PENDING $part" >> "$FAKE_SQ"; echo "$n"
EOF
cat > "$B/nvidia-cuda-mps-control" <<'EOF'
#!/bin/bash
if [ "${1:-}" = -d ]; then echo "daemon" >> "${FAKE_MPS_LOG:-/dev/null}"; else read -r -t 2 c; echo "cmd ${c:-}" >> "${FAKE_MPS_LOG:-/dev/null}"; fi
EOF
cat > "$B/fakepy" <<'EOF'
#!/bin/bash
# fake interpreter: "-c <code>" (the pool's CUDA checks) exits $FAKE_CUDA_RC; "-m auditory_alignment_v3.run --index I --eid E
# --out O" plays $FAKE_BEHAVE/<eid> ("<kind> <seconds>"; kinds ok, fail, oom, infra, norecord, and gate: run until the harness
# creates $FAKE_BEHAVE/go or $FAKE_BEHAVE/<eid>.go, then finish as ok; a fail after <seconds> without either) and traces start / end
if [ "${1:-}" = -c ]; then exit "${FAKE_CUDA_RC:-0}"; fi
[ "${1:-}" = -m ] && [ "${2:-}" = auditory_alignment_v3.run ] || { echo "fakepy: unexpected arguments: $*"; exit 97; }
shift 2; idx=; eid=; out=
while [ $# -gt 0 ]; do case "$1" in --index) idx=$2; shift 2;; --eid) eid=$2; shift 2;; --out) out=$2; shift 2;; *) shift;; esac; done
kind=ok; dur=1; [ -e "$FAKE_BEHAVE/$eid" ] && read -r kind dur < "$FAKE_BEHAVE/$eid"
echo "$(date +%s.%N) start $eid $idx $kind" >> "$FAKE_TRACE"
if [ "$kind" = gate ]; then
  kind=fail; d=${dur%.*}; [[ "$d" =~ ^[0-9]+$ ]] || d=60; end=$(( SECONDS + d ))
  while [ $SECONDS -lt $end ]; do
    if [ -e "$FAKE_BEHAVE/go" ] || [ -e "$FAKE_BEHAVE/$eid.go" ]; then kind=ok; break; fi
    sleep 0.05
  done
else sleep "${dur:-1}"; fi
rc=0
case "$kind" in
  ok) mkdir -p "$out/units"; echo '{"status": "complete"}' > "$out/units/$eid.json.tmp" && mv -f "$out/units/$eid.json.tmp" "$out/units/$eid.json";;
  fail) echo "Traceback (most recent call last): synthetic failure"; rc=1;;
  oom) echo "torch.OutOfMemoryError: CUDA out of memory. Tried to allocate 2.00 GiB (synthetic)"; rc=1;;
  infra) echo "RuntimeError: CUDA unknown error (synthetic)"; rc=1;;
  norecord) ;;
esac
echo "$(date +%s.%N) end $eid $idx $kind rc=$rc" >> "$FAKE_TRACE"
exit $rc
EOF
for command in scancel scontrol srun; do
  cat > "$B/$command" <<'EOF'
#!/bin/bash
echo "infrastructure harness refuses real cluster mutation: ${0##*/} $*" >&2
exit 97
EOF
done
chmod 700 "$B"/*
FPATH="$B:/usr/bin:/bin"
for c in squeue sbatch scancel scontrol srun nvidia-smi nvidia-cuda-mps-control; do
  [ "$(PATH=$FPATH command -v $c)" = "$B/$c" ] || { echo "fake $c is not first on PATH; refusing to run"; exit 1; }
done
# keeper runs only (PATH=$KB:$FPATH): sleep and flock wrappers that are the real ones unless a test asks otherwise
KB=$T/kbin; mkdir -p "$KB"
RSLEEP=$(PATH=/usr/bin:/bin command -v sleep); RFLOCK=$(PATH=/usr/bin:/bin command -v flock)
[ -n "$RSLEEP" ] && [ -n "$RFLOCK" ] || { echo "sleep or flock not found in /usr/bin:/bin; refusing to run"; exit 1; }
cat > "$KB/sleep" <<EOF
#!/bin/bash
# sleep gate: the real sleep unless FAKE_SLEEP_GATE names a directory. Then call n (1, 2, ...) appends n to <gate>/waiting and
# returns, whatever the duration asked for, once the harness creates <gate>/go.<n> or <gate>/open (at the latest after 300 s),
# so a keeper's loops and stale-lock re-checks move one harness step at a time however loaded the node is
G=\${FAKE_SLEEP_GATE:-}
[ -n "\$G" ] && [ -d "\$G" ] || exec $RSLEEP "\$@"
n=\$(( \$(cat "\$G/n" 2>/dev/null || echo 0) + 1 )); echo "\$n" > "\$G/n"; echo "\$n" >> "\$G/waiting"
end=\$((SECONDS + 300))
while [ ! -e "\$G/go.\$n" ] && [ ! -e "\$G/open" ] && [ \$SECONDS -lt \$end ]; do $RSLEEP 0.05; done
EOF
cat > "$KB/flock" <<EOF
#!/bin/bash
# FAKE_FLOCK_RC=<n>: fail with exit n and lock nothing (util-linux flock exits 71 on a lock-manager error such as ENOLCK);
# otherwise the real flock, on the same descriptors
[ -n "\${FAKE_FLOCK_RC:-}" ] && { echo "flock: \$*: No locks available (fake)" >&2; exit "\$FAKE_FLOCK_RC"; }
exec $RFLOCK "\$@"
EOF
chmod 700 "$KB"/*
for c in sleep flock; do
  [ "$(PATH=$KB:$FPATH command -v $c)" = "$KB/$c" ] || { echo "keeper wrapper $c is not first on its PATH; refusing to run"; exit 1; }
done
for c in squeue sbatch; do
  [ "$(PATH=$KB:$FPATH command -v $c)" = "$B/$c" ] || { echo "fake $c is not first on the keeper PATH; refusing to run"; exit 1; }
done

# ---------------------------------------------------------------------------------------------------------------- helpers
declare -A E
NEXT=0
mk() {  # mk NAME: a fresh sandbox repo root S (OUT O, prior pool dir C)
  S=$T/$1; O=$S/private/auditory_alignment_v3; C=$O/pool/queue_v3_prior
  mkdir -p "$O/units" "$O/logs/units" "$O/ckpt" "$C" "$S/behave" "$S/tmp"
  : > "$S/sq"; : > "$S/trace"; : > "$O/queue_v3_prior.txt"; : > "$O/queue_v3_prior_weights.txt"; : > "$O/queue_v3_prior.blocked"
  E=(); NEXT=0
}
newid() { NEXT=$((NEXT+1)); E[$1]=$(printf 'ALN3X_%016x' $((0xa1000 + NEXT))); }
ups_of() { local u s=""; for u in $1; do s+="${s:+,}${E[$u]}"; done; echo "$s"; }
addrow() {  # addrow NAME WEIGHT "UPSTREAM NAMES" "KIND SECONDS": appends "eid|idx|ups" and "eid weight", writes the behaviour
  newid "$1"
  echo "${E[$1]}|$((100000 + NEXT))|$(ups_of "$3")" >> "$O/queue_v3_prior.txt"
  echo "${E[$1]} $2" >> "$O/queue_v3_prior_weights.txt"
  printf '%s\n' "${4:-ok 1}" > "$S/behave/${E[$1]}"
}
record() { echo '{"status": "complete"}' > "$O/units/${E[$1]}.json"; }
pool() {  # pool JOBID PAR MPS [VAR=VALUE ...]: the real pool sbatch, foreground, in sandbox S (poll 0.5 s, idle 3 s, stagger 0)
  local jid=$1 par=$2 mps=$3; shift 3
  ( cd "$S" && exec env -i HOME="$HOME" USER="${USER:-tester}" PATH="$FPATH" TMPDIR="$S/tmp" SLURM_SUBMIT_DIR="$S" \
      SLURM_JOB_ID="$jid" SLURM_CPUS_PER_TASK=4 SLURMD_NODENAME=fakenode ALN33_POOL_PY="$B/fakepy" ALN33_POOL_POLL=0.5 \
      ALN33_POOL_IDLE=3 ALN33_POOL_STAGGER=0 FAKE_TRACE="$S/trace" FAKE_BEHAVE="$S/behave" FAKE_SQ="$S/sq" FAKE_GPU_MB=16384 \
      FAKE_MPS_LOG="$S/mps.log" "$@" timeout 120 bash "$POOL" private/auditory_alignment_v3/queue_v3_prior.txt "$par" "$mps" ) \
    < /dev/null >> "$S/pool_$jid.log" 2>&1
}
starts()  { awk '$2=="start"{print $3}' "$S/trace" | tr '\n' ' ' | sed 's/ $//'; }
names()   { local e out=""; for e in "$@"; do out+="${out:+ }${E[$e]}"; done; echo "$out"; }
nstart()  { grep -c " start ${E[$1]} " "$S/trace"; }
tstart()  { awk -v e="${E[$1]}" '$2=="start" && $3==e {print $1; exit}' "$S/trace"; }
tend()    { awk -v e="${E[$1]}" '$2=="end" && $3==e {print $1; exit}' "$S/trace"; }
flt()     { awk -v a="$1" -v b="$2" 'BEGIN{exit !(a != "" && b != "" && a+0 < b+0)}'; }  # a < b (floats)
maxconc() { sort -n "$S/trace" | awk '$2=="start"{n++; if(n>m)m=n} $2=="end"{n--} END{print m+0}'; }
maxw()    {  # largest summed weight of units running together (>= 2 at once): must stay within CAP
  sort -n "$S/trace" | awk -v wf="$O/queue_v3_prior_weights.txt" 'BEGIN{while((getline l < wf) > 0){split(l, a, " "); w[a[1]] = a[2]}}
    $2=="start"{s+=w[$3]; n++; if(n>1 && s>m) m=s} $2=="end"{s-=w[$3]; n--} END{print m+0}'
}
has() { grep -qF -- "$2" "$1"; }
noclaims() { [ -z "$(ls -d "$C"/*.claim 2>/dev/null | while read -r d; do [ "$(cat "$d/job" 2>/dev/null)" = "$1" ] && echo "$d"; done)" ]; }
eq() { [ "$1" = "$2" ] || { echo "       expected [$2] got [$1]"; return 1; }; }
contains() { grep -qF -- "$2" <<< "$1" || { echo "       [$2] not in: $(head -c 300 <<< "$1")"; return 1; }; }
lacks() { ! grep -qF -- "$2" <<< "$1" || { echo "       unexpected [$2] in: $(head -c 300 <<< "$1")"; return 1; }; }
empty() { [ -z "$1" ] || { echo "       expected no output, got: $(head -c 300 <<< "$1")"; return 1; }; }
now() { date +%s.%N; }
fadd() { awk -v a="$1" -v b="$2" 'BEGIN{printf "%.3f", a+b}'; }  # a + b (awk's default %.6g would mangle epoch seconds)
# event-based waits (robust under load): poll a condition every 0.1 s instead of sleeping a fixed time
TW=${ALN33_HARNESS_WAIT:-90}; [[ "$TW" =~ ^[0-9]+$ ]] || TW=90; NTO=0
waitfor() {  # waitfor SECONDS CMD...: 0 once CMD succeeds, 1 if SECONDS pass first
  local end=$((SECONDS + $1)); shift
  until "$@"; do [ $SECONDS -lt $end ] || return 1; sleep 0.1; done
}
w() {  # w DESCRIPTION CMD...: waitfor TW s; running out is a FAIL of its own (after 3 of them every later wait gets 2 s)
  local d=$1; shift
  waitfor "$TW" "$@" && return 0
  bad "waited ${TW}s in vain for: $d"; NTO=$((NTO + 1)); [ $NTO -ge 3 ] && TW=2; return 1
}
nlines() { local n; n=$(grep -cF -- "$2" "$1" 2>/dev/null); echo "${n:-0}"; }  # nlines FILE STRING: lines holding it (0: no file)
atleast() { [ "$(nlines "$1" "$2")" -ge "$3" ]; }                                # atleast FILE STRING N
ended() { ! kill -0 "$1" 2>/dev/null; }                                         # ended PID: the (reaped) process is gone
started() { grep -q " start ${E[$1]} " "$S/trace"; }                            # started NAME: the unit's fake run began
nstarts_ge() { [ "$(awk '$2=="start"' "$S/trace" | wc -l)" -ge "$1" ]; }       # nstarts_ge N: at least N unit runs began
gated() { local n; n=$(grep -c '' "$S/gate/waiting" 2>/dev/null); [ "${n:-0}" -ge "$1" ]; }  # gated N: the keeper's sleep N waits
go() { touch "$S/gate/go.$1"; }                                                               # go N: let sleep N return
polls() {  # polls JOBID N: wait for N more polls of the running pool worker JOBID. Poll markers: every poll starts with oomcheck,
  # which consumes a .oom_<jobid> flag (it logs a 6-GB lower memory budget, floor 12 GB, and removes the flag)
  local i; for i in $(seq 1 "$2"); do touch "$C/.oom_$1"; w "pool $1: poll marker $i consumed" test ! -e "$C/.oom_$1"; done
}

# ------------------------------------------------------------------------------------------------------------ pool tests
echo "pool: admission order, packing and skip rules on a 16 GB card (CAP 13 GB, PAR 8 -> 5)"
mk s1
addrow D1 8 "" "ok 3"; addrow D2 8 "" "ok 1"
addrow Bdone 6 "" "ok 1"; record Bdone
addrow Bfail 6 "" "ok 1"; touch "$C/${E[Bfail]}.failed"
addrow Bblk 6 "" "ok 1"; echo "${E[Bblk]}" >> "$O/queue_v3_prior.blocked"
addrow Bclaim 6 "" "ok 1"; mkdir "$C/${E[Bclaim]}.claim"; echo 999 > "$C/${E[Bclaim]}.claim/job"
addrow Boom 6 "" "ok 1"; echo 1 > "$C/${E[Boom]}.oomtries"
addrow Bwait 6 "D1" "ok 1"; addrow T1 3 "" "ok 2"; addrow Z1 2 "D1 Bwait" "ok 1"
newid Xnone; addrow Twait 3 "Xnone" "ok 1"
printf '999 c3_aln3pr RUNNING\n1001 c3_aln3pr RUNNING\n' > "$S/sq"
pool 1001 8 0; L=$S/pool_1001.log
chk "admission order D1 T1 D2 Bwait Z1 (pool log; process scheduling may reorder child start traces)" eq \
  "$(awk '$2 == "start" && $3 ~ /^ALN/ {print $3}' "$L" | tr '\n' ' ' | sed 's/ $//')" "$(names D1 T1 D2 Bwait Z1)"
chk "the light row T1 is admitted while D1 runs and the heavy D2 does not fit" bash -c "$(declare -f flt); flt $(tstart T1) $(tend D1) && flt $(tstart T1) $(tstart D2)"
chk "D2 starts only once the card is idle again (8 + 8 > 13)" flt "$(tend D1)" "$(tstart D2)"
chk "Bwait waits for its upstream record, then for room (8 + 6 > 13)" bash -c "$(declare -f flt); flt $(tend D1) $(tstart Bwait) && flt $(tend D2) $(tstart Bwait)"
chk "Z1 starts after both upstreams have records" flt "$(tend Bwait)" "$(tstart Z1)"
chk "done, failed, blocked, claimed, OOM-marked (< 20 GB) and unready rows never start" eq "$(for k in Bdone Bfail Bblk Bclaim Boom Twait; do nstart $k; done | tr '\n' ' ')" "0 0 0 0 0 0 "
chk "summed weight of co-running units stays within CAP 13" [ "$(maxw)" -le 13 ]
chk "the runner receives the queue line's index" bash -c "grep -q ' start ${E[D1]} 100001 ' '$S/trace'"
chk "worker ends after the idle window" has "$L" "no unit running and no row admissible"
chk "another live worker's claim is kept; none of ours is left" bash -c "$(declare -f noclaims); C='$C'; [ \"\$(cat '$C/${E[Bclaim]}.claim/job')\" = 999 ] && noclaims 1001"
chk "PAR is clamped to 5 below 30 GB" has "$L" "par=5"

echo "pool: OOM, tries, claim sweep and _last.pt cleanup on a 24 GB card (CAP 21 GB)"
mk s2
addrow Boom 6 "" "ok 0.3"; echo 1 > "$C/${E[Boom]}.oomtries"
addrow Ooom 3 "" "oom 0.1"; addrow Ffail 2 "" "fail 0.1"; addrow Norec 2 "" "norecord 0.1"
addrow Stale 2 "" "ok 0.3"; mkdir "$C/${E[Stale]}.claim"; echo 555 > "$C/${E[Stale]}.claim/job"; touch -d '10 minutes ago' "$C/${E[Stale]}.claim"
addrow Mine 2 "" "ok 0.3"; mkdir "$C/${E[Mine]}.claim"; echo 1002 > "$C/${E[Mine]}.claim/job"
touch "$O/ckpt/${E[Mine]}_last.pt" "$O/ckpt/${E[Mine]}_c0_last.pt" "$O/ckpt/${E[Mine]}_best.pt"
echo '1002 c3_aln3pr RUNNING' > "$S/sq"
pool 1002 8 0 FAKE_GPU_MB=24576; L=$S/pool_1002.log
chk "an OOM-marked row runs on a >= 20 GB card" bash -c "[ -e '$O/units/${E[Boom]}.json' ]"
chk "OOM: 6 attempts, not counted as tries, then failed" bash -c "[ \"\$(cat '$C/${E[Ooom]}.oomtries')\" = 6 ] && [ ! -e '$C/${E[Ooom]}.tries' ] && grep -q 'out of GPU memory 6 times' '$C/${E[Ooom]}.failed'"
chk "OOM lowers the memory budget by 6 GB down to the 12 GB floor" bash -c "grep -q 'memory budget now 15 GB' '$L' && grep -q 'memory budget now 12 GB' '$L' && ! grep -q 'memory budget now [0-9] GB' '$L'"
chk "a failing unit: 3 tries, then failed" bash -c "[ \"\$(cat '$C/${E[Ffail]}.tries')\" = 3 ] && [ -e '$C/${E[Ffail]}.failed' ]"
chk "rc 0 without a record counts as a try" bash -c "[ \"\$(cat '$C/${E[Norec]}.tries')\" = 3 ] && [ -e '$C/${E[Norec]}.failed' ]"
chk "starts: Ooom x6, Ffail x3, Norec x3, the others once" eq "$(for k in Boom Ooom Ffail Norec Stale Mine; do nstart $k; done | tr '\n' ' ')" "1 6 3 3 1 1 "
chk "a stale claim of a non-running worker and our own requeued claim are swept, then run" bash -c "[ -e '$O/units/${E[Stale]}.json' ] && [ -e '$O/units/${E[Mine]}.json' ]"
chk "_last.pt states are removed, _best.pt kept" bash -c "[ ! -e '$O/ckpt/${E[Mine]}_last.pt' ] && [ ! -e '$O/ckpt/${E[Mine]}_c0_last.pt' ] && [ -e '$O/ckpt/${E[Mine]}_best.pt' ]"
chk "no claims left" bash -c "[ -z \"\$(ls -d '$C'/*.claim 2>/dev/null)\" ]"

echo "pool: STOP_queue_v3_prior and .infra_<jobid> stop claiming; running units finish"
for mode in stop infra; do  # A runs until released (gate), so the flag always lands while it runs; idle 60 s: no idle exit
  mk s3_$mode; addrow A 3 "" "gate 100"; addrow Bq 3 "" "ok 0.3"; addrow Cq 3 "" "ok 0.3"
  echo '1003 c3_aln3pr RUNNING' > "$S/sq"; L=$S/pool_1003.log
  pool 1003 1 0 ALN33_POOL_IDLE=60 & pid=$!
  w "s3_$mode: A started" started A
  if [ $mode = stop ]; then touch "$O/STOP_queue_v3_prior"; else touch "$C/.infra_1003"; fi
  w "s3_$mode: the worker saw the flag" atleast "$L" "present: no more claims; waiting for 1 running unit(s)" 1
  touch "$S/behave/${E[A]}.go"; wait $pid; t_exit=$(now)
  chk "$mode: only the running unit ran, and it completed" bash -c "[ '$(starts)' = '${E[A]}' ] && [ -e '$O/units/${E[A]}.json' ]"
  chk "$mode: the worker waited for it and exited soon after (well before its 60-s idle exit)" bash -c "$(declare -f flt); flt $(tend A) $t_exit && flt $t_exit $(fadd "$(tend A)" 30)"
  if [ $mode = stop ]; then chk "stop: log line" has "$L" "stop file private/auditory_alignment_v3/STOP_queue_v3_prior; worker ends"
  else chk "infra: log line 'infrastructure failure'" has "$L" "infrastructure failure on fakenode; worker ends"; fi
done

echo "pool: an INFRA error in a unit is not a try and stops claiming"
mk s5; addrow I 3 "" "infra 0.2"; addrow Bq 3 "" "ok 0.3"
echo '1005 c3_aln3pr RUNNING' > "$S/sq"
pool 1005 1 0; L=$S/pool_1005.log
chk "INFRA: flag set, no try counted, nothing else started" bash -c "[ -e '$C/.infra_1005' ] && [ ! -e '$C/${E[I]}.tries' ] && [ '$(starts)' = '${E[I]}' ] && grep -q 'INFRA ${E[I]}' '$L' && grep -q 'infrastructure failure' '$L'"

echo "pool: idle exit (time-compressed 20 s / 3 s), reset by a late upstream; queue and .blocked re-read every poll"
# The 20-s idle window gives a loaded node ample time to write the late upstream (its two polls take about 1 s on an idle node);
# the upper time bounds below leave 15 s of slack, the lower bounds follow from the pool's idle rule alone.
mk s6; newid U; addrow W 2 "U" "ok 3"; L=$S/pool_1006.log
pool 1006 5 0 ALN33_POOL_IDLE=20 & pid=$!
w "s6: the worker in its loop" atleast "$L" "idle exit after 20s" 1
polls 1006 2   # the upstream comes late: after at least one complete idle poll
t_up=$(now); record U
wait $pid; t1=$(now)
chk "the row is admitted once its upstream record appears" bash -c "$(declare -f flt); [ '$(starts)' = '${E[W]}' ] && flt $t_up $(tstart W)"
# (the pool's idle clock has 1-s resolution, date +%s, and restarts at the poll that reaps the unit: exit at least 19 s after the
# unit's end; a clock that the unit did not reset would end the worker at most 20.5 s after its start, i.e. at most 17.5 s after
# the unit's end, since the 3-s unit started after two polls)
chk "the idle clock restarts after the unit: exit 19-20 s after it ended" bash -c "$(declare -f flt); flt $(fadd "$(tend W)" 18.9) $t1 && flt $t1 $(fadd "$(tend W)" 36)"
mk s6b; newid U; addrow W 2 "U" "ok 0.5"
t0=$(now); pool 1016 5 0; t1=$(now)
chk "nothing admissible: the worker exits after the idle window (3 s), claiming nothing" bash -c "$(declare -f flt); [ -z '$(starts)' ] && flt $(fadd $t0 1.9) $t1 && flt $t1 $(fadd $t0 18)"
mk s7; echo '1007 c3_aln3pr RUNNING' > "$S/sq"; L=$S/pool_1007.log
newid R1; newid R2; echo "${E[R2]}" > "$O/queue_v3_prior.blocked"   # R2 is blocked before the worker starts
printf 'ok 0.3\n' > "$S/behave/${E[R1]}"; printf 'ok 0.3\n' > "$S/behave/${E[R2]}"
pool 1007 5 0 ALN33_POOL_IDLE=60 & pid=$!
w "s7: the worker in its loop" atleast "$L" "idle exit after 60s" 1
printf '%s|100001|\n%s|100002|\n' "${E[R1]}" "${E[R2]}" > "$O/q.tmp"; printf '%s 2\n%s 2\n' "${E[R1]}" "${E[R2]}" > "$O/queue_v3_prior_weights.txt"
mv "$O/q.tmp" "$O/queue_v3_prior.txt"
w "s7: R1 done" test -e "$O/units/${E[R1]}.json"   # R2 would have started beside R1 in the same pass, had .blocked been ignored
: > "$O/b.tmp"; t_unb=$(now); mv "$O/b.tmp" "$O/queue_v3_prior.blocked"
w "s7: R2 done" test -e "$O/units/${E[R2]}.json"
touch "$O/STOP_queue_v3_prior"; wait $pid
chk "rows added to the queue file after the start are admitted (re-read)" bash -c "[ -e '$O/units/${E[R1]}.json' ]"
chk "a blocked row is skipped until .blocked no longer lists it" bash -c "$(declare -f flt); flt $t_unb $(tstart R2) && [ -e '$O/units/${E[R2]}.json' ]"

echo "pool: three-field parsing (empty third field, two fields, malformed lines, no final newline)"
mk s8; newid A; newid Bb; newid Cc; newid Dd; newid Ee; newid Ff
{ echo "${E[A]}|100011|"; echo "${E[Bb]}|100012"; echo "garbage"; echo "${E[Cc]}|notanumber|"; echo
  echo "${E[Dd]}|100014|${E[A]}"; echo "${E[Ee]}|100015|${E[A]},${E[Bb]}"; printf '%s|100016|' "${E[Ff]}"; } > "$O/queue_v3_prior.txt"
for k in A Bb Cc Dd Ee Ff; do echo "${E[$k]} 2" >> "$O/queue_v3_prior_weights.txt"; printf 'ok 0.3\n' > "$S/behave/${E[$k]}"; done
echo '1008 c3_aln3pr RUNNING' > "$S/sq"
pool 1008 2 0; L=$S/pool_1008.log
chk "well-formed rows run with their own index" bash -c "for x in '${E[A]} 100011' '${E[Bb]} 100012' '${E[Dd]} 100014' '${E[Ee]} 100015' '${E[Ff]} 100016'; do grep -q \" start \$x \" '$S/trace' || exit 1; done"
chk "malformed lines are skipped and reported once" bash -c "[ \$(grep -c ' start ${E[Cc]} ' '$S/trace') = 0 ] && [ \$(grep -c 'skipping malformed queue line' '$L') = 1 ]"
chk "upstreams are honoured (Dd and Ee after A and Bb)" bash -c "$(declare -f flt); flt $(tend A) $(tstart Dd) && flt $(tend Bb) $(tstart Ee)"

echo "pool: PAR caps concurrency on a large card"
mk s9; for k in 1 2 3 4 5 6; do addrow P$k 2 "" "gate 100"; done   # every unit runs until it is released
echo '1009 c3_aln3pr RUNNING' > "$S/sq"
pool 1009 3 0 FAKE_GPU_MB=49152 & pid=$!
w "s9: 3 units running" nstarts_ge 3
polls 1009 3   # three consumed poll markers: at least two complete polls while the three units ran (budget 45 -> 27 GB)
n_held=$(awk '$2=="start"' "$S/trace" | wc -l); touch "$S/behave/go"; wait $pid
chk "at most PAR=3 units at once ($n_held started over 2+ polls while 3 ran), all 6 done" bash -c "[ $n_held = 3 ] && [ $(maxconc) = 3 ] && [ \$(ls '$O/units' | wc -l) = 6 ]"

echo "pool: MPS on, wrong queue, unusable GPU, squeue failure at start"
mk s10; addrow M 2 "" "ok 0.3"; echo '1010 c3_aln3pr RUNNING' > "$S/sq"
pool 1010 5 1; L=$S/pool_1010.log
chk "MPS: daemon started, unit done, quit at exit" bash -c "grep -q 'mps on' '$L' && [ -e '$O/units/${E[M]}.json' ] && grep -q daemon '$S/mps.log' && grep -q 'cmd quit' '$S/mps.log'"
mk s11; addrow M 2 "" "ok 0.3"
( cd "$S" && env -i PATH="$FPATH" SLURM_SUBMIT_DIR="$S" SLURM_JOB_ID=1011 USER=t bash "$POOL" private/auditory_alignment_v3/queue_v3_fm.txt 5 0 ) < /dev/null > "$S/out" 2>&1; rc=$?
chk "a queue other than queue_v3_prior.txt is refused (exit 2, nothing claimed)" bash -c "[ $rc = 2 ] && grep -q 'serves queue_v3_prior.txt only' '$S/out' && [ -z '$(starts)' ]"
mk s12; addrow M 2 "" "ok 0.3"
pool 1012 5 0 FAKE_CUDA_RC=1; L=$S/pool_1012.log
chk "unusable GPU: exits without claiming" bash -c "grep -q 'GPU unusable on fakenode' '$L' && [ -z '$(starts)' ] && [ -z \"\$(ls -d '$C'/*.claim 2>/dev/null)\" ]"
mk s13; addrow Own 2 "" "ok 0.3"; addrow Other 2 "" "ok 0.3"
mkdir "$C/${E[Own]}.claim" "$C/${E[Other]}.claim"; echo 1013 > "$C/${E[Own]}.claim/job"; echo 555 > "$C/${E[Other]}.claim/job"; touch -d '10 minutes ago' "$C/${E[Other]}.claim"
pool 1013 5 0 FAKE_SQUEUE_FAIL=1
chk "squeue failing at start: only our own claims are swept" bash -c "[ -e '$O/units/${E[Own]}.json' ] && [ -d '$C/${E[Other]}.claim' ] && [ \$(grep -c ' start ${E[Other]} ' '$S/trace') = 0 ]"
mk s14; addrow M 2 "" "ok 0.3"; touch "$O/STOP_queue_v3_prior"
pool 1014 5 0 ALN33_POOL_POLL=abc ALN33_POOL_IDLE=1.5 ALN33_POOL_STAGGER=-1; L=$S/pool_1014.log
chk "test hooks: non-numeric values fall back to 30 / 1200 / 20 s, and the log names the hooks in effect" bash -c "grep -q 'poll 30s; idle exit after 1200s' '$L' && grep -q 'test hooks in effect: .*ALN33_POOL_POLL.*stagger 20s' '$L' && grep -q 'stop file' '$L' && [ -z '$(starts)' ]"
chk "the first pool run logged its hooks too (they are visible whenever set)" has "$T/s1/pool_1001.log" "test hooks in effect: "

# ---------------------------------------------------------------------------------------------------------- keeper tests
# Event-based: each step waits for a number of keeper heartbeats (one per loop), a submission count or the keeper's end, never
# for a fixed time, so a loaded node only makes the tests slower. "N more heartbeats" means N more complete keeper loops. A step
# that must land between two loops (or inside a stale-lock re-check) holds the keeper in its gated sleep (gated N, go N).
KL=""
keeper() {  # keeper [VAR=VALUE ...] -- [ARGS]: the real keeper_prior.sh in sandbox S (poll 0.2 s), background; sets KPID. Its
  # PATH starts with the keeper wrappers (KB): with FAKE_SLEEP_GATE=$S/gate every sleep waits for go N (or $S/gate/open)
  local envs=() ; while [ $# -gt 0 ] && [ "$1" != -- ]; do envs+=("$1"); shift; done; [ "${1:-}" = -- ] && shift
  KL=$S/keeper.log
  ( cd "$S" && exec env -i HOME="$HOME" USER="${USER:-tester}" PATH="$KB:$FPATH" ALN33_ROOT="$S" ALN33_KEEPER_POLL=0.2 \
      FAKE_SQ="$S/sq" FAKE_SBATCH_LOG="$S/sbatch.log" "${envs[@]}" timeout 300 bash "$KEEPER" "$@" ) < /dev/null >> "$KL" 2>&1 &
  KPID=$!
}
stopk() { touch "$O/STOP_queue_v3_prior"; [ -d "$S/gate" ] && touch "$S/gate/open"; wait $KPID; rm -f "$O/STOP_queue_v3_prior"; }
nsub() { [ -e "$S/sbatch.log" ] && wc -l < "$S/sbatch.log" || echo 0; }
nsub_ge() { [ "$(nsub)" -ge "$1" ]; }
hbs() {  # hbs N: wait for N more keeper heartbeats (N more complete loops) in KL
  local want=$(( $(nlines "$KL" ' heartbeat ready=') + $1 ))   # loop heartbeats only (a refusal line may say 'heartbeat')
  w "$1 more keeper heartbeats in ${KL#"$T"/}" atleast "$KL" ' heartbeat ready=' "$want"
}
flip() { sed -E 's/ PENDING( |$)/ RUNNING\1/' "$S/sq" > "$S/sq.tmp" && mv "$S/sq.tmp" "$S/sq"; }
WANT="--parsable --job-name=c3_aln3pr --nice=0 slurm/aln33_prior_pool.sbatch private/auditory_alignment_v3/queue_v3_prior.txt 8 1"

echo "keeper: submits only while ready unclaimed rows exist"
mk k1
addrow Kd 2 "" ""; record Kd; addrow Kf 2 "" ""; touch "$C/${E[Kf]}.failed"
addrow Kb 2 "" ""; echo "${E[Kb]}" >> "$O/queue_v3_prior.blocked"; addrow Kc 2 "" ""; mkdir "$C/${E[Kc]}.claim"
newid Kx; addrow Kw 2 "Kx" ""; echo 5 > "$O/queue_v3_prior.remaining"
keeper; hbs 4; stopk
chk "no ready row: nothing submitted, heartbeat lines with ready=0" bash -c "[ $(nsub) = 0 ] && [ \$(grep -c 'heartbeat ready=0 ' '$KL') -ge 4 ] && grep -q 'stop file STOP_queue_v3_prior; keeper ends' '$KL'"

echo "keeper: caps at 4 c3_aln3pr jobs with at most 2 pending"
mk k2; for k in 1 2 3 4 5 6; do addrow R$k 2 "" ""; done; echo 6 > "$O/queue_v3_prior.remaining"
echo '77 c3_aln3fm RUNNING' > "$S/sq"
keeper; w "k2: 2 submissions" nsub_ge 2; hbs 3; n1=$(nsub)                 # 3 more loops while 2 pend: no third
flip; w "k2: 4 submissions" nsub_ge 4; hbs 3; n2=$(nsub)                   # they run: 2 more, then 2 pend again
flip; hbs 3; n3=$(nsub); stopk                                              # 4 running: none
chk "2 pending, then 2 more once they run, then no more (4 jobs): $n1 $n2 $n3" eq "$n1 $n2 $n3" "2 4 4"
chk "submission arguments: c3_aln3pr, nice 0, the prior pool and queue, PAR 8, MPS 1" bash -c "[ \$(grep -cxF -- '$WANT' '$S/sbatch.log') = 4 ]"
chk "other job names (c3_aln3fm) do not count" bash -c "grep -q 'workers=4 pending=0' '$KL'"
mk k2b; for k in 1 2 3 4 5 6; do addrow R$k 2 "" ""; done; echo 6 > "$O/queue_v3_prior.remaining"
keeper -- 10; w "k2b: 2 submissions" nsub_ge 2; hbs 2; flip; w "k2b: 4 submissions" nsub_ge 4; hbs 2; flip; hbs 4; n4=$(nsub); stopk
chk "MAXG 10 is capped at 4 (project rule; uncapped it would have submitted 2 more in those 4 loops)" eq "$n4" "4"

echo "keeper: two consecutive reads of .remaining 0 stop it; 'unknown', 'held', a missing file or a single 0 keep it running"
mk k3; newid Kx; addrow Kw 2 "Kx" ""; echo unknown > "$O/queue_v3_prior.remaining"
keeper; hbs 4; alive=$(kill -0 $KPID 2>/dev/null && echo yes); echo 0 > "$O/queue_v3_prior.remaining"
w "k3: the keeper ends" ended $KPID; gone=$(kill -0 $KPID 2>/dev/null || echo yes); wait $KPID
chk "'unknown' keeps it running; 0 ends it" bash -c "[ '$alive' = yes ] && [ '$gone' = yes ] && grep -q 'remaining=unknown' '$KL' && grep -q 'queue_v3_prior.remaining is 0 on two consecutive loops (lane complete); keeper ends' '$KL'"
mk k3b; newid Kx; addrow Kw 2 "Kx" ""
keeper; hbs 4; alive=$(kill -0 $KPID 2>/dev/null && echo yes); stopk
chk "a missing .remaining keeps it running" bash -c "[ '$alive' = yes ] && grep -q 'remaining=unknown' '$KL'"
mk k3c; newid Kx; addrow Kw 2 "Kx" ""; echo held > "$O/queue_v3_prior.remaining"
keeper; hbs 4; alive=$(kill -0 $KPID 2>/dev/null && echo yes); stopk
chk "'held' (make_queue: a paused lane) keeps it running and is shown as written" bash -c "[ '$alive' = yes ] && grep -q 'remaining=held' '$KL'"
mk k3d; newid Kx; addrow Kw 2 "Kx" ""; echo 0 > "$O/queue_v3_prior.remaining"; mkdir "$S/gate"
# lock-step (sleep gate): loop N reads .remaining, heartbeats and waits in its sleep N until go N, so each write below lands
# between two reads however slow the harness is
keeper FAKE_SLEEP_GATE="$S/gate"
w "k3d: loop 1 read 0" gated 1; echo held > "$O/queue_v3_prior.remaining"; go 1
w "k3d: loop 2 read 'held'" gated 2; alive=$(kill -0 $KPID 2>/dev/null && echo yes); echo 0 > "$O/queue_v3_prior.remaining"; go 2
w "k3d: loop 3 read 0" gated 3; go 3   # loop 4 reads 0 again: the second consecutive 0
w "k3d: the keeper ends" ended $KPID; gone=$(kill -0 $KPID 2>/dev/null || echo yes); wait $KPID
seen=$(sed -n 's/.* heartbeat .* remaining=\([a-z0-9]*\).*/\1/p' "$KL" | tr '\n' ' ')
chk "a single read of 0 (e.g. between write_queue's 0 and make_queue's 'held') does not end it; two reads a loop apart do (remaining: $seen)" \
  bash -c "[ '$alive' = yes ] && [ '$gone' = yes ] && [ '$seen' = '0 held 0 ' ]"

echo "keeper: a row must be ready and unclaimed on two consecutive passes (one a running worker claims at once never triggers one)"
mk k7; addrow R1 2 "" ""; echo 1 > "$O/queue_v3_prior.remaining"; mkdir "$S/gate"
keeper FAKE_SLEEP_GATE="$S/gate"   # lock-step (sleep gate): the claim lands between the first and the second pass
w "k7: pass 1" gated 1; mkdir "$C/${E[R1]}.claim"; echo 1 > "$C/${E[R1]}.claim/job"; go 1
w "k7: pass 2" gated 2; go 2; w "k7: pass 3" gated 3; stopk
first=$(grep -m 1 ' heartbeat ready=' "$KL"); n0=$(grep -c ' heartbeat ready=0 ' "$KL")
chk "ready on the first pass, claimed before the second: nothing submitted ($n0 later passes with ready=0)" bash -c "[ $(nsub) = 0 ] && [ $n0 -ge 2 ] && grep -qF 'heartbeat ready=1 (no oom mark: 1; also ready last pass: 0)' <<< \"\$1\"" _ "$first"

echo "keeper: OOM-only ready rows go to >= 24 GB partitions; squeue / sbatch failures"
OOMW='--parsable --job-name=c3_aln3pr --nice=0 --partition=A30,A40,L40S slurm/aln33_prior_pool.sbatch private/auditory_alignment_v3/queue_v3_prior.txt 8 1'
mk k4; addrow Ko 2 "" ""; echo 1 > "$C/${E[Ko]}.oomtries"; echo 2 > "$O/queue_v3_prior.remaining"
keeper; w "k4: a submission" nsub_ge 1; hbs 3; n_a=$(nsub); flip; w "k4: a second submission" nsub_ge 2; hbs 3; n_b=$(nsub); stopk
chk "OOM-only: workers restricted to A30,A40,L40S, one pending at a time ($n_a while it pends, $n_b once it runs)" \
  bash -c "[ $n_a = 1 ] && [ $n_b = 2 ] && [ \"\$(sort -u '$S/sbatch.log')\" = '$OOMW' ] && grep -q 'an A30,A40,L40S worker is already pending' '$KL'"
mk k4b; addrow Ko 2 "" ""; echo 1 > "$C/${E[Ko]}.oomtries"; addrow Kn 2 "" ""; echo 2 > "$O/queue_v3_prior.remaining"
keeper; w "k4b: 2 submissions" nsub_ge 2; hbs 3; stopk
chk "a normal row ready beside it: unrestricted workers" bash -c "[ $(nsub) = 2 ] && [ \"\$(sort -u '$S/sbatch.log')\" = '$WANT' ]"
mk k4c; addrow Ko 2 "" ""; echo 1 > "$C/${E[Ko]}.oomtries"; echo 2 > "$O/queue_v3_prior.remaining"; echo '900 c3_aln3pr PENDING A30,A40,L40S' > "$S/sq"
keeper; hbs 4; n_a=$(nsub); addrow Kn 2 "" ""; w "k4c: a submission" nsub_ge 1; hbs 3; n_b=$(nsub); stopk
chk "a restricted worker pending for days does not block a worker for a normal row that turns ready ($n_a, then $n_b)" \
  bash -c "[ $n_a = 0 ] && [ $n_b = 1 ] && [ \"\$(cat '$S/sbatch.log')\" = '$WANT' ]"
mk k5; addrow R1 2 "" ""; echo 1 > "$O/queue_v3_prior.remaining"
keeper FAKE_SQUEUE_FAIL=1; hbs 4; stopk
chk "squeue failing: nothing submitted, heartbeat says so" bash -c "[ $(nsub) = 0 ] && grep -q 'squeue failed: nothing submitted' '$KL'"
mk k6; addrow R1 2 "" ""; echo 1 > "$O/queue_v3_prior.remaining"
keeper FAKE_SBATCH_FAIL=1; w "k6: 3 refusals" atleast "$KL" 'sbatch refused' 3; stopk
chk "sbatch refused: logged, the keeper keeps looping" bash -c "[ \$(grep -c 'sbatch refused' '$KL') -ge 3 ]"

echo "keeper: one instance only (lock), so a Slurm keeper job and the session fallback cannot exceed the cap together"
mk k8; for k in 1 2 3 4 5 6; do addrow R$k 2 "" ""; done; echo 6 > "$O/queue_v3_prior.remaining"
printf '1 c3_aln3pr RUNNING\n2 c3_aln3pr RUNNING\n3 c3_aln3pr RUNNING\n' > "$S/sq"
KL=$S/keeper.log; KP=()
for i in 1 2; do
  ( cd "$S" && exec env -i HOME="$HOME" USER="${USER:-tester}" PATH="$FPATH" ALN33_ROOT="$S" ALN33_KEEPER_POLL=0.2 \
      FAKE_SQ="$S/sq" FAKE_SBATCH_LOG="$S/sbatch.log" timeout 300 bash "$KEEPER" ) < /dev/null >> "$KL" 2>&1 &
  KP+=($!)
done
w "k8: the second keeper refused" atleast "$KL" 'another instance holds' 1; w "k8: a submission" nsub_ge 1; hbs 4
jobs_now=$(grep -c ' c3_aln3pr ' "$S/sq"); touch "$O/STOP_queue_v3_prior"; wait "${KP[@]}"; rm -f "$O/STOP_queue_v3_prior"
chk "two keepers started together: one runs, the other exits at once" bash -c "[ \$(grep -c 'keeper_prior start' '$KL') = 1 ] && [ \$(grep -c 'another instance holds' '$KL') = 1 ]"
chk "3 running + 1 submitted = 4 c3_aln3pr jobs, not 5 ($jobs_now)" eq "$jobs_now" 4
third() { atleast "$KL" 'keeper_prior start' 2 || atleast "$KL" 'another instance holds' 2; }
keeper; w "k8: a third keeper starts or is refused" third; started=$(grep -c 'keeper_prior start' "$KL"); stopk
chk "the lock is free again once that keeper has ended" eq "$started" 2

echo "keeper: the NFSv3 stale-lock rules (holder record, heartbeat; a lock that looks stale is re-checked, then refused with exit 3)"
# On NFSv3 the server keeps a crashed node's lock until that node reboots. Here a helper process holds the lock file under the
# record a test writes (the stand-in for that server); every keeper started against it must refuse, and only by the rules.
HOSTN=$(hostname); DEADPID=$(bash -c 'echo $$')   # a process that has ended
LKN=private/auditory_alignment_v3/.keeper_prior.lock; PRESQ=""
holdlock() {  # holdlock RECORD [TOUCH-DATE]: a helper process (HP) holds the lock file's flock on its fd 9, as a keeper does; then
  # the file gets RECORD ('@HP' stands for the helper's pid) and the mtime TOUCH-DATE
  LK=$S/$LKN; : > "$LK"
  ( exec 9>> "$LK"; flock 9 && touch "$S/held" && while [ ! -e "$S/release" ]; do sleep 0.05; done ) < /dev/null > /dev/null 2>&1 &
  HP=$!; w "${S#"$T"/}: the helper holds the lock" test -e "$S/held"
  echo "${1//@HP/$HP}" > "$LK"; [ -n "${2:-}" ] && touch -d "$2" "$LK"
}
release() { touch "$S/release"; wait "$HP" 2>/dev/null; }
RACE=""
recheck_or_end() { gated 1 || ended "$KPID"; }
refused() {  # refused NAME RECORD TOUCH-DATE|"" [VAR=VALUE ...]: one keeper against a lock that the helper holds under RECORD, run to
  # its end (squeue lists PRESQ, if set); sets RC and UNTOUCHED (yes: the keeper left the lock file unchanged and still held,
  # submitted nothing, ran no loop and logged no ' heartbeat '). Its stale-lock re-checks run at once (sleep gate open); with
  # RACE set to a function, its first re-check waits until RACE has run (RACE may write a record, as a keeper that has just
  # taken the lock would: the lock file after it is the reference). The helper keeps holding the lock until release.
  local name=$1 rec=$2 when=$3 sha held race=$RACE; RACE=""; shift 3
  mk "$name"; addrow R1 2 "" ""; echo 1 > "$O/queue_v3_prior.remaining"; [ -n "$PRESQ" ] && printf '%s\n' "$PRESQ" > "$S/sq"; PRESQ=""
  holdlock "$rec" "$when"; mkdir "$S/gate"; [ -n "$race" ] || touch "$S/gate/open"; sha=$(sha256sum < "$LK")
  keeper FAKE_SLEEP_GATE="$S/gate" "$@"
  if [ -n "$race" ]; then
    w "$name: the keeper's first re-check waits" recheck_or_end && gated 1 && "$race"; sha=$(sha256sum < "$LK"); touch "$S/gate/open"
  fi
  wait $KPID; RC=$?; UNTOUCHED=no
  flock -n -E 42 "$LK" true 2>/dev/null; held=$?   # 42: the lock is still held (a conflict, not an error)
  [ "$(sha256sum < "$LK")" = "$sha" ] && [ "$held" = 42 ] && [ "$(nsub)" = 0 ] \
    && ! grep -qE 'keeper_prior start| heartbeat ' "$KL" && UNTOUCHED=yes   # (no ' heartbeat ' either: the watcher's word)
}
logs() { grep -q -- "$1" "$KL" || { echo "       no line matching [$1] in ${KL#"$T"/}: $(tail -n 2 "$KL" | head -c 400)"; return 1; }; }
stale3() {  # stale3 WHY: refused as stale for WHY, and only after the full re-check (2 + 9 x 4 = 38 s of keeper sleeps)
  [ "$RC" = 3 ] && [ "$UNTOUCHED" = yes ] && logs "looks stale: $1" && logs "STALE LOCK .*: $1 .*still so after re-checking for 38s" \
    && logs 'recovery: .*mv .*keeper_prior.lock .*keeper_prior.lock.stale_'
}
alive0() { [ "$RC" = 0 ] && [ "$UNTOUCHED" = yes ] && logs "another instance holds .*$1" && ! grep -qE 'STALE|looks stale' "$KL"; }
alive0r() {  # alive0r HOLDER WHY: exit 0 after a re-check: the first look found WHY, a later one the holder HOLDER alive
  [ "$RC" = 0 ] && [ "$UNTOUCHED" = yes ] && logs "looks stale: $2" && logs "another instance holds .*$1" && ! grep -q 'STALE LOCK' "$KL"
}
mk k11; addrow R1 2 "" ""; echo 1 > "$O/queue_v3_prior.remaining"; LK=$S/$LKN
keeper; hbs 2; touch -d '1 hour ago' "$LK"; hbs 2
rec=$(grep '^holder ' "$LK" | tail -n 1); hpid=$(sed -n 's/^holder host=[^ ]* pid=\([0-9]*\) .*/\1/p' <<< "$rec")
age=$(( $(date +%s) - $(stat -c %Y "$LK") )); stopk; last=$(tail -n 1 "$LK")
k11rec() { [[ "$rec" == "holder host=$HOSTN pid=$hpid job=session started="* ]] && [ -n "$hpid" ] && [ "$age" -le 30 ]; }
chk "the holder records 'holder host= pid= job= started=' in the lock file and refreshes its mtime every loop (${age}s old after an aged touch)" k11rec
chk "a keeper that ends appends 'released host= pid= job= at='" bash -c "[[ \"\$1\" == 'released host=$HOSTN pid=$hpid job=session at='* ]]" _ "$last"
mk k11b; addrow R1 2 "" ""; echo 1 > "$O/queue_v3_prior.remaining"; LK=$S/$LKN
keeper SLURM_JOB_ID=1039458; hbs 1; rec=$(grep '^holder ' "$LK" | tail -n 1); stopk   # (the other keeper runs have no SLURM_JOB_ID)
chk "a keeper inside a Slurm allocation (a session fallback inherits its SLURM_JOB_ID) records that job id, not 'session'" \
  bash -c "[[ \"\$1\" == 'holder host=$HOSTN pid='*' job=1039458 started='* ]]" _ "$rec"
refused k12 "holder host=$HOSTN pid=$DEADPID job=session started=2026-10-17T00:00:00" ""
chk "a lock held under a dead pid on this host: STALE LOCK, exit 3 ($RC), the recovery named, the lock untouched" stale3 "its pid $DEADPID is gone from $HOSTN or does not hold this lock file"
mv "$LK" "$LK.stale_test"; keeper; hbs 2; started=$(grep -c 'keeper_prior start' "$KL"); stopk; release
chk "the documented recovery (mv the lock file aside, the old lock still held) lets the next keeper start" eq "$started" 1
refused k12b "holder host=elsewhere.invalid pid=4242 job=session started=2026-10-17T00:00:00" '11 minutes ago'; release
chk "a holder on another host whose heartbeat is 11 min old: STALE LOCK, exit 3 ($RC), the lock untouched" stale3 "its lock file was last touched [0-9]*s ago (the holder touches it every loop), more than 600s"
refused k12c "holder host=$HOSTN pid=@HP job=session started=2026-10-17T00:00:00" '11 minutes ago'; release   # the helper: a live holder
chk "a live holder pid on this host (it holds the lock) with an 11-min-old heartbeat: STALE LOCK (hung?), exit 3 ($RC)" stale3 "its lock file was last touched [0-9]*s ago .* more than 600s (pid $HP still holds it on $HOSTN: hung?)"
refused k12h "holder host=$HOSTN pid=$$ job=session started=2026-10-17T00:00:00" ""; release   # a live pid that is no holder (reused)
chk "a live pid on this host that does not hold the lock (a reused pid), fresh heartbeat: STALE LOCK, exit 3 ($RC)" stale3 "its pid $$ is gone from $HOSTN or does not hold this lock file"
refused k12d "holder host=elsewhere.invalid pid=4242 job=session started=2026-10-17T00:00:00" ""; release
chk "a holder on another host with a fresh heartbeat: 'another instance holds', exit 0 ($RC), naming the holder" alive0 "(host=elsewhere.invalid pid=4242 job=session started=2026-10-17T00:00:00; lock touched [0-9]*s ago)"
refused k12e "holder host=elsewhere.invalid pid=4242 job=4242 started=2026-10-17T00:00:00" ""; release
chk "a holder Slurm job that squeue no longer lists: STALE LOCK, exit 3 ($RC)" stale3 "its Slurm job 4242 is not running (squeue)"
PRESQ='4242 c3_p33keeper RUNNING'; refused k12f "holder host=elsewhere.invalid pid=4242 job=4242 started=2026-10-17T00:00:00" ""; release
chk "a holder Slurm job that squeue lists as running (fresh heartbeat): 'another instance holds', exit 0 ($RC)" alive0 "job=4242"
refused k12g "holder host=elsewhere.invalid pid=4242 job=4243 started=2026-10-17T00:00:00" "" SLURM_JOB_ID=4243; release
chk "a requeued keeper job that finds its own job id in the record: STALE LOCK, exit 3 ($RC)" stale3 "its job 4243 is this job: an earlier run of this requeued keeper job"
# the race (review 2026-10-17): a keeper that has just taken the lock writes its record a moment after its flock, so a keeper
# refused in between reads the previous record; it must not call the lock stale. RACE runs while the first re-check waits.
newlocal() { echo "holder host=$HOSTN pid=$HP job=session started=2026-10-17T00:00:01" >> "$LK"; }   # the helper's own record
RACE=newlocal; refused k14 "holder host=$HOSTN pid=$DEADPID job=session started=2026-10-17T00:00:00" ""; release
chk "the last record a dead pid on this host, then the new holder's record during the re-check: exit 0 ($RC), never STALE" \
  alive0r "host=$HOSTN pid=$HP job=session" "its pid $DEADPID is gone from $HOSTN or does not hold this lock file"
newremote() { echo "holder host=elsewhere.invalid pid=4243 job=session started=2026-10-17T00:00:01" >> "$LK"; touch "$LK"; }
RACE=newremote; refused k14b "released host=elsewhere.invalid pid=4242 job=session at=2026-10-17T00:00:00" '2 hours ago'; release
chk "the last line 'released' with a 2-h-old mtime, then a new holder's record and first heartbeat: exit 0 ($RC), never STALE" \
  alive0r "host=elsewhere.invalid pid=4243 job=session" "its lock file was last touched [0-9]*s ago (the holder touches it every loop), more than 600s"
mk k14c; addrow R1 2 "" ""; echo 1 > "$O/queue_v3_prior.remaining"
holdlock "holder host=$HOSTN pid=$DEADPID job=session started=2026-10-17T00:00:00" ""; mkdir "$S/gate"
keeper FAKE_SLEEP_GATE="$S/gate"
w "k14c: the keeper's first re-check waits" gated 1; release; go 1   # the holder ends meanwhile: the lock is free
w "k14c: the keeper took the lock and finished a loop" gated 2; last=$(grep '^holder ' "$LK" | tail -n 1); stopk
chk "a lock freed during the re-check is taken, not called stale: 'freed ... takes it', a new holder record, then its loops" \
  bash -c "grep -qF 'was freed while this keeper re-checked it (its holder ended); this keeper takes it' '$KL' && grep -q 'keeper_prior start' '$KL' && grep -q ' heartbeat ready=' '$KL' && ! grep -q 'STALE LOCK' '$KL' && [[ \"\$1\" == 'holder host=$HOSTN pid='*' job=session started='* ]] && [[ \"\$1\" != *' pid=$DEADPID '* ]]" _ "$last"
mk k15; addrow R1 2 "" ""; echo 1 > "$O/queue_v3_prior.remaining"; LK=$S/$LKN
keeper FAKE_FLOCK_RC=71; wait $KPID; RC=$?
chk "a flock error (a fake exit 71, as util-linux gives for ENOLCK) is no conflict: 'cannot lock', exit 1 ($RC), no record, no loop" \
  bash -c "[ $RC = 1 ] && grep -qF 'cannot lock private/auditory_alignment_v3/.keeper_prior.lock (flock exit 71: an error, not a conflict)' '$KL' && ! grep -qE 'another instance|STALE|looks stale|keeper_prior start| heartbeat ' '$KL' && [ -e '$LK' ] && [ ! -s '$LK' ] && [ $(nsub) = 0 ]"
mk k13; addrow R1 2 "" ""; echo 1 > "$O/queue_v3_prior.remaining"; LK=$S/$LKN
keeper; hbs 2; mv "$LK" "$LK.aside"; w "k13: the keeper ends" ended $KPID; wait $KPID; RC=$?
chk "a running keeper whose lock file is moved aside (a recovery while it lived) ends at its next loop: exit 4 ($RC)" \
  bash -c "[ $RC = 4 ] && grep -qF 'keeper_prior.lock was moved or replaced (a stale-lock recovery?): this keeper no longer holds the keeper lock and ends' '$KL' && [ \"\$(tail -n 1 '$LK.aside' | cut -d' ' -f1)\" = released ]"

echo "keeper: test hooks never reach a worker submission, nor the keeper job's keeper"
mk k9; addrow R1 2 "" ""; echo 1 > "$O/queue_v3_prior.remaining"
keeper ALN33_POOL_PY=/bin/false ALN33_POOL_POLL=0.1 ALN33_POOL_IDLE=1 ALN33_POOL_STAGGER=0 FAKE_SBATCH_ENV="$S/sbatch.env"
w "k9: a submission" nsub_ge 1; hbs 2; stopk
n9=$(nsub)
chk "submissions ($n9) carry none of ALN33_ROOT / ALN33_KEEPER_POLL / ALN33_POOL_* (the keeper had all six)" bash -c "[ $n9 -ge 1 ] && [ \$(wc -l < '$S/sbatch.env') = $n9 ] && ! grep -q ALN33_ '$S/sbatch.env'"
mk k10
printf '#!/bin/bash\necho "stub args: $*"; env | grep "^ALN33_" | sed "s/^/stub env: /"\n' > "$S/private/auditory_alignment_v3/keeper_prior.sh"
( cd "$S" && exec env -i HOME="$HOME" PATH="$FPATH" SLURM_SUBMIT_DIR="$S" SLURM_JOB_ID=4321 ALN33_ROOT=/nonexistent ALN33_KEEPER_POLL=1 \
    ALN33_POOL_PY=/bin/false ALN33_POOL_POLL=1 ALN33_POOL_IDLE=1 ALN33_POOL_STAGGER=1 bash "$REPO/slurm/aln33_prior_keeper.sbatch" 3 5 ) < /dev/null > "$S/wrap.out" 2>&1
W10=$(cat "$S/wrap.out")
chk "keeper job (stub keeper): arguments passed on, every ALN33_* hook unset, rc logged" bash -c "grep -q 'stub args: 3 5' <<< \"\$1\" && ! grep -q 'stub env:' <<< \"\$1\" && grep -q 'rc=0' <<< \"\$1\"" _ "$W10"

echo "refresher (modelled): a dead worker's claim blocks its row until refresh.sh releases it"
RF=$LIVE/refresh.sh
sed -e 's#^cd /home/infres/yinwang/EEG_auditory$#cd "$REFRESH_ROOT"#' -e 's#^  PYTHONPATH=\$PWD .*make_queue\.py.*$#  :#' -e 's#^  sleep 600$#  break#' "$RF" > "$T/refresh_test.sh"
# hard guard (lead review 2026-10-17): the copy must be sandboxed, or the harness would release LIVE claims
if ! grep -qx 'cd "$REFRESH_ROOT"' "$T/refresh_test.sh" || grep -qE '^[[:space:]]*cd[[:space:]]+/' "$T/refresh_test.sh" || grep -q '/home/infres/yinwang/EEG_auditory' "$T/refresh_test.sh"; then
  echo "ABORT: the refresher test copy is not sandboxed (refresh.sh changed?); not running it"; exit 1
fi
chk "refresher test copy differs from refresh.sh in exactly 3 lines (cd, the make_queue call, sleep -> break)" bash -c "[ \$(diff '$RF' '$T/refresh_test.sh' | grep -c '^>') = 3 ]"
mk r1; addrow R1 2 "" "ok 0.3"; echo 1 > "$O/queue_v3_prior.remaining"
mkdir "$C/${E[R1]}.claim"; echo 4242 > "$C/${E[R1]}.claim/job"; touch -d '30 minutes ago' "$C/${E[R1]}.claim"
echo '77 c3_aln3fm RUNNING' > "$S/sq"
keeper; hbs 3; n0=$(nsub)
( cd "$S" && exec env -i HOME="$HOME" USER=tester PATH="$FPATH" REFRESH_ROOT="$S" FAKE_SQ="$S/sq" timeout 60 bash "$T/refresh_test.sh" ) < /dev/null > "$S/refresh.out" 2>&1
w "r1: a submission once the claim is released" nsub_ge 1; n1=$(nsub); stopk
chk "while the claim of the gone job 4242 stands: the row is not ready, nothing submitted" bash -c "[ $n0 = 0 ] && grep -q 'heartbeat ready=0 ' '$KL'"
chk "refresh.sh (sandbox copy) releases the claim; the keeper then submits a worker" bash -c "grep -q 'released claim ${E[R1]} of non-running job 4242' '$S/refresh.out' && [ ! -d '$C/${E[R1]}.claim' ] && [ $n1 -ge 1 ]"
pool 1021 5 0
chk "... and a worker runs the row" bash -c "[ -e '$O/units/${E[R1]}.json' ]"

# --------------------------------------------------------------------------------------------------------------- patches
echo "patches: apply each to a temporary copy of the live file (sha256 from the header), then test the copy"
P=$T/patched; mkdir -p "$P"
P33MARK=E34_PUBLIC_PRIOR   # every prior33 patch adds it and no unpatched live file holds it (test_infra_harness.py checks both)
declare -A PSTATE UNP
apply_patch() {  # apply_patch NAME FILE VAR: VAR = the tested copy (set in the states live and deployed); PSTATE[NAME] = live |
  # deployed | changed | bad (the header's patch states); UNP[NAME] = the verified unpatched file (its sha256 is live-sha256)
  local name=$1 f=$2 pf=$PATCHES/$1.prior33.patch live_sha want_sha got_sha src=$PL/$2 dst=$P/$2
  printf -v "$3" '%s' ""; PSTATE[$name]=bad
  live_sha=$(sed -n 's/^# live-sha256: *\([0-9a-f]\{64\}\).*/\1/p' "$pf"); want_sha=$(sed -n 's/^# patched-sha256: *\([0-9a-f]\{64\}\).*/\1/p' "$pf")
  [ -n "$live_sha" ] && [ -n "$want_sha" ] || { echo "       $pf: no live-sha256 / patched-sha256 header"; return 1; }
  cp -p "$src" "$dst" || return 1; got_sha=$(sha256sum "$dst" | cut -d' ' -f1)
  if [ "$got_sha" = "$live_sha" ]; then                  # not deployed: the patch is applied to the copy
    cp -p "$dst" "$dst.unpatched"
    patch --no-backup-if-mismatch --silent "$dst" < "$pf" || return 1
    [ "$(sha256sum "$dst" | cut -d' ' -f1)" = "$want_sha" ] || { echo "       $f: patched copy differs from patched-sha256"; return 1; }
    PSTATE[$name]=live
  elif [ "$got_sha" = "$want_sha" ]; then                # deployed: tested as it is; the unpatched file is its reverse patch
    cp -p "$dst" "$dst.unpatched"
    patch -R --no-backup-if-mismatch --silent "$dst.unpatched" < "$pf" || { echo "       $f: the reverse patch does not apply"; return 1; }
    [ "$(sha256sum "$dst.unpatched" | cut -d' ' -f1)" = "$live_sha" ] || { echo "       $f: its reverse patch differs from live-sha256"; return 1; }
    echo "       $f is deployed (patched-sha256): tested as it is, against its reverse patch (live-sha256)"
    PSTATE[$name]=deployed
  elif grep -qF "$P33MARK" "$dst"; then PSTATE[$name]=changed; return 0   # changed after deployment (the caller reports n/a)
  else
    echo "       $f: live sha256 $got_sha is neither the header's live-sha256 nor patched-sha256, and the file does not carry" \
         "$P33MARK: it changed before deployment; regenerate the patch"
    return 1
  fi
  UNP[$name]=$dst.unpatched; printf -v "$3" '%s' "$dst"
}
for x in watch_anyhost:watch_anyhost.sh:WP make_queue:make_queue.py:MP ckpt_offload:ckpt_offload.py:CP; do
  IFS=: read -r name f var <<< "$x"; apply_patch "$name" "$f" "$var"
  case ${PSTATE[$name]} in
    live) ok "$name patch applies to a copy of the live file (sha256 checked)";;
    deployed) ok "$name patch is deployed: the live file has patched-sha256, its reverse patch live-sha256 (the unpatched file below)";;
    changed) na "$name patch checks (patch, behaviour, line count, recipe)" \
                "the live $f carries $P33MARK but matches neither sha256 header: it changed after deployment, so nothing pins it any more";;
    *) bad "$name patch applies to a copy of the live file (sha256 checked)";;
  esac
done
unp() {  # unp NAME DESCRIPTION: 0 when NAME's verified unpatched file exists; otherwise 1, and a FAIL for DESCRIPTION unless the
  # live file changed after deployment (already reported n/a)
  [ -n "${UNP[$1]:-}" ] && return 0
  [ "${PSTATE[$1]}" = changed ] || bad "$2 (no verified unpatched $1 file: see above)"; return 1
}
pre() { [ "${PSTATE[$1]}" = deployed ] && echo " (on the pre-deployment file, the reverse patch)"; }   # pre NAME: a check label
for x in make_queue ckpt_offload; do
  chk "$x patch only adds lines" bash -c "[ \$(grep -c '^-' '$PATCHES/$x.prior33.patch') = 1 ]"  # the '--- a/...' line
done
if unp watch_anyhost "watch_anyhost patch replaces exactly 5 live lines"; then
  chk "watch_anyhost patch replaces exactly 5 live lines$(pre watch_anyhost) (v3 header end, spec, set, strike, EVENT); everything else is added" \
    bash -c "diff <(grep '^-[^-]' '$PATCHES/watch_anyhost.prior33.patch' | cut -c2-) <(sed -n '5p;34p;35p;39p;40p' '${UNP[watch_anyhost]}') && [ \$(grep -c '^-' '$PATCHES/watch_anyhost.prior33.patch') = 6 ]"
fi

if [ -n "$WP" ]; then
  chk "watch_anyhost (patched): bash -n" bash -n "$WP"
  # runnable copy: sandbox root, 0.05-s ticks that also log each finished loop to ./watch_ticks, no python (bc_done prints
  # nothing); exactly these three lines change
  sed -e 's#^cd /home/infres/yinwang/EEG_auditory$#cd "$WATCH_ROOT"#' -e 's#^  sleep 60$#  echo "$tick" >> watch_ticks; sleep 0.05#' -e 's#^PY=/home/infres/yinwang/anaconda3/envs/eeg2025/bin/python$#PY=/bin/false#' "$WP" > "$T/watch_test.sh"
  chk "watcher test copy differs from the patched file in exactly 3 lines" bash -c "[ \$(diff '$WP' '$T/watch_test.sh' | grep -c '^>') = 3 ]"
  wsand() {  # wsand NAME [REMAINING|-] [rows|empty|none]: watcher sandbox with fresh refresh / offload logs, empty fm / small
    # queues, queue_v3_prior.remaining (default 2; '-': no file) and the prior queue: 2 unclaimed rows (default), empty, or no file
    local rem=${2:-2} q=${3:-rows}
    mk "$1"; mkdir -p "$O/logs"; touch "$O/logs/refresh.log" "$O/logs/ckpt_offload.log" "$O/logs/c3_dummy.log"
    : > "$O/queue_v3_fm.txt"; : > "$O/queue_v3_small.txt"
    case $q in rows) addrow W1 2 "" ""; addrow W2 2 "" "";; none) mv "$O/queue_v3_prior.txt" "$O/queue_v3_prior.txt.absent";; esac
    [ "$rem" = - ] || echo "$rem" > "$O/queue_v3_prior.remaining"
    echo '7 c3_ckptoff RUNNING' > "$S/sq"
  }
  # Event-based: a watcher run ends at its EVENT (it exits) or once it has finished LOOPS loops, counted in its own log, and
  # MAX s only bound a run that hangs; so a check never depends on how many loops fit into a fixed time on a loaded node.
  wdone() { [ "$(grep -c '' "$S/watch_ticks" 2>/dev/null)" -ge "$1" ] || ! kill -0 "$2" 2>/dev/null; }
  watch() {  # watch LOOPS MAX: runs the watcher test copy; sets out (its output) and WT (the loops it finished)
    local pid
    : > "$S/watch_ticks"
    ( cd "$S" && exec env -i HOME="$HOME" USER=tester PATH="$FPATH" WATCH_ROOT="$S" FAKE_SQ="$S/sq" timeout "$2" bash "$T/watch_test.sh" ) \
      < /dev/null > "$S/watch.out" 2>&1 &
    pid=$!; waitfor "$2" wdone "$1" $pid; kill $pid 2>/dev/null; wait $pid 2>/dev/null
    WT=$(grep -c '' "$S/watch_ticks"); out=$(cat "$S/watch.out")
  }
  quiet() {  # quiet N: no output, and the watcher finished at least N loops (every EVENT needs at most 20 loops in a row)
    empty "$out" && { [ "$WT" -ge "$1" ] || { echo "       the watcher finished only $WT loops (wanted $1)"; return 1; }; }
  }
  hb() {  # hb SUFFIX N: N keeper heartbeat lines ending in SUFFIX
    local i; for i in $(seq 1 "$2"); do echo "2026-10-17T03:$(printf %02d "$i"):00 heartbeat ready=2 (no oom mark: 2; also ready last pass: 2) workers=0 pending=0 remaining=2$1"; done
  }
  FOUR='11 c3_aln3pr RUNNING\n12 c3_aln3pr RUNNING\n13 c3_aln3pr RUNNING\n14 c3_aln3pr RUNNING\n'
  wsand w1; watch 1000 120
  chk "watcher: dead prior keeper (no log), no workers, unclaimed rows -> EVENT" contains "$out" "EVENT keeper for queue_v3_prior seems dead: 0/4 workers"
  wsand w2; touch "$O/logs/keeper_prior.log"; ( while [ ! -e "$S/touch.stop" ]; do touch "$O/logs/keeper_prior.log"; sleep 0.1; done ) & hb=$!
  watch 12 120; touch "$S/touch.stop"; wait $hb
  chk "watcher: a keeper heartbeat < 3 min old -> no EVENT ($WT loops)" quiet 12
  wsand w4; printf "$FOUR" >> "$S/sq"; watch 12 120
  chk "watcher: 4 workers running, stale keeper -> no EVENT ($WT loops)" quiet 12
  wsand w5; touch "$O/STOP_queue_v3_prior"; watch 12 120
  chk "watcher: STOP_queue_v3_prior -> no EVENT ($WT loops)" quiet 12
  wsand w6; for k in W1 W2; do record $k; done; watch 12 120
  chk "watcher: lane end (every listed row done) -> no EVENT ($WT loops)" quiet 12
  wsand w7 - none; watch 22 120
  chk "watcher: no prior queue file yet (and no .remaining) -> no EVENT and no error output ($WT loops)" quiet 22
  wsand w8; touch "$O/STOP_queue_v3_prior"; echo 'X|1' > "$O/queue_v3_fm.txt"; watch 1000 120
  chk "watcher: the fm spec still raises its own EVENT (unchanged)" contains "$out" "EVENT keeper for queue_v3_fm seems dead"
  echo "  watcher: prior staleness 120 s / 9 strikes (about 10 min after the last heartbeat); fm keeps 180 s"
  # agedlog holds a log 90 s / 130 s old while the watcher runs (re-touched every 0.1 s), so these runs need no time bound;
  # 10 / 11 finished loops exceed the 9 (prior) / 10 (fm) strikes that an EVENT at a lower threshold would need
  agedlog() { ( while [ ! -e "$S/age.stop" ]; do touch -d "$1 seconds ago" "$2"; sleep 0.1; done ) & AGP=$!; }   # agedlog SECONDS FILE
  agedstop() { touch "$S/age.stop"; wait "$AGP"; }
  wsand w9; agedlog 90 "$O/logs/keeper_prior.log"; watch 10 120; agedstop
  chk "watcher: prior keeper log 90 s old, no workers, unclaimed rows -> no EVENT ($WT loops)" quiet 10
  wsand w10; touch -d '130 seconds ago' "$O/logs/keeper_prior.log"; watch 1000 120
  chk "watcher: prior keeper log 130 s old, no workers, unclaimed rows -> EVENT" contains "$out" "EVENT keeper for queue_v3_prior seems dead"
  wsand w10b; touch "$O/STOP_queue_v3_prior"; echo 'X|1' > "$O/queue_v3_fm.txt"; agedlog 130 "$O/logs/keeper_fm.log"; watch 11 120; agedstop
  chk "watcher: fm keeper log 130 s old -> no EVENT (the fm threshold stays 180 s; $WT loops)" quiet 11
  echo "  watcher: a prior keeper that heartbeats but cannot act"
  wsand w11; hb " sbatch refused (rc=1)" 10 > "$O/logs/keeper_prior.log"; watch 1000 120
  chk "watcher: fresh keeper log, last 10 heartbeats 'sbatch refused' -> EVENT cannot act" contains "$out" "EVENT keeper for queue_v3_prior cannot act"
  wsand w12; { hb " sbatch refused (rc=1)" 9; hb " submitted worker 5001" 1; } > "$O/logs/keeper_prior.log"; watch 12 120
  chk "watcher: 9 refusals, then a submission -> no EVENT ($WT loops)" quiet 12
  wsand w12b; { hb " sbatch refused (rc=1)" 10; echo "2026-10-17T03:11:00 queue_v3_prior.remaining is 0 on two consecutive loops (lane complete); keeper ends"; } > "$O/logs/keeper_prior.log"
  watch 12 120
  chk "watcher: 10 refusals, then the keeper ended -> no 'cannot act' EVENT ($WT loops)" bash -c "$(declare -f lacks); lacks \"\$1\" 'cannot act' && [ $WT -ge 12 ]" _ "$out"
  wsand w13; hb " squeue failed: nothing submitted" 10 > "$O/logs/keeper_prior.log"; watch 1000 120
  chk "watcher: last 10 heartbeats 'squeue failed' -> EVENT cannot act" contains "$out" "EVENT keeper for queue_v3_prior cannot act"
  wsand w14; hb " sbatch refused (rc=1)" 10 > "$O/logs/keeper_prior.log"; touch -d '10 minutes ago' "$O/logs/keeper_prior.log"; printf "$FOUR" >> "$S/sq"
  watch 12 120
  chk "watcher: the same refusals in a stale log (keeper gone; 4 workers) -> no EVENT ($WT loops)" quiet 12
  echo "  watcher: the prior queue in make_queue.py's error state"
  wsand w15 unknown empty; touch "$O/logs/keeper_prior.log"
  echo "01:00:00 small 3 {} fm 0 {} prior queue error ValueError('synthetic'): queue_v3_prior written empty, .remaining unknown " >> "$O/logs/refresh.log"
  watch 1000 120
  chk "watcher: .remaining 'unknown' for 20 ticks -> EVENT error state, with refresh.log's error" bash -c "grep -qF \"EVENT prior queue in make_queue.py's error state for 20 min (queue_v3_prior.remaining 'unknown')\" <<< \"\$1\" && grep -qF \"prior queue error ValueError('synthetic')\" <<< \"\$1\"" _ "$out"
  wsand w16 held empty; watch 22 120
  chk "watcher: .remaining 'held' (paused lane, empty queue) -> no EVENT ($WT loops)" quiet 22
  wsand w17 - empty; watch 1000 120
  chk "watcher: a prior queue without .remaining for 20 ticks -> EVENT error state ('missing')" contains "$out" "queue_v3_prior.remaining 'missing'"
  wsand w18 0 empty; watch 22 120
  chk "watcher: .remaining 0 (lane complete) -> no EVENT ($WT loops)" quiet 22
  wsand w19 unknown empty; touch "$O/STOP_queue_v3_prior"; watch 22 120
  chk "watcher: 'unknown' with STOP_queue_v3_prior -> no EVENT ($WT loops)" quiet 22
fi

if [ -n "$MP" ]; then
  chk "make_queue (patched): python syntax" "$PYH" -B -c "import ast, sys; ast.parse(open(sys.argv[1]).read())" "$MP"
  echo "  make_queue (patched) in a sandbox with a fake core / registry and the real prior33:"
  ALN33_HARNESS_DIR=$T PYTHONPATH=$REPO "$PYH" -B "$HERE/harness_checks.py" make_queue "$MP" | sed 's/^/  /'
  chk "make_queue (patched): sandbox checks" [ "${PIPESTATUS[0]}" = 0 ]
fi
if [ -n "$CP" ]; then
  chk "ckpt_offload (patched): python syntax" "$PYH" -B -c "import ast, sys; ast.parse(open(sys.argv[1]).read())" "$CP"
  if [ -e "$CP.unpatched" ]; then
    echo "  ckpt_offload (patched) import test with fake runner modules and the real prior33, against the unpatched copy$(pre ckpt_offload):"
    ALN33_HARNESS_DIR=$T PYTHONPATH=$REPO "$PYH" -B "$HERE/harness_checks.py" ckpt_offload "$CP" "$CP.unpatched" | sed 's/^/  /'
    chk "ckpt_offload (patched): import and deps_of checks" [ "${PIPESTATUS[0]}" = 0 ]
  else bad "ckpt_offload (patched): import and deps_of checks (no unpatched copy to compare with)"; fi
fi

# ------------------------------------------------------------------------------------------------------- apply recipes
echo "recipes: each patch header's apply recipe, run verbatim in a sandbox copy of the repo layout"
recipe() {  # recipe NAME DIR: runs the header recipe of NAME's patch from DIR (the unpatched file already placed); prints the exit status
  local name=$1 R=$2
  mkdir -p "$R/private/auditory_alignment_v3/aln34/prior33_patches"
  cp -p "$PATCHES/$name.prior33.patch" "$R/private/auditory_alignment_v3/aln34/prior33_patches/"
  sed -n '/^# apply (/,/^#   mv -f /p' "$PATCHES/$name.prior33.patch" | sed -n 's/^#   //p' > "$R/recipe.sh"
  # PATH=$FPATH: the fake squeue / sbatch come first, so recipe text that ever named them could not reach the live fleet
  # (the recipes need only sha256sum, cp, patch, mv, date, bash and the absolute python, all in /usr/bin)
  ( cd "$R" && exec env -i HOME="$HOME" PATH="$FPATH" bash recipe.sh ) < /dev/null > "$R/recipe.out" 2>&1
  echo $?
}
for x in watch_anyhost:watch_anyhost.sh make_queue:make_queue.py ckpt_offload:ckpt_offload.py; do
  name=${x%%:*}; f=${x#*:}; unp "$name" "$name recipe" || continue
  R=$T/recipe_$name; D=$R/private/auditory_alignment_v3; mkdir -p "$D"; cp -p "${UNP[$name]}" "$D/$f"
  want=$(sed -n 's/^# patched-sha256: *\([0-9a-f]\{64\}\).*/\1/p' "$PATCHES/$name.prior33.patch")
  have=$(sed -n 's/^# live-sha256: *\([0-9a-f]\{64\}\).*/\1/p' "$PATCHES/$name.prior33.patch")
  rc=$(recipe $name "$R")
  chk "$name recipe$(pre $name): exit 0 ($rc), file = patched-sha256, dated backup = live-sha256, no tmp left, $(grep -c . "$R/recipe.sh") lines run" \
    bash -c "[ '$rc' = 0 ] && [ \"\$(sha256sum '$D/$f' | cut -d' ' -f1)\" = '$want' ] && [ \"\$(cat '$D/$f'.before_prior33_* | sha256sum | cut -d' ' -f1)\" = '$have' ] && [ ! -e '$D/$f.tmp_prior33' ]"
  [ "$rc" = 0 ] || sed 's/^/       /' "$R/recipe.out" | tail -5
done
if unp make_queue "the recipe's sha256 check on a live file changed since the patch"; then
  R=$T/recipe_drift; D=$R/private/auditory_alignment_v3; mkdir -p "$D"; cp -p "${UNP[make_queue]}" "$D/make_queue.py"; echo "# drift" >> "$D/make_queue.py"
  drift=$(sha256sum "$D/make_queue.py" | cut -d' ' -f1); rc=$(recipe make_queue "$R")
  chk "a live file that changed since the patch: the recipe stops at its sha256 check (file untouched, no backup, no tmp)" \
    bash -c "[ '$rc' != 0 ] && [ \"\$(sha256sum '$D/make_queue.py' | cut -d' ' -f1)\" = '$drift' ] && ! ls '$D'/make_queue.py.before_prior33_* > /dev/null 2>&1 && [ ! -e '$D/make_queue.py.tmp_prior33' ]"
fi

# ------------------------------------------------------------------------------------------------------- sbatch syntax
echo "sbatch files: bash -n, directives"
for f in aln33_prior_pool aln33_prior_keeper aln33_prior_cpu aln33_prior_gpu_probe; do chk "slurm/$f.sbatch: bash -n" bash -n "$REPO/slurm/$f.sbatch"; done
chk "keeper_prior.sh: bash -n" bash -n "$KEEPER"
chk "pool: job name c3_aln3pr, partitions V100,A30,A40,L40S, runfill, no --time, no --nice" bash -c "f='$POOL'; grep -qx '#SBATCH --job-name=c3_aln3pr' \$f && grep -qx '#SBATCH --partition=V100,A30,A40,L40S' \$f && grep -qx '#SBATCH --qos=runfill' \$f && ! grep -q '^#SBATCH --time' \$f && ! grep -q '^#SBATCH --nice' \$f"
chk "probe: partitions V100,A30,A40,L40S, no --time, no --nice, ALN3 logs" bash -c "f='$REPO/slurm/aln33_prior_gpu_probe.sbatch'; grep -qx '#SBATCH --partition=V100,A30,A40,L40S' \$f && ! grep -q '^#SBATCH --time' \$f && ! grep -q '^#SBATCH --nice' \$f && grep -qx '#SBATCH --output=private/auditory_alignment_v3/logs/%x-%j.log' \$f"
chk "keeper job: CPU, 1 CPU, 1G, no --time, keeper_prior.log appended" bash -c "f='$REPO/slurm/aln33_prior_keeper.sbatch'; grep -qx '#SBATCH --partition=CPU' \$f && grep -qx '#SBATCH --cpus-per-task=1' \$f && grep -qx '#SBATCH --mem=1G' \$f && ! grep -q '^#SBATCH --time' \$f && grep -qx '#SBATCH --open-mode=append' \$f && grep -qx '#SBATCH --output=private/auditory_alignment_v3/logs/keeper_prior.log' \$f"
chk "cpu job: CPU partition, no runfill, --time=2-00:00:00, append, ALN3 logs" bash -c "f='$REPO/slurm/aln33_prior_cpu.sbatch'; grep -qx '#SBATCH --partition=CPU' \$f && ! grep -q '^#SBATCH --qos' \$f && grep -qx '#SBATCH --time=2-00:00:00' \$f && grep -qx '#SBATCH --open-mode=append' \$f && grep -qx '#SBATCH --output=private/auditory_alignment_v3/logs/%x-%j.log' \$f"
chk "no new job name starts with c3_aln3 except the pool workers" bash -c "! grep -h '^#SBATCH --job-name=' '$REPO/slurm/aln33_prior_keeper.sbatch' '$REPO/slurm/aln33_prior_cpu.sbatch' '$REPO/slurm/aln33_prior_gpu_probe.sbatch' | grep -q 'c3_aln3'"
finish
