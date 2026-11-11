# 把《通往模拟电路之路》并入 BMS-Z，合成《从模拟电路到 BMS》设计

状态：定稿待评审  
日期：2026-11-11  
决策人：项目所有者  
执行仓库：`zhuguang-ZFG/BMS-Z`

---

## 0. 一句话定义

在 BMS-Z 仓库里，把模拟电路书与 BMS 书合成一本两卷的《从模拟电路到 BMS》：一份内容源，站点由 VitePress 全量承载，成书由统一装配层产出单文件 HTML、A4/16K PDF 与 EPUB。

## 1. 背景与现状

| 维度 | 模拟电路书 | BMS 书 |
|---|---|---|
| 仓库 | `zhuguang-ZFG/analog-circuit-roadmap` | `zhuguang-ZFG/BMS-Z` |
| 当前分支 | `fix/legacy-rebuild-batch2`（工作区干净） | `feat/w4-publication-epub`（有未提交改动） |
| 跟踪文件 | 5,203 | 1,597 |
| 正文 | 63 页书页，19 章（第 0–18 章），71 万字符 | 38 个书文件（前言 + 32 章 + 附录 A–E），9,424 行 |
| 站点 | MkDocs Material，由 `scripts/build_site.py` 生成 | VitePress 1.6.4，`docs/.vitepress/` |
| 成书 | 单文件 HTML、A4 PDF（400+ 页）、16K 两卷（448 + 508 页）、EPUB | 单文件 HTML、PDF（380 页、512 书签）、EPUB |
| 动画 | 153 张 SVG（含 SMIL） | 177 张（SVG/WebP） |
| 许可 | 文档与自制动画 CC BY-SA 4.0 | 正文 CC BY-SA 4.0，代码 MIT |
| 构建依赖 | Python + Playwright/PyMuPDF + MkDocs | Node ≥24 + VitePress + Python 构建器 |

兼容性实测（仅书页 `docs/p*.md`）：

- `{{` 与 `<script>`：0 处；
- 内联 `<svg>`：1 页；
- `data-calc` 计算器：11 页；
- 自定义 `<a id>` 锚点：50 页；
- `$$` 数学：16 页（BMS 站已有同款 `markdown-it-mathjax3`）。

结论：卷 I 迁移到 VitePress 的主要成本是适配层（锚点、计算器、资源路径、画廊），不是重写正文。

## 2. 目标与非目标

### 2.1 目标

1. 一个仓库、一本书：书名《从模拟电路到 BMS》，卷一《通往模拟电路之路》，卷二《BMS 实战：从一颗电芯到一套证据链》。
2. 一条构建入口：`python book/build.py all` 产出站点、HTML、PDF、EPUB，并跑完整审计。
3. 一套站点：一个域名、一套导航、一套本地搜索，卷 I 63 页全部可达且交互不倒退。
4. 卷内编号保留：卷 I 第 0–18 章，卷 II 第 1–32 章 + 附录；跨卷引用统一为「见卷 X·第 N 章」并由审计拦截悬空引用。
5. 内容治理：共享前言、共享术语表、重叠主题加显式互引；本阶段不删除、不改写正文。
6. 旧仓库归档，README 指向新家；旧站主要入口提供可达的重定向页。

### 2.2 非目标

- 不重写两书正文，不做文风统一、不重排章节顺序。
- 不改 BMS 现有站点路由（`/book/`、`/course/` 等保持原地址）。
- 不把卷 I 重编号为 1–19（已决策沿用 0–18）。
- 不迁移视频工程、社交发布脚本之外的媒体成品；`media/` 仍不入库。
- 不引入 Git LFS，不新建独立域名。
- 不物理删除旧仓库，只归档与重定向。

## 3. 决策记录

| 决策 | 结论 |
|---|---|
| 合并方式 | 真正合并成一个仓库、一本书 |
| 主仓库 | BMS-Z |
| 章节编号 | 分卷编号；卷 I 保留 0–18，卷 II 保留 1–32 |
| 迁移范围 | 模拟电路整仓迁入（docs、assets、analog-book、scripts、tests、CI） |
| 书名 | 《从模拟电路到 BMS》，两卷保留原名作副题 |
| 介质 | 在线阅读站点、单文件 HTML、A4/16K PDF、EPUB |
| 站点技术路线 | 路线 B：VitePress 全量承载卷 I |
| 成书技术路线 | 保留装配层出 PDF/EPUB；VitePress 只负责站点，不承担打印 |

