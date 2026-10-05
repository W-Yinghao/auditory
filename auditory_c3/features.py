"""P0 stimulus features for FAU/TUD (03 §3.3; 07 P0): frozen speech models used as feature extractors only.

Units (each atomic, done-marked, preemption-safe):
  whisper : openai/whisper-large-v3 encoder, all hidden states (embedding + 32 layers, 1280-d, 50 Hz) + 128-bin log-mel (100 Hz)
  xlsr    : facebook/wav2vec2-xls-r-300m, all hidden states (CNN output + 24 layers, 1024-d, ~50 Hz)
  asr     : Whisper-large-v3 German transcription with word timestamps
  gpt2    : dbmdz/german-gpt2 word surprisal (bits) over the asr words, context restricted to the same stream
Every stimulus code x stream (attended / distractor) is read from the HA HDF5 stimulus_files (the copy aligned to the EEG);
the CI and TH copies are hashed and must be identical. Silent streams (single-speaker distractor) are flagged, not encoded.
No EEG is read. PCA (k = 3/5/8) is a separate CPU step on these caches.

Usage: python -m auditory_c3.features <whisper|xlsr|asr|gpt2|check>
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time

import numpy as np

ROOT = "/projects/EEG-foundation-model/auditory_public"
H5 = {"ha": "fau_tud/zenodo_17927767_ha/hi_dataset_1kHz.hdf5", "ci": "fau_tud/zenodo_17952844_ci/ci_dataset_1kHz.hdf5",
      "th": "fau_tud/zenodo_17952231_th/nh_dataset_1kHz.hdf5"}
OUT = os.path.join(ROOT, "derived", "c3_features_v1", "fau_tud")
MODELS = {"whisper": "openai/whisper-large-v3", "xlsr": "facebook/wav2vec2-xls-r-300m", "gpt2": "dbmdz/german-gpt2"}
WAV_SR, SR = 48000, 16000
WIN_S, HOP_S = 30.0, 20.0  # sliding encoder windows; each frame is taken from the window where it is most central


def _streams():
    import h5py
    from scipy.signal import resample_poly
    with h5py.File(os.path.join(ROOT, H5["ha"]), "r") as f:
        for code in sorted(f["stimulus_files"].keys()):
            for stream in ("attended", "distractor"):
                raw = f[f"stimulus_files/{code}/{stream}_wav"][()]
                x = raw.astype(np.float64) / 2**31
                silent = bool(np.sqrt(np.mean(x**2)) < 1e-6)
                x16 = resample_poly(x, 1, 3).astype(np.float32)
                yield code, stream, x16, silent, hashlib.sha256(raw.tobytes()).hexdigest()


def _windows(n_samples):
    """Return [(start, end, keep_lo, keep_hi)] in samples at SR; keep ranges tile [0, n) without overlap."""
    win, hop = int(WIN_S * SR), int(HOP_S * SR)
    margin = (win - hop) // 2
    starts = list(range(0, max(1, n_samples - win + hop), hop))
    out = []
    for i, s in enumerate(starts):
        e = min(s + win, n_samples)
        lo = s if i == 0 else s + margin
        hi = e if (i == len(starts) - 1 or e >= n_samples) else s + win - margin
        out.append((s, e, lo, hi))
        if e >= n_samples:
            break
    return out


def _atomic_h5(path):
    import h5py
    tmp = path + ".tmp"
    if os.path.exists(tmp):
        os.remove(tmp)
    return h5py.File(tmp, "w"), tmp


def _done(path):
    return os.path.exists(path) and os.path.exists(path + ".done.json")


def _finish(path, tmp, meta):
    os.replace(tmp, path)
    meta["sha256"] = hashlib.sha256(open(path, "rb").read()).hexdigest()
    meta["bytes"] = os.path.getsize(path)
    with open(path + ".done.json", "w") as fh:
        json.dump(meta, fh, indent=1)
    print("done", path, meta["sha256"][:16], flush=True)


def _snapshot(model_id):
    """Download config/tokenizer + safetensors weights only (fall back to .bin when a repo has no safetensors)."""
    from huggingface_hub import list_repo_files, snapshot_download
    files = list_repo_files(model_id)
    weights = ["*.safetensors"] if any(f.endswith(".safetensors") for f in files) else ["pytorch_model*.bin"]
    p = snapshot_download(model_id, allow_patterns=["*.json", "*.txt", "*.model", "*.tiktoken"] + weights)
    return p, os.path.basename(p.rstrip("/"))


def run_whisper():
    import torch
    from transformers import WhisperFeatureExtractor, WhisperModel
    path = os.path.join(OUT, "whisper_large_v3_hidden.h5")
    if _done(path):
        print("skip", path); return
    snap, rev = _snapshot(MODELS["whisper"])
    fe = WhisperFeatureExtractor.from_pretrained(snap)
    enc = WhisperModel.from_pretrained(snap, dtype=torch.float16).encoder.cuda().eval()
    f, tmp = _atomic_h5(path)
    fmel_path = os.path.join(OUT, "whisper_logmel128.h5")
    fm, tmpm = _atomic_h5(fmel_path)
    for code, stream, x, silent, wsha in _streams():
        g = f.create_group(f"{code}/{stream}"); gm = fm.create_group(f"{code}/{stream}")
        for gg in (g, gm):
            gg.attrs.update(silent=silent, wav_sha256=wsha, n_samples_16k=len(x), seconds=len(x) / SR)
        if silent:
            continue
        n_frames = int(np.ceil(len(x) / SR * 50))
        hs = None
        mel_full = np.zeros((128, int(np.ceil(len(x) / SR * 100))), np.float16)
        for s, e, lo, hi in _windows(len(x)):
            feats = fe(x[s:e], sampling_rate=SR, return_tensors="pt").input_features  # (1, 128, 3000), padded to 30 s
            with torch.no_grad():
                out = enc(feats.half().cuda(), output_hidden_states=True)
            H = torch.stack(out.hidden_states, 0)[:, 0].float().cpu().numpy()  # (33, 1500, 1280)
            if hs is None:
                hs = np.zeros((H.shape[0], n_frames, H.shape[2]), np.float16)
            a, b = int(round((lo - s) / SR * 50)), int(round((hi - s) / SR * 50))
            A = int(round(lo / SR * 50))
            b = min(b, a + n_frames - A)
            hs[:, A:A + (b - a)] = H[:, a:b]
            ma, mb, MA = int(round((lo - s) / SR * 100)), int(round((hi - s) / SR * 100)), int(round(lo / SR * 100))
            mb = min(mb, ma + mel_full.shape[1] - MA)
            mel_full[:, MA:MA + (mb - ma)] = feats[0, :, ma:mb].numpy().astype(np.float16)
        for li in range(hs.shape[0]):
            g.create_dataset(f"layer_{li:02d}", data=hs[li], compression="lzf")
        g.attrs["frame_rate_hz"] = 50.0; g.attrs["frame_time_offset_s"] = 0.01
        gm.create_dataset("logmel", data=mel_full, compression="lzf"); gm.attrs["frame_rate_hz"] = 100.0
        print(code, stream, hs.shape, flush=True)
    f.attrs.update(model=MODELS["whisper"], revision=rev, windows=f"{WIN_S}s/{HOP_S}s centre-kept", dtype="float16")
    fm.attrs.update(model=MODELS["whisper"], revision=rev, note="Whisper feature-extractor log-mel input, 128 bins")
    f.close(); fm.close()
    meta = {"model": MODELS["whisper"], "revision": rev, "torch": torch.__version__}
    _finish(fmel_path, tmpm, dict(meta)); _finish(path, tmp, meta)


def run_xlsr():
    import torch
    from transformers import Wav2Vec2FeatureExtractor, Wav2Vec2Model
    path = os.path.join(OUT, "xlsr300m_hidden.h5")
    if _done(path):
        print("skip", path); return
    snap, rev = _snapshot(MODELS["xlsr"])
    try:
        fe = Wav2Vec2FeatureExtractor.from_pretrained(snap)
    except OSError:  # pretraining checkpoint without preprocessor_config.json: XLS-R defaults
        fe = Wav2Vec2FeatureExtractor(feature_size=1, sampling_rate=SR, padding_value=0.0, do_normalize=True)
    model = Wav2Vec2Model.from_pretrained(snap).cuda().eval()  # fp32: layer-norm statistics are sensitive in fp16
    f, tmp = _atomic_h5(path)
    for code, stream, x, silent, wsha in _streams():
        g = f.create_group(f"{code}/{stream}")
        g.attrs.update(silent=silent, wav_sha256=wsha, n_samples_16k=len(x), seconds=len(x) / SR)
        if silent:
            continue
        n_frames = (len(x) - 400) // 320 + 1
        hs = None
        for s, e, lo, hi in _windows(len(x)):
            inp = fe(x[s:e], sampling_rate=SR, return_tensors="pt").input_values.cuda()
            with torch.no_grad():
                out = model(inp, output_hidden_states=True)
            H = torch.stack(out.hidden_states, 0)[:, 0].cpu().numpy()  # (25, frames, 1024)
            if hs is None:
                hs = np.zeros((H.shape[0], n_frames, H.shape[2]), np.float16)
            # frame i of this window is centred at s + i*320 + 200 samples
            idx = np.arange(H.shape[1]); centre = s + idx * 320 + 200
            sel = (centre >= lo) & (centre < hi)
            gi = (centre[sel] - 200) // 320
            ok = gi < n_frames
            hs[:, gi[ok]] = H[:, idx[sel][ok]].astype(np.float16)
        for li in range(hs.shape[0]):
            g.create_dataset(f"layer_{li:02d}", data=hs[li], compression="lzf")
        g.attrs["frame_rate_hz"] = 50.0; g.attrs["frame_time_offset_s"] = 200 / SR
        print(code, stream, hs.shape, flush=True)
    f.attrs.update(model=MODELS["xlsr"], revision=rev, windows=f"{WIN_S}s/{HOP_S}s centre-kept", dtype="float16")
    f.close()
    _finish(path, tmp, {"model": MODELS["xlsr"], "revision": rev, "torch": torch.__version__})


def run_asr():
    import torch
    from transformers import pipeline
    path = os.path.join(OUT, "asr_words_whisper_large_v3.json")
    if os.path.exists(path + ".done.json"):
        print("skip", path); return
    snap, rev = _snapshot(MODELS["whisper"])
    pipe = pipeline("automatic-speech-recognition", model=snap, dtype=torch.float16, device=0,
                    chunk_length_s=30, return_timestamps="word")
    res, failures = {}, {}
    for code, stream, x, silent, wsha in _streams():
        key = f"{code}/{stream}"
        if silent:
            res[key] = {"silent": True}; continue
        try:
            o = pipe({"raw": x, "sampling_rate": SR}, generate_kwargs={"language": "german", "task": "transcribe"})
            words = [{"w": c["text"].strip(), "t0": c["timestamp"][0], "t1": c["timestamp"][1]} for c in o["chunks"]]
            res[key] = {"silent": False, "wav_sha256": wsha, "text": o["text"], "words": words}
            print(key, len(words), "words", flush=True)
        except Exception as ex:  # recorded, never silently dropped
            failures[key] = f"{type(ex).__name__}: {ex}"[:500]
            print("ASR_FAIL", key, failures[key], flush=True)
    tmp = path + ".tmp"
    json.dump({"model": MODELS["whisper"], "revision": rev, "streams": res, "failures": failures}, open(tmp, "w"), ensure_ascii=False)
    os.replace(tmp, path)
    json.dump({"model": MODELS["whisper"], "revision": rev, "n_failures": len(failures),
               "sha256": hashlib.sha256(open(path, "rb").read()).hexdigest()}, open(path + ".done.json", "w"), indent=1)
    print("done", path, "failures", len(failures))


def run_gpt2():
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    src = os.path.join(OUT, "asr_words_whisper_large_v3.json")
    path = os.path.join(OUT, "gpt2_german_word_surprisal.json")
    if os.path.exists(path + ".done.json"):
        print("skip", path); return
    if not os.path.exists(src + ".done.json"):
        raise SystemExit("asr unit not done")
    snap, rev = _snapshot(MODELS["gpt2"])
    tok = AutoTokenizer.from_pretrained(snap)
    lm = AutoModelForCausalLM.from_pretrained(snap).cuda().eval()
    asr = json.load(open(src))
    out = {}
    ctx_max, stride = lm.config.n_positions, lm.config.n_positions // 2
    # dbmdz/german-gpt2 has no <|endoftext|> in its 50265-token vocabulary: transformers appends one at id 50265
    # (outside the embedding table) and config.bos_token_id = 50256 is the ordinary subword "riegel". The vocabulary's
    # own sequence-start special token <s> (id 0) is used as context start; only each stream's first word depends on it.
    start_id = tok.convert_tokens_to_ids("<s>")
    n_emb = lm.get_input_embeddings().num_embeddings
    assert start_id == 0 and start_id < n_emb, (start_id, n_emb)
    for key, s in asr["streams"].items():
        if s.get("silent") or "words" not in s:
            continue
        ids, owner = [start_id], [-1]
        for i, w in enumerate(s["words"]):
            t = tok((" " if i else "") + w["w"], add_special_tokens=False)["input_ids"]
            ids += t; owner += [i] * len(t)
        assert max(ids) < n_emb, (key, max(ids), n_emb)  # fail on the CPU side, never as a CUDA device assert
        ids_t = torch.tensor(ids)
        lp = np.full(len(ids), np.nan)
        start = 0
        while True:
            end = min(start + ctx_max, len(ids))
            with torch.no_grad():
                logits = lm(ids_t[start:end][None].cuda()).logits[0].float()
            logp = torch.log_softmax(logits, -1)
            first = 1 if start == 0 else stride  # score each target position exactly once, with >= stride context
            for p in range(start + first, end):
                lp[p] = logp[p - start - 1, ids[p]].item()
            if end == len(ids):
                break
            start = end - stride
        sur = np.zeros(len(s["words"]))
        for p in range(1, len(ids)):
            sur[owner[p]] += -lp[p] / np.log(2)
        out[key] = [{"w": w["w"], "t0": w["t0"], "t1": w["t1"], "surprisal_bits": float(v)} for w, v in zip(s["words"], sur)]
        print(key, len(out[key]), flush=True)
    tmp = path + ".tmp"
    json.dump({"model": MODELS["gpt2"], "revision": rev, "asr_source_sha256": hashlib.sha256(open(src, "rb").read()).hexdigest(),
               "context": "within stream, sliding 1024/512", "context_start_token": "<s> (id 0)",
               "note": "first word of each stream is conditioned on <s> only", "streams": out}, open(tmp, "w"), ensure_ascii=False)
    os.replace(tmp, path)
    json.dump({"model": MODELS["gpt2"], "revision": rev, "sha256": hashlib.sha256(open(path, "rb").read()).hexdigest()},
              open(path + ".done.json", "w"), indent=1)


def run_check():
    """CI/TH stimulus copies must equal the HA copy (the features are computed once from HA)."""
    import h5py
    rep = {}
    hashes = {}
    for grp, rel in H5.items():
        with h5py.File(os.path.join(ROOT, rel), "r") as f:
            for code in sorted(f["stimulus_files"].keys()):
                for k in sorted(f[f"stimulus_files/{code}"].keys()):
                    hashes.setdefault(f"{code}/{k}", {})[grp] = hashlib.sha256(f[f"stimulus_files/{code}/{k}"][()].tobytes()).hexdigest()
    diff = {k: v for k, v in hashes.items() if len(set(v.values())) != 1 or len(v) != 3}
    rep["n_arrays"] = len(hashes); rep["n_differing"] = len(diff); rep["differing"] = diff
    os.makedirs(OUT, exist_ok=True)
    json.dump(rep, open(os.path.join(OUT, "stimulus_copy_check.json"), "w"), indent=1)
    print(json.dumps({k: rep[k] for k in ("n_arrays", "n_differing")}))
    if diff:
        raise SystemExit("stimulus copies differ across groups")


def main(argv=None):
    unit = (argv or sys.argv[1:])[0]
    os.makedirs(OUT, exist_ok=True)
    t = time.time()
    {"whisper": run_whisper, "xlsr": run_xlsr, "asr": run_asr, "gpt2": run_gpt2, "check": run_check}[unit]()
    print(f"unit {unit} finished in {time.time() - t:.0f}s")


if __name__ == "__main__":
    main()
