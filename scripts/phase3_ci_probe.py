"""Compact CI/MFF provenance and reader probe, without printing identities."""
import csv,json,os,re,hashlib,traceback
from collections import Counter,defaultdict
from pathlib import Path
import numpy as np
import mne
from audit_mff import xml,nodes,value,table
BASE=Path(__file__).resolve().parents[1]

def main():
    assert os.environ.get('SLURM_JOB_ID');os.umask(0o077)
    out=BASE/'results/phase3_ci_probe_002';out.mkdir(exist_ok=False)
    private=BASE/'private/phase3_ci_probe_002';private.mkdir(mode=0o700,exist_ok=False)
    reg=json.loads((BASE/'private/mff_001/registry.json').read_text())
    history={r['container_id']:r for r in json.loads((BASE/'private/mff_001/history.json').read_text())}
    index={r['container_id']:r for r in csv.DictReader((BASE/'manifests/mff_export_index.csv').open())}
    rows=[];fields=defaultdict(Counter);subjects=Counter();times=Counter();layouts=Counter();examples=[];errors=[]
    for r in reg:
        mid=r['container_id'];p=Path(r['path']);ix=index[mid];sf=r.get('subject_fields',{})
        for k,v in sf.items():fields[k]['nonempty' if v else 'empty']+=1
        subject=sf.get('Patient ID','');subjects[subject]+=1;times[(subject,r.get('record_time',''))]+=1
        label=re.sub(r'[\u4e00-\u9fff]+','<Han>',str(p.relative_to('/projects/EEG-foundation-model/auditory')))
        label=re.sub(r'\d{4}[-_.]\d{1,2}[-_.]\d{1,2}.*','<date...>',label)
        pathparts=p.parts;layout='/'.join(re.sub(r'[\u4e00-\u9fff]+','<Han>',x) for x in pathparts[4:-1])
        layouts[layout]+=1
        methods=history[mid]['methods'];settings=history[mid]['settings']
        rows.append(dict(container_id=mid,subject_token='P'+hashlib.sha256(subject.encode()).hexdigest()[:12],
            has_subject=bool(subject),data_level=ix['data_level'],n_samples=ix.get('n_samples',''),
            sfreq=ix.get('sampling_rate_hz',''),channels=ix.get('n_signal_channels',''),
            source_methods=json.dumps(methods),topology=ix.get('topology_status',''),
            n_history_sources=len(history[mid]['source_paths']),n_storage_epochs=ix.get('n_storage_epochs',''),
            candidate_time_group='T'+hashlib.sha256((subject+'|'+r.get('record_time','')).encode()).hexdigest()[:12]))
        if ix['data_level']=='continuous_or_discontinuous' and ix.get('topology_status')=='structure_passed':
            key=(tuple(methods),int(ix.get('n_signal_channels',0)),int(ix.get('n_storage_epochs',0))>1)
            if key not in {e['key'] for e in examples}:
                examples.append(dict(key=key,container_id=mid,path=str(p)))
    table(out/'export_candidates.csv',rows)
    safeexamples=[]
    for e in examples[:12]:
        p=Path(e['path']);item={'container_id':e['container_id'],'methods':list(e['key'][0])}
        try:
            raw=mne.io.read_raw_egi(p,preload=False,verbose='ERROR')
            picks=mne.pick_types(raw.info,eeg=True,exclude=[])
            xx=raw.get_data(picks=picks,start=0,stop=min(raw.n_times,int(raw.info['sfreq']*2)))
            units=Counter(str(c['unit']) for c in raw.info['chs'] if c['kind']==2)
            item.update(reader='MNE1.11',sfreq=raw.info['sfreq'],n_times=int(raw.n_times),eeg_channels=len(picks),
                eeg_channel_names_preview=[raw.ch_names[i] for i in list(picks[:4])+list(picks[-4:])],channel_units=dict(units),
                first2s_median_channel_ptp_uv=float(np.median(np.ptp(xx,axis=1))*1e6),
                n_annotations=len(raw.annotations),extras_keys=sorted(raw._raw_extras[0]),
                calibration_range=[float(min(raw._cals)),float(max(raw._cals))])
            info=xml(p/'info1.xml');sensors=xml(p/'sensorLayout.xml')
            item['info1_element_names']=sorted({x.tag.rsplit('}',1)[-1] for x in info.iter()}) if info is not None else []
            item['sensor_type_counts']=dict(Counter(value(x,'type') for x in nodes(sensors,'sensor'))) if sensors is not None else {}
            raw.close()
        except Exception as exc:
            errors.append(dict(container_id=e['container_id'],error=repr(exc),trace=traceback.format_exc()));item['error_class']=type(exc).__name__
        safeexamples.append(item)
    # Keep paths, original IDs, dates and settings in private only.
    (private/'layouts.json').write_text(json.dumps(dict(layouts),ensure_ascii=False,indent=2))
    (private/'records.json').write_text(json.dumps([dict(**r,history=history[r['container_id']]) for r in reg],ensure_ascii=False,indent=2))
    (private/'errors.json').write_text(json.dumps(errors,indent=2))
    labelmap=json.loads((BASE/'private/mff_001/label_map.json').read_text())
    event_dictionary={k:v for k,v in labelmap.items() if re.fullmatch(r'[A-Za-z+\-0-9]{1,8}',v)}
    summary=dict(job_id=os.environ['SLURM_JOB_ID'],containers=len(rows),subject_field_counts={k:dict(v) for k,v in fields.items()},
        unique_nonempty_patient_id_strings=len([s for s in subjects if s]),empty_patient_id_exports=subjects.get('',0),
        unique_subject_recordtime_pairs=len(times),level_counts=dict(Counter(r['data_level'] for r in rows)),
        continuous_method_counts=dict(Counter(r['source_methods'] for r in rows if r['data_level']=='continuous_or_discontinuous')),
        reader_examples=safeexamples,event_dictionary_letter_numeric_only=event_dictionary,reader_errors=len(errors))
    (out/'summary.json').write_text(json.dumps(summary,indent=2,default=lambda x:x.item() if isinstance(x,np.generic) else str(x)));print(json.dumps(summary,indent=2,default=str),flush=True)
if __name__=='__main__':main()
