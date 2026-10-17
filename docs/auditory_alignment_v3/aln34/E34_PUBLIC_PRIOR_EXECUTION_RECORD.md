# E34_PUBLIC_PRIOR execution record — M13

Frozen 2026-10-17T14:26:25.030321+02:00 by Slurm CPU job 1044059. Real M12 GPU job 1043922 passed all three phases on Tesla V100S-PCIE-32GB. This record precedes production registration. Its 1,154 planned rows are not described as completed training.

Authority: ALN3.4 and the researcher's instructions to execute the package, complete the handoff and design/submit the next experiments. The standalone ALN3.3 zip never arrived; the byte-preserved ALN3.4 inherited contract and PUBLIC_PRIOR_DESIGN.md define aln33_env64_125ms_v1. No model-performance or wording gate applies.

## Completed prerequisites and scope

FIXC fixes the full/private manifest fallback, binds the rich supplement, verifies consumed bytes lazily, guards C2 reference eligibility, corrects the sub-051 reason, separates truncated probes from production and records resume code lineage. The generated target trainer retains the inherited computation; changed wrappers and seed descriptions are hashed below. Existing running ALN3 training files remain byte-identical.

CPU cache job 1043917 completed core → rich PCA refit → rich supplement → CPU probe selection → plan dry-run and compute-node sbatch --test-only. Core has N_SK=84,132; 673,056 anchors per epoch-equivalent; 2,629.125 steps per epoch-equivalent (ceil 2,630); initial 30-ep-eq S0=78,874. The eligible rich refit uses 1,899,000 unique windows. Pass-1 recomputed zero streams; original rich files are retained in rich_before_fixc_20261017. PCA SHA: 39ae5ee387c56ba624871db49d535c7af78edd1a5a8d158b788e9aa7d6bbfa07.

The 1,154 rows comprise core 540, zero-shot access 210, seed panel 120, rich 126 and CSX 158. Rich is a separate comparison, not a full cross-product of the core matrix. Compatible results are reused. Private data are loaded in memory inside target units; no private EEG cache is added.

## Decisions, limitations and deviations recorded before production results

1. Donor extension uses the first minimum without tolerance, excludes XM from its trigger and applies the same rule to all eligible contract members. Continuations retain previous results, source checkpoints and code hashes.
2. PCA and sigma use the same core-manifest unique donor-fit windows, excluding whole presentations barred by any target's donor set. Historical C7 outputs are preserved and are not the production basis.
3. SparrKULee sub-051 audiobook_12_2 remains a declared exclusion despite C2 classing it unverifiable. This departs from the general retention rule. The scout off-peak set contains the -8.84 s peak, so equality to its maximum was not prominence evidence. C2 diagnostics and the original decision provenance remain in the manifest.
4. Of 616 C2-audited runs, 148 are aligned, one misaligned and 467 unverifiable; another 50 entries were not audited. Unverifiable runs are generally retained under the declared rule. This is partial clock verification, not proof that every donor stream is correctly aligned. Restricted participants never enter reference or training reads.
5. Private test stimuli were not scanned against donors: non-overlap remains unverified. Historical individual overlap in generic foundation-model pretraining is also uncertified. These limitations do not become claims of independence.
6. The FAU:123 MAP_UNPLAYED_BY_CODE exclusion removes 2,025 of 16,848 FAU core-pool rows in each affected DTU/Federici donor set; the possibly inaudible stereo-channel caveat is retained.
7. FAU raw-uV mode C clips beyond +/-65,000 uV: two samples, participant 221. The aborted pre-clip output is preserved; A/B z-score caches are unchanged. Federici mode C is partial and cannot restore absent frequencies.
8. B_uni_cal uses bridge_cal as a labelled sensitivity. Primary bridges use donor fit. Rich and CSX bridges reuse the core fit/calibration rows, without silently adding fau_cs. Zero-shot mode C uses donor statistics.
9. Every consumed cache file is verified by SHA256 and byte size, memoized only while its stat and expected digest are unchanged. Donor opening does not load target caches. M12's integrity and bank-load timing include different work and are not pure hashing-overhead benchmarks.
10. Production wrappers refuse truncated donor chains and epoch overrides. Probe records remain parseable but excluded from production analysis. Resume records retain original/current code hashes and mismatches.
11. Analysis resamples identities, with group_seed(family, endpoint), separate NLL/AUC max-t families and actual paired coverage. Intervals condition on available fitted models; seeds and folds do not increase n.
12. Seed labels follow executed code: the manifest replaces the inherited target-statistics +5 fit; public early-stopping segment draws use 12345 and anchor draws use batch index, private early stopping uses batch index, +99 initializes objective calibration in both target paths, +98/+1000 are public-only, and +77 is the private CS kernel-reference path. Complete record fields describe applicable paths; unused labels are not executed randomness.
13. Original build_rich.py remains byte-identical for reusable pass-1 markers. Its three-versus-four no-source reason count and old Slurm docstring are documentation defects; actual availability is in the rich manifest. select.py's duplicate names_limit helper remains; operational dependency checks are separate.
14. M12 includes one-ep-eq DTU and private NCE donor groups for correct leave-target-out provenance. Its rich short run uses the initial H=30 schedule with the actual short core AP checkpoint solely as an engineering override; it does not establish a production horizon. Rich clock checks read the frozen C7 evidence for three streams per available cohort; C2 and the first SparrKULee participant are actually recomputed.

