"""Aggregate completed outputs, create navigation tables/figures, and audit gaps."""
import csv,json,os,re,hashlib,shutil,zipfile
from collections import Counter,defaultdict
from pathlib import Path
import numpy as np
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pymatreader import read_mat
from audit_mff import table,dump,j
from audit_signals import preview
BASE=Path(__file__).resolve().parents[1]
assert os.environ.get('SLURM_JOB_ID')
out=BASE/'results/overview_001';out.mkdir(exist_ok=False);priv=BASE/'private/overview_001';priv.mkdir(mode=0o700,exist_ok=False)
figs=BASE/'figures/overview_001';figs.mkdir(exist_ok=False)
def readcsv(p):return list(csv.DictReader(p.open()))
mapping=readcsv(BASE/'private/inventory_001/file_path_map.csv');paths={r['file_id']:Path(r['absolute_path']) for r in mapping};inv=readcsv(BASE/'results/inventory_001/file_inventory.csv')
mff=readcsv(BASE/'results/mff_001/container_index.csv');recovery=readcsv(BASE/'results/mff_recovery_001/recovery_summary.csv');recids={r['container_id'] for r in recovery}
clinical=json.loads((BASE/'results/clinical_003/clinical_003_summary.json').read_text());link=json.loads((BASE/'results/linkage_001/summary.json').read_text());signal=json.loads((BASE/'results/signal_001/summary.json').read_text())
epochs=readcsv(BASE/'results/mff_001/epoch_ledger.csv');categories=readcsv(BASE/'results/mff_001/category_segment_ledger.csv')
epoch_stats=Counter((e['data_level'],e['label_status']) for e in epochs);statuses=Counter(s['status'] for s in categories)
levelrows=[]
for level in sorted(set(r['data_level'] for r in mff)):
 rr=[r for r in mff if r['data_level']==level];levelrows.append({'data_level':level,'containers':len(rr),'storage_epoch_entries':sum(int(r['n_storage_epochs'] or 0) for r in rr),'category_segment_entries':sum(int(r['n_category_segments'] or 0) for r in rr),'independent_sample_count':'unknown'})
table(out/'mff_level_counts.csv',levelrows)
correct_event_count=sum(int(r['n_events'] or 0) for r in mff if r['container_id'] not in recids)+sum(int(r['n_recovered_event_entries']) for r in recovery)
issues=[
 ('Q01','Clinical label timing','93 BDF exports, 95 clinical rows; dates in row names and vendor metadata support candidate matching, no separate scale assessment timestamp verified','Incremental concurrent function or longitudinal claims','Use candidate linkage for audit only; keep outcome tests gated'),
 ('Q02','Device state and sound level','Device suffixes and acquisition protocol documents do not establish device-on/off state or audibility for every recording','Device experience effects and group comparisons','Unknown strata; analyze only explicitly comparable conditions'),
 ('Q03','HA code 1/2 acoustic identity','Codes and approximate ratios exist; available protocol describes 800/1200 Hz but no explicit digital-code mapping established','Named standard/deviant and MMN interpretation','Retain numerical codes; do not infer mapping from counts'),
 ('Q04','BDF companion clocks','84 pairs have equal header times; 9 differ by -1,+1,+2 seconds; every annotation falls in signal duration','Raw event alignment','Use source metadata and independent timing evidence; no automatic shift chosen from EEG response'),
 ('Q05','Source identity','91 vendor PatientGUIDs but 78 leading-name candidates; 11 candidates have multiple GUIDs and 2 have DOB discrepancies','Child splits and longitudinal linkage','Do not split by export GUID; preserve conflicts and conservative subject grouping'),
 ('Q06','Processing versions','1160 nonempty MFF containers and 3843 history edges; historical filters/references/windows differ','All pooled analyses','Choose traceable parent/version; report sensitivity and known 40 ms offsets'),
 ('Q07','Broken SET companion pointer','One SET references a nonexistent FDT filename; a same-directory alternative may exist','That preprocessed signal','Audit alternative independently; do not silently replace its parent'),
 ('Q08','MAT arrays without axis dictionary','8 MATLAB TF arrays expose dimensions but no subject/trial/condition metadata','Feature reuse','Keep as legacy derived arrays; do not treat as epoch datasets'),
 ('Q09','Expanded CI clinical fields','Expanded workbook has nonempty scales and dates; association to signals and timing is not resolved','CI clinical route','Reconcile identities and instruments; prior assumption of no CI scales is obsolete'),
 ('Q10','Scale definitions','Mixed IT-MAIS/MAIS header, percentage scores, MUSS=87, CAP observed maximum 9, daily-use units missing','Endpoint selection','Do not merge instruments or interpret maximum without version evidence'),
 ('Q11','Scope of signal QC','Full SET payloads except broken pointer; 3 BDF previews, 13 MFF first-block previews','Task usability and cortical interpretation','Previews do not establish per-child reliability; formal P1 remains necessary'),
 ('Q12','Uninspected visual material','81 PNG and 2 AVI indexed; no content interpretation','Completeness of visual protocol evidence','Retain catalog; inspect targeted files if needed, without treating images/video as extra EEG acquisitions')]
