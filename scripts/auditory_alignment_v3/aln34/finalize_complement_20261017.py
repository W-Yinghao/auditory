"""Validate the full GPU continuation, then run the unchanged v2 analysis."""
import json
import os
from pathlib import Path
import shutil
from datetime import datetime
from auditory_alignment_v3.aln34 import complement_function as C
from auditory_alignment_v3.aln34 import learning_budget as B

assert os.environ.get('SLURM_JOB_ID')
root=Path(C.REPO)
ids=[x.split()[0] for x in Path(C.UNITS_TXT).read_text().splitlines() if x.strip() and not x.startswith('#')]
assert len(ids)==len(set(ids))==234
assert B.sha(root/'auditory_alignment_v3/aln34/complement_function.py')=='d98dce999c4b83d4b5c545f08d05162612decf3ceb50a97e816ed0e906c61229'
assert B.sha(root/'auditory_alignment_v3/aln34/complement_function_eval.py')=='be2107d36af9addfb2d8787abc9d259d92175181de797b72a020fea9027637a6'
checks={}
for eid in ids:
    path=Path(C.UNITS_DIR)/f'{eid}.json'
    v=json.loads(path.read_text())
    assert v['eid']==eid and v['comparable_to_record'] and not v['dev_only'],eid
    assert not v['limits']['tiny'] and v['limits']['max_test_participants'] is None and v['limits']['max_queries'] is None,eid
    checks[eid]={'sha256':B.sha(path),'device':v['device'],'device_name':v.get('device_name')}
dest=Path(B.BASE).parent/'complement_final_20261017'
dest.mkdir(exist_ok=True,mode=0o700)
for path in (Path(C.DOC),Path(C.RES)/'complement_function.json'):
    backup=dest/('before_'+path.name)
    if not backup.exists():shutil.copy2(path,backup)
print('234 full comparable outputs verified; run unchanged aggregation',flush=True)
result=C.aggregate()
summary=json.loads((Path(C.RES)/'complement_function.json').read_text())
assert summary['gpu_plan']['n_units_pending']==0
receipt={'job':os.environ['SLURM_JOB_ID'],'completed':datetime.now().astimezone().isoformat(),'outputs':checks,
         'aggregate_sha256':B.sha(Path(C.RES)/'complement_function.json'),'report_before_receipt_sha256':B.sha(C.DOC)}
text=Path(C.DOC).read_text()
banner=('\n> Execution update, 2026-10-17: all234 listed nonzero-epoch units now have full comparable v2 outputs; '
        '10 pre-existing CPU outputs were reused and224 were evaluated by GPU workers1043886/1043887. '
        'The16 epoch-zero units retain their exact-zero checkpoint evidence. Final CPU job'+os.environ['SLURM_JOB_ID']+
        ' verified coverage and reran the unchanged v2 analysis. Historical plan/estimate statements below describe the pre-launch snapshot, '
        'not missing work. The execution receipt is private/auditory_alignment_v3/aln34/complement_final_20261017/receipt.json.\n')
first,rest=text.split('\n',1);Path(C.DOC).write_text(first+'\n'+banner+'\n'+rest)
receipt['report_sha256']=B.sha(C.DOC);B.write(dest/'receipt.json',receipt)
print('final aggregation complete',result,flush=True)
