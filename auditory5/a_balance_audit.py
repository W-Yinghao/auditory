"""Describe missing A history/position cells without changing selection rules."""
import argparse,json
import numpy as np
import pandas as pd
from auditory5.provenance import ROOT,require_slurm,digest,write_json


def main():
    require_slurm();p=argparse.ArgumentParser();p.add_argument('--run',required=True);a=p.parse_args()
    base=ROOT/'private/auditory5_v1';out=ROOT/'results/auditory5_v1'/a.run;dest=base/'routes'/a.run
    dest.mkdir(parents=True,exist_ok=False);out.mkdir(parents=True,exist_ok=False)
    splitpath=base/'splits/splits_001/folds.json';split=json.loads(splitpath.read_text())
    support=pd.read_parquet(splitpath.parent/'support.parquet');parts=[];hashes={str(splitpath):digest(splitpath)}
    for rec in support[support.A].to_dict('records'):
        folder=base/'data'/split['export_run']/'P1_CAUSAL20'/rec['record_id'];sp=folder/'summary.json'
        if digest(sp)!=split['input_hashes']['P1_CAUSAL20/'+rec['record_id']]:raise ValueError('A balance source changed')
        meta=json.loads(sp.read_text());ep=folder/'events.parquet'
        if digest(ep)!=meta['output_sha256']['events.parquet']:raise ValueError('A event ledger changed')
        hashes[str(ep)]=digest(ep);r=pd.read_parquet(ep);parts.append(r[r.accepted & r.A_boundary_eligible.fillna(False)])
    rows=pd.concat(parts,ignore_index=True);rows['position_bin']=np.minimum((rows.segment_position_fraction*3).astype(int),2)
    cells=[];eligible=set(support.loc[support.A,'split_group_id'])
    for group in sorted(eligible):
        own=rows[rows.split_group_id.eq(group)]
        for half in [0,1]:
            for label in [0,1]:
                sub=own[own.A_half.eq(half)&own.stimulus_local_id.eq(label)]
                for history in [0,1]:
                    for position in [0,1,2]:
                        cell=sub[sub.history_target.eq(history)&sub.position_bin.eq(position)]
                        quota=4 if history==0 and position in [0,1] else 3
                        cells.append({'split_group_id':group,'half':half,'stimulus_local_id':label,'history':history,
                            'position_third':position,'trials':len(cell),'blocks':int(cell.A_block_id.nunique()),
                            'quota':quota,'below_quota':len(cell)<quota,'zero_cell':len(cell)==0,
                            'half_class_trials':len(sub),'half_class_unknown_or_omitted_history':int((~sub.history_target.isin([0,1])).sum())})
    frame=pd.DataFrame(cells);frame.to_parquet(dest/'candidate_cell_counts.parquet',index=False)
    aggregate=frame.groupby(['half','stimulus_local_id','history','position_third','quota']).agg(
        candidates=('split_group_id','nunique'),median_trials=('trials','median'),minimum_trials=('trials','min'),
        zero_cell_candidates=('zero_cell','sum'),below_quota_candidates=('below_quota','sum')).reset_index()
    aggregate['literal_code']=aggregate.stimulus_local_id+1;aggregate.to_csv(out/'history_position_support.csv',index=False)
    complete=~frame.groupby('split_group_id').below_quota.any()
    summary={'stage':'A_history_position_support_audit','status':'COMPLETE','candidate_groups':len(eligible),
        'candidates_with_all_24_cells_at_fixed_quota':int(complete.sum()),
        'cell_quota':'same allocation for both halves/classes: H0 positions0/1 have4, all other cells3; total20',
        'block_draw_eligibility_not_inferred_from_counts':True,'selection_rules_changed':False,
        'interpretation':'descriptive support audit of the frozen secondary balance; no EEG outcome used or new primary'}
    write_json(out/'summary.json',summary);write_json(dest/'input_hashes.json',hashes)
    print(json.dumps(summary),flush=True)

if __name__=='__main__':main()
