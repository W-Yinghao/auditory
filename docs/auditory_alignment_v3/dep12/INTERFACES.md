# DEP12 shared interfaces (owner: Agent S)

Status: **v1, 2026-10-23.** Module: `auditory_alignment_v3/dep12/encoders.py`. Checked on Slurm CPU (1047358) for B0, an ALN4.1 arm, an ALN3.4 CB and REVE fold model, REVE0 and the MindMix branch, on both the 64-channel and the private 20-channel montage.

## 1. Encoder API

```python
from auditory_alignment_v3.dep12 import encoders as ENC
enc = ENC.load('B0', 'cuda')                       # KeyError / NotServable / EncoderNotReady on failure
U = enc.represent(x, channel_names, pad_mask)      # torch.float32 [N, D] on the encoder device, rows L2 = 1
enc.meta                                           # static identity (below); enc.last_call = montage, D, token shape, padding check
enc.project(x, channel_names, pad_mask, view)      # diagnostics only: new-round 32-d training heads, source montage only
ENC.REGISTRY / ENC.refresh() / ENC.servable() / ENC.describe()
```

### Input `x`

- Shape `[N, C, 200]`, float32 (numpy or torch). It is one 1 s container at 200 Hz.
- The caller does the cropping (03 §1): native crop first, then resample the crop with `aln41.timebank.resample` (scipy-equivalent FFT), then pad.
  - Source / SparrKULee: the 64 Hz window q+[-26:38] (64 samples) becomes 200 samples, with no padding.
  - Private children: the real 0.8 s becomes 160 samples, standardised by the training-side rule, then 40 leading zeros are added.
- Amplitude: the cohort's established z-score units. The encoder applies its own amplitude convention exactly once:
  - CBraMod: 0.15·z;
  - REVE: clip(z, ±15);
  - MindMix: z unchanged.

### `channel_names`

- They must equal one registered montage order. Legacy aliases T3/T4/T5/T6 are mapped to T7/T8/P7/P8.
- Registered montages:
  - `sparrkulee` (equal to the `dtu` BioSemi-64 order);
  - `fau` (31);
  - `federici` (32);
  - `private_bdf` (20);
  - `mff` (E1..E128).
- Any other order raises `ValueError`. Why: CBraMod has no channel-name embedding. Its positional convolution reads the channel index order, so a silently permuted order would change U.

### `pad_mask`

- `[N, 200]` or `[200]` bool, where True means padding. `None` means nothing is declared.
- Padded samples must be exactly 0; otherwise `ValueError`.
- None of the backbones has a sample-level mask, so the mask is validated and recorded but does not change the forward.

### Representation `U`

The rule is identical for every servable encoder and is never conditioned on candidate audio:

1. Take the predetermined final-layer tokens `[N, C, P, E]`.
2. Apply a **parameter-free** LayerNorm over E for each token (eps 1e-5).
3. Flatten in channel-major (channel, patch, feature) order.
4. L2-normalise.

`D = C·P·E`:

| Encoder | Layer | Tokens (P × E) | D on 64 ch | D on private 20 ch |
|---|---|---|---|---|
| CBraMod (B0, new arms, ALN4.1, ALN3.4 CB) | transformer layer 12/12, proj_out removed | 1 × 200 | 12,800 | 4,000 |
| REVE (REVE0, ALN3.4 REVE) | final transformer output | 1 × 512 | 32,768 | 10,240 |
| MindMix branch | official fc_norm patch tokens; container right-padded to 400 (patch 1 = padding) | 2 × 200 | 25,600 | 8,000 |

`tokens_to_U(h)` is the single implementation. The trainer and the dev probe call it too.

- `represent` runs in `torch.no_grad()` and eval mode, in chunks of 512.
- Memory: at D = 12,800, 10k rows take 0.5 GB. Chunk large panels yourself and move U to the CPU.

### `meta`

Fields: name, kind, arch, checkpoint, checkpoint_sha256, mode, step, objective, seed, layer, token_E, patches, input_support, input_support_flag, data_access, representation, ln_eps, api_version.

- New-round arms also carry `run` and `net_digest`.
- After each call, `last_call` gives montage, n_channels, D, token_shape and the padding check.

## 2. Registry (212 entries, 165 servable at v1)

