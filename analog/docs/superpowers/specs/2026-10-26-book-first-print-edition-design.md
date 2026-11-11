# 《通往模拟电路之路》书稿优先版 · 设计规格

- 日期：2026-10-26
- 状态：方向已确认，待作者复核
- 目标仓库：`analog-circuit-roadmap`
- 关联规格：
  - [16K 印刷版设计](2026-10-25-print-book-design.md)（内容蓝图与 DoD 继续有效；第 9 节工程架构由本规格取代）
  - [离线整书与仓库工程化改进](2026-10-24-offline-book-and-repo-polish-design.md)
- 目标版本：书 2.0.0；Phase 0 为草稿，不切换线上发布

## 1. 背景与目标

现有仓库同时维护 `docs/` 站点源、641KB 拼接式 README 与一套 A4 离线整书。站点内容、书籍结构和构建器三者耦合：书稿不是一等公民，书籍形态也受站点页面组织限制。

本次把项目整理成《御舆：解码 Agent Harness》式的**书稿优先**仓库：

1. **书稿是唯一内容源**：正文、图、表、练习、来源全部以根目录书稿为准；站点与离线书都是投影。
2. **保留现有站点资产**：61 个旧 URL、1517 条跨页链接、108 张动画、计算器、视频与搜索体验不丢失。
3. **原生书稿构建**：Markdown 直接渲染为单文件 HTML 与 16K PDF，不再从站点 HTML 反向抽取正文。
4. **御舆式书籍部件**：篇章骨架、阅读路线、自绘插图、白话术语层、主题索引、来源台账、图表目录。
5. **按印刷规格推进内容**：19 章最终达到每章 15,000 非空白字符以上，附录 A–H、仿真与实测、索引与封面齐全；首期只做基础设施与第 1 章样章。
6. **分波交付**：Phase 0 验证全链路，之后按波次扩写，避免一次性攒到最后。

## 2. 已确认决策

| 决策 | 结论 |
|---|---|
| 内容源 | 书稿接管为唯一源；`docs/` 不再维护正文 |
| 仓库形态 | 根目录按前置、五篇、附录、后置组织；构建器在 `analog-book/` |
| 构建路线 | 原生重写：Markdown 直出书；站点另由 MkDocs 从同一书稿生成 |
| 站点 URL | 保留现有 61 个旧 URL；manifest 记录每页旧路径 |
| README | 改为书籍门面（封面、简介、阅读路线、目录），不再生成全文拼接版 |
| site-only 页面 | 首页、篇落地页、附录分隔页、动画中心、目录页留在 `site/` 或由 manifest 生成 |
| 书籍部件 | 四组全部纳入：篇章骨架与阅读路线、自绘插图、通俗层、索引与来源台账 |
| 成品形态 | 中文；16K（185×260mm）印刷版 + 单文件 HTML |
| 首期范围 | Phase 0 基础设施 + 第 1 章扩写样章 |
| 授权 | 保持 CC BY-SA 4.0；只借鉴御舆的结构与方法，不复制正文、代码、插图 |

## 3. 非目标

- 不做英文版、双语镜像或上下册拆分。
- 不在 Phase 0 完成其余 18 章扩写；不在 Phase 0 发布 2.0。
- 不改写或重拍现有 108 张动画、20 集视频与 3 套实验数据。
- 不复制参考书的 CSS、Python 代码、SVG 插图或正文；不复用其 CC BY-NC-SA 内容。
- 不做 CMYK 转换、印刷打样、ISBN/条码生成；封面只预留区域。
- 不删除旧 A4 1.0 产物与线上 `/book/`，直到 2.0 稳定版发布。
- 不把 `analog-book/dist/`、`build/`、字体源文件、SPICE 输出或视频产物提交进仓库。

## 4. 内容源与仓库结构

### 4.1 书稿树

