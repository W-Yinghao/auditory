"""CPU-only attribution from existing compatible production fusion caches."""
from __future__ import annotations
import argparse
from datetime import datetime
from functools import lru_cache
import hashlib
import json
import os
from pathlib import Path
import sys
import numpy as np
from .. import core
from ..aln34 import data_inner as I, learning_budget as B, strong_fusion as F
from . import fusion_math as M

ROOT=Path(core.REPO);BASE=Path(core.OUT)/'aln35/fusion'
RESULTS=ROOT/'results/auditory_alignment_v3/aln35/fusion'
NOTE=ROOT/'docs/auditory_alignment_v3/aln35/FUSION_ATTRIBUTION_DESIGN.md'
PLAN=BASE/'plan.json'
NEXT={3401:3407,3407:3413,3413:3401}
PACKAGE=ROOT/'AUDITORY_ALN3_SERVER_PACKAGE_v3_5_20261018'
read=lambda p:json.loads(Path(p).read_text())
digest=lambda value:hashlib.sha256(B.dumps(value).encode()).hexdigest()

@lru_cache(None)
def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(8<<20),b''):h.update(block)
    return h.hexdigest()

def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x') as f:json.dump(value,f,indent=2,allow_nan=False);f.write('\n')

def sources():
    return {str(p.relative_to(ROOT)):sha(str(p)) for p in [Path(__file__),Path(M.__file__),Path(__file__).with_name('fusion_report.py'),NOTE,F.PLAN,I.PLAN,Path(F.__file__),Path(I.__file__)]}

def make_plan():
    I.register();old=read(F.PLAN);F.verify(old)
    body={'version':'S35_FUSION_ATTRIBUTION_v1','sources':sources(),'rows':old['rows'],
          'required_seeds':list(NEXT),'required_folds':['content_0','content_1'],
          'permutation_seeds':M.PERM_SEEDS,'ensemble_rule':NEXT,
          'families':{'four':['cb_direct','cb_temperature','cb_shrink','cb_repeated'],
                      'three':['cb_direct','cb_temperature','cb_shrink']}}
    # JSON canonicalization also normalizes tuple and integer dictionary keys.
    body=json.loads(json.dumps(body))
    if PLAN.exists():assert read(PLAN)==body
    else:write(PLAN,body);PLAN.chmod(0o444)
    return body

def metadata(plan):
    from auditory_alignment_v2.run import load_cohort
    out={}
    for cf in (0,1):
        row=next(u['models']['local']['outer']['row'] for u in plan['rows'] if u['content_fold']==cf)
        coh=load_cohort(core.bind(row));value=I.metadata(coh)
        assert digest(value)==read(I.PLAN)['metadata_sha256'][str(cf)]
        out[cf]=value;del coh
    return out

def cache_index():
    index={}
    for p in sorted((F.STORE/'cache').glob('*/meta.json')):
        meta=read(p);sig=meta['signature']
        if sig['probe']:continue
        key=sig['source']['experiment_id']
        assert key not in index,'ambiguous production cache'
        index[key]=(p,meta)
    return index

def load(row,stage,index,meta):
    eid=row['experiment_id']
    if eid not in index:raise FileNotFoundError('missing existing production cache:'+eid)
    path,record=index[eid];sig=record['signature'];root=I.BASE if stage=='inner' else Path(core.OUT)
    assert sig['source']==row and not sig['probe']
    assert sig['fusion_source_sha256']==sha(str(Path(F.__file__)))
    assert sig['inner_plan_sha256']==sha(str(I.PLAN))
    assert sig['record_sha256']==sha(str(root/'units'/f'{eid}.json'))
    assert sig['checkpoint_sha256']==sha(str(root/'ckpt'/f'{eid}_best.pt'))
    npz=path.parent/'arrays.npz';assert record['arrays_sha256']==sha(str(npz))
    with np.load(npz,allow_pickle=False) as z:
        a={k:z[k] for k in ('query_e0','query_people','query_own','query_direct_native','query_direct_unified')}
    role='es' if stage=='inner' else 'test';assert record['role']==role
    segs=meta['segments'];parts=meta['participants'];pool=[];seen=set()
    eligible={}
    for s in segs:
        if s['kind']!='ss' or s['role']!=role:continue
        if s['uid'] not in seen:seen.add(s['uid']);pool.append(s['uid'])
        key=(parts[s['p']]['id'],s['e0']);assert key not in eligible
        eligible[key]=s
    poolhash=digest(pool);ids=[]
    for p,e0,own in zip(a['query_people'],a['query_e0'],a['query_own']):
        s=eligible[(str(p),int(e0))];assert pool[int(own)]==s['uid']
        ids.append(f'dtu/cf{row["content_fold"]}/{p}/e0={e0}/uid={s["uid"]}')
    assert len(ids)==len(set(ids)) and len(pool)==a['query_direct_native'].shape[1]
    actual=set(a['query_people'].tolist());assert actual==set(record['evaluation_ids'])
    assert not actual&set(record['train_ids'])
    if stage=='inner':
        split=read(I.PLAN)['splits'][row['spec']['split_key']]
        assert set(record['train_ids'])==set(split['train_ids']) and actual==set(split['inner_ids'])
    else:assert actual=={p['id'] for p in parts if p['fold']==row['subject_fold']}
    return dict(arrays=a,provenance=record,query_ids=ids,pool_ids=pool,pool_hash=poolhash,cache=str(path))

def aligned(a,b):
    assert a['query_ids']==b['query_ids'] and a['pool_ids']==b['pool_ids']
    for k in ('query_e0','query_people','query_own'):assert np.array_equal(a['arrays'][k],b['arrays'][k]),k

