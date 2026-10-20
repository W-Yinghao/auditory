"""Frozen-score temporal-order sensitivity; CPU only, no model fitting."""
from __future__ import annotations
from collections import defaultdict
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import sys
import numpy as np
from auditory_alignment import data
from .. import core,run_attention
from ..aln34 import attention_transfer as T,attention_order as AO,learning_budget as B

ROOT=Path(core.REPO);BASE=Path(core.OUT)/'aln35/attention'
RESULTS=ROOT/'results/auditory_alignment_v3/aln35/attention'
NOTE=ROOT/'docs/auditory_alignment_v3/aln35/ATTENTION_ORDER_DESIGN.md'
PLAN=BASE/'plan.json';PACKAGE=ROOT/'AUDITORY_ALN3_SERVER_PACKAGE_v3_5_20261018'
read=lambda p:json.loads(Path(p).read_text())
digest=lambda x:hashlib.sha256(B.dumps(x).encode()).hexdigest()

def write(p,v):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x') as f:json.dump(v,f,indent=2,allow_nan=False);f.write('\n')

def permutations(x,ids):
    assert x.ndim==2 and x.shape[1] in (2,4) and len(x)==len(ids)
    out=x.copy()
    for i,ident in enumerate(ids):
        seed=int(hashlib.sha256(f'351620|{ident}'.encode()).hexdigest()[:16],16)
        out[i]=x[i,np.random.default_rng(seed).permutation(x.shape[1])]
    assert np.array_equal(np.sort(out,axis=1),np.sort(x,axis=1))
    return out

def ordered_logits(fits,name,x,changed):
    assert np.allclose(x.mean(1),changed.mean(1),rtol=1e-14,atol=1e-14)
    return T.logits(fits,name,x if name=='mean' else changed)

def expected_rosters():
    import csv
    _,fau=data.fau_panel()
    part=Path(data.PUB)/'dtu_snhl/ds-eeg-snhl/ds-eeg-snhl/participants.tsv'
    with part.open() as f:groups={r['participant_id']:r['hearing_status'] for r in csv.DictReader(f,delimiter='\t')}
    ids=sorted(p.stem for p in (ROOT/'private/auditory_c3/public/dtu_v2').glob('*.json'))
    dtu={pid:groups[pid] for pid in ids}
    assert len(fau)==67 and len(dtu)==44
    return {'fau':{pid:v[0] for pid,v in fau.items()},'dtu':dtu}

def make_plan():
    old=read(T.PLAN);T.verify(old)
    files=[Path(__file__),NOTE,Path(T.__file__),Path(AO.__file__),Path(data.__file__),Path(run_attention.__file__),T.PLAN]
    body={'version':'S35_ATTENTION_ORDER_v1','sources':{str(p.relative_to(ROOT)):B.sha(p) for p in files},
          'rows':old['rows'],'expected':expected_rosters(),'seconds':[10,20],
          'permutation_seed':351620,'bootstrap_seed':351621,'bootstrap_B':4000,
          'segment_samples':640,'source_loader_fs':128,'interval_method':'fixed-original-SE max-|z*|'}
    if PLAN.exists():assert read(PLAN)==body
    else:write(PLAN,body);PLAN.chmod(0o444)
    return body

def evaluate(unit,record,path,plan):
    assert record['unit']==unit and record['status']=='complete' and not record['probe']
    assert record['plan_sha256']==B.sha(T.PLAN)
    row=unit['source']['row'];ds=row['dataset'];outer=record['outer'];inner=record['inner']
    arch=('local' if row['spec']['architecture']=='lag_local_tokens' else
         'cb_pre' if row['spec']['architecture']=='cbramod' and row['spec']['adaptation']=='pretrained_full' else
         'cb_random' if row['spec']['architecture']=='cbramod' else 'reve_pre')
    coordinates=outer['evaluation_coordinates'];segs=[{'p':pid,'code':code,'e0':int(e0),'role':role} for pid,code,e0,role in coordinates]
    assert len({(s['p'],s['e0']) for s in segs})==len(segs)
    assert {s['p'] for s in segs}.isdisjoint(outer['training_people'])
    margins={(s['person'],s['e0']):s['scores'] for s in outer['segment_margins']}
    observations=[];details={}
    for sec in plan['seconds']:
        windows=T.windows(segs,plan['segment_samples'],sec)
        ids=[ds+'/cf'+str(row['content_fold'])+'/'+digest([(s['p'],s.get('code'),s['e0'],s['role']) for s in w]) for w in windows]
        people=np.array([w[0]['p'] for w in windows]);assert len(ids)==len(set(ids))
        for mode in ('native','unified'):
            key=f'{sec}|{mode}';saved=outer['metrics'][key];fits=saved['fits']
            assert len(windows)==saved['evaluation_windows']
            x=T.matrix(windows,margins,mode,sec);variants={'original':x,'reverse':x[:,::-1],'permuted':permutations(x,ids)}
            entries={}
            for integrator in T.INTEGRATORS:
                if fits[integrator]['status']!='ok':
                    entries[integrator]={'status':fits[integrator]['status']};continue
                entries[integrator]={}
                for order,changed in variants.items():
                    logits=ordered_logits(fits,integrator,x,changed)
                    other=ordered_logits(fits,integrator,-x,-changed)
                    assert np.allclose(logits,-other,rtol=1e-12,atol=1e-12)
                    ll=AO.order_logloss_bits(logits,other);acc=AO.order_credit(logits,other)
                    per={}
                    for pid in sorted(set(people)):
                        mask=people==pid;ref=saved['candidates'][integrator][pid]
                        assert int(mask.sum())==ref['n_windows']
                        if order=='original':
                            assert np.isclose(ll[mask].mean(),ref['nll_bits'],rtol=1e-10,atol=1e-10)
                            assert np.isclose(acc[mask].mean(),ref['accuracy'],rtol=0,atol=1e-12)
                        qids=[q for q,take in zip(ids,mask) if take]
                        per[pid]={'nll_bits':float(ll[mask].mean()),'accuracy':float(acc[mask].mean()),'n_windows':int(mask.sum())}
                        observations.append(dict(dataset=ds,identity=pid,group=ref['group'],fold=f'content_{row["content_fold"]}',
                            seed=row['seed'],arm=f'{arch}/{integrator}/{order}',window=str(sec),metric='attention_nll_'+mode,
                            unit='bits/window',value=per[pid]['nll_bits'],query_set_id=digest(qids),analysis_role='outer_test',
                            provenance={'query_ids':qids,'support_ids':[],'population_fit_identities':outer['training_people'],
                                'selection_identities':inner['evaluation_people'],'outer_fold':f'subject_{row["subject_fold"]}',
                                'source_record':str(path),'source_sha256':B.sha(path)}))
                    entries[integrator][order]=per
            details[key]={'frozen_fits':fits,'inner_selected_integrator':record['chosen_integrators'][key],'results':entries}
    return observations,dict(id=unit['id'],source_sha256=B.sha(path),unit=unit,results=details,
                             physical_segments=len(segs),mean_score_exactly_unchanged=True)

