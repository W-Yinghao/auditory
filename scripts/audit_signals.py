#!/usr/bin/env python3
"""Full SET signal QC, event alignment checks, and bounded raw signal previews."""
import csv,json,os,hashlib,traceback
from pathlib import Path
from collections import Counter,defaultdict
import numpy as np
from scipy.signal import welch
from pymatreader import read_mat
import pyedflib
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
from audit_mff import dump,table,j
from audit_other_eeg import records,seq,token
BASE=Path(__file__).resolve().parents[1]
def preview(x,sf,label,path,unit,tmin=0,mean_by_code=None):
    fig,axs=plt.subplots(1,3 if mean_by_code else 2,figsize=(12 if mean_by_code else 9,3.2))
    n=min(x.shape[-1],int(2*sf));pick=np.linspace(0,x.shape[0]-1,min(3,x.shape[0]),dtype=int)
    for k in pick:axs[0].plot(np.arange(n)/sf+tmin,x[k,:n],lw=.7,label=f'channel {k+1}')
    axs[0].set(xlabel='Time (s)',ylabel=unit,title='Stored signal; no additional filtering');axs[0].legend(fontsize=6)
    f,p=welch(x,fs=sf,nperseg=min(x.shape[-1],int(2*sf)),axis=-1)
    axs[1].semilogy(f,np.median(p,axis=0));axs[1].set(xlim=(0,min(100,sf/2)),xlabel='Frequency (Hz)',ylabel=f'{unit} squared / Hz',title='Median channel PSD')
    if mean_by_code:
        for code,(wave,ntrial) in mean_by_code.items():axs[2].plot(np.arange(len(wave))/sf+tmin,wave,label=f'code {code}, n={ntrial}')
        axs[2].axvline(0,color='k',lw=.5);axs[2].legend(fontsize=6);axs[2].set(xlabel='Epoch time (s)',ylabel=unit,title='Channel 1 mean; semantics unverified')
    fig.suptitle(label,fontsize=9);fig.tight_layout();fig.savefig(path,dpi=140);plt.close(fig)
