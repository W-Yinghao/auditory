import copy
from auditory_alignment_v3.aln34 import private_cb_factorial as P


def test_crossed_rates_are_complementary_without_changing_initialization():
    for obj in P.RATES:
        for ad in ('pretrained_full','random_full'):
            row={'spec':{'objective':obj,'adaptation':ad}};saved=copy.deepcopy(row)
            own,other=P.crossed(row)
            assert own!=other and set((own,other))==set(P.RATES[obj]) and row==saved


def test_new_family_registration_does_not_change_original_private_hash():
    old=P.core.code_hash('E_GENERIC');P.register();P.register()
    assert P.core.code_hash('E_GENERIC')==old
    assert P.core.code_hash(P.FAMILY)!=old
