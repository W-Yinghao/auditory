"""Bound exact source people, update budgets and existing doubled-horizon assets."""
from __future__ import annotations
import copy
import json
from pathlib import Path
import numpy as np
from .. import core
from ..aln34 import data_inner as I, learning_budget as B, learning_budget_v2 as V
from . import support_contract as K

ROOT=Path(core.OUT)/'aln35'
FRACTIONS=(.25,.5,1.)


def read(path):return json.loads(Path(path).read_text())


def selected_sources():
    ip=read(I.PLAN);I.verify(ip);vp=read(V.PLAN);V.verify_plan(vp)
    result=[]
    for inner in ip['rows']:
        s=inner['spec']
        if s['axis']!='inner_person' or inner['seed']!=3401 or s['objective']!='NCE':continue
        if s['architecture'] not in ('lag_local_tokens','cbramod'):continue
        baseline=ip['baselines'][s['baseline_id']]
        budget=next(r for r in vp['rows'] if r['spec']['baseline_id']==s['baseline_id'])
        result.append({'inner':inner,'outer':baseline,'budget2x':budget,'split':ip['splits'][s['split_key']],
                       'inner_plan_sha256':B.sha(I.PLAN),'budget_plan_sha256':B.sha(V.PLAN),
                       'architecture':s['architecture'],'adaptation':s.get('adaptation','local'),
                       'source_execution_id':s['baseline_id']})
    assert len(result)==30 and len({s['source_execution_id'] for s in result})==30
    return sorted(result,key=lambda s:(s['architecture'],s['adaptation'],s['outer']['row']['subject_fold'],s['outer']['row']['content_fold']))


def stage_split(meta,source,stage,fraction):
    row=source['outer']['row'];sf=row['subject_fold'];inner=(sf+1)%5
    full=[p for p in meta['participants'] if p['fold']!=sf and (stage!='inner' or p['fold']!=inner)]
    chosen=[]
    for group in sorted({p['group'] for p in full}):
        chosen.extend(I.prefix([p['id'] for p in full if p['group']==group],fraction,
                              f'ALN34-20261017|people|sf{sf}|{group}'))
    ids=set(chosen);fullids={p['id'] for p in full}
    ix={i for i,p in enumerate(meta['participants']) if p['id'] in ids}
    fullix={i for i,p in enumerate(meta['participants']) if p['id'] in fullids}
    def indices(people,role):return [i for i,s in enumerate(meta['segments']) if s['p'] in people and s['role']==role and s['kind']=='ss']
    evaluation=[p['id'] for p in meta['participants'] if p['fold']==(inner if stage=='inner' else sf)]
    assert not ids&set(evaluation) and not fullids&set(evaluation)
    return {'train_ids':sorted(ids),'full_source_audio_ids':sorted(fullids),'evaluation_ids':sorted(evaluation),
            'fit_indices':indices(ix,'fit'),'es_indices':indices(ix,'es'),
            'audio_statistics_fit_indices':indices(fullix,'fit'),
            'readout_fit_cal_ids':sorted(ids),'evaluation_content':'original source-ES' if stage=='inner' else 'outer test',
            'fraction':fraction,'stage':stage,'inner_fold':inner,'outer_fold':sf,
            'audio_statistics_access':'full legal source audio fixed in 50% and100%; EEG population only is reduced'}


