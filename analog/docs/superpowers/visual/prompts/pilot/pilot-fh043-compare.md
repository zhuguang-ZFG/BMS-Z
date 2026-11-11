---
id: pilot-fh043-compare
kind: pilot-base-image
subject: 失效对比图底版（正常与鼓包电容对照）
generator: imagegen-tool
model_note: 实际调用为本机图像生成工具；上游能力判定按库基线模型 gpt-image-2 解析。
reference_policy: name+style+traits
reference_image: none（三套候选均判定为不需垫图）
prompt_used: zh_prompt（en_prompt 为同一底图提示词的英译，供复用与审阅）
style_id: FH-043
style_name: Vintage Risograph and Silkscreen Print Illustration
layout_id: IG-004
color_ids: C-03 / C-21 / C-30
anchor: '17.2 放大与信号链类'
source_facts:
- docs/p4-02-ch17.md#17.2 放大与信号链类
output: docs/superpowers/visual/reviews/pilot-2026-11-04/ch17-pilot-fh043-compare.png
overlay_origin: assets/figures/ch17-virtual-short-test.svg
overlay_numbers: ['8mV']
text_policy: 底图不含任何文字；判读句、数值、单位与电路符号一律由 SVG overlay 绘制。
status: generated
zh_prompt: |
  风格名称：Vintage Risograph and Silkscreen Print Illustration。参考作者/风格名称：复古 Risograph 与丝网印刷插画。主题色：普鲁士蓝（Prussian Blue）与珊瑚粉（Coral Pink）双色套印在象牙白（Ivory）旧纸上。核心风格特征：暖象牙色纤维旧纸底；限色双色套印；大量纸白留白与大面积负空间；手绘轮廓、蚀刻排线、断续干笔、粗颗粒半调网点、点描与平涂墨块塑形；墨色浓淡不均、磨损边缘、纸纹透出、轻微双色套印错位与局部掉墨；构图简洁疏朗，主体突出。画面主题：左右对照的两只电解电容——左侧电容外形平整、普鲁士蓝平涂墨块塑形，下方一条细密平稳的波形线；右侧电容顶部鼓起、底部渗液痕迹、珊瑚红套印，下方一条振幅大的锯齿波形线；中间一条断续干笔竖线分隔，大面积纸白留白。画面内不出现任何文字、字母、数字、箭头或图例，标注位置留空给我们后续叠加图层。横版 4:3。
en_prompt: |
  Style name: Vintage Risograph and Silkscreen Print Illustration. Theme colour: Prussian Blue and Coral Pink overprint on aged ivory paper. Core traits: warm ivory fibrous paper, limited two-colour overprint, wide negative space, hand outlines, etched hatching, dry-brush breaks, coarse halftone dots, flat ink blocks, uneven ink, worn edges, paper grain, slight misregistration, sparse composition. Subject: two electrolytic capacitors side by side - the left one undomed, shaped with Prussian blue flat ink blocks, a fine steady waveform beneath; the right one domed with seepage stains at the base in coral-red overprint, a large-amplitude jagged waveform beneath; a single broken dry-brush vertical rule between them, wide paper-white margins. No text, letters, digits, arrows or legend; label positions left blank for our overlay layer. Landscape 4:3.
---
