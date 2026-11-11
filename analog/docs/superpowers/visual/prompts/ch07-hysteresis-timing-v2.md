---
id: ch07-hysteresis-timing-v2
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
- value: '2.3'
  label: 示意
  reason: 教学模型坐标刻度和节拍序号，不是器件额定。
- value: '2.5'
  label: 示意
  reason: 教学模型坐标刻度和节拍序号，不是器件额定。
- value: '2.727'
  label: 示意
  reason: 教学模型坐标刻度和节拍序号，不是器件额定。
- value: '3'
  label: 示意
  reason: 教学模型坐标刻度和节拍序号，不是器件额定。
- value: '4'
  label: 示意
  reason: 教学模型坐标刻度和节拍序号，不是器件额定。
- value: '200'
  label: 示意
  reason: 教学模型坐标刻度和节拍序号，不是器件额定。
- value: '500'
  label: 示意
  reason: 教学模型坐标刻度和节拍序号，不是器件额定。
zh_prompt: 相对中点的延时，只跨半个对称窗口。无迟滞参考门限 2.5 V，输入在 200 s 到达。 迟滞上阈值 2.727 V，在约 427.3 s 才翻转。
  相对 2.5 V 的推迟是 227.3 s，不是 454.5 s。 只有拿下阈值作起点，时间差才对应整个窗口。 初态输出高；输入由 2.3 V 以 1 mV/s
  上行，忽略传播与 RC 延迟。
en_prompt: Four causal snapshots with exact comparator polarity, physical units and
  explicit model boundary. hysteresis timing
---
