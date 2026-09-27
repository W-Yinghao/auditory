"""Reconstruct every target epoch from selected raw continuous MFF sources."""
import argparse,csv,hashlib,json,os,shutil,tempfile,traceback
from collections import Counter
from pathlib import Path
import numpy as np
import mne
from phase1_core import epoch_grid
from phase1_prepare import readcsv,table
from phase1_epochs import digest
BASE=Path(__file__).resolve().parents[1]

def streamed_interval(raw,eeg,first,last,sf,cfg,filename,rawhash):
    """Finite FIR support permits exact central chunks with >=10 s padding."""
    n=last-first;step=int(60*sf);pad=int(cfg['edge_guard_s']*sf)
    kernel=mne.filter.create_filter(None,sf,cfg['highpass_hz'],cfg['lowpass_hz'],l_trans_bandwidth=cfg['highpass_hz'],h_trans_bandwidth=7.5,verbose='ERROR')
    assert (len(kernel)-1)//2<pad
    dest=np.memmap(filename,dtype=np.float64,mode='w+',shape=(len(eeg),n))
    mins=np.full(len(eeg),np.inf);maxs=-mins.copy();badch=np.zeros(len(eeg),bool)
    for start in range(first,last,step):
        stop=min(last,start+step);lo=max(first,start-pad);hi=min(last,stop+pad)
        x=raw.get_data(picks=eeg,start=lo,stop=hi)*1e6
        central=x[:,start-lo:stop-lo];rawhash.update(memoryview(np.ascontiguousarray(central)).cast('B'))
        badch|=(~np.isfinite(central)).any(axis=1);np.nan_to_num(x,copy=False)
        mins=np.minimum(mins,central.min(axis=1));maxs=np.maximum(maxs,central.max(axis=1))
        filtered=mne.filter.filter_data(x,sf,cfg['highpass_hz'],cfg['lowpass_hz'],l_trans_bandwidth=cfg['highpass_hz'],h_trans_bandwidth=7.5,filter_length='auto',method='fir',phase='zero',fir_window='hamming',fir_design='firwin',copy=False,n_jobs=1,verbose='ERROR')
        dest[:,start-first:stop-first]=filtered[:,start-lo:stop-lo]
    dest.flush();return dest,mins,maxs,badch

