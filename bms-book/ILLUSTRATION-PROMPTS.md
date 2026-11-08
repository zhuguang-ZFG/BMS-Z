# 插画提示词存档与原创工程手绘重制

本文保留 R3 的原始双语场景，作为画面内容的来源。旧版使用矢量插图；本次按用户要求启用真实生图 API，生成式插图与定量 SVG 分工，不用图片模型重画数字或电路拓扑。

## 本次重制口径

- 计划范围共 37 张。本轮 **3 张已接入**（第 1、7 章首与 S2 章首），1 张信号链候选因擅加文字/缺机制被拒绝，另从旧批次磁盘恢复 6 张已付费待审候选，27 张尚未生成。候选均保留而不发布；封面与阶段页继续使用原有效 SVG。状态见 [`illustrations/handdraw/manifest.json`](illustrations/handdraw/manifest.json)。
- 实际画风为本项目原创工程手绘：暖纸、深墨、普鲁士蓝，青绿/赭黄少量平涂；无正式画风库编号。下文旧作者/画风标签是历史记录，**不是本次生成的风格身份**。
- 初次参考图请求返回 HTTP 400 `content_policy_violation`，服务端未说明具体触发项。本轮不继续提交作者复现要求；只提取存档中的「画面要求」，以项目自绘参考图重新创作。
- 客户端：[`handdraw_api.py`](../code/engineering/illustration/handdraw_api.py)；目录与场景映射：[`handdrawn_assets.py`](../code/engineering/illustration/handdrawn_assets.py)；生成与身份校验：[`make_handdrawn.py`](../code/engineering/illustration/make_handdrawn.py)。认证只读 `BMS_IMAGE_API_KEY` 环境变量，不入库。
- HTTPS 默认校验证书，拒绝带凭据跳转；只读取返回的 base64，不抓取图片 URL。失败不自动重试，避免重复付费或绕过授权问题。
- 交付 WebP 与原 PNG、实际提示词、参考图均记录 SHA-256。模型非确定，摘要只证明身份和来源，不承诺重跑得到相同像素。WebP 等比装入画布并留白，不裁切、不拉伸。
- 录用插图不含数字与刻度。AI 机制插图只辅助定性解释，不作为实拍、示波器记录、真实测量、电路连通性或硬件验收证据；详细拓扑和数值图仍保留代码真源。

生成器支持 `--only <key>`、`--all --jobs 3` 和离线 `--check`。账户已返回 HTTP 403 `insufficient_user_quota`，当前 `PAUSE` 保持，禁止继续付费提交；必须先由账户所有者解决额度并完成 SPEC §6.2 三类代表图审读。清单仅由一个持锁进程发布，逐条合并最新文件；每张图另存收据。已存在但不匹配/被拒绝的候选必须显式 `--replace`，不会静默重生付费。完整 `--check` 目前会因缺少其余图和被拒绝候选报未完成，这不是通过状态。

## R3 历史制作记录

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

---


## 4. 阶段页手绘机制图（A3 批次 + W2 补图，33 张，960×560）


矢量件在 `docs/stages/assets/s<N>-<slug>.svg`，随阶段讲义入库。按 SPEC §3.1，raster 通道恢复后按本档重出即可替换；注意阶段图的 raster 落点是 `docs/stages/assets/`（**不是** §3 那种书内 `bms-book/assets/concepts/`）。替换时改的是生成器的**源文件** `docs/stages/stage-N-*.md` 里那一行 Markdown 图（`![手绘机制图：…](assets/sN-….svg)` 的路径与扩展名；阶段页不用 `<img>` 标签、没有 `src`/宽高），再重跑 `node docs/.vitepress/prepare-stageN.mjs` 让主线页跟着更新——直接改生成页会在下次 `docs:build` 被覆盖；阶段 1/7 是手写页，直接改页面即可。


### 4.1 阶段 0 · 电芯与充电电量（4 张）

#### s0-load-sag（阶段 0 · 带载瞬态）

**中文**

```
风格名称：Geometric Literary Deadpan。主题色：那不勒斯黄（Naples Yellow）。参考作者与风格名称：Tom Gauld。核心风格特征：极小几何人物、极简场景、文学/科技梗、冷面幽默；脸部与服装主动做减法，依靠清楚轮廓、眼口和少量关键形状建立人物辨识度；表情偏冷脸、尴尬或突然夸张，姿态要有明确喜剧节奏。画面要求：暖象牙纸底，画面左侧一条手绘坐标轴，横轴向右表示时间，纵轴向上表示端电压；一条墨线先水平向右，忽然垂直下落一小段，再沿缓坡向右下走；垂直下落处站着一个极小的几何人物，双手抱着一块画满横线的记录板，板子挡住他半张脸；画面右侧是一颗电芯的剖面，左半边是石墨负极，右半边是电解液，中间一道窄窄的双电层；几粒深色小圆点从负极一侧挤向界面，几粒浅色小圆点从电解液一侧慢慢游向界面；一条实线箭头和一条虚线箭头分别标出两种圆点的方向；只用深墨线、一点青与一点金，留白充足，不含任何文字、数字与刻度值。
```

**English**

```
Style name: Geometric Literary Deadpan. Theme color: Naples Yellow. Reference author and style name: Tom Gauld. Core style traits: tiny geometric figures, minimal settings, literary and science jokes, deadpan humor; faces and clothing are reduced so that a clear silhouette, eyes, mouth and a few key shapes carry the character; expressions stay flat, awkward or suddenly exaggerated, with a definite comic rhythm in the posture. Scene: warm ivory paper background; on the left, a hand-drawn axis, time running right and terminal voltage rising upward; an ink line runs right, drops vertically for a short step, then slopes slowly down to the right; at the vertical step stands a tiny geometric figure holding a lined notebook with both hands, the notebook hiding half of his face; on the right, a cut-away cell, graphite anode on the left half, electrolyte on the right half, a narrow double layer between them; several dark dots press from the anode side toward the interface while several pale dots drift slowly from the electrolyte side; one solid arrow and one dashed arrow mark the two directions; only deep ink, a touch of teal and a touch of gold, generous white space, no text, numbers or scale values.
```

#### s0-cold-friction（阶段 0 · 低温内阻）

**中文**

```
风格名称：Geometric Literary Deadpan。主题色：那不勒斯黄（Naples Yellow）。参考作者与风格名称：Tom Gauld。核心风格特征：极小几何人物、极简场景、文学/科技梗、冷面幽默；脸部与服装主动做减法，依靠清楚轮廓、眼口和少量关键形状建立人物辨识度；表情偏冷脸、尴尬或突然夸张，姿态要有明确喜剧节奏。画面要求：暖象牙纸底，一条粗的浅绿管道从左到右横贯画面，管道上有三道收窄的闸口；第一道闸口前，几粒小圆点在黏稠的液体里挤成一团；第二道闸口是一道窄缝，圆点贴着缝壁挤过去；第三道闸口是几层水平叠放的黑色薄片，圆点卡在层间；每个闸口上方悬着一枚小小的冰晶标记；管道下方一条细箭头指向右，表示离子流方向；画面右侧一个极小的几何人物缩着肩膀、抱着手臂，站在管道末端；只用深墨线、一点青、一点金与一点红，留白充足，不含任何文字、数字与刻度值。
```

**English**

```
Style name: Geometric Literary Deadpan. Theme color: Naples Yellow. Reference author and style name: Tom Gauld. Core style traits: tiny geometric figures, minimal settings, literary and science jokes, deadpan humor; faces and clothing are reduced so that a clear silhouette, eyes, mouth and a few key shapes carry the character; expressions stay flat, awkward or suddenly exaggerated, with a definite comic rhythm in the posture. Scene: warm ivory paper background; a thick pale-green pipe runs across the picture from left to right with three narrowed gates; before the first gate, a few dots bunch together in a viscous liquid; the second gate is a narrow slit and the dots squeeze along its walls; the third gate is a stack of horizontal black sheets with dots stuck between the layers; a small ice-crystal mark hangs above each gate; a thin arrow below the pipe points right to show the ion flow; at the pipe's end on the right, a tiny geometric figure stands with hunched shoulders and folded arms; only deep ink, a touch of teal, a touch of gold and a touch of red, generous white space, no text, numbers or scale values.
```

#### s0-cv-handoff（阶段 0 · 恒压段）

**中文**

```
风格名称：Geometric Literary Deadpan。主题色：那不勒斯黄（Naples Yellow）。参考作者与风格名称：Tom Gauld。核心风格特征：极小几何人物、极简场景、文学/科技梗、冷面幽默；脸部与服装主动做减法，依靠清楚轮廓、眼口和少量关键形状建立人物辨识度；表情偏冷脸、尴尬或突然夸张，姿态要有明确喜剧节奏。画面要求：暖象牙纸底，画面左侧一只敞口容器，容器里浅绿色的液面正在上升；容器上方悬着一块水平的红色挡板，挡板与液面之间留着一道窄缝；容器左壁外有两条箭头指向容器，一条粗实线、一条细虚线，表示电流由大到小；容器右侧立着一把没有数字的卡尺，卡尺卡在挡板与液面之间；画面右侧四个小方框从上到下排成一列，框与框之间用向下的箭头连接，最后一个框旁边一个极小的几何人物举起一面小旗；只用深墨线、一点青、一点金与一点红，留白充足，不含任何文字、数字与刻度值。
```

**English**

```
Style name: Geometric Literary Deadpan. Theme color: Naples Yellow. Reference author and style name: Tom Gauld. Core style traits: tiny geometric figures, minimal settings, literary and science jokes, deadpan humor; faces and clothing are reduced so that a clear silhouette, eyes, mouth and a few key shapes carry the character; expressions stay flat, awkward or suddenly exaggerated, with a definite comic rhythm in the posture. Scene: warm ivory paper background; on the left, an open vessel with a pale-green liquid surface rising inside; a horizontal red ceiling bar hangs above the vessel, leaving a narrow gap above the liquid; two arrows outside the vessel's left wall point inward, one thick and solid, one thin and dashed, showing current falling from large to small; to the right of the vessel stands a caliper with no numbers, spanning the gap between the ceiling and the liquid; on the right, four small boxes are stacked in a column, joined by downward arrows, and beside the last box a tiny geometric figure raises a small flag; only deep ink, a touch of teal, a touch of gold and a touch of red, generous white space, no text, numbers or scale values.
```

#### s0-soh-tank（阶段 0 · SOC 与 SOH）

**中文**

```
风格名称：Geometric Literary Deadpan。主题色：那不勒斯黄（Naples Yellow）。参考作者与风格名称：Tom Gauld。核心风格特征：极小几何人物、极简场景、文学/科技梗、冷面幽默；脸部与服装主动做减法，依靠清楚轮廓、眼口和少量关键形状建立人物辨识度；表情偏冷脸、尴尬或突然夸张，姿态要有明确喜剧节奏。画面要求：暖象牙纸底，画面上方一只半圆形油表，表盘没有数字，只有几道短刻痕，红色表针垂直指向上方；油表下方左右各有一只油箱，左边的油箱高大、液面接近箱口，右边的油箱矮小、液面同样接近箱口；两条虚线从油表分别引到两只油箱；右边油箱底部接出一根细短的出油管，管口比左边窄；一个极小的几何人物站在两只油箱之间，左手搭在左边油箱上，右手按在右边油箱上，低头看着两只油箱；只用深墨线、一点青、一点金与一点红，留白充足，不含任何文字、数字与刻度值。
```

