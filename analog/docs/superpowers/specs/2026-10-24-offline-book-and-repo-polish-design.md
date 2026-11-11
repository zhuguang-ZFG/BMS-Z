# 离线整书与仓库工程化改进 · 设计规格

- 日期：2026-10-24
- 状态：已与作者确认方向，待作者复核
- 目标仓库：`analog-circuit-roadmap`（对应站点 v3.61）
- 参考仓库：同级 `STM32` 知识库（`stm32-book/`、`Makefile`、`CREDITS.md`、CI）

## 1. 背景与目标

本仓库目前有在线 MkDocs 站（含打印样式）和由 `docs/` 生成的单文件 README，但没有可离线分发、可打印的成书产物；仓库也缺少与 `STM32` 对齐的工程化入口（Makefile、来源致谢、徽章）与面向故障读者的首页直查入口。

本次改进交付三块能力：

1. **离线整书**：从现有站点产物生成单文件 HTML（断网可读、保留动画与计算器）与 A4 PDF（书签、页眉、页码、目录页码），带构建自检与 CI。
2. **工程化收口**：顶层 Makefile、`CREDITS.md`、完整体检徽章、整书 CI 与维护铁律。
3. **内容入口**：首页新增「按现象直查」一屏表；英文版给出暂缓结论。

## 2. 非目标

- 不翻译英文版。评估见 §9。
- 不改变仓库现有授权（内容 CC BY-SA 4.0）。
- 不重构 `docs/` 内容生产链路，不引入第二份内容源。
- 不把 `dist/` 产物提交进仓库（与 `stm32-book/dist/` 一致）。
- 不触碰 `video/remotion` 下未提交的改动。

## 3. 已确认决策

| 决策 | 结论 |
|---|---|
| 整书构建方式 | **站点产物拼装**（方案 A）：复用 `build_site.py --build` 的页面，抽取正文拼装 |
| 整书范围 | 收录 `docs/` 除首页外的全部 60 个内容页（含动画中心、题库、更新日志、致谢与新增来源页） |
| 首页 | 不进入正文章节；由生成的封面页、版权页、目录替代 |
| 英文版 | 本期不做，仅在规格中给出可行性结论 |
| 产物 | `dist/analog-circuit-book.html`、`dist/analog-circuit-book.pdf`，不入库，CI 上传 artifact |
| 数学公式 | 整书使用 MathJax **SVG 输出**并内联，保证单文件断网可排版；在线站继续用现有 CHTML |
| 现象直查表 | 放在首页 hero 之后、「找到适合你的起点」之前，改 `docs/index.md` |

## 4. 总体架构

```text
docs/ (唯一内容源)
  └─ scripts/build_site.py --build
        └─ build/site/*.html + assets/ (在线站产物)
              └─ analog-book/build_book.py
                    ├─ analog-book/manifest.json   (书目结构与元数据)
                    ├─ 抽取 <article> → 命名空间化 ID → 重写链接
                    ├─ 内嵌图片/CSS/JS/MathJax(SVG)
                    ├─ 生成封面/版权页/目录 → 单文件 HTML
                    └─ Playwright 打印 → PyMuPDF 盖章 → A4 PDF
                          └─ analog-book/dist/ (+ CI artifact)
```

- 构建链仍以 `docs/` 为唯一数据源；`manifest.json` 只定义「收录哪些页、如何分篇」，不存正文。
- 整书是站点的派生产物：站点构建失败，整书构建必须失败；不允许绕过站点自行渲染 Markdown。
- 产物不进入 Git；`analog-book/dist/` 加入 `.gitignore`。

## 5. 离线整书设计

### 5.1 目录与文件

```text
analog-book/
├── README.md              # 构建方式、依赖、范围、发布说明
├── manifest.json          # 书目元数据 + 篇/页顺序
├── build_book.py          # 单文件 HTML + PDF 构建
├── requirements.txt       # Playwright、PyMuPDF（HTML 构建只需仓库 requirements）
├── styles/book.css        # 书版式 + 打印样式（源文件，构建时内联）
├── static/
│   ├── roadmap.source.txt # Mermaid 源快照（与 p0-06 比对，漂移即红灯）
│   └── roadmap.svg        # 预渲染的静态路线图（书内嵌入）
├── tests/
│   ├── test_build.py      # 单元 + 集成审计
│   └── test_pdf.py        # 浏览器/PDF 结构校验（缺依赖时 skip）
└── dist/                  # 构建产物（gitignore）
```

