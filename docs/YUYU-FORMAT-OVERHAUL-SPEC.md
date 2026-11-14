# 《从模拟电路到 BMS》yuyu 合集格式改造 SPEC（2026-11-13）

> 参考系：`D:\Users\claude` 的 yuyu 合集格式（currentColor 线描章徽/篇题/封面层 + 六要素章节结构 + 契约化门禁）。
> 目标仓：`D:\Users\BMS-Z`（两卷：《通往模拟电路之路》= 卷 I analog-book；《BMS 实战：从一颗电芯到一套证据链》= 卷 II bms-book）。
> 方式：主代理规划与验收，子代理分片施工；先 SPEC 后实现；执行期不 commit/push。

## 0. 目标 / 非目标

### 0.1 目标（插图 + 文字）
1. **插图**：卷 II 补齐 yuyu 式插画层——38 枚章徽（currentColor 线描 SVG，章首展示）+ 9 枚篇题（篇首插画，接入 part-divider）+ 与卷 I 统一的视觉语言；卷 I 对拍核查（章徽/篇题/封面契约与接线），缺则补。
2. **文字**：两卷 57 章跑「yuyu 六要素 × BMS-Z 既有契约」适配审计，差距分片补齐（开场场景/原理+图/可跑实验/翻车对照/同构点/版本核对，按各卷 STYLE 口径映射）。
3. **门禁**：插画契约校验 + 结构审计脚本化，接入 local-gates 与 CI，全量复跑绿。

### 0.2 非目标
1. 不移植 yuyu 构建器（yuyu_book 包不进本仓）；不照搬其登记表体系（本仓已有 glossary/index_terms/chapter_guides/curriculum 对应物）。
2. 不动卷 II 的 handdraw AI 位图管线（manifest 门保持原样；矢量章徽层与其并存，如同 yuyu omp 的 jpg+SVG 双轨）。
3. 不改 kp-backlink 生成块、concepts.json、curriculum 生成物。
4. 不动 de-AI 残留 20 处（callout 标签/表头/表题/事实性「真正」，结构性保留）。
5. 不动 index.md v3.* 日志段、p9-12-changelog.md、p9-14-credits.md 历史段。
6. 不做英文版；不扩充handdraw PNG 数量（另有管线与预算）。

## 1. 现状快照（2026-11-13 实测）

### 1.1 卷 I（analog/analog-book/，19 章 + 5 篇 + 附录 A–G）
- 章源：`analog/docs/p*-*.md`（精修与记录审计都读这里；`analog/build/docs/` 是站点侧生成分叉副本，不是源）。
- **插画层已完备**：`static/illustrations/` 有 ch00–ch18.svg（19 枚章徽）、part-i–v.svg（5 枚篇题）、`static/cover-art.svg`（封面）。
- 契约：`book/illustrations.py`——篇题 SAFE_NAME_RE `^part-(i|ii|iii|iv|v)\.svg$`，禁 script/style/image/foreignObject/iframe/object/embed/xlink:/data:/@import/href/url()（白名单 w3.org）/事件属性/CJK；assemble.py:531 消费 opener_art，缺文件即 BookError。
- manifest.json：schema 2，front_matter + parts I–V（units→chapters）+ appendices A–G + back_matter；cover 段为印刷参数（bleed/crop/spine/back_cover 文案），无封面图引用（封面图由 static/cover-art.svg 承担）。

### 1.2 卷 II（bms-book/，38 章 + 9 篇）
- 章源：`bms-book/book/*.md`（38 个：p0 导读 1 + p1 5 + p2 4 + p3 8 + p4 4 + p5 5 + p6 4 + p7 2 + p8 附录 5）。
- 构建：build_html.py / build_epub.py / build_print_book.py / check.py；manifest.json（parts→files + part_goals + chapter_guides×32 + index_terms）。
- **封面已有**：build_html.py:969 内嵌 base64 手绘 SVG（cover_src，剖开电芯搬运离子场景）。
- **插画缺口**：无章徽层（章首无徽章机制）、无篇首插画（part-divider 仅 data-part 配色 CSS，build_html.py:363-369）；技术 SVG 图在 assets/（按章编号），handdraw AI 位图在 illustrations/handdraw/（有 manifest 门 tools/check_handraw_manifest.py + tests/test_handraw_manifest.py）。