**English**

```
Style name: Geometric Literary Deadpan. Theme color: Naples Yellow. Reference author and style name: Tom Gauld. Core style traits: tiny geometric figures, minimal settings, literary and science jokes, deadpan humor; faces and clothing are reduced so that a clear silhouette, eyes, mouth and a few key shapes carry the character; expressions stay flat, awkward or suddenly exaggerated, with a definite comic rhythm in the posture. Scene: warm ivory paper background; at the top, a semicircular fuel gauge with no numbers, only a few short ticks, its red needle pointing straight up; below the gauge, two fuel tanks side by side, the left one tall with its liquid near the rim, the right one short with its liquid also near the rim; two dashed lines lead from the gauge to the two tanks; a short narrow outlet pipe leaves the bottom of the right tank, its opening narrower than the left one; a tiny geometric figure stands between the tanks, one hand resting on the left tank, the other hand on the right tank, looking down at both; only deep ink, a touch of teal, a touch of gold and a touch of red, generous white space, no text, numbers or scale values.
```


### 4.2 阶段 1 · 认识 BMS（4 张）

阶段 1 共四张：`s1-fault-pickoff`、`s1-switch-directions`、`s1-balance-energy`、`s1-series-voltage`。
画风与措辞沿用 `bms-book/ILLUSTRATION-PROMPTS.md` 顶部口径；图内零数字。

#### s1-fault-pickoff（阶段 1 · 五条保护在同一条链上的截获点）

**中文**

```
风格名称：Geometric Literary Deadpan。主题色：那不勒斯黄（Naples Yellow）。参考作者与风格名称：Tom Gauld。核心风格特征：极小几何人物、极简场景、文学/科技梗、冷面幽默；脸部与服装主动做减法，依靠清楚轮廓、眼口和少量关键形状建立人物辨识度；表情偏冷脸、尴尬或突然夸张，姿态要有明确喜剧节奏。画面要求：暖象牙纸底，横向一条手绘链条穿过画面中部靠下的位置。画面左侧竖着三张巴掌大的便签，自上而下依次写着「电压」「电流」「温度」，每张便签右侧伸出一条短引线，三条短线在便签右边合成一条竖直总线，总线再向右进入一只方框，方框上写「采样」。方框右侧分两路：上路依次串两只方框，分别写「软件比较」和「确认延时」，再连到画面最右侧一只画着两道并排闸门的方框；下路一只方框写「比较器」，从采样方框底部直接向右下绕行，越过上路的两只方框，末端箭头向上接进同一只闸门方框。上路方框上方挂一张便签，写「过充 过放 过流 温度」；下路方框左下方挂一张小便签，写「过流尖峰 短路」。画面底部一条横向浅绿底条，条上一行短句。所有箭头都是信号或动作的流向，不要装饰性箭头；不出现任何数字、刻度或表格。
```

**English**

```
Style name: Geometric Literary Deadpan. Theme color: Naples Yellow. Reference author and style name: Tom Gauld. Core style traits: tiny geometric figures, minimal settings, literary and science jokes, deadpan humor; faces and clothing are reduced so that a clear silhouette, eyes, mouth and a few key shapes carry the character; expressions stay flat, awkward or suddenly exaggerated, with a definite comic rhythm in the posture. Scene: warm ivory paper background, a hand-drawn chain runs horizontally across the lower middle of the frame. On the left, three small stacked notes read "voltage", "current" and "temperature"; each note sends a short lead to the right, the three leads merge into one vertical bus, and the bus enters a box labeled "sampling". Right of that box the path splits in two: the upper lane passes through two boxes labeled "software compare" and "confirm delay" before reaching a box at the far right that holds two side-by-side gate symbols; the lower lane is a single box labeled "comparator" that leaves the bottom of the sampling box, runs down and right, bypasses the two upper boxes entirely, and turns up with an arrow into the same gate box. A note above the upper boxes reads "overcharge, overdischarge, overcurrent, temperature"; a smaller note below the comparator reads "current spike, short circuit". A pale green strip across the bottom carries one short line of text. All arrows mark signal or action direction only, no decorative arrows; no numerals, ticks or tables anywhere.
```

#### s1-switch-directions（阶段 1 · 断口的两个方向）

**中文**

```
风格名称：Geometric Literary Deadpan。主题色：那不勒斯黄（Naples Yellow）。参考作者与风格名称：Tom Gauld。核心风格特征：极小几何人物、极简场景、文学/科技梗、冷面幽默；脸部与服装主动做减法，依靠清楚轮廓、眼口和少量关键形状建立人物辨识度；表情偏冷脸、尴尬或突然夸张，姿态要有明确喜剧节奏。画面要求：暖象牙纸底，画面左侧一只虚线大框，框内一条竖直线自上而下穿过，线中段画一只张开的闸刀开关（一只圆触点、一根斜起的刀臂、下方另一只圆触点），刀臂旁边一枚向下的箭头，旁边写「放电」；这条线的右侧并联一条细线，细线中段画一只二极管符号——朝上的三角与压在三角尖上的短横——二极管旁一枚向上的箭头，旁边写「充电」；竖直线上端与下端各连一条水平短线，分别引出框外，标注「电池」与「端子」。画面右侧另一只虚线大框，框内上下两只方块，上块写「充电 MOS」、下块写「放电 MOS」，两块之间用一条竖直虚线相连并在旁边注「背靠背」；两块的文字分别注明各自挡住的方向，以及关断后另一个方向仍可通行的走法；框底一条浅金底小条写一句「只装一只，总有一个方向关不掉」。箭头只表示电流方向；不出现数字、公式或电气参数表。
```

**English**

```
Style name: Geometric Literary Deadpan. Theme color: Naples Yellow. Reference author and style name: Tom Gauld. Core style traits: tiny geometric figures, minimal settings, literary and science jokes, deadpan humor; faces and clothing are reduced so that a clear silhouette, eyes, mouth and a few key shapes carry the character; expressions stay flat, awkward or suddenly exaggerated, with a definite comic rhythm in the posture. Scene: warm ivory paper background. On the left a large dashed frame holds one vertical conductor; halfway down sits an open knife switch drawn with two round contacts and a raised blade, with a downward arrow beside it labeled "discharge". To the right of that conductor a thin parallel line carries a diode symbol, an upward triangle with a short bar across its tip, and an upward arrow beside it labeled "charge"; the top and bottom of the vertical conductor each run a short horizontal lead out of the frame, marked "battery" and "terminal". On the right another dashed frame holds two stacked boxes, the upper one labeled "charge MOS" and the lower one "discharge MOS", joined by a vertical dashed line annotated "back to back"; each box states which direction it blocks and that the other direction still passes through when it turns off. A pale gold strip at the bottom of that frame reads "with only one, one direction can never be closed". Arrows only show current direction; no numerals, formulas or parameter tables.
```

#### s1-balance-energy（阶段 1 · 均衡的能量去哪里）

**中文**

```
风格名称：Geometric Literary Deadpan。主题色：那不勒斯黄（Naples Yellow）。参考作者与风格名称：Tom Gauld。核心风格特征：极小几何人物、极简场景、文学/科技梗、冷面幽默；脸部与服装主动做减法，依靠清楚轮廓、眼口和少量关键形状建立人物辨识度；表情偏冷脸、尴尬或突然夸张，姿态要有明确喜剧节奏。画面要求：暖象牙纸底，画面左侧一只浅金底方块，写「偏高单体」，方块右侧引出一条短线，线上一个小圆点后分叉成上下两支。上支向右再折上，进入一只方框写「电阻」，方框右侧一枚向右的短箭头，箭头右边三缕红色热浪向上飘，热浪上方一个小字「热」，热浪下方两行小字写「散到空气里」和「邻节拿不到」。下支向右再折下，进入一只浅绿底方框写「电感或电容」，方框右侧一枚向右的箭头，箭头落进画面右下一只方框，写「偏低单体」。两支的左上与左下各有一行小标题，分别写「被动」与「主动」。画面底部一条浅绿底横条，写一句「被动烧成热，主动搬到邻节」。箭头只表示能量流向，不画电流波形；不出现数字与刻度。
```

**English**

```
Style name: Geometric Literary Deadpan. Theme color: Naples Yellow. Reference author and style name: Tom Gauld. Core style traits: tiny geometric figures, minimal settings, literary and science jokes, deadpan humor; faces and clothing are reduced so that a clear silhouette, eyes, mouth and a few key shapes carry the character; expressions stay flat, awkward or suddenly exaggerated, with a definite comic rhythm in the posture. Scene: warm ivory paper background. At the left a pale gold box reads "high cell"; a short lead leaves its right edge, passes a small dot, and splits into an upper and a lower branch. The upper branch turns right and up into a box labeled "resistor"; a short arrow leaves that box to the right, and three red heat squiggles rise beside the arrow, with the single word "heat" above them and two small lines below reading "lost to the air" and "the neighbor gets none". The lower branch turns right and down into a pale green box labeled "inductor or capacitor"; an arrow leaves it to the right and lands on a box at the lower right labeled "low cell". Small captions above the two branches read "passive" and "active". A pale green strip across the bottom reads "passive burns it to heat, active carries it to the neighbor". Arrows show energy flow only; no current waveforms, numerals or scales.
```


#### s1-series-voltage（阶段 1 · 一串电池：电流只有一个，电压层层相加）

**中文**

```
风格名称：Geometric Literary Deadpan。主题色：那不勒斯黄（Naples Yellow）。参考作者与风格名称：Tom Gauld。核心风格特征：极小几何人物、极简场景、文学/科技梗、冷面幽默；脸部与服装主动做减法，依靠清楚轮廓、眼口和少量关键形状建立人物辨识度；表情偏冷脸、尴尬或突然夸张，姿态要有明确喜剧节奏。画面要求：暖象牙纸底，横向排开三块米黄卡片。左卡自上而下堆着几只扁长方形电芯，一条深墨导线把它们串成一条竖链，链旁一枚向下的箭头表示同一个电流穿过每一只；卡内一行小字「全包同一个电流」，卡底一行更小的字「谁先触线，全包同停」。中卡画一条细导线自左向右，导线下方三只方块自上而下叠放，最下一只描成深金边，旁边引出「× 串数」的短箭头；卡顶一行小字「电压沿链相加」。右卡竖着三只扁长方形电芯，最下一只用浅红底与红边单独描出，旁边一枚红色箭头指向它，卡底一行小字「先到电压边界」。画面最下方一条横贯的长条卡片，写「串联抬电压，并联加容量」。
```

**English**

