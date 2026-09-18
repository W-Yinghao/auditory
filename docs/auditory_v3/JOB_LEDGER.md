> GitHub 发布副本：本轮执行完成后，用户明确要求发布代码与聚合结果。文内“未 push”和早期运行状态是历史记录；V3 以 final_002 为准。个体数据、预测、模型和详细日志留在服务器。见[发布范围](../../PUBLICATION.md)。

# v3 resource reservations

All numerical work is submitted through Slurm. Original YAML and design are preserved; configs/auditory_v3_plan.yaml is an exact execution copy. Maximum 160 CPU core-hours including GPU-job CPUs, 16 GPU-hours, 3000 head attempts,30 formal encoders and3 synthetic encoders. No P100. No automatic publication. Jobs are reserved before submission; failures remain charged.

| Run | Purpose | CPU cores | Walltime | GPU | CPU core-hour upper bound |
|---|---|---:|---|---:|---:|
| inspect_001 | Resolve and hash relevant inputs, zero fitting | 2 | 00:15:00 | 0 | 0.5 |

Formal R3 reservation, conditional on support and capability:30 × 30min ×1GPU and4CPUs =15GPU-hours and60CPU core-hours. Synthetic R3:3 ×10min =0.5GPU-hours and2CPU core-hours. RemainingGPU reserve0.5h. P0real260,N2Rreal550,R3probe280,N2Rcapability1200,P0capability30head calls; remaining680 cover tests/development/numerical recovery. Exact fit catalog follows frozen support.

