"""ALN3.6 R2 (package ALN3.7) matched AP / APwrong for the private children with seed 3407.

Package docs/05: the matched pair is repeated with one other seed (3407), with the same donor exclusion, initialisation rule,
exposure-stream matching and target folds: one donor pair (AP + APwrong, 2 donor trainings) and 2 x 5 target trainings.
Nothing compatible exists: the seed-3407 panel AP lineage used the original stream and horizon, not the common h30 sampler
(the R1 audit already excluded the old AP as an equal-budget comparator).

The R1 runner aln35/ap_wrong.py stays byte-identical. Per process it is re-pointed (`configure`): OUT / STORAGE / PLAN go to the
R2 roots, and its two seeded constructors are swapped for the same calls with seed 3407. In the R1 runner these are the
shared-initialisation encoder build and the common pair sampler, both written with the literal 3401. The seed field of the
target record is set to 3407; the R1 runner writes the literal. Lineage: the seed-3407 panel donor row ALN3X_89596ce9168aa591
(same spec as the R1 core donor apart from seeds and block label: same manifest, same private_bdf donor set). Templates are the
seed-3407 panel AP target rows; the panel S rows are scratch references. The full h30 metadata stream is audited on CPU at
registration, and the GPU donor must reproduce its hash.
"""
from __future__ import annotations

import argparse
import copy
from collections import Counter
from datetime import datetime, timezone
import fcntl
import gc
import json
import os
from pathlib import Path
import traceback

from .. import core, registry
from ..aln35 import ap_wrong as AW
from ..aln35.ap_wrong_sampler import PairSampler, RULE, REVISION, WRONG_RNG_TAG
from . import common as C

SEED = 3407
R1_LITERAL_SEED = 3401
DONOR_ROW = 'ALN3X_89596ce9168aa591'
FORMAT = 'aln36_r2_apwrong_h30_s3407_v1'
OUT = C.OUT / 'r2_s3407' / 'apwrong_v1'
STORAGE = C.STORE / 'r2_s3407' / 'apwrong_v1'
PLAN = OUT / 'plan.json'
NAME, LANE, SBATCH = 'c3_s35r2a36apw', 's35_r2_aln36_apwrong', 'slurm/aln35_r2a36_apwrong.sbatch'
sha, digest, write = AW.sha, AW.digest, AW.write


class SeededSampler(PairSampler):
    """The R1 runner's PairSampler(man, target, 3401, ...) call with the R2 seed (EEG stream and wrong-row RNG)."""

    def __init__(self, manifest, target, seed, device, **kw):
        assert seed == R1_LITERAL_SEED, 'only the R1 literal is substituted'
        super().__init__(manifest, target, SEED, device, **kw)


def build_pair(manifest, target, device):
    """R1 build_pair with the R2 seed: one shared initialisation for both arms."""
    names = [n for n in AW.C.VOCAB if n in set(manifest["seen"][target])]
    encoders = {arm: AW.M.build_shared(names, names, SEED).to(device) for arm in AW.ARMS}
    initial = {arm: AW.state_sha(enc.state_dict()) for arm, enc in encoders.items()}
    if len(set(initial.values())) != 1:
        raise AssertionError("AP and APwrong initialisation differs")
    return encoders, initial


def configure():
    AW.OUT, AW.STORAGE, AW.PLAN = OUT, STORAGE, PLAN
    AW.PairSampler, AW.build_pair = SeededSampler, build_pair


def code_names():
    names = set()
    for group in ('prior33_donor', 'prior33_target'):
        names.update(str(Path(d) / f) for d, f in registry.FAMILY_CODE[group] + core.V2_DEPS)
    names.update(['auditory_alignment_v3/aln35/ap_wrong.py', 'auditory_alignment_v3/aln35/ap_wrong_sampler.py',
                  'auditory_alignment_v3/aln36/r2_apwrong.py', 'auditory_alignment_v3/aln36/common.py', SBATCH])
    return sorted(names)


