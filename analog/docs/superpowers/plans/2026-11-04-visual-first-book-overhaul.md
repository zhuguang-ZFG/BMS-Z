# 视觉优先彻底改造 Implementation Plan

> **当前状态（2026-11-08 ch14/ch15 续作实测）**：执行中，未达到完成定义。正文视觉锚点 **444**，**19/19章密度通过**（最长≤1500、零堆图）；ch14为23个锚点/最长1496字，ch15为31个/1487字。已验收独立动画 **94/220**，已验收静态资产 **169/180**；本轮22张新建或技术改图保持generated，不沿用旧评分。正文331,946字符，较基线减少 **21.07%**，超过“原则10%–20%”区间，需继续保全复核。153旧动画仍缺逐项处置，发布闸 **346项失败**，正文内嵌非legacy待审资产 **60项**。65项定向回归通过；A4/16K最终PDF未验收。详见[本轮ch14/ch15记录](../visual/reviews/ch14-15-continuation-2026-11-08.md)及[此前续作记录](../visual/reviews/spec-continuation-2026-11-08.md)。

> 下列带日期的复核段落是历史证据；最新进度以上述实测和续作记录为准。

> **Task 0–3 实测复核（2026-11-04，逐项查文件与跑闸，非按提交信息推断）**：`test_visual_density.py` 7 项、`test_visual_distribution.py` 11 项、`test_visual_manifest.py` 11 项、`test_handraw_prompt_records.py` 8 项全绿；`python scripts/check_visual_manifest.py` PASS（0 项）。manifest 已登记 249 条（239 `legacy-unreviewed` + 10 `generated`）。
> 历史缺口（本轮已补齐，见各 Task 勾选及续作实测）：Task 0 — SVG 正文引用数与打印分镜状态未入基线、A4/16K PDF 页数尺寸未记录（`quality-rubric.md` 已于 2026-11-05 写）；Task 1 — 三个上游 JSON 的哈希未记录；Task 2 — 审计未输出视觉类型数/逐 H2 覆盖/堆图位置、缺公式块夹具；Task 3 — 静态字段缺替代文本、动画缺参数与结论帧且未建 `animation-v2-manifest.yml`、状态机未强制越级、数值校验无「示意」豁免。

> **Task 4 三章试片实测复核（2026-11-05，`python scripts/check_backlog_layout.py --check` 实跑＋全文数字回查，非按提交信息推断）**：ch00 15 候选（10 套用／5 deferred）套用后视觉 18/18、最长段 1369、硬超 0、堆图 1（既有锚点 42→50 隔 166 字）；ch08 25 候选（20／5）视觉 32/32、最长段 1470、硬超 0、堆图 1（既有锚点 128→139 隔 311 字）；ch17 15 候选（10／5）视觉 24/18、最长段 2257、硬超 2（表 17-2／表 17-3 两处表墙）。三章合计 5 项待修，逐条对应上面三条 FAIL／堆图，全部已登记在 8 个 `open_decisions`（ch00 2／ch08 4／ch17 2）内，无未登记失败。数值可追溯性：`keep_facts` 323 条里的 718 个阿拉伯数字逐条回查对应正文，命中 717；唯一未命中是千分位拆词假阳性（`$4\,700\,\Omega$` 被切成 4 与 700，原文在 `docs/p1-01-ch0.md:255` 逐字存在）。分型勘误：ch17 的 V3/V5 占比原记 11/24 = 46%，按 `ch17.yml` 套用后重算为 V3 6 ＋ V5 7 = 13/24 = 54%（`ch17.yml`、`reviews/pilot-decision.md`、`reviews/pilot-contact-sheet.html` 三处同步改正）。
> 全量 `python -m pytest scripts/ -q`：**389 passed / 7 failed**。7 项失败与本轮视觉工作无关（本轮只新增 `chapter-backlog/*.yml`，未改这些测试读取的任何文件）：3 项缺 ngspice（本机未装，环境）；3 项 `test_curriculum` 章节数漂移（ch0 卡片写「11 节」、文档实测 14 节，metadata 表未重跑）；1 项 `test_site_build` 构建产物 `p4-02-ch17.html` 残留未渲染 Markdown。视觉相关四套（`test_backlog_layout`／`test_visual_density`／`test_handraw_prompt_records`／`test_grayscale_fixture`）**55 项全绿**。
> 历史生产形态偏差（2026-11-04 更正，见 `handraw-style-lock.md`）：**本机生图工具可用**，ch17 三套方向共 9 张无文字底图已由生图产出（`reviews/pilot-2026-11-04/`，`generator: imagegen-tool`）；此前「当前环境无生图模型」的记录已被证伪。偏差仍在另一处——底图 + 技术 overlay 的双层合成（Task 5 的 `compose_technical_overlay.py` 与 `assets/figures-v2/`）尚未落地，故生图底图**只用于接触表打分、不进正文**，已发布的静态图仍走确定性 SVG 并落 `assets/figures/`（字形子集与既有闸只扫这里）。公式、器件参数、中文标注与数值任何情况下都不交给生图模型。 当前合成管线状态见本轮续作实测与 `technical-overlay-contract.md`。

