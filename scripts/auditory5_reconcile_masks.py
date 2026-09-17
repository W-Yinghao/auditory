import json
import pandas as pd
from auditory5.provenance import ROOT,require_slurm,write_json

def main():
    require_slurm();base=ROOT/'private/auditory5_v1/data/ha_export_001';old=pd.read_csv(ROOT/'results/phase1_final_001/epoch_ledger.csv')
    rows=[]
    for bank in ['P1_CAUSAL20','P2_SPATIAL_SPLIT']:
        for f in sorted((base/bank).glob('*/events.parquet')):
            now=pd.read_parquet(f);prior=old[old.recording_id==f.parent.name]
            oldset=set(prior.loc[prior.accepted_150uv.astype(str).str.lower().eq('true'),'event_index_1based'].astype(int))
            newset=set(now.loc[now.accepted,'event_index_1based'].astype(int))
            rows.append({'bank':bank,'record_id':f.parent.name,'legacy_accepted':len(oldset),'new_accepted':len(newset),
              'both':len(oldset&newset),'legacy_only':len(oldset-newset),'new_only':len(newset-oldset)})
    data=pd.DataFrame(rows);dest=ROOT/'private/auditory5_v1/validation/legacy_masks_001';dest.mkdir(parents=True,exist_ok=False)
    data.to_parquet(dest/'record_comparison.parquet',index=False)
    summary=data.drop(columns='record_id').groupby('bank').sum().reset_index().to_dict('records')
    out=ROOT/'results/auditory5_v1/legacy_masks_001';out.mkdir(parents=True,exist_ok=False)
    write_json(out/'summary.json',{'status':'PASS','comparison':summary,'interpretation':'same frozen index sources; different causal reference/filter and guard definition; no expected equality'})
    print(json.dumps(summary))
if __name__=='__main__':main()
