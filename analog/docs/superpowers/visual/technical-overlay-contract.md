# 技术图层与印刷交付契约

`scripts/compose_technical_overlay.py` 把无文字底图和 SVG 技术图层合成到同一画布。
纸雕底图表达媒介和注意力；电路、公式、数值、单位与中文标注只出现在 SVG 图层。

## 输入与输出

每张图保存一份 JSON，字段为 `id`、`title`、`alt`、`canvas`、`print_width_mm`、
`paper`、`base_image`、`overlay`、`output`。文件路径相对项目根目录，画布默认
1448×1086。`print_width_mm` 取实际版心，本轮按更保守的 138mm 验证。

- `base_image`：PNG/WebP/JPEG，无文字；宽高比须与画布相同，不静默裁切。
- `base_svg`：用户授权的 Python 矢量纸层底图，与 `base_image` 二选一；只允许无文字静态图形。
  矢量底图在打印版中保留实体图形、去掉 `data-paper-shadow` 阴影，因此不会丢掉芯片、工具或传热链。
- `overlay`：与画布同 viewBox 的静态 SVG；不允许脚本、外链、内嵌 HTML 或外部样式。
- `output`：合成 SVG，底图以 data URI 内嵌，技术标注仍为矢量。
- 同名 `-print.svg`：去掉位图底图，保留纸色和完整技术图层；印刷无需网络或底图文件。
- `--preview`：生成 PNG、无损 WebP、灰度 PNG 与 `.audit.json`。真实浏览器检查文字边界和
  变换后的有效字号；最低 8.5pt，文字与声明纸底对比度至少 4:1。

```bash
python scripts/compose_technical_overlay.py --spec <composition.json> --preview
```

底图尚未生成时，允许显式使用 `--print-only` 输出技术校样。此路径不会生成合成 SVG，
也不会替资产填写评分或改变状态。机器检查不代替对纸雕构图、标注遮挡及色盲辨识的人工复评。

## 进入正文之前

正式产物放在 `assets/figures-v2/`，在 `visual-manifest.yml` 登记 `output`、`print_fallback`、
可选 `preview` 与 `alt`。替代文字必须讲明图意。所有派生 SVG/WebP 都纳入磁盘登记校验。
`analog-book/book/content.py` 按 manifest 选用纯 SVG 印刷图；V2 动画选用 `storyboard`。
未审图的 V2 静态图和缺失回退会阻断书构建。字体子集扫描包含 figures-v2、svg-v2 和 storyboards-v2。

`animation-v2-manifest.yml` 是主 manifest 的派生动画视图，不单独编辑：

```bash
python scripts/check_visual_manifest.py --write-animation-index
python scripts/check_visual_manifest.py --transition <id> reviewed
```

`status_history` 从 planned 逐级到达当前状态；迁移命令一次只前进一步，并在写入前检查评分与文件。
对照两份快照可用 `--previous <old-manifest.yml>`，即使手填完整履历，一次跨越多个阶段也会失败。
动画须声明具名 `beats`、`duration`、`parameters`、`conclusion_frame`、`reduced_motion` 和 `storyboard`。
没有参数扫描时显式写 `parameters: []`；A3 不允许空扫描列表。

来源检查限定在 `source_facts` 指向的小节。除 prompt 的 `numbers` 外，还扫描 SVG 中实际可见的
数字，防止漏填声明。教学示意值在 `numbers` 中逐项写 `{value, label: 示意, reason}`，
并在图内可见文字标注“示意”；不能仅在隐藏描述里标注。

## 接触表与本轮校样

```bash
python scripts/build_visual_contact_sheet.py --wave ch17 --out <review.html> --grayscale --page-size 18
```

每页可选 12、18、24 张；支持嵌套输出目录，动画使用静帧预览并保留七项评分。
缺图显示“待生成”，不会用破图或旧底图冒充新试片。

本轮三张技术校样在 `reviews/quant-pilot-2026-11-05/index.html`；对应提示词在
`prompts/quant-pilot/`。它们未进入生产 manifest、未回填正文，风格评分为空。
其输出由 `scripts/build_quant_pilot.py` 重建；该命令只生成技术图层与提示词，不调用生图服务。