新增第三方静态资产：

- `assets/vendor/mathjax-svg/tex-svg-full.js`（MathJax 3.2.2，Apache-2.0，来源与哈希写入 `assets/vendor/mathjax-svg/README.md`）。现有 `assets/vendor/mathjax/`（CHTML）保持不动，在线站继续使用。
- 23 张原本热链到 Wikimedia Commons 的章节配图落到 `assets/photos/web/`（其中 `Photo-SMDcapacitors.jpg` 复用已有 `assets/photos/capacitors.jpg`，故新增 22 个文件）。`docs/` 的图片引用改为本地路径，站点、README 与整书共用同一份资产；作者/原图页/授权统一登记在 `docs/p9-14-credits.md`，`assets/photos/README.md` 保留处理说明并指向该页。
- 3 张 YouTube 视频缩略图仍留在在线站；整书把「缩略图链接」改写为文字视频入口，不把第三方缩略图打包进 CC BY-SA 书籍。

### 5.2 manifest 结构

```json
{
  "title": "通往模拟电路之路",
  "subtitle": "从欧姆定律到芯片内部结构",
  "version": "1.0.0",
  "source_version": "3.61",
  "date": "2026-10-24",
  "language": "zh-CN",
  "author": "zhuguang-ZFG 与贡献者",
  "site_url": "https://aliyun-hutuji.donglicao.com/analog-circuit-roadmap/",
  "repository": "https://github.com/zhuguang-ZFG/analog-circuit-roadmap",
  "license": "CC BY-SA 4.0",
  "parts": [
    {"id": "p0", "files": ["p0-01-preface.md", "..."]},
    {"id": "p1", "files": ["p1-00-part1.md", "..."]}
  ],
  "appendix": {
    "title": "附录",
    "files": ["p9-12-changelog.md", "p9-13-thanks.md", "p9-14-credits.md"]
  }
}
```

**篇/页映射（合计 60 个内容页）：**

| 篇 | 文件 | 页数 |
|---|---|---:|
| p0 开始之前 | `p0-01` … `p0-10` | 10 |
| p1 器件深度原理解析 | `p1-00` … `p1-11` | 12 |
| p2 经典电路拓扑原理 | `p2-00` … `p2-03` | 4 |
| p3 电路设计要点与 PCB 实战 | `p3-00` … `p3-02` | 3 |
| p4 故障分析与排故方法论 | `p4-00` … `p4-03` | 4 |
| p5 动画演示中心 | `p5-00` | 1 |
| p6 常用芯片实物图鉴与速查 | `p6-00` … `p6-05` | 6 |
| p7 视频资源汇总 | `p7-00` … `p7-03` | 4 |
| p8 学习路线与资源索引 | `p8-00` … `p8-11` | 12 |
| p9 自测与练习 | `p9-00` | 1 |
| 附录 | `p9-12`、`p9-13`、`p9-14` | 3 |

- 篇标题、页面标题不写进 manifest，构建时从页面渲染后的第一个 `<h1>` 提取；缺失即构建失败，避免标题双份维护。
- `parts` + `appendix` 必须恰好覆盖 `docs/*.md` 中除 `index.md` 外的 60 个文件；多、少、重复都报错。
- 来源与致谢的**唯一内容源是 `docs/p9-14-credits.md`**（进 README、进站点导航、进整书附录）；仓库根 `CREDITS.md` 只放一段简短索引与授权摘要，指向该页，避免双份正文。
- 版本号：整书自身 `1.0.0`；`source_version` 手动对应 `docs/p9-12-changelog.md` 当前版本（v3.61），发版时同步更新。

### 5.3 HTML 拼装流水线

1. **站点构建**：`build_book.py` 默认调用 `python scripts/build_site.py --build`；`--site-dir` 或 `--no-build` 允许复用已生成的 `build/site`（测试/CI 用）。
2. **清单对账**：校验 manifest 覆盖率、文件存在、站点 HTML 存在；解析每页 `<article class="md-content__inner md-typeset">…</article>`，缺 `<article>` 或 `<h1>` 即失败。
3. **清洗站点专属块**：
   - 删除 `.legacy-anchor`（旧 URL 跳转占位，且是重复 ID 的主要来源）；
   - 删除含「参与共建」的页脚 `<hr> + <blockquote>`；
   - 保留 `.reading-checkpoint`（章末自测/下一章入口），链接稍后重写为书内锚点。
