---
id: pilot-ff015-hero
kind: pilot-base-image
subject: 现象主图（鼓包电解电容与板上热区）
generator: imagegen-tool
model_note: 实际调用为本机图像生成工具；上游能力判定按库基线模型 gpt-image-2 解析。
reference_policy: name+style+traits
reference_image: none（三套候选均判定为不需垫图）
prompt_used: zh_prompt（en_prompt 为同一底图提示词的英译，供复用与审阅）
style_id: FF-015
style_name: Paper Sculpture Illustration
layout_id: IG-027
color_ids: C-30 / C-35 / C-26
anchor: '17.5 热与器件失效类'
source_facts:
- docs/p4-02-ch17.md#17.5 热与器件失效类
output: docs/superpowers/visual/reviews/pilot-2026-11-04/ch17-pilot-ff015-hero.png
overlay_origin: assets/figures/ch17-hot-spot-reading.svg
overlay_numbers: ['60°C', '10°C']
text_policy: 底图不含任何文字；判读句、数值、单位与电路符号一律由 SVG overlay 绘制。
status: generated
zh_prompt: |
  风格名称：Paper Sculpture Illustration（纸雕插画）。参考作者/风格名称：纸雕 · Paper Sculpture Illustration。主题色：象牙白（Ivory）纸层与石板灰（Slate Gray）阴影，柿子橙（Persimmon Orange）只用于故障处。核心风格特征：纸雕；场景只保留最必要的物件与动作；大面积留白。画面主题：多层手工纸片叠成的微距立体小景——一块由厚纸层叠切割的电路板台面上，立着一只纸雕电解电容，其顶部纸层微微鼓起、十字泄压槽撕开露出内层，旁边只保留两三件最必要的纸片器件与一条走线；真实微距立体柔光，纸边有手工切割与轻微毛边，层与层之间投下柔和大面积留白。画面内不出现任何文字、字母、数字、箭头或图例，标注位置留空给我们后续叠加图层。横版 4:3。
en_prompt: |
  Style name: Paper Sculpture Illustration. Theme colour: ivory paper layers with slate grey shadows, persimmon orange reserved for the fault. Core traits: paper sculpture; scenes reduced to the fewest necessary objects and actions; generous whitespace. Subject: a macro paper-cut diorama built from stacked hand-cut paper layers - on a board台面 of laminated thick paper stands a paper-sculpted electrolytic capacitor whose top layer is gently domed and whose cross-shaped vent is torn open to reveal an inner layer; only two or three other indispensable paper components and a single trace nearby; real macro three-dimensional soft light, hand-cut edges with a slight fuzz, soft shadows between layers, large areas of blank paper. No text, letters, digits, arrows or legend; label positions left blank for our overlay layer. Landscape 4:3.
---