```
Style name: Geometric Literary Deadpan. Theme color: Naples Yellow. Reference author and style name: Tom Gauld. Core style traits: tiny geometric figures, minimal settings, literary and science jokes, deadpan humor; faces and clothing are reduced so that a clear silhouette, eyes, mouth and a few key shapes carry the character; expressions stay flat, awkward or suddenly exaggerated, with a definite comic rhythm in the posture. Scene: warm ivory paper background with three cream cards in a row. The left card stacks several flat rectangles as cells wired into one vertical chain, a downward arrow beside the chain showing a single current passing through every cell; a small line inside reads "one current for the whole pack" and a smaller line at the card foot reads "the first to hit the limit stops the pack". The middle card runs a thin wire left to right with three stacked blocks beneath it, the lowest outlined in deep gold and a short arrow beside it labeled "times the cell count"; a small line at the card top reads "voltage adds along the chain". The right card holds three flat cell rectangles, the lowest drawn alone in pale red with a red outline and a red arrow pointing at it; a small line at the card foot reads "reaches the voltage limit first". Along the bottom a long strip card reads "series raises voltage, parallel adds capacity".
```


### 4.3 阶段 2 · 保护板实践（4 张）

#### s2-blocked-direction（阶段 2 · 单节保护板的断口方向）

**中文**

```
风格名称：Geometric Literary Deadpan。主题色：那不勒斯黄（Naples Yellow）。参考作者与风格名称：Tom Gauld。核心风格特征：极小几何人物、极简场景、文学/科技梗、冷面幽默；脸部与服装主动做减法，依靠清楚轮廓、眼口和少量关键形状建立人物辨识度；表情偏冷脸、尴尬或突然夸张，姿态要有明确喜剧节奏。画面要求：暖象牙纸底，横向构图。左边一只立着的方形电芯，顶面一条粗导线向右接到右边一只方形负载，负载下沿再接一条粗导线向左回走；这条回路上并排站着两只相向而立的单向阀门符号，靠负载那只被一道红色断口横断，阀门下方另有一条细回路绕过断口；一枚绿色箭头从负载端沿细回路向左穿过断口旁的阀门，再折向上进入电芯底面；靠电芯那只阀门通道完整，其下方一只反方向的单向阀门被一道细红叉标出。画面不出现文字与数字，方向全靠箭头和阀门朝向表达。
```

**English**

```
Style name: Geometric Literary Deadpan. Theme color: Naples Yellow. Reference author and style name: Tom Gauld. Core style traits: tiny geometric figures, minimal settings, literary and science jokes, deadpan humor; faces and clothing are reduced so that a clear silhouette, eyes, mouth and a few key shapes carry the character; expressions stay flat, awkward or suddenly exaggerated, with a definite comic rhythm in the posture. Scene: warm ivory paper, landscape composition. On the left a standing rectangular battery cell; a thick wire leaves its top and runs right into a rectangular load box, whose lower edge returns a thick wire leftward; on that return path stand two one-way valve symbols facing toward each other. The valve nearer the load is cut by a red gap; a thin bypass loop runs beneath it and a green arrow travels from the load end along that loop, through the valve beside the gap, then turns upward into the cell's bottom face. The valve nearer the cell stays open, with a small reverse valve below it marked by a thin red cross. No text or numerals; direction is carried only by arrows and valve orientation.
```

#### s2-multicell-reference（阶段 2 · 多串采样的参考点）

**中文**

```
风格名称：Geometric Literary Deadpan。主题色：那不勒斯黄（Naples Yellow）。参考作者与风格名称：Tom Gauld。核心风格特征：极小几何人物、极简场景、文学/科技梗、冷面幽默；脸部与服装主动做减法，依靠清楚轮廓、眼口和少量关键形状建立人物辨识度；表情偏冷脸、尴尬或突然夸张，姿态要有明确喜剧节奏。画面要求：暖象牙纸底。左侧三只相同的方盒自下而上摞成一列，盒与盒之间各有一个小圆点，相邻两盒共用同一个圆点；每只盒子右侧伸出两根细虚线，三对虚线向右扇开，分别落进右侧一整块大方形芯片左侧的三对小孔；芯片内部再横着分成三格，每格自成一间小屋，彼此之间没有连线。画面中一条细细的虚线自下而上穿过整列盒子的右侧，标出参考点的位置逐级抬高。画面不出现文字与数字。
```

**English**

```
Style name: Geometric Literary Deadpan. Theme color: Naples Yellow. Reference author and style name: Tom Gauld. Core style traits: tiny geometric figures, minimal settings, literary and science jokes, deadpan humor; faces and clothing are reduced so that a clear silhouette, eyes, mouth and a few key shapes carry the character; expressions stay flat, awkward or suddenly exaggerated, with a definite comic rhythm in the posture. Scene: warm ivory paper. Three identical boxes stack vertically on the left, with a small dot between adjacent boxes so that neighbors share one dot; two thin dashed wires leave each box's right side, and the three pairs fan out rightward into three pairs of small holes on the left edge of one large square chip. Inside the chip, three separate compartments sit one above another with no link between them. A fine dashed line runs up along the right side of the stack, showing the reference point stepping higher with each cell. No text or numerals.
```

#### s2-ntc-placement（阶段 2 · NTC 贴附位置）

**中文**

```
风格名称：Geometric Literary Deadpan。主题色：那不勒斯黄（Naples Yellow）。参考作者与风格名称：Tom Gauld。核心风格特征：极小几何人物、极简场景、文学/科技梗、冷面幽默；脸部与服装主动做减法，依靠清楚轮廓、眼口和少量关键形状建立人物辨识度；表情偏冷脸、尴尬或突然夸张，姿态要有明确喜剧节奏。画面要求：暖象牙纸底，左右两块并排的浅色面板。左面板里一只很大的方盒占据中央，右上角贴着一颗小圆珠，珠子与盒壁之间一条短引线相接，两道虚线热流从盒内缓缓弯向圆珠；右面板里一只小一号的方盒偏左上，右下角外贴着同样的小圆珠，两道又短又直的虚线热流从盒角直接冲向圆珠；两颗珠子外形完全一致。画面不出现文字与数字，快慢靠热流线的长短与弯曲表达。
```

**English**

```
Style name: Geometric Literary Deadpan. Theme color: Naples Yellow. Reference author and style name: Tom Gauld. Core style traits: tiny geometric figures, minimal settings, literary and science jokes, deadpan humor; faces and clothing are reduced so that a clear silhouette, eyes, mouth and a few key shapes carry the character; expressions stay flat, awkward or suddenly exaggerated, with a definite comic rhythm in the posture. Scene: warm ivory paper, two pale panels side by side. In the left panel a large square box fills the middle, with a small round bead attached at its upper right corner by a short lead, and two dashed heat streams curving slowly from inside the box toward the bead. In the right panel a smaller box sits high on the left, with an identical bead just outside its lower right corner and two short straight dashed heat streams driving from the corner into the bead. Both beads are drawn identically. No text or numerals; the difference in speed is carried by the length and curvature of the heat streams.
```

#### s2-common-ground-short（阶段 2 · 共地叠串的短路回路）

**中文**

```
风格名称：Geometric Literary Deadpan。主题色：那不勒斯黄（Naples Yellow）。参考作者与风格名称：Tom Gauld。核心风格特征：极小几何人物、极简场景、文学/科技梗、冷面幽默；脸部与服装主动做减法，依靠清楚轮廓、眼口和少量关键形状建立人物辨识度；表情偏冷脸、尴尬或突然夸张，姿态要有明确喜剧节奏。画面要求：暖象牙纸底。左边上下两只方形电源盒，各自从左侧垂下一条细线，两条细线汇到同一根竖杆，竖杆下端落在一条带三道短斜线的接地横杠上；两只盒子右沿各伸出正负两条导线，四条线向右汇入右边上下相叠的两只方盒（模拟两节电芯），中间的汇合点是一个圆点；最右侧一条红色虚线自上而下绕过下面那只方盒，首尾各接在圆点与方盒底角上，虚线中段压着一枚带地字圆牌，旁边一道红色闪电。画面不出现文字与数字。
```

**English**

```
Style name: Geometric Literary Deadpan. Theme color: Naples Yellow. Reference author and style name: Tom Gauld. Core style traits: tiny geometric figures, minimal settings, literary and science jokes, deadpan humor; faces and clothing are reduced so that a clear silhouette, eyes, mouth and a few key shapes carry the character; expressions stay flat, awkward or suddenly exaggerated, with a definite comic rhythm in the posture. Scene: warm ivory paper. Two square supply boxes stack on the left, each dropping a thin wire from its left side; the two wires meet one vertical trunk that lands on a horizontal earth bar marked with three short slashes. Each supply also sends two leads from its right edge, and the four leads converge rightward into two stacked boxes standing for two cells, meeting at a single dot between them. On the far right a red dashed line loops down around the lower box, one end on the dot and the other on the lower corner, with a small round earth seal and a red lightning bolt at its midpoint. No text or numerals.
```


### 4.4 阶段 3 · AFE 与采样（5 张）

交付口径：`docs/视觉缺口表.md` A-16（阶段 3，下限 5 张）。当前入库的是同画风矢量版
（`docs/stages/assets/s3-*.svg`），本文件是 prompt 侧留档：后端恢复后按节重出 raster，
替换矢量文件即可；页面仍两行（图 + 看图），但图行的路径/扩展名要跟着改成 raster 文件。

画风：`FA-010` · Geometric Literary Deadpan（参考作者 Tom Gauld）；主题色 `C-27` 那不勒斯黄。
每张图零阿拉伯数字；画面内只出现中文标注。

#### s3-sense-chain（阶段 3 · 采样链每一级掺什么）

**中文**

```
风格名称：Geometric Literary Deadpan。主题色：那不勒斯黄（Naples Yellow）。参考作者与风格名称：Tom Gauld。核心风格特征：极小几何人物、极简场景、文学/科技梗、冷面幽默；脸部与服装主动做减法，依靠清楚轮廓、眼口和少量关键形状建立人物辨识度；表情偏冷脸、尴尬或突然夸张，姿态要有明确喜剧节奏。画面要求：暖象牙纸底，横向一排五张微微歪斜的浅色卡片，从左到右依次标注「电芯两端」「分压与 RC」「多路开关」「转换与基准」「寄存器」，卡片之间用细箭头相连；第二到第五张卡片的底边各被一枚红色小箭头从下方扎进去，箭头下面各有一行小字，依次是「比例误差」「偏置误差」「偏置与台阶」「年龄」；五张卡片下方并排三张更大的卡片，左边浅绿底写「校准修得掉」，中间浅红底写「校准修不掉」，右边浅金底写「只能靠设计」，每张卡片里有两行小字；画面最下方一条浅绿横条，写一句结论。所有标注用中文，画面内不出现阿拉伯数字，不出现坐标轴、示波器或仪器。
```

**English**

```
Style name: Geometric Literary Deadpan. Theme color: Naples Yellow. Reference author and style name: Tom Gauld. Core style traits: tiny geometric figures, minimal settings, literary and science jokes, deadpan humor; faces and clothing are reduced so that a clear silhouette, eyes, mouth and a few key shapes carry the character; expressions stay flat, awkward or suddenly exaggerated, with a definite comic rhythm in the posture. Scene: warm ivory paper background; five slightly tilted pale cards in a row, labelled from left to right "cell terminals", "divider and RC", "multiplexer", "conversion and reference", "register", joined by thin arrows; a small red arrow stabs up into the bottom edge of the second through fifth cards, each with a one-line caption underneath reading "gain error", "offset error", "offset and steps", "age"; under the row, three larger cards side by side, the left pale green reading "calibration fixes it", the middle pale red reading "calibration cannot", the right pale gold reading "design only", each holding two short lines; a pale green strip at the bottom carries one closing sentence. All labels in Chinese, no Arabic numerals anywhere, no axes, oscilloscope or bench instruments.
```