```text
前置/
├── 00-前言.md
├── 01-怎样读这本书.md
├── 02-模拟电路简史.md
├── 03-排版术语与引用约定.md
└── 04-符号与单位表.md

第一部分-基础篇/
├── 00-电路直觉.md
└── 01-无源元件的真实面目.md

第二部分-器件篇/
├── 02-二极管.md
├── 03-BJT三极管.md
├── 04-MOSFET.md
├── 05-输出结构.md
├── 06-运算放大器.md
├── 07-比较器.md
├── 08-模拟开关.md
├── 09-基准与稳压.md
└── 10-555定时器.md

第三部分-拓扑篇/
├── 11-放大拓扑.md
├── 12-运放应用族.md
└── 13-电源与信号产生.md

第四部分-设计篇/
├── 14-设计方法论.md
└── 15-PCB设计.md

第五部分-调试篇/
├── 16-排故五步法.md
├── 17-故障模式速查.md
└── 18-大师的排故智慧.md

附录/
├── A-动画与图示索引.md
├── B-公式与设计速查.md
├── C-常用芯片速查/{C1…C5}.md
├── D-视频课程与配套资源/{D1…D11}.md
├── E-学习路线选读与诊断/{E1…E6}.md
├── F-习题答案与综合自测.md
├── G-术语表/{G1…G2}.md
└── H-模型近似与适用边界.md

后置/
├── 版本记录.md
├── 致谢.md
└── 来源与许可.md

site/                       # 站点专属页源（首页、篇落地页、动画中心）与 landing.yml
assets/                     # 现有 SVG、照片、实验、SPICE 资产
analog-book/
├── manifest.json           # schema 2，书稿唯一结构源
├── build_print_book.py     # 新 16K 书入口
├── book/                   # 原生书稿构建器
├── manifest-a4.json        # 冻结的 1.0 清单
├── build_book.py           # 冻结的 A4 1.0 构建器
└── ...
```

- 章号保持 0–18；文件名前缀是排序与检索用，不改变书中章号。
- 附录 C/D/E/G 保留“一个旧页面 = 一个文件”的粒度，书内按附录合并装配；这样旧 URL 与书内附录分组同时成立。
- `docs/superpowers/` 只放设计/计划等工程文档，不进入站点与书。

### 4.2 manifest schema 2

```json
{
  "schema": 2,
  "title": "通往模拟电路之路",
  "subtitle": "从欧姆定律到芯片内部结构",
  "edition": "第一版",
  "version": "2.0.0",
  "source_version": "3.61",
  "date": "2026-10-26",
  "language": "zh-CN",
  "license": "CC BY-SA 4.0",
  "format": {"trim_mm": [185, 260], "bleed_mm": 3},
  "start_reading": "前置/01-怎样读这本书.md",
  "parts": [
    {
      "id": "I",
      "title": "基础",
      "subtitle": "先建立电路直觉",
      "motto": "从一条支路开始",
      "intro": "从电压、电流与功率的基本直觉出发，走向真实器件。",
      "opener_art": "part-i.svg",
      "units": [
        {
          "id": "ch00",
          "file": "第一部分-基础篇/00-电路直觉.md",
          "site_path": "p1-01-ch0.md",
          "site_group": "p1",
          "no": "第 0 章",
          "title": "电路直觉"
        }
      ]
    }
  ],
  "front_matter": [
    {"id": "preface", "file": "前置/00-前言.md", "site_path": "p0-01-preface.md", "title": "前言"}
  ],
  "appendices": [
    {"id": "A", "title": "动画与图示索引", "kind": "generated", "data": "analog-book/data/animations.yml"},
    {"id": "C", "title": "常用芯片速查", "kind": "files", "units": [
      {"id": "C1", "file": "附录/C-常用芯片速查/C1-实物图鉴.md", "site_path": "p6-01-s6-1.md", "site_group": "p6", "title": "实物图鉴"}
    ]}
  ],
  "back_matter": [
    {"id": "changelog", "file": "后置/版本记录.md", "site_path": "p9-12-changelog.md", "title": "版本记录"}
  ],
  "site_only": [
    {"path": "index.md", "kind": "landing", "source": "generated"},
    {"path": "p0-07-toc.md", "kind": "toc", "source": "generated"},
    {"path": "p1-00-part1.md", "kind": "part_landing", "site_group": "p1", "source": "generated"},
    {"path": "p2-00-part2.md", "kind": "part_landing", "site_group": "p2", "source": "generated"},
    {"path": "p3-00-part3.md", "kind": "part_landing", "site_group": "p3", "source": "generated"},
    {"path": "p4-00-part4.md", "kind": "part_landing", "site_group": "p4", "source": "generated"},
    {"path": "p5-00-part5.md", "kind": "animation_center", "source": "site/p5-00-part5.md"},
    {"path": "p6-00-part6.md", "kind": "appendix_divider", "appendix": "C", "source": "generated"},
    {"path": "p7-00-part7.md", "kind": "appendix_divider", "appendix": "D", "source": "generated"},
    {"path": "p8-00-part8.md", "kind": "appendix_divider", "appendix": "E", "source": "generated"}
  ],
  "site_groups": ["p0", "p1", "p2", "p3", "p4", "p5", "p6", "p7", "p8", "p9"],
  "guides": {},
  "release": {"edition_status": "draft", "stable_version": "1.0.0"}
}
```

