# 待审图清单（129 张 generated）

本页索引 129 张 `status: generated` 的手绘资产，分为未插候选、已插动画和已插旧图返审三类：

**终审工作台（2026-11-07 生成）**：[接触表 · 全部新图 174 张，含状态徽章与七项评分栏、灰度对照](../pending-2026-11-07/index.html)（`python scripts/build_visual_contact_sheet.py --out docs/superpowers/visual/reviews/pending-2026-11-07/index.html --grayscale --page-size 18` 可重建）。

**分章审阅包（2026-11-07）**：`ch00`–`ch18` 各一张章级接触表（含已 accepted 卡作对照，待审卡以 `generated` 徽章区分）——[ch00](../pending-2026-11-07/chapters/ch00.html) · [ch01](../pending-2026-11-07/chapters/ch01.html) · [ch02](../pending-2026-11-07/chapters/ch02.html) · [ch03](../pending-2026-11-07/chapters/ch03.html) · [ch04](../pending-2026-11-07/chapters/ch04.html) · [ch05](../pending-2026-11-07/chapters/ch05.html) · [ch06](../pending-2026-11-07/chapters/ch06.html) · [ch07](../pending-2026-11-07/chapters/ch07.html) · [ch08](../pending-2026-11-07/chapters/ch08.html) · [ch09](../pending-2026-11-07/chapters/ch09.html) · [ch10](../pending-2026-11-07/chapters/ch10.html) · [ch11](../pending-2026-11-07/chapters/ch11.html) · [ch12](../pending-2026-11-07/chapters/ch12.html) · [ch13](../pending-2026-11-07/chapters/ch13.html) · [ch14](../pending-2026-11-07/chapters/ch14.html) · [ch15](../pending-2026-11-07/chapters/ch15.html) · [ch16](../pending-2026-11-07/chapters/ch16.html) · [ch17](../pending-2026-11-07/chapters/ch17.html) · [ch18](../pending-2026-11-07/chapters/ch18.html)。评分回填模板：[scores-template.csv](../pending-2026-11-07/scores-template.csv)（129 行，仅 `generated`；静态图后两列填 `N/A`，动画七项全填且合计 ≥30）。

| 子集 | 张数 | 是否已在正文里 |
|---|---:|---|
| `kind: figure`（figures-v2） | 116 | **未插入**。`content.py:_asset_path` 要求 `accepted`/`published`，否则抛 `BookError: V2 插图尚未通过审图` |
| `kind: animation`（svg-v2） | 12 | **已插入且读者可见**（`docs/` 里已有 `assets/svg-v2/<id>.svg` 的 `<img>`）。动画不校验状态，只要求 `storyboard` 回退存在——12 张都满足 |
| `kind: figure`（figures，旧图返审） | 1 | **已插入**。`ch17-virtual-short-test` 的条件判据与版面已重绘，原签核仅绑定旧 SHA；原评分、状态历程和审图记录完整保存在 `review_history`，当前改后字节须重新人工审图 |

116 张候选的分数决定它们能否进书；12 张动画已经可见，仍待人工评分；新增的 1 张是已插旧图的返审，不是又一张待上线候选。当前有效 `accepted` 为 45 张，不得把旧图归档的审批算作改后字节已获批准。

## 近期修订（会改变已发布字节，审图请以本页下方清单为准）

