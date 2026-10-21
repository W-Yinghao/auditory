import json, numpy as np
for uid in ('ALN41Z_c68e8a1b8a67837b', 'ALN41Z_35bbb2e942077c93'):
    d = f'<private checkpoint storage>/auditory_alignment_v3/aln41/frozen_v1/units/{uid}'
    m = json.load(open(d + '/meta.json'))
    z = np.load(d + '/arrays.npz', allow_pickle=False)
    print(uid, {k: (z[k].shape, z[k].dtype) for k in ('cs_person', 'cs_code', 'cs_e0', 'cs_role', 'cs_offsets')})
    print(' roles', dict(zip(*np.unique(z['cs_role'], return_counts=True))), 'people', len(set(z['cs_person'])), 'dev', m['dev_people'])
    print(' folds', sorted(set(m['folds'].values())), {k: len(v['train_people']) for k, v in m['pca'].items()}, m['cs'])
    print(' first', z['cs_person'][:2], z['cs_code'][:2], z['cs_e0'][:2])
