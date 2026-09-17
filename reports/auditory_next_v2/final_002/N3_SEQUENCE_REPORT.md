N3：实现 `PASS`；支持 `SUFFICIENT_FOR_SCREEN`；对照 `FAILED`；科学状态 `NOT_EVALUABLE`。固定来源 `N3_core_001`；执行状态 `CORE_MATRIX_RECORDED`。

主结果使用每个视图的训练OOF选族，禁止事后替换为某固定族。H基线风险与H→HP、HB→HBP、H→Hnoise并列；0.005 bits/trial主增量还须在H+pre以外成立。负增益表示当前有限读出下预测风险上升，可能包含扩维代价和OOF选择不同模型族的容量差异；噪声扩维也受损时尤其不能写成“EEG负信息”或“脑内无信息”。历史稀疏/结构空格只描述，不能补造两类支持。

保存的训练OOF选族（折数，不是人数）：

| mode | population | view | family | n_outer_folds |
| --- | --- | --- | --- | --- |
| L0 | P_bal | H | logistic | 5 |
| L0 | P_bal | HB | logistic | 5 |
| L0 | P_bal | HBP | logistic | 5 |
| L0 | P_bal | HP | logistic | 5 |
| L0 | P_bal | Hnoise | logistic | 5 |
| L0 | P_nat | H | logistic | 5 |
| L0 | P_nat | HB | logistic | 5 |
| L0 | P_nat | HBP | logistic | 5 |
| L0 | P_nat | HP | logistic | 5 |
| L0 | P_nat | Hnoise | logistic | 5 |
| R_SIM | P_bal | H | mlp32 | 5 |
| R_SIM | P_bal | HB | logistic | 5 |
| R_SIM | P_bal | HBP | logistic | 5 |
| R_SIM | P_bal | HP | logistic | 5 |
| R_SIM | P_bal | Hnoise | logistic | 5 |
| R_SIM | P_nat | H | mlp32 | 5 |
| R_SIM | P_nat | HB | logistic | 5 |
| R_SIM | P_nat | HBP | logistic | 5 |
| R_SIM | P_nat | HP | logistic | 5 |
| R_SIM | P_nat | Hnoise | logistic | 5 |

H与增强视图若选中不同模型族，主风险差同时包含选族/容量变化；固定族结果保留作诊断，不能事后替代主比较。

主预设效应（空表表示尚无合格主聚合，不能当作零）：

| analysis_id | readout_family | estimate | ci_lower | ci_upper | n_candidates | unit | descriptive_screen |
| --- | --- | --- | --- | --- | --- | --- | --- |
| selected_H_minus_HP | training_OOF_selected | -0.0506316587586698 | -0.0577564657244072 | -0.0411938981089999 | 60.0 | bits/trial | NEGATIVE_SCREEN |

固定对照执行状态：

