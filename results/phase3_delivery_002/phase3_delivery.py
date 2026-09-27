"""Final integrity, prediction-metric and deliverable checks under Slurm."""
import csv,hashlib,json,os,re,shutil
from collections import Counter
from datetime import datetime
from pathlib import Path
import numpy as np
import pandas as pd
from phase1_prepare import readcsv,table
BASE=Path(__file__).resolve().parents[1]
def main():
    assert os.getenv('SLURM_JOB_ID');os.umask(0o077)
    out=BASE/'results/phase3_delivery_002';out.mkdir(exist_ok=False)
    completion=[json.loads((BASE/f'results/phase3_ci_epochs_001/completion_{i:02d}.json').read_text()) for i in range(8)]
    assert sum(c['completed'] for c in completion)==203 and all(c['completed']==c['attempted'] and c['errors']==0 for c in completion)
    ci=json.loads((BASE/'results/phase3_ci_measurements_001/summary.json').read_text());assert ci['records']==203
    labels={r['container_id']:r for r in readcsv(BASE/'results/phase3_ci_linkage_005/canonical_source_labels.csv')};assert len(labels)==203
    metadata=readcsv(BASE/'results/phase3_metadata_addendum_001/source_metadata.csv')
    assert {r['container_id'] for r in metadata}==set(labels) and len(metadata)==203
    assert sum(bool(r['metadata_caution_flags']) for r in metadata)==1
    assert all(r['device_power_state']=='not_established' for r in metadata)
    dates={r['container_id']:datetime.fromisoformat(r['record_time'].replace('Z','+00:00')).date() for r in readcsv(BASE/'private/phase3_ci_sources_001/source_paths_and_tokens.csv')}
    pairs=readcsv(BASE/'results/phase3_synthesis_001/pair_availability.csv')
    for r in pairs:
        a,b=r['container_a'],r['container_b'];assert dates[a]==dates[b]
        assert labels[a]['unique_same_day_pid']==labels[b]['unique_same_day_pid']==r['participant_id']
        assert labels[a]['source_candidate_ambiguity']==labels[b]['source_candidate_ambiguity']=='unique_participant'
    ha=json.loads((BASE/'results/phase3_ha_science_001/summary.json').read_text())
    pred=pd.read_csv(BASE/'private/phase3_ha_science_001/predictions.csv')
    assert not pred.duplicated(['participant_id','recording_id','target','model','repeat']).any()
    assert pred.participant_id.nunique()==50 and np.isfinite(pred[['y','pred']].to_numpy()).all()
    for r in ha['targets_models']:
        p=pred[(pred.target==r['target'])&(pred.model==r['model'])];assert len(p)==250
        assert abs(np.mean(abs(p.y-p.pred))-r['MAE'])<1e-10
        assert all(g.fold.nunique()==1 for _,g in p.groupby(['participant_id','repeat']))
    # Historical RAW coverage combines name evidence and sparse numeric evidence;
    # none of these statuses turns an export into an independent child.
    num={r['file_id']:r for r in readcsv(BASE/'results/phase3_raw_numeric_links_003/raw_mff_numeric_links.csv')}
    combined=[]
    for r in readcsv(BASE/'results/phase3_egi_coverage_001/raw_export_coverage.csv'):
        n=num.get(r['file_id'],{});sources=set(filter(None,r['source_candidate_ids'].split('|')))|set(filter(None,n.get('source_candidate_ids','').split('|')))
        combined.append(dict(file_id=r['file_id'],data_level=r['data_level'],name_status=r['coverage_status'],numeric_status=n.get('numeric_status','segmented_not_tested'),source_candidate_ids='|'.join(sorted(sources)),evidence_status='source_association_candidate_not_full_equivalence' if sources else 'unresolved_source_association'))
    table(out/'combined_raw_coverage.csv',combined)
    documents=[BASE/'README.md']+[BASE/'docs'/p for p in ['phase3_report.md','PHASE3_ARTIFACTS.md','PHASE3_SCIENTIFIC_PROTOCOL.md','ORIGINAL_IDEA_EVIDENCE_MAP.md','PHASE3_HA_SENSITIVITY_PROTOCOL.md','PHASE3_CI_SUMMARY_RULES.md']]
    checked=[]
    for doc in documents:
        for target in re.findall(r'\]\(([^)]+)\)',doc.read_text()):
            if target.startswith(('http:','https:','#')):continue
            path=(doc.parent/target.split('#')[0]).resolve();assert path.exists(),(doc.name,target);checked.append(str(path.relative_to(BASE)))
    artifacts=documents+[p for folder in ['figures/phase3','figures/phase3_final'] for p in (BASE/folder).iterdir() if p.suffix in ['.png','.pdf']]
    for run in ['phase3_ci_clinical_004','phase3_ha_covariates_004','phase3_ci_sources_001','phase3_ci_verification_001','phase3_ci_stream_check_001','phase3_ci_linkage_005','phase3_ci_measurements_001','phase3_ci_clinical_feasibility_001','phase3_metadata_addendum_001','phase3_group_clues_001','phase3_ha_science_001','phase3_ha_sensitivity_001','phase3_trial_budget_001','phase3_raw_numeric_links_003','phase3_synthesis_001']:
        artifacts.append(BASE/'results'/run/'summary.json')
    hashes={str(p.relative_to(BASE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in artifacts}
    assert all(p.stat().st_size>0 for p in artifacts)
    (out/'artifact_sha256.json').write_text(json.dumps(hashes,indent=2));shutil.copy2(Path(__file__),out/Path(__file__).name)
    summary=dict(job_id=os.environ['SLURM_JOB_ID'],status='passed',completed_ci_sources=203,completion_jobs=[r['job_id'] for r in completion],ha_model_metric_checks=len(ha['targets_models']),same_day_pair_checks=len(pairs),raw_coverage_counts=dict(Counter(r['evidence_status'] for r in combined)),unmatched_numeric_raw_with_name_source=sum(r['numeric_status']=='no_sparse_numeric_match' and bool(r['source_candidate_ids']) for r in combined),documents_checked=len(documents),local_links_checked=len(checked),artifact_hashes=len(hashes))
    (out/'verification.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
