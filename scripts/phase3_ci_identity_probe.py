"""Probe patient-token normalization and uninterrupted raw MFF candidates."""
import csv,json,os,re,importlib.util
from collections import Counter
from pathlib import Path
from audit_mff import table
BASE=Path(__file__).resolve().parents[1]
def main():
    assert os.environ.get('SLURM_JOB_ID');os.umask(0o077)
    out=BASE/'results/phase3_ci_identity_probe_001';out.mkdir(exist_ok=False)
    private=BASE/'private/phase3_ci_identity_probe_001';private.mkdir(mode=0o700,exist_ok=False)
    reg=json.loads((BASE/'private/mff_001/registry.json').read_text());index={r['container_id']:r for r in csv.DictReader((BASE/'manifests/mff_export_index.csv').open())}
    components={r['container_id']:r['candidate_processing_component'] for r in csv.DictReader((BASE/'results/mff_recovery_001/processing_components.csv').open())}
    hist={r['container_id']:r for r in json.loads((BASE/'private/mff_001/history.json').read_text())}
    rows=[];eligible=[];pat=Counter();profiles=Counter();rules=Counter()
    for r in reg:
        mid=r['container_id'];ix=index[mid];p=Path(r['path']);subject=r.get('subject_fields',{}).get('Patient ID','')
        if ix['data_level']!='continuous_or_discontinuous' or hist[mid]['methods']:continue
        codes=json.loads(ix['event_code_counts'] or '{}');targets=sum(v for k,v in codes.items() if k in ['stad','La4a6587385f6','L420168119949','Lb906c82d887d','L519a151598f7'])
        row=dict(container_id=mid,subject=subject,basename=p.name,path=str(p),record_time=r.get('record_time',''),component=components[mid],
            n_samples=ix.get('n_samples',''),n_channels=ix.get('n_signal_channels',''),sfreq=ix.get('sampling_rate_hz',''),
            n_storage_epochs=ix.get('n_storage_epochs',''),topology=ix.get('topology_status',''),target_event_count=targets,
            codes=json.dumps(codes),history_settings=json.dumps(hist[mid]['settings']))
        rows.append(row)
        if targets>=80 and ix.get('topology_status')=='structure_passed':
            eligible.append(row)
            # Shape examples remove all alphabetic/Han identity content.
            pattern=re.sub(r'[A-Za-z]+','A',re.sub(r'[\u4e00-\u9fff]+','H',subject));pattern=re.sub(r'\d+','N',pattern);pat[pattern]+=1
            profiles[(row['n_channels'],row['sfreq'],row['n_storage_epochs'])]+=1
            for token in ['puretone','pure','bapa','ba1ba4','bada','ciha','naked','quiet','noise','front','left','right']:
                if token in (subject+' '+str(p)).lower():rules[token]+=1
    table(private/'unfiltered_continuous.csv',rows)
    table(out/'record_candidates.csv',[{k:r[k] for k in ['container_id','component','n_samples','n_channels','sfreq','n_storage_epochs','topology','target_event_count','codes']} for r in eligible])
    shapes=[dict(subject_pattern=k,count=v) for k,v in pat.items()]
    summary=dict(job_id=os.environ['SLURM_JOB_ID'],unfiltered_continuous=len(rows),target80_topology_eligible=len(eligible),
        candidate_components=len({r['component'] for r in eligible}),candidate_exact_record_times=len({r['record_time'] for r in eligible}),
        nonempty_subject_count=sum(bool(r['subject']) for r in eligible),patient_token_shapes=shapes,
        shape_counts={str(k):v for k,v in profiles.items()},protocol_path_clues=dict(rules),
        python_modules={x:importlib.util.find_spec(x) is not None for x in ['pypinyin','text_unidecode','sklearn','mffpy']})
    (out/'summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2),flush=True)
if __name__=='__main__':main()
