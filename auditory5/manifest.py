"""Outcome-blind reuse of audited identity, source and clinical contracts."""
import csv,json,re
from collections import Counter,defaultdict
from pathlib import Path
import numpy as np
import pandas as pd
from auditory5.provenance import ROOT,digest,object_hash,write_json,require_slurm


def readcsv(rel):
    with (ROOT/rel).open() as f:return list(csv.DictReader(f))


def true(x):return str(x).lower()=='true'


class IdentityGraph:
    def __init__(self):self.parent={};self.edges=[]
    def find(self,x):
        self.parent.setdefault(x,x)
        if self.parent[x]!=x:self.parent[x]=self.find(self.parent[x])
        return self.parent[x]
    def union(self,a,b,evidence):
        if not a or not b:raise ValueError('empty identity node')
        aa,bb=self.find(a),self.find(b)
        self.parent[max(aa,bb)]=min(aa,bb)
        self.edges.append({'a':a,'b':b,'evidence':evidence})
    def groups(self):
        components=defaultdict(list)
        for x in self.parent:components[self.find(x)].append(x)
        return {x:'G'+object_hash(sorted(v))[:16] for v in components.values() for x in v}


def build_manifest(config,run):
    require_slurm()
    priv=ROOT/config['paths']['private_relative']/'data'/run;priv.mkdir(parents=True,exist_ok=False)
    out=ROOT/config['paths']['aggregates_relative']/run;out.mkdir(parents=True,exist_ok=False)
    ha=readcsv('results/phase1_sources_001/source_manifest.csv')
    index={r['recording_id']:r for r in readcsv('results/phase2_cohort_001/index_recordings.csv')}
    lookup={r['file_id']:r['absolute_path'] for r in readcsv('private/inventory_001/file_path_map.csv')}
    sources=readcsv('results/phase3_ci_sources_001/source_manifest.csv')
    mffpaths={r['container_id']:r for r in readcsv('private/phase3_ci_sources_001/source_paths_and_tokens.csv')}
    labels={r['container_id']:r for r in readcsv('results/phase3_metadata_addendum_001/source_metadata.csv')}
    links=readcsv('results/phase3_ci_linkage_005/clinical_source_links.csv')
    graph=IdentityGraph()
    ridpid={r['recording_id']:r['participant_id'] for r in ha}
    for pid in ridpid.values():graph.find(pid)
    accepted=defaultdict(set)
    for r in links:
        if true(r['accepted_name_link']):
            accepted[r['canonical_container_id']].add(r['participant_id'])
    for s in sources:
        mid=s['canonical_container_id']
        graph.union('record:'+mid,'token:'+s['candidate_token_id'],'audited_source_identity_token_conservative_group_only')
        for pid in accepted[mid]:graph.union('record:'+mid,pid,'exact_full_name_candidate_including_date_mismatch')
    clinical_rows=readcsv('private/phase3_ci_clinical_004/candidate_rows_index.csv')
    overlap_edges=0
    for r in clinical_rows:
        if r['row_status']!='candidate_row':continue
        graph.find(r['participant_id'])
        for rid in re.findall(r'B[0-9a-f]{12}',r['vendor_overlap_recording_ids']):
            if rid in ridpid:
                graph.union(r['participant_id'],ridpid[rid],'audited_cross_archive_name_overlap_conservative')
                overlap_edges+=1
    gids=graph.groups()
    records=[];locators=[]
    for r in ha:
        rid=r['recording_id'];ix=index[rid]
        eligible=true(ix['eligible_measurement_identity_index']) and ix['cohort']=='HA'
        records.append(dict(candidate_id=r['participant_id'],split_group_id=gids[r['participant_id']],record_id=rid,
            canonical_record_id=rid,branch='HA_BDF',cohort_evidence=ix['cohort'],device_evidence='unknown',device_change_flag=False,
            dynamic_condition_unknown=True,paradigm_id='HA_literal_1_2',task_evidence_level='source_protocol_numeric_mapping_unconfirmed',
            index_record=true(ix['index_recording_flag']),identity_safe=not true(ix['identity_dob_conflict']),
            source_eligible=r['source_gate']=='eligible_technical_measurement',analysis_index=eligible,
            index_hold_reason=ix['index_hold_reason'],label_semantics='literal_only',
            code_map_hash=object_hash({'1':0,'2':1,'scope':'HA_literal_1_2'}),
            channel_map_hash=object_hash(json.loads(r['channel_labels'])),original_fs=float(r['sfreq_hz']),
            n_samples=int(r['n_samples']),n_channels=int(r['n_channels']),raw_locator_key=rid,
            clinical_link_status=ix['clinical_link_evidence'],clinical_assessment_timing_status='unknown',
            source_sha256_status='pending_full_file_hash_at_export'))
        locators.append({'record_id':rid,'signal_path':lookup[r['signal_file_id']],
                         'event_path':lookup[r['event_file_id']],'signal_file_id':r['signal_file_id'],'event_file_id':r['event_file_id']})
    for s in sources:
        mid=s['container_id']
        if mid!=s['canonical_container_id']:continue
        meta=labels[mid];pid=meta['unique_same_day_pid']
        safe=bool(pid) and meta['source_candidate_ambiguity']=='unique_participant'
        task=meta['protocol_task'];flag=bool(meta['metadata_caution_flags'])
        records.append(dict(candidate_id=pid or 'unresolved:'+mid,split_group_id=gids['record:'+mid],record_id=mid,
            canonical_record_id=mid,branch='MFF',cohort_evidence=meta['source_label_expanded'],
            device_evidence=meta['wearing_evidence'],device_change_flag=flag,dynamic_condition_unknown=True,
            paradigm_id=task,task_evidence_level='literal_source_task_not_acoustic_validation',index_record=False,
            identity_safe=safe,source_eligible=s['source_status']=='eligible',analysis_index=False,
            index_hold_reason='pending_task_index' if safe else 'identity_unresolved_or_ambiguous',label_semantics='literal_only',
            code_map_hash=object_hash({'stad':0,'devt':1,'scope':task}),
            channel_map_hash=object_hash({'sensor_net':s['sensor_net'],'n_channels':s['n_channels']}),
            sensor_net=s['sensor_net'],original_fs=float(s['sfreq']),n_samples=int(s['reader_n_samples']),
            n_channels=int(s['n_channels']),raw_locator_key=mid,clinical_link_status='same_day_candidate' if safe else 'unresolved',
            clinical_assessment_timing_status='not_confirmed_concurrent',source_sha256_status='pending_export',
            storage_intervals_samples=s['storage_intervals_samples']))
        locators.append({'record_id':mid,'signal_path':mffpaths[mid]['path'],'record_time':mffpaths[mid]['record_time']})
    # Per-task indices use timestamp only, without looking at EEG quality or outcomes.
    selected=set()
    for r in sorted((r for r in records if r['branch']=='MFF' and r['identity_safe'] and r['paradigm_id'] in ['puretone','bapa']),
                    key=lambda r:(mffpaths[r['record_id']]['record_time'],r['record_id'])):
        key=(r['candidate_id'],r['paradigm_id'])
        if key in selected:continue
        selected.add(key);r['index_record']=True
        r['analysis_index']=r['source_eligible'] and not r['device_change_flag']
        r['index_hold_reason']='' if r['analysis_index'] else 'source_or_condition_gate'
    cov=readcsv('private/phase3_ha_covariates_004/candidate_covariates.csv')
    clinical=[]
    for r in cov:
        def numeric(key):
            try:
                v=float(r[key]);return v if np.isfinite(v) else None
            except (ValueError,TypeError):return None
        age,duration,pta,y=[numeric(k) for k in ['clinical_age_months','duration_months','better_unaided_pta','MUSS']]
        complete=(r['pta_status']=='linked_complete_unaided' and all(v is not None for v in [age,duration,pta,y])
                  and age>=0 and duration>=0 and 0<=y<=100 and true(r['strong_unique_link']) and true(r['eligible_measurement_identity_index']))
        clinical.append(dict(candidate_id=r['participant_id'],split_group_id=gids[r['participant_id']],record_id=r['recording_id'],
            age_months=age,log1p_device_duration_months=float(np.log1p(duration)) if duration is not None and duration>=0 else None,
            better_ear_4freq_source_units=pta,MUSS_source_percentage=y,clinical_complete=complete,
            clinical_assessment_timing_status='unknown',threshold_unit_status='source_units_not_confirmed_dB_HL'))
    assert len({r['record_id'] for r in records})==len(records)==296
    pd.DataFrame(records).to_parquet(priv/'records.parquet',index=False)
    pd.DataFrame(locators).to_parquet(priv/'raw_locators.parquet',index=False)
    pd.DataFrame(clinical).to_parquet(priv/'clinical_index.parquet',index=False)
    write_json(priv/'identity_graph.json',{'edges':graph.edges,'node_to_group':gids,'hash':object_hash(graph.edges)})
    # Aggregate event dictionaries: no source or candidate keys leave private outputs.
    counts=Counter()
    for r in ha:
        if index[r['recording_id']]['cohort']=='HA':counts.update(json.loads(r['annotation_counts']))
    pairs=readcsv('results/phase3_synthesis_001/pair_availability.csv')
    pd.DataFrame(pairs).to_parquet(priv/'E_existing_pairs.parquet',index=False)
    tasks=Counter((r['paradigm_id'],r.get('sensor_net',''),r['n_channels']) for r in records if r['branch']=='MFF' and r['analysis_index'])
    summary={'stage':'S1_metadata','status':'metadata_complete_signal_support_pending','records':len(records),
        'HA_records':len(ha),'canonical_MFF_records':203,
        'HA_frozen_index_metadata_eligible':sum(r['analysis_index'] for r in records if r['branch']=='HA_BDF'),
        'HA_clinical_complete_before_new_EEG_QC':sum(r['clinical_complete'] for r in clinical),
        'known_cross_archive_overlap_edges':overlap_edges,'existing_same_day_task_pairs':len(pairs),
        'MFF_task_layout_metadata_support':[{'task':k[0],'sensor_net':k[1],'channels':k[2],'candidate_indices':v} for k,v in sorted(tasks.items())],
        'HA_annotation_code_counts':dict(counts),'identity_graph_hash':object_hash(graph.edges),
        'record_manifest_hash':digest(priv/'records.parquet'),'clinical_values_used_for_EEG_selection':False,
        'note':'Metadata support is not new-QC trial eligibility; no scientific outcome has been examined.'}
    write_json(out/'summary.json',summary)
    write_json(priv/'completion.json',{'config_hash':object_hash(config),'output_hashes':{p.name:digest(p) for p in priv.glob('*') if p.is_file()}})
    return summary