| control | population_id | readout_family | calibration | status | estimate | ci_lower | ci_upper | source_run |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| frozen_implementation_contracts | 未提供 | 未提供 | 未提供 | COMPLETE | 未提供 | 未提供 | 未提供 | tests_010 |
| legacy_integrity_and_private_permissions | 未提供 | 未提供 | 未提供 | COMPLETE | 未提供 | 未提供 | 未提供 | postflight_002 |
| complete_prespecified_primary_aggregates | 未提供 | 未提供 | 未提供 | COMPLETE | 未提供 | 未提供 | 未提供 | N3_core_001 |
| prespecified_synthetic_execution_coverage | 未提供 | 未提供 | 未提供 | FAILED | 未提供 | 未提供 | 未提供 | synthetic_001 |
| prespecified_synthetic_direction_and_controls | 未提供 | 未提供 | 未提供 | MISSING | 未提供 | 未提供 | 未提供 | synthetic_001 |
| saved_training_OOF_family_selection | 未提供 | 未提供 | 未提供 | COMPLETE | 未提供 | 未提供 | 未提供 | N3_core_001 |
| complete_required_head_families | 未提供 | 未提供 | 未提供 | COMPLETE | 未提供 | 未提供 | 未提供 | N3_core_001 |
| declared_inner_OOF_calibration | 未提供 | 未提供 | 未提供 | COMPLETE | 未提供 | 未提供 | 未提供 | N3_core_001 |
| selected_HB_minus_HBP | P_nat | training_OOF_selected | temperature | COMPLETE | 0.0001004002383222 | -0.0019035027100663 | 0.0021865901184356 | N3_core_001 |
| selected_H_minus_Hnoise | P_nat | training_OOF_selected | temperature | COMPLETE | -0.0519103031575786 | -0.0589538202026109 | -0.042284318799605 | N3_core_001 |
| fixed_history_strata_description | 未提供 | 未提供 | 未提供 | COMPLETE | 未提供 | 未提供 | 未提供 | N3_core_001 |
| stratum_two_class_support_counts | 未提供 | 未提供 | 未提供 | COMPLETE | 未提供 | 未提供 | 未提供 | metrics_001 |
| fixed_prediction_metrics_and_influence | 未提供 | 未提供 | 未提供 | COMPLETE | 未提供 | 未提供 | 未提供 | metrics_001 |

全部表示、raw/temperature及诊断混合校准在paired_effects与metrics_aggregate保留。区间是固定OOF候选cluster bootstrap，并非重拟合整条pipeline。缺失字段表示源聚合未提供；未由试次或记录数倒推儿童人数。


预设风险与准确率（固定来源，不按大小筛选；未提供AUROC/Brier/区间时保持空值）：

