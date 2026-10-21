"""Common query (Q) and training-side manifests of the 10 public DTU units, from the frozen ALN4.1 B0 DTU unit arrays
(cs list identical to the core3 attention endpoint) with readout.py's people rules:
train people = meta pca[sf].train_people; test people = ss-anchor people with fold == sf and not dev.
Q (per unit) = cs segments of test people with role 'test'; training side = cs segments of train people with role fit/es."""
import hashlib, json, sys
import numpy as np
from auditory_alignment_v3.aln42 import external_mindmix as X

out_q, out_units = sys.argv[1], sys.argv[2]
fz = X.frozen_b0()
Q, units = [], []
for cf in (0, 1):
    d = fz[str(cf)]['dest']
    meta = json.load(open(d + '/meta.json'))
    with np.load(d + '/arrays.npz', allow_pickle=False) as z:
        person, code, e0, role = z['cs_person'], z['cs_code'], z['cs_e0'], z['cs_role']
        ss_people = set(z['person'].tolist())
    for sf in range(5):
        body = {'method': 'MindMix_released_full_architecture_common_protocol', 'dataset': 'dtu', 'content_fold': cf, 'person_fold': sf, 'seed': X.SEED}
        uid = 'ALN42X_' + X.digest(body, 16)
        train = meta['pca'][str(sf)]['train_people']
        test = sorted(p for p in ss_people if meta['folds'].get(p) == sf and p not in set(meta['dev_people']))
        q = [int(i) for i in np.flatnonzero(np.isin(person, test) & (role == 'test'))]
        tr = np.isin(person, train)
        units.append({'id': uid, 'content_fold': cf, 'person_fold': sf, 'seed': X.SEED, 'train_people': train, 'test_people': test,
                      'n_fit_segments': int((tr & (role == 'fit')).sum()), 'n_es_segments': int((tr & (role == 'es')).sum()),
                      'n_query_segments': len(q), 'train_windows': 3 * int((tr & (role == 'fit')).sum()),
                      'score_windows': 3 * (int((tr & np.isin(role, ['fit', 'es'])).sum()) + len(q))})
        Q += [{'unit': uid, 'cf': cf, 'sf': sf, 'cs_index': i, 'person': str(person[i]), 'code': str(code[i]), 'e0': int(e0[i])} for i in q]
blob = json.dumps(Q, sort_keys=True, separators=(',', ':'))
json.dump({'n': len(Q), 'sha256_of_rows': hashlib.sha256(blob.encode()).hexdigest(), 'frozen_b0_dtu': fz, 'rows': Q}, open(out_q, 'w'))
json.dump(units, open(out_units, 'w'), indent=1)
print(len(Q), hashlib.sha256(blob.encode()).hexdigest())
for u in units:
    print(u['id'], u['content_fold'], u['person_fold'], len(u['train_people']), len(u['test_people']), u['n_fit_segments'], u['n_es_segments'], u['n_query_segments'])
