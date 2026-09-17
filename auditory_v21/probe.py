"""Metadata shape/integrity probe; no EEG arrays and no model evaluation."""
import json
import subprocess
import numpy as np
import pandas as pd
from .runtime import digest,write_json


def run(root,private,public,report,config):
    release=root.parent/'auditory_github'
    commit=subprocess.check_output(['git','-C',str(release),'rev-parse','HEAD'],text=True).strip()
    if commit!=config['baseline_commit']:raise ValueError('BASELINE_COMMIT_MISMATCH')
    audit=pd.read_csv(root/'results/auditory_next_v2/public_audit_002/audited_artifact_hashes.csv')
    for row in audit.itertuples():
        if digest(root/row.artifact)!=row.sha256:raise ValueError('FINAL_V2_ARTIFACT_CHANGED')
    history=root/'private/auditory_next_v2/S1_support_004/full_event_history.parquet'
    df=pd.read_parquet(history)
    selected=df[df.accepted & df.history_chain_complete & df.stimulus_local_id.isin([0,1])]
    groups=selected.groupby('split_group_id').size()
    rates=selected.groupby('split_group_id').stimulus_local_id.mean()
    schemas={}
    for rel in ('private/auditory_next_v2/S1_support_004/full_event_history.parquet',
                'private/auditory_next_v2/S1_support_004/N2_k8_bags.parquet',
                'private/auditory_next_v2/A2_core_001/candidate_statistics.parquet',
                'private/auditory_next_v2/N1_core_001/candidate_losses.parquet',
                'private/auditory_next_v2/N3_core_001/candidate_losses.parquet'):
        p=root/rel
        if p.exists():
            table=pd.read_parquet(p)
            schemas[rel]=dict(columns={c:str(t) for c,t in table.dtypes.items()},rows=len(table),sha256=digest(p))
        else:schemas[rel]=dict(status='PATH_NOT_PRESENT')
    for lane in ('A2_core_001','N1_core_001','N2_core_001','N3_core_001'):
        folder=root/'private/auditory_next_v2'/lane
        schemas[lane+'_top_level_files']=[p.name for p in sorted(folder.iterdir()) if p.is_file()]
    write_json(private/'schemas.json',schemas)
    summary=dict(status='PASS',baseline_commit=commit,final_artifacts_verified=len(audit),
        history_records=int(df.record_id.nunique()),history_groups=int(df.split_group_id.nunique()),
        accepted_complete_history_trials=len(selected),
        samples_per_group_quantiles=np.quantile(groups,[0,.25,.5,.75,1]).tolist(),
        positive_fraction_per_group_quantiles=np.quantile(rates,[0,.25,.5,.75,1]).tolist(),
        dimensions_to_match=[64,400],new_head_fits=0,new_encoder_fits=0)
    write_json(private/'input_hashes.json',{str(history):digest(history)})
    (report/'PROBE.md').write_text('Metadata-only support and immutable final-artifact verification. No participant predictions, EEG features or fitted models were evaluated.\n')
    return summary
