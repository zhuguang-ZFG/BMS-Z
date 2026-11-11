# 工程深研册：已实现单元审阅版

这里保留 BMS v3 的 P1 三样章入口，也导航已有工程单元、先修桥梁和 C1 草案。工程稿与旧完整本分开维护，**不进入** `bms-book/book/` 的 32 章清单；旧书章数与导航仍由 `docs/.vitepress/book-sources.mjs` 枚举。当前装配器按登记选择已实现源稿：B01–B05、D01–D12、S1–S3、C1草案共21单元，另随册交付工程约定、最小先修包、来源/实验附录；不是尚未实现的全册。任务状态只在[唯一执行表](../../docs/superpowers/plans/2026-11-08-bms-depth-rebuild.md)维护。

## 当前状态

源入口核对日期：2026-11-10。下表只说明产物是否存在和仍缺什么，不把历史测试/图审记录改写成本轮验收。

| 单元 | 正文 | 图 | 参考实现与测试入口 | 当前边界 |
|---|---|---|---|---|
| S1 测量链 | [S1-精度够了保护为什么反而慢了.md](S1-精度够了保护为什么反而慢了.md) | 4 张 SVG（`assets/s1-measurement/`，F1 机制路径图） | [测量实验](../../code/engineering/measurement/) | 源包已有；完整物理链起止边界未冻结，最终尺寸/技术/出版复核及真人、硬件证据仍待验 |
| S2 一条电压曲线能识别出多少东西 | [S2-一条电压曲线能识别出多少东西.md](S2-一条电压曲线能识别出多少东西.md) | 5 张 SVG + 1 张概念图（`assets/s2-model/`） | [辨识实验](../../code/engineering/identification/) | 源包已有；三样章装配能力不代替当前源、独立审读与最终版式验收 |
| S3 预充时序 | [S3-预充时序母线起来了许可还差四样证据.md](S3-预充时序母线起来了许可还差四样证据.md) | 5 张 SVG（`assets/s3-precharge/`，F1/F4 机制图） | [预充实验](../../code/engineering/precharge/) | 源包已有，不是未开工；F1 拓扑技术复核、最终尺寸/出版及真人、硬件证据仍待验 |

`manifest.json` 的 `locally_verified` 是既有登记状态，不自动等于总 SPEC 要求的完整本地交付。这里的“可复算”指正文、图源、参考实现、冻结配置、留出验证与反例有对应复跑入口；不是声称本轮已经执行命令。它**不**包含：

- 独立工程审读与最终出版链的图文验收——浏览器几何审计不能替代；
- 硬件或台架证据（全部数值为合成真值）；
- 真人读者试读与独立作答记录；
- 最终印刷逐页、全部图版最终尺寸、EPUB专用阅读器与独立领域终审。第三批已取得当前源HTML/EPUB/PDF装配、390/820px页宽与实际检索证据，范围见执行表第12节，不代签这些外部/终版门。

## 已有工程稿与桥梁

维护归属见[复用矩阵](../../docs/superpowers/plans/bms-depth/reuse-map.md)，登记身份见 [manifest.json](manifest.json)；来源、断言、图和实验分别回查 [claims.json](claims.json)、[figures.json](figures.json)、[experiments.json](experiments.json) 及其来源记录。源文件存在、维护归属明确与出版/技术/外部验收是三件事。

先修入口：[P1 最小先修包](P1-先修最小包.md)。五份桥梁的当前维护源为：

| 单元 | 实际源入口 |
|---|---|
| B01 | [电路与能量](../bridges/B01-电路与能量.md) |
| B02 | [变化与采样](../bridges/B02-变化与采样.md) |
| B03 | [误差矩阵与拟合](../bridges/B03-误差矩阵与拟合.md) |
| B04 | [时间与状态](../bridges/B04-时间与状态.md) |
| B05 | [数据身份与留出](../bridges/B05-数据身份与留出.md) |

下列 D01–D12 已随独立工程产物装配；源稿、技术审查与正式验收仍分别报告，不另设完成勾选。

| 单元 | 实际源入口 |
|---|---|
| D01 | [电芯内部与端子证据](D01-电芯内部与端子证据.md) |
| D02 | [动态等效模型](D02-动态等效模型.md) |
| D03 | [参数规格与任务定义](D03-参数规格与任务定义.md) |
| D04 | [测量与误差传播](D04-测量与误差传播.md) |
| D05 | [AFE 与动态采样](D05-AFE与动态采样.md) |
| D06 | [PCB 回流与 EMC](D06-PCB回流与EMC.md) |
| D07 | [MOS 与功率路径](D07-MOS与功率路径.md) |
| D08 | [保护与时间预算](D08-保护与时间预算.md) |
| D09 | [独立保护与失效](D09-独立保护与失效.md) |
| D10 | [均衡与测量协调](D10-均衡与测量协调.md) |
| D11 | [HPPC 与参数辨识](D11-HPPC与参数辨识.md) |
| D12 | [SOC 基线与校准](D12-SOC基线与校准.md) |

