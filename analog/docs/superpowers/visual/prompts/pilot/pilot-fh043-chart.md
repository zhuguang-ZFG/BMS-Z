---
id: pilot-fh043-chart
kind: pilot-base-image
subject: 定量图底版（上电电流三条签名形状）
generator: imagegen-tool
model_note: 实际调用为本机图像生成工具；上游能力判定按库基线模型 gpt-image-2 解析。
reference_policy: name+style+traits
reference_image: none（三套候选均判定为不需垫图）
prompt_used: zh_prompt（en_prompt 为同一底图提示词的英译，供复用与审阅）
style_id: FH-043
style_name: Vintage Risograph and Silkscreen Print Illustration
layout_id: IG-009
color_ids: C-03 / C-21 / C-30
anchor: '17.7 上电即挂与保护类'
source_facts:
- docs/p4-02-ch17.md#17.7 上电即挂与保护类
output: docs/superpowers/visual/reviews/pilot-2026-11-04/ch17-pilot-fh043-chart.png
overlay_origin: assets/figures/ch17-power-on-current-signature.svg
overlay_numbers: []
text_policy: 底图不含任何文字；判读句、数值、单位与电路符号一律由 SVG overlay 绘制。
status: generated
zh_prompt: |
  风格名称：Vintage Risograph and Silkscreen Print Illustration。参考作者/风格名称：复古 Risograph 与丝网印刷插画。主题色：普鲁士蓝（Prussian Blue）与珊瑚粉（Coral Pink）双色套印在象牙白（Ivory）旧纸上。核心风格特征：暖象牙色纤维旧纸底；限色双色套印；大量纸白留白与大面积负空间；手绘轮廓、蚀刻排线、断续干笔、粗颗粒半调网点、点描与平涂墨块塑形；墨色浓淡不均、磨损边缘、纸纹透出、轻微双色套印错位与局部掉墨；构图简洁疏朗。画面主题：一张旧图纸质感的空白直角坐标网格，网格内三条手绘曲线——一条快速上冲后平缓回落、一条持续冲高保持高位、一条刚上冲便立刻断回零；两条用普鲁士蓝干笔线，一条用珊瑚红蚀刻排线，网格线断续干笔，纸白大面积留空。画面内不出现任何文字、字母、数字、刻度值、单位或图例，坐标轴标注区留空给我们后续叠加图层。横版 4:3。
en_prompt: |
  Style name: Vintage Risograph and Silkscreen Print Illustration. Theme colour: Prussian Blue and Coral Pink overprint on aged ivory paper. Core traits: warm ivory fibrous paper, limited two-colour overprint, wide paper-white negative space, hand-drawn outlines, etched hatching, broken dry-brush lines, coarse halftone dots, flat ink blocks, uneven ink, worn edges, visible paper grain, slight misregistration, sparse composition. Subject: a blank right-angled grid with the texture of an old drawing sheet holding three hand-drawn curves - one surging then easing back, one holding high, one starting and snapping straight back to zero; two drawn in Prussian blue dry-brush lines, one in coral-red etched hatching; grid lines broken and dry, most of the paper left white. No text, letters, digits, tick values, units or legend; axis annotation areas left blank for our overlay layer. Landscape 4:3.
---