#### s3-ntc-divider（阶段 3 · 温度变成数字的链）

**中文**

```
风格名称：Geometric Literary Deadpan。主题色：那不勒斯黄（Naples Yellow）。参考作者与风格名称：Tom Gauld。核心风格特征：极小几何人物、极简场景、文学/科技梗、冷面幽默；脸部与服装主动做减法，依靠清楚轮廓、眼口和少量关键形状建立人物辨识度；表情偏冷脸、尴尬或突然夸张，姿态要有明确喜剧节奏。画面要求：暖象牙纸底，画面左半部竖着画一条手绘电路：顶部一条短横线标「基准电压」，往下接一个浅色方框「上拉电阻」，方框下面一个分压点圆点，圆点向右伸出一条线接浅色小方框「转换」；圆点向下先是一段红色锯齿线，旁边标「线阻」和「走线、插件、开关」，锯齿线下面接浅绿方框「NTC」，再往下是接地符号；NTC 左侧三道红色热浪弯线，标「电芯的热」。画面右半部自上而下三张卡片：「分压点电压偏高」「查表当成阻值偏大」「判成温度偏低」，最后一张用浅红底，卡片之间用向下箭头连接；三张卡片下面一张浅金说明卡，写热端份额更大；最下方一条浅绿横条。所有标注用中文，画面内不出现阿拉伯数字，不出现坐标轴或仪表。
```

**English**

```
Style name: Geometric Literary Deadpan. Theme color: Naples Yellow. Reference author and style name: Tom Gauld. Core style traits: tiny geometric figures, minimal settings, literary and science jokes, deadpan humor; faces and clothing are reduced so that a clear silhouette, eyes, mouth and a few key shapes carry the character; expressions stay flat, awkward or suddenly exaggerated, with a definite comic rhythm in the posture. Scene: warm ivory paper background; the left half holds a hand-drawn vertical circuit: a short rail on top labelled "reference voltage", a pale box below labelled "pull-up resistor", a node dot under it, a line from the dot going right into a small pale box labelled "conversion"; from the dot downward a red zigzag labelled "wire resistance" with a second line "trace, connector, switch", then a pale green box labelled "NTC", then a ground symbol; three red heat waves enter the NTC from the left, labelled "heat from the cell". The right half stacks three cards top to bottom: "divider node reads high", "table assumes larger resistance", "reads as colder", the last one pale red, joined by downward arrows; a pale gold note card below them about the hot end share; a pale green strip at the bottom. All labels in Chinese, no Arabic numerals, no axes or instruments.
```

#### s3-fault-snapshot（阶段 3 · 故障快照）

**中文**

```
风格名称：Geometric Literary Deadpan。主题色：那不勒斯黄（Naples Yellow）。参考作者与风格名称：Tom Gauld。核心风格特征：极小几何人物、极简场景、文学/科技梗、冷面幽默；脸部与服装主动做减法，依靠清楚轮廓、眼口和少量关键形状建立人物辨识度；表情偏冷脸、尴尬或突然夸张，姿态要有明确喜剧节奏。画面要求：暖象牙纸底，左上一排八个小方格代表滚动缓冲，最左一格浅红，最右一格浅绿并在格里点一个圆点，格子上方一行小字说明每拍写一格；一条虚线箭头从最右格绕到最左格下方，箭头回到最左格底边；一根红色粗箭头从缓冲右端指向一张浅红卡片「触发：停写」，卡片里两行小字；再一根箭头指向右上方浅绿卡片「非易失区」，卡片里三行小字；绿色卡片下方一条红色横虚线标「复位 / 掉电」，一根红色虚线箭头穿过横线指向下方的浅色卡片「下次上电」；左下角一张浅金说明卡列出快照内容；最下方一条浅绿横条。所有标注用中文，画面内不出现阿拉伯数字。
```

**English**

```
Style name: Geometric Literary Deadpan. Theme color: Naples Yellow. Reference author and style name: Tom Gauld. Core style traits: tiny geometric figures, minimal settings, literary and science jokes, deadpan humor; faces and clothing are reduced so that a clear silhouette, eyes, mouth and a few key shapes carry the character; expressions stay flat, awkward or suddenly exaggerated, with a definite comic rhythm in the posture. Scene: warm ivory paper background; a row of eight small squares at the upper left stands for a rolling buffer, the leftmost pale red, the rightmost pale green with a dot inside, one line of small text above saying every tick writes one cell; a dashed arrow loops from the rightmost square around to the bottom of the leftmost one; a thick red arrow leads from the buffer to a pale red card "trigger: stop writing" with two short lines; another arrow leads to a pale green card "non-volatile area" at the upper right with three short lines; under the green card a red dashed horizontal line labelled "reset or power loss", with a red dashed arrow crossing it down to a pale card "next power-up"; a pale gold note card at the lower left lists what the snapshot holds; a pale green strip at the bottom. All labels in Chinese, no Arabic numerals.
```

#### s3-charge-pump（阶段 3 · 电荷泵抬栅压）

**中文**

```
风格名称：Geometric Literary Deadpan。主题色：那不勒斯黄（Naples Yellow）。参考作者与风格名称：Tom Gauld。核心风格特征：极小几何人物、极简场景、文学/科技梗、冷面幽默；脸部与服装主动做减法，依靠清楚轮廓、眼口和少量关键形状建立人物辨识度；表情偏冷脸、尴尬或突然夸张，姿态要有明确喜剧节奏。画面要求：暖象牙纸底，左上横排三张卡片「低压电源」「飞电容」「栅极电容」，卡片之间箭头相连，最右一张向右伸出一条折线落到右下方的栅极；画面右侧竖着画电池符号、高边开关符号与一个「负载」方框，电池正极引出的横线向右接开关上端，开关下端接负载再回到负极；最右侧一条竖直虚线做电位尺，从上到下三个刻度标「栅极」「母线」「地」，母线刻度向左伸一条虚线接到电池正极那条横线；左下两张卡片「第一拍：充电」「第二拍：搬高」，各两行小字；再往下一张说明卡；最下方一条浅绿横条。所有标注用中文，画面内不出现阿拉伯数字。
```

**English**

```
Style name: Geometric Literary Deadpan. Theme color: Naples Yellow. Reference author and style name: Tom Gauld. Core style traits: tiny geometric figures, minimal settings, literary and science jokes, deadpan humor; faces and clothing are reduced so that a clear silhouette, eyes, mouth and a few key shapes carry the character; expressions stay flat, awkward or suddenly exaggerated, with a definite comic rhythm in the posture. Scene: warm ivory paper background; three cards in a row at the upper left, "low-voltage supply", "flying capacitor", "gate capacitor", joined by arrows, the rightmost sending a bent line down to the gate of the switch at the lower right; on the right side a battery symbol, a high-side switch symbol and a "load" box are stacked, the positive terminal rail running right into the switch, the switch feeding the load and returning to the negative terminal; at the far right a vertical dashed scale with three marks from top to bottom, "gate", "bus", "ground", the bus mark sending a dashed line left to the positive rail; two cards at the lower left, "phase one: charge" and "phase two: lift", each with two short lines; a note card below them; a pale green strip at the bottom. All labels in Chinese, no Arabic numerals.
```

#### s3-sense-route（阶段 3 · 采样线收磁通）

**中文**

```
风格名称：Geometric Literary Deadpan。主题色：那不勒斯黄（Naples Yellow）。参考作者与风格名称：Tom Gauld。核心风格特征：极小几何人物、极简场景、文学/科技梗、冷面幽默；脸部与服装主动做减法，依靠清楚轮廓、眼口和少量关键形状建立人物辨识度；表情偏冷脸、尴尬或突然夸张，姿态要有明确喜剧节奏。画面要求：暖象牙纸底，画面分成左右两个虚线方框。左框里一个粗线大电流回路方框，右边紧挨一个敞开的细线采样回路方框，两个方框之间有三道红色虚线弧从大电流回路鼓出来，其中一道穿过采样回路的边框，另有一根红色箭头扎进采样回路内部，旁边标「变化的磁通」和「感应电压叠进读数」。右框里同样的粗线大电流回路，但采样回路改成两根几乎贴在一起的细线斜着往上走，中间画几道绞合的小横杠，红色虚线弧只在大电流回路附近鼓一下就停住，够不到细线；两根细线顶端接一个小方框「转换」。两个方框下方各一行小字说明，最下方一条浅绿横条。所有标注用中文，画面内不出现阿拉伯数字。
```

**English**

```
Style name: Geometric Literary Deadpan. Theme color: Naples Yellow. Reference author and style name: Tom Gauld. Core style traits: tiny geometric figures, minimal settings, literary and science jokes, deadpan humor; faces and clothing are reduced so that a clear silhouette, eyes, mouth and a few key shapes carry the character; expressions stay flat, awkward or suddenly exaggerated, with a definite comic rhythm in the posture. Scene: warm ivory paper background, two dashed panels side by side. In the left panel a thick-line high-current loop box sits beside an open thin-line sampling loop box; three red dashed arcs bulge out of the high-current loop toward the sampling loop, one crossing its frame, and a red arrow pierces into the sampling loop interior, with captions "changing flux" and "induced voltage added to the reading". In the right panel the same thick high-current loop, but the sampling path is two thin lines running almost parallel upward with a few short crossing ticks, and the red dashed arcs stop near the high-current loop without reaching the pair; the two thin lines end at a small box "conversion". One line of small text under each panel, a pale green strip at the bottom. All labels in Chinese, no Arabic numerals.
```


### 4.5 阶段 4 · SOC / SOH / SOP（6 张）

交付口径：`docs/视觉缺口表.md` A-17（阶段 4，下限 6 张）。当前入库的是同画风矢量版
（`docs/stages/assets/s4-*.svg`），本文件是 prompt 侧留档：后端恢复后按节重出 raster，
替换矢量文件即可；页面仍两行（图 + 看图），但图行的路径/扩展名要跟着改成 raster 文件。

画风：`FA-010` · Geometric Literary Deadpan（参考作者 Tom Gauld）；主题色 `C-27` 那不勒斯黄。
每张图零阿拉伯数字；画面内只出现中文标注（允许页面正文原样出现的英文缩写，如 SOC、SOH、SOP、EKF）。

#### s4-soc-denominator（阶段 4 · 账本与分母）

**中文**

