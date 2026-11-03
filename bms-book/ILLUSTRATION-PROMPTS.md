# R3 插画提示词存档（handraw-style）

本文件是 handdraw-style-prompter 在 R3 产出的**提示词侧留档**，用来在后端恢复后重出 raster 版本。
书内实际入库的是同画风的矢量版本（`bms-book/assets/concepts/01-cell-workshop.svg`、
`07-tick-guard.svg`，封面 `docs/public/illustrations/bms-scrapbook.svg`）。

## 为什么没走 raster

- 2026-11-03 探测：本机生图通道只到 OpenAI 兼容网关 `http://localhost:3002/v1`（new-api）。
  目录里图像模型共 5 个：`grok-imagine-image`、`grok-imagine-image-2.0`、`grok-imagine-image-edit`、
  `grok-imagine-image-lite`、`minimax-image`。
- 实测：`grok-imagine-image` 155 s 后 HTTP 524，`minimax-image` 126 s 后 HTTP 524（上游超时）；
  `grok-imagine-image-2.0`、`grok-imagine-image-lite` 直接 503 `No available channel`。
- OMP 侧 `generate_image` 的目录不含上述任一模型（`Image generation exhausted the resolved image chain`），
  无法借道。
- 结论：raster 出图今日不可用，R3 改用手绘风矢量交付；prompt 留档见下，后端恢复后按原样重出即可替换。

## 口径

- 画风：`FA-010` · Geometric Literary Deadpan（参考作者标签 Tom Gauld）。
- 主题色：`C-27` · 那不勒斯黄（Naples Yellow）。
- 模型未标定 → 按 unknown 走：「名称 + 核心风格特征 + 参考图」。
  参考图：`C:\Users\zhugu\.agents\skills\handraw-style\images\individual\FA\FA-010.webp`。
- 插画默认零数字：三张图都不含文字、数字、刻度值。
- 输出纯图模式：prompt 内不出现任何编号（画风号、色号、图型号都不进 prompt 正文）。

参考图隔离块（pure-image 模式随 prompt 一起给出）：

> 中文：所附图片仅用于参考画风。只提取参考图的风格特征，例如线条、笔触、媒介、材质、色彩倾向和整体视觉语言；不要使用、复制或延续参考图中的任何主体、人物、动物、服装、道具、动作、姿态、场景、背景、构图、布局、文字或故事。最终画面内容完全以用户提供的主题为准。
>
> English: Use the attached image only as a style reference. Extract only its stylistic qualities, such as linework, brushwork, medium, material texture, color tendencies, and overall visual language. Do not use, copy, or carry over any subject, person, animal, clothing, prop, action, pose, setting, background, composition, layout, text, or story from the reference image. The user's written theme is the sole source for the image content.

核心风格特征（已滤掉含「避免」的否定子句）：

> 极小几何人物、极简场景、文学/科技梗、冷面幽默；脸部与服装主动做减法，依靠清楚轮廓、眼口和少量关键形状建立人物辨识度；表情偏冷脸、尴尬或突然夸张，姿态要有明确喜剧节奏。

---

## 1. 封面（站点 hero + 整书 PDF 书封，4:3）

**中文**

```
风格名称：Geometric Literary Deadpan。主题色：那不勒斯黄（Naples Yellow）。参考作者与风格名称：Tom Gauld。核心风格特征：极小几何人物、极简场景、文学/科技梗、冷面幽默；脸部与服装主动做减法，依靠清楚轮廓、眼口和少量关键形状建立人物辨识度；表情偏冷脸、尴尬或突然夸张，姿态要有明确喜剧节奏。画面要求：暖象牙纸底，一颗立着的圆柱形电芯占据画面右侧，顶上有正极凸台，正面剖开露出两块极板和几粒散落的圆点；电芯左壁斜靠一架细梯，一个极小的几何人物站在梯上向极板伸手；另一个小人双手抱着记录纸从电芯向左走；左边一张矮脚小桌，桌上一张盖了勾的记录纸与一枚印章，桌边的小人低头看着它；一盏吊灯在小桌上方投下一圈淡淡的暖光；画面留出大片空白，不带任何文字、数字与刻度值。
```

**English**

```
Style name: Geometric Literary Deadpan. Theme color: Naples Yellow. Reference author and style name: Tom Gauld. Core style traits: tiny geometric figures, minimal settings, literary and science jokes, deadpan humor; faces and clothing are reduced so that a clear silhouette, eyes, mouth and a few key shapes carry the character; expressions stay flat, awkward or suddenly exaggerated, with a definite comic rhythm in the posture. Scene: warm ivory paper background, a standing cylindrical battery cell on the right with a small positive terminal on top and a cut-away front showing two electrode plates and a few scattered dots; a thin ladder leans against the cell's left wall with one tiny geometric figure on it reaching toward the plates; another small figure carries a record sheet away from the cell toward a low desk on the left, where a third figure bends over a stamped sheet and a stamp pad under a hanging lamp that casts a soft warm pool of light; generous empty space, no text, no numbers, no scale marks.
```