综合任务入口：[C1 测量与保护综合预算草案](C1-测量与保护综合预算草案.md)。它是 P7.1 的前置草案，不是已完成的新工况迁移或独立复核；器件、来源及技术判据仍需按对应单元审读。D13–D28、R01–R04 尚未交付，C2–C4 仍在总范围内；工作区未跟踪的 D13 实验草稿不计入本页交付，也不因本次导航收口而纳管。

以下三套命令均从仓库根目录执行；参考报告和学员包分别使用新的输出目录，不覆盖已有证据。测试命令仅列对应样章的已存在测试文件，不在本页手抄易失真的测试总数；本轮未执行这些命令。

### 构建与检索

```text
python -X utf8 tools/build_engineering.py --out <输出目录> --pdf
npm run docs:build
node .github/scripts/check_search.mjs docs/.vitepress/site-dist
```

独立构建产出 `engineering-book.html`、`engineering.epub`、`pdf/engineering-book.pdf`、`build-report.json` 及图资产。站点既有构建结束后复用同一装配器发布到 `/engineering/engineering-book.html`，导航“工程深研”可达；不改变完整本或基础册默认输出。

HTML搜索在首次查询才从已交付正文建立MiniSearch索引，与主站共用中文二元组分词；折叠答案和被阅读层级过滤的正文仍可搜，点结果临时显露所在小节，再点层级可恢复。索引与脚本均无网络依赖，复制单个HTML也能断网搜索；代码/旧书等外链明确需要联网。根索引仍限4900KiB、gzip1200KiB，工程正文不重复进入根索引。EPUB用阅读器自带搜索，不嵌入交互脚本；PDF展开答案并使用A4打印样式。

## S1 的复算入口

```text
python code/engineering/measurement/s1_measurement.py --out <新目录>
python code/engineering/measurement/s1_measurement.py --students
python code/engineering/measurement/make_s1_figures.py
python -m pytest code/engineering/measurement/test_s1_measurement.py code/engineering/measurement/test_s1_figures.py -q --basetemp=".tmp-s1"
```

- `--out` 写 `report.json`（含 `config_sha256`）；
- `--students` 向终端打印学员题，不写 `questions.md`、`config.json` 或报告；它与 `--out` 是两种调用方式；
- 图由 `make_s1_figures.py` 基于 `s1_measurement.py` 的参数与计算生成；图、报告和正文的一致性仍需核对，不能由生成成功代签技术验收。

S1的三个已登记场景：`S1-sense-chain`（测量链）、`S1-scan-settling`（独立扫描）、`S1-filter-post-afe`（AFE输出后滤波）。S1.8已列各段起止时刻：77/117/157 ms以首个高输出等待≤20 ms为前提；`S1-physical-chain`仍缺实际模拟采样、输出发布及调度上界，不能再盲加10.26337 ms或假设重叠。

| 图 | 回答的问题 |
|---|---|
| `S1-F1-sense-chain.svg` | 竖排三段：模拟采样、数字保护与独立反馈；功能箭头不是板级接线 |
| `S1-F2-error-budget.svg` | 最坏界 4.5 mV 与 RSS 2.51595 mV 的适用条件，ρ=1 时合成 σ=1.4 mV |
| `S1-F3-settling-scan.svg` | 621.46 µs 才达 1 mV、5τ 不足；16 串 10.26337 ms 超 10 ms 任务但塞进 20 ms 周期 |
| `S1-F4-filter-budget.svg` | N=1/5/9首达0/40/80 ms，确认另40 ms；冻结首拍等待等假设下的反馈预算77/117/157 ms |


## S2 的复算入口

```text
python code/engineering/identification/s2_identification.py --out <新目录>
python code/engineering/identification/s2_identification.py --out <新目录> --mode student
python code/engineering/identification/make_s2_figures.py
python -m pytest code/engineering/identification/test_s2_identification.py code/engineering/identification/test_s2_figures.py -q --basetemp=".tmp-s2"
```

- `--mode reference` 写 `config.json`、`observations.csv`、`report.json`；
- `--mode student` 不生成 `report.json`，只写配置、观测与问题；合成真值保留在配置里供自查，交付物是过程与结论；
- 图由 `make_s2_figures.py` 基于 `s2_identification.py` 生成；修改参数或时间侧后须同步审查报告、图与正文。

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

