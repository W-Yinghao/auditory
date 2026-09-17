"""S0-only audit: required local contracts, environment, and reference delta."""
import argparse, csv, importlib, importlib.metadata, json, os, platform, re, shutil, subprocess, sys, zipfile
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from auditory5.provenance import digest,write_json,require_slurm


def main():
    require_slurm()
    parser=argparse.ArgumentParser();parser.add_argument('--run',required=True);args=parser.parse_args()
    priv=ROOT/'private/auditory5_v1/inputs'/args.run;priv.mkdir(parents=True,exist_ok=False)
    out=ROOT/'results/auditory5_v1'/args.run;out.mkdir(parents=True,exist_ok=False)
    shutil.copy2(__file__,priv/'bootstrap_source.py')
    plan=ROOT/'AUDITORY_FIVE_IDEAS_SERVER_PLAN_v1.md'
    yaml_block=re.findall(r'```yaml\n(.*?)\n```',plan.read_text(),re.S)
    assert len(yaml_block)==1
    cfgpath=ROOT/'configs/auditory5_v1.yaml'
    if cfgpath.exists():assert cfgpath.read_text()==yaml_block[0]+'\n'
    else:cfgpath.write_text(yaml_block[0]+'\n')
    packages={}
    for package in ['numpy','scipy','pandas','mne','scikit-learn','matplotlib','pyedflib','torch','PyYAML','pyarrow','fastparquet']:
        try: packages[package]=importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:packages[package]=None
    torch_info={}
    try:
        import torch
        torch_info={'version':torch.__version__,'build_cuda':torch.version.cuda,'cuda_available_on_cpu_node':torch.cuda.is_available()}
    except Exception as e:torch_info={'import_error_class':type(e).__name__}
    paths=[
      'results/phase1_sources_001/source_manifest.csv','results/phase2_cohort_001/index_recordings.csv',
      'results/phase2_archival_001/candidate_eligibility.csv','private/phase3_ha_covariates_004/candidate_covariates.csv',
      'private/phase2_cohort_001/linked_index.csv','private/inventory_001/file_path_map.csv',
      'results/other_eeg_001/event_ledger.csv','results/phase3_ci_sources_001/source_manifest.csv',
      'results/phase3_ci_sources_001/binary_duplicates.csv','private/phase3_ci_sources_001/source_paths_and_tokens.csv',
      'results/phase3_ci_linkage_005/clinical_source_links.csv','results/phase3_ci_linkage_005/canonical_source_labels.csv',
      'results/phase3_metadata_addendum_001/source_metadata.csv','results/phase3_synthesis_001/pair_availability.csv',
      'private/phase3_ci_clinical_004/candidate_rows_index.csv','private/linkage_001/vendor_identity_records.json',
      'configs/phase1_v1.json','configs/phase3_science_v1.json']
    schemas={};missing=[]
    for rel in paths:
        p=ROOT/rel
        if not p.is_file():missing.append(rel);continue
        schema={'sha256':digest(p),'bytes':p.stat().st_size}
        if p.suffix=='.csv':
            with p.open() as f:
                reader=csv.DictReader(f);schema['columns']=reader.fieldnames;schema['rows']=sum(1 for _ in reader)
        else:
            val=json.loads(p.read_text());schema['type']=type(val).__name__
            schema['fields']=list(val[0]) if isinstance(val,list) and val else list(val)
        schemas[rel]=schema
    # Inspect compressed NPY headers, not full individual arrays.
    import numpy as np
    examples={}
    for label,folder,name in [('HA','phase1_epochs_001','epochs.npz'),('MFF','phase3_ci_epochs_001','epochs_roi.npz')]:
        p=next(iter(sorted((ROOT/'results'/folder).glob('*/'+name))),None)
        if p is None:missing.append(folder+'/'+name);continue
        columns={}
        with zipfile.ZipFile(p) as archive:
            for member in archive.namelist():
                with archive.open(member) as f:
                    version=np.lib.format.read_magic(f)
                    assert version in [(1,0),(2,0)],version
                    header_reader=np.lib.format.read_array_header_1_0 if version==(1,0) else np.lib.format.read_array_header_2_0
                    shape,fortran,dtype=header_reader(f)
                    columns[member]={'shape':shape,'dtype':str(dtype)}
        examples[label]=columns
    disk=shutil.disk_usage(ROOT)
    gitroot=ROOT.parent/'auditory_github'
    commit=subprocess.check_output(['git','-C',str(gitroot),'rev-parse','HEAD'],text=True).strip()
    status=subprocess.check_output(['git','-C',str(gitroot),'status','--porcelain'],text=True)
    release=json.loads((gitroot/'release/manifest.json').read_text())
    delta=[]
    for e in release['files']:
        if not e['path'].startswith(('scripts/','configs/')):continue
        p=ROOT/e['path']
        if p.is_file() and e.get('source_sha256') and digest(p)!=e['source_sha256']:
            delta.append(e['path'])
    environment={'python':sys.version,'executable':sys.executable,'platform':platform.platform(),
        'packages':packages,'torch':torch_info,'disk_free_bytes':disk.free,
        'job_id':os.environ['SLURM_JOB_ID'],'git_checkout':str(gitroot),'actual_commit':commit,'git_status':status,
        'reference_commit':'aac4c366fdaf23507cc5d8b6510f675ae7af615b'}
    write_json(priv/'environment.lock.json',environment)
    write_json(priv/'input_contract.json',{'status':'PASS' if not missing else 'BLOCKED_INPUT','schemas':schemas,'epoch_schemas':examples,'missing':missing,'plan_sha256':digest(plan)})
    write_json(priv/'source_snapshot_delta.json',{'changed_original_analysis_sources':delta,'git_commit_matches_plan':commit==environment['reference_commit'],'working_workspace_is_git_checkout':False})
    report=ROOT/'reports/auditory5_v1/snapshot_delta.md'
    report.write_text('# Snapshot delta\n\nThe active scientific workspace is separate from the curated Git checkout. Original source hashes were compared with the publication manifest\'s source hashes, not the publication-adapted hashes. No reset or checkout was performed.\n\n'+f'Reference and actual publication commit: `{commit}`. Changed original code/config files: {len(delta)}.\n\n'+'The five-ideas plan and auditory5 implementation are new work. Existing Phase 0–3 outputs remain read-only. Full schema and environment records are restricted.\n')
    summary={'stage':'S0','status':'PASS' if not missing and not delta else 'REVIEW_REQUIRED',
        'job_id':os.environ['SLURM_JOB_ID'],'required_files_verified':len(schemas),'missing_files':missing,
        'original_code_config_changes':len(delta),'plan_sha256':digest(plan),'packages':packages,'torch':torch_info,
        'data_scope':'HA and canonical MFF local inputs present; no new scientific outcomes evaluated'}
    write_json(out/'summary.json',summary)
    print(json.dumps(summary,indent=2))


if __name__=='__main__':main()