def process(row,path,cfg,out,private):
    mid=row['container_id'];dest=out/mid;dest.mkdir(exist_ok=False)
    raw=mne.io.read_raw_egi(path,preload=False,verbose='ERROR');sf=float(raw.info['sfreq'])
    eeg=mne.pick_types(raw.info,eeg=True,exclude=[]);names=np.array([raw.ch_names[i] for i in eeg])
    refnames=set(json.loads(row['reference_channels']));physical=np.array([n not in refnames for n in names])
    roi_names=json.loads(row['roi_channels']);roi_indices=[list(names).index(n) for n in roi_names]
    intervals=json.loads(row['storage_intervals_samples']);blocks=[];blockptp=[];finitebad=np.zeros(len(eeg),bool)
    raw_min=np.full(len(eeg),np.inf);raw_max=np.full(len(eeg),-np.inf);rawhash=hashlib.sha256();total=0;streamed=0
    tmp=tempfile.TemporaryDirectory(prefix='auditory-ci-',dir=os.environ.get('SLURM_TMPDIR','/tmp'))
    guard=int(round(cfg['edge_guard_s']*sf));span=int(round(2*sf))
    for first,last in intervals:
        if (last-first)*len(eeg)>int(os.environ.get('AUDIT_STREAM_THRESHOLD_SAMPLES','200000000')) and last-first>2*guard+int(sf):
            filtered,mn,mx,nb=streamed_interval(raw,eeg,first,last,sf,cfg,Path(tmp.name)/f'interval_{first}.dat',rawhash)
            total+=(last-first)*len(eeg);streamed+=1;raw_min=np.minimum(raw_min,mn);raw_max=np.maximum(raw_max,mx);finitebad|=nb
            length=(last-first-2*guard)//span
            # Process QC blocks in small temporal batches too; no full-array copy.
            pts=[]
            for k in range(0,length,30):
                take=min(30,length-k);z=filtered[:,guard+k*span:guard+(k+take)*span]
                pts.append(np.ptp(z.reshape(len(eeg),take,span),axis=-1))
            blockptp.append(np.concatenate(pts,axis=1));blocks.append((first,last,filtered));continue
        x=raw.get_data(picks=eeg,start=first,stop=last);x*=1e6
        rawhash.update(memoryview(np.ascontiguousarray(x)).cast('B'));total+=x.size
        bad=~np.isfinite(x);finitebad|=bad.any(axis=1);np.nan_to_num(x,copy=False)
        raw_min=np.minimum(raw_min,x.min(axis=1));raw_max=np.maximum(raw_max,x.max(axis=1))
        if last-first<=2*guard+int(sf):continue
        filtered=mne.filter.filter_data(x,sf,cfg['highpass_hz'],cfg['lowpass_hz'],
            l_trans_bandwidth=cfg['highpass_hz'],h_trans_bandwidth=7.5,filter_length='auto',
            method='fir',phase='zero',fir_window='hamming',fir_design='firwin',copy=False,n_jobs=1,verbose='ERROR')
        length=(filtered.shape[1]-2*guard)//span
        bp=np.ptp(filtered[:,guard:guard+length*span].reshape(len(eeg),length,span),axis=-1)
        blockptp.append(bp);blocks.append((first,last,filtered))
    assert total==int(row['stored_samples'])*len(eeg)
    allptp=np.concatenate(blockptp,axis=1) if blockptp else np.full((len(eeg),1),np.nan)
    med=np.median(allptp,axis=1);flat=np.mean(allptp<cfg['flat_2s_ptp_uv'],axis=1)
    reference_median=np.median(med[physical&~finitebad])
    badchannels=finitebad|(flat>=cfg['flat_fraction_threshold'])|(med>cfg['bad_channel_median_2s_ptp_uv'])|(med>cfg['bad_channel_relative_ptp_factor']*reference_median)|~np.isfinite(med)
    good=physical&~badchannels
    channel_ok=good.sum()>=cfg['minimum_good_channel_fraction']*physical.sum()
    roi_ok=all(not badchannels[k] or not physical[k] for k in roi_indices)
    table(dest/'channel_qc.csv',[dict(channel=str(n),physical_nonreference=bool(physical[i]),reference_member=bool(good[i]),
        raw_nonfinite=bool(finitebad[i]),raw_min_uv=float(raw_min[i]),raw_max_uv=float(raw_max[i]),
        filtered_median_2s_ptp_uv=float(med[i]),filtered_flat_block_fraction=float(flat[i])) for i,n in enumerate(names)])
    target=set(cfg['event_codes']);events=[]
    for ordinal,(onset,code) in enumerate(zip(raw.annotations.onset,raw.annotations.description)):
        if str(code) in target:events.append((ordinal,float(onset),int(round(onset*sf)),str(code)))
    codes_at_sample={}
    for _,_,sample,code in events:codes_at_sample.setdefault(sample,[]).append(code)
    offsets,decimation,times=epoch_grid(sf,*cfg['epoch_s'],int(round(sf/cfg['stored_sampling_hz'])))
    baseline=(offsets/sf>=cfg['baseline_s'][0]-1e-10)&(offsets/sf<cfg['baseline_s'][1]-1e-10)
    waves=[];codes=[];samplelist=[];eventordinal=[];masks=[];ledger=[];sums={};counts=Counter()
    for ordinal,onset,sample,code in events:
        reasons=[];found=None
        for si,(first,last,x) in enumerate(blocks):
            if sample+offsets[0]>=first+guard and sample+offsets[-1]<last-guard:found=(si,first,x);break
        if len(codes_at_sample[sample])!=1:reasons.append('target_sample_collision')
        item=dict(container_id=mid,annotation_index_0based=ordinal,onset_s=onset,sample_0based=sample,event_code=code,
            roi_epoch_index='',accepted=False,strict_accepted=False,over_threshold_fraction='',max_good_channel_ptp_uv='',roi_max_ptp_uv='')
        if found is None:reasons.append('interval_or_edge_guard')
        else:
            si,first,x=found
            ep=x[:,sample-first+offsets].copy()
            if not good.any():reasons.append('no_reference_channels');ref=np.zeros(ep.shape[1])
            else:ref=ep[good].mean(axis=0)
            ep-=ref[None,:];ep-=ep[:,baseline].mean(axis=1,keepdims=True)
            roi=ep[roi_indices]
            p2p=np.ptp(ep[good],axis=1) if good.any() else np.array([np.inf])
            fraction=float(np.mean(p2p>cfg['epoch_ptp_threshold_uv']))
            rp=float(np.max(np.ptp(roi,axis=1)))
            if not channel_ok:reasons.append('insufficient_record_good_channels')
            if not roi_ok:reasons.append('record_roi_channel_bad')
            if fraction>cfg['maximum_fraction_channels_over_threshold']:reasons.append('too_many_channels_over_ptp')
            if rp>cfg['epoch_ptp_threshold_uv']:reasons.append('roi_over_ptp')
            accepted=not reasons;strict=accepted and np.max(p2p)<=cfg['epoch_ptp_threshold_uv']
            item.update(roi_epoch_index=len(waves),accepted=accepted,strict_accepted=bool(strict),
                over_threshold_fraction=fraction,max_good_channel_ptp_uv=float(np.max(p2p)),roi_max_ptp_uv=rp,storage_interval_index=si)
            waves.append(roi[:,decimation].astype(np.float32));codes.append(code);samplelist.append(sample);eventordinal.append(ordinal);masks.append([accepted,strict])
            if accepted:
                ev=ep[:,decimation];sums[code]=sums.get(code,np.zeros_like(ev))+ev;counts[code]+=1
        item['rejection_reasons']='|'.join(reasons);ledger.append(item)
    table(dest/'epoch_ledger.csv',ledger)
    np.savez_compressed(dest/'epochs_roi.npz',roi_uv=np.array(waves,dtype=np.float32).reshape(-1,2,len(times)),
        event_codes=np.array(codes),samples_0based=np.array(samplelist,dtype=np.int64),annotation_indices_0based=np.array(eventordinal),
        accepted=np.array(masks,dtype=bool).reshape(-1,2),times_s=times,roi_channels=np.array(roi_names),sfreq=sf)
    keys=sorted(sums)
    np.savez_compressed(dest/'evoked.npz',data_uv=np.array([sums[c]/counts[c] for c in keys]),event_codes=np.array(keys),
        counts=np.array([counts[c] for c in keys]),times_s=times,channels=names,good_reference_channels=good)
    summary=dict(**row,job_id=os.environ['SLURM_JOB_ID'],status='processed',raw_numeric_uv_sha256=rawhash.hexdigest(),
        streamed_intervals=streamed,raw_hash_order='per_interval_then_60s_chunk_then_channel' if streamed else 'per_interval_then_channel',
        raw_channel_samples_examined=total,record_good_channels=int(good.sum()),physical_channels=int(physical.sum()),
        record_channel_gate=bool(channel_ok),roi_channel_gate=bool(roi_ok),target_annotations=len(events),
        stored_epochs=len(waves),primary_retained=int(sum(m[0] for m in masks)),strict_retained=int(sum(m[1] for m in masks)),
        accepted_counts=dict(counts),rejection_counts=dict(Counter(reason for r in ledger for reason in r['rejection_reasons'].split('|') if reason)),
        epoch_data_sha256=digest(dest/'epochs_roi.npz'),source_annotations_to_stored_consistent=True)
    (dest/'summary.json').write_text(json.dumps(summary,indent=2));raw.close();tmp.cleanup()
    return summary