def main():
    assert os.environ.get('SLURM_JOB_ID')
    out=BASE/'results/signal_001';out.mkdir(exist_ok=False);figs=BASE/'figures/signal_001';figs.mkdir(exist_ok=False)
    priv=BASE/'private/signal_001';priv.mkdir(mode=0o700,exist_ok=False)
    paths={r['file_id']:Path(r['absolute_path']) for r in csv.DictReader((BASE/'private/inventory_001/file_path_map.csv').open())}
    sets=list(csv.DictReader((BASE/'results/other_eeg_001/set_index.csv').open()));bdfs=list(csv.DictReader((BASE/'results/other_eeg_001/bdf_index.csv').open()))
    epochs=[];summaries=[];errors=[];crosschecks=[];digest_counts=Counter();bdf_pairs=[]
    for row in sets:
      fid=row['file_id'];p=paths[fid]
      try:
        d=read_mat(p);d=d.get('EEG',d);sf=float(d['srate']);nc=int(d['nbchan']);nt=int(d['trials']);ns=int(d['pnts']);xmin=float(d['xmin'])
        comp=p.parent/d['data'];assert comp.stat().st_size==4*nc*nt*ns
        data=np.memmap(comp,dtype='<f4',mode='r',shape=(nt,ns,nc));es=records(d.get('event',[]));eps=records(d.get('epoch',[]));sums={};counts=Counter();allp=[];nfinite=0;nflat=0;checks=[]
        if nt>1:
            assert len(eps)==nt
            for ei,e in enumerate(eps):
                x=np.asarray(data[ei].T,dtype=np.float64);p2p=np.ptp(x,axis=1);finite=np.isfinite(x).all();flat=int(np.sum(p2p==0));digest=hashlib.sha256(data[ei].tobytes()).hexdigest();digest_counts[digest]+=1
                refs=[int(v)-1 for v in seq(e.get('event',[]))];stored=[float(v)/1000 for v in seq(e.get('eventlatency',[]))];codes=[token(v) for v in seq(e.get('eventtype',[]))]
                computed=[(float(es[k]['latency'])-1-ei*ns)/sf+xmin for k in refs if 0<=k<len(es)]
                mismatch=len(computed)!=len(stored);maxdiff=max((abs(a-b) for a,b in zip(computed,stored)),default=0);mismatch|=maxdiff>1e-6
                checks.append(maxdiff);zero=[codes[k] for k,t in enumerate(stored) if abs(t)<=.5/sf and k<len(codes)]
                if len(zero)==1 and finite:
                    code=zero[0];sums[code]=sums.get(code,np.zeros(ns))+x[0];counts[code]+=1
                epochs.append({'file_id':fid,'epoch_1based':ei+1,'all_finite':finite,'flat_channels':flat,'median_channel_peak_to_peak_native':float(np.median(p2p)),'max_abs_native':float(np.nanmax(abs(x))),'signal_sha256':digest,'event_latency_max_difference_s':maxdiff,'event_alignment_consistent':not mismatch,'zero_label_count':len(zero),'clinical_label_status':'not_linked'})
                allp.append(float(np.median(p2p)));nfinite+=not finite;nflat+=flat>0
            preview(data[0].T,sf,fid+' | existing epochs',figs/(fid+'.png'),'EEGLAB native units',xmin,{k:(sums[k]/counts[k],counts[k]) for k in sums})
        else:
            # Every continuous sample is examined in non-overlapping 10-second chunks.
            for start in range(0,ns,int(sf*10)):
                x=np.asarray(data[0,start:start+int(sf*10)].T,dtype=np.float64);p2p=np.ptp(x,axis=1);allp.append(float(np.median(p2p)));nfinite+=not np.isfinite(x).all();nflat+=bool(np.any(p2p==0))
            preview(data[0,:min(ns,int(sf*30))].T,sf,fid+' | continuous preview',figs/(fid+'.png'),'EEGLAB native units')
        summaries.append({'file_id':fid,'format':'SET','data_level':row['data_level'],'samples_examined':nt*ns,'n_epochs_examined':nt if nt>1 else 0,'nonfinite_blocks_or_epochs':nfinite,'blocks_or_epochs_with_flat_channels':nflat,'median_block_or_epoch_channel_p2p_native':float(np.median(allp)),'event_max_alignment_difference_s':max(checks,default=0),'clinical_outcome_used':False,'status':'measured_not_task_approved'})
        # Independent MNE read for one continuous and one epoched layout.
        if not any(c['data_level']==row['data_level'] for c in crosschecks):
            import mne
            obj=mne.read_epochs_eeglab(str(p),verbose='ERROR') if nt>1 else mne.io.read_raw_eeglab(str(p),preload=False,verbose='ERROR')
            xx=obj.get_data()[0,:,:10] if nt>1 else obj.get_data(start=0,stop=10)
            expected=data[0,:10].T.astype(float)*1e-6
            crosschecks.append({'file_id':fid,'data_level':row['data_level'],'mne_max_abs_difference_V':float(np.max(abs(xx-expected))),'sfreq_equal':obj.info['sfreq']==sf})
            del obj
        del data
      except Exception as e:errors.append({'file_id':fid,'error':repr(e),'trace':traceback.format_exc()})
    # Pairing and timing validation use both header timestamps and annotation positions.
    bh=json.loads((BASE/'private/other_eeg_001/bdf_private_headers.json').read_text());bh={r['file_id']:r for r in bh}
    groups=defaultdict(list)
    for r in bdfs:groups[r['candidate_acquisition_id']].append(r)
    eventrows=list(csv.DictReader((BASE/'results/other_eeg_001/event_ledger.csv').open()));ev=defaultdict(list)
    for e in eventrows:
        if e['source']=='BDF_annotations':ev[e['file_id']].append(float(e['onset_s']))
    for gid,rs in groups.items():
        sig=[r for r in rs if r['file_role']=='signal'];evt=[r for r in rs if r['file_role']=='event_companion']
        if len(sig)!=1 or len(evt)!=1:continue
        a,b=sig[0],evt[0];ha,hb=bh[a['file_id']],bh[b['file_id']];times=ev[b['file_id']];dur=float(a['duration_s']);same=ha['date']==hb['date'] and ha['time']==hb['time']
        bdf_pairs.append({'candidate_acquisition_id':gid,'signal_file_id':a['file_id'],'event_file_id':b['file_id'],'header_start_equal':same,'annotation_count':len(times),'events_outside_signal_duration':sum(t<0 or t>=dur for t in times),'event_file_duration_is_not_signal_duration':float(b['duration_s'])!=dur,'acoustic_trigger_delay_status':'unknown','pairing_status':'same_directory_headers_checked'})
    candidates=sorted([r for r in bdfs if r['file_role']=='signal'],key=lambda r:(float(r['duration_s']),r['file_id']))
    for idx in sorted(set([0,len(candidates)//2,len(candidates)-1])):
      r=candidates[idx];fid=r['file_id']
      try:
        with pyedflib.EdfReader(str(paths[fid])) as reader:
            sf=reader.getSampleFrequency(0);ns=min(int(sf*30),int(reader.getNSamples()[0]));x=np.array([reader.readSignal(k,start=0,n=ns) for k in range(reader.signals_in_file)])
            unit=reader.getPhysicalDimension(0)
        preview(x,sf,fid+' | first 30 s, duration-stratified',figs/(fid+'.png'),unit)
        summaries.append({'file_id':fid,'format':'BDF','samples_examined':ns,'all_finite':bool(np.isfinite(x).all()),'flat_channels':int(np.sum(np.ptp(x,axis=1)==0)),'median_block_or_epoch_channel_p2p_native':float(np.median(np.ptp(x,axis=1))),'unit':unit,'status':'bounded_preview'})
      except Exception as e:errors.append({'file_id':fid,'error':repr(e),'trace':traceback.format_exc()})
    table(out/'epoch_signal_qc.csv',epochs);table(out/'signal_qc_summary.csv',summaries);table(out/'bdf_pairing.csv',bdf_pairs);dump(out/'reader_crosschecks.json',crosschecks);dump(priv/'errors.json',errors)
    dump(out/'summary.json',{'job_id':os.environ['SLURM_JOB_ID'],'set_signal_files':sum(r.get('format')=='SET' for r in summaries),'set_epochs_qc':len(epochs),'epoch_alignment_failures':sum(not r['event_alignment_consistent'] for r in epochs),'duplicate_epoch_signal_extra_copies':sum(v-1 for v in digest_counts.values() if v>1),'nonfinite_epochs':sum(not r['all_finite'] for r in epochs),'flat_channel_epochs':sum(r['flat_channels']>0 for r in epochs),'bdf_signal_previews':sum(r.get('format')=='BDF' for r in summaries),'bdf_pairs':len(bdf_pairs),'bdf_start_mismatches':sum(not r['header_start_equal'] for r in bdf_pairs),'bdf_pairs_with_out_of_range_events':sum(r['events_outside_signal_duration']>0 for r in bdf_pairs),'errors':len(errors)})
if __name__=='__main__':main()