## 4. 总体架构：一份源，两个渲染器

```
内容源                              渲染器                              产物
analog/docs/*.md      ──┬──> VitePress + 站点适配层      ──> 在线阅读站点（统一导航/搜索）
bms-book/book/*.md    ──┤
docs/course/*.md      ──┘
                      └──> book/ 装配层（manifest 驱动） ──> 单文件 HTML / PDF / EPUB
```

原则：

- 内容源只有一份，站点镜像目录是构建产物（gitignore），禁止手工编辑。
- 站点与成书共享同一份页序（总书 manifest），避免目录漂移。
- 审计在渲染之后执行，不信任任一渲染器的默认行为。

## 5. 目标仓库结构

```
BMS-Z/
├── analog/                         # git subtree 整仓迁入，保留历史
│   ├── docs/                       # 卷 I 唯一内容源（63 页）
│   ├── assets/                     # 动画、图、照片、icons
│   ├── analog-book/                # 原成书管线，P2 起并入 book/
│   ├── scripts/  tests/            # 原样，根路径指向 analog/
│   └── build/                      # 原站点构建中间产物，迁入后 gitignore
├── bms-book/                       # 卷 II 内容源，保持原位
│   ├── book/*.md
│   ├── manifest.json
│   ├── build_html.py  build_epub.py  check.py  check_pdf.py
│   └── dist/                       # gitignore
├── docs/                           # VitePress 站点
│   ├── .vitepress/                 # 新增 prepare-volume-1.mjs 与统一导航/搜索
│   ├── volume-1/                   # 构建期生成，gitignore
│   ├── public/volume-1-assets/     # 构建期复制，gitignore
│   ├── book/  course/ ...          # 现状
├── book/                           # 新增：总书与统一成书
│   ├── manifest.json               # 总书 manifest（schema 3）
│   ├── manifests/                  # 卷级 manifest（迁入/转换）
│   ├── build.py                    # 唯一入口
│   ├── assemble.py  epub.py  pdf.py
│   ├── glossary.md  terminology.json
│   ├── styles/  fonts/  static/  cover/
│   ├── dist/                       # gitignore
│   └── tests/
├── code/  challenges/  curriculum/  tools/  scripts/   # 原样
└── .github/workflows/              # 合并后的四条工作流
```

卷 II 不搬家：课程、代码、挑战、测试均以 `bms-book/` 和 `docs/` 为基准，搬家只增加断链风险。

## 6. 总书 manifest（schema 3）

`book/manifest.json`：

```json
{
  "schema": 3,
  "title": "从模拟电路到 BMS",
  "subtitle": "一条从器件原理走到电池管理系统的硬件自学路线",
  "author": "zhuguang-ZFG 与贡献者",
  "license": {"docs": "CC BY-SA 4.0", "code": "MIT"},
  "language": "zh-CN",
  "shared_front_matter": ["book/front/00-总前言.md", "book/front/01-怎样读这本书.md", "book/front/02-符号与单位.md", "book/front/03-排版与术语约定.md"],
  "volumes": [
    {
      "id": "I",
      "title": "通往模拟电路之路",
      "subtitle": "从欧姆定律到芯片内部结构",
      "manifest": "analog/analog-book/manifest.json",
      "print": {"trim_mm": [185, 260], "max_pages_per_volume": 700}
    },
    {
      "id": "II",
      "title": "BMS 实战：从一颗电芯到一套证据链",
      "subtitle": "把“为什么”讲到能复现，把“谁签字”写进流程",
      "manifest": "bms-book/manifest.json",
      "print": {"trim_mm": [185, 260], "max_pages_per_volume": 700}
    }
  ]
}
```

卷级 manifest 统一到 schema 2 的字段集，并把 BMS 专有契约升级为可选字段，一项不丢：

- `chapter_guides`：每章「本章要回答 / 读完应交出 / 这一章不证明」；
- `sources` / `book_sources` / `chapter_sources`：来源锚点与访问日期；
- `index_terms`：索引术语清单；
- `part_goals`：篇目标；
- `front_matter` / `parts`：页序与篇结构。

转换器 `book/manifests/convert_bms.py` 负责 `bms-book/manifest.json` → schema 3 卷级格式，并在构建前校验：章节罗盘全覆盖、来源锚点无孤儿、索引术语无空项。

## 7. 构建管线

### 7.1 唯一入口

