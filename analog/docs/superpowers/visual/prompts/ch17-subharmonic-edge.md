---
id: ch17-subharmonic-edge
generator: svg-v2-scene
reference_policy: none
numbers:
- 50%
zh_prompt: |
  风格名称：几何图式叙事。主题色：象牙白（Ivory）、佩恩灰（Payne's grey）、赭石（Ochre）。
  动画类型：A4 失效边界（显当前值+工作点+方向）。节拍 6：旋钮在40% → 推过50% → 一宽一窄 → 纹波半频 → 斜坡补偿 → 边界指纹（结论停留）。
  画面：左上占空比滑标从 40%（蓝）推到 55%（赭石），滑轨上有红色「50% 临界」虚线；右上 SW 波形窗：规整窄脉冲（蓝）→ 变宽（赭石）→ 一宽一窄交替、周期翻倍（红）；中部纹波频谱窗出现 f_sw/2 分量（紫）；左下斜坡补偿卡「下斜坡压回放大系数 < 1，人为叠加抵消逐周期放大」；结论帧绿色卡「边界指纹：占空比一过 50% 就振，降到 50% 以下就好——一分钟验证：调高输入电压（减小占空比）看振荡是否消失；消失即次谐波振荡，加斜坡补偿或降低环路增益」。
en_prompt: |
  Style name: Geometric Diagrammatic Narrative. Theme color: Ivory, Payne's grey, Ochre.
  Animation type: A4 failure boundary (current value, operating point, direction). Six beats: knob at 40% → pushed past 50% → wide-narrow → half-frequency ripple → slope compensation → boundary fingerprint (hold final frame).
  Canvas: a duty-cycle slider rides from 40% (blue) to 55% (ochre) past a red dashed "50% critical" mark; the SW window morphs from tidy narrow pulses (blue) to stretched pulses (ochre) to alternating wide/narrow, period doubled (red); a mid-panel ripple spectrum grows an f_sw/2 component (purple); a blue card explains slope compensation ("a人为 down-ramp pushes the amplification factor below 1 — injected to cancel the per-cycle growth"); the final green card states the fingerprint: "past 50% it oscillates, back under 50% it calms — one-minute test: raise the input voltage (shrink the duty cycle) and watch the oscillation vanish; if it does, add slope compensation or cut loop gain."
  beats: [旋钮在40%, 推过50%, 一宽一窄, 纹波半频, 斜坡补偿, 边界指纹]
  duration: 9.5s
  reduced_motion: assets/svg-v2/ch17-subharmonic-edge-static.svg
  storyboard: assets/svg-v2/ch17-subharmonic-edge-storyboard.svg
---
