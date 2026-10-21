#!/usr/bin/env python3
"""Synthetic mathematical and contract checks; no EEG or model validity claim."""
import math
import numpy as np
from source_probe_metrics import analyse, representation_stats

def check(condition, message):
    if not condition:
        raise AssertionError(message)

def make(z, pos=None, exc=None):
    n = z.shape[-1]
    return {"logits": z, "positive": np.eye(n, dtype=bool) if pos is None else pos,
            "exclusion": np.zeros((n,n), dtype=bool) if exc is None else exc,
            "q_prior": np.array([.5,.5]), "q_support": np.array([.75,.25])}

def main():
    names = []
    zero = np.zeros((1,2,4,4))
    a = analyse(make(zero))
    check(abs(a["uniform_score_loss_nats"]-math.log(4))<1e-12, "single-positive chance")
    check(abs(a["slot_diagnostics"][0]["top1_tie_credit_eeg_to_audio"]-.25)<1e-12,
          "ties must receive fractional credit")
    names.append("uniform loss and tie credit")

    pos = np.array([[1,1,0,0],[1,1,0,0],[0,0,1,1],[0,0,1,1]],dtype=bool)
    exc = np.array([[0,0,1,0],[0,0,0,0],[1,0,0,0],[0,0,0,0]],dtype=bool)
    a = analyse(make(zero,pos,exc))
    expected = .5*(math.log(3/2)+math.log(4/2))
    check(abs(a["uniform_score_loss_nats"]-expected)<1e-12, "mask-aware multipositive chance")
    check(abs(a["slot_diagnostics"][0]["gain_over_uniform_score_nats"])<1e-12, "matched zero scores")
    names.append("masked multipositive chance differs from lnN")

    strong=zero.copy()
    strong[0,0]=10*np.eye(4)
    a=analyse(make(strong))
    check(a["support_gate_gain_in_supplied_nce_nats"]>0, "more mass on stronger slot must improve NCE")
    names.append("gate gain direction")

    masked = zero.copy()
    masked[...,exc] = 1000
    a=analyse(make(masked,pos,exc)); b=analyse(make(zero,pos,exc))
    check(abs(a["slot_diagnostics"][0]["loss_nats"]-b["slot_diagnostics"][0]["loss_nats"])<1e-12,
          "excluded scores influence loss")
    names.append("excluded very large scores have no loss effect")

    s = representation_stats(np.full((67,8), .1))
    check(s["zero_variance_flag"] and s["effective_rank"]==0, "constant feature rank")
    s2 = representation_stats(np.eye(4))
    check(abs(s2["effective_rank"]-3)<1e-10, "centred simplex rank")
    names.append("effective rank and roundoff")

    for bad in ["overlap", "missing_positive", "nan", "bad_q", "nonboolean"]:
        x = make(zero.copy())
        if bad=="overlap": x["exclusion"][0,0]=True
        if bad=="missing_positive": x["positive"][0]=False
        if bad=="nan": x["logits"][0,0,0,0]=np.nan
        if bad=="bad_q": x["q_support"]=np.array([.2,.2])
        if bad=="nonboolean": x["positive"]=np.full((4,4),.2)
        try:
            analyse(x)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid case accepted: "+bad)
    names.append("invalid masks, values and probabilities rejected")
    import json
    import subprocess
    import sys
    import tempfile
    from pathlib import Path
    with tempfile.TemporaryDirectory(prefix="aln42-source-check-") as tmp:
        root=Path(tmp)
        source, out=root/"synthetic.npz", root/"summary.json"
        np.savez(source, **make(zero))
        command=[sys.executable,"-B",str(Path(__file__).with_name("source_probe_metrics.py")),
                 "--input",str(source),"--output",str(out)]
        first=subprocess.run(command,capture_output=True,text=True,timeout=15)
        check(first.returncode==0 and out.is_file(), "valid CLI did not export JSON")
        saved=out.read_bytes()
        result=json.loads(saved)
        check("support_gate_gain_in_supplied_nce_nats" in result, "CLI diagnostic scope names")
        repeat=subprocess.run(command,capture_output=True,text=True,timeout=15)
        check(repeat.returncode==2 and out.read_bytes()==saved, "CLI overwrote existing output")
        invalid=make(zero.copy()); invalid["positive"][0]=False
        np.savez(source, **invalid)
        command[-1]=str(root/"invalid.json")
        failed=subprocess.run(command,capture_output=True,text=True,timeout=15)
        check(failed.returncode==2 and not (root/"invalid.json").exists(), "invalid CLI produced a result")
    names.append("CLI JSON export, overwrite protection and invalid input rejection")
    print(json.dumps({"status":"PASS","checks":names,
                      "scope":"synthetic numerical contract only"},ensure_ascii=False))
if __name__=="__main__":
    main()