# ----------------------------------------------------------------------------------------------- registration (CPU, once)
def register():
    from ..prior33 import views as V, donor_train as D
    if PLAN.exists():
        raise FileExistsError('plan already frozen; no in-place rewrite')
    code_hashes = {name: sha(AW.ROOT / name) for name in code_names()}
    code_digest = digest(code_hashes)
    rows = [json.loads(line) for line in (AW.ROOT / 'private/auditory_alignment_v3/plan_ext.jsonl').read_text().splitlines()]
    donor_row = next(r for r in rows if r['experiment_id'] == DONOR_ROW)
    assert (donor_row['family_id'], donor_row['dataset'], donor_row['seed'], donor_row['spec']['objective']) == \
        ('ALN32_PUBLIC_AUDIO_PRIOR_DONOR', 'private_bdf', SEED, 'NCE')
    targets_all = [r for r in rows if r['family_id'] == 'ALN32_PUBLIC_AUDIO_PRIOR_TARGET' and r['dataset'] == 'private_bdf'
                   and r['seed'] == SEED and r['spec']['objective'] == 'NCE' and r['spec']['block'] == donor_row['spec']['block']]
    donor_path = AW.ROOT / 'private/auditory_alignment_v3/units' / f'{DONOR_ROW}.json'
    assert json.loads(donor_path.read_text())['status'] == 'complete'
    man = V.open_for_row(donor_row)
    inputs = {man.path: sha(man.path), str(donor_path): sha(donor_path)}
    sam = SeededSampler(man, 'private_bdf', R1_LITERAL_SEED, 'cpu', revised=True, metadata_only=True)
    steps = D.steps_at(30, man['budget']['anchors_per_ep_eq'])
    for _ in range(steps):                     # full h30 metadata stream: legal derangement at every step, before any GPU
        sam.next_draw()
    meta = {'target': 'private_bdf', 'seed': SEED, 'steps': steps, 'stream_sha256': sam.stream_hash(), 'hash_log': sam.hash_log,
            'rejections': dict(sam.rejections), 'all_steps_strictly_feasible': True}
    print(json.dumps({'metadata_stream_checked': 'private_bdf', 'steps': steps, 'rejections': dict(sam.rejections)}), flush=True)
    r1 = json.loads((C.REPO / 'private/auditory_alignment_v3/aln35/apwrong_v1/plan.json').read_text())
    r1_donor = next(u for u in r1['units'] if u['stage'] == 'donor_pair' and u['dataset'] == 'private_bdf')
    assert steps == r1_donor['updates_per_member'] and man.sha256 == r1_donor['spec']['manifest_sha256']
    spec = {'format': FORMAT, 'dataset': 'private_bdf', 'seed': SEED, 'code_digest': code_digest, 'original_donor': DONOR_ROW,
            'original_record_sha256': inputs[str(donor_path)], 'manifest_sha256': man.sha256, 'rule': RULE, 'revision': REVISION,
            'horizon': 30, 'updates': steps, 'revised_stream_sha256': sam.stream_hash()}
    uid = 'ALN36R2W_' + digest(spec)[:16]
    units = [{'unit_id': uid, 'stage': 'donor_pair', 'dataset': 'private_bdf', 'spec': spec, 'source_row': donor_row,
              'source_audit': {'r1_plan': 'private/auditory_alignment_v3/aln35/apwrong_v1/plan.json',
                               'r1_donor_unit': r1_donor['unit_id'], 'old_AP_retained': True,
                               'old_AP_not_used_as_equal_budget_comparator': True,
                               'note': 'seed-3407 panel AP lineage used the original stream/horizon; R2 trains the common h30 pair'},
              'updates_per_member': steps}]
    templates = sorted((r for r in targets_all if r['spec']['variant'] == 'AP'), key=lambda r: r['subject_fold'])
    assert [t['subject_fold'] for t in templates] == list(C.PERSON_FOLDS)
    for template in templates:
        scratch = [r for r in targets_all if r['spec']['variant'] == 'S' and r['subject_fold'] == template['subject_fold']]
        assert len(scratch) == 1
        refs = {}
        for label, ref in (('scratch', scratch[0]), ('original_ap', template)):
            path = AW.ROOT / 'private/auditory_alignment_v3/units' / f'{ref["experiment_id"]}.json'
            record = json.loads(path.read_text()); assert record['status'] == 'complete'
            inputs[str(path)] = sha(path)
            refs[label] = {'experiment_id': ref['experiment_id'], 'path': str(path), 'sha256': inputs[str(path)],
                           'code_hash': record.get('code_hash'), 'split_hash': ref['spec']['split_hash']}
        for arm in AW.ARMS:
            binding = {'donor_unit': uid, 'arm': arm, 'template': template['experiment_id'], 'template_sha256': digest(template),
                       'code_digest': code_digest}
            tid = 'ALN36R2T_' + digest(binding)[:16]
            adapter = copy.deepcopy(template)
            adapter['experiment_id'] = tid; adapter['spec']['donor_group'] = uid; adapter['logical_dependencies'] = [uid]
            adapter['registered'] = 'ALN3.6 R2 matched APwrong fixed h30 common-sampler control, seed 3407'
            units.append({'unit_id': tid, 'stage': 'target', 'dataset': 'private_bdf', 'arm': arm, 'donor_unit': uid,
                          'binding': binding, 'source_template': template, 'adapter_row': adapter,
                          'scratch_reference': refs['scratch'], 'original_ap_reference': refs['original_ap']})
    assert Counter(u['stage'] for u in units) == {'donor_pair': 1, 'target': 10}
    OUT.mkdir(parents=True, exist_ok=True, mode=0o700)
    metapath = OUT / 'revised_stream_audit.json'
    write(metapath, {'job': os.environ['SLURM_JOB_ID'], 'lineages': [meta]}); inputs[str(metapath)] = sha(metapath)
    for p in (C.PACKAGE / 'docs/05_THREE_ROUND_CLOSURE.md', C.REPO / 'private/auditory_alignment_v3/aln35/apwrong_v1/plan.json'):
        inputs[str(p)] = sha(p)
    plan = {'format': FORMAT, 'created_utc': datetime.now(timezone.utc).isoformat(), 'registration_job': os.environ['SLURM_JOB_ID'],
            'workpackage': 'ALN36_R2_AP_WRONG_S3407', 'outer_wrong_results_seen_for_seed': False,
            'code_hashes': code_hashes, 'input_hashes': inputs, 'units': units,
            'contract': {**r1['contract'], 'seed': SEED, 'wrong_rng': {'seed_sequence': [SEED, WRONG_RNG_TAG], 'independent_of_eeg_stream': True},
                         'r1_runner': 'aln35/ap_wrong.py byte-identical; seeded constructors replaced (aln36/r2_apwrong.configure)'}}
    write(PLAN, plan)
    PLAN.with_suffix('.sha256').write_text(sha(PLAN) + '\n')
    PLAN.chmod(0o444); PLAN.with_suffix('.sha256').chmod(0o444)
    print(json.dumps({'status': 'PASS', 'plan_sha256': sha(PLAN), 'units': len(units), 'donor': uid}), flush=True)


