"""Outcome-blind eligibility and identity-component outer/inner folds."""
import json
from collections import Counter
import numpy as np
import pandas as pd
from auditory5.provenance import ROOT,require_slurm,digest,object_hash,write_json


def supported_classes(frame, minimum=40, block_minimum=8):
    return all(((frame.stimulus_local_id==k).sum()>=minimum and
                frame.loc[frame.stimulus_local_id==k,'time_block_id'].nunique()>=block_minimum) for k in [0,1])


def record_support(p1,p2,clinical_complete=False):
    x=p1[p1.accepted].copy();z=p2[p2.accepted].copy()
    a=x[x.A_boundary_eligible.fillna(False)]
    aok=all((a.A_half.eq(h)&a.stimulus_local_id.eq(k)).sum()>=20 for h in [0,1] for k in [0,1])
    aok=aok and all(a.loc[a.A_half==h,'A_block_id'].nunique()>=4 for h in [0,1])
    b=x[(x.event_literal=='1')&(x.previous_code=='1')&x.history_target.notna()]
    bok=all((b.history_target==h).sum()>=20 and b.loc[b.history_target==h,'time_block_id'].nunique()>=4 for h in [0,1])
    general=supported_classes(x)
    # C's prespecified test support is 20/class; no automatic reuse of P1's QC.
    cok=all((z.stimulus_local_id==k).sum()>=20 for k in [0,1])
    return {'general':general,'A':bool(aok),'B':bool(bok),'C':bool(cok),
            'D':bool(clinical_complete and all((x.stimulus_local_id==k).sum()>=40 for k in [0,1])),
            'accepted_P1':len(x),'accepted_P2_joint':len(z),
            'P1_class0':int(x.stimulus_local_id.eq(0).sum()),'P1_class1':int(x.stimulus_local_id.eq(1).sum()),
            'P2_class0':int(z.stimulus_local_id.eq(0).sum()),'P2_class1':int(z.stimulus_local_id.eq(1).sum()),
            'A_half0_blocks':int(a.loc[a.A_half==0,'A_block_id'].nunique()),
            'A_half1_blocks':int(a.loc[a.A_half==1,'A_block_id'].nunique()),
            'B_history0':int(b.history_target.eq(0).sum()),'B_history1':int(b.history_target.eq(1).sum())}


def balanced_component_folds(rows,n_folds,seed=20260917):
    """Greedy balance counts of route support, never targets or model outcomes."""
    features=['general','A','B','C','D']
    grouped=rows.groupby('split_group_id',sort=True)[features].sum()
    ids=grouped.index.to_numpy();rng=np.random.default_rng(seed)
    tie=rng.random(len(ids));vectors=grouped.to_numpy(float)
    # Rare supported routes are balanced first. Final column balances all components.
    scales=np.maximum(vectors.sum(axis=0),1);v=np.c_[vectors/scales,np.ones(len(ids))/len(ids)]
    order=sorted(range(len(ids)),key=lambda i:(-float(v[i].sum()),tie[i]))
    loads=np.zeros((n_folds,v.shape[1]));counts=np.zeros(n_folds,int);assignment={}
    for i in order:
        minimum=counts.min();allowed=np.flatnonzero(counts<=minimum+1)
        j=min(allowed,key=lambda j:(float(np.sum((loads[j]+v[i])**2)-np.sum(loads[j]**2)),counts[j],j))
        assignment[str(ids[i])]=int(j);loads[j]+=v[i];counts[j]+=1
    return assignment


def run(config,args):
    require_slurm()
    base=ROOT/config['paths']['private_relative'];dest=base/'splits'/args.run;dest.mkdir(parents=True,exist_ok=False)
    out=ROOT/config['paths']['aggregates_relative']/args.run;out.mkdir(parents=True,exist_ok=False)
    export_run=args.export_run
    audit=json.loads((ROOT/config['paths']['aggregates_relative']/args.export_validation/'validation.json').read_text())
    if audit['status']!='PASS' or audit['export_run']!=export_run:raise ValueError('Export integration gate mismatch')
    records=pd.read_parquet(base/'data'/args.manifest/'records.parquet')
    clinical=pd.read_parquet(base/'data'/args.manifest/'clinical_index.parquet').set_index('record_id')
    selected=records[(records.branch=='HA_BDF')&records.analysis_index].sort_values('record_id')
    rows=[];hashes={}
    for r in selected.to_dict('records'):
        rid=r['record_id'];folder=base/'data'/export_run
        p1=pd.read_parquet(folder/'P1_CAUSAL20'/rid/'events.parquet')
        p2=pd.read_parquet(folder/'P2_SPATIAL_SPLIT'/rid/'events.parquet')
        cc=rid in clinical.index and bool(clinical.loc[rid,'clinical_complete'])
        row={k:r[k] for k in ['record_id','candidate_id','split_group_id']}
        row.update(record_support(p1,p2,cc));rows.append(row)
        for bank in ['P1_CAUSAL20','P2_SPATIAL_SPLIT']:hashes[bank+'/'+rid]=digest(folder/bank/rid/'summary.json')
    support=pd.DataFrame(rows);support.to_parquet(dest/'support.parquet',index=False)
    eligible=support[support[['general','A','B','C','D']].any(axis=1)].copy()
    n=eligible.split_group_id.nunique();folds=5 if n>=25 else 4 if n>=20 else 0
    outer=balanced_component_folds(eligible,folds,config['splits']['seed']) if folds else {}
    plan=[]
    for outer_index in range(folds):
        test=sorted(g for g,f in outer.items() if f==outer_index);train=sorted(set(outer)-set(test))
        drows=eligible[(eligible.D)&eligible.split_group_id.isin(train)]
        inner=balanced_component_folds(drows,3,config['splits']['seed']+outer_index+1) if len(drows)>=3 else {}
        plan.append({'outer_fold':outer_index,'train_groups':train,'test_groups':test,
                     'D_inner_fold_by_group':inner,'D_encoder_policy':'exclude all EEG of outer-test and clinical-inner-validation groups; other eligible outer-train groups permitted'})
    write_json(dest/'folds.json',{'outer_fold_by_group':outer,'folds':plan,'fold_count':folds,
                               'export_run':export_run,'manifest':args.manifest,'input_hashes':hashes,
                               'seed':config['splits']['seed'],'outcome_blind':True})
    summary={'stage':'S1_support_and_splits','status':'PASS','metadata_indices':len(support),'outer_groups':n,'outer_folds':folds,
             'route_support':{k:int(support.loc[support[k],'split_group_id'].nunique()) for k in ['general','A','B','C','D']},
             'route_minimum':{'general':20,'A':25,'B':20,'C':25,'D':30},
             'held_out_individual_counts_by_fold':dict(Counter(outer.values())),
             'E1_status':'SUPPORT_INSUFFICIENT','E1_reason':'bapa shared-layout metadata support16 <20 before EEG QC',
             'D_clinical_values_used_for_split':False,'export_run':export_run,'split_hash':digest(dest/'folds.json'),
             'general_block_rule':'each class spans >=8 original 30s blocks',
             'B_support_stage':'preliminary counts; training-derived common-context support still required'}
    write_json(out/'summary.json',summary);print(json.dumps(summary,indent=2))