约束：

- 有源文件的书稿单元必须有且只有一个 `site_path`；生成型附录（如附录 A）只有 `data`，其对应的旧站点页列入 `site_only`。文件组附录（C/D/E/G）在 `units` 内逐文件登记。
- `front_matter` 只登记有源文件的页面；半书名、书名、版权、目录、图表目录由 `pages.py` 生成，不占 manifest 单元。
- 所有站点页面（61 个旧页 + 新增的 `p0-11`、`p0-12`、`p9-15`，共 64 个）必须且只能出现在书稿单元或 `site_only` 中一次。
- `site_only` 固定为 10 页：`index.md`、`p0-07-toc.md`、`p1-00`–`p4-00`、`p5-00`、`p6-00`、`p7-00`、`p8-00`。`source` 为 `generated` 时由 manifest 数据生成，否则指向 `site/` 下的源文件。
- `site_path` 全局唯一；新增前置/附录页（`p0-11`、`p0-12`、`p9-15`）按现有 `site_group` 登记。
- 5 篇恰好覆盖 19 章；章号递增；附录 A–H 连续。
- `guides` 在 `final` 时必须覆盖全部单元；Phase 0 至少填写第 1 章（含问题、交付、边界、来源锚点）。
- `release.edition_status` 为 `draft` 时，内容 DoD 只做机制校验；`final` 时全部硬门禁。Phase 0 固定 `draft`，不得用 skip 掩盖失败。

### 4.3 站点投影

- `scripts/build_site.py` 改为读 manifest：按 `site_path` 生成 MkDocs 源 `build/docs/`，再由 MkDocs 输出 `build/site/`；旧 URL 完全不变。
- 站点导航仍按 `site_group`（p0–p9）分组，不改成书的五篇；书与站点共享正文，不共享导航。
- 书稿中的跨页链接一律写“新书稿相对路径”；站点构建时通过 manifest 映射回旧 URL，书构建时解析为书内锚点。
- 正文不直接链接 `site_only` 页面；需要引用时改指书内等价目标（如附录 A/D），站点侧再由映射回旧 URL。
- 资源路径统一写指向根 `assets/` 的相对路径（章节目录用 `../assets/...`，二级附录目录用 `../../assets/...`）；站点构建复制并改写为站点根路径，书构建内联为 data URI。
- `site_only` 的 `source: site/...` 页面由站点构建读取；`generated` 页面由 manifest 与 `site/landing.yml` 生成。它们不进入书。
- 站点继续保留 Material 搜索、108 张动画、计算器、视频、深浅色与移动端体验。

### 4.4 README 与站点首页

- 根 `README.md` 由 manifest 生成书籍门面：封面、书名/副标题、简介、三条阅读路线、篇/章目录、获取方式、构建与贡献入口。
- README 封面使用仓库内的 `assets/cover-preview.png`（源资产）；印刷封面 PDF 与预览仍由构建生成，不提交 `dist/`。
- 不再生成 641KB 全文拼接 README；全文以章节文件、在线站点、单文件 HTML 与 PDF 为准。
- 站点 `index.md` 与 README 共用 `site/landing.yml`（简介、路线、徽章、获取方式），避免两处维护。
- 旧 `build_readme.py` 的“docs 拼接/同步”契约由“manifest + landing.yml → README/landing”契约取代。

## 5. 原生书稿构建器

### 5.1 包结构

```text
analog-book/book/
├── __init__.py
├── core.py        # manifest、Unit、路径、UTF-8、配置校验
├── render.py      # Markdown → HTML、锚点、表格、代码、脚注
├── math.py        # MathJax v3 预算 SVG + 缓存键
├── figures.py     # 图/表编号、图注、图表目录数据
├── transforms.py  # 去 emoji、提示框、答案拆分、计算器替身、视频改写
├── pages.py       # 封面、版权、目录、图表目录、篇首页、罗盘、来源页、索引
├── plain.py       # 导读带、术语白话、tier 徽、原理札记
├── art.py         # SVG 插图装载与安全校验
├── style.py       # 屏幕样式 + 16K 印刷样式 + 装饰矢量
├── fonts.py       # 子集字体、缺字检查
├── pdf.py         # Chromium 打印 + PyMuPDF 后处理
└── audit.py       # 落盘前 HTML 契约
analog-book/build_print_book.py   # CLI
```