> **本轮续作实测（2026-11-05）**：Task 0–3 的列明缺口已补齐；Task 5 的合成/印刷管线与三张技术校样已落地，实际底图复评尚未完成。当前会话没有内置生图工具，`OPENAI_API_KEY` 也未配置，用户已授权继续并要求自行寻找通道；本机聚合服务与现有相关供应商已只读核查，未发现已启用的图像模型。三张 API 请求已完成 dry-run，未产生调用费用。下文早期复核段落作为历史记录保留；本节与各 Task 当前勾选状态为准。不得把 3 张技术校样当作新 FF-015 底图，不能据此启动全书波次。
> 审阅入口：`docs/superpowers/visual/reviews/quant-pilot-2026-11-05/index.html`。本轮仅准备三张 priority-1 试片，ch00/ch08/ch17 的全部点位仍需继续做 planner 全章复核。
> 验证：相关测试 **165 passed**，manifest PASS；三张技术校样最小 9.185pt，桌面/手机审阅页无破图或溢出。详细证据与未过闸项目见 `docs/superpowers/visual/reviews/continuation-2026-11-05.md`。
> **后续动画续作（2026-11-05）**：Task 6–7 已实现，六组动画技术审阅页 `build/visual-v2/review.html` 可直接打开；ch17 四个正文播放器实测可用。最终组合回归 **200 passed**，另一次站点相关回归 76 passed（有重叠）；站点、A4 离线 HTML 与 16K 书稿已重建。尚未重渲最终 PDF，也未完成纸雕底图与人工复评。证据见 `docs/superpowers/visual/reviews/animation-v2-2026-11-05.md`。

> **Python 插图波次（2026-11-05）**：用户允许代码绘制后，I²C 上拉、热阻链、排故四象限三图已接入 ch17。被替换的三段说明净减少 149 字（不含新增图注/标签）；纯 SVG 印刷版和三页 16K 彩色/灰度校样已生成。审阅入口 `reviews/python-papercut-2026-11-05/index.html`，证据 `review.md`。旧 API 阻塞段落保留作历史，当前以 Python 绘图路径继续。
> 本波验证：相关组合测试 204 passed，另 4 项纸层专用测试通过，合计 208；manifest PASS，派生数据同步。三张图在真实 ch17 页面加载成功，手机无横向溢出；三页校样 PDF 无位图、文字可提取。A4 离线 HTML 与 16K 书稿已重建，未宣称全书最终 PDF 验收通过。

**Goal:** 把当前“文字为主、图作为补充”的教材改造成“图承担推理、文字负责精确补充”的视觉教材；使用 `yang0/handraw-style` 规划并生成静态视觉底图，以模块化 SVG 动画 V2 承担动态机理，最终在站点、离线书、PDF、视频和社媒五线保持一致。

**Current baseline:** 452,536 原文字符（含 alt、figcaption 与标签语法）／420,573 正文字符（剥掉 `<figure>` 整块与独立 `<img>`）；54 静态分析图、32 照片、114 个正文内嵌动画实例；200 个正文视觉锚点；153 个独立 SVG；19/19 章最长无图段 >3000 字；旧生成器 9589 行。

**Exit:** ≥390 个正文视觉锚点、≥220 个独立动画、19/19 章最长无图段 ≤1500 字、所有视觉资产有 handraw-style 记录与事实来源、A4/16K/网页/无障碍全绿。

---

## Global Constraints

- `docs/*.md` 仍是唯一内容源。
- 当前未提交视频和 PDF 只作基线，不在本计划 Accepted 前推送。
- `handraw-style` 只参与视觉规划、风格/图型/色彩选择和视觉底图生成；公式、电路、中文标注与数值由确定性 SVG/HTML 绘制。
- 每张图先规划再生成，禁止批量“看标题出图”。
- 每个旧动画必须逐张审查，禁止全库统一换色冒充重做。
- 先三章试片，用户确认后才进入全书波次。
- 视觉增加必须伴随文字替换；不得只加图不减文。
- 新旧资产并存迁移，禁止一次性覆盖导致无法回滚。
- 不提交 handraw-style 外部仓库副本；项目只记录 URL、commit、选择结果、提示词与最终资产。
- 每个 Task 单独提交；发布前不 push，除非用户再次明确授权。

---

## Target File Structure

```text
docs/superpowers/visual/
  baseline-2026-11-04.json
  visual-manifest.yml
  animation-v2-manifest.yml
  handraw-style-lock.md
  quality-rubric.md
  chapter-backlog/
    ch00.yml ... ch18.yml
  prompts/
  reviews/
scripts/
  audit_visual_density.py
  check_visual_manifest.py
  build_visual_contact_sheet.py
  visuals/
    tokens.py
    primitives.py
    timeline.py
    layouts.py
    render.py
    scenes/
assets/
  figures-v2/
  svg-v2/
  storyboards-v2/
scripts/test_visual_density.py
scripts/test_visual_manifest.py
scripts/test_visual_distribution.py
scripts/test_animation_v2.py
scripts/test_visual_fidelity.py
scripts/test_print_storyboard_v2.py
scripts/test_visual_player.py
```

---

## Task 0: 冻结当前发布动作与保存基线

