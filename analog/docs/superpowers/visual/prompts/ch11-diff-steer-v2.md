---
id: ch11-diff-steer-v2
generator: svg-v2-scene
reference_policy: none
style_id: FA-029
layout_id: IG-015
color_ids:
- C-34
- C-32
source_facts:
- docs/p2-01-ch11.md#11.2
numbers:
- value: '-60'
  label: 示意
  reason: 教学模型的坐标或节拍编号，按正文假设计算，不作为器件保证。
- value: '0'
  label: 示意
  reason: 教学模型的坐标或节拍编号，按正文假设计算，不作为器件保证。
- value: '0.5'
  label: 示意
  reason: 教学模型的坐标或节拍编号，按正文假设计算，不作为器件保证。
- value: '1'
  label: 示意
  reason: 教学模型的坐标或节拍编号，按正文假设计算，不作为器件保证。
- value: '2'
  label: 示意
  reason: 教学模型的坐标或节拍编号，按正文假设计算，不作为器件保证。
- value: '3'
  label: 示意
  reason: 教学模型的坐标或节拍编号，按正文假设计算，不作为器件保证。
- value: '4'
  label: 示意
  reason: 教学模型的坐标或节拍编号，按正文假设计算，不作为器件保证。
- value: '60'
  label: 示意
  reason: 教学模型的坐标或节拍编号，按正文假设计算，不作为器件保证。
- value: '0.177'
  label: 示意
  reason: 匹配 BJT 的 tanh 电流分配模型，在该节拍指定差模电压处求值，单位 mA，显示三位小数。
- value: '0.823'
  label: 示意
  reason: 匹配 BJT 的 tanh 电流分配模型，在该节拍指定差模电压处求值，单位 mA，显示三位小数。
- value: '0.500'
  label: 示意
  reason: 匹配 BJT 的 tanh 电流分配模型，在该节拍指定差模电压处求值，单位 mA，显示三位小数。
- value: '0.500'
  label: 示意
  reason: 匹配 BJT 的 tanh 电流分配模型，在该节拍指定差模电压处求值，单位 mA，显示三位小数。
- value: '0.683'
  label: 示意
  reason: 匹配 BJT 的 tanh 电流分配模型，在该节拍指定差模电压处求值，单位 mA，显示三位小数。
- value: '0.317'
  label: 示意
  reason: 匹配 BJT 的 tanh 电流分配模型，在该节拍指定差模电压处求值，单位 mA，显示三位小数。
- value: '0.823'
  label: 示意
  reason: 匹配 BJT 的 tanh 电流分配模型，在该节拍指定差模电压处求值，单位 mA，显示三位小数。
- value: '0.177'
  label: 示意
  reason: 匹配 BJT 的 tanh 电流分配模型，在该节拍指定差模电压处求值，单位 mA，显示三位小数。
zh_prompt: 差分电压重新分配同一份尾电流。负差模把电流分给右管，总量仍是 1 mA。 零差模时两管各得 0.5 mA。 各输入 ±10 mV 对应差模 20
  mV，已偏离直线近似。 大差模让一边接近独占，不能无限线性放大。 示意匹配 BJT，集电流和 1 mA，VT=26 mV；忽略基流与 Early 效应。
en_prompt: Four causal model frames with physical axes, explicit conditions, readable
  print and dashed reference curves. diff steer
---
