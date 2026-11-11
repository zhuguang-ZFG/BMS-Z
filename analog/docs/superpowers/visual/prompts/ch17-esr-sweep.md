---
id: ch17-esr-sweep
generator: svg-v2-scene
reference_policy: none
numbers:
- 100Hz
- 400mV
- 三成
- value: 0.1Ω
  label: 示意
  reason: 扫描起点只用于呈现变化过程，不是正文测量值或器件保证值。
- value: 3Ω
  label: 示意
  reason: 扫描终点只用于呈现变化过程，不是正文测量值或器件保证值。
zh_prompt: |
  风格名称：几何图式叙事。主题色：象牙白（Ivory）、佩恩灰（Payne's grey）、赭石（Ochre）。
  动画类型：A3 参数扫描（显当前值+工作点+方向）。节拍 5：扫描对象 → 纹波爬升 → 内部生热 → 容量蒸发 → 闭环（结论停留）。
  画面：左侧大电解电容符号卡（引线+平行板+极性标，标签「输出大电解」）；右侧 100Hz 纹波波形窗从细纹爬升到 400mV 大摆幅（红色标注）；温度计升起（内部生热）；容量条从 100% 缩到标称三成（紫色）；结论帧绿色闭环卡「纹波电流生热 → 热又推高 ESR → ESR 再抬纹波 → 更热」+「量 100Hz 纹波幅度 = 免费的 ESR 表——先问频率，再问幅度」。
en_prompt: |
  Style name: Geometric Diagrammatic Narrative. Theme color: Ivory, Payne's grey, Ochre.
  Animation type: A3 parameter sweep (show current value, operating point, direction). Five beats: subject → ripple climbs → internal heating → capacity evaporates → closed loop (hold final frame).
  Canvas: left card draws a bulk electrolytic (leads, plates, polarity mark, "output bulk cap"); the right 100Hz ripple window grows from hairline to a fat 400mV sine (red callout); a thermometer rises (internal heating); the capacity bar shrinks from 100% to a third of rating (purple); the final green loop card reads "ripple current heats → heat raises ESR → ESR lifts ripple → hotter still" plus "read the 100Hz ripple amplitude = a free ESR meter — frequency first, amplitude second".
  beats: [扫描对象, 纹波爬升, 内部生热, 容量蒸发, 闭环]
  duration: 8.0s
  reduced_motion: assets/svg-v2/ch17-esr-sweep-static.svg
  storyboard: assets/svg-v2/ch17-esr-sweep-storyboard.svg
---
