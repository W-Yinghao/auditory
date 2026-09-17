"""Check bilingual group/device clues without deriving a clinical diagnosis."""
import json,os,re
from collections import Counter
from pathlib import Path
from phase1_prepare import readcsv,table
BASE=Path(__file__).resolve().parents[1]
assert os.getenv('SLURM_JOB_ID');os.umask(0o077)
out=BASE/'results/phase3_group_clues_001';out.mkdir(exist_ok=False)
terms=['人工耳蜗','耳蜗','耳蝸','植入','正常','健听','健聽','对照','助听','助聽','normal','control','healthy','implant','hearing aid']
source=[];clinical=[]
for r in readcsv(BASE/'private/phase3_ci_sources_001/source_paths_and_tokens.csv'):
    s=(r['path']+' '+r['subject']).lower();hits=[t for t in terms if t in s]
    if hits:source.append(dict(container_id=r['container_id'],matched_terms='|'.join(hits)))
for r in readcsv(BASE/'private/phase3_ci_clinical_004/candidate_rows_index.csv'):
    # raw cell values preserve remarks which might have escaped field-name parsing.
    s=r['raw_cells_json'].lower();hits=[t for t in terms if t in s]
    if hits:clinical.append(dict(participant_id=r['participant_id'],sheet_index=r['source_sheet_index'],row_index=r['source_worksheet_row'],matched_terms='|'.join(hits)))
table(out/'source_clues.csv',source);table(out/'clinical_row_clues.csv',clinical)
summary=dict(job_id=os.environ['SLURM_JOB_ID'],source_records_with_additional_terms=len(source),clinical_rows_with_additional_terms=len(clinical),source_term_counts=dict(Counter(t for r in source for t in r['matched_terms'].split('|'))),clinical_term_counts=dict(Counter(t for r in clinical for t in r['matched_terms'].split('|'))),scope='Keyword coverage check only; a term can describe project context, an ear or configuration rather than a participant group')
(out/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2));print(json.dumps(summary,ensure_ascii=False))