```bash
python book/build.py site                 # 卷 I 适配 + VitePress 构建 + 站点审计
python book/build.py html --volume I|II|all
python book/build.py pdf --format a4|16k --volume I|II|all
python book/build.py epub --volume I|II|all
python book/build.py check                # 只审计已有产物
python book/build.py all                  # 全链路 + 全审计
```

约束：

- 构建全程不联网；第三方资产先本地化并登记来源。
- `--no-build` 复用已有站点/中间产物；其余情况从源重新装配。
- 产物与报告记录源提交哈希，便于对账与回滚。

### 7.2 产物布局

```
book/dist/
├── site/                          # VitePress 产物（部署用）
├── volume-1/
│   ├── book.html
│   ├── book-a4.pdf
│   ├── book-16k-1.pdf  book-16k-2.pdf
│   └── book.epub
├── volume-2/
│   ├── book.html
│   ├── book-a4.pdf
│   ├── book-16k-1.pdf
│   └── book.epub
└── build-report.json              # 源提交、页数、体积、哈希、审计结果
```

16K 分册按 700 页硬上限自动切分：卷 I 两册（约 448+508 页），卷 II 一册（约 380 页），共 3 本物理书。分册沿用现有「重新装配而非截断」逻辑，跨册锚点降级为「见上/下册」。

### 7.3 总审计闸

合并两边现有检查，缺一不可：

| 闸 | 来源 | 拦截对象 |
|---|---|---|
| 远程资源 | analog-book | 远程图片、外链样式/脚本、iframe/video |
| 重复 ID 与锚点 | analog-book + BMS | 重复锚点、悬空锚点、跨卷降级失败 |
| 页数与体积 | analog-book + BMS | 单册 >700 页；单文件 HTML 超卷级上限（卷 I 24 MB、卷 II 32 MB） |
| 章节罗盘 | BMS | 编号章缺「本章要回答/读完应交出/这一章不证明」 |
| 来源锚点 | BMS | 未登记来源、孤儿来源、未知来源引用 |
| 索引术语 | BMS | 空项、重复项、无法定位 |
| PDF 书签 | BMS | 书签数与章数/锚点数不符 |
| EPUB spine | BMS | 缺页、乱序、资源缺失 |
| 站点死链 | 新增 | 站内 404、跨卷引用悬空 |

### 7.4 CI 工作流（四条，按路径分派）

| 工作流 | 触发路径 | 内容 |
|---|---|---|
| `book.yml` | `analog/**`、`bms-book/**`、`book/**`、`docs/**` | 站点 + 四类介质 + 总审计，上传 artifact |
| `book-print.yml` | 同上 | 16K 分册构建与 artifact 上传，`/book/` 只发布 A4/HTML |
| `tests.yml` | 代码与内容变更 | 两库单测 + 内容闸 + 站点适配层测试 |
| `links.yml` | 定时 + PR | 外链巡检，沿用现有排除清单 |

路径过滤必须保证：只改卷 I 时也跑站点与成书，只改卷 II 时同理；两边都改时全量跑。

## 8. 站点：VitePress 全量承载

### 8.1 站点适配层

新增 `docs/.vitepress/prepare-volume-1.mjs`，构建前执行，产物 gitignore：

1. 页序读取：以 `book/manifest.json` → 卷 I manifest 为唯一顺序源。
2. 页面镜像：`analog/docs/p*.md` → `docs/volume-1/*.md`，保留原文件名与锚点。
3. 资源重写：`assets/...` → `/volume-1-assets/...`；只复制被引用的动画、图、照片与字体，输出到 `docs/public/volume-1-assets/`。
4. 锚点保留：`<a id="ch0">` 等原样保留；标题 slug 与锚点冲突由构建期检查。
5. 计算器：11 页的 `.calc[data-calc]` 容器保留，计算逻辑移植为独立 ES 模块，经主题 `enhanceApp` 全局注册；不依赖 MkDocs 的脚本注入。
6. 数学：沿用 `markdown-it-mathjax3`，与卷 II 同配置。
7. 画廊：由动画索引生成 `/volume-1/gallery`，筛选与搜索沿用现有实现思路。
8. 导航：侧栏按卷/篇/章生成；顶部导航为「首页 / 卷一 / 卷二 / 课程 / 资源」。
9. 搜索：VitePress 本地搜索索引必须包含 `docs/volume-1/**`，构建后抽查关键术语命中。

