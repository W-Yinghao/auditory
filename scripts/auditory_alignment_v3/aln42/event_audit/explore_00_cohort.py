"""Exploration step 0 (read-only): list the 64-child private BDF lane and child60's raw event literals.
Prints to stdout only (private Slurm log); writes nothing."""
import os
import sys
from collections import Counter

import numpy as np
import pandas as pd
import pyedflib

REPO = os.getcwd()
P = os.path.join(REPO, "private")
ch = pd.read_csv(os.path.join(P, "auditory_pf", "prepare_002", "children.csv"))
pf = pd.read_csv(os.path.join(P, "auditory_pf", "prepare_002", "records.csv"))
st = pd.read_parquet(os.path.join(P, "auditory_st", "ST1_scope_001", "records.parquet")).set_index("record_id")
kids = []
for _, c in ch.iterrows():
    grp = "HA" if (c.group == "labelled" and bool(c.eligible)) else ("NH" if (c.group == "nh" and bool(c.nh_eligible)) else None)
    if grp is None:
        continue
    kids.append((int(c.child), grp, pf.record_id[int(c.primary_rec)]))
print("n kids", len(kids), Counter(g for _, g, _ in kids))
b = st[st.lane == "bdf_puretone"]
print("clock offsets", b.ha_event_clock_offset_s.value_counts(dropna=False).to_dict())
print("literal sets", b.literal_code_set.value_counts().to_dict())
print("orig fs", b.d1_original_fs.value_counts().to_dict(), "stride", b.d1_stride.value_counts().to_dict())
print("index flag", b.ha_index_recording_flag.value_counts().to_dict(), b.ha_index_hold_reason.value_counts().to_dict())
for child, grp, rid in kids:
    r = st.loc[rid]
    with pyedflib.EdfReader(r["_event_path"]) as rd:
        t, d, codes = rd.readAnnotations()
    lit = Counter(str(x).strip() for x in codes)
    seq = [str(x).strip() for x in codes]
    s = np.array([1 if x == "2" else 0 for x in seq if x in ("1", "2")])
    # run lengths of '1' between '2'
    pos = np.flatnonzero(s == 1)
    sp = np.diff(pos) - 1 if len(pos) > 1 else np.array([])
    print(f"child{child} {grp} rid={rid} n={len(seq)} lit={dict(lit)} devrate={s.mean():.3f} "
          f"spacing min/med/max={sp.min() if len(sp) else -1}/{np.median(sp) if len(sp) else -1}/{sp.max() if len(sp) else -1} "
          f"dd={int(np.sum(sp == 0))} ioi_med={np.median(np.diff(t)):.3f} first={seq[:3]} offset={r.ha_event_clock_offset_s}", flush=True)
