# 只读工具的合成输入示例

`normalized_record_index.jsonl`不是真实服务器记录。它演示3401/3407有两侧、3413缺候选的情况。

在包根目录运行：

```bash
python scripts/audit_seed_pairs.py \
  --index examples/normalized_record_index.jsonl \
  --spec configs/pairing_example.yaml \
  --output /tmp/aln34_synthetic_pair_audit.json
```

实际使用需由server从自己的registry提取相同字段、分配语义角色。任何缺项或重复都不得根据性能择优消除。这个工具只核对元数据相等，不替代对完整训练依赖和身份泄漏的检查。
