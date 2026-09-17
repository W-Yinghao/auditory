import csv,json,os,subprocess,traceback
from pathlib import Path
from collections import Counter,defaultdict
from pdfminer.high_level import extract_text
from audit_mff import dump,table
BASE=Path(__file__).resolve().parents[1]
assert os.environ.get('SLURM_JOB_ID')
out=BASE/'results/supporting_001';out.mkdir(exist_ok=False)
private=BASE/'private/supporting_001';private.mkdir(mode=0o700,exist_ok=False)
rows=list(csv.DictReader((BASE/'private/inventory_001/file_path_map.csv').open()))
summaries=[];jsons=[];texts=[];errors=[];other=Counter()
for r in rows:
    p=Path(r['absolute_path']);ext=p.suffix.lower();fid=r['file_id']
    if p.name.startswith('._'):other['appledouble_sidecars']+=1;continue
    try:
        if ext=='.pdf':
            text=extract_text(str(p));(private/(fid+'.txt')).write_text(text)
            summaries.append({'file_id':fid,'type':'pdf','text_characters':len(text),'status':'text_extracted'})
        elif ext=='.7z':
            proc=subprocess.run(['/home/infres/yinwang/anaconda3/bin/bsdtar','-tvf',str(p)],capture_output=True,text=True)
            (private/(fid+'.archive_listing.txt')).write_text(proc.stdout);(private/(fid+'.archive_errors.txt')).write_text(proc.stderr)
            summaries.append({'file_id':fid,'type':'7z','status':'listed' if proc.returncode==0 else 'list_error','entries':len(proc.stdout.splitlines())})
        elif ext=='.json':
            obj=json.loads(p.read_text());jsons.append({'file_id':fid,'basename':p.name,'data':obj})
            summaries.append({'file_id':fid,'type':'json','status':'parsed','top_level_type':type(obj).__name__,'n_keys_or_items':len(obj) if isinstance(obj,(dict,list)) else 0})
        elif ext in ('.txt','.log','.rtf'):
            with p.open('rb') as f:head=f.read(1600).decode(errors='replace')
            texts.append({'file_id':fid,'basename':p.name,'bytes':p.stat().st_size,'first_bytes':head})
            other['text_headers_inspected']+=1
        elif ext in ('.png','.avi'):other[ext+'_not_interpreted']+=1
    except Exception as e:errors.append({'file_id':fid,'error':repr(e),'trace':traceback.format_exc()})
dump(private/'json_contents.json',jsons);dump(private/'text_headers.json',texts);dump(private/'errors.json',errors)
table(out/'document_index.csv',summaries)
dump(out/'summary.json',{'job_id':os.environ['SLURM_JOB_ID'],'counts':other,'pdfs':sum(r['type']=='pdf' for r in summaries),'archives':[r for r in summaries if r['type']=='7z'],'jsons':len(jsons),'errors':len(errors)})