### 1.3 共享层
- 顶层 book/：两卷 orchestrator（manifest.json volumes I/II，单文件 HTML + EPUB + PDF，卷 I 上限 700 页）。
- 门禁：.github/scripts/check_docs.py（6208 链接 + 草图契约 generate/render_course_sketches --check）、scripts/local-gates.{sh,ps1}、book/tests + analog-book/tests + bms-book/tests（pytest 16+）、glossary_lint.py、tools/gen_curriculum_pages.py --check（80 概念 kp-backlink 零漂移）。
- de-AI 已两轮（1306a1c + 64f744e）：残留 20 处全部结构性保留。

## 2. 缺口清单（K 编号）
- **K1 卷 II 无章徽层**：38 章章首无 yuyu 式徽章；build_html.py 无 emblem 装载与展示挂点。← 本轮主战场
- **K2 卷 II 无篇题层**：9 个 part-divider 无篇首插画机制与文件。
- **K3 卷 I 未对拍**：章徽/篇题/封面文件齐备，但未按 yuyu 契约（viewBox/currentColor/字节上限/aria 标注）核查过；章徽在章首页的展示接线待确认（grep 未见 frontmatter 消费 ch*.svg，需追 assemble/content 链路）。
- **K4 六要素未审计**：两卷 57 章未跑过结构审计；BMS-Z 既有契约（analog STYLE.md/SPEC-V4.md、bms chapter_guides/part_goals）与 yuyu 六要素的映射未建立。
- **K5 门禁缺口**：插画契约校验（若有）未覆盖章徽层（卷 I illustrations.py 只校验篇题）；结构审计脚本不存在。

## 3. Global Constraints（硬红线）
1. **生成物不改**：kp-backlink 块内部（含 concepts.json 引文）、curriculum/、dist/、site/ 一律不手改。
2. **结构行不动**：标题行/锚点、`:::` 围栏、`<figure>/<figcaption>`/图号/表号、代码块、行内码、`$…$`、链接 URL/text、callout 标签行、表格单元格。
3. **SVG 契约（两卷统一）**：单根 `<svg>` 带 viewBox；线条/填充只用 currentColor；禁 `id=`/`href=`/`url(`/`<style>`/`<script>`/`<iframe>`/`<image>`/`xlink:`/`data:`/`@import`/事件属性；章徽 ≤6KB、篇题 ≤6KB（卷 I 篇题已有更严黑名单，从其约定）；不加 role/aria-label（包装层统一处理）；纯几何线描不用 `<text>`。
4. **视觉统一**：卷 II 章徽/篇题必须读卷 I `static/illustrations/ch00.svg`、`part-i.svg` 校准线宽/留白/圆角，两卷同一视觉语言（同一部作品）。
5. **不回归**：两卷现有全部门禁（check_docs、pytest、glossary lint、gen_curriculum_pages --check、build.py check、handraw manifest、local-gates）保持绿；卷 I 单文件 HTML 已 83% 体积上限，新增内联 SVG 计入体积预算。
6. **子代理纪律**：只改分派文件；禁跑 build/test/lint/git；禁碰 .tmp-*/.local 历史目录；拿不准不改、记 Deferred。
7. **执行期不 commit/push**；每里程碑留「命令 + Expected + 实测」证据。

## 4. 里程碑总表

| 里程碑 | 内容 | 分工 | 本地验收 |
|--------|------|------|---------|
| **M0 基线冻结** | 落盘现状清单；追清卷 I 章徽展示接线（ch*.svg 谁在消费）；确认卷 II 章首/part-divider 模板挂点；跑全门禁记录基线 | 主代理 | docs/yuyu-overhaul/baseline.md |
| **M1 卷 II 章徽层** | 38 枚章徽 SVG（bms-book/assets/emblems/ 或 static/illustrations/，按既有结构）；build_html.py 装载+章首展示；契约校验函数+测试 | 插画 worker ×3（按篇分片）+ 工具 worker（接线） | 校验脚本 0 违例；卷 II HTML 构建绿且章首见徽 |
| **M2 卷 II 篇题层** | 9 枚篇题 SVG；part-divider 插画接线 | 插画 worker ×1 + 工具 worker | 篇首插画在 HTML 可见；校验绿 |
| **M3 卷 I 对拍补缺** | 19 章徽+5 篇题+封面按统一契约核查；缺/违规则补；确认章徽展示接线 | 1 worker + 主代理复核 | 卷 I 构建绿；契约核查 0 违例 |
| **M4 六要素审计与补齐** | 适配审计脚本（yuyu 六要素 × STYLE/SPEC-V4/chapter_guides 映射）→ 两卷差距报告 → 子代理分片补要素（增量补丁，不动红线行） | 工具 worker + 文字 worker ×4（按卷分片） | 审计 PASS；抽查 10% 技术句无歧义 |
| **M5 门禁接入** | check_emblems 契约校验 + 结构审计接入 local-gates 与 CI workflow | 工具 worker | local-gates 全绿输出 |
| **M6 总验收** | 两卷 HTML/EPUB/PDF 重建 + 全量门禁复跑 + 前后对比报告 | 主代理 | 报告落盘 docs/yuyu-overhaul/acceptance.md |