## Engineering evidence and actual resources

The broad FIXC suite 1043898 passed 418 cases and failed one obsolete private input-mode assertion. After correcting it and applicable seed descriptions, affected job 1043916 passed all 42 checks. Earlier 1043888 (181 passed, five failures) and 1043896 (three refit tests passed, one infrastructure admission-order whitespace assertion failed) are retained below with their corrections; they are not represented as clean runs. Registry staging check 1043934 preserved all 21 legacy groups across 7,398 records and 25 families. No unrecorded-family bypass was used.

| M12 phase | Wall seconds | GPU peak GiB | Status |
|---|---:|---:|---|
| integrity | 63.16 | 0.000 | pass |
| short | 1536.68 | 5.096 | pass |
| tiny | 59.36 | 4.695 | pass |

Detailed timings, selection checks, paired target budgets, sample windows, exact-resume checks, member curves and all short-run checkpoint provenance are in the complete receipt linked below. The probe is truncated engineering evidence. Production resource projections inherit the measured device/recipe limitations and are not a promised completion date. Pool weights are conservative admission estimates; the existing memory-aware pool and 10-GPU cap remain authoritative.

M12 receipt: `private/auditory_alignment_v3/probe_out_prior33/20261017T115309/receipt.json` SHA256 `4e715a92599ef5d6839538d3b8911acb54d2932d2ebb57ea9ea0616a429a6ac5`. Freeze audit: `private/auditory_alignment_v3/aln34/prior33_freeze_audit.json` SHA256 `d0ee1efdf8ba7141b107eb81e021c1063af1a52ab99f5482f98674b07b51efac`. Finalizer source SHA256: `34fa3d0c21e3e74747eb150fba93d66256090fbb73f15f03b2f3ecb59ba3c254`.

## Results known before registration

Already viewed: D multi-seed, the paired-order attention correction, D_ADAPT true risk, private E multi-seed, record-level complement findings, and TF refresh 1043925 (232/400 panel units; DTU 44 people fully paired across three seeds). The result-informed 150-unit DTU doubled-budget plan was registered independently. Private calibration stage-1 diagnosis 1043948 was also viewed: positive-affine NLL worsens REVE's three CS panel configurations; its 120-checkpoint leave-self-out evaluation is separately registered. Complement GPU evaluation is running. No production public-prior result has yet been generated under this record.

## Deployment and execution identity

Next, deploy checked registry, dispatch and offload; stop the old offload daemon gracefully and wait for exit before resubmitting. Append the locked plan only after these checks; then install queue/watcher changes and start the prior keeper (at most four prior workers, within ten running project GPUs). Existing obsolete execution holds stay intact. Use squeue/scancel/sbatch only; scontrol is prohibited. Every actual operation and job belongs in logs/operations.log and the mutable completion ledger, not retroactively in this frozen record.

## Frozen manifests

