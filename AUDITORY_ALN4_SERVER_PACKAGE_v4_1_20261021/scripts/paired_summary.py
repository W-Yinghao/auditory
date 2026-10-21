"""Person-paired conditional-on-fitted-model bootstrap reference.

Input JSON: {rows:[{person_id,contrast,seed,value}], contrasts:[...],
             seeds:[...], family:'...', cohort:'...'}. Each value is an already matched-query
benefit contrast, not an unpaired score. Reject duplicates/missing seed cells.
For simultaneous CIs use the explicitly reported complete-person intersection
for all columns of ONE predeclared family. Never impute missing values.
"""
from pathlib import Path
import argparse,json
import numpy as np

def summarize(data,draws=4000,rng_seed=3441):
    if not data.get('cohort'):raise ValueError('one explicitly named cohort per paired family required')
    contrasts=data['contrasts'];seeds=data['seeds']
    if not contrasts or len(set(contrasts))!=len(contrasts) or not seeds or len(set(seeds))!=len(seeds):
        raise ValueError('nonempty unique declared contrasts/seeds required')
    people=sorted({str(r['person_id']) for r in data['rows']});cells={}
    for r in data['rows']:
        k=(str(r['person_id']),r['contrast'],r['seed'])
        if k in cells:raise ValueError('duplicate person/contrast/seed')
        if k[1] not in contrasts or k[2] not in seeds:raise ValueError('undeclared contrast/seed')
        value=float(r['value'])
        if not np.isfinite(value):raise ValueError('only finite complete-valid contrasts accepted; list missing separately')
        cells[k]=value
    coverage={c:sum(all((p,c,s) in cells for s in seeds) for p in people) for c in contrasts}
    kept=[p for p in people if all((p,c,s) in cells for c in contrasts for s in seeds)]
    dropped=[p for p in people if p not in kept]
    if len(kept)<3:raise ValueError('fewer than 3 complete people for declared family; report descriptive individual data')
    x=np.asarray([[np.mean([cells[p,c,s] for s in seeds]) for c in contrasts] for p in kept])
    n=len(x);mean=x.mean(0);se=x.std(0,ddof=1)/np.sqrt(n)
    rng=np.random.default_rng(rng_seed);boot=x[rng.integers(n,size=(draws,n))].mean(1)
    nz=se>0
    maxt=np.max(np.abs((boot[:,nz]-mean[nz])/se[nz]),axis=1) if nz.any() else np.zeros(draws)
    critical=float(np.quantile(maxt,.95))
    return {'family':data['family'],'cohort':data['cohort'],'n_people':n,'seeds_averaged_within_person':seeds,'draws':draws,'rng_seed':rng_seed,
      'coverage_by_contrast_before_family_intersection':coverage,'family_complete_people':kept,
      'excluded_incomplete_people':dropped,'interval_method':'bootstrap max absolute centered mean / original person SE; simultaneous within this declared family',
      'scope':'target-person sampling conditional on fitted source/target models; not source-training-population resampling',
      'critical':critical,'contrasts':[{'contrast':c,'benefit_mean':float(mean[j]),'simultaneous_95_ci':[float(mean[j]-critical*se[j]),float(mean[j]+critical*se[j])],
          'zero_empirical_variance':bool(not nz[j]),'note':'zero empirical variance is not proof of a population constant' if not nz[j] else ''} for j,c in enumerate(contrasts)]}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--input',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    result=summarize(json.loads(a.input.read_text()));a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'out':str(a.out),'n_people':result['n_people']}))