table(BASE/'manifests/questions_to_resolve.csv',[dict(zip(['issue_id','topic','evidence','affected_analysis','next_action'],q),status='unresolved_or_scope_limit') for q in issues])
for name in ['participant_index','recording_index','files_to_recordings','clinical_link']:
 shutil.copyfile(BASE/f'results/linkage_001/{name}.csv',BASE/f'manifests/{name}.csv')
shutil.copyfile(BASE/'results/inventory_001/file_inventory.csv',BASE/'manifests/file_inventory.csv')
shutil.copyfile(BASE/'results/mff_001/container_index.csv',BASE/'manifests/mff_export_index.csv')
visits=[{'visit_id':'V'+r['recording_id'][1:],'recording_id':r['recording_id'],'participant_id':r['participant_id'],'visit_status':'candidate_acquisition_date','clinical_concurrence':'unknown','identity_status':'candidate'} for r in readcsv(BASE/'results/linkage_001/recording_index.csv')]
table(BASE/'manifests/visit_index.csv',visits)
# Use explicit scope rather than silently treating MFF files as independent acquisitions.
table(BASE/'manifests/cohort_support.csv',[
 {'branch':'BDF/vendor','unit':'paired_candidate_acquisition','count':93,'name_candidates':78,'confirmed_concurrent_scale_links':0},
 {'branch':'primary_clinical_table','unit':'clinical_record','count':95,'name_candidates':80,'confirmed_concurrent_scale_links':0},
 {'branch':'MFF','unit':'processing_export','count':1160,'name_candidates':'unknown','confirmed_concurrent_scale_links':'not_established'}])