| File | SHA256 |
|---|---|
| /home/infres/yinwang/EEG_auditory/private/auditory_alignment_v3/aln34/prior33/manifest.json | `b751976b9238590026f26a6fbe6c84177b69802ef9e55e687425af210b627426` |
| /home/infres/yinwang/EEG_auditory/private/auditory_alignment_v3/aln34/prior33/manifest_rich.json | `c8f11c28b4014aec3f06f52e3c058640409d8fa9d0d8a91c95f2f05505eabcfd` |
| /projects/EEG-foundation-model/auditory_public/derived/aln33_env64_125ms_v1/manifest.json | `3ffa6e6d013283368d1f7eb09bf6c9e7573c0ae4009304cf3bc1d9836c197046` |
| /projects/EEG-foundation-model/auditory_public/derived/aln33_env64_125ms_v1/manifest_rich.json | `c8f11c28b4014aec3f06f52e3c058640409d8fa9d0d8a91c95f2f05505eabcfd` |

## Frozen training code groups

| Family | Code hash |
|---|---|
| ALN32_PUBLIC_AUDIO_PRIOR_BRIDGE | `e4388a47f659071a` |
| ALN32_PUBLIC_AUDIO_PRIOR_CSX_DONOR | `eed1a3a8bfa32d78` |
| ALN32_PUBLIC_AUDIO_PRIOR_DONOR | `eed1a3a8bfa32d78` |
| ALN32_PUBLIC_AUDIO_PRIOR_RICH_DONOR | `dd9467c57d3dc672` |
| ALN32_PUBLIC_AUDIO_PRIOR_TARGET | `ab726824e6bc30b5` |
| ALN32_PUBLIC_AUDIO_PRIOR_ZEROSHOT | `401807c2b8250d44` |

## Frozen file hashes