def update_grid(meta,split,epochs,seed,fs=128,seg_len=640,grid=3):
    """Exact inherited batch stream count, including anchor-phase RNG draws."""
    from auditory_alignment_v2.train import Batcher
    fake=Batcher.__new__(Batcher);fake.coh_segments=meta['segments'];fake.fit=split['fit_indices']
    rng=np.random.default_rng(seed);points={0:0};step=0;exposures=0
    epoch_points={round(epochs*f) for f in FRACTIONS}
    stride=max(grid,(seg_len//8)//grid*grid)
    for epoch in range(1,epochs+1):
        for batch in fake.epoch_batches(rng,32):
            rng.integers(0,max(1,stride//grid),size=len(batch))
            step+=1;exposures+=len(batch)*8
        if epoch in epoch_points:points[epoch]=step
    horizon=2*epochs*max(1,len(fake.fit)//32)
    return {'U':step,'scheduler_horizon_updates':horizon,
            'candidate_steps':[0]+[points[round(epochs*f)] for f in FRACTIONS],
            'candidate_fractions':[0.,*FRACTIONS], 'candidate_epochs':[0]+[round(epochs*f) for f in FRACTIONS],
            'full_data_anchor_exposures_to_U':exposures,'baseline_epochs':epochs,
            'horizon_rule':'original doubled epoch cosine:2E*floor(full fit segments/32), not short1x and not assumed2U'}


def inspect_reuse(source,grid):
    row=source['budget2x'];prefix=V.BASE/'ckpt'/row['experiment_id'];records=[]
    for epoch,step in zip(grid['candidate_epochs'][1:],grid['candidate_steps'][1:]):
        path=Path(str(prefix)+f'_trajectory_e{epoch:04d}.pt')
        rec={'path':str(path),'epoch':epoch,'expected_optimizer_steps':step,'exists':path.is_file()}
        if path.is_file():
            import torch
            state=torch.load(path,map_location='cpu',weights_only=True)
            assert state['code_hash']==core.code_hash(row['family_id']) and state['experiment_id']==row['experiment_id']
            assert state['optimizer_steps']==step and state['epoch']==epoch
            rec['checkpoint_sha256']=B.sha(path)
        records.append(rec)
    return {'source_row':row,'required_snapshots':records,'reusable_now':all(x['exists'] for x in records),
            'epoch0':'reconstruct exact source seed/model/head initialization and source-only statistics; no training',
            'missing_policy':'await this already registered doubled-budget dependency; never substitute short1x cosine'}


def prepare_bindings(sources):
    from auditory_alignment_v2.run import load_cohort
    metas={};output=[]
    for cf in (0,1):
        cohort=load_cohort(core.bind(next(s['outer']['row'] for s in sources if s['outer']['row']['content_fold']==cf)))
        metas[cf]=I.metadata(cohort);del cohort
    for source in sources:
        row=source['outer']['row'];meta=metas[row['content_fold']]
        item={'source':source,'metadata_sha256':K.digest(meta),'stages':{}}
        for stage in ('inner','outer'):
            full=stage_split(meta,source,stage,1.)
            budget=update_grid(meta,full,source['budget2x']['spec']['baseline_epochs'],3401,grid=core.grid_samples(128))
            parent=I.BASE/'units'/f'{source["inner"]["experiment_id"]}.json' if stage=='inner' else Path(core.OUT)/'units'/f'{row["experiment_id"]}.json'
            if parent.is_file():
                rec=read(parent);assert rec['status']=='complete' and not rec.get('truncated')
                assert rec['optimizer_steps']==budget['U'], 'actual registered update budget differs from exact metadata stream'
                budget['registered_baseline_record_sha256']=B.sha(parent)
            item['stages'][stage]={'budget':budget,'splits':{str(f):stage_split(meta,source,stage,f) for f in (.5,1.)}}
            if stage=='outer':item['outer_reuse']=inspect_reuse(source,budget)
        output.append(item)
    return output


def audit_cli():
    import os
    assert os.environ.get('SLURM_JOB_ID')
    chosen=selected_sources();bindings=prepare_bindings(chosen)
    target=ROOT/'matched_updates_v1/asset_audit.json'
    B.write(target,{'status':'pass','job':os.environ['SLURM_JOB_ID'],'bindings':bindings,
                    'existing_outer_trajectories_reusable':sum(b['outer_reuse']['reusable_now'] for b in bindings),
                    'full_scope_sources':len(bindings),'no_checkpoint_training':True})
    print('Asset audit',target,flush=True)


if __name__=='__main__':audit_cli()
