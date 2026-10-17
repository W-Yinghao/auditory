"""Breadth cohorts use the same identity/contrast machinery, separate artifacts."""
from datetime import datetime
import os
import shutil
from pathlib import Path
from . import new_lane_aggregate as A
from . import learning_budget as B
from .. import core, bc_interim


def main():
    assert os.environ.get('SLURM_JOB_ID');os.umask(0o077)
    from . import breadth_budget as BB, breadth_inner as BI, breadth_policy as BP, breadth_fusion as BF, breadth_episode as BE
    panel=A.Panel(bc_interim.load_manifest());provenance={};status={}
    for m,parser in zip((BB,BI,BP,BF,BE),(A.budget,A.data,A.adapt,A.fusion,A.episode)):
        plan=A.read(m.PLAN);(m.verify_plan if m is BB else m.verify)(plan)
        audit=[];parser(panel,plan,audit,lane=m.BASE.name)
        provenance[m.BASE.name]={'plan_sha256':B.sha(m.PLAN),'units':audit}
        status[m.BASE.name]={'planned':len(audit),'complete':sum(x['status']=='complete' for x in audit),
                             'failed_markers':sum(x.get('failure_marker',False) for x in audit)}
    A.model_contrasts(panel);families=panel.summarise()
    result={'time':datetime.now().astimezone().isoformat(),'job':os.environ['SLURM_JOB_ID'],'units':status,
            'status':'complete' if all(x['planned']==x['complete'] for x in status.values()) else 'interim',
            'families':families,'provenance':provenance,'source_sha256':B.sha(__file__),'shared_aggregation_sha256':B.sha(A.__file__),
            'analysis_note_sha256':B.sha(A.NOTE),'analysis_addendum_sha256':B.sha(A.ADDENDUM),'design_note_sha256':B.sha(BB.NOTE),'excluded_nonhuman_entities':sorted(panel.excluded_entities)}
    root=Path(core.REPO)/'results/auditory_alignment_v3/aln34/breadth';target=root/'efficacy.json'
    if target.exists():
        backup=root/'history'/(B.sha(target)+'.json');backup.parent.mkdir(parents=True,exist_ok=True)
        if not backup.exists():shutil.copy2(target,backup)
    B.write(target,result)
    lines=['# FAU/Federici breadth intervention results','',f"Snapshot {result['time']}, CPU job {result['job']}; **{result['status']}**.",'',
           'Seed3401 breadth; independent of the DTU three-seed panel. Strict identity pairing; phantom excluded. Historical baseline comparisons reuse completed records and are not new intervention results.', '',
           '| Lane | Complete / registered | Failed markers |','|---|---:|---:|']
    lines += [f"| {k} | {v['complete']} / {v['planned']} | {v['failed_markers']} |" for k,v in status.items()]
    for f in families:
        st=f['groups']['all']
        if f['common_identity_n']<3 or 'est' not in st:continue
        lines += ['',f"## {f['dataset']} / {f['scope']} / {f['readout']}",'',f"{f['evidence_origin']}. Paired n={f['common_identity_n']}/{f['expected_identity_n']}.",'',
                  '| Contrast | ΔR bits/query | Simultaneous95% interval |','|---|---:|---:|']
        for j,label in enumerate(f['labels']):lines.append(f"| {label} | {st['est'][j]:+.4f} | [{st['band_low'][j]:+.4f},{st['band_high'][j]:+.4f}] |")
    (Path(core.REPO)/'docs/auditory_alignment_v3/PUBLIC_BREADTH_RESULTS.md').write_text('\n'.join(lines)+'\n')
    print(status,flush=True)


if __name__=='__main__':main()
