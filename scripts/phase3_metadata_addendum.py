"""Adjudicate bilingual free-text clues discovered in the final metadata check.

No EEG is deleted or reprocessed and no predictive outcome model is refit.
"""
import hashlib,json,os,re,shutil
from collections import Counter,defaultdict
from pathlib import Path
from phase1_prepare import readcsv,table
from phase3_ci_linkage import parse_date,numeric
BASE=Path(__file__).resolve().parents[1]
def load_rules():
    """Load adjudicated clinical row rules retained with restricted study inputs."""
    path = BASE / 'private/phase3_metadata_addendum_rules.json'
    if not path.is_file():
        raise FileNotFoundError('Restricted adjudication rule map is required; it is not part of the GitHub snapshot.')
    entries = json.loads(path.read_text(encoding='utf-8'))
    return {(str(r['source_sheet_index']), str(r['source_worksheet_row'])): r['rule'] for r in entries}
def rowref(r):return 'R'+hashlib.sha256((r['participant_id']+'|'+r['source_sheet_index']+'|'+r['source_worksheet_row']).encode()).hexdigest()[:12]
def main():
    RULES=load_rules()
    assert os.getenv('SLURM_JOB_ID');os.umask(0o077)
    out=BASE/'results/phase3_metadata_addendum_001';out.mkdir(exist_ok=False)
    priv=BASE/'private/phase3_metadata_addendum_001';priv.mkdir(mode=0o700,exist_ok=False)
    clinical={rowref(r):r for r in readcsv(BASE/'private/phase3_ci_clinical_004/candidate_rows_index.csv')}
    notes={};note_rows=[];private=[]
    for ref,r in clinical.items():
        rule=RULES.get((r['source_sheet_index'],r['source_worksheet_row']))
        if not rule:continue
        assert rule['required'] in r['raw_cells_json']
        notes[ref]=rule
        note_rows.append(dict(clinical_row_ref=ref,participant_id=r['participant_id'],**{k:v for k,v in rule.items() if k!='required'},device_power_state='not_established'))
        private.append(dict(clinical_row_ref=ref,source_sheet=r['source_sheet_title'],source_row=r['source_worksheet_row'],raw_cells_json=r['raw_cells_json'],clinical_date=r['raw_clinical_date'],vendor_overlap_recording_ids=r['vendor_overlap_recording_ids']))
    assert len(notes)==len(RULES);table(out/'clinical_note_annotations.csv',note_rows);table(priv/'note_provenance.csv',private)
    labels=readcsv(BASE/'results/phase3_ci_linkage_005/canonical_source_labels.csv')
    source={r['container_id']:r for r in readcsv(BASE/'private/phase3_ci_sources_001/source_paths_and_tokens.csv')}
    links=defaultdict(list)
    for r in readcsv(BASE/'results/phase3_ci_linkage_005/clinical_source_links.csv'):
        if r['link_status']=='exact_name_date' and r['source_candidate_ambiguity']=='unique_participant':links[r['container_id']].append(r['clinical_row_ref'])
    enriched=[]
    for r in labels:
        mid=r['container_id'];ss=source[mid];normal='normal' in re.findall('[a-z]+',(ss['path']+' '+ss['subject']).lower())
        nn=[notes[ref] for ref in links[mid] if ref in notes]
        strict=r['source_cohort_evidence'];expanded='normal_literal' if normal and strict=='unknown' else strict
        enriched.append(dict(**r,source_label_expanded=expanded,clinical_CI_history_same_day=any(n['clinical_group_context']=='CI_HA_history' for n in nn),
            wearing_evidence='|'.join(sorted({n['wearing_evidence'] for n in nn if n['wearing_evidence']!='unknown'})) or 'unknown',
            metadata_caution_flags='|'.join(sorted({n['flag'] for n in nn if n['flag']})),
            note_row_refs='|'.join(sorted(ref for ref in links[mid] if ref in notes)),device_power_state='not_established'))
    table(out/'source_metadata.csv',enriched)
    measured={r['container_id'] for r in readcsv(BASE/'results/phase3_ci_measurements_001/features.csv') if r['variant']=='primary' and r['event_code']=='stad' and r['status']=='measured'}
    selected={}
    for r in sorted(enriched,key=lambda r:(source[r['container_id']]['record_time'],r['container_id'])):
        if not r['unique_same_day_pid'] or r['source_candidate_ambiguity']!='unique_participant':continue
        if r['source_cohort_evidence'] in ['CI','CIHA_label'] or r['clinical_CI_history_same_day']:selected.setdefault(r['unique_same_day_pid'],r)
    eligibility=[]
    for pid,r in selected.items():
        mid=r['container_id'];rr=[clinical[ref] for ref in links[mid]];dob={parse_date(x['raw_dob']) for x in rr if parse_date(x['raw_dob'])};day=parse_date(source[mid]['record_time'])
        age=len(dob)==1 and 0<(day-next(iter(dob))).days/365.25<19
        muss={numeric(x['raw_muss']) for x in rr if numeric(x['raw_muss']) is not None}
        eligibility.append(dict(participant_id=pid,container_id=mid,stad_measurable=mid in measured,age_unique=age,muss_unique=len(muss)==1,age_MUSS_stad_complete=mid in measured and age and len(muss)==1,cohort_scope='CI_or_CIHA_literal_source_or_explicit_same_day_clinical_CI_history'))
    table(out/'expanded_CI_clinical_eligibility.csv',eligibility)
    caveats=[r for r in enriched if r['metadata_caution_flags']];table(out/'source_metadata_cautions.csv',caveats)
    normal_ids={r['container_id'] for r in enriched if r['source_label_expanded']=='normal_literal'}
    source_note_ids={r['container_id'] for r in enriched if r['note_row_refs']}
    note_vendor={bid for r in private for bid in re.findall(r'B[0-9a-f]{12}',r['vendor_overlap_recording_ids'])}
    modelids={r['recording_id'] for r in readcsv(BASE/'private/phase3_ha_science_001/predictions.csv')}
    summary=dict(job_id=os.environ['SLURM_JOB_ID'],clinical_rows_adjudicated=len(notes),canonical_sources_with_same_day_notes=len(source_note_ids),
        expanded_source_label_counts=dict(Counter(r['source_label_expanded'] for r in enriched)),normal_literal_sources=len(normal_ids),
        wearing_evidence_counts=dict(Counter(r['wearing_evidence'] for r in enriched if r['wearing_evidence']!='unknown')),
        sources_with_metadata_cautions=len(caveats),source_caution_counts=dict(Counter(r['metadata_caution_flags'] for r in caveats)),
        expanded_CI_candidate_indices=len(eligibility),expanded_CI_age_MUSS_stad_complete=sum(r['age_MUSS_stad_complete'] for r in eligibility),
        note_vendor_name_overlap_HA_phase3_recordings=len(note_vendor&modelids),
        interpretation='Final-audit metadata refinement after v1 outcomes: preserve all v1 EEG/model results; normal is a literal source label, CI history differs from device power, and eight-minute origin is not anchored to an EEG sample. No automatic trimming or subject exclusion.')
    (out/'summary.json').write_text(json.dumps(summary,indent=2));shutil.copy2(Path(__file__),out/Path(__file__).name);print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
