# 离线整书与仓库工程化实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 `analog-circuit-roadmap` 中交付单文件离线 HTML 整书与 A4 PDF，并补齐图片来源、许可登记、首页直查、Makefile、统计与 CI，使 `docs/` 仍是唯一内容源。

**Architecture:** 新建 `analog-book/` 作为构建子系统：`build_book.py` 调用现有 `scripts/build_site.py --build` 生成站点，再抽取每页 `<article>`，清洗站点专属 DOM、命名空间化 ID、重写链接、内嵌图片/CSS/JS/MathJax SVG，拼成 60 页单文件 HTML；Playwright 以 `file://` 打印 PDF，PyMuPDF 写元数据、书签、页眉页码与目录页码。站点与阅读体验的改动全部先落在 `docs/`，README 由 `scripts/build_readme.py` 重建。

**Tech Stack:** Python 3.12+（stdlib `re`/`html`/`base64`/`argparse`）、MkDocs Material（现有站点构建）、MathJax 3.2.2 SVG、Playwright Chromium、PyMuPDF 1.28、unittest、GitHub Actions、GNU Make（CI）/`mingw32-make`（本机）。

**Spec:** `docs/superpowers/specs/2026-10-24-offline-book-and-repo-polish-design.md`

## Global Constraints

- **不执行 git commit / push / reset / clean**，除非用户明确要求；本计划的步骤一律不含提交动作。
- **不得改动** `video/remotion/` 下的未提交改动与 `social-auto-upload/`；构建产物只写入 `build/`、`analog-book/dist/`、临时目录。
- `docs/` 是唯一内容源；README 只能由 `scripts/build_readme.py` 生成，禁止手改。
- 书内页面只收录 manifest 列出的 60 个内容页；`docs/index.md` 不进书。
- 书内禁止 `<iframe>`、`<video>`、`<script src>`、`<link rel="stylesheet">`、远程 `<img>`；图片全部 data URI；任何未知远程图片直接构建失败。
- 所有内部 `href="#..."` 必须在整书中真实存在；未知目标直接构建失败，不允许静默死链。
- HTML 体积硬上限 20 MB；超过即失败并报告最大资源。
- 构建必须确定性：相同输入连续两次生成字节级相同的 HTML。
- 现有测试必须全绿；新增测试用 `python -B -m unittest discover -s ...` 运行。
- Windows 本机命令用 `python`，CI 用 `python`/`make`；本机没有 `make` 时用 `mingw32-make`。

---

## File Structure

```text
analog-book/
├── README.md                     # 构建方式、依赖、范围、发布说明
├── manifest.json                 # 书目元数据 + 篇/页顺序（60 页）
├── requirements.txt              # Playwright、PyMuPDF
├── build_book.py                 # 站点构建 → HTML → 审计 → PDF
├── styles/book.css               # 书版式 + 打印样式（构建时内联）
├── static/
│   ├── roadmap.source.txt        # Mermaid 源码快照（与 docs/p0-06 比对）
│   └── roadmap.svg               # 预渲染静态路线图
├── tests/
│   ├── test_build.py             # 单元 + 整书审计
│   └── test_pdf.py               # 浏览器/PDF 结构校验（缺依赖 skip）
└── dist/                         # 构建产物（gitignore）

assets/vendor/mathjax-svg/        # tex-svg-full.js + README + LICENSE
assets/photos/web/                # 22 张章节配图
docs/p9-14-credits.md             # 来源与许可唯一内容源
CREDITS.md                        # 根目录简短索引
.github/workflows/book.yml        # 整书 CI
Makefile                          # 顶层命令入口
scripts/build_stats.py            # make stats
```

---

### Task 1: 图片本地化与来源许可登记

**Files:**
- Create: `assets/photos/web/*.jpg|png`（22 个）
- Modify: `docs/p1-02-ch1.md`、`p1-03-ch2.md`、`p1-04-ch3.md`、`p1-07-ch6.md`、`p1-10-ch9.md`、`p1-11-ch10.md`、`p2-03-ch13.md`、`p3-02-ch15.md`、`p4-01-ch16.md`、`p6-01-s6-1.md`
- Create: `docs/p9-14-credits.md`
- Create: `CREDITS.md`
- Modify: `assets/photos/README.md`
- Modify: `docs/p9-13-thanks.md`
- Modify: `scripts/build_site.py:617`
- Test: `scripts/test_docs_links.py`

**Interfaces:**
- Produces: 站点/README/整书共用的本地照片路径 `assets/photos/web/<name>`；唯一授权清单 `docs/p9-14-credits.md`；`build_site.APPENDIX` 含 `p9-14-credits.md`。

- [ ] **Step 1: 写失败测试（docs 远程图片只允许 YouTube 缩略图）**

在 `scripts/test_docs_links.py` 末尾的 `DocsLinks` 类中追加三个方法（放在 `test_numbered_section_links_point_to_the_same_chapter` 之后，保持缩进）：

```python
    REMOTE_IMG = re.compile(r'<img[^>]+src="(https?://[^"]+)"')
    ALLOWED_REMOTE_IMG = re.compile(
        r"https://img\.youtube\.com/vi/[\w-]+/[a-z]+\.jpg")
    LOCAL_PHOTO_IMG = re.compile(r'<img[^>]+src="(assets/photos/[^"]+)"')

    def test_only_youtube_thumbnails_may_stay_remote(self):
        bad = []
        for page in self.pages:
            for url in self.REMOTE_IMG.findall(page.read_text(encoding="utf-8")):
                if not self.ALLOWED_REMOTE_IMG.fullmatch(url):
                    bad.append(f"{page.name}: {url}")
        self.assertEqual([], bad,
                         "远程图片必须本地化到 assets/photos/：\n" + "\n".join(bad[:10]))

    def test_local_photo_references_exist(self):
        missing = []
        for page in self.pages:
            for rel in self.LOCAL_PHOTO_IMG.findall(page.read_text(encoding="utf-8")):
                if not (ROOT / rel).is_file():
                    missing.append(f"{page.name}: {rel}")
        self.assertEqual([], missing,
                         "引用了不存在的照片：\n" + "\n".join(missing[:10]))

    def test_credits_page_lists_every_web_photo(self):
        credits = (DOCS / "p9-14-credits.md").read_text(encoding="utf-8")
        photos = sorted(p.name for p in (ROOT / "assets/photos/web").glob("*"))
        missing = [name for name in photos if name not in credits]
        self.assertEqual([], missing, f"来源页漏登记：{missing[:10]}")
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python -B -m unittest discover -s scripts -p test_docs_links.py -v`
Expected: FAIL（`test_only_youtube_thumbnails_may_stay_remote` 报 23 个 Wikimedia URL；`test_local_photo_references_exist` 通过；`test_credits_page_lists_every_web_photo` 因文件不存在报错）。

- [ ] **Step 3: 落地 22 张照片**

临时下载目录 `D:/Temp/User/tmp_xe8vtya/` 中已有全部文件；若缺失，按下面 URL 重新下载（Git Bash）：

```bash
mkdir -p assets/photos/web
C="curl --ssl-no-revoke -L -A 'analog-circuit-roadmap/1.0 (build; contact: repo owner)'"
base=https://upload.wikimedia.org/wikipedia/commons
$C -o assets/photos/web/2n2222a-and-schema.jpg "$base/5/5e/2N2222A_and_schema.jpg"
$C -o assets/photos/web/400-points-breadboard.jpg "$base/7/73/400_points_breadboard.jpg"
$C -o assets/photos/web/die-first-555-chip.jpg "$base/c/c3/Die_of_the_first_555_chip.jpg"
$C -o assets/photos/web/digital-multimeter-aka.jpg "$base/a/a6/Digital_Multimeter_Aka.jpg"
$C -o assets/photos/web/diode-closeup.jpg "$base/thumb/d/d5/Diode-closeup.jpg/500px-Diode-closeup.jpg"
$C -o assets/photos/web/electrolytic-exploded.jpg "$base/thumb/c/c2/ElectrolyticCapacitorExploded.jpg/500px-ElectrolyticCapacitorExploded.jpg"
$C -o assets/photos/web/electrolytic-capacitors.jpg "$base/f/f6/Electrolytic_capacitors-P1090328.JPG"
$C -o assets/photos/web/generic-2n2222a.jpg "$base/thumb/d/d4/Generic_2N2222A.jpeg/500px-Generic_2N2222A.jpeg"
$C -o assets/photos/web/mosfet-jcs4n65f.jpg "$base/thumb/3/39/Jilin_Sino-Microelectronics_JCS4N65F-2383.jpg/500px-Jilin_Sino-Microelectronics_JCS4N65F-2383.jpg"
$C -o assets/photos/web/led-5mm-rgb.jpg "$base/thumb/0/0a/LED_5mm_RGB.jpg/500px-LED_5mm_RGB.jpg"
$C -o assets/photos/web/buck-converter-modules.jpg "$base/thumb/6/66/LM2596_buck_converter_module%2C_MP1584_buck_converter_module%2C_and_SDB628_boost_converter_module.jpg/960px-LM2596_buck_converter_module%2C_MP1584_buck_converter_module%2C_and_SDB628_boost_converter_module.jpg"
$C -o assets/photos/web/lm555-timer.jpg "$base/9/94/LM555-555-Timer_5734-480x452_%284791854328%29.jpg"
$C -o assets/photos/web/macro-circuit-board.jpg "$base/thumb/c/c4/Macro_circuit_board.JPG/500px-Macro_circuit_board.JPG"
$C -o assets/photos/web/scanned-multimeter-gossen.jpg "$base/thumb/2/24/Multimeter_Gossen_Metra_Hit.jpg/500px-Multimeter_Gossen_Metra_Hit.jpg"
$C -o assets/photos/web/ne555-dip-soic.jpg "$base/6/64/NE555_DIP_%26_SOIC.jpg"
$C -o assets/photos/web/oscilloscope-front-panel.png "$base/8/8a/Oscilloscope_Front_Panel_Numbered.svg"
$C -o assets/photos/web/printed-circuit-board.jpg "$base/thumb/0/0b/Printed_circuit_board.jpg/500px-Printed_circuit_board.jpg"
$C -o assets/photos/web/soldering-0805.jpg "$base/thumb/f/f8/Soldering_a_0805.jpg/500px-Soldering_a_0805.jpg"
$C -o assets/photos/web/ts7805-regulator.jpg "$base/thumb/d/d8/TS7805_voltage_regulator.JPG/500px-TS7805_voltage_regulator.JPG"
$C -o assets/photos/web/transistors-cropped.jpg "$base/thumb/2/21/Transistorer_%28cropped%29.jpg/500px-Transistorer_%28cropped%29.jpg"
$C -o assets/photos/web/4-band-resistor.png "$base/6/6e/4-Band_Resistor.svg"
$C -o assets/photos/web/digital-oscilloscope.jpg "$base/thumb/0/0b/Digital_oscilloscope_in_use.jpg/500px-Digital_oscilloscope_in_use.jpg"
```

若临时目录仍在，直接复制（更快且与已核对文件逐字节一致）：

