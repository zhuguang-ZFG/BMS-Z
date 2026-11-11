---
id: pilot-fa029-compare
kind: pilot-base-image
subject: 失效对比图底版（正常与鼓包电容对照）
generator: imagegen-tool
model_note: 实际调用为本机图像生成工具；上游能力判定按库基线模型 gpt-image-2 解析。
reference_policy: name+style
reference_image: none（三套候选均判定为不需垫图）
prompt_used: zh_prompt（en_prompt 为同一底图提示词的英译，供复用与审阅）
style_id: FA-029
style_name: Geometric Diagrammatic Narrative
layout_id: IG-004
color_ids: C-30 / C-31 / C-29
anchor: '17.2 放大与信号链类'
source_facts:
- docs/p4-02-ch17.md#17.2 放大与信号链类
output: docs/superpowers/visual/reviews/pilot-2026-11-04/ch17-pilot-fa029-compare.png
overlay_origin: assets/figures/ch17-virtual-short-test.svg
overlay_numbers: ['8mV']
text_policy: 底图不含任何文字；判读句、数值、单位与电路符号一律由 SVG overlay 绘制。
status: generated
zh_prompt: |
  风格名称：Geometric Diagrammatic Narrative（几何图式叙事）。参考作者/风格名称：Chris Ware · Geometric Diagrammatic Narrative。主题色：象牙白（Ivory）。画面主题：正常与失效对照的定量对比底版——画面由一条居中的细线竖向分成左右两个规整矩形区块。左块：一只外形平整的铝壳电解电容立于细线矩形电路板面上，其下方一条细密平稳的波形线。右块：同一只电容顶部鼓起、底部渗出少量液滴痕迹，其下方一条振幅大且锯齿状的波形线。全部由几何精密线条、规整矩形与克制三色调构成（象牙白底、佩恩灰线、赭石只用于右块异常处），大量留白。画面内不出现任何文字、字母、数字、箭头或图例标注，所有标注位置留空给我们后续叠加图层。横版 4:3。
en_prompt: |
  Style name: Geometric Diagrammatic Narrative (Chris Ware). Theme colour: Ivory. Subject: a normal-versus-failed comparison base plate - the picture split by a single centred hairline into two tidy rectangular fields. Left: an undomed aluminium electrolytic capacitor standing on a hairline board plane, a fine steady waveform line below it. Right: the same capacitor with a domed top and a few seepage marks at its base, a large-amplitude jagged waveform line below. All in precise geometric linework, tidy rectangles and a restrained three-colour scheme (ivory ground, Payne's grey lines, ochre only on the abnormal right field), generous whitespace. No text, letters, digits, arrows or legend; every label position left blank for our overlay layer. Landscape 4:3.
---
