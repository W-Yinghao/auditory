"""Sparse cross-format signal audit; no full equality or new-person claims."""
import json,os,shutil,traceback
from collections import Counter,defaultdict
from pathlib import Path
import mne
import numpy as np
from audit_egi_events import read_header
from phase1_prepare import readcsv,table
BASE=Path(__file__).resolve().parents[1]

def sample_indices(n):
    assert n>=16
    return np.concatenate([np.arange(s,s+16) for s in np.linspace(0,n-16,9).astype(int)])

def mff_sparse(raw,indices,compressed):
    ex=raw._raw_extras[0]
    starts=np.asarray(ex['first_samps']);ends=np.asarray(ex['last_samps'])
    if compressed:
        length=ends-starts;cum=np.cumsum(length);part=np.searchsorted(cum,indices,side='right')
        index=starts[part]+indices-np.r_[0,cum[:-1]][part]
    else:index=indices
    eeg=mne.pick_types(raw.info,eeg=True,exclude=[]);out=np.empty((len(indices),len(eeg)))
    first=0
    while first<len(index):
        last=first+1
        while last<len(index) and index[last]==index[last-1]+1:last+=1
        out[first:last]=raw.get_data(picks=eeg,start=int(index[first]),stop=int(index[last-1])+1).T*1e6
        first=last
    return out

