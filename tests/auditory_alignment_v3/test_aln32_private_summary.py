"""ADDENDUM_08 synthetic check: known group difference, age slope and stage contrast are recovered; NH duration not used."""
import numpy as np

from auditory_alignment_v3 import aln32_private_summary as PS


def test_cell_recovers_known_effects():
    rng = np.random.default_rng(0)
    cov, Y = {}, {}
    for i in range(60):
        age = 6 + 60 * i / 59; dur = (i % 20) * 1.0
        cov[f"k{i}"] = {"group": "HA", "age_m": age, "dur_m": dur}
        Y[f"k{i}"] = 0.6 + 0.02 * age / 12 + 0.001 * rng.standard_normal()
    for i in range(9):
        cov[f"n{i}"] = {"group": "NH", "age_m": 30.0, "dur_m": None}; Y[f"n{i}"] = 0.5 + 0.001 * rng.standard_normal()
    out = PS.cell(Y, cov, "t")
    assert out["n_HA"] == 60 and out["n_NH"] == 9
    assert abs(out["age_per_year"]["est"] - 0.02) < 0.002 and out["age_per_year"]["ci_low"] > 0
    assert out["HA_minus_NH"]["est"] > 0.1
    assert out["duration_per_year"]["n"] == 60 and "est" in out["stage_>=13 m_minus_0-2"]