```
风格名称：Geometric Literary Deadpan。主题色：那不勒斯黄（Naples Yellow）。参考作者与风格名称：Tom Gauld。核心风格特征：极小几何人物、极简场景、文学/科技梗、冷面幽默；脸部与服装主动做减法，依靠清楚轮廓、眼口和少量关键形状建立人物辨识度；表情偏冷脸、尴尬或突然夸张，姿态要有明确喜剧节奏。画面要求：暖象牙纸底，横向一条单向流程。左侧一张轻歪的浅色卡片写「安时账本」，卡内三行小字「只累加电流与时间」「对错全看电流」「这就是分子」；卡片右边一个大圆圈，圈里一个手写除号；圆圈下方一张卡片写「满充容量」，卡内两行小字「这就是分母」「老化让它缩」，一条黄褐色虚线箭头从这张卡笔直向上指进除号，旁边小字「分母在动」；除号向右一条青绿色箭头，通到两只并排的水桶，左桶宽、水面低，右桶窄、水面高，两桶水面各是一条青色虚线，桶下各有一行小字「水面＝读数」「水面更高」，两桶之间一道小箭头标「老化」；画面下三分之一并排三张卡片，依次写「分子」「分母」「除出来的读数」，卡片下面一行小字说明两个账谁也纠不了谁；最下方一条浅绿横条写结论。只用深墨线、一点青绿与一点那不勒斯黄，留白充足，不含任何数字与刻度，不出现坐标轴、仪表或示波器。
```

**English**

```
Style name: Geometric Literary Deadpan. Theme color: Naples Yellow. Reference author and style name: Tom Gauld. Core style traits: tiny geometric figures, minimal settings, literary and science jokes, deadpan humor; faces and clothing are reduced so that a clear silhouette, eyes, mouth and a few key shapes carry the character; expressions stay flat, awkward or suddenly exaggerated, with a definite comic rhythm in the posture. Scene: warm ivory paper background with one left-to-right pipeline. On the left a slightly tilted pale card labelled "hour ledger" with three short lines inside: "adds current times time", "correctness depends on current", "this is the numerator"; to its right a large circle holding a hand-drawn division sign; below the circle a card labelled "full-charge capacity" with two lines "this is the denominator" and "aging shrinks it", an ochre dashed arrow running straight up from that card into the circle, a small caption "the denominator moves"; a teal arrow leaves the circle to the right and reaches two side-by-side buckets, the left one wide with a low water line, the right one narrow with a high water line, each water line drawn as a teal dashed stroke, a caption under each bucket ("water line is the reading", "line sits higher"), a small arrow between the buckets labelled "aging"; the lower third holds three cards in a row ("numerator", "denominator", "the reading"), with a one-line caption that the two accounts cannot correct each other; at the bottom a pale green band carries the conclusion. Ink lines, one teal accent and a little Naples Yellow only, generous white space, no digits, no axes, gauges or oscilloscope.
```

#### s4-anchor-reset（阶段 4 · 三个锚点）

**中文**

```
风格名称：Geometric Literary Deadpan。主题色：那不勒斯黄（Naples Yellow）。参考作者与风格名称：Tom Gauld。核心风格特征：极小几何人物、极简场景、文学/科技梗、冷面幽默；脸部与服装主动做减法，依靠清楚轮廓、眼口和少量关键形状建立人物辨识度；表情偏冷脸、尴尬或突然夸张，姿态要有明确喜剧节奏。画面要求：暖象牙纸底，画面中部一条绿色水平虚线横贯，左端小字「真值」；真值线下方一条红色折线单向往下滑，在三个位置被竖直虚线截断并出现一段几乎垂直的跳回，跳到真值附近，每个跳回顶端一个绿色小圆点；三处竖直虚线顶端各有一行深色小标题，从左到右写「满充校准」「静置校准」「下电保存」；折线下方一条灰色细横轴，右端小字「时间」，左端小字「估算」；横轴下面并排三张卡片，依次写「满充判据」「静置条件」「保存校验」，每张卡里两行小字；最下方一条浅绿横条写结论。只用深墨线、一点绿、一点红与一点那不勒斯黄，留白充足，不含任何数字与刻度。
```

**English**

```
Style name: Geometric Literary Deadpan. Theme color: Naples Yellow. Reference author and style name: Tom Gauld. Core style traits: tiny geometric figures, minimal settings, literary and science jokes, deadpan humor; faces and clothing are reduced so that a clear silhouette, eyes, mouth and a few key shapes carry the character; expressions stay flat, awkward or suddenly exaggerated, with a definite comic rhythm in the posture. Scene: warm ivory paper background with a long green dashed horizontal line across the middle labelled "truth" at its left end; below that line a red polyline slides steadily downward and is cut three times by vertical dashed guides, each cut followed by a nearly vertical snap back up to the truth line, each snap topped by a small green dot; above the three guides, one short dark heading each, left to right: "full-charge calibration", "rest calibration", "power-down save"; under the polyline a thin grey time axis with "time" at the right end and "estimate" at the left; below the axis three cards in a row ("full-charge criteria", "rest condition", "stored-check"), two short lines of text inside each; at the bottom a pale green band carries the conclusion. Ink lines, a touch of green, a touch of red and a little Naples Yellow, generous white space, no digits, no scales.
```

#### s4-hppc-grid（阶段 4 · 参数表是一格一格打出来的）

**中文**

```
风格名称：Geometric Literary Deadpan。主题色：那不勒斯黄（Naples Yellow）。参考作者与风格名称：Tom Gauld。核心风格特征：极小几何人物、极简场景、文学/科技梗、冷面幽默；脸部与服装主动做减法，依靠清楚轮廓、眼口和少量关键形状建立人物辨识度；表情偏冷脸、尴尬或突然夸张，姿态要有明确喜剧节奏。画面要求：暖象牙纸底，左侧竖排三张浅绿小卡，依次写「荷电高」「荷电中」「荷电低」，卡内一行小字；每张卡右边一条短箭头，箭头上一行小字「脉冲」，指进一张浅色卡片，三张卡都写「一套参数」，卡内一行小字「欧姆内阻 · 极化支路」；三张参数卡各引出一条青色虚线，汇到一条竖直母线上，母线再一条带箭头的短线指进右侧一张高卡片；高卡片上半部写「合起来才是一张表」，下面两行小字，卡片中间一条细横线；高卡片下半部写「跨点硬套」，再两行小字；画面最下方一条浅绿横条写结论，横条下一行脚注小字。只用深墨线、一点青绿与一点那不勒斯黄，留白充足，不含任何数字、坐标轴或示波器。
```

**English**

```
Style name: Geometric Literary Deadpan. Theme color: Naples Yellow. Reference author and style name: Tom Gauld. Core style traits: tiny geometric figures, minimal settings, literary and science jokes, deadpan humor; faces and clothing are reduced so that a clear silhouette, eyes, mouth and a few key shapes carry the character; expressions stay flat, awkward or suddenly exaggerated, with a definite comic rhythm in the posture. Scene: warm ivory paper background; on the left a vertical stack of three pale green cards labelled "high state of charge", "mid state of charge", "low state of charge", one short line of text inside each; a short arrow with the caption "pulse" leaves each card to the right and enters a pale card labelled "one parameter set" carrying the line "ohmic resistance and polarization branch"; each of the three parameter cards sends a teal dashed line into a single vertical bus, and the bus feeds one short arrow into a tall card on the right; the upper half of the tall card reads "together they form a table" with two short lines beneath, a thin rule divides the card, the lower half reads "reused across points" with two more short lines; at the bottom a pale green band carries the conclusion and one footnote line beneath it. Ink lines, one teal accent and a little Naples Yellow, generous white space, no digits, no axes, no oscilloscope.
```

#### s4-residual-triage（阶段 4 · 残差的三种形状）

**中文**

```
风格名称：Geometric Literary Deadpan。主题色：那不勒斯黄（Naples Yellow）。参考作者与风格名称：Tom Gauld。核心风格特征：极小几何人物、极简场景、文学/科技梗、冷面幽默；脸部与服装主动做减法，依靠清楚轮廓、眼口和少量关键形状建立人物辨识度；表情偏冷脸、尴尬或突然夸张，姿态要有明确喜剧节奏。画面要求：暖象牙纸底，横向并排三张浅色卡片，卡内各画一条水平灰虚线当零线。第一张卡里一条绿线围着零线上下抖动，标题「围着零抖」；第二张卡里一条黄褐线整段压在零线一侧、几乎不再回来，标题「偏在一侧」；第三张卡里一条红线从零线出发越走越低、越走越开，标题「越走越开」；每张卡右下角一行小字「时间」；三张卡下面各有两行小字，依次写「只是噪声／动增益不算错」「参数漂了／先查温度与容量」「模型错了／别动滤波器，去修模型」；最下方一条浅绿横条写结论，横条下一行脚注小字。只用深墨线、绿、黄褐、红与一点那不勒斯黄，留白充足，不含任何数字与刻度。
```

**English**

```
Style name: Geometric Literary Deadpan. Theme color: Naples Yellow. Reference author and style name: Tom Gauld. Core style traits: tiny geometric figures, minimal settings, literary and science jokes, deadpan humor; faces and clothing are reduced so that a clear silhouette, eyes, mouth and a few key shapes carry the character; expressions stay flat, awkward or suddenly exaggerated, with a definite comic rhythm in the posture. Scene: warm ivory paper background; three pale cards side by side, each holding a horizontal grey dashed line as a zero line. In the first card a green line wiggles around the zero line, heading "wobbles around zero"; in the second a ochre line sits on one side of the zero line and stays there, heading "leans to one side"; in the third a red line leaves the zero line and diverges lower and wider, heading "opens up"; each card carries the small caption "time" at its lower right; under each card two short lines: "just noise / gain is fine", "parameter drift / check temperature and capacity", "model is wrong / leave the filter alone, fix the model"; at the bottom a pale green band carries the conclusion with one footnote line beneath. Ink lines, green, ochre, red and a little Naples Yellow, generous white space, no digits, no scales.
```

#### s4-sop-horizon（阶段 4 · 时间窗与电压墙）

**中文**

```
风格名称：Geometric Literary Deadpan。主题色：那不勒斯黄（Naples Yellow）。参考作者与风格名称：Tom Gauld。核心风格特征：极小几何人物、极简场景、文学/科技梗、冷面幽默；脸部与服装主动做减法，依靠清楚轮廓、眼口和少量关键形状建立人物辨识度；表情偏冷脸、尴尬或突然夸张，姿态要有明确喜剧节奏。画面要求：暖象牙纸底，左侧一个深色圆点标「此刻」，圆点向右分出三条虚线路径，像三根视线：第一条几乎水平、末端标「短窗口」；第二条缓缓下垂、末端标「中窗口」；第三条下垂最多、末端贴近画面下方一条红色水平虚线，标「长窗口」，红色虚线右端小字「电压下限」，虚线旁小字「贴墙」；三条路径上方一行小字说明两种消耗；画面下半部并排两张浅色卡片，左卡写「闭式除法」并两行小字，末行红字「报得偏大」，右卡写「逐秒向前推演」并两行小字，末行绿字「收得回来」；最下方一条浅绿横条写结论，横条下一行脚注小字。只用深墨线、绿、黄褐、红与一点那不勒斯黄，留白充足，不含任何数字与刻度。
```

**English**

