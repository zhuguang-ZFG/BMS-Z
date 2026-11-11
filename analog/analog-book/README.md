# 离线整书

从 `docs/` 构建《通往模拟电路之路》的单文件 HTML 与 A4 PDF。内容源仍在 `docs/`，本目录只放构建器、清单与样式。

**直接下载**：

- GitHub Pages：<https://zhuguang-zfg.github.io/analog-circuit-roadmap/book/>（每次 main 分支构建自动更新）
- 国内镜像：<https://aliyun-hutuji.donglicao.com/analog-circuit-roadmap/book/>（每 6 小时同步）

## 构建

在仓库根目录运行：

```bash
pip install -r requirements.txt -r analog-book/requirements.txt
python -m playwright install chromium   # 也可复用本机 Edge / Chrome
python analog-book/build_book.py        # 站点 + HTML
python analog-book/build_book.py --pdf  # 追加 PDF
python analog-book/build_book.py --check --no-build  # 只审计已有产物
```

Windows 上装了 GNU Make 时可用 `make book` / `make book-pdf` / `make book-check`；本仓库用 `mingw32-make` 验证。

- 默认调用 `scripts/build_site.py --build`；`--no-build` 复用 `build/site`。自定义 `--site-dir` 只能配合 `--no-build`。
- 产物在 `analog-book/dist/`（gitignored）：`analog-circuit-book.html`、`analog-circuit-book.pdf`。
- 新增/删除内容页必须同步 `manifest.json`（16K，输出 `dist/print/`），否则 16K 整书审计失败。A4 1.0 已冻结在 `manifest-a4.json`（输出 `dist/`），Phase 5 前不再改。
- 书内禁止远程图片、外链样式/脚本、iframe/video；第三方资产先本地化并登记 `docs/p9-14-credits.md`。
- 页眉内置离线全文搜索：`Ctrl/Cmd+K` 或 `/` 聚焦，方向键选择、回车跳转；索引在首次输入时从正文构建，不增加网络依赖。
- Mermaid 路线图使用 `static/roadmap.svg`；改 `docs/p0-06-roadmap.md` 后必须重新生成 `roadmap.source.txt` / `roadmap.svg`。
- 缺 Playwright/PyMuPDF 时 HTML 仍可构建；PDF 相关测试自动 skip。
- PDF 默认优先本机 Edge/Chrome，找不到时回退 Playwright 自带 Chromium；可用 `--browser <path>` 指定浏览器。
- 审计会检查远程资源、重复 ID、跨页锚点、页面数与 24 MB 体积上限（2026-11-10 印规修订：20→24，V4 wave 合并后实测 21.46MB，owner 批准）；`--check` 不重新构建。

## 16K 印刷版

16K（185 × 260 mm）印刷版与 A4 1.0 共用 `docs/`，但使用独立的
`manifest.json`，产物写到 `analog-book/dist/print/`（gitignored）：

```bash
python analog-book/build_print_book.py --sample   # 十页样张
python analog-book/build_print_book.py --pdf --cover
python analog-book/build_print_book.py --no-build --report
```

`PRINT-SPEC.md` 与 `build-report.json` 从已有产物生成；Phase 0 的 16K 只上传
CI artifact，`/book/` 仍由 A4 1.0 发布。

### 上下卷

整书 16K 单卷排到 812 页，超过 `book/pdf.py` 的 700 页硬上限。上限不动，改为按
自然篇界出两卷：

```bash
python analog-book/build_print_book.py --volumes --pdf --no-build   # make print-volumes
```

产物在 `dist/print/volume-1/`、`dist/print/volume-2/`：

| 卷 | 内容 | HTML | PDF |
|---|---|---:|---:|
| 上卷 | 前置页 + 第 I～II 篇（第 0～10 章）+ 参考文献 + 索引 | 26 逻辑页 / 9,258,758 B | 336 页 / 16,757,100 B |
| 下卷 | 前置页 + 第 III 篇起（第 11～18 章、附录 A～H）+ 参考文献 + 索引 | 64 逻辑页 / 10,477,528 B | 516 页 / 22,924,788 B |

分卷是重新装配而非截断：`assemble.build_html(volume=…)` 先选页再重编页序，目录、
插图目录、表格目录与索引都按本卷重算，索引只收本卷可见锚点。指向另一卷的锚点降级为
「（见上卷/见下卷）」提示，因此分卷审计不会出现悬空锚点。参考文献与索引两卷都带。

`--volumes` 暂不支持 `--cover` / `--report`；站点只在上卷构建时重建一次。

## 阅读体验

- 每页页尾提供上一篇 / 下一篇，按整书顺序跨篇连续翻页，中间按钮回到全书目录。
- 正文链接带下划线，键盘焦点与文本选区有明确视觉反馈；手机端翻页收成两行。
- 页眉保留搜索（`Ctrl/Cmd+K`、`/`）、阅读进度与回到顶部；这些交互不依赖网络。

完整变更记录见 [`READING-FLOW.md`](READING-FLOW.md)。

## 测试

```bash
python -B -m unittest discover -s analog-book/tests -p test_build.py -v
python -B -m unittest discover -s analog-book/tests -p test_browser_book.py -v
python -B -m unittest discover -s analog-book/tests -p test_pdf.py -v
```

`test_browser_book.py` 需要 Playwright 与可用的 Chromium/Chrome；`test_pdf.py` 需要先生成 PDF 和 PyMuPDF。

设计说明见 [`../docs/superpowers/specs/2026-10-24-offline-book-and-repo-polish-design.md`](../docs/superpowers/specs/2026-10-24-offline-book-and-repo-polish-design.md)，实施计划见 [`../docs/superpowers/plans/2026-10-24-offline-book-and-repo-polish.md`](../docs/superpowers/plans/2026-10-24-offline-book-and-repo-polish.md)。
