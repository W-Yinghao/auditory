"""Exact-update NCE trajectories with legal source populations and fixed states.

The model/batcher/objective/optimizer construction follows the registered
full-onestep and aligned-local recipes. Only source population and stopping
update change. Existing long-horizon outer/full checkpoints can be loaded.
"""
from __future__ import annotations
import gc
import os
from pathlib import Path
import time
import numpy as np
import torch

from auditory_alignment.train import Objective
from auditory_alignment_v2.audio_targets import build_head,target_stats
from auditory_alignment_v2.foundation_adapter import Backbone
from auditory_alignment_v2.run import load_cohort
from auditory_alignment_v2.temporal import build_encoder
from auditory_alignment_v2.train import N_SEL
from .. import core,fm_aligned,fm_dense,local_support
from ..aln34 import adaptation_policy as D,episode_training as E,learning_budget as B
from . import support_contract as K,selection_assets as A


class Context:
    def __init__(self,unit,device='cuda'):
        self.unit=unit;self.row=unit['binding']['source']['outer']['row'];self.split=unit['split'];self.dev=torch.device(device)
        bound=core.bind(self.row);self.coh=load_cohort(bound);self.grid=core.grid_samples(self.coh.fs)
        assert K.digest(A.I.metadata(self.coh))==unit['binding']['metadata_sha256']
        self.local=self.row['spec']['architecture']=='lag_local_tokens';torch.manual_seed(3401)
        if self.local:
            self.bt=local_support.batcher_for('aligned1000')(self.coh,bound['spec'],bound,self.dev,self.grid)
            self.model=build_encoder('lag_local_tokens',self.coh.n_ch,32,self.bt.W,self.coh.fs).to(self.dev)
        else:
            bb=Backbone('cbramod','dtu',self.row['spec']['adaptation'],self.coh.fs)
            self.bt=fm_aligned.AlignedBatcher(self.coh,bound['spec'],bound,self.dev,self.grid)
            self.model=fm_aligned.AlignedFM(bb,32).to(self.dev)
        # Target coordinate statistics are identical for 50/100% EEG people and
        # use only the legal full source side of this inner/outer stage.
        self.bt.fit=list(self.split['audio_statistics_fit_indices'])
        stats=target_stats(self.bt,np.random.default_rng(3401+5))
        self.head=build_head('fixed_features',self.bt.audio_dim,32,'dtu',stats).to(self.dev)
        self.bt.fit=list(self.split['fit_indices']);self.bt.es=list(self.split['es_indices'])
        self.bt.train_p={i for i,p in enumerate(self.coh.participants) if p['id'] in self.split['train_ids']}
        assert not self.bt.selection and set(self.split['train_ids']).isdisjoint(self.split['evaluation_ids'])
        if self.local:
            self.groups=[{'params':[p for m in (self.model,self.head) for p in m.parameters() if p.requires_grad], 'lr':1e-3,'name':'local'}]
        else:
            self.groups=[{'params':[p for p in ps if p.requires_grad], 'lr':float(self.row['spec']['lr_backbone']), 'name':f'{kind}{i}'}
                         for kind,i,ps in fm_dense.block_groups(self.model.bb) if any(p.requires_grad for p in ps)]
            self.groups.append({'params':list(self.model.readout.parameters()),'lr':float(self.row['spec']['lr_head']),'name':'readout'})
        self.optimizer=torch.optim.AdamW(self.groups,weight_decay=1e-4)
        self.params=[p for g in self.groups for p in g['params']]
        self.scheduler=torch.optim.lr_scheduler.CosineAnnealingLR(self.optimizer,T_max=unit['budget']['scheduler_horizon_updates'])
        batch=next(self.bt.epoch_batches(np.random.default_rng(3401+99),32))
        rows=self.rows(batch,np.random.default_rng(3401+98))
        with torch.no_grad():u,v,keys=self.forward_rows(rows)
        self.objective=Objective({'objective':'NCE','config':{'temperature':.1,'bandwidth_multiplier':1.,'fmca_relative_ridge':1e-3}},u,v)
        rng=np.random.default_rng(12345);batches=[]
        while len(batches)<N_SEL:
            got=[b for b,_ in zip(self.bt.epoch_batches(rng,32,self.bt.es),range(N_SEL-len(batches)))]
            if not got:break
            batches+=got
        self.es_sets=[(self.rows(b,np.random.default_rng(k)),self.rows(b,np.random.default_rng(k),roll=True)) for k,b in enumerate(batches)]
        self.initial_sha=self.state_digest()

    def rows(self,batch,rng,roll=False):
        return self.bt.rows(batch,rng,roll=roll) if self.local else self.bt.dense_rows(batch,rng,anchors=8,roll=roll)

    def forward_rows(self,rows):
        if self.local:
            e,a,keys=rows;return self.model(self.bt.patches(e)),self.head(self.bt.audio(a)),keys
        e,t,a,keys=rows;return self.model(self.bt.windows(e,t)),self.head(self.bt.audio(a)),keys

    def state_digest(self):
        import hashlib
        h=hashlib.sha256()
        for name,module in (('model',self.model),('head',self.head)):
            for key,value in module.state_dict().items():
                h.update((name+'/'+key).encode());h.update(value.detach().cpu().numpy().tobytes())
        return h.hexdigest()

    def state(self):return {'model':E.cpu_state(self.model),'head':E.cpu_state(self.head)}

    def load(self,state):
        self.model.load_state_dict(state['model'] if 'model' in state else state['enc'],strict=True)
        if 'head' in state:self.head.load_state_dict(state['head'],strict=True)

    @torch.no_grad()
    def gain(self):
        self.model.eval();self.head.eval();truth=[];wrong=[]
        for rows,rr in self.es_sets:
            u,v,keys=self.forward_rows(rows);loss,_=self.objective(u,v,keys=keys)
            uw,vw,kw=self.forward_rows(rr);mismatch,_=self.objective(uw,vw,keys=kw)
            truth.append(float(loss));wrong.append(float(mismatch))
        return {'source_ES_true_nats':float(np.mean(truth)),'source_ES_wrong_nats':float(np.mean(wrong)),
                'inherited_gain_selection_score':float(np.mean(truth)-np.mean(wrong)),
                'source_ES_fixed_batches':len(truth),'role':'source training identities only'}

    def evaluate(self,probe=False):
        from auditory_alignment import evaluate as ev
        self.model.eval();self.head.eval()
        bundle=D.Bundle(self.row,{'row':self.row},self.coh,self.bt,self.model,self.head,self.grid,self.local)
        role='es' if self.unit['stage']=='inner' else 'test';pool=bundle.eval_pool(role);uid,v,a=pool
        people=[i for i,p in enumerate(self.coh.participants) if p['id'] in self.split['evaluation_ids']]
        if probe:people=people[:1]
        per={}
        for person in people:
            identity=self.coh.participants[person]['id'];query=bundle.items(person,role)
            if not query:per[identity]={'status':'no_query'};continue
            u=bundle.reps.u([s['e0'] for s in query]);own=np.asarray([uid[s['uid']] for s in query])
            values={}
            for mode in ('native','unified'):
                scores=bundle.readout.scores(u,v,a,mode);true=ev._metrics(scores,own,bundle.readout.tau[mode])
                wrong=ev._metrics(np.roll(scores,1,axis=0),own,bundle.readout.tau[mode])
                values[mode]={'nll_bits':true['logloss_bits'],'wrong_nll_bits':wrong['logloss_bits'],
                              'mismatch_gain_bits':wrong['logloss_bits']-true['logloss_bits'],
                              'top1':true['top1'],'rank_pct':true['rank_pct'],'n_query':len(query),'n_candidates':len(uid)}
            per[identity]={'status':'complete','group':self.coh.participants[person]['group'],'metrics':values,
                           'query_hash':K.digest([{k:s[k] for k in ('e0','s0','uid')} for s in query]),
                           'candidate_hash':K.digest(list(uid)), 'personal_adaptation_steps':0}
        return {'per_participant':per,'readouts':{'tau':bundle.readout.tau,'unified_alpha':float(bundle.readout.alpha_uni)},
                'fit_ids':self.split['train_ids'],'calibration_ids':self.split['train_ids'],
                'evaluation_ids':self.split['evaluation_ids'],'evaluation_content':self.split['evaluation_content'],
                'selection_level':'whole task-specific model/readout/statistics excludes inner identities' if self.unit['stage']=='inner' else 'held-out outer people/content'}


