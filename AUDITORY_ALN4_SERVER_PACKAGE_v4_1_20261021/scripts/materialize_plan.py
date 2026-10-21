"""Read-only logical plan expansion. No scheduler, network or model invocation."""
from pathlib import Path
import argparse,json,hashlib

def expand(plan):
    units=[];seed=plan['seed']
    def add(key,kind,deps=(),**kw):
        ident='ALN41_'+key
        units.append({'id':ident,'kind':kind,'depends_on':['ALN41_'+d for d in deps],
                      'status':'NOT_RUN','seed':seed,**kw})
        return key
    add('INTAKE','intake',expanded_fits=0)
    add('ASSET','stage1_asset_readiness',['INTAKE'],expanded_fits=0)
    add('IMPLEMENT','server_implementation',['INTAKE','ASSET'],expanded_fits=0)
    add('READY','engineering_readiness',['IMPLEMENT'],expanded_fits=0)
    add('PANELS','fixed_source_panels_and_sigmas',['READY'],expanded_fits=0)
    cal=[]
    for arm in plan['source']['calibration_arms']:
        for ix,lr in enumerate(plan['source']['calibration_lrs']):
            key=f'CAL_{arm}_LR{ix}_S{seed}';cal.append(key)
            add(key,'source_short_calibration',['PANELS'],arm=arm,lr=lr,updates=1000,expanded_fits=1)
    add('LR_FREEZE','source_only_selection',cal,expanded_fits=0)
    dep={'B0':'READY'}
    for arm in plan['source']['production_arms']:
        dep[arm]=f'SOURCE_{arm}_S{seed}'
        add(dep[arm],'source_production',['LR_FREEZE'],arm=arm,updates=10000,expanded_fits=1)
    downstream=[]
    for arm in plan['arms']:
        for dataset in plan['downstream']['datasets']:
            exp=f'CACHE_{arm}_{dataset}_S{seed}';probe=f'PROBE_{arm}_{dataset}_S{seed}'
            add(exp,'frozen_cache_bundle',[dep[arm]],arm=arm,dataset=dataset,expanded_fits=0,
                actual_cache_units='bind target folds and row identities before execution')
            add(probe,'frozen_content_time_history_bundle',[exp],arm=arm,dataset=dataset,
                expanded_fits=None,expansion_required='public fold spec / private five folds and registered common heads')
            downstream.append(probe)
    for arm in plan['core_arms']:
        for fold in range(5):
            key=f'PRIVATE_CE_{arm}_F{fold}_S{seed}'
            add(key,'private_full_finetune',[dep[arm]],arm=arm,fold=fold,epochs=100,expanded_fits=1)
            downstream.append(key)
        key=f'AGE_{arm}_S{seed}'
        add(key,'frozen_age_nested_ridge',[f'CACHE_{arm}_PRIVATE_BDF_S{seed}'],arm=arm,
            expanded_fits=105,counts_condition='5 valid outer folds, each with 4 valid inner folds and 5 alphas')
        downstream.append(key)
        for ds in ['DTU','FAU']:
            key=f'ATTENTION_{arm}_{ds}_S{seed}'
            add(key,'frozen_attention_bundle',[f'CACHE_{arm}_{ds}_S{seed}'],arm=arm,dataset=ds,
                main_window_seconds=20,expanded_fits=None,expansion_required='bound common target readout folds')
            downstream.append(key)
    add('AGE_BASELINES','age_raw_ridge_and_trainmean',['READY'],expanded_fits=110,
        counts_condition='105 raw ridge fits plus 5 trainmean fits with full valid roster')
    downstream.append('AGE_BASELINES')
    add('SUMMARY','paired_scientific_summary',downstream,expanded_fits=0)
    ids={u['id'] for u in units}
    assert len(ids)==len(units)
    assert all(d in ids for u in units for d in u['depends_on'])
    counts={kind:sum(u['kind']==kind for u in units) for kind in sorted({u['kind'] for u in units})}
    assert counts['source_short_calibration']==6 and counts['source_production']==4
    assert counts['private_full_finetune']==15
    return {'schema':'auditory_aln41_logical_units_v1','not_scheduler_submission':True,
            'logical_units_count':len(units),'logical_kind_counts':counts,
            'cpu_fit_expansion_not_finished_until_binding':True,'units':units}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--plan',type=Path,default=Path(__file__).resolve().parents[1]/'plans/round1.json');p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    raw=a.plan.read_bytes();r=expand(json.loads(raw));r['plan_sha256']=hashlib.sha256(raw).hexdigest()
    a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'out':str(a.out),'logical_units':r['logical_units_count'],'counts':r['logical_kind_counts']},ensure_ascii=False))
