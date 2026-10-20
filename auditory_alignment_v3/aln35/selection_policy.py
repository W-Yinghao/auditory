"""S35_TRUE_RISK_SELECTION: freeze inner-only rules before opening outer results."""
from __future__ import annotations
from datetime import datetime
import os
from pathlib import Path
import numpy as np
from ..aln34 import learning_budget as B
from . import selection_assets as A,support_contract as K

BASE=A.ROOT/'true_risk_selection_v1'


def choose(inner):
    points=inner['budget']['candidate_steps'];curves=inner['candidates'];out={}
    # Both policies see exactly the same trajectory states, including epoch0.
    gain={str(s):curves[str(s)]['gain']['inherited_gain_selection_score'] for s in points}
    selected_gain=min(points,key=lambda s:(gain[str(s)],s))
    for mode in ('native','unified'):
        tables={str(s):{pid:row['metrics'][mode]['nll_bits'] for pid,row in curves[str(s)]['evaluation']['per_participant'].items()
                        if row['status']=='complete' and np.isfinite(row['metrics'][mode]['nll_bits'])} for s in points}
        people=set.intersection(*(set(rows) for rows in tables.values()))
        if not people:out[mode]={'status':'no_common_inner_people','candidate_risks':tables};continue
        risks={step:float(np.mean([rows[pid] for pid in sorted(people)])) for step,rows in tables.items()}
        selected=min(points,key=lambda s:(risks[str(s)],s))
        out[mode]={'status':'complete','true_risk_selected_step':selected,'gain_selected_step':selected_gain,
                   'true_risk_candidate_index':points.index(selected),'gain_candidate_index':points.index(selected_gain),
                   'true_risk_fraction':inner['budget']['candidate_fractions'][points.index(selected)],
                   'gain_fraction':inner['budget']['candidate_fractions'][points.index(selected_gain)],
                   'true_risk_selected_epoch0':selected==0,'gain_selected_epoch0':selected_gain==0,
                   'true_risks_equal_person':risks,'inherited_gain_scores':gain,'per_inner_identity_risks':tables,
                   'complete_inner_ids':sorted(people),'personal_adaptation_steps':0,
                   'policy_scope':'independent inner people, source-ES content; separate readout, no outer-result input'}
    return out


def apply_choice(policy,outer):
    """Apply the already frozen relative candidate position, never argmin outer."""
    out={};points=outer['budget']['candidate_steps']
    for mode,rule in policy.items():
        if rule['status']!='complete':out[mode]={'status':rule['status']};continue
        a=points[rule['true_risk_candidate_index']];b=points[rule['gain_candidate_index']]
        av=outer['candidates'][str(a)]['evaluation']['per_participant'];bv=outer['candidates'][str(b)]['evaluation']['per_participant']
        per={}
        for identity in sorted(set(av)|set(bv)):
            if identity not in av or identity not in bv or av[identity]['status']!='complete' or bv[identity]['status']!='complete':
                per[identity]={'status':'missing_candidate_query'};continue
            assert av[identity]['query_hash']==bv[identity]['query_hash'] and av[identity]['candidate_hash']==bv[identity]['candidate_hash']
            x,y=av[identity]['metrics'][mode],bv[identity]['metrics'][mode]
            per[identity]={'status':'complete','group':av[identity]['group'],'true_risk_policy':x,'gain_policy':y,
                           'true_risk_minus_gain_improvement_bits':y['nll_bits']-x['nll_bits'],
                           'query_hash':av[identity]['query_hash'],'candidate_hash':av[identity]['candidate_hash']}
        out[mode]={'status':'complete','true_risk_outer_step':a,'gain_outer_step':b,'per_participant':per}
    return out


def refresh():
    from . import matched_updates as M
    assert os.environ.get('SLURM_JOB_ID')
    plan=A.read(M.PLAN);M.verify(plan);groups={}
    for unit in plan['rows']:
        groups.setdefault(unit['source_lineage'],{})[(unit['stage'],unit['fraction'])]=unit
    ledger=[]
    for lineage,units in groups.items():
        for fraction in (.5,1.):
            innerunit=units[('inner',fraction)];innerpath=M.BASE/'units'/f'{innerunit["id"]}.json'
            if not innerpath.exists():continue
            inner=A.read(innerpath);assert inner['status']=='complete' and not inner['probe'] and inner['plan_sha256']==B.sha(M.PLAN)
            policy_id='ALN35SEL_'+K.digest({'lineage':lineage,'fraction':fraction,'inner_sha256':B.sha(innerpath),
                                         'code_sha256':B.sha(__file__),'matched_plan_sha256':B.sha(M.PLAN)})[:16]
            path=BASE/'policies'/f'{policy_id}.json';frozen=choose(inner)
            body={'id':policy_id,'status':'complete','lineage':lineage,'fraction':fraction,'inner_record_sha256':B.sha(innerpath),
                  'matched_plan_sha256':B.sha(M.PLAN),'policy':frozen,'selection_code_sha256':B.sha(__file__),
                  'outer_data_access_for_selection':False}
            if path.exists():assert A.read(path)==body
            else:B.write(path,body);path.chmod(0o444)
            # The policy is now committed in the server filesystem. Only now
            # open the paired outer trajectory; it cannot affect the choice.
            outerunit=units[('outer',fraction)];outerpath=M.BASE/'units'/f'{outerunit["id"]}.json'
            entry={'id':policy_id,'fraction':fraction,'lineage':lineage,'outer_available':outerpath.exists()}
            if outerpath.exists():
                outer=A.read(outerpath);assert outer['status']=='complete' and not outer['probe'] and outer['plan_sha256']==B.sha(M.PLAN)
                result={**body,'outer_record_sha256':B.sha(outerpath),'outer':apply_choice(frozen,outer)}
                B.write(BASE/'units'/f'{policy_id}.json',result)
            ledger.append(entry)
    B.write(BASE/'coverage.json',{'created':datetime.now().astimezone().isoformat(),'status':'complete' if len(ledger)==60 and all(x['outer_available'] for x in ledger) else 'interim',
              'expected_policy_units':60,'source_policies_frozen':len(ledger),'with_outer':sum(x['outer_available'] for x in ledger),
              'matched_plan_sha256':B.sha(M.PLAN),'units':ledger,'independent_people':44,
              'analysis_scope':'fixed U50%-100% and true-risk-vs-gain effects remain separate; no aggregate CI subtraction'})


def fleet_status():
    status={'name':'c3_s35selection','lane':'s35_selection','state':'dependent_cpu_rollup','ready':0,'remaining':60,'slots':0,'initial':[],'submit':[]}
    path=BASE/'coverage.json'
    if path.exists():
        value=A.read(path);status.update(remaining=60-value['with_outer'],state='complete' if value['status']=='complete' else 'dependent_cpu_rollup')
    return status


if __name__=='__main__':refresh()