**Files:**
- Modify: `docs/superpowers/checklists/ship-gate.md`
- Create: `docs/superpowers/visual/baseline-2026-11-04.json`
- Create: `docs/superpowers/visual/quality-rubric.md`

- [x] 在 ship-gate 文首标记“视觉彻底改造 Draft 期间不发布”。
- [x] 记录当前 19 章字符、静态图、照片、内嵌动画、最长无图段。
- [x] 记录当前 153 张 SVG 文件清单、SHA-256、正文引用数和打印分镜状态。（`capture_visual_baseline.py --enrich` 从冻结提交 8961d38 补录：153 张、114 个正文引用、153/153 内存分镜无动画残留；原章节统计和原 SHA 保留。生成器代码哈希与实测日期单独记录。）
- [x] 保存当前 A4 PDF、16K 双卷页数与文件尺寸，仅作对照，不入 Git。（本地 `build/visual-baseline/pdf-baseline-2026-11-05.json`：A4 803 页 / 67,513,457 bytes；16K 上卷 532 页 / 27,351,484 bytes，下卷 592 页 / 26,890,121 bytes；含 SHA-256、页面尺寸及文件修改时间。是当前本地产物快照，不推断为 11-04 构建。）
- [x] 写 35 分视觉质量量规：教学必要性、事实精度、构图层级、风格一致性、印刷可读性、运动叙事、交互节奏。（2026-11-05 落地 `docs/superpowers/visual/quality-rubric.md`：静态 5 维每项 ≥4、动画 7 维每项 ≥4 且合计 ≥30，1–5 分锚点取自 ch17 试片实测失分，并列出定量图四规的 manifest 字段表。代码侧同轮补齐此前只在规格里的动画合计闸 `ANIM_TOTAL_FLOOR=30`（原来仅逐维查 ≥4），夹具 `test_visual_manifest.py` 22 项全绿）

**Exit:** 基线可复现；后续每波能比较“增了什么、删了什么、文字减了多少”。

**Commit:** `docs: 冻结视觉改造基线与质量量规`

---

## Task 1: 锁定 handraw-style 工具链

**Files:**
- Create: `docs/superpowers/visual/handraw-style-lock.md`
- Create: `docs/superpowers/visual/prompts/README.md`
- Create: `scripts/test_handraw_prompt_records.py`

- [x] 记录上游 `https://github.com/yang0/handraw-style` 与使用 commit `572dff8f8cc1dc16ff9bef1422e90b3dfc42284d`。
- [x] 记录实际使用的 `styles.json`、`layouts.json`、`colors.json` 哈希。（11-05 再次读取本地上游，HEAD 与三项 SHA 均匹配 `handraw-style-lock.md`。）
- [x] 说明本地上游全库校验当前因无关文件中的绝对路径泄漏失败；项目 CI 只校验被使用条目，不依赖上游全库通过。
- [x] 定义 prompt 记录格式：原始主题、style_id、layout_id、color_ids、参考图策略、中文 prompt、英文 prompt、生成模型、输出文件。
- [x] 写测试：任一 `figures-v2` 或动画关键帧没有 prompt 记录即失败。（`test_handraw_prompt_records.py` 8 项全绿）
- [x] 不把用户机器绝对路径写进项目 prompt；参考图只记录上游相对路径与 commit。（全项目视觉文件扫描无绝对路径命中）

**Exit:** handraw-style 的使用是可追溯、可升级、可复现的，不是“口头说用了”。

**Commit:** `chore: 锁定 handraw-style 版本与提示词记录契约`

---

## Task 2: 视觉密度审计器与永久闸

**Files:**
- Create: `scripts/audit_visual_density.py`
- Create: `scripts/test_visual_density.py`
- Create: `scripts/test_visual_distribution.py`
- Modify: `Makefile`

- [x] 扫描 `docs/p*-ch*.md` 中实际内嵌的 figures/photos/svg-v2；链接不计数。
- [x] 输出每章字符数、视觉类型数、每个 H2 的视觉覆盖、最长无图段和聚集位置。（`--json` 包含 `by_kind`、`h2_coverage`、`gap_spans`、`cluster_spans`；V2 目录正确归类，多行图片保留原文行号。）
- [x] 视觉间距少于 400 字时报“堆图”；超过 1200 字警告，超过 1500 字失败。
- [x] H2 正文超过 800 字无图直接失败。
- [x] 写夹具测试，覆盖 HTML `<img>`、Markdown 图片、链接冒充图、代码块和公式块；另测 V2 分型与多行标签之后的堆图行号。
- [x] 增加 `make visual-audit` 与 `make visual-ship`。

**Exit:** 旧树预期失败；三章试片后对应章节转绿；全书完成时 19/19 转绿。

**Commit:** `test: 视觉密度与章节分布永久闸`

---

## Task 3: Manifest、事实源与审图状态机

**Files:**
- Create: `docs/superpowers/visual/visual-manifest.yml`
- Create: `docs/superpowers/visual/animation-v2-manifest.yml`
- Create: `scripts/check_visual_manifest.py`
- Create: `scripts/test_visual_manifest.py`
- Create: `scripts/test_visual_fidelity.py`

