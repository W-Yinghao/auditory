"""Read-only: per run, on samples 6400..12799 (100 s) of all 64 rows: |sum over channels| / per-channel SD (CAR check), per-channel SD
range, flat rows (SD < 1e-6), non-finite count."""
import json, os
import numpy as np
D = "/projects/EEG-foundation-model/auditory_public/sparrkulee_nm000238_v1.0.0/derivatives/preprocessed_eeg"
HERE = os.path.dirname(os.path.abspath(__file__)); RT = json.load(open(os.path.join(HERE, "runtable.json")))
car, sdmin, sdmax, flat, nonfin, rows = [], [], [], 0, 0, []
for r in RT["runs"]:
    p = f"{D}/sub-{r['sub']}/ses-{r['ses']}/sub-{r['sub']}_ses-{r['ses']}_task-{r['task']}_run-{r['run']}_desc-preproc-audio-{r['stim']}_eeg.npy"
    x = np.ascontiguousarray(np.load(p, mmap_mode="r", allow_pickle=False)[:, 6400:12800])
    nonfin += int((~np.isfinite(x)).sum()); sd = x.std(1); flat += int((sd < 1e-6).sum())
    car.append(float(np.abs(x.sum(0)).max() / np.median(sd))); sdmin.append(float(sd.min())); sdmax.append(float(sd.max()))
    rows.append({"sub": r["sub"], "stim": r["stim"], "sd_min": float(sd.min()), "sd_med": float(np.median(sd)), "sd_max": float(sd.max())})
car = np.array(car); print("runs", len(car), "max |channel-sum| / median SD: max %.2e (CAR if ~1e-12)" % car.max(), "runs with ratio > 1e-6:", int((car > 1e-6).sum()))
md = np.array([x["sd_med"] for x in rows]); print("per-run median channel SD (uV?): q0 %.2f q5 %.2f q50 %.2f q95 %.2f q100 %.2f" % tuple(np.quantile(md, [0, .05, .5, .95, 1])))
print("per-run max channel SD: q50 %.1f q95 %.1f max %.1f; flat rows %d; non-finite %d" % (np.median(sdmax), np.quantile(sdmax, .95), max(sdmax), flat, nonfin))
json.dump(rows, open(os.path.join(HERE, "car_scale.json"), "w"))
