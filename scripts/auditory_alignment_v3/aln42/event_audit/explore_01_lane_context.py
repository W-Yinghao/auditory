"""Exploration step 1 (read-only): protocol statistics of all 93 bdf_puretone lane records from the ST1 event tables
(derived tables, context only), to see whether child60's sequence form occurs elsewhere in the lane. Prints only."""
import os

import numpy as np
import pandas as pd

P = os.path.join(os.getcwd(), "private")
st = pd.read_parquet(os.path.join(P, "auditory_st", "ST1_scope_001", "records.parquet"))
pf = pd.read_csv(os.path.join(P, "auditory_pf", "prepare_002", "records.csv"))
child_of = dict(zip(pf.record_id, pf.child))
rows = []
for r in st[st.lane == "bdf_puretone"].itertuples():
    e = pd.read_parquet(os.path.join(P, "auditory_st", "ST1_scope_001", "events", f"{r.record_id}.parquet"))
    t = e[e.event_kind == "target"]
    y = t.stimulus_local_id.to_numpy()
    soa = np.diff(t.onset_sample.to_numpy()) / 1000.0
    dd = int(np.sum((y[1:] == 1) & (y[:-1] == 1)))
    rows.append({"child": child_of.get(r.record_id), "n_ev": len(e), "n_t": len(t), "dev": float(np.mean(y == 1)),
                 "dd": dd, "soa_med": float(np.median(soa)), "soa_sd": float(np.std(soa[soa < 2])),
                 "lit4": int((e.event_literal == "4").sum()), "lit0": int((e.event_literal == "0").sum()),
                 "dur_min": float(r.d1_seconds) / 60, "src": r.source_cohort_evidence, "flag": r.ha_index_recording_flag})
d = pd.DataFrame(rows)
pd.set_option("display.width", 200)
print(d.describe().to_string())
print(d[(d.dd > 0) | (d.lit4 > 0) | (d.n_t < 900) | (d.soa_med > 0.8)].to_string())
