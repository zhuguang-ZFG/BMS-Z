# 两卷合集构建

《从模拟电路到 BMS》由卷一《通往模拟电路之路》和卷二《BMS 实战》组成。

先用 `book/build.py` 构建所需分卷成品，再运行：

```powershell
python -X utf8 book/build.py combined
python -X utf8 book/downloads.py --site-dir book/dist/site
```

输出在 `book/dist/combined/`：

- `from-analog-to-bms.pdf`：合集封面、共享卷首、按实际 PDF 书签生成的可点击总目录、两卷正文。原卷页脚不变；总目录列出卷内页和文件页，PDF 页码标签使用 `I-`、`II-` 前缀。
- `from-analog-to-bms.epub`：共用一套合集卷首与封面。跨卷源文链接和带卷次的章节文字引用改成书内链接。书籍标识稳定，修改时间随构建更新，ZIP 内容采用无损压缩。
- `combined-build-report.json`：输入与输出哈希、构建器源码哈希、提交和未提交状态、链接修复数量与校验结果。

下载页会复制合集构建记录，并检查它的输出哈希与当前文件一致。顶层 `book/dist/build-report.json` 的 `combined` 字段记录本次合集检查；原有分卷检查的时间不会被冒充更新。

合集构建先写临时成品并校验，通过后才替换正式文件。输入分卷若在构建期间变化，会停止替换。此流程只生成本地成品，不发布站点。

验证命令：

```powershell
python -X utf8 -m unittest discover -s book/tests -v
python -X utf8 book/build_combined.py --check
```

EPUB 检查包含 CRC、XML、重复 ID、资源和锚点、阅读顺序、目录覆盖、合集封面、OPF/NCX 标识及跨卷外链。设置 `EPUBCHECK_JAR` 后，构建和 `--check` 都调用官方 EPUBCheck；错误或警告会阻止成品替换。Pages 与站点 CI 固定使用 5.4.0，并核对安装包 SHA-256。构建记录保存实际检查版本与结果。

PDF 检查逐页比较保留正文，并逐条核对原链接的区域、目标页和落点，以及新增总目录和页码标签。

```powershell
python -X utf8 book/check_compatibility.py --channel msedge
# CI 默认使用已安装的 Playwright Chromium；检查另一份站点可加 --site 路径。
```

自动显示检查覆盖下载页的桌面、320/360 像素小屏、200% 字号、深色、灰度、键盘滑块与关闭 JavaScript；EPUB 的全部 spine 文档在 390 像素、28px 字号下检查溢出和缺图，另检查两卷的深色正文。JSON 与截图存入 `book/dist/compatibility/`。这些是软件自动化结果，不能充当实体阅读器导入、触控、刷新与续航记录。

下载页与封面采用“工程师的实验手记”：以同一电芯的两次电压观察引入测量、保护和估算三条路线。下载页设计审查参考 Unslop，Damir Sokolovsky，CC BY 4.0；本项目的插画、公式示例与版式均单独实现。

卷首的“三次观察，一张手记”将静置、带载与撤去负载画成三个连续读数，并附换电流计算、解释电压回升、判断证据是否足够的三题与对照解。PDF 和 EPUB 共用 `reading_lab.py` 的内容；网页用原生折叠答案，关闭 JavaScript 仍可核对。参考成品书的具体差异见 [开放教材对比与改进](REFERENCE_REVIEW.md)。

正文另有 20 幅“手绘札记”，分布于卷 I 的 4 章、卷 II 的 16 章，补充 RC、米勒平台、虚短条件、探头负载，以及采样、保护、估算、通信、数据与热路径。每幅都有原生文字图注和观察题，静态阅读时保留完整过程。`reading-sketches.json` 记录插入位置、解释目的和图型，`generate_reading_sketches.py` 维护可编辑的原创 SVG；这些是程序绘制的矢量线稿，并非图像模型生成。重新生成运行 `python book/generate_reading_sketches.py`；一致性检查加 `--check`。

手绘的文字嵌入固定 Noto Serif 字体，并按每幅图的实际用字精简，避免服务器字体回退导致 PDF 中的数字复制成字母。字库来源、SHA-256 与两份 OFL 许可保存在 `assets/ReadingSketch.*` 和 `assets/ReadingSketch*-OFL.txt`；重新生成字库使用 `--font-source analog/build/fonts-src/NotoSerifSC-VF.ttf`。发布前运行 `python book/check_reading_sketches.py`，逐图检查 PDF 的完整文字、数字、同页图注与问题，以及 EPUB 中的 SVG 原文件。

仅修改合集编排时，可手动触发 `deploy-pages`，传入成功全量发布的 `collection_base_run`。`refresh_collection.py` 检查基线提交为当前提交的祖先，且差异全部在合集构建器、下载页、检查和说明的白名单内；正文、站点、依赖或总清单变化会拒绝。随后从该 run 的 Pages 产物恢复两卷六份文件，逐份核对哈希，再重建合集并运行原有发布检查。构建记录额外保留基线 run、提交与原报告哈希；不把复用正文冒充重新生成。增量发布不能再作为另一轮增量的基线。
