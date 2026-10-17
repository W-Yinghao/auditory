"""Complete-identity fixed and inner-selected attention-transfer comparisons."""
from collections import defaultdict
from datetime import datetime
import os
from pathlib import Path
import shutil

from .. import core, bc_interim
from . import attention_transfer as T, learning_budget as B, new_lane_aggregate as A

ARMS=('local','cbramod/pretrained_full','cbramod/random_full','reve/pretrained_full')


def select_model(records,key):
    assert set(records)==set(ARMS)
    # Deliberately accepts only the previously frozen development scores.
    risk={a:records[a]['inner_risks'][key][records[a]['chosen_integrators'][key]] for a in ARMS}
    return min(ARMS,key=lambda a:(risk[a],ARMS.index(a))),risk


def observations(per,metric):
    return {p: (-v[metric] if metric=='accuracy' else v[metric]) for p,v in per.items()}


def collect(panel,plan,records):
    cells=defaultdict(dict);populations={};sources={}
    for unit in plan['rows']:
        row=unit['source']['row'];old=A.source(row['experiment_id'],unit['source']['record_sha256'])
        pop=old['eval']['per_participant'];arm=A.arm(row);rec=records.get(unit['id'])
        cell=tuple(row[k] for k in ('dataset','seed','subject_fold','content_fold'))
        cells[cell][arm]=(unit,rec);populations[unit['id']]=pop;sources[unit['id']]=row
        for seconds in T.SECONDS:
            scope=f'policy/attention_transfer/{seconds}s'
            for mode in ('native','unified'):
                key=f'{seconds}|{mode}'
                for metric in ('nll_bits','accuracy'):
                    readout=mode+'/'+metric
                    for variant in (*T.INTEGRATORS,'selected'):
                        per=(rec['outer']['metrics'][key]['selected'] if variant=='selected' else
                             rec['outer']['metrics'][key]['candidates'][variant]) if rec else None
                        panel.add(scope,arm+'/'+variant,readout,row,pop,observations(per,metric) if per is not None else None)
                    panel.compare(row['dataset'],scope,readout,arm+'/mean',arm+'/antisymmetric')
                    panel.compare(row['dataset'],scope,readout,arm+'/mean',arm+'/selected')
                    if arm!='local':panel.compare(row['dataset'],scope,readout,'local/selected',arm+'/selected')
    selections=[]
    for cell,items in sorted(cells.items()):
        assert set(items)==set(ARMS),'registered model policy lacks a comparator'
        unit,_=items['local'];row=sources[unit['id']];pop=populations[unit['id']]
        full=all(rec is not None for _,rec in items.values())
        records_={a:rec for a,(_,rec) in items.items()}
        if full:
            coords=[r['outer']['evaluation_coordinates'] for r in records_.values()]
            assert all(c==coords[0] for c in coords),'attention models evaluated different outer windows'
        for seconds in T.SECONDS:
            scope=f'policy/attention_transfer/{seconds}s'
            for mode in ('native','unified'):
                key=f'{seconds}|{mode}';per=None
                if full:
                    choice,risk=select_model(records_,key)
                    selections.append({'cell':list(cell),'duration_readout':key,'model':choice,'inner_risks':risk})
                    per=records_[choice]['outer']['metrics'][key]['selected']
                for metric in ('nll_bits','accuracy'):
                    readout=mode+'/'+metric
                    panel.add(scope,'inner_selected_model',readout,row,pop,observations(per,metric) if per is not None else None)
                    for ref in ('local/selected','cbramod/pretrained_full/selected'):
                        panel.compare(row['dataset'],scope,readout,ref,'inner_selected_model')
    return selections


def main():
    assert os.environ.get('SLURM_JOB_ID');os.umask(0o077)
    plan=A.read(T.PLAN);T.verify(plan);audit=[];records={};sha=B.sha(T.PLAN)
    for unit in plan['rows']:
        r=A.production(T.BASE.name,unit,sha,audit)
        if r:records[unit['id']]=r
    panel=A.Panel(bc_interim.load_manifest());selections=collect(panel,plan,records);families=panel.summarise()
    for f in families:
        f['direction']='positive = candidate minus reference accuracy' if f['readout'].endswith('/accuracy') else 'positive = reference minus candidate NLL, bits/attention window'
    result={'time':datetime.now().astimezone().isoformat(),'job':os.environ['SLURM_JOB_ID'],
            'status':'complete' if len(records)==len(plan['rows']) else 'interim','complete':len(records),'planned':len(plan['rows']),
            'families':families,'inner_source_selections':selections,'provenance':audit,
            'source_sha256':B.sha(__file__),'shared_aggregation_sha256':B.sha(A.__file__),
            'plan_sha256':sha,'design_sha256':B.sha(T.NOTE)}
    root=Path(core.REPO)/'results/auditory_alignment_v3/aln34/attention_transfer';target=root/'efficacy.json'
    if target.exists():
        old=root/'history'/(B.sha(target)+'.json');old.parent.mkdir(parents=True,exist_ok=True)
        if not old.exists():shutil.copy2(target,old)
    B.write(target,result)
    lines=['# Frozen retrieval-source transfer to attention','',f"{result['time']}, CPU job{result['job']}; **{result['status']}**, {len(records)}/{len(plan['rows'])} units.",'',
           'New aligned/true-full encoders were trained for single-speaker retrieval. Integrators and source-model policy are selected using inner listeners; outer attention is not used for selection. Paired candidate orders share one physical window.5/10/20s are evidence durations. All fixed alternatives and direct group interactions are retained in the JSON.','']
    for f in families:
        st=f['groups']['all']
        if f['common_identity_n']<3 or 'est' not in st:continue
        lines += [f"## {f['dataset']} / {f['scope']} / {f['readout']} / {f['seed_scope']}",'',
                  f"Complete paired identities{f['common_identity_n']}/{f['expected_identity_n']}; {f['direction']}.",'',
                  '| Comparison | Benefit | Simultaneous95% interval |','|---|---:|---:|']
        for j,label in enumerate(f['labels']):lines.append(f"| {label} | {st['est'][j]:+.4f} | [{st['band_low'][j]:+.4f},{st['band_high'][j]:+.4f}] |")
        lines.append('')
    (Path(core.REPO)/'docs/auditory_alignment_v3/ATTENTION_TRANSFER_RESULTS.md').write_text('\n'.join(lines)+'\n')
    print({'complete':len(records),'planned':len(plan['rows']),'fully_developed_cells':len(selections)},flush=True)


if __name__=='__main__':main()