### 5.2 渲染管线

1. 读 manifest，校验覆盖率、文件存在、`site_path` 唯一。
2. 读 Markdown，按标题层级映射：章标题 → `h1`；编号节与未编号的章内节（如“配套视频”）→ `h2`；编号小节 → `h3`；缺 id 的标题分配确定性 id。
3. python-markdown（`extra`、`sane_lists`、`toc`、`codehilite`、`md_in_html`、`footnotes`）渲染；原始 HTML 保留。
4. MathJax 预算：`$...$` / `$$...$$` 转 SVG，按“配色指纹 + MathJax 版本 + 源文本”缓存；失败即构建失败。
5. 书内转换：
   - 去装饰性 emoji（含正文、标题、表格与内联 SVG 文本）；`✅/❌/⚠️` → `✓/✗/注意`。
   - 引用块按语义转为“先修 / 学完你应能 / 公式速查 / 模型边界”标签框。
   - 第 1 章样章：`<details>` 答案移入附录 F，题目留在章末；其余草稿章节先把 `<details>` 渲染为静态“答案”块，拆分随该章扩写波次完成。
   - `.calc` 保留默认读数、公式与算例，删除输入控件与按钮。
   - 视频块与 `data-study-video` 链接改写为“视频 D-xx（见附录 D）”。
   - 图片内联为 data URI；动画改用静态帧/静止 SVG。
   - 站内链接改为书内交叉引用；外链转章末尾注。
6. 图/表编号与图注、表注；生成 `figures.yml` / `tables.yml` 只读产物。
7. 单元装配、目录/图表目录/索引条目、篇首页、后置页。
8. 落盘前审计：锚点唯一可达、无残留围栏/占位符、无远程资源、无 script、图表数量与登记一致、术语标记数与面板一致。

### 5.3 书籍部件

- **篇章骨架**：5 张篇首页（罗马篇号、篇名、副标题、导语、章清单、题刻）；19 枚章徽；章首罗盘（本章问题 / 读完交付 / 本章边界 / 来源锚点）；章末收束装饰。`guides` 未登记的草稿单元不出罗盘，`final` 时必须齐全。
- **阅读路线**：manifest 的 `start_reading` + `reading-paths.json`（按 H2 位置标 `start/core/deep`）；`plain.py` 盖 tier 徽；书前给三条路线。Phase 0 只覆盖第 1 章，未登记单元不盖徽；`final` 时必须全覆盖。
- **自绘插图**：扉页图版、5 幅篇题刻、19 枚章徽、章末装饰；全部原创 SVG、`currentColor` 描线、无 id/href/url/script/style，单枚体积上限；装载器拒绝不合规文件。
- **通俗层**：`glosses.json` 每条含 `term/forms/plain/why/analogy/evidence/priority`；正文首现术语画虚线，屏幕悬停浮窗，纸面退回章首“新词”面板；书末“原理札记”按章收拢 `why`。
- **索引与来源**：`index-terms.yml` 300–400 条（Phase 0 种子 40 条）；`sources.yml` 逐条登记；`chapter-signoff.yml` 记录 19 章审读状态（Phase 0 仅第 1 章自检，审读者留空）；`references.yml` 由各章“延伸阅读”合并去重。
- **目录与后置**：详细目录、图目录、表目录、主题索引、参考文献、版本记录、致谢、来源与许可、版本页。
- **封面**：内文补白后按页数计算书脊；前封/书脊/后封；3mm 出血、裁切线；预留 ISBN 区域但不填假号。

### 5.4 16K 成品

- 185×260mm；版心 145×218mm；镜像版心优先，Chromium 不支持时退回统一边距并在 `PRINT-SPEC.md` 记录。
- 正文思源宋体 10.5/17.5pt；标题思源黑体；代码 JetBrains Mono 8.5/12pt；字体全部子集化并内联。
- 前置罗马页码，正文/附录/索引阿拉伯页码；篇首页、章首页、版权页、空白页不排页眉页脚。
- PDF：三级书签、目录/图表目录/索引页码回填（固定 3 位 `000` 占位后覆盖）、正式书补白到 4 的倍数、元数据、字体嵌入检查。
- 页数：扩写完成后目标 535–653 页，硬区间 450–700；Phase 0 只记录，不据此失败。
- 产物：`analog-circuit-book.html`、`analog-circuit-book-16k.pdf`、`cover.pdf`、`cover-preview.png`、`PRINT-SPEC.md`、构建报告。
- 体积：HTML 目标 <60MB、硬上限 80MB；PDF <100MB；超限报告最大资源并失败。

