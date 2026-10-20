"""Identity-paired readout summaries; no subtraction of aggregate intervals."""
from datetime import datetime
import json
import os
import sys
import numpy as np

def report(plan,completed,missing,metadata):
    from . import fusion_attribution as A
    sys.path.insert(0,str(A.PACKAGE/'src'))
    from aln35_reference.contrasts import analyze,validate_rows
    observations=[];expected={p['id']:p['group'] for p in metadata[0]['participants']}
    for rec in completed:
        prov=rec['provenance'];source=A.BASE/'units'/f'{rec["id"]}.json'
        augment=A.BASE/'units'/f'{rec["id"]}_ensemble.json'
        if rec['ensemble_status']=='available' and augment.exists():source=augment
        fit=sorted(set(p for d in prov['outer'].values() for p in d['provenance']['train_ids']))
        selected=sorted(set(prov['inner']['local']['provenance']['evaluation_ids']))
        outer=prov['outer']['local'];people=np.array(outer['provenance']['evaluation_ids'])
        # Query row order is recorded explicitly, not inferred from group size.
        query_to_person={q:pid for mode in ('native',) for pid,p in rec['modes'][mode]['per_person'].items() for q in p['query_ids']}
        qpeople=np.array([query_to_person[q] for q in outer['query_ids']])
        for mode,item in rec['modes'].items():
            for pid,person in item['per_person'].items():
                def add(arm,value,ids,window='full'):
                    observations.append(dict(dataset='dtu',identity=pid,group=person['group'],
                        fold=f'content_{rec["content_fold"]}',seed=rec['seed'],arm=arm,window=window,
                        metric='true_query_nll_'+mode,unit='bits/query',value=float(value),
                        query_set_id=A.digest(ids),analysis_role='outer_test',provenance=dict(query_ids=ids,
                        support_ids=[],population_fit_identities=fit,selection_identities=selected,
                        outer_fold=f'subject_{rec["subject_fold"]}',source_record=str(source),source_sha256=A.sha(str(source)))))
                for name,values in person['conditions'].items():add(name,values['true_nll_bits'],person['query_ids'])
                vals=[];validids=None;actual=None
                for perm in item['permutations']:
                    indices=np.asarray(perm['outer_indices']);take=qpeople[indices]==pid
                    if not take.any():continue
                    ix=indices[take];ids=[outer['query_ids'][j] for j in ix]
                    assert validids is None or ids==validids
                    validids=ids;vals.append(float(np.asarray(perm['metrics']['true_nll_bits'])[take].mean()))
                    actual=float(np.asarray(item['query_metrics']['actual_mix']['true_nll_bits'])[ix].mean())
                if len(vals)==10:
                    add('local_permuted_mix',np.mean(vals),validids,'permutation_valid')
                    add('actual_mix',actual,validids,'permutation_valid')
    validate_rows(observations)
    families=[];specs=[];groups=sorted(set(expected.values()))
    for mode in ('native','unified'):
        for seeds,label in [([3401,3407,3413],'three_seed_primary'),([3401],'seed3401_interim'),([3407],'seed3407_interim'),([3413],'seed3413_interim')]:
            for name,references in [*plan['families'].items(),('permutation',['local_permuted_mix'])]:
                window='permutation_valid' if name=='permutation' else 'full'
                spec={'family_id':f'S35_FUSION_{mode}_{name}_{label}','dataset':'dtu','metric':'true_query_nll_'+mode,
                      'unit':'bits/query','required_seeds':seeds,'required_folds':['content_0','content_1'],
                      'group_sets':{'all':groups},'expected_identities':{'all':sorted(expected)},
                      'minimum_n':3,'require_full_provenance':True,
                      'bootstrap':{'B':4000,'seed':351510,'alpha':.05,'resampling':'independent'},
                      'contrasts':[{'id':ref+'_minus_actual_mix','terms':[
                          {'group':'all','arm':ref,'window':window,'weight':1},
                          {'group':'all','arm':'actual_mix','window':window,'weight':-1}]} for ref in references]}
                families.append(analyze(observations,spec));specs.append(spec)
    path=A.RESULTS/f'run_{os.environ["SLURM_JOB_ID"]}'
    value={'created':datetime.now().astimezone().isoformat(),'job':os.environ['SLURM_JOB_ID'],
        'status':'complete' if len(completed)==30 and all(r['ensemble_status']=='available' for r in completed) else 'interim',
        'plan_sha256':A.sha(str(A.PLAN)),'completed_bundles':len(completed),'expected_bundles':30,
        'missing':missing,'ensemble_unavailable':[r['id'] for r in completed if r['ensemble_status']!='available'],
        'families':families,'interpretation':'existing source models and source-inner selectors; no new encoder; original primary fusion results retained'}
    A.write(path/'contrasts.json',value);A.write(A.BASE/f'families_{os.environ["SLURM_JOB_ID"]}.json',specs)
    with (A.BASE/f'normalized_rows_{os.environ["SLURM_JOB_ID"]}.jsonl').open('x') as f:
        for row in observations:f.write(json.dumps(row,allow_nan=False)+'\n')
    lines=['# ALN3.5 probability-fusion attribution','',f"CPU Slurm {value['job']}; {len(completed)}/30 bundles; status **{value['status']}**.",
        '', 'Positive contrasts mean the actual local+CB mixture has lower true risk. Intervals use person-level fixed-SE max-|z*|; folds, seeds and permutations do not increase n. Original primary fusion statistics are unchanged.',
        '', '| Family | Contrast | Estimate | Simultaneous interval |','|---|---|---:|---|']
    for family in families:
        if 'three_seed_primary' not in family['family_id']:continue
        for c in family['contrasts']:
            lines.append(f"| {family['family_id']} | {c['id']} | {c.get('estimate')} | {c.get('simultaneous_ci')} |")
    lines+=['','Incomplete cyclic seed ensembles are explicitly missing; the three-reference family was declared separately before reading its outcomes.',
        '',f"Detailed coverage and seed-specific interim sensitivities: `{(path/'contrasts.json').relative_to(A.ROOT)}`. Exact query metadata remains private."]
    doc=A.ROOT/'docs/auditory_alignment_v3/aln35'/f'FUSION_ATTRIBUTION_RESULTS_{value["job"]}.md'
    doc.write_text('\n'.join(lines)+'\n')
    print(json.dumps({k:value[k] for k in ('status','job','completed_bundles','expected_bundles','ensemble_unavailable')}) ,flush=True)
