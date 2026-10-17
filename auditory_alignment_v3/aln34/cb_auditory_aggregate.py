"""Matched public-auditory CB donor accounting and paired target risks."""
from collections import defaultdict
from datetime import datetime
import os
from pathlib import Path
import shutil
from .. import core,bc_interim
from . import cb_auditory as C,new_lane_aggregate as A,learning_budget as B


def check_streams(donors):
    groups=defaultdict(set)
    for d in donors:groups[d['unit']['seed']].add((d['updates'],d['query_rows'],d['stream_sha256']))
    assert all(len(v)==1 for v in groups.values()),'paired CB donor exposure differs'
    return {str(k):{'updates':next(iter(v))[0],'query_rows':next(iter(v))[1],'stream_sha256':next(iter(v))[2]} for k,v in groups.items()}


def main():
    assert os.environ.get('SLURM_JOB_ID');os.umask(0o077)
    plan=A.read(C.PLAN);C.verify(plan);sha=B.sha(C.PLAN);panel=A.Panel(bc_interim.load_manifest());audit=[];donors=[]
    for row in plan['rows']:
        rec=A.production(C.BASE.name,row,sha,audit)
        if C.is_donor(row):
            if rec:donors.append(rec)
            continue
        name=row['spec']['intermediate_arm'];base=plan['baselines'][row['spec']['baseline_id']]
        old=A.source(row['spec']['baseline_id'],base['record_sha256'])
        ref='random_direct' if name=='random_paired' else 'generic_direct'
        for mode in ('native','unified'):
            scope='CB_auditory_intermediate'
            panel.add(scope,ref,mode,row,old['eval']['per_participant'],A.standard(old['eval'],mode))
            panel.add(scope,name,mode,row,old['eval']['per_participant'],A.standard(rec['eval'],mode) if rec else None)
            panel.compare(row['dataset'],scope,mode,ref,name)
            panel.compare(row['dataset'],scope,mode,'random_paired','generic_paired')
            panel.compare(row['dataset'],scope,mode,'generic_wrong','generic_paired')
    streams=check_streams(donors);families=panel.summarise();done=sum(x['status']=='complete' for x in audit)
    result={'time':datetime.now().astimezone().isoformat(),'job':os.environ['SLURM_JOB_ID'],'status':'complete' if done==len(audit) else 'interim',
            'complete':done,'planned':len(audit),'donors_complete':len(donors),'paired_donor_exposure':streams,'donors':donors,
            'families':families,'provenance':audit,'source_sha256':B.sha(__file__),'shared_aggregation_sha256':B.sha(A.__file__),
            'plan_sha256':sha,'design_sha256':B.sha(C.NOTE)}
    root=Path(core.REPO)/'results/auditory_alignment_v3/aln34/cb_auditory';target=root/'efficacy.json'
    if target.exists():
        backup=root/'history'/(B.sha(target)+'.json');backup.parent.mkdir(parents=True,exist_ok=True)
        if not backup.exists():shutil.copy2(target,backup)
    B.write(target,result)
    lines=['# CBraMod intermediate public auditory training','',f"{result['time']}, CPU job {result['job']}, **{result['status']}**; {done}/{len(audit)} units, {len(donors)}/9 donors complete.",'',
           'Matched donor update counts/data streams; only backbone weights transfer. Target heads, source-only selection and original direct baselines are retained. Donor64Hz preprocessing differs from target preprocessing. All registered target effects and donor costs are in the JSON; neither extra optimization nor a single contrast establishes auditory-specific knowledge.','']
    for f in families:
        st=f['groups']['all']
        if f['common_identity_n']<3 or 'est' not in st:continue
        lines += [f"## {f['dataset']} / {f['readout']} / {f['seed_scope']}",'',f"Complete paired identities {f['common_identity_n']}/{f['expected_identity_n']}.",'',
                  '| Comparison | ΔR bits/query | Simultaneous95% interval |','|---|---:|---:|']
        for j,label in enumerate(f['labels']):lines.append(f"| {label} | {st['est'][j]:+.4f} | [{st['band_low'][j]:+.4f},{st['band_high'][j]:+.4f}] |")
        lines.append('')
    (Path(core.REPO)/'docs/auditory_alignment_v3/CB_AUDITORY_CONTINUATION_RESULTS.md').write_text('\n'.join(lines)+'\n')
    print({'complete':done,'planned':len(audit),'donors_complete':len(donors)},flush=True)


if __name__=='__main__':main()
