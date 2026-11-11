---
id: pilot-fa029-hero
kind: pilot-base-image
subject: 现象主图（鼓包电解电容与板上热区）
generator: imagegen-tool
model_note: 实际调用为本机图像生成工具；上游能力判定按库基线模型 gpt-image-2 解析。
reference_policy: name+style
reference_image: none（三套候选均判定为不需垫图）
prompt_used: zh_prompt（en_prompt 为同一底图提示词的英译，供复用与审阅）
style_id: FA-029
style_name: Geometric Diagrammatic Narrative
layout_id: IG-027
color_ids: C-30 / C-31 / C-29
anchor: '17.5 热与器件失效类'
source_facts:
- docs/p4-02-ch17.md#17.5 热与器件失效类
output: docs/superpowers/visual/reviews/pilot-2026-11-04/ch17-pilot-fa029-hero.png
overlay_origin: assets/figures/ch17-hot-spot-reading.svg
overlay_numbers: ['60°C', '10°C']
text_policy: 底图不含任何文字；判读句、数值、单位与电路符号一律由 SVG overlay 绘制。
status: generated
zh_prompt: |
  风格名称：Geometric Diagrammatic Narrative（几何图式叙事）。参考作者/风格名称：Chris Ware · Geometric Diagrammatic Narrative。主题色：象牙白（Ivory）。画面主题：开关电源故障排查教材的现象主图——一块印刷电路板以规整矩形与细线构成的等距平面呈现，板上一只铝壳电解电容顶部微微鼓起、泄压槽裂开成十字，旁边排布若干矩形器件块与细线走线，用几何精密线条与信息图式留白组织画面，克制的三色调（象牙白纸底、佩恩灰墨线、少量赭石色只标出故障电容与其周围一块区域）。整幅画面安静、像一张城市图表，器件与环境全部由规整矩形和细线组成。画面内不出现任何文字、字母、数字、箭头标注或图例符号，所有标注区域保持空白留给我们后续叠加的图层。横版 4:3 构图，纸面质感。
en_prompt: |
  Style name: Geometric Diagrammatic Narrative (reference author: Chris Ware). Theme colour: Ivory. Subject: the phenomenon key image for a switching-power-supply troubleshooting chapter - a printed circuit board drawn as an isometric plane of tidy rectangles and hairlines; one aluminium electrolytic capacitor on the board has a slightly domed top with its score vent split into a cross; a few rectangular component blocks and hairline traces sit around it; everything organised with precise geometric linework and infographic-style whitespace in a restrained three-colour scheme (ivory paper, Payne's grey ink, a little ochre marking only the failed capacitor and one warm region around it); the whole picture quiet, like a city diagram. No text, letters, digits, arrows or legend anywhere in the image; all label areas left blank for our overlay layer. Landscape 4:3, paper texture.
---
