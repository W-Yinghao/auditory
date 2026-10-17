"""Complete-cohort prior science summaries; no training, selection or unit rewrites."""
from collections import defaultdict
from datetime import datetime
import os
from pathlib import Path
import numpy as np

from .. import core,bc_interim
from ..sci_r1 import stats
from . import learning_budget as B,new_lane_aggregate as A,science_aggregate as S,prior_science as Q

def add(panel,scope,label,metric,row,pop,values):
    panel.add(scope,label,metric,row,pop,values)

def public(panel,row,rec,pop):
    cfg=Q.slot(row)+'/'+row['spec']['objective']
    for name,cells in rec['decoding'].items():
        for cell,v in cells.items():
            per=v['per_participant']
            for metric in ('r','mse','matched_minus_mismatch_r','mismatch_minus_matched_mse'):
                obs={p:x.get(metric) if metric in ('r','mse') else S.difference(x['r'],x['mismatch_r']) if metric=='matched_minus_mismatch_r'
                     else S.difference(x['mismatch_mse'],x['mse']) for p,x in per.items()}
                add(panel,'public/'+cfg+'/'+name,cell,metric,row,pop,obs)

def private(panel,row,rec,pop):
    cfg=Q.slot(row)+'/'+row['spec']['objective'];per=rec['per_participant']
    for metric in S.PRIVATE_METRICS:
        for window in Q.WINDOWS:
            add(panel,'private/windows/'+cfg,window,metric,row,pop,{p:v['windows'][window].get(metric) for p,v in per.items()})
    windows=[k for k in Q.WINDOWS if k!='full']
    for cal in ('original_calibration','source_only_destination_calibration'):
        for metric in ('auc','nll_bits','brier'):
            for src in windows:
                for dst in windows:
                    label=src+'/'+dst
                    add(panel,'private/tg/'+cfg+'/'+cal,label,metric,row,pop,
                        {p:v['temporal_generalization'][label][cal].get(metric) for p,v in per.items()})
    for fraction in ('0.1','0.3'):
        for metric in ('auc','nll_bits','brier','history_gain_bits','benefit_bits'):
            for step in ('0','5','20'):
                values={}
                for p,v in per.items():
                    a=v['adaptation'][fraction]
                    if a['status']!='complete':continue
                    cc=a['candidates'];values[p]=cc['0']['nll_bits']-cc[step]['nll_bits'] if metric=='benefit_bits' else cc[step].get(metric)
                add(panel,'private/adapt/'+cfg+'/'+fraction,step,metric,row,pop,values)

def matched_arms(panel,Bn):
    """Joint arm×cell family; direct group comparisons use individual changes."""
    groups=defaultdict(dict)
    for ds,scope,metric,cell in panel.expected:
        parts=scope.split('/')
        if parts[0]=='public':prefix='public';slot,obj=parts[1:3];suffix='/'.join(parts[3:])
        else:prefix='/'.join(parts[:2]);slot,obj=parts[2:4];suffix='/'.join(parts[4:])
        key=(ds,prefix,obj,suffix,metric);groups[key][(slot,cell)]=panel.complete((ds,scope,metric,cell),{3401})
    results=[]
    for key,values in sorted(groups.items()):
        ds,prefix,obj,suffix,metric=key;cells=sorted({c for s,c in values});pairs=[];mapped={}
        high_good=metric in ('r','auc','gain_vs_base_bits','history_gain_bits','history_gain_common_support_bits',
                             'history_twin_gain_bits','history_minus_twin_bits','benefit_bits','matched_minus_mismatch_r','mismatch_minus_matched_mse')
        # group_interactions computes reference minus candidate: orient once here.
        for (slot,cell),v in values.items():mapped[slot+'/'+cell]={p:-x if high_good else x for p,x in v.items()}
        for slot in ('AP','XP','J*','XM'):
            for cell in cells:
                a='S/'+cell;b=slot+'/'+cell
                if a in mapped and b in mapped:pairs.append((a,b))
        if not pairs:continue
        ids=sorted(set.intersection(*[set(mapped[a])&set(mapped[b]) for a,b in pairs]))
        gg={'all':ids};gg.update({str(g):[p for p in ids if panel.groups[(ds,p)]==g] for g in sorted({panel.groups[(ds,p)] for p in ids},key=str)})
        labels=[b+' versus '+a for a,b in pairs]
        entry={'dataset':ds,'scope':prefix+'/'+obj+'/'+suffix,'metric':metric,'seed':3401,'paired_n':len(ids),'labels':labels,
               'direction':'positive = improvement versus scratch; correlation/AUC/gain higher, loss lower','groups':{}}
        for g,people in gg.items():
            y=np.array([[mapped[a][p]-mapped[b][p] for a,b in pairs] for p in people])
            entry['groups'][g]=A.as_json(stats.summary(y,B=Bn,seed=stats.group_seed('prior_science',*key,g)))
        entry['group_effect_difference']=A.group_interactions(mapped,pairs,gg,labels,Bn,stats.group_seed('prior_science',*key,'interaction'))
        results.append(entry)
    return results

