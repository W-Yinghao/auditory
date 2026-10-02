#!/usr/bin/env python3
"""Generate a bounded *planned* task registry. No patient data and no training."""
from __future__ import annotations
import argparse,json
from pathlib import Path
import yaml


def build(cfg: dict) -> dict:
    tasks=[]
    seeds=cfg['splits']['outer_seeds']; folds=cfg['splits']['outer_folds']
    inner=cfg['splits']['clinical_inner_folds']; nl=len(cfg['clinical']['lambda_mean_loss'])
    calls=inner*nl+1
    for seed in seeds:
        for fold in range(folds):
            for arm in cfg['profile']['arms']:
                tasks.append(dict(phase='profile',seed=seed,fold=fold,arm=arm,small_profile_fits=1,clinical_fit_calls=0))
            for budget in cfg['label_budgets']['values']:
                for rep in range(cfg['label_budgets']['repeats'][str(budget)]):
                    for arm in cfg['clinical']['fitted_sir_arms']:
                        tasks.append(dict(phase='sir',seed=seed,fold=fold,budget=budget,repeat=rep,arm=arm,clinical_fit_calls=calls))
            for arm in cfg['clinical']['muss_arms']:
                tasks.append(dict(phase='muss',seed=seed,fold=fold,budget='all',repeat=0,arm=arm,clinical_fit_calls=calls))
            for arm in cfg['clinical']['technical_full_label_arms']:
                tasks.append(dict(phase='sir_technical',seed=seed,fold=fold,budget='all',repeat=0,arm=arm,clinical_fit_calls=calls))
    for i,t in enumerate(tasks): t['unit_id']=f"STORY_{i:05d}";t['status']='PLANNED_NOT_RUN'
    profile=sum(t.get('small_profile_fits',0) for t in tasks)
    clinical=sum(t.get('clinical_fit_calls',0) for t in tasks)
    if profile>cfg['resources']['small_profile_fits_max'] or clinical>cfg['resources']['clinical_optimizer_calls_max']:
        raise ValueError('Planned task matrix exceeds the frozen caps.')
    return {'status':'PLANNED_NOT_RUN','base_commit':cfg['project']['base_commit'],
            'small_profile_fits':profile,'clinical_optimizer_calls':clinical,'frozen_inference_units_max':len(seeds)*folds,
            'new_raw_backbones':0,'mandatory_response_evaluation':'population/pooled/conditional; no extra fits',
            'optional_mff_enabled':cfg['mff_validation']['enabled'],'competitor_enabled':cfg['competitor']['enabled'],
            'note':'Clinical subsets and patient IDs must be resolved privately by the server; PRIOR needs no fit.',
            'tasks':tasks}


def main():
    p=argparse.ArgumentParser();p.add_argument('--config',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();cfg=yaml.safe_load(a.config.read_text(encoding='utf8'));out=build(cfg)
    a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:v for k,v in out.items() if k!='tasks'},ensure_ascii=False,indent=2))
if __name__=='__main__': main()
