N1：实现 `PASS`；支持 `SUFFICIENT_FOR_SCREEN`；对照 `FAILED`；科学状态 `NOT_EVALUABLE`。固定来源 `N1_core_001`；执行状态 `CORE_MATRIX_RECORDED`。

主量为 R_SIM/P_nat/MLP32/temperature 的 HP−HPB，背景增益需达到0.005 bits/trial且区间下界>0；还需 HB−HPB>0并超过PP和噪声扩维对照。raw、自然先验与平衡先验分列。donor冻结时不使用当前标签；固定头替换及匹配训练donor对照保留同支持参考，其变化可能反映输入分布失配，不能直接解释为背景的因果必要性。

主预设效应（空表表示尚无合格主聚合，不能当作零）：

| analysis_id | readout_family | estimate | ci_lower | ci_upper | n_candidates | unit | descriptive_screen |
| --- | --- | --- | --- | --- | --- | --- | --- |
| HP_minus_HPB | mlp32 | -0.0249566826589322 | -0.027988789208733 | -0.0221691542158125 | 59.0 | bits/trial | NEGATIVE_SCREEN |

固定对照执行状态：

| control | population_id | readout_family | calibration | status | estimate | ci_lower | ci_upper | source_run |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| frozen_implementation_contracts | 未提供 | 未提供 | 未提供 | COMPLETE | 未提供 | 未提供 | 未提供 | tests_010 |
| legacy_integrity_and_private_permissions | 未提供 | 未提供 | 未提供 | COMPLETE | 未提供 | 未提供 | 未提供 | postflight_002 |
| complete_prespecified_primary_aggregates | 未提供 | 未提供 | 未提供 | COMPLETE | 未提供 | 未提供 | 未提供 | N1_core_001 |
| prespecified_synthetic_execution_coverage | 未提供 | 未提供 | 未提供 | FAILED | 未提供 | 未提供 | 未提供 | synthetic_001 |
| prespecified_synthetic_direction_and_controls | 未提供 | 未提供 | 未提供 | MISSING | 未提供 | 未提供 | 未提供 | synthetic_001 |
| complete_required_head_families | 未提供 | 未提供 | 未提供 | COMPLETE | 未提供 | 未提供 | 未提供 | N1_core_001 |
| declared_inner_OOF_calibration | 未提供 | 未提供 | 未提供 | COMPLETE | 未提供 | 未提供 | 未提供 | N1_core_001 |
| two_fixed_head_donor_assignments | 未提供 | 未提供 | 未提供 | COMPLETE | 未提供 | 未提供 | 未提供 | N1_core_001 |
| matched_donor_training_same_support_reference | 未提供 | 未提供 | 未提供 | COMPLETE | 未提供 | 未提供 | 未提供 | N1_core_001 |
| fixed_head_donor:same_child_B-actual_B | 未提供 | 未提供 | 未提供 | COMPLETE | 0.0030460265981769 | 0.0003866922786802 | 0.0056752592411666 | N1_core_001 |
| fixed_head_donor:training_child_B-actual_B | 未提供 | 未提供 | 未提供 | COMPLETE | -0.002205871766235 | -0.0060475978099179 | 0.0012624272082767 | N1_core_001 |
| matched_training_donor_vs_same_support_reference:HPB_donor_support_reference-HPB_training_child_donor | 未提供 | 未提供 | 未提供 | COMPLETE | -0.0062084418450781 | -0.0126918063498331 | -0.0012426184504645 | N1_core_001 |
| HPP_minus_HPB | P_nat | mlp32 | temperature | COMPLETE | -0.0119874380903146 | -0.0145278597463982 | -0.0094226354263356 | N1_core_001 |
| HPBnoise_minus_HPB | P_nat | mlp32 | temperature | COMPLETE | 0.004886121246093 | -0.0011759657678446 | 0.0099085427205381 | N1_core_001 |
| HB_minus_HPB | P_nat | mlp32 | temperature | COMPLETE | -0.0241528137667634 | -0.027591464758276 | -0.020944091986163 | N1_core_001 |
| fixed_prediction_metrics_and_influence | 未提供 | 未提供 | 未提供 | COMPLETE | 未提供 | 未提供 | 未提供 | metrics_001 |