4. **ID 命名空间化**：对每页所有 `id` 与 `name` 属性加前缀 `<页 stem>--`（如 `p1-01-ch0--ch0`）。同一页内已带该前缀的不重复加。目标：整书 ID 全局唯一。
5. **链接重写**：
   - `#x` → `#<当前页>--x`；
   - `page.html#x` → `#<目标页>--x`（目标页在书中）；
   - `page.html` → `#<目标页>`；
   - `index.html` → `#book-toc`（书内目录，取代「回到学习起点」）；
   - 其余未收录页（`gallery.html`、`CONTRIBUTING.html` 等）→ `site_url + page.html[#x]`；
   - `assets/**` 下载文件（`.zip`、`.cir` 等）→ `site_url + 相对路径`；
   - `http(s)`、`mailto:`、纯 `#` 原样保留；
   - 未知内部锚点或未知页面：构建失败并列出文件/链接，禁止静默留死链。
6. **资源内嵌**：
   - `<img src="assets/...">`、`<source srcset="assets/...">` → data URI（SVG/PNG/JPEG；SVG 用 base64，保持 `<picture>` 的减弱动效选源行为）；
   - 远程图片：`img.youtube.com` 的缩略图连同外层链接改写为文字视频入口（`▶ 视频标题`）；其余 `http(s)` 图片一律构建失败，新增外链图必须先本地化到 `assets/`；
   - CSS 内联：Material `main.*.min.css`、`palette.*.min.css`、`typography.css`、`gallery.css`、`learning.css`、`reading.css`、`diag.css`、`book.css`；移除指向外部文件的 `<link>`（`gallery.css` 是 p5 动画画廊的静态排版依赖，`gallery.js` 仍不进书）；
   - JS 内联：`calc.js`、`learning.js`、`learning-catalog.js`、`diag.js`（按需）；剔除 `progress.js`、`reading.js`、`gallery.js` 与 Material bundle；移除所有 `<script src>`；
   - 数学：内联 `tex-svg-full.js` 与书版配置（`svg.fontCache = 'local'`，沿用 `processHtmlClass: "arithmatex"`），保证 `file://` 断网可排版；
   - 站点专属 DOM：删除编辑按钮（`.md-content__button`）、标题后的 `headerlink` ¶ 锚点、`.legacy-anchor` 与「参与共建」页脚；保留 `.reading-checkpoint`；
   - 禁止 `<iframe>`、`<video>`；发现即构建失败（当前正文内为 0）。
6b. **Mermaid 静态化**：`p0-06-roadmap` 的 `<pre class="mermaid">` 依赖 Material bundle 在浏览器端渲染。整书改为嵌入预渲染的 `static/roadmap.svg`，并在构建时把页面里的 Mermaid 源码与 `static/roadmap.source.txt` 比对；不一致即失败，提示重新生成快照。在线站保持原有交互渲染。
7. **书结构**：
   - `<header class="book-header">`：书名 + 「目录」链接；
   - 封面页（CSS 排版：书名、副标题、版本/日期、在线地址、仓库标识）；
   - 版权页（授权、来源、版本、仓库、免责声明）；
   - 目录（篇 + 页面，链接到书内锚点；PDF 另行盖章页码）；
   - 每个篇包在 `<section class="book-part" data-part="pN">`，其内先放篇首页，再放该篇各章；每个页面再包一层 `<section class="book-page" data-page="<stem>">`；附录使用 `data-part="appendix"`；
   - 页尾「返回目录」链接；不引入固定侧栏，保持单文件轻量。
8. **字体与主题**：书版固定浅色（打印一致），沿用站点系统字体栈；不使用 Material 的导航/搜索/暗色主题样式。
9. **输出版本与审计**：`dist/analog-circuit-book.html`；`<head>` 写入 `<meta name="book-manifest-sha256">` 与书名/版本/日期；构建结束打印页数、图片数、公式数、内联体积；`--check` 对现有 HTML 复用同一审计器并比对 manifest 哈希，不落盘。