```bash
mkdir -p assets/photos/web
cp /d/Temp/User/tmp_xe8vtya/2N2222A-and-schema.jpg        assets/photos/web/2n2222a-and-schema.jpg
cp /d/Temp/User/tmp_xe8vtya/400-points-breadboard.jpg     assets/photos/web/400-points-breadboard.jpg
cp /d/Temp/User/tmp_xe8vtya/Die-of-the-first-555-chip.jpg assets/photos/web/die-first-555-chip.jpg
cp /d/Temp/User/tmp_xe8vtya/Digital-Multimeter-Aka.jpg    assets/photos/web/digital-multimeter-aka.jpg
cp /d/Temp/User/tmp_xe8vtya/Digital-oscilloscope-in-use.jpg assets/photos/web/digital-oscilloscope.jpg
cp /d/Temp/User/tmp_xe8vtya/Diode-closeup.jpg             assets/photos/web/diode-closeup.jpg
cp /d/Temp/User/tmp_xe8vtya/ElectrolyticCapacitorExploded.jpg assets/photos/web/electrolytic-exploded.jpg
cp /d/Temp/User/tmp_xe8vtya/Electrolytic-capacitors-P1090328.JPG assets/photos/web/electrolytic-capacitors.jpg
cp /d/Temp/User/tmp_xe8vtya/Generic-2N2222A.jpeg          assets/photos/web/generic-2n2222a.jpg
cp /d/Temp/User/tmp_xe8vtya/Jilin-Sino-Microelectronics-JCS4N65F-2383.jpg assets/photos/web/mosfet-jcs4n65f.jpg
cp /d/Temp/User/tmp_xe8vtya/LED-5mm-RGB.jpg               assets/photos/web/led-5mm-rgb.jpg
cp /d/Temp/User/tmp_xe8vtya/LM2596-buck-converter-module-MP1584-buck-converter-module-and-SDB628-boost-converter-module.jpg assets/photos/web/buck-converter-modules.jpg
cp /d/Temp/User/tmp_xe8vtya/LM555-555-Timer-5734-480x452-4791854328-.jpg assets/photos/web/lm555-timer.jpg
cp /d/Temp/User/tmp_xe8vtya/Macro-circuit-board.JPG       assets/photos/web/macro-circuit-board.jpg
cp /d/Temp/User/tmp_xe8vtya/Multimeter-Gossen-Metra-Hit.jpg assets/photos/web/scanned-multimeter-gossen.jpg
cp /d/Temp/User/tmp_xe8vtya/NE555-DIP-SOIC.jpg            assets/photos/web/ne555-dip-soic.jpg
cp /d/Temp/User/tmp_xe8vtya/Oscilloscope-Front-Panel-Numbered.png assets/photos/web/oscilloscope-front-panel.png
cp /d/Temp/User/tmp_xe8vtya/Printed-circuit-board.jpg     assets/photos/web/printed-circuit-board.jpg
cp /d/Temp/User/tmp_xe8vtya/Soldering-a-0805.jpg          assets/photos/web/soldering-0805.jpg
cp /d/Temp/User/tmp_xe8vtya/TS7805-voltage-regulator.JPG  assets/photos/web/ts7805-regulator.jpg
cp /d/Temp/User/tmp_xe8vtya/Transistorer-cropped-.jpg     assets/photos/web/transistors-cropped.jpg
cp /d/Temp/User/tmp_xe8vtya/4-Band-Resistor.png           assets/photos/web/4-band-resistor.png
```

- [ ] **Step 4: 改写 10 个 docs 页面里的 URL**

按下表做精确字符串替换（只换 `src`，`<img>` 其余属性、`<a href>` 原样保留）：

| 页面 | 远程 URL（唯一片段） | 本地路径 |
|---|---|---|
| p1-02-ch1.md | `upload.wikimedia.org/wikipedia/commons/8/86/Photo-SMDcapacitors.jpg` | `assets/photos/capacitors.jpg` |
| p1-02-ch1.md | `thumb.wikimedia.org/.../f/f8/Soldering_a_0805.jpg/500px-Soldering_a_0805.jpg` | `assets/photos/web/soldering-0805.jpg` |
| p1-02-ch1.md | `thumb.wikimedia.org/.../c/c2/ElectrolyticCapacitorExploded.jpg/500px-ElectrolyticCapacitorExploded.jpg` | `assets/photos/web/electrolytic-exploded.jpg` |
| p1-03-ch2.md | `thumb.wikimedia.org/.../d/d5/Diode-closeup.jpg/500px-Diode-closeup.jpg` | `assets/photos/web/diode-closeup.jpg` |
| p1-04-ch3.md | `thumb.wikimedia.org/.../d/d4/Generic_2N2222A.jpeg/500px-Generic_2N2222A.jpeg` | `assets/photos/web/generic-2n2222a.jpg` |
| p1-04-ch3.md | `upload.wikimedia.org/wikipedia/commons/5/5e/2N2222A_and_schema.jpg` | `assets/photos/web/2n2222a-and-schema.jpg` |
| p1-10-ch9.md | `thumb.wikimedia.org/.../d/d8/TS7805_voltage_regulator.JPG/500px-TS7805_voltage_regulator.JPG` | `assets/photos/web/ts7805-regulator.jpg` |
| p1-11-ch10.md | `upload.wikimedia.org/wikipedia/commons/9/94/LM555-555-Timer_5734-480x452_%284791854328%29.jpg` | `assets/photos/web/lm555-timer.jpg` |
| p1-11-ch10.md | `upload.wikimedia.org/wikipedia/commons/6/64/NE555_DIP_%26_SOIC.jpg` | `assets/photos/web/ne555-dip-soic.jpg` |
| p1-11-ch10.md | `upload.wikimedia.org/wikipedia/commons/c/c3/Die_of_the_first_555_chip.jpg` | `assets/photos/web/die-first-555-chip.jpg` |
| p2-03-ch13.md | `upload.wikimedia.org/.../thumb/6/66/LM2596_..._module.jpg/960px-LM2596_..._module.jpg` | `assets/photos/web/buck-converter-modules.jpg` |
| p3-02-ch15.md | `thumb.wikimedia.org/.../c/c4/Macro_circuit_board.JPG/500px-Macro_circuit_board.JPG` | `assets/photos/web/macro-circuit-board.jpg` |
| p4-01-ch16.md | `upload.wikimedia.org/wikipedia/commons/a/a6/Digital_Multimeter_Aka.jpg` | `assets/photos/web/digital-multimeter-aka.jpg` |
| p4-01-ch16.md | `thumb.wikimedia.org/.../0/0b/Digital_oscilloscope_in_use.jpg/500px-Digital_oscilloscope_in_use.jpg` | `assets/photos/web/digital-oscilloscope.jpg` |
| p6-01-s6-1.md | `thumb.wikimedia.org/.../d/d4/Generic_2N2222A.jpeg/500px-Generic_2N2222A.jpeg` | `assets/photos/web/generic-2n2222a.jpg` |
| p6-01-s6-1.md | `upload.wikimedia.org/wikipedia/commons/f/f6/Electrolytic_capacitors-P1090328.JPG` | `assets/photos/web/electrolytic-capacitors.jpg` |
| p6-01-s6-1.md | `thumb.wikimedia.org/.../2/21/Transistorer_%28cropped%29.jpg/500px-Transistorer_%28cropped%29.jpg` | `assets/photos/web/transistors-cropped.jpg` |
| p6-01-s6-1.md | `upload.wikimedia.org/wikipedia/commons/6/6e/4-Band_Resistor.svg` | `assets/photos/web/4-band-resistor.png` |
| p6-01-s6-1.md | `thumb.wikimedia.org/.../0/0a/LED_5mm_RGB.jpg/500px-LED_5mm_RGB.jpg` | `assets/photos/web/led-5mm-rgb.jpg` |
| p6-01-s6-1.md | `thumb.wikimedia.org/.../3/39/Jilin_Sino-Microelectronics_JCS4N65F-2383.jpg/500px-...jpg` | `assets/photos/web/mosfet-jcs4n65f.jpg` |
| p6-01-s6-1.md | `upload.wikimedia.org/wikipedia/commons/7/73/400_points_breadboard.jpg` | `assets/photos/web/400-points-breadboard.jpg` |
| p6-01-s6-1.md | `thumb.wikimedia.org/.../2/24/Multimeter_Gossen_Metra_Hit.jpg/500px-Multimeter_Gossen_Metra_Hit.jpg` | `assets/photos/web/scanned-multimeter-gossen.jpg` |
| p6-01-s6-1.md | `upload.wikimedia.org/wikipedia/commons/8/8a/Oscilloscope_Front_Panel_Numbered.svg` | `assets/photos/web/oscilloscope-front-panel.png` |
| p6-01-s6-1.md | `thumb.wikimedia.org/.../0/0b/Printed_circuit_board.jpg/500px-Printed_circuit_board.jpg` | `assets/photos/web/printed-circuit-board.jpg` |

YouTube 缩略图改成文字入口（在线站同样去外链图；整书因此不再需要打包缩略图）：

```html
<!-- p1-02-ch1.md -->
<a data-study-video href="https://www.youtube.com/watch?v=BcJ6UdDx1vg">▶ EEVblog #859 去耦电容教程</a>
<a data-study-video href="https://www.youtube.com/watch?v=1xicZF9glH0">▶ EEVblog #1085 去耦电容可视化</a>

<!-- p1-07-ch6.md -->
<a data-study-video href="https://www.youtube.com/watch?v=K03Rom3Cs28">▶ w2aew #75 运放电路理解法</a>
```

- [ ] **Step 5: 创建 `docs/p9-14-credits.md`**

结构固定为：标题 `# 📜 来源与许可`、一段总声明、照片表、第三方软件表、视频与外部资料说明、更新规则。照片表必须逐条列出 25 张（3 张教学样板 + 22 张章节配图），列：文件、作者、原图页、授权。内容如下（表格行顺序与 `assets/photos/README.md` 一致）：

