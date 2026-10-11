# 本地验证回执

2026-10-10；所有数据为人工构造；未连接科研server，未运行真实EEG或基础模型训练。

## 实际完成

- **43项pytest测试通过**，原始输出见reference_tests.txt，JUnit见reference_tests.xml。
- 覆盖：dense query形状/通道敏感性/有效mask/梯度/状态往返；相位读出的仿射性；残差零初始化与梯度；正斜率截距校准、类别先验、排序保持、稳定对数损失；Federici规范长表的人类/phantom分离、HC/HC-v配对、真实身份聚类及重复行防误计；计划确定性、非赢家选择的多seed面板、任务/技术依赖。
- **5,996条计划记录**通过JSON schema；Python源文件通过AST语法检查；本地Markdown链接检查通过。
- 规范CSV重汇总CLI在人工例子上实际运行：3个人工human identity、1个人工phantom；输出分组与配对，不生成混合人类/phantom总体。见SYNTHETIC_CLI_TEST.json。
- 最终SHA256逐文件校验和zip逐成员字节比对在压缩包生成时完成；最终外部发布回执与zip一并提供。

## 不属于本回执的内容

真实身份核实、ALN2逐人结果重汇总、GPU模型微调、teacher/donor接入、年龄/设备统计和任务性能均**尚未在本地执行**。这43项测试只验证参考模块与材料包，不证明server端整个管线已正确。

环境版本见LOCAL_ENVIRONMENT.json。需求文件列出参考模块依赖；不要求server据此升级已有模型环境。
