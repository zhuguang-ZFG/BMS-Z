# 生动化方案：动画节奏升级 + 交互演示加深（2026-10-31）

与 §11.11 场景化插图（v3.72 已上线两张：`ch11-two-stage-chain.svg`、`ch11-miller-charge.svg`）同轮定稿的后续两条线。参考对象均为开源项目：manim（3Blue1Brown，MIT）、Explorable Explanations（Nicky Case，CC0/公共领域）、Falstad CircuitJS（GPLv2，本书已有 40+ 处外链）。

## A · 动画节奏升级（108 张 SMIL）

现状：节拍系统 = `scripts/generate_svgs.py` 的 `_BEATS` + `caption()`（每拍一条字幕，`keyTimes` 线性推进）+ `trace2()`（波形描边 0.85 时刻起步）+ `flow()`（电流粒子匀速）+ `note_box()`（结论卡 0.82 时刻弹出）。所有拍子**线性推进、同速同权**，没有「先让你看这里」的视线管理。

manim 的四条可搬原则（`manim.animation` 的实现语义，非审美口号）：

1. **缓动非线性**：manim 默认 `rate_functions.ease_in_out`，运动两端慢、中间快。我们的 `flow()` 粒子与 `trace2()` 描边是线性速率。落法：`flow()` 的 `keyTimes` 从 `[0;1]` 两点改为四点缓动采样（0;0.35;0.65;1 配 keySplines 或加密采样点），改一个函数、108 张图全部受益，无需逐图改。
2. **逐拍揭示（progressive build）**：manim 一场戏一次只引入一个对象。我们不少图（如 `*-four-beats` 系列）四拍字幕齐上、图元全程在场。落法：给 `caption()` 加 `reveal=` 参数——字幕所属拍的图元挂同一 keyTimes 的 opacity 0→1 过渡，拍与拍之间旧图元降到 30% 透明度（manim 的 `FadeToColor` 等价）。改动集中在 `beat_captions()` 与各图拍登记处，先改 3 张样板（`mosfet-four-beats`、`555-astable-beats`、`miller-effect`）测观感。
3. **视线引导（focus）**：manim 用 `FocusOn`/`Indicate`（闪烁放大）指认主角。落法：`note_box()` 弹出前 0.2 拍，对当拍主角图元做一次 1.0→1.06→1.0 的缩放脉冲（`pulse()` 已有，改 keyTimes 复用），成本一处。
4. **注记接力**：manim 的 `TransformMatchingText` 让上一句字幕演化成下一句。SMIL 做不到文本 morph，但可做位置接力：`beat_captions()` 里相邻拍字幕若共享前缀（「先……再……」结构），后拍从上一拍的位置淡入而非固定 y。改 `_wrap`/`beat_captions` 的坐标计算。

成本与边界：①②③ 合计改 `generate_svgs.py` 四个函数 + 108 张重生成（`python scripts/generate_svgs.py`，几分钟）；护栏 `test_svg_assets`（对账 work 副本）、`test_svg_layout`、`test_waveform_timing`、`test_reduced_motion` 全量复跑。**不动**：无 `feTurbulence` 铁律（HANDRAW-STYLE.md §2，移动端帧率与印刷不可逆）。

## B · 交互演示加深（就地算）

现状：7 只计算器 = `scripts/site_media/calc.js` 的 `CALCS` spec 表（key/label/unit/value/step/min + 一个 compute），`docs/` 里放 `<div class="calc" data-calc="…">`，打印端隐藏控件只留手算（`check_calculator_fallbacks` 护住「例 N-x/算一笔」兜底，`test_calcs.py` 用正文原数回归默认值）。

EE/Falstad 的两条可搬做法：

1. **读数之外给曲线**（EE 的 live chart 惯例）：Miller 电容是目前最痛的「只给三个数」的算例（§11.11 例 11-3：C_in、 f_p、三条路）。落法：新 spec `miller`，输入增益 |A| 与源阻 Rs，除 C_in/f_p 读数外画一条 f_p(Rs) 或 f_p(|A|) 曲线（canvas 或 inline SVG，纯 JS 无依赖，~60 行），当前工作点高亮。`FALLBACK_RE` 不变（「算一笔」字样保留），打印端照旧隐藏。
2. **多预设一键切换**（Falstad 的 circuit menu 思路）：给既有 `div-load`（分压器带载）加 3 个预设按钮（空载 / 10k / 1k），点一下把滑块组打到预设值——教学上「同一电路三种命运」比自由拖更聚焦。落法：spec 加 `presets` 数组，`build()` 里渲染按钮行，test_calcs 对每只预设回归一次正文原数。

候选第三只（再议）：Buck 占空比（13 章 §13.2）联动纹波曲线。

两个护栏前置检查：新增 spec 必须让 `test_calcs.py` 的「正文原数回归」逐条过（默认值 = 正文算例原数，v3.58 铁律）；曲线/预设是纯增强，JS 关闭时算例正文仍是完整兜底（无障碍与打印审计不漂移）。

## 排期建议

A1（缓动）+ B1（Miller 曲线）先行：改动面小、收益立见、护栏现成；A2（逐拍揭示）需要逐图登记拍元归属，放第二批；A3/A4/B2 视观感反馈再定。
