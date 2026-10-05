# C3 独立复核补充包

- `01_REVIEW_AND_MINIMAL_ADDENDUM.md`：详细评审、解析反例、定位与运行中补充建议。
- `SERVER_ADDENDUM.md`：可交给服务器代理的有限补充文本；不是完整替换执行包。
- `numerical_checks/gcmi_core.py`：从用户C3包复制的原始参考实现，未修改。
- `numerical_checks/independent_c3_checks.py`：仅合成检查；不读取EEG或网络资源。
- `numerical_checks/independent_results.json`：本次实际输出。
- `numerical_checks/VALIDATION_SCOPE.json`：原包hash、8项测试、S1–S8重跑一致性和未运行事项。

依赖：Python、NumPy、SciPy。运行：

```bash
python numerical_checks/independent_c3_checks.py
```

该命令覆盖同目录的 `independent_results.json`；已有输出需留存时先复制目录。服务器遵守其Slurm规则。

检查覆盖解析与有限合成例，不证明真实EEG含有或不含任何临床信息。没有修改原ZIP、GitHub或服务器。