- inspect_001: Slurm997615 COMPLETE,0fits;49groups/698bags/5584trials,20P0featurelanes,49epochrecords.
- support_001: reserve2CPU×15min=0.5core-hour,0GPU,0fits; frozen bag/split/scope/epoch/quartet audit. Cumulative submitted upper bound1CPU core-hour.
- support_001/job997616 failed before model fitting: integer versus nullable-float half metadata was compared as strings. Corrected equality preserves exact numeric values; original failure retained.
- support_002 reserved2CPU×15min=0.5core-hour,0GPU/0fits. Cumulative submitted1.5CPU core-hours.
- support_002/job997617 COMPLETE: allP0/N2R/R3 supportSUFFICIENT;R3quartets98/98cells.
- plan_001: reserve2CPU×5min=1/6core-hour,0GPU/0fits. Cumulative submitted1+2/3CPU core-hours.
- plan_001/job997618 COMPLETE; planned2283headcalls including3R3smokeprobes;717remainingwithin3000forcontract tests/development/recovery. No models fitted.
- tests_P0_001: reserve2CPU×5min=1/6core-hour; expected5real synthetic testfits; noencoder/GPU. Cumulative submitted upperbound11/6CPU core-hours.
- tests_P0_001/job997619 FAILED duringcollection,0fits: pytest testpackage clashes withsame-namedsourcepackage whenrunninginprocess. Useimportlibtestimportmode; noalgorithmchange.
- tests_P0_002 reserved2CPU×5min=1/6core-hour. Cumulative submitted2CPUcore-hours.
- tests_P0_002/job997620 PASS16tests,5actualsyntheticfits; expectednonfinite-injectiontestwarning retained.
- capability_P0_001 reserved2CPU×15min=0.5core-hour,32heads(30world+2equivalence). Codefrozenfromtests_P0_002/source. Cumulative submitted2.5CPUcore-hours.
- capability_P0_001/job997621 PASS15worlds/30heads plus2equivalenceheads;32attempts. Lowvariance5/5andtopPCA5/5recovered, no development revision.
- P0_001: reserve2CPU×1h=2CPUcore-hours,0GPU;260headmatrix. Frozen code tests_P0_002/source and matching capability_P0_001. Cumulative submitted4.5CPUcore-hours.
- P0_001/job997622 COMPLETE in73.95s;260/260heads, execution/controlPASS; primary scientifically NO_DETECTABLE_COMPRESSION_PENALTY. All failed/negative outcomes retained.
- tests_N2R_001 reserved2CPU×5min=1/6core-hour; synthetic contract tests only. Cumulative submitted upper bound14/3CPUcore-hours.
- tests_N2R_001/job997624 FAILED2of24tests,1synthetichead. Obsolete helpertest passed raw400coordinates into PC8view builder and asserted unbroadcasted arrays; strengthened helper to require8PCs and separate400sensitivity statistics, correctedtestcontract. Real N2R sharedrunner unaffected; no real fits.
- tests_N2R_002 reserved2CPU×5min=1/6core-hour. Cumulative submitted upperbound29/6CPUcore-hours.
- tests_N2R_002/job997625 PASS24tests,1syntheticfit. Full3foldselection, HQQgeometry, train-onlytransforms andcompletefailuredenominators covered.
- development_N2R_001 reserve2CPU×30min=1core-hour,60plannedheads,3independentdevelopmentseeds50001–50003 ontheexact698bagtemplate. Codefrozenfromtests_N2R_002/source. Cumulative submittedupperbound35/6CPUcore-hours. Formal53001–53060bank remainsunseen.
- development_N2R_001/job997626 PASS3worlds/60heads in18.14s; stronggain0.209255, mean-nullgain0.000401, history-nullgain−0.000142 bits/bag. Generator frozenwithoutrevision beforeevaluationseedbank.
- capability_N2R_001 reserve2CPU×30min=1core-hour,1200plannedheads/60worlds; tests_N2R_002 frozen source and matchingdevelopment_N2R_001. Cumulative submittedupperbound41/6CPUcore-hours.
- tests_R3_001 reserve2CPU×5min=1/6core-hour; CPUcontracttests only,1expectedsyntheticlogisticfit,zeroencoders. Cumulative submittedupperbound7CPUcore-hours.
- tests_R3_001/job997628 FAILED2of29tests,1syntheticlogisticfit,zeroencoders: invalidsynthetictestreshape andrelative-SVDdiagnostic inflated rankofroundoff inconstantcoordinates. Correctedtest usinghand-computedNT-Xent andMATCHloss; rankdiagnostic zerosdeclaredconstantcoordinates (nochangeprobeinputs/optimization).
- tests_R3_002 reserved2CPU×5min=1/6core-hour. Cumulative submittedupperbound43/6CPUcore-hours.
- tests_R3_002/job997629 FAILED1of29,1synthetichead/zeroencoders; exactconstantcolumns canleave roundofflargerthanmachineepsilon inweightedcentering. Rankdiagnostic nowusesrowdifferencesandexactconstantmask; fittedinputs/risksunchanged. AddedexplicitCNNbindingandcompletehashed15-encoderselectiongatebeforefinaltraining.
- tests_R3_003 reserve2CPU×5min=1/6core-hour. Cumulative submittedupperbound22/3CPUcore-hours.
- tests_R3_003/job997630 FAILED1of29 afterranktestpassed: constantchanceCE assertionrequiredexact1.0 butfloatweightedCE=0.9999999999999998. Replacedexactfloatcomparisonwith1e-14absolute tolerance; noalgorithmchange.1synthetichead,zeroencoders.
- tests_R3_004 reserve2CPU×5min=1/6core-hour. Cumulative submittedupperbound7.5CPUcore-hours.
- capability_N2R_001/job997627 PASS60/60worlds,1200/1200heads,329.25s. VAR_EXTRA20/20gain>.01; MEAN_SUFFICIENT0/20andHISTORY_ONLY0/20nullscreenhits. Noevaluation-seedreuse/revision.
- N2R_001 reserve2CPU×1h=2core-hours,550realheads; independentN2Rgatecapability_N2R_001,immutabletests_N2R_002/source. Cumulative submittedupperbound9.5CPUcore-hours.
- tests_R3_004/job997631 PASS29tests,1synthetichead/zeroencoders. R3sourcefrozenattests_R3_004/source.
- exposures_R3_001 reserve2CPU×30min=1core-hour,zeroEEGfits;10sharedselection/finalplans. Cumulative CPUupperbound10.5h.
- capability_R3_SUP_001,capability_R3_SIM_001,capability_R3_MATCH_001 eachreserveA100×10min+4CPU:total0.5GPUhours/2CPUcore-hours,3syntheticencoders+3probes. Maximum2concurrent;MATCHdependsafterSUP. CumulativeCPUupperbound12.5h,GPUupperbound0.5h.
- N2R_001/job997632 COMPLETE550/550realheads. Primarygain−0.000843949bits/bag CI[−0.008416885,0.006606403], NO_CONTROLLED_GAIN_ESTABLISHED. Full400sensitivity also retainednegative.
- exposures_R3_001/job997633 COMPLETE10plans,0fits; sharedfixedmetadataexposureplansretained. Futurebackendrepairneednotredrawplans; sourcebindingforplanscomparesmetadata/data/splitcodeandconfig.
- capability_R3_SUP_001/job997634 andSIM_001/job997635 FAILED atfirstbackward: nativeCUDAadaptivepoolbackwardrejectsstrictdeterminism. Bothoriginalencoderallocationsremaincharged; zerooptimizerupdates (errorprecedesfirstoptimizer.step), noprobe, nocheckpoint/progress. MATCH997636cancelledwhilepending,zeroexecution/fits.
- Backendrepair preservesexactnativeadaptivepoolbinboundarieswithparameter-freeslicemeans. Strictdeterminismremainsenabled. SUP/SIM mayeachcontinueoriginalzero-updateallocationonlyafterconfig/generator/scientificcode/initialencoder/exposurehashchecks; failedjobsremainvisible. Noalternativeinitialization/seed/model tuning. Ledger rejectsduplicaterecoveryreservation. Therewillstillbeonly3distinctsyntheticmodels,atmost5attemptedGPUexecutionsincluding2failedfirstbackwards.
- tests_R3_005 reserve2CPU×5min=1/6core-hour. CumulativeCPUupperbound38/3h. TwoSUP/SIMrecoveryjobsreserveadditional4/3CPUhours+1/3GPUhours (10mineach); MATCHreplacementusesitscancelledreservation. TotalreservedCPU14h,GPU5/6h beforeformalencoders.
- tests_R3_005/job997637 PASS33tests,1synthetichead/zeroencoders. Includesnative-versus-replacement poolingforward/backward atbothpost/prelengths, unchangedparameterobjects/statekeys/RNG. Recoveries useimmutabletests_R3_005/source.
- Correction afterglobalfit-ledgeraudit: MATCH997636startedbetweenqueueinspectionandcancel, thenhitthesamefirst-backwardfailure; itdidconsumeitsoriginalsyntheticallocation. Nooptimizerupdateoccurred. Earlier"pendingcancel/zeroexecution"noteissuperseded, originalfailure/log/ledgerpreserved. SUP/SIM/MATCHdistinctsyntheticallocations=3.
- SUP002/997638 andSIM002/997639 completedsame-statecontinuations,all60epochs,strongheldoutbAcc1.0andcheckpointrestartmaxdifference0.0. SlurmRunTime13seach (schedulerreceiptsretained). MATCH002/997640 wasblockedbyglobal3-modelceilingbeforefitting,RunTime7s; thiscorrectlypreventedafourthallocation.
- MATCH003 recoverywillreferenceoriginalMATCH001zero-updateallocation. ReserveA100×10min+4CPUs. Completed997638/997639/997640reservationsreleasedtotheirverified13+13+7GPU-seconds;retainfull30minfororiginal3failedsmokes. ConservativeGPUboundbeforeformal=30min+33s+10min=0.675833h; plus30formal×30min=15.675833h<16h. Allfailedjobsremaincounted. CPUreservationsremainfarbelow160h.
- capability_R3_001 join reserve2CPU×5min=1/6core-hour,zeroheads/encoders; dependsaftercompletedMATCH003 andrequiresall3independentobjectivePASSreceipts/sourcebindings.
- MATCH003/997641 PASSbAcc1.0,restartdifference0.0;sameoriginalallocationrecovery. capability_R3_001/997642 PASSall3objectives;SUP/MATCHbAcc1.0,SIMfinite,identicalinit/exposureconfirmed.3distinctsyntheticallocations,3first-backwardfailures,3same-statecontinuations,1budget-blockedzerofitjobretained.
- R3_selection_001 tasks0–14 reserve15A100×30min=7.5GPUhours+30CPUcore-hours;arrayconcurrency2, fixed60epochs, noouter-testinselectiontraining. Formalencodercatalogfirst15of30. Fullroundremainingfinal15pre-reserved7.5GPUhours/30CPUhours; conservativeallGPUbound15.675833h<16h beforefuturecompletedjobcredits.
- R3_probe_selection_001 reserve2CPU×30min=1CPUcore-hour,180selectionheads; dependencyafterentire15-taskR3_selection_001array997643. Allcheckpoint/source/exposure/scopesverifiedagain; noouter-testinference.
- R3_selection_001/997643 COMPLETE15/15encoders. Probe_selection_001/997656 attemptedall180heads;56/60choicegridsreportedfinite. Fourfold3SUP/MATCHpostgridsbecameunscorablebecausefinitepositive logits roundedtoexactprobability1, producinginfiniteprobability-domainCE. Originalresultsretained; nofailedhead/foldorpenaltyisremoved.
- Numericalpostprocessingamendment: evaluateidenticalBCEaslogaddexp(0,(1−2y)logit)/ln2 fromsavedcoefficients; no probabilityclipping, no readout/encoderrefit, noepoch/backbone/penaltychange, noouter-testusedtorepairselection. Basefittingalgorithm/sourcehashesremainunchanged; newscoringcodehasseparatetests/hash. All180savedheadsrescored, notonlythefouraffectedchoices. TrueNaN/Inf/fittingfailurestillinvalidateswholemodel.
- tests_R3_scoring_001 reserve2CPU×5min=1/6core-hour,zerohead/encoderfits. Selectionrepairreserve2CPU×30min=1core-hour,zeroadditionalfits. Actualremainingformalencoderbudget15 unchanged.
- tests_R3_scoring_001/job997660 PASS6tests,0fits. Analytic±1000logits,moderateprobabilityagreement,rawlogitAUCordering,sharedidentitybootstrap andmissing-foldfailure tested.
- R3_probe_selection_002/job997661 COMPLETE60/60choices fromall180existingmodels,0additionalfits,13.44s. Originalprobabilityfailuresretained; noouter-testscored.
- R3_final_001 tasks0–14 nowreleasepre-reserved15A100×30min=7.5GPUhours/30CPUcore-hours,maximum2concurrent. Togetherwithselectionexactly30formalencoderallocations. Eachfinaljobhash-checkscomplete15-encoderselectionreceiptandall60choices beforetrainingonallouter-traingroups.
- R3_001 finalprobe+stable-scoring reserve2CPU×30min=1CPUcore-hour,60plannedheads. Dependsonall15finalencoders997662. Fitcoreusesfixedlambda choices fromR3_probe_selection_002; stablelogitpostprocessingadds0fits,retainsoriginalprobabilityoutputsprivately.
- final_001 reserve2CPU×10min=1/3CPUcore-hour,zerohead/encoderfits; dependencyafterR3_001/997666. Readscompletedthreepacketreceipts, verifiesindependentcapabilityreceipts, emitsprimarytable/figure,globalfit/resourceaccountingandknownparticipant-identifierscan. Requiresallpacketexecutioncomplete; neveraveragesonlysuccessfulfolds.
- R3_final_001/997662 COMPLETE15/15; totalformalencoderallocations30/30. R3_001/997666 COMPLETE60/60finalheads,12completeOOFviews; primarygain0.034124750bits/trial CI[−0.031362724,0.098477156], NO_ADDED_VALUE_OVER_SUPERVISION. Stable-logitpostprocess0additionalfits.
- final_001/997678 COMPLETE, all3primaryresultsrecorded;2357headattempts,30formalencoders,3syntheticallocations+3same-statecontinuations. ConservativeCPUupper45.442778core-hours,GPUupper8.3075h;allwithinlimits. Knownidentifieraudit102textfiles/6429tokens/0matches. Finalfigures/tableproduced.
- final_002 reserve2CPU×10min=1/3core-hour,0fits; final_001preserved. Reporting-onlyupdate improvesfiguretickspacing/contrastlabels and addsR3scientificinterpretation; repeatsidentifierauditafternewR3/decisiondocs. Scientificinputs/resultsunchanged.
- final_002/job997679 COMPLETE, authoritativefinalreport. Allscientificvaluesand2357/30/3fitcountsunchanged;110textfiles/6429knownparticipanttokens/0matches. UpdatedconservativeCPUupper45.776111core-hours,GPUupper8.3075h;budgetsPASS. Allv3jobsfinished;unrelated994815untouched. NoGitHubpush.