### 5.4 PDF 流水线

1. Playwright Chromium 打开 `dist/analog-circuit-book.html`（`file://` URI）。
2. 浏览器上下文设 `reduced_motion="reduce"`：`<picture>` 选静止版 SVG，SMIL 动画停止，打印帧稳定。
3. 等待：`document.fonts.ready`、MathJax `startup.promise`、`MathJax.typesetPromise`，以及 `img` 全部 `complete`；超时 120 秒。
4. `page.pdf()`：A4、`print_background=True`、`prefer_css_page_size=True`、页边距由 `@page` 控制；不启用 Chrome 自带页眉页脚。
5. PyMuPDF 后处理：
   - 写入 PDF 元数据（title/subject/author/keywords/creator）；
   - 目录页码：按目录链接的矩形位置，把目标页页码盖在右侧；
   - 页眉：奇数页书名、偶数页当前篇/章标题；页脚居中页码；封面/版权页/目录页不加页眉页码；
   - 书签：篇 = 一级、页面 = 二级，基于目录链接目标页生成；
   - 输出 `dist/analog-circuit-book.pdf`。
6. 失败处理：缺少 Playwright/PyMuPDF 或浏览器时，`--pdf` 给出可操作的错误（安装命令），HTML 仍可单独构建。

### 5.5 书版打印样式（`styles/book.css`）

- `@page { size: A4; margin: 18mm 16mm 20mm; }`。
- 篇首页、章节页 `break-before: page`；封面/版权/目录各自成页。
- `h1–h3`、图注、表格行、提示卡 `break-inside: avoid`；`h2/h3` `break-after: avoid`。
- 打印隐藏：书头、返回目录、`.reading-nav`、计算器输入控件与按钮；保留计算器默认读数。
- 图片 `max-width: 100%`；宽表允许横向缩放或换行，不裁切。
- 站点 `reading.css` 中依赖 `:has(#cheatsheet)` 的页面级分页规则在书中不生效；书版用 `data-page` 选择器复刻速查表/题库的分组分页。
- 目录页码由 PyMuPDF 盖印，不依赖 CSS 计数器。

## 6. 工程化收口

### 6.1 顶层 Makefile

`PY ?= python3`，目标定义：

| 目标 | 作用 |
|---|---|
| `make readme` | `scripts/build_readme.py` 重建 README |
| `make site` | `scripts/build_site.py --build` 构建在线站 |
| `make book` | 构建单文件 HTML（内部先构建站点） |
| `make book-pdf` | 构建 HTML + PDF（需 Playwright/PyMuPDF） |
| `make book-check` | 对现有整书产物跑离线审计，不重建 |
| `make test-static` | SVG 复现、docs↔README、锚点、页面结构、站点构建、smartsymbols |
| `make test-browser` | Playwright 回归（计算器/首屏/阅读路线/无障碍） |
| `make verify` | `test-static` + README 同步检查 + 整书构建与审计 |
| `make stats` | 文档/动画/题库/视频/测试规模统计 |
| `make clean` | 清理 `build/`、`analog-book/dist/`、`__pycache__` |

- `make verify` 不依赖联网与浏览器；`make book-pdf` 才需要 Playwright/PyMuPDF。
- README 与 CONTRIBUTING 增加「常用命令」表。

### 6.2 来源与致谢

新增 `docs/p9-14-credits.md` 作为**唯一内容源**（进 README、站点附录导航与整书附录），按资产类别列出：

- 正文、SVG 动画、实验包、网表：本仓库生成，CC BY-SA 4.0；
- 实物照片：25 张 Wikimedia Commons（3 张教学样板 + 22 张章节配图；作者、原图页、授权逐条列在页内）；
- 第三方软件/资产：MathJax（Apache-2.0）、MkDocs Material（MIT）、jieba（MIT）、Playwright（Apache-2.0）、PyMuPDF（AGPL-3.0，仅构建工具）、视频字体 ZCOOL KuaiLe（OFL-1.1）；
- 外部资料：官方 datasheet、应用笔记、论文与视频链接的引用原则（不复制受版权保护的图片；3 张 YouTube 缩略图只在在线站预览，整书不打包）；
- 更新规则：新增第三方图片/字体/代码资产必须同步该页，并同时更新 `assets/photos/README.md` 的处理说明。

