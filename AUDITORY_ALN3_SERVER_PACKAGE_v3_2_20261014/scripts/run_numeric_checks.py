#!/usr/bin/env python3
from pathlib import Path
import argparse,json,sys
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from aln32_reference.schedules import legacy_coverage
from aln32_reference.geometry import support_counts
from aln32_reference.diagnostics import phase_coordinate_example,query_content_diagnostic

def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    q=np.linspace(0,2*np.pi,40)
    timeonly=np.tile(np.stack([np.sin(q),np.cos(q)],-1)[None],(30,1,1))
    out={'scope':'Independent arithmetic and synthetic data only; no EEG/backbone training',
         'legacy_schedule':{'reve':legacy_coverage(22,50),'cbramod':legacy_coverage(12,100)},
         'reve_nonblock_llrd':.75**22,
         'input_support':{'128Hz':support_counts(128),'100Hz':support_counts(100)},
         'phase_example':phase_coordinate_example(),
         'time_only_output':query_content_diagnostic(timeonly)}
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'reve_open':out['legacy_schedule']['reve']['final_open_blocks'],
                      'phase_example':out['phase_example']},ensure_ascii=False))
if __name__=='__main__':main()