```markdown
# 📜 来源与许可

本页是全仓库第三方资产的唯一授权清单。正文、SVG 动画、实验包与网表由本仓库生成，按 [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) 发布；转载或改编时请保留本页与仓库地址。

## 实物照片（Wikimedia Commons）

照片仅作器件外观与封装示意，引脚序、极性、参数一律以对应厂商数据手册为准。表内“文件”指仓库内路径。

| 文件 | 作者 | 原图页 | 授权 |
|---|---|---|---|
| assets/photos/capacitors.jpg | Shaddack | [Photo-SMDcapacitors.jpg](https://commons.wikimedia.org/wiki/File:Photo-SMDcapacitors.jpg) | 公有领域 |
| assets/photos/mosfets.jpg | Mister rf | [MOSFET transistors.jpg](https://commons.wikimedia.org/wiki/File:MOSFET_transistors.jpg) | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) |
| assets/photos/lm358n.jpg | Mister rf | [LM358N.jpg](https://commons.wikimedia.org/wiki/File:LM358N.jpg) | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) |
| assets/photos/web/2n2222a-and-schema.jpg | Transisto | [2N2222A and schema.jpg](https://commons.wikimedia.org/wiki/File:2N2222A_and_schema.jpg) | 公有领域 |
| assets/photos/web/4-band-resistor.png | jjbeard | [4-Band Resistor.svg](https://commons.wikimedia.org/wiki/File:4-Band_Resistor.svg) | 公有领域 |
| assets/photos/web/400-points-breadboard.jpg | oomlout | [400 points breadboard.jpg](https://commons.wikimedia.org/wiki/File:400_points_breadboard.jpg) | [CC BY-SA 2.0](https://creativecommons.org/licenses/by-sa/2.0/) |
| assets/photos/web/die-first-555-chip.jpg | CQ出版社 | [Die of the first 555 chip.jpg](https://commons.wikimedia.org/wiki/File:Die_of_the_first_555_chip.jpg) | 公有领域 |
| assets/photos/web/digital-multimeter-aka.jpg | André Karwath aka Aka | [Digital Multimeter Aka.jpg](https://commons.wikimedia.org/wiki/File:Digital_Multimeter_Aka.jpg) | [CC BY-SA 2.5](https://creativecommons.org/licenses/by-sa/2.5/) |
| assets/photos/web/digital-oscilloscope.jpg | Radarvector | [Digital oscilloscope in use.jpg](https://commons.wikimedia.org/wiki/File:Digital_oscilloscope_in_use.jpg) | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) |
| assets/photos/web/diode-closeup.jpg | John Maushammer（原上传者 Morcheeba） | [Diode-closeup.jpg](https://commons.wikimedia.org/wiki/File:Diode-closeup.jpg) | [CC BY-SA 2.5](https://creativecommons.org/licenses/by-sa/2.5/) |
| assets/photos/web/electrolytic-exploded.jpg | Binarysequence | [ElectrolyticCapacitorExploded.jpg](https://commons.wikimedia.org/wiki/File:ElectrolyticCapacitorExploded.jpg) | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) |
| assets/photos/web/electrolytic-capacitors.jpg | Elcap | [Electrolytic capacitors-P1090328.JPG](https://commons.wikimedia.org/wiki/File:Electrolytic_capacitors-P1090328.JPG) | CC0 |
| assets/photos/web/generic-2n2222a.jpg | MarkMossGH | [Generic 2N2222A.jpeg](https://commons.wikimedia.org/wiki/File:Generic_2N2222A.jpeg) | CC0 |
| assets/photos/web/led-5mm-rgb.jpg | Mister rf | [LED 5mm RGB.jpg](https://commons.wikimedia.org/wiki/File:LED_5mm_RGB.jpg) | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) |
| assets/photos/web/buck-converter-modules.jpg | Matthew Berardi | [LM2596 / MP1584 / SDB628 模块](https://commons.wikimedia.org/wiki/File:LM2596_buck_converter_module,_MP1584_buck_converter_module,_and_SDB628_boost_converter_module.jpg) | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) |
| assets/photos/web/lm555-timer.jpg | Emilian Robert Vicol | [LM555-555-Timer](https://commons.wikimedia.org/wiki/File:LM555-555-Timer_5734-480x452_(4791854328).jpg) | [CC BY 2.0](https://creativecommons.org/licenses/by/2.0/) |
| assets/photos/web/macro-circuit-board.jpg | Ingo Dierking | [Macro circuit board.JPG](https://commons.wikimedia.org/wiki/File:Macro_circuit_board.JPG) | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) |
| assets/photos/web/scanned-multimeter-gossen.jpg | Harke | [Multimeter Gossen Metra Hit.jpg](https://commons.wikimedia.org/wiki/File:Multimeter_Gossen_Metra_Hit.jpg) | [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/) |
| assets/photos/web/ne555-dip-soic.jpg | Swift.Hg | [NE555 DIP & SOIC.jpg](https://commons.wikimedia.org/wiki/File:NE555_DIP_%26_SOIC.jpg) | [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/) |
| assets/photos/web/oscilloscope-front-panel.png | jjbeard | [Oscilloscope Front Panel Numbered.svg](https://commons.wikimedia.org/wiki/File:Oscilloscope_Front_Panel_Numbered.svg) | 公有领域 |
| assets/photos/web/printed-circuit-board.jpg | Cjp24 | [Printed circuit board.jpg](https://commons.wikimedia.org/wiki/File:Printed_circuit_board.jpg) | [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/) |
| assets/photos/web/soldering-0805.jpg | Aisart | [Soldering a 0805.jpg](https://commons.wikimedia.org/wiki/File:Soldering_a_0805.jpg) | [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/) |
| assets/photos/web/ts7805-regulator.jpg | Anonimski | [TS7805 voltage regulator.JPG](https://commons.wikimedia.org/wiki/File:TS7805_voltage_regulator.JPG) | CC0 |
| assets/photos/web/transistors-cropped.jpg | Mister rf | [Transistorer (cropped).jpg](https://commons.wikimedia.org/wiki/File:Transistorer_(cropped).jpg) | [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/) |
| assets/photos/web/mosfet-jcs4n65f.jpg | Raimond Spekking | [Jilin Sino-Microelectronics JCS4N65F](https://commons.wikimedia.org/wiki/File:Jilin_Sino-Microelectronics_JCS4N65F-2383.jpg) | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) |

处理说明：JPEG/PNG 均从 Commons 下载后按原字节入库（SVG 原图另存为 PNG 渲染，不内嵌外部字体）；`assets/photos/README.md` 保留教学样板的编号叠加说明。

## 视频缩略图

3 张 YouTube 缩略图只用于在线站的原视频入口，不打包进离线整书。整书把它们改写为文字链接 `▶ 视频标题`。视频版权归原频道所有，本站只做链接推荐。

## 第三方软件与字体

| 组件 | 用途 | 许可 |
|---|---|---|
| [MathJax 3.2.2](https://www.mathjax.org/) `tex-svg-full.js` | 离线整书公式排版 | [Apache-2.0](https://www.apache.org/licenses/LICENSE-2.0) |
| [MkDocs Material](https://squidfunk.github.io/mkdocs-material/) | 在线站与整书样式来源 | MIT |
| [jieba](https://github.com/fxsjy/jieba) | 中文搜索分词 | MIT |
| [Playwright](https://playwright.dev/) | 整书 PDF 构建 | Apache-2.0 |
| [PyMuPDF](https://pymupdf.readthedocs.io/) | PDF 元数据/书签/页码后处理（仅构建工具） | AGPL-3.0 |
| [ZCOOL KuaiLe](https://fonts.google.com/specimen/ZCOOL+KuaiLe) | 视频字卡字体 | OFL-1.1 |

## 外部资料引用原则

- 官方数据手册、应用笔记、论文与视频只引用链接与必要短句，不复制受版权保护的整图、整表或字幕。
- 新增第三方图片、字体、代码资产时，必须同时更新本页；本项目照片处理说明在 `assets/photos/README.md`。
- 若权利人认为某处使用不当，请在本仓库提 Issue，我们会核实并替换或移除。
```

- [ ] **Step 6: 根 `CREDITS.md`、照片说明、致谢页、附录导航**

`CREDITS.md`：

```markdown
# 来源与许可（索引）

本仓库正文、SVG 动画、实验包与网表按 [CC BY-SA 4.0](LICENSE) 发布；第三方照片、软件与字体的完整清单、作者与授权条款见 **[docs/p9-14-credits.md](docs/p9-14-credits.md)**。

- 实物照片：25 张 Wikimedia Commons 图片（3 张教学样板 + 22 张章节配图）
- 第三方软件：MathJax（Apache-2.0）、MkDocs Material（MIT）、jieba（MIT）、Playwright（Apache-2.0）、PyMuPDF（AGPL-3.0，仅构建工具）
- 视频字体：ZCOOL KuaiLe（OFL-1.1）
- 新增第三方资产必须同步更新该清单。
```

`assets/photos/README.md` 末尾追加：

```markdown
章节配图已统一登记到唯一授权清单 [docs/p9-14-credits.md](../../docs/p9-14-credits.md)；本文件只保留教学样板的处理说明。
```

`docs/p9-13-thanks.md` 末尾追加：

```markdown
照片、软件与字体的完整来源与授权见[来源与许可](p9-14-credits.md)。
```

`scripts/build_site.py:617`：

```python
APPENDIX = {"p9-12-changelog.md", "p9-13-thanks.md", "p9-14-credits.md"}
```

- [ ] **Step 7: 跑测试与站点构建**

Run:
```bash
python -B -m unittest discover -s scripts -p test_docs_links.py -v
python -B -m unittest discover -s scripts -p test_a11y.py -v
python scripts/build_site.py --build
python -B -m unittest discover -s scripts -p test_site_build.py -v
```
Expected: 全部 PASS；站点 `build/site/p9-14-credits.html` 存在；`build/site/p1-02-ch1.html` 中已无 Wikimedia URL。

---

### Task 2: 首页「按现象直查」、徽章、常用命令与 README 重建

**Files:**
- Modify: `docs/index.md`（第 9-13 行徽章区；第 37 行前插入现象表；`<a id="news">` 前插入常用命令）
- Regenerate: `README.md`
- Test: `scripts/test_first_screen.py`、`scripts/test_docs_links.py`、`scripts/test_readme_links.py`、`scripts/test_docs_sync.py`

**Interfaces:**
- Consumes: Task 1 的 `docs/p9-14-credits.md`。
- Produces: 首页 10 行现象表；6 枚徽章；README 的「常用命令」表。

- [ ] **Step 1: 修改徽章区**

把 `docs/index.md` 第 9-13 行的 `.repo-badges` 内容替换为：

```markdown
[![tests](https://github.com/zhuguang-ZFG/analog-circuit-roadmap/actions/workflows/tests.yml/badge.svg)](https://github.com/zhuguang-ZFG/analog-circuit-roadmap/actions/workflows/tests.yml)
[![docs](https://img.shields.io/badge/docs-60%20%E9%A1%B5-blue)](p0-07-toc.md#toc)
[![SVG animations](https://img.shields.io/badge/SVG%20%E5%8A%A8%E7%94%BB-108-ff69b4)](p5-00-part5.md#part5)
[![video](https://img.shields.io/badge/%E8%A7%86%E9%A2%91%E8%AF%BE-20%20%E9%9B%86-red)](p7-03-s7-3.md#s7-3)
[![book](https://img.shields.io/badge/%E7%A6%BB%E7%BA%BF%E6%95%B4%E4%B9%A6-HTML%20%2B%20PDF-success)](analog-book/)
[![license](https://img.shields.io/badge/%E6%8E%88%E6%9D%83-CC%20BY--SA%204.0-lightgrey)](LICENSE)
```

- [ ] **Step 2: 插入「按现象直查」**

在第 37 行 `## 找到适合你的起点` 之前插入（逐字）：

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

- [ ] **Step 3: 插入「常用命令」**

在 `<a id="news"></a>` 之前插入：

```markdown
## 常用命令

| 目标 | 命令 |
|---|---|
| 重建 README | `make readme` |
| 构建在线站 | `make site` |
| 构建离线整书 HTML | `make book` |
| 构建 HTML + PDF | `make book-pdf` |
| 审计已有整书产物 | `make book-check` |
| 静态测试（无需浏览器） | `make test-static` |
| 浏览器回归 | `make test-browser` |
| 全量校验 | `make verify` |
| 内容规模统计 | `make stats` |

Windows 无 `make` 时用 `mingw32-make <目标>`，或直接运行 `Makefile` 中对应的 `python` 命令。
```

- [ ] **Step 4: 重建 README 并跑测试**

Run:
```bash
python scripts/build_readme.py
python -B -m unittest discover -s scripts -p test_docs_links.py -v
python -B -m unittest discover -s scripts -p test_readme_links.py -v
python -B -m unittest discover -s scripts -p test_docs_sync.py -v
python -B -m unittest discover -s scripts -p test_first_screen.py -v
```
Expected: README 中出现「按现象直查」「常用命令」与 6 枚徽章；测试全 PASS。若 `test_first_screen.py` 依赖浏览器则按该文件说明启动；静态断言必须通过。

---

### Task 3: 引入 MathJax SVG 与静态路线图

**Files:**
- Create: `assets/vendor/mathjax-svg/tex-svg-full.js`
- Create: `assets/vendor/mathjax-svg/README.md`
- Create: `assets/vendor/mathjax-svg/LICENSE`
- Create: `analog-book/static/roadmap.svg`
- Create: `analog-book/static/roadmap.source.txt`

**Interfaces:**
- Produces: 构建器读取的固定资产；`roadmap.source.txt` 必须与 `docs/p0-06-roadmap.md` 中 Mermaid fenced block 逐字节一致。

- [ ] **Step 1: 复制 MathJax SVG 构建包并登记**

```bash
mkdir -p assets/vendor/mathjax-svg
cp /d/Temp/mj-svg/package/es5/tex-svg-full.js assets/vendor/mathjax-svg/
cp /d/Temp/mj-svg/package/LICENSE assets/vendor/mathjax-svg/
python - <<'PY'
import hashlib, pathlib
for name in ("tex-svg-full.js", "LICENSE"):
    p = pathlib.Path("assets/vendor/mathjax-svg") / name
    print(name, p.stat().st_size, hashlib.sha256(p.read_bytes()).hexdigest())
PY
```
Expected: `tex-svg-full.js` 2,275,113 bytes，SHA-256 `a4354ff94fd868aea0cc6eaaa79a57fda0588646fc46ee3700a349ee0a11cbe6`；`LICENSE` SHA-256 `cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30`。

若临时包不存在，从 npm 包 `mathjax@3.2.2` 取 `es5/tex-svg-full.js`：

```bash
cd /d/Temp && npm pack mathjax@3.2.2 && tar -xzf mathjax-3.2.2.tgz
```

`assets/vendor/mathjax-svg/README.md`：

```markdown
# MathJax 3.2.2 SVG 构建包（离线整书专用）

- 来源：npm `mathjax@3.2.2`，`es5/tex-svg-full.js`
- 体积：2,275,113 字节
- SHA-256：`a4354ff94fd868aea0cc6eaaa79a57fda0588646fc46ee3700a349ee0a11cbe6`
- 许可：Apache-2.0（见同目录 `LICENSE`）
- 用途：`analog-book/build_book.py` 把它内联进单文件 HTML，保证断网 `file://` 下公式可排版
- 在线站继续使用 `assets/vendor/mathjax/tex-chtml-full.js`，两者互不影响
```

- [ ] **Step 2: 生成静态路线图与源码快照**

用已下载的 mermaid 11.12.2 UMD 通过 Playwright 渲染，脚本可临时写到 `/d/Temp/render_roadmap.py`（不要入库）：

```python
import pathlib, re
from playwright.sync_api import sync_playwright

root = pathlib.Path(r"D:/Users/monidianlu/analog-circuit-roadmap")
text = (root / "docs/p0-06-roadmap.md").read_text(encoding="utf-8")
source = re.search(r"```mermaid\n(.*?)```", text, re.S).group(1).strip() + "\n"
(root / "analog-book/static").mkdir(parents=True, exist_ok=True)
(root / "analog-book/static/roadmap.source.txt").write_text(
    source, encoding="utf-8", newline="\n")