### 5.5 旧 A4 1.0

- `analog-book/build_book.py` 与 `manifest-a4.json` 冻结：A4 构建器的 `MANIFEST_PATH` 改指 `manifest-a4.json`，正文仍从新 `build_site.py` 生成的 `build/site` 旧页面读取。
- 修订（2026-11-10，spec owner 批准）：A4 HTML 体积上限 20→24 MB。V4/V2 图 wave 合并入正文后整书实测 21.46MB，超原上限 1.46MB；构建器与 manifest 其余冻结内容不变，A4 仍不取 16K 线的 60/80MB。
- 线上 `/book/`、Pages 与镜像继续发布 A4 1.0；新 16K 书在 Phase 0 只上传 CI artifact。
- 2.0 稳定版发布时再切换 `/book/`，删除或归档 A4 管线。

## 6. 迁移

### 6.1 页面归宿

| 旧页面 | 新位置 | 处理 |
|---|---|---|
| `index.md` | `site/` | 站点首页，生成 |
| `p0-01` | `前置/00-前言.md` | 扩写 |
| `p0-02` | `前置/01-怎样读这本书.md` | 扩写 |
| `p0-03` | `前置/02-模拟电路简史.md` | 扩写 |
| `p0-04` | `附录/E/…/E1-按需求选电路.md` | 收录 |
| `p0-05` | `附录/E/…/E2-精选路线.md` | 收录 |
| `p0-06` | `附录/E/…/E3-学习路线图.md` | 收录 |
| `p0-07` | `site/` | 站点目录，生成 |
| `p0-08` | `附录/B-公式与设计速查.md` | 重排两栏 |
| `p0-09` | `附录/E/…/E4-自诊断.md` | 收录 |
| `p0-10` | `附录/H-模型近似与适用边界.md` | 收录 |
| `p0-11` | `前置/03-排版术语与引用约定.md` | 新增 |
| `p0-12` | `前置/04-符号与单位表.md` | 新增 |
| `p1-00` | `site/` | 篇落地页，生成 |
| `p1-01-ch0` | `第一部分-基础篇/00-电路直觉.md` | 扩写 |
| `p1-02-ch1` | `第一部分-基础篇/01-无源元件的真实面目.md` | 样章扩写 |
| `p1-03-ch2`…`p1-11-ch10` | `第二部分-器件篇/02…10-*.md` | 扩写 |
| `p2-00` | `site/` | 篇落地页，生成 |
| `p2-01-ch11`…`p2-03-ch13` | `第三部分-拓扑篇/11…13-*.md` | 扩写 |
| `p3-00` | `site/` | 篇落地页，生成 |
| `p3-01-ch14`…`p3-02-ch15` | `第四部分-设计篇/14…15-*.md` | 扩写 |
| `p4-00` | `site/` | 篇落地页，生成 |
| `p4-01-ch16`…`p4-03-ch18` | `第五部分-调试篇/16…18-*.md` | 扩写 |
| `p5-00` | `site/` + `data/animations.yml` | 站点动画中心；书附录 A 由数据生成 |
| `p6-00` | `site/` | 附录分隔页，生成 |
| `p6-01`…`p6-05` | `附录/C-常用芯片速查/C1…C5.md` | 收录 |
| `p7-00` | `site/` | 附录分隔页，生成 |
| `p7-01`…`p7-03`、`p8-02`…`p8-09` | `附录/D-视频课程与配套资源/D1…D11.md` | 合并去重 |
| `p8-00` | `site/` | 附录分隔页，生成 |
| `p8-01` | `附录/E/…/E5-分阶段路线.md` | 收录 |
| `p8-10` | `附录/G-术语表/G2-黑话速查.md` | 收录 |
| `p8-11` | `附录/E/…/E6-19章总表.md` | 收录 |
| `p9-00` | `附录/F-习题答案与综合自测.md` | Phase 0 整页作为附录 F 草稿；第 1 章题目/答案按样章拆分，其余章节随扩写波次拆分 |
| `p9-12` | `后置/版本记录.md` | 收录 |
| `p9-13` | `后置/致谢.md` | 收录 |
| `p9-14` | `后置/来源与许可.md` | 收录 |
| `p9-15` | `附录/G-术语表/G1-术语表.md` | 新增 |

