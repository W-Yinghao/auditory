"""Second REVE fine-tuning lane (c3_s35pereveB): same provider and work as lane R (flock claims prevent double work), takes only
the ready units beyond lane R's two slots; never submits the smoke (lane Z owns it)."""
from . import paper_enc_fleet_r_v2 as R

NAME, LANE, SBATCH = 'c3_s35pereveB', 's35_paper_enc_ft_reve_b', 'slurm/aln35_paper_enc_reve_b.sbatch'


def fleet_status():
    st = R.status()
    out = {**st, 'name': NAME, 'lane': LANE, 'slots': min(int(st['slots']), 2)}
    if st['state'] != 'ready' or not st['submit'] or 'worker' not in st['submit']:
        return {**out, 'state': st['state'] if st['state'] != 'ready' else 'waiting_smoke', 'ready': 0, 'submit': []}
    return {**out, 'ready': max(0, int(st['ready']) - 2), 'submit': [SBATCH, *st['submit'][1:]]}
