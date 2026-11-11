---
id: ch09-bandgap-balance-v2
generator: svg-v2-scene
reference_policy: none
style_id: FA-029
layout_id: IG-015
color_ids:
- C-34
- C-32
source_facts:
- docs/p1-10-ch9.md#9.1
numbers:
- value: '-40'
  label: 示意
  reason: 模型坐标刻度与节拍序号，不是器件规格。
- value: '0'
  label: 示意
  reason: 模型坐标刻度与节拍序号，不是器件规格。
- value: '0.7'
  label: 示意
  reason: 模型坐标刻度与节拍序号，不是器件规格。
- value: '1'
  label: 示意
  reason: 模型坐标刻度与节拍序号，不是器件规格。
- value: '1.4'
  label: 示意
  reason: 模型坐标刻度与节拍序号，不是器件规格。
- value: '2'
  label: 示意
  reason: 模型坐标刻度与节拍序号，不是器件规格。
- value: '3'
  label: 示意
  reason: 模型坐标刻度与节拍序号，不是器件规格。
- value: '4'
  label: 示意
  reason: 模型坐标刻度与节拍序号，不是器件规格。
- value: '25'
  label: 示意
  reason: 模型坐标刻度与节拍序号，不是器件规格。
- value: '85'
  label: 示意
  reason: 模型坐标刻度与节拍序号，不是器件规格。
zh_prompt: 带隙的一阶补偿，要把电流密度比算进去。先看 VBE：温度上升时，示意电压线性下降。 ΔVBE=(kT/q)ln8，乘合适比例后斜率相反。 令两条斜率相消，本例总电压为
  1.2463 V。 一阶平直不等于实际零漂；曲率、修调和应力另计。 线性示意：25°C 的 VBE 为 0.65 V，斜率 −2 mV/°C，N=8。
en_prompt: Four causal snapshots, physical axes, model equations and explicit device
  boundaries. bandgap balance
---
