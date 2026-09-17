#!/usr/bin/env python3
import csv,hashlib,json,re
from collections import Counter,defaultdict
from pathlib import Path
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parents[1]; S=R/'private/probe_001'; O=R/'results/clinical_001'; P=R/'private/clinical_001'; C='file_e254c9a75c971ac7d4e76bf6df2b4030'
def n(v): return re.sub(r'\s+',' ',str(v).strip()).lower() if v is not None else ''
def x(v):
    if isinstance(v,(int,float)) and not isinstance(v,bool): return float(v)
    m=re.fullmatch(r'[-+]?\d+(?:\.\d+)?',n(v).replace(',','')); return float(m.group()) if m else None
def main():
    O.mkdir(parents=True,exist_ok=True); P.mkdir(parents=True,exist_ok=True); out={'source':'generated sheet JSON only','books':[],'warnings':[]}; books=defaultdict(list)
    for p in S.glob('file_*_sheet*.json'):
        m=re.match(r'(file_[0-9a-f]+)_sheet(\d+)\.json$',p.name)
        if m: books[m.group(1)].append((int(m.group(2)),p))
    for b,ps in sorted(books.items()):
        sh=[]; rh=Counter(); it=0; fc=Counter(); fcl=defaultdict(set)
        for i,p in sorted(ps):
            d=json.loads(p.read_text(encoding='utf-8')); a=d.get('rows',[]); h=a[0] if a else []; z=[r for r in a[1:] if any(n(v) for v in r)]; ni=next((j for j,v in enumerate(h) if n(v) in ('name','姓名')),None); it+=sum(bool(ni is not None and ni<len(r) and n(r[ni])) for r in z)
            for r in z: rh[hashlib.sha256('\x1f'.join(n(v) for v in r).encode()).hexdigest()]+=1
            for j,hv in enumerate(h):
                if hv is not None: fc[str(hv)] += sum(bool(n(r[j] if j<len(r) else None)) for r in z)
            if ni is not None:
                for r in z:
                    nh=hashlib.sha256(n(r[ni] if ni<len(r) else '').encode()).hexdigest()[:16]
                    for j,hv in enumerate(h):
                        if hv is not None and n(r[j] if j<len(r) else '') and any(t in str(hv) for t in ('CAP','SIR','IT-MAIS','MUSS')): fcl[str(hv)].add(nh)
            sh.append({'sheet_index':i,'title':d.get('title'),'rows_including_header':len(a),'nonempty_rows':len(z),'nonempty_identity_fields':sum(bool(ni is not None and ni<len(r) and n(r[ni])) for r in z),'columns':len(h),'headers':[str(v) if v is not None else '' for v in h]})
        out['books'].append({'file_id':b,'sha256_by_sheet':{str(i):hashlib.sha256(p.read_bytes()).hexdigest() for i,p in sorted(ps)},'sheets':sh,'nonempty_identity_fields':it,'nonempty_field_counts':dict(fc),'nonempty_field_candidate_clusters':{k:len(v) for k,v in fcl.items()},'duplicate_normalized_row_hashes':sum(v-1 for v in rh.values() if v>1)})
    rows=[]; fs=defaultdict(set); sc=[]
    for p in sorted(S.glob(C+'_sheet*.json')):
        d=json.loads(p.read_text(encoding='utf-8')); a=d.get('rows',[]); h=a[0] if a else []; z=[r for r in a[1:] if any(n(v) for v in r)]; sc.append({'title':d.get('title'),'rows_including_header':len(a),'nonempty_rows':len(z)})
        for v in h:
            if v is not None: fs[str(v)].add(str(d.get('title')))
        for ri,r in enumerate(a[1:],1):
            if not any(n(v) for v in r): continue
            q={str(v):r[j] if j<len(r) else None for j,v in enumerate(h) if v is not None}; nm=n(q.get('姓名')); q.update(_sheet=d.get('title'),_source_row=ri,_name_cluster=hashlib.sha256(nm.encode()).hexdigest()[:16] if nm else ''); rows.append(q)
    all_clinical_rows=rows
    rows=[r for r in rows if r['_sheet']=='Sheet1']
    def vals(k): return [x(r.get(k)) for r in rows if x(r.get(k)) is not None]
    def miss(k): return sum(not n(r.get(k)) for r in rows)
    age=vals('实际月龄'); dur=vals('HA使用时长（月）'); ks=('CAP得分','SIR得分','IT-MAIS/MAIS得分（%）','MUSS得分（%）'); sv={k:vals(k) for k in ks}; bg=defaultdict(list)
    for r in rows:
        if n(r.get('分组')): bg[n(r['分组'])].append(r)
    du=Counter((r['_name_cluster'],x(r.get('实际月龄')),x(r.get('HA使用时长（月）'))) for r in rows if r['_name_cluster'] and x(r.get('实际月龄')) is not None and x(r.get('HA使用时长（月）')) is not None)
    out['clinical']={'file_id':C,'primary_sheet':'Sheet1','sheet_counts':sc,'all_sheet_nonempty_rows':len(all_clinical_rows),'nonempty_rows':len(rows),'name_cluster_candidates':len({r['_name_cluster'] for r in rows if r['_name_cluster']}),'group_record_and_candidate_counts':{k:{'records':len(v),'name_cluster_candidates':len({r['_name_cluster'] for r in v if r['_name_cluster']})} for k,v in bg.items()},'fields':sorted(fs),'missing_counts':{k:miss(k) for k in ('实际月龄','HA使用时长（月）','每日佩戴时长',*ks)},'ranges':{'age_months':[min(age),max(age)] if age else None,'HA_duration_months':[min(dur),max(dur)] if dur else None},'scale_ranges':{k:[min(v),max(v)] if v else None for k,v in sv.items()},'scale_ceiling_counts':{'CAP_9':sum(v==9 for v in sv['CAP得分']),'SIR_5':sum(v==5 for v in sv['SIR得分']),'IT_MAIS_100':sum(v==100 for v in sv['IT-MAIS/MAIS得分（%）']),'MUSS_100':sum(v==100 for v in sv['MUSS得分（%）'])},'MUSS_87_count':sum(v==87 for v in sv['MUSS得分（%）']),'daily_wear_numeric_count':len(vals('每日佩戴时长')),'daily_wear_non_numeric_nonempty':sum(bool(n(r.get('每日佩戴时长'))) and x(r.get('每日佩戴时长')) is None for r in rows),'duration_negative_count':sum(v<0 for v in dur),'same_name_age_duration_duplicate_groups':sum(v>1 for v in du.values()),'same_name_age_duration_duplicate_rows':sum(v for v in du.values() if v>1)}
    with (P/'clinical_rows_clean.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=['name_cluster','sheet','source_row','group','age_months','HA_duration_months','MUSS','IT_MAIS_MAIS','CAP','SIR','daily_wear']); w.writeheader()
        for r in rows: w.writerow({'name_cluster':r['_name_cluster'],'sheet':r['_sheet'],'source_row':r['_source_row'],'group':r.get('分组',''),'age_months':r.get('实际月龄',''),'HA_duration_months':r.get('HA使用时长（月）',''),'MUSS':r.get('MUSS得分（%）',''),'IT_MAIS_MAIS':r.get('IT-MAIS/MAIS得分（%）',''),'CAP':r.get('CAP得分',''),'SIR':r.get('SIR得分',''),'daily_wear':r.get('每日佩戴时长','')})
    cs=sorted({r['_name_cluster'] for r in rows if r['_name_cluster']}); (P/'candidate_identity_map.csv').write_text('name_cluster,identity_status\n'+'\n'.join(f'{v},candidate_only' for v in cs)+'\n',encoding='utf-8'); (O/'clinical_summary.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
    with (O/'data_dictionary.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f); w.writerow(['field','observed_sheets','unit_or_definition','missing_count']); [w.writerow([k,'; '.join(sorted(fs[k])),'header-defined; verify convention',miss(k)]) for k in sorted(fs)]
    pairs=[(x(r.get('HA使用时长（月）')),x(r.get('实际月龄'))) for r in rows if x(r.get('HA使用时长（月）')) is not None and x(r.get('实际月龄')) is not None]
    fig,ax=plt.subplots(); ax.scatter([a for a,b in pairs],[b for a,b in pairs],s=10,alpha=.6); ax.set(xlabel='HA use duration (months)',ylabel='Age (months)'); fig.tight_layout(); fig.savefig(O/'age_duration.png',dpi=140); plt.close(fig)
    fig,ax=plt.subplots(); [ax.hist(v,bins=12,alpha=.45,label=k.split('（')[0]) for k,v in sv.items() if v]; ax.set_xlabel('score'); ax.legend(fontsize=7); fig.tight_layout(); fig.savefig(O/'scale_distributions.png',dpi=140); plt.close(fig)
if __name__=='__main__': main()
