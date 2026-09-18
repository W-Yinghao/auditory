"""Read only the two registered research documents; no EEG/clinical fitting."""
import csv
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import time
import traceback
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path('/home/infres/yinwang/EEG_auditory')
RUN = 'document_evidence_002'
CONFIG = 'configs/auditory_fseries_qualification_v1.json'
DESIGN = 'AUDITORY_FUNCTIONAL_DECODING_F1_F4_RESEARCH_PLAN_v1.md'


def write(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    path.chmod(0o600)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    assert os.environ.get('SLURM_JOB_ID'), 'SLURM_REQUIRED'
    os.umask(0o077)
    private = ROOT / 'private/auditory_fseries' / RUN
    public = ROOT / 'results/auditory_fseries' / RUN
    assert not private.exists() and not public.exists(), 'RUN_OCCUPIED'
    private.mkdir(mode=0o700)
    public.mkdir(mode=0o700)
    snapshot = private / 'source'
    snapshot.mkdir(mode=0o700)
    sources = [Path(__file__), ROOT / CONFIG, ROOT / DESIGN, ROOT / 'docs/auditory_fseries/STAGE1_PROTOCOL.md']
    hashes = {}
    for src in sources:
        rel = src.relative_to(ROOT)
        target = snapshot / rel
        target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        shutil.copyfile(src, target)
        hashes[str(rel)] = digest(src)
    write(private / 'start.json', dict(job_id=os.environ['SLURM_JOB_ID'], source_hashes=hashes, start_unix=time.time()))
    try:
        inventory = {r['file_id']: r for r in csv.DictReader((ROOT / 'private/inventory_001/file_path_map.csv').open())}
        ids = ['file_fb30d5c47a7336642835a336782da5c1', 'file_08a60863dfa6ba33e6d21f368562af39']
        patterns = {
            'auditory_scale_terms': r'IT[\s-]*MAIS|\bMAIS\b|婴幼儿有意义听觉|有意义听觉整合',
            'speech_scale_terms': r'\bMUSS\b|有意义言语|有意义使用言语',
            'ordinal_scale_terms': r'\bCAP\b|\bSIR\b|听觉行为分级|言语可懂度',
            'clinical_assessment_or_followup_terms': r'量表|问卷|随访|复诊|评估日期|评估时间|同次就诊|同日评估',
            'stimulus_protocol_terms': r'800|1200|纯音|标准|偏差',
        }
        rows = []
        evidence = []
        for fid in ids:
            src = Path(inventory[fid]['absolute_path'])
            with zipfile.ZipFile(src) as z:
                names = [n for n in z.namelist() if n.startswith('word/') and n.endswith('.xml') and any(k in n for k in ['document', 'header', 'footer', 'footnotes', 'endnotes', 'comments'])]
                parts = []
                for name in names:
                    xml = ET.fromstring(z.read(name))
                    parts.extend(n.text or '' for n in xml.iter() if n.tag.endswith('}t'))
            text = '\n'.join(parts)
            write(private / (fid + '_text.json'), dict(path=str(src), parts=parts))
            counts = {key: len(re.findall(pattern, text, re.I)) for key, pattern in patterns.items()}
            rows.append(dict(document_role='HA_acquisition_description' if fid == ids[0] else 'EEG_report_template', text_characters=len(text), **counts))
            evidence.append(dict(file_id=fid, path=str(src), sha256=digest(src), extracted_word_parts=names, **counts))
        write(private / 'document_evidence.json', evidence)
        definition_text = ''.join(json.loads((private / (ids[0] + '_text.json')).read_text())['parts'])
        assert all(s in definition_text for s in ['IT-MAIS', 'CAP-II', 'MUSS', 'SIR', '总分40分', '得分0-9分', '得分1-5分'])
        definitions = [
            dict(measure='IT-MAIS', declared_construct='daily_auditory_behavior', declared_item_range='0–4', declared_total_range='0–40', declared_percentage_formula='score/40*100', row_assignment='not_established_by_this_document'),
            dict(measure='CAP-II', declared_construct='auditory_performance', declared_ordinal_range='0–9', row_assignment='not_established_by_this_document'),
            dict(measure='MUSS', declared_construct='daily_speech_use', declared_items=10, declared_item_range='0–4', declared_total_range='0–40', declared_percentage_formula='score/40*100', row_assignment='not_established_by_this_document'),
            dict(measure='SIR', declared_construct='speech_intelligibility', declared_ordinal_range='1–5', row_assignment='not_established_by_this_document'),
        ]
        result = dict(status='COMPLETE', job_id=os.environ['SLURM_JOB_ID'], documents_checked=len(rows), documents=rows,
            declared_scale_definitions=definitions,
            interpretation='Manual review of the original HA acquisition document confirms questionnaire definitions. This corrects an omission in the old source-document summary and the unsupported generic interpretation in document_evidence_001. Original term counts remain valid. The document does not bind every clinical row to a scale version or establish assessment timing; it cannot automatically resolve the CI percentage-versus-raw-score conflict.',
            supersedes='document_evidence_001_interpretation_only',
            hearing_units_evidence='Document-level WHO hearing-loss grading uses 500–4000 Hz thresholds in dB HL; not a row-level date/calibration or aided-threshold assessment record.',
            assessment_time_evidence='No explicit clinical assessment date, EEG-to-functional-assessment interval or same-visit statement identified in manual review.',
            new_model_fits=0, eeg_values_read=False, original_sources_modified=False)
        write(public / 'summary.json', result)
        write(private / 'completion.json', result)
        print(json.dumps(result, ensure_ascii=False))
    except Exception:
        write(private / 'failure.json', dict(traceback=traceback.format_exc()))
        write(public / 'failure.json', dict(status='FAILED', details='private'))
        raise RuntimeError('FAILED_DETAILS_PRIVATE') from None


if __name__ == '__main__':
    main()
