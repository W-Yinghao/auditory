N2：实现 `NUMERICAL_FAILURE`；支持 `SUFFICIENT_FOR_SCREEN`；对照 `MISSING`；科学状态 `NOT_EVALUABLE`。固定来源 `N2_core_001`；执行状态 `CORE_MATRIX_RECORDED`。

主对象固定 R_SIM/P_bal/logistic、k=8同一袋上的HMU−HMUVAR，量级0.01 bits/bag；需要超过重复均值列、pre与H_BAG解释。10次测试重组不重新拟合，必须先按候选平均后评价方向。k=4/8/16共同支持审计只说明支持；未运行的k曲线不得作图或宣称已完成。pre与post窗长度不同，二者差异不是纯因果响应。

主预设效应（空表表示尚无合格主聚合，不能当作零）：

| analysis_id | readout_family | estimate | ci_lower | ci_upper | n_candidates | unit | descriptive_screen |
| --- | --- | --- | --- | --- | --- | --- | --- |
| post_gain_mu_var | logistic | -0.0014935038347629 | -0.0030173067911442 | -0.0002579784684654 | 57.0 | bits/bag | NEGATIVE_SCREEN |

固定对照执行状态：

| control | population_id | readout_family | calibration | status | estimate | ci_lower | ci_upper | source_run |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| frozen_implementation_contracts | 未提供 | 未提供 | 未提供 | COMPLETE | 未提供 | 未提供 | 未提供 | tests_010 |
| legacy_integrity_and_private_permissions | 未提供 | 未提供 | 未提供 | COMPLETE | 未提供 | 未提供 | 未提供 | postflight_002 |
| complete_prespecified_primary_aggregates | 未提供 | 未提供 | 未提供 | COMPLETE | 未提供 | 未提供 | 未提供 | N2_core_001 |
| prespecified_synthetic_execution_coverage | 未提供 | 未提供 | 未提供 | COMPLETE | 未提供 | 未提供 | 未提供 | synthetic_001 |
| prespecified_synthetic_direction_and_controls | 未提供 | 未提供 | 未提供 | MISSING | 未提供 | 未提供 | 未提供 | synthetic_001 |
| post_mv_vs_dup | P_bal | logistic | temperature | COMPLETE | -0.000828735991338 | -0.0017620540304157 | 0.0001031153272239 | N2_core_001 |
| pre_gain_mu_var | P_bal | logistic | temperature | COMPLETE | 0.0009098707435204 | -0.000192159062132 | 0.0021043825935774 | N2_core_001 |
| post_minus_pre_gain_mu_var_post_minus_pre | P_bal | logistic | temperature | COMPLETE | -0.0024033745782834 | -0.0048201105577513 | -0.0006369280766953 | N2_core_001 |
| ten_frozen_test_regroupings | 未提供 | 未提供 | 未提供 | COMPLETE | 未提供 | 未提供 | 未提供 | N2_core_001 |
| regrouping_average_post_gain_mu_var | 未提供 | logistic | temperature | COMPLETE | -0.0005423520268466 | -0.0012754500941366 | 0.0002696078337295 | N2_core_001 |
| regrouping_average_post_mv_vs_dup | 未提供 | logistic | temperature | COMPLETE | -0.0007018547620667 | -0.0012637186230403 | -0.0001684802534161 | N2_core_001 |
| regrouping_average_pre_gain_mu_var | 未提供 | logistic | temperature | COMPLETE | 0.0001980273794837 | -0.0006700764805348 | 0.0012713640031106 | N2_core_001 |
| regrouping_average_pre_mv_vs_dup | 未提供 | logistic | temperature | COMPLETE | 0.0003318463390711 | -0.0005460152322084 | 0.0014053793057686 | N2_core_001 |
| regrouping_average_post_gain_mu_var | 未提供 | logistic | temperature | COMPLETE | -0.0015236912218686 | -0.0031559840655442 | -0.0001977305286167 | N2_core_001 |
| regrouping_average_post_mv_vs_dup | 未提供 | logistic | temperature | COMPLETE | -0.0009215024675311 | -0.0019632072946629 | 8.140796169223956e-05 | N2_core_001 |
| regrouping_average_pre_gain_mu_var | 未提供 | logistic | temperature | COMPLETE | 0.0002111274306447 | -0.0005299652825255 | 0.0008989215655122 | N2_core_001 |
| regrouping_average_pre_mv_vs_dup | 未提供 | logistic | temperature | COMPLETE | 0.0003473490596605 | -0.0003338576645715 | 0.0010259126528834 | N2_core_001 |
| fixed_prediction_metrics_and_influence | 未提供 | 未提供 | 未提供 | COMPLETE | 未提供 | 未提供 | 未提供 | metrics_001 |