| File | SHA256 |
|---|---|
| AUDITORY_ALN3_SERVER_PACKAGE_v3_4_20261016/inherited/OBJECTIVES_v3_3.md | `b85b9d270c6de8718cd2f6badda820b358cc2f6e145ff2d10cd29e6342f3a181` |
| AUDITORY_ALN3_SERVER_PACKAGE_v3_4_20261016/inherited/PUBLIC_PRIOR_EXECUTION_v3_3.md | `8a4217a8d94545d87d8026f288d89f4824b6b3f24ef0be166b1aaa1078967f3e` |
| AUDITORY_ALN3_SERVER_PACKAGE_v3_4_20261016/inherited/public_prior_v3_3.yaml | `e8ecded1f0f9713f29f20ac0c03b9fd8aced09638732b523350a642459454baa` |
| auditory_alignment/aggregate.py | `bd6198da958a6f56f1cd3b57609dd6fbceecb5e80f73ac3f07bd08ba75632662` |
| auditory_alignment/data.py | `abeb9d368116e4b1b6becace401299660248e48356fa12f72084950282ebb6b5` |
| auditory_alignment/evaluate.py | `2393bb5cff5b37c3dd4443c990b19cfdc76cec4ac71581ac03230baba17ff800` |
| auditory_alignment/losses.py | `df8c862475b4f723d33e6236d1183b469e5f8f54a7b9df4748ee2e04ff2c65cb` |
| auditory_alignment/losses_reference.py | `e61566bf327e99c5b769dc69dd2fc9a3ffc7b4abfd2a3ea49dd082a2c1460aa0` |
| auditory_alignment/train.py | `930615f1e88ee61e26610623be24a7b199b912da9c7eb47b9d6e9627fb7c3b21` |
| auditory_alignment_v2/audio_targets.py | `a7699ae8ddc17cc58986e85ed02b043c8201072222edcd7459242ad626c5df1f` |
| auditory_alignment_v2/eval_fm.py | `81178c67ce879ae504d446f6dd427b5e06fef9583c9d066a5c81a12522c8abe7` |
| auditory_alignment_v2/evaluate.py | `84faf358c361eb33ccd7a6039806760433b1e447ac5d4faaebc5a8229aebbc4a` |
| auditory_alignment_v2/fm_readout.py | `7035108ab87aed6bcf7e297a6ca24f2728c5dceb64749b0a6fc028856efb3c4e` |
| auditory_alignment_v2/foundation_adapter.py | `09cd929720cfc9348a7b3c9b87139a1fae6e9e6c6adbe26556a7d5f6fb79e355` |
| auditory_alignment_v2/gx.py | `153cbdd50e341251f8e446a9437e13ab54563bac3f7dbcd7cc11874b62373f29` |
| auditory_alignment_v2/temporal.py | `790d66525b87aa3e32c355a77fb2c328bb7381d5f127b57b3e5cc2a867c131f9` |
| auditory_alignment_v2/train.py | `1a00101c1514c1cb790c8927c778e3fd80d3b0505685e71ec058bb7720b6f9a4` |
| auditory_alignment_v2/train_fm.py | `611b945aad7f86c593a828b209a7344d98f2433c4ece514513d7a7838aa1082a` |
| auditory_alignment_v3/aln3_reference/calibration.py | `77708987e75aa0c257dc597f9e0c17a2c94c57ce8c5779bbf845580e44f61a2b` |
| auditory_alignment_v3/calib.py | `f21e3933d83bcea0dfd766780fe0359e2da535ec3e803b1d7728a7a869649603` |
| auditory_alignment_v3/core.py | `a3851b4a601a1bd7a6365514d408703bb8c4ecb0b615751107f56b7fc3987262` |
| auditory_alignment_v3/local_train.py | `dee8d0cd58297e038b7a6e82c58a897aeb22dcc4109f1683396bce883a174c83` |
| auditory_alignment_v3/prior33/__init__.py | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| auditory_alignment_v3/prior33/analysis.py | `221405c791bee1917af91b26dcc33cfb726941c808b44b5b74a9eaea21dfe9c5` |
| auditory_alignment_v3/prior33/bridge.py | `e7b945d099a0baff66fd705bf8bf73782f270fe288b075f95bacc66c6eec6647` |
| auditory_alignment_v3/prior33/build_public.py | `be91be16b630120318d69447bf82ca0a4e765c570aa05e3100ee64a297bc00f5` |
| auditory_alignment_v3/prior33/build_rich.py | `5d272aa960bc2b2e35185c267571d1e191e0f9cd44db3421d8883661faffd271` |
| auditory_alignment_v3/prior33/build_sparrkulee.py | `53e7dcf925cfbd5d782902b2a29d421442dc46047b014d91b47bfa9c09597777` |
| auditory_alignment_v3/prior33/contract.py | `68311699262632445ddcd4e1ab93bfde19ede3eee7c11c8e9d538b956555d053` |
| auditory_alignment_v3/prior33/deps.py | `1b8ed34204cf9ffdb610bdbd915c467b98ef599afade4532889605146101732d` |
| auditory_alignment_v3/prior33/donor_train.py | `259525c53a5e8666c650994973d52295395f666f1f19663b13208604344ebd79` |
| auditory_alignment_v3/prior33/fit_target.py | `3b89e7f7311db38828a14e065dffa62eb7767f4fc26db724867c0957d611f559` |
| auditory_alignment_v3/prior33/gen_fit_target.py | `e177a37da34ee30930b83963f305e348dbb2220b955420c43374dc8f911a6e4e` |
| auditory_alignment_v3/prior33/losses.py | `144c5f0b065c6057c766a76f87f23fc7b2f94c61899d65780f8bfb67f8dfc123` |
| auditory_alignment_v3/prior33/manifest.py | `e1ad10f994eb5ac3bdb0c7e26387a463b34a0a078c5653c5d24de1ae597462f7` |
| auditory_alignment_v3/prior33/model.py | `ae5c2ee5b18d04f55f90e167c12c6093ba43b3d8b52e3870ff1f2c6e0b1add62` |
| auditory_alignment_v3/prior33/refit_rich.py | `31627186f7636b3f8c5304623355a1a706ca23da846023a5392810bd6ba9089e` |
| auditory_alignment_v3/prior33/registry_patch.py | `0bb557c199181c677fc645f2fb386736b74c9d3fc8f6b8c956692dbeefa9eca8` |
| auditory_alignment_v3/prior33/rich.py | `f2738dcbc7b40488055284a3e7a4439d1c9a9b9299a09a49416ff7ffb53794c9` |
| auditory_alignment_v3/prior33/run_bridge.py | `c97fd68b34dabf67ac05388f5a8c09eba63580d5b82600675e39262bafb959ee` |
| auditory_alignment_v3/prior33/run_donor.py | `9faa83c66b21fd797bfbc511aa6f73ba3da1127ec77c2c1ca828d29a8c0bc9d0` |
| auditory_alignment_v3/prior33/run_target.py | `908ee9de48984b2a4c2a1034c1bd95a23b6f146152e3f803c8e5d3eaa9fded8d` |
| auditory_alignment_v3/prior33/run_zeroshot.py | `d024c061270f1ab4cd1bdc2622059a210cc7dbb93efe89724902980c9106815e` |
| auditory_alignment_v3/prior33/sampler.py | `574ed2b7d32a208f051db962913d7892e5c46facdbe7f073ff145690c3986d2b` |
| auditory_alignment_v3/prior33/scan_audio.py | `479fbe3e0c915101ad19cd9c38ed35ebc0e526e7cd22788703e7664d4ee217a7` |
| auditory_alignment_v3/prior33/select.py | `09a43fe6061811b6e47eceb705ce632b5c8b627b7291984e5ccbc51f3a7029b4` |
| auditory_alignment_v3/prior33/target_train.py | `7d301bf3ba7440582399d1d7d1eb0b5fd9f09b553948c9104cf779365f59a2a8` |
| auditory_alignment_v3/prior33/views.py | `15e3326c70288200c69f8f3e35c4ef1a691ce7e90c9e864d4e26f765ac905545` |
| auditory_alignment_v3/prior33/zeroshot.py | `c7e559135b0f920d84bee61ef129dac6c6193a055c0d2321aae0d22089d1cd32` |
| auditory_alignment_v3/sci_r1/stats.py | `8bb141cf6070dabbad48082dd3938a73b0f60bf6c665489e917c255830d8d10e` |
| private/auditory_alignment_v3/aln34/PUBLIC_PRIOR_DESIGN.md | `292130327b8dd3797e386c578e20ab1e801a108b62054197899732a96f25950b` |
| private/auditory_alignment_v3/keeper_prior.sh | `d360065f6aec4f3d2e83e5401cd2d30f705cd1bdbcddf0d73f4e4e20fc993f10` |
| private/auditory_alignment_v3/make_plan_ext_prior33.py | `18cb1c510aad7a2e2b4b942181c8d68df193f75889180141b44647f5f10de587` |
| private/auditory_alignment_v3/probe_prior33.py | `4b70b6d69f54d71137df7fc6f8c1c2beebab390fa86d255da820fb653a3b7c9e` |
| slurm/aln33_prior_cpu.sbatch | `1d1e4207017b206854d8c4164bbd2b6dbc937e5825c22d700054ce11d80c59f2` |
| slurm/aln33_prior_gpu_probe.sbatch | `f960129ff2b2f0bfc063b9948acb57faca41f52db57f652dfa22ae1d427367f4` |
| slurm/aln33_prior_keeper.sbatch | `23d604a66fa4c4efb3f9d29775ab8b7f68eaa709b5d6a1f6423bcd9b61e9836f` |
| slurm/aln33_prior_pool.sbatch | `0d026b8490037a08c43ddc9e9129cac0c2f10cb8e065696c5586611ca807d723` |
| slurm/aln34_prior_finalize_cache.sbatch | `2294a3a939873a7e3250a670d404062823c0ac6dabba812852117ff71f9a0260` |
| tests/auditory_alignment_v3/prior33/fixtures.py | `a12826c4c93a5a23e5a2e4f016323f05450bb04ba8539ec8e9967c18e8aca73b` |
| tests/auditory_alignment_v3/prior33/infra/harness_checks.py | `4227caf02512b05f01a67a7114f9877f3468af3dca693ff0ab990adfe547f546` |
| tests/auditory_alignment_v3/prior33/infra/run_harness.sh | `03db92eb6a9ecc1bb00288813593bd6b8081615936678e2333426e916d857556` |
| tests/auditory_alignment_v3/prior33/test_analysis.py | `e4c4d88f616e493d0ee25bb5f94b5ad1b8a67e83d2653a378049c4b9f8295f2f` |
| tests/auditory_alignment_v3/prior33/test_bridge_zeroshot.py | `52fa4b6f77090fdcbc6a6d95d2eccdddcae462a6b206379e29ebb97764fa4a4d` |
| tests/auditory_alignment_v3/prior33/test_build_public.py | `a9610b53f6ef66876004d2bed470fc52e07bf5cfc3ee88696167cfceee8fef7f` |
| tests/auditory_alignment_v3/prior33/test_build_rich.py | `2e67e6c83ffed0913953c6acc95439f3e17693c163d58f8e267a0b369cd9e9ee` |
| tests/auditory_alignment_v3/prior33/test_build_sparrkulee.py | `b255022530d98aeeef69f78327dbf998e13a4e9a8e78a5c187fb72302638f8a8` |
| tests/auditory_alignment_v3/prior33/test_contract.py | `6f85f8f2094f3192f67cedd6ff50e6f0294b94274775a9caf84b7231bafd0f8a` |
| tests/auditory_alignment_v3/prior33/test_deps_select.py | `0cf0312395ae1840f55b67a8a3b452d3fb066625bc3163f1007eacc545fa818a` |
| tests/auditory_alignment_v3/prior33/test_donor_train.py | `af96c7d25f657d7e062e6b7a304728cd92dc3d987ade596a6482c0c28f1e3b4e` |
| tests/auditory_alignment_v3/prior33/test_fixc.py | `3ee689d8aad6dd66b7f953931908ed80cfab7e8ffaa1a90d62bae16a3a58073d` |
| tests/auditory_alignment_v3/prior33/test_infra_harness.py | `9eff76ad2d288c59457a3e2fbd102ae14e017ee7de070bfac8ca382835a1f426` |
| tests/auditory_alignment_v3/prior33/test_manifest.py | `dadb514e44cd0fc866989a9b3f84ecd5d8cb2c6b9cca01413a2cea225b281830` |
| tests/auditory_alignment_v3/prior33/test_model_losses.py | `02aded87b7d9a1b6e6394ef880c1e84383f7766f383983d691b6dd12347d5ad1` |
| tests/auditory_alignment_v3/prior33/test_plan_prior33.py | `dcb8acb85e6065e40defa8f21f8a5b7bd2e79aa3813b1cd9a4cfb2ea7b406271` |
| tests/auditory_alignment_v3/prior33/test_probe_prior33.py | `0d7889bde6b22686c338c70a96c432d9b1fff1f3cc8e81381aaac34cea02e783` |
| tests/auditory_alignment_v3/prior33/test_refit_rich.py | `265bbde72523b733cbd5c69fbc2ffaec87fcd31b6d4e60c9d1526a909e2c557f` |
| tests/auditory_alignment_v3/prior33/test_scan_audio.py | `3afcbc2baac3a068ed783eee2444edf702e7ab7410e2152f25475c56fc32ca8b` |
| tests/auditory_alignment_v3/prior33/test_target_train.py | `6ac145a297ae769ee906bb7c51fe4af051b7b3b2586d7c0f77a221ed72123b04` |
| tests/auditory_alignment_v3/prior33/test_views_sampler.py | `bed8b0c1426ea00363c2a46c6a7fd6032924a1c7f112f429c375f7aae03ff514` |