### 6.2 链接与资源迁移

- 迁移脚本读 manifest，按页面映射把 1517 条 `.md` 链接改写成新书稿相对路径。
- 248 处图片引用（以原始 `<img>` 为主）统一改为指向根 `assets/` 的相对路径；站点构建时再改写为站点根路径。
- 指向站点专属页的链接按语义改指书内目标（如 `p5-00#demoN` → 附录 A `#demoN`）；站点侧再由映射回旧 URL。
- 迁移后做三向校验：
  1. 书稿内每条链接都能在书内解析；
  2. 站点输出每条旧链接都能解析；
  3. 旧 URL → 新书稿 → 旧 URL 回环一致。
- 逐页统计非空白字符数，除第 1 章扩写外，迁移前后不得减少；差异需人工确认。

### 6.3 迁移方式

- 在分支上执行；使用 `git mv` 保留文件历史。
- Phase 0 完成迁移后删除 `docs/` 内容页，只保留 `docs/superpowers/` 工程文档。
- 旧 A4 管线改指 `manifest-a4.json`，正文经新站点构建读取，保证迁移期间仍可构建 A4 1.0。
- 所有迁移动作由脚本完成，脚本与校验测试入库。

## 7. Phase 0 样章

### 7.1 第 1 章扩写范围

第 1 章按旧规格同一口径（非空白字符，不含 HTML/SVG/Math 标记）从约 11.7k 扩到 18k，按印刷规格 §6.5 执行：

- 保留 1.1–1.7；新增 1.8 电阻噪声与热噪声、1.9 电容阻抗/自谐振/去耦、1.10 电感饱和/直流偏置/磁芯损耗、1.11 降额与选型矩阵、1.12 RC 实测完整版。
- 3 个完整算例：戴维南等效与最大功率、RC 截止频率与上升时间、电容自谐振与去耦。
- 1 个可运行仿真：`assets/spice/ch01/rc.cir` + `assert.json`（fc、tr、增益）。
- RC 实测：现有 `assets/labs/rc/` 的目标、原理图、BOM、仪器与接线、步骤、`measurements.csv` 数据图、`reference.csv` 对比、误差来源。
- 3 个“工程师视角”、3 条误区/失败案例、8–12 题（概念/手算/设计/排故/仿真）、6–8 条延伸阅读、≥4 个编号图表。
- 章末速查卡、本章小结、下一步。

### 7.2 数据种子

- `glosses.json`：第 1 章与前置的 ~12 条 core/extra 术语，含 `plain/why/analogy/evidence`。
- `reading-paths.json`：第 1 章 13 个 H2 位置（12 个编号节 + 配套视频）的 tier 位置表。
- `index-terms.yml`：~40 条词条，锚点必须可解析。
- `sources.yml`：~10 条来源（数据手册、教材、实验 CSV、仿真 deck）。
- `references.yml`：第 1 章 7 条延伸阅读。
- `chapter-signoff.yml`：19 章各一条；第 1 章记录自检与待审状态，审读者字段留空直到真实审读，不伪造非作者签字；其余 `draft`、`open_issues` 非空。
- `animations.yml`：108 条动画索引骨架；第 1 章至少 1 条完整。Phase 0 允许字段不全，但条数与 19 章覆盖必须过校验。
- 自绘插图：扉页图版、5 幅篇题刻、19 枚章徽、第 1 章章末装饰。

### 7.3 产物

- `sample-16k.pdf`：前置 + 第一篇（第 0 章 + 扩写后的第 1 章）+ 附录/后置样页。
- `draft-full-16k.pdf`：全部单元按现有内容 + 第 1 章扩写，验证装配、目录、索引回填、页数与书脊。
- 单文件 HTML、封面 PDF、封面预览、`PRINT-SPEC.md`、构建报告。
- 站点仍按旧 URL 发布；第 1 章扩写同步出现在站点。

## 8. 内容扩写波次

Phase 0 之后：