def evaluate(unit,paired,index,meta):
    data={};missing_ensemble=[]
    for stage in ('inner','outer'):
        data[stage]={}
        for arm in ('local','cb_pre'):
            info=unit['models'][arm];row=info['inner'] if stage=='inner' else info['outer']['row']
            data[stage][arm]=load(row,stage,index,meta)
        aligned(data[stage]['local'],data[stage]['cb_pre'])
        info=paired['models']['cb_pre'];row=info['inner'] if stage=='inner' else info['outer']['row']
        try:
            data[stage]['repeated']=load(row,stage,index,meta)
            aligned(data[stage]['cb_pre'],data[stage]['repeated'])
        except (FileNotFoundError,AssertionError) as exc:
            missing_ensemble.append({'stage':stage,'reason':str(exc)})
    include=not missing_ensemble
    result={'id':unit['id'],'seed':unit['seed'],'subject_fold':unit['subject_fold'],'content_fold':unit['content_fold'],
            'ensemble_status':'available' if include else 'not_available','ensemble_missing':missing_ensemble,'modes':{},
            'provenance':{stage:{arm:{k:v for k,v in d.items() if k!='arrays'} for arm,d in value.items()} for stage,value in data.items()}}
    for mode in ('native','unified'):
        sets={};probs={}
        for stage in ('inner','outer'):
            probs[stage]={arm:M.probability(d['arrays']['query_direct_'+mode]) for arm,d in data[stage].items()}
            sets[stage]=M.candidate_sets(probs[stage]['local'],probs[stage]['cb_pre'],probs[stage].get('repeated') if include else None)
        inn=data['inner']['local'];out=data['outer']['local'];ia=inn['arrays'];oa=out['arrays']
        choices={};pred={}
        for name,candidates in sets['inner'].items():
            selected,risks=M.select(candidates,ia['query_own'],ia['query_people'])
            choices[name]={'selected':selected,'inner_risk':risks}
            pred[name]=M.metrics(sets['outer'][name][selected],oa['query_own'],probs['outer']['cb_pre'])
        coverage={};permuted=[]
        for seed in M.PERM_SEEDS:
            perms={};covers={}
            for stage,d in [('inner',inn),('outer',out)]:
                perms[stage],covers[stage]=M.derangement(d['query_ids'],d['arrays']['query_people'],seed,d['provenance']['role'],d['pool_hash'])
            coverage[str(seed)]=covers
            im=perms['inner']>=0;om=perms['outer']>=0
            if not im.any() or not om.any():continue
            candidates={w:w*probs['inner']['local'][perms['inner'][im]]+(1-w)*probs['inner']['cb_pre'][im] for w in M.WEIGHTS}
            selected,risks=M.select(candidates,ia['query_own'][im],ia['query_people'][im])
            p=selected*probs['outer']['local'][perms['outer'][om]]+(1-selected)*probs['outer']['cb_pre'][om]
            met=M.metrics(p,oa['query_own'][om],probs['outer']['cb_pre'][om])
            permuted.append({'seed':seed,'selected_weight':selected,'inner_risk':risks,'outer_indices':np.flatnonzero(om).tolist(),
                             'metrics':{k:v.tolist() for k,v in met.items()}})
        per={}
        for pid in sorted(set(oa['query_people'])):
            mask=oa['query_people']==pid
            per[str(pid)]={'group':out['provenance']['groups'][str(pid)],'n_query':int(mask.sum()),
                'query_ids':[q for q,take in zip(out['query_ids'],mask) if take],
                'conditions':{name:{k:float(v[mask].mean()) for k,v in met.items()} for name,met in pred.items()}}
        result['modes'][mode]={'choices':choices,'per_person':per,'query_metrics':{name:{k:v.tolist() for k,v in met.items()} for name,met in pred.items()},
                               'permutation_coverage':coverage,'permutations':permuted,
                               'extra_model_cost':{'actual_mix':2,'temperature_or_shrink':1,'repeated_cb':2 if include else None}}
    result.update(status='complete',plan_sha256=sha(str(PLAN)),job=os.environ['SLURM_JOB_ID'])
    return result

def main():
    assert os.environ.get('SLURM_JOB_ID') and not os.environ.get('CUDA_VISIBLE_DEVICES','').strip().isdigit()
    ap=argparse.ArgumentParser();ap.add_argument('--make-plan',action='store_true');args=ap.parse_args()
    plan=make_plan();assert plan['sources']==sources()
    if args.make_plan:return
    meta=metadata(plan);index=cache_index();by={(r['seed'],r['subject_fold'],r['content_fold']):r for r in plan['rows']}
    completed=[];missing=[]
    for unit in plan['rows']:
        dest=BASE/'units'/f'{unit["id"]}.json'
        augment=BASE/'units'/f'{unit["id"]}_ensemble.json'
        if augment.exists():dest=augment
        if dest.exists():
            saved=read(dest);assert saved['plan_sha256']==sha(str(PLAN))
            pair=by[(NEXT[unit['seed']],unit['subject_fold'],unit['content_fold'])]['models']['cb_pre']
            if saved['ensemble_status']=='available' or not all(r['experiment_id'] in index for r in (pair['inner'],pair['outer']['row'])):
                completed.append(saved);continue
            dest=augment
        pair=by[(NEXT[unit['seed']],unit['subject_fold'],unit['content_fold'])]
        try:value=evaluate(unit,pair,index,meta[unit['content_fold']])
        except FileNotFoundError as exc:
            missing.append({'id':unit['id'],'reason':str(exc)});continue
        write(dest,value);completed.append(value)
        print(unit['id'],'complete; ensemble',value['ensemble_status'],flush=True)
    from .fusion_report import report
    report(plan,completed,missing,meta)

if __name__=='__main__':main()
