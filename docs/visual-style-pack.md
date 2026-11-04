# 视觉画风包（BMS-Z）

> 状态：**画风定稿**（2026-11-04）。逐张验收另行记录（第一批 20 张，见 `docs/circuits/handraw/`）。
> 上位合同：`docs/superpowers/specs/2026-11-04-handraw-visual-overhaul-design.md` §2；验收：同文 §5.1。

## 定稿

| 项 | 定稿 |
|----|------|
| 主画风 | **FA-002 Saul Steinberg** — 连续线概念图 |
| 辅画风 | **FA-029 Chris Ware** — 几何叙事图 |
| 主色 | **C-03 普鲁士蓝** |
| 危险点缀 | **仅 C-15 朱砂红** |
| 图注 | **原理示意 / 非实拍** |

### 选用规则

- **FA-002（机制）**：机制因果、电流路径、保护动作链、时序因果、物理量沿路径的变化。读者要记住的是「过程」。
- **FA-029（信息结构）**：对照、分层、路线图、预算账、误差瀑布、边界条件。读者要记住的是「结构」。
- 一张图只允许一种主画风。需要混排时，按「读者最终要复述的是过程还是结构」定，不按画面元素多少定。

### 色板

| 合同名 | 含义 | 近似色值 | 用法 |
|--------|------|----------|------|
| C-03 | 普鲁士蓝 | `#003153` | 结构线、标注、常规路径；第二组对比曲线用虚线/细线区分，仍用 C-03 |
| C-15 | 朱砂红 | `#E34234` | 仅危险 / 切断 / 越限；点状或短线段，不铺面 |

**合同名优先于 hex**：渲染偏色时以 C-03 / C-15 的语义为准，不以取色器为准。

## 禁区

- 无人、无卡通 IP、无萌系角色、无假品牌 Logo。
- 不写「实拍」「示波器截屏」「真机照片」。
- 不大面积铺 C-15；不引入第三主色。
- 不把静态帧伪装成假 SMIL 动画。

反例（出现即判不合格）：

1. 整片朱红当背景或大面积危险色块——危险只剩一个「点」，不是一层「底色」。
2. 给电芯画表情 / 卡通脸 / 拟人吉祥物——机制图不带角色。
3. 图注写「示波器实拍」「实测截图」——统一「原理示意 / 非实拍」。

## 图注合同

每图必须带 **「原理示意 / 非实拍」**。正文链接处保留观察题；观察题只问「看什么」，不提前给答案。

## 与动画画风规范的过渡

- 未归档旧 SVG 仍守 `docs/circuits/动画画风规范.md`（`viewBox` 800、SMIL、类名配色）。
- handraw 产物**不要求** `viewBox 800` 与类名配色体系；但导出动画须**可暂停**，首末帧须**静态可读、可打印**。
- 同一图不得双源并存：换链完成后旧 SVG 进 `archive/`，正文与索引只留 handraw 路径。

## 提示词模板

### FA-002 机制

```text
Hand-drawn educational mechanism diagram, FA-002 Saul Steinberg continuous-line style:
one unbroken ink contour, generous white space, deadpan textbook tone, paper grain.
Primary linework and labels in Prussian blue C-03 only; vermilion C-15 only at the
danger / cutoff / limit instant, small and never as fill. No people, no cartoon mascot,
no brand logos, no photorealistic or oscilloscope-screenshot claim. Schematic only.
Frames: <3–8 帧，逐帧写「什么在变」>.
Caption: 原理示意 / 非实拍.
```

### FA-029 信息结构

```text
Hand-drawn educational information diagram, FA-029 Chris Ware geometric narrative style:
flat geometric panels, precise ruled framing, restrained deadpan composition, paper grain.
Primary linework and labels in Prussian blue C-03 only; vermilion C-15 reserved for the
single hazard / cutoff / limit boundary. No people, no cartoon mascot, no brand logos,
no photorealistic claim. Schematic only.
Frames: <3–8 帧，逐帧写层级/路线/对照如何展开>.
Caption: 原理示意 / 非实拍.
```

要求：帧数 3–8；**纯图**（提示词里不写 slug、KP 编号等 ID）；数字只用源图已有值，并保留「示意」标记。

## 抽检表

- [ ] 无人、无卡通 IP
- [ ] 色板：C-03 主色，危险仅 C-15
- [ ] 图注含「原理示意 / 非实拍」
- [ ] 动画可暂停
- [ ] 正文有观察题
- [ ] 首末帧静态可读
