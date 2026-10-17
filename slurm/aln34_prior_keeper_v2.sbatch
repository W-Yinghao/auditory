#!/bin/bash
#SBATCH --job-name=c3_p33keeper
#SBATCH --partition=CPU
#SBATCH --qos=normal
#SBATCH --cpus-per-task=1
#SBATCH --mem=1G
#SBATCH --time=4-00:00:00
#SBATCH --open-mode=append
#SBATCH --output=private/auditory_alignment_v3/logs/keeper_prior.log
set -uo pipefail
umask 077
cd "$SLURM_SUBMIT_DIR" || exit 1
unset ALN33_ROOT ALN33_KEEPER_POLL ALN33_POOL_PY ALN33_POOL_POLL ALN33_POOL_IDLE ALN33_POOL_STAGGER
export PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=$PWD
echo "efficiency keeper v2 start $(date -Is) job=$SLURM_JOB_ID"
/home/infres/yinwang/anaconda3/envs/eeg2025/bin/python -B private/auditory_alignment_v3/aln34/efficiency_loop.py --keeper-start || exit 1
bash private/auditory_alignment_v3/keeper_prior_v2.sh 4 8
rc=$?
echo "efficiency keeper v2 end $(date -Is) job=$SLURM_JOB_ID rc=$rc"
exit "$rc"
