#!/bin/bash
#SBATCH --job-name=c3_p33probe
# E34_PUBLIC_PRIOR GPU engineering probe (ALN3.4; PUBLIC_PRIOR_DESIGN.md §6.5, §7.2, §8): a copy of aln2_gpu_probe.sbatch with
# --partition=V100,A30,A40,L40S, no nice (submit at nice 0, so it outranks the FM keeper's nice-50 replacements), no --time (user
# rule: no time limit on V100/A30/A40/L40S; the partition maximum applies) and ALN3 logs. Runs the python script given as
# arguments on one whole GPU (no MPS); probe_prior33.py writes only to private/auditory_alignment_v3/probe_out_prior33/.
# The name avoids the c3_aln3 prefix (watch_anyhost.sh / ckpt_offload.py read it as ALN3 pool workers).
# Usage (from the repo root): sbatch slurm/aln33_prior_gpu_probe.sbatch private/auditory_alignment_v3/probe_prior33.py [args]
#SBATCH --qos=runfill
#SBATCH --partition=V100,A30,A40,L40S
#SBATCH --exclude=node52
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=12
#SBATCH --mem=64G
#SBATCH --open-mode=append
#SBATCH --output=private/auditory_alignment_v3/logs/%x-%j.log
set -uo pipefail
umask 077
cd "$SLURM_SUBMIT_DIR" || exit 1
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 OMP_NUM_THREADS=12 MKL_NUM_THREADS=12 PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=0 PYTHONPATH=$PWD _MNE_FAKE_HOME_DIR=$(mktemp -d) MNE_USE_NUMBA=false
echo "start $(date -Is) node=${SLURMD_NODENAME:-?} gpu=$(nvidia-smi --query-gpu=name,memory.total --format=csv,noheader) job=${SLURM_JOB_ID:-?} args=$*"
/home/infres/yinwang/anaconda3/envs/eeg2025/bin/python "$@"
rc=$?; echo "end $(date -Is) rc=$rc"; exit $rc  # capture before $(date) runs (audit 2026-10-11)