# ----------------------------------------------------------------------------------------------- GPU (R1 functions, re-pointed)
def finish_target(result):
    assert result['seed'] == R1_LITERAL_SEED and result['adapter_row']['seed'] == SEED
    return {**result, 'seed': SEED, 'r1_runner_literal_seed_replaced': True, 'format_r2': FORMAT}


def probe(plan, plan_sha, steps, tag):
    donor = next(u for u in plan['units'] if u['stage'] == 'donor_pair')
    base = OUT / 'probes' / tag; base.mkdir(parents=True, exist_ok=True)
    donor_result = AW.train_donor(donor, plan, plan_sha, probe_steps=steps, probe_tag=tag)
    write(base / f'{donor["unit_id"]}.json', donor_result)
    target = next(u for u in plan['units'] if u['stage'] == 'target' and u['arm'] == 'APwrong')
    target_result = finish_target(AW.train_target(target, plan, plan_sha, donor_result, epochs=1, probe_tag=tag))
    write(base / f'{target["unit_id"]}.json', target_result)
    receipt = {'status': 'PASS', 'dataset': 'private_bdf', 'plan_sha256': plan_sha, 'donor_steps_per_arm': steps,
               'donor_pair': donor['unit_id'], 'target': target['unit_id'], 'target_epochs': 1, 'no_performance_gate': True,
               'initial_state_sha256': donor_result['initial_state_sha256'], 'job': os.environ.get('SLURM_JOB_ID'),
               'code_hashes': plan['code_hashes']}
    write(base / 'receipt.json', receipt); write(OUT / 'engineering' / 'private_bdf.json', receipt)
    return receipt