| Name pattern | Kind | Servable | Input-support flag | Data access |
|---|---|---|---|---|
| `B0` | stage1_zero_update | yes | same_as_new_round | generic pretraining only |
| `cs_pair@{3401,3407,3413}`, `info_nce@…`, `sigmoid@…`, `raw_cs@3401`, `cs_pair_wrong@3401` | new_round_production (step 10000) | yes once trained | same_as_new_round | SparrKULee fit paired audio |
| `E0.{cs_pair,info_nce}.{full,lora}@3401` | new_round_e0_pilot (step 2500) | yes once trained | same_as_new_round | as above |
| `aln41_{TCS,TNCE,GCS,WRONG}@{3401,3407,3413}` | reused_aln41 (update 10000) | yes | **different_input_support** (trained on three 400 ms crops: 80 real + 120 zero samples) | SparrKULee fit |
| `aln34_cb_full@{ds}.s{seed}.sf{k}.cf{j}`, `aln34_cb_random@…`, `aln34_reve_full@…` | reused_aln34 (ALN32 best checkpoint) | yes | **same_1s_span_different_resampler_and_data_access** | **target-cohort training people of that fold** |
| `aln34_local@…` | reused_aln34 | **no** | not applicable | — |
| `REVE0` | generic_reference | yes | same_container_different_backbone | generic pretraining |
| `MINDMIX_branch` | external_branch | yes | **different_interface_padding_and_amplitude** | external release |
| `MINDMIX_full_fusion`, `MINDMIX_stage1_eeg_only` | external | **no** | — | — |

Fold models: DTU has 3 seeds × 10 folds; FAU has seed 3401 × 10; Federici has seed 3401 × 5.

New-round names stay `planned_mode_unselected` until `results/auditory_alignment_v3/dep12/E0_SELECTION.json` exists. After that they stay `planned` until their run receipt lists the checkpoint, and then they become `available`. Call `ENC.refresh()` to pick up new checkpoints.

Not-servable reasons (also in `REGISTRY[name]['not_servable_reason']`):

- **aln34_local:** a lag-token model with its own native-rate input contract and no transformer token layer. The 200 Hz container is not its input, and it cannot be inverted to native samples for 250 Hz private data. Use the archived ALN3.4 content_time arrays.
- **MINDMIX_full_fusion:** the system conditions on candidate audio (CALRA). It is a system score, not an independent EEG representation.
- **MINDMIX_stage1_eeg_only:** the ALN4.1 STAGE1_GATE was not passed (architecture and position-table gaps, unrecoverable channel→position mapping).

### Identities

- **B0 weights:**
  - `/projects/EEG-foundation-model/auditory_public/foundation_models/weighting666__CBraMod@500543c/pretrained_weights.pth`
  - sha256 `0792cb808c14e6b7a2bb2ce1dff379bc47bc54c49a779825bdfeb33bf8157178`
  - HF revision 500543c7; official code b9e96100. This is the same Stage1 file that ALN4.1 bound in `aln41/intake/STAGE1_GATE.json`.
  - Strict load via `foundation_adapter.Backbone('cbramod', …, 'pretrained_full', 200)`.
- **MindMix branch:** `paper/encoders_v1/assets/mindmix_eeg_branch.pt`, sha256 `b9fa2cfd…8646d`, extracted from release `fe2603e3…`.

## 3. Things measurement and private agents must not assume

- **Same channel count is not enough.** CBraMod applied to another montage only works because the positional convolution is index-based; channel identity is not encoded.
- **ALN4.1 arms are served off their training interface.** They were trained on 400 ms crops, not on the 1 s container. Report them with their flag. Their own frozen 3-crop arrays are an alternative that is not identical to this interface.
- **ALN3.4 CB/REVE are fold models.** They were trained on target-cohort training people. Use only the fold whose held-out people and contents you evaluate, and flag the access.
- **New-round arms are not available yet.** Until E0 selects a mode, `cs_pair@3401` etc. raise `EncoderNotReady`.

## 4. Registry version 2 (`encoders_v2.py`, extension 1, 2026-10-23)

- **What it adds:** four names, `raw_cs@3407`, `raw_cs@3413`, `cs_pair_wrong@3407` and `cs_pair_wrong@3413` (LoRA, step 10,000). These are the extension-1 mechanism controls, trained by `source_fleet_ext1` (DECISIONS 2026-10-23 07:30, S18, S19).
- **Same API** as v1: `REGISTRY`, `refresh()`, `servable()`, `describe()`, `load()`. Import `from auditory_alignment_v3.dep12 import encoders_v2 as ENC`.
- **Identical representation:** v1 (`encoders.py`, sha256 0201f975…) is imported unchanged and not edited. Every v1 name loads through `encoders.load`. The extension names use the same `CBraModEncoder` branch.
  - Checked: U of `raw_cs@3401` is bit-identical through v1 and v2.
  - `meta['api_version']` stays `dep12_encoders_v1`. Extension encoders also carry `meta['registry_module'] = 'encoders_v2'`.
- **State:** the four names are `planned` until their run receipts list step 10,000, then `available`.
- **For Agents M/P:** extraction of these names needs a versioned change on your side. Your arm lists are hard-coded, and your `sources()` pin `encoders.py`; add `encoders_v2.py` to the pins and keep `encoders.py`.