仓库根 `CREDITS.md` 保留简短索引与授权摘要，指向 `docs/p9-14-credits.md`，不复制正文。`docs/p9-13-thanks.md` 增加指向该页的链接；`scripts/build_site.py` 的 `APPENDIX` 集合加入 `p9-14-credits.md`，使站点附录导航自动出现「来源与许可」。

### 6.3 徽章

在 `docs/index.md` 的 `.repo-badges` 容器内补齐（README 自动重建，站点端仍整块隐藏）：

- tests（现有）
- 文档 60 页（不含首页；新增来源页后）
- SVG 动画 108 张
- 视频课 20 集
- 离线整书 HTML/PDF（链接 `analog-book/`）
- 授权 CC BY-SA 4.0

### 6.4 CI

新增 `.github/workflows/book.yml`：

- 触发：`push main`、`pull_request`、`workflow_dispatch`；
- Python 3.12，安装 `requirements.txt` + `analog-book/requirements.txt` + Playwright Chromium；
- 步骤：站点构建 → 整书 HTML 构建 → 整书单元/审计测试 → `--check` → PDF 构建 → PDF 结构测试 → 上传 HTML/PDF artifact（保留 14 天）；
- 整书校验统一放在 `book.yml`，`tests.yml` 与 `pages.yml` 不改，避免拖慢现有 PR 与站点发布。
- `book.yml` 在 PR 上跑完整 HTML+PDF（与 `stm32-book` 的 CI 一致）；上游站点构建失败时整书作业直接失败。

### 6.5 CONTRIBUTING 增补

- 改 `docs/` 后：`make readme`；涉及整书范围/标题时 `make book`；提交前 `make verify`。
- 新增内容页必须加入 `manifest.json`，否则整书审计红灯。
- 新增第三方资产必须更新 `CREDITS.md`。
- 不直接编辑 `analog-book/dist/`、`build/`、`README.md`。

## 7. 首页「按现象直查」

在 `docs/index.md` hero 之后、「找到适合你的起点」之前新增：

```markdown
## 卡住了？按现象直查

板子不工作、波形不对、读数在跳——先对号入座，再回到原理。完整故障表见[第 17 章](p4-02-ch17.md#ch17)，按需求找电路见[情景导航](p0-04-by-need.md)。

| 你看到的现象 | 最可能的原因 | 先看这里 |
|---|---|---|
| 上电没反应、整机不工作 | 电源、极性、保险丝、地没接 | [第 16 章 排故五步法](p4-01-ch16.md#ch16) · [第 17 章 速查](p4-02-ch17.md#ch17) |
| 输出比算出来的低，一接负载就塌 | 内阻与带载效应 | [第 0 章 电路直觉](p1-01-ch0.md#ch0) · [速查表·直流](p0-08-cheatsheet.md#dc) |
| 波形顶部/底部被削平 | 限幅、钳位、输出轨限 | [第 2 章 二极管](p1-03-ch2.md#ch2) · [第 12 章 运放电路族](p2-02-ch12.md#ch12) |
| 运放输出贴轨、不放大 | 供电、共模范围、反馈接错 | [第 6 章 运放](p1-07-ch6.md#ch6) · [第 12 章](p2-02-ch12.md#ch12) |
| 三极管/MOSFET 发烫 | 驱动不足、导通损耗、米勒振荡 | [第 3 章 BJT](p1-04-ch3.md#ch3) · [第 4 章 MOSFET](p1-05-ch4.md#ch4) |
| 输出自激、莫名振荡 | 容性负载、相位裕度、布局 | [第 6 章 运放](p1-07-ch6.md#ch6) · [第 15 章 PCB](p3-02-ch15.md#ch15) |
| ADC 读数在跳、噪声大 | 地线、去耦、基准 | [第 9 章 基准](p1-10-ch9.md#ch9) · [第 15 章 接地](p3-02-ch15.md#ch15) |
| 高频信号过不去、边沿变肉 | 寄生参数、带宽、探头负载 | [第 1 章 无源](p1-02-ch1.md#ch1) · [第 12 章 Sallen-Key](p2-02-ch12.md#ch12) |
| MCU 引脚推不动、总线通信失败 | 上拉、开漏、总线电容 | [第 5 章 推挽与开漏](p1-06-ch5.md#ch5) |
| 板子偶发复位、上电烧器件 | 电源跌落、地弹、浪涌 | [第 16 章](p4-01-ch16.md#ch16) · [第 17 章](p4-02-ch17.md#ch17) |
```