def worker(plan, plan_sha, max_units):
    import torch
    done = 0
    eng = OUT / 'engineering' / 'private_bdf.json'
    if not eng.exists() or json.loads(eng.read_text()).get('plan_sha256') != plan_sha:
        return {'completed_this_worker': 0, 'reason': 'no engineering receipt'}
    for unit in plan['units']:
        uid = unit['unit_id']; dest = OUT / 'units' / f'{uid}.json'; failed = OUT / 'units' / f'{uid}.FAILED.json'
        dep = OUT / 'units' / f'{unit.get("donor_unit")}.json'
        if dest.exists() or failed.exists() or (unit['stage'] == 'target' and not dep.exists()):
            continue
        lock = OUT / 'claims' / f'{uid}.lock'; lock.parent.mkdir(parents=True, exist_ok=True)
        with lock.open('a+') as h:
            try:
                fcntl.flock(h.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                continue
            if dest.exists() or failed.exists():
                continue
            try:
                if unit['stage'] == 'donor_pair':
                    result = AW.train_donor(unit, plan, plan_sha)
                else:
                    result = finish_target(AW.train_target(unit, plan, plan_sha, json.loads(dep.read_text())))
                write(dest, result)
            except Exception as error:
                write(failed, {'status': 'technical_failed', 'unit_id': uid, 'plan_sha256': plan_sha, 'error': str(error),
                               'traceback': traceback.format_exc(), 'job': os.environ.get('SLURM_JOB_ID')})
                raise
            done += 1; gc.collect(); torch.cuda.empty_cache()
            if done >= max_units:
                break
    return {'completed_this_worker': done, 'plan_sha256': plan_sha}


# ----------------------------------------------------------------------------------------------- fleet readiness (read-only)
def fleet_status():
    st = {'name': NAME, 'lane': LANE, 'state': 'plan_missing', 'ready': 0, 'remaining': 11, 'slots': 1, 'initial': [], 'submit': []}
    if not PLAN.exists():
        return st
    expected = PLAN.with_suffix('.sha256').read_text().strip()
    if sha(PLAN) != expected:
        return {**st, 'state': 'plan_hash_mismatch'}
    plan = json.loads(PLAN.read_text())
    if any(sha(AW.ROOT / n) != v for n, v in plan['code_hashes'].items()):
        return {**st, 'state': 'code_hash_mismatch'}
    left = [u for u in plan['units'] if not (OUT / 'units' / f'{u["unit_id"]}.json').exists()]
    st['remaining'] = len(left)
    if not left:
        return {**st, 'state': 'complete'}
    if any((OUT / 'units' / f'{u["unit_id"]}.FAILED.json').exists() for u in left):
        return {**st, 'state': 'technical_failure'}
    eng = OUT / 'engineering' / 'private_bdf.json'
    if not eng.exists():
        if list((OUT / 'probes').glob('*')) and not any((p / 'receipt.json').exists() for p in (OUT / 'probes').glob('*')):
            return {**st, 'state': 'probe_running_or_failed'}
        return {**st, 'state': 'ready', 'ready': 1, 'submit': [SBATCH, 'probe']}
    ready = [u for u in left if u['stage'] == 'donor_pair' or (OUT / 'units' / f'{u["donor_unit"]}.json').exists()]
    if not ready:
        return {**st, 'state': 'waiting_for_donor_pair'}
    return {**st, 'state': 'ready', 'ready': len(ready), 'slots': 2 if len(ready) > 1 else 1,
            'submit': [SBATCH, 'worker', '--max-units', '1']}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('command', choices=('register', 'probe', 'worker'))
    ap.add_argument('--max-units', type=int, default=1); ap.add_argument('--probe-steps', type=int, default=8)
    a = ap.parse_args()
    if not os.environ.get('SLURM_JOB_ID'):
        raise RuntimeError('Slurm only')
    os.umask(0o077)
    if a.command == 'register':
        register(); return
    configure()
    plan, plan_sha = AW.open_plan(PLAN)
    if a.command == 'probe':
        result = probe(plan, plan_sha, a.probe_steps, f'private_bdf_{os.environ["SLURM_JOB_ID"]}')
    else:
        result = worker(plan, plan_sha, a.max_units)
    print(json.dumps(result), flush=True)


if __name__ == '__main__':
    main()
