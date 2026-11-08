# 深研样章（P1）

这里是 BMS v3 深度改造的 P1 样章工作区。正文暂时独立存放，**不进入** `bms-book/book/` 的 32 章清单：书稿章数与导航由 `docs/.vitepress/book-sources.mjs` 枚举，提前塞入会破坏构建门。P2 装配时再决定章节编号、导航与页面组件。

## 当前状态

| 单元 | 正文 | 图 | 参考实现 + 测试 | 状态 |
|---|---|---|---|---|
| S2 一条电压曲线能识别出多少东西 | [S2-一条电压曲线能识别出多少东西.md](S2-一条电压曲线能识别出多少东西.md) | 5 张 SVG + 1 张概念图（`engineering/assets/s2-model/`） | `code/engineering/identification/`（20 项测试） | 数值复算与图像几何检查通过；P2 装配/独立审读待验 |
| S1 测量链 | [S1-精度够了保护为什么反而慢了.md](S1-精度够了保护为什么反而慢了.md) | 4 张 SVG（`engineering/assets/s1-measurement/`，F1 机制路径图） | `code/engineering/measurement/`（23 项测试） | 数值复算/结构检查通过；390/820 px、A4、真人试读待 P2 |
| S3 预充时序 | 未开始 | — | — | 未开工 |

S2 的"可复算"指：正文、图源生成、参考实现、窄测试、留出验证与反例都能从冻结配置重跑。它**不**包含：

- 独立工程审读与最终出版链的图文验收——浏览器几何审计不能替代；
- 硬件或台架证据（全部数值为合成真值）；
- 真人读者试读与独立作答记录；
- 窄屏（390/820 px）、A4、离线包验收——这些依赖 P2 装配后的站点与出版链。

## S1 的复算入口

```text
python code/engineering/measurement/s1_measurement.py --out <新目录>
python code/engineering/measurement/s1_measurement.py --out <新目录> --students
python code/engineering/precharge/s3_precharge.py --out .tmp-s3-evidence
python code/engineering/precharge/s3_precharge.py --students
python code/engineering/measurement/make_s1_figures.py
python -m pytest code/engineering/measurement -q --basetemp=".tmp-s1"
```

- `--out` 写 `report.json`（含 `config_sha256`）；
- `--students` 写 `questions.md` 与 `config.json`，不写报告；
- 生成图的每个数字都读自 `s1_measurement.py`，图与报告不会漂移。

S1 的三个场景 ID：`S1-sense-chain`（测量链主场景）、`S1-scan-settling`（独立扫描场景）、`S1-filter-post-afe`（AFE 输出后滤波算例）。`S1-physical-chain`（完整物理链）尚未冻结起止时刻，不能把 10.26337 ms 盲加到 77/117/157 ms 或隐式忽略。

| 图 | 回答的问题 |
|---|---|
| `S1-F1-sense-chain.svg` | 传感—校准—采样—保护的信号路径与独立反馈，数字只属边界 |
| `S1-F2-error-budget.svg` | 最坏界 4.5 mV 与 RSS 2.51595 mV 的适用条件，ρ=1 时合成 σ=1.4 mV |
| `S1-F3-settling-scan.svg` | 621.46 µs 才达 1 mV、5τ 不足；16 串 10.26337 ms 超 10 ms 任务但塞进 20 ms 周期 |
| `S1-F4-filter-budget.svg` | N=1/5/9 首达 0/40/80 ms，确认另 40 ms；完整预算 77/117/157 ms |


```text
python code/engineering/identification/s2_identification.py --out <新目录>
python code/engineering/identification/s2_identification.py --out <新目录> --mode student
python code/engineering/identification/make_s2_figures.py
python -m pytest code/engineering/identification -q --basetemp=".tmp-s2"
```

- `--mode reference` 写 `config.json`、`observations.csv`、`report.json`；
- `--mode student` 不生成 `report.json`，只写配置、观测与问题；合成真值保留在配置里供自查，交付物是过程与结论；
- 生成图的每个数字都读自 `s2_identification.py`，图与报告不会各自漂移。

S2 的三个场景 ID：`S2-pulse-identification`（主场景）、`S2-flat-ocv`（偏置反例）、`S2-short-window-ambiguity`（短窗混淆的独立曲线）。改动任一配置字段都必须登记新 ID。

## 图

| 图 | 回答的问题 |
|---|---|
| `S2-handdrawn-intro.webp` | API 概念图（非测量）：独立库存卡只比喻内部状态，不是电解液液位，不提供测量数值 |
| `S2-F1-rc-polarity.svg` | 三项电压归谁所有、极性怎么定、R1∥C1 为何必须是串联二端网络 |
| `S2-F2-common-time-axis.svg` | 电流、OCV、欧姆项、极化项、端电压在同一时间轴上的先后 |
| `S2-F3-window-and-tau-profile.svg` | 短窗与长窗的每样本 RMS 残差剖面、本窗 argmin 与 120 s 边界解；残差大小不跨窗排名精度 |
| `S2-F4-slope-sensitivity.svg` | 同一个电压误差在不同 OCV 斜率上换算成多少 SOC；条形按 pp 线性缩放 |
| `S2-F5-bias-counterexample.svg` | 电压完全重合、SOC 相差 10 pp 的严格反例；左图用短虚线叠加让重合可见 |

五张 SVG 仍按 800 宽、`role="img"`、非空 `<title>/<desc>`、样式类、字号 ≥12 与 XML 转义编写；`test_s2_figures.py` 覆盖结构、拓扑与轴向。该目录不在 `docs/circuits/assets` 门禁的扫描范围内，P2 上站前仍需站点门禁与人工版式复核，不能据此声称已通过站点硬门。