- 链接使用 `docs/` 相对路径与已存在的章级锚点（`#chN`）；README 构建自动反写为 `#anchor`，站点构建自动转 `.html`。
- 文案与现有章节标题逐字一致；新增行若指向不存在锚点，`test_docs_links` 必须红灯。
- 不改动 hero、学习路径、阶梯与统计块，避免破坏首屏测试。

## 8. 测试与验收

### 8.1 整书单元/集成测试（`analog-book/tests/`）

- manifest：覆盖全部 60 个内容页，无遗漏/重复/多余；篇 ID 唯一；附录文件存在。
- 站点产物：每页 `<article>` 与 `<h1>` 存在；清洗后无 `.legacy-anchor`、无「参与共建」页脚。
- ID：整书无重复 ID；所有 `href="#..."` 目标存在；所有 `page.html#x` 已转为书内锚点或站外绝对地址。
- 资源：无 `src="assets/`、无远程 `<img src="http…">`、无 `srcset="assets/`、无 `<script src>`、无 `<link rel="stylesheet">`、无 `<iframe>/<video>`；图片全部 data URI；Mermaid 页面已换成静态 SVG；YouTube 缩略图已变成文字入口。
- 结构：封面、版权页、目录、60 个内容页、附录齐全；目录条目数与清单一致；MathJax SVG 脚本存在；公式容器数 > 0；`roadmap.source.txt` 与页面 Mermaid 源码一致。
- 体积：HTML < 20 MB；超过则失败并报告最大图片。
- 确定性：连续两次构建的 HTML SHA-256 一致。
- `--check`：对现有产物跑同一审计；产物缺失或过期（manifest 哈希不一致）时失败。

### 8.2 浏览器与 PDF 冒烟

- Playwright 打开 `file://` 整书：等待 MathJax；断言 `.mjx-container` 数量 > 1000；断言至少一只计算器已渲染默认结果；点击目录条目后目标元素进入视口；无 console error。
- PDF：页数 > 40；元数据 title 正确；书签包含全部篇与页面；目录页码已盖印（抽查 3 个条目）；封面/版权/目录页无页码。
- 缺 Playwright/PyMuPDF 时 `test_pdf.py` 自动 skip，`make verify` 不受影响。

### 8.3 既有回归

- 跑现有 `scripts/test_*.py`：static 组必须全绿；browser 组在本机/CI 按现有方式全绿。
- 首页改动后重点跑 `test_first_screen.py`、`test_docs_links.py`、`test_readme_links.py`、`test_site_build.py`。
- README 重建后跑 `test_docs_sync.py`。

## 9. 英文版可行性结论

**本期暂缓，理由：**

- 规模：60 页正文、1,680 处公式、108 张动画、20 集中文视频；翻译不是线性工作量，技术术语与故障案例需要双语审校。
- 维护：`docs/` 是唯一源，当前每次内容更新只需维护一份；双语后每次改动都要双份同步，现有 `test_docs_sync`、链接对账、SEO/导航测试全部要扩成双语矩阵。
- 站点：MkDocs Material 需要 `mkdocs-static-i18n` 之类插件，导航、搜索分词、`use_directory_urls: false` 的平铺路由、旧锚点重定向都要重新设计。
- 需求：现有读者、视频与公众号均为中文；英文版缺少配套视频与传播渠道。

**若未来启动**：先做 `docs/en/index.md` + 第 0 章试译，接入 i18n 插件与双语链接测试，跑一个版本周期评估维护成本，再决定是否全量。该试点不属于本次范围。

## 10. 依赖与资产

- HTML：仓库现有 requirements（mkdocs-material、jieba、numpy）。
- PDF：`analog-book/requirements.txt`：`Playwright>=1.61,<2`、`PyMuPDF>=1.28,<2`；本机需 Chromium/Edge 或 `playwright install chromium`。
- MathJax SVG：3.2.2 官方 npm 包 `es5/tex-svg-full.js`，记录来源、SHA-256、许可证；与 CHTML 版本保持一致。
- 章节配图：22 个新文件，640px 缩略图合计约 3.6 MB，下载后逐字节入库；`docs/` 改本地路径，整书按现有 data URI 流程内嵌。
- 不新增运行时依赖到在线站。