mermaid_js = pathlib.Path(r"D:/Temp/mmd/package/dist/mermaid.min.js").read_text(encoding="utf-8")
html = (
    "<!doctype html><meta charset='utf-8'><body><div id='out'></div>"
    f"<script>{mermaid_js}</script>"
    "<script>mermaid.initialize({startOnLoad:false,theme:'neutral'});"
    "mermaid.render('roadmap', " + repr(source) + ").then(({svg})=>{"
    "document.getElementById('out').innerHTML=svg;});</script></body>"
)
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.set_content(html, wait_until="load")
    page.wait_for_function("document.querySelector('#out svg') !== null", timeout=30000)
    svg = page.inner_html("#out svg")
    browser.close()
svg = svg.replace("max-width:", "max-width:", 1)
(root / "analog-book/static/roadmap.svg").write_text(
    '<svg xmlns="http://www.w3.org/2000/svg"' + svg.split('<svg', 1)[1] + "\n",
    encoding="utf-8", newline="\n")
print("svg bytes", (root / "analog-book/static/roadmap.svg").stat().st_size)
```

Run: `python /d/Temp/render_roadmap.py`
Expected: 输出约 21,898 bytes，`viewBox="0 0 544.984375 1222"`。

- [ ] **Step 3: 校验快照与文档一致**

Run:
```bash
python - <<'PY'
import pathlib, re
doc = pathlib.Path('docs/p0-06-roadmap.md').read_text(encoding='utf-8')
src = re.search(r'```mermaid\n(.*?)```', doc, re.S).group(1).strip() + '\n'
snap = pathlib.Path('analog-book/static/roadmap.source.txt').read_text(encoding='utf-8')
assert src == snap, 'roadmap source drift'
print('roadmap snapshot: PASS')
PY
```
Expected: `roadmap snapshot: PASS`。

---

### Task 4: manifest 与书构建器骨架（校验、抽取、清洗、命名空间化）

**Files:**
- Create: `analog-book/manifest.json`
- Create: `analog-book/build_book.py`
- Create: `analog-book/tests/test_build.py`

**Interfaces:**
- Produces:
  - `load_manifest() -> dict`
  - `validate_manifest(manifest) -> list[str]`（页面 stem 按书目顺序）
  - `build_site(site_dir: Path) -> None`
  - `extract_article(site_dir, stem) -> tuple[str, str]`（fragment 已清洗、已命名空间化；返回 `(title, fragment)`）
  - `manuscript(manifest) -> list[Part]`，`Part = {"id": str, "title": str, "pages": [{"stem","title","html"}]}`
  - `BookError(RuntimeError)`

- [ ] **Step 1: 写 `analog-book/manifest.json`**

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
    {"id": "p0", "files": ["p0-01-preface.md", "p0-02-how-to-use.md", "p0-03-timeline.md", "p0-04-by-need.md", "p0-05-picks.md", "p0-06-roadmap.md", "p0-07-toc.md", "p0-08-cheatsheet.md", "p0-09-diagnostic.md", "p0-10-model-limits.md"]},
    {"id": "p1", "files": ["p1-00-part1.md", "p1-01-ch0.md", "p1-02-ch1.md", "p1-03-ch2.md", "p1-04-ch3.md", "p1-05-ch4.md", "p1-06-ch5.md", "p1-07-ch6.md", "p1-08-ch7.md", "p1-09-ch8.md", "p1-10-ch9.md", "p1-11-ch10.md"]},
    {"id": "p2", "files": ["p2-00-part2.md", "p2-01-ch11.md", "p2-02-ch12.md", "p2-03-ch13.md"]},
    {"id": "p3", "files": ["p3-00-part3.md", "p3-01-ch14.md", "p3-02-ch15.md"]},
    {"id": "p4", "files": ["p4-00-part4.md", "p4-01-ch16.md", "p4-02-ch17.md", "p4-03-ch18.md"]},
    {"id": "p5", "files": ["p5-00-part5.md"]},
    {"id": "p6", "files": ["p6-00-part6.md", "p6-01-s6-1.md", "p6-02-s6-2.md", "p6-03-s6-3.md", "p6-04-s6-4.md", "p6-05-s6-5.md"]},
    {"id": "p7", "files": ["p7-00-part7.md", "p7-01-s7-1.md", "p7-02-s7-2.md", "p7-03-s7-3.md"]},
    {"id": "p8", "files": ["p8-00-part8.md", "p8-01-s8-1.md", "p8-02-s8-2.md", "p8-03-s8-3.md", "p8-04-s8-4.md", "p8-05-s8-5.md", "p8-06-s8-6.md", "p8-07-s8-7.md", "p8-08-s8-8.md", "p8-09-s8-9.md", "p8-10-s8-10.md", "p8-11-s8-11.md"]},
    {"id": "p9", "files": ["p9-00-quiz.md"]}
  ],
  "appendix": {
    "title": "附录",
    "files": ["p9-12-changelog.md", "p9-13-thanks.md", "p9-14-credits.md"]
  }
}
```

- [ ] **Step 2: 写 `analog-book/tests/test_build.py` 的第一组失败测试**

```python
#!/usr/bin/env python3
"""整书构建单元测试：manifest、清洗、ID 命名空间、链接、资源与结构审计。"""
import json
import re
import sys
import unittest
from pathlib import Path

BOOK = Path(__file__).resolve().parent.parent
ROOT = BOOK.parent
sys.path.insert(0, str(BOOK))

import build_book  # noqa: E402


class ManifestTests(unittest.TestCase):
    def setUp(self):
        self.manifest = build_book.load_manifest()

    def test_covers_every_content_page_exactly_once(self):
        stems = build_book.validate_manifest(self.manifest)
        docs = {p.stem for p in (ROOT / "docs").glob("*.md")} - {"index"}
        self.assertEqual(60, len(stems))
        self.assertEqual(docs, set(stems))
        self.assertEqual(60, len(set(stems)))
        self.assertEqual(3, len(self.manifest["appendix"]["files"]))

    def test_metadata_is_complete(self):
        for key in ("title", "subtitle", "version", "source_version", "date",
                    "language", "author", "site_url", "repository", "license"):
            self.assertTrue(self.manifest[key], key)
```

Run: `python -B -m unittest discover -s analog-book/tests -p test_build.py -v`
Expected: FAIL（`ModuleNotFoundError: build_book`）。

- [ ] **Step 3: 实现 builder 骨架**

`analog-book/build_book.py` 第一版（后续任务增量扩展）：

```python
#!/usr/bin/env python3
"""Build the offline single-file book and A4 PDF from the MkDocs site."""
import argparse
import base64
import hashlib
import html
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

BOOK_DIR = Path(__file__).resolve().parent
ROOT = BOOK_DIR.parent
DOCS = ROOT / "docs"
SITE_DIR = ROOT / "build" / "site"
DIST_DIR = BOOK_DIR / "dist"
MANIFEST_PATH = BOOK_DIR / "manifest.json"
OUTPUT_NAME = "analog-circuit-book.html"
PDF_NAME = "analog-circuit-book.pdf"
MAX_HTML_BYTES = 20 * 1024 * 1024

ARTICLE_RE = re.compile(
    r'<article class="md-content__inner md-typeset">(.*?)</article>', re.S)
H1_RE = re.compile(r"<h1[^>]*>(.*?)</h1>", re.S)
TAG_RE = re.compile(r"<[^>]+>")


class BookError(RuntimeError):
    pass


def load_manifest() -> dict:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def manifest_sha256() -> str:
    return hashlib.sha256(MANIFEST_PATH.read_bytes()).hexdigest()


def validate_manifest(manifest: dict) -> list[str]:
    files = [name for part in manifest["parts"] for name in part["files"]]
    files += manifest["appendix"]["files"]
    stems = [Path(name).stem for name in files]
    actual = {p.stem for p in DOCS.glob("*.md")} - {"index"}
    problems = []
    duplicates = sorted({s for s in stems if stems.count(s) > 1})
    if duplicates:
        problems.append("重复页面: " + ", ".join(duplicates))
    if set(stems) != actual:
        problems.append(
            "清单与 docs 不一致；缺少: %s；多余: %s" % (
                sorted(actual - set(stems)), sorted(set(stems) - actual)))
    if len(stems) != 60:
        problems.append("内容页应为 60，实际 %d" % len(stems))
    for page in files:
        if not (SITE_DIR / page.replace(".md", ".html")).is_file():
            problems.append("站点产物缺失: %s" % page)
    ids = [part["id"] for part in manifest["parts"]]
    if len(ids) != len(set(ids)):
        problems.append("篇 ID 重复")
    if problems:
        raise BookError("manifest 校验失败:\n" + "\n".join(problems))
    return stems


def build_site(site_dir: Path = SITE_DIR) -> None:
    if site_dir != SITE_DIR:
        # 复用已有站点目录时不做构建
        return
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "build_site.py"), "--build"],
        cwd=ROOT)
    if result.returncode != 0:
        raise BookError("站点构建失败，整书无法继续")


def _plain_text(fragment: str) -> str:
    text = html.unescape(TAG_RE.sub("", fragment))
    return re.sub(r"\s+", " ", text).replace("¶", "").strip()


def _strip_tags(fragment: str) -> str:
    return TAG_RE.sub("", fragment).replace("¶", "").strip()


def _clean_fragment(fragment: str) -> str:
    fragment = re.sub(
        r'<a[^>]+class="md-content__button md-icon".*?</a>', "", fragment, flags=re.S)
    fragment = re.sub(
        r'<a class="headerlink".*?</a>', "", fragment, flags=re.S)
    fragment = re.sub(
        r'<div class="legacy-anchor".*?</div>', "", fragment, flags=re.S)
    fragment = re.sub(
        r"<hr\s*/?>\s*<blockquote>\s*<p>✍️ <strong>参与共建.*$", "",
        fragment, flags=re.S)
    fragment = fragment.replace(' loading="lazy"', "")
    return fragment.strip()


def _namespace(fragment: str, stem: str) -> str:
    prefix = stem + "--"
    return re.sub(
        r'\b(id|name)="([^"]+)"',
        lambda m: '%s="%s%s"' % (m.group(1), prefix, m.group(2)),
        fragment)


def extract_article(site_dir: Path, name: str) -> tuple[str, str]:
    path = site_dir / name.replace(".md", ".html")
    page = path.read_text(encoding="utf-8")
    match = ARTICLE_RE.search(page)
    if not match:
        raise BookError(f"{path.name}: 找不到 <article class=\"md-content__inner md-typeset\">")
    fragment = _clean_fragment(match.group(1))
    h1 = H1_RE.search(fragment)
    if not h1:
        raise BookError(f"{path.name}: <article> 中缺少 <h1>")
    title = _strip_tags(h1.group(1))
    if not title:
        raise BookError(f"{path.name}: <h1> 标题为空")
    stem = Path(name).stem
    return title, _namespace(fragment, stem)


def manuscript(manifest: dict, site_dir: Path = SITE_DIR) -> list[dict]:
    parts = []
    for part in manifest["parts"] + [
            {"id": "appendix", "files": manifest["appendix"]["files"]}]:
        pages = []
        for name in part["files"]:
            title, fragment = extract_article(site_dir, name)
            pages.append({"stem": Path(name).stem, "title": title, "html": fragment})
        parts.append({
            "id": part["id"],
            "title": manifest["appendix"]["title"] if part["id"] == "appendix" else pages[0]["title"],
            "pages": pages,
        })
    return parts
```

- [ ] **Step 4: 补第二组测试（抽取/清洗/命名空间）**

追加到 `analog-book/tests/test_build.py`：

