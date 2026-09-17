"""Validate the completed Phase 1 deliverables and save a delivery snapshot."""
import json
import os
import re
from pathlib import Path
from pdfminer.pdfpage import PDFPage
from phase1_prepare import readcsv,table
from phase1_epochs import digest

BASE=Path(__file__).resolve().parents[1]
assert os.environ.get('SLURM_JOB_ID')
os.umask(0o077)
out=BASE/'results/phase1_delivery_001';out.mkdir(exist_ok=False)
measurement=json.loads((BASE/'results/phase1_measurements_001/summary.json').read_text())
final=json.loads((BASE/'results/phase1_final_001/summary.json').read_text())
similarity=json.loads((BASE/'results/phase1_similarity_002/summary.json').read_text())
assert final['status']=='passed' and final['complete_source_records']==93
assert measurement['records_verified']==84 and measurement['primary_accepted_epochs']==57879
assert measurement['sufficient_by_cohort']=={'HA':71,'NH':9}
assert measurement['clinical_outcomes_used'] is False
assert similarity['targeted_pairs']==11 and similarity['figure_selected_pair_included'] is True
assert not list((BASE/'results/phase1_epochs_001').glob('B*/error*'))
for p in (BASE/'results/phase1_epochs_001').glob('B*/summary.json'):
    value=json.loads(p.read_text())
    assert 'source_signal_mtime_ns' not in value
for r in readcsv(BASE/'results/phase1_final_001/artifact_checksums.csv'):
    assert digest(BASE/r['artifact'])==r['sha256'],r['artifact']
pdf=BASE/'figures/phase1_measurements_001/record_waveforms.pdf'
with pdf.open('rb') as f:pages=sum(1 for _ in PDFPage.get_pages(f))
assert pages==84
documents=[BASE/'README.md',BASE/'docs/phase1_report.md',BASE/'docs/PHASE1_ARTIFACTS.md',
           BASE/'docs/PHASE1_MEASUREMENT_PROTOCOL.md']
links=0
for p in documents:
    for target in re.findall(r'\]\(([^)]+)\)',p.read_text()):
        if target.startswith(('https://','http://','#')):continue
        assert (p.parent/target).resolve().exists(),(p.name,target)
        links+=1
summary=dict(job_id=os.environ['SLURM_JOB_ID'],status='passed',source_records=93,
             reconstructed_recordings=84,accepted_epochs=57879,sufficient_records=80,
             waveform_pdf_pages=pages,local_document_links_checked=links,
             source_mtime_removed_from_nonprivate_production_summaries=True,
             phase1_final_checksums_verified=True,figure_selected_similarity_pair_verified=True,
             clinical_outcomes_used=False,raw_data_modified=False)
(out/'verification.json').write_text(json.dumps(summary,indent=2))
paths=documents+[BASE/'AGENTS.md',BASE/'configs/phase1_v1.json',pdf]
paths+=list((BASE/'scripts').glob('phase1_*.py'))
for folder in ('phase1_sources_001','phase1_measurements_001','phase1_final_001','phase1_diagnostics_001','phase1_similarity_002'):
    paths+=list((BASE/'results'/folder).glob('*.csv'))
    paths+=list((BASE/'results'/folder).glob('*.json'))
paths+=list((BASE/'figures/phase1_measurements_001').glob('*.png'))
paths+=list((BASE/'figures/phase1_diagnostics_001').glob('*.png'))
table(out/'artifact_checksums.csv',[dict(artifact=str(p.relative_to(BASE)),sha256=digest(p)) for p in sorted(set(paths))])
print(json.dumps(summary,indent=2),flush=True)