| 日期 | 资产 | 改了什么 | 证据 |
|---|---|---|---|
| 2026-11-07 | `ch18-power-three-touchpoints`、`ch18-dmm-averaging` 重建 + `ch18-williams-workbench` 新注册（见清单 129） | 场景化试点：两张旧的文字卡升级为「上方纸雕场景 + 下方两栏技术注释」版式（新布局 IG-013）——电源触点图画成 PCB + LDO + 橙色电源走线 + 三支探针 ①②③；万用表图画成台式万用表平线与示波器正弦的对照。新增一张 Williams 工作台主图（V1）：示波器、万用表、最小电路板、预测笔记、前级放大器与短弹簧地针，左栏四条纪律①先预测②短地线③最小电路④源头放大。三张全部确定性 SVG，图内数字逐字取自 §18.1/§18.2 原文；仍未插入正文（保持 `generated`） | 发射器逐图预览：`bounds` 全 pass、最小印刷字号 8.6449pt（阈值 8.5）；字体子集补 U+96D5「雕」后 2288/2288 覆盖；`check_visual_manifest.py` PASS（0 项）；13 套视觉测试全绿；ch18 章级接触表 15→16 张、总工作台 173→174 张、评分模板 128→129 行 |
| 2026-11-07 | `ch16-record-card` 等 4 张（wave20，见清单 125–128） | 新注册而非改旧字节：补四个无手绘图且无待审覆盖的长节——ch16 §16.9「一页纸排故记录表」（整节零图）、ch11 §11.6「噪声：放大器躲不掉的"本底"」、ch4 §4.1「沟道形成原理」、ch3 §3.2「三个工作区」。四张分别是：记录表三栏卡（现场/推演/收口＋边界与交接）、噪声五症状对照表、沟道形成三步剖面、三区判读四路分流。图内每个数字逐字取自对应小节原文 | 发射器逐图预览：`bounds` 全 pass、最小印刷字号 8.606pt（阈值 8.5）；字体覆盖闸无 <8.5pt 文本；`check_visual_manifest.py` PASS（0 项）；视觉测试组合 **134 passed**；`test_figures.py` 5 项全绿；`audit_visual_geometry.py` 全库 365→369 张、缺陷 0；接触表 169→173 张 |
| 2026-11-07 | `ch15-return-mirror` 等 4 张（wave19，见清单 121–124） | 新注册而非改旧字节：ch15 §15.2「接地——模拟工程师的终极命题」是全书最后一个零图大空档（14002 字符无插图），补 4 张纸墨手绘——高频回流镜像电流剖面（完整平面 vs 开槽绕路）、地弹与精度三笔账（回路电感/总线量级/基准 LSB）、接地策略频段分工（单点/混合/多点 + 1/20 波长判据）、叠层与跨分割补救（四层/六层剖面 + 桥接纪律）。图内每个数字逐字取自 §15.2 原文 | 发射器逐图预览：`bounds` 全 pass、最小印刷字号 8.606pt（阈值 8.5）；字体覆盖闸无 <8.5pt 文本；`check_visual_manifest.py` PASS（0 项）；`make visual-check` 等价 13 套 + `analog-book/tests/test_visual_v2_assets.py` 全绿；`test_figures.py` 5 项全绿；接触表 165→169 张 |
| 2026-11-07 | `ch10-555-fault-tree` | ③行判据原被截成半句「热风一吹 >5% 即介质」，改为完整句「热风一吹变化 >5%：元件介质问题」（对应正文 §10.3 原句）；底部绿框原高 40、贴画布底缘只剩 6px，重排中/琥珀/绿三框（312/88@542/48@642），框间距 8–14px、底缘留 10px | `measure_svg.py` 24 字 OVERFLOW/OCCLUDED/OVERLAP 0；`probe_lines_edges.py` 贴边最小 6.3px 与全库已审风格一致；`check_visual_manifest.py` PASS；alt 同步 |
| 2026-11-07 | 印刷管线 `svg_refine.is_legacy_svg` | handraw 纸墨皮肤的静态手绘图（带 `page-grain`、无 SMIL）不再误判为旧模板：PDF/EPUB 印刷保留纸面渐变、颗粒、暗角与楷体手写体，不再剥皮换成黑体；带 SMIL 的旧动画判定不变 | `test_svg_refine.py` 新增 2 项夹具（皮肤静态图豁免 / 皮肤动画仍净化）全绿；`test_storyboard.py` 通过 |
| 2026-11-07 | 194 张 figures-v2 handraw 草图（含 -print） | 仅元数据：根元素补 `data-composition="python-handraw-v1"`、`<title>`/`<desc>`（取自各图 composition JSON，与 manifest 同源），图面字节未动；波次重建后需重跑 `scripts/label_handraw_figures.py` | `test_figures.py` 5 项全绿；`make visual-check` 等价 13 套全绿；manifest 闸 PASS |
| 2026-11-07 | 测试快照三处（需人审口径，不改 runner/policy/评分） | ① `test_figures.py` data-composition 断言改为已授权血统集合 {technical-overlay-v1, python-handraw-v1}，估宽探针白名单收录 ch11-noise-three-taxes 一句（Chromium 实测零越界，楷体拉丁窄于等宽估计）；② `test_svg_refine.py` 库存围栏 118→153（exp-* 35 张逐张过印刷循环全部通过）；③ `test_wave1_chapters.py` ch0 figures 7→17、ch16 6→7（正文实数，17 张全非空图注） | 三套测试文件本地全绿；证据见各行 |
| 2026-11-06 | `ch17-symptom-four-fields` | 结论帧原本四行全空：每拍只画当拍一行、且不保留，播完右侧仍是「（待填写）」。改为累积重画前 N 行，未填行才画占位；结论帧四行全留 | 浏览器 `setCurrentTime(9.5)`：修前已填 0 行、占位 4；修后已填 4、占位 0。逐拍实测 0→1→2→3→4 行、占位 4→3→2→1→0。静态回退与分镜同步重建，分镜逐格 0/1/2/3/4 |
| 2026-11-06 | `ch00-source-types-v2` 与动画中心 `source-types.svg` | 上轮补回结论曲线后，仍沿用了错误方向：横轴 I、纵轴 V，却把恒压画竖线、恒流画水平线。本轮统一新旧图的坐标约定，恒压水平、恒流竖直，负斜率的绝对值对应输出阻抗；正文、速查、动画中心、字幕与 alt 同步，旧图改生成器后重建 | V2 旧版 8 个视图回归失败，修后通过；关联旧图回归修前因恒压端点 120≠290 失败，修后通过；生成一致性与库存检查通过 |
| 2026-11-06 | `ch00-divider-loading-v2` | 结论拍只剩一根虚线加「RL」二字，负载电阻本身没画出来，「下臂被并联」在图上无证据。改为结论拍保留负载支路与 `RL 10kΩ` 标注 | 静态回退含 `RL 10kΩ` 与电阻矩形；截图可见完整负载支路 |
| 2026-11-06 | `ch17-esr-sweep` | 结论帧的容量条是空框，「只剩标称三成」没有图形证据；闭环卡底边又被字幕条切掉。改为结论拍保留 30% 填充与标注，画布 620→660 | 浏览器终帧：容量条 1 条填充、卡底 572 < 字幕条 596；静态回退含填充与标注 |
| 2026-11-06 | `ch08-mux-address-glitch-v2` | 上轮补回时序后，将错误通道已导通画进了 INH 高电平保护帧。本轮分开危险与保护示例：先拉 INH、地址变化期间全断，最终地址稳定才释放，接通并完成信号建立后再采样 | 旧版 5 个保护视图回归失败；新版检查 INH 高电平覆盖地址变化，采样标记在解除禁止之后；浏览器逐拍核对 |
| 2026-11-06 | `ch17-virtual-short-probe` 与 `ch17-virtual-short-test` | 在补回读数之后进一步纠正判据：8mV 只是测量值，不能直接判运放正常。探针图补画信号经 Rin、输出经 Rf 回反相端的实际负反馈路径；判读分为核前提、算误差、验输出，关联静态决策图同步重绘为最小 22px 标注 | 修前拓扑回归在动画、静态及 5 格分镜共 7 个视图失败，修后通过；2.500V/2.508V/8mV 保留。静态旧图原签核已失效，完整原评分、审图记录及旧 SHA 归档到 `review_history` |
| 2026-11-06 | `ch08-transfer-gate-v2` | 上轮恢复曲线并避开字幕后，仍将 4V 标在横轴约 1.26V 处，包络用任意鼓包代替正文模型。本轮由正文电导公式生成单管曲线及 1~4V 的约 26.7Ω 平台，统一电压/电阻映射并取消定量层漂移；结论明确单 N 的限制不等于并联传输门的摆幅上限，双头箭头表示双向 | 修前主动画、静态和分镜 6 个视图的刻度回归失败；新版 2.5V 居中、4V 位于轴长 4/5，数值回归按图中刻度反算电阻与平台 |
| 2026-11-06 | `ch17-subharmonic-edge` | 「SW 节点波形」窗在最后三拍全空：波形按拍重画、补偿拍与结论拍都不带波形。改为补偿拍保留待修的一宽一窄，结论拍画回规整波形并把旋钮移回 40% | 浏览器实测 7.2s/9.2s 均可见波形 path；静态回退含波形、`40%` 与外框；分镜 5 格全含波形 |
| 2026-11-06 | `ch08-sample-hold-v2` | 波形原本按拍拆成三段、互不保留，「再采样」拍干脆不含波形——播完只剩空坐标轴。改为每拍重画整条已发生波形，结论帧呈现完整一个采样周期（上升→保持→下垂） | 浏览器实测终帧：修前可见波形段 0，修后 1 条完整曲线；静态回退含三段端点 `M110,400` / `L700,180` / `864,220` |