- [x] 定义静态资产字段：ID、章、锚点、类型、职责、style/layout/color、来源、prompt、输出、替代文本、状态、评分。（10 条非 legacy 资产已补 alt 与履历，未提升审图状态。）
- [x] 定义动画字段：静态字段 + 具名 beats、duration、parameters、conclusion_frame、reduced_motion、print_fallback、storyboard。动画表 `animation-v2-manifest.yml` 从主表派生，检查缺失及漂移；4 条 V2 动画已迁移。
- [x] 状态只允许 `planned → generated → reviewed → accepted → published`；`status_history` 验证完整顺序，`--transition` 每次只前进一步，`--previous` 拦截跨快照越级或回退。评分限制到 4..5，并验证动画总分 ≥30。
- [x] 检查 docs 锚点与来源存在。
- [x] 图中数字回对 `source_facts` 指向的小节；同时检查 prompt numbers 与 SVG 可见文字。示意值须逐项写 value/label/reason 且图内标注“示意”。本轮拦出 ESR 的 0.1Ω→3Ω 未声明端点，已在生成器、三件套和 prompt 中补注。
- [x] 旧 153 张动画先全部登记为 `legacy-unreviewed`。（bootstrap 实登记 249 条：157 动画 + 61 figure + 31 照片）

**Exit:** 无 manifest 资产不能进入正文。

**Commit:** `feat: 视觉资产 manifest 与事实一致性闸`

---

## Task 4: 三章风格试片与用户确认

**Scope:** ch0、ch8、ch17。

**Files:**
- Create: `docs/superpowers/visual/chapter-backlog/ch00.yml`
- Create: `docs/superpowers/visual/chapter-backlog/ch08.yml`
- Create: `docs/superpowers/visual/chapter-backlog/ch17.yml`
- Create: `docs/superpowers/visual/reviews/pilot-contact-sheet.html`
- Create: `docs/superpowers/visual/reviews/pilot-decision.md`

- [ ] 用 article-illustration-planner 标出每章 12–20 个候选点位。（已：三章 backlog 齐了，`python scripts/check_backlog_layout.py --check` 实测——`ch00.yml` 15 个候选（10 套用／5 deferred，套用后视觉 18/18、最长段 1369、硬超 0、堆图 1）、`ch08.yml` 25 个候选（20 套用／5 deferred，视觉 32/32、最长段 1470、硬超 0、堆图 1）、`ch17.yml` 15 个候选（10 套用／5 deferred，视觉 24/18、最长段 2257、硬超 2、堆图 0）。数字勘误：本行原写「ch17.yml 24 个点位」，24 实为套用后的视觉数（14 既有锚点＋10 新增），候选点位是 15。点位来源仍是 `audit_visual_density.py` ＋ `check_backlog_layout.py` 的断层／堆图实测，未走 article-illustration-planner 推荐流程；15 个 deferred 各自附实测间隔或「预算已满」理由，被闸挡下的合法候选登记在三个文件的 `open_decisions`（ch00 2 项／ch08 4 项／ch17 2 项，含 ch08 预算 32/32 吃满与两处既有堆图 311／166 字）
- [x] 每个点位写清：要替代的文字、保留的公式/数字、图型 ID、图片类型。（三章 55 个候选点位＝40 可套用＋15 deferred，全部含 `replace_text`/`keep_facts`/`layout_id`/`type`/`anchor`/`insert_after_line`/`delete_lines`。数值回查实测：`keep_facts` 共 323 条（ch00 73／ch08 142／ch17 108），其中阿拉伯数字 718 个（226／388／104）逐条回查对应正文，未命中 1 个——查证为 LaTeX 千分位假阳性（`$4\,700\,\Omega$` 被拆成 4 与 700，原文在 `docs/p1-01-ch0.md:255` 逐字存在），实际 100% 可追溯。口径须记明：`keep_facts` 是给图上用的压缩句，不逐字引用正文（整句原文匹配仅 16＋11＋28＝55/323 条），数字与型号一律取正文原值）
- [x] 从 handraw-style 全库动态推荐 3 套视觉方向；FA-029 只作为其中一套技术图候选。（A=FA-029 几何图式叙事、B=FH-043 复古 Risograph/丝网、C=FF-015 纸雕微距；三套均经 `resolve_reference.py --model gpt-image-2 --style <完整ID>` 判定为不需垫图）
- [x] 每套各做 3 张代表图：现象主图、定量图、失效对比图。（9 张无文字底图在 `reviews/pilot-2026-11-04/`：hero/chart/compare ×3；提示词记录 `prompts/pilot/pilot-*.md`，`generator: imagegen-tool`，zh_prompt 取自实际调用而非重建）
- [x] 关键文字和电路用 SVG overlay 重绘，不直接采用 AI 图中文字。（本轮经用户授权改为 Python 绘制无文字纸层 + 独立技术 SVG，三张完整风险插图已完成；记录 `reviews/python-papercut-2026-11-05/review.md`。）
- [x] 生成原版/候选 A/B/C 接触表，按 35 分量规打分。（`reviews/pilot-contact-sheet.html`：原版+A/B/C × 3 行，浏览器实测 12 图全部加载、0 破图、无横向溢出。口径偏差须记明：试片是静态图，用的是**静态 25 分量规**（5 项 ×5，A 20 / B 16 / C 15，动画两项标 N/A）；本行写的「35 分量规」是规格里动画七项口径（≥30/35），本轮不适用）
- [x] 用户选择主风格、辅助风格和色彩；未确认前停止批量生产。（2026-11-05 拍板：主风格 **FF-015 纸雕微距**作全书主语言；色族换装 **C-34 奶油白纸 / C-32 炭黑墨 / C-35 石板灰阴影 / C-26 柿子橙重点**——拍板标签把石板灰写成「纸」，实测纸墨仅 1.91:1、纸重点 1.24:1，已由用户确认改判为阴影调；夹具 `scripts/make_grayscale_fixture.py` + `scripts/test_grayscale_fixture.py` 4 项 + `make visual-gray`。缺口：**辅助风格仍空**（原推荐「C 限定 V1/V6」以主风格为 A 为前提，主风格改 C 后自相矛盾、失效）。批量生产按主风格/色彩两项解锁，但 V3/V5 定量与流程点位（ch17 原记 11/24 = 46% 有误，2026-11-05 按 `ch17.yml` 套用后重算为 V3 6 ＋ V5 7 = 13/24 = 54%；三章按「可套用点位」口径：ch00 7/10、ch08 12/20、ch17 6/10，合计 25/40 = 62%——ch00／ch08 的张数记在各自 `style.blocked_until`／`style_decision.blocked_until`，恰是 FF-015 本轮失分最狠处：事实精度 3、印刷可读性 2、构图层级 3）在「3 张 FF-015 定量底图带灰度对照复评」完成前不得进入波次——同句原先并列的「四条定量图规则写进闸」已于 2026-11-05 完成：`check_visual_manifest.py` 新增 `quant_rules` 五字段闸（仅约束 `style_id=FF-015` 的 V3/V5 非 legacy 条目）＋ `quality-rubric.md`，夹具 22 项）