```
Style name: Geometric Literary Deadpan. Theme color: Naples Yellow. Reference author and style name: Tom Gauld. Core style traits: tiny geometric figures, minimal settings, literary and science jokes, deadpan humor; faces and clothing are reduced so that a clear silhouette, eyes, mouth and a few key shapes carry the character; expressions stay flat, awkward or suddenly exaggerated, with a definite comic rhythm in the posture. Scene: warm ivory paper background; on the left a dark dot labelled "this instant", from which three dashed paths fan out to the right like three lines of sight: the first almost level, ending with the caption "short window"; the second sagging gently, ending with "medium window"; the third sagging furthest and ending just above a red dashed horizontal line near the bottom labelled "long window", the red line carrying "voltage floor" at its right end and the caption "touching the wall" beside it; a one-line caption above the paths names the two drains; the lower half holds two pale cards side by side: the left one "closed-form division" with two short lines and a red last line "reports too much", the right one "step-by-step rollout" with two short lines and a green last line "pulls it back"; at the bottom a pale green band carries the conclusion with one footnote line beneath. Ink lines, green, ochre, red and a little Naples Yellow, generous white space, no digits, no scales.
```

#### s4-ocv-temp-tables（阶段 4 · 温度分表）

**中文**

```
风格名称：Geometric Literary Deadpan。主题色：那不勒斯黄（Naples Yellow）。参考作者与风格名称：Tom Gauld。核心风格特征：极小几何人物、极简场景、文学/科技梗、冷面幽默；脸部与服装主动做减法，依靠清楚轮廓、眼口和少量关键形状建立人物辨识度；表情偏冷脸、尴尬或突然夸张，姿态要有明确喜剧节奏。画面要求：暖象牙纸底，左半部一张手绘小曲线图：竖直与水平两条灰细轴，纵轴顶端标「电压」，横轴右端标「荷电」；三条形状相同、上下错开的曲线，最上一条标「冷」、中间标「常温」、最下一条标「热」，三条曲线颜色分别是黄褐、青绿、红；一条深色水平虚线横穿三条曲线，标「量到的电压」，虚线与三条曲线各交于一个深色圆点，三个圆点各引一条竖直虚线落到横轴；曲线图下方一行小字说明三个交点落在不同荷电位置。右半部上下两张浅色卡片：上卡写「一张表跨温度」并两行小字，末行说偏差是系统的；一条红色短箭头从上卡指向下卡；下卡写「先量温度，再挑表」并两行小字，卡片下一行脚注小字。最下方一条浅绿横条写结论，横条下一行脚注小字。只用深墨线、黄褐、青绿、红与一点那不勒斯黄，留白充足，不含任何数字与刻度值。
```

**English**

```
Style name: Geometric Literary Deadpan. Theme color: Naples Yellow. Reference author and style name: Tom Gauld. Core style traits: tiny geometric figures, minimal settings, literary and science jokes, deadpan humor; faces and clothing are reduced so that a clear silhouette, eyes, mouth and a few key shapes carry the character; expressions stay flat, awkward or suddenly exaggerated, with a definite comic rhythm in the posture. Scene: warm ivory paper background; the left half holds a hand-drawn small plot with two thin grey axes, "voltage" at the top of the vertical axis and "state of charge" at the right end of the horizontal axis; three curves of the same shape offset vertically, the top one labelled "cold", the middle "room temperature", the bottom "hot", drawn in ochre, teal and red; a dark dashed horizontal line crosses all three curves labelled "the voltage we measured", meeting each curve at a dark dot, and each dot drops a vertical dashed line to the horizontal axis; one caption line under the plot says the three crossings sit at different states of charge. The right half holds two pale cards, one above the other: the upper reads "one table across temperatures" with two short lines ending in a note that the shift is systematic; a short red arrow points down from it to the lower card "measure temperature first, then pick the table" with two short lines, and one footnote line under the card. At the bottom a pale green band carries the conclusion with one footnote line beneath. Ink lines, ochre, teal, red and a little Naples Yellow, generous white space, no digits, no tick values.
```


### 4.6 阶段 5 · 通信与集成（3 张）

交付口径：`docs/视觉缺口表.md` A-18（阶段 5，下限 3 张）。当前入库的是同画风矢量版
（`docs/stages/assets/s5-*.svg`），本文件是 prompt 侧留档：后端恢复后按节重出 raster，
替换矢量文件即可；页面仍两行（图 + 看图），但图行的路径/扩展名要跟着改成 raster 文件。

画风：`FA-010` · Geometric Literary Deadpan（参考作者 Tom Gauld）；主题色 `C-27` 那不勒斯黄。
每张图零阿拉伯数字；画面内只出现中文标注。

#### s5-can-termination（阶段 5 · 终端只认线的两个尽头）

**中文**

```
风格名称：Geometric Literary Deadpan。主题色：那不勒斯黄（Naples Yellow）。参考作者与风格名称：Tom Gauld。核心风格特征：极小几何人物、极简场景、文学/科技梗、冷面幽默；脸部与服装主动做减法，依靠清楚轮廓、眼口和少量关键形状建立人物辨识度；表情偏冷脸、尴尬或突然夸张，姿态要有明确喜剧节奏。画面要求：暖象牙纸底，横向并排三块虚线圆角方框。每块方框里画一对平行的细线横着穿过，两条线之间加几道小斜杠表示两根线绞在一起；线端各有一只浅金色小方块把两条线连起来，代表终端电阻；波被接住的地方点一枚绿色小圆点，没被接住的地方画一条红色虚线箭头在端头打个弯、沿原路掉头往回走。左框只在左端有那只金色小方块，右端敞口，红色掉头箭头在右端；中框的金色小方块挪到正中，两端都敞口，两端各有一条红色掉头箭头；右框两端各有一只金色小方块，各有一枚绿点，没有红箭头。三块方框下面各两行小字，再往下一行说明文字，最下方一条浅绿横条写一句结论。全图只用深墨线、一点那不勒斯黄、一点绿与一点红，留白充足，不含任何文字之外的刻度与数字。
```

**English**

```
Style name: Geometric Literary Deadpan. Theme color: Naples Yellow. Reference author and style name: Tom Gauld. Core style traits: tiny geometric figures, minimal settings, literary and science jokes, deadpan humor; faces and clothing are reduced so that a clear silhouette, eyes, mouth and a few key shapes carry the character; expressions stay flat, awkward or suddenly exaggerated, with a definite comic rhythm in the posture. Scene: warm ivory paper background; three dashed rounded panels side by side. Each panel holds a pair of thin parallel lines running horizontally, with a few small slanted ticks between them so the pair reads as twisted; at a line end a small pale-gold square bridges the pair, standing for the terminator; where the wave is absorbed a small green dot sits, where it is not a red dashed arrow hooks at the open end and travels back along the line. The left panel has the gold square only at its left end and one red return arrow at its open right end; the middle panel has the gold square moved to the centre with both ends open and a red return arrow at each end; the right panel has a gold square and a green dot at both ends and no red arrow. Two short lines of caption sit under each panel, one explanatory line below them, and a pale-green strip at the bottom carries the conclusion. Ink lines, a little Naples Yellow, a little green and a little red only, generous white space, no numerals.
```

#### s5-crc-detect-only（阶段 5 · 校验只回答像不像）

**中文**

```
风格名称：Geometric Literary Deadpan。主题色：那不勒斯黄（Naples Yellow）。参考作者与风格名称：Tom Gauld。核心风格特征：极小几何人物、极简场景、文学/科技梗、冷面幽默；脸部与服装主动做减法，依靠清楚轮廓、眼口和少量关键形状建立人物辨识度；表情偏冷脸、尴尬或突然夸张，姿态要有明确喜剧节奏。画面要求：暖象牙纸底，左边横向一排六个小方格代表一帧，第三格涂成浅红，上方一行小字说明这一帧坏了一位；一根细箭头把这排方格送进中间一个左宽右窄的漏斗形框，框里写「校验」；漏斗窄口伸出一根箭头，指向一只浅金色小方块，方块里写「残余」；再一根箭头指向右侧一张卡片，卡片三行字：第一行问「哪一位坏了」，第二行答只回一句「不像」，第三行说残余里没有地址。下方一张横贯画面的浅色卡片两行字，说明整帧被压成一小截、要修得另加位置信息（纠错码带地址，否则只能重读、重传）；最下方一条浅绿横条写结论。全图只用深墨线、一点那不勒斯黄与一点红，留白充足，不含任何数字。
```

**English**

```
Style name: Geometric Literary Deadpan. Theme color: Naples Yellow. Reference author and style name: Tom Gauld. Core style traits: tiny geometric figures, minimal settings, literary and science jokes, deadpan humor; faces and clothing are reduced so that a clear silhouette, eyes, mouth and a few key shapes carry the character; expressions stay flat, awkward or suddenly exaggerated, with a definite comic rhythm in the posture. Scene: warm ivory paper background; a row of six small squares on the left stands for one frame, the third square tinted pale red, one small line of text above saying this frame has one bad bit; a thin arrow carries the row into a funnel-shaped box in the middle, wide on the left and narrow on the right, labelled "checksum"; from the narrow throat an arrow points to a small pale-gold square labelled "remainder"; another arrow points to a card on the right with three lines: the first asks "which bit is bad", the second answers with a single "does not match", the third says the remainder carries no address. Below, a wide pale card with two lines explains that the whole frame was squeezed into a short stub and that repair needs extra position information, which means an error-correcting code that carries addresses, or else a re-read or a full retransmission; a pale-green strip at the bottom carries the conclusion. Ink lines, a little Naples Yellow and a little red only, generous white space, no numerals.
```

#### s5-field-by-variation（阶段 5 · 只动一个量）

**中文**

```
风格名称：Geometric Literary Deadpan。主题色：那不勒斯黄（Naples Yellow）。参考作者与风格名称：Tom Gauld。核心风格特征：极小几何人物、极简场景、文学/科技梗、冷面幽默；脸部与服装主动做减法，依靠清楚轮廓、眼口和少量关键形状建立人物辨识度；表情偏冷脸、尴尬或突然夸张，姿态要有明确喜剧节奏。画面要求：暖象牙纸底，顶部并排两张浅色卡片，左卡写「只动一个量」、下面小字「其余量按住不动」，右卡写「连抓几帧，对齐」、下面小字「同一位置竖着比」，两卡之间一根细箭头相连。中段左侧竖排三行小字「第一次」「第二次」「第三次」，每行右边横排六个小方格，第三格涂成浅绿，格里画一条短横线，三行的短横线依次变长；其余五个格里的横线长度都一样。这列绿色小格右侧一行小字「只有这一列在动」，再接一根箭头指向右边一张浅绿卡片，卡片写「它就是那个量」，下面小字列出要记的项。再往下一条浅红卡片写反例：同时改两个量，两列一起动就分不清。最下方一条浅绿横条写结论，底下一行小字说明图上只画载荷列，帧尾校验位另算。全图只用深墨线、一点绿与一点红，留白充足，不含任何数字。
```

**English**