## 图源与风格

五张 SVG 是 `make_s2_figures.py` 的自绘可编辑矢量图，采用仓库自己的手绘工程语言：暖纸底、Prussian blue 结构线、teal 正常分支、ochre 对照、vermilion 反例/故障批注，KaiTi 标题。这套语言是仓库内部的原创规格，不声称对应任何外部艺术流派或规范编号。器件体（电阻、负载、5 s 拟合窗）使用克制的斜线剖面；剖面线只表示器件体或窗口，不表示导体、电流路径或误差带。

数据纪律：`polyline` 的每个点直接来自 `s2_identification.py`，`line` 端点保持精确；定量坐标轴、数据曲线与文字不做抖动、滤波或手绘化扰动。图内字号不小于 12 px，画布宽 800，`role="img"`、`<title>/<desc>` 与 XML 转义由生成器和 `test_s2_figures.py` 守住。

`S2-handdrawn-intro.webp` 来自实际生图 API：两只外观相同的电芯旁有不同的库存状态卡，卡片只比喻不可见状态，不是电解液液位，也不是电化学剖面。图中没有测量数值，不参与拟合或数值结论；来源见[图像清单](../illustrations/handdraw/manifest.json)。[离线图版预览](手绘图版预览.html)展示实际图像与三类机制试版。

## 审查记录

- S2-F1 拓扑：初版把 R1、C1 从顶轨直接画到底部回线，等于把极化支路跨接在端子上，且外部回路未与端子相连。已改为「源 → R0 → R1∥C1 二端网络 → 正端子 → 外部负载 → 负端子」；生成器内注释与图注同步写明约束。检查方式：从 `make_s2_figures.py` 输出解析 `line` 端点，确认两条桥接、串联段与外部回路的 8 条关键线段存在，且二端网络底轨与负回线之间没有竖直连线。
- 文本转义：F5 的标注曾含裸 `<`（`差 < 1e-12 V`），整份 SVG 因此不是良构 XML，浏览器按容错路径渲染，掩盖了问题。生成器的 `text()` 与 `svg()` 现统一转义；`test_s2_figures.py` 逐张做 XML 解析，裸 `<`/`&` 会直接失败。
- 手绘改版：暖纸/Prussian blue/KaiTi 标题；F1 的 R0、R1、负载矩形与 F3 的 5 s 拟合窗加剖面线；F4 补 0–7 pp 的线性刻度轴（0/2/4/6/7）。剖面线只作器件体或窗口标记，数据折线、定量轴与文字未抖动；F4 条形长度仍由同一个 `value / max_pp` 计算。
- 版式：手绘改版后的五张 SVG 已在 Chromium 做 `getBBox()` 检查，文字出界 0、两两文字框交叠 0，并实际查看渲染图。F5 标注再次右移，避开脉冲折线；未声称机器检查涵盖所有文字/曲线交点或替代领域审读。
- F5 标注：纵轴翻转后原 y=128 落在静置线上；现为 x=150、y=272，避开左侧脉冲。A 组短虚线叠加 B 组实线显示重合，所有数据点未动。
- F3 纵轴与措辞：右图已从对数 SSE 改为每样本 RMS（mV），同一窗口内 argmin 不变；图注与脚注明确两窗样本数和可辨识性不同，残差大小不能跨窗当精度排名，极小点也不是置信区间。
- F3 首点：旧 `desc` 写 3.6724 V 不准确，现区分带噪观测首点与无噪声释放值 3.6718 V、渐近值约 3.678 V；图注按实际种子给近似读数，不把噪声点写成精确解析值。

## 合同

符号、时钟与数据口径以 [engineering-conventions.md](../engineering-conventions.md) 为准：新深研侧放电为正（`I > 0` 放电），旧 `code/soc` 保留充电为正（`I_legacy = -I`，`u_rc = -v_p`），SOC 为 0–1 比例。

## 未验证项

- 无电芯数据表、测量链或硬件结果；所有参数为教学合成值。
- 无真人读者试读、无独立作答记录、无具资质工程审读签字。
- 全局生图计划受账户额度限制：三张已接入，一张机制候选拒绝，另六张已付费候选恢复后待审，27 张未生成；封面/阶段页未切换，不得声称全书改完。
- 新增安全/并发测试与 S2 单位/轴方向测试仍须独立审阅；`task_verify` 无可用项目基线，结果为 unverified。报告的行列式说明已同步为 V/SOC，不再混写为 V²/SOC。
- 窄屏、A4、离线包与全文检索验收留待 P2 装配。


| S3 预充时序 | [S3-预充时序母线起来了许可还差四样证据.md](S3-预充时序母线起来了许可还差四样证据.md) | 5 张 SVG（`engineering/assets/s3-precharge/`，F1/F4 机制图） | `code/engineering/precharge/`（24 项测试） | 数值复算/结构检查通过；窄屏/A4、出版与技术审读待 P2 |

S3 场景 ID：`S3-inrush-precharge`（理想 RC 主线）、`S3-precharge-with-load`（2 kΩ 并联负载）。2 kΩ 稳态 368.66 V 到不了 95%，有限窗口 5τ 能量账 `192.76 = 88.31 + 37.41 + 67.04 J`。

| `S3-F1` | 预充态里主闸与泄放哪条路在导电 | 见 S3 章 |
| `S3-F2` | 95% 时源供的 152 焦耳从哪来 | 见 S3 章 |
| `S3-F3` | 锁存阶段的跌落尖峰能不能在同一轴上对齐 | 见 S3 章 |
| `S3-F4` | 母线 380 V 的四种根因怎么区分 | 见 S3 章 |
| `S3-F5` | 20 V 残压在主回路里会冲多大电流 | 见 S3 章 |
