"""Read exact bilingual clue context, redacting identifiers in review previews."""
import json,os,re
from pathlib import Path
from phase1_prepare import readcsv,table
from phase3_ci_linkage import name_key,pinyin_token
BASE=Path(__file__).resolve().parents[1]
assert os.getenv('SLURM_JOB_ID');os.umask(0o077)
out=BASE/'private/phase3_group_context_001';out.mkdir(mode=0o700,exist_ok=False)
clin=readcsv(BASE/'private/phase3_ci_clinical_004/candidate_rows_index.csv');terms=['耳蜗','助听','植入']
names=set()
for r in clin:
    py,hn,initial=pinyin_token(r['raw_name']);names.update(x for x in [py,hn] if x)
def redact(s):
    for n in sorted(names,key=len,reverse=True):s=s.replace(n,'[name]')
    return re.sub(r'\d+','[number]',s)
rr=[]
for r in clin:
    cells=json.loads(r['raw_cells_json'])
    seq=cells.items() if isinstance(cells,dict) else enumerate(cells)
    for col,val in seq:
        if any(t in str(val) for t in terms):rr.append(dict(participant_id=r['participant_id'],sheet=r['source_sheet_index'],row=r['source_worksheet_row'],column=col,redacted_context=redact(str(val))))
table(out/'clinical_context.csv',rr)
ss=[]
for r in readcsv(BASE/'private/phase3_ci_sources_001/source_paths_and_tokens.csv'):
    p=Path(r['path']);segments=[s for s in p.parts if 'normal' in s.lower()]
    if segments:ss.append(dict(container_id=r['container_id'],context=redact(' / '.join(segments)),in_basename='normal' in p.name.lower()))
table(out/'source_context.csv',ss)
print(json.dumps(dict(job_id=os.environ['SLURM_JOB_ID'],clinical_context_cells=len(rr),source_contexts=len(ss))))