全部表示、raw/temperature及诊断混合校准在paired_effects与metrics_aggregate保留。区间是固定OOF候选cluster bootstrap，并非重拟合整条pipeline。缺失字段表示源聚合未提供；未由试次或记录数倒推儿童人数。


预设风险与准确率（固定来源，不按大小筛选；未提供AUROC/Brier/区间时保持空值）：

| analysis_id | representation | population_id | model | readout_family | calibration | metric | estimate | ci_lower | ci_upper | n_candidates | n_records |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| N1__ | L0 | P_bal | H | logistic | temperature | ce_bits | 0.6816646689589353 | 0.615715531370024 | 0.7817816728054325 | 59.0 | 未提供 |
| N1__ | L0 | P_bal | H | logistic | temperature | J_bits | 0.3183353310410647 | 0.21821832719456746 | 0.384284468629976 | 59.0 | 未提供 |
| N1__ | L0 | P_bal | H | logistic | temperature | bacc | 0.7592954109045562 | 0.7434866670636346 | 0.7706574442969031 | 59.0 | 未提供 |
| N1__ | L0 | P_bal | HB | logistic | temperature | ce_bits | 0.6826324291503479 | 0.6180985772472891 | 0.7802615586750894 | 59.0 | 未提供 |
| N1__ | L0 | P_bal | HB | logistic | temperature | J_bits | 0.31736757084965206 | 0.2197384413249106 | 0.3819014227527109 | 59.0 | 未提供 |
| N1__ | L0 | P_bal | HB | logistic | temperature | bacc | 0.7536227118251613 | 0.7386906913506722 | 0.7644238523618141 | 59.0 | 未提供 |
| N1__ | L0 | P_bal | HP | logistic | temperature | ce_bits | 0.6818467766733127 | 0.6172347608684853 | 0.7792942871878095 | 59.0 | 未提供 |
| N1__ | L0 | P_bal | HP | logistic | temperature | J_bits | 0.3181532233266873 | 0.22070571281219054 | 0.3827652391315147 | 59.0 | 未提供 |
| N1__ | L0 | P_bal | HP | logistic | temperature | bacc | 0.7539367187264326 | 0.7386225043861374 | 0.7649590694026864 | 59.0 | 未提供 |
| N1__ | L0 | P_bal | HPB | logistic | temperature | ce_bits | 0.6828137520849988 | 0.6195908217070192 | 0.7776990236010952 | 59.0 | 未提供 |
| N1__ | L0 | P_bal | HPB | logistic | temperature | J_bits | 0.31718624791500116 | 0.22230097639890478 | 0.3804091782929808 | 59.0 | 未提供 |
| N1__ | L0 | P_bal | HPB | logistic | temperature | bacc | 0.7504839104327774 | 0.7348652620740461 | 0.7616986688071774 | 59.0 | 未提供 |
| N1__ | L0 | P_bal | HPBnoise | logistic | temperature | ce_bits | 0.6823815984413184 | 0.6184635332367358 | 0.778223153511472 | 59.0 | 未提供 |
| N1__ | L0 | P_bal | HPBnoise | logistic | temperature | J_bits | 0.3176184015586816 | 0.22177684648852802 | 0.38153646676326425 | 59.0 | 未提供 |
| N1__ | L0 | P_bal | HPBnoise | logistic | temperature | bacc | 0.7507259102444152 | 0.7347313149926431 | 0.7621040049827441 | 59.0 | 未提供 |
| N1__ | L0 | P_bal | HPP | logistic | temperature | ce_bits | 0.6818783906529151 | 0.6173357593894979 | 0.7791852916556798 | 59.0 | 未提供 |
| N1__ | L0 | P_bal | HPP | logistic | temperature | J_bits | 0.3181216093470849 | 0.22081470834432015 | 0.3826642406105021 | 59.0 | 未提供 |
| N1__ | L0 | P_bal | HPP | logistic | temperature | bacc | 0.7540199091084676 | 0.7387301074727143 | 0.76499811999026 | 59.0 | 未提供 |
| N1__ | L0 | P_nat | H | logistic | temperature | ce_bits | 0.5168787240299256 | 0.4854082842310701 | 0.562709126199008 | 59.0 | 未提供 |
| N1__ | L0 | P_nat | H | logistic | temperature | bacc | 0.5960072439282826 | 0.5890294646339228 | 0.6015014259714037 | 59.0 | 未提供 |
| N1__ | L0 | P_nat | HB | logistic | temperature | ce_bits | 0.5176488654073991 | 0.4864012622352835 | 0.5630974596246463 | 59.0 | 未提供 |
| N1__ | L0 | P_nat | HB | logistic | temperature | bacc | 0.5958278434121863 | 0.5886761344016732 | 0.6012613215053115 | 59.0 | 未提供 |
| N1__ | L0 | P_nat | HP | logistic | temperature | ce_bits | 0.5174078787545053 | 0.4861857209069933 | 0.5630623408715435 | 59.0 | 未提供 |
| N1__ | L0 | P_nat | HP | logistic | temperature | bacc | 0.5979792663040185 | 0.5905042533092109 | 0.6037612649604212 | 59.0 | 未提供 |
| N1__ | L0 | P_nat | HPB | logistic | temperature | ce_bits | 0.5181274930550498 | 0.4871033348511925 | 0.5633811225090242 | 59.0 | 未提供 |
| N1__ | L0 | P_nat | HPB | logistic | temperature | bacc | 0.599367281157731 | 0.5920513104724775 | 0.6050064423495756 | 59.0 | 未提供 |
| N1__ | L0 | P_nat | HPBnoise | logistic | temperature | ce_bits | 0.5176662977419385 | 0.4867514928816455 | 0.562998157066107 | 59.0 | 未提供 |
| N1__ | L0 | P_nat | HPBnoise | logistic | temperature | bacc | 0.5992065159831401 | 0.5917133733371861 | 0.6049707320720076 | 59.0 | 未提供 |
| N1__ | L0 | P_nat | HPP | logistic | temperature | ce_bits | 0.5174557076517331 | 0.4862879444383458 | 0.5631087844167438 | 59.0 | 未提供 |
| N1__ | L0 | P_nat | HPP | logistic | temperature | bacc | 0.5979612809956782 | 0.5905576335636846 | 0.6037803204728562 | 59.0 | 未提供 |
| N1__ | R_SIM | P_bal | H | logistic | temperature | ce_bits | 0.6816646689589353 | 0.615715531370024 | 0.7817816728054325 | 59.0 | 未提供 |
| N1__ | R_SIM | P_bal | H | logistic | temperature | J_bits | 0.3183353310410647 | 0.21821832719456746 | 0.384284468629976 | 59.0 | 未提供 |
| N1__ | R_SIM | P_bal | H | logistic | temperature | bacc | 0.7592954109045562 | 0.7434866670636346 | 0.7706574442969031 | 59.0 | 未提供 |
| N1__ | R_SIM | P_bal | HB | logistic | temperature | ce_bits | 0.6838943264566825 | 0.6188922967096954 | 0.782448542549118 | 59.0 | 未提供 |
| N1__ | R_SIM | P_bal | HB | logistic | temperature | J_bits | 0.31610567354331753 | 0.217551457450882 | 0.38110770329030463 | 59.0 | 未提供 |
| N1__ | R_SIM | P_bal | HB | logistic | temperature | bacc | 0.7492669970902255 | 0.7342271551742174 | 0.7600482167303835 | 59.0 | 未提供 |
| N1__ | R_SIM | P_bal | HP | logistic | temperature | ce_bits | 0.681940301899874 | 0.6169501731939675 | 0.7803372185551298 | 59.0 | 未提供 |
| N1__ | R_SIM | P_bal | HP | logistic | temperature | J_bits | 0.318059698100126 | 0.21966278144487017 | 0.3830498268060325 | 59.0 | 未提供 |
| N1__ | R_SIM | P_bal | HP | logistic | temperature | bacc | 0.7517139649300288 | 0.7360797866731087 | 0.7628817333234947 | 59.0 | 未提供 |
| N1__ | R_SIM | P_bal | HPB | logistic | temperature | ce_bits | 0.6839717661564899 | 0.6199528758770108 | 0.7805596856099494 | 59.0 | 未提供 |
| N1__ | R_SIM | P_bal | HPB | logistic | temperature | J_bits | 0.3160282338435101 | 0.21944031439005063 | 0.38004712412298924 | 59.0 | 未提供 |
| N1__ | R_SIM | P_bal | HPB | logistic | temperature | bacc | 0.7485199765509246 | 0.7327690845178161 | 0.7598272109232329 | 59.0 | 未提供 |
| N1__ | R_SIM | P_bal | HPBnoise | logistic | temperature | ce_bits | 0.6826365450728091 | 0.6189001769347153 | 0.7791266392981626 | 59.0 | 未提供 |
| N1__ | R_SIM | P_bal | HPBnoise | logistic | temperature | J_bits | 0.31736345492719087 | 0.22087336070183738 | 0.38109982306528467 | 59.0 | 未提供 |
| N1__ | R_SIM | P_bal | HPBnoise | logistic | temperature | bacc | 0.7505952962238893 | 0.7352374728763631 | 0.7616502650640188 | 59.0 | 未提供 |
| N1__ | R_SIM | P_bal | HPP | logistic | temperature | ce_bits | 0.6822176460061098 | 0.6176565113042913 | 0.7800234269409457 | 59.0 | 未提供 |
| N1__ | R_SIM | P_bal | HPP | logistic | temperature | J_bits | 0.3177823539938902 | 0.21997657305905427 | 0.38234348869570867 | 59.0 | 未提供 |
| N1__ | R_SIM | P_bal | HPP | logistic | temperature | bacc | 0.7514326457864384 | 0.7362083603083768 | 0.7625533659728755 | 59.0 | 未提供 |
| N1__ | R_SIM | P_bal | H | mlp32 | temperature | ce_bits | 0.5974988715589957 | 0.5561056430841236 | 0.6629475536474032 | 59.0 | 未提供 |
| N1__ | R_SIM | P_bal | H | mlp32 | temperature | J_bits | 0.4025011284410043 | 0.3370524463525968 | 0.4438943569158764 | 59.0 | 未提供 |
| N1__ | R_SIM | P_bal | H | mlp32 | temperature | bacc | 0.7900614651620187 | 0.7722640424372186 | 0.8019870113180696 | 59.0 | 未提供 |
| N1__ | R_SIM | P_bal | HB | mlp32 | temperature | ce_bits | 0.6638285900472644 | 0.6360805024991172 | 0.7056853788327865 | 59.0 | 未提供 |
| N1__ | R_SIM | P_bal | HB | mlp32 | temperature | J_bits | 0.33617140995273564 | 0.2943146211672135 | 0.3639194975008828 | 59.0 | 未提供 |
| N1__ | R_SIM | P_bal | HB | mlp32 | temperature | bacc | 0.73944443783777 | 0.7250648681624771 | 0.7501782866638865 | 59.0 | 未提供 |
| N1__ | R_SIM | P_bal | HP | mlp32 | temperature | ce_bits | 0.664780542257348 | 0.6387443609379745 | 0.7029948147154567 | 59.0 | 未提供 |
| N1__ | R_SIM | P_bal | HP | mlp32 | temperature | J_bits | 0.33521945774265205 | 0.29700518528454334 | 0.3612556390620255 | 59.0 | 未提供 |
| N1__ | R_SIM | P_bal | HP | mlp32 | temperature | bacc | 0.7352023349879699 | 0.7205914165095121 | 0.7468668416045642 | 59.0 | 未提供 |
| N1__ | R_SIM | P_bal | HPB | mlp32 | temperature | ce_bits | 0.7108820030851594 | 0.688431820235743 | 0.7433882114609142 | 59.0 | 未提供 |
| N1__ | R_SIM | P_bal | HPB | mlp32 | temperature | J_bits | 0.28911799691484064 | 0.25661178853908584 | 0.311568179764257 | 59.0 | 未提供 |
| N1__ | R_SIM | P_bal | HPB | mlp32 | temperature | bacc | 0.7096835605908637 | 0.6955044817074735 | 0.7206465616399909 | 59.0 | 未提供 |
| N1__ | R_SIM | P_bal | HPBnoise | mlp32 | temperature | ce_bits | 0.7198670763246329 | 0.698437420740833 | 0.7497389193216332 | 59.0 | 未提供 |
| N1__ | R_SIM | P_bal | HPBnoise | mlp32 | temperature | J_bits | 0.28013292367536713 | 0.25026108067836683 | 0.30156257925916696 | 59.0 | 未提供 |
| N1__ | R_SIM | P_bal | HPBnoise | mlp32 | temperature | bacc | 0.7062928031162161 | 0.6941703131247182 | 0.716000229403836 | 59.0 | 未提供 |
| N1__ | R_SIM | P_bal | HPP | mlp32 | temperature | ce_bits | 0.6818471532294217 | 0.6565681235639379 | 0.7189300098702359 | 59.0 | 未提供 |
| N1__ | R_SIM | P_bal | HPP | mlp32 | temperature | J_bits | 0.3181528467705783 | 0.2810699901297641 | 0.3434318764360621 | 59.0 | 未提供 |
| N1__ | R_SIM | P_bal | HPP | mlp32 | temperature | bacc | 0.7296584523934543 | 0.7154091049801344 | 0.7397529809700117 | 59.0 | 未提供 |
| N1__ | R_SIM | P_nat | H | logistic | temperature | ce_bits | 0.5168787240299256 | 0.4854082842310701 | 0.562709126199008 | 59.0 | 未提供 |
| N1__ | R_SIM | P_nat | H | logistic | temperature | bacc | 0.5960072439282826 | 0.5890294646339228 | 0.6015014259714037 | 59.0 | 未提供 |
| N1__ | R_SIM | P_nat | HB | logistic | temperature | ce_bits | 0.5184389061795361 | 0.4867874514598857 | 0.5642595660956659 | 59.0 | 未提供 |
| N1__ | R_SIM | P_nat | HB | logistic | temperature | bacc | 0.596286157601168 | 0.5891405175353669 | 0.6019543578888509 | 59.0 | 未提供 |
| N1__ | R_SIM | P_nat | HP | logistic | temperature | ce_bits | 0.5172168957393931 | 0.4852876893627936 | 0.563770614909887 | 59.0 | 未提供 |
| N1__ | R_SIM | P_nat | HP | logistic | temperature | bacc | 0.5983195763327688 | 0.5909072998115513 | 0.6041482638148895 | 59.0 | 未提供 |
| N1__ | R_SIM | P_nat | HPB | logistic | temperature | ce_bits | 0.5185906053364068 | 0.4864576725943297 | 0.5653501199666141 | 59.0 | 未提供 |
| N1__ | R_SIM | P_nat | HPB | logistic | temperature | bacc | 0.5994118799771317 | 0.5917385534608478 | 0.6052218440032825 | 59.0 | 未提供 |
| N1__ | R_SIM | P_nat | HPBnoise | logistic | temperature | ce_bits | 0.5174763719742054 | 0.4856750855104371 | 0.5636027870666132 | 59.0 | 未提供 |
| N1__ | R_SIM | P_nat | HPBnoise | logistic | temperature | bacc | 0.6007880074097856 | 0.5934666018044239 | 0.6066497614642072 | 59.0 | 未提供 |
| N1__ | R_SIM | P_nat | HPP | logistic | temperature | ce_bits | 0.5175120013175425 | 0.4856227550208974 | 0.5641929508055683 | 59.0 | 未提供 |
| N1__ | R_SIM | P_nat | HPP | logistic | temperature | bacc | 0.5993044848991945 | 0.5916577212443046 | 0.6051434802300214 | 59.0 | 未提供 |
| N1__ | R_SIM | P_nat | H | mlp32 | temperature | ce_bits | 0.464342194257184 | 0.4448913809749162 | 0.4926395961536024 | 59.0 | 未提供 |
| N1__ | R_SIM | P_nat | H | mlp32 | temperature | bacc | 0.6254978598844075 | 0.6179160828660061 | 0.6314068324335649 | 59.0 | 未提供 |
| N1__ | R_SIM | P_nat | HB | mlp32 | temperature | ce_bits | 0.4941164259421147 | 0.47474592938935 | 0.5221583633553374 | 59.0 | 未提供 |
| N1__ | R_SIM | P_nat | HB | mlp32 | temperature | bacc | 0.6181902087031488 | 0.6088903084311078 | 0.6249977811567861 | 59.0 | 未提供 |
| N1__ | R_SIM | P_nat | HP | mlp32 | temperature | ce_bits | 0.4933125570499458 | 0.4744217452802981 | 0.5207403106941679 | 59.0 | 未提供 |
| N1__ | R_SIM | P_nat | HP | mlp32 | temperature | bacc | 0.6213819945087977 | 0.6136848802837344 | 0.6274990522775377 | 59.0 | 未提供 |
| N1__ | R_SIM | P_nat | HPB | mlp32 | temperature | ce_bits | 0.5182692397088782 | 0.4981590567949723 | 0.5467690675230501 | 59.0 | 未提供 |
| N1__ | R_SIM | P_nat | HPB | mlp32 | temperature | bacc | 0.641582087356711 | 0.632124159111239 | 0.6495148487484562 | 59.0 | 未提供 |
| N1__ | R_SIM | P_nat | HPB_donor_support_reference | mlp32 | temperature | ce_bits | 0.518998061772856 | 0.4987262209992136 | 0.5476550852227112 | 59.0 | 未提供 |
| N1__ | R_SIM | P_nat | HPB_donor_support_reference | mlp32 | temperature | bacc | 0.64121063679215 | 0.6309519020374244 | 0.6494596535460724 | 59.0 | 未提供 |
| N1__ | R_SIM | P_nat | HPB_training_child_donor | mlp32 | temperature | ce_bits | 0.5252065036179342 | 0.5017493498597769 | 0.5588317085158632 | 59.0 | 未提供 |
| N1__ | R_SIM | P_nat | HPB_training_child_donor | mlp32 | temperature | bacc | 0.64050285264189 | 0.6307184538949918 | 0.6481891771991674 | 59.0 | 未提供 |
| N1__ | R_SIM | P_nat | HPBnoise | mlp32 | temperature | ce_bits | 0.5231553609549712 | 0.5070024460860415 | 0.5458775340618757 | 59.0 | 未提供 |
| N1__ | R_SIM | P_nat | HPBnoise | mlp32 | temperature | bacc | 0.6367551402507866 | 0.6279361941790867 | 0.6433720963458293 | 59.0 | 未提供 |
| N1__ | R_SIM | P_nat | HPP | mlp32 | temperature | ce_bits | 0.5062818016185635 | 0.4873076805111612 | 0.5330814275168769 | 59.0 | 未提供 |
| N1__ | R_SIM | P_nat | HPP | mlp32 | temperature | bacc | 0.6323018551602554 | 0.6234626778558922 | 0.6398016087681095 | 59.0 | 未提供 |