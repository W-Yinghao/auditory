#!/usr/bin/env python3
"""Verify this handoff's static contracts and SHA256 inventory; never run production jobs."""
from __future__ import annotations
import argparse
import ast
import hashlib
import json
import sys
from pathlib import Path

BASELINE = "5d2960eee61a75c048f6b6ee3cef8427d945c3cd"
ORIGINAL_SHA = "eb9b343beb81994bf564a81b65577f0160547005a162db7894766e36e7971b2c"
ORIGINAL = "inherited/AUDITORY_ALN4_SERVER_PACKAGE_v4_1_20261021.zip"
EXCLUDED = {"MANIFEST.json", "SHA256SUMS"}
REQUIRED = [
    "README.md", "SERVER_START_PROMPT.md", "SERVER_FULL_DOCUMENT.md", "AGENTS_APPEND.md",
    "PACKAGE_METADATA.json", "requirements-tools.txt", ORIGINAL,
    "docs/00_STORY_AND_DECISIONS.md", "docs/01_EVIDENCE_BASELINE.md",
    "docs/02_EXECUTION_AND_BUDGET.md", "docs/03_SOURCE_LEARNING_DIAGNOSIS.md",
    "docs/04_PRIVATE_SUPPORT_AND_CROSS_STIM.md", "docs/05_PAIRED_RISK_AND_INFERENCE.md",
    "docs/06_EXTERNAL_COMPARISON_AND_CLOSURE.md", "docs/07_REPORTING_AND_HANDOFF.md",
    "plans/round2_continuation.json", "plans/round3_closure.json", "plans/decision_rules.json",
    "schemas/private_event_trace.schema.json", "schemas/source_probe_inputs.md",
    "tools/source_probe_metrics.py", "tools/paired_risk_summary.py",
    "tools/inspect_existing_state.py", "tools/verify_package.py",
    "tools/check_source_probe_metrics.py", "tools/check_paired_risk_summary.py",
    "tools/check_inspect_existing_state.py", "reports/LOCAL_VALIDATION.json",
    "reports/LOCAL_VALIDATION.md", "evidence/github_baseline.json",
    "evidence/external_sources.json", "evidence/inherited_aln41_evidence_ledger.json",
]
def sha(path):
    h=hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()

