#!/usr/bin/env python3
"""Inventory-driven schema discovery; all source content stays private."""
import csv, json, os, re, traceback, zipfile
from collections import Counter, defaultdict
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np
from scipy.io import whosmat, loadmat
import h5py, openpyxl

BASE=Path(__file__).resolve().parents[1]
assert os.environ.get('SLURM_JOB_ID'), 'Submit through Slurm'
OUT=BASE/'results/probe_001'; OUT.mkdir(exist_ok=False)
PRIV=BASE/'private/probe_001'; PRIV.mkdir(mode=0o700,exist_ok=False)
rows=list(csv.DictReader((BASE/'private/inventory_001/file_path_map.csv').open()))
def save(path,obj): path.write_text(json.dumps(obj,ensure_ascii=False,indent=2,default=str))
def local(x): return x.rsplit('}',1)[-1]
def shape(x):
    if isinstance(x,dict): return {k:shape(v) for k,v in x.items()}
    if isinstance(x,np.ndarray):
        if x.size<8:return {'shape':x.shape,'dtype':str(x.dtype),'values':x.tolist()}
        if x.dtype==object:return {'shape':x.shape,'first':shape(x.flat[0])}
        return {'shape':x.shape,'dtype':str(x.dtype)}
    if isinstance(x,list):return {'len':len(x),'first':shape(x[0]) if x else None}
    return x
errors=[]; mats=[]; workbooks=[]; documents=[]; mffs={}; bdfs=[]; info_counts=Counter()
for r in rows:
    p=Path(r['absolute_path']); ext=p.suffix.lower(); fid=r['file_id']
    try:
        if ext in ('.set','.mat'):
            item={'file_id':fid,'suffix':ext,'bytes':p.stat().st_size}
            if h5py.is_hdf5(p):
                with h5py.File(p) as f:
                    ds=[]
                    f.visititems(lambda n,x: ds.append({'key':n,'shape':x.shape,'dtype':str(x.dtype)}) if isinstance(x,h5py.Dataset) else None)
                    item['hdf5']=ds[:1000]
            else:
                item['variables']=whosmat(p)
                if ext=='.set':
                    d=loadmat(p,simplify_cells=True); item['schema']=shape(d)
                    save(PRIV/(fid+'.set_schema.json'),item['schema'])
                    item.pop('schema')
            mats.append(item)
        if ext=='.xlsx':
            wb=openpyxl.load_workbook(p,read_only=True,data_only=True)
            wi={'file_id':fid,'sheets':[]}
            for si,s in enumerate(wb):
                vals=[list(x) for x in s.iter_rows(values_only=True)]
                save(PRIV/(fid+f'_sheet{si}.json'),{'title':s.title,'rows':vals})
                wi['sheets'].append({'sheet_index':si,'title':s.title,'rows':s.max_row,'columns':s.max_column,'first_rows':vals[:4]})
            workbooks.append(wi); wb.close()
        if ext=='.docx':
            with zipfile.ZipFile(p) as z: root=ET.fromstring(z.read('word/document.xml'))
            paras=[''.join(e.itertext()) for e in root.iter() if local(e.tag)=='t']
            save(PRIV/(fid+'.document.json'),paras); documents.append({'file_id':fid,'suffix':ext,'text_parts':len(paras)})
        if ext=='.bdf':
            with p.open('rb') as f: h=f.read(256)
            bdfs.append({'file_id':fid,'file_role_name':p.name,'header_bytes':h[184:192].decode(errors='replace'),'n_records':h[236:244].decode(errors='replace'),'record_duration':h[244:252].decode(errors='replace'),'n_channels':h[252:256].decode(errors='replace')})
        for par in p.parents:
            if par.suffix.lower()=='.mff':
                if par not in mffs: mffs[par]=[]
                mffs[par].append(p); break
    except Exception as e:errors.append({'file_id':fid,'error':repr(e),'trace':traceback.format_exc()})
save(PRIV/'workbook_schemas.json',workbooks);save(OUT/'mat_schemas.json',mats)
save(PRIV/'bdf_headers.json',bdfs);save(PRIV/'errors.json',errors)
registry=[]; examples={}; mffsummary=[]
for i,(p,files) in enumerate(sorted(mffs.items(),key=lambda x:str(x[0])),1):
    mid=f'M{i:04d}';registry.append({'container_id':mid,'path':str(p),'file_ids':[r['file_id'] for r in rows if Path(r['absolute_path']) in files]})
    item={'container_id':mid,'n_files':len(files),'bytes':sum(f.stat().st_size for f in files),'basenames':dict(Counter(f.name for f in files))}
    for f in files:
        if f.suffix=='.xml':
            try:
                root=ET.parse(f).getroot(); key=f.name
                info_counts[key]+=1
                if key not in examples:examples[key]={'container_id':mid,'text':f.read_text()[:60000]}
                if key in ('epochs.xml','categories.xml','info.xml','info1.xml','sensorLayout.xml'):
                    vals=defaultdict(list)
                    for el in root.iter():
                        if el.text and el.text.strip(): vals[local(el.tag)].append(el.text.strip())
                    item[key]={k:dict(Counter(v)) for k,v in vals.items() if k not in ('recordTime','name','comment','label','subject')}
            except Exception as e:errors.append({'container_id':mid,'xml':f.name,'error':repr(e)})
    mffsummary.append(item)
save(PRIV/'mff_registry.json',registry);save(PRIV/'xml_examples.json',examples);save(PRIV/'mff_metadata.json',mffsummary)
save(OUT/'probe_summary.json',{'job_id':os.environ['SLURM_JOB_ID'],'mff_containers':len(mffs),'xml_basenames':info_counts,'mat_files':len(mats),'bdf_files':len(bdfs),'workbooks':[{'file_id':w['file_id'],'sheets':[{k:v for k,v in s.items() if k not in ('title','first_rows')} for s in w['sheets']]} for w in workbooks],'documents':documents,'errors':len(errors)})
print(json.dumps({'mff_containers':len(mffs),'mat_files':len(mats),'errors':len(errors)}))
