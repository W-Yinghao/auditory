#!/usr/bin/env python3
"""Summarize verified Federici identities; no HC/HC-v filename pairing."""
from pathlib import Path
import argparse,hashlib,json,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
import pandas as pd
from aln3_reference.aggregation import summarize_conditions,independent_group_contrasts,phantom_sessions

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input",type=Path,required=True);p.add_argument("--output-dir",type=Path,required=True)
    p.add_argument("--n-boot",type=int,default=4000);p.add_argument("--seed",type=int,default=3401)
    a=p.parse_args()
    if a.output_dir.exists() and any(a.output_dir.iterdir()):
        raise SystemExit("Output directory is not empty; use a new versioned directory")
    df=pd.read_csv(a.input)
    if set(df.dataset)!={"federici"}:raise SystemExit("This entry point only accepts Federici")
    outputs={"summary_by_condition.json":summarize_conditions(df,a.n_boot,a.seed),
             "independent_group_contrasts.json":independent_group_contrasts(df,n_boot=a.n_boot,seed=a.seed),
             "phantom_sessions.json":phantom_sessions(df)}
    receipt={"version":"ALN3.1","input_sha256":hashlib.sha256(a.input.read_bytes()).hexdigest(),
             "n_input_rows":len(df),"human_identities":int(df[df.entity_type=="human"].subject_uid.nunique()),
             "phantom_identities":int(df[df.entity_type=="phantom"].subject_uid.nunique()),
             "identity_source":"supplied_metadata_not_inferred","HC_HCv_design":"independent_groups",
             "note":"No same-child HC-HCv contrast; no pooled human/phantom population result."}
    outputs["receipt.json"]=receipt;a.output_dir.mkdir(parents=True,exist_ok=True)
    for name,obj in outputs.items():(a.output_dir/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+"\n")
    print(json.dumps(receipt,ensure_ascii=False))
if __name__=="__main__":main()
