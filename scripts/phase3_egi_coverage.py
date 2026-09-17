"""Account for historical RAW exports relative to MFF source lineages."""
import json,os,re
from collections import Counter,defaultdict
from pathlib import Path
from phase1_prepare import readcsv,table
BASE=Path(__file__).resolve().parents[1]
def norm(stem):return re.sub(r'[^a-z0-9\u4e00-\u9fff]','',stem.lower())
def main():
    assert os.getenv('SLURM_JOB_ID');os.umask(0o077)
    out=BASE/'results/phase3_egi_coverage_001';out.mkdir(exist_ok=False)
    priv=BASE/'private/phase3_egi_coverage_001';priv.mkdir(mode=0o700,exist_ok=False)
    reg=json.loads((BASE/'private/mff_001/registry.json').read_text());raws=readcsv(BASE/'results/other_eeg_001/egi_raw_index.csv')
    paths={r['file_id']:Path(r['absolute_path']) for r in readcsv(BASE/'private/inventory_001/file_path_map.csv')}
    hist=json.loads((BASE/'private/mff_001/history.json').read_text())
    exact=defaultdict(set);historical=defaultdict(set)
    for r in reg:exact[norm(Path(r['path']).stem)].add(r['container_id'])
    for r in hist:
        for s in r.get('source_paths',[]):historical[norm(Path(str(s).replace('\\','/')).stem)].add(r['container_id'])
    lineage={r['container_id']:r['source_candidate_ids'] for r in readcsv(BASE/'results/phase3_ci_sources_001/all_mff_source_lineage.csv')}
    rows=[];private=[]
    for r in raws:
        key=norm(paths[r['file_id']].stem);matches=exact[key]|historical[key]
        sources=set(s for mid in matches for s in lineage.get(mid,'').split('|') if s)
        status='one_source_lineage_name_evidence' if len(sources)==1 else 'multiple_source_lineages_name_evidence' if sources else 'MFF_name_match_without_selected_source' if matches else 'unmatched_name'
        rows.append(dict(file_id=r['file_id'],data_level=r['data_level'],mff_name_matches=len(matches),source_candidate_ids='|'.join(sorted(sources)),coverage_status=status,numeric_equivalence='not_established'))
        private.append(dict(file_id=r['file_id'],path=str(paths[r['file_id']]),matched_mff_ids='|'.join(sorted(matches))))
    table(out/'raw_export_coverage.csv',rows);table(priv/'path_matches.csv',private)
    summary=dict(job_id=os.environ['SLURM_JOB_ID'],raw_files=len(rows),status_counts=dict(Counter(r['coverage_status'] for r in rows)),by_level_status=dict(Counter(r['data_level']+'/'+r['coverage_status'] for r in rows)),scope='Source-name/provenance association only; not proof of sample equivalence. Historical RAW exports are not additional independent observations.')
    (out/'summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary))
if __name__=='__main__':main()
