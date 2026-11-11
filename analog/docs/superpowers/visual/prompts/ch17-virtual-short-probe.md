---
id: ch17-virtual-short-probe
generator: svg-v2-scene
reference_policy: none
numbers:
- 8mV
zh_prompt: |
  风格名称：几何图式叙事。主题色：象牙白（Ivory）、佩恩灰（Payne's grey）、赭石（Ochre）。
  动画类型：A5 操作演示。节拍 5：认脚 → 量V− → 量V+ → 算压差 → 判读（结论停留）。
  画面：中央反相级画出信号经 Rin 接到反相端、输出经 Rf 回到反相端的负反馈支路；节点相接、引线在图外绕行，不误接同相端。示意只用于逐线核对，不能代替实际通断测量。右上万用表卡按同一静态工况依次保留 2.500V、2.508V；赭石压差卡计算 2.508 − 2.500 = 8mV，明确这是读数而非合格线。结论分三步：先核供电、共模、输出摆幅和反馈通断；按器件失调、开环增益与仪器误差预算压差；再用小信号核对输出响应。不得把小压差直接判成运放无故障，也不得用通用几十 mV 阈值替代器件与工况判断。各拍与结论共用几何，终帧保留读数、反馈支路与条件判读。
en_prompt: |
  Style name: Geometric Diagrammatic Narrative. Theme color: Ivory, Payne's grey, Ochre.
  Animation type: A5 procedure demo. Five beats: identify pins → probe V− → probe V+ → difference → verdict (hold final frame).
  Canvas: draw an inverting stage with the signal passing through Rin to the inverting input, and the output returning through Rf to that same node. Route the feedback wire outside the amplifier; show real junctions and never connect it to the non-inverting input. The drawing is a continuity-check guide, not proof of measured continuity. Retain both DMM readings, 2.500V and 2.508V, under one unchanged operating condition. An ochre card computes 2.508 − 2.500 = 8mV and labels this a reading, not an acceptance limit. The final frame separates prerequisites, the offset/open-loop-gain/instrument-error budget, and a small-signal output-response check. Do not infer a healthy amplifier from a small input difference or use a universal tens-of-millivolts threshold. Retain the feedback circuit and readings in the final frame and print variants.
  beats: [认脚, 量V−, 量V+, 算压差, 判读]
  duration: 7.5s
  reduced_motion: assets/svg-v2/ch17-virtual-short-probe-static.svg
  storyboard: assets/svg-v2/ch17-virtual-short-probe-storyboard.svg
---
