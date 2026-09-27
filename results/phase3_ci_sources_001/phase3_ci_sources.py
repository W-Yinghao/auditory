"""Select continuous MFF sources without using signal responses or clinical scores."""
import csv,hashlib,json,os,re,traceback
from collections import Counter,defaultdict
from pathlib import Path
import numpy as np
import mne
from mne.io.egi.general import _get_signalfname
from audit_mff import table
from phase1_epochs import digest
BASE=Path(__file__).resolve().parents[1]

def protocol_clue(text):
    t=text.lower()
    if 'puretone' in t:return 'puretone'
    ma=re.search(r'ba[1-4]ba[1-4]',t)
    if ma:return ma[0]
    if 'bapa' in t:return 'bapa'
    return 'unknown'

def identity_clue(subject,path):
    # These are candidate tokens only; clinical linkage is a separate evidence step.
    candidates=[]
    for label in [subject,path.stem,path.parent.name]:
        name=re.sub(r'^\d+','',label.lower()).split('_')[0].split('-')[0]
        if re.fullmatch(r'[a-z]{2,30}',name) and name not in {'ci','ciha','nh','ha','puretone','bapa','naked','quiet','noise'}:candidates.append(name)
    return candidates[0] if candidates else str(path.parent)

def main():
    assert os.environ.get('SLURM_JOB_ID');os.umask(0o077)
    out=BASE/'results/phase3_ci_sources_001';out.mkdir(exist_ok=False)
    private=BASE/'private/phase3_ci_sources_001';private.mkdir(mode=0o700,exist_ok=False)
    cfg=BASE/'configs/phase3_science_v1.json';chash=digest(cfg)
    reg={r['container_id']:r for r in json.loads((BASE/'private/mff_001/registry.json').read_text())}
    rows=list(csv.DictReader((BASE/'results/phase3_ci_identity_probe_001/record_candidates.csv').open()))
    grouped=defaultdict(list);paths={};originals=[];errors=[]
    for r in rows:
        mid=r['container_id'];meta=reg[mid];p=Path(meta['path']);paths[mid]=p
        key=(meta.get('record_time'),r['n_samples'],r['n_channels'],r['sfreq'])
        grouped[key].append(mid)
    canonical={r['container_id']:r['container_id'] for r in rows};duplicates=[]
    for mids in grouped.values():
        if len(mids)<2:continue
        byhash=defaultdict(list)
        for mid in mids:
            try:
                signal=_get_signalfname(str(paths[mid]))['EEG']['signal']
                hh=digest(paths[mid]/signal);byhash[hh].append(mid)
            except Exception as exc:errors.append(dict(container_id=mid,stage='duplicate_hash',error=repr(exc)))
        for hh,ids in byhash.items():
            primary=min(ids)
            for mid in ids:canonical[mid]=primary
            if len(ids)>1:duplicates.append(dict(canonical_container_id=primary,duplicate_container_ids='|'.join(sorted(ids)),eeg_binary_sha256=hh))
    # Map physical frontocentral coordinates, not assumptions about electrode numbers.
    standard=mne.channels.make_standard_montage('standard_1020')
    transform=mne.channels.compute_native_head_t(standard,verbose='ERROR')
    target=np.array([mne.transforms.apply_trans(transform,standard.get_positions()['ch_pos'][c]) for c in ['Fz','Cz']])
    output=[]
    for r in rows:
        mid=r['container_id'];p=paths[mid];meta=reg[mid];subj=meta.get('subject_fields',{}).get('Patient ID','')
        clue=identity_clue(subj,p);pid='Q'+hashlib.sha256(clue.encode()).hexdigest()[:12]
        row=dict(container_id=mid,canonical_container_id=canonical[mid],candidate_token_id=pid,
            protocol_clue=protocol_clue(subj+' '+str(p)),protocol_evidence='literal_source_label_not_acoustic_validation',
            sfreq=float(r['sfreq']),n_channels=int(r['n_channels']),stored_samples=int(r['n_samples']),
            n_storage_intervals=int(r['n_storage_epochs']),target_events_in_audit=int(r['target_event_count']),
            config_sha256=chash,source_status='pending',device_state='unknown')
        output.append(row)
        originals.append(dict(container_id=mid,path=str(p),subject=subj,identity_clue=clue,record_time=meta.get('record_time',''),candidate_token_id=pid))
        if canonical[mid]!=mid:row['source_status']='exact_binary_duplicate';continue
        try:
            raw=mne.io.read_raw_egi(p,preload=False,verbose='ERROR')
            eeg=mne.pick_types(raw.info,eeg=True,exclude=[])
            names=[raw.ch_names[i] for i in eeg]
            xyz=np.array([raw.info['chs'][i]['loc'][:3] for i in eeg])
            distances=np.linalg.norm(target[:,None,:]-xyz[None,:,:],axis=2)
            roi=np.argmin(np.nan_to_num(distances,nan=np.inf),axis=1)
            mind=distances[np.arange(2),roi]
            extra=raw._raw_extras[0]
            assert len(eeg)==row['n_channels']
            codecounts=Counter(str(c) for c in raw.annotations.description)
            row.update(roi_channels=json.dumps([names[i] for i in roi]),roi_distance_m=json.dumps(mind.tolist()),
                eeg_calibration_min=float(min(raw._cals[eeg])),eeg_calibration_max=float(max(raw._cals[eeg])),
                reference_channels=json.dumps([n for n in names if n in ['VREF','Cz','E129','REF']]),
                reader_n_samples=int(raw.n_times),annotation_code_counts=json.dumps(dict(codecounts)),
                storage_intervals_samples=json.dumps([[int(a),int(b)] for a,b in zip(extra['first_samps'],extra['last_samps'])]),
                sensor_net=str(extra['device']),source_status='eligible' if np.all(np.isfinite(mind)) and max(mind)<=.04 and len(set(roi))==2 else 'hold_roi_geometry')
            assert int(np.sum(extra['last_samps']-extra['first_samps']))==row['stored_samples']
            raw.close()
        except Exception as exc:
            row['source_status']='hold_reader';errors.append(dict(container_id=mid,stage='MNE_source',error=repr(exc),trace=traceback.format_exc()))
    table(out/'source_manifest.csv',output);table(out/'binary_duplicates.csv',duplicates)
    table(private/'source_paths_and_tokens.csv',originals)
    (private/'errors.json').write_text(json.dumps(errors,indent=2))
    # Every MFF version is connected to a source candidate if historical edges support it.
    comps=list(csv.DictReader((BASE/'results/mff_recovery_001/processing_components.csv').open()))
    comp_sources=defaultdict(set)
    for r in rows:comp_sources[r['component']].add(canonical[r['container_id']])
    lineage=[dict(container_id=r['container_id'],source_candidate_ids='|'.join(sorted(comp_sources[r['candidate_processing_component']])),
        linkage_status='one_source_candidate' if len(comp_sources[r['candidate_processing_component']])==1 else 'no_source_candidate' if not comp_sources[r['candidate_processing_component']] else 'multiple_source_candidates') for r in comps]
    table(out/'all_mff_source_lineage.csv',lineage)
    for p in [Path(__file__),cfg]:(out/p.name).write_bytes(p.read_bytes())
    summary=dict(job_id=os.environ['SLURM_JOB_ID'],config_sha256=chash,unfiltered_event_sufficient_candidates=len(rows),
        exact_binary_duplicate_groups=len(duplicates),duplicate_copies=sum(r['source_status']=='exact_binary_duplicate' for r in output),
        status_counts=dict(Counter(r['source_status'] for r in output)),
        eligible_protocol_clues=dict(Counter(r['protocol_clue'] for r in output if r['source_status']=='eligible')),
        eligible_candidate_token_groups=len({r['candidate_token_id'] for r in output if r['source_status']=='eligible'}),
        roi_mappings=dict(Counter(r.get('roi_channels','') for r in output if r['source_status']=='eligible')),
        net_counts=dict(Counter(r.get('sensor_net','') for r in output if r['source_status']=='eligible')),
        all_mff_lineage_counts=dict(Counter(r['linkage_status'] for r in lineage)),reader_errors=len(errors),
        note='Q tokens are provisional source-name groups, not confirmed people or diagnoses; clinical linkage follows separately')
    (out/'summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2),flush=True)
if __name__=='__main__':main()