| analysis_id | representation | population_id | model | readout_family | calibration | metric | estimate | ci_lower | ci_upper | n_candidates | n_records |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| N3__ | L0 | P_bal | H | logistic | temperature | ce_bits | 0.95716464373869 | 0.9518673719708886 | 0.96384898706531 | 60.0 | 未提供 |
| N3__ | L0 | P_bal | H | logistic | temperature | J_bits | 0.042835356261309965 | 0.03615101293469003 | 0.048132628029111446 | 60.0 | 未提供 |
| N3__ | L0 | P_bal | H | logistic | temperature | bacc | 0.5868926844577007 | 0.5816213572740079 | 0.5916559740504514 | 60.0 | 未提供 |
| N3__ | L0 | P_bal | HB | logistic | temperature | ce_bits | 0.9594781792065176 | 0.9548098853954118 | 0.9653309645546432 | 60.0 | 未提供 |
| N3__ | L0 | P_bal | HB | logistic | temperature | J_bits | 0.04052182079348243 | 0.03466903544535682 | 0.045190114604588216 | 60.0 | 未提供 |
| N3__ | L0 | P_bal | HB | logistic | temperature | bacc | 0.5906127296802212 | 0.5861591586282564 | 0.594923367810437 | 60.0 | 未提供 |
| N3__ | L0 | P_bal | HBP | logistic | temperature | ce_bits | 0.9596257264577068 | 0.9546902513199162 | 0.9652037624627738 | 60.0 | 未提供 |
| N3__ | L0 | P_bal | HBP | logistic | temperature | J_bits | 0.04037427354229317 | 0.03479623753722616 | 0.04530974868008375 | 60.0 | 未提供 |
| N3__ | L0 | P_bal | HBP | logistic | temperature | bacc | 0.5946131054356076 | 0.5895548264230801 | 0.5994201514100107 | 60.0 | 未提供 |
| N3__ | L0 | P_bal | HP | logistic | temperature | ce_bits | 0.957455431777726 | 0.9521341467673532 | 0.9635602520441472 | 60.0 | 未提供 |
| N3__ | L0 | P_bal | HP | logistic | temperature | J_bits | 0.04254456822227404 | 0.03643974795585281 | 0.047865853232646804 | 60.0 | 未提供 |
| N3__ | L0 | P_bal | HP | logistic | temperature | bacc | 0.5948393998686197 | 0.5899790075852244 | 0.5995988556445804 | 60.0 | 未提供 |
| N3__ | L0 | P_bal | Hnoise | logistic | temperature | ce_bits | 0.9581353341580426 | 0.95263145597115 | 0.9645524149651036 | 60.0 | 未提供 |
| N3__ | L0 | P_bal | Hnoise | logistic | temperature | J_bits | 0.04186466584195736 | 0.03544758503489642 | 0.047368544028850046 | 60.0 | 未提供 |
| N3__ | L0 | P_bal | Hnoise | logistic | temperature | bacc | 0.5898682992236205 | 0.5827163389728793 | 0.5961327765634196 | 60.0 | 未提供 |
| N3__ | L0 | P_nat | H | logistic | temperature | ce_bits | 0.8157495346233741 | 0.8055410528208818 | 0.8238556030168733 | 60.0 | 未提供 |
| N3__ | L0 | P_nat | H | logistic | temperature | bacc | 0.5043256875553204 | 0.5035435325805954 | 0.5051683897578405 | 60.0 | 未提供 |
| N3__ | L0 | P_nat | HB | logistic | temperature | ce_bits | 0.817245398007364 | 0.8069177365847071 | 0.8254506676221782 | 60.0 | 未提供 |
| N3__ | L0 | P_nat | HB | logistic | temperature | bacc | 0.5071887769347464 | 0.505311345213348 | 0.5092968317290846 | 60.0 | 未提供 |
| N3__ | L0 | P_nat | HBP | logistic | temperature | ce_bits | 0.8174024758796351 | 0.8070252467472939 | 0.8258722939148332 | 60.0 | 未提供 |
| N3__ | L0 | P_nat | HBP | logistic | temperature | bacc | 0.5155237359207681 | 0.5118460053047513 | 0.5203236170571621 | 60.0 | 未提供 |
| N3__ | L0 | P_nat | HP | logistic | temperature | ce_bits | 0.8158266391511464 | 0.8054721981347824 | 0.8242202944513302 | 60.0 | 未提供 |
| N3__ | L0 | P_nat | HP | logistic | temperature | bacc | 0.5117411913446529 | 0.5090988964934376 | 0.5143710465917004 | 60.0 | 未提供 |
| N3__ | L0 | P_nat | Hnoise | logistic | temperature | ce_bits | 0.8163627099895986 | 0.8062500819668796 | 0.8246094733081969 | 60.0 | 未提供 |
| N3__ | L0 | P_nat | Hnoise | logistic | temperature | bacc | 0.5071206723857823 | 0.5054101383003804 | 0.5089134583111967 | 60.0 | 未提供 |
| N3__ | R_SIM | P_bal | H | logistic | temperature | ce_bits | 0.95716464373869 | 0.9518673719708886 | 0.96384898706531 | 60.0 | 未提供 |
| N3__ | R_SIM | P_bal | H | logistic | temperature | J_bits | 0.042835356261309965 | 0.03615101293469003 | 0.048132628029111446 | 60.0 | 未提供 |
| N3__ | R_SIM | P_bal | H | logistic | temperature | bacc | 0.5868926844577007 | 0.5816213572740079 | 0.5916559740504514 | 60.0 | 未提供 |
| N3__ | R_SIM | P_bal | HB | logistic | temperature | ce_bits | 0.961136904160612 | 0.9559179493301122 | 0.9674970843233752 | 60.0 | 未提供 |
| N3__ | R_SIM | P_bal | HB | logistic | temperature | J_bits | 0.03886309583938796 | 0.03250291567662478 | 0.044082050669887796 | 60.0 | 未提供 |
| N3__ | R_SIM | P_bal | HB | logistic | temperature | bacc | 0.5925004332998837 | 0.5877834208979628 | 0.5972252567493139 | 60.0 | 未提供 |
| N3__ | R_SIM | P_bal | HBP | logistic | temperature | ce_bits | 0.9616525803629404 | 0.9562448701690088 | 0.9681115335233512 | 60.0 | 未提供 |
| N3__ | R_SIM | P_bal | HBP | logistic | temperature | J_bits | 0.038347419637059565 | 0.03188846647664878 | 0.04375512983099117 | 60.0 | 未提供 |
| N3__ | R_SIM | P_bal | HBP | logistic | temperature | bacc | 0.594954102671769 | 0.5891676064120173 | 0.6002408274742568 | 60.0 | 未提供 |
| N3__ | R_SIM | P_bal | HP | logistic | temperature | ce_bits | 0.9584800967944934 | 0.9528945750327632 | 0.9655649915492436 | 60.0 | 未提供 |
| N3__ | R_SIM | P_bal | HP | logistic | temperature | J_bits | 0.04151990320550658 | 0.03443500845075642 | 0.0471054249672368 | 60.0 | 未提供 |
| N3__ | R_SIM | P_bal | HP | logistic | temperature | bacc | 0.5970903432648306 | 0.5921455029565192 | 0.6020159544105882 | 60.0 | 未提供 |
| N3__ | R_SIM | P_bal | Hnoise | logistic | temperature | ce_bits | 0.9590574492592449 | 0.9538913592891076 | 0.965244683194816 | 60.0 | 未提供 |
| N3__ | R_SIM | P_bal | Hnoise | logistic | temperature | J_bits | 0.040942550740755146 | 0.034755316805183956 | 0.04610864071089238 | 60.0 | 未提供 |
| N3__ | R_SIM | P_bal | Hnoise | logistic | temperature | bacc | 0.590808469393013 | 0.5845065811034045 | 0.5968722476871099 | 60.0 | 未提供 |
| N3__ | R_SIM | P_bal | H | mlp32 | temperature | ce_bits | 0.7634127077121525 | 0.71496520572871 | 0.8322095244977264 | 60.0 | 未提供 |
| N3__ | R_SIM | P_bal | H | mlp32 | temperature | J_bits | 0.23658729228784747 | 0.16779047550227355 | 0.28503479427128997 | 60.0 | 未提供 |
| N3__ | R_SIM | P_bal | H | mlp32 | temperature | bacc | 0.7491621215379928 | 0.7328881299524258 | 0.7617516106535697 | 60.0 | 未提供 |
| N3__ | R_SIM | P_bal | HB | mlp32 | temperature | ce_bits | 0.98071550424745 | 0.9771154003941536 | 0.9852758942277372 | 60.0 | 未提供 |
| N3__ | R_SIM | P_bal | HB | mlp32 | temperature | J_bits | 0.01928449575254998 | 0.014724105772262797 | 0.022884599605846434 | 60.0 | 未提供 |
| N3__ | R_SIM | P_bal | HB | mlp32 | temperature | bacc | 0.5781743815125856 | 0.5717113890937201 | 0.5845016182965214 | 60.0 | 未提供 |
| N3__ | R_SIM | P_bal | HBP | mlp32 | temperature | ce_bits | 0.9889090979802316 | 0.9866216387945071 | 0.9912627443054024 | 60.0 | 未提供 |
| N3__ | R_SIM | P_bal | HBP | mlp32 | temperature | J_bits | 0.011090902019768367 | 0.008737255694597601 | 0.01337836120549285 | 60.0 | 未提供 |
| N3__ | R_SIM | P_bal | HBP | mlp32 | temperature | bacc | 0.5577720817141786 | 0.5505465222519733 | 0.5653407040901939 | 60.0 | 未提供 |
| N3__ | R_SIM | P_bal | HP | mlp32 | temperature | ce_bits | 0.9807829425728888 | 0.9777140591873787 | 0.9843162962180092 | 60.0 | 未提供 |
| N3__ | R_SIM | P_bal | HP | mlp32 | temperature | J_bits | 0.019217057427111217 | 0.0156837037819908 | 0.022285940812621252 | 60.0 | 未提供 |
| N3__ | R_SIM | P_bal | HP | mlp32 | temperature | bacc | 0.5723844671367665 | 0.5637278426898478 | 0.5816728193459823 | 60.0 | 未提供 |
| N3__ | R_SIM | P_bal | Hnoise | mlp32 | temperature | ce_bits | 0.9819504975739588 | 0.9791742573158436 | 0.985606820911018 | 60.0 | 未提供 |
| N3__ | R_SIM | P_bal | Hnoise | mlp32 | temperature | J_bits | 0.018049502426041197 | 0.014393179088981967 | 0.02082574268415638 | 60.0 | 未提供 |
| N3__ | R_SIM | P_bal | Hnoise | mlp32 | temperature | bacc | 0.5723805597903717 | 0.5646191379670719 | 0.5802596557265891 | 60.0 | 未提供 |
| N3__ | R_SIM | P_nat | H | logistic | temperature | ce_bits | 0.8157495346233741 | 0.8055410528208818 | 0.8238556030168733 | 60.0 | 未提供 |
| N3__ | R_SIM | P_nat | H | logistic | temperature | bacc | 0.5043256875553204 | 0.5035435325805954 | 0.5051683897578405 | 60.0 | 未提供 |
| N3__ | R_SIM | P_nat | HB | logistic | temperature | ce_bits | 0.8183336119028356 | 0.8080351298861365 | 0.8264922818166528 | 60.0 | 未提供 |
| N3__ | R_SIM | P_nat | HB | logistic | temperature | bacc | 0.5062037016427512 | 0.504515825835739 | 0.5080331812623596 | 60.0 | 未提供 |
| N3__ | R_SIM | P_nat | HBP | logistic | temperature | ce_bits | 0.8182332116645135 | 0.8082223110500023 | 0.8267001705724492 | 60.0 | 未提供 |
| N3__ | R_SIM | P_nat | HBP | logistic | temperature | bacc | 0.5143077076225571 | 0.5114526612561212 | 0.5171656891130265 | 60.0 | 未提供 |
| N3__ | R_SIM | P_nat | HP | logistic | temperature | ce_bits | 0.8159380310265735 | 0.806076968120524 | 0.8241352544084134 | 60.0 | 未提供 |
| N3__ | R_SIM | P_nat | HP | logistic | temperature | bacc | 0.5107464232627433 | 0.5081261552350594 | 0.5132997869756438 | 60.0 | 未提供 |
| N3__ | R_SIM | P_nat | Hnoise | logistic | temperature | ce_bits | 0.8172166754254823 | 0.8070427389482789 | 0.8252415261734305 | 60.0 | 未提供 |
| N3__ | R_SIM | P_nat | Hnoise | logistic | temperature | bacc | 0.506953962486104 | 0.5051253708857694 | 0.508781347752491 | 60.0 | 未提供 |
| N3__ | R_SIM | P_nat | H | mlp32 | temperature | ce_bits | 0.7653063722679035 | 0.7599001436075518 | 0.7703434872196671 | 60.0 | 未提供 |
| N3__ | R_SIM | P_nat | H | mlp32 | temperature | bacc | 0.5693354908829352 | 0.564810266098376 | 0.5737795187167852 | 60.0 | 未提供 |
| N3__ | R_SIM | P_nat | HB | mlp32 | temperature | ce_bits | 0.8378239151811048 | 0.8308311079399191 | 0.8445236911967503 | 60.0 | 未提供 |
| N3__ | R_SIM | P_nat | HB | mlp32 | temperature | bacc | 0.5578068138122673 | 0.5518515341392685 | 0.5642683784624685 | 60.0 | 未提供 |
| N3__ | R_SIM | P_nat | HBP | mlp32 | temperature | ce_bits | 0.8852904316463069 | 0.8790431525343563 | 0.8914296066435632 | 60.0 | 未提供 |
| N3__ | R_SIM | P_nat | HBP | mlp32 | temperature | bacc | 0.550752165913507 | 0.5441545312887309 | 0.557100526765441 | 60.0 | 未提供 |
| N3__ | R_SIM | P_nat | HP | mlp32 | temperature | ce_bits | 0.8430879627434601 | 0.8350892088379308 | 0.8500970444588017 | 60.0 | 未提供 |
| N3__ | R_SIM | P_nat | HP | mlp32 | temperature | bacc | 0.5561701900484363 | 0.5508409256701596 | 0.5616705419331429 | 60.0 | 未提供 |
| N3__ | R_SIM | P_nat | Hnoise | mlp32 | temperature | ce_bits | 0.8563722787669646 | 0.8505041517016553 | 0.8620271678477276 | 60.0 | 未提供 |
| N3__ | R_SIM | P_nat | Hnoise | mlp32 | temperature | bacc | 0.5543989275499076 | 0.5470829126321971 | 0.561172023869432 | 60.0 | 未提供 |
| N3_selected__ | L0 | P_bal | H | training_OOF_selected | temperature | ce_bits | 0.95716464373869 | 0.9518673719708886 | 0.96384898706531 | 60.0 | 未提供 |
| N3_selected__ | L0 | P_bal | H | training_OOF_selected | temperature | J_bits | 0.042835356261309965 | 0.03615101293469003 | 0.048132628029111446 | 60.0 | 未提供 |
| N3_selected__ | L0 | P_bal | H | training_OOF_selected | temperature | bacc | 0.5868926844577007 | 0.5816213572740079 | 0.5916559740504514 | 60.0 | 未提供 |
| N3_selected__ | L0 | P_bal | HB | training_OOF_selected | temperature | ce_bits | 0.9594781792065176 | 0.9548098853954118 | 0.9653309645546432 | 60.0 | 未提供 |
| N3_selected__ | L0 | P_bal | HB | training_OOF_selected | temperature | J_bits | 0.04052182079348243 | 0.03466903544535682 | 0.045190114604588216 | 60.0 | 未提供 |
| N3_selected__ | L0 | P_bal | HB | training_OOF_selected | temperature | bacc | 0.5906127296802212 | 0.5861591586282564 | 0.594923367810437 | 60.0 | 未提供 |
| N3_selected__ | L0 | P_bal | HBP | training_OOF_selected | temperature | ce_bits | 0.9596257264577068 | 0.9546902513199162 | 0.9652037624627738 | 60.0 | 未提供 |
| N3_selected__ | L0 | P_bal | HBP | training_OOF_selected | temperature | J_bits | 0.04037427354229317 | 0.03479623753722616 | 0.04530974868008375 | 60.0 | 未提供 |
| N3_selected__ | L0 | P_bal | HBP | training_OOF_selected | temperature | bacc | 0.5946131054356076 | 0.5895548264230801 | 0.5994201514100107 | 60.0 | 未提供 |
| N3_selected__ | L0 | P_bal | HP | training_OOF_selected | temperature | ce_bits | 0.957455431777726 | 0.9521341467673532 | 0.9635602520441472 | 60.0 | 未提供 |
| N3_selected__ | L0 | P_bal | HP | training_OOF_selected | temperature | J_bits | 0.04254456822227404 | 0.03643974795585281 | 0.047865853232646804 | 60.0 | 未提供 |
| N3_selected__ | L0 | P_bal | HP | training_OOF_selected | temperature | bacc | 0.5948393998686197 | 0.5899790075852244 | 0.5995988556445804 | 60.0 | 未提供 |
| N3_selected__ | L0 | P_bal | Hnoise | training_OOF_selected | temperature | ce_bits | 0.9581353341580426 | 0.95263145597115 | 0.9645524149651036 | 60.0 | 未提供 |
| N3_selected__ | L0 | P_bal | Hnoise | training_OOF_selected | temperature | J_bits | 0.04186466584195736 | 0.03544758503489642 | 0.047368544028850046 | 60.0 | 未提供 |
| N3_selected__ | L0 | P_bal | Hnoise | training_OOF_selected | temperature | bacc | 0.5898682992236205 | 0.5827163389728793 | 0.5961327765634196 | 60.0 | 未提供 |
| N3_selected__ | L0 | P_nat | H | training_OOF_selected | temperature | ce_bits | 0.8157495346233741 | 0.8055410528208818 | 0.8238556030168733 | 60.0 | 未提供 |
| N3_selected__ | L0 | P_nat | H | training_OOF_selected | temperature | bacc | 0.5043256875553204 | 0.5035435325805954 | 0.5051683897578405 | 60.0 | 未提供 |
| N3_selected__ | L0 | P_nat | HB | training_OOF_selected | temperature | ce_bits | 0.817245398007364 | 0.8069177365847071 | 0.8254506676221782 | 60.0 | 未提供 |
| N3_selected__ | L0 | P_nat | HB | training_OOF_selected | temperature | bacc | 0.5071887769347464 | 0.505311345213348 | 0.5092968317290846 | 60.0 | 未提供 |
| N3_selected__ | L0 | P_nat | HBP | training_OOF_selected | temperature | ce_bits | 0.8174024758796351 | 0.8070252467472939 | 0.8258722939148332 | 60.0 | 未提供 |
| N3_selected__ | L0 | P_nat | HBP | training_OOF_selected | temperature | bacc | 0.5155237359207681 | 0.5118460053047513 | 0.5203236170571621 | 60.0 | 未提供 |
| N3_selected__ | L0 | P_nat | HP | training_OOF_selected | temperature | ce_bits | 0.8158266391511464 | 0.8054721981347824 | 0.8242202944513302 | 60.0 | 未提供 |
| N3_selected__ | L0 | P_nat | HP | training_OOF_selected | temperature | bacc | 0.5117411913446529 | 0.5090988964934376 | 0.5143710465917004 | 60.0 | 未提供 |
| N3_selected__ | L0 | P_nat | Hnoise | training_OOF_selected | temperature | ce_bits | 0.8163627099895986 | 0.8062500819668796 | 0.8246094733081969 | 60.0 | 未提供 |
| N3_selected__ | L0 | P_nat | Hnoise | training_OOF_selected | temperature | bacc | 0.5071206723857823 | 0.5054101383003804 | 0.5089134583111967 | 60.0 | 未提供 |
| N3_selected__ | R_SIM | P_bal | H | training_OOF_selected | temperature | ce_bits | 0.7634127077121525 | 0.71496520572871 | 0.8322095244977264 | 60.0 | 未提供 |
| N3_selected__ | R_SIM | P_bal | H | training_OOF_selected | temperature | J_bits | 0.23658729228784747 | 0.16779047550227355 | 0.28503479427128997 | 60.0 | 未提供 |
| N3_selected__ | R_SIM | P_bal | H | training_OOF_selected | temperature | bacc | 0.7491621215379928 | 0.7328881299524258 | 0.7617516106535697 | 60.0 | 未提供 |
| N3_selected__ | R_SIM | P_bal | HB | training_OOF_selected | temperature | ce_bits | 0.961136904160612 | 0.9559179493301122 | 0.9674970843233752 | 60.0 | 未提供 |
| N3_selected__ | R_SIM | P_bal | HB | training_OOF_selected | temperature | J_bits | 0.03886309583938796 | 0.03250291567662478 | 0.044082050669887796 | 60.0 | 未提供 |
| N3_selected__ | R_SIM | P_bal | HB | training_OOF_selected | temperature | bacc | 0.5925004332998837 | 0.5877834208979628 | 0.5972252567493139 | 60.0 | 未提供 |
| N3_selected__ | R_SIM | P_bal | HBP | training_OOF_selected | temperature | ce_bits | 0.9616525803629404 | 0.9562448701690088 | 0.9681115335233512 | 60.0 | 未提供 |
| N3_selected__ | R_SIM | P_bal | HBP | training_OOF_selected | temperature | J_bits | 0.038347419637059565 | 0.03188846647664878 | 0.04375512983099117 | 60.0 | 未提供 |
| N3_selected__ | R_SIM | P_bal | HBP | training_OOF_selected | temperature | bacc | 0.594954102671769 | 0.5891676064120173 | 0.6002408274742568 | 60.0 | 未提供 |
| N3_selected__ | R_SIM | P_bal | HP | training_OOF_selected | temperature | ce_bits | 0.9584800967944934 | 0.9528945750327632 | 0.9655649915492436 | 60.0 | 未提供 |
| N3_selected__ | R_SIM | P_bal | HP | training_OOF_selected | temperature | J_bits | 0.04151990320550658 | 0.03443500845075642 | 0.0471054249672368 | 60.0 | 未提供 |
| N3_selected__ | R_SIM | P_bal | HP | training_OOF_selected | temperature | bacc | 0.5970903432648306 | 0.5921455029565192 | 0.6020159544105882 | 60.0 | 未提供 |
| N3_selected__ | R_SIM | P_bal | Hnoise | training_OOF_selected | temperature | ce_bits | 0.9590574492592449 | 0.9538913592891076 | 0.965244683194816 | 60.0 | 未提供 |
| N3_selected__ | R_SIM | P_bal | Hnoise | training_OOF_selected | temperature | J_bits | 0.040942550740755146 | 0.034755316805183956 | 0.04610864071089238 | 60.0 | 未提供 |
| N3_selected__ | R_SIM | P_bal | Hnoise | training_OOF_selected | temperature | bacc | 0.590808469393013 | 0.5845065811034045 | 0.5968722476871099 | 60.0 | 未提供 |
| N3_selected__ | R_SIM | P_nat | H | training_OOF_selected | temperature | ce_bits | 0.7653063722679035 | 0.7599001436075518 | 0.7703434872196671 | 60.0 | 未提供 |
| N3_selected__ | R_SIM | P_nat | H | training_OOF_selected | temperature | bacc | 0.5693354908829352 | 0.564810266098376 | 0.5737795187167852 | 60.0 | 未提供 |
| N3_selected__ | R_SIM | P_nat | HB | training_OOF_selected | temperature | ce_bits | 0.8183336119028356 | 0.8080351298861365 | 0.8264922818166528 | 60.0 | 未提供 |
| N3_selected__ | R_SIM | P_nat | HB | training_OOF_selected | temperature | bacc | 0.5062037016427512 | 0.504515825835739 | 0.5080331812623596 | 60.0 | 未提供 |
| N3_selected__ | R_SIM | P_nat | HBP | training_OOF_selected | temperature | ce_bits | 0.8182332116645135 | 0.8082223110500023 | 0.8267001705724492 | 60.0 | 未提供 |
| N3_selected__ | R_SIM | P_nat | HBP | training_OOF_selected | temperature | bacc | 0.5143077076225571 | 0.5114526612561212 | 0.5171656891130265 | 60.0 | 未提供 |
| N3_selected__ | R_SIM | P_nat | HP | training_OOF_selected | temperature | ce_bits | 0.8159380310265735 | 0.806076968120524 | 0.8241352544084134 | 60.0 | 未提供 |
| N3_selected__ | R_SIM | P_nat | HP | training_OOF_selected | temperature | bacc | 0.5107464232627433 | 0.5081261552350594 | 0.5132997869756438 | 60.0 | 未提供 |
| N3_selected__ | R_SIM | P_nat | Hnoise | training_OOF_selected | temperature | ce_bits | 0.8172166754254823 | 0.8070427389482789 | 0.8252415261734305 | 60.0 | 未提供 |
| N3_selected__ | R_SIM | P_nat | Hnoise | training_OOF_selected | temperature | bacc | 0.506953962486104 | 0.5051253708857694 | 0.508781347752491 | 60.0 | 未提供 |