| 波次 | 章节 | 重点 |
|---|---|---|
| Wave 1 | 第 0、2、11、14、16 章 | 基础/器件/拓扑/设计/调试各一章，跑通全链路 |
| Wave 2 | 第 3、12、15、17 章 | BJT、运放应用、PCB、故障表 |
| Wave 3 | 第 4、6、13、18 章 | MOSFET 实验、LM358 实验、电源、大师智慧 |
| Wave 4 | 第 5、7、8、9、10 章 | 输出结构、比较器、模拟开关、基准、555 |
| Phase 5 | 附录 A–H、索引、术语、参考文献、封面、总校 | 收口与 2.0 发布 |

每波门禁：

1. 内容 DoD：字数、散文占比、进阶框、误区、算例、仿真、练习、延伸阅读、图表。
2. 数据：仿真 deck 全过；来源台账完整；章节签字 `open_issues` 为空。
3. 印刷：16K 样张无溢出；图表编号/来源齐全；表格不超过 6 列。
4. 回归：站点旧 URL、搜索、动画、计算器、视频全绿；书 HTML/PDF 契约全绿。
5. 发布：扩写期只更新站点与 CI artifact；2.0 收口后才切换 `/book/`。

## 9. 测试与 CI

### 9.1 内容与结构

- manifest：schema 2；5 篇覆盖 19 章；附录 A–H；64 个站点页面覆盖对账；`site_path` 唯一。
- 迁移：逐页字符数对账；书内链接、站点链接、回环链接三向校验。
- 内容 DoD：Phase 0 只对第 1 章硬校验；其余章节 `draft` 只校验机制。
- 禁止项：`TODO/TBD/待补/占位`；书内 emoji；远程图片/iframe/video。

### 9.2 书构建

- HTML 契约：锚点唯一、无残留围栏/占位符、无 script、资源内联、图表数量、术语标记数与面板一致。
- Math：公式全部转 SVG；无 `$$` 残留；缓存键正确。
- 数据：glosses/reading-paths/index/sources/references/animations/chapter-signoff 的 schema 与引用完整性；白话证据 `file:line` 落在正文散文。
- 插图：25 份齐全、体积上限、无 id/href/url/script/style、全部 `currentColor`。

### 9.3 PDF 与封面

- 正式书与 `draft-full-16k.pdf` 页面 185×260mm、补白到 4 的倍数；样章 PDF 不强制补白。
- 页数在 450–700 硬区间（Phase 0 只记录、不失败）。
- 字体全部嵌入、无缺字；三级书签；罗马/阿拉伯页码；目录/图目录/表目录/索引页码一致。
- 篇首页、章首页、版权页、空白页无页眉页脚；文字不越出版心。
- 封面尺寸、出血、裁切线、书脊误差 <0.5mm；无假 ISBN/条码。

### 9.4 站点回归

- 61 个旧 URL 与 3 个新增页全部存在；`test_docs_links`、`test_readme_links`、`test_first_screen`、`test_site_build`、`test_release_gate` 等现有测试更新后全绿。
- 动画中心、108 张动画、8 个计算器、6 个视频块、搜索、移动端 390×844 无回归。
- README/landing 的目录链接可达。

### 9.5 CI

- PR：站点构建 + manifest/迁移/内容测试 + 书 HTML 构建与审计；不强制 PDF。
- main/manual：全套 + 16K 样例/草稿 PDF + 封面 + PDF 测试 + artifact（14 天）。
- 旧 A4 1.0：保留构建与发布测试，确保迁移期间不断线。
- CI 不允许用 skip 掩盖 Math、字体、来源或内容的失败。

## 10. 风险与缓解

| 风险 | 缓解 |
|---|---|
| 1517 条链接迁移出错 | 自动改写 + 三向校验 + 逐页字符对账；分支验证后再合并 |
| 原生渲染破坏现有交互 | 原始 HTML 原样保留；站点仍走 MkDocs；浏览器回归覆盖动画/计算器/视频 |
| Math 兼容性 | MathJax SVG 预算 + 缓存；样章覆盖第 0/1 章全部公式；失败即构建失败 |
| 参考书授权 | 只借鉴结构与方法；代码、CSS、SVG、正文全部自行实现；保留 CC BY-SA |
| Phase 0 范围膨胀 | 只扩写第 1 章；其余章节 `draft`；最终门禁不在草稿上假装通过 |
| 16K 版心/分页不稳定 | Phase 0 出样张；Chromium 不支持镜像版心时退回统一边距并记录 |
| 字体/体积超限 | 子集字体 + 资源去重 + 体积审计；HTML 60/80MB、PDF 100MB 上限 |
| 站点与书双渲染分叉 | 同一书稿、同一链接/资源解析器；成品层测试各自覆盖 |
| 旧 A4 断线 | 冻结 manifest-a4 与构建器；迁移期继续发布 A4 1.0 |
| 扩写注水 | 逐章蓝图 + 散文占比 + 算例/仿真/图表硬指标 + 抽样复审 |

