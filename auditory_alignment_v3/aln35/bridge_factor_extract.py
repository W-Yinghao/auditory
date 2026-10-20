"""Four bounded donor feature replays on runfill GPUs; never trains a donor."""
from __future__ import annotations
import argparse
from datetime import datetime
import gc
import json
import os
from pathlib import Path
import numpy as np
import torch
from auditory_alignment_v3.prior33 import bridge as BR, model as M, views as V, zeroshot as ZS
from auditory_alignment_v3 import core
from . import bridge_factor as F
from . import science_binding as B


def target_query_id(ds, cf, pid, s):
    return f'{ds}/cf{cf}/{pid}/e0={int(s["e0"])}/presentation={int(s["presentation"])}/fs0={int(s["fs0"])}/segment5s'


@torch.no_grad()
def extract(key):
    assert os.environ.get('SLURM_JOB_ID') and torch.cuda.is_available(), 'encoder forwards require allocated GPU'
    assert key in F.KEYS
    os.umask(0o077); plan = B.read(F.BASE / 'plan.json')
    for p, digest in plan['code_sha256'].items(): assert B.sha(B.ROOT / p) == digest, p
    item = next(e for e in plan['entries'] if e['key'] == key)
    for p, digest in item['source_paths_sha256'].items(): assert B.sha(p) == digest, p
    cache = Path(item['cache']); cache.mkdir(parents=True, exist_ok=False)
    row = item['rows'][0]; man = BR.open_row_manifest(row)
    dep = BR.load_member(row, F.load_rows(), core.OUT)
    bridge = BR.load_bridge(item['bridge_file'], expect_id=row['spec']['bridge'])
    br, uc, source = F.source_metadata(man, bridge, row['dataset'])
    assert source == item['source_metadata']
    dev = torch.device('cuda')
    # Only the source bridge-cal rows are replayed; donor-fit B is already frozen.
    rr = sorted(set(map(int, br['cal']['queries'].rows)) | set(map(int, uc['set'].rows)))
    bank = V.DonorBank(man, 'sparrkulee', ('bridge_cal',), dev, root=man.root, segments=rr)
    enc, _ = BR.donor_encoder(dep['ckpt'], man, row['dataset'], dev)
    Uq, Yq = BR.encode_segments(enc, bank, br['cal']['queries'], montage=False)
    Uu, Yu = BR.encode_segments(enc, bank, uc['set'], montage=False)
    candidate = br['cal']['candidates']
    Ac = BR.segment_targets(bank, candidate.presentation, candidate.s)
    assert np.allclose(Yq, Ac[np.asarray(source['own'])], atol=1e-6, rtol=1e-6)
    np.savez(cache / 'source.npz', Uq=Uq, Yq=Yq, Uu=Uu, Yu=Yu, Ac=Ac,
             fold_q=np.asarray(source['query_fold']), fold_uc=np.asarray(source['bridgecal_fit_fold']))
    B.write_new(cache / 'source_metadata.json', source)
    del bank, enc, Uq, Yq, Uu, Yu, Ac; gc.collect(); torch.cuda.empty_cache()
    print(key, 'source_features_complete', flush=True)
    output = {'source.npz': B.sha(cache / 'source.npz'), 'source_metadata.json': B.sha(cache / 'source_metadata.json')}
    for cf in (0, 1):
        row_cf = next(r for r in item['rows'] if r['content_fold'] == cf)
        coh = V.target_view(row_cf['dataset'], cf, man, 'A', root=man.root)
        meta, parts = dict(coh.meta), coh.participants
        bt = V.TickBatcher(coh, row_cf['spec'], row_cf, dev, man, train_p=set())
        purity = ZS._check_purity(bt, coh)
        enc, tmap = BR.donor_encoder(dep['ckpt'], man, row_cf['dataset'], dev, layout=coh.layout)
        head = M.fixed_heads(man, man.root)['env'].to(dev).eval()
        reps = V.TickReps(enc, head, bt)
        lookup, candidates = V.pool_of(coh, 'test', 'ss')
        _, Ac = reps.va([s['s0'] for s in candidates])
        arrays = {'Ac': Ac}; people = []
        candidate_ids = [f'{row_cf["dataset"]}/cf{cf}/uid={s["uid"]}/presentation={int(s["presentation"])}/fs0={int(s["fs0"])}' for s in candidates]
        assert len(candidate_ids) == len(set(candidate_ids))
        expected = set()
        for r in item['rows']:
            if r['content_fold'] == cf:
                old = B.read(Path(core.OUT) / 'units' / (r['experiment_id'] + '.json'))
                expected.update(old['eval']['per_participant'])
        for p, info in enumerate(parts):
            pid = info['id']
            if pid not in expected: continue
            q = [s for s in coh.segments if s['p'] == p and s['role'] == 'test' and s['kind'] == 'ss']
            q = [q[i] for i in np.argsort([s['e0'] for s in q])]
            assert q
            j = len(people); arrays[f'U_{j}'] = reps.u([s['e0'] for s in q])
            arrays[f'own_{j}'] = np.asarray([lookup[s['uid']] for s in q], dtype=np.int64)
            query_ids = [target_query_id(row_cf['dataset'], cf, pid, s) for s in q]
            assert len(query_ids) == len(set(query_ids))
            people.append({'id': pid, 'group': info['group'], 'fold': info['fold'], 'array_index': j,
                           'query_ids': query_ids, 'own_candidate_ids': [candidate_ids[int(v)] for v in arrays[f'own_{j}']]})
        assert {p['id'] for p in people} == expected
        np.savez(cache / f'target_cf{cf}.npz', **arrays)
        B.write_new(cache / f'target_cf{cf}_metadata.json', {'content_fold': cf, 'dataset': row_cf['dataset'],
                    'people': people, 'candidate_ids': candidate_ids, 'view': meta, 'purity': purity,
                    'normalization': ZS.access_of(row_cf['dataset'], 'A', man), 'tensor_map': BR.jsonable(tmap)})
        for filename in (f'target_cf{cf}.npz', f'target_cf{cf}_metadata.json'): output[filename] = B.sha(cache / filename)
        del coh, bt, reps, enc, head, arrays, Ac; gc.collect(); torch.cuda.empty_cache()
        print(key, 'target_content_fold', cf, 'complete', flush=True)
    result = {'status': 'complete', 'key': key, 'job': os.environ['SLURM_JOB_ID'], 'time': datetime.now().astimezone().isoformat(),
              'plan_sha256': B.sha(F.BASE / 'plan.json'), 'extract_code_sha256': B.sha(__file__),
              'source_paths_sha256': item['source_paths_sha256'], 'files': output, 'cache': str(cache),
              'device': torch.cuda.get_device_name(0), 'encoder_training': False, 'target_fitted_parameters': 0}
    B.write_new(cache / 'complete.json', result)
    B.write_new(F.BASE / 'extract_receipts' / (key + '.json'), result)
    print(json.dumps({'status': 'complete', 'key': key, 'cache': str(cache)}), flush=True)


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--key', required=True, choices=F.KEYS)
    extract(ap.parse_args().key)
