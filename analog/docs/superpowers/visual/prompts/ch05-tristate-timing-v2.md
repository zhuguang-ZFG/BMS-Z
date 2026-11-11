---
id: ch05-tristate-timing-v2
generator: svg-v2-scene
reference_policy: none
style_id: FA-029
layout_id: IG-015
color_ids:
- C-34
- C-32
source_facts:
- docs/p1-06-ch5.md#5.4
numbers:
- value: '0'
  label: 示意
  reason: 示意模型坐标刻度或归一化时间；不是器件保证值。
- value: '60'
  label: 示意
  reason: 示意模型坐标刻度或归一化时间；不是器件保证值。
zh_prompt: 三态驱动条共用纳秒轴。旧器件最晚三十纳秒释放，新器件使能最小十纳秒；指令间隔五纳秒可重叠十五纳秒，间隔三十纳秒则留十纳秒空档。
en_prompt: Compare actual drive intervals using worst-case disable maximum and enable
  minimum. Distinguish command separation, drive overlap and legal undriven time.
---