本轮回归代码需人审：`scripts/test_animation_v2.py` 的两项固定坐标/字符串测试改为物理方向与禁止时序的不变量检查；`scripts/test_svg_assets.py` 新增关联旧图的方向回归。测试均实际运行，但修改过的测试不自动成为可信基线；没有更改执行器、策略或评分门禁。

传输门本轮另将一项固定 path 字符串测试替换成刻度比例回归，并补充按可见刻度反算电阻、核对平台的行为测试。两项均保留修前失败证据；这些测试修改同样需要人工审查，不改变 runner、policy 或人工评分状态。

虚短探针本轮新增拓扑回归：从输出节点沿图面导线与 Rf 能到达反相输入节点，且不能误接同相端；动画、静态回退与每格分镜均检查。这项测试修改需人审。`review_history` 是旧字节的审图证据归档，不是改后资产的有效审批；当前评分保持空，后续重新按阶段审图。

动画中心的“看点”同时供印刷附录 A 生成摘要。修改 `docs/p5-00-part5.md` 后，除重建 `BOOK.md`，还必须运行 `python scripts/build_book_data.py --write`，再用 `--check` 核验派生台账。本次漏更新导致 `test_book_data.AnimationTests.test_real_generator_matches_committed_yaml` 在 CI 抓到 `anim-078.one_line` 仍是旧方向；已重新生成，153 条动画的其他记录及来源、文献、审读台账保持不变。

