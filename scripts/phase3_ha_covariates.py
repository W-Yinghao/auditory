#!/usr/bin/env python3
import csv,hashlib,json,os,re,datetime as dt
from collections import Counter,defaultdict
from pathlib import Path
import openpyxl
R=Path(__file__).resolve().parents[1];M=R/'private/inventory_001/file_path_map.csv';L=R/'private/phase2_cohort_001/linked_index.csv';O=R/'results/phase3_ha_covariates_004';P=R/'private/phase3_ha_covariates_004'
FID='file_e254c9a75c971ac7d4e76bf6df2b4030'
def norm(v):return re.sub(r'\s+',' ',str(v).strip()).lower() if v is not None else ''
def num(v):
 if isinstance(v,(int,float)) and not isinstance(v,bool):return float(v)
 m=re.fullmatch(r'[-+]?\d+(?:\.\d+)?',norm(v).replace(',',''));return float(m.group()) if m else None
def path():
 for r in csv.reader(M.open()):
  if r and r[0]==FID:return Path(r[3])
 raise FileNotFoundError(FID)
def pta(vals):return sum(vals)/4 if len(vals)==4 and all(v is not None for v in vals) else None
def main():
 assert os.getenv('SLURM_JOB_ID'),'Slurm required';O.mkdir(exist_ok=False,parents=True);P.mkdir(exist_ok=False,parents=True);src=path();wb=openpyxl.load_workbook(src,read_only=False,data_only=True);ws=wb['Sheet1'];rows=list(ws.iter_rows(values_only=True));h=list(rows[0]);
 exact={'r_unaided':[next(i for i,v in enumerate(h) if norm(v)==norm(f'右耳{f}Hz(裸耳)')) for f in (500,1000,2000,4000)],'l_unaided':[next(i for i,v in enumerate(h) if norm(v)==norm(f'左耳{f}Hz(裸耳)')) for f in (500,1000,2000,4000)],'r_aided':[next(i for i,v in enumerate(h) if norm(v)==norm(f'右耳{f}Hz(助听)')) for f in (500,1000,2000,4000)],'l_aided':[next(i for i,v in enumerate(h) if norm(v)==norm(f'左耳{f}Hz(助听)')) for f in (500,1000,2000,4000)]}
 header_evidence={k:[{'column':i+1,'header':h[i],'unit_evidence':'dBHL not explicit in this Sheet1 header; preserved as source label'} for i in v] for k,v in exact.items()}
 clinical=[];seq=0
 for rn,r in enumerate(rows[1:],2):
  if not any(norm(v) for v in r):continue
  seq+=1; u={k:[num(r[i]) for i in ix] for k,ix in exact.items()};u.update(source_row=rn,clinical_row_id=f'C{seq:04d}',group=str(r[0]) if r[0] is not None else '',r_unaided_pta=pta(u['r_unaided']),l_unaided_pta=pta(u['l_unaided']),better_unaided_pta=min([pta(u['r_unaided']),pta(u['l_unaided'])],default=None) if pta(u['r_unaided']) is not None and pta(u['l_unaided']) is not None else None,r_aided_pta=pta(u['r_aided']),l_aided_pta=pta(u['l_aided']),better_aided_pta=min([pta(u['r_aided']),pta(u['l_aided'])],default=None) if pta(u['r_aided']) is not None and pta(u['l_aided']) is not None else None,raw_values={k:[r[i] for i in ix] for k,ix in exact.items()});clinical.append(u)
 links=list(csv.DictReader(L.open()));by_c={r['clinical_row_id']:r for r in clinical};cand=[r for r in links if r['cohort']=='HA' and r['archival_association_candidate']=='True' and r['strong_unique_link']=='True' and r['eligible_measurement_identity_index']=='True'];
 eligpath=R/'results/phase2_archival_001/candidate_eligibility.csv'; eligible_ids=set()
 if eligpath.exists():
  eligible_ids={r['participant_id'] for r in csv.DictReader(eligpath.open()) if r.get('eligible')=='True'}
 def add_cov(r):
  c=by_c.get(r['clinical_row_id']);return {**r,'pta_status':('linked_complete_unaided' if c and c['better_unaided_pta'] is not None else 'not_available_or_unlinked'),'source_row':c['source_row'] if c else '','clinical_id_found':bool(c),'better_unaided_pta':c['better_unaided_pta'] if c else '','r_unaided_pta':c['r_unaided_pta'] if c else '','l_unaided_pta':c['l_unaided_pta'] if c else '','better_aided_pta':c['better_aided_pta'] if c else ''}
 cand_out=[add_cov(r) for r in cand];reps=defaultdict(list)
 for r in links:
  if r['cohort']=='HA' and r['participant_id']:reps[r['participant_id']].append(r)
 repeat=[]
 for pid,rs in reps.items():
  rs=sorted(rs,key=lambda r:r.get('vendor_exam_time','')); 
  for a,b in zip(rs,rs[1:]):
   try:elapsed=(dt.datetime.fromisoformat(b['vendor_exam_time'])-dt.datetime.fromisoformat(a['vendor_exam_time'])).total_seconds()/2629800
   except Exception:elapsed=None
   repeat.append({'participant_id':pid,'recording_a':a['recording_id'],'recording_b':b['recording_id'],'exam_time_a':a.get('vendor_exam_time',''),'exam_time_b':b.get('vendor_exam_time',''),'delta_age_months':num(b.get('clinical_age_months'))-num(a.get('clinical_age_months')) if num(b.get('clinical_age_months')) is not None and num(a.get('clinical_age_months')) is not None else '','delta_duration_months':num(b.get('duration_months'))-num(a.get('duration_months')) if num(b.get('duration_months')) is not None and num(a.get('duration_months')) is not None else '','elapsed_vendor_exam_months':elapsed,'age_minus_elapsed_months':(num(b.get('clinical_age_months'))-num(a.get('clinical_age_months'))-elapsed) if elapsed is not None and num(b.get('clinical_age_months')) is not None and num(a.get('clinical_age_months')) is not None else '','duration_minus_elapsed_months':(num(b.get('duration_months'))-num(a.get('duration_months'))-elapsed) if elapsed is not None and num(b.get('duration_months')) is not None and num(a.get('duration_months')) is not None else ''})
 with (P/'candidate_covariates.csv').open('w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=list(cand_out[0]) if cand_out else ['clinical_row_id']);w.writeheader();w.writerows(cand_out)
 with (P/'repeat_audit.csv').open('w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=list(repeat[0]) if repeat else ['participant_id']);w.writeheader();w.writerows(repeat)
 (P/'schema_evidence.json').write_text(json.dumps({'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'header_evidence':header_evidence},ensure_ascii=False,indent=2))
 def stats(key):
  v=sorted(x[key] for x in repeat if isinstance(x[key],(int,float)))
  return {'n':len(v),'min':min(v) if v else None,'median':v[len(v)//2] if v else None,'max':max(v) if v else None,'abs_gt_3_n':sum(abs(x)>3 for x in v)}
 model_out=[x for x in cand_out if x['participant_id'] in eligible_ids];summary={'job_id':os.environ['SLURM_JOB_ID'],'source_file_id':FID,'records_sheet1':len(clinical),'archival_HA_index_candidates':len(cand),'archival_HA_pta_complete_n':sum(x['pta_status']=='linked_complete_unaided' for x in cand_out),'archival_HA_pta_missing_or_unlinked_n':sum(x['pta_status']!='linked_complete_unaided' for x in cand_out),'actual_phase2_model_candidates':len(model_out),'actual_phase2_model_pta_complete_n':sum(x['pta_status']=='linked_complete_unaided' for x in model_out),'repeat_candidate_pairs':len(repeat),'repeat_participants':len({x['participant_id'] for x in repeat}),'repeat_delta_age_summary':stats('delta_age_months'),'repeat_delta_duration_summary':stats('delta_duration_months'),'repeat_elapsed_exam_summary':stats('elapsed_vendor_exam_months'),'repeat_age_minus_elapsed_summary':stats('age_minus_elapsed_months'),'repeat_duration_minus_elapsed_summary':stats('duration_minus_elapsed_months'),'repeat_exact_same_exam_time_pairs':sum(x['exam_time_a']==x['exam_time_b'] and x['exam_time_a']!='' for x in repeat),'units_note':'Source headers do not explicitly state dBHL for Sheet1 unaided columns; no SPL conversion performed. Non-numeric/NR values remain missing. Broader workbook headers that explicitly include dBHL are separate evidence and are not used to relabel Sheet1 values.','column_evidence':header_evidence}
 (O/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
