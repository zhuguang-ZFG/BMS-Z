# 参与共建 🤝

本指南是开放知识库，欢迎一切形式的贡献。

## 你可以贡献什么

| 类型 | 举例 | 渠道 |
|---|---|---|
| 🐛 纠错 | 公式错误、参数过时、链接失效（附 datasheet 页码最佳） | Issue |
| 🔧 故障案例 | 你的真实翻车现场——症状/根因/解法三要素 | PR 或 Issue |
| 📺 资源 | 高质量视频/论文/应用笔记（注明为什么好） | PR |
| 🎬 动画 | 新主题 SVG 动画（见下方铁律） | PR |
| ✍️ 章节 | 新器件/新拓扑深度解析（遵循统一结构） | PR |
| 🧪 题目 | 自测题库新增好题（含答案与解析） | PR |

> 📮 **不想写代码？两条最快的路**：
> 1. **提 Issue**——[纠错](https://github.com/zhuguang-ZFG/analog-circuit-roadmap/issues/new?template=content-fix.yml)（错别字 / 公式 / 事实 / 失效链接）
>    或 [建议](https://github.com/zhuguang-ZFG/analog-circuit-roadmap/issues/new?template=new-topic.yml)（新增主题 / 动画 / 资源）。
>    模板已把"位置 / 问题类型 / 依据"列好，填完即可，不需要懂 Git。
> 2. **在线站每页右上角有 ✎「编辑此页」**，直接跳到该页对应的 `docs/xxx.md` 开 PR；
>    页面底部还有「参与共建」快捷入口。发现一处错字，30 秒就能改完。

## 仓库铁律（PR 前自查）

0. **`docs/` 是唯一数据源，不要直接改 `README.md`**——README 由 `scripts/build_readme.py` 从 `docs/` 拼出，改完必须重跑（CI 会比对，漂移即红灯）
1. **`assets/svg/` 内文件必须 == `scripts/generate_svgs.py` 的输出**——改图先改脚本，再 `python3 generate_svgs.py` 重跑，绝不允许只改 SVG 文件不回灌脚本
2. **外链必须可达**：提交前自行 HTTP 验证；CI（lychee）会对 README.md 全量外链做检查，红灯的 PR 无法合并
3. **实物图仅用公有领域 / CC 授权**（Wikimedia Commons 优先），并在图注注明来源
4. **统一结构**：新器件章遵循「物理原理 → 数学模型 → 内部电路 → 关键参数 → 典型应用 → 故障模式 → 动态分析 → 配套视频」
5. **文风**：说人话、给数量级、每图配"**精髓**"或"怎么看"段——参考现有章节（提示块用纯文本粗体标签，如 `> **精髓**：`，不要加 emoji 前缀）
6. **跨页跳转用锚点**：`docs/` 是多页站点，`#ch3` 这类锚点要写成 `p1-04-ch3.md#ch3`（拼回 README 时脚本会自动还原成 `#ch3`）
7. **锚点必须与内容同页**：`#chN` 放在第 N 章页首、`#partN` 放在对应篇页首，节级锚点紧邻它的标题；不能留在上一页页尾。检查必须同时验证「存在」与「归属正确」。历史外链兼容记录在 `scripts/site_media/legacy-anchors.json`，只向站点产物注入兼容入口，不能在 `docs/` 重复定义锚点。
8. **参数与结论要能核对**：涉及具体器件时写明型号、供电、负载、温度等相关条件，区分典型值与保证值；教学示意、仿真结果与实测数据分别说明。关键结论优先附厂商手册或应用笔记及章节，避免把经验值写成无条件规律。
9. **学习目标可验证**：用「能解释什么、算出什么、测到什么」描述目标。自测用于定位薄弱环节，不把题目分数当成独立设计能力的认证。
10. **正文里写 HTML 标签要转义尖括号**：反引号只保护**渲染**，不保护 MkDocs 的**源码扫描**——它用 HTML 解析器扫源码登记页内锚点，遇到 `script` / `title` 这类「原始文本」元素、或没写右尖括号的起始标签，会一路吞掉其后每个 `id` 属性，把真实存在的 `<a id>` 报成死链（v3.55.1 实测三处写法造成 7 条误报）。要展示标签就写 `<code>&lt;title&gt;</code>`，站点与 README 显示一字不差；`test_site_build.test_build_log_reports_no_missing_anchors` 在构建日志出现锚点误报时直接红灯。
11. **一个符号在一篇里只有一个意思，公式与文字必须同向**：v3.55.3 的第 7 章 §7.5 正是栽在这里——公式里乘 $V_{OH}$ 的是反馈电阻、正文却说反馈是另一个符号，于是"把 $R_2$ 改小 → 迟滞宽到 4.5V"方向与数值双错，还顺着抄进了题库答案。改数值要把数字代回**它上面那行公式**核对是否等于文中写的结果；同一个物理量存在两种判据（整 LSB / 半 LSB 这种）时，写清哪个更松、差多少，并互相链接，别让读者以为其中一处写错了。

## 三种产物，一条流水线

| 产物 | 生成命令 | 说明 |
|---|---|---|
| `README.md` | `python scripts/build_readme.py` | 单文件版，给 GitHub 阅读 |
| `build/docs/` + `build/mkdocs.yml` | `python scripts/build_site.py` | 站点源：内容页 + 动画画廊 + 主题配置 |
| `build/site/`（在线站） | `python scripts/build_site.py --build` | MkDocs Material 静态站，`main` 推送后自动部署 Pages |

新增一个章节 = 在 `docs/` 里加一个 `pN-MM-slug.md`（文件名前缀决定它在目录与侧栏里的位置），
然后跑一次 `build_readme.py`；导航与动画卡片由脚本自动生成，无需手工维护索引。
初次切分可复用 `python scripts/split_readme.py`（会把 README 拆成 docs 并改写锚点链接）。

实验说明的唯一来源是 `docs/p8-03-s8-3.md` 中的 `labs:common` 和 `lab:<id>` 注释区间。
`assets/labs/<id>/` 保存源电路、BOM、教学参考值和空白测量表。修改后运行
`python scripts/build_lab_packages.py` 重建三个 ZIP；ZIP 使用固定元数据和无压缩存储，可跨平台逐字节验证。
`python -B -m unittest discover -s scripts -p test_lab_packages.py -v` 会执行真实 ngspice 并比较参考采样点；
先安装 ngspice，或将 `NGSPICE` 环境变量指向其控制台可执行文件。不要用实测表伪装参考值，不要把教学模型标成厂商模型。

`assets/examples/` 的运放稳定性与积分器教学网表由 `test_circuit_examples.py` 执行，验证返回比、阶跃与幅值。它们是标明假设的线性教学模型，不是厂商宏模型；相关正文结论须保持模型条件一致。这一条同样要跑**真实 ngspice**：机器上没装、也没设 `NGSPICE` 时，全量 `discover` 会连同 `test_lab_packages.py` 一起红三条——那是缺仿真器，不是电路错了，CI 的「实验包 SPICE 仿真」作业装了 ngspice，以它为准。

发布由 `pages.yml` 编排：同一提交的可复用 `tests.yml` 和 `links.yml` 都成功后，才能构建和部署。
main 推送只运行这条带门禁的发布流程；其他分支、PR 和每周链接巡检保留各自入口。

## 本地检查

在仓库根目录运行以下基础检查（完整检查由 CI 的各作业执行）：

```bash
python -B -m unittest discover -s scripts -p 'test_docs_sync.py'    # docs → README 可 1:1 重建
python -B -m unittest discover -s scripts -p 'test_docs_links.py'   # 跨页锚点 / SVG 引用 / 标题
python -B -m unittest discover -s scripts -p 'test_readme_links.py' # README 锚点完整性
python -B -m unittest discover -s scripts -p 'test_svg_assets.py'   # SVG 与生成器逐字节一致
python -B -m unittest discover -s scripts -p 'test_a11y.py'         # SVG 可读名称/描述 + 图片 alt
```

`test_svg_assets.py` 使用生成器已有的 NumPy 依赖，在临时目录执行生成器，检查 SVG 文件集合、内容一致性和 XML 格式；不会覆盖仓库产物，忽略跨平台 LF/CRLF 差异。`test_waveform_timing.py` 需要 Playwright 和已安装的 Google Chrome，检查五张时间轴图（模拟开关、LDO、555、整流滤波、MOSFET 四拍）的时间轴、跳变、循环与圆点同步，以及 7 站点（comparator/wien/integrator/LDO/miller/peak/neg-feedback）的 x-匀速配速（delta=0.6px）。

这组测试已在 CI 中强制执行：`.github/workflows/tests.yml` 在每次推送和 PR 上运行 SVG 一致性检查（NumPy）、docs 单一数据源校验、站点可构建性与 Chromium 时间轴回归；`.github/workflows/links.yml` 用 lychee 巡检全量外链；`.github/workflows/pages.yml` 在 `main` 推送后部署 GitHub Pages。

使用 OMP 的 `task_verify` 时，从本仓库根目录启动会话。检查命令由本机 `task-verification-policy.json` 登记；新增或修改测试、检查参数和策略后，须审核并在下一用户轮建立基线。干净且本轮未修改的仓库返回 `not-required`，不表示测试已执行。

## 站点体验（`build_site.py` 生成，改这里就改全站）

首页内容在 `docs/index.md`；路线卡片、章末学习导航和旧链接提示的样式在 `scripts/site_media/reading.css`。

`progress.js` 管理本地阅读位置、手动完成状态和错题收藏，使用按站点路径隔离的 `analog-learning:v1:` 存储键。
旧版整份记录仍作为读取基线；新增完成状态和错题按 `completed:<章 ID>` / `bookmarks:<题 ID>` 后缀分别同步写入，阅读位置使用 `last` 后缀，均追加在原存储键后。
各条目独立保存，避免两个标签页写回旧快照互相覆盖，也避免异步保存被立即刷新取消。撤销写入 `false`，不能删除覆盖键，否则旧版基线中的记录会复活。
保存失败的条目留在本页内存，下次操作重试；首页、章末与题库提示存储状态。首页章节进度列表和错题列表更新时保留展开状态与键盘焦点。
导出使用 `format=analog-circuit-learning, version=1` 的 JSON，包含完成章节、错题与阅读位置。导入先校验整个文件（上限 256KB），仅接受已知稳定 ID，合并完成/收藏状态，已有阅读位置优先；不读取文件里的标题或 URL，不上传。失败的临时条目也须可以导出。
题目 ID（`q-chN-NN` / `q-extra-NN`）写在源文档中，重排题目时必须保留；新增题目分配新 ID，不能按当前题号批量重编号。
标题与跳转目标由 `learning-catalog.js` 从文档生成，禁止信任存储中的标题或 URL。存储失败、JSON 损坏和禁用 JS 时阅读仍须可用。
19 章的「上一章 → 本章自测 → 下一章」由章节文件自动生成；题库的 `#quiz-chN` 与返回复习链接在 `docs/p9-00-quiz.md` 维护。
`reading.js` 只负责旧锚点跳转，禁用 JavaScript 时仍有可点击的兼容入口。构建器显式生成页面标题，避免页首 HTML 锚点让标题退化成文件名。

打印样式在 `scripts/site_media/reading.css` 的 `@media print` 中维护：更新日志按系列、速查表按场景、题库按章节及专题组另起一页，长组允许续页；通过页面独有锚点限定范围，不给全站 h2 强制分页。精选保留连续排版。屏幕的 `body` 最小高度不能直接用于纸张：`min-height:100%` 加正文顶距曾使六条精选之后多打一张空白页；打印时设为 `0`。修改后既要检查 print 计算样式，也要实际生成 A4 PDF，核对组标题页首、正文完整性和末尾空白页；`test_picks_print_without_a_trailing_blank_page` 覆盖这个回归。

入场诊断的结果卡与无 JS 对照表必须提供同路线的速查出口，目标段以章首「公式速查」链接为准。`test_diagnostic.py` 实际回答四条路线、比较两种入口、点开目标并重测；修改路线时不要只核对 JS 源码里的字符串。

修改学习路线或导航后运行：

```bash
python -B -m unittest discover -s scripts -p test_docs_links.py -v
python -B -m unittest discover -s scripts -p test_split_readme.py -v
python -B -m unittest discover -s scripts -p test_site_build.py -v
python -B -m unittest discover -s scripts -p test_reading_journey.py -v
```

最后一组需要站点依赖、Playwright 和 Google Chrome，在临时目录构建完整站点，以子路径访问，检查首页入口、正文与题库往返、旧书签与浏览器返回、无 JavaScript 退化、手机明暗主题及真实搜索结果。外部请求全部拦截，不依赖线上部署。此组与拆分脚本回归均已纳入 CI。

测试构建的 sitemap 必须改写为测试 origin；否则 Material 不使用即时导航，测试会悄悄退回整页刷新。关键往返用页面内标记确认 document 未被重建，并验证真实 MathJax 产物。MathJax 配置在 `build_site.py`，等待首次排版后订阅 `document$`，串行处理后续排版并跳过已失效的页面。
Material 即时导航会替换 `<head>`，MathJax 的 CHTML 输出对象仍可能缓存已脱离文档的样式节点；因此每次后续排版在 `typesetPromise` 前执行 `MathJax.startup.output.clearCache()`，不能只清除公式和编号。仅检查 `mjx-container` 存在不足以证明公式可见：`test_mobile_formula_exit_keeps_glyphs_and_anchor_after_back` 在 390px 下比较完整加载与连续 SPA 往返的每个字形计算样式，并检查速查锚点落在视口内。函数应用符 U+2061 本来就是空字形，不可把“所有字形必须非空”当成正确性断言。
引擎和字体固定在 `assets/vendor/mathjax/`，保留上游授权与版本记录；不要只替换引擎而漏掉字体。长行内公式须局部滚动，不能撑宽页面。Markdown 列表与前段之间须有空行；题库的小节引用必须落到相应标题，章首返回入口仍指向章首。
题库源文件保留 GitHub 可读的 `<details markdown="1">`，与前面的题干、内部答案之间均留空行，保持在所属列表项内缩进四空格。构建器将该结构转换为原生 `pymdownx.details` 块，避免 Python-Markdown 把列表内的 HTML 包进段落。必须用浏览器实际展开答案并点击复习链接验证，同时确认产物不残留未处理的 `markdown` 属性。

修改画廊交互后运行 `python -B -m unittest discover -s scripts -p test_gallery_interactions.py -v`。
这组测试需要 Playwright 和 Google Chrome，直接加载生成器输出并拦截外部请求，覆盖弹窗焦点循环与恢复、单张结果、输入区域快捷键、筛选分享和空结果；CI 的 `svg-render` 作业会执行同一组检查。

教学样板的控制逻辑与样式在 `scripts/site_media/learning.js`、`learning.css`。正文用 `data-study="rc|mosfet|lm358"` 标记现有 SVG，用 `data-study-video` 标记 YouTube 原站链接；构建器复制脚本与样式，播放器只在点击后加载。新增阶段必须对照 SVG 的真实时序，不能把教学秒数当成电路时间。修改后运行 `python -B -m unittest discover -s scripts -p test_learning_interactions.py -v`（Playwright + Google Chrome）；覆盖真实 SVG 暂停、阶段定位、进度拖动、加载失败重试、手机放大和视频关闭。照片授权记录在 `assets/photos/README.md`，标注要在图注与 alt 中保留文字对应，以便无样式阅读。

## 无障碍与「减弱动效」

全站 251 张正文图片都有非空 `alt`；108 张动画 SVG 自带 `role="img"`、`aria-labelledby` 与非空 `<desc>`——`<desc>` 的节拍文案由 `caption()` 自动登记、`save()` 落盘时写进描述，读屏用户因此能听到这张图"讲了哪几拍"，而不只是一个文件名。

### 减弱动效**不能**写在 SVG 里（v3.45 的翻车点）

SVG 作为 `<img>` 载入时——**本站 108 张动画就是这么嵌的**——Chrome 把 `prefers-reduced-motion` **恒判为 reduce**：页面自己明明是无偏好，图片文档里却是 reduce。有头/无头、`data:`/`http`、以及独立启动的 Chrome 155 都实测一致。

后果是写在 SVG 里的 media query 只有两种结局：**要么恒不生效，要么恒生效**。v3.45 就是后者——全站动画对**所有人**都是静止的。更糟的是当时全套测试都绿灯，因为那些测试是"把 SVG 当**顶层文档**打开"的，而在那种上下文里偏好是正常的。

正确做法是让**页面**选源：`build_site.py` 用 `REDUCE_CSS` 生成一份静止版 `<stem>.reduce.svg`（只进站点产物，仓库里不留第二份），再把每个动画 `<img>` 包进

```html
<picture><source srcset="assets/svg/X.reduce.svg" media="(prefers-reduced-motion: reduce)"><img src="assets/svg/X.svg" …></picture>
```

`<source media>` 在**页面**上下文里求值，所以是准的。画廊弹窗里的 `<img>` 用不了 `<picture>`，由 `gallery.js` 的 `pickSvg()` 用 `matchMedia` 手动挑源。站点自身的悬停位移另在 `GALLERY_CSS` 与 `scripts/site_media/diag.css` 里各自关掉。

### 三条容易踩的规矩

1. **别把 media query 写回 SVG**——`test_a11y.py` 会把这条钉成红灯。想改减弱动效的行为，改 `build_site.py` 的 `REDUCE_CSS`，不要动 `generate_svgs.py`。
2. **新增动画不需要登记**——静止版的选择器按结构匹配（`:has(> animateMotion):not(:has(text))` 等），任何"带位移子节点且不含文字"的元素都会被关掉；反过来，**不要把位移动画挂在含正文文字的组上**，否则它会被当成字幕保留下来继续动。
3. **`svg_open()` 不能清空节拍登记**——有 8 张图（debug-flow / design-flow / diagnosis-tree / fault-lookup / ground-star / master-wisdom / thinking-toolbox / transformer）是先拼字幕、后调 `svg_open` 的；清空只放在 `save()` 落盘之后。字幕文案在生成器里已按 XML 转义（如 `距离&lt;3mm`），写进 `<desc>` 时**不能再转义一次**。

修改后运行：

```bash
python -B -m unittest discover -s scripts -p test_a11y.py -v             # 静态：role / desc / alt / 禁止 SVG 内 media query
python -B -m unittest discover -s scripts -p test_site_build.py -v       # 静态：每个动画都包了 <picture>、静止版都在
python -B -m unittest discover -s scripts -p test_reduced_motion.py -v   # Chromium：选源正确、粒子全停、字幕不误伤
```

第三组需要 Playwright 和 Google Chrome，分两步走：先在**页面**里断言 `<picture>` 在 reduce 下确实挑中静止版（这是机制本身），再把 SVG 当**顶层文档**逐张打开量 computed style——静止版必须零可见运动载体、节拍字幕一个不少，动画版必须真能看到上千个运动载体（防假绿）。只测后者正是 v3.45 漏掉的那一半。

| 能力 | 实现位置 | 说明 |
|---|---|---|
| 🎬 动画画廊 + 放大播放 | `gallery.md` / `gallery.js` / `gallery.css` | 108 张卡片，按章筛选 + 关键字搜索；「▶ 放大播放」弹窗全尺寸观看（SMIL 自动播放，Esc 关闭） |
| ✎ 编辑此页 | `mkdocs.yml` 的 `edit_uri` | 每页右上角直达 `docs/` 里对应的 Markdown |
| ✍️ 参与共建页脚 | `FEEDBACK_FOOTER` 常量 | 每页底部追加纠错 / 建议 / 共建指南入口（只加在站点产物，`docs/` 保持干净） |
| 🔎 SEO | `OVERRIDES_MAIN_HTML` + `ROBOTS_TXT` | og/twitter 社交卡片 meta、`robots.txt`；`sitemap.xml` 由 MkDocs 依 `site_url` 自动生成 |
| 📮 Issue 模板 | `.github/ISSUE_TEMPLATE/*.yml` | 纠错 / 建议两张表单 + 联系入口；PR 模板见 `.github/pull_request_template.md` |

> 💬 **评论区（可选）**：本站预留了 giscus（GitHub Discussions 评论）的接入位置。
> 仓库 ID 为 `R_kgDOU8y93w`。若要开启：① 在仓库 Settings 打开 Discussions 并建一个
> `Announcements` 分类；② 在 <https://giscus.app> 授权 giscus App 并取得 `data-category-id`；
> ③ 在 `scripts/build_site.py` 的 `FEEDBACK_FOOTER` 后追加 giscus 的 `<script>` 片段并重跑生成脚本。
> 未安装 giscus App 时不要打开，否则页面上会出现报错的空评论框。

## 流程

Fork → 特性分支 → 提交（commit message 中英文皆可，说明 why）→ PR。
文档许可 CC BY-SA 4.0，贡献即表示同意按此许可发布。

## 整书与离线产物

- 已发布整书（每次 main 构建更新）：<https://zhuguang-zfg.github.io/analog-circuit-roadmap/book/>；`pages` 复用 `book` 作业的产物，tests/links/book 全绿才部署。
- 改 `docs/` 后跑 `make gen`：README、`analog-book/data/animations.yml`、
  `assets/labs/*-lab.zip`、`analog-book/fonts/*.woff2` 四样都从 `docs/` 派生，漏一样 CI 就红一样（字体子集缺字会印成豆腐块，`make gen` 前先
  `python scripts/subset_fonts.py --download` 取一次源字体）。涉及整书标题或页面范围时运行 `make book`。
- 新增内容页必须加入 `analog-book/manifest.json`（16K 印刷书），否则 16K 整书审计红灯。A4 1.0 已冻结在 `analog-book/manifest-a4.json`，Phase 5 前不再改；`make book` 仍构建 A4，16K 用 `python analog-book/build_print_book.py`。
- 新增第三方图片/字体/代码资产必须更新 `docs/p9-14-credits.md`。
- 不直接编辑 `README.md`、`build/`、`analog-book/dist/`。
- 提交前跑 `make verify`；改了交互/样式再跑 `make test-browser`。
- Windows 没有 `make` 时用 `mingw32-make`，目标名一致。