## 11. 交付物清单

```text
analog-book/{README.md,manifest.json,build_book.py,requirements.txt,styles/book.css,static/roadmap.{svg,source.txt},tests/*}
assets/vendor/mathjax-svg/{tex-svg-full.js,README.md,LICENSE}
assets/photos/web/*.jpg|png（22 个章节配图）
assets/photos/README.md（处理说明 + 指向唯一授权清单）
.github/workflows/book.yml
Makefile
CREDITS.md（根索引，指向 docs/p9-14-credits.md）
docs/p9-14-credits.md（来源与许可的唯一内容源，含 25 张照片清单）
docs/superpowers/specs/2026-10-24-offline-book-and-repo-polish-design.md
docs/index.md（现象直查表 + 徽章）
docs/p9-13-thanks.md（链接来源页）
docs/p1-02-ch1.md、p1-03-ch2.md、p1-04-ch3.md、p1-07-ch6.md、p1-10-ch9.md、p1-11-ch10.md、p2-03-ch13.md、p3-02-ch15.md、p4-01-ch16.md、p6-01-s6-1.md（10 页远程图片改本地路径）
scripts/build_site.py（APPENDIX 加入 p9-14）
scripts/build_stats.py（make stats）
README.md（由 docs/ 重建）
CONTRIBUTING.md（整书/来源页/命令）
.gitignore（analog-book/dist/）
```

## 12. 风险与缓解

| 风险 | 缓解 |
|---|---|
| 站点产物结构变化导致抽取/重写静默失效 | `<article>`/`<h1>` 缺失即失败；链接/ID 审计；CI 整书作业 |
| 104 个重复 ID 造成锚点错乱 | 全量 ID 命名空间化 + 全局唯一性断言 |
| MathJax 1,680 处公式拖慢加载/打印 | SVG 内联；Playwright 显式等待 `typesetPromise`；超时 120s；体积/公式数审计 |
| 单文件体积过大（动画画廊重复内嵌 + 新增 22 张配图） | 实测本地图片 4.05 MB + 新增配图约 3.6 MB，base64 后约 10.8 MB；预计整书 16–18 MB；硬上限 20 MB；审计报告最大资源；超限时优先对 p5 同图去重或降配图尺寸 |
| 远程图片导致“假离线” | 23 张 Wikimedia 配图本地化并入站；3 张 YouTube 缩略图改为文字入口；构建器遇到未知远程 `<img>` 直接失败 |
| Mermaid 依赖 Material bundle | 预渲染 `static/roadmap.svg`，源快照比对漂移；在线站保持原交互 |
| 第三方配图授权登记不全 | 25 张照片逐条登记作者/原图页/授权；新增资产规则写入 CONTRIBUTING 与构建测试 |
| PDF 字体/分页/页码异常 | 浏览器预览 + PyMuPDF 抽页断言；封面/目录不加页眉页码；打印用减弱动效 |
| PyMuPDF AGPL 许可 | 仅作构建工具，不进入在线站；`CREDITS.md` 明示 |
| 首页新增表格破坏首屏测试 | 不动 hero/阶梯；新增区块在 hero 之后；跑 `test_first_screen` 与对比度测试 |
| 现有未提交视频改动被误伤 | 只改上述文件；构建产物在 ignored 目录；不执行 git clean/reset |

## 13. 验收清单

- [ ] `make book` 生成单文件 HTML，断网打开：目录可跳转、公式已排版、图片可见、至少一只计算器可用。
- [ ] `make book-pdf` 生成 A4 PDF：封面/版权/目录齐全，篇/章另起页，书签与页码正确。
- [ ] `make book-check` 在无浏览器环境通过审计。
- [ ] `make verify` 通过（README 同步、SVG 复现、整书审计）。
- [ ] 现有 static/browser 测试全绿。
- [ ] 首页「按现象直查」在 README 与站点均正确渲染，10 行链接全部可达。
- [ ] `CREDITS.md`、徽章、Makefile、CI、CONTRIBUTING 就位。
- [ ] `git status` 中无 `dist/`、无构建缓存、无视频目录改动。
