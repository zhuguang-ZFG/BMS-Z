---
id: pilot-ff015-compare
kind: pilot-base-image
subject: 失效对比图底版（正常与鼓包电容对照）
generator: imagegen-tool
model_note: 实际调用为本机图像生成工具；上游能力判定按库基线模型 gpt-image-2 解析。
reference_policy: name+style+traits
reference_image: none（三套候选均判定为不需垫图）
prompt_used: zh_prompt（en_prompt 为同一底图提示词的英译，供复用与审阅）
style_id: FF-015
style_name: Paper Sculpture Illustration
layout_id: IG-004
color_ids: C-30 / C-35 / C-26
anchor: '17.2 放大与信号链类'
source_facts:
- docs/p4-02-ch17.md#17.2 放大与信号链类
output: docs/superpowers/visual/reviews/pilot-2026-11-04/ch17-pilot-ff015-compare.png
overlay_origin: assets/figures/ch17-virtual-short-test.svg
overlay_numbers: ['8mV']
text_policy: 底图不含任何文字；判读句、数值、单位与电路符号一律由 SVG overlay 绘制。
status: generated
zh_prompt: |
  风格名称：Paper Sculpture Illustration（纸雕插画）。参考作者/风格名称：纸雕 · Paper Sculpture Illustration。主题色：象牙白（Ivory）纸层与石板灰（Slate Gray）阴影，柿子橙（Persimmon Orange）只用于右侧异常处。核心风格特征：纸雕；场景只保留最必要的物件与动作；大面积留白。画面主题：同一层纸台面上的左右两只纸雕电解电容对照——左侧外形平整、纸层干净套叠，下方一条细密平稳的剪纸波形条；右侧顶部鼓起、底部渗出几片 torn 纸边示意漏液，下方一条振幅大的锯齿剪纸波形条并染成柿子橙；中间只用一条压印的浅线分隔，大面积留白，真实微距立体柔光与手工纸边毛糙质感。画面内不出现任何文字、字母、数字、箭头或图例，标注位置留空给我们后续叠加图层。横版 4:3。
en_prompt: |
  Style name: Paper Sculpture Illustration. Theme colour: ivory paper layers, slate grey shadows, persimmon orange on the right-hand fault only. Core traits: paper sculpture; fewest necessary objects; broad whitespace. Subject: two paper-sculpted electrolytic capacitors compared on the same paper tabletop - left undomed with clean nested paper layers and a fine, steady cut-paper waveform strip below; right domed at the top with a few torn paper strips at the base suggesting leakage and a wide jagged cut-paper waveform strip dyed persimmon orange below; separated only by a pale embossed line, generous whitespace, real macro soft light and fuzzy hand-torn paper edges. No text, letters, digits, arrows or legend; label positions left blank for our overlay layer. Landscape 4:3.
---
