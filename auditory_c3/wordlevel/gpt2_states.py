"""Word-level GPT-2 hidden states (docs/auditory_c3/WORDLEVEL_REG_v1.md), stimulus side only, no EEG.

Same model, revision, tokenisation, <s> context start and sliding 1024/512 context as the frozen surprisal file
(auditory_c3.features.run_gpt2): every token position takes its hidden states from the window in which it is scored,
so each word's state has >= 512 tokens of context (except near the stream start). Word state = mean over the word's
tokens, for every layer 0..12 (0 = embeddings).

Usage: python -m auditory_c3.wordlevel.gpt2_states
Output: private/auditory_c3/wordlevel/gpt2_word_states.h5  ({stream}/layer_XX (n_words, 768) float16, n_tokens)
"""
from __future__ import annotations

import hashlib
import json
import os

import numpy as np

from ..features import MODELS, OUT as FEAT, _snapshot

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DST = os.path.join(REPO, "private", "auditory_c3", "wordlevel", "gpt2_word_states.h5")


def main():
    import h5py
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    if os.path.exists(DST + ".done.json"):
        print("skip", DST); return
    sur = json.load(open(os.path.join(FEAT, "gpt2_german_word_surprisal.json")))
    snap, rev = _snapshot(MODELS["gpt2"])
    assert rev == sur["revision"], (rev, sur["revision"])
    tok = AutoTokenizer.from_pretrained(snap)
    lm = AutoModelForCausalLM.from_pretrained(snap).cuda().eval()
    start_id = tok.convert_tokens_to_ids("<s>"); n_emb = lm.get_input_embeddings().num_embeddings
    assert start_id == 0
    ctx_max, stride = lm.config.n_positions, lm.config.n_positions // 2
    tmp = DST + ".tmp"
    with h5py.File(tmp, "w") as o:
        for key, words in sur["streams"].items():
            ids, owner = [start_id], [-1]
            for i, w in enumerate(words):
                t = tok((" " if i else "") + w["w"], add_special_tokens=False)["input_ids"]
                ids += t; owner += [i] * len(t)
            assert max(ids) < n_emb
            ids_t = torch.tensor(ids)
            H = None
            start = 0
            while True:
                end = min(start + ctx_max, len(ids))
                with torch.no_grad():
                    hs = lm(ids_t[start:end][None].cuda(), output_hidden_states=True).hidden_states
                hs = torch.stack(hs, 0)[:, 0].float().cpu().numpy()  # (13, L, 768)
                if H is None:
                    H = np.zeros((hs.shape[0], len(ids), hs.shape[2]), np.float32)
                first = 0 if start == 0 else stride
                H[:, start + first:end] = hs[:, first:end - start]
                if end == len(ids):
                    break
                start = end - stride
            owner = np.array(owner)
            nw = len(words)
            cnt = np.bincount(owner[1:], minlength=nw)
            W = np.zeros((H.shape[0], nw, H.shape[2]), np.float32)
            np.add.at(W, (slice(None), owner[1:]), H[:, 1:])
            W /= np.maximum(cnt, 1)[None, :, None]
            g = o.create_group(key)
            for li in range(W.shape[0]):
                g.create_dataset(f"layer_{li:02d}", data=W[li].astype(np.float16), compression="lzf")
            g.create_dataset("n_tokens", data=cnt.astype(np.int16))
            print(key, nw, flush=True)
        o.attrs.update(model=MODELS["gpt2"], revision=rev, context="within stream, sliding 1024/512, <s> start",
                       word_state="mean over the word's tokens", surprisal_source_sha256=hashlib.sha256(
                           open(os.path.join(FEAT, "gpt2_german_word_surprisal.json"), "rb").read()).hexdigest())
    os.replace(tmp, DST)
    json.dump({"model": MODELS["gpt2"], "revision": rev, "sha256": hashlib.sha256(open(DST, "rb").read()).hexdigest()},
              open(DST + ".done.json", "w"), indent=1)
    print("done", DST)


if __name__ == "__main__":
    main()
