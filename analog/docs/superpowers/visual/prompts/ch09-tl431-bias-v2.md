---
id: ch09-tl431-bias-v2
generator: svg-v2-scene
reference_policy: none
style_id: FA-029
layout_id: IG-015
color_ids:
- C-34
- C-32
source_facts:
- docs/p1-10-ch9.md#9.2
numbers:
- value: '0'
  label: 示意
  reason: 模型坐标刻度与节拍序号，不是器件规格。
- value: '1'
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
- value: '10'
  label: 示意
  reason: 模型坐标刻度与节拍序号，不是器件规格。
- value: '100'
  label: 示意
  reason: 模型坐标刻度与节拍序号，不是器件规格。
- value: '200'
  label: 示意
  reason: 模型坐标刻度与节拍序号，不是器件规格。
zh_prompt: TL431 偏流流入 REF，输出误差是加号。REF 节点：上电阻电流等于下电阻电流加偏流。 Vout=Vref(1+R1/R2)+Iref·R1，符号为正。
  各 10 kΩ 时输出为 5.020 V，不是 4.980 V。 各 100 kΩ 时输出为 5.200 V；阻值上限由预算反推。 示意 Vref=2.5 V、Iref=2
  µA，两电阻相等；忽略其余误差。
en_prompt: Four causal snapshots, physical axes, model equations and explicit device
  boundaries. tl431 bias
---