def analyze(plan,observations):
    sys.path.insert(0,str(PACKAGE/'src'))
    from aln35_reference.contrasts import analyze as paired
    output=[]
    for ds in ('dtu','fau'):
        for mode in ('native','unified'):
            for sec in (10,20):
                common={'dataset':ds,'metric':'attention_nll_'+mode,'unit':'bits/window',
                    'required_seeds':[3401,3407,3413] if ds=='dtu' else [3401],'required_folds':['content_0','content_1'],
                    'group_sets':{'all':sorted(set(plan['expected'][ds].values()))},
                    'expected_identities':{'all':sorted(plan['expected'][ds])},'minimum_n':3,'require_full_provenance':True,
                    'bootstrap':{'B':4000,'seed':351621,'alpha':.05,'resampling':'independent'}}
                def term(arm,weight):return dict(group='all',arm=arm,window=str(sec),weight=weight)
                for arch in ('local','cb_pre','cb_random','reve_pre'):
                    for integrator in T.INTEGRATORS:
                        spec=dict(common,family_id=f'S35_ORDER_{ds}_{mode}_{sec}_{arch}_{integrator}',contrasts=[
                            {'id':order+'_minus_original','terms':[term(f'{arch}/{integrator}/{order}',1),term(f'{arch}/{integrator}/original',-1)]}
                            for order in ('reverse','permuted')])
                        output.append(paired(observations,spec))
                spec=dict(common,family_id=f'S35_TRANSFER_VS_INTEGRATION_{ds}_{mode}_{sec}',contrasts=[
                    {'id':'local_mean_minus_cb_mean','terms':[term('local/mean/original',1),term('cb_pre/mean/original',-1)]},
                    {'id':'cb_mean_minus_cb_learned','terms':[term('cb_pre/mean/original',1),term('cb_pre/antisymmetric/original',-1)]}])
                output.append(paired(observations,spec))
    return output

def main():
    assert os.environ.get('SLURM_JOB_ID');plan=make_plan();observations=[];details=[];missing=[]
    for unit in plan['rows']:
        path=T.BASE/'units'/f'{unit["id"]}.json'
        if not path.exists():missing.append(unit['id']);continue
        rows,record=evaluate(unit,read(path),path,plan);observations.extend(rows);details.append(record)
    families=analyze(plan,observations);job=os.environ['SLURM_JOB_ID']
    out=RESULTS/f'run_{job}';record={'job':job,'created':datetime.now().astimezone().isoformat(),
        'status':'complete' if not missing else 'interim','completed_units':len(details),'expected_units':160,
        'missing_units':missing,'plan_sha256':B.sha(PLAN),'families':families,
        'scope':'frozen score/integrator ordering; no encoder or integrator refitting; no behavioral RT variable'}
    write(out/'contrasts.json',record);write(out/'unit_order_metrics.json',details)
    with (BASE/f'normalized_{job}.jsonl').open('x') as f:
        for row in observations:f.write(json.dumps(row,allow_nan=False)+'\n')
    doc=ROOT/'docs/auditory_alignment_v3/aln35'/f'ATTENTION_ORDER_RESULTS_{job}.md'
    doc.write_text(f'# ALN3.5 frozen attention order\n\nCPU{job}; {len(details)}/160 original units available. '
        'Reconstructed original windows/metrics agree with saved production results. Mean-score outputs are exactly unchanged by ordering. '
        'All incomplete identity/seed cells remain explicit in contrasts.json; this does not mark the original attention training complete.\n\n'
        'Fixed mean and learned-integrator order effects, fixed CB-versus-local transfer and CB integrator-versus-mean gains are separate families. '
        'New fixed-SE max-|z*| intervals do not replace the old sparse max-t outputs. Five-second single-segment windows are skipped; no behavioral RT is measured.\n\n'
        f'Results: `{(out/"contrasts.json").relative_to(ROOT)}`.\n')
    print(json.dumps({k:record[k] for k in ('job','status','completed_units','expected_units')}) ,flush=True)

if __name__=='__main__':main()