全部表示、raw/temperature及诊断混合校准在paired_effects与metrics_aggregate保留。区间是固定OOF候选cluster bootstrap，并非重拟合整条pipeline。缺失字段表示源聚合未提供；未由试次或记录数倒推儿童人数。


预设风险与准确率（固定来源，不按大小筛选；未提供AUROC/Brier/区间时保持空值）：

| analysis_id | representation | population_id | model | readout_family | calibration | metric | estimate | ci_lower | ci_upper | n_candidates | n_records |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| N2_post_ | L0 | P_bal | H | logistic | temperature | ce_bits | 0.1316776394975503 | 0.0410395742365194 | 0.3054368325976156 | 57.0 | 未提供 |
| N2_post_ | L0 | P_bal | H | logistic | temperature | J_bits | 0.8683223605024497 | 0.6945631674023844 | 0.9589604257634806 | 57.0 | 未提供 |
| N2_post_ | L0 | P_bal | H | logistic | temperature | bacc | 0.982883404569792 | 0.9665593462892385 | 0.9921385816004068 | 57.0 | 未提供 |
| N2_pre_ | L0 | P_bal | H | logistic | temperature | ce_bits | 0.1316776394975503 | 0.0410395742365194 | 0.3054368325976156 | 57.0 | 未提供 |
| N2_pre_ | L0 | P_bal | H | logistic | temperature | J_bits | 0.8683223605024497 | 0.6945631674023844 | 0.9589604257634806 | 57.0 | 未提供 |
| N2_pre_ | L0 | P_bal | H | logistic | temperature | bacc | 0.982883404569792 | 0.9665593462892385 | 0.9921385816004068 | 57.0 | 未提供 |
| N2_post_ | L0 | P_bal | HMU | logistic | temperature | ce_bits | 0.1310694608270171 | 0.0414915846601707 | 0.3034124244493481 | 57.0 | 未提供 |
| N2_post_ | L0 | P_bal | HMU | logistic | temperature | J_bits | 0.8689305391729829 | 0.6965875755506519 | 0.9585084153398293 | 57.0 | 未提供 |
| N2_post_ | L0 | P_bal | HMU | logistic | temperature | bacc | 0.9831944547696632 | 0.9669115093698252 | 0.9924282990768662 | 57.0 | 未提供 |
| N2_pre_ | L0 | P_bal | HMU | logistic | temperature | ce_bits | 0.132738225049188 | 0.0412086493659619 | 0.3081211123350146 | 57.0 | 未提供 |
| N2_pre_ | L0 | P_bal | HMU | logistic | temperature | J_bits | 0.867261774950812 | 0.6918788876649854 | 0.9587913506340381 | 57.0 | 未提供 |
| N2_pre_ | L0 | P_bal | HMU | logistic | temperature | bacc | 0.9826342367221196 | 0.9666485733417528 | 0.9919521607472084 | 57.0 | 未提供 |
| N2_post_ | L0 | P_bal | HMUMU | logistic | temperature | ce_bits | 0.1308508212660176 | 0.0415927482673073 | 0.3022773106712539 | 57.0 | 未提供 |
| N2_post_ | L0 | P_bal | HMUMU | logistic | temperature | J_bits | 0.8691491787339825 | 0.697722689328746 | 0.9584072517326927 | 57.0 | 未提供 |
| N2_post_ | L0 | P_bal | HMUMU | logistic | temperature | bacc | 0.9831944547696632 | 0.9669115093698252 | 0.9924282990768662 | 57.0 | 未提供 |
| N2_pre_ | L0 | P_bal | HMUMU | logistic | temperature | ce_bits | 0.1330495879693615 | 0.0413548817768483 | 0.3086741781207411 | 57.0 | 未提供 |
| N2_pre_ | L0 | P_bal | HMUMU | logistic | temperature | J_bits | 0.8669504120306385 | 0.6913258218792588 | 0.9586451182231517 | 57.0 | 未提供 |
| N2_pre_ | L0 | P_bal | HMUMU | logistic | temperature | bacc | 0.983005356830082 | 0.9674736587432284 | 0.992088767365704 | 57.0 | 未提供 |
| N2_post_ | L0 | P_bal | HMUVAR | logistic | temperature | ce_bits | 0.132520710895277 | 0.0425904048024619 | 0.304813382173483 | 57.0 | 未提供 |
| N2_post_ | L0 | P_bal | HMUVAR | logistic | temperature | J_bits | 0.8674792891047229 | 0.6951866178265169 | 0.9574095951975381 | 57.0 | 未提供 |
| N2_post_ | L0 | P_bal | HMUVAR | logistic | temperature | bacc | 0.9828685051653862 | 0.9666508376243464 | 0.9922745527472256 | 57.0 | 未提供 |
| N2_pre_ | L0 | P_bal | HMUVAR | logistic | temperature | ce_bits | 0.132586500564046 | 0.0413177968339404 | 0.3074556430906874 | 57.0 | 未提供 |
| N2_pre_ | L0 | P_bal | HMUVAR | logistic | temperature | J_bits | 0.867413499435954 | 0.6925443569093126 | 0.9586822031660596 | 57.0 | 未提供 |
| N2_pre_ | L0 | P_bal | HMUVAR | logistic | temperature | bacc | 0.9834815279976 | 0.9680583528979532 | 0.992509247224373 | 57.0 | 未提供 |
| N2_post_ | L0 | P_bal | HRFF | logistic | temperature | ce_bits | 0.1307694336291982 | 0.0417572748158828 | 0.3013696828695573 | 57.0 | 未提供 |
| N2_post_ | L0 | P_bal | HRFF | logistic | temperature | J_bits | 0.8692305663708018 | 0.6986303171304427 | 0.9582427251841172 | 57.0 | 未提供 |
| N2_post_ | L0 | P_bal | HRFF | logistic | temperature | bacc | 0.9830103596423728 | 0.9666095776579676 | 0.9923931382615092 | 57.0 | 未提供 |
| N2_pre_ | L0 | P_bal | HRFF | logistic | temperature | ce_bits | 0.1321577878818285 | 0.0415902283679843 | 0.3051090173768433 | 57.0 | 未提供 |
| N2_pre_ | L0 | P_bal | HRFF | logistic | temperature | J_bits | 0.8678422121181715 | 0.6948909826231566 | 0.9584097716320157 | 57.0 | 未提供 |
| N2_pre_ | L0 | P_bal | HRFF | logistic | temperature | bacc | 0.983332774319522 | 0.9670341643984582 | 0.9927025040171364 | 57.0 | 未提供 |
| N2_post_ | L0 | P_bal | HVAR | logistic | temperature | ce_bits | 0.1334939780290358 | 0.042435275662987 | 0.308003359855611 | 57.0 | 未提供 |
| N2_post_ | L0 | P_bal | HVAR | logistic | temperature | J_bits | 0.8665060219709642 | 0.691996640144389 | 0.957564724337013 | 57.0 | 未提供 |
| N2_post_ | L0 | P_bal | HVAR | logistic | temperature | bacc | 0.9830201750517834 | 0.9668084669698812 | 0.9923890800304124 | 57.0 | 未提供 |
| N2_pre_ | L0 | P_bal | HVAR | logistic | temperature | ce_bits | 0.1312945219106828 | 0.0412310011283996 | 0.304178114537713 | 57.0 | 未提供 |
| N2_pre_ | L0 | P_bal | HVAR | logistic | temperature | J_bits | 0.8687054780893172 | 0.6958218854622871 | 0.9587689988716004 | 57.0 | 未提供 |
| N2_pre_ | L0 | P_bal | HVAR | logistic | temperature | bacc | 0.9832572427526876 | 0.9673515786384538 | 0.9923024215384284 | 57.0 | 未提供 |
| N2_post_ | R_SIM | P_bal | H | logistic | temperature | ce_bits | 0.1316776394975503 | 0.0410395742365194 | 0.3054368325976156 | 57.0 | 未提供 |
| N2_post_ | R_SIM | P_bal | H | logistic | temperature | J_bits | 0.8683223605024497 | 0.6945631674023844 | 0.9589604257634806 | 57.0 | 未提供 |
| N2_post_ | R_SIM | P_bal | H | logistic | temperature | bacc | 0.982883404569792 | 0.9665593462892385 | 0.9921385816004068 | 57.0 | 未提供 |
| N2_pre_ | R_SIM | P_bal | H | logistic | temperature | ce_bits | 0.1316776394975503 | 0.0410395742365194 | 0.3054368325976156 | 57.0 | 未提供 |
| N2_pre_ | R_SIM | P_bal | H | logistic | temperature | J_bits | 0.8683223605024497 | 0.6945631674023844 | 0.9589604257634806 | 57.0 | 未提供 |
| N2_pre_ | R_SIM | P_bal | H | logistic | temperature | bacc | 0.982883404569792 | 0.9665593462892385 | 0.9921385816004068 | 57.0 | 未提供 |
| N2_post_ | R_SIM | P_bal | HMU | logistic | temperature | ce_bits | 0.134407589765505 | 0.0413365855448929 | 0.3125812626740535 | 57.0 | 未提供 |
| N2_post_ | R_SIM | P_bal | HMU | logistic | temperature | J_bits | 0.865592410234495 | 0.6874187373259465 | 0.958663414455107 | 57.0 | 未提供 |
| N2_post_ | R_SIM | P_bal | HMU | logistic | temperature | bacc | 0.9836186358260464 | 0.967613521893532 | 0.9926828539534892 | 57.0 | 未提供 |
| N2_pre_ | R_SIM | P_bal | HMU | logistic | temperature | ce_bits | 0.1320580278930576 | 0.0410060504229425 | 0.3068333380118441 | 57.0 | 未提供 |
| N2_pre_ | R_SIM | P_bal | HMU | logistic | temperature | J_bits | 0.8679419721069423 | 0.6931666619881559 | 0.9589939495770575 | 57.0 | 未提供 |
| N2_pre_ | R_SIM | P_bal | HMU | logistic | temperature | bacc | 0.9841883861379314 | 0.9685221065423956 | 0.9933261447658384 | 57.0 | 未提供 |
| N2_post_ | R_SIM | P_bal | HMUMU | logistic | temperature | ce_bits | 0.1350723576089299 | 0.0415313357965784 | 0.3140234890055557 | 57.0 | 未提供 |
| N2_post_ | R_SIM | P_bal | HMUMU | logistic | temperature | J_bits | 0.8649276423910701 | 0.6859765109944442 | 0.9584686642034216 | 57.0 | 未提供 |
| N2_post_ | R_SIM | P_bal | HMUMU | logistic | temperature | bacc | 0.983469959049359 | 0.9674214211017852 | 0.992569551594943 | 57.0 | 未提供 |
| N2_pre_ | R_SIM | P_bal | HMUMU | logistic | temperature | ce_bits | 0.13212559503386 | 0.0410556078261355 | 0.3070373351677106 | 57.0 | 未提供 |
| N2_pre_ | R_SIM | P_bal | HMUMU | logistic | temperature | J_bits | 0.86787440496614 | 0.6929626648322894 | 0.9589443921738645 | 57.0 | 未提供 |
| N2_pre_ | R_SIM | P_bal | HMUMU | logistic | temperature | bacc | 0.9841883861379314 | 0.9685221065423956 | 0.9933261447658384 | 57.0 | 未提供 |
| N2_post_ | R_SIM | P_bal | HMUVAR | logistic | temperature | ce_bits | 0.1359010936002679 | 0.0422932674356787 | 0.3156224299706782 | 57.0 | 未提供 |
| N2_post_ | R_SIM | P_bal | HMUVAR | logistic | temperature | J_bits | 0.8640989063997321 | 0.6843775700293218 | 0.9577067325643213 | 57.0 | 未提供 |
| N2_post_ | R_SIM | P_bal | HMUVAR | logistic | temperature | bacc | 0.9830656469551166 | 0.9666221353137908 | 0.992446425306288 | 57.0 | 未提供 |
| N2_pre_ | R_SIM | P_bal | HMUVAR | logistic | temperature | ce_bits | 0.1311481571495371 | 0.0403835811999361 | 0.3057230909544814 | 57.0 | 未提供 |
| N2_pre_ | R_SIM | P_bal | HMUVAR | logistic | temperature | J_bits | 0.8688518428504629 | 0.6942769090455185 | 0.9596164188000639 | 57.0 | 未提供 |
| N2_pre_ | R_SIM | P_bal | HMUVAR | logistic | temperature | bacc | 0.9836610096203868 | 0.967366387950882 | 0.9929724018991096 | 57.0 | 未提供 |
| N2_post_ | R_SIM | P_bal | HRFF | logistic | temperature | ce_bits | 0.1348756825174286 | 0.0416371466882159 | 0.3130001083109076 | 57.0 | 未提供 |
| N2_post_ | R_SIM | P_bal | HRFF | logistic | temperature | J_bits | 0.8651243174825713 | 0.6869998916890925 | 0.9583628533117841 | 57.0 | 未提供 |
| N2_post_ | R_SIM | P_bal | HRFF | logistic | temperature | bacc | 0.9826006393127968 | 0.966193766529442 | 0.9919441022041376 | 57.0 | 未提供 |
| N2_pre_ | R_SIM | P_bal | HRFF | logistic | temperature | ce_bits | 0.1328186739499093 | 0.0410788115536551 | 0.3086402104088894 | 57.0 | 未提供 |
| N2_pre_ | R_SIM | P_bal | HRFF | logistic | temperature | J_bits | 0.8671813260500907 | 0.6913597895911106 | 0.9589211884463449 | 57.0 | 未提供 |
| N2_pre_ | R_SIM | P_bal | HRFF | logistic | temperature | bacc | 0.983328544225458 | 0.9668905980623914 | 0.9926815765461956 | 57.0 | 未提供 |
| N2_post_ | R_SIM | P_bal | HVAR | logistic | temperature | ce_bits | 0.1329928573584442 | 0.0418821556812007 | 0.3079558288299015 | 57.0 | 未提供 |
| N2_post_ | R_SIM | P_bal | HVAR | logistic | temperature | J_bits | 0.8670071426415558 | 0.6920441711700984 | 0.9581178443187993 | 57.0 | 未提供 |
| N2_post_ | R_SIM | P_bal | HVAR | logistic | temperature | bacc | 0.983523363968677 | 0.9670638910534302 | 0.993056263282231 | 57.0 | 未提供 |
| N2_pre_ | R_SIM | P_bal | HVAR | logistic | temperature | ce_bits | 0.1309097021092248 | 0.0406278589431721 | 0.304516434500991 | 57.0 | 未提供 |
| N2_pre_ | R_SIM | P_bal | HVAR | logistic | temperature | J_bits | 0.8690902978907752 | 0.695483565499009 | 0.9593721410568279 | 57.0 | 未提供 |
| N2_pre_ | R_SIM | P_bal | HVAR | logistic | temperature | bacc | 0.9826666579239624 | 0.965916054193232 | 0.9921916788620958 | 57.0 | 未提供 |