def main():
    assert os.environ.get('SLURM_JOB_ID');os.umask(0o077)
    parser=argparse.ArgumentParser();parser.add_argument('--smoke',action='store_true');parser.add_argument('--resume',action='store_true');args=parser.parse_args()
    cfgpath=BASE/'configs/phase3_science_v1.json';cfg=json.loads(cfgpath.read_text())['ci']
    run='phase3_ci_smoke_001' if args.smoke else 'phase3_ci_epochs_001'
    out=BASE/'results'/run;out.mkdir(exist_ok=True);private=BASE/'private'/run;private.mkdir(mode=0o700,exist_ok=True)
    shard=0 if args.smoke else int(os.environ.get('SLURM_ARRAY_TASK_ID',0));nshards=1 if args.smoke else 8
    rows=[r for r in readcsv(BASE/'results/phase3_ci_sources_001/source_manifest.csv') if r['source_status']=='eligible']
    if args.smoke:
        choices={}
        for r in rows:choices.setdefault((r['n_channels'],r['sfreq']),r)
        rows=list(choices.values())[:4]
    else:rows=rows[shard::nshards]
    paths={r['container_id']:r['path'] for r in readcsv(BASE/'private/phase3_ci_sources_001/source_paths_and_tokens.csv')}
    snap=out/(f'code_shard_{shard:02d}_resume_{os.environ["SLURM_JOB_ID"]}' if args.resume else f'code_shard_{shard:02d}');snap.mkdir(exist_ok=False)
    for p in [Path(__file__),cfgpath,BASE/'scripts/phase1_core.py']:shutil.copy2(p,snap/p.name)
    summaries=[];errors=[]
    for r in rows:
        assert r['config_sha256']==digest(cfgpath)
        if args.resume:
            dest=out/r['container_id'];summarypath=dest/'summary.json'
            if summarypath.exists():
                prior=json.loads(summarypath.read_text())
                assert prior['config_sha256']==digest(cfgpath) and prior['epoch_data_sha256']==digest(dest/'epochs_roi.npz')
                summaries.append(prior);continue
            if dest.exists():shutil.move(str(dest),str(private/(r['container_id']+'_incomplete_before_'+os.environ['SLURM_JOB_ID'])))
        try:
            result=process(r,paths[r['container_id']],cfg,out,private);summaries.append(result)
            print(json.dumps({k:result[k] for k in ['container_id','stored_epochs','primary_retained','record_good_channels','accepted_counts']}),flush=True)
        except Exception as exc:
            errors.append(dict(container_id=r['container_id'],error=repr(exc),trace=traceback.format_exc()))
    (private/f'errors_{shard:02d}.json').write_text(json.dumps(errors,indent=2))
    (out/f'completion_{shard:02d}.json').write_text(json.dumps(dict(job_id=os.environ['SLURM_JOB_ID'],attempted=len(rows),completed=len(summaries),errors=len(errors)),indent=2))
    if errors:raise RuntimeError(f'{len(errors)} CI source errors; inspect private errors')
if __name__=='__main__':main()
