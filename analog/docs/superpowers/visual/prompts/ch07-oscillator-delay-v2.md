---
id: ch07-oscillator-delay-v2
generator: svg-v2-scene
reference_policy: none
style_id: FA-029
layout_id: IG-015
color_ids:
- C-34
- C-32
source_facts:
- docs/p1-08-ch7.md#7.3
numbers:
- value: '0'
  label: 示意
  reason: 教学模型坐标刻度和节拍序号，不是器件额定。
- value: '0.25'
  label: 示意
  reason: 教学模型坐标刻度和节拍序号，不是器件额定。
- value: '0.75'
  label: 示意
  reason: 教学模型坐标刻度和节拍序号，不是器件额定。
- value: '1'
  label: 示意
  reason: 教学模型坐标刻度和节拍序号，不是器件额定。
- value: '2'
  label: 示意
  reason: 教学模型坐标刻度和节拍序号，不是器件额定。
- value: '3'
  label: 示意
  reason: 教学模型坐标刻度和节拍序号，不是器件额定。
- value: '4'
  label: 示意
  reason: 教学模型坐标刻度和节拍序号，不是器件额定。
- value: '25'
  label: 示意
  reason: 教学模型坐标刻度和节拍序号，不是器件额定。
- value: '50'
  label: 示意
  reason: 教学模型坐标刻度和节拍序号，不是器件额定。
zh_prompt: 传播等待期间，电容还在继续充放电。无延迟时 T=2RC ln3，约 21.972 µs。 越过门限后再等 1.3 µs，电容继续向电源轨运动。
  实际峰谷越过 3/4 与 1/4，下半周期路程也改变。 T=2[d+RC ln(4−exp(−d/RC))]，不能只加 2d。 理想推挽；阈值 1/4、3/4
  电源，RC=10 µs，双向延迟 1.3 µs。
en_prompt: Four causal snapshots with exact comparator polarity, physical units and
  explicit model boundary. oscillator delay
---