def verify(root: Path, structural_only: bool = False):
    errors, checked = [], []
    def require(condition, message):
        if not condition:
            errors.append(message)
    require(root.is_dir(), "package root is not a directory")
    for rel in REQUIRED:
        require((root/rel).is_file(), "missing required file: "+rel)
    if errors:
        return {"status":"FAIL", "errors":errors, "checked":[]}
    all_files = {}
    for path in sorted(root.rglob("*")):
        rel=path.relative_to(root).as_posix()
        require(not path.is_symlink(), "symlink not allowed: "+rel)
        require("__pycache__" not in path.parts and path.suffix != ".pyc", "bytecode not allowed: "+rel)
        if path.is_file():
            all_files[rel]=path
    for rel,path in all_files.items():
        try:
            if path.suffix == ".json":
                json.loads(path.read_text(encoding="utf-8"), parse_constant=lambda x: (_ for _ in ()).throw(ValueError("nonfinite JSON")))
            if path.suffix == ".py":
                ast.parse(path.read_text(encoding="utf-8"), filename=rel)
        except (ValueError,SyntaxError,UnicodeError) as exc:
            errors.append("parse failure "+rel+": "+str(exc))
    checked.append("all JSON parses strictly and all Python parses without executing imports")
    def load(rel):
        return json.loads((root/rel).read_text(encoding="utf-8"))
    try:
        meta=load("PACKAGE_METADATA.json")
        r2=load("plans/round2_continuation.json")
        r3=load("plans/round3_closure.json")
        require(meta["design_baseline"]==BASELINE, "metadata baseline drift")
        require(meta["research_rounds"]==[2,3] and meta["max_research_round"]==3 and meta["new_research_round"] is False, "research rounds drift")
        require(meta["journal_target"]=="Pattern Recognition", "journal target drift")
        require(meta["inherited_package"]["sha256"]==ORIGINAL_SHA and sha(root/ORIGINAL)==ORIGINAL_SHA, "original inherited ZIP hash mismatch")
        require(r2["source_arms"]==["TCS","TNCE","GCS","TCS_WRONG"], "R2 source arms drift")
        require(r2["core_arms"]==["B0","TCS","TNCE"], "R2 core arms drift")
        a=r2["aln41"]
        require(a["all_seeds"]==[3401,3407,3413] and a["r2_seeds"]==[3407,3413], "ALN41 seeds drift")
        require(a["existing_source_fits"]==8 and a["existing_private_ce_fits"]==30, "inherited training counts drift")
        require(a["new_source_fits"]==0 and a["new_private_ce_fits"]==0, "unregistered main training added")
        require(a["source_transfer_step"]==10000 and a["source_lr"]==0.0001, "R2 source selection drift")
        d=r2["source_diagnostic"]
        require(d["snapshots"]==[0,2500,5000,10000] and d["seed"]==3401, "source diagnostic panel drift")
        require(d["persistent_optimizer_updates"]==0 and d["gpu_hours_a100_equivalent_cap"]==4, "diagnostic update or cost drift")
        require(d["fit_episodes"]==32 and d["dev_episodes"]==32 and d["ridge_refit_per_snapshot"] is True, "source probe design drift")
        for key,n in (("support",20),("cross_stim",13)):
            family=r2[key]
            require(family["expected_members"]==n and len(family["semantic_index"])==n, key+" family size drift")
            require(len({x["id"] for x in family["semantic_index"]})==n, key+" duplicate semantic member")
        require(r2["support"]["u10_draw_seeds"]==[351410,351411,351412,351413,351414], "U10 sampling drift")
        require(r2["cross_stim"]["low_auc_flip_labels"] is False, "label flipping enabled")
        require(r2["net_risk"]["status"]=="post_R1_diagnostic" and r2["net_risk"]["original_families_preserved"] is True, "NET scope drift")
        ext=r3["external"]
        require(r3["research_round"]==3 and ext["seats"]==1 and ext["routes_mutually_exclusive"] is True, "external seat drift")
        units=len(ext["content_folds"])*len(ext["person_folds"])*len(ext["downstream_seeds"])
        require(units==10 and ext["public_downstream_fit_cap"]==10 and ext["downstream_seeds"]==[3401], "external unit budget drift")
        require(ext["new_source_pretraining_fit_cap"]==0 and ext["private_external_ft_fit_cap"]==0, "unregistered external pretraining/private FT")
        require(ext["routes"]["MindMix"]["full_encoder_downstream_fit_cap"]==10, "MindMix Stage3 budget drift")
        require(ext["routes"]["TransformerCLIP"]["full_encoder_downstream_fit_cap"]==0 and ext["routes"]["TransformerCLIP"]["frozen_readout_fit_cap"]==10, "frozen fallback budget drift")
        require(ext["dataset"]["doi"]=="10.5281/zenodo.3618205", "wrong DTU identity")
        require(r3["optional_ablation"]["enabled"] is False and r3["closure"]["automatic_round4"] is False, "unplanned research expansion")
        local=load("reports/LOCAL_VALIDATION.json")
        require(local["status"]=="PASS" and local["real_data_validation_performed"] is False, "local validation status/scope wrong")
        checked.append("research story, inherited counts, fixed families, diagnostics and R3 budgets")
        schema=load("schemas/private_event_trace.schema.json")
        def walk(value):
            if isinstance(value,dict):
                if "$ref" in value and value["$ref"].startswith("#/"):
                    obj=schema
                    for part in value["$ref"][2:].split("/"):
                        obj=obj[part.replace("~1","/").replace("~0","~")]
                for v in value.values(): walk(v)
            elif isinstance(value,list):
                for v in value: walk(v)
        walk(schema)
        checked.append("private-event schema internal references resolve; not full semantic schema validation")
    except (KeyError,ValueError,TypeError) as exc:
        errors.append("contract/schema validation failed: "+str(exc))
    if not structural_only:
        try:
            manifest=load("MANIFEST.json")
            entries=manifest["files"]
            require(set(entries)==set(all_files)-EXCLUDED, "manifest does not exactly cover package payload")
            for rel,record in entries.items():
                path=Path(rel)
                safe=not path.is_absolute() and ".." not in path.parts and rel not in EXCLUDED
                require(safe, "unsafe manifest path: "+rel)
                if safe and rel in all_files:
                    require(sha(all_files[rel])==record["sha256"], "hash mismatch: "+rel)
                    require(all_files[rel].stat().st_size==record["bytes"], "size mismatch: "+rel)
            sums={}
            for line in (root/"SHA256SUMS").read_text(encoding="utf-8").splitlines():
                digest,rel=line.split("  ",1)
                require(rel not in sums, "duplicate SHA256SUMS entry: "+rel)
                sums[rel]=digest
            require(set(sums)==set(all_files)-{"SHA256SUMS"}, "SHA256SUMS coverage mismatch")
            for rel,digest in sums.items():
                require(rel in all_files, "unknown SHA256SUMS file: "+rel)
                if rel in all_files:
                    require(sha(all_files[rel])==digest, "SHA256SUMS mismatch: "+rel)
            checked.append("full SHA256 manifest and SHA256SUMS including manifest")
        except (OSError,KeyError,ValueError,TypeError) as exc:
            errors.append("manifest validation failed: "+str(exc))
    else:
        checked.append("structural-only mode: no archive integrity claim")
    return {"schema":"aln42_package_verification_v1", "status":"FAIL" if errors else "PASS",
            "package_root":str(root), "files_seen":len(all_files), "structural_only":structural_only,
            "checked":checked, "errors":errors,
            "scope":"handoff static integrity only; no production model/data/server execution"}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root",type=Path,default=Path(__file__).resolve().parents[1])
    p.add_argument("--structural-only",action="store_true",help="builder-only; skips manifest integrity")
    args=p.parse_args()
    try:
        report=verify(args.root.resolve(),args.structural_only)
    except (OSError,ValueError) as exc:
        report={"status":"FAIL","errors":[str(exc)]}
    print(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False))
    return 0 if report["status"]=="PASS" else 2
if __name__=="__main__":
    sys.exit(main())

