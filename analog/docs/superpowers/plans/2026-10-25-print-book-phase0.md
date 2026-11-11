# 16K 印刷书 Phase 0 基础设施实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在不破坏现有线上书的前提下，搭好 16K 印刷书的 manifest、字体、样张、内容转换、数据校验、装配、PDF、封面与仿真骨架，并让新的 `analog-book/build_print_book.py` 独立产出 77 个逻辑页的 16K 草稿书；16K 在 Phase 0 只作为 CI artifact，`/book/` 继续发布 A4 1.0。

**Architecture:** 把 16K 构建拆成 `analog-book/book/` 包：`config`、`manifest`、`content`、`data`、`frontmatter`、`assemble`、`pdf`、`cover`、`fonts`、`sample`、`report`、`cli`。新模块先在夹具目录上以 TDD 建起来；旧 A4 管线、旧测试与冻结的 `manifest-a4.json` 保持可运行并继续服务 Pages。Task 11 并行接入 16K 管线、schema-2 `manifest.json` 和三张新前置/附录页。所有最终内容门禁（每章字数、练习、图表编号、300 条索引、19 个 deck、450–700 页）由 `release.edition_status` 控制，Phase 0 只验证机制。

**Tech Stack:** Python 3.12、PyYAML、pypinyin、fontTools + brotli、Playwright Chromium、PyMuPDF、matplotlib、ngspice、MkDocs Material（既有站点构建）。

**Spec:** `docs/superpowers/specs/2026-10-25-print-book-design.md`

## Global Constraints

- `docs/` 是唯一内容源；书和站点都从 `docs/` 经 `scripts/build_site.py --build` 生成的 HTML 取内容，不直接渲染 Markdown。
- 不伪造实测数据、文献、DOI、厂商图片或“某实验室数据”；实测只允许现有 RC、LM358、MOSFET 三套实验。
- 构建输出只写 `build/`、`analog-book/dist/` 或临时目录；不提交 `analog-book/dist/`、`build/`、字体源文件、SPICE 运行输出。
- 根 `README.md` 只由 `scripts/build_readme.py` 重建，不手改。
- `.github/workflows/pages.yml` 的 job 图（`tests`、`links`、`book`）在 Phase 0 保持不变；`scripts/test_release_gate.py` 是这条约束的守门测试。
- 扩写期 `/book/` 继续发布 A4 1.0：`pages.yml` 仍下载 `analog-circuit-book` 并调用 `publish_a4_book.py`；16K 只上传为 CI artifact `analog-circuit-book-16k-draft`，不得进入 Pages 部署产物。站点印刷版入口、README 与 `/book/` 切换统一留到 Phase 5。
- Phase 0 的 `manifest.release.edition_status` 固定为 `draft`；最终内容门禁不得在草稿上假装通过，也不得用 `skip` 掩盖。最终门禁的夹具测试从 Task 6 开始建立，真实内容断言在后续内容波次计划中启用。
- 新代码用 UTF-8、`pathlib.Path`、`unittest`；不新增运行时依赖，依赖只加到 `analog-book/requirements.txt` 或根 `requirements.txt`，并同步 CI。
- 书内输出不得含 emoji、远程图片、iframe、video；外部链接转本章尾注，站内链接转书内锚点。
- 字体只提交按实际字符集子集化的 WOFF2、`BookSans-Stamp.ttf` 与 OFL 许可证；源字体下载到 `build/fonts-src/`，不入库。
- 不提交 `docs/superpowers/specs/2026-10-25-print-book-design.md` 与本计划，除非用户明确要求。
- 测试必须在仓库根目录运行；测试文件把 `analog-book` 插入 `sys.path` 后 `from book...` 导入。CI 用 Linux，开发机用 Windows Git Bash，路径一律用 `pathlib`。

## Scope And Deferred Gates

Phase 0 交付：

- schema-2 manifest 模型、覆盖校验、77 个逻辑页描述。
- 五套 OFL 子集字体（正文宋体常规/粗体、标题黑体常规/粗体、等宽常规）与印章字体。
- 16K 打印样式和 10 页样张 PDF，验证版心、镜像边距回退、表格/代码/公式/索引不溢出。
- 内容抽取、链接改写、emoji 清理、语义提示卡、图表编号、尾注、来源标记、计算器印刷替身检查。
- `animations.yml`（108 条）、`chapter-signoff.yml`（19 条）、`index-terms.yml` 初始种子、空的 `sources.yml`/`references.yml` 与 schema 校验。
- 前置/后置页面渲染、两级目录/图表目录/索引占位、77 页装配、HTML 审计、构建模型 JSON。
- 16K PDF：探测链接、三级书签、罗马/阿拉伯页码标签、目录/索引 `000` 回填、页眉页脚、补白到 4 的倍数。
- 封面生成：书脊公式、出血、裁切线、正/背/书脊、预览 PNG。
- 一个可运行的 ngspice 第 1 章 RC deck、断言、批处理 runner 和 SVG 绘图骨架。
- 并行接入提交：新增 `p0-11`、`p0-12`、`p9-15`，schema-2 manifest，站点附录导航，16K CLI，A4 测试保留并新增 16K 测试与 CI job。

明确推迟到后续计划（不得在 Phase 0 用假数据或跳过冒充完成）：

- 19 章逐章扩写、字数/散文占比、3 个进阶框、3 条失败案例、3 个算例、8–12 题、6–8 条延伸阅读、每章 ≥4 个编号图表。
- 每章练习与附录 F 的题目/答案拆分、题库 34 题重排。
- 300–400 条索引、150–250 条术语、100+ 符号、≥100 条去重参考文献、`sources.yml` 全量来源覆盖与审读签字。
- 19 个 ngspice deck 与对应仿真图、三套实测 CSV 的误差分析图。
- 附录 A–H 的专属版式与最终结构：A 的 24 张关键帧、B 两栏速查、D 合并去重、E 三段路线、G 拼音合并与 150–250 条术语；Phase 0 只装配源页与 108 行动画总表，不把占位当定稿。
- PDF 印前全检：字体嵌入、缺字 `�`、公式矢量、版心 2mm、表格/代码横向溢出、图表跨页、元数据与 PDF <100MB；Phase 0 只检查 16K 结构项，并在草稿报告里明示未做印前全检。
- 公式 >2000、535–653 页目标与 300–400 条索引等最终数量门禁继续由 `edition_status=final` 控制；Phase 0 只建 schema、种子与草稿阈值。
- 450–700 页硬区间、535–653 页目标区间、最终 2.0.0 发布与 pages 发布节奏切换。
- 站点印刷版入口、README 的 16K 文案、`/book/` 从 A4 1.0 切换到 16K、2.0 稳定版发布。

## File Structure

新建：

```text
analog-book/book/__init__.py
analog-book/book/config.py              # 路径、尺寸、字节上限、文件名
analog-book/book/manifest.py            # schema 2 校验、页面模型
analog-book/book/fonts.py               # 必需字符集、font-face CSS、印章字体
analog-book/book/content.py             # 抽取、标题、锚点、链接、图片、表格
analog-book/book/transforms.py          # 去 emoji、展开折叠块、提示框、图表编号、尾注、计算器校验
analog-book/book/quiz.py                # 题库拆分：章末练习 + 附录 F 答案
analog-book/book/data.py                # YAML schema、动画/索引/来源/签字/参考文献
analog-book/book/frontmatter.py         # 半书名/书名/版权/目录/图表目录/索引/后置
analog-book/book/assemble.py            # 77 页装配、资源内联、审计、模型、figures.yml/tables.yml
analog-book/book/pdf.py                 # 16K 打印、探测、书签、页码回填、页眉页脚
analog-book/book/cover.py               # 书脊、封面 HTML/PDF/预览
analog-book/book/sample.py              # 10 页 16K 样张
analog-book/book/report.py              # 构建报告与 PRINT-SPEC.md
analog-book/book/cli.py                 # 16K 构建实现入口
analog-book/build_print_book.py         # 16K 薄入口
analog-book/manifest-a4.json            # 1.0 A4 的冻结 manifest（Phase 5 删除）
analog-book/styles/print.css            # 16K 版式
analog-book/cover/cover.css             # 封面版式
analog-book/fonts/                      # 5 个 WOFF2 + BookSans-Stamp.ttf + OFL + sources.json
analog-book/data/animations.yml
analog-book/data/index-terms.yml
analog-book/data/references.yml
analog-book/data/sources.yml
analog-book/data/chapter-signoff.yml
analog-book/STYLE.md
analog-book/tests/book_fixtures.py
analog-book/tests/test_book_manifest.py
analog-book/tests/test_book_fonts.py
analog-book/tests/test_book_sample.py
analog-book/tests/test_book_content.py
analog-book/tests/test_book_figures.py
analog-book/tests/test_book_quiz.py
analog-book/tests/test_book_data.py
analog-book/tests/test_book_build.py
analog-book/tests/test_book_pdf.py
analog-book/tests/test_book_cover.py
analog-book/tests/test_book_real.py
analog-book/tests/test_book_report.py
analog-book/tests/test_browser_print_book.py
analog-book/tests/test_spice.py
scripts/subset_fonts.py
scripts/build_book_data.py
scripts/run_spice.py
scripts/plot_sim.py
scripts/publish_a4_book.py              # 由 scripts/publish_book.py 改名
scripts/test_publish_a4_book.py         # 由 scripts/test_publish_book.py 改名
assets/spice/ch01/rc.cir
assets/spice/ch01/assert.json
assets/spice/ch01/README.md
docs/p0-11-conventions.md
docs/p0-12-symbols.md
docs/p9-15-glossary.md
.github/workflows/book-print.yml        # 16K 草稿工作流，独立于 Pages
```

修改：

```text
analog-book/build_book.py               # 1.0 A4 构建器；Task 11 只改 MANIFEST_PATH
analog-book/manifest.json               # Task 11 升到 schema 2（16K）
analog-book/styles/book.css             # Task 7 增补屏幕样式；保留 A4 @page 给 1.0
analog-book/requirements.txt            # fonttools/brotli/PyYAML/matplotlib/pypinyin
scripts/build_site.py                   # Task 11 APPENDIX 加入 p9-15
scripts/test_site_build.py              # Task 11 附录导航断言
scripts/publish_book.py                 # Task 12 改为 16K 发布入口（Phase 5 才接入 Pages）
scripts/test_publish_book.py            # Task 12 16K 发布测试
scripts/test_release_gate.py            # Task 12 守住 A4 在线、16K 不进 Pages 的边界
.github/workflows/pages.yml             # 只把发布命令改名为 publish_a4_book.py
.github/workflows/tests.yml             # Task 12 只把 A4 发布器测试换名
Makefile                                # Task 12 的 test-static 跑两个发布器测试
README.md                               # Task 11 由 scripts/build_readme.py 重建
CONTRIBUTING.md                         # Task 11 补两个 manifest 的贡献说明
analog-book/README.md                   # Task 11 补 16K 入口与 A4 冻结说明
analog-book/READING-FLOW.md             # Task 12 把 A4 发布器改名写清楚
```

任务顺序是刻意的：Task 1–10 只新增模块、测试与 SPICE 资产，旧 A4 构建器、旧 manifest 与 `docs/` 都不动；Task 11 并行接入 16K，同时把 A4 manifest 冻结为 `manifest-a4.json`，线上书继续由旧管线生成。Phase 5 才删除 A4 管线并把 `/book/` 切到 16K。

> 遗留测试想法（来自 2026-10-27 会话丢失的本地草稿，恢复于此）：`test_book_assemble` 应补一条 **copy 后 page stem 唯一性** 检查——`assemble` 把源页复制进整书目录时，若两个不同路径的源页产生相同 stem（附录装配页与正文章重名是典型风险），后者会静默覆盖前者；夹具里放两个同 stem 源页、断言构建报错而不是静默丢页。Phase 5 附录定稿（A–H 装配页批量上线）前必须先有这条护栏。

---

### Task 1: schema-2 manifest 模型、覆盖校验与测试夹具

**Files:**
- Create: `analog-book/book/__init__.py`
- Create: `analog-book/book/config.py`
- Create: `analog-book/book/manifest.py`
- Create: `analog-book/tests/book_fixtures.py`
- Create: `analog-book/tests/test_book_manifest.py`

**Interfaces:**
- Produces: `BookError`、`load_manifest(path=MANIFEST_PATH) -> dict`、`manifest_sha256(path=MANIFEST_PATH) -> str`、`validate_manifest(manifest, docs_dir=DOCS) -> None`、`direct_files(manifest) -> list[str]`、`excluded_files(manifest) -> list[str]`、`book_pages(manifest) -> list[dict]`。
- Page dict keys: `kind`、`stem`、`title`、`file`、`part_id`、`part_title`、`unit_title`、`appendix_id`、`transform`、`generated`。
- Produces fixture helpers: `manifest() -> dict`、`write_docs(docs_dir) -> None`、`write_site(site_dir) -> Path`、`write_data(data_dir) -> Path`、`direct_files(manifest) -> list[str]`。三个 write_* 的参数都是最终目录，不再追加 `site/` 或 `data/` 子目录。

- [ ] **Step 1: 写失败测试**

Create `analog-book/tests/test_book_manifest.py`:

```python
#!/usr/bin/env python3
"""schema-2 manifest 必须覆盖每一页 docs，并给出 77 个逻辑页。"""
import sys
import tempfile
import unittest
from pathlib import Path

BOOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BOOK))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from book.manifest import (BookError, book_pages, direct_files,  # noqa: E402
                           excluded_files, validate_manifest)
import book_fixtures  # noqa: E402


class ManifestTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.docs = self.root / "docs"
        self.manifest = book_fixtures.manifest()
        book_fixtures.write_docs(self.docs)

    def problems(self, manifest=None):
        try:
            validate_manifest(manifest or self.manifest, self.docs)
        except BookError as exc:
            return str(exc)
        return ""

    def test_accepts_complete_schema_2_manifest(self):
        validate_manifest(self.manifest, self.docs)
        self.assertEqual(54, len(direct_files(self.manifest)))
        self.assertEqual(10, len(excluded_files(self.manifest)))
        self.assertEqual(64, len(direct_files(self.manifest)) + len(excluded_files(self.manifest)))

    def test_book_pages_are_77_and_ordered(self):
        pages = book_pages(self.manifest)
        self.assertEqual(77, len(pages))
        self.assertEqual(
            ["half-title", "title-page", "copyright", "p0-01-preface",
             "p0-02-how-to-use", "p0-03-timeline", "p0-11-conventions",
             "p0-12-symbols", "toc", "list-of-figures", "list-of-tables"],
            [p["stem"] for p in pages[:11]])
        self.assertEqual("part-I", pages[11]["stem"])
        self.assertEqual(24, sum(1 for p in pages if p["kind"] in {"part", "chapter"}))
        self.assertEqual(36, sum(1 for p in pages if p["kind"].startswith("appendix")))
        self.assertEqual(["bibliography", "index", "p9-12-changelog",
                          "p9-13-thanks", "p9-14-credits", "colophon"],
                         [p["stem"] for p in pages[-6:]])
        self.assertEqual(77, len({p["stem"] for p in pages}))

    def test_rejects_legacy_schema(self):
        self.manifest["schema"] = 1
        self.assertIn("schema", self.problems())

    def test_rejects_missing_chapter(self):
        self.manifest["parts"][0]["units"][0]["chapters"].pop()
        self.assertIn("19", self.problems())

    def test_rejects_duplicate_chapter(self):
        self.manifest["parts"][0]["units"][0]["chapters"].append("p1-01-ch0.md")
        self.assertIn("重复", self.problems())

    def test_rejects_unknown_excluded_page(self):
        self.manifest["excluded_pages"][0]["file"] = "p1-01-ch0.md"
        self.assertIn("排除", self.problems())

    def test_rejects_excluded_without_reason(self):
        self.manifest["excluded_pages"][0]["reason"] = ""
        self.assertIn("reason", self.problems())

    def test_rejects_missing_new_page(self):
        self.manifest["front_matter"] = [
            e for e in self.manifest["front_matter"]
            if e.get("file") != "p0-11-conventions.md"]
        self.assertIn("p0-11", self.problems())

    def test_rejects_duplicate_direct_page(self):
        self.manifest["appendices"][1]["files"].append("p0-01-preface.md")
        self.assertIn("重复", self.problems())

    def test_rejects_manual_spine(self):
        self.manifest["cover"]["spine_mm"] = 20
        self.assertIn("spine_mm", self.problems())

    def test_rejects_negative_bleed(self):
        self.manifest["cover"]["bleed_mm"] = -1
        self.assertIn("bleed_mm", self.problems())

    def test_rejects_unknown_appendix_id(self):
        self.manifest["appendices"][-1]["id"] = "Z"
        self.assertIn("附录", self.problems())

    def test_rejects_wrong_appendix_file_count(self):
        self.manifest["appendices"][2]["files"].pop()
        self.assertIn("C", self.problems())

    def test_rejects_missing_back_matter_kind(self):
        self.manifest["back_matter"] = [
            e for e in self.manifest["back_matter"] if e["kind"] != "index"]
        self.assertIn("index", self.problems())

if __name__ == "__main__":
    unittest.main()
```

Create `analog-book/tests/book_fixtures.py` with the canonical schema-2 manifest and file-tree helpers. The manifest lists must be exact:

```python
"""临时 docs/site/data 树，供新书管线测试使用。"""
from __future__ import annotations

import json
from pathlib import Path

FRONT = [
    {"kind": "half_title"},
    {"kind": "title_page"},
    {"kind": "copyright"},
    {"file": "p0-01-preface.md", "title": "前言"},
    {"file": "p0-02-how-to-use.md", "title": "怎样读这本书"},
    {"file": "p0-03-timeline.md", "title": "模拟电路简史"},
    {"file": "p0-11-conventions.md", "title": "排版、术语与引用约定"},
    {"file": "p0-12-symbols.md", "title": "符号与单位表"},
    {"kind": "toc"},
    {"kind": "list_of_figures"},
    {"kind": "list_of_tables"},
]

PARTS = [
    {"id": "I", "title": "基础", "subtitle": "先建立电路直觉",
     "intro": "这一篇从电压、电流与无源元件开始，先把电路为什么会这样工作讲清楚。"
              "你会反复使用欧姆定律、基尔霍夫定律与戴维南等效，把复杂网络化简成可计算的小模型。"
              "学完后，你应能独立分析由电源、电阻、电容、电感与负载组成的电路，并解释每个元件为什么在那里。"
              "遇到不确定的符号或单位，先回到附录 G 与前置约定页核对，再继续推导。",
     "opener_art": "part-i.svg",
     "units": [{"title": "电路直觉与无源世界",
                "chapters": ["p1-01-ch0.md", "p1-02-ch1.md"]}]},
    {"id": "II", "title": "器件", "subtitle": "从 PN 结到 555",
     "intro": "器件篇沿着 PN 结、二极管、BJT、MOSFET 一路走到运放、比较器、模拟开关、基准与 555。"
              "重点不是背参数，而是理解器件在什么条件下近似成什么模型，以及模型失效时会发生什么。"
              "每类器件都会配仿真与实测边界，帮助你把手算、仿真与真实波形对上。"
              "读完后，你应能根据数据手册和电路目标选出合适的器件，并预判它的非理想行为。",
     "opener_art": "part-ii.svg",
     "units": [
         {"title": "分立器件", "chapters": ["p1-03-ch2.md", "p1-04-ch3.md",
                                            "p1-05-ch4.md", "p1-06-ch5.md"]},
         {"title": "模拟集成器件", "chapters": ["p1-07-ch6.md", "p1-08-ch7.md",
                                                "p1-09-ch8.md", "p1-10-ch9.md",
                                                "p1-11-ch10.md"]},
     ]},
    {"id": "III", "title": "拓扑", "subtitle": "把器件接成可复用的电路",
     "intro": "拓扑篇把已经认识的器件接成可复用的电路块：放大、滤波、稳压、振荡与信号产生。"
              "你会看到同一组器件如何因偏置、反馈与负载不同而呈现完全不同的传递函数。"
              "分析时先抓大信号工作点，再看小信号等效，最后用仿真检查边角。"
              "目标是让你面对一张陌生原理图时，能先说出它属于哪类拓扑，再决定从哪里下手。",
     "opener_art": "part-iii.svg",
     "units": [{"title": "信号链与功率",
                "chapters": ["p2-01-ch11.md", "p2-02-ch12.md", "p2-03-ch13.md"]}]},
    {"id": "IV", "title": "设计", "subtitle": "从指标到可打样的板",
     "intro": "设计篇从指标出发，把想要什么翻译成增益、带宽、噪声、功耗与成本之间的取舍。"
              "你会练习选型、偏置、稳定性、保护与 PCB 布局，并学会在打样前用计算和仿真排除明显错误。"
              "这里没有唯一正确答案，只有被记录下来的假设、验证与余量。"
              "读完后，你应能独立完成一块小信号模拟板的设计评审。",
     "opener_art": "part-iv.svg",
     "units": [{"title": "方法与实现",
                "chapters": ["p3-01-ch14.md", "p3-02-ch15.md"]}]},
    {"id": "V", "title": "调试", "subtitle": "从现象到根因",
     "intro": "调试篇把前面学到的知识收束成一套可重复的排故方法：先观察现象，再分割电路，提出假设，用测量验证，最后回到根因。"
              "故障速查表覆盖电源、偏置、噪声、振荡、接口与焊接等常见问题，但它的用法是索引而不是背答案。"
              "你会看到经验丰富的工程师如何控制变量、选择接地点与探头，以及如何避免把假象当成结论。"
              "读完后，你应能在没有原理图标注的情况下，仍然有条理地缩小问题范围。",
     "opener_art": "part-v.svg",
     "units": [{"title": "方法与经验",
                "chapters": ["p4-01-ch16.md", "p4-02-ch17.md", "p4-03-ch18.md"]}]},
]

APPENDICES = [
    {"id": "A", "title": "动画与图示索引", "transform": "animation_index",
     "data": "analog-book/data/animations.yml"},
    {"id": "B", "title": "公式与设计速查", "files": ["p0-08-cheatsheet.md"]},
    {"id": "C", "title": "常用芯片速查",
     "files": ["p6-01-s6-1.md", "p6-02-s6-2.md", "p6-03-s6-3.md",
               "p6-04-s6-4.md", "p6-05-s6-5.md"]},
    {"id": "D", "title": "视频课程与配套资源",
     "files": ["p7-01-s7-1.md", "p7-02-s7-2.md", "p7-03-s7-3.md",
               "p8-02-s8-2.md", "p8-03-s8-3.md", "p8-04-s8-4.md",
               "p8-05-s8-5.md", "p8-06-s8-6.md", "p8-07-s8-7.md",
               "p8-08-s8-8.md", "p8-09-s8-9.md"]},
    {"id": "E", "title": "学习路线、选读与诊断",
     "files": ["p0-04-by-need.md", "p0-05-picks.md", "p0-06-roadmap.md",
               "p0-09-diagnostic.md", "p8-01-s8-1.md", "p8-11-s8-11.md"]},
    {"id": "F", "title": "习题答案与综合自测", "transform": "answers",
     "files": ["p9-00-quiz.md"]},
    {"id": "G", "title": "术语表", "files": ["p9-15-glossary.md", "p8-10-s8-10.md"]},
    {"id": "H", "title": "模型、近似与适用边界", "files": ["p0-10-model-limits.md"]},
]

EXCLUDED = [
    {"file": "index.md", "reason": "站点首页"},
    {"file": "p0-07-toc.md", "reason": "由书内详细目录替代"},
    {"file": "p1-00-part1.md", "reason": "由书内第 II 篇首页替代"},
    {"file": "p2-00-part2.md", "reason": "由书内第 III 篇首页替代"},
    {"file": "p3-00-part3.md", "reason": "由书内第 IV 篇首页替代"},
    {"file": "p4-00-part4.md", "reason": "由书内第 V 篇首页替代"},
    {"file": "p5-00-part5.md", "reason": "附录 A 素材"},
    {"file": "p6-00-part6.md", "reason": "附录 C 分隔页由构建生成"},
    {"file": "p7-00-part7.md", "reason": "附录 D 分隔页由构建生成"},
    {"file": "p8-00-part8.md", "reason": "附录 D/E/G 分隔页由构建生成"},
]

BACK = [
    {"kind": "bibliography"},
    {"kind": "index", "terms": "analog-book/data/index-terms.yml"},
    {"file": "p9-12-changelog.md", "title": "版本记录"},
    {"file": "p9-13-thanks.md", "title": "致谢"},
    {"file": "p9-14-credits.md", "title": "来源与许可"},
    {"kind": "colophon"},
]


def manifest():
    return {
        "schema": 2,
        "title": "通往模拟电路之路",
        "subtitle": "从欧姆定律到芯片内部结构",
        "edition": "第一版",
        "version": "2.0.0-draft.1",
        "source_version": "3.61",
        "date": "2026-10-25",
        "language": "zh-CN",
        "author": "zhuguang-ZFG 与贡献者",
        "site_url": "https://aliyun-hutuji.donglicao.com/analog-circuit-roadmap/",
        "repository": "https://github.com/zhuguang-ZFG/analog-circuit-roadmap",
        "license": "CC BY-SA 4.0",
        "trim": {"width_mm": 185, "height_mm": 260},
        "front_matter": FRONT,
        "parts": PARTS,
        "appendices": APPENDICES,
        "excluded_pages": EXCLUDED,
        "back_matter": BACK,
        "cover": {
            "bleed_mm": 3, "crop_marks": True, "paper_caliper_mm": 0.10,
            "spine_allowance_mm": 1.0, "isbn_area": False,
            "back_cover": {
                "blurb": "把直觉、推导、仿真、实测与排故连起来。",
                "audience": "电子、自动化、通信与嵌入式方向的学生和工程师。",
                "highlights": ["19 章完整知识链", "三层读法", "可复现仿真",
                               "实测实验", "故障速查与索引"],
            },
        },
        "release": {"edition_status": "draft", "stable_version": "1.0.0"},
    }


def direct_files(manifest_data):
    files = [e["file"] for e in manifest_data["front_matter"] if "file" in e]
    for part in manifest_data["parts"]:
        for unit in part["units"]:
            files.extend(unit["chapters"])
    for appendix in manifest_data["appendices"]:
        files.extend(appendix.get("files", []))
    files.extend(e["file"] for e in manifest_data["back_matter"] if "file" in e)
    return files


def all_docs(manifest_data):
    return direct_files(manifest_data) + [e["file"] for e in manifest_data["excluded_pages"]]


def write_docs(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    for name in all_docs(manifest()):
        title = Path(name).stem.replace("-", " ")
        (root / name).write_text(f"# {title}\n\n正文示例。\n", encoding="utf-8")


def write_site(site_dir: Path) -> Path:
    site = site_dir
    for rel in ("assets/stylesheets/main.abc.min.css", "assets/stylesheets/palette.abc.min.css"):
        path = site / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("body{margin:0}", encoding="utf-8")
    for name in ("typography", "gallery", "learning", "reading", "diag"):
        path = site / "stylesheets" / f"{name}.css"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("/* fixture */", encoding="utf-8")
    for name in ("calc", "learning", "learning-catalog", "diag"):
        path = site / "javascripts" / f"{name}.js"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("/* fixture */", encoding="utf-8")
    svg = site / "assets" / "svg" / "fixture.svg"
    svg.parent.mkdir(parents=True, exist_ok=True)
    svg.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="80" height="40"></svg>',
                   encoding="utf-8")
    for name in all_docs(manifest()):
        title = Path(name).stem.replace("-", " ")
        body = f'<h1>{title}</h1><p>正文示例。</p><h2>1.1 示例小节</h2><p>内容。</p>'
        if name == "p1-01-ch0.md":
            body = ('<h1>第 0 章 电路直觉</h1><p>正文。</p>'
                    '<h2>0.1 电压与电位</h2><p>内容。</p>'
                    '<p><img src="assets/svg/fixture.svg" alt="夹具图"></p>')
        path = site / name.replace(".md", ".html")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            '<html><body><article class="md-content__inner md-typeset">'
            + body + "</article></body></html>", encoding="utf-8")
    return site


def write_data(data_dir: Path) -> Path:
    data = data_dir
    data.mkdir(parents=True, exist_ok=True)
    animations = [
        {"id": f"anim-{i:03d}", "file": "p5-00-part5.md", "title": f"动画 {i}",
         "chapter": i % 19, "anchor": f"demo{i}", "one_line": "示例动画。",
         "static_svg": "assets/svg/fixture.svg"}
        for i in range(1, 109)
    ]
    import yaml
    (data / "animations.yml").write_text(
        yaml.safe_dump(animations, allow_unicode=True, sort_keys=False), encoding="utf-8")
    terms = [
        {"term": "米勒效应", "english": "Miller effect",
         "primary": "page-p1-01-ch0", "anchors": ["page-p1-01-ch0"], "see_also": []},
        {"term": "欧姆定律", "english": "Ohm's law",
         "primary": "page-p1-01-ch0", "anchors": ["page-p1-01-ch0"], "see_also": []},
    ]
    (data / "index-terms.yml").write_text(
        yaml.safe_dump(terms, allow_unicode=True, sort_keys=False), encoding="utf-8")
    (data / "sources.yml").write_text("[]\n", encoding="utf-8")
    (data / "references.yml").write_text("[]\n", encoding="utf-8")
    signoff = [{"chapter": i, "draft_version": "2.0.0-draft.1",
                "technical_reviewer": "", "editorial_reviewer": "",
                "safety_reviewer": "", "date": "2026-10-25", "open_issues": []}
               for i in range(19)]
    (data / "chapter-signoff.yml").write_text(
        yaml.safe_dump(signoff, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return data
```

- [ ] **Step 2: 运行测试，确认失败**

Run: `python -B -m unittest discover -s analog-book/tests -p "test_book_manifest.py" -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'book'` or missing `BookError`.

- [ ] **Step 3: 写最小实现**

`analog-book/book/config.py`:

```python
from pathlib import Path

BOOK_DIR = Path(__file__).resolve().parent.parent
ROOT = BOOK_DIR.parent
DOCS = ROOT / "docs"
SITE_DIR = ROOT / "build" / "site"
DIST_DIR = BOOK_DIR / "dist" / "print"  # 16K 产物；A4 1.0 仍在 dist/ 根
MANIFEST_PATH = BOOK_DIR / "manifest.json"
FONTS_DIR = BOOK_DIR / "fonts"
DATA_DIR = BOOK_DIR / "data"
STYLES_DIR = BOOK_DIR / "styles"
STATIC_DIR = BOOK_DIR / "static"
COVER_DIR = BOOK_DIR / "cover"

OUTPUT_NAME = "analog-circuit-book.html"
PDF_NAME = "analog-circuit-book.pdf"
COVER_PDF_NAME = "cover.pdf"
COVER_PREVIEW_NAME = "cover-preview.png"
MODEL_NAME = "book-model.json"
SAMPLE_HTML_NAME = "sample.html"
SAMPLE_PDF_NAME = "sample.pdf"
SAMPLE_REPORT_NAME = "sample-report.json"

HTML_TARGET_BYTES = 60 * 1024 * 1024
MAX_HTML_BYTES = 80 * 1024 * 1024
MAX_PDF_BYTES = 100 * 1024 * 1024

TRIM_WIDTH_MM = 185.0
TRIM_HEIGHT_MM = 260.0
TEXT_WIDTH_MM = 145.0
TEXT_HEIGHT_MM = 218.0
BLEED_MM = 3.0
```

`analog-book/book/manifest.py`: implement `BookError`, JSON load/hash, and validators with these exact rules:

```python
SCHEMA_VERSION = 2
PART_IDS = ["I", "II", "III", "IV", "V"]
APPENDIX_IDS = list("ABCDEFGH")
APPENDIX_FILE_COUNTS = {"A": 0, "B": 1, "C": 5, "D": 11, "E": 6, "F": 1, "G": 2, "H": 1}
NEW_PAGES = {"p0-11-conventions.md", "p0-12-symbols.md", "p9-15-glossary.md"}
EXCLUDED_ALLOWED = {
    "index.md", "p0-07-toc.md",
    "p1-00-part1.md", "p2-00-part2.md", "p3-00-part3.md", "p4-00-part4.md",
    "p5-00-part5.md", "p6-00-part6.md", "p7-00-part7.md", "p8-00-part8.md",
}
CHAPTER_RE = re.compile(r"^p\d+-\d+-ch(\d+)\.md$")
FRONT_KINDS = {"half_title", "title_page", "copyright", "toc",
               "list_of_figures", "list_of_tables"}
BACK_KINDS = {"bibliography", "index", "colophon"}
```

Rules:

1. `schema == 2`; required metadata non-empty; `trim.width_mm == 185` and `trim.height_mm == 260`.
2. `front_matter` has all six kinds exactly once; file entries exist and are in `NEW_PAGES` when new.
3. `parts` IDs exactly `PART_IDS` in order; each unit has a title and non-empty chapters; flattening yields exactly 19 chapters, chapter numbers exactly `0..18`, strictly increasing inside each unit and across the flattened list.
4. `appendices` IDs exactly `APPENDIX_IDS`; A has `transform == "animation_index"` and data; F has `transform == "answers"`; each appendix file count equals `APPENDIX_FILE_COUNTS`.
5. `back_matter` contains `bibliography`, `index`, `colophon` exactly once.
6. `excluded_pages` equals `EXCLUDED_ALLOWED`, each with a non-empty reason.
7. `direct_files` + excluded equals every `docs/*.md` stem exactly once; direct files are unique; existing documents (all but `NEW_PAGES`) split exactly 51 direct + 10 excluded; all `NEW_PAGES` are direct.
8. Cover params `bleed_mm`, `paper_caliper_mm`, `spine_allowance_mm` are positive; `spine_mm` must not be present.
9. `release.edition_status` in `{"draft", "final"}`.

`book_pages(manifest)` builds in this exact order:

- Front: one page per `front_matter` entry. Generated kinds use stems `half-title`, `title-page`, `copyright`, `toc`, `list-of-figures`, `list-of-tables`; file entries use their stem and manifest title.
- Body: for each part, a `kind="part"` page with stem `part-<id>` and title `第 <id> 篇 <part title>`, then each chapter as `kind="chapter"` with `part_id`, `part_title`, `unit_title`.
- Appendices: for each, a `kind="appendix_opener"` with stem `appendix-<id>`; then A's generated `appendix-A-index`; each file as `kind="appendix"`; F's generated `appendix-F-answers`; use title from appendix for generated pages.
- Back: `bibliography` and `index` generated pages, file entries, `colophon`.

- [ ] **Step 4: 运行测试，确认通过**

Run: `python -B -m unittest discover -s analog-book/tests -p "test_book_manifest.py" -v`
Expected: PASS (14 tests).

- [ ] **Step 5: 提交**

```bash
git add analog-book/book/__init__.py analog-book/book/config.py analog-book/book/manifest.py \
  analog-book/tests/book_fixtures.py analog-book/tests/test_book_manifest.py
git commit -m "feat(book): add schema-2 manifest model and coverage validator"
```

新测试暂不进 `book.yml`：Pages 通过 `workflow_call` 调用它，把 16K 测试放进去会让 16K 失败阻断 A4 发布。Task 11B 创建独立的 `book-print.yml` 后，用 `test_book_*.py` 统一纳入 CI。

---

### Task 2: OFL 子集字体与内联 font-face

**Files:**
- Create: `scripts/subset_fonts.py`
- Create: `analog-book/book/fonts.py`
- Create: `analog-book/fonts/NotoSerifSC-Regular.woff2`
- Create: `analog-book/fonts/NotoSerifSC-Bold.woff2`
- Create: `analog-book/fonts/NotoSansSC-Regular.woff2`
- Create: `analog-book/fonts/NotoSansSC-Bold.woff2`
- Create: `analog-book/fonts/JetBrainsMono-Regular.woff2`
- Create: `analog-book/fonts/BookSans-Stamp.ttf`
- Create: `analog-book/fonts/OFL-NotoSerifSC.txt`
- Create: `analog-book/fonts/OFL-NotoSansSC.txt`
- Create: `analog-book/fonts/OFL-JetBrainsMono.txt`
- Create: `analog-book/fonts/sources.json`
- Create: `analog-book/fonts/README.md`
- Create: `analog-book/tests/test_book_fonts.py`
- Modify: `analog-book/requirements.txt`

**Interfaces:**
- Produces: `FONT_FACES`、`STAMP_FONT_NAME`、`required_text(docs_dir=DOCS, book_dir=BOOK_DIR) -> str`、`missing_glyphs(font_path, text) -> set[str]`、`font_css(fonts_dir=FONTS_DIR) -> str`、`stamp_font_path(fonts_dir=FONTS_DIR) -> Path`。
- `font_css` returns five `@font-face` blocks with families `Book Serif` (400/700), `Book Sans` (400/700), `Book Mono` (400), all `font-display:block` and data URIs.
- `scripts/subset_fonts.py` CLI: `--download`, `--build`, `--check`, `--out`.

- [ ] **Step 1: 写失败测试**

Create `analog-book/tests/test_book_fonts.py`:

```python
#!/usr/bin/env python3
"""书内字体必须覆盖全书字符，而且以 data URI 内联。"""
import base64
import json
import re
import sys
import unittest
from pathlib import Path

BOOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BOOK))
from book import config  # noqa: E402
from book.fonts import (FONT_FACES, font_css, missing_glyphs,  # noqa: E402
                        required_text, stamp_font_path)
from fontTools.ttLib import TTFont  # noqa: E402


class FontTests(unittest.TestCase):
    def test_all_faces_exist_and_are_valid_woff2(self):
        self.assertEqual(5, len(FONT_FACES))
        for _family, _weight, name in FONT_FACES:
            path = config.FONTS_DIR / name
            self.assertTrue(path.is_file(), path)
            font = TTFont(path)
            self.assertIn("cmap", font)

    def test_serif_and_sans_cover_every_book_character(self):
        text = required_text()
        self.assertGreater(len(set(text)), 1000)
        for name in ("NotoSerifSC-Regular.woff2", "NotoSerifSC-Bold.woff2",
                     "NotoSansSC-Regular.woff2", "NotoSansSC-Bold.woff2"):
            missing = missing_glyphs(config.FONTS_DIR / name, text)
            self.assertEqual(set(), missing,
                             f"{name} 缺字: {''.join(sorted(missing))[:80]}")

    def test_mono_covers_ascii(self):
        missing = missing_glyphs(config.FONTS_DIR / "JetBrainsMono-Regular.woff2",
                                 "".join(chr(c) for c in range(32, 127)))
        self.assertEqual(set(), missing)

    def test_stamp_font_covers_running_titles(self):
        titles = "通往模拟电路之路目录索引参考文献第一篇基础第二篇器件第三篇拓扑第四篇设计第五篇调试"
        missing = missing_glyphs(stamp_font_path(), titles)
        self.assertEqual(set(), missing)

    def test_font_css_is_five_data_uris_and_no_remote(self):
        css = font_css()
        self.assertEqual(5, css.count("@font-face"))
        self.assertEqual(5, css.count("data:font/woff2;base64,"))
        self.assertNotIn("http", css)
        self.assertIn('font-family: "Book Serif"', css)
        self.assertIn("font-weight: 700", css)
        for _family, _weight, name in FONT_FACES:
            raw = (config.FONTS_DIR / name).read_bytes()
            encoded = base64.b64encode(raw).decode("ascii")
            self.assertIn(encoded[:80], css)

    def test_sources_json_records_hashes_and_licenses(self):
        data = json.loads((config.FONTS_DIR / "sources.json").read_text(encoding="utf-8"))
        self.assertEqual(5, len(data["subsets"]))
        for entry in data["subsets"]:
            self.assertRegex(entry["sha256"], r"^[0-9a-f]{64}$")
            self.assertEqual(entry["name"], Path(entry["name"]).name)
        for name in ("OFL-NotoSerifSC.txt", "OFL-NotoSansSC.txt",
                     "OFL-JetBrainsMono.txt"):
            self.assertTrue((config.FONTS_DIR / name).is_file())


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 运行测试，确认失败**

Run: `python -B -m unittest discover -s analog-book/tests -p "test_book_fonts.py" -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'book.fonts'`.

- [ ] **Step 3: 实现字体子集工具**

`analog-book/book/fonts.py`:

```python
import base64
import html
import re
from pathlib import Path

from fontTools.ttLib import TTFont

from . import config

FONT_FACES = [
    ("Book Serif", 400, "NotoSerifSC-Regular.woff2"),
    ("Book Serif", 700, "NotoSerifSC-Bold.woff2"),
    ("Book Sans", 400, "NotoSansSC-Regular.woff2"),
    ("Book Sans", 700, "NotoSansSC-Bold.woff2"),
    ("Book Mono", 400, "JetBrainsMono-Regular.woff2"),
]
STAMP_FONT_NAME = "BookSans-Stamp.ttf"
EMOJI_RE = re.compile(
    "[\U0001F000-\U0001FAFF\u2300-\u23FF\u2600-\u27BF\u2B00-\u2BFF"
    "\uFE0F\u200D]+")

def _strip_emoji(text: str) -> str:
    return EMOJI_RE.sub("", text)

def required_text(docs_dir=config.DOCS, book_dir=config.BOOK_DIR) -> str:
    chunks = []
    for path in sorted(Path(docs_dir).glob("*.md")):
        chunks.append(path.read_text(encoding="utf-8"))
    for path in sorted((Path(book_dir) / "book").glob("*.py")):
        chunks.append(path.read_text(encoding="utf-8"))
    chunks.append((Path(book_dir) / "manifest.json").read_text(encoding="utf-8"))
    data = Path(book_dir) / "data"
    if data.is_dir():
        for path in sorted(data.glob("*.yml")):
            chunks.append(path.read_text(encoding="utf-8"))
    for path in sorted((config.ROOT / "assets" / "svg").rglob("*.svg")):
        chunks.append(html.unescape(re.sub(r"<[^>]+>", " ", path.read_text(
            encoding="utf-8", errors="replace"))))
    text = _strip_emoji("\n".join(chunks))
    return text + "".join(chr(c) for c in range(32, 127)) + "　、。“”‘’—…·×÷±≤≥≠≈∞Ωμ°℃"

def missing_glyphs(font_path, text) -> set[str]:
    font = TTFont(font_path)
    cmap = set()
    for table in font["cmap"].tables:
        cmap.update(table.cmap.keys())
    return {ch for ch in set(text) if ch not in "\r\n\t" and ord(ch) not in cmap}

def font_css(fonts_dir=config.FONTS_DIR) -> str:
    faces = []
    for family, weight, name in FONT_FACES:
        raw = (Path(fonts_dir) / name).read_bytes()
        uri = base64.b64encode(raw).decode("ascii")
        faces.append(
            f'@font-face{{font-family:"{family}";'
            f'src:url(data:font/woff2;base64,{uri}) format("woff2");'
            f'font-weight:{weight};font-style:normal;font-display:block}}')
    return "\n".join(faces)

def stamp_font_path(fonts_dir=config.FONTS_DIR) -> Path:
    return Path(fonts_dir) / STAMP_FONT_NAME
```

`scripts/subset_fonts.py` implements:

```python
SOURCES = {
    "NotoSerifSC": ("https://raw.githubusercontent.com/google/fonts/main/ofl/notoserifsc/NotoSerifSC%5Bwght%5D.ttf",
                    "OFL-NotoSerifSC.txt"),
    "NotoSansSC": ("https://raw.githubusercontent.com/google/fonts/main/ofl/notosanssc/NotoSansSC%5Bwght%5D.ttf",
                   "OFL-NotoSansSC.txt"),
    "JetBrainsMono": ("https://raw.githubusercontent.com/google/fonts/main/ofl/jetbrainsmono/JetBrainsMono%5Bwght%5D.ttf",
                      "OFL-JetBrainsMono.txt"),
}
TARGETS = {
    ("NotoSerifSC", 400): "NotoSerifSC-Regular.woff2",
    ("NotoSerifSC", 700): "NotoSerifSC-Bold.woff2",
    ("NotoSansSC", 400): "NotoSansSC-Regular.woff2",
    ("NotoSansSC", 700): "NotoSansSC-Bold.woff2",
    ("JetBrainsMono", 400): "JetBrainsMono-Regular.woff2",
}
```

Download each source and its `OFL.txt` from the same directory into `build/fonts-src/`. Instantiate variable fonts:

```python
from fontTools.varLib.instancer import instantiateVariableFont
font = TTFont(source)
if "fvar" in font:
    font = instantiateVariableFont(font, {"wght": weight})
subsetter = Subsetter()
subsetter.populate(unicodes={ord(ch) for ch in chars})
subsetter.subset(font)
font.flavor = "woff2"
font.save(target)
```

For the stamp font: instantiate `NotoSansSC` at 700, subset to ASCII plus all strings that can appear in running heads/footers (`manifest.title`, part titles, chapter titles from docs, appendix titles, `目录`, `索引`, `参考文献`, `版本记录`), save as TTF. Record `sources.json`:

```json
{
  "schema": 1,
  "sources": [
    {"family": "NotoSerifSC", "url": "...", "sha256": "...", "bytes": 0}
  ],
  "subsets": [
    {"name": "NotoSerifSC-Regular.woff2", "family": "NotoSerifSC", "weight": 400,
     "characters": 0, "bytes": 0, "sha256": "..."}
  ]
}
```

`--check` verifies all five subsets, their hashes, licenses, and coverage of `required_text()`. `--build` regenerates subsets from `build/fonts-src/` without downloading. Commit only `analog-book/fonts/` outputs, never the source TTF/OFL downloads in `build/fonts-src/`.

- [ ] **Step 4: 下载并生成字体**

Run:

```bash
python scripts/subset_fonts.py --download
python scripts/subset_fonts.py --build
python scripts/subset_fonts.py --check
```

Expected: five WOFF2 + stamp TTF + three licenses + `sources.json`; `--check` prints coverage counts and exits 0. If a character is missing, the command must fail with the exact code points; resolve by correcting the required-text generator or adding the missing glyph source, not by deleting the assertion.

- [ ] **Step 5: 加依赖并跑测试**

Modify `analog-book/requirements.txt` to:

```text
Playwright>=1.61,<2
PyMuPDF>=1.28,<2
fonttools>=4.47,<5
brotli>=1.1,<2
PyYAML>=6,<7
matplotlib>=3.8,<4
pypinyin>=0.51,<1
```

Run: `python -B -m unittest discover -s analog-book/tests -p "test_book_fonts.py" -v`
Expected: PASS (8 tests；含 ✓✗ 与 schema-2 印章覆盖回归).

- [ ] **Step 6: 提交**

```bash
git add scripts/subset_fonts.py analog-book/book/fonts.py analog-book/fonts \
  analog-book/tests/test_book_fonts.py analog-book/requirements.txt
git commit -m "feat(book): add OFL font subsets and inline font-face CSS"
```

---

### Task 3: 16K 打印样式与十页样张

**Files:**
- Create: `analog-book/styles/print.css`
- Create: `analog-book/book/sample.py`
- Create: `analog-book/tests/test_book_sample.py`

**Interfaces:**
- Produces: `SAMPLE_SECTIONS`（9 个标题）、`sample_html(fonts_css, manifest=None) -> str`、`inspect_sample(pdf_path) -> dict`、`build_sample(out_dir, fonts_dir=FONTS_DIR, browser_override=None) -> tuple[Path, Path, dict]`。
- `sample-report.json` keys: `page_size_mm`、`text_width_mm`、`margins_mm`、`mirrored`、`fallback`、`sections`。
- `print.css` 不得依赖 `book.css` 的 `@page`；本任务不改 `book.css`。

- [ ] **Step 1: 写失败测试**

Create `analog-book/tests/test_book_sample.py`:

```python
#!/usr/bin/env python3
"""16K 样张必须证明版心、镜像边距回退与九类版式都不溢出。"""
import sys
import unittest
from pathlib import Path

BOOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BOOK))
from book import config  # noqa: E402
from book.sample import SAMPLE_SECTIONS, build_sample, inspect_sample  # noqa: E402

try:
    import fitz
except ImportError:  # pragma: no cover
    fitz = None

try:
    from playwright.sync_api import sync_playwright
except ImportError:  # pragma: no cover
    sync_playwright = None


@unittest.skipIf(fitz is None or sync_playwright is None,
                 "需要 PyMuPDF 与 Playwright")
class SampleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html, cls.pdf, cls.report = build_sample(config.DIST_DIR / "sample")

    def test_page_is_16k(self):
        doc = fitz.open(self.pdf)
        try:
            for page in doc:
                width = page.rect.width * 25.4 / 72
                height = page.rect.height * 25.4 / 72
                self.assertAlmostEqual(185, width, delta=0.5)
                self.assertAlmostEqual(260, height, delta=0.5)
        finally:
            doc.close()

    def test_nine_sections_are_present(self):
        self.assertEqual(9, len(SAMPLE_SECTIONS))
        doc = fitz.open(self.pdf)
        try:
            text = "\n".join(page.get_text() for page in doc)
        finally:
            doc.close()
        for title in SAMPLE_SECTIONS:
            self.assertIn(title, text)

    def test_text_stays_inside_145mm_text_block(self):
        report = inspect_sample(self.pdf)
        self.assertLessEqual(report["text_width_mm"], 145.5)
        self.assertGreaterEqual(report["text_width_mm"], 130)
        self.assertEqual(9, len(report["sections"]))
        self.assertIn(report["fallback"], {"mirrored", "uniform-20mm"})
        self.assertTrue((self.html.parent / "sample-report.json").is_file())

    def test_print_css_has_16k_and_typography_contract(self):
        css = (config.STYLES_DIR / "print.css").read_text(encoding="utf-8")
        self.assertIn("size: 185mm 260mm", css)
        self.assertIn("font-size: 10.5pt", css)
        self.assertIn("line-height: 17.5pt", css)
        self.assertIn("font-size: 28pt", css)
        self.assertIn(".book .half-title", css)
        self.assertIn("font-size: 8.5pt", css)
        self.assertIn("column-count: 2", css)
        self.assertRegex(
            css, r"\.toc-row a\s*\{[^}]*grid-template-columns:\s*auto\s+minmax\([^)]*\)\s+auto")
        self.assertIn("break-inside: avoid", css)
        self.assertIn("thead", css)
        self.assertIn("@page :left", css)
        self.assertIn("@page :right", css)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 运行测试，确认失败**

Run: `python -B -m unittest discover -s analog-book/tests -p "test_book_sample.py" -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'book.sample'`.

- [ ] **Step 3: 写 `print.css`**

Create `analog-book/styles/print.css` with this contract:

```css
@page { size: 185mm 260mm; margin: 20mm 20mm 22mm; }
@page :left { margin: 20mm 22mm 22mm 18mm; }
@page :right { margin: 20mm 18mm 22mm 22mm; }

:root {
  --print-ink: #1f2933;
  --print-muted: #52606d;
  --print-rule: #d9e2ec;
}

html, body { background: #fff !important; }
body {
  margin: 0; color: var(--print-ink);
  font-family: "Book Serif", "Noto Serif SC", "Songti SC", serif;
  font-size: 10.5pt; line-height: 17.5pt;
}
.book-header, .book-footer, .book-page-nav, .reading-nav, .book-search,
.book-top, .book-progress, .book-skip, .book-search-panel,
.gal-bar, .gal-actions, .gal-hint, .gal-modal, .gal-play,
.learning-backup { display: none !important; }
.book { max-width: none; padding: 0; margin: 0; }
.book .md-typeset { max-width: none; font-size: 10.5pt; line-height: 17.5pt; }
.book .md-typeset h1, .book .md-typeset h2, .book .md-typeset h3,
.book .md-typeset h4 { font-family: "Book Sans", "Noto Sans SC", sans-serif; }
.book .md-typeset h1 { font-size: 22pt; line-height: 28pt; margin: 0 0 8mm; }
.book .md-typeset h2 { font-size: 15pt; line-height: 21pt; }
.book .md-typeset h3 { font-size: 12pt; line-height: 18pt; }
.book .md-typeset h4 { font-size: 10.5pt; line-height: 17.5pt; }
.book .half-title, .book .title-page {
  display: flex; flex-direction: column; justify-content: center;
  min-height: 160mm; text-align: center;
}
.book .half-title .book-title { font-size: 30pt; line-height: 38pt; margin: 0 0 6mm; }
.book .half-title .book-subtitle { font-size: 14pt; line-height: 22pt; }
.book .half-title .book-edition { margin-top: 12mm; font-size: 11pt; letter-spacing: .2em; }
.book .title-page .title-kicker { font-size: 11pt; letter-spacing: .3em; }
.book .title-page h1 { font-size: 30pt; line-height: 38pt; margin: 8mm 0 4mm; }
.book .title-page .title-subtitle { font-size: 14pt; line-height: 22pt; }
.book .title-page .title-author { margin-top: 16mm; font-size: 12pt; }
.book .title-page .title-edition, .book .title-page .title-date { font-size: 10pt; }
.book .copyright-page { font-size: 9pt; line-height: 13pt; }
.book .copyright-page h1 { font-size: 15pt; line-height: 21pt; }
.book .part-opener, .book .appendix-opener {
  display: flex; flex-direction: column; justify-content: center;
  min-height: 160mm;
}
.book .part-opener h1, .book .appendix-opener h1 { font-size: 28pt; line-height: 34pt; }
.book .part-kicker { display: block; font-size: 11pt; letter-spacing: .3em; }
.book .part-title { display: block; margin-top: 4mm; }
.book .part-subtitle { font-size: 13pt; line-height: 20pt; }
.book .part-units { font-size: 10pt; line-height: 16pt; }
.book .part-art { margin-top: 12mm; border-top: 0.2mm solid var(--print-rule); }
.book .appendix-intro { font-size: 10pt; line-height: 16pt; }
.book .colophon { font-size: 9pt; line-height: 13pt; }
.book .colophon h1 { font-size: 15pt; line-height: 21pt; }
.book .md-typeset p, .book .md-typeset li { text-align: justify; }
.book .md-typeset a { color: inherit; text-decoration: none; }
.book .md-typeset pre {
  white-space: pre-wrap; overflow-wrap: anywhere; word-break: break-word;
  font-family: "Book Mono", "JetBrains Mono", monospace;
  font-size: 8.5pt; line-height: 12pt; background: #f7f8fa;
  padding: 2.4mm 3mm; border: 0.2mm solid var(--print-rule);
}
.book .md-typeset code { font-family: "Book Mono", monospace; font-size: 8.5pt; }
.book .md-typeset table {
  width: 100%; border-collapse: collapse; table-layout: fixed;
  font-size: 9pt; line-height: 13pt;
}
.book .md-typeset thead { display: table-header-group; }
.book .md-typeset tr { break-inside: avoid; }
.book .md-typeset th, .book .md-typeset td {
  border: 0.2mm solid var(--print-rule); padding: 1.2mm 1.6mm;
  overflow-wrap: anywhere; vertical-align: top;
}
.book .md-typeset th { background: #f2f4f7; font-family: "Book Sans", sans-serif; }
.table-wrap, .book .md-typeset figure { overflow: visible; }
.book .md-typeset figure { break-inside: avoid; margin: 4mm 0; }
.book .md-typeset figcaption {
  font-family: "Book Sans", sans-serif; font-size: 9pt; line-height: 13pt;
  color: var(--print-muted); margin-top: 1.5mm; text-align: center;
}
.book .md-typeset img, .book .md-typeset svg { max-width: 100%; height: auto; }
.book .md-typeset img { max-height: 185mm; }
.book .md-typeset blockquote {
  border-left: 1.2mm solid #b45309; margin: 3mm 0; padding: 0 0 0 4mm;
}
.book .book-callout {
  border: 0.2mm solid var(--print-rule); border-left: 1.2mm solid #b45309;
  padding: 2.4mm 3mm; margin: 3mm 0; break-inside: avoid;
}
.book .book-callout-label {
  font-family: "Book Sans", sans-serif; font-size: 9pt; font-weight: 700;
  color: #b45309; display: block; margin-bottom: 1mm;
}
.book .book-reveal {
  border-left: 0.6mm solid var(--print-rule); padding: 1mm 0 1mm 3mm;
  margin: 3mm 0; break-inside: avoid;
}
.book .book-reveal-title {
  font-family: "Book Sans", sans-serif; font-size: 9pt; font-weight: 700;
  color: var(--print-muted); margin: 0 0 1mm;
}
.book .arithmatex { overflow: visible; break-inside: avoid; }
.book .calc { display: none !important; }  /* 计算器只服务屏幕，纸上保留示例推导 */
.book-figure { break-inside: avoid; }
.book-table { break-inside: avoid; }
.book-toc { break-before: auto; }  /* 外层 .book-page 已经分页，内层不得再断一次 */
.book-toc h1 { font-size: 28pt; }
.book-toc .book-toc-list {
  margin: 0; padding: 0; list-style: none; column-count: 2; column-gap: 6mm;
}
.toc-row {
  break-inside: avoid; margin: 0 0 1.2mm;
  font-size: 10.5pt; line-height: 15pt;
}
.toc-row a {
  display: grid; grid-template-columns: auto minmax(8mm, 1fr) auto; gap: 2mm;
  align-items: baseline; color: inherit; text-decoration: none;
}
.toc-row.toc-level-1 { font-family: "Book Sans", sans-serif; font-weight: 700; }
.toc-row.toc-level-2 { padding-left: 5mm; }
.toc-row.toc-level-3 { padding-left: 10mm; font-size: 9pt; line-height: 13.5pt; }
.toc-dots { border-bottom: 0.2mm dotted #98a2b3; transform: translateY(-1mm); }
.toc-page, .book-index-page { font-variant-numeric: tabular-nums; }
.book-index { column-count: 2; column-gap: 6mm; font-size: 9pt; line-height: 12.5pt; }
.book-index-entry { break-inside: avoid; margin: 0 0 1.2mm; }
.book-index-page.is-primary { font-weight: 700; }
.book-endnotes { font-size: 9pt; line-height: 13pt; border-top: 0.2mm solid var(--print-rule); margin-top: 6mm; }
.book-page { break-before: page; }
.book-page:first-of-type { break-before: auto; }
.book-part > .book-page:first-child, .book-appendix > .book-page:first-child {
  break-before: right;
}
h1, h2, h3 { break-after: avoid; }
p, li { orphans: 2; widows: 2; }
```

- [ ] **Step 4: 写样张生成器**

`analog-book/book/sample.py` builds a standalone HTML document with `font_css()` and `print.css`, then prints it with Playwright to `sample.pdf`. The nine sections must be exactly:

```python
SAMPLE_SECTIONS = ["章首页样张", "正文样张", "插图样张", "表格样张",
                   "代码样张", "公式样张", "脚注样张", "目录样张", "索引样张"]
```

Each section is a `section.book-page` with `break-before: page`; the table has 6 columns and 8 rows; the code block has 12 lines of at most 78 characters; the index has 40 synthetic terms in two columns. The formula section uses a local inline SVG (not MathJax) so the sample does not depend on MathJax initialization. `inspect_sample` must:

```python
import fitz
MM = 72 / 25.4

def inspect_sample(pdf_path):
    doc = fitz.open(pdf_path)
    try:
        page = doc[0]
        size = (page.rect.width / MM, page.rect.height / MM)
        sections = []
        for pno, page in enumerate(doc):
            blocks = [b for b in page.get_text("blocks") if b[4].strip()]
            xs0 = min(b[0] for b in blocks) / MM
            xs1 = max(b[2] for b in blocks) / MM
            sections.append({"page": pno + 1, "left": round(xs0, 2),
                             "right": round(xs1, 2),
                             "width": round(xs1 - xs0, 2)})
        mirrored = abs(sections[1]["left"] - sections[2]["left"]) > 2.0
        report = {
            "page_size_mm": [round(x, 2) for x in size],
            "text_width_mm": max(s["width"] for s in sections),
            "margins_mm": {"top": 20, "bottom": 22},
            "mirrored": mirrored,
            "fallback": "mirrored" if mirrored else "uniform-20mm",
            "sections": sections,
        }
    finally:
        doc.close()
    return report
```

`build_sample` writes `sample.html`, `sample.pdf`, `sample-report.json`; if Chromium does not apply `@page :left/:right`, the report must say `uniform-20mm` and `PRINT-SPEC` later records it. Do not fail the build for this fallback; fail only if text width exceeds 145.5mm or page size is wrong.

- [ ] **Step 5: 运行测试，确认通过**

Run: `python -B -m unittest discover -s analog-book/tests -p "test_book_sample.py" -v`
Expected: PASS (4 tests). Inspect `analog-book/dist/print/sample/sample.pdf` visually once.

- [ ] **Step 6: 提交**

```bash
git add analog-book/styles/print.css analog-book/book/sample.py \
  analog-book/tests/test_book_sample.py
git commit -m "feat(book): add 16K print stylesheet and nine-page proof"
```

---

### Task 4: 站点 HTML 抽取、标题层级、锚点、链接与资源内联

**Files:**
- Create: `analog-book/book/content.py`
- Create: `analog-book/tests/test_book_content.py`
- Modify: none（旧 `build_book.py` 保持不动）

**Interfaces:**
- Consumes: `config.ROOT`、`config.DOCS`、`config.SITE_DIR`、`manifest.BookError`。
- Produces:
  - `ContentPage(stem, source, title, html, headings, images)`
  - `extract_article(site_dir: Path, name: str) -> ContentPage`
  - `assign_heading_ids(fragment: str, stem: str) -> str`
  - `namespace_ids(fragment: str, stem: str) -> str`
  - `collect_headings(fragment: str) -> list[Heading]`
  - `rewrite_links(fragment: str, current_stem: str, page_stems: set[str], manifest: dict) -> str`
  - `inline_images(fragment: str, site_dir: Path) -> tuple[str, int]`
  - `replace_mermaid(fragment: str, docs_dir: Path = config.DOCS, static_dir: Path = config.BOOK_DIR / "static") -> str`
  - `wrap_tables(fragment: str) -> str`
  - `load_page(site_dir: Path, name: str, page_stems: set[str], manifest: dict) -> ContentPage`
- 本任务只做 DOM 级处理，不改变文字、不生成编号；语义转换留给 Task 5。

- [ ] **Step 1: 先写失败测试**

Create `analog-book/tests/test_book_content.py`:

```python
#!/usr/bin/env python3
"""站点 HTML -> 书内片段：标题、锚点、链接、图片、表格与 Mermaid。"""
import sys
import tempfile
import unittest
from pathlib import Path

BOOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BOOK))

from book import content  # noqa: E402
from book.manifest import BookError  # noqa: E402

ARTICLE = '<html><body><article class="md-content__inner md-typeset">{}</article></body></html>'
MANIFEST = {"site_url": "https://example.test/book/"}


def write_site(root, name, body):
    path = root / name.replace(".md", ".html")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(ARTICLE.format(body), encoding="utf-8")
    return path


class ExtractTests(unittest.TestCase):
    def test_extracts_title_and_namespaced_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            site = Path(tmp)
            write_site(site, "p1-01-ch0.md",
                       '<h1>第 0 章 电路直觉</h1><h2 id="why">0.1 为什么</h2>'
                       '<p name="why">正文。</p>')
            page = content.extract_article(site, "p1-01-ch0.md")
            self.assertEqual(page.title, "第 0 章 电路直觉")
            self.assertIn('id="p1-01-ch0--why"', page.html)
            self.assertNotIn('name="why"', page.html)
            self.assertEqual(page.stem, "p1-01-ch0")

    def test_missing_article_and_missing_h1_raise(self):
        with tempfile.TemporaryDirectory() as tmp:
            site = Path(tmp)
            (site / "p1-01-ch0.html").write_text("<html></html>", encoding="utf-8")
            with self.assertRaisesRegex(BookError, "article"):
                content.extract_article(site, "p1-01-ch0.md")
            write_site(site, "p1-02-ch1.md", "<p>没有标题</p>")
            with self.assertRaisesRegex(BookError, "h1"):
                content.extract_article(site, "p1-02-ch1.md")


class HeadingTests(unittest.TestCase):
    def test_assigns_deterministic_ids_only_when_missing(self):
        fragment = ('<h1 id="p--title">章</h1><h2 id="p--a">0.1 A</h2>'
                    '<h2>0.2 B</h2><h3>0.2.1 C</h3>')
        result = content.assign_heading_ids(fragment, "p")
        self.assertIn('id="p--a"', result)
        self.assertIn('id="p--h2-1"', result)
        self.assertIn('id="p--h3-1"', result)
        self.assertEqual(result, content.assign_heading_ids(fragment, "p"))

    def test_collects_numbered_headings(self):
        fragment = ('<h1 id="p--title">第 0 章</h1>'
                    '<h2 id="p--s1">0.1 电压</h2>'
                    '<h2 id="p--s2">本章练习</h2>'
                    '<h3 id="p--s3">0.1.1 电位</h3>')
        headings = content.collect_headings(fragment)
        self.assertEqual([h.level for h in headings], [1, 2, 2, 3])
        self.assertEqual([h.numbered for h in headings], [False, True, False, True])
        self.assertEqual(headings[1].text, "0.1 电压")


class LinkTests(unittest.TestCase):
    def setUp(self):
        self.manifest = MANIFEST
        self.stems = {"p1-01-ch0", "p1-02-ch1"}

    def rewrite(self, href, current="p1-01-ch0"):
        return content.rewrite_links(
            f'<a href="{href}">x</a>', current, self.stems, self.manifest)

    def test_same_page_anchor(self):
        self.assertIn('href="#p1-01-ch0--sec"', self.rewrite("#sec"))

    def test_cross_page_anchor_and_page(self):
        self.assertIn('href="#p1-02-ch1--sec"',
                      self.rewrite("p1-02-ch1.html#sec"))
        self.assertIn('href="#page-p1-02-ch1"', self.rewrite("p1-02-ch1.html"))

    def test_index_and_excluded_pages_use_book_targets(self):
        self.assertIn('href="#book-toc"', self.rewrite("index.html"))
        self.assertIn('href="#book-toc"', self.rewrite("p0-07-toc.html"))
        self.assertIn('href="#part-i"', self.rewrite("p1-00-part1.html"))
        self.assertIn('href="#anim-87"',
                      self.rewrite("p5-00-part5.html#demo87"))
        self.assertIn('href="#appendix-c"', self.rewrite("p6-00-part6.html"))

    def test_external_and_assets_are_not_namespaced(self):
        self.assertIn('href="https://example.test/x"', self.rewrite("https://example.test/x"))
        self.assertIn('href="https://example.test/book/assets/a.svg"',
                      self.rewrite("assets/a.svg"))


class ResourceTests(unittest.TestCase):
    def test_inline_images_and_remote_rejection(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "assets").mkdir()
            (root / "assets" / "a.svg").write_text("<svg/>", encoding="utf-8")
            result, count = content.inline_images(
                '<p><img src="assets/a.svg" alt="a"></p>', root)
            self.assertEqual(1, count)
            self.assertIn('src="data:image/svg+xml;base64,', result)
            with self.assertRaisesRegex(BookError, "远程图片"):
                content.inline_images('<img src="https://x.test/a.png">', root)

    def test_rejects_image_outside_repo_and_site(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            outside = root / "outside.svg"
            outside.write_text("<svg/>", encoding="utf-8")
            with self.assertRaisesRegex(BookError, "不在仓库或站点目录内"):
                content._data_uri(outside, root / "site")

    def test_wrap_tables(self):
        fragment = '<table><tr><td>1</td></tr></table>'
        self.assertEqual(
            '<div class="table-wrap"><table><tr><td>1</td></tr></table></div>',
            content.wrap_tables(fragment))

    def test_mermaid_snapshot_mismatch_raises(self):
        source = (BOOK / "static" / "roadmap.source.txt").read_text(encoding="utf-8")
        fragment = '<pre class="mermaid">x</pre>'
        self.assertIn('<figure class="book-roadmap">',
                      content.replace_mermaid(fragment))
        with tempfile.TemporaryDirectory() as tmp:
            docs = Path(tmp)
            (docs / "p0-06-roadmap.md").write_text(
                "```mermaid\nflowchart LR\n  A-->B\n```\n", encoding="utf-8")
            with self.assertRaisesRegex(BookError, "不一致"):
                content.replace_mermaid(fragment, docs_dir=docs)
        self.assertTrue(source)


class LoadPageTests(unittest.TestCase):
    def test_load_page_pipeline(self):
        with tempfile.TemporaryDirectory() as tmp:
            site = Path(tmp)
            (site / "assets" / "svg").mkdir(parents=True)
            (site / "assets" / "svg" / "a.svg").write_text("<svg/>", encoding="utf-8")
            write_site(site, "p1-01-ch0.md",
                       '<h1>第 0 章</h1><h2 id="s">0.1 节</h2>'
                       '<p><img src="assets/svg/a.svg"></p><table><tr><td>1</td></tr></table>')
            page = content.load_page(
                site, "p1-01-ch0.md", {"p1-01-ch0"}, MANIFEST)
            self.assertIn("data:image/svg+xml;base64,", page.html)
            self.assertIn('<div class="table-wrap">', page.html)
            self.assertEqual(1, page.images)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 运行测试，确认失败**

Run: `python -B -m unittest discover -s analog-book/tests -p "test_book_content.py" -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'book.content'`.

- [ ] **Step 3: 实现 `content.py`**

```python
"""站点 HTML -> 书内片段：抽取、锚点、标题、链接、图片、表格与 Mermaid。"""
from __future__ import annotations

import base64
import html
import re
from dataclasses import dataclass, field
from pathlib import Path

from . import config
from .manifest import BookError

ARTICLE_RE = re.compile(
    r'<article class="md-content__inner md-typeset">(.*?)</article>', re.S)
H1_RE = re.compile(r"<h1[^>]*>(.*?)</h1>", re.S)
HEADING_RE = re.compile(
    r"<h([123])(?P<attrs>[^>]*)>(?P<body>.*?)</h\1>", re.S)
HEADING_ID_RE = re.compile(
    r'<h([123])\s+id="([^"]+)"[^>]*>(.*?)</h\1>', re.S)
TAG_RE = re.compile(r"<[^>]+>")
ID_ATTR_RE = re.compile(r'(?<![\w-])(id|name)="([^"]+)"')
NUMBERED_RE = re.compile(r"^(?:\d+|[A-H])(?:\.\d+)+")
MIME = {
    ".svg": "image/svg+xml", ".png": "image/png", ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg", ".webp": "image/webp", ".gif": "image/gif",
}
EXTERNAL_PREFIXES = ("http://", "https://", "mailto:", "tel:", "data:")
SPECIAL_TARGETS = {
    "index": "#book-toc",
    "p0-07-toc": "#book-toc",
    "p1-00-part1": "#part-i",
    "p2-00-part2": "#part-ii",
    "p3-00-part3": "#part-iii",
    "p4-00-part4": "#part-iv",
    "p5-00-part5": "#appendix-a",
    "p6-00-part6": "#appendix-c",
    "p7-00-part7": "#appendix-d",
    "p8-00-part8": "#appendix-d",
}


@dataclass(frozen=True)
class Heading:
    level: int
    text: str
    anchor: str
    numbered: bool


@dataclass
class ContentPage:
    stem: str
    source: str
    title: str
    html: str
    headings: list[Heading] = field(default_factory=list)
    images: int = 0


def plain_text(fragment: str) -> str:
    # 源码里必须写成转义，避免 fonts.required_text() 把 ¶ 当成需要出图的字符。
    return re.sub(r"\s+", " ", html.unescape(TAG_RE.sub("", fragment))).replace(
        "\u00b6", "").strip()


def clean_fragment(fragment: str) -> str:
    fragment = re.sub(r'<a[^>]+class="md-content__button md-icon".*?</a>', "", fragment, flags=re.S)
    fragment = re.sub(r'<a class="headerlink".*?</a>', "", fragment, flags=re.S)
    fragment = re.sub(r'<div class="legacy-anchor".*?</div>', "", fragment, flags=re.S)
    fragment = re.sub(r"<hr\s*/?>\s*<blockquote>\s*<p>✍️ <strong>参与共建.*$", "",
                      fragment, flags=re.S)
    fragment = re.sub(r"\s+data-study-video(?:=\"[^\"]*\")?", "", fragment)
    # 题库页靠 <details> 解析答案；非题库页随后由 transforms.unwrap_details 展开。
    fragment = re.sub(r"<details(?![^>]*\bopen\b)", "<details open", fragment)
    fragment = fragment.replace(' loading="lazy"', "")
    return fragment.strip()


def _drop_duplicate_name(match: re.Match) -> str:
    tag = match.group(0)
    name = re.search(r'(?<![\w-])name="([^"]+)"', tag)
    if name is None:
        return tag
    value = name.group(1)
    if re.search(r'(?<![\w-])id="%s"' % re.escape(value), tag):
        return tag[:name.start()] + tag[name.end():]
    return tag


def namespace_ids(fragment: str, stem: str) -> str:
    prefix = stem + "--"

    def rewrite_tag(match: re.Match) -> str:
        tag = _drop_duplicate_name(match)
        return ID_ATTR_RE.sub(
            lambda m: '%s="%s%s"' % (m.group(1), prefix, m.group(2)), tag)

    # 只改标签内部；转义文本里的 id="..." 必须原样保留。
    return TAG_RE.sub(rewrite_tag, fragment)


def assign_heading_ids(fragment: str, stem: str) -> str:
    counters = {2: 0, 3: 0}
    used = set()
    for tag in TAG_RE.findall(fragment):
        used.update(m.group(2) for m in ID_ATTR_RE.finditer(tag)
                    if m.group(1) == "id")

    def repl(match: re.Match) -> str:
        level, attrs, body = int(match.group(1)), match.group(2), match.group(3)
        if level == 1 or re.search(r'(?<![\w-])id="[^"]+"', attrs):
            return match.group(0)
        while True:
            counters[level] += 1
            anchor = f"{stem}--h{level}-{counters[level]}"
            if anchor not in used:
                break
        used.add(anchor)
        return f'<h{level} id="{anchor}"{attrs}>{body}</h{level}>'

    return HEADING_RE.sub(repl, fragment)


def collect_headings(fragment: str) -> list[Heading]:
    result = []
    for match in HEADING_ID_RE.finditer(fragment):
        level = int(match.group(1))
        text = plain_text(match.group(3))
        result.append(Heading(
            level=level, text=text, anchor=match.group(2),
            numbered=level > 1 and bool(NUMBERED_RE.match(text))))
    return result


def _special_target(stem: str, anchor: str) -> str:
    if stem == "p5-00-part5" and anchor.startswith("demo"):
        return "#anim-" + anchor[4:]
    return SPECIAL_TARGETS.get(stem, "#book-toc")


def rewrite_links(fragment: str, current_stem: str, page_stems: set[str],
                  manifest: dict) -> str:
    site_url = manifest["site_url"].rstrip("/") + "/"

    def repl(match: re.Match) -> str:
        href = match.group(1)
        if not href or href == "#" or href.startswith(EXTERNAL_PREFIXES):
            return match.group(0)
        path, _, anchor = href.partition("#")
        if path.startswith("#"):
            return f'href="#{current_stem}--{path[1:]}"'
        name = path.rsplit("/", 1)[-1]
        if name.endswith(".html"):
            stem = name[:-5]
            if stem in page_stems:
                target = f"page-{stem}" if not anchor else f"{stem}--{anchor}"
                return f'href="#{target}"'
            return f'href="{_special_target(stem, anchor)}"'
        if path.startswith("assets/"):
            return f'href="{site_url}{href}"'
        return f'href="{site_url}{href.lstrip("/")}"'

    return re.sub(r'href="([^"]+)"', repl, fragment)


def _asset_path(rel: str, site_dir: Path) -> Path:
    for base in (config.ROOT, site_dir):
        candidate = (base / rel).resolve()
        if candidate.is_file():
            return candidate
    raise BookError(f"图片不存在: {rel}")


def _data_uri(path: Path, *allowed_roots: Path) -> str:
    resolved = path.resolve()
    if not resolved.is_file():
        raise BookError(f"图片不存在: {path}")
    roots = allowed_roots or (config.ROOT,)
    if not any(resolved.is_relative_to(root.resolve()) for root in roots):
        raise BookError(f"图片不在仓库或站点目录内: {path}")
    mime = MIME.get(resolved.suffix.lower())
    if mime is None:
        raise BookError(f"不支持的图片类型: {path}")
    return f"data:{mime};base64," + base64.b64encode(resolved.read_bytes()).decode("ascii")


def inline_images(fragment: str, site_dir: Path) -> tuple[str, int]:
    count = 0

    def source(match: re.Match) -> str:
        nonlocal count
        count += 1
        target = _asset_path(match.group(2), site_dir)
        return f'{match.group(1)}="{_data_uri(target, config.ROOT, site_dir)}"'

    fragment = re.sub(r'(?<![\w-])(src)="(assets/[^"]+)"', source, fragment)
    fragment = re.sub(r'(?<![\w-])(srcset)="(assets/[^"]+)"', source, fragment)
    remote = re.search(r'(?<![\w-])(?:src|srcset)="(https?://[^"]+)"', fragment)
    if remote:
        raise BookError(f"书内仍有远程图片: {remote.group(1)}")
    return fragment, count


def replace_mermaid(fragment: str, docs_dir: Path = config.DOCS,
                    static_dir: Path = config.BOOK_DIR / "static") -> str:
    if '<pre class="mermaid">' not in fragment:
        return fragment
    snapshot = static_dir / "roadmap.svg"
    source_file = static_dir / "roadmap.source.txt"
    if not snapshot.is_file() or not source_file.is_file():
        raise BookError("缺少 static/roadmap.svg 或 static/roadmap.source.txt")
    doc = (docs_dir / "p0-06-roadmap.md").read_text(encoding="utf-8")
    match = re.search(r"```mermaid\n(.*?)```", doc, re.S)
    if match is None:
        raise BookError("docs/p0-06-roadmap.md 缺少 mermaid 代码块")
    source = match.group(1).strip() + "\n"
    if source != source_file.read_text(encoding="utf-8"):
        raise BookError("docs/p0-06-roadmap.md 与 static/roadmap.source.txt 不一致")
    svg = snapshot.read_text(encoding="utf-8").strip()
    return re.sub(r'<pre class="mermaid">.*?</pre>',
                  '<figure class="book-roadmap">' + svg + "</figure>",
                  fragment, flags=re.S)


def wrap_tables(fragment: str) -> str:
    def wrap(match: re.Match) -> str:
        before = fragment[:match.start()]
        if re.search(r'<div class="table-wrap"[^>]*>\s*$', before):
            return match.group(0)
        return f'<div class="table-wrap">{match.group(0)}</div>'

    return re.sub(r'<table(?:\s[^>]*)?>.*?</table>', wrap,
                  fragment, flags=re.S)


def extract_article(site_dir: Path, name: str) -> ContentPage:
    path = site_dir / name.replace(".md", ".html")
    page = path.read_text(encoding="utf-8")
    match = ARTICLE_RE.search(page)
    if not match:
        raise BookError(f"{path.name}: 找不到 <article>")
    fragment = clean_fragment(match.group(1))
    h1 = H1_RE.search(fragment)
    if not h1:
        raise BookError(f"{path.name}: <article> 中缺少 <h1>")
    title = plain_text(h1.group(1))
    if not title:
        raise BookError(f"{path.name}: <h1> 标题为空")
    stem = Path(name).stem
    fragment = assign_heading_ids(namespace_ids(fragment, stem), stem)
    return ContentPage(stem=stem, source=name, title=title, html=fragment,
                       headings=collect_headings(fragment))


def load_page(site_dir: Path, name: str, page_stems: set[str],
              manifest: dict) -> ContentPage:
    page = extract_article(site_dir, name)
    fragment = replace_mermaid(page.html)
    fragment = rewrite_links(fragment, page.stem, page_stems, manifest)
    fragment, images = inline_images(fragment, site_dir)
    page.html = wrap_tables(fragment)
    page.images = images
    return page
```

- [ ] **Step 4: 运行测试，确认通过**

Run: `python -B -m unittest discover -s analog-book/tests -p "test_book_content.py" -v`
Expected: PASS (18 tests；除上面 13 个外，另含 5 个回归：`wrap_tables` 幂等、转义文本 `id="..."` 原样保留、生成标题 ID 避让已有 ID、`assets/` 链接行为、Mermaid 缺 code fence 报 `BookError`)。

- [ ] **Step 5: 提交**

```bash
git add analog-book/book/content.py analog-book/tests/test_book_content.py
git commit -m "feat(book): extract site HTML into namespaced page fragments"
```

---

### Task 5: 去 emoji、展开折叠块、语义提示框、图表编号、尾注与计算器兜底校验

**Files:**
- Create: `analog-book/book/transforms.py`
- Create: `analog-book/tests/test_book_figures.py`
- Modify: none

**Interfaces:**
- Consumes: `content.plain_text()`、`manifest.BookError`。
- Produces:
  - `strip_emoji(fragment: str) -> str`
  - `unwrap_details(fragment: str) -> str`
  - `transform_callouts(fragment: str) -> str`
  - `number_figures(fragment, label, stem, final=False) -> tuple[str, list[dict], list[str]]`
  - `number_tables(fragment, label, stem, final=False) -> tuple[str, list[dict], list[str]]`
  - `transform_endnotes(fragment, stem) -> tuple[str, list[dict]]`
  - `check_calculator_fallbacks(fragment, stem, final=False) -> list[str]`
  - `chapter_label(stem: str, appendix_id: str | None = None) -> str | None`
- 规则（与规格 §9.4 一致）：
  - 非题库页的 `<details>` 折叠块展开为可见的 `.book-reveal`：`<summary>` 变标题、正文原样保留；书中不得残留 `<details>`/`<summary>`。题库页在 `parse_quiz` 之前**不得**展开。
  - 图注/表注必须已在源内容中存在；构建只加编号，**不拿 alt 猜标题**。草稿无注记入 warning，`final` 直接失败。
  - `.calc` 必须有相邻的“例 N-x / 算一笔 / 再算一笔”或 `.calc-print`；草稿 warning，`final` 失败。
  - 外部链接转章末尾注，同章同 URL 只留一条；站内锚点不受影响。
  - `✅/❌/⚠️` 映射为 `✓/✗/注意`，其余装饰 emoji 删除；数学符号与箭头保留。

- [ ] **Step 1: 先写失败测试**

Create `analog-book/tests/test_book_figures.py`:

```python
#!/usr/bin/env python3
"""书内语义转换：emoji、提示框、图表编号、尾注与计算器兜底。"""
import sys
import unittest
from pathlib import Path

BOOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BOOK))

from book import transforms  # noqa: E402
from book.manifest import BookError  # noqa: E402


class EmojiAndCalloutTests(unittest.TestCase):
    def test_maps_check_marks_and_drops_decoration(self):
        text = transforms.strip_emoji(
            "<p>✅ 对，❌ 错，⚠️ 注意，🚀 直觉，α→β，R≤10kΩ</p>")
        self.assertIn("✓ 对", text)
        self.assertIn("✗ 错", text)
        self.assertIn("注意 注意", text)
        self.assertNotIn("🚀", text)
        self.assertIn("α→β", text)
        self.assertIn("R≤10kΩ", text)

    def test_semantic_callout_gets_label_and_keeps_body(self):
        fragment = ('<div class="callout callout-goal"><p>🎯 <strong>学完你应能</strong>：'
                    '看懂分压。</p></div>')
        result = transforms.transform_callouts(transforms.strip_emoji(fragment))
        self.assertIn('<aside class="book-callout book-callout-goal"', result)
        self.assertIn('data-label="学习目标"', result)
        self.assertIn('<p class="callout-label">学习目标</p>', result)
        self.assertIn("看懂分压。", result)
        self.assertNotIn("学完你应能", result)

    def test_unknown_callout_becomes_plain_quote(self):
        fragment = '<div class="callout callout-mystery"><p>正文</p></div>'
        result = transforms.transform_callouts(fragment)
        self.assertIn('<blockquote class="book-quote">', result)
        self.assertNotIn("callout-mystery", result)


class DetailsTests(unittest.TestCase):
    def test_details_become_visible_blocks(self):
        fragment = ('<details open><summary>展开公式</summary>'
                    '<p>正文 <strong>加粗</strong>。</p></details>'
                    '<details><summary>自测</summary><p>答案。</p></details>')
        result = transforms.unwrap_details(fragment)
        self.assertNotIn("<details", result)
        self.assertNotIn("<summary", result)
        self.assertEqual(2, result.count('class="book-reveal"'))
        self.assertIn('class="book-reveal-title">展开公式<', result)
        self.assertIn('正文 <strong>加粗</strong>。', result)
        self.assertIn('class="book-reveal-title">自测<', result)


class FigureTests(unittest.TestCase):
    def test_numbers_captioned_figure_and_records_entry(self):
        fragment = ('<figure><img src="data:image/svg+xml;base64,AA" alt="波形">'
                    '<figcaption>共射输出削顶</figcaption></figure>')
        result, entries, warnings = transforms.number_figures(
            fragment, "3", "p1-04-ch3")
        self.assertIn('id="p1-04-ch3--fig-1"', result)
        self.assertIn("图 3-1　共射输出削顶", result)
        self.assertEqual([], warnings)
        self.assertEqual("图 3-1", entries[0]["number"])
        self.assertEqual("p1-04-ch3--fig-1", entries[0]["anchor"])

    def test_uncaptioned_figure_warns_in_draft_and_fails_final(self):
        fragment = '<figure><img src="data:image/svg+xml;base64,AA" alt="波形"></figure>'
        _, entries, warnings = transforms.number_figures(
            fragment, "3", "p1-04-ch3")
        self.assertEqual([], entries)
        self.assertTrue(warnings)
        with self.assertRaisesRegex(BookError, "图注"):
            transforms.number_figures(fragment, "3", "p1-04-ch3", final=True)

    def test_table_caption_precedes_wrapped_table(self):
        fragment = ('<p><strong>表 2-1　二极管三种工作区</strong></p>'
                    '<table><tr><td>1</td></tr></table>')
        wrapped, entries, warnings = transforms.number_tables(
            fragment, "2", "p1-03-ch2")
        self.assertIn('class="table-wrap"', wrapped)
        self.assertIn("表 2-1", wrapped)
        self.assertEqual("表 2-1", entries[0]["number"])
        self.assertEqual([], warnings)

    def test_uncaptioned_table_warns(self):
        result, entries, warnings = transforms.number_tables(
            "<table><tr><td>1</td></tr></table>", "2", "p1-03-ch2")
        self.assertIn('<div class="table-wrap">', result)
        self.assertEqual([], entries)
        self.assertTrue(warnings)


class EndnoteTests(unittest.TestCase):
    def test_deduplicates_and_appends_notes(self):
        fragment = ('<p><a href="https://a.test/x">资料甲</a> 与 '
                    '<a href="https://a.test/x">资料甲</a> 与 '
                    '<a href="mailto:a@b.test">邮件</a>。</p>'
                    '<p><a href="#p1-01-ch0--s">站内</a></p>')
        result, notes = transforms.transform_endnotes(fragment, "p1-01-ch0")
        self.assertEqual(2, len(notes))
        self.assertIn('id="p1-01-ch0--note-ref-1"', result)
        self.assertIn('id="p1-01-ch0--note-ref-2"', result)
        self.assertNotIn('href="https://a.test/x"', result)
        self.assertIn('href="#p1-01-ch0--s"', result)
        self.assertIn("chapter-endnotes", result)

    def test_note_ids_are_stable_and_unique(self):
        fragment = '<a href="https://a.test/1">1</a><a href="https://a.test/2">2</a>'
        result, notes = transforms.transform_endnotes(fragment, "p")
        ids = [note["id"] for note in notes]
        self.assertEqual(["p--note-1", "p--note-2"], ids)
        self.assertEqual(result, transforms.transform_endnotes(fragment, "p")[0])


class CalculatorTests(unittest.TestCase):
    def test_adjacent_example_is_accepted(self):
        fragment = ('<div class="calc" data-calc="divider"></div>'
                    '<p><strong>例 0-1</strong>：分压器带载。</p>')
        self.assertEqual([], transforms.check_calculator_fallbacks(
            fragment, "p1-01-ch0"))

    def test_missing_fallback_warns_then_fails(self):
        fragment = '<div class="calc" data-calc="opamp"></div><p>无关正文。</p>'
        warnings = transforms.check_calculator_fallbacks(fragment, "p1-07-ch6")
        self.assertEqual(1, len(warnings))
        with self.assertRaisesRegex(BookError, "计算器"):
            transforms.check_calculator_fallbacks(
                fragment, "p1-07-ch6", final=True)

    def test_chapter_and_appendix_labels(self):
        self.assertEqual("0", transforms.chapter_label("p1-01-ch0"))
        self.assertEqual("18", transforms.chapter_label("p4-03-ch18"))
        self.assertIsNone(transforms.chapter_label("p0-01-preface"))
        self.assertEqual("C", transforms.chapter_label("p6-01-s6-1", "C"))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 运行测试，确认失败**

Run: `python -B -m unittest discover -s analog-book/tests -p "test_book_figures.py" -v`
Expected: FAIL with `No module named 'book.transforms'`.

- [ ] **Step 3: 实现 `transforms.py`**

```python
"""书内语义转换：去 emoji、展开折叠块、提示框、图表编号、尾注与计算器兜底。"""
from __future__ import annotations

import html
import re

from .content import plain_text, wrap_tables
from .manifest import BookError

EMOJI_MAP = (("✅", "✓"), ("❌", "✗"), ("⚠️", "注意"), ("⚠", "注意"))
EMOJI_RE = re.compile(
    "[\U0001F000-\U0001FAFF\u2300-\u23FF\u2600-\u27BF\u2B00-\u2BFF"
    "\uFE0F\u200D]+")
CALLOUT_LABELS = {
    "goal": "学习目标", "prereq": "先修", "calc": "公式速查",
    "limit": "模型边界", "gem": "精髓", "warn": "注意",
    "fix": "修复方法", "idea": "设计直觉", "video": "配套视频",
    "demo": "动画演示", "photo": "实测记录", "attach": "附件",
    "pin": "记忆锚点", "link": "延伸阅读",
}
CALLOUT_RE = re.compile(
    r'<div class="callout callout-([a-z]+)">(.*?)</div>', re.S)
LEADING_TITLE_RE = re.compile(
    r"<p>\s*<strong>([^<]{1,20})</strong>\s*[：:]\s*", re.S)
FIGURE_RE = re.compile(r"<figure(?P<attrs>[^>]*)>(?P<body>.*?)</figure>", re.S)
FIGCAPTION_RE = re.compile(r"<figcaption[^>]*>(?P<cap>.*?)</figcaption>", re.S)
TABLE_CAPTION_RE = re.compile(
    r"<p[^>]*>\s*<strong>\s*(表\s*[0-9A-H]+-\d+[^<]*)</strong>\s*</p>\s*"
    r"<div class=\"table-wrap\">(?P<table><table.*?</table>)</div>", re.S)
LINK_RE = re.compile(
    r'<a\s+(?P<pre>[^>]*?)href="(?P<href>[^"]+)"(?P<post>[^>]*)>(?P<text>.*?)</a>',
    re.S)
CALC_RE = re.compile(r'<div class="calc" data-calc="([^"]+)"></div>')
CHAPTER_RE = re.compile(r"-ch(\d+)$")
FALLBACK_RE = re.compile(r'class="calc-print"|例\s*\d+-\d+|算一笔|再算一笔')
DETAILS_RE = re.compile(
    r"<details(?:\s[^>]*)?>\s*<summary>(?P<title>.*?)</summary>"
    r"(?P<body>.*?)</details>", re.S)


def strip_emoji(fragment: str) -> str:
    placeholders = {}
    for index, (emoji, replacement) in enumerate(EMOJI_MAP):
        token = f"\ue000{index}\ue001"
        if emoji in fragment:
            placeholders[token] = replacement
            fragment = fragment.replace(emoji, token)
    fragment = EMOJI_RE.sub("", fragment)
    for token, replacement in placeholders.items():
        fragment = fragment.replace(token, replacement)
    return fragment


def unwrap_details(fragment: str) -> str:
    def repl(match: re.Match) -> str:
        title = match.group("title").strip()
        body = match.group("body").strip()
        return ('<div class="book-reveal">'
                f'<p class="book-reveal-title">{title}</p>{body}</div>')

    return DETAILS_RE.sub(repl, fragment)


def transform_callouts(fragment: str) -> str:
    def repl(match: re.Match) -> str:
        slug, body = match.group(1), match.group(2)
        label = CALLOUT_LABELS.get(slug)
        if label is None:
            return f'<blockquote class="book-quote">{body}</blockquote>'
        body = LEADING_TITLE_RE.sub("<p>", body, count=1)
        return (f'<aside class="book-callout book-callout-{slug}" '
                f'data-label="{label}" role="note">'
                f'<p class="callout-label">{label}</p>{body}</aside>')

    return CALLOUT_RE.sub(repl, fragment)


def chapter_label(stem: str, appendix_id: str | None = None) -> str | None:
    if appendix_id:
        return appendix_id
    match = CHAPTER_RE.search(stem)
    return str(int(match.group(1))) if match else None


def number_figures(fragment: str, label: str, stem: str,
                   final: bool = False) -> tuple[str, list[dict], list[str]]:
    counter = 0
    entries, warnings = [], []

    def repl(match: re.Match) -> str:
        nonlocal counter
        body = match.group("body")
        caption_match = FIGCAPTION_RE.search(body)
        if caption_match is None:
            warnings.append(f"{stem}: 图片缺少 <figcaption> 图注，未编号")
            return match.group(0)
        counter += 1
        number = f"图 {label}-{counter}"
        caption = plain_text(caption_match.group("cap"))
        if not caption:
            warnings.append(f"{stem}: 图注为空")
            return match.group(0)
        if not caption.startswith(number):
            caption = f"{number}　{caption}"
            body = body[:caption_match.start()] + (
                f'<figcaption>{html.escape(caption)}</figcaption>') + body[caption_match.end():]
        anchor = re.search(r'(?<![\w-])id="([^"]+)"', match.group("attrs"))
        anchor_id = anchor.group(1) if anchor else f"{stem}--fig-{counter}"
        attrs = match.group("attrs")
        if anchor is None:
            attrs += f' id="{anchor_id}"'
        entries.append({"number": number, "caption": caption,
                        "anchor": anchor_id, "stem": stem})
        return f'<figure{attrs}>{body}</figure>'

    result = FIGURE_RE.sub(repl, fragment)
    if final and warnings:
        raise BookError("图注校验失败:\n" + "\n".join(warnings))
    return result, entries, warnings


def number_tables(fragment: str, label: str, stem: str,
                  final: bool = False) -> tuple[str, list[dict], list[str]]:
    fragment = wrap_tables(fragment)
    counter = 0
    entries, warnings = [], []

    def repl(match: re.Match) -> str:
        nonlocal counter
        counter += 1
        raw = plain_text(match.group(1))
        number = f"表 {label}-{counter}"
        caption = raw if raw.startswith(number) else f"{number}　{raw}"
        anchor = f"{stem}--table-{counter}"
        entries.append({"number": number, "caption": caption,
                        "anchor": anchor, "stem": stem})
        return (f'<div class="table-wrap" id="{anchor}">'
                f'<p class="table-caption">{html.escape(caption)}</p>'
                f'{match.group("table")}</div>')

    result = TABLE_CAPTION_RE.sub(repl, fragment)
    remaining = len(re.findall(r'<div class="table-wrap">', result))
    if remaining:
        warnings.append(f"{stem}: {remaining} 个表格缺少“表 X-Y”表注，未编号")
    if final and warnings:
        raise BookError("表注校验失败:\n" + "\n".join(warnings))
    return result, entries, warnings


def transform_endnotes(fragment: str, stem: str) -> tuple[str, list[dict]]:
    notes, seen = [], {}

    def repl(match: re.Match) -> str:
        href = match.group("href")
        if href.startswith("#"):
            return match.group(0)
        number = seen.get(href)
        if number is None:
            number = len(notes) + 1
            seen[href] = number
            notes.append({"number": number, "id": f"{stem}--note-{number}",
                          "href": href, "text": plain_text(match.group("text"))})
        anchor = f"{stem}--note-{number}"
        return (f'{match.group("text")}<sup class="endnote-ref">'
                f'<a href="#{anchor}" id="{stem}--note-ref-{number}">{number}</a></sup>')

    result = LINK_RE.sub(repl, fragment)
    if not notes:
        return result, []
    items = "".join(
        f'<li id="{note["id"]}"><span class="endnote-text">'
        f'{html.escape(note["text"])}</span> '
        f'<span class="endnote-url">{html.escape(note["href"])}</span></li>'
        for note in notes)
    section = (
        f'<section class="chapter-endnotes" id="{stem}--notes">'
        f'<h2 class="endnotes-title">注释与链接</h2>'
        f'<ol class="endnote-list">{items}</ol></section>')
    return result + section, notes


def check_calculator_fallbacks(fragment: str, stem: str,
                               final: bool = False) -> list[str]:
    warnings = []
    for match in CALC_RE.finditer(fragment):
        tail = fragment[match.end():match.end() + 1600]
        if not FALLBACK_RE.search(tail):
            warnings.append(f"{stem}: 计算器 {match.group(1)} 附近没有印刷替代"
                            "（例 N-x / 算一笔 / .calc-print）")
    if final and warnings:
        raise BookError("计算器兜底校验失败:\n" + "\n".join(warnings))
    return warnings
```

- [ ] **Step 4: 运行测试，确认通过**

Run: `python -B -m unittest discover -s analog-book/tests -p "test_book_figures.py" -v`
Expected: PASS (13 tests).

- [ ] **Step 5: 提交**

```bash
git add analog-book/book/transforms.py analog-book/tests/test_book_figures.py
git commit -m "feat(book): add semantic callouts, numbering and endnotes"
```

---

### Task 6: 数据 schema、108 条动画台账、索引种子与审读/来源校验

**Files:**
- Create: `analog-book/book/data.py`
- Create: `scripts/build_book_data.py`
- Create: `analog-book/data/animations.yml`
- Create: `analog-book/data/index-terms.yml`
- Create: `analog-book/data/sources.yml`
- Create: `analog-book/data/references.yml`
- Create: `analog-book/data/chapter-signoff.yml`
- Create: `analog-book/tests/test_book_data.py`
- Modify: `analog-book/requirements.txt`（Task 2 已加入 `pypinyin`；本任务安装并验证）

**Interfaces:**
- Consumes: `config.ROOT`、`config.DOCS`、`manifest.BookError`、`pypinyin`、`PyYAML`。
- Produces:
  - `load_list(path: Path) -> list[dict]`
  - `validate_animations(items, static_root=config.ROOT) -> None`
  - `validate_index_terms(items, anchors: set[str], final=False) -> None`
  - `validate_sources(items, used_ids: set[str] | None = None, final=False) -> None`
  - `validate_signoffs(items, final=False) -> None`
  - `validate_references(items, final=False) -> None`
  - `pinyin_key(term: str) -> str`
  - `index_sections(terms: list[dict]) -> list[tuple[str, list[dict]]]`
  - `used_source_ids(fragment: str) -> set[str]`
- 数据文件 UTF-8、两空格缩进、英文键名；缺字段/未知字段/重复项立即失败。草稿只强制结构，`final` 才强制 300 条索引、100 条文献、审读签字与来源闭合。

- [ ] **Step 1: 先写失败测试**

Create `analog-book/tests/test_book_data.py`:

```python
#!/usr/bin/env python3
"""数据台账：动画 108、索引、来源、审读、文献与拼音排序。"""
import copy
import sys
import tempfile
import unittest
from pathlib import Path

BOOK = Path(__file__).resolve().parent.parent
ROOT = BOOK.parent
sys.path.insert(0, str(BOOK))
sys.path.insert(0, str(ROOT / "scripts"))

from book import data  # noqa: E402
from book.manifest import BookError  # noqa: E402
import book_fixtures  # noqa: E402


def fixture_data():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        data_dir = book_fixtures.write_data(root / "data")
        (root / "assets" / "svg").mkdir(parents=True)
        (root / "assets" / "svg" / "fixture.svg").write_text("<svg/>", encoding="utf-8")
        return (data.load_list(data_dir / "animations.yml"),
                data.load_list(data_dir / "index-terms.yml"),
                root)


class AnimationTests(unittest.TestCase):
    def test_fixture_has_108_and_covers_every_chapter(self):
        items, _, root = fixture_data()
        data.validate_animations(items, static_root=root)
        chapters = {item["chapter"] for item in items}
        self.assertEqual(set(range(19)), chapters)

    def test_rejects_duplicate_and_missing_file(self):
        items, _, root = fixture_data()
        broken = copy.deepcopy(items)
        broken[1]["anchor"] = broken[0]["anchor"]
        with self.assertRaisesRegex(BookError, "anchor"):
            data.validate_animations(broken, static_root=root)
        broken = copy.deepcopy(items)
        broken[0]["static_svg"] = "assets/svg/missing.svg"
        with self.assertRaisesRegex(BookError, "不存在"):
            data.validate_animations(broken, static_root=root)

    def test_real_generator_matches_committed_yaml(self):
        import build_book_data
        generated = build_book_data.build_animations()
        self.assertEqual(108, len(generated))
        committed = data.load_list(BOOK / "data" / "animations.yml")
        self.assertEqual(generated, committed)
        data.validate_animations(committed)


class IndexTests(unittest.TestCase):
    def test_anchors_must_exist_and_terms_are_unique(self):
        terms = [{"term": "米勒效应", "english": "Miller effect",
                  "primary": "page-p1-01-ch0", "anchors": ["page-p1-01-ch0"],
                  "see_also": []}]
        data.validate_index_terms(terms, {"page-p1-01-ch0"})
        with self.assertRaisesRegex(BookError, "锚点"):
            data.validate_index_terms(terms, {"page-other"})
        duplicated = terms + copy.deepcopy(terms)
        with self.assertRaisesRegex(BookError, "重复"):
            data.validate_index_terms(duplicated, {"page-p1-01-ch0"})

    def test_final_requires_300_terms(self):
        anchor = "page-p1-01-ch0"
        terms = [{"term": f"术语{i:03d}", "english": f"Term {i}",
                  "primary": anchor, "anchors": [anchor], "see_also": []}
                 for i in range(300)]
        data.validate_index_terms(terms, {anchor}, final=True)
        with self.assertRaisesRegex(BookError, "300"):
            data.validate_index_terms(terms[:-1], {anchor}, final=True)

    def test_pinyin_sorting_and_sections(self):
        terms = [{"term": "欧姆定律", "english": "Ohm's law",
                  "primary": "p", "anchors": ["p"], "see_also": []},
                 {"term": "米勒效应", "english": "Miller effect",
                  "primary": "p", "anchors": ["p"], "see_also": []}]
        self.assertTrue(data.pinyin_key("米勒效应").startswith("mile"))
        sections = data.index_sections(terms)
        self.assertEqual(["M", "O"], [letter for letter, _ in sections])
        self.assertEqual("米勒效应", sections[0][1][0]["term"])


class SourceTests(unittest.TestCase):
    def source(self, **overrides):
        item = {"id": "ch06-datasheet-lm358", "chapter": 6,
                "claim": "LM358 的 GBW 约 0.7MHz", "source_type": "数据手册",
                "citation": "Texas Instruments, LM358 datasheet, 2023",
                "url_or_doi": "https://example.test/lm358.pdf",
                "verified_on": "2026-10-20", "verifier": "zuguang"}
        item.update(overrides)
        return item

    def test_final_requires_all_used_and_no_unused(self):
        item = self.source()
        data.validate_sources([item], {"ch06-datasheet-lm358"}, final=True)
        with self.assertRaisesRegex(BookError, "未使用"):
            data.validate_sources([item], set(), final=True)
        with self.assertRaisesRegex(BookError, "不存在"):
            data.validate_sources([item], {"ch06-datasheet-lm358", "missing"},
                                  final=True)

    def test_rejects_unknown_type_and_bad_date(self):
        with self.assertRaisesRegex(BookError, "source_type"):
            data.validate_sources([self.source(source_type="博客")])
        with self.assertRaisesRegex(BookError, "verified_on"):
            data.validate_sources([self.source(verified_on="2026/10/20")])

    def test_marks_in_fragments(self):
        fragment = ('<sup class="source-ref" data-source="ch06-datasheet-lm358"></sup>'
                    '<p data-source="ch06-datasheet-lm358">x</p>')
        self.assertEqual({"ch06-datasheet-lm358"}, data.used_source_ids(fragment))


class SignoffAndReferenceTests(unittest.TestCase):
    def test_signoff_draft_then_final(self):
        items = [{"chapter": i, "draft_version": "2.0.0-draft.1",
                  "technical_reviewer": "", "editorial_reviewer": "",
                  "safety_reviewer": "", "date": "2026-10-25",
                  "open_issues": []} for i in range(19)]
        data.validate_signoffs(items)
        with self.assertRaisesRegex(BookError, "technical_reviewer"):
            data.validate_signoffs(items, final=True)
        for item in items:
            item.update(technical_reviewer="t", editorial_reviewer="e",
                        safety_reviewer="s")
        data.validate_signoffs(items, final=True)
        items[0]["open_issues"] = ["待核"]
        with self.assertRaisesRegex(BookError, "open_issues"):
            data.validate_signoffs(items, final=True)

    def test_references_final_minimum(self):
        item = {"id": "ref-001", "authors": "Horowitz, P.; Hill, W.",
                "title": "The Art of Electronics", "edition": "3rd",
                "publisher": "Cambridge University Press", "year": 2015,
                "isbn_or_url": "978-0521809269", "chapters": [1, 6, 11, 12]}
        data.validate_references([item])
        with self.assertRaisesRegex(BookError, "100"):
            data.validate_references([item], final=True)
        hundred = [dict(item, id=f"ref-{i:03d}", title=f"Book {i}")
                   for i in range(100)]
        data.validate_references(hundred, final=True)


if __name__ == "__main__":
    unittest.main()
```

评审补充（已回写实现）：`fixture_data()` 不能在 `with TemporaryDirectory()` 内直接返回，测试用模块级 `_TEMPDIRS` 持有临时目录到进程退出；另补 3 个测试——`test_one_line_summaries_are_well_formed`（摘要 ≤120 字、`$` 成对、全角括号配平、不以 `、，；：,;:（→` 结尾）、`test_committed_seed_files_validate`（真实 `data/` 的 108/40/19/0/0 与锚点校验）、`test_final_source_closure_requires_fragments`（final 必须提供正文片段）。本任务共 14 个测试。

- [ ] **Step 2: 安装依赖并确认测试失败**

```bash
python -m pip install -r analog-book/requirements.txt
python -B -m unittest discover -s analog-book/tests -p "test_book_data.py" -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'book.data'`.

- [ ] **Step 3: 实现 `data.py`**

```python
"""书内数据台账：动画、索引、来源、审读签字与参考文献。"""
from __future__ import annotations

import re
from pathlib import Path

import yaml
from pypinyin import Style, lazy_pinyin

from . import config
from .manifest import BookError

ANIMATION_FIELDS = {"id", "file", "title", "chapter", "anchor", "one_line", "static_svg"}
INDEX_FIELDS = {"term", "english", "primary", "anchors", "see_also"}
SOURCE_FIELDS = {"id", "chapter", "claim", "source_type", "citation",
                 "url_or_doi", "verified_on", "verifier"}
REFERENCE_FIELDS = {"id", "authors", "title", "edition", "publisher",
                    "year", "isbn_or_url", "chapters"}
SIGNOFF_FIELDS = {"chapter", "draft_version", "technical_reviewer",
                  "editorial_reviewer", "safety_reviewer", "date", "open_issues"}
SOURCE_TYPES = {"教材", "数据手册", "应用笔记", "论文", "仓库实测", "仿真"}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def load_list(path: Path) -> list[dict]:
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise BookError(f"{path.name}: YAML 解析失败: {exc}") from exc
    if not isinstance(value, list):
        raise BookError(f"{path.name}: 顶层必须是列表")
    if not all(isinstance(item, dict) for item in value):
        raise BookError(f"{path.name}: 列表项必须是映射")
    return value


def _fields(item: dict, expected: set[str], where: str) -> None:
    missing = sorted(expected - item.keys())
    unknown = sorted(item.keys() - expected)
    if missing:
        raise BookError(f"{where}: 缺字段 {missing}")
    if unknown:
        raise BookError(f"{where}: 未知字段 {unknown}")


def _nonempty(item: dict, names: tuple[str, ...], where: str) -> None:
    for name in names:
        value = item[name]
        if not isinstance(value, str) or not value.strip():
            raise BookError(f"{where}: {name} 不能为空")


def validate_animations(items: list[dict], static_root: Path = config.ROOT) -> None:
    if len(items) != 108:
        raise BookError(f"animations.yml 应恰好 108 条，实际 {len(items)}")
    ids, anchors = set(), set()
    for index, item in enumerate(items, 1):
        where = f"animations.yml 第 {index} 条"
        _fields(item, ANIMATION_FIELDS, where)
        _nonempty(item, ("id", "file", "title", "anchor", "one_line", "static_svg"), where)
        if item["id"] in ids:
            raise BookError(f"{where}: id 重复 {item['id']}")
        if item["anchor"] in anchors:
            raise BookError(f"{where}: anchor 重复 {item['anchor']}")
        ids.add(item["id"])
        anchors.add(item["anchor"])
        if item["file"] != "p5-00-part5.md":
            raise BookError(f"{where}: file 必须是 p5-00-part5.md")
        if not isinstance(item["chapter"], int) or not 0 <= item["chapter"] <= 18:
            raise BookError(f"{where}: chapter 必须是 0–18")
        if not re.fullmatch(r"demo\d+", item["anchor"]):
            raise BookError(f"{where}: anchor 必须形如 demo12")
        if not item["static_svg"].startswith("assets/svg/"):
            raise BookError(f"{where}: static_svg 必须位于 assets/svg/")
        if not (static_root / item["static_svg"]).is_file():
            raise BookError(f"{where}: 静态图不存在 {item['static_svg']}")
    covered = {item["chapter"] for item in items}
    if covered != set(range(19)):
        raise BookError(f"动画未覆盖全部 19 章；缺少 {sorted(set(range(19)) - covered)}")


def validate_index_terms(items: list[dict], anchors: set[str],
                         final: bool = False) -> None:
    if final and not 300 <= len(items) <= 400:
        raise BookError(f"索引应为 300–400 条，实际 {len(items)}")
    names = set()
    for index, item in enumerate(items, 1):
        where = f"index-terms.yml 第 {index} 条"
        _fields(item, INDEX_FIELDS, where)
        _nonempty(item, ("term", "english", "primary"), where)
        if item["term"] in names:
            raise BookError(f"{where}: 术语重复 {item['term']}")
        names.add(item["term"])
        if not isinstance(item["anchors"], list) or not item["anchors"]:
            raise BookError(f"{where}: anchors 必须是非空列表")
        if not isinstance(item["see_also"], list):
            raise BookError(f"{where}: see_also 必须是列表")
        for anchor in [item["primary"], *item["anchors"]]:
            if anchor not in anchors:
                raise BookError(f"{where}: 索引锚点不存在 {anchor}")
    for item in items:
        for other in item["see_also"]:
            if other not in names:
                raise BookError(f"{item['term']}: see_also 指向未知术语 {other}")


def pinyin_key(term: str) -> str:
    return "".join(lazy_pinyin(term, style=Style.NORMAL)).lower()


def index_sections(terms: list[dict]) -> list[tuple[str, list[dict]]]:
    ordered = sorted(terms, key=lambda item: (pinyin_key(item["term"]), item["term"]))
    groups: dict[str, list[dict]] = {}
    for item in ordered:
        key = pinyin_key(item["term"])
        letter = key[0].upper() if key and key[0].isalpha() else "#"
        groups.setdefault(letter, []).append(item)
    return sorted(groups.items())


def validate_sources(items: list[dict], used_ids: set[str] | None = None,
                     final: bool = False) -> None:
    ids = set()
    for index, item in enumerate(items, 1):
        where = f"sources.yml 第 {index} 条"
        _fields(item, SOURCE_FIELDS, where)
        _nonempty(item, ("id", "claim", "citation", "url_or_doi", "verifier"), where)
        if item["id"] in ids:
            raise BookError(f"{where}: id 重复 {item['id']}")
        ids.add(item["id"])
        if not isinstance(item["chapter"], int) or not 0 <= item["chapter"] <= 18:
            raise BookError(f"{where}: chapter 必须是 0–18")
        if item["source_type"] not in SOURCE_TYPES:
            raise BookError(f"{where}: source_type 不在枚举内")
        if not DATE_RE.match(str(item["verified_on"])):
            raise BookError(f"{where}: verified_on 必须是 YYYY-MM-DD")
    if used_ids is None:
        if final:
            raise BookError("final 阶段必须提供正文片段以校验来源闭合")
        return
    missing = sorted(used_ids - ids)
    unused = sorted(ids - used_ids)
    if missing and final:
        raise BookError(f"正文引用的来源不存在: {missing}")
    if unused and final:
        raise BookError(f"sources.yml 有未使用条目: {unused}")


def used_source_ids(fragment: str) -> set[str]:
    return set(re.findall(r'data-source="([^"]+)"', fragment))


def validate_signoffs(items: list[dict], final: bool = False) -> None:
    if len(items) != 19:
        raise BookError(f"chapter-signoff.yml 应有 19 条，实际 {len(items)}")
    chapters = [item.get("chapter") for item in items]
    if chapters != list(range(19)):
        raise BookError("chapter-signoff.yml 必须按 0–18 每章一条")
    for item in items:
        where = f"chapter-signoff.yml 第 {item['chapter']} 章"
        _fields(item, SIGNOFF_FIELDS, where)
        if not DATE_RE.match(str(item["date"])):
            raise BookError(f"{where}: date 必须是 YYYY-MM-DD")
        if not isinstance(item["open_issues"], list):
            raise BookError(f"{where}: open_issues 必须是列表")
        if final:
            for name in ("technical_reviewer", "editorial_reviewer", "safety_reviewer"):
                if not str(item[name]).strip():
                    raise BookError(f"{where}: final 阶段 {name} 不能为空")
            if item["open_issues"]:
                raise BookError(f"{where}: final 阶段 open_issues 必须为空")


def validate_references(items: list[dict], final: bool = False) -> None:
    if final and len(items) < 100:
        raise BookError(f"参考文献去重后应 ≥100 条，实际 {len(items)}")
    ids = set()
    for index, item in enumerate(items, 1):
        where = f"references.yml 第 {index} 条"
        _fields(item, REFERENCE_FIELDS, where)
        _nonempty(item, ("id", "authors", "title", "publisher", "isbn_or_url"), where)
        if item["id"] in ids:
            raise BookError(f"{where}: id 重复 {item['id']}")
        ids.add(item["id"])
        if not isinstance(item["year"], int):
            raise BookError(f"{where}: year 必须是整数")
        if not isinstance(item["chapters"], list) or not item["chapters"]:
            raise BookError(f"{where}: chapters 必须是非空列表")
        if any(not isinstance(ch, int) or not 0 <= ch <= 18 for ch in item["chapters"]):
            raise BookError(f"{where}: chapters 必须是 0–18 的整数")
```

- [ ] **Step 4: 生成数据文件**

Create `scripts/build_book_data.py`：

```python
#!/usr/bin/env python3
"""从 docs/ 生成书内动画台账；种子索引与审读表只在缺失时写入。"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
BOOK = ROOT / "analog-book"
DOCS = ROOT / "docs"
DATA = BOOK / "data"
sys.path.insert(0, str(BOOK))

from book.data import pinyin_key  # noqa: E402

DEMO_HEAD = re.compile(r'^## (5\.\d+)\s+(.+?)\s*<a id="(demo\d+)"')
DEMO_IMG = re.compile(r'<img src="assets/svg/([\w\-]+\.svg)"[^>]*alt="([^"]*)"')
DEMO_LINK = re.compile(r"\[(5\.\d+)\]\((?:[\w\-]+\.md)?#(demo\d+)\)")
CHAPTER_ROW = re.compile(r"^\|\s*§(\d+)\s+(第\s*\d+\s*章[^|]*?)\s*\|")
LOOK_RE = re.compile(r"\*\*看点\*\*[：:]\s*(.+)")

CHAPTER_FILES = [
    "p1-01-ch0", "p1-02-ch1", "p1-03-ch2", "p1-04-ch3", "p1-05-ch4",
    "p1-06-ch5", "p1-07-ch6", "p1-08-ch7", "p1-09-ch8", "p1-10-ch9",
    "p1-11-ch10", "p2-01-ch11", "p2-02-ch12", "p2-03-ch13", "p3-01-ch14",
    "p3-02-ch15", "p4-01-ch16", "p4-02-ch17", "p4-03-ch18",
]

SEED_INDEX = [
    ("电压", "voltage", 0), ("欧姆定律", "Ohm's law", 0),
    ("恒压源", "ideal voltage source", 0), ("恒流源", "ideal current source", 0),
    ("分压器", "voltage divider", 1), ("戴维南等效", "Thevenin equivalent", 1),
    ("电容", "capacitor", 1), ("电感", "inductor", 1),
    ("阻抗", "impedance", 1), ("谐振", "resonance", 1),
    ("二极管", "diode", 2), ("正向压降", "forward voltage", 2),
    ("齐纳击穿", "Zener breakdown", 2),
    ("BJT", "bipolar junction transistor", 3),
    ("静态工作点", "quiescent point", 3), ("跨导", "transconductance", 3),
    ("MOSFET", "MOSFET", 4), ("阈值电压", "threshold voltage", 4),
    ("米勒效应", "Miller effect", 4),
    ("推挽输出", "push-pull output", 5), ("开漏输出", "open-drain output", 5),
    ("运算放大器", "operational amplifier", 6), ("虚短", "virtual short", 6),
    ("共模抑制比", "common-mode rejection ratio", 6),
    ("增益带宽积", "gain-bandwidth product", 6),
    ("比较器", "comparator", 7), ("迟滞", "hysteresis", 7),
    ("模拟开关", "analog switch", 8),
    ("电压基准", "voltage reference", 9),
    ("低压差稳压器", "low-dropout regulator", 9),
    ("555 定时器", "555 timer", 10), ("占空比", "duty cycle", 10),
    ("差分对", "differential pair", 11), ("电流镜", "current mirror", 11),
    ("Sallen-Key 滤波器", "Sallen-Key filter", 12),
    ("Buck 变换器", "buck converter", 13), ("相位裕度", "phase margin", 13),
    ("误差预算", "error budget", 14), ("回流路径", "return current path", 15),
    ("探头负载", "probe loading", 16),
]


def _plain(text):
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    text = text.replace("**", "").replace("`", "")
    return re.sub(r"\s+", " ", text).strip()


SENTENCE_END = "。；！？"
CLAUSE_END = "，、:"
TRAILING = "、，；：,;:（→"


def _last_unmatched(text, opening, closing):
    stack = []
    for index, char in enumerate(text):
        if char == opening:
            stack.append(index)
        elif char == closing and stack:
            stack.pop()
    return stack[-1] if stack else None


def summarize(text, limit=120):
    """按句末/分句边界截断，保证摘要不切断词、公式或括号。"""
    if len(text) <= limit:
        return text
    window = text[:limit - 1]
    cut = max(window.rfind(char) for char in SENTENCE_END)
    if cut < 0:
        cut = max(window.rfind(char) for char in CLAUSE_END)
    if cut >= 0:
        summary = window[:cut + 1]
    else:
        space = max(window.rfind(char) for char in " \t")
        summary = window[:space] if space >= 0 else window
    if summary.count("$") % 2:
        summary = summary[:summary.rfind("$")]
    while summary.count("（") > summary.count("）"):
        unmatched = _last_unmatched(summary, "（", "）")
        if unmatched is None:
            break
        summary = summary[:unmatched]
    summary = summary.rstrip()
    while summary and summary[-1] in TRAILING:
        summary = summary[:-1].rstrip()
    if not summary.endswith(("。", "！", "？")):
        summary += "…"
    return summary


def build_animations():
    lines = (DOCS / "p5-00-part5.md").read_text(encoding="utf-8").splitlines()
    chapter_of = {}
    for line in lines:
        match = CHAPTER_ROW.match(line)
        if match:
            for _num, demo in DEMO_LINK.findall(line):
                chapter_of[demo] = int(match.group(1))
    items, current, body = [], None, []

    def finish():
        nonlocal current, body
        if current is None:
            return
        if not current["svg"]:
            raise SystemExit(f'{current["anchor"]}: 缺少 SVG')
        look = None
        for line in body:
            found = LOOK_RE.search(line)
            if found:
                look = _plain(found.group(1))
                break
        if not look:
            look = current["title"]
        chapter = chapter_of.get(current["anchor"])
        if chapter is None:
            raise SystemExit(f'{current["anchor"]}: 章节映射表缺少该动画')
        items.append({
            "id": f"anim-{len(items) + 1:03d}",
            "file": "p5-00-part5.md",
            "title": current["title"],
            "chapter": chapter,
            "anchor": current["anchor"],
            "one_line": summarize(look),
            "static_svg": "assets/svg/" + current["svg"],
        })
        current, body = None, []

    for line in lines:
        match = DEMO_HEAD.match(line)
        if match:
            finish()
            current = {"num": match.group(1), "title": _plain(match.group(2)),
                       "anchor": match.group(3), "svg": ""}
            continue
        if current is not None:
            if not current["svg"]:
                image = DEMO_IMG.search(line)
                if image:
                    current["svg"] = image.group(1)
                    continue
            body.append(line)
    finish()
    if len(items) != 108:
        raise SystemExit(f"动画应为 108 条，解析到 {len(items)}")
    for item in items:
        if not (ROOT / item["static_svg"]).is_file():
            raise SystemExit(f'缺少图片 {item["static_svg"]}')
    return items


def build_index_terms():
    terms = []
    for term, english, chapter in SEED_INDEX:
        anchor = "page-" + CHAPTER_FILES[chapter]
        terms.append({"term": term, "english": english, "primary": anchor,
                      "anchors": [anchor], "see_also": []})
    return sorted(terms, key=lambda item: (pinyin_key(item["term"]), item["term"]))


def build_signoffs():
    return [{"chapter": i, "draft_version": "2.0.0-draft.1",
             "technical_reviewer": "", "editorial_reviewer": "",
             "safety_reviewer": "", "date": "2026-10-25", "open_issues": []}
            for i in range(19)]


def dump(path, value):
    text = yaml.safe_dump(value, allow_unicode=True, sort_keys=False, width=100)
    if path.is_file() and path.read_text(encoding="utf-8") == text:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return True


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    animations = build_animations()
    if args.check:
        path = DATA / "animations.yml"
        if not path.is_file():
            print("缺少 animations.yml，请运行 --write", file=sys.stderr)
            return 1
        current = yaml.safe_load(path.read_text(encoding="utf-8"))
        if current != animations:
            print("animations.yml 与 p5-00-part5.md 不一致，请运行 --write", file=sys.stderr)
            return 1
        return 0
    if not args.write:
        parser.error("需要 --write 或 --check")
    dump(DATA / "animations.yml", animations)
    for name, value in (("index-terms.yml", build_index_terms()),
                        ("chapter-signoff.yml", build_signoffs()),
                        ("sources.yml", []),
                        ("references.yml", [])):
        path = DATA / name
        if not path.exists():
            dump(path, value)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 5: 生成并校验**

```bash
python scripts/build_book_data.py --write
python scripts/build_book_data.py --check
python -B -m unittest discover -s analog-book/tests -p "test_book_data.py" -v
```

Expected: `--check` 退出 0；测试 PASS（14 tests）。`animations.yml` 108 条、`index-terms.yml` 40 条、`chapter-signoff.yml` 19 条、`sources.yml`/`references.yml` 为空列表。

- [ ] **Step 6: 提交**

```bash
git add analog-book/book/data.py scripts/build_book_data.py analog-book/data \
  analog-book/tests/test_book_data.py
git commit -m "feat(book): add data schemas and 108-animation ledger"
```

---

### Task 7A: 前置页、篇首页、附录首页、目录/图表目录/索引与后置页

**Files:**
- Create: `analog-book/book/frontmatter.py`
- Create: `analog-book/tests/test_book_frontmatter.py`
- Modify: none

**Interfaces:**
- Consumes: `manifest` 字典、`data.index_sections()`、`references` 列表、统计字典。
- Produces（全部返回 HTML 片段，不含 `<section class="book-page">` 外壳）：
  - `half_title(manifest) -> str`
  - `title_page(manifest) -> str`
  - `copyright_page(manifest) -> str`
  - `render_toc(entries: list[dict]) -> str`
  - `render_list(title, page_id, entries, label) -> str`
  - `part_opener(part: dict) -> str`
  - `appendix_opener(appendix: dict) -> str`
  - `render_bibliography(references: list[dict]) -> str`
  - `render_index(sections: list[tuple[str, list[dict]]]) -> str`
  - `colophon(manifest, stats: dict) -> str`
- 页码占位统一用 `<span class="toc-page">000</span>` / `index-page`，且占位必须在 `<a>` 内部，供 Task 8 用链接矩形定位。
- 版权页不写虚构 ISBN、条码、出版社或印次；草稿状态明示“草稿”。

- [ ] **Step 1: 先写失败测试**

Create `analog-book/tests/test_book_frontmatter.py`:

```python
#!/usr/bin/env python3
"""前置/后置页：元数据、目录、图表目录、索引与版权安全文案。"""
import sys
import unittest
from pathlib import Path

BOOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BOOK))

from book import frontmatter  # noqa: E402

MANIFEST = {
    "title": "通往模拟电路之路", "subtitle": "从欧姆定律到芯片内部结构",
    "edition": "第一版", "version": "2.0.0-draft.1", "date": "2026-10-25",
    "author": "zhuguang-ZFG 与贡献者", "license": "CC BY-SA 4.0",
    "site_url": "https://example.test/book/",
    "repository": "https://example.test/repo",
    "release": {"edition_status": "draft"},
}


class FrontPageTests(unittest.TestCase):
    def test_half_title_and_title_page(self):
        half = frontmatter.half_title(MANIFEST)
        self.assertIn("通往模拟电路之路", half)
        self.assertIn("第一版", half)
        self.assertNotIn("000", half)
        self.assertEqual(1, half.count("<h1"),
                         "半书名页必须恰好一个 h1，供 PDF 定位页首")
        self.assertIn('<h1 class="book-title">', half)
        title = frontmatter.title_page(MANIFEST)
        self.assertIn("从欧姆定律到芯片内部结构", title)
        self.assertIn("zhuguang-ZFG", title)
        self.assertIn("2.0.0-draft.1", title)

    def test_copyright_has_license_safety_and_no_fake_isbn(self):
        page = frontmatter.copyright_page(MANIFEST)
        for text in ("CC BY-SA 4.0", "SIL Open Font License", "安全", "仿真",
                     "草稿", "185×260", "勘误"):
            self.assertIn(text, page)
        self.assertNotIn("ISBN", page)
        self.assertNotIn("条码", page)


class TocTests(unittest.TestCase):
    def test_three_levels_links_and_placeholders(self):
        entries = [
            {"level": 1, "title": "第一篇 基础", "anchor": "part-i", "kind": "part"},
            {"level": 2, "title": "第 0 章 电路直觉", "anchor": "page-p1-01-ch0",
             "kind": "chapter"},
            {"level": 3, "title": "0.1 电压与电位", "anchor": "p1-01-ch0--s1",
             "kind": "section"},
        ]
        page = frontmatter.render_toc(entries)
        self.assertIn('id="book-toc"', page)
        self.assertEqual(3, page.count('class="toc-page">000</span>'))
        self.assertIn('href="#p1-01-ch0--s1"', page)
        self.assertIn("toc-level-3", page)

    def test_list_of_figures(self):
        entries = [{"number": "图 2-1", "caption": "图 2-1　整流波形",
                    "anchor": "p1-03-ch2--fig-1"}]
        page = frontmatter.render_list("插图目录", "list-of-figures", entries, "图")
        self.assertIn('id="list-of-figures"', page)
        self.assertIn("图 2-1", page)
        self.assertIn('class="toc-page">000</span>', page)


class StructurePageTests(unittest.TestCase):
    def test_part_and_appendix_openers(self):
        part = {"id": "I", "title": "基础", "subtitle": "先建立电路直觉",
                "intro": "从电压、电流与无源元件开始。",
                "units": [{"title": "电路直觉与无源世界"}]}
        html = frontmatter.part_opener(part)
        self.assertIn('id="part-i"', html)
        self.assertIn("第I篇", html)
        self.assertIn("基础", html)
        appendix = {"id": "B", "title": "公式与设计速查",
                    "intro": "把全书常用公式收在一处。"}
        html = frontmatter.appendix_opener(appendix)
        self.assertIn('id="appendix-b"', html)
        self.assertIn("附录 B", html)


class BackMatterTests(unittest.TestCase):
    def test_empty_bibliography_is_honest_draft_note(self):
        page = frontmatter.render_bibliography([])
        self.assertIn('id="bibliography"', page)
        self.assertIn("草稿", page)
        self.assertNotIn("TODO", page)

    def test_bibliography_is_numbered_and_sorted(self):
        refs = [
            {"id": "b", "authors": "B", "title": "Beta", "year": 2020,
             "publisher": "P", "edition": "", "isbn_or_url": "u", "chapters": [1]},
            {"id": "a", "authors": "A", "title": "Alpha", "year": 2019,
             "publisher": "P", "edition": "", "isbn_or_url": "u", "chapters": [0]},
        ]
        page = frontmatter.render_bibliography(refs)
        self.assertLess(page.index("Alpha"), page.index("Beta"))
        self.assertIn("[1]", page)
        self.assertIn("第 1 章", page)

    def test_index_two_column_primary_bold_and_multiple_pages(self):
        sections = [("M", [{
            "term": "米勒效应", "english": "Miller effect",
            "primary": "page-p1-05-ch4",
            "anchors": ["page-p1-05-ch4", "p1-05-ch4--miller"],
            "see_also": [],
        }])]
        page = frontmatter.render_index(sections)
        self.assertIn("index-columns", page)
        self.assertIn("<strong>米勒效应</strong>", page)
        self.assertEqual(2, page.count('class="index-page">000</span>'))
        self.assertIn("Miller effect", page)

    def test_colophon_lists_production_facts(self):
        page = frontmatter.colophon(MANIFEST, {"pages": 500, "spine_mm": 26.0})
        for text in ("500", "26.0", "Chromium", "PyMuPDF", "SIL Open Font License"):
            self.assertIn(text, page)

    def test_colophon_defers_physical_pagination_until_pdf_facts(self):
        page = frontmatter.colophon(MANIFEST, {"pages": 77})
        self.assertIn("77 个逻辑页", page)
        self.assertIn("最终 PDF 与 PRINT-SPEC.md", page)
        self.assertNotIn("书脊厚度约", page)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 运行测试，确认失败**

Run: `python -B -m unittest discover -s analog-book/tests -p "test_book_frontmatter.py" -v`
Expected: FAIL with `No module named 'book.frontmatter'`.

- [ ] **Step 3: 实现 `frontmatter.py`**

```python
"""书内生成页：半书名、书名、版权、目录、图表目录、索引与后置。"""
from __future__ import annotations

import html


def _e(value) -> str:
    return html.escape(str(value), quote=True)


def _draft_note(manifest: dict) -> str:
    if manifest["release"]["edition_status"] != "draft":
        return ""
    return ('<p class="draft-note">本版为构建草稿，尚未完成技术、编辑与安全审读，'
            '不得作为稳定版发行。</p>')


def half_title(manifest: dict) -> str:
    return (
        '<div class="half-title">'
        f'<h1 class="book-title">{_e(manifest["title"])}</h1>'
        f'<p class="book-subtitle">{_e(manifest["subtitle"])}</p>'
        f'<p class="book-edition">{_e(manifest["edition"])}</p>'
        '</div>')


def title_page(manifest: dict) -> str:
    return (
        '<div class="title-page">'
        f'<p class="title-kicker">模拟电路 · 从直觉到工程</p>'
        f'<h1 id="title-page">{_e(manifest["title"])}</h1>'
        f'<p class="title-subtitle">{_e(manifest["subtitle"])}</p>'
        f'<p class="title-author">{_e(manifest["author"])}</p>'
        f'<p class="title-edition">{_e(manifest["edition"])} · '
        f'{_e(manifest["version"])}</p>'
        f'<p class="title-date">{_e(manifest["date"])}</p>'
        '</div>')


def copyright_page(manifest: dict) -> str:
    return (
        '<div class="copyright-page">'
        '<h1 id="copyright">版权、授权与安全</h1>'
        f'<p>《{_e(manifest["title"])}》<br>'
        f'{_e(manifest["subtitle"])}</p>'
        f'<p>{_e(manifest["edition"])} · 版本 {_e(manifest["version"])} · '
        f'{_e(manifest["date"])}</p>'
        f'<p>作者：{_e(manifest["author"])}</p>'
        f'<p>正文、SVG 动画、网表与实验数据采用 {_e(manifest["license"])} 授权；'
        '转载、改编与再分发请保留署名并以相同方式共享。第三方照片、软件与字体的'
        '完整清单见书末「来源与许可」。</p>'
        '<p>正文字体为 Noto Serif SC 与 Noto Sans SC，代码字体为 JetBrains Mono，'
        '均按 SIL Open Font License 1.1 嵌入。</p>'
        f'<p>在线阅读：{_e(manifest["site_url"])}<br>'
        f'勘误与讨论：{_e(manifest["repository"])}/issues</p>'
        '<p><strong>安全声明</strong>：本书是学习读物，不是器件、电源或高压设备的'
        '操作许可。动手前必须断电、放电、限流并确认绝缘与接地；电解电容、电感与'
        '电池可能储存危险能量。器件参数、热设计与安全间距请以厂商最新数据手册、'
        '当地法规和实际测量为准。作者与贡献者不对因照书操作造成的损失承担责任。</p>'
        '<p><strong>关于数据</strong>：仿真是模型结果，不是实测；实测只覆盖书中'
        '明确标出的三套实验。读者设计必须用数据手册、仿真与实际测量三方复核。</p>'
        '<p>印刷规格：16K（185×260mm），正文 80g 纯质纸，封面 250g 铜版纸覆哑膜，'
        '胶装。本 PDF 为按需印刷母版；书号、出版者与印次均未分配，'
        '不按正式出版物发行。</p>'
        + _draft_note(manifest) +
        '</div>')


def render_toc(entries: list[dict]) -> str:
    rows = ['<div class="book-toc">', '<h1 id="book-toc">目录</h1>',
            '<nav class="book-toc-list" aria-label="目录">']
    for entry in entries:
        level = int(entry["level"])
        kind = entry.get("kind", "")
        rows.append(
            f'<div class="toc-row toc-level-{level} toc-{_e(kind)}">'
            f'<a href="#{_e(entry["anchor"])}">'
            f'<span class="toc-title">{_e(entry["title"])}</span>'
            '<span class="toc-dots" aria-hidden="true"></span>'
            '<span class="toc-page">000</span></a></div>')
    rows.append("</nav></div>")
    return "\n".join(rows)


def render_list(title: str, page_id: str, entries: list[dict], label: str) -> str:
    rows = ['<div class="book-toc">',
            f'<h1 id="{_e(page_id)}">{_e(title)}</h1>',
            '<nav class="book-toc-list" aria-label="' + _e(title) + '">']
    for entry in entries:
        rows.append(
            f'<div class="toc-row toc-level-2"><a href="#{_e(entry["anchor"])}">'
            f'<span class="toc-title">{_e(entry["caption"])}</span>'
            '<span class="toc-dots" aria-hidden="true"></span>'
            '<span class="toc-page">000</span></a></div>')
    rows.append("</nav></div>")
    if not entries:
        rows.append(f'<p class="draft-note">本版尚未登记{_e(label)}。</p>')
    return "\n".join(rows)


def part_opener(part: dict) -> str:
    units = "".join(f"<li>{_e(unit['title'])}</li>" for unit in part.get("units", []))
    return (
        f'<div class="part-opener" data-part="{_e(part["id"])}">'
        f'<h1 id="part-{_e(part["id"].lower())}" class="part-heading">'
        f'<span class="part-kicker">第{_e(part["id"])}篇</span>'
        f'<span class="part-title">{_e(part["title"])}</span></h1>'
        f'<p class="part-subtitle">{_e(part.get("subtitle", ""))}</p>'
        f'<p class="part-intro">{_e(part.get("intro", ""))}</p>'
        f'<ul class="part-units">{units}</ul>'
        '<div class="part-art" aria-hidden="true"></div>'
        '</div>')


def appendix_opener(appendix: dict) -> str:
    return (
        f'<div class="appendix-opener" data-appendix="{_e(appendix["id"])}">'
        f'<h1 id="appendix-{_e(appendix["id"].lower())}">'
        f'附录 {_e(appendix["id"])}　{_e(appendix["title"])}</h1>'
        f'<p class="appendix-intro">{_e(appendix.get("intro", ""))}</p>'
        '</div>')


def render_bibliography(references: list[dict]) -> str:
    rows = ['<h1 id="bibliography">参考文献</h1>']
    if not references:
        rows.append('<p class="draft-note">本版为草稿：参考文献将在各章“延伸阅读”'
                    '统一为五列表后去重生成；稳定版要求不少于 100 条。</p>')
        return "\n".join(rows)
    ordered = sorted(references, key=lambda item: (
        str(item.get("authors", "")).lower(), str(item.get("title", "")).lower()))
    rows.append('<ol class="bibliography-list">')
    for number, item in enumerate(ordered, 1):
        chapters = "、".join(f"第 {ch} 章" for ch in item["chapters"])
        edition = f"，{_e(item['edition'])}" if item.get("edition") else ""
        rows.append(
            f'<li>[{number}] {_e(item["authors"])}：'
            f'《{_e(item["title"])}》{edition}。{_e(item["publisher"])}，'
            f'{_e(item["year"])}。{_e(item["isbn_or_url"])}。{_e(chapters)}。</li>')
    rows.append("</ol>")
    return "\n".join(rows)


def render_index(sections: list[tuple[str, list[dict]]]) -> str:
    rows = ['<h1 id="book-index">索引</h1>', '<div class="index-columns">']
    for letter, terms in sections:
        rows.append(f'<section class="index-letter"><h2>{_e(letter)}</h2><ul>')
        for term in terms:
            anchors = [term["primary"]] + [
                item for item in term["anchors"] if item != term["primary"]]
            pages = " ".join(
                f'<a class="index-page-link" href="#{_e(anchor)}">'
                '<span class="index-page">000</span></a>' for anchor in anchors)
            rows.append(
                f'<li><a class="index-term-link" href="#{_e(term["primary"])}">'
                f'<strong>{_e(term["term"])}</strong></a> '
                f'<span class="index-en">{_e(term["english"])}</span> {pages}</li>')
        rows.append("</ul></section>")
    rows.append("</div>")
    return "\n".join(rows)


def colophon(manifest: dict, stats: dict) -> str:
    pages = _e(stats["pages"])
    if "spine_mm" in stats:
        pagination = f'内文 {pages} 页，书脊厚度约 {_e(stats["spine_mm"])} mm。'
    else:
        # HTML 装配时还不知道物理页数；不得用逻辑页数冒充印前事实。
        pagination = (f'内文 {pages} 个逻辑页；印前页数与书脊厚度'
                      '以最终 PDF 与 PRINT-SPEC.md 为准。')
    return (
        '<div class="colophon">'
        '<h1 id="colophon">版本页</h1>'
        f'<p>《{_e(manifest["title"])}》{_e(manifest["edition"])}，'
        f'版本 {_e(manifest["version"])}，{_e(manifest["date"])}。</p>'
        f'<p>{pagination}'
        '开本 16K（185×260mm），正文 80g 纯质纸，封面 250g 铜版纸覆哑膜，胶装。</p>'
        '<p>内容源：docs/；排版：HTML + CSS + Chromium；PDF 后处理：PyMuPDF；'
        '公式：MathJax SVG；动画：仓库内 SMIL SVG。</p>'
        '<p>字体：Noto Serif SC、Noto Sans SC、JetBrains Mono，'
        'SIL Open Font License 1.1。</p>'
        f'<p>授权：{_e(manifest["license"])}。'
        f'仓库：{_e(manifest["repository"])}。</p>'
        '</div>')
```

- [ ] **Step 4: 运行测试，确认通过**

Run: `python -B -m unittest discover -s analog-book/tests -p "test_book_frontmatter.py" -v`
Expected: PASS (9 tests).

- [ ] **Step 5: 提交**

```bash
git add analog-book/book/frontmatter.py analog-book/tests/test_book_frontmatter.py
git commit -m "feat(book): add front and back matter renderers"
```

---

### Task 7B: 题库拆分、77 页装配、模型 JSON、审计与构建入口

**Files:**
- Create: `analog-book/book/quiz.py`
- Create: `analog-book/book/assemble.py`
- Create: `analog-book/tests/test_book_quiz.py`
- Create: `analog-book/tests/test_book_build.py`
- Modify: `analog-book/tests/book_fixtures.py`（给夹具题库页加 2 道章节题、1 道专题题；给 ch0 加带图注插图和带表注表格）
- Modify: `analog-book/styles/book.css`（只增补新屏幕样式；暂不动 `@page`）

**Interfaces:**
- Consumes: `content`、`transforms`、`frontmatter`、`data`、`fonts`、`manifest`、`config`、站点 CSS/JS、MathJax。
- Produces:
  - `QuizData(chapters: dict[int, list[Question]], extra: list[Question])`
  - `parse_quiz(fragment: str) -> QuizData`
  - `merge_exercises(fragment: str, questions: list[Question], stem: str) -> str`
  - `render_answers(data: QuizData, chapter_stems: dict[int, str], appendix_stem: str) -> str`
  - `build_html(out_dir, site_dir, data_dir, docs_dir, manifest, fonts_dir=config.FONTS_DIR, rebuild_site=False, final=None) -> Path`
  - `audit_html(document, model, final=False) -> dict`
  - `check_html(out_dir, manifest, final=None) -> int`
  - 模型 `book-model.json` 含 `pages`（77）、`toc`、`lof`、`lot`、`endnotes`、`figures`、`tables`、`headings`、`audit`、`stats`。
- 页面顺序固定：11 前置 +（5 篇首页 + 19 章）+（8 附录首页 + A 总表 + 27 附录源页/答案页）+ 6 后置 = 77。
- 章习题从题库并入章末，答案只进附录 F；书中不得出现 `<details>`。

- [ ] **Step 1: 先写题库测试**

Create `analog-book/tests/test_book_quiz.py`:

```python
#!/usr/bin/env python3
"""题库拆分：章末题目、附录 F 答案与编号稳定性。"""
import sys
import unittest
from pathlib import Path

BOOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BOOK))

from book import quiz  # noqa: E402

QUIZ = """
<h1>题库</h1>
<p><a id="p9--quiz-ch0"></a></p><h2>第 0 章</h2><ol>
<li><p><a id="p9--q-ch0-01" data-quiz-question="true"></a>问题一？</p>
<details class="note"><summary>答案</summary><p>答案一。</p></details></li>
<li><p><a id="p9--q-ch0-02" data-quiz-question="true"></a>问题二？</p>
<details class="note"><summary>答案</summary><p>答案二。</p></details></li>
</ol>
<h2>专题加练</h2><ol>
<li><p><a id="p9--q-extra-01" data-quiz-question="true"></a>专题问题？</p>
<details class="note"><summary>答案</summary><p>专题答案。</p></details></li>
</ol>
"""


class ParseTests(unittest.TestCase):
    def test_splits_chapter_and_extra(self):
        data = quiz.parse_quiz(QUIZ)
        self.assertEqual([0], list(data.chapters))
        self.assertEqual(2, len(data.chapters[0]))
        self.assertEqual("q-ch0-01", data.chapters[0][0].id)
        self.assertEqual("问题一？", data.chapters[0][0].question)
        self.assertEqual(1, len(data.extra))
        self.assertEqual("q-extra-01", data.extra[0].id)

    def test_strips_emoji_from_answers(self):
        data = quiz.parse_quiz(QUIZ.replace("答案一。", "✅ 答案一。"))
        self.assertEqual("✓ 答案一。", data.chapters[0][0].answer)


class MergeTests(unittest.TestCase):
    def test_appends_exercise_section_without_answers(self):
        data = quiz.parse_quiz(QUIZ)
        result = quiz.merge_exercises("<h1>第 0 章</h1><p>正文。</p>",
                                      data.chapters[0], "p1-01-ch0")
        self.assertIn('class="chapter-exercises"', result)
        self.assertIn('id="p1-01-ch0--q-q-ch0-01"', result)
        self.assertIn("问题一？", result)
        self.assertNotIn("<details", result)
        self.assertNotIn("答案一", result)

    def test_answers_only_in_appendix(self):
        data = quiz.parse_quiz(QUIZ)
        page = quiz.render_answers(data, {0: "p1-01-ch0"}, "p9-00-quiz")
        self.assertIn("答案一。", page)
        self.assertIn("专题答案。", page)
        self.assertEqual(2, page.count('class="answer-list"'))
        self.assertNotIn("<details", page)
        self.assertIn('href="#p1-01-ch0--q-q-ch0-01"', page)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 实现 `quiz.py`**

```python
"""题库拆分：章节题进章末，答案进附录 F。"""
from __future__ import annotations

import re
from dataclasses import dataclass

from .manifest import BookError
from .transforms import strip_emoji

SECTION_RE = re.compile(
    r'<p><a id="[^"]*quiz-ch(\d+)"></a></p>(.*?)'
    r'(?=<p><a id="[^"]*quiz-ch\d+"></a></p>|<h2[^>]*>[^<]*专题|$)',
    re.S)
QUESTION_RE = re.compile(
    r'<li>\s*<p><a id="(?P<raw>[^"]*q-(?P<kind>ch(?P<ch>\d+)|extra)-\d+)"'
    r'[^>]*></a>(?P<q>.*?)</p>\s*<details[^>]*>\s*<summary>.*?</summary>'
    r'(?P<a>.*?)</details>\s*</li>', re.S)
QID_RE = re.compile(r'(q-(?:ch\d+|extra)-\d+)$')


@dataclass(frozen=True)
class Question:
    id: str
    chapter: int | None
    question: str
    answer: str


@dataclass
class QuizData:
    chapters: dict[int, list[Question]]
    extra: list[Question]


def _question(match: re.Match) -> Question:
    qid = QID_RE.search(match.group("raw")).group(1)
    chapter = int(match.group("ch")) if match.group("kind").startswith("ch") else None
    return Question(id=qid, chapter=chapter,
                    question=strip_emoji(match.group("q").strip()),
                    answer=strip_emoji(match.group("a").strip()))


def parse_quiz(fragment: str) -> QuizData:
    chapters: dict[int, list[Question]] = {}
    for match in SECTION_RE.finditer(fragment):
        chapter = int(match.group(1))
        questions = [_question(item) for item in QUESTION_RE.finditer(match.group(2))]
        if not questions:
            raise BookError(f"题库第 {chapter} 章没有解析到题目")
        chapters[chapter] = questions
    if not chapters:
        raise BookError("题库中没有 quiz-chN 分节")
    extra = [_question(item) for item in QUESTION_RE.finditer(fragment)
             if item.group("kind") == "extra"]
    ids = [q.id for group in chapters.values() for q in group] + [q.id for q in extra]
    if len(ids) != len(set(ids)):
        raise BookError("题库题目 ID 重复")
    return QuizData(chapters=chapters, extra=extra)


def merge_exercises(fragment: str, questions: list[Question], stem: str) -> str:
    if not questions:
        return fragment
    items = "".join(
        f'<li><a id="{stem}--q-{q.id}"></a>{q.question}</li>' for q in questions)
    existing = re.search(
        r'(<h2[^>]*>[^<]*本章练习[^<]*</h2>\s*<ol[^>]*>)(.*?)(</ol>)',
        fragment, re.S)
    if existing:
        return (fragment[:existing.start(2)] + existing.group(2) + items
                + fragment[existing.end(2):])
    section = (
        f'<section class="chapter-exercises" id="{stem}--exercises">'
        f'<h2 id="{stem}--exercises-title">本章练习</h2>'
        f'<ol class="exercise-list">{items}</ol>'
        '<p class="exercise-hint">答案见附录 F；先盖住答案在纸上算。</p></section>')
    return fragment + section


def render_answers(data: QuizData, chapter_stems: dict[int, str],
                   appendix_stem: str) -> str:
    rows = ['<h1 id="appendix-f-answers">习题答案与综合自测</h1>',
            '<p class="answers-note">章节题按题号对应章末练习；专题题为综合加练。</p>']
    for chapter in sorted(data.chapters):
        stem = chapter_stems[chapter]
        rows.append(f'<section class="answer-group"><h2>第 {chapter} 章</h2>'
                    '<ol class="answer-list">')
        for q in data.chapters[chapter]:
            rows.append(
                f'<li id="{appendix_stem}--ans-{q.id}">'
                f'<a class="answer-ref" href="#{stem}--q-{q.id}">{q.id}</a>'
                f'<div class="answer-body">{q.answer}</div></li>')
        rows.append("</ol></section>")
    if data.extra:
        rows.append('<section class="answer-group"><h2>专题加练</h2>'
                    '<ol class="answer-list">')
        for q in data.extra:
            rows.append(
                f'<li id="{appendix_stem}--ans-{q.id}">'
                f'<p class="answer-question">{q.question}</p>'
                f'<div class="answer-body">{q.answer}</div></li>')
        rows.append("</ol></section>")
    return "\n".join(rows)
```

- [ ] **Step 3: 扩展夹具与装配测试**

在 `book_fixtures.write_site` 的 `if name == "p1-01-ch0.md":` 分支改为：

```python
        if name == "p1-01-ch0.md":
            body = ('<h1>📘 第 0 章 电路直觉</h1><p>正文。</p>'
                    '<h2>0.1 电压与电位</h2><p>内容。</p>'
                    '<figure><img src="assets/svg/fixture.svg" alt="夹具图">'
                    '<figcaption>夹具插图</figcaption></figure>'
                    '<p><strong>表 0-1　夹具表</strong></p>'
                    '<table><tr><td>1</td></tr></table>')
        if name == "p9-00-quiz.md":
            body = ('<h1>自测</h1>'
                    '<p><a id="quiz-ch0"></a></p><h2>第 0 章</h2><ol>'
                    '<li><p><a id="q-ch0-01" data-quiz-question="true"></a>'
                    '示例问题？</p><details class="note"><summary>答案</summary>'
                    '<p>示例答案。</p></details></li></ol>'
                    '<p><a id="quiz-ch1"></a></p><h2>第 1 章</h2><ol>'
                    '<li><p><a id="q-ch1-01" data-quiz-question="true"></a>'
                    '第二题？</p><details class="note"><summary>答案</summary>'
                    '<p>第二答案。</p></details></li></ol>'
                    '<h2>专题加练</h2><ol>'
                    '<li><p><a id="q-extra-01" data-quiz-question="true"></a>'
                    '综合题？</p><details class="note"><summary>答案</summary>'
                    '<p>综合答案。</p></details></li></ol>')
```

Create `analog-book/tests/test_book_build.py`:

```python
#!/usr/bin/env python3
"""77 页装配、模型、目录占位、习题拆分、索引与审计。"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

BOOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BOOK))

from book import assemble  # noqa: E402
from book.manifest import validate_manifest  # noqa: E402
import book_fixtures  # noqa: E402


class BuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        root = Path(cls.tmp.name)
        cls.manifest = book_fixtures.manifest()
        book_fixtures.write_docs(root / "docs")
        cls.site = book_fixtures.write_site(root / "site")
        cls.data = book_fixtures.write_data(root / "data")
        cls.out = root / "dist"
        validate_manifest(cls.manifest, docs_dir=root / "docs")
        cls.html_path = assemble.build_html(
            cls.out, cls.site, cls.data, root / "docs", cls.manifest,
            rebuild_site=False, final=False)
        cls.document = cls.html_path.read_text(encoding="utf-8")
        cls.model = json.loads((cls.out / "book-model.json").read_text(encoding="utf-8"))

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_77_pages_in_fixed_order(self):
        self.assertEqual(77, len(self.model["pages"]))
        kinds = [page["kind"] for page in self.model["pages"]]
        self.assertEqual(11, kinds[:11].count("front") + kinds[:11].count("half_title")
                         + kinds[:11].count("title_page") + kinds[:11].count("copyright")
                         + kinds[:11].count("toc") + kinds[:11].count("list_of_figures")
                         + kinds[:11].count("list_of_tables"))
        self.assertEqual(5, kinds.count("part"))
        self.assertEqual(19, kinds.count("chapter"))
        self.assertEqual(8, kinds.count("appendix_opener"))
        self.assertEqual(6, kinds.count("back"))
        self.assertEqual("half_title", kinds[0])
        self.assertEqual("copyright", kinds[2])
        self.assertEqual("part", kinds[11])
        self.assertEqual("chapter", kinds[12])
        self.assertEqual(5, self.document.count('class="part-intro"'))
        self.assertNotIn('class="part-intro"></p>', self.document)

    def test_titles_are_emoji_free(self):
        self.assertNotIn("📘", self.document)
        self.assertIn('data-title="第 0 章 电路直觉"', self.document)

    def test_toc_lof_lot_and_index_use_000(self):
        for page in self.model["pages"]:
            if page["kind"] in {"toc", "list_of_figures", "list_of_tables", "index"}:
                self.assertIn("000", page["html"])
        self.assertTrue(self.model["toc"])
        self.assertTrue(self.model["lof"])
        self.assertTrue(self.model["lot"])

    def test_chapter_exercises_and_appendix_answers(self):
        self.assertIn("示例问题？", self.document)
        self.assertIn("示例答案。", self.document)
        self.assertNotIn("<details", self.document)
        self.assertEqual(2, self.document.count('class="chapter-exercises"'))
        self.assertIn('href="#p1-01-ch0--q-q-ch0-01"', self.document)

    def test_assets_inline_and_no_remote(self):
        self.assertIn("data:image/svg+xml;base64,", self.document)
        self.assertNotIn('src="assets/', self.document)
        self.assertNotIn('src="http', self.document)
        self.assertNotIn("<iframe", self.document)

    def test_unique_ids_and_reachable_internal_links(self):
        audit = self.model["audit"]
        self.assertEqual([], audit["errors"])
        self.assertEqual(77, audit["pages"])
        self.assertGreater(audit["bytes"], 100_000)

    def test_model_stats(self):
        stats = self.model["stats"]
        self.assertEqual(77, stats["logical_pages"])
        self.assertGreaterEqual(stats["figures"], 1)
        self.assertGreaterEqual(stats["tables"], 1)
        self.assertGreater(stats["images"], 0)

    def test_exports_figure_and_table_manifests(self):
        for name in ("figures.yml", "tables.yml"):
            entries = yaml.safe_load(
                (self.out / name).read_text(encoding="utf-8"))
            self.assertTrue(entries, name)
            self.assertEqual(
                {"id", "chapter", "number", "title", "anchor", "source"},
                set(entries[0]), name)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 4: 运行测试，确认失败**

Run: `python -B -m unittest discover -s analog-book/tests -p "test_book_quiz.py" -v`
Expected: FAIL with `No module named 'book.quiz'`.

- [ ] **Step 5: 实现 `assemble.py`（核心）**

`assemble.py` 的职责是“把 7 个来源装成 77 个逻辑页”。按以下顺序实现，函数名与参数必须与接口一致：

```python
"""77 页装配：前置、篇、章、附录、后置、目录、索引与审计。"""
from __future__ import annotations

import datetime as dt
import hashlib
import html
import json
import re
import sys
from pathlib import Path

import yaml

from . import config, content, data, fonts, frontmatter, quiz, transforms
from .manifest import BookError, book_pages, direct_files, excluded_files, validate_manifest

CSS_FILES = ["typography", "gallery", "learning", "reading", "diag"]
BOOK_SCRIPTS = ["calc", "learning", "learning-catalog", "diag"]
MATHJAX_PATH = config.ROOT / "assets" / "vendor" / "mathjax-svg" / "tex-svg-full.js"
CHAPTER_STEMS = {
    0: "p1-01-ch0", 1: "p1-02-ch1", 2: "p1-03-ch2", 3: "p1-04-ch3",
    4: "p1-05-ch4", 5: "p1-06-ch5", 6: "p1-07-ch6", 7: "p1-08-ch7",
    8: "p1-09-ch8", 9: "p1-10-ch9", 10: "p1-11-ch10", 11: "p2-01-ch11",
    12: "p2-02-ch12", 13: "p2-03-ch13", 14: "p3-01-ch14",
    15: "p3-02-ch15", 16: "p4-01-ch16", 17: "p4-02-ch17",
    18: "p4-03-ch18",
}
```

1. **资源内联**：从 `build_book.py` 原样移植 `_material_css`、`inline_css`、`inline_scripts`、`inline_static`、`MATHJAX_CONFIG`、`inline_mathjax`，把 `BOOK_DIR` 改为 `config.BOOK_DIR`、`SITE_DIR` 改为传入的 `site_dir`；`inline_css` 追加 `config.BOOK_DIR / "styles" / "print.css"`，并由 `fonts.font_css(fonts_dir)` 放在最前。`print.css` 放进 `<style media="print">`，其余屏幕 CSS 放普通 `<style>`。
2. **页面对象**：生成 `pages: list[dict]`，每项包含 `kind, id, title, html, source, group, header, bookmark_level, headings, figures, tables, endnotes`。所有页面标题（生成页与源页）在进入 `pages`、模型目录与外壳 `data-title` 前，统一先过 `transforms.strip_emoji`；正文 h1 原文保留。`id` 规则：
   - 生成的前置页：`half-title`、`title-page`、`copyright`、`book-toc`、`list-of-figures`、`list-of-tables`；**源文件前置页**用 `page-<stem>`（与 `content.rewrite_links` 的目标一致）。
   - 正文/附录源页/后置源页：`page-<stem>`。
   - 篇：`part-i`…；附录首页：`appendix-a`…。
   - 生成页正文里的 `h1` 可能带与外壳相同的 `id`（如 `title-page`、`book-toc`、`part-i`、`appendix-b`、`bibliography`、`book-index`、`colophon`）。包装前必须调用下面的 `_strip_page_id`，只保留外壳 ID；正文 `<h1>` 本身不删。
   - 后置生成页的 shell `id` 分别是 `bibliography`、`book-index`、`colophon`；源文件页仍是 `page-<stem>`。
3. **前置 11 页**：半书名、书名、版权直接来自 `frontmatter`；`p0-01`、`p0-02`、`p0-03`、`p0-11`、`p0-12` 用 `load_page` + `strip_emoji` + `unwrap_details` + `transform_callouts` + `wrap_tables`（不编号、不加尾注）；TOC/LOF/LOT 先占位。
4. **题库**：`quiz_page = content.load_page(site_dir, "p9-00-quiz.md", stems, manifest)`；`quiz_data = quiz.parse_quiz(quiz_page.html)`；题库页保留 `<details>` 供解析，本身不进入 77 页，也不做展开。
5. **正文 24 页**：对每篇生成 opener；每章 `load_page` → `strip_emoji` → `unwrap_details` → `transform_callouts` → `number_figures/table`（label 为章号）→ `transform_endnotes` → `check_calculator_fallbacks` → `quiz.merge_exercises`。章 h1 保留；章末追加习题后，收集 h2（含编号节）作为 level 3 目录项。若章内没有 `goal` 提示框，草稿 warning、final error。
6. **附录 36 页**：每个附录先生成 opener；A 生成 108 行总表页（shell id `appendix-a-table`，行 id `anim-N`）；24 张关键帧与附录专属版式（B 两栏、D 合并去重、E 三节、G 拼音合并）留到 Phase 5 附录定稿，Phase 0 不伪造关键帧。B–H 逐文件 `load_page`，把 h1 降为 h2（`demote_h1` 保留 id），应用与章相同的转换（含 `unwrap_details`，label 为附录字母），F 用 `quiz.render_answers` 代替 quiz 原文，A 总表页标题为“附录 A 动画总表”。附录 opener 是 level 1 书签，源页是 level 2，页内编号 h2 是 level 3。
7. **后置 6 页**：参考文献（shell id `bibliography`）、索引（`book-index`）、版本记录/致谢/来源与许可（`page-<stem>`，走 `strip_emoji` + `unwrap_details` + `transform_callouts`，不编号、不加尾注）、版本页（`colophon`）。索引要等所有页与锚点收集完成后生成；`index_sections` 排序；`validate_index_terms(..., anchors, final=final)`。
8. **TOC/LOF/LOT**：按页面顺序生成 `toc`（篇/附录 level 1；章/附录源页 level 2；章内编号 h2、附录内编号 h2 level 3）、`lof`、`lot`；回填到前置页位置。`lof`/`lot` 每条含 `number`（如 `图 3-1`）、`title`（去掉编号前缀的图注）、`caption`、`anchor`、`source`（源页 stem）。**TOC 不展开附录内部未编号小节。**
9. **导航与外壳**：沿用旧 `assemble_book` 的屏幕骨架（skip link、进度条、header、搜索、footer、回到顶部、MathJax、`book-search.js`、`book-ui.js`），页面 nav 保留；打印时由 `print.css` 隐藏。每个页面外壳：
```python
def _strip_page_id(body: str, page_id: str) -> str:
    pattern = re.compile(
        r'(<h1\b[^>]*?)\s+id="%s"' % re.escape(page_id))
    return pattern.sub(r"\1", body, count=1)


page_html = (
    f'<section class="book-page page-{kind}" id="{page_id}" data-page="{stem}" '
    f'data-title="{esc(title)}" data-kind="{kind}" data-header="{esc(header)}">'
    f'<div class="md-typeset">{_strip_page_id(body, page_id)}</div>'
    f'{page_nav}</section>')
```

10. **模型**：写 `book-model.json`，字段至少：

```json
{
  "schema": 1,
  "manifest_sha256": "...",
  "edition_status": "draft",
  "pages": [{"index": 0, "kind": "half_title", "id": "half-title",
             "title": "…", "source": null, "group": "front"}],
  "toc": [{"level": 1, "title": "第一篇 基础", "anchor": "part-i",
           "kind": "part", "bookmark": 1}],
  "lof": [{"number": "图 0-1", "title": "夹具插图",
           "caption": "图 0-1　夹具插图",
           "anchor": "p1-01-ch0--fig-1", "source": "p1-01-ch0"}],
  "lot": [{"number": "表 0-1", "title": "夹具表",
           "caption": "表 0-1　夹具表",
           "anchor": "p1-01-ch0--table-1", "source": "p1-01-ch0"}],
  "figures": 1, "tables": 1, "endnotes": 0,
  "audit": {"errors": [], "warnings": [], "pages": 77, "bytes": 0},
  "stats": {"logical_pages": 77, "images": 1, "formulas": 0,
            "chapters": {"0": {"chars": 10}}}
}
```

11. **审计**：复用旧 `audit_html` 的 ID/锚点/远程资源/iframe/体积检查，另外：
   - 77 个 `book-page`；每页恰好一个 `h1`（附录源页降级后由 opener 提供；A 总表页自备 h1）。
   - 无 emoji、无 `<details>`、无 `TODO/TBD/待补/占位`、无 `http://` 图片。
   - TOC/LOF/LOT/索引含 `000`；所有索引锚点存在。
   - 草稿把缺图注/表注、计算器兜底、字数不足、索引/文献/审读数量写入 `warnings`；`final=True` 时这些是 errors。结构错误永远 errors。
   - HTML 目标 <60MB、硬上限 80MB。
12. **写出**：`out_dir.mkdir(parents=True)`；写 `analog-circuit-book.html`、`book-model.json`、`figures.yml`、`tables.yml`。两个 YAML 从 `model["lof"]`/`model["lot"]` 投影，字段为 `id`（= `anchor`）、`chapter`（`number` 中 `-` 前的章号或附录字母）、`number`、`title`、`anchor`、`source`，用 `yaml.safe_dump(..., allow_unicode=True, sort_keys=False)`；它们是只读产物，不反向驱动 LOF/LOT。打印页数/体积/警告数。

`check_html(out_dir, manifest, final=None)` 读取 HTML 与模型，重跑审计但不重建；结构错误返回 1，草稿 warning 只打印。

- [ ] **Step 6: 增补屏幕样式**

在 `book.css` 末尾追加（不改旧规则）：

```css
.half-title, .title-page, .copyright-page, .part-opener, .appendix-opener, .colophon {
  max-width: 46rem; margin: 0 auto;
}
.half-title { min-height: 70vh; display: grid; place-content: center; text-align: center; }
.half-title .book-title { font-size: clamp(2rem, 5vw, 3.4rem); font-weight: 700; }
.half-title .book-subtitle { color: var(--md-default-fg-color--light); }
.part-opener { min-height: 70vh; display: grid; align-content: center; }
.part-kicker { display: block; letter-spacing: .3em; color: var(--md-primary-fg-color); }
.part-title { display: block; font-size: clamp(2rem, 5vw, 3.2rem); }
.part-art { height: 8rem; border-top: 1px solid var(--md-default-fg-color--lightest); }
.book-callout { border-left: 3px solid var(--md-primary-fg-color); padding: .4rem 1rem; margin: 1rem 0; }
.callout-label { font-weight: 700; font-size: .8em; letter-spacing: .08em; }
.book-reveal { border-left: 3px solid var(--md-default-fg-color--lighter); padding: .3rem 1rem; margin: 1rem 0; }
.book-reveal-title { font-weight: 700; font-size: .9em; margin: 0 0 .4rem; }
.book-toc .book-toc-list {
  margin: 0; padding: 0; list-style: none;
  columns: 2; column-gap: 2rem;
}
.book-toc .toc-row { break-inside: avoid; }
.book-toc .toc-row a {
  display: grid; grid-template-columns: 1fr auto auto;
  align-items: baseline; gap: .5rem; min-height: 44px; padding: .2rem 0;
}
.toc-dots { border-bottom: 1px dotted currentColor; opacity: .35; }
.toc-level-2 { padding-left: 1.2rem; }
.toc-level-3 { padding-left: 2.4rem; font-size: .92em; }
@media (max-width: 44.99em) {
  .book-toc .book-toc-list { columns: 1; }
}
.index-columns { column-count: 2; column-gap: 2rem; }
.index-letter h2 { font-size: 1rem; }
.index-page { display: inline-block; min-width: 3ch; text-align: right; }
.answer-list { list-style: none; padding-left: 0; }
.answer-ref { font-family: var(--book-mono, monospace); font-size: .85em; margin-right: .6rem; }
.draft-note { border: 1px dashed currentColor; padding: .6rem .8rem; opacity: .8; }
```

- [ ] **Step 7: 运行装配测试**

Run: `python -B -m unittest discover -s analog-book/tests -p "test_book_quiz.py" -v`
Expected: PASS (4 tests).

Run: `python -B -m unittest discover -s analog-book/tests -p "test_book_build.py" -v`
Expected: PASS (8 tests)。若失败，先修实现，不改测试断言。

- [ ] **Step 8: 提交**

```bash
git add analog-book/book/quiz.py analog-book/book/assemble.py \
  analog-book/tests/test_book_quiz.py analog-book/tests/test_book_build.py \
  analog-book/tests/book_fixtures.py analog-book/styles/book.css
git commit -m "feat(book): assemble 77-page model with exercises and index"
```

---

### Task 8: 16K 内文 PDF——补白、页码标签、三级书签、页码回填与页眉页脚

**Files:**
- Create: `analog-book/book/pdf.py`
- Create: `analog-book/tests/test_book_pdf.py`
- Modify: none

**Interfaces:**
- Consumes: `config`、`fonts.stamp_font_path()`、`manifest.BookError`、`book-model.json`。
- Produces:
  - `print_pdf(html_path, output_pdf, browser_override=None) -> Path`
  - `pad_to_multiple(document, multiple=4) -> list[int]`
  - `stamp_pdf(raw_pdf, output_pdf, model, manifest, fonts_dir=config.FONTS_DIR) -> dict`
  - `check_pdf(pdf_path, model, manifest) -> dict`
  - `build_pdf(html_path, out_dir, manifest, browser_override=None) -> Path`
- `stamp_pdf` 报告键：`pages`、`original_pages`、`body_start`、`starts`、`padded`、`backfilled`、`bookmarks`、`labels`。
- 物理页左右由 **PDF 物理页序** 决定（第 1 物理页为右页），与 CSS 镜像边距一致；阿拉伯页码只用于显示，不用于判断左右。

- [ ] **Step 1: 写失败测试**

Create `analog-book/tests/test_book_pdf.py`:

```python
#!/usr/bin/env python3
"""16K PDF：补白、罗马/阿拉伯标签、三级书签、000 回填、页眉页脚。"""
import sys
import tempfile
import unittest
from pathlib import Path

BOOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BOOK))

from book.pdf import check_pdf, pad_to_multiple, stamp_pdf  # noqa: E402

try:
    import fitz
except ImportError:  # pragma: no cover
    fitz = None

try:
    from playwright.sync_api import sync_playwright
except ImportError:  # pragma: no cover
    sync_playwright = None

MM = 72 / 25.4

FRONT = [
    {"kind": "half_title", "id": "half-title", "title": "半书名", "group": "front"},
    {"kind": "title_page", "id": "title-page", "title": "书名页", "group": "front"},
    {"kind": "copyright", "id": "copyright", "title": "版权页", "group": "front"},
    {"kind": "front", "id": "page-front-a", "title": "前言", "group": "front"},
    {"kind": "front", "id": "page-front-b", "title": "导读", "group": "front"},
    {"kind": "front", "id": "page-front-c", "title": "简史", "group": "front"},
    {"kind": "front", "id": "page-front-d", "title": "约定", "group": "front"},
    {"kind": "toc", "id": "book-toc", "title": "全书目录", "group": "front"},
    {"kind": "list_of_figures", "id": "list-of-figures", "title": "插图目录",
     "group": "front"},
    {"kind": "list_of_tables", "id": "list-of-tables", "title": "表格目录",
     "group": "front"},
    {"kind": "front", "id": "page-front-e", "title": "符号", "group": "front"},
]
BODY = [
    {"kind": "part", "id": "part-i", "title": "第一篇 测试", "group": "body"},
    {"kind": "chapter", "id": "page-p1-01-ch0", "title": "第 0 章 测试章",
     "group": "body"},
    {"kind": "appendix_opener", "id": "appendix-a", "title": "附录 A 测试",
     "group": "appendix"},
    {"kind": "appendix", "id": "page-p0-08-cheatsheet", "title": "附录 B 速查",
     "group": "appendix"},
]
BACK = [
    {"kind": "bibliography", "id": "bibliography", "title": "参考文献", "group": "back"},
    {"kind": "index", "id": "book-index", "title": "索引", "group": "back"},
    {"kind": "back", "id": "page-p9-12-changelog", "title": "版本记录", "group": "back"},
    {"kind": "colophon", "id": "colophon", "title": "版本页", "group": "back"},
]
PAGES = FRONT + BODY + BACK
TOC = [
    {"level": 1, "title": "第一篇 测试", "anchor": "part-i", "kind": "part"},
    {"level": 2, "title": "第 0 章 测试章", "anchor": "page-p1-01-ch0",
     "kind": "chapter"},
    {"level": 3, "title": "0.1 测试小节", "anchor": "p1-01-ch0--s1",
     "kind": "section"},
    {"level": 1, "title": "附录 A 测试", "anchor": "appendix-a", "kind": "appendix"},
    {"level": 2, "title": "附录 B 速查", "anchor": "page-p0-08-cheatsheet",
     "kind": "appendix"},
]
MODEL = {
    "schema": 1, "manifest_sha256": "0" * 64, "edition_status": "draft",
    "pages": PAGES, "toc": TOC,
    "lof": [{"caption": "图 0-1　测试图", "anchor": "p1-01-ch0--fig-1"}],
    "lot": [{"caption": "表 0-1　测试表", "anchor": "p1-01-ch0--table-1"}],
    "figures": 1, "tables": 1, "endnotes": 0,
    "audit": {"errors": [], "warnings": [], "pages": len(PAGES), "bytes": 0},
    "stats": {"logical_pages": len(PAGES), "images": 1, "formulas": 0,
              "chapters": {}},
}
MANIFEST = {
    "title": "通往模拟电路之路", "subtitle": "从欧姆定律到芯片内部结构",
    "author": "zhuguang-ZFG 与贡献者", "license": "CC BY-SA 4.0",
    "release": {"edition_status": "draft"},
}


def _rows(entries):
    return "".join(
        f'<div class="toc-row"><a href="#{e["anchor"]}">'
        f'{e["title"]}<span class="toc-page">000</span></a></div>'
        for e in entries)


def synthetic_html():
    toc = _rows(TOC)
    lof = _rows(MODEL["lof"])
    lot = _rows(MODEL["lot"])
    paragraphs = "".join(
        "<p>" + ("测试正文用于把章节撑到多页，验证续页页眉与页脚。" * 3) + "</p>"
        for _ in range(80))
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
@page {{ size: 185mm 260mm; margin: 20mm; }}
html, body {{ margin: 0; }}
body {{ font-family: serif; font-size: 10.5pt; line-height: 17.5pt; }}
.book-page {{ break-before: page; }}
.book-page:first-of-type {{ break-before: auto; }}
h1 {{ font-size: 22pt; }}
.toc-row a {{ display: flex; justify-content: space-between; }}
figure, table {{ break-inside: avoid; }}
</style></head><body>
<section class="book-page"><h1 id="half-title">半书名</h1></section>
<section class="book-page"><h1 id="title-page">书名页</h1></section>
<section class="book-page"><h1 id="copyright">版权页</h1></section>
<section class="book-page"><h1 id="page-front-a">前言</h1></section>
<section class="book-page"><h1 id="page-front-b">导读</h1></section>
<section class="book-page"><h1 id="page-front-c">简史</h1></section>
<section class="book-page"><h1 id="page-front-d">约定</h1></section>
<section class="book-page"><h1 id="book-toc">全书目录</h1><nav>{toc}</nav></section>
<section class="book-page"><h1 id="list-of-figures">插图目录</h1><nav>{lof}</nav></section>
<section class="book-page"><h1 id="list-of-tables">表格目录</h1><nav>{lot}</nav></section>
<section class="book-page"><h1 id="page-front-e">符号</h1></section>
<section class="book-page"><h1 id="part-i">第一篇 测试</h1></section>
<section class="book-page"><h1 id="page-p1-01-ch0">第 0 章 测试章</h1>
<h2 id="p1-01-ch0--s1">0.1 测试小节</h2>
<figure id="p1-01-ch0--fig-1"><p>图</p><figcaption>图 0-1 测试图</figcaption></figure>
<table id="p1-01-ch0--table-1"><caption>表 0-1 测试表</caption>
<tr><th>列</th></tr><tr><td>值</td></tr></table>{paragraphs}</section>
<section class="book-page"><h1 id="appendix-a">附录 A 测试</h1></section>
<section class="book-page"><h1 id="page-p0-08-cheatsheet">附录 B 速查</h1></section>
<section class="book-page"><h1 id="bibliography">参考文献</h1></section>
<section class="book-page"><h1 id="book-index">索引</h1>
<p><a href="#page-p1-01-ch0"><strong>测试术语</strong></a>
<a href="#p1-01-ch0--s1"><span class="index-page">000</span></a></p></section>
<section class="book-page"><h1 id="page-p9-12-changelog">版本记录</h1></section>
<section class="book-page"><h1 id="colophon">版本页</h1></section>
</body></html>"""


@unittest.skipIf(fitz is None or sync_playwright is None,
                 "需要 PyMuPDF 与 Playwright")
class PdfTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.tmp.cleanup)
        cls.root = Path(cls.tmp.name)
        cls.html = cls.root / "synthetic.html"
        cls.html.write_text(synthetic_html(), encoding="utf-8")
        cls.raw = cls.root / "raw.pdf"
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(cls.html.resolve().as_uri(), wait_until="load")
            page.pdf(path=str(cls.raw), print_background=True,
                     prefer_css_page_size=True, outline=True, tagged=True)
            browser.close()
        cls.pdf = cls.root / "stamped.pdf"
        cls.report = stamp_pdf(cls.raw, cls.pdf, MODEL, MANIFEST)
        cls.doc = fitz.open(cls.pdf)

    @classmethod
    def tearDownClass(cls):
        cls.doc.close()

    def test_page_is_16k_and_padded_to_four(self):
        self.assertEqual(0, self.report["pages"] % 4)
        for page in self.doc:
            self.assertAlmostEqual(185, page.rect.width / MM, delta=0.5)
            self.assertAlmostEqual(260, page.rect.height / MM, delta=0.5)
        self.assertTrue(self.report["padded"])

    def test_page_labels_are_roman_then_arabic(self):
        self.assertEqual("i", self.doc[0].get_label())
        self.assertEqual("xi", self.doc[10].get_label())
        self.assertEqual("1", self.doc[self.report["body_start"]].get_label())
        self.assertEqual("2", self.doc[self.report["body_start"] + 1].get_label())

    def test_bookmarks_are_three_levels_from_model(self):
        toc = self.doc.get_toc()
        self.assertEqual([1, 2, 3, 1, 2], [entry[0] for entry in toc])
        self.assertEqual([entry["title"] for entry in MODEL["toc"]],
                         [entry[1] for entry in toc])
        starts = self.report["starts"]
        self.assertEqual(starts[11] + 1, toc[0][2])
        self.assertEqual(starts[12] + 1, toc[1][2])
        self.assertEqual(starts[12] + 1, toc[2][2])
        self.assertEqual(starts[13] + 1, toc[3][2])
        self.assertEqual(starts[14] + 1, toc[4][2])

    def test_000_is_backfilled_and_links_survive(self):
        starts = self.report["starts"]
        regions = [(starts[7], starts[8]), (starts[8], starts[9]),
                   (starts[9], starts[10]), (starts[16], starts[17])]
        for begin, end in regions:
            text = "\n".join(self.doc[p].get_text() for p in range(begin, end))
            self.assertNotIn("000", text)
        self.assertGreaterEqual(self.report["backfilled"], 7)
        toc_links = [link for link in self.doc[starts[7]].get_links()
                     if isinstance(link.get("page"), int)]
        self.assertEqual(len(TOC), len(toc_links))

    def test_openers_and_front_pages_have_no_folio(self):
        starts = self.report["starts"]
        height = self.doc[0].rect.height
        clip = fitz.Rect(0, height - 18 * MM, self.doc[0].rect.width, height)
        for pno in (0, 1, 2, starts[11], starts[12]):
            self.assertEqual("", self.doc[pno].get_text("text", clip=clip).strip())
        continuation = starts[12] + 1
        self.assertTrue(self.doc[continuation].get_text("text", clip=clip).strip())

    def test_running_heads_use_outer_edge_and_chapter_title(self):
        starts = self.report["starts"]
        clip = fitz.Rect(0, 0, self.doc[0].rect.width, 18 * MM)
        chapter_start = starts[12]
        left_page = chapter_start + 1
        right_page = chapter_start + 2
        self.assertEqual(1, left_page % 2, "物理奇数页必须是左页")
        self.assertEqual(0, right_page % 2, "物理偶数页必须是右页")
        self.assertIn("通往模拟电路之路",
                      self.doc[left_page].get_text("text", clip=clip))
        self.assertIn("第 0 章 测试章",
                      self.doc[right_page].get_text("text", clip=clip))

    def test_check_pdf_reports_draft_length_without_failing(self):
        report = check_pdf(self.pdf, MODEL, MANIFEST)
        self.assertEqual([], report["problems"])
        self.assertTrue(any("450" in warning for warning in report["warnings"]))

    def test_pad_to_multiple_is_idempotent(self):
        doc = fitz.open(self.pdf)
        try:
            before = doc.page_count
            padded = pad_to_multiple(doc, 4)
            self.assertEqual([], padded)
            self.assertEqual(before, doc.page_count)
        finally:
            doc.close()


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 运行测试，确认失败**

Run: `python -B -m unittest discover -s analog-book/tests -p "test_book_pdf.py" -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'book.pdf'`.

- [ ] **Step 3: 实现 `book/pdf.py`**

Create `analog-book/book/pdf.py`:

```python
"""16K 内文 PDF：Chromium 打印、补白、页码标签、书签、回填、页眉页脚。"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from . import config, fonts
from .manifest import BookError

MM = 72 / 25.4
SKIP_KINDS = {"half_title", "title_page", "copyright", "part", "chapter",
              "appendix_opener"}
FRONT_KINDS = {"half_title", "title_page", "copyright", "toc",
               "list_of_figures", "list_of_tables"}
MUTED = (0.32, 0.38, 0.44)
RULE = (0.78, 0.82, 0.86)


def _roman(number: int) -> str:
    values = ((1000, "m"), (900, "cm"), (500, "d"), (400, "cd"), (100, "c"),
              (90, "xc"), (50, "l"), (40, "xl"), (10, "x"), (9, "ix"),
              (5, "v"), (4, "iv"), (1, "i"))
    out = []
    for value, glyph in values:
        while number >= value:
            out.append(glyph)
            number -= value
    return "".join(out)


def _group(page: dict) -> str:
    if page.get("group"):
        return page["group"]
    kind = page["kind"]
    if kind in FRONT_KINDS:
        return "front"
    if kind in {"part", "chapter"}:
        return "body"
    if kind.startswith("appendix"):
        return "appendix"
    return "back"


def _browser_candidates(override: str | None) -> list[Path]:
    candidates = [Path(override)] if override else []
    for command in ("msedge", "chrome", "chromium"):
        found = shutil.which(command)
        if found:
            candidates.append(Path(found))
    for raw in (
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    ):
        candidates.append(Path(raw))
    result, seen = [], set()
    for candidate in candidates:
        resolved = candidate.expanduser().resolve()
        if resolved not in seen and resolved.is_file():
            result.append(resolved)
            seen.add(resolved)
    return result


def print_pdf(html_path: Path, output_pdf: Path,
              browser_override: str | None = None) -> Path:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise BookError(
            "PDF 需要 Playwright：pip install -r analog-book/requirements.txt") from exc
    executables = _browser_candidates(browser_override)
    if browser_override and not executables:
        raise BookError(f"浏览器不存在: {browser_override}")
    launch = {"headless": True}
    if executables:
        launch["executable_path"] = str(executables[0])
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(**launch)
            try:
                context = browser.new_context(reduced_motion="reduce")
                page = context.new_page()
                page.set_default_timeout(300000)
                page.goto(html_path.resolve().as_uri(), wait_until="load")
                page.evaluate(
                    "async () => { if (document.fonts) await document.fonts.ready; }")
                if page.evaluate("() => !!window.MathJax"):
                    page.evaluate("() => MathJax.startup.promise")
                page.wait_for_function(
                    "() => Array.from(document.querySelectorAll('.arithmatex'))"
                    ".every(el => el.querySelector('mjx-container svg'))",
                    timeout=120000)
                page.wait_for_function(
                    "() => Array.from(document.images).every("
                    "img => img.complete && img.naturalWidth > 0)",
                    timeout=60000)
                page.pdf(path=str(output_pdf), print_background=True,
                         prefer_css_page_size=True, outline=True, tagged=True)
            finally:
                browser.close()
    except BookError:
        raise
    except Exception as exc:
        raise BookError(f"PDF 构建失败: {exc}") from exc
    return output_pdf


def pad_to_multiple(document, multiple: int = 4) -> list[int]:
    if document.page_count == 0:
        raise BookError("PDF 没有页面")
    remainder = document.page_count % multiple
    if remainder == 0:
        return []
    first = document.page_count
    width = document[0].rect.width
    height = document[0].rect.height
    for _ in range(multiple - remainder):
        document.new_page(width=width, height=height)
    return list(range(first, document.page_count))


def _is_blank(page) -> bool:
    return not page.get_text().strip() and not page.get_images()


def _page_starts(document, model: dict) -> list[int]:
    outline = [entry for entry in document.get_toc() if entry[0] == 1]
    pages = model["pages"]
    if len(outline) != len(pages):
        raise BookError(
            f"PDF 一级大纲 {len(outline)} 个，书模型 {len(pages)} 页；"
            "每页必须恰好一个可见 h1")
    starts = [entry[2] - 1 for entry in outline]
    if len(set(starts)) != len(starts) or starts != sorted(starts):
        raise BookError("PDF 一级大纲顺序与页序不一致")
    if starts[0] != 0:
        raise BookError(f"PDF 第一个 h1 不在第 1 页: {starts[0] + 1}")
    return starts


def _000_word(page, rect):
    words = [word for word in page.get_text("words", clip=rect)
             if word[4] == "000"]
    return words[0] if words else None


def _region_links(document, start: int, end: int, body_start: int):
    import fitz
    links = []
    for pno in range(start, end):
        page = document[pno]
        for link in page.get_links():
            target = link.get("page")
            if not isinstance(target, int) or target < body_start:
                continue
            rect = fitz.Rect(link["from"])
            word = _000_word(page, rect)
            if word is None:
                continue
            links.append({"page": pno, "target": target, "rect": rect,
                          "word": word})
    links.sort(key=lambda item: (item["page"], round(item["rect"].y0, 1),
                                 round(item["rect"].x0, 1)))
    return links


def _backfill(document, start: int, end: int, body_start: int,
              expected: int | None = None):
    import fitz
    links = _region_links(document, start, end, body_start)
    if expected is not None and len(links) != expected:
        raise BookError(
            f"页码占位 {len(links)} 个，目录项 {expected} 个；"
            "每个目录行必须恰好一个链接且包含 000")
    for item in links:
        page = document[item["page"]]
        label = str(item["target"] - body_start + 1)
        page.draw_rect(
            fitz.Rect(item["word"][0] - 0.6, item["word"][1] - 0.6,
                      item["word"][2] + 0.6, item["word"][3] + 0.6),
            color=None, fill=(1, 1, 1), overlay=True)
        width = fitz.get_text_length(label, fontname="helv", fontsize=9)
        page.insert_text((item["word"][2] - width, item["word"][3] - 1.2),
                         label, fontname="helv", fontsize=9, color=MUTED)
    remaining = [pno + 1 for pno in range(start, end)
                 if "000" in document[pno].get_text()]
    if remaining:
        raise BookError(f"页码回填后仍有 000：物理页 {remaining[:5]}")
    return links


def _section_for(pno: int, starts: list[int], model: dict) -> dict:
    pages = model["pages"]
    chosen = 0
    for index, start in enumerate(starts[:len(pages)]):
        if start <= pno:
            chosen = index
        else:
            break
    return pages[chosen]


def _stamp_running(document, model: dict, starts: list[int], body_start: int,
                   manifest: dict, padding: list[int], fonts_dir: Path) -> None:
    import fitz
    stamp_path = fonts.stamp_font_path(fonts_dir)
    if not stamp_path.is_file():
        raise BookError(f"缺少印章字体: {stamp_path}")
    stamp = fitz.Font(fontfile=str(stamp_path))
    skip = set(padding)
    for index, page in enumerate(model["pages"]):
        if page["kind"] in SKIP_KINDS:
            skip.add(starts[index])
    width_page = document[0].rect.width
    height_page = document[0].rect.height
    outside = 18 * MM
    inside = 22 * MM
    for pno in range(document.page_count):
        page = document[pno]
        if pno in skip or _is_blank(page):
            continue
        page.insert_font(fontname="bookstamp", fontfile=str(stamp_path))
        is_right = pno % 2 == 0
        info = _section_for(pno, starts, model)
        label = _roman(pno + 1) if pno < body_start else str(pno - body_start + 1)
        heading = info.get("header") or info["title"]
        if is_right:
            header = heading
            header_x = width_page - outside - stamp.text_length(header, 8)
            folio_x = width_page - outside - fitz.get_text_length(
                label, fontname="helv", fontsize=8)
            rule_start, rule_end = inside, width_page - outside
        else:
            header = manifest["title"]
            header_x = outside
            folio_x = outside
            rule_start, rule_end = outside, width_page - inside
        page.insert_text((header_x, 12 * MM), header, fontname="bookstamp",
                         fontsize=8, color=MUTED)
        page.draw_line(fitz.Point(rule_start, 14.2 * MM),
                       fitz.Point(rule_end, 14.2 * MM),
                       color=RULE, width=0.3)
        page.insert_text((folio_x, height_page - 9 * MM), label,
                         fontname="helv", fontsize=8, color=MUTED)


def _bookmarks(model: dict, starts: list[int], toc_targets: dict[str, int]):
    page_targets = {page["id"]: starts[index]
                    for index, page in enumerate(model["pages"])}
    entries, previous_level = [], 0
    for entry in model["toc"]:
        anchor = entry["anchor"]
        target = page_targets.get(anchor, toc_targets.get(anchor))
        if target is None:
            raise BookError(f"书签锚点没有目标页: {anchor}")
        level = int(entry["level"])
        if level < 1 or level > 3 or level > previous_level + 1:
            raise BookError(f"书签层级非法: {entry}")
        entries.append([level, entry["title"], target + 1])
        previous_level = level
    return entries


def stamp_pdf(raw_pdf: Path, output_pdf: Path, model: dict, manifest: dict,
              fonts_dir: Path = config.FONTS_DIR) -> dict:
    try:
        import fitz
    except ImportError as exc:
        raise BookError(
            "PDF 需要 PyMuPDF：pip install -r analog-book/requirements.txt") from exc
    if model.get("edition_status") != manifest["release"]["edition_status"]:
        raise BookError("PDF 模型与 manifest 的版本状态不一致，请重建 HTML")
    document = fitz.open(raw_pdf)
    try:
        original_pages = document.page_count
        padding = pad_to_multiple(document)
        starts = _page_starts(document, model)
        body_start = starts[next(
            index for index, page in enumerate(model["pages"])
            if _group(page) != "front")]
        kinds = [page["kind"] for page in model["pages"]]
        toc_index = kinds.index("toc")
        lof_index = kinds.index("list_of_figures")
        lot_index = kinds.index("list_of_tables")
        index_index = kinds.index("index")
        toc_start, toc_end = starts[toc_index], starts[toc_index + 1]
        lof_start, lof_end = starts[lof_index], starts[lof_index + 1]
        lot_start, lot_end = starts[lot_index], starts[lot_index + 1]
        index_start, index_end = starts[index_index], starts[index_index + 1]
        toc_links = _backfill(document, toc_start, toc_end, body_start,
                              expected=len(model["toc"]))
        toc_targets = {entry["anchor"]: link["target"]
                       for entry, link in zip(model["toc"], toc_links)}
        filled = len(toc_links)
        filled += len(_backfill(document, lof_start, lof_end, body_start,
                                expected=len(model["lof"])))
        filled += len(_backfill(document, lot_start, lot_end, body_start,
                                expected=len(model["lot"])))
        filled += len(_backfill(document, index_start, index_end, body_start))
        _stamp_running(document, model, starts, body_start, manifest,
                       padding, fonts_dir)
        document.set_toc(_bookmarks(model, starts, toc_targets))
        document.set_page_labels([
            {"startpage": 0, "prefix": "", "style": "r", "firstpagenum": 1},
            {"startpage": body_start, "prefix": "", "style": "D",
             "firstpagenum": 1},
        ])
        document.set_metadata({
            "title": manifest["title"],
            "author": manifest["author"],
            "subject": manifest["subtitle"],
            "keywords": "模拟电路, 电子, 16K, " + manifest["license"],
            "creator": "analog-circuit-roadmap/book",
        })
        document.save(output_pdf, garbage=3, deflate=True)
        return {
            "pages": document.page_count,
            "original_pages": original_pages,
            "body_start": body_start,
            "starts": starts,
            "padded": padding,
            "backfilled": filled,
            "bookmarks": len(model["toc"]),
            "labels": ["i", _roman(body_start), "1"],
        }
    finally:
        document.close()


def check_pdf(pdf_path: Path, model: dict, manifest: dict) -> dict:
    try:
        import fitz
    except ImportError as exc:
        raise BookError(
            "PDF 需要 PyMuPDF：pip install -r analog-book/requirements.txt") from exc
    document = fitz.open(pdf_path)
    try:
        problems, warnings = [], []
        pages = document.page_count
        final = manifest["release"]["edition_status"] == "final"
        for page in document:
            width = page.rect.width / MM
            height = page.rect.height / MM
            if abs(width - 185) > 0.5 or abs(height - 260) > 0.5:
                problems.append(f"页面尺寸 {width:.1f}×{height:.1f}mm 不是 16K")
                break
        if pages % 4:
            problems.append(f"页数 {pages} 不是 4 的倍数")
        labels = [page.get_label() for page in document]
        if not labels or labels[0] != "i":
            problems.append("第 1 页页码标签不是 i")
        try:
            body_start = labels.index("1")
        except ValueError:
            body_start = -1
            problems.append("找不到阿拉伯页码 1 的起始页")
        toc = document.get_toc()
        if len(toc) != len(model["toc"]):
            problems.append(f"书签 {len(toc)} 条，模型 {len(model['toc'])} 条")
        if any(entry[0] > 3 for entry in toc):
            problems.append("书签超过三级")
        if pages < 450:
            if final:
                problems.append(f"页数 {pages} 低于硬区间下限 450")
            else:
                warnings.append(f"草稿页数 {pages}，低于目标区间 450–700")
        if pages > 700:
            problems.append(f"页数 {pages} 超过硬上限 700")
        if final and pages < 535:
            warnings.append(f"页数 {pages} 低于目标区间下限 535")
        if final and pages > 653:
            warnings.append(f"页数 {pages} 高于目标区间上限 653")
        if not final:
            warnings.append(
                "草稿只检查 16K 结构项；字体嵌入、缺字、公式矢量、版心溢出、"
                "图表跨页与 PDF <100MB 等印前全检在 Phase 5 执行")
        return {"pages": pages, "body_start": body_start, "labels": labels[:12],
                "bookmarks": len(toc),
                "max_level": max((entry[0] for entry in toc), default=0),
                "problems": problems, "warnings": warnings}
    finally:
        document.close()


def build_pdf(html_path: Path, out_dir: Path, manifest: dict,
              browser_override: str | None = None) -> Path:
    model_path = out_dir / config.MODEL_NAME
    if not model_path.is_file():
        raise BookError(f"缺少书模型: {model_path}")
    model = json.loads(model_path.read_text(encoding="utf-8"))
    raw = out_dir / ".analog-book.raw.pdf"
    output = out_dir / config.PDF_NAME
    try:
        print_pdf(html_path, raw, browser_override)
        report = stamp_pdf(raw, output, model, manifest)
        pdf_report = check_pdf(output, model, manifest)
    finally:
        raw.unlink(missing_ok=True)
    if pdf_report["problems"]:
        raise BookError("PDF 审计失败:\n" + "\n".join(pdf_report["problems"]))
    for warning in pdf_report["warnings"]:
        print(f"pdf warning: {warning}")
    print(f"pdf   {output} ({output.stat().st_size} bytes, {report['pages']} pages)")
    return output
```

实现要点：

- `_page_starts` 只用 PDF 一级大纲。每页一个可见 h1 是 7B 审计的硬约束；大纲数量不等于 77 时直接失败，不猜测。
- `_backfill` 先按 `(物理页, y0, x0)` 排序再配对，保证多页目录与折行目录都不乱序；每条链接矩形内必须找到 `000`，否则不计入。
- 目录/图目录/表目录期望条数分别等于模型 `toc`/`lof`/`lot`；索引只要求回填全部占位。回填后用 `get_text()` 再查一遍 `000`，防止漏网。
- `stamp_pdf` 不修改链接注记，只覆盖白底并重写数字；`000` 占位必须位于 `<a>` 内部，这是 7A 的契约。
- 页眉：物理右页（索引偶）放当前章节名，物理左页放书名；页码在外下角。章首页、篇首页、附录首页、前置前三页、空白页跳过。正文页码从 1 开始，但页眉左右按物理页序，不按页码奇偶。
- 页数补到 4 的倍数在 `stamp_pdf` 内完成；补白页无页眉页脚，但占页码标签。
- 若 Chromium 因 `break-before: right` 插入空白页，`starts` 会自动包含它；空白页靠 `_is_blank` 跳过页眉页脚。

- [ ] **Step 4: 运行测试，确认通过**

Run: `python -B -m unittest discover -s analog-book/tests -p "test_book_pdf.py" -v`
Expected: PASS (8 tests). 若页码标签断言失败，先打印 `[page.get_label() for page in fitz.open(pdf)]`，确认 `body_start` 来自一级大纲而不是 `front` 页数硬算。

- [ ] **Step 5: 提交**

```bash
git add analog-book/book/pdf.py analog-book/tests/test_book_pdf.py
git commit -m "feat(book): stamp 16K PDF with labels, bookmarks and folios"
```

---

---

### Task 9: 印刷封面——书脊公式、正/背/书脊、出血裁切线、二维码与预览

**Files:**
- Create: `analog-book/book/cover.py`
- Create: `analog-book/cover/cover.css`
- Create: `analog-book/tests/test_book_cover.py`
- Modify: `analog-book/requirements.txt`（加入 `qrcode>=7.4,<9`）

**Interfaces:**
- Consumes: `config`、`fonts.font_css()`、`pdf.print_pdf()`、`static/cover-art.svg`、manifest 的 `cover.back_cover`。
- Produces:
  - `spine_mm(pages, manifest) -> float`
  - `cover_size_mm(pages, manifest) -> tuple[float, float]`
  - `qr_svg(data: str) -> str`
  - `cover_html(manifest, pages, fonts_css="") -> str`
  - `inspect_cover(pdf_path, pages, manifest) -> dict`
  - `build_cover(out_dir, pages, manifest, browser_override=None) -> tuple[Path, Path, Path]`
- 书脊公式唯一来源：`pages / 2 × paper_caliper_mm + spine_allowance_mm`，四舍五入 2 位；manifest 的 `spine_mm` 不允许手填（Task 1 已校验）。
- 封面页尺寸：(2×185 + spine + 2×3) × (260 + 2×3) mm；不写假 ISBN、假条码、假出版社。

- [ ] **Step 1: 写失败测试**

Create `analog-book/tests/test_book_cover.py`:

```python
#!/usr/bin/env python3
"""封面：书脊公式、尺寸、出血、裁切线、二维码与无假 ISBN。"""
import re
import sys
import tempfile
import unittest
from pathlib import Path

BOOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BOOK))

from book import config  # noqa: E402
from book.cover import (build_cover, cover_html, cover_size_mm,  # noqa: E402
                        inspect_cover, qr_svg, spine_mm)

try:
    import fitz
except ImportError:  # pragma: no cover
    fitz = None

try:
    from playwright.sync_api import sync_playwright
except ImportError:  # pragma: no cover
    sync_playwright = None

MANIFEST = {
    "title": "通往模拟电路之路",
    "subtitle": "从欧姆定律到芯片内部结构",
    "edition": "第一版", "version": "2.0.0-draft.1", "date": "2026-10-25",
    "author": "zhuguang-ZFG 与贡献者", "license": "CC BY-SA 4.0",
    "site_url": "https://example.test/analog/",
    "repository": "https://github.com/example/analog",
    "trim": {"width_mm": 185, "height_mm": 260},
    "cover": {
        "bleed_mm": 3, "crop_marks": True, "paper_caliper_mm": 0.10,
        "spine_allowance_mm": 1.0, "isbn_area": False,
        "back_cover": {
            "blurb": "把直觉、推导、仿真、实测与排故连起来。",
            "audience": "电子、自动化、通信与嵌入式方向的学生和工程师。",
            "highlights": ["19 章完整知识链", "三层读法", "可复现仿真",
                           "实测实验", "故障速查与索引"],
        },
    },
    "release": {"edition_status": "draft"},
}


class SpineTests(unittest.TestCase):
    def test_spine_formula_uses_final_page_count(self):
        self.assertEqual(31.0, spine_mm(600, MANIFEST))
        self.assertEqual(33.5, spine_mm(650, MANIFEST))
        self.assertEqual(26.0, spine_mm(500, MANIFEST))

    def test_cover_size_includes_two_trim_panels_and_bleed(self):
        width, height = cover_size_mm(650, MANIFEST)
        self.assertAlmostEqual(409.5, width, places=2)
        self.assertAlmostEqual(266.0, height, places=2)

    def test_cover_size_rejects_zero_pages(self):
        with self.assertRaises(ValueError):
            cover_size_mm(0, MANIFEST)


class CoverHtmlTests(unittest.TestCase):
    def setUp(self):
        self.html = cover_html(MANIFEST, 650)

    def test_three_panels_and_title(self):
        for value in ('class="cover-panel cover-back"',
                      'class="cover-panel cover-spine"',
                      'class="cover-panel cover-front"',
                      "通往模拟电路之路", "从欧姆定律到芯片内部结构",
                      "zhuguang-ZFG 与贡献者", "第一版"):
            self.assertIn(value, self.html)

    def test_has_eight_crop_marks_and_bleed(self):
        self.assertEqual(8, self.html.count('<line class="crop-mark"'))
        self.assertIn("3mm", (config.COVER_DIR / "cover.css").read_text(
            encoding="utf-8").replace("__BLEED__", "3"))

    def test_spine_is_vertical_and_can_be_thin(self):
        css = (config.COVER_DIR / "cover.css").read_text(encoding="utf-8")
        self.assertIn("writing-mode: vertical-rl", css)
        thin = cover_html(MANIFEST, 80)
        self.assertIn('class="cover-panel cover-spine is-thin"', thin)
        self.assertNotIn('class="spine-text"', thin)

    def test_back_cover_has_blurb_highlights_qr_and_blank_isbn(self):
        for text in ("把直觉、推导、仿真、实测与排故连起来。",
                     "电子、自动化、通信与嵌入式方向", "19 章完整知识链",
                     "故障速查与索引", "ISBN / 条码预留区（留空）",
                     'data-qr="site"', 'data-qr="repo"'):
            self.assertIn(text, self.html)
        self.assertNotRegex(self.html, r"ISBN[^<]{0,16}\d{10,13}")
        self.assertNotIn("978-", self.html)

    def test_qr_is_inline_vector_and_no_remote_assets(self):
        svg = qr_svg(MANIFEST["site_url"])
        self.assertTrue(svg.startswith("<svg"))
        self.assertIn("path", svg)
        self.assertNotIn("<image", svg)
        self.assertNotIn('<img src="http', self.html)
        self.assertNotIn("<iframe", self.html)

    def test_cover_art_is_inlined(self):
        self.assertIn("cover-dots", self.html)
        self.assertIn("<svg", self.html)


@unittest.skipIf(fitz is None or sync_playwright is None,
                 "需要 PyMuPDF 与 Playwright")
class CoverBuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.tmp.cleanup)
        cls.out = Path(cls.tmp.name) / "dist"
        cls.html_path, cls.pdf_path, cls.png_path = build_cover(
            cls.out, 650, MANIFEST)

    def test_pdf_size_and_single_page(self):
        report = inspect_cover(self.pdf_path, 650, MANIFEST)
        self.assertEqual([], report["problems"])
        self.assertEqual(1, report["pages"])
        width, height = report["size_mm"]
        self.assertAlmostEqual(409.5, width, delta=0.5)
        self.assertAlmostEqual(266.0, height, delta=0.5)

    def test_preview_is_150dpi(self):
        doc = fitz.open(self.pdf_path)
        try:
            pix = doc[0].get_pixmap(dpi=150)
            expected_width = round(409.5 / 25.4 * 150)
            self.assertAlmostEqual(expected_width, pix.width, delta=3)
            self.assertTrue(self.png_path.is_file())
            self.assertGreater(self.png_path.stat().st_size, 50_000)
        finally:
            doc.close()

    def test_text_survives_printing(self):
        doc = fitz.open(self.pdf_path)
        try:
            text = doc[0].get_text()
        finally:
            doc.close()
        for value in ("通往模拟电路之路", "从欧姆定律到芯片内部结构",
                      "zhuguang-ZFG 与贡献者", "ISBN / 条码预留区"):
            self.assertIn(value, text)

    def test_build_refuses_wrong_page_count(self):
        with self.assertRaises(ValueError):
            build_cover(self.out / "bad", 0, MANIFEST)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 运行测试，确认失败**

Run: `python -B -m unittest discover -s analog-book/tests -p "test_book_cover.py" -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'book.cover'`.

- [ ] **Step 3: 写 `cover/cover.css`**

Create `analog-book/cover/cover.css`:

```css
@page { size: __WIDTH__mm __HEIGHT__mm; margin: 0; }
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; background: #fffdf8; }
body {
  font-family: "Book Sans", "Noto Sans SC", sans-serif;
  color: #1f2933;
}
.cover {
  position: relative; overflow: hidden;
  width: __WIDTH__mm; height: __HEIGHT__mm; background: #fffdf8;
}
.cover-marks { position: absolute; inset: 0; width: 100%; height: 100%; z-index: 20; }
.crop-mark { stroke: #111; stroke-width: .2; }
.cover-panel { position: absolute; top: __BLEED__mm; height: __TRIM_H__mm; }
.cover-front {
  left: calc(__BLEED__mm + __TRIM_W__mm + __SPINE__mm);
  width: __TRIM_W__mm; padding: 18mm 16mm;
  display: flex; flex-direction: column;
}
.cover-spine {
  left: calc(__BLEED__mm + __TRIM_W__mm);
  width: __SPINE__mm; background: #b45309; color: #fffdf8;
  display: flex; align-items: center; justify-content: center;
}
.cover-back {
  left: __BLEED__mm; width: __TRIM_W__mm; padding: 18mm 16mm;
  background: #1f2933; color: #fffdf8;
  display: flex; flex-direction: column; justify-content: space-between;
}
.front-kicker {
  margin: 0; font-size: 10pt; letter-spacing: .22em; color: #b45309;
}
.front-art { margin: 4mm 0 6mm; }
.front-art svg { display: block; width: 100%; height: auto; max-height: 86mm; }
.front-title {
  margin: 0; font-family: "Book Serif", "Noto Serif SC", serif;
  font-size: 34pt; line-height: 1.18; letter-spacing: .04em;
}
.front-subtitle { margin: 4mm 0 0; font-size: 14pt; line-height: 1.5; color: #52606d; }
.front-rule { width: 34mm; height: 1.2mm; margin: 9mm 0; background: #b45309; }
.front-author { margin: 0; font-size: 12pt; }
.front-edition { margin: 3mm 0 0; font-size: 10pt; color: #52606d; }
.front-site { margin: auto 0 0; font-size: 8.5pt; color: #52606d; }
.spine-text {
  writing-mode: vertical-rl; text-orientation: upright;
  display: flex; align-items: center; gap: 8mm;
  font-family: "Book Serif", "Noto Serif SC", serif;
}
.spine-title { font-size: 13pt; letter-spacing: .12em; }
.spine-author { font-size: 9pt; letter-spacing: .08em; opacity: .85; }
.cover-spine.is-thin .spine-text { display: none; }
.back-kicker { margin: 0; font-size: 9pt; letter-spacing: .2em; color: #f0c38a; }
.back-blurb {
  margin: 3mm 0 0; font-family: "Book Serif", "Noto Serif SC", serif;
  font-size: 15pt; line-height: 1.7;
}
.back-audience { margin: 5mm 0 0; font-size: 9.5pt; line-height: 1.7; color: #cfd8e3; }
.back-highlights { margin: 5mm 0 0; padding-left: 5mm; font-size: 9.5pt; line-height: 1.8; }
.back-highlights li::marker { color: #f0c38a; }
.back-qr { display: flex; gap: 8mm; margin-top: 6mm; }
.qr {
  width: 24mm; padding: 2mm; background: #fffdf8; color: #1f2933;
  text-align: center; font-size: 7.5pt; line-height: 1.4;
}
.qr svg { display: block; width: 20mm; height: 20mm; }
.isbn-area {
  margin-top: 5mm; width: 40mm; height: 25mm; border: .3mm dashed #98a2b3;
  display: flex; align-items: center; justify-content: center;
  font-size: 7pt; color: #98a2b3; text-align: center;
}
.back-license { margin: 5mm 0 0; font-size: 8pt; color: #cfd8e3; }
.back-errata { margin: 1.5mm 0 0; font-size: 8pt; color: #cfd8e3; }
```

- [ ] **Step 4: 实现 `book/cover.py`**

Create `analog-book/book/cover.py`:

```python
"""印刷封面：书脊公式、三栏版式、裁切线、二维码与 150dpi 预览。"""
from __future__ import annotations

import html
import json
from pathlib import Path

from . import config, fonts
from .manifest import BookError
from .pdf import print_pdf


def spine_mm(pages: int, manifest: dict) -> float:
    if pages <= 0:
        raise ValueError("页数必须为正")
    cover = manifest["cover"]
    value = pages / 2 * cover["paper_caliper_mm"] + cover["spine_allowance_mm"]
    return round(value, 2)


def cover_size_mm(pages: int, manifest: dict) -> tuple[float, float]:
    if pages <= 0:
        raise ValueError("页数必须为正")
    trim = manifest["trim"]
    bleed = manifest["cover"]["bleed_mm"]
    width = 2 * trim["width_mm"] + spine_mm(pages, manifest) + 2 * bleed
    height = trim["height_mm"] + 2 * bleed
    return round(width, 2), round(height, 2)


def qr_svg(data: str) -> str:
    try:
        import qrcode
        import qrcode.image.svg
    except ImportError as exc:
        raise BookError("封面二维码需要 qrcode：pip install qrcode") from exc
    image = qrcode.make(data, image_factory=qrcode.image.svg.SvgPathImage,
                        box_size=10, border=2)
    text = image.to_string().decode("utf-8")
    return text[text.index("<svg"):]


def _e(value) -> str:
    return html.escape(str(value), quote=True)


def _crop_marks(width: float, height: float, bleed: float) -> str:
    left, right = bleed, width - bleed
    top, bottom = bleed, height - bleed
    short = max(1.0, bleed - 0.8)
    lines = [
        (left, 0, left, short), (left, height - short, left, height),
        (right, 0, right, short), (right, height - short, right, height),
        (0, top, short, top), (width - short, top, width, top),
        (0, bottom, short, bottom), (width - short, bottom, width, bottom),
    ]
    return "".join(
        f'<line class="crop-mark" x1="{x1:.2f}" y1="{y1:.2f}" '
        f'x2="{x2:.2f}" y2="{y2:.2f}"/>'
        for x1, y1, x2, y2 in lines)


def _cover_css(width: float, height: float, spine: float,
               manifest: dict) -> str:
    trim = manifest["trim"]
    bleed = manifest["cover"]["bleed_mm"]
    template = (config.COVER_DIR / "cover.css").read_text(encoding="utf-8")
    return (template.replace("__WIDTH__", f"{width:.2f}")
            .replace("__HEIGHT__", f"{height:.2f}")
            .replace("__TRIM_W__", f"{trim['width_mm']:.2f}")
            .replace("__TRIM_H__", f"{trim['height_mm']:.2f}")
            .replace("__BLEED__", f"{bleed:.2f}")
            .replace("__SPINE__", f"{spine:.2f}"))


def _cover_art() -> str:
    path = config.STATIC_DIR / "cover-art.svg"
    if not path.is_file():
        raise BookError(f"缺少封面插图: {path}")
    return path.read_text(encoding="utf-8")


def cover_html(manifest: dict, pages: int, fonts_css: str = "") -> str:
    width, height = cover_size_mm(pages, manifest)
    spine = spine_mm(pages, manifest)
    back = manifest["cover"]["back_cover"]
    highlights = "".join(f"<li>{_e(item)}</li>" for item in back["highlights"])
    spine_class = "cover-spine is-thin" if spine < 6 else "cover-spine"
    spine_text = "" if spine < 6 else (
        '<div class="spine-text">'
        f'<span class="spine-title">{_e(manifest["title"])}</span>'
        f'<span class="spine-author">{_e(manifest["author"])}</span>'
        '</div>')
    site_qr = qr_svg(manifest["site_url"])
    repo_qr = qr_svg(manifest["repository"])
    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><title>{_e(manifest["title"])} · 封面</title>
<style>{fonts_css}
{_cover_css(width, height, spine, manifest)}</style></head>
<body><div class="cover">
<svg class="cover-marks" viewBox="0 0 {width:.2f} {height:.2f}" xmlns="http://www.w3.org/2000/svg">
{_crop_marks(width, height, manifest["cover"]["bleed_mm"])}
</svg>
<section class="cover-panel cover-back">
<div>
<p class="back-kicker">关于本书</p>
<p class="back-blurb">{_e(back["blurb"])}</p>
<p class="back-audience"><strong>适合读者</strong>　{_e(back["audience"])}</p>
<ul class="back-highlights">{highlights}</ul>
</div>
<div>
<div class="back-qr">
<div class="qr" data-qr="site">{site_qr}<span>在线站</span></div>
<div class="qr" data-qr="repo">{repo_qr}<span>仓库</span></div>
</div>
<div class="isbn-area"><span>ISBN / 条码预留区（留空）</span></div>
<p class="back-license">{_e(manifest["license"])} · {_e(manifest["edition"])} · {_e(manifest["version"])}</p>
<p class="back-errata">勘误与讨论：{_e(manifest["repository"])}/issues</p>
</div>
</section>
<section class="cover-panel {spine_class}">{spine_text}</section>
<section class="cover-panel cover-front">
<p class="front-kicker">16K · 模拟电路</p>
<div class="front-art">{_cover_art()}</div>
<h1 class="front-title">{_e(manifest["title"])}</h1>
<p class="front-subtitle">{_e(manifest["subtitle"])}</p>
<p class="front-rule"></p>
<p class="front-author">{_e(manifest["author"])}</p>
<p class="front-edition">{_e(manifest["edition"])} · {_e(manifest["version"])}</p>
<p class="front-site">{_e(manifest["site_url"])}</p>
</section>
</div></body></html>
"""


def inspect_cover(pdf_path: Path, pages: int, manifest: dict) -> dict:
    try:
        import fitz
    except ImportError as exc:
        raise BookError("封面检查需要 PyMuPDF") from exc
    expected_width, expected_height = cover_size_mm(pages, manifest)
    document = fitz.open(pdf_path)
    try:
        problems = []
        if document.page_count != 1:
            problems.append(f"封面应为 1 页，实际 {document.page_count} 页")
        page = document[0]
        width = page.rect.width / (72 / 25.4)
        height = page.rect.height / (72 / 25.4)
        if abs(width - expected_width) > 0.5 or abs(height - expected_height) > 0.5:
            problems.append(
                f"封面尺寸 {width:.2f}×{height:.2f}mm，"
                f"应为 {expected_width}×{expected_height}mm")
        return {"pages": document.page_count,
                "size_mm": [round(width, 2), round(height, 2)],
                "spine_mm": spine_mm(pages, manifest),
                "problems": problems}
    finally:
        document.close()


def build_cover(out_dir: Path, pages: int, manifest: dict,
                browser_override: str | None = None):
    if pages <= 0:
        raise ValueError("页数必须为正")
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    html_path = out_dir / "cover.html"
    pdf_path = out_dir / config.COVER_PDF_NAME
    preview_path = out_dir / config.COVER_PREVIEW_NAME
    html_path.write_text(
        cover_html(manifest, pages, fonts.font_css()), encoding="utf-8",
        newline="\n")
    print_pdf(html_path, pdf_path, browser_override)
    report = inspect_cover(pdf_path, pages, manifest)
    if report["problems"]:
        raise BookError("封面审计失败:\n" + "\n".join(report["problems"]))
    try:
        import fitz
    except ImportError as exc:
        raise BookError("封面预览需要 PyMuPDF") from exc
    document = fitz.open(pdf_path)
    try:
        pixmap = document[0].get_pixmap(dpi=150)
        pixmap.save(preview_path)
    finally:
        document.close()
    print(f"cover {pdf_path} ({pages} pages -> spine {report['spine_mm']} mm)")
    return html_path, pdf_path, preview_path
```

- [ ] **Step 5: 运行测试，确认通过**

Run: `python -B -m unittest discover -s analog-book/tests -p "test_book_cover.py" -v`
Expected: PASS (13 tests). 打开 `analog-book/dist/print/cover-preview.png` 目检：前封标题不压纹样、书脊文字距上下边 ≥10mm、后封二维码完整、ISBN 区为空白。

- [ ] **Step 6: 提交**

```bash
git add analog-book/book/cover.py analog-book/cover/cover.css \
  analog-book/tests/test_book_cover.py analog-book/requirements.txt
git commit -m "feat(book): generate print cover with spine and crop marks"
```

---

---

### Task 10: 可运行 SPICE 骨架——第 1 章 RC deck、断言、批处理与真实数据出图

**Files:**
- Create: `assets/spice/ch01/rc.cir`
- Create: `assets/spice/ch01/assert.json`
- Create: `assets/spice/ch01/README.md`
- Create: `scripts/run_spice.py`
- Create: `scripts/plot_sim.py`
- Create: `analog-book/tests/test_spice.py`

**Interfaces:**
- Produces（`scripts/run_spice.py`）：
  - `Case` dataclass：`directory`、`deck`、`spec`
  - `find_ngspice() -> Path | None`
  - `discover_cases(root=SPICE_DIR) -> list[Case]`
  - `parse_measurements(text) -> dict[str, float]`
  - `compare_metrics(actual, expected) -> list[str]`
  - `load_data(path, min_rows) -> list[tuple[float, float]]`
  - `run_case(case, ngspice, timeout=120) -> dict`
  - `main(argv=None) -> int`
- Produces（`scripts/plot_sim.py`）：`load_data(path) -> list[tuple[float, float]]`、`plot(csv_path, output, title) -> Path`。
- `assert.json` schema：`deck`、`analysis`、`data`、`min_rows`、`metrics`；每个 metric 为 `{"expected": float, "tolerance": float > 0}`。没有 ngspice 时本地跳过；`BOOK_REQUIRE_NGSPICE=1` 时缺失即失败。

- [ ] **Step 1: 写 deck、断言与说明**

Create `assets/spice/ch01/rc.cir`:

```spice
* RC 一阶阶跃响应：R=1k, C=100n, tau=100us
* 仅用 ngspice 内置元件，不依赖任何厂商模型。
.param VDD=5 R=1k C=100n
V1 in 0 PULSE(0 {VDD} 1u 1u 1u 10m 20m)
R1 in out {R}
C1 out 0 {C}
.tran 1u 5m 0 1u
.control
run
set wr_singlescale
set wr_vecnames
wrdata rc.dat v(out)
meas tran vfinal FIND v(out) AT=5m
meas tran vhalf WHEN v(out)=2.5 RISE=1
meas tran trise TRIG v(out) VAL=0.5 RISE=1 TARG v(out) VAL=4.5 RISE=1
print vfinal vhalf trise
.endc
.end
```

Create `assets/spice/ch01/assert.json`:

```json
{
  "deck": "rc.cir",
  "analysis": "tran",
  "data": "rc.dat",
  "min_rows": 200,
  "metrics": {
    "vfinal": {"expected": 5.0, "tolerance": 0.02},
    "vhalf": {"expected": 0.0000693, "tolerance": 0.000005},
    "trise": {"expected": 0.0002197, "tolerance": 0.00002}
  }
}
```

Create `assets/spice/ch01/README.md`:

```markdown
# 第 1 章 RC 阶跃响应

- 电路：5 V 阶跃源、R = 1 kΩ、C = 100 nF，时间常数 τ = RC = 100 µs。
- 期望：终值 5.0 V；50% 时刻 69.3 µs；10%–90% 上升时间 2.197τ ≈ 219.7 µs。
- 运行：`python scripts/run_spice.py --root assets/spice`
- 数据：`rc.dat` 由本 deck 的 `wrdata` 生成，不是手写或拟合数据。
- 模型边界：理想阶跃源、理想电阻电容、无负载；用于验证工具链与一阶模型，不代表实测。
```

- [ ] **Step 2: 写失败测试**

Create `analog-book/tests/test_spice.py`:

```python
#!/usr/bin/env python3
"""SPICE 骨架：schema、测量解析、容差比较、真实运行与出图。"""
import json
import os
import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import plot_sim  # noqa: E402
import run_spice  # noqa: E402

REQUIRE = os.environ.get("BOOK_REQUIRE_NGSPICE") == "1"
NGSPICE = run_spice.find_ngspice()


class SchemaTests(unittest.TestCase):
    def test_discovers_the_rc_case(self):
        cases = run_spice.discover_cases()
        self.assertEqual(1, len(cases))
        case = cases[0]
        self.assertEqual("rc.cir", case.deck.name)
        self.assertEqual({"vfinal", "vhalf", "trise"}, set(case.spec["metrics"]))

    def test_deck_has_no_external_models(self):
        text = (ROOT / "assets" / "spice" / "ch01" / "rc.cir").read_text(
            encoding="utf-8")
        self.assertIn(".control", text)
        self.assertIn("wrdata", text)
        self.assertNotIn(".include", text.lower())
        self.assertNotIn(".lib", text.lower())
        self.assertNotIn("http", text.lower())
        self.assertIn("PULSE(", text)

    def test_tran_step_is_positive(self):
        text = (ROOT / "assets" / "spice" / "ch01" / "rc.cir").read_text(
            encoding="utf-8")
        match = re.search(r"^\s*\.tran\s+(\S+)", text, re.M)
        self.assertIsNotNone(match, "deck 缺少 .tran 指令")
        number = re.match(r"([-+]?(?:\d+\.?\d*|\.\d+))", match.group(1))
        self.assertIsNotNone(number, "TSTEP 不是数值")
        self.assertGreater(float(number.group(1)), 0,
                           "TSTEP 必须大于 0，ngspice 拒绝 TSTEP=0")

    def test_rejects_negative_tolerance(self):
        spec = json.loads(
            (ROOT / "assets" / "spice" / "ch01" / "assert.json").read_text(
                encoding="utf-8"))
        spec["metrics"]["vfinal"]["tolerance"] = -1
        with self.assertRaises(ValueError):
            run_spice.validate_spec(spec, Path("rc.cir"))

    def test_rejects_orphan_assertion(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "assert.json").write_text("{}", encoding="utf-8")
            with self.assertRaises(ValueError):
                run_spice.discover_cases(root)


class ParsingTests(unittest.TestCase):
    def test_parses_measurements_in_scientific_notation(self):
        text = """
vfinal = 5.000000e+00
vhalf = 7.034000e-05
trise = 2.197000e-04
"""
        values = run_spice.parse_measurements(text)
        self.assertAlmostEqual(5.0, values["vfinal"])
        self.assertAlmostEqual(70.34e-6, values["vhalf"])
        self.assertAlmostEqual(219.7e-6, values["trise"])

    def test_compare_accepts_inside_tolerance(self):
        expected = {"vfinal": {"expected": 5.0, "tolerance": 0.02}}
        self.assertEqual([], run_spice.compare_metrics({"vfinal": 5.01}, expected))

    def test_compare_rejects_outside_tolerance_and_missing(self):
        expected = {"vfinal": {"expected": 5.0, "tolerance": 0.02}}
        self.assertTrue(run_spice.compare_metrics({"vfinal": 5.1}, expected))
        self.assertTrue(run_spice.compare_metrics({}, expected))

    def test_load_data_skips_header_and_requires_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "rc.dat"
            path.write_text("time v(out)\n0 0\n1e-6 0.1\n2e-6 0.2\n",
                            encoding="utf-8")
            rows = run_spice.load_data(path, min_rows=3)
            self.assertEqual(3, len(rows))
            self.assertAlmostEqual(0.2, rows[-1][1])
            with self.assertRaises(ValueError):
                run_spice.load_data(path, min_rows=10)


@unittest.skipIf(NGSPICE is None and not REQUIRE,
                 "未安装 ngspice；设置 BOOK_REQUIRE_NGSPICE=1 可强制")
class SimulationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if NGSPICE is None:
            raise RuntimeError("BOOK_REQUIRE_NGSPICE=1 但找不到 ngspice")
        cls.tmp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.tmp.cleanup)
        cls.out = Path(cls.tmp.name)
        case = run_spice.discover_cases()[0]
        cls.result = run_spice.run_case(case, NGSPICE, output_dir=cls.out)
        cls.case = case

    def test_metrics_match_rc_theory(self):
        self.assertEqual([], self.result["problems"], self.result["log"])
        self.assertAlmostEqual(5.0, self.result["metrics"]["vfinal"], delta=0.02)
        self.assertAlmostEqual(69.3e-6, self.result["metrics"]["vhalf"],
                               delta=5e-6)
        self.assertAlmostEqual(219.7e-6, self.result["metrics"]["trise"],
                               delta=20e-6)

    def test_data_is_written_and_monotonic(self):
        path = self.out / self.case.spec["data"]
        rows = run_spice.load_data(path, min_rows=200)
        self.assertGreaterEqual(len(rows), 200)
        self.assertTrue(all(b[0] > a[0] for a, b in zip(rows, rows[1:])))
        self.assertAlmostEqual(5.0, rows[-1][1], delta=0.03)

    def test_plot_is_generated_from_simulation_data(self):
        path = self.out / self.case.spec["data"]
        output = self.out / "rc-step.svg"
        plot_sim.plot(path, output, "RC 一阶阶跃响应")
        text = output.read_text(encoding="utf-8")
        self.assertIn("<svg", text)
        self.assertIn("ngspice", text)
        self.assertIn("RC 一阶阶跃响应", text)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: 运行测试，确认失败**

Run: `python -B -m unittest discover -s analog-book/tests -p "test_spice.py" -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'run_spice'`.

- [ ] **Step 4: 实现 `scripts/run_spice.py`**

```python
#!/usr/bin/env python3
"""发现并运行 assets/spice 下的 ngspice deck，按 assert.json 校验测量值。"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPICE_DIR = ROOT / "assets" / "spice"
DEFAULT_REPORT = ROOT / "build" / "spice" / "report.json"
MEASURE_RE = re.compile(
    r"^\s*([A-Za-z_]\w*)\s*=\s*"
    r"([-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?)\s*$", re.M)
ANALYSES = {"tran", "ac", "op", "dc"}
REQUIRED = {"deck", "analysis", "data", "min_rows", "metrics"}


@dataclass(frozen=True)
class Case:
    directory: Path
    deck: Path
    spec: dict


def find_ngspice() -> Path | None:
    candidates = []
    override = os.environ.get("NGSPICE")
    if override:
        candidates.append(Path(override))
    for command in ("ngspice", "ngspice.exe"):
        found = shutil.which(command)
        if found:
            candidates.append(Path(found))
    for candidate in candidates:
        if candidate.expanduser().is_file():
            return candidate.expanduser().resolve()
    return None


def validate_spec(spec: dict, deck: Path) -> None:
    if set(spec) != REQUIRED:
        raise ValueError(f"{deck}: assert.json 字段应为 {sorted(REQUIRED)}")
    if spec["deck"] != deck.name:
        raise ValueError(f"{deck}: assert.deck 必须是 {deck.name}")
    if spec["analysis"] not in ANALYSES:
        raise ValueError(f"{deck}: 未知 analysis {spec['analysis']}")
    if not isinstance(spec["min_rows"], int) or spec["min_rows"] < 1:
        raise ValueError(f"{deck}: min_rows 必须为正整数")
    if not isinstance(spec["metrics"], dict) or not spec["metrics"]:
        raise ValueError(f"{deck}: metrics 不能为空")
    for name, metric in spec["metrics"].items():
        if set(metric) != {"expected", "tolerance"}:
            raise ValueError(f"{deck}: metric {name} 字段不合法")
        if not isinstance(metric["expected"], (int, float)):
            raise ValueError(f"{deck}: metric {name} expected 不是数字")
        if not isinstance(metric["tolerance"], (int, float)) \
                or metric["tolerance"] <= 0:
            raise ValueError(f"{deck}: metric {name} tolerance 必须为正")


def discover_cases(root: Path = SPICE_DIR) -> list[Case]:
    root = Path(root)
    if not root.is_dir():
        raise ValueError(f"SPICE 目录不存在: {root}")
    cases = []
    assertions = set(root.glob("**/assert.json"))
    for deck in sorted(root.glob("**/*.cir")):
        spec_path = deck.with_name("assert.json")
        if not spec_path.is_file():
            raise ValueError(f"{deck}: 缺少 assert.json")
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
        validate_spec(spec, deck)
        text = deck.read_text(encoding="utf-8")
        if re.search(r"^\s*\.(include|lib)\b", text, re.I | re.M):
            raise ValueError(f"{deck}: deck 必须自包含，不得 .include/.lib 外部模型")
        if Path(spec["data"]).is_absolute():
            raise ValueError(f"{deck}: data 必须是相对路径")
        cases.append(Case(deck.parent, deck, spec))
        assertions.discard(spec_path)
    if assertions:
        raise ValueError("孤儿 assert.json: " + ", ".join(
            str(path.relative_to(root)) for path in sorted(assertions)))
    if not cases:
        raise ValueError(f"{root} 下没有 .cir deck")
    return cases


def parse_measurements(text: str) -> dict[str, float]:
    return {name: float(value) for name, value in MEASURE_RE.findall(text)}


def compare_metrics(actual: dict[str, float],
                    expected: dict[str, dict]) -> list[str]:
    problems = []
    for name, spec in expected.items():
        if name not in actual:
            problems.append(f"缺少测量值 {name}")
            continue
        error = abs(actual[name] - spec["expected"])
        if error > spec["tolerance"]:
            problems.append(
                f"{name}={actual[name]:.6g}，期望 {spec['expected']:.6g} "
                f"±{spec['tolerance']:.6g}（差 {error:.6g}）")
    return problems


def load_data(path: Path, min_rows: int) -> list[tuple[float, float]]:
    rows = []
    for line in Path(path).read_text(encoding="utf-8", errors="replace").splitlines():
        parts = line.replace(",", " ").split()
        if len(parts) < 2:
            continue
        try:
            time_value, voltage = float(parts[0]), float(parts[1])
        except ValueError:
            continue
        rows.append((time_value, voltage))
    if len(rows) < min_rows:
        raise ValueError(f"{path}: 数据 {len(rows)} 行，少于 {min_rows}")
    if not all(b[0] > a[0] for a, b in zip(rows, rows[1:])):
        raise ValueError(f"{path}: 时间列不是严格递增")
    return rows


def run_case(case: Case, ngspice: Path,
             output_dir: Path | None = None, timeout: int = 120) -> dict:
    directory = (Path(output_dir) if output_dir
                 else ROOT / "build" / "spice" / case.deck.parent.name)
    directory.mkdir(parents=True, exist_ok=True)
    deck_copy = directory / case.deck.name
    shutil.copy2(case.deck, deck_copy)
    started = time.monotonic()
    result = subprocess.run(
        [str(ngspice), "-b", deck_copy.name],
        cwd=directory, capture_output=True, text=True, timeout=timeout)
    log = (result.stdout or "") + (result.stderr or "")
    problems = []
    if result.returncode != 0:
        problems.append(f"ngspice 退出码 {result.returncode}")
    metrics = parse_measurements(log)
    problems += compare_metrics(metrics, case.spec["metrics"])
    data_source = directory / case.spec["data"]
    rows = []
    if not data_source.is_file():
        problems.append(f"缺少数据文件 {data_source.name}")
    else:
        try:
            rows = load_data(data_source, case.spec["min_rows"])
        except ValueError as exc:
            problems.append(str(exc))
    return {
        "case": case.deck.parent.name + "/" + case.deck.name,
        "seconds": round(time.monotonic() - started, 2),
        "returncode": result.returncode,
        "metrics": metrics,
        "rows": len(rows),
        "problems": problems,
        "log": log[-4000:],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=SPICE_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--timeout", type=int, default=120)
    args = parser.parse_args(argv)
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    try:
        cases = discover_cases(args.root)
    except ValueError as exc:
        print(f"spice error: {exc}", file=sys.stderr)
        return 1
    ngspice = find_ngspice()
    require = os.environ.get("BOOK_REQUIRE_NGSPICE") == "1"
    if ngspice is None:
        message = "未找到 ngspice；安装后重试，或设置 BOOK_REQUIRE_NGSPICE=1 强制 CI 失败"
        print("spice skip: " + message)
        return 1 if require else 0
    reports, failed = [], False
    for case in cases:
        result = run_case(case, ngspice, timeout=args.timeout)
        reports.append(result)
        if result["problems"]:
            failed = True
            print(f"spice FAIL {result['case']}")
            for problem in result["problems"]:
                print("  " + problem)
        else:
            print(f"spice OK   {result['case']} ({result['rows']} rows, "
                  f"{result['seconds']}s)")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(
        json.dumps({"ngspice": str(ngspice), "cases": reports},
                   ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 5: 实现 `scripts/plot_sim.py`**

```python
#!/usr/bin/env python3
"""把 ngspice 的 wrdata 输出画成 SVG；图只来自实际仿真数据。"""
from __future__ import annotations

import argparse
from pathlib import Path


def load_data(path: Path) -> list[tuple[float, float]]:
    rows = []
    for line in Path(path).read_text(encoding="utf-8", errors="replace").splitlines():
        parts = line.replace(",", " ").split()
        if len(parts) < 2:
            continue
        try:
            rows.append((float(parts[0]), float(parts[1])))
        except ValueError:
            continue
    if not rows:
        raise ValueError(f"{path}: 没有可绘制的数据")
    return rows


def plot(csv_path: Path, output: Path, title: str) -> Path:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    rows = load_data(csv_path)
    seconds = [row[0] * 1e3 for row in rows]
    voltage = [row[1] for row in rows]
    figure, axes = plt.subplots(figsize=(6.4, 3.6), dpi=150)
    axes.plot(seconds, voltage, color="#b45309", linewidth=1.4)
    axes.axhline(5.0, color="#d9e2ec", linewidth=0.8, linestyle="--")
    axes.set_title(title, fontsize=11, color="#1f2933")
    axes.set_xlabel("时间 / ms", fontsize=9)
    axes.set_ylabel("v(out) / V", fontsize=9)
    axes.grid(True, color="#e5e7eb", linewidth=0.5)
    axes.text(0.99, 0.04, "数据：ngspice 仿真 " + Path(csv_path).name,
              transform=axes.transAxes, ha="right", va="bottom",
              fontsize=7, color="#52606d")
    figure.tight_layout()
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output, format="svg", bbox_inches="tight")
    plt.close(figure)
    return output


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("data", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--title", default="仿真结果")
    args = parser.parse_args(argv)
    try:
        plot(args.data, args.output, args.title)
    except (ValueError, ImportError) as exc:
        print(f"plot error: {exc}")
        return 1
    print(f"plot  {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 6: 运行 SPICE 回归（CI 留到 Task 11B）**

```bash
python -B -m unittest discover -s analog-book/tests -p "test_spice.py" -v
python scripts/run_spice.py --root assets/spice
python scripts/plot_sim.py build/spice/ch01/rc.dat build/spice/rc-step.svg --title "RC 一阶阶跃响应"
```

Expected: PASS (12 tests)，`spice OK ch01/rc.cir (5001 rows ...)`，`build/spice/report.json` 与 `build/spice/rc-step.svg` 生成。`rc.dat` 只写入 `build/spice/ch01/`，不落进 `assets/`。没有 ngspice 的机器只跳过 `SimulationTests`；此时不得声称“仿真已验证”。

不要改 `book.yml`：它被 Pages 通过 `workflow_call` 调用，A4 发布不能因为 16K/SPICE 新测试变红而中断。Task 11B 的 `book-print.yml` 会安装 ngspice 并在 main/manual 上跑同一套测试。

- [ ] **Step 7: 提交**

```bash
git add assets/spice/ch01 scripts/run_spice.py scripts/plot_sim.py \
  analog-book/tests/test_spice.py
git commit -m "feat(spice): add runnable RC deck with assertions and SVG plot"
```

---

### Task 11A: 并行接入 16K（上）——真实种子页、schema-2 manifest、16K CLI 与站点导航

**Files:**
- Create: `docs/p0-11-conventions.md`
- Create: `docs/p0-12-symbols.md`
- Create: `docs/p9-15-glossary.md`
- Create: `analog-book/book/cli.py`
- Create: `analog-book/build_print_book.py`
- Create: `analog-book/manifest-a4.json`（由现有 `manifest.json` 改名冻结）
- Modify: `analog-book/manifest.json`（新 schema 2，16K）
- Modify: `analog-book/build_book.py:19`（`MANIFEST_PATH` 指向 `manifest-a4.json`；A4 覆盖校验排除 16K 专属页）
- Modify: `analog-book/tests/test_build.py`（A4 覆盖断言排除 16K 专属页，仍锁 60 页）
- Modify: `scripts/build_site.py:617`（`APPENDIX` 加入 `p9-15-glossary.md`）
- Modify: `scripts/test_site_build.py`（新页面不进章首舞台）
- Modify: `analog-book/tests/test_book_manifest.py`（真实 manifest 覆盖测试）
- Modify: `CONTRIBUTING.md`、`analog-book/README.md`、`analog-book/READING-FLOW.md`（A4 冻结 manifest 与 16K manifest 的分工）

**Interfaces:**
- Consumes: Task 1–10 的 `manifest`、`content`、`transforms`、`data`、`frontmatter`、`assemble`、`pdf`、`cover`、`sample`、`fonts`、`config`。
- Produces: `book.cli.main(argv=None) -> int` 与薄入口 `build_print_book.py`：
  - 默认：构建站点（除非 `--no-build`）→ 77 页 HTML → 模型 JSON，输出到 `analog-book/dist/print/`；
  - `--check`：只审计已有 HTML；
  - `--pdf`：在 HTML 后生成补白后的 16K PDF；
  - `--cover`：隐含 `--pdf`，再按 PDF 实际页数生成封面与预览；
  - `--sample`：只生成十页 16K 样张；
  - `--browser`：Chromium 可执行文件覆盖。
- 旧 `build_book.py` 仍是 A4 1.0 构建器，只把 `MANIFEST_PATH` 指向冻结的 `manifest-a4.json`；旧 `test_build.py`、`test_pdf.py`、`test_browser_book.py` 全部保留并继续通过。
- 真实 16K manifest：前置 5 个文件页 + 19 章 + 27 个附录源页 + 3 个后置文件页 = 54 个直接页；10 个排除页；77 个逻辑页。
- **本任务与 11B 之间不提交。** 中间提交会让新 16K 测试、真实内容与 CI 矩阵只完成一半。

- [ ] **Step 1: 先写真实 manifest 测试**

在 `analog-book/tests/test_book_manifest.py` 顶部把导入改为：

```python
from book import config  # noqa: E402
from book.manifest import (BookError, book_pages, direct_files,  # noqa: E402
                           excluded_files, load_manifest, validate_manifest)
```

在文件末尾、`if __name__ == "__main__":` 之前追加：

```python
class RepositoryManifestTests(unittest.TestCase):
    def test_real_manifest_is_schema_2_and_covers_repository_docs(self):
        manifest = load_manifest()
        validate_manifest(manifest, docs_dir=config.DOCS)
        self.assertEqual(77, len(book_pages(manifest)))
        direct = direct_files(manifest)
        for name in ("p0-11-conventions.md", "p0-12-symbols.md",
                     "p9-15-glossary.md"):
            self.assertIn(name, direct)
        self.assertEqual(10, len(excluded_files(manifest)))
```

- [ ] **Step 2: 运行测试，确认失败**

Run: `python -B -m unittest discover -s analog-book/tests -p "test_book_manifest.py" -v`
Expected: FAIL，旧 manifest 是 schema 1（`schema` 校验失败）或找不到三张新页。

- [ ] **Step 3: 创建三张真实种子页**

Create `docs/p0-11-conventions.md`:

```markdown
<a id="conventions"></a>
## 🧭 排版、术语与引用约定

这一页把全书共用的读法、单位、证据与引用规则放在一起。第一次遇到不认识的记号，先回这里；做设计复核或写实验记录时，也按同一套口径记录——单位、有效数字和“典型值”一旦走样，后面的计算与结论都会跟着错。

### 三层读法：主线、进阶、速查

| 层次 | 版式 | 怎么读 | 什么时候用 |
|---|---|---|---|
| 主线 | 正文、算例、章末练习 | 从现象到模型，按章节顺序读 | 第一次学、补齐因果链 |
| 进阶 | 「进阶」「坑」「实测」「仿真」提示框 | 第一遍可跳过，做设计时回来 | 复查边界、准备打样 |
| 速查 | 加粗结论、表格、附录 B/G | 只查不算，先定位再回正文 | 已有基础、现场排故 |

主线讲“为什么”，进阶框讲“什么时候不成立”，速查页讲“现在该查哪一行”。同一结论在三层里出现时，以正文的限定条件为准；速查表不重复抄条件，只给出口径。

### 公式、单位与有效数字

- 物理量符号用斜体（$V$、$I$、$R$），单位符号用正体（V、A、Ω），数值与单位之间留一个空格：$5.0\ \mathrm{V}$。
- 默认使用 SI 词头：$10^3$ 写 k，$10^{-3}$ 写 m，$10^{-6}$ 写 µ；避免混用“兆/千”和字母 M/k。
- 工程算例一般保留三位有效数字；中间步骤至少多留一位，最后再按测量不确定度或元件容差取舍。结果写“≈3.33 V”时，表示按给定条件算得，不表示实测一定等于 3.33 V。
- 百分比、dB 与 ppm 都写清参考量：增益 −3 dB 是相对值，0 dBm 才以 1 mW 为参考；ppm 是百万分之一，不是“精度单位”。
- 温度写成“25 °C”“−40~85 °C”；涉及温漂时同时给参考温度，否则 ppm/°C 没有意义。
- “典型值”只用于设计起点，不能当最坏情况。datasheet 的 min/max 才是做批量与极限验证的依据；书里没有 min/max 的地方，会明确写“典型值”或“量级”。

### 电压、电流与方向

| 约定 | 写法 | 说明 |
|---|---|---|
| 节点电压 | $V_A$、$V_{\mathrm{out}}$ | 默认以地为 0 V 参考点；先标参考点，再谈电位 |
| 电压差 | $V_{BE}=V_B-V_E$ | 双下标表示“前者减后者”，不是两个绝对值相加 |
| 电流方向 | 箭头 + 正号 | 箭头是参考方向；算出来为负，表示真实方向与箭头相反 |
| 关联参考方向 | 电流从电压“+”端流入 | 此时 $P=VI$ 为吸收功率；否则要加负号 |
| 交流量 | 小写 $v(t)$、$i(t)$ | 大写 $V$、$I$ 表示直流或有效值，具体看上下文 |
| 有效值 | $V_{\mathrm{rms}}$ | 正弦波 $V_{\mathrm{rms}}=V_p/\sqrt{2}$；峰峰值是 $2V_p$，三者别混 |

功率正负号只说明“吸收还是发出”，不代表元件好坏。算不准方向时，先按关联参考方向列式，最后用符号解释结果。

### 术语与缩写

术语第一次出现时给中文、英文与缩写，例如“跨导（transconductance，$g_m$）”；后文只用缩写。常见缩写按首次定义为准：

| 缩写 | 全称 | 中文 |
|---|---|---|
| BJT | bipolar junction transistor | 双极型晶体管 |
| MOSFET | metal-oxide-semiconductor field-effect transistor | 金属-氧化物-半导体场效应管 |
| op-amp | operational amplifier | 运算放大器 |
| GBW | gain-bandwidth product | 增益带宽积 |
| SR | slew rate | 压摆率 |
| CMRR | common-mode rejection ratio | 共模抑制比 |
| PSRR | power-supply rejection ratio | 电源抑制比 |
| ESR | equivalent series resistance | 等效串联电阻 |
| ESL | equivalent series inductance | 等效串联电感 |
| LDO | low-dropout regulator | 低压差线性稳压器 |
| PWM | pulse-width modulation | 脉宽调制 |
| ADC / DAC | analog-to-digital / digital-to-analog converter | 模数 / 数模转换器 |
| SNR / THD | signal-to-noise ratio / total harmonic distortion | 信噪比 / 总谐波失真 |
| ENOB | effective number of bits | 有效位数 |

同一符号在不同语境有不同含义时，正文会加限定词：BJT 的 $\beta$ 是电流增益，反馈网络里的 $\beta$ 是反馈系数；$D$ 在二极管语境是器件，在开关电源里是占空比。读公式前先看限定词。

### 证据等级：书上的话从哪里来

| 等级 | 来源 | 书里怎么标 | 能证明什么 |
|---|---|---|---|
| A | 教材、手册、厂商数据手册、应用笔记 | 给出书名/版次/章节，或厂商与文档编号 | 定义、公式、极限参数、典型应用 |
| B | 可复现的仿真 | 给出 `assets/spice/` 下的 deck 与分析方法 | 在模型适用范围内，电路“应该”怎样 |
| C | 本仓库实测 | 只限 RC、LM358、MOSFET 三套实验，给 CSV、仪器条件与日期 | 在样机与测量条件下，实际怎样 |
| D | 经验判断、工程惯例 | 用“经验上”“通常”“量级”标明 | 给设计起点，不能当保证 |

仿真不是实测：它证明的是“按这个模型算出来是什么”，不证明手里的元件一定这样。实测也不是普遍真理：三套实验覆盖不了所有批次的离散性、温度与布局。书里不会把仿真曲线写成“实测”，也不会编造“某实验室数据”；没有数据来源的图不进书。

### 引用、链接与勘误

- 印刷版用“第 N 章”“§N.M”“图 N-M”“表 N-M”定位；在线版用可点击的章节链接。两者指向同一段正文。
- 外部资料（数据手册、应用笔记、论文、视频）在章末“延伸阅读”或页下注给出；正文只引必要短句，不复制受版权保护的整图、整表与字幕。
- 网址给出标题、机构与访问日期；链接失效时以标题和编号仍可检索。厂商文档优先给文档编号，不只给一个短链接。
- 发现错误请到仓库的 Issues 页面提交，写清版本、页码/章节、原文与你的依据。勘误会进入下一印次与在线版的更新日志；不要只在聊天群里说一句“这里不对”。

### 图表、代码与实验记录

- 图、表按章编号（图 6-3、表 13-2），图注在图下、表注在表上；引用时写编号，不写“上图”“下表”。
- 图必须能脱离正文读懂：坐标轴有量和单位，曲线有图例，数据图注明来源（仿真 deck 或实测 CSV）。
- 代码块标语言；ngspice 网表第一行写用途，关键节点用注释说明，分析类型与 `.meas` 断言放在同一 deck 里，保证别人能重跑。
- 实验记录至少写：日期、温度、仪器型号与量程、探头/夹具、元件标称与实测、原始数据文件名。只写“测出来差不多”不算记录。
- 计算结果与仿真、实测对不上时，先查单位、参考点、负载与探头，再怀疑模型；把差异写进“坑”框，而不是把数据改成好看的样子。

### 安全边界

本书是学习与设计参考，不替代具体器件的数据手册、安规标准与专业评审。涉及市电、高压、储能电容、功率器件与锂电池时，断电、放电、隔离、限流、防火一个都不能省；第一次上电用限流电源，别直接怼市电。你按书搭的每一块板，安全责任都在搭建者与使用者。
```

Create `docs/p0-12-symbols.md`:

```markdown
<a id="symbols"></a>
## 🔣 符号与单位表

公式里最贵的错误是符号歧义：同一个 $\beta$ 在 BJT 是电流增益、在反馈网络是反馈系数；同一个 $D$ 在二极管是器件名、在开关电源是占空比。本表按语境列出全书主要符号、含义、单位与首次系统讨论的章。遇到表里没有的符号，回该章第一次定义处；不同章重复使用同一符号时，以当页限定词为准。

**读法**：单位栏的“—”表示无量纲；`V/√Hz` 这类组合单位按噪声密度理解；温度单位统一用 °C，热阻用 °C/W。首次出现栏给章号，不代替小节定位。

### 基础电学与电路

| 符号 | 含义（语境） | 单位 | 首次出现 |
|---|---|---|---|
| $V$ | 电压、电位差 | V | 0 |
| $v(t)$ | 瞬时电压 | V | 0 |
| $I$ | 电流（直流或有效值） | A | 0 |
| $i(t)$ | 瞬时电流 | A | 0 |
| $R$ | 电阻 | Ω | 0 |
| $G$ | 电导，$G=1/R$ | S | 1 |
| $P$ | 功率 | W | 0 |
| $q$ | 电荷 | C | 2 |
| $E$ | 能量 | J | 1 |
| $Z$ | 阻抗（复数） | Ω | 1 |
| $Y$ | 导纳（复数） | S | 1 |
| $f$ | 频率 | Hz | 1 |
| $T$ | 周期 | s | 1 |
| $\omega$ | 角频率，$\omega=2\pi f$ | rad/s | 1 |
| $\tau$ | 时间常数 | s | 1 |
| $\phi$ | 相位 | rad | 11 |
| $\mathrm{dB}$ | 分贝，$20\log_{10}(A_2/A_1)$ | dB | 11 |

### 无源元件与寄生

| 符号 | 含义（语境） | 单位 | 首次出现 |
|---|---|---|---|
| $C$ | 电容 | F | 1 |
| $L$ | 电感 | H | 1 |
| $X_C$ | 容抗，$1/(2\pi fC)$ | Ω | 1 |
| $X_L$ | 感抗，$2\pi fL$ | Ω | 1 |
| $\mathrm{ESR}$ | 等效串联电阻 | Ω | 1 |
| $\mathrm{ESL}$ | 等效串联电感 | H | 1 |
| $Q$ | 品质因数（谐振/元件） | — | 1 |
| $\tan\delta$ | 介质损耗角正切 | — | 1 |
| $\mathrm{SRF}$ | 自谐振频率 | Hz | 1 |
| $\mathrm{TC}$ | 温度系数 | 1/°C | 9 |

### 二极管、BJT 与 MOSFET

| 符号 | 含义（语境） | 单位 | 首次出现 |
|---|---|---|---|
| $I_S$ | 二极管反向饱和电流 | A | 2 |
| $V_T$ | 热电压，$kT/q$（约 26 mV @ 25 °C） | V | 2 |
| $n$ | 二极管理想因子 | — | 2 |
| $V_F$ | 正向压降 | V | 2 |
| $V_{BR}$ | 反向击穿电压 | V | 2 |
| $r_d$ | 二极管动态电阻 | Ω | 2 |
| $C_j$ | 结电容 | F | 2 |
| $t_{rr}$ | 反向恢复时间 | s | 2 |
| $\beta$ | BJT 共射电流增益（反馈语境另见下表） | — | 3 |
| $h_{FE}$ | BJT 直流电流增益（datasheet 口径） | — | 3 |
| $\alpha$ | BJT 共基电流增益 | — | 3 |
| $g_m$ | 跨导，$\Delta I/\Delta V$ | S | 3 |
| $r_\pi$ | BJT 输入电阻 | Ω | 3 |
| $r_o$ | 小信号输出电阻 | Ω | 3 |
| $V_A$ | 厄利电压 | V | 3 |
| $V_{BE}$ | 基极—发射极电压 | V | 3 |
| $V_{CE(sat)}$ | 饱和压降 | V | 3 |
| $I_C$ | 集电极电流 | A | 3 |
| $I_E$ | 发射极电流 | A | 3 |
| $V_{TH}$ | MOSFET 阈值电压 | V | 4 |
| $k_n$ | MOSFET 跨导参数 | A/V² | 4 |
| $\lambda$ | 沟道长度调制系数 | 1/V | 4 |
| $R_{DS(on)}$ | 导通电阻（热态要乘温度系数） | Ω | 4 |
| $Q_g$ | 栅极总电荷 | C | 4 |
| $C_{iss}$ | 输入电容 | F | 4 |
| $C_{oss}$ | 输出电容 | F | 4 |
| $C_{rss}$ | 反向传输电容 | F | 4 |
| $V_{DS}$ | 漏源电压 | V | 4 |
| $V_{GS}$ | 栅源电压 | V | 4 |
| $I_D$ | 漏极电流 | A | 4 |

### 运放、反馈与信号链

| 符号 | 含义（语境） | 单位 | 首次出现 |
|---|---|---|---|
| $A_{ol}$ | 运放开环电压增益 | — | 6 |
| $A_{cl}$ | 闭环电压增益 | — | 6 |
| $\mathrm{GBW}$ | 增益带宽积 | Hz | 6 |
| $\mathrm{SR}$ | 压摆率 | V/µs | 6 |
| $V_{OS}$ | 输入失调电压 | V | 6 |
| $I_B$ | 运放输入偏置电流（BJT 基极电流另见上表） | A | 6 |
| $I_{OS}$ | 输入失调电流 | A | 6 |
| $\mathrm{CMRR}$ | 共模抑制比 | dB | 6 |
| $\mathrm{PSRR}$ | 电源抑制比 | dB | 6 |
| $e_n$ | 输入电压噪声密度 | V/√Hz | 11 |
| $i_n$ | 输入电流噪声密度 | A/√Hz | 11 |
| $\mathrm{THD}$ | 总谐波失真 | dB 或 % | 11 |
| $\mathrm{SNR}$ | 信噪比 | dB | 13 |
| $\mathrm{ENOB}$ | 有效位数 | bit | 13 |
| $\mathrm{PM}$ | 相位裕度 | ° | 11 |
| $\mathrm{GM}$ | 增益裕度 | dB | 11 |
| $\beta$ | 反馈系数（反馈网络） | — | 11 |
| $R_{neg}$ | 负阻（振荡器起振判据） | Ω | 13 |
| $R_{in}$ | 输入电阻 | Ω | 6 |
| $R_{out}$ | 输出电阻 | Ω | 6 |
| $t_r$ | 上升时间（10%~90%） | s | 11 |
| $t_{settle}$ | 建立时间（到给定误差带） | s | 6 |

### 电源、开关与热

| 符号 | 含义（语境） | 单位 | 首次出现 |
|---|---|---|---|
| $D$ | 占空比，$t_{on}/T$（二极管器件另见上表） | — | 13 |
| $f_{sw}$ | 开关频率 | Hz | 13 |
| $\Delta I_L$ | 电感电流纹波（峰峰值） | A | 13 |
| $\Delta V_o$ | 输出电压纹波（峰峰值） | V | 13 |
| $\eta$ | 效率，$P_{out}/P_{in}$ | — | 13 |
| $I_Q$ | 静态电流 | A | 9 |
| $V_{drop}$ | 稳压器压差 | V | 9 |
| $\theta_{JA}$ | 结到环境热阻 | °C/W | 14 |
| $T_J$ | 结温 | °C | 14 |
| $T_A$ | 环境温度 | °C | 14 |
| $P_D$ | 器件耗散功率 | W | 14 |
| $\mathrm{SOA}$ | 安全工作区 | — | 14 |

### 测量、噪声与统计

| 符号 | 含义（语境） | 单位 | 首次出现 |
|---|---|---|---|
| $\mathrm{LSB}$ | 最低有效位对应的量 | V 或 A | 13 |
| $\mathrm{FS}$ | 满量程 | V 或 A | 13 |
| $\mathrm{INL}$ | 积分非线性 | LSB | 13 |
| $\mathrm{DNL}$ | 微分非线性 | LSB | 13 |
| $\mathrm{ppm}$ | 百万分之一 | — | 9 |
| $\sigma$ | 标准差 | 与被测量同 | 11 |
| $\mu$ | 平均值 | 与被测量同 | 11 |
| $k$ | 包含因子（不确定度） | — | 11 |
| $\mathrm{NF}$ | 噪声系数 | dB | 11 |

### 最容易混淆的四组

| 易混 | 区分口诀 |
|---|---|
| $V$ 与 $v(t)$ | 大写多半是直流/有效值，小写是瞬时量；看正文限定词 |
| $\beta$ 的两副面孔 | 三极管里是 $I_C/I_B$；反馈网络里是“反馈回去多少” |
| $D$ 的两副面孔 | 二极管是器件；开关电源里是占空比 |
| $Q$ 的两副面孔 | 谐振/元件品质因数是无量纲；电荷用 $q$ 或 $Q$ 时看单位 C |

> 读到表里没有的符号，先查本章第一次定义；仍不确定时，以“单位 + 语境”反推，不要凭字母猜。
```

Create `docs/p9-15-glossary.md`:

```markdown
<a id="glossary"></a>
## 📚 术语表

术语表按拼音排序，每条给英文、一句话定义与首次系统讨论的章。它和 [8.10 模拟黑话速查表](p8-10-s8-10.md#sec810) 分工不同：这里回答“这个词是什么”，黑话表回答“这个词在工程现场怎么用”。同一条目在两处出现时，定义以本表为准，例句与故障语境看黑话表。

**用法**：读正文卡住时先查这里，再回章号；写报告时用“中文（English）”首次定义，之后统一用中文或缩写，不要中英混用同一句。

### B

| 术语 | English | 定义 | 章 |
|---|---|---|---|
| 旁路 | bypass | 给交流或瞬态电流提供低阻抗通路，常指电源引脚到地的电容。 | 1 |
| 饱和 | saturation | BJT 进入集电结正偏、$V_{CE}$ 很小的开关状态；MOSFET 则指沟道夹断后的恒流区，语境不同。 | 3 |
| 比较器 | comparator | 比较两个电压并输出高低电平的开环或正反馈器件，不做线性放大。 | 7 |
| 闭环增益 | closed-loop gain | 接入负反馈后“输出/输入”的比值，由反馈网络主导而不是开环增益。 | 6 |
| 波特图 | Bode plot | 增益与相位随频率变化的对数坐标图，用来读带宽、极点和稳定性。 | 11 |

### C

| 术语 | English | 定义 | 章 |
|---|---|---|---|
| 采样保持 | sample and hold | 在开关闭合时跟踪输入、断开时把电压存储在电容上的电路。 | 8 |
| 差模 | differential mode | 两个输入端大小相等、极性相反的信号分量。 | 6 |
| 差分对 | differential pair | 两只特性匹配的器件尾端相连、分别接两个输入的对称结构，是运放输入级的核心。 | 6 |
| 衬底 | substrate | 集成电路中支撑器件并常接固定电位的半导体本体。 | 4 |
| 迟滞 | hysteresis | 让比较器在上下两个不同门限之间翻转，避免噪声在单一门限附近反复触发。 | 7 |
| 充电泵 | charge pump | 用电容和开关把电荷搬运到更高或更低电位，得到高于电源或负的电压。 | 13 |

### D

| 术语 | English | 定义 | 章 |
|---|---|---|---|
| 戴维南等效 | Thévenin equivalent | 把线性含源二端网络化成“一个电压源串一个电阻”，用于快速估算负载效应。 | 1 |
| 单点接地 | single-point ground | 让多个回路只在一个物理点汇合，避免共享地线阻抗把噪声耦合到别处。 | 15 |
| 导通电阻 | on-resistance | 开关器件完全导通时漏源或集射之间的等效电阻，决定导通损耗。 | 4 |
| 地弹 | ground bounce | 大电流快速变化在接地电感上产生压降，使局部“地”电位瞬间抬升。 | 15 |
| 电流镜 | current mirror | 用一只器件的 $V_{BE}$ 或 $V_{GS}$ 复制另一只器件电流的偏置结构。 | 3 |
| 电压基准 | voltage reference | 在温度、负载与电源变化下仍保持稳定电压的电路，是 ADC 与稳压的标尺。 | 9 |
| 电源抑制比 | power-supply rejection ratio | 电源变化传到输出被衰减多少，通常用 dB 表示。 | 6 |
| 叠加定理 | superposition | 线性电路中多个独立源共同作用时，可分别求响应再相加。 | 1 |
| 断续导通模式 | discontinuous conduction mode | 开关电源电感电流在每个周期内降到零并停留一段时间的运行模式。 | 13 |

### E

| 术语 | English | 定义 | 章 |
|---|---|---|---|
| 厄利效应 | Early effect | BJT 集电结耗尽层随 $V_{CE}$ 变化，使输出特性上翘、输出电阻有限。 | 3 |

### F

| 术语 | English | 定义 | 章 |
|---|---|---|---|
| 反馈系数 | feedback factor | 输出被反馈网络送回输入端的比例，常记作 $\beta$，与三极管电流增益同名不同义。 | 11 |
| 反向恢复 | reverse recovery | 二极管从导通转为截止时，存储电荷被抽走所需的时间与电荷量。 | 2 |
| 分压器 | voltage divider | 两只阻抗串联，从中间取电压；带载后输出会因负载并联而下降。 | 0 |
| 伏秒平衡 | volt-second balance | 开关电源稳态时，电感一周期内“充入的伏秒”等于“放出的伏秒”。 | 13 |
| 负反馈 | negative feedback | 把输出的一部分反相送回输入，用牺牲增益换取稳定、带宽与线性度。 | 6 |
| 负载调整率 | load regulation | 负载电流变化时输出电压的变化量，通常用 % 或 mV 表示。 | 9 |

### G

| 术语 | English | 定义 | 章 |
|---|---|---|---|
| 共模 | common mode | 两个输入端大小与极性都相同的信号分量。 | 6 |
| 共模抑制比 | common-mode rejection ratio | 差模增益与共模增益之比，衡量运放或差分电路抗共模干扰的能力。 | 6 |
| 共射 | common emitter | BJT 发射极交流接地、输入接基极、输出接集电极的放大组态。 | 3 |
| 共源 | common source | MOSFET 源极交流接地、输入接栅极、输出接漏极的放大组态。 | 4 |
| 过冲 | overshoot | 阶跃响应第一次超过最终值的部分，常由相位裕度不足或寄生电感引起。 | 11 |

### H

| 术语 | English | 定义 | 章 |
|---|---|---|---|
| 耗尽层 | depletion region | PN 结或 MOS 结构中载流子被电场排空、只剩固定电荷的区域。 | 2 |
| 环路增益 | loop gain | 信号绕反馈环一周的增益，决定闭环精度与稳定性。 | 11 |
| 混叠 | aliasing | 采样率不足时高频信号伪装成低频信号，采样后无法用软件还原。 | 13 |

### J

| 术语 | English | 定义 | 章 |
|---|---|---|---|
| 基尔霍夫定律 | Kirchhoff's laws | 节点电流代数和为零、回路电压代数和为零，是电路方程的两条根。 | 0 |
| 积分器 | integrator | 输出与输入对时间的积分成正比的电路，常用运放加电容实现。 | 6 |
| 极点 | pole | 使传递函数分母为零的复频率，表现为增益下降与相位滞后。 | 11 |
| 降额 | derating | 让器件在低于额定电压、电流或温度下工作，以换取寿命与可靠性。 | 14 |
| 结温 | junction temperature | 半导体芯片内部 PN 结的实际温度，决定寿命与参数漂移。 | 14 |
| 静态电流 | quiescent current | 电路无负载或待机时自身消耗的电流，是电池寿命的直接账本。 | 9 |
| 截止频率 | cutoff frequency | 增益比通带下降 3 dB 的频率，一阶 RC 的截止频率为 $1/(2\pi RC)$。 | 1 |

### K

| 术语 | English | 定义 | 章 |
|---|---|---|---|
| 开漏 | open drain | MOSFET 漏极不内部上拉、只向下拉低的输出结构，需要外部上拉。 | 5 |
| 开环增益 | open-loop gain | 不加反馈时运放或放大器的差模增益，通常很大且随频率下降。 | 6 |
| 跨导 | transconductance | 输入电压变化引起输出电流变化的比值，单位 S。 | 3 |

### L

| 术语 | English | 定义 | 章 |
|---|---|---|---|
| 零点 | zero | 使传递函数分子为零的复频率，表现为增益上升与相位超前。 | 11 |
| 滤波器 | filter | 让某些频率通过、抑制另一些频率的网络，分低通、高通、带通与带阻。 | 1 |

### M

| 术语 | English | 定义 | 章 |
|---|---|---|---|
| 脉宽调制 | pulse-width modulation | 保持周期不变、调节导通脉宽来控制平均功率或输出电压。 | 13 |
| 米勒平台 | Miller plateau | MOSFET 开关过程中栅极电压被 $C_{gd}$ 反馈“钉住”的平台段。 | 4 |
| 米勒效应 | Miller effect | 跨接在输入与输出之间的电容被增益放大，等效到输入端变大。 | 4 |

### N

| 术语 | English | 定义 | 章 |
|---|---|---|---|
| 奈奎斯特 | Nyquist | 采样率必须大于信号最高频率的两倍，否则发生混叠。 | 13 |
| 内阻 | internal resistance | 电源或信号源自身串联的等效电阻，决定带载后的压降与最大输出。 | 0 |

### P

| 术语 | English | 定义 | 章 |
|---|---|---|---|
| 漂移 | drift | 温度、时间或老化引起的参数缓慢变化，与随机噪声不同。 | 9 |
| 品质因数 | quality factor | 谐振时储能与每周期耗能之比，衡量电感、电容或谐振回路的选择性。 | 1 |

### Q

| 术语 | English | 定义 | 章 |
|---|---|---|---|
| 齐纳击穿 | Zener breakdown | 高掺杂 PN 结在较低反压下发生的可逆击穿，用于稳压。 | 2 |
| 钳位 | clamp | 把电压限制在给定范围内，常用二极管、TVS 或有源电路实现。 | 2 |
| 去耦 | decoupling | 在电源引脚附近放电容，给器件瞬间电流提供本地回路并降低电源阻抗。 | 1 |

### R

| 术语 | English | 定义 | 章 |
|---|---|---|---|
| 热阻 | thermal resistance | 单位功率引起的温升，单位 °C/W，串联起来算“结—壳—散热器—环境”。 | 14 |
| 软启动 | soft start | 上电时让输出电压或占空比缓慢上升，限制浪涌电流与过冲。 | 13 |

### S

| 术语 | English | 定义 | 章 |
|---|---|---|---|
| 上升时间 | rise time | 波形从 10% 到 90% 稳态值所需的时间，与带宽近似成反比。 | 11 |
| 失调电压 | offset voltage | 输入为零时输出不为零所对应的等效输入误差电压。 | 6 |
| 时间常数 | time constant | 一阶系统达到最终值 63.2% 所需的时间，RC 电路为 $RC$。 | 1 |
| 死区时间 | dead time | 半桥或全桥换向时上下管都关闭的空窗，防止直通短路。 | 13 |
| 速度饱和 | velocity saturation | 高电场下载流子漂移速度不再随电场线性增加，短沟道器件更明显。 | 4 |

### T

| 术语 | English | 定义 | 章 |
|---|---|---|---|
| 体二极管 | body diode | MOSFET 结构自带的源—漏寄生二极管，反向续流时导通。 | 4 |
| 同步整流 | synchronous rectification | 用 MOSFET 代替整流二极管，降低低压大电流时的导通损耗。 | 13 |
| 推挽 | push-pull | 上下两只器件交替拉高、拉低输出的结构，静态时通常只有一只导通。 | 5 |

### W

| 术语 | English | 定义 | 章 |
|---|---|---|---|
| 温度系数 | temperature coefficient | 参数随温度变化的相对速率，常用 ppm/°C 或 %/°C。 | 9 |
| 纹波 | ripple | 直流输出上叠加的周期性波动，开关电源里由电感电流与电容充放电形成。 | 13 |

### X

| 术语 | English | 定义 | 章 |
|---|---|---|---|
| 线性调整率 | line regulation | 输入电压变化时输出电压的变化量，衡量稳压器抗输入波动能力。 | 9 |
| 相位裕度 | phase margin | 环路增益降到 0 dB 时，相位距 −180° 还有多少度，工程上常留 45°~60°。 | 11 |
| 谐振 | resonance | 电感与电容的容抗、感抗相互抵消，回路呈纯阻或电压/电流出现峰值的状态。 | 1 |
| 虚短 | virtual short | 深负反馈下运放两输入端电压近似相等，不是物理短路。 | 6 |
| 虚断 | virtual open | 深负反馈下运放输入端电流近似为零，不是物理断路。 | 6 |
| 续流二极管 | freewheeling diode | 给电感电流提供关断后的连续通路，防止电压尖峰。 | 2 |
| 雪崩击穿 | avalanche breakdown | 强电场使载流子碰撞电离、电流雪崩式增加的击穿机制。 | 2 |

### Y

| 术语 | English | 定义 | 章 |
|---|---|---|---|
| 压摆率 | slew rate | 运放输出每微秒最多能变化的伏数，大信号时限制全功率带宽。 | 6 |
| 亚阈值 | subthreshold | 栅源电压低于阈值、沟道未完全形成但仍有微小电流的区段。 | 4 |
| 仪表放大器 | instrumentation amplifier | 高输入阻抗、高共模抑制、增益由一只电阻设定的差分放大器。 | 12 |
| 有源负载 | active load | 用晶体管电流源代替电阻做负载，提高增益与电压余量。 | 3 |
| 源极跟随 | source follower | MOSFET 漏极接电源、输入接栅极、输出取自源极的电压跟随组态。 | 4 |
| 运放 | operational amplifier | 高开环增益的差分放大器，配合负反馈实现放大、滤波、积分等功能。 | 6 |
| 阈值电压 | threshold voltage | MOSFET 开始形成导电沟道所需的栅源电压，离散范围必须按 datasheet 看。 | 4 |

### Z

| 术语 | English | 定义 | 章 |
|---|---|---|---|
| 噪声 | noise | 与信号无关的随机波动，热噪声、散粒噪声与闪烁噪声是模拟电路的三类常客。 | 11 |
| 增益带宽积 | gain-bandwidth product | 运放开环增益与频率的乘积，闭环增益越高可用带宽越窄。 | 6 |
| 占空比 | duty cycle | 一个周期内导通时间所占比例，开关电源用它控制能量传输。 | 13 |
| 正反馈 | positive feedback | 反馈信号与输入同相相加，用于迟滞、振荡与锁存，不用于线性放大。 | 7 |
| 直流偏置 | DC bias | 给器件设定的静态工作点，决定它在线性区、饱和区还是截止区。 | 3 |
| 主极点 | dominant pole | 频率最低、决定系统带宽与相位滞后的那个极点。 | 11 |
| 自举 | bootstrap | 用电容把高侧开关的驱动参考点抬到电源之上，使高侧管充分导通。 | 13 |
| 自热 | self-heating | 器件自身功耗使结温升高，进而改变参数、形成热反馈。 | 14 |
```

- [ ] **Step 4: 冻结 A4 manifest，并写入 schema-2 16K manifest**

先把现有 schema-1 manifest 改名冻结，供 A4 1.0 管线继续使用：

```bash
git mv analog-book/manifest.json analog-book/manifest-a4.json
```

Modify `analog-book/build_book.py:19`:

```python
MANIFEST_PATH = BOOK_DIR / "manifest-a4.json"
```

旧 `build_book.load_manifest()` 与 `test_build.py` 因此继续读 schema 1。但新增的三张 docs 页会让 A4 的「manifest 必须覆盖 docs 每一页」校验红掉——A4 1.0 必须保持 60 页，方案是让 A4 校验显式排除这三张 16K 专属页：

在 `analog-book/build_book.py` 的 `DOCS = ...` 后加：

```python
PRINT_ONLY_STEMS = {"p0-11-conventions", "p0-12-symbols", "p9-15-glossary"}
```

并把 `validate_manifest()` 里的：

```python
    actual = {p.stem for p in DOCS.glob("*.md")} - {"index"}
```

改为：

```python
    actual = ({p.stem for p in DOCS.glob("*.md")} - {"index"}
              - PRINT_ONLY_STEMS)
```

`test_build.py` 的 `test_covers_every_content_page_exactly_once` 同步排除这三页（仍断言 60 页与完整覆盖）：

```python
        docs = ({p.stem for p in (ROOT / "docs").glob("*.md")}
                - {"index"} - build_book.PRINT_ONLY_STEMS)
```

这三页由 16K 的 schema-2 校验负责；A4 对其他任何新增页仍然会红灯。

然后 Replace `analog-book/manifest.json` entirely（新文件，schema 2，只给 16K 管线）：

```json
{
  "schema": 2,
  "title": "通往模拟电路之路",
  "subtitle": "从欧姆定律到芯片内部结构",
  "edition": "第一版",
  "version": "2.0.0-draft.1",
  "source_version": "3.61",
  "date": "2026-10-25",
  "language": "zh-CN",
  "author": "zhuguang-ZFG 与贡献者",
  "site_url": "https://aliyun-hutuji.donglicao.com/analog-circuit-roadmap/",
  "repository": "https://github.com/zhuguang-ZFG/analog-circuit-roadmap",
  "license": "CC BY-SA 4.0",
  "trim": {"width_mm": 185, "height_mm": 260},
  "front_matter": [
    {"kind": "half_title"},
    {"kind": "title_page"},
    {"kind": "copyright"},
    {"file": "p0-01-preface.md", "title": "前言"},
    {"file": "p0-02-how-to-use.md", "title": "怎样读这本书"},
    {"file": "p0-03-timeline.md", "title": "模拟电路简史"},
    {"file": "p0-11-conventions.md", "title": "排版、术语与引用约定"},
    {"file": "p0-12-symbols.md", "title": "符号与单位表"},
    {"kind": "toc"},
    {"kind": "list_of_figures"},
    {"kind": "list_of_tables"}
  ],
  "parts": [
    {"id": "I", "title": "基础", "subtitle": "先建立电路直觉",
     "intro": "这一篇从电压、电流与无源元件开始，先把电路为什么会这样工作讲清楚。"
              "你会反复使用欧姆定律、基尔霍夫定律与戴维南等效，把复杂网络化简成可计算的小模型。"
              "学完后，你应能独立分析由电源、电阻、电容、电感与负载组成的电路，并解释每个元件为什么在那里。"
              "遇到不确定的符号或单位，先回到附录 G 与前置约定页核对，再继续推导。",
     "opener_art": "part-i.svg",
     "units": [{"title": "电路直觉与无源世界",
                "chapters": ["p1-01-ch0.md", "p1-02-ch1.md"]}]},
    {"id": "II", "title": "器件", "subtitle": "从 PN 结到 555",
     "intro": "器件篇沿着 PN 结、二极管、BJT、MOSFET 一路走到运放、比较器、模拟开关、基准与 555。"
              "重点不是背参数，而是理解器件在什么条件下近似成什么模型，以及模型失效时会发生什么。"
              "每类器件都会配仿真与实测边界，帮助你把手算、仿真与真实波形对上。"
              "读完后，你应能根据数据手册和电路目标选出合适的器件，并预判它的非理想行为。",
     "opener_art": "part-ii.svg",
     "units": [
       {"title": "分立器件", "chapters": ["p1-03-ch2.md", "p1-04-ch3.md",
                                          "p1-05-ch4.md", "p1-06-ch5.md"]},
       {"title": "模拟集成器件", "chapters": ["p1-07-ch6.md", "p1-08-ch7.md",
                                              "p1-09-ch8.md", "p1-10-ch9.md",
                                              "p1-11-ch10.md"]}
     ]},
    {"id": "III", "title": "拓扑", "subtitle": "把器件接成可复用的电路",
     "intro": "拓扑篇把已经认识的器件接成可复用的电路块：放大、滤波、稳压、振荡与信号产生。"
              "你会看到同一组器件如何因偏置、反馈与负载不同而呈现完全不同的传递函数。"
              "分析时先抓大信号工作点，再看小信号等效，最后用仿真检查边角。"
              "目标是让你面对一张陌生原理图时，能先说出它属于哪类拓扑，再决定从哪里下手。",
     "opener_art": "part-iii.svg",
     "units": [{"title": "信号链与功率",
                "chapters": ["p2-01-ch11.md", "p2-02-ch12.md", "p2-03-ch13.md"]}]},
    {"id": "IV", "title": "设计", "subtitle": "从指标到可打样的板",
     "intro": "设计篇从指标出发，把想要什么翻译成增益、带宽、噪声、功耗与成本之间的取舍。"
              "你会练习选型、偏置、稳定性、保护与 PCB 布局，并学会在打样前用计算和仿真排除明显错误。"
              "这里没有唯一正确答案，只有被记录下来的假设、验证与余量。"
              "读完后，你应能独立完成一块小信号模拟板的设计评审。",
     "opener_art": "part-iv.svg",
     "units": [{"title": "方法与实现",
                "chapters": ["p3-01-ch14.md", "p3-02-ch15.md"]}]},
    {"id": "V", "title": "调试", "subtitle": "从现象到根因",
     "intro": "调试篇把前面学到的知识收束成一套可重复的排故方法：先观察现象，再分割电路，提出假设，用测量验证，最后回到根因。"
              "故障速查表覆盖电源、偏置、噪声、振荡、接口与焊接等常见问题，但它的用法是索引而不是背答案。"
              "你会看到经验丰富的工程师如何控制变量、选择接地点与探头，以及如何避免把假象当成结论。"
              "读完后，你应能在没有原理图标注的情况下，仍然有条理地缩小问题范围。",
     "opener_art": "part-v.svg",
     "units": [{"title": "方法与经验",
                "chapters": ["p4-01-ch16.md", "p4-02-ch17.md", "p4-03-ch18.md"]}]}
  ],
  "appendices": [
    {"id": "A", "title": "动画与图示索引", "transform": "animation_index",
     "data": "analog-book/data/animations.yml"},
    {"id": "B", "title": "公式与设计速查", "files": ["p0-08-cheatsheet.md"]},
    {"id": "C", "title": "常用芯片速查",
     "files": ["p6-01-s6-1.md", "p6-02-s6-2.md", "p6-03-s6-3.md",
               "p6-04-s6-4.md", "p6-05-s6-5.md"]},
    {"id": "D", "title": "视频课程与配套资源",
     "files": ["p7-01-s7-1.md", "p7-02-s7-2.md", "p7-03-s7-3.md",
               "p8-02-s8-2.md", "p8-03-s8-3.md", "p8-04-s8-4.md",
               "p8-05-s8-5.md", "p8-06-s8-6.md", "p8-07-s8-7.md",
               "p8-08-s8-8.md", "p8-09-s8-9.md"]},
    {"id": "E", "title": "学习路线、选读与诊断",
     "files": ["p0-04-by-need.md", "p0-05-picks.md", "p0-06-roadmap.md",
               "p0-09-diagnostic.md", "p8-01-s8-1.md", "p8-11-s8-11.md"]},
    {"id": "F", "title": "习题答案与综合自测", "transform": "answers",
     "files": ["p9-00-quiz.md"]},
    {"id": "G", "title": "术语表", "files": ["p9-15-glossary.md", "p8-10-s8-10.md"]},
    {"id": "H", "title": "模型、近似与适用边界", "files": ["p0-10-model-limits.md"]}
  ],
  "excluded_pages": [
    {"file": "index.md", "reason": "站点首页"},
    {"file": "p0-07-toc.md", "reason": "由书内详细目录替代"},
    {"file": "p1-00-part1.md", "reason": "由书内第 II 篇首页替代"},
    {"file": "p2-00-part2.md", "reason": "由书内第 III 篇首页替代"},
    {"file": "p3-00-part3.md", "reason": "由书内第 IV 篇首页替代"},
    {"file": "p4-00-part4.md", "reason": "由书内第 V 篇首页替代"},
    {"file": "p5-00-part5.md", "reason": "附录 A 素材"},
    {"file": "p6-00-part6.md", "reason": "附录 C 分隔页由构建生成"},
    {"file": "p7-00-part7.md", "reason": "附录 D 分隔页由构建生成"},
    {"file": "p8-00-part8.md", "reason": "附录 D/E/G 分隔页由构建生成"}
  ],
  "back_matter": [
    {"kind": "bibliography"},
    {"kind": "index", "terms": "analog-book/data/index-terms.yml"},
    {"file": "p9-12-changelog.md", "title": "版本记录"},
    {"file": "p9-13-thanks.md", "title": "致谢"},
    {"file": "p9-14-credits.md", "title": "来源与许可"},
    {"kind": "colophon"}
  ],
  "cover": {
    "bleed_mm": 3,
    "crop_marks": true,
    "paper_caliper_mm": 0.10,
    "spine_allowance_mm": 1.0,
    "isbn_area": false,
    "back_cover": {
      "blurb": "把直觉、推导、仿真、实测与排故连起来。",
      "audience": "电子、自动化、通信与嵌入式方向的学生和工程师。",
      "highlights": ["19 章完整知识链", "三层读法", "可复现仿真",
                     "实测实验", "故障速查与索引"],
      "structure": [
        {"title": "第一篇 基础", "scope": "电路直觉、无源元件与基本定律"},
        {"title": "第二篇 器件", "scope": "二极管、BJT、MOSFET 与运放内部"},
        {"title": "第三篇 拓扑", "scope": "放大、比较、电源、定时与信号产生"},
        {"title": "第四篇 设计", "scope": "设计方法、参数容差与 PCB 实战"},
        {"title": "第五篇 调试", "scope": "排故五步、故障速查与大师心法"}
      ]
    }
  },
  "release": {"edition_status": "draft", "stable_version": "1.0.0"}
}
```

两份 manifest 的分工必须写进贡献文档，避免有人继续按旧说明只改一份：

- `CONTRIBUTING.md`：「新增内容页必须加入 `analog-book/manifest.json`」改为同时说明——`manifest.json` 服务 16K；A4 1.0 已冻结在 `manifest-a4.json`，Phase 5 前不再改；`make book` 仍构建 A4，16K 用 `python analog-book/build_print_book.py`。
- `analog-book/README.md`：把「新增/删除内容页必须同步 `manifest.json`」改成同样的双 manifest 说明，并标明 A4 产物仍在 `dist/`、16K 在 `dist/print/`。
- `analog-book/READING-FLOW.md`：把「只需改 `manifest.json`」改成「16K 改 `manifest.json`；A4 1.0 已冻结」。

- [ ] **Step 5: 站点附录导航与回归断言**

Modify `scripts/build_site.py:617`:

```python
APPENDIX = {"p9-12-changelog.md", "p9-13-thanks.md", "p9-14-credits.md",
            "p9-15-glossary.md"}
```

Modify `scripts/test_site_build.py` 的 `test_non_chapter_pages_have_no_hero_stage`，把新页面加入列表：

```python
        for name in ("index.html", "p0-08-cheatsheet.html", "p5-00-part5.html",
                     "p1-00-part1.html", "p9-12-changelog.html",
                     "p0-11-conventions.html", "p0-12-symbols.html",
                     "p9-15-glossary.html"):
```

三张新页会让根 `README.md` 与 `docs/` 不同步。必须用生成器重建，不手改；这只是保持现有同步约束，不是 Phase 5 的 16K 文案：

```bash
python scripts/build_readme.py
python scripts/build_readme.py --check
```

- [ ] **Step 6: 16K CLI 与薄入口**

Create `analog-book/book/cli.py`:

```python
"""16K 整书构建入口：HTML、审计、PDF 与印刷封面。"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import config
from .assemble import build_html, check_html
from .cover import build_cover
from .manifest import BookError, load_manifest, validate_manifest
from .pdf import build_pdf, check_pdf
from .sample import build_sample


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=config.DIST_DIR)
    parser.add_argument("--site-dir", type=Path, default=config.SITE_DIR)
    parser.add_argument("--no-build", action="store_true", help="复用已有站点产物")
    parser.add_argument("--check", action="store_true", help="只审计已有整书")
    parser.add_argument("--pdf", action="store_true", help="生成 16K 内文 PDF")
    parser.add_argument("--cover", action="store_true", help="生成印刷封面（隐含 --pdf）")
    parser.add_argument("--sample", action="store_true", help="生成十页 16K 样张")
    parser.add_argument("--browser")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.sample:
            build_sample(args.out_dir / "sample", browser_override=args.browser)
            return 0
        manifest = load_manifest()
        validate_manifest(manifest)
        final = manifest["release"]["edition_status"] == "final"
        if args.check:
            return check_html(args.out_dir, manifest, final=final)
        html_path = build_html(args.out_dir, args.site_dir, config.DATA_DIR,
                               config.DOCS, manifest, rebuild_site=not args.no_build,
                               final=final)
        if not (args.pdf or args.cover):
            return 0
        pdf_path = build_pdf(html_path, args.out_dir, manifest,
                             browser_override=args.browser)
        if not args.cover:
            return 0
        model = json.loads(
            (args.out_dir / config.MODEL_NAME).read_text(encoding="utf-8"))
        report = check_pdf(pdf_path, model, manifest)
        build_cover(args.out_dir, report["pages"], manifest,
                    browser_override=args.browser)
        return 0
    except (BookError, ValueError) as exc:
        print(f"book build error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
```

Create `analog-book/build_print_book.py`:

```python
#!/usr/bin/env python3
"""16K 印刷书入口：实现位于 analog-book/book/cli.py。"""
import sys
from pathlib import Path

BOOK_DIR = Path(__file__).resolve().parent
if str(BOOK_DIR) not in sys.path:
    sys.path.insert(0, str(BOOK_DIR))

from book.cli import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
```

`build_book.py` 不动构建逻辑，只保留 A4 1.0 入口；16K 一律走 `build_print_book.py`，输出默认落在 `analog-book/dist/print/`。

- [ ] **Step 7: 重建字体子集**

新页面、schema-2 manifest 与 `cli.py` 会引入现有字体子集未覆盖的字符；重建并验证子集，避免正文出现方框：

```bash
python scripts/subset_fonts.py --download --build
python scripts/subset_fonts.py --check
```

Expected: `--check` 退出 0，五套 WOFF2 覆盖 `docs/` 新页、`manifest.json` 与 `analog-book/book/*.py` 的全部字符；只提交 `analog-book/fonts/` 下的子集与 `sources.json`，不提交 `build/fonts-src/`。

- [ ] **Step 8: 运行并行验证（不提交）**

```bash
python -B -m unittest discover -s analog-book/tests -p "test_book_manifest.py" -v
python -B -m unittest discover -s analog-book/tests -p "test_book_fonts.py" -v
python scripts/build_site.py --build
python analog-book/build_print_book.py --no-build
python analog-book/build_print_book.py --check --no-build
python -B -m unittest discover -s analog-book/tests -p "test_build.py" -v
python -B -m unittest discover -s scripts -p "test_docs_sync.py" -v
python -B -m unittest discover -s scripts -p "test_docs_links.py" -v
python -B -m unittest discover -s scripts -p "test_page_structure.py" -v
python analog-book/build_book.py --no-build
```

Expected: manifest 测试 PASS（35 tests）；字体测试 PASS（8 tests），新页字符无缺字；站点构建成功；README 与 `docs/` 同步；16K HTML 77 个 `book-page`、模型 77 页；`--check` 返回 0；旧 A4 单元测试 PASS，A4 HTML 仍能构建。草稿允许字数、索引数量、审读等 warning；结构错误必须为 0。不要提交，直接进入 Task 11B。

---

### Task 11B: 并行接入 16K（下）——真实整书集成、16K 浏览器回归与并行 CI

**Files:**
- Create: `analog-book/tests/test_book_real.py`
- Create: `analog-book/tests/test_browser_print_book.py`
- Create: `.github/workflows/book-print.yml`

**Interfaces:**
- Consumes: `book.assemble.build_html`、`book.config`、`book.cli.main`、schema-2 manifest。
- Produces: 真实 77 个逻辑页内容的集成门槛；16K 的浏览器回归；独立于 Pages 的 16K 草稿工作流。
- 不新增生产代码；本任务只补测试、加 16K CI 工作流。若真实测试暴露装配缺陷，回到对应模块修实现，不改断言。旧 A4 测试与构建器一律保留，`book.yml` 不动。

- [ ] **Step 1: 写真实整书集成测试**

Create `analog-book/tests/test_book_real.py`:

```python
#!/usr/bin/env python3
"""真实仓库整书：77 页、无站点残留、锚点全通、习题拆分与 16K 打印契约。"""
import html
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path
from urllib.parse import unquote

BOOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BOOK))

from book import assemble, config  # noqa: E402
from book.manifest import direct_files, excluded_files, load_manifest  # noqa: E402

SITE_READY = (config.SITE_DIR / "p1-01-ch0.html").is_file()
SHELL_MARKERS = (
    "md-content__button", "headerlink", "data-study-video",
    "<iframe", "<video", '<pre class="mermaid">', "mermaid.min.js",
    "TODO", "TBD", "待补", "占位",
)
EMOJI = "📚🧭🔣💡⚠️🎯🔧📐🧪📝"
# MathJax 的内联源码里可能出现 TODO/emoji；内联 base64 也可能恰含 TBD。
# 占位检查只针对可见正文，先剥离脚本/样式与 base64 data URI 载荷。
SCRIPT_STYLE_RE = re.compile(
    r"<(script|style)\b[^>]*>.*?</\1>", re.S | re.I)
DATA_URI_RE = re.compile(
    r"data:[a-zA-Z0-9.+-]+/[a-zA-Z0-9.+-]+;base64,[A-Za-z0-9+/=]+")


@unittest.skipUnless(SITE_READY, "先运行 python scripts/build_site.py --build")
class RealBookTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.tmp.cleanup)
        cls.out = Path(cls.tmp.name)
        cls.manifest = load_manifest()
        cls.html_path = assemble.build_html(
            cls.out, config.SITE_DIR, config.DATA_DIR, config.DOCS,
            cls.manifest, rebuild_site=False, final=False)
        cls.document = cls.html_path.read_text(encoding="utf-8")
        cls.visible = DATA_URI_RE.sub(
            "", SCRIPT_STYLE_RE.sub("", cls.document))
        cls.model = json.loads(
            (cls.out / config.MODEL_NAME).read_text(encoding="utf-8"))

    def test_inventory_and_manifest_coverage(self):
        self.assertEqual(77, len(self.model["pages"]))
        self.assertEqual(77, len({page["id"] for page in self.model["pages"]}))
        self.assertEqual(54, len(direct_files(self.manifest)))
        self.assertEqual(10, len(excluded_files(self.manifest)))
        ids = {page["id"] for page in self.model["pages"]}
        for page_id in ("page-p0-11-conventions", "page-p0-12-symbols",
                        "page-p9-15-glossary", "appendix-a-table",
                        "book-index", "colophon"):
            self.assertIn(page_id, ids)
        for page_id in ("part-i", "part-ii", "part-iii", "part-iv", "part-v"):
            opener = re.search(
                rf'id="{page_id}".*?<p class="part-intro">(.*?)</p>',
                self.visible, re.S)
            self.assertIsNotNone(opener, f"{page_id} 缺少篇导语")
            self.assertTrue(opener.group(1).strip(), f"{page_id} 篇导语为空")

    def test_site_shell_and_draft_markers_are_gone(self):
        for marker in SHELL_MARKERS:
            self.assertNotIn(marker, self.visible)
        for emoji in EMOJI:
            self.assertNotIn(emoji, self.visible)
        self.assertNotIn("<details", self.visible)
        self.assertNotIn("<summary", self.visible)
        self.assertGreaterEqual(self.visible.count('class="book-reveal"'), 4,
                                "章内折叠块应展开为可见块")
        self.assertNotRegex(self.visible, r'(?:src|srcset|poster)="https?://')
        self.assertNotRegex(self.document, r"url\(https?://")

    def test_ids_unique_and_internal_links_resolve(self):
        # 排除 data-id 等复合属性，只统计真正的 id 属性。
        ids = re.findall(r'(?<![\w-])id="([^"]+)"', self.visible)
        self.assertEqual(len(ids), len(set(ids)), "整书不应有重复 id")
        known = set(ids)
        hrefs = {unquote(html.unescape(value))
                 for value in re.findall(r'\bhref="#([^"]+)"', self.visible)}
        missing = sorted(hrefs - known)
        self.assertEqual([], missing[:20], f"{len(missing)} 个锚点无法到达")
        self.assertEqual([], self.model["audit"]["errors"])

    def test_chapter_exercises_and_appendix_answers(self):
        self.assertEqual(19, self.document.count('class="chapter-exercises"'))
        self.assertEqual(20, self.document.count('class="answer-list"'))
        merged = len(re.findall(
            r'<li><a id="[^"]+--q-q-ch\d+-\d+"></a>', self.visible))
        self.assertEqual(58, merged, "58 道章节题应全部并入章末")
        self.assertEqual(merged, self.document.count('class="answer-ref"'),
                         "章末每题都要在附录 F 有一条答案回链")
        self.assertEqual(34, self.document.count('class="answer-question"'))
        self.assertIn('id="appendix-f-answers"', self.document)
        self.assertIn('href="#p1-01-ch0--q-q-ch0-01"', self.document)

    def test_stats_cross_real_content_thresholds(self):
        stats = self.model["stats"]
        self.assertEqual(77, stats["logical_pages"])
        self.assertGreater(stats["images"], 120,
                           "真实构建 137 张；阈值防批量丢图，不锁死数量")
        self.assertGreater(stats["formulas"], 800,
                           "Phase 0 草稿阈值；最终 >2000 在 Phase 5 启用")
        self.assertGreaterEqual(stats["figures"], 1)
        self.assertGreaterEqual(stats["tables"], 1)
        self.assertGreater(len(self.model["toc"]), 100)
        self.assertGreaterEqual(len(self.model["lof"]), 1)
        self.assertGreater(stats["tables"], 0)
        self.assertIsInstance(self.model["lot"], list)

    def test_print_contract_is_inline(self):
        self.assertIn('<style media="print">', self.document)
        match = re.search(
            r'<style media="print">(.*?)</style>', self.document, re.S)
        self.assertIsNotNone(match, "16K 打印样式必须内联")
        print_css = match.group(1)
        self.assertIn("size: 185mm 260mm", print_css)
        self.assertIn("@page :left", print_css)
        # book.css 仍保留 A4 @page 给 1.0 管线；16K 的打印块必须覆盖它。
        self.assertNotIn("size: A4", print_css)
        self.assertIn("data:font/woff2;base64,", self.document)

    def test_colophon_does_not_claim_unverified_physical_pagination(self):
        page = next(item for item in self.model["pages"]
                    if item["id"] == "colophon")
        self.assertIn("77 个逻辑页", page["html"])
        self.assertIn("PRINT-SPEC.md", page["html"])
        self.assertNotIn("书脊厚度约", page["html"])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 运行真实集成测试**

```bash
python scripts/build_site.py --build
python -B -m unittest discover -s analog-book/tests -p "test_book_real.py" -v
```

Expected: PASS (7 tests)。若 `dict` 重复 ID 或锚点失败，先修 `assemble._strip_page_id` 与 TOC/LOF/LOT 锚点，再重跑；不得放宽唯一 ID 或锚点断言。若题数或回链断言失败，核对 `docs/p9-00-quiz.md` 的 19 个 `quiz-chN`、58 道章节题与 34 道“专题加练”，不得改成更宽的阈值。

- [ ] **Step 3: 新增 16K 浏览器测试**

复制现有 A4 测试，保留 `test_browser_book.py` 继续测 1.0：

```bash
cp analog-book/tests/test_browser_book.py analog-book/tests/test_browser_print_book.py
```

In `analog-book/tests/test_browser_print_book.py`, replace the import block:

```python
BOOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BOOK))

from book import config  # noqa: E402
from book.cli import main as book_main  # noqa: E402
```

Replace `setUpClass`:

```python
    @classmethod
    def setUpClass(cls):
        cls.html = config.DIST_DIR / config.OUTPUT_NAME
        if not cls.html.is_file():
            if book_main(["--no-build"]) != 0:
                raise RuntimeError(
                    "16K 整书构建失败；先运行 python scripts/build_site.py --build")
```

In `test_mobile_toc_layout_and_anchor_offset`, replace the old `<ul>/<li>` assumptions:

```python
                    const tocLink = document.querySelector('#book-toc .toc-row a');
                    const footerToc = document.querySelector('.book-page-nav-toc');
                    const list = document.querySelector('#book-toc .book-toc-list');
```

`columns` 断言保留 `self.assertEqual("1", layout["columns"])`：Task 7B 的 `@media (max-width: 44.99em)` 已把 `.book-toc .book-toc-list` 设为单栏，`min-height: 44px` 保证触达高度。其余选择器（`.book-skip`、`#book-search-input`、`#book-search-results`、`.book-header`、`.chapter-hero-num`、`#book-top`、`#book-progress`）保持不变；若 16K 外壳改了节点，按 Task 7B 的实际 DOM 调整，不改断言。

- [ ] **Step 4: 运行两条浏览器回归**

```bash
python analog-book/build_book.py --no-build
python analog-book/build_print_book.py --no-build
python -B -m unittest discover -s analog-book/tests -p "test_browser_book.py" -v
python -B -m unittest discover -s analog-book/tests -p "test_browser_print_book.py" -v
```

Expected: 两条各 PASS (5 tests)。A4 测 `analog-book/dist/`，16K 测 `analog-book/dist/print/`。重点确认：MathJax 离线公式 >1000、计算器 `data-calc-ready` 存在、`Ctrl+K` 搜索命中“米勒”、手机端目录单栏且触达 44px、锚点不被 sticky 页眉遮挡。

- [ ] **Step 5: 独立 16K CI**

Create `.github/workflows/book-print.yml`。不要改 `book.yml`：Pages 通过 `workflow_call` 调用的就是 `book.yml`，把 16K 放进同一个可复用工作流会让任何 16K 失败连带阻断 A4 发布：

```yaml
name: book-print

on:
  push:
    branches: [main]
  pull_request:
  workflow_dispatch:

permissions:
  contents: read

jobs:
  print16k:
    runs-on: ubuntu-latest
    timeout-minutes: 45
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          cache: pip
          cache-dependency-path: |
            requirements.txt
            analog-book/requirements.txt
      - run: pip install -r requirements.txt -r analog-book/requirements.txt
      - uses: actions/cache@v4
        with:
          path: ~/.cache/ms-playwright
          key: ${{ runner.os }}-playwright-${{ hashFiles('analog-book/requirements.txt') }}
      - run: python -m playwright install --with-deps chromium
      - name: 站点构建
        run: python scripts/build_site.py --build
      - name: 16K 单元、装配与真实内容
        run: python -B -m unittest discover -s analog-book/tests -p "test_book_*.py" -v
      - name: 安装 ngspice
        if: github.event_name != 'pull_request'
        run: sudo apt-get update && sudo apt-get install -y ngspice
      - name: SPICE 回归
        if: github.event_name != 'pull_request'
        env:
          BOOK_REQUIRE_NGSPICE: '1'
        run: python -B -m unittest discover -s analog-book/tests -p "test_spice.py" -v
      - name: 16K HTML
        run: python analog-book/build_print_book.py --no-build
      - name: 16K 产物审计
        run: python analog-book/build_print_book.py --check --no-build
      - name: 16K 样张
        if: github.event_name != 'pull_request'
        run: python analog-book/build_print_book.py --sample
      - name: 16K 内文与封面
        if: github.event_name != 'pull_request'
        run: python analog-book/build_print_book.py --no-build --pdf --cover
      - name: 16K 浏览器离线回归
        run: python -B -m unittest discover -s analog-book/tests -p "test_browser_print_book.py" -v
      - uses: actions/upload-artifact@v4
        if: github.event_name != 'pull_request'
        with:
          name: analog-circuit-book-16k-draft
          path: analog-book/dist/print/
          retention-days: 14
```

`book-print.yml` 不进入 `pages.yml` 的 `needs`，也不被 `workflow_call` 调用：16K 失败只让这条草稿工作流变红，A4 的 `book.yml` 与 `/book/` 部署继续独立运行。PR 上只跑单元、装配、真实内容、HTML 审计与浏览器回归；SPICE、样张、PDF、封面与 artifact 只在 main/manual 上生成。`BOOK_REQUIRE_NGSPICE=1` 让 main/manual 缺少 ngspice 时失败而不是静默跳过；本机没有 ngspice 时仍可跳过，但不得声称仿真已验证。

- [ ] **Step 6: 全量草稿构建**

```bash
python scripts/build_site.py --build
python analog-book/build_print_book.py --no-build
python analog-book/build_print_book.py --check --no-build
python analog-book/build_print_book.py --sample
python analog-book/build_print_book.py --no-build --pdf --cover
python -B -m unittest discover -s analog-book/tests -p "test_browser_print_book.py" -v
python analog-book/build_book.py --no-build
python -B -m unittest discover -s analog-book/tests -p "test_browser_book.py" -v
```

Expected:
- `analog-book/dist/print/book-model.json` 77 页，HTML 中 77 个 `book-page`。
- `--check` 返回 0；草稿字数、索引数量、审读 warning 允许，结构 error 必须为 0。
- PDF 页数为 4 的倍数；`cover.pdf` 高度为 266 mm，宽度按 `376 + 书脊` mm 用**实际 PDF 页数**计算（书脊 = 页数 ÷ 2 × 0.10 + 1.0），并与 `cover.pdf` 的实际 MediaBox 一致；不得照抄某个固定页数下的尺寸。`build-report.json`/`PRINT-SPEC.md` 的三处一致性留到 Task 12 生成报告后再核对。
- 16K 浏览器 5 项 PASS；A4 HTML 与浏览器回归仍 PASS。
- 草稿页数若 <450 只出现 warning；不得为了消 warning 注水或提前把 `edition_status` 改成 `final`。

- [ ] **Step 7: 原子提交 11A + 11B**

```bash
git add docs/p0-11-conventions.md docs/p0-12-symbols.md docs/p9-15-glossary.md \
  analog-book/manifest.json analog-book/manifest-a4.json \
  analog-book/book analog-book/build_print_book.py analog-book/build_book.py \
  analog-book/tests/test_book_manifest.py analog-book/tests/test_book_real.py \
  analog-book/tests/test_browser_print_book.py \
  analog-book/fonts README.md CONTRIBUTING.md \
  analog-book/README.md analog-book/READING-FLOW.md \
  scripts/build_site.py scripts/test_site_build.py .github/workflows/book-print.yml
git commit -m "feat(book): add the parallel 16K pipeline without touching the 1.0 book"
```

11A 与 11B 必须同一个提交：只提交 11A 会让 16K 的真实内容与浏览器门槛缺失；只提交 11B 则 manifest、CLI 与测试不匹配。提交后不要推送，等 Task 12 的报告与发布准备完成。`book.css`、`test_build.py`、`test_pdf.py`、`test_browser_book.py` 一律不动。

---

### Task 12: 构建报告、PRINT-SPEC、写作规范与 16K 发布准备

**Files:**
- Create: `analog-book/book/report.py`
- Create: `analog-book/tests/test_book_report.py`
- Create: `analog-book/STYLE.md`
- Modify: `analog-book/book/cli.py`
- Rename: `scripts/publish_book.py` → `scripts/publish_a4_book.py`（1.0 发布器）
- Rename: `scripts/test_publish_book.py` → `scripts/test_publish_a4_book.py`
- Create: `scripts/publish_book.py`（16K 发布入口）
- Create: `scripts/test_publish_book.py`（16K 发布测试）
- Modify: `scripts/test_release_gate.py`
- Modify: `.github/workflows/book-print.yml`（加构建报告步骤）
- Modify: `.github/workflows/pages.yml`（只把发布命令改为 `publish_a4_book.py`）
- Modify: `.github/workflows/tests.yml`（只把命令换成 `test_publish_a4_book.py`）
- Modify: `Makefile`（`test-static` 跑两个发布器测试）
- Modify: `analog-book/READING-FLOW.md`（A4 发布器改名后的说明）

**Interfaces:**
- Produces:
  - `build_report(out_dir, model, manifest, pdf_report, cover_report, sample_report=None, pdf_path=None, cover_path=None) -> dict`
  - `print_spec_markdown(report: dict, manifest: dict) -> str`
  - `write_report(out_dir, model, manifest, pdf_report, cover_report, sample_report=None, pdf_path=None, cover_path=None) -> dict`
  - `publish(html_path, pdf_path, site_dir, cover_pdf, cover_preview, print_spec, report) -> Path`
- 报告只读已有产物，不重建 HTML/PDF；`--report` 必须在 `--pdf --cover` 之后运行。
- `PRINT-SPEC.md` 中的书脊与封面尺寸必须由实际页数和 manifest 参数算出，不得手写。
- 16K 发布器在 Phase 0 只跑测试，不接入 Pages；`/book/` 仍由 `publish_a4_book.py` 发布 A4 1.0。

- [ ] **Step 1: 先写报告测试**

Create `analog-book/tests/test_book_report.py`:

```python
#!/usr/bin/env python3
"""构建报告与 PRINT-SPEC：只读事实、书脊算术、草稿门与稳定版。"""
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

BOOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BOOK))

from book import config, report  # noqa: E402
from book.manifest import BookError  # noqa: E402

MANIFEST = {
    "title": "通往模拟电路之路",
    "edition": "第一版",
    "version": "2.0.0-draft.1",
    "source_version": "3.61",
    "date": "2026-10-25",
    "trim": {"width_mm": 185, "height_mm": 260},
    "parts": [{"id": str(i), "units": [{"chapters": [f"c{i}"]}]}
              for i in range(5)],
    "cover": {"bleed_mm": 3, "paper_caliper_mm": 0.10,
              "spine_allowance_mm": 1.0},
    "release": {"edition_status": "draft"},
}
MODEL = {
    "pages": [{"id": f"p{i}"} for i in range(77)],
    "stats": {"figures": 12, "tables": 8, "formulas": 900, "images": 200},
    "endnotes": 123,
    "audit": {"errors": [], "warnings": ["draft word count"]},
}
PDF = {"pages": 652, "body_start": 13, "bookmarks": 143,
       "size_mm": [184.83, 260.01],
       "problems": [],
       "warnings": ["草稿只检查 16K 结构项；印前全检在 Phase 5 执行"]}
COVER = {"pages": 1, "size_mm": [409.6, 266.0],
         "spine_mm": 33.6, "problems": []}


class ReportTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.out = Path(self.tmp.name)
        files = {
            config.OUTPUT_NAME: b"<!doctype html><title>book</title>",
            config.PDF_NAME: b"%PDF-1.7\n" + b"0" * 2048,
            config.COVER_PDF_NAME: b"%PDF-1.7\n" + b"1" * 1024,
            config.COVER_PREVIEW_NAME: b"\x89PNG\r\n\x1a\n" + b"2" * 512,
        }
        for name, payload in files.items():
            (self.out / name).write_bytes(payload)

    def write(self, manifest=MANIFEST, pdf=PDF, cover=COVER):
        return report.write_report(
            self.out, MODEL, manifest, pdf, cover,
            sample_report={"fallback": "mirrored"})

    def test_json_report_records_actual_facts(self):
        data = self.write()
        self.assertEqual(77, data["logical_pages"])
        self.assertEqual(5, data["parts"])
        self.assertEqual(652, data["pdf_pages"])
        self.assertEqual(13, data["body_start"])
        self.assertEqual(143, data["bookmarks"])
        self.assertEqual(20, data["figures"] + data["tables"])
        self.assertEqual("PDF 1.7", data["pdf_version"])
        self.assertEqual("mirrored", data["mirrored"])
        self.assertEqual(652, data["cover"]["pages"])
        self.assertEqual(33.6, data["cover"]["spine_mm"])
        self.assertEqual([409.6, 266.0], data["cover"]["size_mm"])
        self.assertEqual([184.83, 260.01], data["interior_size_mm"])
        self.assertEqual(PDF["warnings"], data["pdf_warnings"])
        self.assertIn("Phase 5", data["preflight"])
        saved = json.loads(
            (self.out / "build-report.json").read_text(encoding="utf-8"))
        self.assertEqual(data, saved)

    def test_print_spec_has_spine_math_and_no_fake_isbn(self):
        self.write()
        spec = (self.out / "PRINT-SPEC.md").read_text(encoding="utf-8")
        self.assertIn("652 / 2 × 0.10 + 1.0 = 33.60 mm", spec)
        self.assertIn("2 × 185 + 33.60 + 2 × 3 = 409.60 mm", spec)
        self.assertIn("185 × 260 mm", spec)
        self.assertIn("未申请 ISBN", spec)
        self.assertNotIn("978-", spec)
        self.assertIn("草稿", spec)
        self.assertIn("内文实际 MediaBox | 184.83 × 260.01 mm", spec)
        self.assertIn("4 的倍数：是", spec)
        self.assertIn("印前全检：未执行（Phase 5 印前门禁）", spec)
        self.assertIn("## 9 PDF 结构检查警告", spec)
        self.assertIn(PDF["warnings"][0], spec)
        self.assertIn("BookSans-Stamp.ttf", spec)
        for heading in ("开本与版心", "页数、书脊与封面", "字体与许可",
                        "打样与校对页", "尚未关闭的质量门"):
            self.assertIn(heading, spec)

    def test_problems_block_report(self):
        broken = dict(COVER, problems=["spine mismatch"])
        with self.assertRaisesRegex(BookError, "封面结构问题"):
            self.write(cover=broken)

    def test_final_has_no_deferred_gates(self):
        final = {**MANIFEST, "release": {"edition_status": "final"}}
        data = self.write(manifest=final)
        self.assertEqual([], data["deferred"])
        spec = (self.out / "PRINT-SPEC.md").read_text(encoding="utf-8")
        self.assertIn("无（本版为稳定版）", spec)
        self.assertIn("印前全检：未执行", spec)

    def test_print_spec_geometry_matches_print_css(self):
        css = (config.BOOK_DIR / "styles" / "print.css").read_text(
            encoding="utf-8")
        page = re.search(
            r"@page\s*\{\s*size:\s*(\d+)mm\s+(\d+)mm;\s*"
            r"margin:\s*(\d+)mm\s+(\d+)mm\s+(\d+)mm;", css)
        left = re.search(
            r"@page\s*:left\s*\{\s*margin:\s*(\d+)mm\s+(\d+)mm\s+"
            r"(\d+)mm\s+(\d+)mm;", css)
        right = re.search(
            r"@page\s*:right\s*\{\s*margin:\s*(\d+)mm\s+(\d+)mm\s+"
            r"(\d+)mm\s+(\d+)mm;", css)
        self.assertIsNotNone(page)
        self.assertIsNotNone(left)
        self.assertIsNotNone(right)
        width, height, top, _right_margin, bottom = map(int, page.groups())
        left_top, inside, left_bottom, outside = map(int, left.groups())
        right_top, right_outside, right_bottom, right_inside = map(
            int, right.groups())
        self.assertEqual((top, bottom), (left_top, left_bottom))
        self.assertEqual((top, bottom), (right_top, right_bottom))
        self.assertEqual(inside, right_inside)
        self.assertEqual(outside, right_outside)
        data = self.write()
        self.assertEqual([width, height], data["trim_mm"])
        self.assertEqual([width - inside - outside, height - top - bottom],
                         data["text_block_mm"])
        self.assertEqual(
            {"top": top, "bottom": bottom,
             "inside": inside, "outside": outside},
            data["margins_mm"])

    def test_print_css_lets_long_tables_split_and_repeat_headers(self):
        css = (config.BOOK_DIR / "styles" / "print.css").read_text(
            encoding="utf-8")
        self.assertIn(
            ".book .book-table { margin: 3mm 0 0; break-inside: auto; }", css)
        self.assertIn(".book .table-wrap { break-inside: auto; }", css)
        self.assertIn("thead { display: table-header-group; }", css)
        self.assertIn("tr { break-inside: avoid; }", css)

    def test_style_evidence_levels_match_reader_conventions(self):
        style = (config.BOOK_DIR / "STYLE.md").read_text(encoding="utf-8")
        conventions = (config.DOCS / "p0-11-conventions.md").read_text(
            encoding="utf-8")
        for row in ("| A | 教材、手册、厂商数据手册、应用笔记",
                    "| B | 可复现的仿真",
                    "| C | 本仓库实测",
                    "| D | 经验判断、工程惯例"):
            self.assertIn(row, style)
            self.assertIn(row, conventions)

    def test_style_guide_is_executable(self):
        text = (config.BOOK_DIR / "STYLE.md").read_text(encoding="utf-8")
        for heading in ("三层读法", "证据等级", "仿真与实测", "交稿检查"):
            self.assertIn(heading, text)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 运行测试，确认失败**

Run: `python -B -m unittest discover -s analog-book/tests -p "test_book_report.py" -v`
Expected: FAIL with `No module named 'book.report'`.

- [ ] **Step 3: 实现 `book/report.py`**

```python
"""构建报告与印刷规格：只读已有产物，不重复构建。"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from . import config
from .manifest import BookError

REPORT_NAME = "build-report.json"
PRINT_SPEC_NAME = "PRINT-SPEC.md"
FONT_LICENSE = "SIL OFL 1.1"
PAPER = "80g 纯质纸"
COVER_STOCK = "250g 铜版纸覆哑膜"
BINDING = "胶装"
COLOR = "sRGB"
DEFERRED = [
    "19 章正文扩写与统稿（目标 320,000 字）",
    "图表、动画与视频配套补齐",
    "19 章 SPICE 仿真与三套实测复核",
    "索引、参考文献与外部审读",
    "封面打样、纸张与印厂参数确认",
    "印前全检（字体嵌入、缺字、公式图形、版心溢出、图表跨页与 PDF <100MB）",
    "ISBN 与条码（尚未申请）",
]


def _require(path: Path) -> Path:
    path = Path(path)
    if not path.is_file() or path.stat().st_size == 0:
        raise BookError(f"报告所需产物不存在或为空: {path}")
    return path


def _pdf_version(pdf_path: Path) -> str:
    head = Path(pdf_path).read_bytes()[:8].decode("latin-1", "replace")
    if head.startswith("%PDF-"):
        return "PDF " + head[5:].strip()
    return "PDF"


def _fonts(fonts_dir=config.FONTS_DIR) -> list[dict]:
    data = json.loads(
        (Path(fonts_dir) / "sources.json").read_text(encoding="utf-8"))
    fonts = [{"family": item["family"], "weight": item["weight"],
              "file": item["name"], "license": FONT_LICENSE}
             for item in data["subsets"]]
    stamp = data.get("stamp") or {}
    if stamp:
        fonts.append({"family": stamp["family"], "weight": stamp["weight"],
                      "file": stamp["name"], "license": FONT_LICENSE})
    return fonts


def _sample(out_dir: Path) -> dict | None:
    path = Path(out_dir) / "sample" / config.SAMPLE_REPORT_NAME
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def build_report(out_dir, model, manifest, pdf_report, cover_report,
                 sample_report=None, pdf_path=None, cover_path=None) -> dict:
    if pdf_report.get("problems"):
        raise BookError("PDF 结构问题: " + "; ".join(pdf_report["problems"]))
    if cover_report.get("problems"):
        raise BookError("封面结构问题: " + "; ".join(cover_report["problems"]))
    out_dir = Path(out_dir)
    html_path = _require(out_dir / config.OUTPUT_NAME)
    pdf_path = _require(pdf_path or out_dir / config.PDF_NAME)
    cover_path = _require(cover_path or out_dir / config.COVER_PDF_NAME)
    preview = out_dir / config.COVER_PREVIEW_NAME
    sample = sample_report if sample_report is not None else _sample(out_dir)
    stats = model["stats"]
    cover_cfg = manifest["cover"]
    endnotes = model.get("endnotes", 0)
    if isinstance(endnotes, list):
        endnotes = len(endnotes)
    return {
        "schema": 1,
        "generated": dt.datetime.now(
            dt.timezone.utc).isoformat(timespec="seconds"),
        "edition_status": manifest["release"]["edition_status"],
        "title": manifest["title"],
        "edition": manifest["edition"],
        "version": manifest["version"],
        "source_version": manifest.get("source_version", ""),
        "date": manifest["date"],
        "logical_pages": len(model["pages"]),
        "parts": len(manifest["parts"]),
        "chapters": sum(len(unit["chapters"]) for part in manifest["parts"]
                        for unit in part["units"]),
        "pdf_pages": pdf_report["pages"],
        "body_start": pdf_report["body_start"],
        "bookmarks": pdf_report["bookmarks"],
        "pdf_warnings": list(pdf_report.get("warnings", [])),
        "preflight": "未执行（Phase 5 印前门禁）",
        "figures": stats.get("figures", 0),
        "tables": stats.get("tables", 0),
        "formulas": stats.get("formulas", 0),
        "images": stats.get("images", 0),
        "endnotes": endnotes,
        "html_bytes": html_path.stat().st_size,
        "pdf_bytes": pdf_path.stat().st_size,
        "cover_bytes": cover_path.stat().st_size,
        "preview_bytes": preview.stat().st_size if preview.is_file() else 0,
        "trim_mm": [manifest["trim"]["width_mm"],
                    manifest["trim"]["height_mm"]],
        "interior_size_mm": list(pdf_report.get("size_mm") or []),
        "text_block_mm": [config.TEXT_WIDTH_MM, config.TEXT_HEIGHT_MM],
        "margins_mm": {"top": 20, "bottom": 22,
                       "inside": 22, "outside": 18},
        "mirrored": (sample or {}).get("fallback", "not-sampled"),
        "bleed_mm": cover_cfg["bleed_mm"],
        "cover": {
            # inspect_cover 的 pages 是封面 PDF 自身页数（恒为 1）；
            # 报告要记的是书脊所依据的内文页数。
            "pages": pdf_report["pages"],
            "size_mm": cover_report["size_mm"],
            "spine_mm": cover_report["spine_mm"],
            "paper_caliper_mm": cover_cfg["paper_caliper_mm"],
            "spine_allowance_mm": cover_cfg["spine_allowance_mm"],
        },
        "fonts": _fonts(),
        "paper": PAPER,
        "cover_stock": COVER_STOCK,
        "binding": BINDING,
        "color": COLOR,
        "pdf_version": _pdf_version(pdf_path),
        "audit": {"errors": model["audit"]["errors"],
                  "warnings": model["audit"]["warnings"]},
        "deferred": (
            [] if manifest["release"]["edition_status"] == "final"
            else list(DEFERRED)),
    }


def _human(size: int) -> str:
    if size >= 1024 * 1024:
        return "%.1f MB" % (size / (1024 * 1024))
    return "%d KB" % max(1, round(size / 1024))


def print_spec_markdown(report: dict, manifest: dict) -> str:
    cover = report["cover"]
    spine = cover["spine_mm"]
    caliper = cover["paper_caliper_mm"]
    allowance = cover["spine_allowance_mm"]
    width, height = cover["size_mm"]
    trim_w, trim_h = report["trim_mm"]
    bleed = report["bleed_mm"]
    size_mm = report.get("interior_size_mm") or []
    interior = (f"{size_mm[0]:.2f} × {size_mm[1]:.2f} mm"
                if len(size_mm) == 2 else "未记录")
    multiple = "是" if report["pdf_pages"] % 4 == 0 else "否"
    pdf_warnings = report.get("pdf_warnings") or []
    warning_lines = ("\n".join(f"- {item}" for item in pdf_warnings)
                     if pdf_warnings else "- 无")
    formula = (f"{report['pdf_pages']} / 2 × {caliper:.2f} + "
               f"{allowance:.1f} = {spine:.2f} mm")
    nominal_width = 2 * trim_w + spine + 2 * bleed
    nominal_height = trim_h + 2 * bleed
    cover_formula = (
        f"2 × {trim_w:g} + {spine:.2f} + 2 × {bleed:g} = "
        f"{nominal_width:.2f} mm（标称）；"
        f"{trim_h:g} + 2 × {bleed:g} = {nominal_height:.2f} mm（标称）；"
        f"实际 MediaBox {width:.2f} × {height:.2f} mm")
    fonts = "\n".join(
        f"| {item['family']} | {item['weight']} | `{item['file']}` | "
        f"{item['license']} |" for item in report["fonts"])
    deferred = ("\n".join(f"- {item}" for item in report["deferred"])
                if report["deferred"] else "- 无（本版为稳定版）")
    status = "草稿" if report["edition_status"] == "draft" else "稳定版"
    return f"""# 印刷规格：{report['title']} {report['edition']}

> 本文件由 `analog-book/book/report.py` 从实际 HTML、PDF、封面与样张生成。与任何手写数字冲突时，以本文件为准。

## 1 版本与状态

| 项目 | 值 |
|---|---|
| 版本 | {report['version']} |
| 状态 | {status} |
| 内容源版本 | {report['source_version']} |
| 构建日期 | {report['date']} |
| 生成时间 | {report['generated']} |

## 2 开本与版心

| 项目 | 数值 |
|---|---|
| 成品尺寸 | {trim_w:g} × {trim_h:g} mm（16K，标称） |
| 内文实际 MediaBox | {interior}（Chromium 渲染，允许 ±0.5 mm） |
| 版心 | {report['text_block_mm'][0]:g} × {report['text_block_mm'][1]:g} mm |
| 页边距 | 上 {report['margins_mm']['top']} mm / 下 {report['margins_mm']['bottom']} mm / 订口 {report['margins_mm']['inside']} mm / 切口 {report['margins_mm']['outside']} mm |
| 镜像边距 | {report['mirrored']} |

## 3 页数、书脊与封面

| 项目 | 数值 |
|---|---|
| 内文页数 | {report['pdf_pages']}（4 的倍数：{multiple}） |
| 书脊公式 | {formula} |
| 封面展开（含出血） | {width:.2f} × {height:.2f} mm |
| 封面尺寸推导 | {cover_formula} |
| 出血 | {bleed} mm |
| 内文 PDF | {_human(report['pdf_bytes'])} |
| 封面 PDF | {_human(report['cover_bytes'])} |

> 表中“封面展开”是 `cover.pdf` 的实际 MediaBox；推导公式是按页数与纸张参数计算的标称尺寸。Chromium 渲染允许 0.5 mm 内的取整误差，印刷以实际 MediaBox 与打样为准。

> 书脊按 `页数 / 2 × 纸张厚度 + 装订余量` 计算。上机前必须用实际纸张打样复核；不同批次纸张厚度会让书脊相差 1–2 mm。

## 4 纸张与装订

| 项目 | 规格 |
|---|---|
| 正文 | {report['paper']} |
| 封面 | {report['cover_stock']} |
| 装订 | {report['binding']} |
| ISBN | 未申请 ISBN；封面不含 ISBN 与条码 |

## 5 字体与许可

| 字族 | 字重 | 文件 | 许可 |
|---|---:|---|---|
{fonts}

## 6 色彩与文件

| 项目 | 值 |
|---|---|
| 色彩空间 | {report['color']} |
| PDF 版本 | {report['pdf_version']} |
| 单文件 HTML | {_human(report['html_bytes'])} |
| 封面预览 | {_human(report['preview_bytes']) if report['preview_bytes'] else '未生成'} |
| 书签数 | {report['bookmarks']} |
| 图表数 | {report['figures']} 图 / {report['tables']} 表 |
| 公式数 | {report['formulas']} |
| 尾注数 | {report['endnotes']} |

## 7 打样与校对页

- 章首页：确认章号、学习目标与页眉不冲突。
- 跨页表：确认表头重复、单元格不被裁切。
- 长公式：确认不越出版心、不被分页截断。
- 图与图注：确认图注同页、灰阶可辨。
- 目录/索引：确认 `000` 已全部回填，页码与正文一致。
- 封面：确认书脊文字、裁切线、二维码与出血。

## 8 尚未关闭的质量门

**印前全检：{report['preflight']}。** 下表列出尚未关闭的门；第 3 节的书脊与封面仍须打样复核。

{deferred}

## 9 PDF 结构检查警告

{warning_lines}
"""


def write_report(out_dir, model, manifest, pdf_report, cover_report,
                 sample_report=None, pdf_path=None, cover_path=None) -> dict:
    out_dir = Path(out_dir)
    report = build_report(
        out_dir, model, manifest, pdf_report, cover_report,
        sample_report=sample_report, pdf_path=pdf_path,
        cover_path=cover_path)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / REPORT_NAME).write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")
    (out_dir / PRINT_SPEC_NAME).write_text(
        print_spec_markdown(report, manifest), encoding="utf-8")
    return report
```

- [ ] **Step 4: 运行报告实现测试（不含尚未创建的 STYLE.md）**

Run:

```bash
python -B analog-book/tests/test_book_report.py \
  ReportTests.test_json_report_records_actual_facts \
  ReportTests.test_print_spec_has_spine_math_and_no_fake_isbn \
  ReportTests.test_problems_block_report \
  ReportTests.test_final_has_no_deferred_gates -v
```

Expected: PASS (4 tests)。若书脊算术失败，检查 `spine_mm` 是否来自 `inspect_cover` 的实际页数，而不是测试里手填的常量。`test_style_guide_is_executable` 此时仍会失败，这是下一步的交付物。

---

- [ ] **Step 5: 写 `analog-book/STYLE.md` 并跑完整报告测试**

Create `analog-book/STYLE.md`:

```markdown
# 写作与制作规范

本书的唯一定稿源是 `docs/`。站点由 `scripts/build_site.py --build` 生成；16K 印刷版由 `analog-book/build_print_book.py` 从站点 HTML 装配（A4 1.0 走 `build_book.py`，两者共用 `docs/`）。只改书内 HTML 的修补会在下一次构建时丢失。

## 1 三层读法

| 层 | 写什么 | 不写什么 |
|---|---|---|
| 主线 | 零基础读者必须读懂的定义、直觉、最小推导、一个可复现例子 | 依赖未讲概念的跳步 |
| 进阶框 | 推导、模型边界、器件内部、设计取舍、失效模式 | 与主线无关的炫技 |
| 速查层 | 公式、判据、引脚、典型值、排故表 | 大段散文 |

自检：删掉全部进阶框，主线仍然成立；只读速查层，不能替代章节正文。

## 2 章骨架

1. 场景问题或一个反直觉现象。
2. `> 🎯 **学完你应能**：...` 三条以内，可验证。
3. 模型与推导：先物理图像，再公式，再单位检查。
4. 仿真或实测：给出可复现的 deck、条件、波形与结论。
5. 失效边界与排故：至少一个“看起来对、其实错”的坑。
6. 本章练习：4–6 题，答案只写进 `docs/p9-00-quiz.md`。
7. 延伸阅读：只列真实存在、可核对的资料。

每章目标 18,000 非空白字符，硬下限 15,000；Phase 0 草稿不足只产生 warning，不得注水或把状态改成 `final`。

## 3 标记契约

- 提示框用引用块，第一行是 emoji + 粗体标签：
  `> 🎯 **学完你应能**：`、`> 🧮 **公式速查**：`、`> 🔬 **模型边界**：`、
  `> 💎 **精髓**：`、`> ⚠️ **注意**：`、`> 🧰 **修复方法**：`、
  `> 💡 **设计直觉**：`、`> 🎬 **配套视频**：`、`> 📷 **实测记录**：`、
  `> 🔗 **延伸阅读**：`。站点构建器会转成 `.callout`，书内构建器再统一为
  `.book-callout`；不要在正文手写 `.book-callout`。
- 站点用 `<details>` 折叠的补充推导与自测，书内由构建器展开为可见的
  `.book-reveal` 块；书中不得保留 `<details>`/`<summary>`，也不要在正文手写
  `.book-reveal`。
- 图：用 `<figure>` + `<figcaption>`，图注写清“看什么、得出什么”，不手写图号；
  构建器按章编号并生成插图目录。装饰性图标不进图目录。
- 表：表前一行写 `**表 章-序号　标题**`，紧跟 Markdown 表格；表头必须在
  `<thead>`，单位写进列名或单元格，不靠正文补充。表号必须与章号一致。
- 公式：行内 `$...$`，独立 `$$...$$`；量符号斜体、单位正体；公式后立即给
  符号表或一句“其中……”。
- 链接：站内链接指向 `p1-01-ch0.md#anchor` 这类真实源页；外部链接在书中自动
  收进章末尾注，正文只留角标，不把长 URL 排进正文。
- 视频：保留站点的视频引用块；书内构建器把它转成“配套视频”文字引用，
  不内嵌 `<video>`。视频文件不提交仓库。
- 计算器：`<div class="calc" data-calc="..."></div>` 前后必须有“例 N-x /
  算一笔 / 再算一笔”的可手算过程；打印版隐藏计算器控件，只保留手算。

## 4 数字、单位与证据

- SI 单位；数字与单位之间留空格：`5 V`、`10 kΩ`、`100 µF`、`25 °C`。
- 微写作 `µ`，不写 `u`；欧姆写 `Ω`；乘号用 `×`，范围用 `–`。
- 有效数字与容差必须匹配：`4.7 kΩ ±5%`，不写“精确 4.700 kΩ”。
- 估值、典型值、最大值分开写；没有来源的“经验值”标成经验值。
- 不伪造实测数据、器件曲线、厂商截图或文献。实测只覆盖仓库中真实做过的
  RC、LM358 与 MOSFET 三套实验；其余一律标为仿真或教材推导。

### 证据等级

| 等级 | 来源 | 写法 |
|---|---|---|
| A | 教材、手册、厂商数据手册、应用笔记 | 给出书名/版次/章节，或厂商与文档编号 |
| B | 可复现的仿真 | 给出 `assets/spice/` 下的 deck 与分析方法 |
| C | 本仓库实测 | 仅限 RC、LM358、MOSFET；给 CSV、仪器条件与日期 |
| D | 经验判断、工程惯例 | 明写“经验/待验证”，不冒充结论 |

## 5 仿真与实测

- 每章至少一套 `assets/spice/chNN/*.cir` 与 `assert.json`；deck 自包含，
  禁止 `.include` / `.lib` 外部模型，除非该模型已随仓库授权提交。
- `assert.json` 至少一个指标、一个容差、一个最小行数；数据只写入
  `build/spice/`，不得回写 `assets/`。
- 图必须从实际输出生成；手绘示意与仿真结果必须标明区别。
- 实测记录写清仪器、量程、环境、样本数与失败样本；不能只贴一张“完美波形”。

## 6 习题与答案

- 章节题 ID 用 `q-chN-NN`，专题题用 `q-extra-NN`；题号一旦发布不改，
  只追加。Phase 0 现有 58 道章节题、34 道专题题；内容波次按章补到 4–6 题时，
  同步更新真实内容测试的计数，不得为了凑数删题或改旧题号。
- 题干给足条件与单位；答案给推导关键步与常见错法，不只给数字。
- 答案只存在于 `docs/p9-00-quiz.md` 的 `<details>` 中；构建器把题目拆进章末、
  答案拆进附录 F。书中不得残留 `<details>`。

## 7 结构变更

- 新增/删除页面：改 `analog-book/manifest.json`、对应测试与索引种子；新增附录页
  还要加入 `scripts/build_site.py` 的 `APPENDIX`。A4 1.0 已冻结在
  `manifest-a4.json`，Phase 5 前不再改；不允许只加一个 Markdown 文件。
- 改章号：同步所有交叉引用、题库 ID、索引、SPICE 路径、图号与测试。
- 改书名、开本、纸张、书脊参数：只改 manifest 与 `book/config.py`，
  然后重跑样张、PDF、封面与报告；不要手改 `PRINT-SPEC.md`。

## 8 交稿检查

- [ ] 三层读法齐全，删掉进阶框后主线仍可读。
- [ ] 每图有 alt 与图注；每表有表头、表号与单位；长表能跨页重复表头。
- [ ] 公式符号前后一致，单位与有效数字正确。
- [ ] 仿真能一键复跑；实测有记录；没有伪造数据。
- [ ] 站内链接可达；外部链接已进尾注；无远程图片与 iframe。
- [ ] 无 emoji 残留、无 `<details>`、无 TODO/TBD/待补/占位。
- [ ] `python scripts/build_site.py --build` 与整书 `--check` 通过。
- [ ] PDF 页数为 4 的倍数；目录/索引无 `000`；页眉页码正确。
- [ ] 封面书脊与页数一致；未申请 ISBN 时封面不出现假 ISBN/条码。
- [ ] 安全声明、模型边界与许可信息仍在版权页与相关章节。
```

Run: `python -B -m unittest discover -s analog-book/tests -p "test_book_report.py" -v`
Expected: PASS (5 tests)，包括 `test_style_guide_is_executable`。若标题缺失，补齐 STYLE.md 的对应章节，不删测试。

---

- [ ] **Step 6: 给 CLI 加 `--report`**

Modify `analog-book/book/cli.py`:

```python
from .cover import build_cover, inspect_cover
from .report import write_report
```

在 `_parser()` 的 `--cover` 之后加：

```python
    parser.add_argument("--report", action="store_true",
                        help="从已有 HTML/PDF/封面写构建报告与印刷规格")
```

在 `main()` 里 `final = ...` 之后、`if args.check:` 之前插入：

```python
        if args.report:
            if check_html(args.out_dir, manifest, final=final) != 0:
                return 1
            model = json.loads(
                (args.out_dir / config.MODEL_NAME).read_text(encoding="utf-8"))
            pdf_path = args.out_dir / config.PDF_NAME
            cover_path = args.out_dir / config.COVER_PDF_NAME
            for path in (pdf_path, cover_path):
                if not path.is_file():
                    raise BookError(
                        f"--report 需要先运行 --pdf --cover：缺少 {path.name}")
            pdf_report = check_pdf(pdf_path, model, manifest)
            cover_report = inspect_cover(
                cover_path, pdf_report["pages"], manifest)
            summary = write_report(
                args.out_dir, model, manifest, pdf_report, cover_report,
                pdf_path=pdf_path, cover_path=cover_path)
            print(f"report: {summary['pdf_pages']} pages, "
                  f"spine {summary['cover']['spine_mm']:.2f} mm")
            return 0
```

把 `--cover` 分支改成先挡住结构问题，再用返回的封面做一次检查：

```python
        pdf_path = build_pdf(html_path, args.out_dir, manifest,
                             browser_override=args.browser)
        if not args.cover:
            return 0
        model = json.loads(
            (args.out_dir / config.MODEL_NAME).read_text(encoding="utf-8"))
        report = check_pdf(pdf_path, model, manifest)
        if report["problems"]:
            raise BookError("; ".join(report["problems"]))
        _html, cover_pdf, _preview = build_cover(
            args.out_dir, report["pages"], manifest,
            browser_override=args.browser)
        cover_report = inspect_cover(cover_pdf, report["pages"], manifest)
        if cover_report["problems"]:
            raise BookError("; ".join(cover_report["problems"]))
        return 0
```

- [ ] **Step 7: 运行 CLI 报告入口**

```bash
python analog-book/build_print_book.py --help | grep -- --report
python analog-book/build_print_book.py --no-build --report
tail -n 20 analog-book/dist/print/PRINT-SPEC.md
```

Expected: `--report` 出现；在已有 PDF/封面时返回 0，打印 `report: <4 的倍数> pages, spine <xx.xx> mm`；`PRINT-SPEC.md` 第 3 节的书脊公式与实际页数一致。缺少封面时给出明确错误，不得悄悄重建。

---

- [ ] **Step 8: 拆分 1.0 与 16K 发布器**

先把仍在服务 Pages 的 A4 发布器改名冻结：

```bash
git mv scripts/publish_book.py scripts/publish_a4_book.py
git mv scripts/test_publish_book.py scripts/test_publish_a4_book.py
```

把 `scripts/test_publish_a4_book.py` 的导入改为：

```python
from publish_a4_book import BOOK_DIR_NAME, BOOK_URL, publish  # noqa: E402
```

Modify `.github/workflows/pages.yml` 的发布步骤，保持行为不变：

```yaml
      - name: 离线整书并入站点（/book/）
        run: python scripts/publish_a4_book.py
```

再复制 A4 发布器作为 16K 发布器，保留完整落地页骨架：

```bash
cp scripts/publish_a4_book.py scripts/publish_book.py
```

在 `scripts/publish_book.py` 中新增封面、预览、印刷规格、报告四个默认路径，并把 HTML、PDF 两个默认路径改到 16K 目录（共六个）：

```python
DEFAULT_HTML = ROOT / "analog-book" / "dist" / "print" / "analog-circuit-book.html"
DEFAULT_PDF = ROOT / "analog-book" / "dist" / "print" / "analog-circuit-book.pdf"
DEFAULT_COVER_PDF = ROOT / "analog-book" / "dist" / "print" / "cover.pdf"
DEFAULT_COVER_PREVIEW = ROOT / "analog-book" / "dist" / "print" / "cover-preview.png"
DEFAULT_PRINT_SPEC = ROOT / "analog-book" / "dist" / "print" / "PRINT-SPEC.md"
DEFAULT_REPORT = ROOT / "analog-book" / "dist" / "print" / "build-report.json"
```

`DEFAULT_SITE` 保持 `build/site`；A4 发布器的 `DEFAULT_*` 保持指向 `analog-book/dist/` 根目录，两者互不覆盖。

把 `.formats` 改为三列，并在 `.note` 前加印刷区块样式：

```css
.formats {
  display: grid; gap: 12px; grid-template-columns: repeat(3, minmax(0, 1fr));
}
.printbox {
  margin-top: clamp(36px, 6vw, 64px); padding: 24px;
  border: 1px solid var(--line); border-radius: 16px;
  background: var(--card);
}
.printbox h2 { margin: 0 0 16px; font-size: 22px; }
.print-grid {
  display: grid; gap: 24px; align-items: center;
  grid-template-columns: minmax(0, 1.4fr) minmax(220px, 1fr);
}
.cover-preview {
  display: block; width: 100%; height: auto;
  border: 1px solid var(--line); border-radius: 8px; background: #fff;
}
.print-facts { margin: 0; padding-left: 1.1em; color: var(--muted); font-size: 14px; }
.print-facts strong { color: var(--ink); }
.print-links { margin: 16px 0 0; font-size: 14px; }
.print-links a { margin-right: 14px; }
```

在 `@media (max-width: 820px)` 里补：

```css
  .print-grid { grid-template-columns: 1fr; }
```

把 `_stats` 换成只读构建报告：

```python
def _stats(report: dict) -> list[tuple[str, str]]:
    return [
        (f"{report['logical_pages']:,}", "个逻辑页"),
        (f"{report['parts']:,}", "篇结构"),
        (f"{report['figures'] + report['tables']:,}", "张图表"),
        (f"{report['formulas']:,}", "个公式"),
    ]
```

Replace `_landing` entirely:

```python
def _landing(version: str, date: str, html_name: str, pdf_name: str,
             cover_name: str, preview_name: str, spec_name: str,
             report_name: str, html_size: int, pdf_size: int,
             cover_size: int, stats: list[tuple[str, str]], art: str,
             author: str, report: dict) -> str:
    meta = " · ".join(part for part in (
        ("版本 " + version) if version else "", date) if part)
    meta_html = f'<p class="meta">{html.escape(meta)}</p>' if meta else ""
    stats_html = "".join(
        f"<li><strong>{html.escape(value)}</strong>"
        f"<span>{html.escape(label)}</span></li>"
        for value, label in stats)
    spine = report["cover"]["spine_mm"]
    status_text = "草稿" if report["edition_status"] == "draft" else "稳定版"
    description = html.escape(
        f"《通往模拟电路之路》16K 印刷版：{report['logical_pages']} 个逻辑页，"
        "单文件 HTML、16K 内文 PDF、含出血封面 PDF 与印刷规格，"
        "断网可读，内置全文搜索。", quote=True)
    share_title = "离线整书 · 通往模拟电路之路"
    canonical = html.escape(BOOK_URL, quote=True)
    share_image = html.escape(BOOK_URL + OG_IMAGE.name, quote=True)
    author_html = (f'<p class="cover-author">{html.escape(author)}</p>'
                   if author else "")
    author_meta = (
        f'<meta name="author" content="{html.escape(author, quote=True)}">'
        if author else "")
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light dark">
<meta name="description" content="{description}">
{author_meta}
<link rel="canonical" href="{canonical}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="通往模拟电路之路">
<meta property="og:url" content="{canonical}">
<meta property="og:title" content="{share_title}">
<meta property="og:description" content="{description}">
<meta property="og:image" content="{share_image}">
<meta property="og:image:width" content="{OG_WIDTH}">
<meta property="og:image:height" content="{OG_HEIGHT}">
<meta property="og:image:alt" content="《通往模拟电路之路》离线整书封面">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{share_title}">
<meta name="twitter:description" content="{description}">
<meta name="twitter:image" content="{share_image}">
<meta name="theme-color" content="#fffdf8" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#14181d" media="(prefers-color-scheme: dark)">
<link rel="icon" href="{FAVICON}">
<title>{share_title}</title>
<style>{LANDING_CSS}</style>
</head>
<body>
<main>
<section class="hero">
<div class="copy">
<p class="kicker">通往模拟电路之路</p>
<h1>离线整书</h1>
{meta_html}
<p class="lede">单文件 HTML、16K 内文 PDF 与印刷封面，同一本书的三种用法。断网也能排版公式、运行计算器、按 <kbd>Ctrl</kbd> + <kbd>K</kbd> 搜索全书。</p>
<ul class="stats">{stats_html}</ul>
</div>
<div class="cover-card" aria-hidden="true">
{art}
<p class="cover-title">通往模拟电路之路</p>
{author_html}
<p class="cover-meta">16K · 书脊 {spine:.1f} mm · 版本 {html.escape(version or date)}</p>
</div>
</section>
<section class="downloads" aria-labelledby="formats-title">
<h2 id="formats-title">选择格式</h2>
<div class="formats">
<a class="format" href="{html.escape(html_name)}">
<div><strong>单文件 HTML <span class="tag">推荐</span></strong><p>断网可读 · 动画与计算器可用 · Ctrl+K 全文搜索</p></div>
<span class="size">{_human_size(html_size)}</span>
</a>
<a class="format" href="{html.escape(pdf_name)}">
<div><strong>16K 内文 PDF</strong><p>185 × 260 mm · 书签跳转 · 页眉与印刷页码</p></div>
<span class="size">{_human_size(pdf_size)}</span>
</a>
<a class="format" href="{html.escape(cover_name)}">
<div><strong>印刷封面 PDF</strong><p>含 3 mm 出血与裁切线 · 书脊 {spine:.1f} mm</p></div>
<span class="size">{_human_size(cover_size)}</span>
</a>
</div>
</section>
<section class="printbox" aria-labelledby="print-title">
<h2 id="print-title">印刷与制作</h2>
<div class="print-grid">
<img class="cover-preview" src="{html.escape(preview_name)}" alt="16K 封面展开预览，含书脊与出血" loading="lazy">
<div>
<ul class="print-facts">
<li><strong>开本</strong> 185 × 260 mm（16K）</li>
<li><strong>内文</strong> {report['pdf_pages']} 页 · 80g 纯质纸 · 胶装</li>
<li><strong>书脊</strong> {spine:.1f} mm（按实际纸张打样复核）</li>
<li><strong>封面</strong> 250g 铜版纸覆哑膜 · 3 mm 出血</li>
<li><strong>状态</strong> {status_text} · 未申请 ISBN</li>
</ul>
<p class="print-links"><a href="{html.escape(cover_name)}">封面 PDF</a><a href="{html.escape(spec_name)}">印刷规格</a><a href="{html.escape(report_name)}">构建报告</a></p>
</div>
</div>
</section>
<p class="note">由内文、封面与构建报告生成 · 内容许可 CC BY-SA 4.0</p>
<footer class="back">
<a href="../index.html">返回在线站</a><span aria-hidden="true">·</span>
<a href="{REPOSITORY}">GitHub 仓库</a>
</footer>
</main>
</body>
</html>
"""
```

Replace `publish` and `main`:

```python
def publish(html_path: Path, pdf_path: Path, site_dir: Path,
            cover_pdf: Path = DEFAULT_COVER_PDF,
            cover_preview: Path = DEFAULT_COVER_PREVIEW,
            print_spec: Path = DEFAULT_PRINT_SPEC,
            report: Path = DEFAULT_REPORT) -> Path:
    artifacts = (html_path, pdf_path, cover_pdf, cover_preview,
                 print_spec, report)
    for path in artifacts:
        if not Path(path).is_file() or Path(path).stat().st_size == 0:
            raise FileNotFoundError(f"整书产物不存在或为空: {path}")
    if not (site_dir / "index.html").is_file():
        raise FileNotFoundError(f"站点产物不存在，请先构建站点: {site_dir}")
    if not OG_IMAGE.is_file():
        raise FileNotFoundError(f"社交分享图不存在: {OG_IMAGE}")
    data = json.loads(Path(report).read_text(encoding="utf-8"))
    required = ("edition_status", "logical_pages", "parts", "figures",
                "tables", "formulas", "pdf_pages", "cover")
    missing = [key for key in required if key not in data]
    if missing:
        raise ValueError(f"构建报告缺少字段: {', '.join(missing)}")
    target = site_dir / BOOK_DIR_NAME
    target.mkdir(parents=True, exist_ok=True)
    for source in artifacts:
        shutil.copy2(source, target / Path(source).name)
    shutil.copy2(OG_IMAGE, target / OG_IMAGE.name)
    document = Path(html_path).read_text(encoding="utf-8")
    version = _meta(document, "book-version")
    date = _meta(document, "book-date")
    author = _meta(document, "book-author")
    (target / "index.html").write_text(
        _landing(version, date, Path(html_path).name, Path(pdf_path).name,
                 Path(cover_pdf).name, Path(cover_preview).name,
                 Path(print_spec).name, Path(report).name,
                 Path(html_path).stat().st_size,
                 Path(pdf_path).stat().st_size,
                 Path(cover_pdf).stat().st_size,
                 _stats(data), _cover_art(), author, data),
        encoding="utf-8", newline="\n")
    return target


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--html", type=Path, default=DEFAULT_HTML)
    parser.add_argument("--pdf", type=Path, default=DEFAULT_PDF)
    parser.add_argument("--site-dir", type=Path, default=DEFAULT_SITE)
    parser.add_argument("--cover", type=Path, default=DEFAULT_COVER_PDF)
    parser.add_argument("--preview", type=Path, default=DEFAULT_COVER_PREVIEW)
    parser.add_argument("--spec", type=Path, default=DEFAULT_PRINT_SPEC)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args(argv)
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    try:
        target = publish(args.html, args.pdf, args.site_dir, args.cover,
                         args.preview, args.spec, args.report)
    except (FileNotFoundError, ValueError) as exc:
        print(f"publish error: {exc}", file=sys.stderr)
        return 1
    print(f"published {target} ({args.html.name}, {args.pdf.name}, "
          f"{args.cover.name})")
    return 0
```

别忘了在文件顶部 `import json`。

- [ ] **Step 9: 重写发布测试**

Create `scripts/test_publish_book.py`:

```python
"""16K 产物生成三种格式与印刷规格下载页（Phase 5 接入 Pages）。"""
import json
import struct
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from publish_book import BOOK_DIR_NAME, BOOK_URL, publish  # noqa: E402

BOOK_HTML = """<!doctype html>
<html><head>
<meta name="book-version" content="1.2.3">
<meta name="book-date" content="2026-10-24">
<meta name="book-author" content="zhuguang-ZFG 与贡献者">
</head><body>
<section class="book-page" data-part-title="第一篇"><img alt=""></section>
<section class="book-page" data-part-title="第一篇"><span class="arithmatex"></span></section>
</body></html>
"""

REPORT = {
    "schema": 1, "edition_status": "draft", "version": "1.2.3",
    "logical_pages": 2, "parts": 1, "figures": 1, "tables": 0,
    "formulas": 1, "pdf_pages": 4,
    "cover": {"spine_mm": 1.2, "size_mm": [376.0, 266.0]},
}


class PublishBookTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.site = self.root / "site"
        self.site.mkdir()
        (self.site / "index.html").write_text(
            "<!doctype html><title>site</title>", encoding="utf-8")
        self.html = self.root / "analog-circuit-book.html"
        self.html.write_text(BOOK_HTML, encoding="utf-8")
        self.pdf = self.root / "analog-circuit-book.pdf"
        self.pdf.write_bytes(b"%PDF-1.7\n" + b"0" * 4096)
        self.cover_pdf = self.root / "cover.pdf"
        self.cover_pdf.write_bytes(b"%PDF-1.7\n" + b"1" * 1024)
        self.cover_preview = self.root / "cover-preview.png"
        self.cover_preview.write_bytes(b"\x89PNG\r\n\x1a\n" + b"2" * 512)
        self.print_spec = self.root / "PRINT-SPEC.md"
        self.print_spec.write_text(
            "# 印刷规格\n\n16K 185 × 260 mm\n", encoding="utf-8")
        self.report = self.root / "build-report.json"
        self.report.write_text(
            json.dumps(REPORT, ensure_ascii=False), encoding="utf-8")

    def publish(self):
        return publish(self.html, self.pdf, self.site, self.cover_pdf,
                       self.cover_preview, self.print_spec, self.report)

    def test_copies_artifacts_and_writes_landing_page(self):
        target = self.publish()
        self.assertEqual(self.site / BOOK_DIR_NAME, target)
        for name in ("analog-circuit-book.html", "analog-circuit-book.pdf",
                     "cover.pdf", "cover-preview.png", "PRINT-SPEC.md",
                     "build-report.json", "og-cover.png"):
            self.assertTrue((target / name).is_file(), name)
        landing = (target / "index.html").read_text(encoding="utf-8")
        for text in ("离线整书", "1.2.3", "2026-10-24", "16K",
                     "185 × 260 mm", "1.2 mm",
                     'href="analog-circuit-book.html"',
                     'href="analog-circuit-book.pdf"',
                     'href="cover.pdf"', 'href="PRINT-SPEC.md"',
                     'href="build-report.json"', "4 KB",
                     'href="../index.html"'):
            self.assertIn(text, landing)
        self.assertNotIn("A4 PDF", landing)

    def test_landing_shows_cover_stats_and_share_metadata(self):
        target = self.publish()
        landing = (target / "index.html").read_text(encoding="utf-8")
        self.assertIn('class="cover-card"', landing)
        self.assertIn("<svg", landing)
        self.assertIn("cover-dots", landing)
        self.assertIn("zhuguang-ZFG 与贡献者", landing)
        self.assertIn('<meta name="author" content="zhuguang-ZFG 与贡献者">',
                      landing)
        for label in ("个逻辑页", "篇结构", "张图表", "个公式"):
            self.assertIn(label, landing)
        self.assertEqual(1, landing.count("<strong>2</strong>"),
                         "两页同属一篇")
        self.assertEqual(3, landing.count("<strong>1</strong>"),
                         "一篇、一张图、一个公式")
        self.assertIn("单文件 HTML", landing)
        self.assertIn("16K 内文 PDF", landing)
        self.assertIn("印刷封面 PDF", landing)
        self.assertIn("印刷规格", landing)
        self.assertIn("构建报告", landing)
        self.assertIn('<img class="cover-preview" src="cover-preview.png"',
                      landing)
        self.assertIn('name="description"', landing)
        self.assertIn('property="og:title"', landing)
        self.assertIn('rel="icon"', landing)
        self.assertIn("prefers-color-scheme: dark", landing)
        self.assertIn(f'<link rel="canonical" href="{BOOK_URL}">', landing)
        self.assertIn(f'property="og:url" content="{BOOK_URL}"', landing)
        self.assertIn(
            f'property="og:image" content="{BOOK_URL}og-cover.png"', landing)
        self.assertIn('property="og:image:width" content="1200"', landing)
        self.assertIn('property="og:image:height" content="630"', landing)
        self.assertIn('property="og:image:alt"', landing)
        self.assertIn('name="twitter:card" content="summary_large_image"',
                      landing)
        self.assertIn(
            f'name="twitter:image" content="{BOOK_URL}og-cover.png"', landing)
        image = (target / "og-cover.png").read_bytes()
        self.assertEqual(b"\x89PNG\r\n\x1a\n", image[:8])
        self.assertEqual((1200, 630), struct.unpack(">II", image[16:24]))

    def test_rejects_missing_artifact(self):
        self.pdf.unlink()
        with self.assertRaises(FileNotFoundError):
            self.publish()

    def test_rejects_missing_cover(self):
        self.cover_pdf.unlink()
        with self.assertRaises(FileNotFoundError):
            self.publish()

    def test_rejects_missing_site_index(self):
        (self.site / "index.html").unlink()
        with self.assertRaises(FileNotFoundError):
            self.publish()

    def test_rejects_report_without_required_fields(self):
        self.report.write_text(json.dumps({"edition_status": "draft"}),
                               encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "构建报告缺少字段"):
            self.publish()


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 10: 运行发布测试**

```bash
python -B -m unittest discover -s scripts -p "test_publish_book.py" -v
```

Expected: PASS (6 tests)。若统计数不是 2/1/1/1，检查报告 fixture 的 `logical_pages/parts/figures+tables/formulas`，不要退回从 HTML 数 `<img>`。

---

- [ ] **Step 11: 更新 16K CI 与发布边界门**

Modify `.github/workflows/book-print.yml`：在 `print16k` job 的 `16K 内文与封面` 之后加

```yaml
      - name: 构建报告与印刷规格
        if: github.event_name != 'pull_request'
        run: python analog-book/build_print_book.py --no-build --report
```

`book-print.yml` 独立于 Pages，`book.yml` 不动；`pages.yml` 的部署验证清单仍只验证 A4 1.0。在 `16K 单元、装配与真实内容` 之后加 16K 发布器测试：

```yaml
      - name: 16K 发布器测试
        run: python -B -m unittest discover -s scripts -p "test_publish_book.py" -v
```

按归属拆开仍指向旧发布器的入口，避免 16K 测试重新耦合 A4：

`.github/workflows/tests.yml` 的 `site-build` job（被 Pages 调用）只跑 A4 发布器测试：

```yaml
      - run: python -B -m unittest discover -s scripts -p test_publish_a4_book.py -v
```

`Makefile` 的 `test-static`（本地，不 gate Pages）两个都跑：

```make
	$(PY) -B -m unittest discover -s scripts -p "test_publish_a4_book.py" -v
	$(PY) -B -m unittest discover -s scripts -p "test_publish_book.py" -v
```

把 `analog-book/READING-FLOW.md` 中提到 `scripts/publish_book.py` 的 A4 发布说明改为 `scripts/publish_a4_book.py`；不要在这份文档里宣称 16K 已上线。

Modify `scripts/test_release_gate.py`：

1. `test_pages_publishes_the_book_artifact_built_by_the_gated_job` 里把发布命令断言改为 `scripts/publish_a4_book.py`。
2. 新增：

```python
    def test_expansion_keeps_a4_online_and_16k_draft_off_pages(self):
        pages = _jobs('pages')
        runs = "\n".join(
            step.get('run', '') for step in pages['build']['steps'])
        self.assertIn('scripts/publish_a4_book.py', runs)
        self.assertNotIn('scripts/publish_book.py', runs)
        deploy_runs = "\n".join(
            step.get('run', '') for step in pages['deploy']['steps'])
        for forbidden in ('cover.pdf', 'cover-preview.png',
                          'PRINT-SPEC.md', 'build-report.json'):
            self.assertNotIn(forbidden, deploy_runs)

        pages_text = (WORKFLOWS / 'pages.yml').read_text(encoding='utf-8')
        self.assertNotIn('book-print', pages_text,
                         '16K 失败不得阻断 A4 Pages')

        tests_runs = "\n".join(
            step.get('run', '') for job in _jobs('tests').values()
            for step in job.get('steps', []))
        self.assertIn('test_publish_a4_book.py', tests_runs)
        self.assertNotIn('test_publish_book.py', tests_runs)

        book = _jobs('book-print')
        self.assertIn('print16k', book)
        upload = _step(book, 'print16k', 'actions/upload-artifact@')
        self.assertEqual('analog-circuit-book-16k-draft',
                         upload['with']['name'])
        self.assertEqual('analog-book/dist/print/', upload['with']['path'])
        runs16 = "\n".join(
            step.get('run', '') for step in book['print16k']['steps'])
        self.assertIn('build_print_book.py', runs16)
        for flag in ('--pdf', '--cover', '--report'):
            self.assertIn(flag, runs16)
        workflow = yaml.load(
            (WORKFLOWS / 'book-print.yml').read_text(encoding='utf-8'),
            Loader=yaml.BaseLoader)
        self.assertNotIn('workflow_call', workflow['on'])
```

- [ ] **Step 12: 全量回归**

```bash
python scripts/build_site.py --build
python -B -m unittest discover -s analog-book/tests -p "test_book_*.py" -v
python -B -m unittest discover -s analog-book/tests -p "test_spice.py" -v
python -B -m unittest discover -s analog-book/tests -p "test_build.py" -v
python -B -m unittest discover -s analog-book/tests -p "test_pdf.py" -v
python -B -m unittest discover -s scripts -p "test_publish_a4_book.py" -v
python -B -m unittest discover -s scripts -p "test_publish_book.py" -v
python -B -m unittest discover -s scripts -p "test_release_gate.py" -v
python analog-book/build_print_book.py --sample
python analog-book/build_print_book.py --no-build
python analog-book/build_print_book.py --check --no-build
python analog-book/build_print_book.py --no-build --pdf --cover
python analog-book/build_print_book.py --no-build --report
python analog-book/build_book.py --no-build
python analog-book/build_book.py --check --no-build
python -B -m unittest discover -s analog-book/tests -p "test_browser_book.py" -v
python -B -m unittest discover -s analog-book/tests -p "test_browser_print_book.py" -v
```

Expected:
- 所有单元、装配、真实内容、PDF、封面、报告、SPICE、A4 发布、16K 发布与发布门测试 PASS；没有 ngspice 时 SPICE 只跳过，但不得声称已验证。
- `analog-book/dist/` 仍有 A4 1.0 HTML/PDF；`analog-book/dist/print/` 含 16K HTML、PDF、`cover.pdf`、`cover-preview.png`、`PRINT-SPEC.md`、`build-report.json`、`book-model.json`、`sample/`。
- 16K PDF 页数为 4 的倍数；目录、插图目录、索引无 `000`；书签层级 1–3 正常。
- `PRINT-SPEC.md` 的书脊公式、封面尺寸与报告一致；报告里的 `mirrored` 来自样张而不是猜测。
- A4 与 16K 浏览器回归各 5 项 PASS。
- 草稿警告可以存在；结构错误、坏锚点、重复 ID、远程资源必须为 0。
- `pages.yml` 仍只发布 A4 1.0；`publish_book.py` 的 16K 落地页只被单元测试调用。

- [ ] **Step 13: 提交**

```bash
git add analog-book/book/report.py analog-book/tests/test_book_report.py \
  analog-book/STYLE.md analog-book/book/cli.py \
  scripts/publish_book.py scripts/publish_a4_book.py \
  scripts/test_publish_book.py scripts/test_publish_a4_book.py \
  scripts/test_release_gate.py .github/workflows/book-print.yml \
  .github/workflows/pages.yml .github/workflows/tests.yml Makefile \
  analog-book/READING-FLOW.md
git commit -m "feat(book): add build report and stage the 16K publisher"
```

不要推送。推送前按仓库约定执行安全审查门；发现的问题先修复，不得跳过。

### Task 12 post-review amendments（已落分支 `395946c`）

最终整支审查发现并已修复的事实偏差（ledger 有完整记录）：

- `check_pdf` 返回实际内文 `size_mm`；报告新增 `pdf_warnings`、`preflight`、`interior_size_mm`；PRINT-SPEC 第 2/3/8/9 节分别写实际 MediaBox、是/否、印前全检与 PDF 警告；字体表含印章字体。
- 长表允许跨页并重复表头（`.book .book-table` 与 `.table-wrap` 为 `break-inside: auto`），内文 528 → 496 页，书脊 27.40 → 25.80 mm，封面 403.27×266.02 → 401.83×266.02 mm。
- STYLE 证据等级与 `docs/p0-11-conventions.md` 一致；背封“参数扫描”改为“可复现仿真”；`p1-00-part1.md` 排除原因改为第 I 篇；README 增加 16K 小节；`--sample` 帮助改十页。
- 报告测试的 `COVER.pages` 改为 1，使 `cover.pages == pdf_pages` 的断言真正区分来源；新增 CSS↔报告几何、长表分页、证据等级三项测试（共 9 项）。
- 偏离：简报的 `[185.0, 260.0]` 精确断言与 Chromium 实际 `184.83 × 260.01` 冲突，改用 ±0.5 mm 容差。
- 真实产物：496 页、内文 184.83×260.01 mm、书脊 25.80 mm、封面 401.83×266.02 mm；全套 254 tests OK（3 个 ngspice skip）。

---

## Phase 0 完成定义

> 状态（2026-10-26）：已完成，HEAD `395946c`（34 commits，base `6a2c8c9`）。证据、修复轮与遗留项见 `.superpowers/sdd/2026-10-25-print-book-phase0/progress.md`。

Phase 0 只交付“能稳定生产一本书”的机器，不交付最终书稿。全部满足才算完成：

- [ ] `analog-book/manifest.json` 为 schema 2，覆盖 64 个 `docs/` 页面：54 个直入、10 个明确排除；书内 77 个逻辑页；A4 1.0 的 `manifest-a4.json` 已冻结，旧构建器与旧测试继续通过。
- [ ] 新增的三页 `p0-11-conventions.md`、`p0-12-symbols.md`、`p9-15-glossary.md` 已进入站点与 16K 书，站点导航与回归断言同步；根 `README.md` 已由 `scripts/build_readme.py` 重建并通过同步测试；A4 1.0 仍按冻结 manifest 构建。
- [ ] 16K 样张证明 185×260mm、145×218mm 版心、镜像边距与九类版式不溢出。
- [ ] 整书 HTML 无站点外壳、无 emoji、无 `<details>`、无远程资源；ID 唯一、站内锚点全通；`figures.yml`/`tables.yml` 由 `lof`/`lot` 导出，字段与设计规范一致。
- [ ] 19 章题进入章末，58 道章节题与 34 道专题题答案只进附录 F；附录 F 每条章节答案都有回链指向章末原题。
- [ ] 16K PDF 补白到 4 的倍数，页码标签、页眉页脚、三级书签、`000` 回填与索引全部通过。
- [ ] 印刷封面按实际页数算书脊，含出血与裁切线；未申请 ISBN 时封面不出现假 ISBN/条码。
- [ ] `PRINT-SPEC.md` 与 `build-report.json` 由实际产物生成；草稿明确列出未关闭的质量门。
- [ ] `book.yml` 的 A4 job 保持独立；`book-print.yml` 单独运行 `print16k`，不被 `pages.yml` 调用，16K 失败不阻断 A4 发布；真实内容、SPICE、PDF、封面、报告与两条浏览器回归全部纳入。
- [ ] 16K 草稿只上传 `analog-circuit-book-16k-draft` artifact；`pages.yml` 仍下载 A4 `analog-circuit-book`、调用 `publish_a4_book.py`，`/book/` 的部署验证清单不变。
- [ ] `publish_book.py` 是 16K 发布器并有完整测试，但 Phase 0 不接入 Pages；站点印刷版入口、README 与 `/book/` 切换留到 Phase 5。
- [ ] `release.edition_status` 仍为 `draft`；页数不足、字数不足、索引/文献/审读不足只产生 warning。
- [ ] 没有任何伪造的实测数据、文献、ISBN、厂商模型或“已审读”声明。

Phase 0 之后才进入内容波次：Wave 1（第 0、2、11、14、16 章）、Wave 2（第 1、3、12、15、17 章）、Wave 3（第 4、6、13、18 章）、Wave 4（第 5、7、8、9、10 章）、Phase 5（附录、索引、封面打样与 2.0 稳定版）。每波单独出计划、单独验收，不能把内容扩写塞进本计划。
