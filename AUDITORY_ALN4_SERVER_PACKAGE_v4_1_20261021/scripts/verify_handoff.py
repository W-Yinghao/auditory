"""Meaningful contract/aggregation checks; no server or private data access."""
from pathlib import Path
import argparse,ast,copy,hashlib,json,sys
import numpy as np

def run(root):
    sys.path.insert(0,str(root/'scripts'))
    from materialize_plan import expand
    from validate_binding import validate
    from paired_summary import summarize
    checks=[]
    for file in sorted(root.rglob('*.py')):ast.parse(file.read_text())
    checks.append('all_python_files_parse')
    plan=json.loads((root/'plans/round1.json').read_text());units=expand(plan)
    seen=set()
    for u in units['units']:
        assert all(d in seen for d in u['depends_on']);seen.add(u['id'])
    assert units['logical_kind_counts']['private_full_finetune']==15
    assert {u['arm'] for u in units['units'] if u['kind']=='private_full_finetune'}=={'B0','TCS','TNCE'}
    checks.append('logical_DAG_topological_and_no_accidental_GCS_wrong_private_FT')
    assert plan['time']['source_actual_tick_count']==200
    assert plan['time']['source_anchor_offset_inclusive']==[26,281]
    assert plan['time']['public_valid_n']==[80,81,80]
    assert plan['time']['backbone_fs_native_after_wrapper']==200
    checks.append('plan_source_public_private_sample_access_consistency')
    template=json.loads((root/'templates/BINDING.template.json').read_text())
    assert validate(template)['status']=='NOT_READY'
    assert validate(template,scope='source')['status']=='NOT_READY'
    checks.append('unbound_template_cannot_pass_readiness')
    rows=[{'person_id':str(p),'contrast':c,'seed':s,'value':(p-5)*.03 + (c=='d2')*.1+(s-1)*.002}
          for p in range(12) for c in ['d1','d2'] for s in [1,2,3]]
    data={'rows':rows,'contrasts':['d1','d2'],'seeds':[1,2,3],'family':'synthetic','cohort':'synthetic'}
    r=summarize(data,draws=4000)
    assert r['n_people']==12
    expected=np.mean([(p-5)*.03+.002 for p in range(12)])
    assert abs(r['contrasts'][0]['benefit_mean']-expected)<1e-12
    checks.append('seed_averaging_precedes_person_inference_no_seed_n_inflation')
    shifted=copy.deepcopy(data)
    for row in shifted['rows']:row['value']+=.4
    rr=summarize(shifted,draws=4000)
    assert np.allclose(np.array(rr['contrasts'][0]['simultaneous_95_ci'])-r['contrasts'][0]['simultaneous_95_ci'],.4)
    checks.append('paired_bootstrap_translation_equivariance')
    missing=copy.deepcopy(data);missing['rows'].pop()
    rm=summarize(missing)
    assert rm['n_people']==11 and rm['excluded_incomplete_people']==['11']
    assert rm['coverage_by_contrast_before_family_intersection']['d1']==12
    checks.append('missing_seed_person_not_imputed_and_coverage_explicit')
    duplicate=copy.deepcopy(data);duplicate['rows'].append(duplicate['rows'][0])
    try:summarize(duplicate)
    except ValueError:checks.append('duplicate_person_seed_rejected')
    else:raise AssertionError('duplicate accepted')
    ledger=json.loads((root/'evidence/evidence_ledger.json').read_text())
    for src in ledger['sources']:
        p=root/'evidence/repo_snapshots'/src['repo_path']
        assert hashlib.sha256(p.read_bytes()).hexdigest()==src['sha256']
    checks.append('eight_public_evidence_snapshots_match_pinned_ledger')
    return {'status':'PASS','checks':checks,'n_checks':len(checks),'logical_units':units['logical_units_count'],
            'production_trainer_tested':False,'scope':'synthetic reference, plan/coverage/data-contract checks only'}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path);a=p.parse_args()
    r=run(Path(__file__).resolve().parents[1]);text=json.dumps(r,indent=2)
    if a.out:a.out.write_text(text+'\n')
    print(text)