五张SVG均有`role="img"`、非空`<title>/<desc>`与XML转义。S2-F3已改为400宽上下两面板；其余仍为800宽，不能用源字号≥12代替最终显示尺寸验收。`test_s2_figures.py`覆盖结构、拓扑与轴向；该目录不在`docs/circuits/assets`门禁扫描范围，P2上站前仍需实际站点与人工版式复核。

## 图源与风格

五张 SVG 是 `make_s2_figures.py` 的自绘可编辑矢量图，采用仓库自己的手绘工程语言：暖纸底、Prussian blue 结构线、teal 正常分支、ochre 对照、vermilion 反例/故障批注，KaiTi 标题。这套语言是仓库内部的原创规格，不声称对应任何外部艺术流派或规范编号。器件体（电阻、负载、5 s 拟合窗）使用克制的斜线剖面；剖面线只表示器件体或窗口，不表示导体、电流路径或误差带。

数据纪律：`polyline` 的每个点直接来自 `s2_identification.py`，`line` 端点保持精确；定量坐标轴、数据曲线与文字不做抖动、滤波或手绘化扰动。图内字号不小于 12 px，画布宽 800，`role="img"`、`<title>/<desc>` 与 XML 转义由生成器和 `test_s2_figures.py` 守住。

`S2-handdrawn-intro.webp` 来自实际生图 API：两只外观相同的电芯旁有不同的库存状态卡，卡片只比喻不可见状态，不是电解液液位，也不是电化学剖面。图中没有测量数值，不参与拟合或数值结论；来源见[图像清单](../illustrations/handdraw/manifest.json)。[离线图版预览](手绘图版预览.html)展示实际图像与三类机制试版。

## S3 的复算入口

```text
python code/engineering/precharge/s3_precharge.py --out <新目录>
python code/engineering/precharge/s3_precharge.py --students
python code/engineering/precharge/make_s3_figures.py
python -m pytest code/engineering/precharge/test_s3_precharge.py code/engineering/precharge/test_s3_figures.py -q --basetemp=".tmp-s3"
```

- `--out` 写 `report.json`（含配置摘要）；`--students` 仅向终端打印题目，不生成报告或学员包文件。
- S3 场景 ID：`S3-inrush-precharge`（理想 RC 主线）、`S3-precharge-with-load`（2 kΩ 并联负载）。2 kΩ 稳态 368.66 V 到不了 95%，有限窗口 5τ 能量账 `192.76 = 88.31 + 37.41 + 67.04 J`。

| 图 | 回答的问题 | 正文入口 |
|---|---|---|
| `S3-F1` | 不同状态下预充、主路与泄放的电流如何闭合；拓扑仍需技术复核 | [S3 章](S3-预充时序母线起来了许可还差四样证据.md) |
| `S3-F2` | 95% 时源供的 152 焦耳从哪来 | [S3 章](S3-预充时序母线起来了许可还差四样证据.md) |
| `S3-F3` | 锁存阶段的跌落尖峰能不能在同一轴上对齐 | [S3 章](S3-预充时序母线起来了许可还差四样证据.md) |
| `S3-F4` | 母线 380 V 的可能原因及其组合还需要什么证据来区分 | [S3 章](S3-预充时序母线起来了许可还差四样证据.md) |
| `S3-F5` | 20 V 残压在主回路里会冲多大电流 | [S3 章](S3-预充时序母线起来了许可还差四样证据.md) |


## 审查记录

以下保留 2026-11-08 制作与审查记录的具体发现，说明当时如何修图；不是 2026-11-10 的重新运行或终审。特别是几何检查不证明最终尺寸可读或电路、断言正确，当前未闭合项仍按执行表处理。

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
- 2026-11-08 已决定停用生图 API；历史记录为三张接入、一张机制候选拒绝、六张已付费候选待审、27 张未生成。原图、候选、拒稿和冻结试版保留，不因本次状态收口继续生成或改算录用；封面/阶段页未切换，不得声称全书改完。
- 2026-11-08 的安全/并发及 S2 单位/轴方向测试改动记录仍要求独立审阅；当时 `task_verify` 无可用项目基线而记为 unverified，不能沿用为本轮结果。该历史记录中的行列式量纲已同步为 V/SOC，不再混写为 V²/SOC。
- 前两批历史证据见[执行表第10节](../../docs/superpowers/plans/2026-11-08-bms-depth-rebuild.md#10-第一批纠偏实施记录2026-11-10)、[第11节](../../docs/superpowers/plans/2026-11-08-bms-depth-rebuild.md#11-第二批图文精修与测试审查2026-11-10)。第三批已解决390px页面级横溢，装配D01–D12并实现独立全文检索；实际证据与权限/测试review缺口见[第12节](../../docs/superpowers/plans/2026-11-08-bms-depth-rebuild.md#12-第三批实际可读可搜产品2026-11-10)。旧104 passed/3权限errors不作本批结果；`task_verify`仍无可用基线。

