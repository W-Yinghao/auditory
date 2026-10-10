"""Engineering smoke of every repaired code path on real data (tiny budgets; technical pass/fail only, no performance
threshold). Output in private/auditory_alignment_v2/smoke_repair (removed after the check)."""
import glob
import json
import os
import sys
import time

sys.path.insert(0, "/home/infres/yinwang/EEG_auditory")
from auditory_alignment_v2 import run_adapt, run_fm, run_stage  # noqa: E402
from auditory_alignment_v2.donor import train_donor  # noqa: E402
from auditory_alignment_v2.run import PLAN  # noqa: E402

S = "/home/infres/yinwang/EEG_auditory/private/auditory_alignment_v2/smoke_repair"
os.makedirs(S + "/fm_recipe", exist_ok=True); os.makedirs(S + "/ckpt", exist_ok=True)
plan = [json.loads(l) for l in open(PLAN)]
t0 = time.time(); report = []


def row(fam, ds, **spec):
    for r in plan:
        if r["family_id"] == fam and r["dataset"] == ds and r["subject_fold"] == 0 and r["seed"] == 3401 and r.get("content_fold", 0) in (0, None) \
                and all(r["spec"].get(k) == v for k, v in spec.items()):
            return r
    raise KeyError((fam, ds, spec))


def check(r, probe=True):
    p = f"{S}/units/{r['experiment_id']}.json"
    assert os.path.exists(p), ("no record", r["experiment_id"], glob.glob(f"{S}/units/{r['experiment_id']}*"))
    d = json.load(open(p)); assert d["status"] == "complete", d.get("error")
    if probe:
        assert d.get("readout_head", "").startswith("spatial_signed"), d.get("readout_head")
        ev = d["eval"]; assert "channel_probe_error" not in ev, ev.get("channel_probe_error")
        pp = ev["channel_probe"]["per_participant"]; assert len(pp) > 0
        k = next(iter(pp.values())); assert ("probe/regular" in k) or ("probe_auc" in k), list(k)
    report.append((r["family_id"], r["experiment_id"], round(time.time() - t0)))
    print("OK", r["family_id"], r["experiment_id"], f"{time.time() - t0:.0f}s", flush=True)


# 1. learning-rate selection path (1 epoch per candidate); candidate checkpoints must be removed after scoring
run_fm.lr_select("cbramod|pretrained_frozen|fau|NCE", out=S, epochs=1)
assert os.path.exists(f"{S}/fm_recipe/cbramod__pretrained_frozen__fau__NCE.json")
left = glob.glob(f"{S}/ckpt/lrsel/*"); assert not left, left
print("OK lr_select; no candidate checkpoints left", flush=True)
# 2. recipes for the smoke (fixed values; the real ones come from learning-rate selection) and a 2-epoch budget
for key, lr in {"cbramod__pretrained_peft__fau__NCE": (1e-3, 1e-3), "reve__pretrained_full__dtu__NCE": (3e-5, 1e-3),
                "cbramod__pretrained_peft__private_bdf__NCE": (1e-3, 1e-3), "cbramod__pretrained_full__dtu__NCE": (3e-5, 1e-3),
                "cbramod__pretrained_partial__dtu__NCE": (3e-5, 1e-3), "cbramod__pretrained_full__private_bdf__NCE": (3e-5, 1e-3),
                "cbramod__pretrained_partial__fau__NCE": (3e-5, 1e-3)}.items():
    json.dump({"chosen": {"lr_backbone": lr[0], "lr_head": lr[1]}, "smoke": True}, open(f"{S}/fm_recipe/{key}.json", "w"))
json.dump({"cbramod": 2, "reve": 2}, open(f"{S}/fm_recipe/epochs.json", "w"))
# 3. module B and the foundation arms of C / D
r_b = row("B_FM", "fau", architecture="cbramod", adaptation="pretrained_peft", objective="NCE"); run_fm.run_unit(r_b, S); check(r_b)
r_r = row("B_FM", "dtu", architecture="reve", adaptation="pretrained_full", objective="NCE"); run_fm.run_unit(r_r, S); check(r_r)
r_p = row("D_FM_GENERIC", "private_bdf", architecture="cbramod", adaptation="pretrained_peft", objective="NCE"); run_fm.run_unit(r_p, S); check(r_p)
r_c = row("C_ATTENTION", "fau", architecture="cbramod", training_task="alignment_plus_selection", objective="NCE"); run_fm.run_unit(r_c, S); check(r_c)
# 4. personal adaptation from the repaired task-trained base (r_b)
r_a = row("C_ADAPT", "fau", architecture="cbramod", adapter_kind="spatial_adapter", objective="NCE"); run_adapt.run_unit(r_a, S); check(r_a, probe=False)
# 5. donors (1 epoch), continued training, public-donor teacher, distillation
train_donor("cbramod", "full", ["dtu", "fau", "federici"], 3401, S, 3e-5, 1e-3, epochs=1)
train_donor("cbramod", "partial", ["dtu", "federici"], 3401, S, 3e-5, 1e-3, epochs=1)
dj = json.load(open(f"{S}/donors/donor__cbramod__full__dtu+fau+federici__s3401.json")); assert dj["readout_head"].startswith("spatial_signed")
r_t = row("D_FM_PUBLIC", "private_bdf", architecture="cbramod", adaptation="auditory_pretrained_full", objective="NCE"); run_stage.run_unit(r_t, S); check(r_t)
r_k = row("B_AUDITORY_CONTINUE", "fau", architecture="cbramod", adaptation="auditory_continued_partial", objective="NCE"); run_stage.run_unit(r_k, S); check(r_k)
r_d = row("D_LOCAL_DISTILL", "private_bdf", teacher="cbramod_auditory", objective="NCE", window="early"); run_stage.run_unit(r_d, S); check(r_d, probe=False)
last = glob.glob(f"{S}/ckpt/*_last.pt"); assert not last, last
print("ALL SMOKE CHECKS PASSED", json.dumps(report), f"{time.time() - t0:.0f}s")
