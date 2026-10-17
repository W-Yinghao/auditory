"""Paired CS episode risks and explicitly separate NCE continuation references."""
from datetime import datetime
import os
from pathlib import Path
import shutil
from . import cs_episode as C, new_lane_aggregate as A, learning_budget as B
from .. import core


def values(pp, metric, sign=1.):
    return {m: {p: sign*v[m][metric] for p,v in pp.items()} for m in ('native','unified')}


def main():
    assert os.environ.get('SLURM_JOB_ID');os.umask(0o077)
    plan=A.read(C.PLAN);C.verify(plan);panel=A.Panel();audit=[];parents=[]
    # The primary same-CS contrasts are identical to the registered parent
    # family definitions; no NCE parent result is required for these contrasts.
    A.episode(panel,plan,audit,lane=C.BASE.name)
    for unit in plan['rows']:
        row=unit['outer']['row'];old=A.source(row['experiment_id'],unit['outer']['record_sha256'])
        population=old['eval']['per_participant']
        r=A.production(C.BASE.name,unit,B.sha(C.PLAN),[])
        if r:
            assert r['continuation_objective']=='CS_SINGLE' and r['source_sha256']==B.sha(C.__file__)
            for stage in r['stages'].values():
                a,b=(stage['training'][x] for x in ('ordinary','episode'))
                for k in ('cs_calibration','query_draw_sha256','source_ids','encoder_updates',
                          'support_steps','query_anchors','support_eligible_anchors'):
                    assert a[k]==b[k], 'unpaired production stream: '+k
        engine=C.ENGINES[unit['dataset']];parent_plan=A.read(engine.PLAN)
        parent=next(p for p in parent_plan['rows'] if p['id']==unit['parent_episode_id'])
        nr=A.production(engine.BASE.name,parent,B.sha(engine.PLAN),parents)
        for frac in ('0.1','0.3'):
            variants={'source_no_adaptation':None,'ordinary_selected':None,'episode_selected':None}
            if r:
                variants['source_no_adaptation']=values(r['stages']['outer']['candidates']['source'][frac]['0']['per_participant'], 'mismatch_gain_bits',-1)
                for regime in ('ordinary','episode'):
                    variants[regime+'_selected']=values(r['choices'][regime][frac]['outer']['per_participant'],'mismatch_gain_bits',-1)
            for regime in ('source','ordinary','episode'):
                for steps in (0,5,20):
                    variants[f'fixed_{regime}/{steps}']=values(r['stages']['outer']['candidates'][regime][frac][str(steps)]['per_participant'], 'mismatch_gain_bits',-1) if r else None
            pairs=[('source_no_adaptation',k) for k in variants if k!='source_no_adaptation']
            pairs += [('ordinary_selected','episode_selected')]
            pairs += [(f'fixed_ordinary/{s}',f'fixed_episode/{s}') for s in (0,5,20)]
            A.add_risks(panel,'episode/cs/mismatch_gain/support_'+frac,variants,row,population,pairs)
            scope='episode/cs_vs_nce_package/support_'+frac
            # Same original checkpoint, held-out people, query and unified
            # readout definition. Native selection objectives differ by design.
            for objective,record in (('NCE',nr),('CS',r)):
                for regime in ('ordinary','episode'):
                    vals=None if record is None else A.named_risks(record['choices'][regime][frac]['outer']['per_participant'])['unified']
                    panel.add(scope,objective+'/'+regime,'unified',row,population,vals)
            for regime in ('ordinary','episode'):
                panel.compare(row['dataset'],scope,'unified','NCE/'+regime,'CS/'+regime)
    families=panel.summarise()
    for f in families:
        if '/mismatch_gain/' in f['scope']:
            f['metric']='mismatch_gain_bits'
            f['direction']='positive = candidate minus reference mismatch gain, bits/query; not true-risk benefit'
        else:
            f['metric']='true_nll_bits'
    complete=sum(x['status']=='complete' for x in audit)
    result={'status':'complete' if complete==len(audit) else 'interim','time':datetime.now().astimezone().isoformat(),
            'job':os.environ['SLURM_JOB_ID'],'units':{'complete':complete,'planned':len(audit)},
            'families':families,'provenance':{'plan_sha256':B.sha(C.PLAN),'design_sha256':B.sha(C.NOTE),
                'aggregate_sha256':B.sha(__file__),'shared_aggregate_sha256':B.sha(A.__file__),
                'units':audit,'NCE_parent_units':parents},
            'scope':'CS_SINGLE continuation of existing NCE local sources; DTU three seeds, FAU seed3401'}
    root=Path(core.REPO)/'results/auditory_alignment_v3/aln34/cs_episode';target=root/'efficacy.json'
    if target.exists():
        backup=root/'history'/(B.sha(target)+'.json');backup.parent.mkdir(parents=True,exist_ok=True)
        if not backup.exists():shutil.copy2(target,backup)
    B.write(target,result)
    lines=['# Public local CS episode continuation','',f"{result['time']}; CPU job {result['job']}; **{complete}/{len(audit)} complete**.",'',
        'Forty bundles reuse NCE local sources: DTU30 (three seeds), FAU10 (seed3401). These are CS continuations, not from-scratch CS models. Each independent person requires all registered folds/seeds; seeds do not increase n. Engineering probes are excluded. All candidate risk and mismatch-gain families, direct group interactions and actual paired coverage are retained in the aggregate JSON.','',
        'Primary comparison: episode-CS versus ordinary-CS with matched source weights, support computation, samples and100 encoder updates. A separate unified-readout NCE-versus-CS selected-policy comparison changes continuation objective and policy selection/readout protocol; it is a package comparison. Native NCE and CS scores are not treated as the same readout.','']
    for f in families:
        st=f['groups']['all']
        if f['common_identity_n']<3 or 'est' not in st:continue
        lines += [f"## {f['dataset']} / {f['scope']} / {f['readout']} / {f['seed_scope']}",'',
                  f"Paired n={f['common_identity_n']}/{f['expected_identity_n']}. {f['direction']}.",'',
                  '| Contrast | Difference | Simultaneous95% interval |','|---|---:|---:|']
        for j,label in enumerate(f['labels']):
            lines.append(f"| {label} | {st['est'][j]:+.5f} | [{st['band_low'][j]:+.5f}, {st['band_high'][j]:+.5f}] |")
        lines.append('')
    (Path(core.REPO)/'docs/auditory_alignment_v3/CS_EPISODE_RESULTS.md').write_text('\n'.join(lines)+'\n')
    print(result['units'],flush=True)


if __name__=='__main__':main()
