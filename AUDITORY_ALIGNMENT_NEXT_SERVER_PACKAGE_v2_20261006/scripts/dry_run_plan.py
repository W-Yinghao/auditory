#!/usr/bin/env python3
"""Inspect planned comparison units. This script never submits or trains."""
from __future__ import annotations
import argparse,json
from pathlib import Path
from make_plan import summarize

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan',type=Path,default=Path(__file__).resolve().parents[1]/'plans/planned_comparisons.jsonl')
    parser.add_argument('--family')
    parser.add_argument('--index',type=int)
    args=parser.parse_args()
    with args.plan.open(encoding='utf-8') as f:rows=[json.loads(l) for l in f if l.strip()]
    if args.family:rows=[r for r in rows if r['family_id']==args.family]
    if args.index is not None:
        if not 0<=args.index<len(rows):raise SystemExit('Index outside selected plan.')
        print(json.dumps(rows[args.index],ensure_ascii=False,indent=2))
    else:print(json.dumps(summarize(rows),ensure_ascii=False,indent=2))

if __name__=='__main__':main()