def inference_preserving_rng(context,probe=False):
    cpu=torch.get_rng_state();cuda=torch.cuda.get_rng_state_all() if torch.cuda.is_available() else []
    try:return {'gain':context.gain(),'evaluation':context.evaluate(probe)}
    finally:
        torch.set_rng_state(cpu)
        if cuda:torch.cuda.set_rng_state_all(cuda)


def train(context,dest,plan_sha,probe=False):
    """Repeat the inherited sampler to the common U; retain exact RNG on resume."""
    unit=context.unit;budget=unit['budget'];U=budget['U'];points=budget['candidate_steps']
    dest.mkdir(parents=True,exist_ok=True,mode=0o700);resume=dest/'resume.pt';complete=dest/'trajectory.json'
    if complete.exists():
        result=A.read(complete);assert result['plan_sha256']==plan_sha and result['probe']==probe;return result
    model,head=context.model,context.head;rng=np.random.default_rng(3401)
    ledger={'encoder_updates':0,'anchor_exposures':0,'segment_exposures':0,'per_source_person_exposures':{},
            'unique_audio_anchor_keys':set(),'trainable_parameters':sum(p.numel() for p in context.params),
            'gradient_norm_max':0.,'nonfinite_steps':0,'lr_first':[g['lr'] for g in context.optimizer.param_groups],
            'sampling_sha256':'','initial_model_head_sha256':context.initial_sha}
    step=0;pending=[];epoch=0;captures={};began=time.time()
    if resume.exists():
        state=torch.load(resume,map_location=context.dev,weights_only=False)
        assert state['plan_sha256']==plan_sha and state['probe']==probe
        context.load(state);context.optimizer.load_state_dict(state['optimizer']);context.scheduler.load_state_dict(state['scheduler'])
        rng.bit_generator.state=state['rng'];torch.set_rng_state(state['torch_rng'].cpu())
        if state['cuda_rng']:torch.cuda.set_rng_state_all(state['cuda_rng'])
        ledger=state['ledger'];step=ledger['encoder_updates'];pending=state['pending'];epoch=state['epoch'];captures=state['captures']
    def snapshot():
        checkpoint=dest/f'update{step:08d}.pt'
        E.atomic_torch(checkpoint,{**context.state(),'optimizer_steps':step,'plan_sha256':plan_sha,
                                   'initial_sha256':context.initial_sha,'source_unit':unit['id']})
        metrics=inference_preserving_rng(context,probe)
        captures[str(step)]={'optimizer_steps':step,'checkpoint_sha256':B.sha(checkpoint),'checkpoint':str(checkpoint),**metrics}
        B.write(dest/f'update{step:08d}.json',captures[str(step)])
    if step==0 and '0' not in captures:snapshot()
    while step<U:
        if not pending:
            pending=list(context.bt.epoch_batches(rng,32));epoch+=1
            if not pending:raise ValueError('empty source training stream')
        batch=pending.pop(0);rows=context.rows(batch,rng)
        model.train();head.train();u,v,keys=context.forward_rows(rows)
        loss,_=context.objective(u,v,keys=keys)
        context.optimizer.zero_grad();loss.backward();gn=torch.nn.utils.clip_grad_norm_(context.params,5.)
        if not torch.isfinite(loss) or not torch.isfinite(gn):raise FloatingPointError('nonfinite fixed-budget update; no skipped-update substitution')
        context.optimizer.step();context.scheduler.step();step+=1
        ledger['encoder_updates']=step;ledger['anchor_exposures']+=len(keys);ledger['segment_exposures']+=len(batch)
        ledger['unique_audio_anchor_keys'].update(map(int,keys.detach().cpu().tolist()))
        for index in batch:
            person=context.coh.participants[context.coh.segments[index]['p']]['id']
            ledger['per_source_person_exposures'][person]=ledger['per_source_person_exposures'].get(person,0)+8
        ledger['gradient_norm_max']=max(ledger['gradient_norm_max'],float(gn))
        ledger['sampling_sha256']=K.digest([ledger['sampling_sha256'],[int(i) for i in batch],keys.detach().cpu().tolist()])
        if step in points:snapshot()
        if step%100==0 or step in points:
            E.atomic_torch(resume,{**context.state(),'optimizer':context.optimizer.state_dict(),'scheduler':context.scheduler.state_dict(),
                'rng':rng.bit_generator.state,'torch_rng':torch.get_rng_state(),'cuda_rng':torch.cuda.get_rng_state_all(),
                'pending':pending,'epoch':epoch,'ledger':ledger,'captures':captures,'plan_sha256':plan_sha,'probe':probe})
    assert sorted(map(int,captures))==points
    ledger['unique_audio_anchor_count']=len(ledger.pop('unique_audio_anchor_keys'))
    ledger.update(seconds=time.time()-began,lr_after_U=[g['lr'] for g in context.optimizer.param_groups],
                  elapsed_sampler_epochs=epoch,actual_source_people=len(context.split['train_ids']),
                  source_ES_people=len(context.split['readout_fit_cal_ids']),gpu_peak_mb=torch.cuda.max_memory_allocated()/2**20,
                  interpretation='same actual updates and LR horizon; sample repetition/person coverage vary, no equal FLOPs claim')
    result={'status':'complete','plan_sha256':plan_sha,'probe':probe,'unit':unit,'budget':budget,'ledger':ledger,'candidates':captures}
    B.write(complete,result);return result