## Retained test receipts

| Job | Summary | Log SHA256 |
|---|---|---|
| 1043869 | 138 passed in 213.98s (0:03:33); end 2026-10-17T10:37:55+02:00 rc=0 | `bd157b69eb6ea4ee82eaf639132226be1a7738486a7340966d8b73802baee96a` |
| 1043888 | 5 failed, 181 passed in 407.27s (0:06:47); end 2026-10-17T11:03:56+02:00 rc=1 | `1273d70ea6d873bda06c1241592abad42ed7637ad441715e5fd596201499693f` |
| 1043896 | E         M10 infra harness: 128 passed, 1 failed, 0 not applicable (directory /tmp/pytest-of-yinwang/pytest-0/aln33_infra0/aln33_infra.dzS4CK); 1 failed, 5 passed in 119.87s (0:01:59); end 2026-10-17T11:03:47+02:00 rc=1 | `e5a1b0d276f3b637a5f0ced7cada72db1279b70a8765828840404978b8c1e398` |
| 1043898 | 1 failed, 418 passed in 816.42s (0:13:36); end 2026-10-17T11:22:10+02:00 rc=1 | `29fdf818e729c9ba689fda7ff6f5456b84bb84a3284c413c3d25799e33a92fe6` |
| 1043905 | 1 passed in 6.97s; end 2026-10-17T11:12:26+02:00 rc=0 | `9b517df90b49f7f0e7d65aa534e86271ee42717e32554df4f58e6e83e92fe836` |
| 1043916 | 42 passed in 197.82s (0:03:17); end 2026-10-17T11:26:30+02:00 rc=0 | `c846766522546c3ffef07ce74209c73501f5714e0ecf9527abc7177b1e86dffa` |
