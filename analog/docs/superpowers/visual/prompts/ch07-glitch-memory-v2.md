---
id: ch07-glitch-memory-v2
generator: svg-v2-scene
reference_policy: none
style_id: FA-029
layout_id: IG-015
color_ids:
- C-34
- C-32
source_facts:
- docs/p1-08-ch7.md#7.5
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
- value: '2.2'
  label: 示意
  reason: 教学模型坐标刻度和节拍序号，不是器件额定。
- value: '2.5'
  label: 示意
  reason: 教学模型坐标刻度和节拍序号，不是器件额定。
- value: '2.8'
  label: 示意
  reason: 教学模型坐标刻度和节拍序号，不是器件额定。
- value: '3'
  label: 示意
  reason: 教学模型坐标刻度和节拍序号，不是器件额定。
- value: '4'
  label: 示意
  reason: 教学模型坐标刻度和节拍序号，不是器件额定。
- value: '6'
  label: 示意
  reason: 教学模型坐标刻度和节拍序号，不是器件额定。
- value: '12'
  label: 示意
  reason: 教学模型坐标刻度和节拍序号，不是器件额定。
zh_prompt: 毛刺会不会触发，要看离当前门限多远。输入基线 2.4 V；200 mV 毛刺顶到 2.6 V。 300 mV 毛刺到 2.7 V，仍比上阈值低约
  27 mV。 400 mV 毛刺到 2.8 V，输出翻低且回到基线仍保持。 输入再跌到下阈以下才翻高；窗口不是任意毛刺保证。 反相迟滞理想状态模型；上阈 2.727
  V、下阈 2.273 V，初始高。
en_prompt: Four causal snapshots with exact comparator polarity, physical units and
  explicit model boundary. glitch memory
---