def reuse_outer(context,dest,plan_sha,probe=False):
    """No source training: exact existing 2x-horizon states plus reconstructed0."""
    assert context.unit['stage']=='outer' and context.unit['fraction']==1.
    binding=context.unit['binding'];dest.mkdir(parents=True,exist_ok=True,mode=0o700);captures={}
    for index,step in enumerate(context.unit['budget']['candidate_steps']):
        if index:
            asset=binding['outer_reuse']['required_snapshots'][index-1];path=Path(asset['path'])
            state=torch.load(path,map_location=context.dev,weights_only=True)
            assert state['optimizer_steps']==step and state['experiment_id']==binding['source']['budget2x']['experiment_id']
            assert state['code_hash']==core.code_hash(binding['source']['budget2x']['family_id'])
            if asset.get('checkpoint_sha256'):assert B.sha(path)==asset['checkpoint_sha256']
            context.load(state);checkpoint={'checkpoint':str(path),'checkpoint_sha256':B.sha(path),'reused':True}
        else:
            path=dest/'reconstructed_update0.pt';E.atomic_torch(path,{**context.state(),'optimizer_steps':0,'plan_sha256':plan_sha})
            checkpoint={'checkpoint':str(path),'checkpoint_sha256':B.sha(path),'reused':False,'reconstruction_no_training':True}
        captures[str(step)]={'optimizer_steps':step,**checkpoint,**inference_preserving_rng(context,probe)}
    result={'status':'complete','plan_sha256':plan_sha,'probe':probe,'unit':context.unit,'budget':context.unit['budget'],
            'ledger':{'new_encoder_updates':0,'reused_outer_full_doubled_horizon':True,
                      'initial_model_head_sha256':context.initial_sha,'actual_source_people':len(context.split['train_ids'])},'candidates':captures}
    B.write(dest/'trajectory.json',result);return result
