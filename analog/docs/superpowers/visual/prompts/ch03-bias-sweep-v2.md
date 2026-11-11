---
id: ch03-bias-sweep-v2
generator: svg-v2-scene
reference_policy: none
style_id: FA-029
layout_id: IG-015
color_ids:
- C-34
- C-32
source_facts:
- docs/p1-04-ch3.md#3.4
numbers:
- value: '0'
  label: 示意
  reason: 电流坐标轴原点。
zh_prompt: 贝塔从 100 扫到 600，共用电流刻度：固定偏置从 1 毫安升至 5.9 毫安的饱和限流；分压偏置从 0.866 升至 0.919 毫安。贝塔
  300 时分别为 3 与 0.908 毫安。温漂另算。
en_prompt: Sweep beta linearly. Plot both calculated collector currents on the same
  axes. Clip fixed bias at the load limit, preserve divider loading, and label the
  constant-VBE model. Use dashed and solid lines for grayscale readability.
---
