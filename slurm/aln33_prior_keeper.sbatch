#!/bin/bash
#SBATCH --job-name=c3_p33keeper
# E34_PUBLIC_PRIOR keeper job (ALN3.4; PUBLIC_PRIOR_DESIGN.md §6.5, §8): runs private/auditory_alignment_v3/keeper_prior.sh, which
# keeps up to 4 c3_aln3pr pool workers (slurm/aln33_prior_pool.sbatch, at most 2 pending) while ready rows exist, writes a
# heartbeat line every 60 s and stops when queue_v3_prior.remaining reads 0 twice or on STOP_queue_v3_prior. CPU partition,
# normal QOS, 1 CPU, 1 GB, no --time (the CPU partition maximum, 4 days, applies), output appended to
# private/auditory_alignment_v3/logs/keeper_prior.log (the file watch_anyhost.sh checks).
# Normal-QOS budget: this job is one of the user's normal-QOS jobs (MaxSubmitJobsPU 30, shared with another project and every
# session; the design target is 25 or fewer). On 2026-10-17 the count sat at 25-28 of 30, so this job and the 1-2 CPU builders
# that may run at a time (slurm/aln33_prior_cpu.sbatch) can reach 30, where every further submission, from any session or
# project, is refused. Count first (squeue -u $USER -h -q normal | wc -l, the session's own allocation included; do not assume a
# figure) and check the expected start (sbatch --test-only; on 2026-10-17 new CPU-partition jobs showed starts one to three days
# out). While the count is high or the start is far off, run the session fallback in keeper_prior.sh's header instead: it costs
# no Slurm job, and keeper_prior.sh's lock lets only one keeper run if this job starts later (that one then exits: rc 0 at once
# while the holder looks alive, rc 3 if the lock still looks stale after a re-check of up to 40 s, rc 1 if flock itself fails;
# it never takes the lock over, see keeper_prior.sh's header).
# The name avoids the c3_aln3 prefix, which watch_anyhost.sh and ckpt_offload.py read as running ALN3 GPU workers.
# The keeper's and the pool's test hooks (ALN33_*) are unset here, so a value left in the submitting shell (sbatch exports the
# environment by default) never reaches the real keeper or its workers.
# Usage (from the repo root): sbatch slurm/aln33_prior_keeper.sbatch [MAXG [PAR]]
#SBATCH --partition=CPU
#SBATCH --cpus-per-task=1
#SBATCH --mem=1G
#SBATCH --open-mode=append
#SBATCH --output=private/auditory_alignment_v3/logs/keeper_prior.log
set -uo pipefail
umask 077
cd "$SLURM_SUBMIT_DIR" || exit 1
unset ALN33_ROOT ALN33_KEEPER_POLL ALN33_POOL_PY ALN33_POOL_POLL ALN33_POOL_IDLE ALN33_POOL_STAGGER
echo "start $(date -Is) node=${SLURMD_NODENAME:-?} job=${SLURM_JOB_ID:-?} args: $*"
bash private/auditory_alignment_v3/keeper_prior.sh "$@"
rc=$?; echo "end $(date -Is) rc=$rc"; exit $rc  # capture before $(date) runs (audit 2026-10-11)
