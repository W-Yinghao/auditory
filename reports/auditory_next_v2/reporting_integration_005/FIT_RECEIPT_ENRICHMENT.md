逐模型补充回执只读取保存的训练与优化记录。原生字段、明确别名、计算派生、运行层继承和未知分列；不以任务名称替代feature scope hash，不以标签数组hash替代标签映射hash，不把作业资源记为逐fit资源。模型文件集合hash与最终模型hash的语义保持区别；更新前最后梯度不冒充更新后诊断。完整字段值与来源路径仅在private。

| field | attempted_units | native_count | alias_count | derived_count | inherited_count | unknown_count |
| --- | --- | --- | --- | --- | --- | --- |