fig,ax=plt.subplots(figsize=(10,4));ax.axis('off')
boxes=[(.02,.58,'All regular files\n23,166 / 255.0 GiB'),(.36,.74,'BDF: 93 signal + 93 event files\n93 candidate acquisitions'),(.36,.35,'MFF: 1,160 nonempty exports\n397 continuous / 248 epochs / 515 evoked'),(.72,.74,'Primary clinical: 95 records\n80 name candidates'),(.72,.30,'Concurrency and identity unresolved\n0 confirmed concurrent scale links')]
for x,y,t in boxes:ax.text(x,y,t,transform=ax.transAxes,fontsize=9,va='center',bbox=dict(boxstyle='round,pad=.6',fc='#edf4fa',ec='#427aa1'))
ax.set_title('Audit units and current matching status — counts are not interchangeable',fontsize=12);fig.tight_layout();fig.savefig(figs/'data_flow.png',dpi=160);plt.close(fig)
fig,axs=plt.subplots(1,2,figsize=(10,4));axs[0].bar([r['data_level'] for r in levelrows],[r['containers'] for r in levelrows]);axs[0].tick_params(axis='x',rotation=15);axs[0].set(ylabel='Processing exports',title='MFF export levels');axs[1].bar(list(statuses),list(statuses.values()));axs[1].set(ylabel='Category-segment entries across versions',title='Historical segment status; not fresh QC');fig.tight_layout();fig.savefig(figs/'mff_structure.png',dpi=150);plt.close(fig)
sets=readcsv(BASE/'results/other_eeg_001/set_index.csv');set_epochs=readcsv(BASE/'results/other_eeg_001/epoch_ledger.csv');zc=Counter(e['zero_label_status'] for e in set_epochs)
fig,ax=plt.subplots(figsize=(9,3.5));eeg=[r for r in sets if r['data_level']=='epochs'];lab=[f'E{i+1:02d}' for i in range(len(eeg))];a=[json.loads(r['event_code_counts']).get('1',0) for r in eeg];b=[json.loads(r['event_code_counts']).get('2',0) for r in eeg];ax.bar(lab,a,label='code 1');ax.bar(lab,b,bottom=a,label='code 2');ax.set(xlabel='Existing SET export (anonymous plot aliases)',ylabel='Event entries',title='Existing epoch exports: code identity retained, acoustic role unknown');ax.legend();fig.tight_layout();fig.savefig(figs/'epoch_code_counts.png',dpi=150);plt.close(fig)
table(out/'epoch_plot_aliases.csv',[{'plot_alias':a,'file_id':r['file_id']} for a,r in zip(lab,eeg)])
# Replot one representative actual epoched SET with an accurate processing caption.
if eeg:
 r=eeg[0];p=paths[r['file_id']];d=read_mat(p);d=d.get('EEG',d);data=np.memmap(p.parent/d['data'],dtype='<f4',mode='r',shape=(int(d['trials']),int(d['pnts']),int(d['nbchan'])));preview(data[0].T,float(d['srate']),r['file_id']+' | preprocessed epoch; no extra filtering',figs/'representative_epoch.png','EEGLAB native units',float(d['xmin']));del data
broken=[]
for r in sets:
 if r['companion_found']=='True':continue
 p=paths[r['file_id']];expected=4*int(r['n_channels'])*int(r['n_samples_per_epoch_or_continuous'])*max(1,int(r['n_epochs']));cands=[q for q in p.parent.glob('*.fdt') if q.stat().st_size==expected]
 broken.append({'file_id':r['file_id'],'alternative_fdt_size_matches':len(cands),'candidate_file_ids':[next((fid for fid,v in paths.items() if v==q),'') for q in cands],'status':'candidate_only_not_automatically_rebound'})
dump(out/'broken_companion_candidates.json',broken)
# Enumerate empty containers explicitly; regular-file inventory cannot register them.
root=Path('/projects/EEG-foundation-model/auditory');empty=[]
for base,dirs,files in os.walk(root,followlinks=False):
 p=Path(base)
 if p.suffix.lower()=='.mff' and not files and not dirs:empty.append(str(p))
dump(priv/'empty_mff_paths.json',empty)
with zipfile.ZipFile(BASE/'EEG_project_restart_EN_20260916_v1.zip') as z:archive_bad=z.testzip();archive_members=len(z.infolist())
summary={'job_id':os.environ['SLURM_JOB_ID'],'regular_files':len(inv),'bytes':sum(int(r['size_bytes']) for r in inv),'empty_mff_directories':len(empty),'mff_levels':levelrows,'mff_epoch_label_status':{'|'.join(k):v for k,v in epoch_stats.items()},'historical_category_segment_status':dict(statuses),'canonical_mff_event_entries':correct_event_count,'set_zero_label_status':dict(zc),'broken_set_companion_candidates':broken,'restart_archive_members':archive_members,'restart_zip_crc_ok':archive_bad is None}
dump(out/'summary.json',summary);print(j(summary))
