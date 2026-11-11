---
id: ch10-threshold-memory-v2
generator: svg-v2-scene
reference_policy: none
style_id: FA-029
layout_id: IG-015
color_ids:
- C-34
- C-32
source_facts:
- docs/p1-11-ch10.md#10.1
numbers:
- value: '0'
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
zh_prompt: RESET、TRIG、THRES 按优先级改变状态。RESET 有效时，即使 TRIG 低，输出也保持低。 释放 RESET；TRIG 低于
  3 V，优先置位输出。 TRIG 与 THRES 都在非动作区，锁存器保留高态。 TRIG 已释放，THRES 超过 6 V，输出复位并放电。 示意 9 V、标称
  3/6 V 门限；不在相等边界判定保证状态。
en_prompt: Four causal snapshots, explicit circuit conditions, physical axes and separate
  state lanes. threshold memory
---
