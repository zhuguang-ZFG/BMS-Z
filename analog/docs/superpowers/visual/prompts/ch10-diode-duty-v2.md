---
id: ch10-diode-duty-v2
generator: svg-v2-scene
reference_policy: none
style_id: FA-029
layout_id: IG-015
color_ids:
- C-34
- C-32
source_facts:
- docs/p1-11-ch10.md#10.4
numbers:
- value: '0'
  label: 示意
  reason: 物理模型的坐标刻度或节拍编号，不作为器件保证。
- value: '0.4'
  label: 示意
  reason: 物理模型的坐标刻度或节拍编号，不作为器件保证。
- value: '0.8'
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
- value: '50'
  label: 示意
  reason: 物理模型的坐标刻度或节拍编号，不作为器件保证。
- value: '55'
  label: 示意
  reason: 物理模型的坐标刻度或节拍编号，不作为器件保证。
- value: '60'
  label: 示意
  reason: 物理模型的坐标刻度或节拍编号，不作为器件保证。
zh_prompt: 二极管有压降，等电阻也不等于 50%。理想二极管绕过 RB，等电阻给出对称充放时间。 VF=0.3 V 时，充电目标降到 4.7 V，高段变长。
  VF=0.6 V 时，门限仍不变，充电目标只有 4.4 V。 这段扫描中二极管一直导通；压降更大需分段求解。 示意 5 V、RA=RB=10 kΩ、C=100
  nF；VD=0、恒定 VF。
en_prompt: Four causal snapshots, explicit circuit conditions, physical axes and separate
  state lanes. diode duty
---
