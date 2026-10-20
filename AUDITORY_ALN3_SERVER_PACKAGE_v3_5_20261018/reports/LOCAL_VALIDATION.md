# ALN3.5 本地交付核查

本报告验证交付文件、分析参考实现和声明的输入几何；它不是服务器验收，也不表示新EEG实验已经完成。

## 已实际执行

- 封版前以只读 `git ls-remote` 核对 HEAD/main：`5ef4a60bf77eeaeab5582c2cb076077c0b15bd11`，UTC `2026-10-18T20:47:50Z`；随后本地 `git status --short` 为空。未修改或推送项目仓库。
- CPython 3.12.14、标准库环境中运行 `python3 -B -m unittest discover -s tests -v`：**28/28通过**。
- 128行合成JSONL通过runtime契约；schema的required/properties/provenance白名单与runtime一致。未执行外部JSON Schema引擎，工具无该依赖。
- 科学清单10个family转换为明确CLI字段后均通过spec检查，合计30项对比；原主终点清单另列3个family/10项。这里只检查格式、范围和方向；没有伪造真实名册或逐人结果来完成绑定。
- 科学说明中的synthetic observation单独通过字段检查；它不进入研究observations。
- 250 Hz实际访问几何：local pre保留0个位置、置零150个位置；FM pre保留50个位置（200 ms）、置零150个位置。参考工具没有读取EEG值，FM的实际全零状态保持未知。
- 只读intake工具对公开本地checkout的87个选定来源逐个核对SHA-256，全部匹配；不查询调度器或训练。该结果不是live server inventory。
- 9份继承原文与研究者附件逐字节一致；其历史状态和审批措辞不覆盖本包活动规格。
- 对研究关切、终点、支持元数据预算、训练/评价访问、统计方向和资源边界完成交叉审阅；实际源码地址按 `core.OUT` 解析。

具体机器记录：`reports/REFERENCE_VALIDATION.json`、`reports/LOCAL_INTAKE_REFERENCE.json`。

## 文件与压缩包封装

构建程序在全部文件定稿后生成 `MANIFEST.json`、`SHA256SUMS`，调用 `scripts/validate_package.py` 检查本地链接、JSON/JSONL、Python语法、成员清单、字节数和SHA-256；校验失败即不生成最终ZIP。ZIP生成后检查CRC与逐成员字节一致，且完整说明的独立Markdown副本与包内 `SERVER_FULL_DOCUMENT.md` 逐字节一致。

`MANIFEST.json`不对自身递归求hash；`SHA256SUMS`另含MANIFEST本身，且不对自身求hash。交付不含pycache、pyc或符号链接。server接收后可重新运行同一静态校验命令。

## 真实生产仍须绑定的内容

实际现场HEAD、live jobs/holds、可用checkpoint/cache、完整逐人unit、support/query的真实物理边界，以及训练/选择层级由server核验。本包提供输入合同、声明性比较、参考代码与回执模板；训练接入仍需按服务器当前实现完成，不能把本地合成验证报为真实生产兼容性或真实临床结果。
