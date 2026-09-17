import argparse,json
import numpy as np
import pandas as pd
from auditory5.provenance import ROOT,require_slurm,write_json,digest

def main():
    require_slurm();p=argparse.ArgumentParser();p.add_argument('--run',required=True);p.add_argument('--export-run',required=True);a=p.parse_args()
    base=ROOT/'private/auditory5_v1/data'/a.export_run/'P1_CAUSAL20';out=ROOT/'results/auditory5_v1'/a.run;out.mkdir(parents=True,exist_ok=False)
    completions=list(base.glob('shard_*/completion.json'));assert completions and all(json.loads(p.read_text())['status']=='PASS' for p in completions)
    total=kept=records=supported=0;private_rows=[]
    for d in sorted(base.iterdir()):
        if not (d/'summary.json').exists():continue
        s=json.loads((d/'summary.json').read_text());df=pd.read_parquet(d/'events.parquet');x=np.load(d/'all.npy',mmap_mode='r');t=np.load(d/'times_s.npy',mmap_mode='r')
        assert s['within_record_filter_state_isolation'] and s['physical_channels']==128 and s['processed_fs']==250
        assert x.shape==(s['stored_epochs'],128,175) and t.shape==(len(x),175)
        assert df.trial_id.is_unique
        stored=df[df.stored_epoch_index>=0].sort_values('stored_epoch_index');assert stored.stored_epoch_index.tolist()==list(range(len(x)))
        for start in range(0,len(x),128):assert np.isfinite(x[start:start+128]).all()
        assert np.allclose(np.diff(t,axis=1),.004,atol=1e-12)
        accepted=df[df.accepted];assert len(accepted)==s['accepted']
        assert ((accepted.onset_sample-200-accepted.filter_start_sample)>=20000).all()
        assert ((accepted.filter_stop_sample-accepted.onset_sample-500)>=10823).all()
        assert (accepted.over_ptp_channel_fraction<=.1).all() and (accepted.raw_flat_channel_fraction<=.1).all()
        regions=json.loads((d/'processing_contract.json').read_text())['regions']
        for first,second in zip(regions[:-1],regions[1:]):assert first['stop_sample']<=second['start_sample']
        for name,h in s['output_sha256'].items():assert digest(d/name)==h
        good=all((accepted.stimulus_local_id==c).sum()>=40 for c in [0,1]);supported+=good
        private_rows.append({'record_id':d.name,'candidate_id':s['candidate_id'],'accepted':len(accepted),'eligible_40_per_class':good,
             'class0':int((accepted.stimulus_local_id==0).sum()),'class1':int((accepted.stimulus_local_id==1).sum()),'blocks':int(accepted.filter_block_id.nunique())})
        records+=1;total+=len(x);kept+=len(accepted)
    private=ROOT/'private/auditory5_v1/validation'/a.run;private.mkdir(parents=True,exist_ok=False)
    pd.DataFrame(private_rows).to_parquet(private/'support.parquet',index=False)
    summary={'status':'PASS','stage':'MFF_native_E0_export_integration','records':records,'stored_epochs':total,'accepted_epochs':kept,
             'records_40_each_class':int(supported),'physical_channels':128,'independently_filtered_60s_blocks':True,'export_run':a.export_run}
    write_json(out/'validation.json',summary);print(json.dumps(summary))
if __name__=='__main__':main()