## 已有证据的**实际覆盖范围**

各项检查覆盖到哪些条目并不相同，逐项写明：

| 检查 | 覆盖 | 结论 |
|---|---|---|
| 数字双向溯源（图内数字 ⊆ anchor 原文、alt/prompt 数字 ⊆ 图面数字） | **全部 129 张** | `check_visual_manifest.py` 对每条带 `prompt_file` 的资产都跑 `number_gaps` 与 `visible_number_gaps`，PASS（0 项） |
| 登记齐全 / prompt id 与中英文本 / status_history 与评分区间 | **全部 129 张** | 同上，manifest 闸 PASS；返审旧图的有效状态历程重新为 planned / generated，原完整审批在 `review_history` |
| 出画布、文字互压、后画矩形盖字 | **111 张 figures-v2**（`audit_visual_geometry.py` 全库 369 张、缺陷 0） | 见下注① |
| 出画布（字框出 viewBox） | 12 张 svg-v2 动画：一次性脚本补测，**全部 0 处** | 该项与显示状态无关；这 12 张已在正文显示，故该结论直接对读者可见面成立 |
| 文字互压 / 后画矩形盖字 | 12 张 svg-v2 动画：**不作缺陷判定** | 这些 SVG 按 `data-beat` 分组做 opacity 动画，不同节拍互斥显示；静态 DOM 度量无法区分，须动态审图 |
| 16K/138mm 最小印刷字号 ≥ 8.5pt 与版面 `bounds` | **116 张 figures-v2**：逐图 `*.audit.json` | 最小值 **8.606 pt**（阈值 8.5），`bounds` 全部 pass；该证据只覆盖 figures-v2 |
| 同上 | 12 张 svg-v2 动画：**无 `*.audit.json`** | 未记录，本包不作该项声明 |
| 返审旧图的字形与最小名义印刷字号 | `ch17-virtual-short-test`，138mm 宽 | 最小 SVG 字号 22px，按 960 单位画布换算约 8.96pt；字形检查通过。版面另以浏览器实测，不归入 111 张 figures-v2 的 `*.audit.json` 覆盖 |

① 该 369 张的统计口径是 `figures-v2`/`figures`/`svg` 三个目录，`svg-v2` 不在其中；
因此 116 张 `figures-v2` 候选的几何检查由这一次全库运行覆盖；12 张 `svg-v2` 动画的出画布另有补测（0 处），互压/遮字则因分节拍互斥无法静态判定。

人工审图仍未完成。本页中的浏览器截图、拓扑与几何测量是技术校样证据，不代替教学必要性、事实精度或风格的人工评分。

## 签核方式（口径以 `scripts/check_visual_manifest.py` 为准）

1. 五项评分，每项必须落在 **4~5**：`教学必要性`、`事实精度`、`构图层级`、`风格一致性`、`印刷可读性`。
2. **动画（本队列 12 张，`kind: animation`）另加两项**：`运动叙事`、`交互节奏`，且七项合计 **≥ 30/35**。
   评这两项需要动态入口（`storyboard` / `reduced_motion` / `preview`），静态 fallback 不足以评。
3. 先把 `review_scores` 写进 manifest 条目，**再**迁移状态。顺序颠倒会被拒：
   `--transition` 只在 `check()` 全过时才写盘，评分缺失时报
   `FAIL <ID>: 评分「构图层级」须在 4..5 内`，文件保持原样。
   ```bash
   python scripts/check_visual_manifest.py --transition <ID> reviewed
   python scripts/check_visual_manifest.py --transition <ID> accepted
   ```
   `status_history` 必须恰好落在 `["planned","generated","reviewed","accepted"]` 上；
   越级或回退会被拒。`--previous <旧 manifest>` 可选，用来额外禁止一次跳多级。
4. `asset_sha256` 必须按**当前 SVG 字节**重算（CRLF→LF 归一），不得沿用旧签核的值。
5. 任何一张重绘后 SHA 变化，签核作废，必须退回 `generated` 并重新逐级迁移。

## 清单（原 120 个编号保留；wave19 四张追加为 121–124，wave20 四张追加为 125–128，ch18 场景化试点一张追加为 129）

