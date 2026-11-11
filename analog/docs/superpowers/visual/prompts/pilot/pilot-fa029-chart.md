---
id: pilot-fa029-chart
kind: pilot-base-image
subject: 定量图底版（上电电流三条签名形状）
generator: imagegen-tool
model_note: 实际调用为本机图像生成工具；上游能力判定按库基线模型 gpt-image-2 解析。
reference_policy: name+style
reference_image: none（三套候选均判定为不需垫图）
prompt_used: zh_prompt（en_prompt 为同一底图提示词的英译，供复用与审阅）
style_id: FA-029
style_name: Geometric Diagrammatic Narrative
layout_id: IG-009
color_ids: C-30 / C-31 / C-29
anchor: '17.7 上电即挂与保护类'
source_facts:
- docs/p4-02-ch17.md#17.7 上电即挂与保护类
output: docs/superpowers/visual/reviews/pilot-2026-11-04/ch17-pilot-fa029-chart.png
overlay_origin: assets/figures/ch17-power-on-current-signature.svg
overlay_numbers: []
text_policy: 底图不含任何文字；判读句、数值、单位与电路符号一律由 SVG overlay 绘制。
status: generated
zh_prompt: |
  风格名称：Geometric Diagrammatic Narrative（几何图式叙事）。参考作者/风格名称：Chris Ware · Geometric Diagrammatic Narrative。主题色：象牙白（Ivory）。画面主题：开关电源上电电流判读的定量图底版——象牙白纸面上是一张由细线绘制的空白直角坐标网格，网格内三条清晰的曲线形状：一条快速上冲后平缓回落到基线，一条持续冲高保持在高位，一条刚上冲便立刻断回零；曲线用细线描边、局部以赭石色填充一小段以示差别，其余保持佩恩灰墨线。几何精密线条、规整矩形、大面积信息图式留白。画面内不出现任何文字、字母、数字、刻度值、单位或图例，坐标轴标签区域留空给我们后续叠加图层。横版 4:3。
en_prompt: |
  Style name: Geometric Diagrammatic Narrative (Chris Ware). Theme colour: Ivory. Subject: the base plate for a quantitative chart reading power-on current - on ivory paper, a blank right-angled grid drawn in hairlines holding three clear curve shapes: one that shoots up fast and eases back down to the baseline, one that stays high, one that leaps up and snaps straight back to zero; curves outlined in fine lines, one short segment filled with ochre for contrast, the rest in Payne's grey ink; precise geometric linework, tidy rectangles, broad infographic whitespace. No text, letters, digits, tick values, units or legend; axis label areas left blank for our overlay layer. Landscape 4:3.
---