## 11. 交付物清单

Phase 0：

```text
书稿树（前置/五篇/附录/后置）
site/（站点专属页、landing.yml 与模板）
README.md（由 manifest + landing.yml 重建）
assets/cover-preview.png（README 门面图，源资产）
docs/（仅保留 superpowers；内容页迁移后删除）
analog-book/manifest.json（schema 2）
analog-book/manifest-a4.json（冻结）
analog-book/build_print_book.py
analog-book/book/（全部模块）
analog-book/styles/（屏幕 + 16K 印刷）
analog-book/fonts/（子集 WOFF2 + 许可证）
analog-book/cover/（印刷封面 HTML/CSS、书脊计算与预览）
analog-book/illustrations/（扉页图版 + 5 篇题刻 + 19 章徽）
analog-book/data/（animations/index-terms/references/sources/chapter-signoff）
analog-book/glosses.json
analog-book/reading-paths.json
analog-book/revisions.json
analog-book/STYLE.md
analog-book/PRINT-SPEC.md
analog-book/tests/（迁移、manifest、内容、渲染、math、figures、plain、art、pdf、cover、站点回归）
scripts/build_site.py（读书稿、旧 URL 投影）
scripts/build_readme.py（书籍门面）
scripts/migrate_to_book.py（一次性迁移）
analog-book/README.md、CONTRIBUTING.md、Makefile（构建入口更新）
.github/workflows/（站点回归、书构建、16K artifact；A4 发布保留）
assets/spice/ch01/rc.cir + assert.json
前置/03-排版术语与引用约定.md
前置/04-符号与单位表.md
附录/G-术语表/G1-术语表.md
```

不提交：`analog-book/dist/`、`build/`、字体源文件、SPICE 运行输出、视频渲染产物。

## 12. 与旧印刷版规格的关系

- [16K 印刷版设计](2026-10-25-print-book-design.md) 的内容目标、章节模板、DoD、逐章蓝图、版式、印前检查继续有效。
- 本规格取代其第 9 节工程架构中与“docs/ 唯一源、不重命名、不搬家、从站点 HTML 抽取”相关的约束。
- 旧规格的附录 A–H 结构、页面归宿表、字体/色彩/封面参数、验收清单继续作为本书的基线。
- 两者的冲突以本规格为准；内容深度冲突以更严格者为准。

## 13. 验收清单

- [ ] 书稿树、manifest、site-only 页面与旧 URL 对账通过；64 个站点页面（61 旧 + 3 新增）无遗漏、无重复。
- [ ] 站点 61 个旧 URL 与 3 个新增页全部可达；1517 条链接、108 张动画、8 个计算器、6 个视频块无回归。
- [ ] 原生书构建器可产出单文件 HTML、16K 样章 PDF、16K 草稿 PDF、封面 PDF 与预览。
- [ ] 第 1 章达到 18k 非空白字符与全部 DoD；仿真断言通过；RC 实测进书；习题/答案/延伸阅读齐全。
- [ ] 篇章骨架、阅读路线、自绘插图、白话层、索引、来源台账在样章中全部可见。
- [ ] 目录/图目录/表目录/索引页码与链接目标一致；三级书签、页码标签、页眉页脚正确。
- [ ] 字体全部嵌入；封面书脊与最终页数一致；无假 ISBN/条码。
- [ ] HTML <60MB（硬上限 80MB）；PDF <100MB；正式书与草稿 PDF 补白到 4 的倍数。
- [ ] 旧 A4 1.0 仍可构建与发布；扩写期 `/book/` 不被 16K 草稿覆盖。
- [ ] README/站点首页改为书籍门面；旧全文拼接 README 的测试契约已更新。
- [ ] 仓库不提交构建产物、字体源文件、SPICE 输出与视频产物。
- [ ] 无伪造实测数据、文献、DOI、厂商图片、审读签字；参考书的正文/代码/插图未被复制。
