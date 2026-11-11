---
id: ch07-window-logic-v2
generator: svg-v2-scene
reference_policy: none
style_id: FA-029
layout_id: IG-013
color_ids:
- C-34
- C-32
source_facts:
- docs/p1-08-ch7.md#7.2
numbers:
- value: '0'
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
zh_prompt: 窗口内放行，要先接对两路比较极性。欠压路：被测电压进正端，1.5 V 基准进负端。 过压路：1.8 V 基准进正端，被测电压进负端。 欠压或过压时，任一路输出管都能拉低公共节点。
  只有两路都松手，上拉才能给出窗口内的高电平。 电池减半分压；理想门限 3.0 / 3.6 V，等于门限时不保证状态。
en_prompt: Four causal snapshots with exact comparator polarity, physical units and
  explicit model boundary. window logic
---
