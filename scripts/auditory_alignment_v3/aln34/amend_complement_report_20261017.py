"""Report-only v2.1 correction after the completed GPU continuation; no refitting."""
import json
import os
from pathlib import Path
import shutil
from datetime import datetime
from auditory_alignment_v3.aln34 import learning_budget as B
assert os.environ.get('SLURM_JOB_ID')
base=Path('private/auditory_alignment_v3/aln34/complement_final_20261017')
p=Path('docs/auditory_alignment_v3/COMPLEMENT_FUNCTION_REPORT.md')
receipt=json.loads((base/'receipt.json').read_text())
assert B.sha(p)==receipt['report_sha256']
shutil.copy2(p,base/'generated_v2_report_before_status_correction.md')
value=p.read_text();changes={}
replacements={
 '234 units run on CPU and reproduced':'234 units reproduced (10 CPU outputs reused;224 GPU outputs)',
 'This says nothing about the FM-context configurations, which are pending the GPU run.':'All FM-context configurations are now included; this statement describes this configuration only.',
 'the other 0 configurations pending the GPU run':'all30 configurations have complete functional outputs',
 'GPU: none submitted.':'GPU continuation:224 evaluations completed by1043886/1043887; no training was repeated.',
 'Run the per-unit evaluator on the 0 pending units':'Completed: the per-unit evaluator has0 pending units',
 'then `--aggregate` on CPU. No retraining; old checkpoints are only read.':'the final CPU aggregation1044112 is complete. No retraining; old checkpoints were only read.',
}
for old,new in replacements.items():
    changes[old]=value.count(old);value=value.replace(old,new)
value=value.replace('— v2\n','— v2.1 report-status correction\n',1)
value+='\n## Report-status correction, 2026-10-17\n\nThe unchanged v2 report generator contained pre-launch CPU-only/pending-GPU sentences. This report-only amendment corrects those stale execution statements after all234 nonzero-epoch outputs passed the original reproduction checks. No numeric result, interval, selected configuration, source code hash or historical note was changed. The generated v2 document, hashes and exact replacement counts are retained in private/auditory_alignment_v3/aln34/complement_final_20261017/.\n'
p.write_text(value)
B.write(base/'report_status_correction.json',{'job':os.environ['SLURM_JOB_ID'],'date':datetime.now().astimezone().isoformat(),
    'before':receipt['report_sha256'],'after':B.sha(p),'changes':changes,'numeric_aggregate_unchanged':receipt['aggregate_sha256']})
print(changes)
