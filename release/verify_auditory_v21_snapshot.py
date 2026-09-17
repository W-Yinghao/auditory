"""Verify the curated v2.1 release via Slurm; no model fits or EEG array reads.

Optional private dictionaries/snapshot metadata strengthen local verification.
Only counts and public paths enter the release receipt.
"""
import argparse
import ast
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
from urllib.parse import unquote
import xml.etree.ElementTree as ET


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--known-names',type=Path)
    parser.add_argument('--identifier-table',type=Path)
    parser.add_argument('--science-root',type=Path)
    parser.add_argument('--previous-manifest',type=Path)
    args=parser.parse_args()
    if not os.environ.get('SLURM_JOB_ID'):raise RuntimeError('SLURM_REQUIRED')
    os.umask(0o077)
    root=Path(__file__).resolve().parents[1]
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    manifest=json.loads((root/'release/manifest.json').read_text())
    changes=json.loads((root/'release/auditory_v21_publication_changes.json').read_text())
    entries={e['path']:e for e in manifest['files']}
    allowed=set(entries)|set(manifest['self_exclusions'])
    names=json.loads(args.known_names.read_text()) if args.known_names else []
    identifiers=set()
    if args.identifier_table:
        import pandas as pd
        frame=pd.read_parquet(args.identifier_table,columns=['trial_id','record_id','candidate_id','split_group_id'])
        identifiers={str(v) for c in frame for v in frame[c].dropna().unique()}
        assert all(len(s)>=6 for s in identifiers)
    issues=[]
    def issue(rel,kind):issues.append(dict(path=rel,type=kind))
    blocked={'participant_id','recording_id','container_id','raw_name','source_row','source_worksheet_row','clinical_row_ref','unique_same_day_pid','absolute_path','raw_dob','candidate_id','split_group_id','record_id','trial_id','raw_locator_key','fit_groups','test_groups','validation_groups','train_groups','training_groups','signal_path','event_path','original_path','source_path','p0','p1','logit','prediction','model_weights'}
    count_fields={'fit_groups','test_groups','validation_groups','train_groups','training_groups'}
    opaque=re.compile(r'(?<![A-Za-z0-9])(?:B|P|G|M)[0-9a-f]{12,16}(?![A-Za-z0-9])')
    secret_patterns=[r'gh[pousr]_[A-Za-z0-9]{30,}',r'github_pat_[A-Za-z0-9_]{30,}',r'AKIA[A-Z0-9]{16}',r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----']
    counts=dict(python_files_parsed=0,slurm_scripts_syntax_checked=0,local_links_checked=0,pdfs_text_checked=0,pngs_structurally_checked=0,text_files_identifier_scanned=0)
    def inspect(value,rel):
        if isinstance(value,dict):
            bad=set(value)&blocked
            bad -= {k for k in bad&count_fields if type(value[k]) is int and value[k]>=0}
            if bad:issue(rel,'restricted_aggregate_fields')
            for v in value.values():inspect(v,rel)
        elif isinstance(value,list):
            for v in value:inspect(v,rel)
    for rel,e in entries.items():
        p=root/rel
        if p.is_symlink() or not p.is_file():issue(rel,'missing_or_symlink');continue
        blob=p.read_bytes()
        if sha(p)!=e['sha256'] or len(blob)!=e['bytes']:issue(rel,'manifest_mismatch')
        if len(blob)>10*1024*1024:issue(rel,'oversized_file')
        if p.suffix.lower() in {'.pt','.pth','.pkl','.parquet','.npz','.npy','.bdf','.edf','.set','.fdt','.mat','.xlsx','.xls'}:issue(rel,'restricted_extension')
        if p.suffix=='.pdf':
            from pdfminer.high_level import extract_text
            content=extract_text(str(p));counts['pdfs_text_checked']+=1
        elif p.suffix=='.png':
            from PIL import Image
            with Image.open(p) as im:
                im.verify();content=json.dumps(im.info,default=str)
            counts['pngs_structurally_checked']+=1
        else:
            try:content=blob.decode('utf-8')
            except UnicodeDecodeError:issue(rel,'unexpected_binary');continue
        if any(re.search(pattern,content) for pattern in secret_patterns):issue(rel,'credential_pattern')
        if any(name.casefold() in content.casefold() for name in names):issue(rel,'known_name')
        if set(re.findall(r'[\w:.-]+',content))&identifiers:issue(rel,'known_individual_identifier')
        counts['text_files_identifier_scanned']+=1
        if p.suffix=='.py':ast.parse(content,filename=rel);counts['python_files_parsed']+=1
        if p.suffix=='.sbatch':
            subprocess.run(['bash','-n',str(p)],check=True,capture_output=True);counts['slurm_scripts_syntax_checked']+=1
        if p.suffix=='.md':
            for link in re.findall(r'!?\[[^\]]+\]\(([^)]+)\)',content):
                target=unquote(link.split('#',1)[0].strip('<>'))
                if not target or re.match(r'^[a-z]+://',target):continue
                counts['local_links_checked']+=1
                if not (p.parent/target).exists():issue(rel,'broken_local_link:'+target)
        if rel.startswith(('results/auditory_v21/','reports/auditory_v21/')):
            if opaque.search(content):issue(rel,'opaque_individual_identifier')
            if re.search(r'/(?:home|projects|mnt|tmp)/',content):issue(rel,'absolute_path_in_aggregate')
            if p.suffix=='.json':inspect(json.loads(content),rel)
            if p.suffix=='.csv':
                reader=csv.DictReader(io.StringIO(content));rows=list(reader)
                bad=set(reader.fieldnames or [])&blocked
                bad-={k for k in bad&count_fields if rows and all(re.fullmatch(r'[0-9]+',r.get(k,'')) for r in rows)}
                if bad:issue(rel,'restricted_aggregate_columns')
    for p in root.rglob('*'):
        if not p.is_file() or '.git' in p.parts or '__pycache__' in p.parts or '.pytest_cache' in p.parts:continue
        rel=str(p.relative_to(root))
        if not rel.startswith('private/') and rel not in allowed:issue(rel,'outside_manifest')
    previous_preserved=0
    if args.previous_manifest:
        previous=json.loads(args.previous_manifest.read_text())
        editorial={'.gitignore','README.md','PUBLICATION.md','results/README.md','slurm/13_phase1_smoke.sbatch'}
        for e in previous['files']:
            if e['path'] in editorial:continue
            if sha(root/e['path'])!=e['sha256']:issue(e['path'],'historical_payload_changed')
            previous_preserved+=1
    exact=0
    for rel in changes['source_files']:
        if not rel.startswith('docs/'):
            if entries[rel]['sha256']!=entries[rel]['source_sha256']:issue(rel,'source_copy_mismatch')
            exact+=1
        if args.science_root and sha(args.science_root/rel)!=entries[rel]['source_sha256']:issue(rel,'source_changed_since_export')
    figure=json.loads((root/'reports/auditory_v21/figures_002/figure_receipt.json').read_text())
    for rel,h in figure['input_hashes'].items():
        if sha(root/rel)!=h:issue(rel,'figure_input_hash_mismatch')
    final=json.loads((root/'results/auditory_v21/final_001/summary.json').read_text())
    assert final['status']=='FINAL_AGGREGATE_COMPLETE' and not final['required_missing_runs'] and not final['required_failed_runs']
    test=json.loads((root/'results/auditory_v21/tests_009/summary.json').read_text())
    assert test['status']=='PASS' and test['tests']==59
    source_matched=0
    denominator=None
    if args.science_root:
        test_root=args.science_root/'private/auditory_v21/tests_009'
        start=json.loads((test_root/'start.json').read_text())
        for rel,h in start['source_hashes'].items():
            if not rel.endswith('.py') and not rel.endswith('ESTIMATOR_CONTRACT_DRAFT.md'):continue
            if rel not in entries:issue(rel,'tested_source_not_published');continue
            if entries[rel]['source_sha256']!=h:issue(rel,'tested_source_hash_mismatch')
            source_matched+=1
        junit=ET.parse(test_root/'tests.xml').getroot()
        if len(junit.findall('.//testcase'))!=59 or any(junit.findall('.//'+kind) for kind in ('failure','error','skipped')):issue('tests_009','test_evidence_invalid')
        if sha(test_root/'completion.json')!=sha(root/'results/auditory_v21/tests_009/summary.json'):issue('tests_009','test_receipt_mismatch')
        import pandas as pd
        bags=pd.read_parquet(args.science_root/'private/auditory_v21/n2_design_001/matched_bags.parquet',columns=['candidate_id','A_half'])
        half_counts=bags.groupby('candidate_id')['A_half'].nunique()
        design=json.loads((root/'results/auditory_v21/n2_design_001/N2_DESIGN_SUMMARY.json').read_text())
        # Total original-cohort denominator is independently recorded in the design output.
        def find_denominator(obj):
            if isinstance(obj,dict):
                if 'candidate_half_eligible_numerator' in obj:return obj['candidate_denominator']
                for value in obj.values():
                    found=find_denominator(value)
                    if found is not None:return found
            return None
        total=find_denominator(design)
        denominator=dict(original_design_candidates=total,candidates_with_any_matched_bag=int(len(half_counts)),
            both_halves=int((half_counts==2).sum()),one_half_only=int((half_counts==1).sum()),
            no_matched_half=total-int(len(half_counts)),eligible_candidate_halves=int(half_counts.sum()))
        assert denominator==dict(original_design_candidates=57,candidates_with_any_matched_bag=54,both_halves=49,one_half_only=5,no_matched_half=3,eligible_candidate_halves=103)
    report=dict(status='passed' if not issues else 'failed',job_id=os.environ['SLURM_JOB_ID'],files_hashed=len(entries),total_bytes=manifest['total_bytes'],
        **counts,known_name_dictionary_size=len(names),known_identifier_dictionary_size=len(identifiers),
        historical_payload_files_preserved=previous_preserved,v21_source_exact_copies_checked=exact,
        scientific_test_receipt=dict(run='tests_009',job_id=test['job_id'],tests=59,status='PASS',source_files_matched=source_matched,publication_rerun=False),
        n2_denominator_reconciliation=denominator,figure_inputs_matched=len(figure['input_hashes']),
        publication_new_model_fits=0,publication_new_encoder_fits=0,issues=issues,
        limits='Allowlist/content/hash checks are not a formal anonymization certificate. Tests are historical evidence matched to source; no participant models or raw analyses rerun. Exact staged content requires the separate index check.')
    (root/'release/verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
    return int(bool(issues))

if __name__=='__main__':raise SystemExit(main())
