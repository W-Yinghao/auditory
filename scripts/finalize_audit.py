"""Materialize canonical MFF events and verify audit outputs without source writes.

Run once through Slurm. Retain pre-finalization metadata under private/.
The outputs remain pseudonymized local research artifacts, not release data.
"""
import csv
import hashlib
import json
import os
import shutil
from collections import Counter
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
ALLOWED = {'#cel', 'cel#', '#obs', '#spc', 'obs#', 'pos#', 'argu',
           'rsp#', 'eval', 'rtim', 'trl#', 'gidx'}
EVENT_FIELDS = ['container_id', 'track_file_id', 'event_1based', 'code_token',
                'onset_s', 'duration_native', 'relative_begin_native',
                'native_time_unit', 'numeric_keys', 'time_status', 'audit_source']


def readcsv(path):
    with path.open(newline='') as f:
        return list(csv.DictReader(f))


def writecsv(path, rows, fields=None):
    fields = fields or sorted({k for r in rows for k in r})
    with path.open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for data in iter(lambda: f.read(8 * 1024 * 1024), b''):
            h.update(data)
    return h.hexdigest()


def main():
    assert os.environ.get('SLURM_JOB_ID'), 'Submit this analysis through Slurm'
    os.umask(0o077)
    csv.field_size_limit(16 * 1024 * 1024)
    out = BASE / 'results/finalization_001'
    priv = BASE / 'private/finalization_001'
    out.mkdir(exist_ok=False)
    priv.mkdir(mode=0o700, exist_ok=False)
    labels = json.loads((BASE / 'private/mff_001/label_map.json').read_text())
    registry = {r['container_id']: r for r in json.loads(
        (BASE / 'private/mff_001/registry.json').read_text())}
    path_ids = {r['absolute_path']: r['file_id'] for r in readcsv(
        BASE / 'private/inventory_001/file_path_map.csv')}
    topology = {r['container_id']: r for r in readcsv(
        BASE / 'results/mff_validation_001/topology.csv')}
    recovery = {r['container_id']: r for r in readcsv(
        BASE / 'results/mff_recovery_001/recovery_summary.csv')}
    assert len(registry) == 1160 and len(topology) == 1160 and len(recovery) == 70
    removed = Counter()
    counts = Counter()
    lineage = Counter()
    staged = []
    backup_checksums = []

    def preserve(path):
        target = priv / path.relative_to(BASE)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
        digest = sha(path)
        assert sha(target) == digest
        backup_checksums.append({'original_artifact': str(path.relative_to(BASE)),
                                 'backup_sha256': digest})
        return target

    def numeric(raw):
        obj = json.loads(raw or '{}')
        cleaned = {}
        for key, value in obj.items():
            name = labels.get(key, key)
            if name in ALLOWED:
                cleaned[name] = value
            else:
                removed[name] += 1
        return json.dumps(cleaned, ensure_ascii=False, sort_keys=True)

    canonical = out / 'mff_event_ledger.csv'
    with canonical.open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=EVENT_FIELDS)
        writer.writeheader()
        # Clean the complete old ledger, but discard every revisited container
        # from the canonical stream, including any partial earlier output.
        source = BASE / 'results/mff_001/event_ledger.csv'
        backup = preserve(source)
        temp = source.with_suffix('.csv.finalizing')
        with backup.open(newline='') as old, temp.open('w', newline='') as new:
            reader = csv.DictReader(old)
            clean = csv.DictWriter(new, fieldnames=reader.fieldnames)
            clean.writeheader()
            for row in reader:
                row['numeric_keys'] = numeric(row['numeric_keys'])
                clean.writerow(row)
                mid = row['container_id']
                if mid in recovery:
                    lineage['initial_partial_rows_excluded'] += 1
                    continue
                unit = topology[mid].get('epoch_time_unit') or 'unknown'
                writer.writerow(dict(row, native_time_unit=unit,
                                     audit_source='mff_001'))
                counts[mid] += 1
                lineage['initial_rows_retained'] += 1
        staged.append((temp, source))

        source = BASE / 'results/mff_recovery_001/event_ledger_recovered.csv'
        backup = preserve(source)
        temp = source.with_suffix('.csv.finalizing')
        with backup.open(newline='') as old, temp.open('w', newline='') as new:
            clean = csv.DictWriter(new, fieldnames=EVENT_FIELDS)
            clean.writeheader()
            for row in csv.DictReader(old):
                mid = row['container_id']
                track_path = str(Path(registry[mid]['path']) / row['track_basename'])
                track = path_ids[track_path]
                result = {k: row[k] for k in ('container_id', 'event_1based',
                          'code_token', 'onset_s', 'duration_native')}
                result.update(track_file_id=track, relative_begin_native='',
                              native_time_unit=topology[mid].get('epoch_time_unit') or 'unknown',
                              numeric_keys=numeric(row['numeric_keys']),
                              time_status=('timestamp_relative_to_record' if row['onset_s'] != ''
                                           else 'unknown'),
                              audit_source='mff_recovery_001')
                clean.writerow(result)
                writer.writerow(result)
                counts[mid] += 1
                lineage['recovered_rows_retained'] += 1
        staged.append((temp, source))

    # Validate the written canonical ledger independently of the writer counters.
    actual = Counter()
    last_event = {}
    unknown_unit = 0
    with canonical.open(newline='') as f:
        for r in csv.DictReader(f):
            assert set(json.loads(r['numeric_keys'])) <= ALLOWED
            assert r['track_file_id'].startswith('file_')
            k = (r['container_id'], r['track_file_id'])
            event = int(r['event_1based'])
            assert event > last_event.get(k, 0), (k, event)
            last_event[k] = event
            actual[r['container_id']] += 1
            unknown_unit += r['native_time_unit'] == 'unknown'
    assert actual == counts
    assert sum(actual.values()) == 1858215
    assert lineage['recovered_rows_retained'] == 627
    for mid, row in recovery.items():
        assert actual[mid] == int(row['n_recovered_event_entries'])

    index_path = BASE / 'results/mff_001/container_index.csv'
    preserve(index_path)
    index = readcsv(index_path)
    for r in index:
        d = json.loads(r['numeric_event_key_counts'] or '{}')
        r['numeric_event_key_counts'] = json.dumps({
            key: value for key, value in d.items()
            if labels.get(key.rsplit('|', 1)[-1], key.rsplit('|', 1)[-1]) in ALLOWED
        }, sort_keys=True)
    temp = index_path.with_suffix('.csv.finalizing')
    writecsv(temp, index)
    staged.append((temp, index_path))

    gates = Counter()
    for r in index:
        mid = r['container_id']
        t = topology[mid]
        problems = [key for key in ('invalid_epoch_times', 'invalid_block_ranges',
                    'epoch_binary_length_mismatches', 'category_events_outside_segments',
                    'category_segments_without_epoch_match') if float(t.get(key) or 0) > 0]
        if t.get('block_coverage_exact') == 'False':
            problems.append('incomplete_block_coverage')
        status = ('unreadable' if t['status'] != 'ok' else
                  'inconsistent' if problems else 'structure_passed')
        gates[status] += 1
        r.update(canonical_event_entries=actual[mid], topology_status=status,
                 topology_issues=json.dumps(problems),
                 final_event_read_status=(recovery[mid]['status'] if mid in recovery else
                                          r['read_status']),
                 signal_suitability='not_established_by_structure_audit')
    manifest = BASE / 'manifests/mff_export_index.csv'
    preserve(manifest)
    temp = manifest.with_suffix('.csv.finalizing')
    writecsv(temp, index)
    staged.append((temp, manifest))
    writecsv(out / 'mff_quarantine.csv', [r for r in index if r['topology_status'] != 'structure_passed'])

    # Values here are explicit processing labels, not inferred acoustic meanings.
    dictionary = []
    for category, code, token in [('Standard', 'stad', 'stad'),
                                   ('Deviant', 'devt', 'La4a6587385f6')]:
        dictionary.append(dict(scope='MFF_history_exact_rule', event_code=code,
                               event_code_token=token, processing_category=category,
                               frequency_hz='unknown', evidence_status='history_rule_only'))
    for code in ('1', '2'):
        dictionary.append(dict(scope='HA_BDF_and_SET_numeric_events', event_code=code,
                               event_code_token=code, processing_category='unknown',
                               frequency_hz='unknown', evidence_status='code_observed_mapping_unconfirmed'))
    writecsv(BASE / 'manifests/event_dictionary.csv', dictionary)
    issues_path = BASE / 'manifests/questions_to_resolve.csv'
    issues = readcsv(issues_path)
    for issue in issues:
        if issue['issue_id'] == 'Q12':
            issue.update(topic='Visual evidence scope',
                         evidence='81 PNG files, 80 byte-distinct screenshots reviewed as contact sheets; two FMP4 AVI headers and frame chunks scanned, playback unavailable',
                         next_action='Use screenshots as processing/condition clues only; video contents remain unreviewed and are not extra EEG acquisitions')
    writecsv(issues_path, issues)
    writecsv(priv / 'original_metadata_checksums.csv', backup_checksums)
    # Commit sanitized metadata only once the canonical reconstruction passes.
    for temp, destination in staged:
        os.replace(temp, destination)
    (out / 'verification.json').write_text(json.dumps({
        'job_id': os.environ['SLURM_JOB_ID'], 'status': 'passed',
        'canonical_mff_event_rows': sum(actual.values()), 'event_lineage': dict(lineage),
        'canonical_containers_with_events': len(actual),
        'event_rows_with_unknown_native_time_unit': unknown_unit,
        'per_track_event_indices_strictly_increasing': True,
        'numeric_keys_whitelist_verified': True,
        'removed_numeric_key_entries': sum(removed.values()),
        'mff_topology_status': dict(gates), 'source_data_written': False,
        'original_metadata_backups_verified': len(backup_checksums),
        'notice': 'Pseudonymized local audit, not a public release. No claim of acoustic or clinical label validation.'
    }, indent=2) + '\n')
    paths = [BASE / 'README.md', BASE / 'AGENTS.md']
    for folder in ('scripts', 'slurm', 'tests', 'configs', 'docs', 'manifests'):
        paths.extend(p for p in (BASE / folder).rglob('*')
                     if p.is_file() and '__pycache__' not in p.parts)
    paths.extend(p for p in (BASE / 'results').rglob('*.json'))
    paths.extend([canonical, out / 'mff_quarantine.csv'])
    writecsv(out / 'artifact_checksums.csv', [
        {'artifact': str(p.relative_to(BASE)), 'bytes': p.stat().st_size, 'sha256': sha(p)}
        for p in sorted(set(paths))])
    print((out / 'verification.json').read_text(), flush=True)


if __name__ == '__main__':
    main()
