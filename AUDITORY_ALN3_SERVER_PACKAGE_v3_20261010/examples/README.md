# 人工例子

SYNTHETIC_federici_long.csv中的编号和值均人工构造，仅演示规范长表、共享身份与phantom分离。不能引用为真实数据或科研结果。

```bash
python scripts/reaggregate_federici.py --input examples/SYNTHETIC_federici_long.csv --output-dir /tmp/aln3_synthetic_demo
```

真实导出由server从private逐单元JSON和来源核实的身份清单生成，保留在private下。不能把推断的身份关系标作来源核实。
