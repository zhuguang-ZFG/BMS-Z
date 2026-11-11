---
id: ch10-recovery-gap-v2
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
- value: '1'
  label: 示意
  reason: 物理模型的坐标刻度或节拍编号，不作为器件保证。
- value: '1.5'
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
- value: '5'
  label: 示意
  reason: 物理模型的坐标刻度或节拍编号，不作为器件保证。
zh_prompt: 下一次触发，要继承电容尚未放完的电压。输出回低后电容经放电路径衰减，不能瞬间清零。 恢复仅 1 ms 后仍有约 1.228 V，下一拍被缩短。
  等 5 ms 后残压约 27.3 mV，下一拍约 1.093 s。 图的后两拍切换为下一拍脉宽；用允许误差反推最小间隔。 示意 5 V、R=100 kΩ、C=10
  µF；放电等效 100 Ω，保留电源馈入。
en_prompt: Four causal snapshots, explicit circuit conditions, physical axes and separate
  state lanes. recovery gap
---
