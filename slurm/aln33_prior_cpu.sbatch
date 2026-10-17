#!/bin/bash
#SBATCH --job-name=c3_p33cpu
# E34_PUBLIC_PRIOR CPU jobs (ALN3.4; PUBLIC_PRIOR_DESIGN.md §6.2, §6.5 step 1): the cache builders C1-C5 and C7, the manifest C6
# and the synthetic tests. A copy of the bc_interim_cpu.sbatch pattern: CPU partition, normal QOS (no runfill), 8 CPUs, 32 GB
# (lower per job with -c 4 --mem=16G), --time=2-00:00:00, logs appended under private/auditory_alignment_v3/logs/. Each builder
# is resumable per item (done markers, tmp + os.replace), so a resubmission continues where a job stopped.
# Normal-QOS budget: these jobs count against the user's normal-QOS jobs (MaxSubmitJobsPU 30, shared with another project and
# every session; the design target, §6.2, is 25 or fewer). On 2026-10-17 the count sat at 25-28 of 30, so run at most 1-2 of
# these jobs at a time, and run the keeper as the session fallback in keeper_prior.sh's header (it costs no job). Count before
# every submission instead of assuming a figure: squeue -u $USER -h -q normal | wc -l (the session's own allocation included);
# at 30 every further submission, from any session or project, is refused. sbatch --test-only shows the expected start (on
# 2026-10-17 new CPU-partition jobs showed starts one to three days out).
# Order (§6.2 and the modules' own rules): build_sparrkulee runs C1, then C2, then C4 (C4 refuses to start before C2 is
# complete); C3 (scan_audio) and C5 (build_public) read the sources only; C7 (build_rich) reads C4's and C5's tables, and its
# pass 1 may overlap C3 (without a complete C3 it exits 5; the same command after C3 finishes in minutes); C6 (manifest, module
# M2e) freezes the manifest before any donor unit runs: --part core needs C1-C5 and never waits for C7; --part rich runs after
# C7 and the core part (manifest.py's docstring governs both; the full copy goes to --out-private, by default
# private/auditory_alignment_v3/aln34/prior33/). Under the 1-2 job cap: C1; C2 | C5; C4 | C3; C6 core | C7; C6 rich
# (on 2026-10-17 C1, C2 and C4 were complete and C3 and C5 were running).
# Usage (from the repo root): sbatch [-J name] [-c N --mem=M] slurm/aln33_prior_cpu.sbatch <python args...> | pytest <args...>
#   <root> = /projects/EEG-foundation-model/auditory_public/derived/aln33_env64_125ms_v1 (the §6.2 cache root)
#   tests : sbatch -J c3_p33test slurm/aln33_prior_cpu.sbatch pytest -q tests/auditory_alignment_v3/prior33
#   C1    : sbatch -J c3_p33c1 slurm/aln33_prior_cpu.sbatch -m auditory_alignment_v3.prior33.build_sparrkulee --stage C1 --out <root>
#   C2    : sbatch -J c3_p33c2 slurm/aln33_prior_cpu.sbatch -m auditory_alignment_v3.prior33.build_sparrkulee --stage C2 --out <root>
#   C4    : sbatch -J c3_p33c4 slurm/aln33_prior_cpu.sbatch -m auditory_alignment_v3.prior33.build_sparrkulee --stage C4 --out <root>
#   C3    : sbatch -J c3_p33c3 slurm/aln33_prior_cpu.sbatch -m auditory_alignment_v3.prior33.scan_audio --out <root>
#   C5    : sbatch -J c3_p33c5 -c 2 --mem=8G slurm/aln33_prior_cpu.sbatch -m auditory_alignment_v3.prior33.build_public --cohort all --mode all
#   C7    : sbatch -J c3_p33c7 -c 4 --mem=16G slurm/aln33_prior_cpu.sbatch -m auditory_alignment_v3.prior33.build_rich --out <root>
#   C6    : sbatch -J c3_p33c6 slurm/aln33_prior_cpu.sbatch -m auditory_alignment_v3.prior33.manifest --part core --root <root>
#           sbatch -J c3_p33c6 slurm/aln33_prior_cpu.sbatch -m auditory_alignment_v3.prior33.manifest --part rich --root <root>
#   (C5 writes to <root> by default, its --out; every module's docstring and --help give its other options and its CPU / memory
#   needs; run prior33 entry points with -m, never by path: select.py)
# Job names avoid the c3_aln3 prefix, which watch_anyhost.sh and ckpt_offload.py read as running ALN3 GPU workers.
#SBATCH --partition=CPU
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=2-00:00:00
#SBATCH --open-mode=append
#SBATCH --output=private/auditory_alignment_v3/logs/%x-%j.log
set -uo pipefail
umask 077
cd "$SLURM_SUBMIT_DIR" || exit 1
export PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=$PWD PYTHONHASHSEED=0 HF_HUB_OFFLINE=1 _MNE_FAKE_HOME_DIR=$(mktemp -d) MNE_USE_NUMBA=false
export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK MKL_NUM_THREADS=$SLURM_CPUS_PER_TASK OPENBLAS_NUM_THREADS=$SLURM_CPUS_PER_TASK MKL_CBWR=AUTO
PY=/home/infres/yinwang/anaconda3/envs/eeg2025/bin/python
echo "start $(date -Is) node=${SLURMD_NODENAME:-?} job=${SLURM_JOB_ID:-?} args: $*"
if [ "${1:-}" = pytest ]; then shift; $PY -B -m pytest -p no:cacheprovider "$@"; else $PY -B "$@"; fi
rc=$?; echo "end $(date -Is) rc=$rc"; exit $rc  # capture before $(date) runs (audit 2026-10-11)
