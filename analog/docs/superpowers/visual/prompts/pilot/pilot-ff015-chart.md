---
id: pilot-ff015-chart
kind: pilot-base-image
subject: 定量图底版（上电电流三条签名形状）
generator: imagegen-tool
model_note: 实际调用为本机图像生成工具；上游能力判定按库基线模型 gpt-image-2 解析。
reference_policy: name+style+traits
reference_image: none（三套候选均判定为不需垫图）
prompt_used: zh_prompt（en_prompt 为同一底图提示词的英译，供复用与审阅）
style_id: FF-015
style_name: Paper Sculpture Illustration
layout_id: IG-009
color_ids: C-30 / C-35 / C-26
anchor: '17.7 上电即挂与保护类'
source_facts:
- docs/p4-02-ch17.md#17.7 上电即挂与保护类
output: docs/superpowers/visual/reviews/pilot-2026-11-04/ch17-pilot-ff015-chart.png
overlay_origin: assets/figures/ch17-power-on-current-signature.svg
overlay_numbers: []
text_policy: 底图不含任何文字；判读句、数值、单位与电路符号一律由 SVG overlay 绘制。
status: generated
zh_prompt: |
  风格名称：Paper Sculpture Illustration（纸雕插画）。参考作者/风格名称：纸雕 · Paper Sculpture Illustration。主题色：象牙白（Ivory）纸层与石板灰（Slate Gray）阴影，柿子橙（Persimmon Orange）只用于重点曲线。核心风格特征：纸雕；场景只保留最必要的物件与动作；大面积留白。画面主题：一张由象牙白纸层铺成的空白坐标台面，网格以浅石板灰压印线刻出；三条曲线以三条不同高度的剪纸长条立在纸面上——一条先冲高再平缓回落、一条持续保持在高位、一条刚起来便立刻断回零，剪纸边缘有手工切痕与柔和阴影，重点那条为柿子橙纸片；真实微距立体柔光，四周大面积留白。画面内不出现任何文字、字母、数字、刻度值、单位或图例，坐标轴标注区留空给我们后续叠加图层。横版 4:3。
en_prompt: |
  Style name: Paper Sculpture Illustration. Theme colour: ivory paper layers, slate grey shadows, persimmon orange for the key curve only. Core traits: paper sculpture; fewest necessary objects; broad whitespace. Subject: a blank plotting tabletop paved with ivory paper layers, the grid embossed in pale slate grey; three curves as three cut-paper strips standing at different heights on the paper - one rising then easing back, one held high, one starting and snapping back to zero; paper edges show hand-cut marks and soft shadows, the key strip in persimmon orange; real macro soft light, wide whitespace around. No text, letters, digits, tick values, units or legend; axis annotation areas left blank for our overlay layer. Landscape 4:3.
---
