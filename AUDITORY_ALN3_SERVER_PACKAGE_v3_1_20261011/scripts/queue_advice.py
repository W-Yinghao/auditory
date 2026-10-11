#!/usr/bin/env python3
"""Offline ALN3.1 queue advice. NO Slurm, network, process, or filesystem deletion.

Input must be a server-exported JSONL ledger. It is not read from a live queue.
Performance fields, if present, are never used to decide scheduling.
"""
from pathlib import Path
import argparse,json
STATES={'planned','pending','running','completed','failed','held'}

def advise(row:dict, ready_aln3_work:bool=True)->dict:
    needed={'job_id','category','state','interface_valid','dependencies_ready','essential_control','compatible_result_exists'}
    if not needed.issubset(row):raise ValueError(f'Missing fields: {sorted(needed-set(row))}')
    if row['state'] not in STATES or not str(row['job_id']).strip():raise ValueError('Invalid state/job_id')
    for k in ('interface_valid','dependencies_ready','essential_control','compatible_result_exists'):
        if type(row[k]) is not bool:raise ValueError(f'{k} must be a boolean')
    c,s=row['category'],row['state']
    out={'job_id':str(row['job_id']),'category':c,'state':s,'side_effects':False}
    def result(action,reason):return {**out,'advice':action,'reason':reason}
    if s=='completed':
        if not row['interface_valid']:return result('preserve_legacy_exclude_primary','Known-invalid interface; preserve history')
        return result('preserve_reuse_if_contract_matches','Do not retrain for a package version change')
    if not row['interface_valid']:return result('pause_affected_repair_only','Engineering failure, not scientific null')
    if s=='running':
        if c=='item2_fm_legacy' and not row['essential_control'] and ready_aln3_work:
            return result('checkpoint_and_defer_if_blocking','Let near-complete jobs finish when this does not block ready work')
        return result('continue_valid_running','Do not interrupt valid work merely for new package metadata')
    if c=='item3bc':return result('map_into_B_no_duplicate','Register old/new comparison and recipe change')
    if row['compatible_result_exists']:return result('reuse_skip_duplicate','Compatibility must be verified by server contract hashes')
    if c=='item2_fm_legacy' and not row['essential_control']:
        return result('defer_reversible_backlog','No new blanket old-interface seed repetitions')
    if s=='failed':return result('resume_after_cause_check','Do not count infrastructure failure as scientific result')
    if not row['dependencies_ready']:return result('wait_only_own_dependencies','Other independent families continue')
    if c in {'item2_small','aln3_core','aln3_panel','item3a','science'} or row['essential_control']:
        return result('run_when_resource_available','Authorized full experiment or necessary paired control; no performance gate')
    if c=='resource_extension':return result('nonblocking_extension','Must not delay core training')
    return result('classify_without_changing_queue','Unknown category; no automatic cancellation')

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--input',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--no-ready-aln3-work',action='store_true');a=p.parse_args()
    if a.output.exists():raise SystemExit('Refuse overwrite; use a new advice path')
    rows=[json.loads(x) for x in a.input.read_text().splitlines() if x.strip()]
    ids=[str(x['job_id']) for x in rows]
    if len(ids)!=len(set(ids)):raise ValueError('Duplicate job IDs')
    out=[advise(r,not a.no_ready_aln3_work) for r in rows]
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in out))
    print(json.dumps({'rows':len(out),'side_effects':False,'live_queue_read':False}))
if __name__=='__main__':main()
