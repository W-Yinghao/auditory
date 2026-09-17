"""Structural publication boundary check; no automatic publication."""
import json
import re
from io import StringIO
from pathlib import Path
import pandas as pd
from .provenance import ROOT,digest,write_json,finish,require_slurm

DISALLOWED_FIELDS={'trial_id','record_id','candidate_id','split_group_id','original_path',
                   'source_path','p0','p1','logit','prediction','model_weights'}
ALLOWED_SUFFIXES={'.json','.csv','.md','.png','.pdf','.svg'}


def text_findings(text, identifiers):
    findings=[]
    if set(re.findall(r'[\w:.-]+',text)) & identifiers:
        findings.append('KNOWN_INDIVIDUAL_IDENTIFIER')
    if re.search(r'/(?:home|projects|mnt|tmp)/',text):
        findings.append('ABSOLUTE_FILESYSTEM_PATH')
    return findings


def structured_fields(value):
    if isinstance(value,dict):
        keys=set(value)
        for item in value.values():keys.update(structured_fields(item))
        return keys
    if isinstance(value,list):
        keys=set()
        for item in value:keys.update(structured_fields(item))
        return keys
    return set()


def csv_fields(text):
    # A withheld model family can leave an explicitly empty intermediate CSV.
    return set() if not text.strip() else set(pd.read_csv(StringIO(text),nrows=0).columns)


def run(config,registry,site,dest,public,report,source_run=None):
    require_slurm()
    if not source_run or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-' for c in source_run):
        raise ValueError('PUBLIC_AUDIT_EXPLICIT_FINAL_RUN')
    sources=[ROOT/base/'auditory_next_v2'/source_run for base in ('results','reports')]
    history=ROOT/'private/auditory_next_v2'/registry['support_run']/'full_event_history.parquet'
    fields=['trial_id','record_id','candidate_id','split_group_id']
    ids=pd.read_parquet(history,columns=fields)
    identifiers=set(str(v) for col in fields for v in ids[col].dropna().unique())
    if any(len(v)<6 for v in identifiers):raise ValueError('IDENTIFIER_SCAN_SHORT_TOKEN_REQUIRES_REVIEW')
    evidence=[];manifest=[];content_hashes={}
    for folder in sources:
        if not folder.is_dir():raise ValueError('PUBLIC_FINAL_DIRECTORY_REQUIRED')
        for path in sorted(folder.rglob('*')):
            if path.is_symlink():
                evidence.append(dict(path=str(path),finding='SYMLINK'));continue
            if not path.is_file():continue
            logical=str(path.relative_to(ROOT));content_hashes[logical]=digest(path)
            findings=[]
            if path.suffix.lower() not in ALLOWED_SUFFIXES:findings.append('UNAPPROVED_PUBLIC_FILE_TYPE')
            if path.suffix in ('.csv','.json','.md','.svg'):
                text=path.read_text()
                findings.extend(text_findings(text,identifiers))
                if path.suffix=='.csv':
                    cols=csv_fields(text)
                    if DISALLOWED_FIELDS & set(cols):findings.append('INDIVIDUAL_OR_PREDICTION_COLUMNS')
                elif path.suffix=='.json':
                    if DISALLOWED_FIELDS & structured_fields(json.loads(text)):
                        findings.append('INDIVIDUAL_OR_PREDICTION_FIELDS')
            evidence.extend(dict(path=str(path),finding=f) for f in findings)
            manifest.append(dict(artifact=logical,sha256=content_hashes[logical],bytes=path.stat().st_size))
    write_json(dest/'findings.json',evidence)
    write_json(dest/'input_hashes.json',dict(history_sha256=digest(history),artifacts=content_hashes))
    pd.DataFrame(manifest).to_csv(public/'audited_artifact_hashes.csv',index=False)
    (report/'PUBLIC_BOUNDARY_AUDIT.md').write_text('# 聚合产物边界检查\n\n检查固定最终报告与结果的文件类型、结构字段、绝对路径及已知受限试次/记录/身份标识。'
        '图像和PDF不作OCR；临床姓名及未知标识不在本扫描保证范围内。本轮没有自动对外发布。\n')
    return finish(dest,public,dict(status='PASS' if not evidence else 'PUBLIC_BOUNDARY_FINDINGS',
        source_run=source_run,files_checked=len(manifest),finding_count=len(evidence),new_fits=0,
        scan_scope='structural and known restricted identifiers; no image OCR or general anonymization guarantee',
        external_publication=False))