```
Style name: Geometric Literary Deadpan. Theme color: Naples Yellow. Reference author and style name: Tom Gauld. Core style traits: tiny geometric figures, minimal settings, literary and science jokes, deadpan humor; faces and clothing are reduced so that a clear silhouette, eyes, mouth and a few key shapes carry the character; expressions stay flat, awkward or suddenly exaggerated, with a definite comic rhythm in the posture. Scene: warm ivory paper background; two pale cards side by side at the top, the left one reading "change one quantity only" with a small line under it saying the others are held still, the right one reading "capture several frames, align them" with a small line saying compare the same position downwards, the two joined by a thin arrow. Below, three rows of small text on the left reading "first", "second", "third"; each row has six small squares to its right, the third square tinted pale green and carrying a short horizontal bar, and the bars in that green column grow longer row by row while the bars in the other five squares stay the same length. A small line of text right of the green column reads "only this column moves", followed by an arrow into a pale-green card on the right reading "so this is that quantity", with a small line listing what to record. Under it a pale-red card states the counter-example: changing two quantities at once makes two columns move and nothing can be attributed. A pale-green strip at the bottom carries the conclusion, and one small line notes that only payload columns are drawn and the checksum at the frame end must be kept out of the comparison. Ink lines, a little green and a little red only, generous white space, no numerals.
```


### 4.7 阶段 6 · 高压、安全与量产（6 张）

交付物是 6 张手绘风矢量（`docs/stages/assets/s6-*.svg`）。raster 通道不可用（见 `bms-book/ILLUSTRATION-PROMPTS.md` 顶部证据），按 §3.1 走矢量替代；本文件存档对应 prompt，后端恢复后按原样重出即可替换。

画风口径与参考图隔离块同 `bms-book/ILLUSTRATION-PROMPTS.md`：`FA-010` · Geometric Literary Deadpan（Tom Gauld），主题色 `C-27` · 那不勒斯黄（Naples Yellow），参考图 `C:\Users\zhugu\.agents\skills\handraw-style\images\individual\FA\FA-010.webp`。prompt 正文不带编号，画面不含任何文字、数字与刻度值。

#### s6-precharge-pulse（阶段 6 · 预充电阻的脉冲额定）

**中文**

```
风格名称：Geometric Literary Deadpan。主题色：那不勒斯黄（Naples Yellow）。参考作者与风格名称：Tom Gauld。核心风格特征：极小几何人物、极简场景、文学/科技梗、冷面幽默；脸部与服装主动做减法，依靠清楚轮廓、眼口和少量关键形状建立人物辨识度；表情偏冷脸、尴尬或突然夸张，姿态要有明确喜剧节奏。画面要求：暖象牙纸底，左上一颗立着的圆柱形电芯，顶上有正极凸台，一根深墨导线从电芯右侧引出向右，串上一只锯齿状电阻，再接到右方两块竖直极板并排组成的电容；导线在靠近电容处收成一个小箭头，表示电流先过电阻；电容上方一小片空白，一只极小的几何人物蹲在电阻下风处，双手抱头，示意它只承受这一次热。画面下半部左右两栏对照：左栏一团实心方块紧贴一只锯齿电阻，方块上方一道短促的粗弧线，像热一下子涌出；右栏一根细长的平条黏在同一只电阻上，平条旁一个小红叉，示意按平摊的热去买并不对。两栏之间一条竖直虚线分开，底部一条没有刻度的横线收口。全画只用深墨线、一点那不勒斯黄与一点红，留白充足，不含任何文字、数字与刻度值。
```

**English**

```
Style name: Geometric Literary Deadpan. Theme color: Naples Yellow. Reference author and style name: Tom Gauld. Core style traits: tiny geometric figures, minimal settings, literary and science jokes, deadpan humor; faces and clothing are reduced so that a clear silhouette, eyes, mouth and a few key shapes carry the character; expressions stay flat, awkward or suddenly exaggerated, with a definite comic rhythm in the posture. Scene: warm ivory paper background; at the upper left a standing cylindrical cell with a small positive terminal on top, a dark ink wire leaving its right side, running into a zigzag resistor, then into a capacitor drawn as two upright plates on the right; the wire narrows into a small arrowhead near the capacitor to show the current passing through the resistor first; just above the capacitor a tiny geometric figure crouches downwind of the resistor with both hands over its head, showing it takes the heat exactly once. The lower half is a two-column comparison: on the left a solid filled square pressed against a zigzag resistor with one short thick arc above it, as if the heat bursts out all at once; on the right a long thin flat strip glued to the same resistor with a small red cross beside it, showing that buying by the spread-out heat is wrong. A vertical dashed line separates the two columns, and a plain horizontal rule with no tick marks closes the bottom. Ink lines only, a touch of Naples Yellow and a touch of red, generous white space, no text, numerals or scale values.
```

#### s6-iso-double-leak（阶段 6 · 两端同时漏电）

**中文**

```
风格名称：Geometric Literary Deadpan。主题色：那不勒斯黄（Naples Yellow）。参考作者与风格名称：Tom Gauld。核心风格特征：极小几何人物、极简场景、文学/科技梗、冷面幽默；脸部与服装主动做减法，依靠清楚轮廓、眼口和少量关键形状建立人物辨识度；表情偏冷脸、尴尬或突然夸张，姿态要有明确喜剧节奏。画面要求：暖象牙纸底，左右并排两块虚线方框，框内各有三条水平深墨线，自上而下分别是正极母线、机壳与负极母线；两框的右侧都立着一位极小的几何人物，抬头看着框里的读数。左框：一只红色锯齿电阻把正极母线接到机壳线，机壳线到负极母线的那一段留出一个清楚的断口，断口旁一小段墨线挑出一枚小圆点，圆点落在机壳线上靠近正极的位置，示意电位被拉高。右框：正极到机壳、机壳到负极各串一只同样大小的红色锯齿电阻，机壳线上另有一枚小圆点停在正中，两个电阻各挂一滴红色小水珠，示意两边都在漏。两框下方各留一行空白，底部一条没有刻度的横线收口。全画只用深墨线、一点红与一点绿（断口那一侧用绿），留白充足，不含任何文字、数字与刻度值。
```

**English**

```
Style name: Geometric Literary Deadpan. Theme color: Naples Yellow. Reference author and style name: Tom Gauld. Core style traits: tiny geometric figures, minimal settings, literary and science jokes, deadpan humor; faces and clothing are reduced so that a clear silhouette, eyes, mouth and a few key shapes carry the character; expressions stay flat, awkward or suddenly exaggerated, with a definite comic rhythm in the posture. Scene: warm ivory paper background, two dashed boxes side by side, each holding three horizontal dark ink lines: the positive bus on top, the enclosure in the middle, the negative bus at the bottom; on the right edge of each box stands a tiny geometric figure looking up at the reading inside. Left box: a red zigzag resistor joins the positive bus to the enclosure line, while the segment from the enclosure down to the negative bus carries one clear break; beside the break a short ink tick draws out a small dot that sits on the enclosure line close to the positive side, showing the potential pulled high. Right box: two equally sized red zigzag resistors, one from the positive bus to the enclosure and one from the enclosure to the negative bus, with a small dot resting exactly midway on the enclosure line, and one red droplet hanging from each resistor, showing both sides leaking. A blank strip sits under each box and a plain rule with no tick marks closes the bottom. Ink lines, a touch of red and a touch of green on the intact side, generous white space, no text, numerals or scale values.
```

#### s6-common-cause（阶段 6 · 共因失效）

**中文**

```
风格名称：Geometric Literary Deadpan。主题色：那不勒斯黄（Naples Yellow）。参考作者与风格名称：Tom Gauld。核心风格特征：极小几何人物、极简场景、文学/科技梗、冷面幽默；脸部与服装主动做减法，依靠清楚轮廓、眼口和少量关键形状建立人物辨识度；表情偏冷脸、尴尬或突然夸张，姿态要有明确喜剧节奏。画面要求：暖象牙纸底，左右并排两块虚线方框，每框自上而下三块牌子：一块红牌、一块黄牌、两块并排的白牌。左框：红牌上只画一道闪电形折线，黄牌上画三枚紧挨着的小方钉（同一路供电、同一个基准、同一条线束），两枚红色箭头从黄牌底部同时分叉落下，各抵住一块白牌，两块白牌边各打一个红叉；一位极小的几何人物站在左下角摊手。右框：同样的红牌，但只有一枚红色箭头落向左边那块白牌，那牌上打一个红叉；右边那块白牌头顶多一枚小小的绿方钉，旁边一道绿勾，牌面完好，一位极小的几何人物站在右侧举手示意它还醒着。两框下方各留一行空白，底部一条没有刻度的横线收口。全画只用深墨线、一点那不勒斯黄、一点红与一点绿，留白充足，不含任何文字、数字与刻度值。
```

**English**

```
Style name: Geometric Literary Deadpan. Theme color: Naples Yellow. Reference author and style name: Tom Gauld. Core style traits: tiny geometric figures, minimal settings, literary and science jokes, deadpan humor; faces and clothing are reduced so that a clear silhouette, eyes, mouth and a few key shapes carry the character; expressions stay flat, awkward or suddenly exaggerated, with a definite comic rhythm in the posture. Scene: warm ivory paper background, two dashed boxes side by side, each holding three stacked placards: a red one, a yellow one, then two white ones side by side. Left box: the red placard carries a single lightning-shaped zigzag, the yellow placard carries three small nails pressed together (one supply, one reference, one harness), and two red arrows leave the bottom of the yellow placard and fan out at once, each landing on one white placard; a red cross is drawn on each white placard; a tiny geometric figure stands at the lower left with open palms. Right box: the same red placard, but only one red arrow drops toward the left white placard, which gets a red cross; the right white placard has a small green nail above it and a green tick beside it, its face intact, with a tiny geometric figure on the right raising one hand to show it is still awake. A blank strip sits under each box and a plain rule with no tick marks closes the bottom. Ink lines, a touch of Naples Yellow, red and green, generous white space, no text, numerals or scale values.
```

#### s6-dtc-maturity（阶段 6 · 故障从毛刺到确诊）

**中文**

```
风格名称：Geometric Literary Deadpan。主题色：那不勒斯黄（Naples Yellow）。参考作者与风格名称：Tom Gauld。核心风格特征：极小几何人物、极简场景、文学/科技梗、冷面幽默；脸部与服装主动做减法，依靠清楚轮廓、眼口和少量关键形状建立人物辨识度；表情偏冷脸、尴尬或突然夸张，姿态要有明确喜剧节奏。画面要求：暖象牙纸底，一条水平路径从左向右串起四段：一块白牌（牌面画一条越过横线的短折线）、四枚并排小方格（前两枚填实、后两枚空心）、一块白牌（牌面画一枚落下的印章）、四枚并排小方格（一枚填实、三枚空心），最后一块白牌（牌面画一枚对勾）；各段之间用带箭头的小段墨线相连，箭头朝右。确诊那块白牌的上方另有一块黄牌，牌面画一把小锁，一条单向虚线箭头从白牌向上指向黄牌，虚线旁没有回程箭头。路径下方一块小白牌画一根先竖起再被削平的尖刺，尖刺右边三枚空心方格，示意毛刺没有走满。一位极小的几何人物站在路径右端，手里牵着一根细线，线上挂着最后那块白牌。底部一条没有刻度的横线收口。全画只用深墨线、一点那不勒斯黄、一点红与一点绿，留白充足，不含任何文字、数字与刻度值。
```

