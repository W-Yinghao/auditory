#!/usr/bin/env bash
#SBATCH --job-name=auditory_story
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=04:00:00
#SBATCH --qos=runfill
#SBATCH --requeue
#SBATCH --signal=B:USR1@120
set -euo pipefail

# Template only. Supply an allowed CPU/GPU partition at sbatch submission.
# GPU inference additionally needs an allowed --partition and --gres=gpu:1.
# Do not submit until the server adapter/CLI and checkpoint handler are implemented.
if [[ -z "${SLURM_JOB_ID:-}" ]]; then
  echo "Refusing to run outside Slurm on the server." >&2; exit 2
fi
: "${AUDITORY_REPO_ROOT:?Set the existing repository root}"
: "${AUDITORY_STORY_CONFIG:?Set the absolute path to the resolved story config}"
: "${AUDITORY_STORY_PHASE:?Set prepare/train-profile/clinical/evaluate/report}"
: "${AUDITORY_STORY_RUN:?Set a new, explicit run identifier}"
case "$AUDITORY_STORY_PHASE" in
  prepare|train-profile|clinical|evaluate|report) ;;
  *) echo "Phase is outside the default authorized matrix." >&2; exit 2 ;;
esac
cd "$AUDITORY_REPO_ROOT"
[[ -f "$AUDITORY_STORY_CONFIG" ]] || { echo "Configuration missing." >&2; exit 2; }
python - <<'PYCHECK'
from importlib.util import find_spec
try:
    present = find_spec('auditory_story.cli') is not None
except ModuleNotFoundError:
    present = False
if not present:
    raise SystemExit('auditory_story.cli is a to-be-implemented server interface; no job has run.')
PYCHECK
# The future CLI must handle USR1 for checkpoints and atomic per-unit completion.
exec python -m auditory_story.cli "$AUDITORY_STORY_PHASE" \
  --config "$AUDITORY_STORY_CONFIG" --run "$AUDITORY_STORY_RUN"
