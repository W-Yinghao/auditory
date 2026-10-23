"""Paper line (manuscript v2, Table 2 / section 4.1 / App. B.3): external auditory decoders on the common two-candidate
attention protocol -- dispatcher, scoring and fleet status.

Systems (one module each, each with its own frozen plan written before any of its results):
  mtrf  paper/ext_mtrf.py   linear backward mTRF decoder (CPU; runs as srun steps on the evidence allocation)
  vlaai paper/ext_vlaai.py  released VLAAI, PyTorch port verified against TF, target fine-tuned per unit (GPU)
  clip  paper/ext_clip.py   Transformer-CLIP (Bollens et al. 2025) native envelope readout (GPU; see that module)
  mmfau paper/mindmix_fau.py  MindMix complete system on FAU (GPU; DTU = aln42/external_mindmix.py)
Common protocol, partitions, query segments, input cache and integration: paper/ext_common.py.

CLI (Slurm only): python -m auditory_alignment_v3.paper.external_decoders <cmd> [--system S]
  input                       build + verify the cs input cache of both datasets (CPU)
  mtrf                        freeze the mTRF plan and run all 20 units (CPU)
  plan  --system S            freeze S's plan
  smoke --system S            GPU smoke (probe units: training-side segments only)
  worker --system S [--max-units N] | unit --system S --id ID [--probe]
  score --system S            integrate + summarise (refuses unless every unit of S is complete)
  status
fleet_status(lane): lane in {'vlaai', 'clip', 'mmfau'} (plugin shape of paper/arms.py; lanes are registered by the main session).
"""
from __future__ import annotations

import argparse
import importlib
import json
import os
from pathlib import Path

import numpy as np

from . import ext_common as XC

MODULES = {'mtrf': 'ext_mtrf', 'vlaai': 'ext_vlaai', 'clip': 'ext_clip', 'mmfau': 'mindmix_fau'}
read, write, sha = XC.read, XC.write, XC.sha


def module(system):
    return importlib.import_module(f'{__package__}.{MODULES[system]}')


def fleet_status(lane='vlaai'):
    return module(lane).fleet_status()


def unit_margins(rec):
    path = Path(rec['dest']) / 'margins.npz'; assert sha(path) == rec['npz_sha256'], path
    with np.load(path, allow_pickle=False) as z:
        return {k: z[k] for k in z.files}


def score(system):
    S = module(system); plan = read(S.OUT / 'plan.json')
    recs = {r['id']: S.OUT / 'units' / f'{r["id"]}.json' for r in plan['rows']}
    missing = [k for k, p in recs.items() if not p.exists()]
    assert not missing, f'{system}: {len(missing)} units incomplete; scoring refused'
    out = {'system': system, 'plan_sha256': sha(S.OUT / 'plan.json'), 'context': plan.get('context'), 'datasets': {}}
    for ds in XC.DATASETS:
        cache = XC.Cache(ds); per_unit, taus = {}, {}
        for row in plan['rows']:
            if row['dataset'] != ds:
                continue
            rec = read(recs[row['id']]); assert rec['status'] == 'complete' and not rec.get('probe')
            Z = unit_margins(rec)
            for k in ('cs_person', 'cs_code', 'cs_e0'):
                assert np.array_equal(Z[k], cache.arr[k]), k
            assert np.array_equal(Z['cs_role'], cache.role(row['content_fold']))
            res = XC.integrate_unit(cache, row['content_fold'], row['person_fold'], Z['margin'].astype(np.float64))
            per_unit[(row['content_fold'], row['person_fold'])] = res
            taus[f"cf{row['content_fold']}_sf{row['person_fold']}"] = {sec: v['tau'] for sec, v in res.items()}
        summ = XC.summarize(per_unit, cache.index['groups'], ds)
        out['datasets'][ds] = {'summary_by_window_s': {sec: v['groups'] for sec, v in summ.items()},
                               'per_person_by_window_s': {sec: v['people'] for sec, v in summ.items()}, 'tau': taus}
    os.umask(0o022)
    dest = XC.RESULTS / system; dest.mkdir(parents=True, exist_ok=True)
    (dest / f'TABLE2_{system.upper()}.json').write_text(json.dumps(out, indent=1, default=float) + '\n')
    cells = {ds: {g: (round(v['accuracy_mean'], 4), round(v['nll_bits_mean'], 4), v['n_people'])
                  for g, v in out['datasets'][ds]['summary_by_window_s']['20'].items()} for ds in XC.DATASETS}
    print(json.dumps(cells, indent=1))
    return out


def status():
    out = {}
    for system in MODULES:
        try:
            S = module(system)
        except ModuleNotFoundError:
            out[system] = 'module_missing'; continue
        if not (S.OUT / 'plan.json').exists():
            out[system] = 'plan_missing'; continue
        rows = read(S.OUT / 'plan.json')['rows']
        out[system] = f"{sum((S.OUT / 'units' / (r['id'] + '.json')).exists() for r in rows)}/{len(rows)}"
    print(json.dumps(out, indent=1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=('input', 'mtrf', 'plan', 'smoke', 'worker', 'unit', 'score', 'status'))
    ap.add_argument('--system', choices=tuple(MODULES)); ap.add_argument('--id'); ap.add_argument('--probe', action='store_true')
    ap.add_argument('--max-units', type=int, default=1)
    a = ap.parse_args(); assert os.environ.get('SLURM_JOB_ID'); os.umask(0o077)
    if a.cmd == 'input':
        for ds in XC.DATASETS:
            XC.build_input(ds)
            if not (XC.INPUT / ds / 'verify_eeg.json').exists():
                XC.verify_eeg(ds)
        return
    if a.cmd == 'mtrf':
        module('mtrf').run_all(); return
    if a.cmd == 'status':
        status(); return
    S = module(a.system)
    if a.cmd == 'plan':
        S.make_plan()
    elif a.cmd == 'smoke':
        S.smoke()
    elif a.cmd == 'worker':
        from . import ext_fleet as XF
        XF.worker(S, a.max_units, getattr(S, 'ready_fn', None))
    elif a.cmd == 'unit':
        S.unit_cli(a.id, a.probe)
    elif a.cmd == 'score':
        score(a.system)


if __name__ == '__main__':
    main()
