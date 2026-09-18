"""Resolve only executed v2.1 receipts; private source locators never published."""
import json
from pathlib import Path
import subprocess
import numpy as np
import pandas as pd
from .runtime import digest,write_json,require_slurm


def inspect(root,private,public,report,config,args):
    require_slurm()
    base=root/'private/auditory_v21/n2_design_001'
    done=json.loads((base/'completion.json').read_text())
    assert done['status']=='N2_METADATA_DESIGN_COMPLETE'
    historical=json.loads((base/'input_hashes.json').read_text())
    plan_path=root/'private/auditory5_v1/jobs/plan_001/plan.json'
    plan=json.loads(plan_path.read_text())
    files={
        'matched_bag_members':base/'matched_bags.parquet',
        'matched_bag_history':base/'matched_h_bag_metadata.parquet',
        'candidate_half_support':base/'candidate_half_support.parquet',
        'common_cell_support':base/'common_cell_support.parquet',
        'design_manifest':base/'design_manifest.json','support_manifest':base/'support_manifest.json',
        'legacy_outer_folds':root/'private/auditory5_v1/splits/splits_001/folds.json',
        'full_event_history':root/'private/auditory_next_v2/S1_support_004/full_event_history.parquet',
        'legacy_representation_plan':plan_path,
        'legacy_representation_support':root/'private/auditory5_v1/splits/splits_001/support.parquet',
        'legacy_scope_registry':root/'private/auditory_next_v2/S0_001/feature_scope_registry.json',
    }
    entries={}
    schemas={}
    for role,p in files.items():
        h=digest(p)
        if str(p) in historical and h!=historical[str(p)]:raise ValueError('UPSTREAM_INPUT_HASH_MISMATCH:'+role)
        entries[role]=dict(path=str(p),sha256=h,bytes=p.stat().st_size)
        if p.suffix=='.parquet':
            import pyarrow.parquet as pq
            pf=pq.ParquetFile(p);schemas[role]=dict(rows=pf.metadata.num_rows,columns=pf.schema_arrow.names)
    bags=pd.read_parquet(files['matched_bag_members'])
    support=pd.read_parquet(files['candidate_half_support'])
    both=support.groupby('candidate_id')['eligible'].agg(lambda x:len(x)==2 and bool(x.all()))
    candidates=set(both.index[both].astype(str))
    selected=bags[bags.candidate_id.astype(str).isin(candidates)].copy()
    assert selected.trial_id.is_unique
    selected.to_parquet(private/'members_unjoined.parquet',index=False)
    sources=[]
    # Inspect only legacy all-channel outer representations relevant to P0.
    for task in plan['tasks']:
        if task['stage']!='outer' or task['branch']!='all':continue
        folder=plan_path.parent/'outputs'/task['name']
        paths={n:dict(path=str(folder/n),sha256=digest(folder/n)) for n in ('task.json','completion.json','features.npz','feature_rows.parquet','probe_metadata.json')}
        if (folder/'encoder.pt').exists():paths['encoder.pt']=dict(path=str(folder/'encoder.pt'),sha256=digest(folder/'encoder.pt'))
        sources.append(dict(task=task,files=paths))
    export_root=root/'private/auditory5_v1/data'/plan['export_run']/'P1_CAUSAL20'
    exports=[]
    for record in sorted(selected.record_id.astype(str).unique()):
        folder=export_root/record
        fs={}
        for p in sorted(folder.iterdir()):
            if p.name in ('all.npy','events.parquet') or p.suffix=='.json':fs[p.name]=dict(path=str(p),sha256=digest(p),bytes=p.stat().st_size)
        arr=np.load(folder/'all.npy',mmap_mode='r')
        exports.append(dict(record_id=record,files=fs,shape=list(arr.shape),dtype=str(arr.dtype)))
    gitroot=root.parent/'auditory_github'
    head=subprocess.check_output(['git','-C',str(gitroot),'rev-parse','HEAD'],text=True).strip()
    relevant=subprocess.check_output(['git','-C',str(gitroot),'diff',config['baseline']['commit'],'--name-only','--','auditory5','auditory_v21','configs'],text=True).splitlines()
    write_json(private/'source_registry.json',dict(status='RESOLVED',sources=entries,legacy_features=sources,processed_epochs=exports,plan_source_snapshot=plan['source_snapshot'],baseline_commit=config['baseline']['commit'],observed_head=head,relevant_git_changes=relevant))
    write_json(private/'schemas.json',schemas)
    write_json(public/'source_hashes_public.json',{key:value['sha256'] for key,value in entries.items()})
    summary=dict(status='SOURCE_REGISTRY_RESOLVED',new_model_fits=0,clinical_values_read=False,
        candidate_design_denominator=int(support.candidate_id.nunique()),nonempty_bag_candidates=int(bags.candidate_id.nunique()),
        both_half_candidates=len(candidates),identity_groups=int(selected.split_group_id.nunique()),
        matched_bags=int(selected.bag_id.nunique()),matched_trials=len(selected),
        legacy_feature_lanes=len(sources),processed_records=len(exports),
        exported_channel_counts=sorted(set(e['shape'][1] for e in exports)),baseline_head_matches=head==config['baseline']['commit'],
        relevant_git_changes=relevant)
    write_json(public/'input_schemas.json',schemas)
    (report/'SOURCE_REGISTRY.md').write_text('# v3来源接入\n\n从已完成的v2.1匹配袋回执与旧表征计划解析实际输入，未重新装袋或读取量表。全部实际来源及哈希在private。下一步按元数据检查成员、分折、作用域和R3配对支持；本回执不授权真实模型拟合。\n')
    return summary
