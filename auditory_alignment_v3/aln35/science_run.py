"""Execute bounded ALN3.5 paired science and original-endpoint contrasts on CPU."""
from datetime import datetime
import json
import os
from pathlib import Path
import sys

from . import science_binding as B, science_export as E, correction_pre as C


def document(result, correction):
    lines = ['# ALN3.5：成对科学分析与原主端点组差', '',
             f"计算：{result['time']}，Slurm CPU {result['job']}。基准提交 `{B.BASELINE}`。", '',
             '本轮复用已完成表征和原主方法输出；不新增训练，也不按外层结果挑选人、seed、窗口或方法。',
             '以下全部为 `exploratory_after_2026_10_18_review`。10 个科学 family 的 30 项对比与 3 个原主端点 family 的 10 项对比分开报告；原注册 bootstrap-t 统计仍保留在原 ALN3.4 报告中。', '',
             '每个 family 先在同一人的完整内容重复内求均值，再平均所需 seeds，最后以人为抽样单位。新区间采用包中原样的 4,000 次 bootstrap、固定原始 SE 的 max-|z*|；不是旧 bootstrap-t，也不是独立区间相减。', '',
             '| Family | 端点 | 完整 / 预期人数（按组） | 状态 |', '|---|---|---|---|']
    for family in result['families']:
        coverage = ', '.join(f"{g}: {v['common_complete_n']}/{v['expected_n']}" for g, v in family['coverage'].items())
        lines.append(f"| {family['family_id']} | {family['unit']} | {coverage} | {family['status']} |")
    lines += ['', '| Family / contrast | 估计 | 同 family 同时 95% 区间 |', '|---|---:|---|']
    for family in result['families']:
        for c in family['contrasts']:
            estimate = 'NA' if c['estimate'] is None else f"{c['estimate']:+.6f}"
            ci = 'nonregular / 不造区间' if c['simultaneous_ci'] is None else '[%+.6f, %+.6f]' % tuple(c['simultaneous_ci'])
            lines.append(f"| {family['family_id']} / {c['id']} | {estimate} | {ci} |")
    lines += ['', '原主 FAU 风险改善按 reference − candidate（bits/5 s query），私有原主 AUC 按 AP − S；组差按名称的第一组减第二组。科学 probe 的 r/AUC 与原主端点不混合。', '',
              'SCI35-C01：native E_LOCAL / E_PUBLIC_TRANSFER 的 pre 输入实际全零，故标为 `all_zero_input_control_no_pre_access`，不作刺激前 EEG 证据。其余后刺激、full、个人适配、FM 真正 pre 以及新 prior 科学输出保留。详见 `CORRECTION_PRIVATE_PRE_ACCESS.md`。', '',
              'AP−XM 是两种特定先验训练包的差异，尚不是正确声音配对的纯消融；APwrong 为独立待绑定对照。时间对比保留完整一秒访问窗，600 ms 指相对读出位置，不是单点神经潜伏期。HA/CI/NH 直接效应差来自独立组人级抽样，不是治疗效应。', '',
              '完整 per-family 参数、实际缺项、来源哈希、个体 contrasts 及原主统计引用见 `results/auditory_alignment_v3/aln35/science/`。含真实 query 索引的规范行和原始 metadata provenance 留在 `private/auditory_alignment_v3/aln35/science/`，本轮未推送 GitHub。', '']
    return '\n'.join(lines)


