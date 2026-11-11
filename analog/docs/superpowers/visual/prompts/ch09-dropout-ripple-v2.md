---
id: ch09-dropout-ripple-v2
generator: svg-v2-scene
reference_policy: none
style_id: FA-029
layout_id: IG-015
color_ids:
- C-34
- C-32
source_facts:
- docs/p1-10-ch9.md#9.3
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
- value: '3.15'
  label: 示意
  reason: 模型坐标刻度与节拍序号，不是器件规格。
- value: '3.3'
  label: 示意
  reason: 模型坐标刻度与节拍序号，不是器件规格。
- value: '3.7'
  label: 示意
  reason: 模型坐标刻度与节拍序号，不是器件规格。
- value: '4'
  label: 示意
  reason: 模型坐标刻度与节拍序号，不是器件规格。
zh_prompt: 稳压余量看输入谷值，不只看平均值。输入为 3.5 V 加 0.2 V 正弦，平均值看似足够。 最高点 3.7 V，目标输出仍为 3.3 V。
  输入谷值 3.3 V，扣去 0.15 V 压差只能输出 3.15 V。 谷值须覆盖输出加压差；实际还查动态 PSRR 与温度。 准静态示意：目标 3.3 V，负载
  0.5 A，Ron=0.3 Ω，输入正弦 1 kHz。
en_prompt: Four causal snapshots, physical axes, model equations and explicit device
  boundaries. dropout ripple
---
