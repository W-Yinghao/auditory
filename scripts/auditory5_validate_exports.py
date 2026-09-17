"""Integrated, outcome-blind export audit; execute only through Slurm."""
import argparse,json
from pathlib import Path
import numpy as np
import pandas as pd
from auditory5.provenance import ROOT,require_slurm,write_json,digest
from auditory5.events import build_event_history

def main():
    require_slurm();p=argparse.ArgumentParser();p.add_argument('--export-run',required=True);p.add_argument('--run',required=True);a=p.parse_args()
    base=ROOT/'private/auditory5_v1/data'/a.export_run
    out=ROOT/'results/auditory5_v1'/a.run;out.mkdir(parents=True,exist_ok=False)
    banks=['P1_CAUSAL20','P2_SPATIAL_SPLIT'];tables={};counts={};hashes={}
    for bank in banks:
        completions=list((base/bank).glob('shard_*/completion.json'))
        assert completions and all(json.loads(x.read_text())['status']=='PASS' for x in completions)
        expected={r['record_id'] for f in completions for r in json.loads(f.read_text())['complete']}
        dirs=[x for x in (base/bank).iterdir() if (x/'summary.json').exists()]
        assert {x.name for x in dirs}==expected
        tables[bank]={};kept=stored=events=0
        for d in dirs:
            s=json.loads((d/'summary.json').read_text());df=pd.read_parquet(d/'events.parquet')
            assert df.trial_id.is_unique and df.onset_sample.is_monotonic_increasing
            ss=df[df.stored_epoch_index>=0].sort_values('stored_epoch_index')
            assert ss.stored_epoch_index.tolist()==list(range(len(ss)))
            assert len(ss)==s['stored_epochs'] and int(df.accepted.sum())==s['accepted']
            assert not df.loc[df.accepted,'reject_reason'].fillna('').str.len().any()
            # Guard applies to actual retained fixed-grid samples, not an invented
            # exactly -200ms first sample when a trigger falls between grid points.
            assert ((df.loc[df.accepted,'onset_seconds_relative']+
                     df.loc[df.accepted,'grid_first_relative_s'])>=20.-1e-10).all()
            assert ((ss.grid_first_relative_s>=-.2-1e-12)&(ss.grid_first_relative_s<-.196+1e-12)).all()
            assert set(ss.pre_stop_index)=={50} and set(ss.post_start_index)<= {62,63}
            for name,channels in s['branch_channels'].items():
                arr=np.load(d/(name+'.npy'),mmap_mode='r')
                assert arr.shape==(len(ss),len(channels),175) and arr.dtype==np.float32
                for start in range(0,len(arr),512):assert np.isfinite(arr[start:start+512]).all()
                assert digest(d/(name+'.npy'))==s['output_sha256'][name+'.npy']
                q=ss[name+'_accepted'].to_numpy(bool)
                assert (ss.loc[q,name+'_ptp_uv']<=150).all()
            again=pd.DataFrame(build_event_history(df.to_dict('records'),s['original_fs'],target_codes=['1','2']))
            for field in ['previous_event_id','previous_code','previous_run_length','history_target','current_run_length']:
                assert again[field].fillna('NULL').tolist()==df[field].fillna('NULL').tolist()
            arows=df[df.accepted & df.A_boundary_eligible.fillna(False)]
            assert ((arows.onset_seconds_relative-.2-arows.A_block_id*60)>=10.823-1e-10).all()
            assert (((arows.A_block_id+1)*60-arows.onset_seconds_relative-.5)>=10.823-1e-10).all()
            tables[bank][d.name]=df;kept+=s['accepted'];stored+=s['stored_epochs'];events+=len(df)
            hashes[bank+'/'+d.name]=digest(d/'summary.json')
        counts[bank]={'records':len(dirs),'all_annotation_rows':events,'stored_complete_epochs':stored,'accepted_epochs':kept}
    assert set(tables[banks[0]])==set(tables[banks[1]])
    for rid,df in tables[banks[0]].items():
        other=tables[banks[1]][rid]
        for field in ['trial_id','onset_sample','event_literal','stored_epoch_index','previous_event_id','history_target']:
            assert df[field].fillna('NULL').tolist()==other[field].fillna('NULL').tolist()
        assert df.source_sha256.iloc[0]==other.source_sha256.iloc[0]
    write_json(out/'validation.json',{'status':'PASS','stage':'S1_export_integration','export_run':a.export_run,'counts':counts,
        'checked':'source digests, finite shapes, shared event identity, pre-QC history replay, retained rejection, trigger grid, A embargo',
        'scientific_outcomes_examined':False})
    private=ROOT/'private/auditory5_v1/validation'/a.run;private.mkdir(parents=True,exist_ok=False)
    write_json(private/'input_hashes.json',hashes)
    print(json.dumps({'status':'PASS','counts':counts}))
if __name__=='__main__':main()