```python
class ExtractionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = build_book.load_manifest()
        build_book.validate_manifest(cls.manifest)
        cls.parts = build_book.manuscript(cls.manifest)
        cls.pages = [p for part in cls.parts for p in part["pages"]]

    def test_sixty_pages_in_eight_eleven_parts(self):
        self.assertEqual(11, len(self.parts))
        self.assertEqual(60, len(self.pages))

    def test_site_only_dom_is_gone(self):
        for page in self.pages:
            for needle in ("参与共建", "legacy-anchor", "md-content__button",
                           "headerlink", 'loading="lazy"'):
                self.assertNotIn(needle, page["html"], f'{page["stem"]}: {needle}')

    def test_reading_checkpoint_survives(self):
        self.assertTrue(any("reading-checkpoint" in p["html"] for p in self.pages))

    def test_ids_are_namespaced_and_unique_across_book(self):
        seen = {}
        for page in self.pages:
            prefix = page["stem"] + "--"
            ids = re.findall(r'\b(?:id|name)="([^"]+)"', page["html"])
            self.assertTrue(ids, page["stem"])
            for value in ids:
                self.assertTrue(value.startswith(prefix), f'{page["stem"]}: {value}')
                self.assertNotIn(value, seen, f'重复 ID {value}')
                seen[value] = page["stem"]

    def test_every_page_keeps_an_h1_title(self):
        for page in self.pages:
            self.assertTrue(page["title"])
            self.assertRegex(page["html"], r"<h1[^>]*>")
```

Run:
```bash
python scripts/build_site.py --build
python -B -m unittest discover -s analog-book/tests -p test_build.py -v
```
Expected: PASS（除后续任务将加入的链接/资源/结构测试外）。

---

### Task 5: 链接重写、图片/CSS/JS 内嵌、Mermaid 与 YouTube 处理

**Files:**
- Modify: `analog-book/build_book.py`
- Modify: `analog-book/tests/test_build.py`

**Interfaces:**
- Consumes: `manuscript()` 输出的已命名空间化 fragment。
- Produces:
  - `rewrite_links(fragment, current_stem, book_stems, manifest) -> str`
  - `inline_images(fragment) -> tuple[str, int]`
  - `inline_css(site_dir) -> str`
  - `inline_scripts(site_dir) -> str`
  - `inline_mathjax() -> str`
  - `replace_mermaid(fragment) -> str`

- [ ] **Step 1: 追加失败测试**

```python
class LinkAndAssetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = build_book.load_manifest()
        build_book.validate_manifest(cls.manifest)
        cls.parts = build_book.manuscript(cls.manifest)
        cls.pages = [p for part in cls.parts for p in part["pages"]]
        cls.stems = {p["stem"] for p in cls.pages}

    def test_links_are_rewritten(self):
        for page in self.pages:
            page["html"] = build_book.rewrite_links(
                page["html"], page["stem"], self.stems, self.manifest)
        ids = {i for p in self.pages
               for i in re.findall(r'\b(?:id|name)="([^"]+)"', p["html"])}
        broken = []
        for page in self.pages:
            for target in re.findall(r'href="#([^"]+)"', page["html"]):
                if target not in ids:
                    broken.append(f'{page["stem"]}: #{target}')
        self.assertEqual([], broken[:20])

    def test_no_internal_site_links_remain(self):
        for page in self.pages:
            body = build_book.rewrite_links(
                page["html"], page["stem"], self.stems, self.manifest)
            self.assertNotRegex(body, r'href="[\w\-]+\.html')
            self.assertNotRegex(body, r'href="assets/')

    def test_images_become_data_uris(self):
        for page in self.pages:
            body, _count = build_book.inline_images(page["html"])
            self.assertNotRegex(body, r'src="assets/')
            self.assertNotRegex(body, r'srcset="assets/')
            self.assertNotRegex(body, r'src="https?://')
            self.assertNotRegex(body, r'<iframe|<video')
            self.assertEqual(0, body.count("<script src="))
```

Run: `python -B -m unittest discover -s analog-book/tests -p test_build.py -v`
Expected: FAIL（`AttributeError: module 'build_book' has no attribute 'rewrite_links'`）。

- [ ] **Step 2: 实现链接重写**

追加到 `build_book.py`：

```python
EXTERNAL_PREFIXES = ("http://", "https://", "mailto:", "tel:", "data:")


def rewrite_links(fragment: str, current_stem: str, book_stems: set[str],
                  manifest: dict) -> str:
    site_url = manifest["site_url"].rstrip("/") + "/"

    def repl(match: re.Match) -> str:
        href = match.group(1)
        if href.startswith(EXTERNAL_PREFIXES) or href == "#":
            return match.group(0)
        path, _, anchor = href.partition("#")
        name = path.rsplit("/", 1)[-1]
        if path.startswith("#"):
            return f'href="#{current_stem}--{path[1:]}"'
        if name.endswith(".html"):
            stem = name[:-5]
            if stem == "index":
                return 'href="#book-toc"'
            if stem in book_stems:
                target = f"#{stem}" if not anchor else f"#{stem}--{anchor}"
                return f'href="{target}"'
        if path.startswith("assets/"):
            return f'href="{site_url}{path}"'
        return f'href="{site_url}{href}"'

    return re.sub(r'href="([^"]+)"', repl, fragment)
```

注意：`path.startswith("#")` 分支应在 `partition` 前判断更清晰；按上面写法 `href="#x"` 会先进入 `path="#x"`, `anchor=""`，再命中 `path.startswith("#")`，结果正确。`href="page.html#x"` 的 `anchor` 已拆出。

- [ ] **Step 3: 实现资源内嵌**

```python
CSS_FILES = [
    "assets/stylesheets/main.ec1eaa64.min.css",  # 版本号由 _material_css() 重新发现
    "assets/stylesheets/palette.ab4e12ef.min.css",
]
BOOK_CSS = ["typography", "gallery", "learning", "reading", "diag"]
BOOK_SCRIPTS = ["calc", "learning", "learning-catalog", "diag"]

MIME = {
    ".svg": "image/svg+xml", ".png": "image/png", ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg", ".gif": "image/gif", ".webp": "image/webp",
}


def _material_css(site_dir: Path) -> list[Path]:
    styles = site_dir / "assets" / "stylesheets"
    found = []
    for pattern in ("main.*.min.css", "palette.*.min.css"):
        matches = sorted(styles.glob(pattern))
        if not matches:
            raise BookError(f"站点缺少 {pattern}")
        found.append(matches[-1])
    return found


def inline_css(site_dir: Path) -> str:
    chunks = [p.read_text(encoding="utf-8") for p in _material_css(site_dir)]
    for name in BOOK_CSS:
        path = site_dir / "stylesheets" / f"{name}.css"
        if not path.is_file():
            raise BookError(f"站点缺少样式 {path.name}")
        chunks.append(path.read_text(encoding="utf-8"))
    chunks.append((BOOK_DIR / "styles" / "book.css").read_text(encoding="utf-8"))
    return "\n".join(chunks)


def inline_scripts(site_dir: Path) -> str:
    chunks = []
    for name in BOOK_SCRIPTS:
        path = site_dir / "javascripts" / f"{name}.js"
        if not path.is_file():
            raise BookError(f"站点缺少脚本 {path.name}")
        chunks.append(path.read_text(encoding="utf-8"))
    return "\n".join(chunks)


def inline_mathjax() -> str:
    mathjax = BOOK_DIR.parent / "assets" / "vendor" / "mathjax-svg" / "tex-svg-full.js"
    if not mathjax.is_file():
        raise BookError(f"缺少 MathJax SVG 包: {mathjax}")
    config = (
        "<script>window.MathJax={tex:{inlineMath:[[\"\\\\(\",\"\\\\)\"],[\"$\",\"$\"]],"
        "displayMath:[[\"\\\\[\",\"\\\\]\"],[\"$$\",\"$$\"]],processEscapes:true,"
        "processEnvironments:true},svg:{fontCache:\"local\"},options:{"
        "ignoreHtmlClass:\".*|\",processHtmlClass:\"arithmatex\"}};</script>"
    )
    return config + "<script>" + mathjax.read_text(encoding="utf-8") + "</script>"


def _data_uri(path: Path) -> str:
    mime = MIME.get(path.suffix.lower())
    if mime is None:
        raise BookError(f"不支持的图片类型: {path}")
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def inline_images(fragment: str) -> tuple[str, int]:
    count = 0

    def source(match: re.Match) -> str:
        nonlocal count
        rel = match.group(2)
        path = (ROOT / rel).resolve()
        if not path.is_file():
            raise BookError(f"图片不存在: {rel}")
        count += 1
        return f'{match.group(1)}="{_data_uri(path)}"'

    fragment = re.sub(r'(src)="(assets/[^"]+)"', source, fragment)
    fragment = re.sub(r'(srcset)="(assets/[^"]+)"',
                      lambda m: f'{m.group(1)}="{_data_uri((ROOT / m.group(2)).resolve())}"',
                      fragment)
    remote = re.search(r'<img[^>]+src="(https?://[^"]+)"', fragment)
    if remote:
        raise BookError(f"书内仍有远程图片: {remote.group(1)}")
    return fragment, count


def replace_mermaid(fragment: str) -> str:
    snapshot = BOOK_DIR / "static" / "roadmap.svg"
    source_file = BOOK_DIR / "static" / "roadmap.source.txt"
    if not snapshot.is_file() or not source_file.is_file():
        raise BookError("缺少 static/roadmap.svg 或 roadmap.source.txt")
    if '<pre class="mermaid">' not in fragment:
        return fragment
    doc = (DOCS / "p0-06-roadmap.md").read_text(encoding="utf-8")
    source = re.search(r"```mermaid\n(.*?)```", doc, re.S).group(1).strip() + "\n"
    if source != source_file.read_text(encoding="utf-8"):
        raise BookError("docs/p0-06-roadmap.md 与 static/roadmap.source.txt 不一致；请重新生成快照")
    svg = snapshot.read_text(encoding="utf-8")
    return re.sub(r'<pre class="mermaid">.*?</pre>',
                  '<figure class="book-roadmap">' + svg + "</figure>",
                  fragment, flags=re.S)
```

`inline_images` 对重复引用的图片不做去重（p5 画廊同图会重复内嵌）。构建审计会报告最大资源；若超过 20 MB，再按 spec 风险表处理。

- [ ] **Step 4: 运行测试**

Run: `python -B -m unittest discover -s analog-book/tests -p test_build.py -v`
Expected: 新测试 PASS；若 `main.*.min.css` 发现两个版本，取排序最后一个（站点只保留一个）。

---

### Task 6: 拼装全书、审计、确定性与 `--check`

**Files:**
- Modify: `analog-book/build_book.py`
- Modify: `analog-book/tests/test_build.py`

**Interfaces:**
- Produces:
  - `assemble_book(manifest, parts) -> str`
  - `audit_html(document, manifest, parts) -> dict`（计数：pages/images/formulas/bytes/max_asset）
  - `build_html(out_dir: Path, site_dir: Path = SITE_DIR, rebuild_site: bool = True) -> Path`
  - CLI：`--out-dir`、`--site-dir`、`--no-build`、`--check`、`--pdf`、`--browser`

- [ ] **Step 1: 追加失败测试**

```python
class AssemblyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = build_book.load_manifest()
        build_book.validate_manifest(cls.manifest)
        cls.parts = build_book.manuscript(cls.manifest)
        cls.document = build_book.assemble_book(cls.manifest, cls.parts)

    def test_front_matter_and_structure(self):
        self.assertIn('class="book-cover"', self.document)
        self.assertIn('class="book-copyright"', self.document)
        self.assertIn('id="book-toc"', self.document)
        self.assertEqual(60, self.document.count('class="book-page"'))
        self.assertEqual(11, self.document.count('class="book-part"'))
        for stem in ("p0-01-preface", "p1-01-ch0", "p6-01-s6-1",
                     "p9-12-changelog", "p9-14-credits"):
            self.assertIn(f'data-page="{stem}"', self.document)
        self.assertIn('name="book-manifest-sha256"', self.document)
        self.assertIn(build_book.manifest_sha256(), self.document)

    def test_toc_has_every_page(self):
        toc = re.search(r'<section class="book-toc".*?</section>', self.document, re.S).group(0)
        self.assertEqual(60, toc.count('<a href="#page-'))
        self.assertEqual(11, toc.count("<h2"))

    def test_no_remote_or_site_only_assets(self):
        self.assertNotRegex(self.document, r'<script[^>]+src=')
        self.assertNotRegex(self.document, r'<link[^>]+rel="stylesheet"')
        self.assertNotIn("<iframe", self.document)
        self.assertNotIn("<video", self.document)
        self.assertNotRegex(self.document, r'(?:src|srcset)="(?!#)(?:assets/|https?://)')
        self.assertIn("tex-svg-full.js", self.document) if False else None
        self.assertIn("MathJax", self.document)

    def test_ids_are_globally_unique(self):
        ids = re.findall(r'\b(?:id|name)="([^"]+)"', self.document)
        duplicates = sorted({i for i in ids if ids.count(i) > 1})
        self.assertEqual([], duplicates[:10])

    def test_audit_counts(self):
        report = build_book.audit_html(self.document, self.manifest, self.parts)
        self.assertEqual(60, report["pages"])
        self.assertGreater(report["images"], 90)
        self.assertGreater(report["formulas"], 1000)
        self.assertLess(report["bytes"], build_book.MAX_HTML_BYTES)

    def test_deterministic(self):
        again = build_book.assemble_book(self.manifest, self.parts)
        self.assertEqual(hashlib.sha256(self.document.encode()).hexdigest(),
                         hashlib.sha256(again.encode()).hexdigest())
```

