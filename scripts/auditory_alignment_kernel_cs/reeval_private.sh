#!/bin/bash
# evaluation-only rerun (current evaluate.py) of private units whose evaluation predates code hash C; originals archived
cd /home/infres/yinwang/EEG_auditory
export PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=$PWD PYTHONHASHSEED=0 OMP_NUM_THREADS=2 _MNE_FAKE_HOME_DIR=$(mktemp -d)
PY=/home/infres/yinwang/anaconda3/envs/eeg2025/bin/python
O=private/auditory_alignment_kernel_cs; M=AUDITORY_KERNEL_CS_FULL_EXPERIMENTS_SERVER_v1_20261005/planned_jobs.jsonl
mkdir -p $O/units_eval_AB
$PY - > $O/reeval_private_todo.txt <<'PYEOF'
import json, glob
C = json.load(open("private/auditory_alignment_kernel_cs/fleet_code_hashes.json"))["C"]
for p in sorted(glob.glob("private/auditory_alignment_kernel_cs/units/*private_bdf*.json")):
    if p.endswith("FAILED.json"):
        continue
    r = json.load(open(p))
    if r.get("code_hash") != C and r.get("reeval_code_hash") != C:
        print(r["job"]["experiment_id"])
PYEOF
echo "to re-evaluate: $(wc -l < $O/reeval_private_todo.txt)"
while read -r e; do [ -e $O/units_eval_AB/$e.json ] || cp $O/units/$e.json $O/units_eval_AB/$e.json; done < $O/reeval_private_todo.txt
xargs -P 4 -I{} $PY -m auditory_alignment.run --manifest $M --experiment-id {} --reeval-from $O --out $O < $O/reeval_private_todo.txt 2>&1 | grep -v Warning | grep -c "^reeval"
# private linear-reference units: rerun under the current evaluation
mkdir -p $O/units_linear_eval_AB
$PY - <<'PYEOF'
import json, glob, os, shutil
O = "private/auditory_alignment_kernel_cs"; C = json.load(open(f"{O}/fleet_code_hashes.json"))["C"]
for p in glob.glob(f"{O}/units_linear/linear_private_bdf_*.json"):
    if json.load(open(p)).get("code_hash") != C:
        dst = f"{O}/units_linear_eval_AB/{os.path.basename(p)}"
        if not os.path.exists(dst):
            shutil.copy(p, dst)
        os.remove(p)
PYEOF
grep "^private_bdf" $O/linear_units.txt | xargs -P 4 -L 1 $PY -m auditory_alignment.linear_reference 2>&1 | grep -v Warning | grep -c complete
exit 0  # counts above are informational; grep -c returns 1 when the count is 0
