---
search: false
slug: ai-context-vs-truth
style: FA-029
colors: [C-03, C-15]
frames: 6
caption: 原理示意 / 非实拍
bans: [no-people, no-cartoon-IP, no-live-photo-claim]
kp_id: ai-boundary
source_svg: docs/circuits/assets/ai-context-vs-truth.svg
---

# 观察题

同一个问题问两遍会得到两个都挺像的答案——看这张图怎么做减法：哪一栏能当依据，越界的那一刻又被推回哪里。

# 帧大纲

1. 空桌与分界：纸面正中一根竖直虚线把画面切成两栏，左表头「你贴进去的（证据）」、右表头「它凭记忆答的（印象）」，两栏都还空着。
2. 左栏落卡：四张等宽卡片自上而下依次落位——datasheet 片段、寄存器映射表、抓包日志、仓库正文，每张下面一行小字说明它凭什么可查；底部压一条「凡是阈值 / 位宽 / 单位，只认这一边」。
3. 右栏落卡：四张同样尺寸的卡片落在镜像的同一组行位上——参数量里的世界知识、上一个项目的习惯、看着像的相似型号、很顺的解释；形状相同、来源不同，边框换成 C-03 虚线，底栏写「它给的每一个数都要重新取证」。
4. 对位与错位：四根水平对齐线把左右两栏一一配对；配到「相似型号」那一行时，对齐线断开一格——差一个后缀，保护点就换了一档。
5. 越界被打回：右栏的一个数越过中线，被一条虚线箭头推回左上角；中线上那个回折点是全图唯一 C-15 标记，上方小字「越界就打回 / 不是它说错了，是你不该这样问」。
6. 收束：底部口诀落定——数值只认原文，机制随便问；通顺不等于对，能回链才算证据；两条路由分开，右栏那句「同一个模型的两次回答可以互相矛盾，而 datasheet 的两页不会」压在角落。

# Prompt（EN）

Hand-drawn educational information drawing, FA-029 Chris Ware geometric narrative style: flat rectangular panels on a ruler-straight grid, tiny hand-lettered captions, clean diagrammatic rhythm, generous margins, paper grain. All structure lines, panel borders and labels in Prussian blue C-03. The second column is a category, not a hazard, so it is drawn as a C-03 dashed contour rather than the source's red boxes. Vermilion C-15 appears exactly once, as the small fold-back point on the centre divider where an answer is pushed back — never as a large fill, never as a whole red column.

Six frames of the same two-column sheet, same viewpoint, no people, no cartoon mascot, no anthropomorphic robot or AI face, no brand logos, no photorealistic claim, schematic only:

Frame 1 — empty sheet: one vertical dashed divider cuts the page into two columns; the left header reads 你贴进去的（证据）, the right header reads 它凭记忆答的（印象）, both columns still empty.
Frame 2 — left column fills: four equal-width cards drop in top to bottom — datasheet 片段, 寄存器映射表, 抓包日志, 仓库正文 — each with one small line saying why it can be traced; a footer rule reads 凡是阈值 / 位宽 / 单位，只认这一边.
Frame 3 — right column fills: four cards of identical size land on mirrored row positions — 参数量里的世界知识, 上一个项目的习惯, 看着像的相似型号, 很顺的解释 — same shape, different provenance, borders switched to C-03 dashed; footer reads 它给的每一个数都要重新取证.
Frame 4 — pairing: four horizontal alignment rules join left cards to right cards one for one; at the 相似型号 row the rule breaks by one notch — 差一个后缀，保护点就换了一档.
Frame 5 — crossing rejected: one number from the right column crosses the divider and a dashed arrow shoves it back toward the upper left; the fold-back point on the divider carries the only C-15 mark, labelled 越界就打回 / 不是它说错了，是你不该这样问.
Frame 6 — closing panel: the maxim settles at the bottom — 数值只认原文，机制随便问；通顺不等于对，能回链才算证据 — with two separate route arrows, and a corner note: 同一个模型的两次回答可以互相矛盾，而 datasheet 的两页不会.

No on-board threshold appears anywhere in the picture; all text stays as small hand-lettered annotation. Caption: 原理示意 / 非实拍.

# Prompt（ZH）

手绘教学信息图，FA-029 Chris Ware 几何叙事风格：尺规般平直的矩形分栏、细密的手写小注、干净的图版节奏、大片页边、纸纹质感。结构线、栏框与标注全部用 C-03 普鲁士蓝。右栏是一种「类别」而不是危险，所以画成 C-03 虚线轮廓，不用原图那种红框铺面。C-15 朱砂红全图只出现一次，落在中线上那个被推回的回折点；不铺大面积、不整栏上色。

同一张两栏纸、同一视角的六个帧，无人、无卡通吉祥物、无人格化的机器人面孔、无品牌 Logo、不写实拍，纯示意：

1. 空桌与分界：一根竖直虚线把纸切成两栏，左表头「你贴进去的（证据）」，右表头「它凭记忆答的（印象）」，两栏都空着。
2. 左栏落卡：四张等宽卡片自上而下依次落位——datasheet 片段、寄存器映射表、抓包日志、仓库正文，每张配一行小字说明凭什么可查；底部压一条「凡是阈值 / 位宽 / 单位，只认这一边」。
3. 右栏落卡：四张同尺寸卡片落在镜像的行位上——参数量里的世界知识、上一个项目的习惯、看着像的相似型号、很顺的解释；形状一样、来源不同，边框改成 C-03 虚线，底栏写「它给的每一个数都要重新取证」。
4. 对位与错位：四根水平对齐线左右一一配对；到「相似型号」这一行，对齐线断开一格——差一个后缀，保护点就换了一档。
5. 越界被打回：右栏一个数越过中线，虚线箭头把它推回左上；中线上那个回折点是全图唯一 C-15，旁边小字「越界就打回 / 不是它说错了，是你不该这样问」。
6. 收束：底部口诀落定——数值只认原文，机制随便问；通顺不等于对，能回链才算证据；两条路由箭头分开，角落再压一句「同一个模型的两次回答可以互相矛盾，而 datasheet 的两页不会」。

全图不出现任何可上板的阈值，文字一律是小号手写标注。图注：原理示意 / 非实拍。

# 验收自检

- [ ] 无人、无卡通、无人格化 AI 面孔
- [ ] 危险仅 C-15，且只有一处（中线上的回折点）
- [ ] 右栏没有被整栏铺红，改为 C-03 虚线轮廓
- [ ] 图注将用「原理示意 / 非实拍」
- [ ] 六帧同一张两栏纸、同一视角，可暂停阅读
- [ ] 首末帧单独成图仍可读（左证据 / 右印象的分界仍在）
- [ ] 全图不含任何可上板的阈值数字