注意 `self.assertIn("tex-svg-full.js", ...)` 无意义，删除该行，只保留 `MathJax` 断言。

Run: `python -B -m unittest discover -s analog-book/tests -p test_build.py -v`
Expected: FAIL（无 `assemble_book`）。

- [ ] **Step 2: 实现拼装**

```python
BOOK_CSS_PATH = BOOK_DIR / "styles" / "book.css"


def _page_section(page: dict) -> str:
    return (
        f'<section class="book-page" id="page-{page["stem"]}" '
        f'data-page="{page["stem"]}" data-title="{html.escape(page["title"], quote=True)}">\n'
        f'{page["html"]}\n'
        '<p class="book-page-back"><a href="#book-toc">↑ 返回目录</a></p>\n'
        '</section>'
    )


def _cover(manifest: dict) -> str:
    return (
        '<section class="book-cover" data-part="front">'
        f'<p class="book-cover-kicker">{html.escape(manifest["subtitle"])}</p>'
        f'<h1 class="book-cover-title">{html.escape(manifest["title"])}</h1>'
        f'<p class="book-cover-version">版本 {manifest["version"]} · {manifest["date"]}</p>'
        f'<p class="book-cover-site">{html.escape(manifest["site_url"])}</p>'
        f'<p class="book-cover-repo">{html.escape(manifest["repository"])}</p>'
        '</section>'
    )


def _copyright(manifest: dict) -> str:
    return (
        '<section class="book-copyright" data-part="front">'
        '<h1>版权与来源</h1>'
        f'<p>《{html.escape(manifest["title"])}》{manifest["version"]}，'
        f'{manifest["date"]}。作者：{html.escape(manifest["author"])}。</p>'
        f'<p>正文、SVG 动画、实验包与网表采用 {manifest["license"]} 授权；'
        '第三方照片、软件与字体的完整清单见书末「来源与许可」。</p>'
        f'<p>在线地址：{html.escape(manifest["site_url"])}<br>'
        f'仓库：{html.escape(manifest["repository"])}</p>'
        '<p>本书为离线阅读副本，内容与在线站同源；器件参数与安全操作请以厂商数据手册和实际条件为准。</p>'
        '</section>'
    )


def _toc(parts: list[dict]) -> str:
    rows = ['<section class="book-toc" id="book-toc" data-part="toc">',
            '<h1>全书目录</h1>']
    for part in parts:
        rows.append(f'<div class="book-toc-part"><h2>{html.escape(part["title"])}</h2><ul>')
        for page in part["pages"]:
            rows.append(
                f'<li><a href="#page-{page["stem"]}">{html.escape(page["title"])}</a></li>')
        rows.append("</ul></div>")
    rows.append("</section>")
    return "\n".join(rows)


def assemble_book(manifest: dict, parts: list[dict]) -> str:
    body = [_cover(manifest), _copyright(manifest), _toc(parts)]
    for part in parts:
        body.append(f'<section class="book-part" data-part="{part["id"]}">')
        body.extend(_page_section(page) for page in part["pages"])
        body.append("</section>")
    css = inline_css(SITE_DIR)
    scripts = inline_scripts(SITE_DIR)
    mathjax = inline_mathjax()
    document = f"""<!doctype html>
<html lang="{manifest["language"]}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light">
<title>{html.escape(manifest["title"])}</title>
<meta name="book-manifest-sha256" content="{manifest_sha256()}">
<meta name="book-version" content="{manifest["version"]}">
<meta name="book-date" content="{manifest["date"]}">
<style>{css}</style>
</head>
<body>
<header class="book-header"><span>{html.escape(manifest["title"])}</span>
<a href="#book-toc">目录</a></header>
<main class="book">
{''.join(body)}
</main>
<footer class="book-footer">离线整书 · 由 docs/ 构建 · {manifest["license"]}</footer>
{mathjax}
<script>{scripts}</script>
</body>
</html>
"""
    return document
```

`book.css` 在 Task 7 创建；本任务先放最小占位样式（Task 7 替换为正式版）：

```css
@page { size: A4; margin: 18mm 16mm 20mm; }
```

- [ ] **Step 3: 实现审计与命令**

```python
def audit_html(document: str, manifest: dict, parts: list[dict]) -> dict:
    pages = [page for part in parts for page in part["pages"]]
    ids = re.findall(r'\b(?:id|name)="([^"]+)"', document)
    duplicates = sorted({i for i in ids if ids.count(i) > 1})
    problems = []
    if duplicates:
        problems.append("重复 ID: " + ", ".join(duplicates[:10]))
    hrefs = re.findall(r'href="#([^"]+)"', document)
    missing = sorted({h for h in hrefs if h not in set(ids)})
    if missing:
        problems.append("悬空锚点: " + ", ".join(missing[:10]))
    if '<script src=' in document:
        problems.append("含外部脚本")
    if 'rel="stylesheet"' in document:
        problems.append("含外部样式")
    if "<iframe" in document or "<video" in document:
        problems.append("含 iframe/video")
    remote = re.findall(r'<img[^>]+src="https?://[^"]+"', document)
    if remote:
        problems.append("含远程图片: " + remote[0][:80])
    if document.count('class="book-page"') != len(pages):
        problems.append("页面数量与清单不一致")
    if len(document.encode("utf-8")) >= MAX_HTML_BYTES:
        problems.append("HTML 超过 20 MB")
    images = document.count("<img ")
    formulas = document.count('<span class="arithmatex">')
    report = {"pages": len(pages), "images": images, "formulas": formulas,
              "bytes": len(document.encode("utf-8")),
              "max_asset": max((len(m) for m in re.findall(
                  r'data:[^"]+', document)), default=0)}
    if problems:
        raise BookError("整书审计失败:\n" + "\n".join(problems))
    return report


def build_html(out_dir: Path, site_dir: Path = SITE_DIR,
               rebuild_site: bool = True) -> Path:
    manifest = load_manifest()
    if rebuild_site:
        build_site(site_dir)
    validate_manifest(manifest)
    parts = manuscript(manifest, site_dir)
    for part in parts:
        for page in part["pages"]:
            page["html"] = replace_mermaid(page["html"])
            page["html"] = rewrite_links(
                page["html"], page["stem"],
                {p["stem"] for pp in parts for p in pp["pages"]}, manifest)
            page["html"], _ = inline_images(page["html"])
    document = assemble_book(manifest, parts)
    report = audit_html(document, manifest, parts)
    out_dir.mkdir(parents=True, exist_ok=True)
    output = out_dir / OUTPUT_NAME
    output.write_text(document, encoding="utf-8", newline="\n")
    print(f"html  {output} ({report['bytes']} bytes, {report['pages']} pages, "
          f"{report['images']} images, {report['formulas']} formulas, "
          f"max asset {report['max_asset']} bytes)")
    return output


def check_html(out_dir: Path = DIST_DIR) -> int:
    output = out_dir / OUTPUT_NAME
    if not output.is_file():
        raise BookError(f"整书产物不存在: {output}")
    document = output.read_text(encoding="utf-8")
    manifest = load_manifest()
    match = re.search(r'name="book-manifest-sha256" content="([0-9a-f]+)"', document)
    if not match or match.group(1) != manifest_sha256():
        raise BookError("整书产物与 manifest 不同步，请重新构建")
    parts = manuscript(manifest)
    for part in parts:
        for page in part["pages"]:
            page["html"] = replace_mermaid(page["html"])
            page["html"] = rewrite_links(
                page["html"], page["stem"],
                {p["stem"] for pp in parts for p in pp["pages"]}, manifest)
            page["html"], _ = inline_images(page["html"])
    report = audit_html(document, manifest, parts)
    print(f"check {output} OK ({report['pages']} pages, {report['bytes']} bytes)")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=DIST_DIR)
    parser.add_argument("--site-dir", type=Path, default=SITE_DIR)
    parser.add_argument("--no-build", action="store_true", help="复用已有站点产物")
    parser.add_argument("--check", action="store_true", help="只审计已有整书")
    parser.add_argument("--pdf", action="store_true")
    parser.add_argument("--browser")
    args = parser.parse_args(argv)
    try:
        if args.check:
            return check_html(args.out_dir)
        html_path = build_html(args.out_dir, args.site_dir, not args.no_build)
        if args.pdf:
            build_pdf(html_path, args.browser)
        return 0
    except BookError as exc:
        print(f"book build error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
```

`build_pdf` 在 Task 8 实现；本任务先定义占位会违反“无占位”原则，因此本任务的 `main` 先不引用 PDF，`--pdf` 分支留到 Task 8 再加。运行 Task 6 时 `--pdf` 不传。

- [ ] **Step 4: 跑测试与首次构建**

Run:
```bash
python -B -m unittest discover -s analog-book/tests -p test_build.py -v
python analog-book/build_book.py --no-build
python analog-book/build_book.py --check
```
Expected: 测试 PASS；构建输出 60 pages、约 1500+ images（含 MathJax 生成前的 `<img>` 计数；实际图片约 100 张，公式 span 约 1680）；`--check` OK。

---

### Task 7: 正式书版 CSS 与浏览器冒烟

**Files:**
- Create/Modify: `analog-book/styles/book.css`
- Create: `analog-book/tests/test_browser_book.py`

**Interfaces:**
- Produces: 打印分页、封面/版权/目录、阅读版式、计算器与画廊的静态样式；Playwright 可断言的离线页面。

- [ ] **Step 1: 写正式 `analog-book/styles/book.css`**

```css
@page { size: A4; margin: 18mm 16mm 20mm; }

:root {
  --book-ink: #1f2933;
  --book-muted: #52606d;
  --book-brand: #b45309;
  --book-line: #d9e2ec;
  --book-paper: #fffdf8;
}

html, body {
  margin: 0;
  background: var(--book-paper);
  color: var(--book-ink);
  font-family: -apple-system, "Segoe UI", "PingFang SC", "Microsoft YaHei",
    "Noto Sans CJK SC", sans-serif;
  line-height: 1.75;
}

.book { max-width: 860px; margin: 0 auto; padding: 24px 28px 64px; }
.book-header {
  position: sticky; top: 0; z-index: 20; display: flex; gap: 16px;
  align-items: center; justify-content: space-between;
  padding: 10px 28px; background: rgba(255, 253, 248, .94);
  border-bottom: 1px solid var(--book-line); backdrop-filter: blur(6px);
}
.book-header a { color: var(--book-brand); text-decoration: none; font-weight: 600; }
.book-footer { color: var(--book-muted); text-align: center; padding: 24px; font-size: 13px; }

.book-cover {
  min-height: 225mm; display: flex; flex-direction: column;
  justify-content: center; align-items: flex-start; gap: 18px;
  break-after: page;
}
.book-cover-kicker { color: var(--book-brand); font-size: 20px; letter-spacing: .08em; }
.book-cover-title { font-size: 56px; line-height: 1.15; margin: 0; }
.book-cover-version, .book-cover-site, .book-cover-repo {
  color: var(--book-muted); font-size: 15px; margin: 0; word-break: break-all;
}
.book-copyright { break-before: page; break-after: page; }
.book-copyright h1 { font-size: 30px; }
.book-toc { break-before: page; }
.book-toc h1 { font-size: 34px; margin: 0 0 20px; }
.book-toc-part { margin: 0 0 18px; break-inside: avoid; }
.book-toc-part h2 { font-size: 19px; margin: 0 0 6px; color: var(--book-brand); }
.book-toc ul { margin: 0; padding-left: 20px; columns: 2; column-gap: 32px; }
.book-toc li { break-inside: avoid; font-size: 14px; line-height: 1.6; }
.book-toc a { color: var(--book-ink); text-decoration: none; }

.book-part { break-before: page; }
.book-page { break-before: page; }
.book-part > .book-page:first-of-type { break-before: auto; }
.book-page h1 { margin-top: 0; }
.book-page-back { margin: 28px 0 0; text-align: right; font-size: 13px; }
.book-page-back a { color: var(--book-muted); text-decoration: none; }

.book img, .book svg { max-width: 100%; height: auto; }
.book figure { max-width: 100%; overflow-x: auto; }
.book table { width: 100%; border-collapse: collapse; font-size: 13.5px; }
.book th, .book td { border: 1px solid var(--book-line); padding: 6px 8px; vertical-align: top; }
.book th { background: #f4f7fa; text-align: left; }
.book pre { overflow-x: auto; padding: 12px 14px; background: #f4f7fa; border-radius: 6px; }
.book code { font-family: "Cascadia Mono", Consolas, monospace; font-size: .92em; }
.book blockquote { border-left: 4px solid var(--book-brand); margin-left: 0; padding-left: 14px; color: var(--book-muted); }

.book .arithmatex { overflow-x: auto; overflow-y: hidden; }
.book .calc { border: 1px solid var(--book-line); border-radius: 8px; padding: 12px 14px; break-inside: avoid; }
.book .calc input[type="range"] { max-width: 100%; }
.book .reading-checkpoint { border-top: 1px solid var(--book-line); margin-top: 24px; padding-top: 12px; }
.book .gallery-card { break-inside: avoid; }

@media print {
  .book-header, .book-footer, .book-page-back, .reading-nav { display: none !important; }
  .book { max-width: none; padding: 0; }
  a { color: inherit; text-decoration: none; }
  h1, h2, h3, .calc, .book-toc-part, .gallery-card { break-inside: avoid; }
  h2, h3 { break-after: avoid; }
  [data-page="p0-08-cheatsheet"] h2,
  [data-page="p9-00-quiz"] h2 { break-before: page; }
  [data-page="p5-00-part5"] .gallery-card { break-inside: avoid; }
}
```

