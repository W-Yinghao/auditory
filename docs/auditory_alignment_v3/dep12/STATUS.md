# DEP12 status (updated by the coordinator)

| Unit (package) | Status | Notes |
|---|---|---|
| Intake, reference checks, plan | completed | NumPy 18/18, Torch 10/10; intake: remote = 063bef5 |
| SOURCE_UPDATE.md | completed (v1) | `results/auditory_alignment_v3/dep12/SOURCE_UPDATE.md` |
| EXTERNAL_COMPARISON.md | v0 (existing results); F_EXTERNAL pending on common query | |
| encoders.py / INTERFACES.md (Agent S) | completed v1 | B0, ALN4.1 arms, ALN3.4 CB / REVE fold models, REVE0, MindMix branch servable; montages sparrkulee/dtu, fau, federici, private_bdf, mff |
| E0 (4 × 2,500 updates) | **completed 04:03; selected LoRA** | step-2500 dev mean r: cs_pair full −0.0138 / LoRA +0.0085; info_nce full −0.0110 / LoRA −0.0123 → mode scores full −0.0124, LoRA −0.0019 (B0 ≈ +0.0097). All four are at or below B0 on this dev probe (heavy-shrinkage regime). Smoke 1058811 V100: 0.16–0.20 s/update, peak 6.75 GB |
| Main 9 + diagnostic 2 | **running**: 4/11 done at 05:21 (LoRA; 2 jobs on V100) | exactly 115,000 updates; resume.pt every 100 updates |
| Public definitions (Agent M) | completed, frozen | DTU / FAU defs, ACF check (2 s minimum shift kept), 128-anchor panels (4 × 32 at 0.5 s), 199 block-shift nulls, 20 s queries = 4 cs segments (DTU 2,802 / FAU 4,623; 152 anchors; 121 legal shifts) |
| Public features | running | B0 on CPU (job 1058613, 48 CPUs); GPU lanes c3_s35dMfeat / c3_s35dMpert registered 01:25; technical_error until 01:52 (coordinator naming convention: lane 's35_*', submit 'slurm/aln35_*'), fixed via v2 wrappers (swap receipt `swap_dep12_pub_v2_*`); now ready |
| Federici | deferred | 100 Hz cannot hold the window with integer samples (M decision) |
| Private (Agent P) | B0 complete (CPU); lanes c3_s35dPfeat / c3_s35dPmff registered 02:25; smokes on V100 (1058792/3) | B0: G = −0.0058 bits/trial [−0.0072, −0.0045], negative in 61/64 children ≈ expected out-of-sample cost of a 64-slope readout with no signal (≈ −0.0061); so G must be read against ≈ −0.006, not 0. child60 (audited alternative sequence) is the only clearly positive child. δ profile at chance (n128 excess +1.5e-5 nats, 32/64 positive). EEG-part AUC 0.505; real − strict twin +0.0016 [−0.0001, 0.0032]. Cross-stim recovered from R2 (all unresolved). MFF (57 lane-children) added as second private cohort (P21) |
| /projects free space | 955 GiB at 01:45 (97 %); Tier-1 deletion list (96.8 GiB) frozen, executes only below 300 GiB | Agent M stores squared-distance matrices instead of U |
| V100 routing | in progress | The coordinator routes a lane to V100 only if it is in `aln35/v100_20261019/compatibility.json` (V100 pass receipt, peak < 16 GB). Added: s35_dep12_pub_features (V100-16GB smoke 1058747, peak 371 MB). Added 02:55: s35_dep12_private_features (V100-16GB smoke 1058792, peak 682 MB), s35_dep12_private_mff (V100-32GB smoke 1058793, peak 5.4 GB). dMfeat worker now running on V100 (node42). Added 03:37: s35_dep12_src_e0 and s35_dep12_src_prod (V100-32GB smoke 1058811, peak 6.75 GB). Receipts: `v100_smokes_dep12_20261023.json`, `v100_reroute_dep12_20261023b.json`, `v100_policy_add_*` |
| CPU host | `aud_dep12cpu` job 1058917 (runfill, 16 CPU / 64 GB, 2 d) | evidence allocation 1047358 hit its 4-day limit 04:13; normal QoS at 28 (>27). Coordinator 1051045 expires ~10-24 09:40 → resubmit with afterany dependency when normal ≤ 27 |
| Public CPU stage | running on 1058917 (04:36) | measure → attention → report for completed feature units (B0 + reused) |
