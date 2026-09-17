import csv,json,os
from pathlib import Path
import numpy as np
from pymatreader import read_mat
BASE=Path(__file__).resolve().parents[1]
assert os.environ.get('SLURM_JOB_ID')
rows=list(csv.DictReader((BASE/'private/inventory_001/file_path_map.csv').open()))
def desc(x,depth=0):
    if depth>5:return str(type(x))
    if isinstance(x,dict):return {k:desc(v,depth+1) for k,v in x.items()}
    if isinstance(x,(list,tuple)):
        return {'len':len(x),'first':desc(x[0],depth+1) if x else None}
    if isinstance(x,np.ndarray):
        return {'shape':x.shape,'dtype':str(x.dtype),'first':desc(x.flat[0],depth+1) if x.size else None}
    if isinstance(x,np.generic):return x.item()
    return x
out={}; xml={}; refs=[]
for r in rows:
    p=Path(r['absolute_path'])
    if p.name.startswith('._'):continue
    if p.suffix=='.set' and 'set' not in out:out['set']={'file_id':r['file_id'],'schema':desc(read_mat(p))}
    if p.suffix=='.xml' and any(q.suffix=='.mff' for q in p.parents) and p.name not in xml:
        xml[p.name]={'file_id':r['file_id'],'text':p.read_text(errors='replace')[:14000]}
    if p.suffix in ('.pdf','.7z') or (p.suffix=='.txt' and 'ref' in p.parts):refs.append({'file_id':r['file_id'],'name':p.name})
(BASE/'private/layout_examples.json').write_text(json.dumps(out,ensure_ascii=False,indent=2,default=str))
(BASE/'private/xml_layout_examples.json').write_text(json.dumps(xml,ensure_ascii=False,indent=2))
(BASE/'private/reference_names.json').write_text(json.dumps(refs,ensure_ascii=False,indent=2))
