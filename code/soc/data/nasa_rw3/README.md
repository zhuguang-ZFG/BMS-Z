# NASA RW3 实测子集

这些是外部实验的测量数据，许可为 **CC BY 4.0**，不适用本仓库源代码的 MIT 许可。

来源：[NASA PCoE](https://www.nasa.gov/intelligent-systems-division/discovery-and-systems-health/pcoe/pcoe-data-set-repository/) · [固定数据记录](https://zenodo.org/records/15277374) · [许可](https://creativecommons.org/licenses/by/4.0/)。

署名：Brian Bole、Chetan Kulkarni、Matthew Daigle，NASA Ames Research Center。请引用其 2014 年论文 *Adaptation of an Electrochemistry-based Li-Ion Battery Model to Account for Deterioration Observed Under Randomized Use*，以及 *Randomized Battery Usage Data Set*。

[samples.csv](samples.csv)从 RW3 的指定完整步骤导出；[metadata.json](metadata.json)保存步骤、样本数量、来源、归档 MD5、文件 SHA-256 和变换说明。变换包括选择步骤、将电流改成充正放负、各组全局时间归零，以及十进制格式化；没有重采样、插值或人工补齐测量。

`source_step` 和 `source_sample` 均从 0 开始。`time_s` 保留组内步骤间的时间差；`step_time_s` 是原始步骤局部时间。电流单位 A、电压 V、温度 °C。

CSV 不含实测 SOC。[实验教程](../../../../docs/SOC真实数据专题.md)解释计算参考的假设与局限；[转换器](../../prepare_nasa.py)用于从原 ZIP 重新生成本目录。

固定标定使用 step 0（低电流端电压）、2（容量）、5/6/7（长脉冲），验证为同一 RW3 的 step 32–49。读取器同时核对元数据划分、CSV 摘要及各步骤从 0 连续排列的 `source_sample`，不接受重复/缺失/乱序的源行身份。标定不读取验证组；反复利用验证结果选择参数后，需要新的验证工况，脚本不能替操作者证明调参历史。

回放 `trace.csv` 保留源步骤和源样本列，报告记录 `reference_assumptions`、`metric_basis` 与 `evaluation_scope`。`provenance.verified_this_run` 仅列本次实际核对项目；ZIP/MAT 摘要从本文件元数据转录，普通回放没有重新读取这些原始文件。数据与元数据本身未因此修改。新深研的放电正适配应遵循[符号与时间约定](../../../../bms-book/engineering-conventions.md)，避免对已转换的电流重复翻号。