**Exit:** 一份明确的 `pilot-decision.md`，锁定主视觉语言和允许的辅助语言。

**Commit:** `design: 三章视觉试片与 handraw 风格决策`

---

## Task 5: 静态插图生产管线

**Files:**
- Create: `scripts/build_visual_contact_sheet.py`
- Create: `scripts/compose_technical_overlay.py`
- Create: `assets/figures-v2/`
- Modify: `scripts/test_figures.py`

- [x] 定义底图 + 技术 overlay 双层文件规范。（`technical-overlay-contract.md` 与 composition JSON；缺底图失败，显式 `--print-only` 只出技术校样。）
- [x] overlay 负责电路、公式、坐标、参数、中文标注和编号；底图自包含内嵌，禁止外链和脚本。
- [x] 输出 1448×1086 或等比例 SVG/WebP；印刷有效宽度下最小正文 8.5pt。（三张技术校样按 138mm 版心实测最小 9.19pt、浏览器文字边界全过。）
- [x] 保留纯 SVG 印刷版与 WebP 预览；书构建按 manifest 选择 print_fallback，动画选 storyboard，字体子集覆盖 V2 目录。
- [x] 检查画布内文字、对比度、字号、图片 alt、色盲可辨性。（三张真实彩色/灰度图已查看：空心圆/叉号与直接标签区分，最小字号 8.6449pt；纸层厚度不编码值。评分为代理本地试点复核，用户三章验收仍待完成。）
- [x] 自动生成每波接触表，支持 12/18/24 张分页、灰度对照、七项动画评分与嵌套输出目录；缺图明确标待生成。

**Exit:** 静态图能批量生产，但任何图仍必须逐项经过 manifest 与人工评分。

**Commit:** `feat: handraw 底图与技术 overlay 静态插图管线`

---

## Task 6: 动画生成器 V2 骨架

**Files:**
- Create: `scripts/visuals/tokens.py`
- Create: `scripts/visuals/primitives.py`
- Create: `scripts/visuals/timeline.py`
- Create: `scripts/visuals/layouts.py`
- Create: `scripts/visuals/render.py`
- Create: `scripts/visuals/scenes/`
- Create: `scripts/test_animation_v2.py`
- Create: `assets/svg-v2/`

- [x] 从旧单体生成路径分离 token、图元、时间轴、布局与输出层；`tokens.py` / `primitives.py` / `layouts.py` 已落地，旧生成器不再扩张。本轮不等于 153 张旧图全部迁移。
- [x] 场景文件按章拆分；单文件建议不超过 500 行。
- [x] 时间轴使用命名 beat，不直接散写 keyTimes。
- [x] 内置 ease-in-out、progressive reveal、focus、camera、parameter sweep、conclusion hold。
- [x] 默认只播放一次；结论帧停留。
- [x] 自动生成 reduced-motion 版本和 3–5 格打印分镜。
- [x] 先做 3 类代表动画：新增 `ch00-current-loop-v2`（A1）、`ch00-divider-derivation-v2`（A2），并保留 `ch17-esr-sweep`（A3）验证共用时间轴/渲染层。两张新图标记 engine-prototype，仍待主风格复评，未放入正文。
- [x] V2 与旧动画可同时存在，manifest 决定正文引用。

**Exit:** 三类动画在同一框架下可复用，但画面不再同模板同节奏。

**Commit:** `feat: 模块化 SVG 动画 V2 引擎`

---