依赖：M0 → M1/M2（可并行）→ M3 → M4 → M5 → M6。M4 文字补要素与 M1–M3 插画不同文件，但为避免同章冲突仍排在插画后。

## 5. 插画执行细则
1. **卷 II 章徽 38 枚**：文件名按章序号（对齐 assets/ 现有编号习惯，如 `01-electrochemical-evidence-chain.svg` 风格，但章徽独立目录）；意象取该章「读完能干什么」的交付物（如 07-保护tick48 →  tick 守卫/看门狗，12 → 锚点/资格印章），不画抽象装饰；每枚 ≤6KB。
2. **卷 II 篇题 9 枚**：p0 导读 + p1–p7 + p8 附录；意象取该篇 part_goals 关键词；≤6KB。
3. **接线方式**：build_html.py 增加 emblem/part-art 装载（仿卷 I illustrations.py 的校验：SAFE_NAME + token 黑名单），章首模板与 part-divider 模板插入 `<img>`/内联 SVG；alt 用章题（手绘插画：…风格描述参照现有 cover alt 口径）。
4. **风格校准**：所有 worker 先读卷 I ch00.svg/ch07.svg + part-i.svg 三份样张再动笔。
5. **卷 I 对拍**：按第 3 节契约逐文件核查；违规文件重画（保持原意象）；确认 assemble/content 链路中章徽的展示点（M0 追清后在此更新）。

## 6. 文字执行细则（M4）
1. **六要素适配映射**（按卷裁剪，e5 为跨卷同构点）：
   - e1 开场具体场景/失败现场（H1 后首个 H2 前，≤2 段，首段 >40 字）
   - e2 原理讲解配 ≥1 图（技术 SVG/手绘/仿真记录任一）
   - e3 最小可跟做实验（真实命令/仿真步骤 + 成功判据文字）
   - e4 翻车/对照/误区小节含真表格
   - e5 与另一卷的同构点短段（卷 I↔卷 II 互链，格式「参见卷 II 第 M 章」式）
   - e6 章末版本/环境核对或参考资料清单
2. **审计脚本**：tools/audit_structure.py --volume I|II [--check]，输出逐章六要素矩阵 + 缺失统计；判据正则参照 omp audit_structure.py 但适配本仓术语（翻车/对照/误区/排障/踩坑等）。
3. **补齐纪律**：增量补丁不推倒；单段变化 ≤30%；不灌水；不动第 3 节红线行；每章改动 worker 交付「旧→新」对照。
4. **de-AI**：残留 20 处不动；新增补写文字不得引入 21 类模板腔（普查脚本复用 .local/polish-tools/）。

## 7. 风险与回滚
| 风险 | 缓解 |
|------|------|
| 卷 II build_html.py 接线改坏现有构建 | 工具 worker 先出挂点分析报告再动手；接线后立刻跑卷 II 构建 + tests |
| 章徽风格与卷 I 不统一 | 强制三份样张校准 + 主代理逐枚目检 |
| 内联 SVG 增大 HTML 体积（卷 I 已 83%） | 章徽走 `<img src=data:>` 内联计入预算，M6 核验体积；卷 II 无此约束 |
| 六要素补齐引入技术歧义 | 旧→新对照表 + 主代理 10% 抽验 |
| worker 误改生成块/红线行 | 分片说明红线；验收跑 verify_polish + 结构行一致对拍 |

## 8. 待确认（用户裁决后开工）
1. 卷 II 章徽 38 枚全做（推荐）还是只做 p1–p7 正文 33 章？
2. 篇题 9 枚含 p0 导读与 p8 附录（推荐全做）还是只做 p1–p7？
3. 六要素审计范围：两卷 57 章全审全补（推荐）还是先出差距报告再定？
4. 卷 I 对拍：核查+补缺（推荐）还是完全不动卷 I？