### 8.2 路由与兼容

- 卷 I 新路由统一为 `/volume-1/<原文件名去扩展名>`，锚点保持 `#ch0` 等原值。
- 卷 II 路由不变：`/book/`、`/course/`、`/stages/` 等。
- 旧 MkDocs 站点地址（`zhuguang-zfg.github.io/analog-circuit-roadmap/`）无法做 301：P5 在旧仓库保留一个只含重定向页的 Pages 站点，指向新站 `/volume-1/`，并在 README 与下载页注明 canonical 地址。
- 站内跨卷链接渲染为带「卷二」/「卷一」前缀的真实链接；印刷版降级为纯文本引用。

### 8.3 阅读体验 parity 清单（63 页逐页过）

每页检查：可达、锚点可跳、图片/动画可见、公式渲染、计算器可用（11 页）、代码高亮、表格、深浅色、移动端、页内导航、搜索命中。任一不达标即阻断 P3。

## 9. 编号、锚点与跨卷引用

- 卷 I：第 0–18 章；卷 II：第 1–32 章 + 附录 A–E。
- 目录展示：书名下分「卷一 第 0–18 章」「卷二 第 1–32 章」两段，不做全书连续编号。
- 跨卷引用格式：印刷版与单文件 HTML 统一为「见卷二·第 6 章《AFE 怎样轮流看十几节电芯》」；站点版为可点击链接。
- 引用源仍是普通相对链接，由装配层/适配层解析目标归属；禁止手写「见卷 X」硬编码，避免页序调整后失真。
- 审计：跨卷目标必须能解析到唯一章/节；同一卷内锚点必须存在；任何解析失败阻断构建。

## 10. 术语表与去重治理

### 10.1 共享术语表

- 源文件 `book/glossary.md`，条目字段：术语、英文、定义、所属卷、相关条目。
- 以 BMS 附录 C 为主干，并入模拟电路术语表（`analog/docs/p8-10-s8-10.md`）。
- 每卷印刷版渲染完整表（分册自足），站点版提供合并检索；条目互链。
- 术语 lint：`book/terminology.json` 登记首选词与禁用变体（如「基准/参考」「采样/测量」「均衡/平衡」），只拦截新增歧义，不做全量改写。

### 10.2 重叠主题处理

| 卷 I | 卷 II | 处理 |
|---|---|---|
| 第 9 章 基准与稳压 | 第 5 章 测量链、第 6 章 AFE | 卷 I 讲原理；卷 II 加「先读卷一·第 9 章」框，只讲 BMS 增量 |
| 第 15 章 PCB 注意事项 | 阶段 3 主线：PCB 调试与验收 | 卷 I 讲布局与地；卷 II 讲调试流程与验收证据 |
| 第 16–17 章 排故五步法与速查 | 第 8 章 硬件失效与二次保护、第 25 章 功能安全 | 卷 I 讲方法；卷 II 讲失效链与安全证据 |
| 第 6、12 章 运放与电路族 | 第 5–6 章 采样与 AFE | 卷 I 讲器件与拓扑；卷 II 讲共模、校准与误差预算 |

第一阶段只加互引框与术语表，不删除、不改写正文；后续是否合并内容另立项目。

## 11. 迁移阶段与验收闸

### P0 准备（0.5 天）

- BMS-Z 未提交改动先提交或走 PR 合并；从 `main` 拉 `merge/analog-into-bms` 分支。
- 两库打冻结标签：`pre-merge-analog-2026-11-11`；记录两库当前提交。
- 验收：两库工作区干净；两边基线测试全绿。

### P1 迁仓（1 天）

- `git subtree add --prefix=analog <本地 analog 仓库> <当前分支>`，保留历史。
- 迁入 CI（book、book-print、tests、links），改路径与缓存键；Pages 暂由 BMS 现有工作流承担，P5 统一。
- 修 `analog/scripts`、`analog/analog-book` 的相对根路径；保持 `cd analog && pytest` 可跑。
- 根 README、许可证与署名合并。
- 验收：`analog/` 内测试与成书构建全绿；BMS 原测试全绿；仓库体积增量符合预期。

### P2 成书管线（3–5 天）

- 实现 schema 3、总 manifest、BMS manifest 转换器、共享装配器。
- `book/build.py` 五个子命令；产物布局与构建报告；总审计闸。
- 保留两边旧构建器作对照，直到 parity 通过。
- 验收：四类介质全部产出；页数、章数、图数、链接数、书签数与旧产物逐项对账；16K 三册均 ≤700 页；单文件 HTML 不超卷级上限（卷 I 24 MB、卷 II 32 MB）。