def main():
    assert os.environ.get('SLURM_JOB_ID'), 'all computation through Slurm'
    os.umask(0o077)
    job = os.environ['SLURM_JOB_ID']
    private = B.PRIVATE / ('run_' + job)
    result_dir = B.RESULTS / ('run_' + job)
    private.mkdir(parents=True, exist_ok=False, mode=0o700)
    result_dir.mkdir(parents=True, exist_ok=False, mode=0o700)
    print('Binding real metadata and production records', flush=True)
    binding = B.Binding()
    B.write_new(private / 'rosters.json', {'expected': binding.expected, 'private_trial_bindings': binding.private_trial_bindings,
                                         'roster_source_manifest_sha256': binding.manifest_sha})
    print('Correction actual-batch audit', flush=True)
    correction = C.run(binding, result_dir)
    print('Exporting exact paired observations', flush=True)
    observations = E.run(binding)
    compiled = E.bind_families(binding)
    sys.path.insert(0, str(B.PACKAGE / 'src'))
    from aln35_reference.contrasts import analyze, validate_rows
    validation = validate_rows(observations)
    B.write_new(private / 'validation.json', validation)
    with (private / 'observations.jsonl').open('x') as f:
        for row in observations:
            f.write(json.dumps(row, ensure_ascii=False, allow_nan=False, separators=(',', ':')) + '\n')
    print('Rows validated', len(observations), flush=True)
    families = []
    for original, spec in compiled:
        B.write_new(private / 'specs' / (spec['family_id'] + '.json'), spec)
        # The reference code is unchanged. Supply only the endpoint/dataset rows
        # for efficient validation, retaining every declared family condition.
        rows = [r for r in observations if r['dataset'] == spec['dataset'] and r['metric'] == spec['metric']]
        value = analyze(rows, spec)
        value['execution_binding'] = {'real_production_rows': True, 'analysis_origin': 'exploratory_after_2026_10_18_review',
                                      'declarative_plan_member': original}
        families.append(value)
        print(spec['family_id'], value['status'], {g: v['common_complete_n'] for g, v in value['coverage'].items()}, flush=True)
    note = B.PRIVATE / 'ANALYSIS_NOTE.md'
    source_files = [Path(__file__), Path(B.__file__), Path(E.__file__), Path(C.__file__), note,
                    B.PACKAGE / 'src/aln35_reference/contrasts.py',
                    B.PACKAGE / 'plans/science_contrasts.json', B.PACKAGE / 'plans/main_endpoint_group_contrasts.json']
    binding_manifest = {'baseline_commit': B.BASELINE, 'code_and_analysis_note_sha256': {str(p.relative_to(B.ROOT)): B.sha(p) for p in source_files},
                        'plans': binding.plan_hashes, 'source_records_and_caches': binding.sources,
                        'source_manifest_sha256': binding.manifest_sha,
                        'observation_sha256': B.sha(private / 'observations.jsonl'),
                        'query_provenance_reconstruction': 'Public: cached person, segment, source_segment_e0 and anchor_offsets. Private: actual accepted original epoch indices after production history filter; y/bin/block equality checked.',
                        'no_encoder_forward_or_training': True, 'private_query_indices_not_publication_authorized': True}
    B.write_new(private / 'binding_manifest.json', binding_manifest)
    result = {'status': 'complete' if not binding.missing else 'complete_with_explicit_missingness',
              'time': datetime.now().astimezone().isoformat(), 'job': job, 'baseline_commit': B.BASELINE,
              'analysis_origin': 'exploratory_after_2026_10_18_review', 'families': families,
              'n_families': len(families), 'n_contrasts': sum(len(v['contrasts']) for v in families),
              'n_normalized_rows': len(observations), 'binding_manifest_sha256': B.sha(private / 'binding_manifest.json'),
              'analysis_code_and_note_sha256': binding_manifest['code_and_analysis_note_sha256'],
              'missingness': binding.missing,
              'original_registered_statistics_retained': [
                  'results/auditory_alignment_v3/aln34/science_v2/science.json',
                  'results/auditory_alignment_v3/aln34/prior_science/science.json',
                  'results/auditory_alignment_v3/aln34/tf_l1/tf_l1_pairs.json',
                  'results/auditory_alignment_v3/public_prior/public_prior.json']}
    B.write_new(result_dir / 'contrasts.json', result)
    B.write_new(result_dir / 'coverage.json', {'families': {v['family_id']: v['coverage'] for v in families},
                                            'source_dependencies': binding.missing, 'excluded_nonhuman_entities': ['phantom:junior']})
    # A public digest points to restricted full binding without exposing new raw
    # private trial/event rows or identity mappings.
    B.write_new(result_dir / 'binding_manifest.json', {k: v for k, v in binding_manifest.items()
                                                    if k != 'source_records_and_caches'})
    docs = B.ROOT / 'docs/auditory_alignment_v3/aln35'
    docs.mkdir(parents=True, exist_ok=True)
    with (docs / 'SCIENCE_PRIVATE_RESULTS.md').open('x') as f: f.write(document(result, correction))
    with (docs / 'CORRECTION_PRIVATE_PRE_ACCESS.md').open('x') as f:
        f.write('# SCI35-C01：native private local pre 访问勘误\n\n'
                f"Slurm CPU {job}：实际生产 batcher 与原 keep-mask 在真实 epoch 上核查通过。local/旧 E_PUBLIC_TRANSFER 输入为原 epoch [50,200)，pre 请求 [0,50)，交集 0；保留样本数为 0，实际输入被全部置零。FM 对照保留 50 个 pre 样本。\n\n"
                f"现有受影响记录数：{correction['existing_affected_by_lane']}。v2 的合法 v1 复用保持其来源，不增加独立观测。逐 unit/seed/fold、原值引用、哈希及受影响路径见 `{result_dir.relative_to(B.ROOT)}/correction_manifest.json`。\n\n"
                '更正解释标签为 `all_zero_input_control_no_pre_access`，`valid_for_pre_event_inference=false`；包括 windows.pre 全指标与 TG 任一端为 pre 的 7 个 cell，两种校准均在内。\n\n'
                '旧源代码、计划、unit、缓存及原统计未修改。三个后刺激窗、full 后刺激、个人适配、full 发育端点、FM 真实 pre、公开科学及新 prior 科学均不在本次勘误内。全零输入产生的排序波动不是刺激前生理信息。\n')
    B.write_new(B.PRIVATE / ('completed_' + job + '.json'), {'status': 'complete', 'job': job,
                 'results': str(result_dir), 'private': str(private), 'n_rows': len(observations),
                 'n_families': 13, 'n_contrasts': 40, 'correction_items': len(correction['items'])})
    print(json.dumps({'status': result['status'], 'rows': len(observations), 'families': 13, 'contrasts': 40,
                      'result_dir': str(result_dir), 'correction_records': len(correction['items'])}), flush=True)


if __name__ == '__main__': main()
