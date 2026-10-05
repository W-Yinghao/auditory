"""DTU language features for C3_EXTENSIONS_REG_v1 B1: Danish word-level ASR (Whisper large-v3, language="danish",
same revision as FAU/TUD) of every unique TARGET waveform, and word surprisal from the multilingual causal LM
ai-forever/mGPT (sliding context within the stream, as for FAU/TUD GPT-2).

Usage: python -m auditory_c3.features_dtu_lang <asr|lm>
Outputs: <DTU FEAT>/asr_words_whisper_large_v3_da.json, mgpt_word_surprisal_da.json (+ .done.json)
"""
from __future__ import annotations

import hashlib
import json
import os
import sys

import numpy as np

from .features import MODELS, _snapshot
from .features_dtu import OUT, SR, _mono16k

LM = "ai-forever/mGPT"


def _targets():
    inv = json.load(open(os.path.join(OUT, "inventory.json")))
    seen = {}
    for r in inv:
        if r["kind"] == "target" and r.get("sha") and r["path"] and r["sha"] not in seen:
            seen[r["sha"]] = r["path"]
    return seen


PARTS = os.path.join(OUT, "asr_da_parts")


def run_asr_shard(shard, n_shards):
    """Preemption-safe: one JSON per waveform in PARTS (atomic), existing parts skipped; shard = index % n_shards."""
    import torch
    from transformers import pipeline
    os.makedirs(PARTS, exist_ok=True)
    snap, rev = _snapshot(MODELS["whisper"])
    pipe = pipeline("automatic-speech-recognition", model=snap, dtype=torch.float16, device=0, chunk_length_s=30, return_timestamps="word")
    for i, (h, p) in enumerate(sorted(_targets().items())):
        out = os.path.join(PARTS, f"{h}.json")
        if i % n_shards != shard or os.path.exists(out):
            continue
        try:
            x, h2 = _mono16k(p)
            assert h2 == h
            o = pipe({"raw": x, "sampling_rate": SR}, generate_kwargs={"language": "danish", "task": "transcribe"})
            words = [{"w": c["text"].strip(), "t0": c["timestamp"][0], "t1": c["timestamp"][1]} for c in o["chunks"]]
            rec = {"text": o["text"], "words": words, "source": os.path.basename(p), "revision": rev}
        except Exception as ex:  # recorded, never silently dropped
            rec = {"failure": f"{type(ex).__name__}: {ex}"[:500], "revision": rev}
        json.dump(rec, open(out + ".tmp", "w"), ensure_ascii=False); os.replace(out + ".tmp", out)
        print(h[:10], len(rec.get("words", [])), flush=True)


def run_asr():
    """Merge the per-waveform parts (all must exist)."""
    path = os.path.join(OUT, "asr_words_whisper_large_v3_da.json")
    if os.path.exists(path + ".done.json"):
        print("skip", path); return
    tg = _targets()
    missing = [h for h in tg if not os.path.exists(os.path.join(PARTS, f"{h}.json"))]
    if missing:
        raise SystemExit(f"{len(missing)} waveforms not transcribed yet")
    res, failures, rev = {}, {}, None
    for h in sorted(tg):
        r = json.load(open(os.path.join(PARTS, f"{h}.json"))); rev = r.pop("revision", rev)
        if "failure" in r:
            failures[h] = r["failure"]
        else:
            res[h] = r
    tmp = path + ".tmp"
    json.dump({"model": MODELS["whisper"], "revision": rev, "language": "danish", "streams": res, "failures": failures}, open(tmp, "w"), ensure_ascii=False)
    os.replace(tmp, path)
    json.dump({"model": MODELS["whisper"], "revision": rev, "n_streams": len(res), "n_failures": len(failures),
               "sha256": hashlib.sha256(open(path, "rb").read()).hexdigest()}, open(path + ".done.json", "w"), indent=1)


def run_lm():
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    src = os.path.join(OUT, "asr_words_whisper_large_v3_da.json")
    path = os.path.join(OUT, "mgpt_word_surprisal_da.json")
    if os.path.exists(path + ".done.json"):
        print("skip", path); return
    snap, rev = _snapshot(LM)
    tok = AutoTokenizer.from_pretrained(snap)
    lm = AutoModelForCausalLM.from_pretrained(snap, dtype=torch.float16).cuda().eval()
    n_emb = lm.get_input_embeddings().num_embeddings
    start_id = tok.bos_token_id if tok.bos_token_id is not None else tok.eos_token_id
    assert start_id is not None and start_id < n_emb, (start_id, n_emb)
    ctx_max = int(getattr(lm.config, "n_positions", None) or getattr(lm.config, "max_position_embeddings", 1024)); stride = ctx_max // 2
    asr = json.load(open(src))
    out = {}
    for h, s in asr["streams"].items():
        ids, owner = [start_id], [-1]
        for i, w in enumerate(s["words"]):
            t = tok((" " if i else "") + w["w"], add_special_tokens=False)["input_ids"]
            ids += t; owner += [i] * len(t)
        assert max(ids) < n_emb, (h, max(ids), n_emb)
        ids_t = torch.tensor(ids); lp = np.full(len(ids), np.nan); start = 0
        while True:
            end = min(start + ctx_max, len(ids))
            with torch.no_grad():
                logp = torch.log_softmax(lm(ids_t[start:end][None].cuda()).logits[0].float(), -1)
            first = 1 if start == 0 else stride
            for p in range(start + first, end):
                lp[p] = logp[p - start - 1, ids[p]].item()
            if end == len(ids):
                break
            start = end - stride
        sur = np.zeros(len(s["words"]))
        for p in range(1, len(ids)):
            sur[owner[p]] += -lp[p] / np.log(2)
        out[h] = [{"w": w["w"], "t0": w["t0"], "t1": w["t1"], "surprisal_bits": float(v)} for w, v in zip(s["words"], sur)]
        print(h[:10], len(out[h]), float(np.mean(sur)) if len(sur) else None, flush=True)
    tmp = path + ".tmp"
    json.dump({"model": LM, "revision": rev, "asr_source_sha256": hashlib.sha256(open(src, "rb").read()).hexdigest(),
               "context": f"within stream, sliding {ctx_max}/{stride}", "context_start_token_id": int(start_id), "streams": out}, open(tmp, "w"), ensure_ascii=False)
    os.replace(tmp, path)
    json.dump({"model": LM, "revision": rev, "sha256": hashlib.sha256(open(path, "rb").read()).hexdigest()}, open(path + ".done.json", "w"), indent=1)


if __name__ == "__main__":
    if sys.argv[1] == "asr_shard":
        run_asr_shard(int(sys.argv[2]), int(sys.argv[3]))
    else:
        {"asr": run_asr, "lm": run_lm}[sys.argv[1]]()