def main():
    assert os.getenv('SLURM_JOB_ID');os.umask(0o077)
    out=BASE/'results/phase3_raw_numeric_links_003';out.mkdir(exist_ok=False)
    priv=BASE/'private/phase3_raw_numeric_links_003';priv.mkdir(mode=0o700,exist_ok=False)
    paths={r['file_id']:Path(r['absolute_path']) for r in readcsv(BASE/'private/inventory_001/file_path_map.csv')}
    reg={r['container_id']:r['path'] for r in json.loads((BASE/'private/mff_001/registry.json').read_text())}
    allraw=readcsv(BASE/'results/other_eeg_001/egi_raw_index.csv')
    mffs=[r for r in readcsv(BASE/'manifests/mff_export_index.csv') if r['data_level']=='continuous_or_discontinuous' and r['topology_status']=='structure_passed']
    shape=defaultdict(set)
    for r in mffs:shape[(int(r['n_samples']),int(r['n_signal_channels']),float(r['sampling_rate_hz']))].add(r['container_id'])
    for r in readcsv(BASE/'results/phase3_ci_sources_001/source_manifest.csv'):
        if r.get('reader_n_samples'):shape[(int(r['reader_n_samples']),int(r['n_channels']),float(r['sfreq']))].add(r['container_id'])
        if r.get('storage_intervals_samples'):
            for start,stop in json.loads(r['storage_intervals_samples']):shape[(stop-start,int(r['n_channels']),float(r['sfreq']))].add(r['container_id'])
    lineage={r['container_id']:r['source_candidate_ids'] for r in readcsv(BASE/'results/phase3_ci_sources_001/all_mff_source_lineage.csv')}
    rawarrays={};rawmeta={};candidate_by_mid=defaultdict(list);rows=[];errors=[]
    for rr in allraw:
        if rr['data_level']!='continuous_binary':continue
        fid=rr['file_id'];ns=int(rr['n_samples']);nc=int(rr['n_channels']);sf=float(rr['sampling_rate_hz']);candidates=sorted(shape[(ns,nc,sf)])
        row=dict(file_id=fid,shape_candidate_count=len(candidates),numeric_status='no_shape_candidate' if not candidates else 'pending',numeric_candidates_tested=0,numeric_matches=0,matched_mff_ids='',source_candidate_ids='');rows.append(row);rawmeta[fid]=(row,ns)
        if not candidates:continue
        try:
            with paths[fid].open('rb') as f:h=read_header(f)
            assert h['version']%2==0 and h['n_samples']==ns and h['n_channels']==nc
            a=np.memmap(paths[fid],dtype=h['dtype'],mode='r',offset=h['offset'],shape=(ns,nc+h['n_event_channels']))
            # MNE EGI calibration is volts; float RAW with bits/range=0 is already uV.
            bits=int(rr['bits']);vr=int(rr['value_range']);factor=vr/(2.**bits)*1e6 if bits and vr else 1.
            rawarrays[fid]=np.asarray(a[sample_indices(ns),:nc],dtype=float)*factor;del a
            assert np.isfinite(rawarrays[fid]).all()
            for mid in candidates:candidate_by_mid[mid].append(fid)
        except Exception as exc:row['numeric_status']='raw_read_error';errors.append(dict(file_id=fid,error=repr(exc),trace=traceback.format_exc()))
    table(out/'shape_screen.csv',rows)
    comparisons=[];matches=defaultdict(set)
    for done,(mid,fids) in enumerate(sorted(candidate_by_mid.items()),1):
        try:
            raw=mne.io.read_raw_egi(reg[mid],preload=False,verbose='ERROR');ex=raw._raw_extras[0]
            stored=int(sum(ex['last_samps']-ex['first_samps']));cache={}
            for fid in fids:
                row,ns=rawmeta[fid]
                spans=[(int(a),int(b)) for a,b in zip(ex['first_samps'],ex['last_samps']) if b-a==ns]
                mode='compressed_stored' if ns==stored else 'full_axis' if ns==raw.n_times else 'single_stored_interval' if len(spans)==1 else None
                if mode is None:continue
                indices=sample_indices(ns)+(spans[0][0] if mode=='single_stored_interval' else 0)
                if (ns,mode) not in cache:cache[(ns,mode)]=mff_sparse(raw,indices,mode=='compressed_stored')
                a=rawarrays[fid];b=cache[(ns,mode)];assert a.shape==b.shape
                close=np.isclose(a,b,atol=1e-3,rtol=1e-5);ok=bool(close.all());row['numeric_candidates_tested']+=1
                comparisons.append(dict(file_id=fid,container_id=mid,axis_mode=mode,channel_samples_compared=a.size,numeric_match=ok,max_abs_difference_uv=float(np.max(np.abs(a-b))),close_fraction=float(close.mean())))
                if ok:matches[fid].add(mid)
            raw.close()
        except Exception as exc:errors.append(dict(container_id=mid,error=repr(exc),trace=traceback.format_exc()))
        if done%10==0:print(json.dumps(dict(mff_readers_done=done,total=len(candidate_by_mid))),flush=True)
    for row in rows:
        fid=row['file_id'];ids=matches[fid];sources={s for mid in ids for s in lineage.get(mid,'').split('|') if s}
        row.update(numeric_matches=len(ids),matched_mff_ids='|'.join(sorted(ids)),source_candidate_ids='|'.join(sorted(sources)))
        if row['numeric_status']=='pending':row['numeric_status']='sparse_numeric_match' if ids else 'no_sparse_numeric_match' if row['numeric_candidates_tested'] else 'candidate_reader_error'
    table(out/'raw_mff_numeric_links.csv',rows);table(out/'pair_comparisons.csv',comparisons)
    (priv/'errors.json').write_text(json.dumps(errors,indent=2))
    summary=dict(job_id=os.environ['SLURM_JOB_ID'],continuous_raw_files=len(rows),segmented_raw_excluded=len(allraw)-len(rows),continuous_mff_shape_pool=len(mffs),mff_readers_attempted=len(candidate_by_mid),status_counts=dict(Counter(r['numeric_status'] for r in rows)),matched_raw_with_selected_source=sum(bool(r['source_candidate_ids']) for r in rows),errors=len(errors),scope='9 positions x 16 samples x all EEG channels; calibrated uV; sparse consistency is not full equivalence or final identity merge')
    (out/'summary.json').write_text(json.dumps(summary,indent=2));shutil.copy2(Path(__file__),out/Path(__file__).name);print(json.dumps(summary))
if __name__=='__main__':main()