## Task 7: 网页动画播放器

**Files:**
- Create: `scripts/site_media/visual-player.js`
- Modify: `scripts/site_media/learning.js`
- Modify: `scripts/build_site.py`
- Create: `scripts/test_visual_player.py`
- Modify: `scripts/test_reduced_motion.py`

- [x] 构建时为 manifest 中已生成的 V2 动画输出 `data-visual-player` 外壳；静态回退默认可读，点击才加载受控动画。ch17 四个现有正文入口已接通。
- [x] 支持播放、暂停、重播、0.5×/1×/1.5×、节拍跳转。
- [x] 显示当前节拍名称和总进度。
- [x] 键盘可操作，按钮有 aria-label，焦点顺序正确。
- [x] reduced-motion 默认显示结论关键帧。
- [x] 无 JS 保留静态图、图注和动画中心链接。
- [x] 移动端不遮正文，不自动无限循环。

**Exit:** 已在真实 ch17 站点逐个验证四个播放器可加载；390px 手机页面无横向溢出。A4/16K 构建清除网页控件并改用 storyboard。浏览器回归覆盖倍速、暂停、键盘跳转、结论停留、加载失败、无 JS 与 reduced-motion。

**Commit:** `feat: 章节动画播放器与减弱动效回退`

---

## Task 8: 三章试点正文改造

**Files:**
- Modify: `docs/p1-01-ch0.md`
- Modify: `docs/p1-09-ch8.md`
- Modify: `docs/p4-02-ch17.md`
- Create/Modify: 对应 `assets/figures-v2/`、`assets/svg-v2/`、storyboards、prompts、manifest

- [x] ch0 从 8 个视觉锚点提升到 ≥18，最长无图段 ≤1200。（2026-11-08 实测：18、1177。）
- [x] ch8 从 12 提升到 ≥32，覆盖模拟开关、采样保持、注入、时钟馈通、失效边界。（2026-11-08 实测：32、最长段 1474。）
- [x] ch17 从 4 提升到 ≥18，把 15308 字断层拆成症状图、测点图、决策树、逼现流程和回归闭环。（2026-11-08 实测：24、最长段 1481。）
- [ ] 每章至少 6 张静态图、4 个 V2 动画。
- [ ] 删除被图替代的重复文字，章字符数下降 10%–25%。
- [ ] 逐图跑 35 分量规；任一维度 <4 返工。
- [ ] 重建站点、离线书和试点 PDF，人工翻页。

**Exit:** 用户确认“这才是要的书籍质量”。未确认则回 Task 4，不得扩到全书。

**Commit:** `content: ch0 ch8 ch17 视觉优先试点改造`

---

## Task 9: 高断层章节波次

**Scope:** ch18、ch15、ch16、ch10、ch2。

- [ ] 每章先出 backlog，再生成资产。
- [x] 每章达到 spec 预算，最长无图段 ≤1500。（2026-11-08：19/19章密度实测通过，资产验收另计）
- [ ] 优先替代：长列表、连续定义、排故文字链、设计步骤和失效边界。
- [ ] 每章完成后单独跑视觉审计、链接、事实一致性和打印分镜。
- [ ] 每章单独提交，便于回滚。

**Commits:** `content: chN 视觉优先改造（图替繁文+动画V2）`

---

## Task 10: 其余章节全覆盖

**Scope:** ch1、ch3–ch7、ch9、ch11–ch14。

- [ ] 按每章预算补齐静态图和动画。
- [x] 确保每个 >800 字 H2 有视觉锚点。（2026-11-08：全19章审计为0缺口）
- [ ] 复用视觉图型但不复制内容构图；同一篇连续三图不得同布局。
- [ ] 每章字符数、视觉数和删改段落写进波次报告。
- [ ] 每章独立提交。

**Exit:** 19/19 章密度闸全绿。

**Progress 2026-11-08（ch14/ch15续作）:** 19/19章密度通过、444锚点、零堆图。ch14为23/22、最长1496；ch15为31/24、最长1487。新增15张静态图、技术重绘7张，均待审；章节密度达标不替代资产与知识保全验收。

---

## Task 11: 153 张旧动画逐张处置 + 扩到 220

**Files:**
- Modify: `docs/superpowers/visual/animation-v2-manifest.yml`
- Modify/Create: `assets/svg-v2/`
- Modify: `docs/p5-00-part5.md`
- Modify: 19 章动画入口

- [ ] 为 153 张旧动画逐张标记 Rebuild / Retire / Keep after review。
- [ ] Keep 必须重新过 35 分量规，不允许默认通过。
- [ ] 重复主题合并，正文入口指向最强版本。
- [ ] 新增不足的 A1–A5 类型，独立动画总数 ≥220。
- [ ] 每章至少 6 个高价值动画或动态演示；设计/排故章可用操作动画替代纯机理动画。
- [ ] 动画中心按章、类型、难度和失效边界重新筛选。
- [ ] 旧链接保留映射或明确重定向。

**Exit:** 220 是经过审查的动画，不是 220 个模板复制品。

**Commit:** `feat: 动画库 V2 全量重审与扩容`

---

## Task 12: 文字瘦身与图文职责审计

**Files:**
- Modify: 19 章 docs
- Create: `scripts/test_visual_text_replacement.py`