def main():
    assert os.environ.get('SLURM_JOB_ID');os.umask(0o077)
    plan=Q.read(Q.PLAN);Q.verify(plan);by=defaultdict(list)
    for u in plan['rows']:by[(u['source']['dataset'],u['source']['spec']['objective'])].append(u)
    panel=A.Panel(bc_interim.load_manifest());coverage={};cov={};provenance={};total=0
    for (ds,obj),units in sorted(by.items()):
        records={}
        for u in units:
            p=Q.BASE/'units'/f'{u["id"]}.json'
            if not p.exists():continue
            r=Q.read(p)
            if r.get('status')!='complete':continue
            assert not r.get('probe') and r['plan_sha256']==B.sha(Q.PLAN) and r['unit']['source']==u['source']
            bp=Q.BASE/'bindings'/f'{u["id"]}.json';assert r['binding_sha256']==B.sha(bp) and Q.read(bp)==r['unit']
            records[u['id']]=r;provenance[u['id']]={'record_sha256':B.sha(p),'binding_sha256':B.sha(bp)}
        total+=len(records);ready=len(records)==len(units)
        coverage[ds+'/'+obj]={'complete':len(records),'planned':len(units),'ready_for_complete_family':ready}
        if not ready:continue
        for u in units:
            rec=records[u['id']];row=u['source'];orig=A.source(row['experiment_id'],rec['unit']['record_sha256']);pop=orig['eval']['per_participant']
            if ds=='private_bdf':private(panel,row,rec,pop)
            else:public(panel,row,rec,pop)
    # Covariates were recorded independently in the completed historical native panel.
    for row in Q.R.all_rows():
        if row['family_id']=='E_LOCAL' and row['seed']==3401 and row['spec'].get('objective')=='NCE':
            p=Path(core.OUT)/'units'/f'{row["experiment_id"]}.json'
            if not p.exists():continue
            rec=Q.read(p)
            if rec.get('status')=='complete':
                for pid,v in rec['eval']['per_participant'].items():
                    value={'group':v['group'],'age':v.get('age_months'),'duration':v.get('duration_months')}
                    assert pid not in cov or cov[pid]==value;cov[pid]=value
    levels,development=S.summaries(panel,cov,4000);contrasts=matched_arms(panel,4000)
    value={'time':datetime.now().astimezone().isoformat(),'status':'complete' if total==len(plan['rows']) else 'interim',
           'complete':total,'planned':len(plan['rows']),'coverage':coverage,'levels':levels,'arm_comparisons':contrasts,
           'development':development,'provenance':provenance,'plan_sha256':B.sha(Q.PLAN),'job':os.environ['SLURM_JOB_ID'],
           'excluded_nonhuman_entities':sorted(panel.excluded_entities)}
    B.write(Path(core.REPO)/'results/auditory_alignment_v3/aln34/prior_science/science.json',value)
    lines=['# Public-prior content, time and private-task science','',f"Snapshot {value['time']}: **{value['status']}**, {total}/{len(plan['rows'])} frozen primary targets.",'',
           'Representative seed3401 only; complete person/content folds and all five arms are required within each dataset×objective before a family is summarized. Public start shifts retain the actual38-sample/593.75ms access. Private input contains0–578.125ms sample times and no pre-event condition. These are decoding/masked-input analyses, not neural latencies or an online-causal pipeline. Public spectra/Ac/Lz are outside this64Hz feature version.','',
           '| Dataset / objective | Complete / planned | Complete family |','|---|---:|---|']
    for key,v in coverage.items():lines.append(f"| {key} | {v['complete']}/{v['planned']} | {v['ready_for_complete_family']} |")
    lines+=['','All temporal cells, per-arm levels, paired scratch contrasts, direct group-effect differences and declared private developmental models are retained in `results/auditory_alignment_v3/aln34/prior_science/science.json`.4000 identity bootstrap-t; source-arm levels use their full cell family, and arm contrasts jointly cover four arms×all cells. Source-training ES readout fitting is not whole-pipeline held-out-person selection. Historical native S34 results use a different input/target contract.','']
    for item in contrasts:
        if item['paired_n']<3:continue
        lines.append(f"- {item['dataset']} / {item['scope']} / {item['metric']}: {item['paired_n']} paired identities; {len(item['labels'])} contrasts in the full simultaneous family.")
    (Path(core.REPO)/'docs/auditory_alignment_v3/PRIOR_SCIENCE_RESULTS.md').write_text('\n'.join(lines)+'\n')
    print('Prior science',total,'/',len(plan['rows']),len(levels),'families',flush=True)

if __name__=='__main__':main()
