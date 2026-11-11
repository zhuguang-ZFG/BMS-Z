---
id: ch10-reset-ramp-v2
generator: svg-v2-scene
reference_policy: none
style_id: FA-029
layout_id: IG-015
color_ids:
- C-34
- C-32
source_facts:
- docs/p1-11-ch10.md#10.5
numbers:
- value: '0'
  label: 示意
  reason: 物理模型的坐标刻度或节拍编号，不作为器件保证。
- value: '0.7'
  label: 示意
  reason: 物理模型的坐标刻度或节拍编号，不作为器件保证。
- value: '1'
  label: 示意
  reason: 物理模型的坐标刻度或节拍编号，不作为器件保证。
- value: '2'
  label: 示意
  reason: 物理模型的坐标刻度或节拍编号，不作为器件保证。
- value: '3'
  label: 示意
  reason: 物理模型的坐标刻度或节拍编号，不作为器件保证。
- value: '4'
  label: 示意
  reason: 物理模型的坐标刻度或节拍编号，不作为器件保证。
- value: '25'
  label: 示意
  reason: 物理模型的坐标刻度或节拍编号，不作为器件保证。
- value: '50'
  label: 示意
  reason: 物理模型的坐标刻度或节拍编号，不作为器件保证。
zh_prompt: RESET 门限低，RC 常数不是复位保持时间。RC=0.47 s，但复位门限并不是 63.2% 的电源。 越过 0.3 V 只需约 11.9
  ms。 越过 0.7 V 约 28.3 ms，越过 1 V 约 40.9 ms。 双极 RESET 不是理想高阻；精确延时还须考虑脚电流与慢沿。 示意理想高阻
  RESET：12 V、100 kΩ、4.7 µF；真实脚电流另计。
en_prompt: Four causal snapshots, explicit circuit conditions, physical axes and separate
  state lanes. reset ramp
---
