"""Final reproducibility, reported counts, links and artifact verification."""
import json
import os
import re
import shutil
from pathlib import Path
import pandas as pd
from PIL import Image
from pdfminer.pdfpage import PDFPage
from phase1_epochs import digest
from phase1_prepare import table

BASE=Path(__file__).resolve().parents[1]


def main():
    assert os.environ.get('SLURM_JOB_ID')
    os.umask(0o077)
    out=BASE/'results/phase2_delivery_001';out.mkdir(exist_ok=False)
    cfgpath=BASE/'configs/phase2_v1.json';cfg=json.loads(cfgpath.read_text())
    assert digest(cfgpath)=='b2c30fb1f95fe20d18b0907415c540b6c3628f353993b6bfaa248938af2637e4'
    assert digest(BASE/'configs/phase1_v1.json')==cfg['phase1_config_sha256']
    final=json.loads((BASE/'results/phase2_final_001/summary.json').read_text());assert final['status']=='passed'
    assert final['epochs_reconciled']==80441 and final['primary_accepted_reconciled']==57879
    assert final['archival_candidates']==53
    hh=pd.read_csv(BASE/'results/phase2_measurements_001/half_scores.csv')
    nh=hh[(hh.selected_index)&(hh.cohort_label=='NH')&(hh.variant=='hp01_avg20')&(hh.sampling=='all_accepted')&(hh.condition=='code1')&(hh.half_status=='measured')]
    assert nh.groupby('split').size().to_dict()=={'alternating_30s_blocks':9,'early_late':9}
    for folder in ['private','private/phase2_cohort_001','private/phase2_archival_001']:
        assert (BASE/folder).stat().st_mode&0o077==0
    paths=[];checked=0
    for name in ['measurements','archival','diagnostics']:
        for r in pd.read_csv(BASE/'results'/('phase2_'+name+'_001')/'artifact_checksums.csv').itertuples():
            assert digest(BASE/r.file)==r.sha256
            checked+=1
    docs=[BASE/'README.md',BASE/'AGENTS.md']+[BASE/'docs'/name for name in ['phase2_report.md','PHASE2_ARTIFACTS.md','PHASE2_PROTOCOL.md','PROJECT_PLAN.md','ANALYSIS_PROTOCOL_DRAFT.md']]
    links=[]
    for doc in docs:
        content=doc.read_text()
        for target in re.findall(r'\]\(([^)]+)\)',content):
            if '://' in target or target.startswith('#'):continue
            path=(doc.parent/target.split('#')[0]).resolve()
            assert path.exists(),f'broken local link: {doc.name}: {target}'
            links.append(dict(document=str(doc.relative_to(BASE)),target=target,exists=True))
    table(out/'document_links.csv',links)
    figs=[BASE/'figures/phase2_measurements_001/half_amplitude_agreement.png',
          BASE/'figures/phase2_measurements_001/common_support_sensitivity.png',
          BASE/'figures/phase2_diagnostics_001/archival_feasibility.png']
    imageinfo=[]
    for fig in figs:
        with Image.open(fig) as im:
            imageinfo.append(dict(file=str(fig.relative_to(BASE)),width=im.width,height=im.height));im.verify()
    pdf=BASE/'figures/phase2_diagnostics_001/archival_feasibility.pdf'
    with pdf.open('rb') as handle:
        assert sum(1 for _ in PDFPage.get_pages(handle))==1
    # Fail if source names have accidentally been copied into new public text artifacts.
    vendors=json.loads((BASE/'private/linkage_001/vendor_identity_records.json').read_text())
    names={str(r.get('PatientName','')).strip() for r in vendors}-{''}
    textpaths=list(docs)
    for folder in sorted((BASE/'results').glob('phase2_*_001')):
        textpaths.extend(p for p in folder.rglob('*') if p.suffix in {'.csv','.json','.md'})
    leaked=0
    for p in textpaths:
        content=p.read_text()
        leaked+=any(name in content for name in names)
    assert leaked==0,'identifying source name present in new public text artifact'
    snapshot=out/'code_snapshot';snapshot.mkdir()
    for p in [cfgpath,*sorted((BASE/'scripts').glob('phase2_*.py')),*sorted((BASE/'slurm').glob('*phase2*.sbatch')),BASE/'tests/test_phase2.py']:
        shutil.copy2(p,snapshot/p.name)
    summary=dict(job_id=os.environ['SLURM_JOB_ID'],status='passed',phase2_config_sha256=digest(cfgpath),
        source_records=93,candidate_indices=78,primary_measurable_HA_indices=57,NH_indices=9,
        archival_candidates=53,epochs_reconciled=80441,original_primary_retained_epochs=57879,
        upstream_artifact_hashes_verified=checked,local_links_checked=len(links),image_files=imageinfo,pdf_pages=1,
        private_directory_access_checked=True,source_name_scan_passed=True,
        tests='19 passed in Slurm job 995464',independent_reconciliation_job=final['job_id'],
        scope='HA/BDF Phase2 complete; CI signal study and paper-level clinical validation unfinished')
    (out/'verification.json').write_text(json.dumps(summary,indent=2))
    hashes=[]
    for root in [out,BASE/'results/phase2_cohort_001',BASE/'results/phase2_final_001']:
        hashes.extend(dict(file=str(p.relative_to(BASE)),sha256=digest(p)) for p in sorted(root.rglob('*')) if p.is_file())
    hashes.extend(dict(file=str(p.relative_to(BASE)),sha256=digest(p)) for p in docs)
    table(out/'artifact_checksums.csv',hashes)
    print(json.dumps(summary,indent=2),flush=True)


if __name__=='__main__':main()