- [ ] **Step 2: 浏览器冒烟测试**

`analog-book/tests/test_browser_book.py`：

```python
#!/usr/bin/env python3
"""Playwright 冒烟：离线整书能断网排版公式、渲染计算器并跳转。"""
import sys
import unittest
from pathlib import Path

BOOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BOOK))

import build_book  # noqa: E402

try:
    from playwright.sync_api import sync_playwright
except ImportError:  # pragma: no cover
    sync_playwright = None


@unittest.skipIf(sync_playwright is None, "Playwright 未安装")
class BrowserBook(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        out = BOOK / "dist"
        cls.html = out / build_book.OUTPUT_NAME
        if not cls.html.is_file():
            cls.html = build_book.build_html(out, rebuild_site=False)

    def test_offline_formulas_calculators_and_toc(self):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(reduced_motion="reduce")
            errors = []
            page.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" else None)
            page.goto(self.html.resolve().as_uri(), wait_until="load")
            page.wait_for_function(
                "window.MathJax && MathJax.startup && MathJax.startup.promise",
                timeout=60000)
            page.evaluate("MathJax.startup.promise.then(() => MathJax.typesetPromise())")
            page.wait_for_function(
                "document.querySelectorAll('.mjx-container').length > 1000", timeout=120000)
            self.assertGreater(page.evaluate("document.querySelectorAll('.mjx-container').length"), 1000)
            self.assertGreater(page.evaluate("document.querySelectorAll('[data-calc-ready]').length"), 0)
            page.click('a[href="#page-p1-01-ch0"]')
            page.wait_for_function(
                "document.getElementById('page-p1-01-ch0').getBoundingClientRect().top < 300")
            self.assertEqual([], errors[:5])
            browser.close()
```

Run:
```bash
python analog-book/build_book.py --no-build
python -B -m unittest discover -s analog-book/tests -p test_browser_book.py -v
```
Expected: PASS；`.mjx-container` > 1000；至少一只 `[data-calc-ready]`；无 console error。

---

### Task 8: PDF 构建与后处理

**Files:**
- Modify: `analog-book/build_book.py`
- Create: `analog-book/tests/test_pdf.py`

**Interfaces:**
- Produces:
  - `build_pdf(html_path: Path, browser_override: str | None = None) -> Path`
  - `_stamp_pdf(raw_pdf, output_pdf, manifest, page_titles) -> None`
  - 输出 `dist/analog-circuit-book.pdf`

- [ ] **Step 1: 实现 PDF 构建**

在 `build_book.py` 追加（`main` 的 `--pdf` 分支恢复为调用 `build_pdf`）：

```python
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


def build_pdf(html_path: Path, browser_override: str | None = None) -> Path:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise BookError("PDF 需要 Playwright：pip install -r analog-book/requirements.txt") from exc
    browsers = _browser_candidates(browser_override)
    executable = browsers[0] if browsers else None
    if browser_override and executable is None:
        raise BookError(f"浏览器不存在: {browser_override}")
    output = html_path.with_name(PDF_NAME)
    raw_pdf = html_path.with_name(".analog-book.raw.pdf")
    manifest = load_manifest()
    try:
        with sync_playwright() as playwright:
            launch = {"headless": True}
            if executable:
                launch["executable_path"] = str(executable)
            browser = playwright.chromium.launch(**launch)
            try:
                context = browser.new_context(reduced_motion="reduce")
                page = context.new_page()
                page.goto(html_path.resolve().as_uri(), wait_until="load")
                page.evaluate("document.fonts ? document.fonts.ready : Promise.resolve()")
                page.wait_for_function(
                    "window.MathJax && MathJax.startup && MathJax.startup.promise",
                    timeout=60000)
                page.evaluate("MathJax.startup.promise.then(() => MathJax.typesetPromise())")
                page.wait_for_function(
                    "document.querySelectorAll('.mjx-container').length > 1000",
                    timeout=120000)
                page.wait_for_function(
                    "Array.from(document.images).every(img => img.complete && img.naturalWidth > 0)",
                    timeout=30000)
                page.pdf(path=str(raw_pdf), print_background=True,
                         prefer_css_page_size=True, outline=True, tagged=True)
            finally:
                browser.close()
        _stamp_pdf(raw_pdf, output, manifest)
    except BookError:
        raise
    except Exception as exc:
        raise BookError(f"PDF 构建失败: {exc}") from exc
    finally:
        raw_pdf.unlink(missing_ok=True)
    print(f"pdf   {output} ({output.stat().st_size} bytes)")
    return output


def _pdf_page_titles(html_text: str) -> list[tuple[str, str]]:
    return re.findall(
        r'<section class="book-page" id="page-[^"]+" data-page="([^"]+)" data-title="([^"]+)"',
        html_text)


def _stamp_pdf(raw_pdf: Path, output_pdf: Path, manifest: dict) -> None:
    try:
        import fitz
    except ImportError as exc:
        raise BookError("PDF 需要 PyMuPDF：pip install -r analog-book/requirements.txt") from exc
    document = fitz.open(raw_pdf)
    try:
        document.set_metadata({
            "title": manifest["title"],
            "author": manifest["author"],
            "subject": manifest["subtitle"],
            "keywords": "模拟电路, STM32, 电子, 离线书, " + manifest["license"],
            "creator": "analog-circuit-roadmap/build_book.py",
        })
        # 目录页：从「全书目录」出现到首个无内部链接的页
        toc_pages, in_toc = [], False
        for index, page in enumerate(document):
            text = page.get_text()
            if "全书目录" in text:
                in_toc = True
            if not in_toc:
                continue
            links = [l for l in page.get_links() if isinstance(l.get("page"), int)]
            if not links:
                break
            toc_pages.append(index)
        if not toc_pages:
            raise BookError("PDF 中找不到目录页")
        body_start = min(
            link["page"] for index in toc_pages for link in document[index].get_links()
            if isinstance(link.get("page"), int) and link["page"] > max(toc_pages))
        # 目录页码
        for index in toc_pages:
            page = document[index]
            for link in page.get_links():
                target = link.get("page", -1)
                if target < body_start:
                    continue
                rect = fitz.Rect(link["from"])
                label = str(target - body_start + 1)
                width = fitz.get_text_length(label, fontname="helv", fontsize=8)
                page.insert_text(
                    fitz.Point(page.rect.width - 46 - width, rect.y1 - 2),
                    label, fontname="helv", fontsize=8, color=(0.38, 0.42, 0.45))
        # 页面标题（来自 HTML，顺序与 Chrome 大纲 h1 一致）
        html_path = output_pdf.with_name(OUTPUT_NAME)
        page_titles = _pdf_page_titles(html_path.read_text(encoding="utf-8"))
        outline = [entry for entry in document.get_toc()
                   if entry[0] == 1 and entry[2] >= body_start]
        if len(outline) != len(page_titles):
            raise BookError(
                f"PDF 大纲 {len(outline)} 个一级标题，HTML 页面 {len(page_titles)} 个；无法定位页眉")
        starts = [entry[2] - body_start for entry in outline]
        # 书签：篇 = 一级，页 = 二级
        toc = []
        page_index = 0
        for part in _parts_with_titles(page_titles, starts):
            toc.append([1, part["title"], starts[part["first"]] + 1])
            for offset, (stem, title) in enumerate(part["pages"]):
                toc.append([2, title, starts[part["first"] + offset] + 1])
        document.set_toc(toc)
        # 页码标签：正文从 1 开始
        document.set_page_labels([{
            "startpage": body_start, "prefix": "", "style": "D", "firstpagenum": 1}])
        # 页眉与页脚
        short_title = manifest["title"]
        total = max(1, document.page_count - body_start)
        section_starts = {start + body_start: title for (stem, title), start
                          in zip(page_titles, starts)}
        for index in range(document.page_count):
            if index < body_start:
                continue
            page = document[index]
            printed = index - body_start + 1
            label = f"{printed} / {total}"
            width = fitz.get_text_length(label, fontname="helv", fontsize=8)
            page.insert_text(
                fitz.Point((page.rect.width - width) / 2, page.rect.height - 10),
                label, fontname="helv", fontsize=8, color=(0.38, 0.42, 0.45))
            header = short_title if printed % 2 == 1 else section_starts.get(index, "")
            if not header:
                continue
            hwidth = fitz.get_text_length(header, fontname="china-s", fontsize=7.5)
            x = 46 if printed % 2 == 1 else page.rect.width - 46 - hwidth
            page.insert_text(fitz.Point(x, 22), header, fontname="china-s",
                             fontsize=7.5, color=(0.38, 0.42, 0.45))
            page.draw_line(fitz.Point(46, 28), fitz.Point(page.rect.width - 46, 28),
                           color=(0.72, 0.74, 0.76), width=0.35)
        document.save(output_pdf, garbage=3, deflate=True)
    finally:
        document.close()


def _parts_with_titles(page_titles, starts):
    manifest = load_manifest()
    order = [f["files"] and Path(f["files"][0]).stem for f in manifest["parts"]]
    sizes = [len(f["files"]) for f in manifest["parts"]] + [len(manifest["appendix"]["files"])]
    titles = [t for _, t in page_titles]
    offset, parts = 0, []
    for number, size in enumerate(sizes):
        part_pages = page_titles[offset:offset + size]
        title = manifest["appendix"]["title"] if number == len(sizes) - 1 else titles[offset]
        parts.append({"title": title, "first": offset, "pages": part_pages})
        offset += size
    return parts
```

`_stamp_pdf` 依赖大纲顺序与 HTML 页面顺序完全一致；Chrome 会把每个 `<h1>` 作为一级大纲，但页面内 `<h2>` 是二级，过滤 `entry[0] == 1` 后正好 60 项（封面/版权/目录的 h1 在 `body_start` 之前，被过滤）。若页内还有 h1（site 清洗后每页一个），数量吻合。

`_parts_with_titles` 用 manifest 的篇大小切分 `page_titles`，不依赖标题文本，避免 emoji/HTML 转义差异。

- [ ] **Step 2: PDF 测试**

`analog-book/tests/test_pdf.py`：

