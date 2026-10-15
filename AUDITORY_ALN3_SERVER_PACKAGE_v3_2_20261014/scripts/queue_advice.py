#!/usr/bin/env python3
"""Print JSONL advice only; neither cancel nor submit jobs."""
from pathlib import Path
import argparse,json,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from aln32_reference.queue_policy import advise

def main():
    p=argparse.ArgumentParser();p.add_argument('input',type=Path);p.add_argument('--out',type=Path)
    a=p.parse_args();result=[]
    for no,line in enumerate(a.input.read_text().splitlines(),1):
        if not line.strip():continue
        try:result.append(advise(json.loads(line)))
        except (ValueError,TypeError) as e:raise SystemExit(f'Invalid JSONL row {no}: {e}')
    text='\n'.join(json.dumps(x,ensure_ascii=False) for x in result)+'\n'
    if a.out:
        if a.out.resolve()==a.input.resolve():raise SystemExit('Refusing to overwrite source queue')
        a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(text)
    else:print(text,end='')
if __name__=='__main__':main()