- [x] 每张标为 `replaces-text` 的图必须有被删段落记录与精炼导读。
- [x] 检测图注是否复制正文完整句子。
- [x] 检测同一公式是否在相邻正文、图注、字幕三次重复。（2026-11-07 落地：animation 资产解析 SVG 的 `g[data-caption]` 文字与 metadata 节拍 JSON，LaTeX 归一化后按操作数边界匹配（R2 不命中 R20）；字幕源缺失/越界/XML 坏损报错；同节正文∩图注∩字幕命中每公式警告一次。纯公式不算图注复制正文。夹具 6 项先红后绿，全套 17 项绿）
- [ ] 保留公式、量化判据、典型值/保证值区分和来源。
- [ ] 全书正文字符原则上下降 10%–20%，不能靠删知识点完成。
- [ ] 人工抽检每章首、中、尾三段，防止“前密后空”。

**Exit:** 图真正替代文字，而不是让书更厚。

**Progress 2026-11-07:** `scripts/test_visual_text_replacement.py` 已接入 `make visual-check`。它把每条 `replaces-text` 记录与其正文小节、figure 图注、实际非空白字符差逐项对齐；记录漂移即失败。图注整句复制正文、同一公式出现在图前正文/图注/图后正文时给出警告。动画字幕侧已接入：同节正文∩图注∩字幕三重命中按公式各警告一次，字幕源缺失/越界/坏损直接失败；公式三次重复项已勾。

**Progress 2026-11-08（字符口径根因修正）:** 发布闸原先拿 `chars`（章节原文非空白字符，含 alt、figcaption 与 `<img>` 标签语法）判「下降 10%」，实测只有 −4.3% 而红；但同一冻结 head 8961d38 对比下**正文已 −19.6%**（420,573 → 338,275），落在规格要求的 10%–20% 内。红的原因是口径不是作品：新增 232 张图带来 62,749 字符图注 chrome，把原文总量顶了上去。继续压原文到 −10% 需再删 25,704 字符，会把正文推到 −25.7%，超出规格区间并伤及知识点；削 alt 又会破坏无障碍与 `visible_number_gaps` 的数值来源（部分图内数字如今只存在于 alt）。故按根因修口径，不降下限、不改作品迎合：

- `audit_visual_density.py` 新增 `prose_chars()`（剥 `<figure>` 整块与独立 `<img>`）与 `audit()` 的 `prose_chars` 键；`chars` 口径一字未动。
- `capture_visual_baseline.py --enrich-prose` 从**同一冻结 head** 补录 19 章 `prose_chars` 与 `meta.prose_convention`/`prose_provenance`；已逐项断言原有 `chars`/`visuals`/`gaps`/`assets`/`inventory`/`meta` 值与 HEAD 完全相同。
- `check_visual_release.py` 拆出 `character_reduction()`/`reduction_errors()`，改判正文、原文量仍以 `raw_character_reduction` 如实报告。判闸用整数交叉相乘——`1 - 900/1000` 浮点是 `0.0999…`，正好压到 10% 会被误判为失败。
- 证据：9 项新测试先红（含真实误报 `reduction: -100.0% < 10%`）后绿；`test_convention_reproduces_frozen_baseline` 在冻结 head 上逐位复现新键；4 个变异（原文量冒充正文／图注算进正文／下限归零／冻结基线正文数 +1）全部被抓，未改坏时全绿。发布闸 329 → 328 项，剩下的全是 Task 11 旧动画处置与验收。
- 仍未勾的原因：「不能靠删知识点」还依赖 ch13 的 12 项 `check_prose_safety` 失败（在制 worker 资产）与下一行人工抽检。

**Progress 2026-11-08（首中尾人工抽检，15/19 章）:** 对已提交的 15 章（ch0–ch12、ch17、ch18）逐章抽检首、中、尾三段，方法＝密度普查（`audit_visual_density.py --json` 的 `gap_spans` 按文件行号前/中/后三等分定位）＋人工通读章首场景、章尾出处与最长无图段所在小节。结论：**未发现「前密后空」、悬代词、论题漂移或知识点误删**。

- 章首全部具体情景先行（电机一停 MOSFET 先坏／两板输出顶牛／跟随器变三角波／7805 带载掉压／半夜停线「不工作」等），符合「先让人看懂」；章尾全部保留标准 apparatus（厂商 datasheet 权威源＋「示意/典型/保证」区分＋通关打卡），无一段被掏空。
- 最长无图段逐一通读判定为高价值正文，非冗余：ch9 §9.2（1500，TL431 阴极电流/动态阻抗/串联扩流 72.7Ω 算例，典型 0.4mA 与保证 1mA 分开）、ch10 §10.5（1492，RESET 0.47s/11.9/28.3/40.9ms 时序设计＋实验验收步骤）、ch4 §4.5/4.6（1470/1420，热模型/并联均流/换管七条清单＋开通四拍 20.5µJ 算例）、ch17 §17.2（1481，八行症状速查表＋−10→−2.1→47kΩ 错料教学例）、ch11 §11.11（1286，标称模型与实物保证分开＋可复算附录）。
- 后三分之一警告段最多的 ch3（前/中/后＝1/1/4：§3.7 热失控降额账与 ΔT 判据、§3.8 故障速查表、§3.9 动态分析）与 ch7（0/1/2：§7.4 五坑测量判据＋大电容负载算例、§7.5 毛刺四拍）通读后判定为合法worked-example/速查表密度，图已覆盖核心概念，不强改迎合闸。ch6/ch12 全书无警告段（最长 1198/1105）。
- 量化闸佐证：15 章最长无图段均 ≤1500、堆图 0、H2 无图 0。本轮另完成 ch8 §8.3 电荷注入图替繁文（提交 `3a8b337`，正文 −84 字符，记录 `reviews/insertion-ch08/text-replacements.yml`，图文职责审计 17/17 绿、0 警告）。
- 人工抽检行仍未勾的原因：「每章」含 ch13–ch16，四章为在制 worker 资产（243 个未提交文件，ch13 另有 12 项 prose-safety 失败），待该车道落地后补抽检方可勾全书。