### P3 站点（3–5 天）

- 实现 `prepare-volume-1.mjs`、计算器模块、画廊、导航、搜索、重定向页。
- 部署 preview；执行 63 页 parity 清单。
- MkDocs 构建保留为旁路开关，P5 前不删除。
- 验收：63/63 页可达；0 死链；11/11 计算器可用；公式、动画、锚点、深浅色、移动端全部通过；搜索命中卷 I 关键术语。

### P4 内容治理（2–3 天）

- 共享卷首、跨卷互引、术语表合并、去重标注、书名与封面、README/下载页。
- 验收：跨卷引用审计 0 错误；术语表无重复、无悬空；术语 lint 通过；目录与页序和 manifest 一致。

### P5 发布（1 天）

- 单流水线部署新站；更新下载页（HTML/PDF/EPUB）；旧仓库归档 + 重定向 Pages；发版 `v2.0.0`。
- 验收：新站与下载可用；旧入口可达；CI 全绿；发布说明列明书名、卷次、介质与旧地址。

## 12. 风险、缓解与回滚

| 风险 | 概率/影响 | 缓解 |
|---|---|---|
| VitePress 适配层不保真（锚点、HTML、公式、计算器） | 高/中 | 63 页 parity 清单；计算器冒烟测试；P3 前保留 MkDocs 旁路 |
| 跨卷引用悬空 | 中/中 | 统一解析器 + 构建期审计；禁止硬编码「见卷 X」 |
| VitePress 构建变慢/体积膨胀 | 中/低 | 资源按引用复制、懒加载、缓存；构建时长纳入报告 |
| git subtree 历史或冲突 | 低/中 | 一次导入、不做 rebase、冻结标签；冲突时以子树侧为准再手工修 |
| CI 时长与成本上升 | 中/低 | 路径过滤、split 工作流、依赖缓存 |
| 旧站地址失效 | 高/中 | 旧仓库保留重定向 Pages；README/下载页标注 canonical；发布说明提醒 |
| EPUB 统一后回归 | 中/中 | 两套构建器并行到 spine/TOC 金样测试通过；保留旧产物哈希 |
| 未提交改动丢失 | 低/高 | P0 强制先提交；合并分支隔离；不触碰原工作区 |

回滚：

- 全程只在 `merge/analog-into-bms` 分支进行；旧仓库与 `main` 不动。
- P5 前任何阶段失败：保留已完成产物，回退到上一闸；必要时放弃分支，两库保持原状。
- P5 后如需回退：恢复旧仓库 Pages 与下载页，发布说明标注新站暂停。

## 13. 最终验收清单

1. 干净检出执行 `python book/build.py all`，四类介质与站点全部产出，审计全绿。
2. 站点一个域名、一套导航、一套搜索；卷 I 63 页、卷 II 全部页面可达。
3. 卷 I 11 个计算器、50 页锚点、153 张动画、16 页公式全部正常。
4. 跨卷引用 0 悬空；印刷版引用降级为文本且可读。
5. 16K 三册均 ≤700 页；单文件 HTML 不超卷级上限（卷 I 24 MB、卷 II 32 MB）；EPUB spine 完整。
6. 两边原有测试、内容闸、外链巡检全部通过。
7. 旧仓库归档、README 指向新家、旧入口有重定向页。
8. 根 README、下载页、发布说明与书名/卷次/介质一致。

## 14. 事实附录

- 模拟电路书页数：63 页（含篇页与目录页）；核心 19 章（第 0–18 章）。
- BMS 书：前言 + 32 章 + 附录 A–E，共 38 个书文件；PDF 380 页、512 书签。
- 模拟电路 16K 单卷 812 页超上限，已按自然篇界分两卷：448 + 508 页。
- 模拟电路 A4 PDF 400+ 页；单文件 HTML 约 21 MB 量级（以构建报告为准）。
- BMS 单文件 HTML 27.5 MB、PDF 30.3 MB、EPUB 14.0 MB（2026-11 构建产物）。
- 模拟电路书页自定义锚点 50 页、计算器 11 页、内联 SVG 1 页、数学 16 页、`{{` 与 `<script>` 0 处。
- 两书文档许可均为 CC BY-SA 4.0；BMS 代码 MIT。