**English**

```
Style name: Geometric Literary Deadpan. Theme color: Naples Yellow. Reference author and style name: Tom Gauld. Core style traits: tiny geometric figures, minimal settings, literary and science jokes, deadpan humor; faces and clothing are reduced so that a clear silhouette, eyes, mouth and a few key shapes carry the character; expressions stay flat, awkward or suddenly exaggerated, with a definite comic rhythm in the posture. Scene: warm ivory paper background; a horizontal path runs left to right through four stops: a white placard showing a short zigzag crossing a straight line, four small squares in a row with the first two filled and the last two hollow, a white placard showing a stamp coming down, four small squares with one filled and three hollow, and a final white placard showing a tick; short ink segments with arrowheads join the stops, all pointing right. Above the stamp placard hangs a yellow placard with a small padlock, and a one-way dashed arrow runs up from the stamp placard to it, with no return arrow beside it. Below the path a small white placard shows a spike that rises then is cut flat, with three hollow squares to its right, showing the glitch never filled the row. A tiny geometric figure stands at the right end of the path holding a thin cord that carries the last placard. A plain rule with no tick marks closes the bottom. Ink lines, a touch of Naples Yellow, red and green, generous white space, no text, numerals or scale values.
```

#### s6-ota-ab（阶段 6 · 双区升级与回滚）

**中文**

```
风格名称：Geometric Literary Deadpan。主题色：那不勒斯黄（Naples Yellow）。参考作者与风格名称：Tom Gauld。核心风格特征：极小几何人物、极简场景、文学/科技梗、冷面幽默；脸部与服装主动做减法，依靠清楚轮廓、眼口和少量关键形状建立人物辨识度；表情偏冷脸、尴尬或突然夸张，姿态要有明确喜剧节奏。画面要求：暖象牙纸底，左侧上下各一只小盒：上面是一只扎着纸带的包裹盒（升级包），下面是一只带挂锁的小盒（bootloader），锁扣画成闭合的扣环。中部一块白牌在上（备用区，牌面画一支正在写字的笔尖），一块红牌在下（写入中断电，牌面画一圈断开的箭头），最下面一块白牌（现用区，牌面画一张摊开的旧纸）。包裹盒向右引出一枚小箭头指向上面那块白牌；带锁的小盒向右引出一枚小箭头指向下面那块白牌。右上方一列四个小牌自上而下被箭头串起：写、校验（一枚对勾）、翻标记（一枚拨杆）、重启（一枚转动的箭头）；这一列底部并排两块牌，左边一块绿牌画对勾，右边一块红牌画回退箭头。一条细虚线从红牌出发，沿画面右缘绕回第三个牌（拨杆），旁边不加文字，只画一个指向左的小箭头。一位极小的几何人物站在两册白牌之间，手里拿着一枚小旗。全画只用深墨线、一点那不勒斯黄、一点红与一点绿，留白充足，不含任何文字、数字与刻度值。
```

**English**

```
Style name: Geometric Literary Deadpan. Theme color: Naples Yellow. Reference author and style name: Tom Gauld. Core style traits: tiny geometric figures, minimal settings, literary and science jokes, deadpan humor; faces and clothing are reduced so that a clear silhouette, eyes, mouth and a few key shapes carry the character; expressions stay flat, awkward or suddenly exaggerated, with a definite comic rhythm in the posture. Scene: warm ivory paper background; on the left two small boxes stacked: above, a parcel box tied with paper tape (the update package), below, a small box with a closed padlock (the bootloader), the shackle drawn shut. In the middle a white placard sits on top (the spare region, carrying a writing nib), a red placard sits below it (power lost mid-write, carrying a broken circular arrow), and a white placard at the bottom (the running region, carrying an unfolded old sheet). A small arrow leaves the parcel box to the right and points at the upper white placard; a small arrow leaves the padlocked box to the right and points at the lower white placard. At the upper right a column of four small placards is threaded by arrows from top to bottom: writing, verifying (a tick), flipping the marker (a toggle lever), restarting (a turning arrow); beside the bottom of that column two placards sit side by side, a green one with a tick and a red one with a roll-back arrow. A thin dashed line starts at the red placard, runs along the right edge of the frame and returns to the third placard with the lever, ending in a small leftward arrowhead and carrying no text. A tiny geometric figure stands between the two middle placards holding a little flag. Ink lines, a touch of Naples Yellow, red and green, generous white space, no text, numerals or scale values.
```


#### s6-mislabeled-cell（阶段 6 · 总电压及格，替不了逐串对标准源）

**中文**

```
风格名称：Geometric Literary Deadpan。主题色：那不勒斯黄（Naples Yellow）。参考作者与风格名称：Tom Gauld。核心风格特征：极小几何人物、极简场景、文学/科技梗、冷面幽默；脸部与服装主动做减法，依靠清楚轮廓、眼口和少量关键形状建立人物辨识度；表情偏冷脸、尴尬或突然夸张，姿态要有明确喜剧节奏。画面要求：暖象牙纸底，左右两块米黄卡片。左卡自上而下三只方块：前两只浅绿底，分别写「总电压及格」「通信能通」，方块右侧各有一枚小小的对勾；第三只浅金底写「没有逐串对标准源」，右侧一枚空缺；卡底一只浅红底小方块写「结果：错芯出厂」。右卡上方横向排开四只扁长方形电芯，第三条用浅红底与红边单独描出，卡顶一条深墨导线自左向右穿过四只并收成箭头，表示充电电流灌进来；那只红色电芯下方一根短竖线接一只浅红小方框写「保护切断」，旁边两行小字：「保护动作是对的」「切断解释不了为什么只有它高」。画面最下方一条横贯的长条卡片写「对不上就停用这一台」。
```

**English**

```
Style name: Geometric Literary Deadpan. Theme color: Naples Yellow. Reference author and style name: Tom Gauld. Core style traits: tiny geometric figures, minimal settings, literary and science jokes, deadpan humor; faces and clothing are reduced so that a clear silhouette, eyes, mouth and a few key shapes carry the character; expressions stay flat, awkward or suddenly exaggerated, with a definite comic rhythm in the posture. Scene: warm ivory paper background with two cream cards side by side. The left card stacks three blocks: the first two in pale green reading "total voltage within window" and "comms alive", each with a small check mark at its right edge; the third block in pale gold reads "no per-cell check against a reference source" and its check position stays empty; at the card foot a small pale red box reads "result: a mismatched cell ships". The right card shows four flat cell rectangles in a row, the third drawn alone in pale red with a red outline, a dark ink wire running left to right through all four and ending in an arrowhead to show the charging current; under the red cell a short vertical line drops into a pale red box reading "protection trips", with two small lines beside it: "the trip is correct" and "the trip does not explain why only this one is high". Along the bottom a long strip card reads "if the identity does not reconcile, stop using this pack".
```


### 4.8 阶段 7 · BMS × AI（1 张）

交付口径：`docs/视觉缺口表.md` A-20（阶段 7，下限 1 张）。当前入库的是同画风矢量版
（`docs/stages/assets/s7-known-quantity-diff.svg`），本文件是 prompt 侧留档：后端恢复后按节重出 raster，
替换矢量文件即可；页面仍两行（图 + 看图），但图行的路径/扩展名要跟着改成 raster 文件。

画风：`FA-010` · Geometric Literary Deadpan（参考作者 Tom Gauld）；主题色 `C-27` 那不勒斯黄。
每张图零阿拉伯数字；画面内只出现中文标注。

#### s7-known-quantity-diff（阶段 7 · 改一个已知量，找出那一列）

**中文**

```
风格名称：Geometric Literary Deadpan。主题色：那不勒斯黄（Naples Yellow）。参考作者与风格名称：Tom Gauld。核心风格特征：极小几何人物、极简场景、文学/科技梗、冷面幽默；脸部与服装主动做减法，依靠清楚轮廓、眼口和少量关键形状建立人物辨识度；表情偏冷脸、尴尬或突然夸张，姿态要有明确喜剧节奏。画面要求：暖象牙纸底，构图按「改一处、抓两次、逐格比、才提问」四步从上往下走。左上角一张微微歪斜的浅色卡片，写「动一个已知量」和「只改这一项，别的照旧」；它下面一张浅金卡片，写「逐格比一遍」「只有一列不一样」「其余列逐格相同」。画面右上方并排两行小方格，每行十格、格子等宽、同一列上下对齐：上一行标「第一次抓包：什么都没动」，格子全是浅色；下一行标「第二次抓包：只改了一个量」，其中第五格换成浅绿底、青绿描边的格子，其余九格仍是浅色。从这个浅绿格向上、向下各引一条细虚线，把两行的同一列串起来，旁边一行小字「同一列」；浅绿格再向下引一条虚线，落到右下角一张浅绿卡片上，卡片写「动过的那一列，就是它」「改哪个量，就看哪一列先动」「没动的列正好当反证」。一条虚线从这张卡片斜着连到左下角一张浅色卡片，卡片写「有对照，才轮得到模型」「问的是这一列是什么，它给的仍是候选」。画面底部一条浅绿长条，写「改一个已知量，只有一列跟着动，这一列才拿得去核模型的话」；长条下面一行小字「先有对照，再问模型；顺序反了，答得再顺也只是印象」。全画只用深墨线、一点青绿与一点绿，线条手绘感、留白充足，不含任何文字以外的数字与刻度值。
```

**English**

```
Style name: Geometric Literary Deadpan. Theme color: Naples Yellow. Reference author and style name: Tom Gauld. Core style traits: tiny geometric figures, minimal settings, literary and science jokes, deadpan humor; faces and clothing are reduced so that a clear silhouette, eyes, mouth and a few key shapes carry the character; expressions stay flat, awkward or suddenly exaggerated, with a definite comic rhythm in the posture. Scene: warm ivory paper background, the composition runs top to bottom as "change one thing, capture twice, compare cell by cell, then ask". A slightly tilted pale card at the upper left reads "move one known quantity" and "only this one, everything else untouched"; a pale gold card below it reads "compare cell by cell", "only one column differs", "the other columns are identical". At the upper right sit two rows of ten small squares each, equal width, columns aligned: the first row is captioned "first capture: nothing was touched" and is entirely pale; the second row is captioned "second capture: one quantity was changed" and its fifth square is filled pale green with a teal outline while the other nine stay pale. A thin dashed line runs up and down from that green square, threading the same column through both rows, with a small label "same column" beside it; another dashed segment drops from the green square onto a pale green card at the lower right reading "that changed column is the one", "whichever quantity you move, watch which column moves first", "the untouched columns serve as the counter-check". A dashed line slants from that card to a pale card at the lower left reading "only after the comparison does the model get a turn" and "you ask what this column is, and it still only offers candidates". A pale green band along the bottom reads "move one known quantity, only one column follows, and only that column can be taken to check what the model says"; one small line under it reads "compare first, ask second; reverse the order and even a fluent answer is only an impression". Hand-drawn ink lines, generous white space, only dark ink, a little teal and a little green, no numbers and no scales.
```