**Commit:** `edit: 全书图替繁文与重复说明瘦身`

---

## Task 13: 印刷、离线与 PDF

**Files:**
- Modify: `analog-book/book/storyboard.py`
- Modify: `analog-book/styles/print.css`
- Modify: `analog-book/tests/test_storyboard.py`
- Create: `scripts/test_print_storyboard_v2.py`

- [ ] V2 动画自动出 3–5 格关键帧分镜。
- [ ] 静态图在 16K 有效版心内文字 ≥8.5pt。
- [ ] 长图避免整图缩小；必要时拆上下半页。
- [ ] A4、16K 双卷重建；每卷 ≤700 页。
- [ ] 灰度打印仍能区分正常/异常、输入/输出、前/后状态。
- [ ] 随机抽 50 张图检查断页、裁切、字号和图注对应。
- [ ] 生成最终本地 PDF，保存路径和 SHA-256。

**Exit:** PDF 人工翻阅签字，不以“构建成功”代替质量确认。

**Commit:** `build: 视觉 V2 印刷分镜与 PDF 适配`

---

## Task 14: 视频与社媒同源派生

**Files:**
- Modify: `video/shots/*.json`
- Modify: `video/remotion/src/`
- Modify: 社媒模板与样例

- [ ] 视频主视觉引用 accepted 的 V2 资产，不再单独设计另一套图。
- [ ] 章节动画节拍可转换为视频分镜，但视频允许重新剪辑时长。
- [ ] 社媒卡只抽取教材结论，不新增数字。
- [ ] handraw-style 的风格/layout/color 记录沿用教材 manifest。
- [ ] 现有 40 个成片先作为旧基线；视觉改造完成后再决定重渲范围。

**Exit:** 教材、动画、视频和社媒看起来属于同一个产品。

**Commit:** `feat: 视觉 V2 五线同源派生`

---

## Task 15: 全量质量门禁与发布

**Files:**
- Modify: `Makefile`
- Modify: `.github/workflows/tests.yml`
- Modify: `.github/workflows/book.yml`
- Modify: `docs/superpowers/checklists/ship-gate.md`

- [ ] `make visual-ship` 聚合密度、manifest、事实、动画、播放器、印刷和人工评分闸。
- [ ] 19/19 章最长无图段 ≤1500。
- [ ] 视觉锚点 ≥390；动画 ≥220。
- [ ] 153 张旧动画处置率 100%。
- [ ] 静态图/动画无缺 prompt、无缺来源、无缺 print fallback。
- [ ] 跑站点静态/浏览器测试、书测试、PDF 结构、Remotion 冒烟。
- [ ] 生成 A4 与 16K 本地 PDF，人工确认。
- [ ] 用户确认三章试片和最终 PDF。
- [ ] 清理临时文件，只暂存 manifest 允许的产物。
- [ ] 分任务提交；最后经用户明确授权再 push。
- [ ] 监控 GitHub Actions 至 tests、links、book、book-print、pages 全绿。

**Final commit:** `release: 视觉优先彻底改造完成`

---

## Recommended Execution Order

```text
Task 0–3  基线、工具锁、审计、manifest
    ↓
Task 4    三章风格试片
    ↓ 用户确认
Task 5–7  静态管线、动画 V2、播放器
    ↓
Task 8    ch0/ch8/ch17 完整试点
    ↓ 用户确认
Task 9–10 全书波次
    ↓
Task 11–12 动画全审 + 文字瘦身
    ↓
Task 13–14 印刷与五线派生
    ↓
Task 15   全闸、PDF、提交、推送、CI
```

---

## Plan Review Checklist

- [x] 量化了“图少”和“分布差”，没有只写审美口号
- [x] 同时覆盖静态图数量、动画数量和两者质量
- [x] 153 张旧动画全部进入逐张处置，不默认保留
- [x] handraw-style 有版本锁、ID、prompt 和参考图隔离规则
- [x] 公式、电路、中文不交给生图模型猜
- [x] 先三章试片、两次用户确认，再批量生产
- [x] 图替繁文，禁止只加图不减文
- [x] 网页、无障碍、打印、PDF、视频和社媒全部纳入
- [x] 最终提交推送仍需用户明确授权

---

*计划到此为止；未 Accepted 前不执行批量视觉生产。*