```python
#!/usr/bin/env python3
"""PDF 结构冒烟：页数、元数据、书签、页码与封面无页码。"""
import json
import sys
import unittest
from pathlib import Path

BOOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BOOK))

import build_book  # noqa: E402

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
class PdfBook(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = BOOK / "dist" / build_book.OUTPUT_NAME
        if not cls.html.is_file():
            build_book.build_html(BOOK / "dist", rebuild_site=False)
        cls.pdf = build_book.build_pdf(cls.html)

    def test_pdf_structure(self):
        document = fitz.open(self.pdf)
        try:
            self.assertGreater(document.page_count, 40)
            self.assertEqual("通往模拟电路之路", document.metadata["title"])
            toc = document.get_toc()
            self.assertEqual(11, sum(1 for level, _, _ in toc if level == 1))
            self.assertEqual(60, sum(1 for level, _, _ in toc if level == 2))
            # 封面/版权/目录无页码：前 3 页不含 " / " 页脚
            for index in range(min(3, document.page_count)):
                self.assertNotIn(" / ", document[index].get_text())
            # 目录条目已盖印页码
            toc_text = "".join(document[i].get_text() for i in range(min(3, document.page_count)))
            self.assertRegex(toc_text, r"\b[1-9]\d*\b")
            # 正文页有页码
            self.assertIn(" / ", document[document.page_count - 1].get_text())
        finally:
            document.close()
```

Run:
```bash
python analog-book/build_book.py --no-build --pdf
python -B -m unittest discover -s analog-book/tests -p test_pdf.py -v
```
Expected: PASS；PDF > 40 页；一级书签 11、二级 60；封面无页码。

---

### Task 9: Makefile、统计脚本、CI、项目文档

**Files:**
- Create: `Makefile`
- Create: `scripts/build_stats.py`
- Create: `.github/workflows/book.yml`
- Create: `analog-book/README.md`
- Create: `analog-book/requirements.txt`
- Modify: `.gitignore`
- Modify: `CONTRIBUTING.md`

**Interfaces:**
- Produces: `make readme/site/book/book-pdf/book-check/test-static/test-browser/verify/stats/clean`；CI 作业 `book`。

- [ ] **Step 1: 创建 `Makefile`**

```make
PY ?= python

.PHONY: readme site book book-pdf book-check test-static test-browser verify stats clean

readme:
	$(PY) scripts/build_readme.py

site:
	$(PY) scripts/build_site.py --build

book:
	$(PY) analog-book/build_book.py

book-pdf:
	$(PY) analog-book/build_book.py --pdf

book-check:
	$(PY) analog-book/build_book.py --check --no-build

test-static:
	$(PY) -B -m unittest discover -s scripts -p "test_svg_assets.py" -v
	$(PY) -B -m unittest discover -s scripts -p "test_readme_links.py" -v
	$(PY) -B -m unittest discover -s scripts -p "test_a11y.py" -v
	$(PY) -B -m unittest discover -s scripts -p "test_docs_sync.py" -v
	$(PY) -B -m unittest discover -s scripts -p "test_docs_links.py" -v
	$(PY) -B -m unittest discover -s scripts -p "test_split_readme.py" -v
	$(PY) -B -m unittest discover -s scripts -p "test_page_structure.py" -v
	$(PY) -B -m unittest discover -s scripts -p "test_release_gate.py" -v
	$(PY) -B -m unittest discover -s scripts -p "test_site_build.py" -v
	$(PY) -B -m unittest discover -s scripts -p "test_smartsymbols.py" -v
	$(PY) -B -m unittest discover -s analog-book/tests -p "test_build.py" -v

test-browser:
	$(PY) -B -m unittest discover -s scripts -p "test_reading_journey.py" -v
	$(PY) -B -m unittest discover -s scripts -p "test_diagnostic.py" -v
	$(PY) -B -m unittest discover -s scripts -p "test_gallery_interactions.py" -v
	$(PY) -B -m unittest discover -s scripts -p "test_learning_interactions.py" -v
	$(PY) -B -m unittest discover -s scripts -p "test_waveform_timing.py" -v
	$(PY) -B -m unittest discover -s scripts -p "test_svg_layout.py" -v
	$(PY) -B -m unittest discover -s scripts -p "test_svg_contrast.py" -v
	$(PY) -B -m unittest discover -s scripts -p "test_reduced_motion.py" -v
	$(PY) -B -m unittest discover -s scripts -p "test_first_screen.py" -v
	$(PY) -B -m unittest discover -s analog-book/tests -p "test_browser_book.py" -v

verify: test-static
	$(PY) scripts/build_readme.py --check
	$(PY) analog-book/build_book.py
	$(PY) analog-book/build_book.py --check --no-build

stats:
	$(PY) scripts/build_stats.py

clean:
	rm -rf build analog-book/dist
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
```

- [ ] **Step 2: 创建 `analog-book/requirements.txt`**

```text
Playwright>=1.61,<2
PyMuPDF>=1.28,<2
```

- [ ] **Step 3: 统计脚本**

`scripts/build_stats.py`：

```python
#!/usr/bin/env python3
"""打印仓库内容规模：文档页、动画、题库、视频与测试数。"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"


def main() -> None:
    pages = [p for p in DOCS.glob("*.md") if p.name != "index.md"]
    svgs = list((ROOT / "assets" / "svg").glob("*.svg"))
    quiz_ids = set()
    videos = set()
    for page in pages:
        text = page.read_text(encoding="utf-8")
        quiz_ids.update(re.findall(r'<details class="quiz" id="([^"]+)"', text))
        quiz_ids.update(re.findall(r'<div class="quiz[^"]*" id="([^"]+)"', text))
        videos.update(re.findall(r"youtube\.com/watch\?v=([\w-]+)", text))
        videos.update(re.findall(r"youtube\.com/embed/([\w-]+)", text))
    tests = list((ROOT / "scripts").glob("test_*.py"))
    tests += list((ROOT / "analog-book" / "tests").glob("test_*.py"))
    print(f"文档页      {len(pages)}")
    print(f"SVG 动画    {len(svgs)}")
    print(f"题库条目    {len(quiz_ids)}")
    print(f"视频        {len(videos)}")
    print(f"测试文件    {len(tests)}")
    print(f"公式 span   {sum(p.read_text(encoding='utf-8').count('arithmatex') for p in pages)}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: CI**

`.github/workflows/book.yml`：

```yaml
name: book

on:
  push:
    branches: [main]
  pull_request:
  workflow_dispatch:

permissions:
  contents: read

jobs:
  book:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install -r requirements.txt -r analog-book/requirements.txt
      - run: python -m playwright install --with-deps chromium
      - name: 站点构建
        run: python scripts/build_site.py --build
      - name: 整书单元与审计
        run: python -B -m unittest discover -s analog-book/tests -p "test_build.py" -v
      - name: 整书 HTML
        run: python analog-book/build_book.py --no-build
      - name: 产物审计
        run: python analog-book/build_book.py --check
      - name: PDF
        run: python analog-book/build_book.py --no-build --pdf
      - name: PDF 结构测试
        run: python -B -m unittest discover -s analog-book/tests -p "test_pdf.py" -v
      - uses: actions/upload-artifact@v4
        with:
          name: analog-circuit-book
          path: |
            analog-book/dist/analog-circuit-book.html
            analog-book/dist/analog-circuit-book.pdf
          retention-days: 14
```

- [ ] **Step 5: `.gitignore`、`analog-book/README.md`、`CONTRIBUTING.md`**

`.gitignore` 末尾追加：

```gitignore
analog-book/dist/
```

`analog-book/README.md`：

```markdown
# 离线整书

从 `docs/` 构建《通往模拟电路之路》的单文件 HTML 与 A4 PDF。内容源仍在 `docs/`，本目录只放构建器、清单与样式。

## 构建

```bash
pip install -r requirements.txt -r analog-book/requirements.txt
python -m playwright install chromium   # 或使用本机 Edge/Chrome
python analog-book/build_book.py        # 站点 + HTML
python analog-book/build_book.py --pdf  # 追加 PDF
python analog-book/build_book.py --check --no-build  # 只审计已有产物
```

- 默认调用 `scripts/build_site.py --build`；`--no-build` 复用 `build/site`。
- 产物在 `analog-book/dist/`（gitignored）：`analog-circuit-book.html`、`analog-circuit-book.pdf`。
- 新增/删除内容页必须同步 `manifest.json`，否则整书审计失败。
- 书内禁止远程图片、外链样式/脚本、iframe/video；第三方资产先本地化并登记 `docs/p9-14-credits.md`。
- Mermaid 路线图使用 `static/roadmap.svg`；改 `docs/p0-06-roadmap.md` 后必须重新生成 `roadmap.source.txt`/`roadmap.svg`。
- 缺 Playwright/PyMuPDF 时 HTML 仍可构建；PDF 测试自动 skip。
```

`CONTRIBUTING.md` 末尾追加：

```markdown
## 整书与离线产物

- 改 `docs/` 后先 `make readme`；涉及整书标题或页面范围时运行 `make book`。
- 新增内容页必须加入 `analog-book/manifest.json`，否则整书审计红灯。
- 新增第三方图片/字体/代码资产必须更新 `docs/p9-14-credits.md`。
- 不直接编辑 `README.md`、`build/`、`analog-book/dist/`。
- 提交前跑 `make verify`；改了交互/样式再跑 `make test-browser`。
```

- [ ] **Step 6: 验证命令可用（本机用 `mingw32-make`）**

Run:
```bash
mingw32-make stats
mingw32-make book-check
python -B -m unittest discover -s analog-book/tests -p test_build.py -v
```
Expected: 统计输出 60 页/108 张 SVG/20 视频左右；`book-check` OK。

---

### Task 10: 全量验收

**Files:** 无新增；只运行命令并修复回归。

- [ ] **Step 1: 静态组**

Run:
```bash
mingw32-make test-static
```
Expected: 全部 PASS。

- [ ] **Step 2: 整书与确定性**

Run:
```bash
python analog-book/build_book.py --no-build
python analog-book/build_book.py --check
python - <<'PY'
import hashlib, pathlib, tempfile, sys
sys.path.insert(0, 'analog-book')
import build_book
out = pathlib.Path(tempfile.mkdtemp())
a = build_book.build_html(out / 'a', rebuild_site=False)
b = build_book.build_html(out / 'b', rebuild_site=False)
ha = hashlib.sha256(a.read_bytes()).hexdigest()
hb = hashlib.sha256(b.read_bytes()).hexdigest()
assert ha == hb, (ha, hb)
print('determinism PASS', ha)
PY
```
Expected: `check ... OK`；`determinism PASS`；HTML < 20 MB。

- [ ] **Step 3: PDF 与浏览器**

Run:
```bash
python analog-book/build_book.py --no-build --pdf
python -B -m unittest discover -s analog-book/tests -p "test_pdf.py" -v
mingw32-make test-browser
```
Expected: PDF 结构测试 PASS；现有浏览器回归全 PASS。

- [ ] **Step 4: README/链接/首页回归**

Run:
```bash
python scripts/build_readme.py --check
python -B -m unittest discover -s scripts -p test_docs_sync.py -v
python -B -m unittest discover -s scripts -p test_readme_links.py -v
python -B -m unittest discover -s scripts -p test_first_screen.py -v
```
Expected: 全 PASS；README 与 docs 同步；首页 10 行直查链接全部可达。

- [ ] **Step 5: 人工验收**

打开 `analog-book/dist/analog-circuit-book.html`（断网）：
- 目录可跳转；公式已排版；图片可见；至少一只计算器默认读数正确。
- 页面内没有编辑按钮、¶ 锚点、共建页脚；章末自测入口仍在。

打开 `analog-book/dist/analog-circuit-book.pdf`：
- 封面/版权/目录齐全；篇与每页另起页；目录右侧页码正确；奇数页眉书名、偶数页眉当前页标题；封面/版权/目录无页码。
- 书签一级 11 项、二级 60 项。

---

## 风险与回退

- 若整书 HTML 超过 20 MB：先报告最大资源；优先对 p5 画廊重复内嵌的 SVG 做同图去重（同一 `src` 只编码一次并复用 data URI），仍超限再降照片尺寸。
- 若 Chrome 未生成大纲导致 PDF 页标题数量不匹配：`_stamp_pdf` 直接失败并报告数量；回退方案是用 HTML `data-title` 顺序 + `page.get_text()` 逐页首行匹配定位，仍需保持页页另起。
- 若站点产物结构调整导致 `<article>` 抽取失败：构建器立即失败；先修 `scripts/build_site.py` 或选择器，不做静默降级。
- 若本机 Memory/临时目录丢失：照片与 MathJax 均有重新下载命令；`static/roadmap.svg` 可由 Task 3 脚本重建。