| # | 章 | anchor | id | 类型 | 用途 | 源事实数 |
|---:|---:|---|---|---|---|---:|
| 1 | 0 | 0.2 | `ch00-current-loop-v2` | A1 | 闭合回路中的约定电流与串联压降（Task 8 正文试片，待风格复评） | 1 |
| 2 | 0 | 0.3 | `ch00-divider-derivation-v2` | A2 | 空载分压公式的逐步推导（Task 8 正文试片，待风格复评） | 1 |
| 3 | 0 | 0.3 | `ch00-divider-loading-v2` | A4 | 分压器从空载到带载的塌陷与输出电阻判据 | 1 |
| 4 | 0 | 0.6 | `ch00-source-types-v2` | A1 | 恒压源与恒流源的 V-I 曲线、输出阻抗与接法 | 1 |
| 5 | 1 | 1.1 | `ch01-e24-ladder` | V4 | E24 档位与 3.3k 的来历 | 1 |
| 6 | 1 | 1.4 | `ch01-thevenin-two-load` | V4 | 戴维南等效与两负载法实测内阻 | 1 |
| 7 | 1 | 1.5 | `ch01-q-selectivity-map` | V4 | Q 是挑频率的锐度，不是越高越好 | 1 |
| 8 | 1 | 1.7 | `ch01-derating-product` | V4 | 降容是乘法：三项八折只剩一半 | 1 |
| 9 | 1 | 1.7 | `ch01-electrolytic-life` | V4 | 10°C 翻倍法则下的电解电容寿命账 | 1 |
| 10 | 2 | 2.10 | `ch02-rectifier-voltage-ledger` | V4 | 桥式整流的电压分账与峰值电流 | 1 |
| 11 | 2 | 2.11.3 | `ch02-esd-chain` | V4 | IEC 8kV 的 24A 分账 | 1 |
| 12 | 2 | 2.12 | `ch02-bridge-junction-ledger` | V4 | 桥堆与整流管的四个数与结温账 | 1 |
| 13 | 2 | 2.13 | `ch02-diode-fault-order` | V4 | 二极管排故的三步顺序 | 1 |
| 14 | 2 | 2.8 | `ch02-protection-order` | V4 | 接口保护三件套的先后次序 | 1 |
| 15 | 2 | 2.9 | `ch02-junction-margin` | V4 | 结温余量只剩 3°C | 1 |
| 16 | 2 | 2.9 | `ch02-parallel-hog` | V4 | 并联二极管的热抢流 | 1 |
| 17 | 2 | 2.9 | `ch02-zener-budget` | V4 | 稳压管的限流电阻与最坏功耗 | 1 |
| 18 | 3 | 3.1 | `ch03-early-effect` | V4 | 厄利效应与输出阻抗 | 1 |
| 19 | 3 | 3.2 | `ch03-reverse-beta` | V4 | C/E 反接为什么β只剩个位数 | 1 |
| 20 | 3 | 3.3 | `ch03-config-impedance` | V4 | 三种组态共用一条阻抗折算律 | 1 |
| 21 | 3 | 3.5 | `ch03-low-high-side` | V4 | 低边与高边开关的参考点 | 1 |
| 22 | 3 | 3.5 | `ch03-switch-budget` | V4 | 继电器基极电阻的两笔账 | 1 |
| 23 | 3 | 3.9 | `ch03-ce-swing-budget` | V4 | 共射级的摆幅预算与削波方向 | 1 |
| 24 | 4 | 4.3 | `ch04-dvdt-false-turnon` | V4 | dv/dt 误导通的定量图像 | 1 |
| 25 | 4 | 4.4 | `ch04-deadtime-ledger` | V4 | 死区损耗的明账 | 1 |
| 26 | 4 | 4.4 | `ch04-gate-window` | V4 | 栅极保护的电压窗 | 1 |
| 27 | 4 | 4.5 | `ch04-thermal-chain-ledger` | V4 | 热失效的热阻链与四种测量自欺 | 1 |
| 28 | 5 | 5.2 | `ch05-rp-power` | V4 | 上拉电阻自己的功耗 | 1 |
| 29 | 5 | 5.4 | `ch05-tristate-handover` | V4 | 三态总线的交接时序 | 1 |
| 30 | 5 | 5.6 | `ch05-ab-bias-thermal` | V4 | AB 类偏置的热耦合与散热器两笔账 | 1 |
| 31 | 5 | 5.6 | `ch05-shoot-through-ledger` | V4 | 推挽正常半周与直通的电流功率对账 | 1 |
| 32 | 6 | 6.1 | `ch06-741-four-blocks` | V4 | 741 内部四级的分工与补偿代价 | 1 |
| 33 | 6 | 6.3 | `ch06-bias-balance` | V4 | 输入偏置电流与平衡电阻 | 1 |
| 34 | 6 | 6.7 | `ch06-slew-vs-gbw` | V4 | 压摆率与全功率带宽的两套物理 | 1 |
| 35 | 7 | 7.2 | `ch07-pullup-three-accounts` | V4 | 上拉电阻同时挂在三本账上 | 1 |
| 36 | 7 | 7.2 | `ch07-threshold-budget` | V4 | 阈值精度的误差预算排序 | 1 |
| 37 | 7 | 7.3 | `ch07-hysteresis-window` | V4 | 迟滞窗口与两个阈值 | 1 |
| 38 | 8 | 8.1 | `ch08-transfer-gate-v2` | A1 | 传输门的阈值缺口与互补并联（技术原型，待风格复评） | 1 |
| 39 | 8 | 8.2 | `ch08-mux-address-glitch-v2` | A4 | 4051 地址跳变的路过通道与 INH 对策（技术原型，待风格复评） | 1 |
| 40 | 8 | 8.4 | `ch08-sample-hold-v2` | A1 | 采样保持四拍与一个电容的三笔账（技术原型，待风格复评） | 1 |
| 41 | 8 | 8.6 | `ch08-charge-injection-v2` | A4 | 关断瞬间电荷注入的两路分账（技术原型，待风格复评） | 1 |
| 42 | 9 | 9.1 | `ch09-reference-ladder` | V4 | 基准选型的精度阶梯 | 1 |
| 43 | 9 | 9.2 | `ch09-tl431-divider-floor` | V4 | TL431 分压电阻的下限 | 1 |
| 44 | 9 | 9.3 | `ch09-esr-window` | V4 | LDO 的 ESR 稳定窗口 | 1 |
| 45 | 9 | 9.4 | `ch09-ldo-four-accounts` | V4 | 7805 四种死法对应的四本账 | 1 |
| 46 | 10 | 10.1 | `ch10-555-threshold-clamp` | V4 | 555 的两条门限与占空比 | 1 |
| 47 | 10 | 10.3 | `ch10-555-fault-tree` | V4 | 555 故障图谱五站定位 | 1 |
| 48 | 10 | 10.4 | `ch10-astable-reverse-design` | V4 | 按 38kHz 目标反推 555 元件值 | 1 |
| 49 | 10 | 10.4 | `ch10-duty-fifty-paths` | V4 | 准 50% 占空比的三条路与两个极端 | 1 |
| 50 | 10 | 10.5 | `ch10-monostable-budget` | V4 | 单稳态 1.1RC 的误差预算 | 1 |
| 51 | 10 | 10.5 | `ch10-recovery-gap` | V4 | 单稳态恢复时间与连发触发 | 1 |
| 52 | 11 | 11.10 | `ch11-noise-three-taxes` | V4 | 三种噪声税与信噪比算例 | 1 |
| 53 | 11 | 11.11 | `ch11-two-stage-margin` | V4 | 两级放大器四项指标的余量对账 | 1 |
| 54 | 11 | 11.3 | `ch11-mirror-three-errors` | V4 | 电流镜的三笔误差 | 1 |
| 55 | 11 | 11.5 | `ch11-miller-bandwidth` | V4 | 米勒电容把带宽压到 15.8kHz | 1 |
| 56 | 11 | 11.5 | `ch11-phase-margin-table` | V4 | 相位裕度与阻尼比过冲的换算 | 1 |
| 57 | 11 | 11.7 | `ch11-diffpair-four-beats` | V4 | 差分对的四拍：尾电流只准重新分配 | 1 |
| 58 | 12 | 12.10 | `ch12-tia-three-way` | V4 | TIA 的增益带宽稳定三角 | 1 |
| 59 | 12 | 12.12 | `ch12-switch-cap` | V4 | 开关电容的等效电阻 | 1 |
| 60 | 12 | 12.12 | `ch12-switched-cap-equivalent` | V4 | 开关电容等效电阻的来历与代价 | 1 |
| 61 | 12 | 12.13 | `ch12-input-stage-source-z` | V4 | 按源阻抗选运放输入级 | 1 |
| 62 | 12 | 12.13 | `ch12-input-types` | V4 | 按源阻抗选输入级 | 1 |
| 63 | 12 | 12.9 | `ch12-riso-feedback-point` | V4 | 隔离电阻的反馈取点与相位裕度 | 1 |
| 64 | 13 | 13.10 | `ch13-crystal-neg-resistance` | V4 | 晶振起振的负阻裕度 | 1 |
| 65 | 13 | 13.11 | `ch13-opto-ctr` | V4 | 隔离三条路线与 CTR | 1 |
| 66 | 13 | 13.5.1 | `ch13-compliance-ceiling` | V4 | 恒流源的合规电压天花板 | 1 |
| 67 | 13 | 13.6 | `ch13-sampling-quantization` | V4 | 采样率与量化台阶的两道账 | 1 |
| 68 | 13 | 13.7 | `ch13-h-bridge-states` | V4 | H 桥四拍 | 1 |
| 69 | 13 | 13.8 | `ch13-current-sense-budget` | V4 | 10mΩ 分流电阻的两笔账 | 1 |
| 70 | 13 | 13.8 | `ch13-current-sense-sides` | V4 | 低侧与高侧电流检测 | 1 |
| 71 | 13 | 13.9 | `ch13-audio-class-heat` | V4 | B 类与 D 类推同一只喇叭的热账 | 1 |
| 72 | 14 | 14.10 | `ch14-tolerance-three` | V4 | WC、RSS 与 3σ | 1 |
| 73 | 14 | 14.12 | `ch14-pt100-error-budget` | V4 | PT100 的误差预算与比率测量 | 1 |
| 74 | 14 | 14.2 | `ch14-arrhenius-ten-degree` | V4 | 结温与失效率 | 1 |
| 75 | 14 | 14.2 | `ch14-derating-margin` | V4 | 常用降额线 | 1 |
| 76 | 14 | 14.5 | `ch14-thermal-budget` | V3 | LDO 的热阻预算 | 1 |
| 77 | 14 | 14.6 | `ch14-ltspice-five` | V5 | LTspice 五种分析 | 1 |
| 78 | 14 | 14.8 | `ch14-dft-testpoints` | V4 | 测试点与量产测试 | 1 |
| 79 | 15 | 15.1 | `ch15-adc-straddle` | V4 | ADC 骑跨分区线 | 1 |
| 80 | 15 | 15.1 | `ch15-crystal-three-no` | V4 | 晶振布局三不 | 1 |
| 81 | 15 | 15.1 | `ch15-four-zones` | V4 | 四区分团的三条约定 | 1 |
| 82 | 15 | 15.1 | `ch15-layout-ten-questions` | V4 | 布局十问 | 1 |
| 83 | 15 | 15.1 | `ch15-trace-drop` | V4 | 电源走线的压降账 | 1 |
| 84 | 15 | 15.3 | `ch15-crosstalk-3w` | V4 | 串扰三招与包地边界 | 1 |
| 85 | 15 | 15.3 | `ch15-via-parallel` | V3 | 过孔并联与电感 | 1 |
| 86 | 15 | 15.4 | `ch15-dfm-limits` | V4 | DFM 四个数 | 1 |
| 87 | 15 | 15.4 | `ch15-panelization` | V4 | V-cut 与邮票孔 | 1 |
| 88 | 15 | 15.4 | `ch15-testpoint-rules` | V5 | 测试点三条规矩 | 1 |
| 89 | 15 | 15.4 | `ch15-thermal-relief` | V4 | 热焊盘的两难 | 1 |
| 90 | 15 | 15.5 | `ch15-failure-signatures` | V5 | 翻车案例分诊 | 1 |
| 91 | 15 | 15.6 | `ch15-radiated-loop-area` | V4 | 回路面积决定辐射等级 | 1 |
| 92 | 15 | 15.7 | `ch15-ground-grid` | V4 | 双层板地网 | 1 |
| 93 | 15 | 15.7 | `ch15-return-review` | V4 | 回流审查五步 | 1 |
| 94 | 16 | 16.1 | `ch16-first-question` | V4 | 排故第一问 | 1 |
| 95 | 16 | 16.3 | `ch16-bandwidth-five` | V4 | 示波器带宽五倍规则 | 1 |
| 96 | 16 | 16.3 | `ch16-instrument-trust` | V4 | 仪器信任链 | 1 |
| 97 | 16 | 16.3 | `ch16-probe-compensation` | V4 | 探头补偿三种方波 | 1 |
| 98 | 16 | 16.5 | `ch16-bisect-injection` | V3 | 信号注入与二分 | 1 |
| 99 | 16 | 16.5 | `ch16-case-triage` | V4 | 三个案例的分诊 | 1 |
| 100 | 16 | 16.8 | `ch16-postmortem-split` | V4 | 根因与触发条件 | 1 |
| 101 | 17 | 17.1 | `ch17-esr-sweep` | A3 | ESR 参数扫描——纹波爬升 400mV、内部生热、容量蒸发至三成、闭环 | 1 |
| 102 | 17 | 17.1 | `ch17-symptom-four-fields` | A5 | 症状四空格操作演示——多少/何时/多常/改了什么，四空填满才许动烙铁 | 1 |
| 103 | 17 | 17.2 | `ch17-virtual-short-probe` | A5 | 核负反馈路径、量两输入端压差，再核工作前提与输出响应 | 1 |
| 104 | 17 | 17.4 | `ch17-subharmonic-edge` | A4 | 次谐波振荡失效边界——占空比推过 50%、一宽一窄、f_sw/2 分量、斜坡补偿 | 1 |
| 105 | 18 | 18.1 | `ch18-component-signatures` | V4 | 元件失效签名 | 1 |
| 106 | 18 | 18.1 | `ch18-dmm-averaging` | V4 | 万用表的平均滤镜 | 1 |
| 107 | 18 | 18.1 | `ch18-fault-record` | V4 | 可复用的故障档案字段 | 1 |
| 108 | 18 | 18.1 | `ch18-first-minute` | V4 | 60 秒目检 | 1 |
| 109 | 18 | 18.1 | `ch18-four-wire` | V4 | 两线法与四线法 | 1 |
| 110 | 18 | 18.1 | `ch18-power-three-touchpoints` | V4 | 先量电源的三处触点 | 1 |
| 111 | 18 | 18.1 | `ch18-probe-loading` | V4 | 探头电容把拐点拉低 | 1 |
| 112 | 18 | 18.1 | `ch18-reset-clock-enable` | V5 | 不启动的三板斧 | 1 |
| 113 | 18 | 18.1 | `ch18-swap-discipline` | V4 | 交换法三条纪律 | 1 |
| 114 | 18 | 18.1 | `ch18-temp-spray` | V4 | 温度手段与安全边界 | 1 |
| 115 | 18 | 18.2 | `ch18-ground-lead-inductance` | V4 | 探头地线的假振铃 | 1 |
| 116 | 18 | 18.2 | `ch18-measurement-snr` | V4 | 源头放大锁住信噪比 | 1 |
| 117 | 18 | 18.2 | `ch18-predict-before-probe` | V4 | 下探头前先预测 | 1 |
| 118 | 18 | 18.3 | `ch18-assumption-tree` | V4 | 假设树与互斥分支 | 1 |
| 119 | 18 | 18.3 | `ch18-two-way-validation` | V4 | 正向、反向与边界验证 | 1 |
| 120 | 17 | 17.2 | `ch17-virtual-short-test` | V3 | 已插旧图返审：核前提、按误差预算读压差、再验证输出；原审批归档保留 | 1 |
| 121 | 15 | 15.2 | `ch15-return-mirror` | V4 | 高频回流镜像电流：完整地平面 vs 开槽绕路 | 1 |
| 122 | 15 | 15.2 | `ch15-ground-bounce-ledger` | V4 | 地弹三笔账：回路电感、总线 di/dt、基准 LSB | 1 |
| 123 | 15 | 15.2 | `ch15-ground-freq-split` | V4 | 接地策略频段分工与 1/20 波长判据 | 1 |
| 124 | 15 | 15.2 | `ch15-stackup-bridge` | V4 | 四层/六层叠层参考面与跨分割桥接纪律 | 1 |
| 125 | 16 | 16.9 | `ch16-record-card` | V4 | 一页纸排故记录表：现场/推演/收口三栏与边界 | 1 |
| 126 | 11 | 11.6 | `ch11-noise-identify` | V4 | 噪声现场辨认：五症状对频谱与工况 | 1 |
| 127 | 4 | 4.1 | `ch04-channel-formation` | V4 | 沟道形成三步：反型层与栅极电容账 | 1 |
| 128 | 3 | 3.2 | `ch03-region-check` | V5 | 三区判读流程：两个电压分四路 | 1 |
| 129 | 18 | 18.2 | `ch18-williams-workbench` | V1 | Williams 工作台四纪律：先预测、短地线、最小电路、源头放大 | 1 |

## 分布

| 章 | 张数 |
|---:|---:|
| 0 | 4 |
| 1 | 5 |
| 2 | 8 |
| 3 | 7 |
| 4 | 5 |
| 5 | 4 |
| 6 | 3 |
| 7 | 3 |
| 8 | 4 |
| 9 | 4 |
| 10 | 6 |
| 11 | 7 |
| 12 | 6 |
| 13 | 8 |
| 14 | 7 |
| 15 | 19 |
| 16 | 8 |
| 17 | 5 |
| 18 | 16 |
| **合计** | **129** |

| 类型 | 张数 | 说明 |
|---|---:|---|
| V4 | 107 | 静态手绘主图 |
| V1 | 1 | 场景主图（Williams 工作台） |
| V5 | 5 | 流程／决策图 |
| V3 | 4 | 定量／条件判读图，含 1 张已插旧图返审 |
| A1–A5 | 12 | 动画（需动态入口才能评「运动叙事／交互节奏」） |
| **合计** | **129** | figures-v2 116 张、svg-v2 12 张、figures 返审 1 张 |

