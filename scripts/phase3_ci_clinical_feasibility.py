"""Quantify CI/MFF clinical index support without fitting new outcome models."""
import hashlib,json,os
from collections import defaultdict
from pathlib import Path
from phase1_prepare import readcsv,table
from phase3_ci_linkage import parse_date,numeric
BASE=Path(__file__).resolve().parents[1]
def main():
    assert os.getenv('SLURM_JOB_ID');os.umask(0o077)
    out=BASE/'results/phase3_ci_clinical_feasibility_001';out.mkdir(exist_ok=False)
    rows=readcsv(BASE/'private/phase3_ci_clinical_004/candidate_rows_index.csv');clinical={}
    for r in rows:
        pid=r['participant_id'];key='R'+hashlib.sha256((pid+'|'+r['source_sheet_index']+'|'+r['source_worksheet_row']).encode()).hexdigest()[:12];clinical[key]=r
    links=defaultdict(list)
    for r in readcsv(BASE/'results/phase3_ci_linkage_005/clinical_source_links.csv'):
        if r['link_status']=='exact_name_date' and r['source_candidate_ambiguity']=='unique_participant':links[r['container_id']].append(clinical[r['clinical_row_ref']])
    labels=readcsv(BASE/'results/phase3_ci_linkage_005/canonical_source_labels.csv')
    dates={r['container_id']:r['record_time'] for r in readcsv(BASE/'private/phase3_ci_sources_001/source_paths_and_tokens.csv')}
    f=readcsv(BASE/'results/phase3_ci_measurements_001/features.csv');measured={r['container_id'] for r in f if r['variant']=='primary' and r['event_code']=='stad' and r['status']=='measured'}
    output=[];summaries=[]
    for scope in ['all_MFF_candidate_links','literal_CI_or_CIHA_sources']:
        indices={}
        for r in sorted(labels,key=lambda r:(dates[r['container_id']],r['container_id'])):
            if not r['unique_same_day_pid'] or r['source_candidate_ambiguity']!='unique_participant':continue
            if scope=='literal_CI_or_CIHA_sources' and r['source_cohort_evidence'] not in ['CI','CIHA_label']:continue
            indices.setdefault(r['unique_same_day_pid'],r)
        selected=[]
        for pid,r in indices.items():
            rr=links[r['container_id']];dob={parse_date(x['raw_dob']) for x in rr if parse_date(x['raw_dob'])}
            day=parse_date(dates[r['container_id']]);age_ok=len(dob)==1 and 0<(day-next(iter(dob))).days/365.25<19
            vals={k:{numeric(x['raw_'+k]) for x in rr if numeric(x['raw_'+k]) is not None} for k in ['muss','cap','sir','itmais']}
            row=dict(scope=scope,participant_id=pid,container_id=r['container_id'],stad_measurable=r['container_id'] in measured,age_parseable_and_unique=age_ok,source_label=r['source_cohort_evidence'])
            for k,v in vals.items():row[k+'_unique_value']=len(v)==1;row[k+'_value_conflict']=len(v)>1
            row['MUSS_age_EEG_complete']=row['stad_measurable'] and age_ok and row['muss_unique_value'];selected.append(row);output.append(row)
        summaries.append(dict(scope=scope,earliest_candidate_indices=len(selected),stad_measurable=sum(r['stad_measurable'] for r in selected),unique_age_and_MUSS_and_EEG=sum(r['MUSS_age_EEG_complete'] for r in selected),unique_CAP_and_EEG=sum(r['stad_measurable'] and r['cap_unique_value'] for r in selected),unique_SIR_and_EEG=sum(r['stad_measurable'] and r['sir_unique_value'] for r in selected),MUSS_conflict_indices=sum(r['muss_value_conflict'] for r in selected)))
    table(out/'eligibility.csv',output);summary=dict(job_id=os.environ['SLURM_JOB_ID'],scopes=summaries,interpretation='Original raw scores only; no new CI outcome model or instrument conversion; exact-name/date identity remains candidate evidence')
    (out/'summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary))
if __name__=='__main__':main()