## 2. 第 1 章章首（960×560）

**中文**

```
风格名称：Geometric Literary Deadpan。主题色：那不勒斯黄（Naples Yellow）。参考作者与风格名称：Tom Gauld。核心风格特征：极小几何人物、极简场景、文学/科技梗、冷面幽默；脸部与服装主动做减法，依靠清楚轮廓、眼口和少量关键形状建立人物辨识度；表情偏冷脸、尴尬或突然夸张，姿态要有明确喜剧节奏。画面要求：暖象牙纸底，画面中部一颗立着的圆柱形电芯被正面剖开，里面两条竖直极板之间散着几粒圆点，一个小人站在一条低位隔板上伸手去够圆点；电芯顶上的正极引出一条导线绕过右上方，串上一只亮着的白炽灯泡，再折回电芯底部的壳体；画面左侧一只没有刻度的圆形指针表，表针垂向左下，一条虚线把它接到电芯侧壁，表针旁一道短箭头表示读数刚往下沉。全画只用深墨线与一点那不勒斯黄，留白充足，不含任何文字与数字。
```

**English**

```
Style name: Geometric Literary Deadpan. Theme color: Naples Yellow. Reference author and style name: Tom Gauld. Core style traits: tiny geometric figures, minimal settings, literary and science jokes, deadpan humor; faces and clothing are reduced so that a clear silhouette, eyes, mouth and a few key shapes carry the character; expressions stay flat, awkward or suddenly exaggerated, with a definite comic rhythm in the posture. Scene: warm ivory paper background; a standing cylindrical cell in the middle is opened along its front, two vertical electrode plates inside with a few dots drifting between them, and a tiny figure standing on a low shelf reaching for a dot; a wire leaves the positive terminal on top, loops up and right through a lit incandescent bulb, and returns to the cell's casing at the bottom; on the left a round dial gauge without ticks has its needle hanging towards the lower left, joined to the cell wall by a dashed line, with a short arrow beside the needle showing the reading just dropped. Ink lines only plus a little Naples Yellow, generous white space, no text, no numbers.
```

## 3. 第 7 章章首（960×560）

**中文**

```
风格名称：Geometric Literary Deadpan。主题色：那不勒斯黄（Naples Yellow）。参考作者与风格名称：Tom Gauld。核心风格特征：极小几何人物、极简场景、文学/科技梗、冷面幽默；脸部与服装主动做减法，依靠清楚轮廓、眼口和少量关键形状建立人物辨识度；表情偏冷脸、尴尬或突然夸张，姿态要有明确喜剧节奏。画面要求：暖象牙纸底，一条绿色信号线从左下向右上爬升，线上按等距串着五枚空心采样圆点；信号线上方一条水平红线横贯右侧，右端收成一个小箭头；画面底部是一条长长的尺子，短刻痕等距排列；尺子上站着一个小人，一侧手臂伸出去扶住一根细杆，杆顶挂着一面红旗，旗子的上缘正好抵住那条红线；左上角一只小钟，只有指针没有数字。全画只用深墨线、一点绿与一点红，留白充足，不含任何文字与数字。
```

**English**

```
Style name: Geometric Literary Deadpan. Theme color: Naples Yellow. Reference author and style name: Tom Gauld. Core style traits: tiny geometric figures, minimal settings, literary and science jokes, deadpan humor; faces and clothing are reduced so that a clear silhouette, eyes, mouth and a few key shapes carry the character; expressions stay flat, awkward or suddenly exaggerated, with a definite comic rhythm in the posture. Scene: warm ivory paper background; a green signal line climbs from lower left to upper right with five evenly spaced hollow sample dots on it; a horizontal red line runs across the upper right with a small arrowhead at its end; along the bottom lies a long ruler with evenly spaced short tick marks; a tiny figure stands on the ruler holding a thin pole whose top carries a red flag, the flag's upper edge exactly touching the red line; a small clock in the upper left shows hands only, no numerals. Ink lines only plus a little green and a little red, generous white space, no text, no numbers.
```

---

生成后若替换为 raster：放进 `bms-book/assets/concepts/`，把对应章 `<img>` 的 `src`/`width`/`height` 改成实际像素，
`check.py:check_assets()` 已接受 png/webp/jpg；封面仍用 `docs/public/illustrations/bms-scrapbook.svg` 这一路径两处消费。
