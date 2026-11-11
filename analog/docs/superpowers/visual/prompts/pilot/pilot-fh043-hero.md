---
id: pilot-fh043-hero
kind: pilot-base-image
subject: 现象主图（鼓包电解电容与板上热区）
generator: imagegen-tool
model_note: 实际调用为本机图像生成工具；上游能力判定按库基线模型 gpt-image-2 解析。
reference_policy: name+style+traits
reference_image: none（三套候选均判定为不需垫图）
prompt_used: zh_prompt（en_prompt 为同一底图提示词的英译，供复用与审阅）
style_id: FH-043
style_name: Vintage Risograph and Silkscreen Print Illustration
layout_id: IG-027
color_ids: C-03 / C-21 / C-30
anchor: '17.5 热与器件失效类'
source_facts:
- docs/p4-02-ch17.md#17.5 热与器件失效类
output: docs/superpowers/visual/reviews/pilot-2026-11-04/ch17-pilot-fh043-hero.png
overlay_origin: assets/figures/ch17-hot-spot-reading.svg
overlay_numbers: ['60°C', '10°C']
text_policy: 底图不含任何文字；判读句、数值、单位与电路符号一律由 SVG overlay 绘制。
status: generated
zh_prompt: |
  风格名称：Vintage Risograph and Silkscreen Print Illustration。参考作者/风格名称：复古 Risograph 与丝网印刷插画。主题色：普鲁士蓝（Prussian Blue）与珊瑚粉（Coral Pink）双色套印在象牙白（Ivory）旧纸上。核心风格特征：暖象牙色纤维旧纸底；深普鲁士蓝与灰珊瑚红限色双色套印；大量纸白留白与大面积负空间；手绘轮廓、蚀刻排线、断续干笔、粗颗粒半调网点、点描与平涂墨块塑形；墨色浓淡不均、磨损边缘、纸纹透出、轻微双色套印错位与局部掉墨；构图简洁疏朗，主体突出，背景层叠概括；20世纪中期复古旅行宣传插画与私人速写怀旧文学感。画面主题：一块旧电源板上的电解电容，顶部鼓起、泄压槽裂开，周围是层叠概括的铜箔与器件块面，普鲁士蓝为主墨、珊瑚红只落在故障电容一处，纸纹与半调网点清楚可见。画面内不出现任何文字、字母、数字、箭头或图例，标注位置全部留空给我们后续叠加图层。横版 4:3。
en_prompt: |
  Style name: Vintage Risograph and Silkscreen Print Illustration. Theme colour: Prussian Blue with Coral Pink two-colour overprint on aged ivory paper. Core traits: warm ivory fibrous old-paper ground; limited two-colour risograph overprint; large areas of paper-white negative space; hand-drawn outlines, etched hatching, broken dry-brush strokes, coarse halftone dots, stippling and flat ink blocks; uneven ink density, worn edges, paper grain showing through, slight misregistration and local ink drop-out; sparse mid-century travel-poster composition with a nostalgic private-sketch feeling. Subject: an electrolytic capacitor on an old power board, top domed, score vent cracked, surrounded by summarised layered copper shapes and component blocks; Prussian blue as the main ink, coral red on the failed capacitor only, paper grain and halftone dots clearly visible. No text, letters, digits, arrows or legend; every label position left blank for our overlay layer. Landscape 4:3.
---
