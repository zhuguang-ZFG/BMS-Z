---
search: false
---

# handraw 真源树（路径 B）

- `prompts/<slug>.md` — 提示词（默认交付；未授权「出图」时只维护这里）
- `storyboard/<slug>/frame-01.webp` … `frame-08.webp` — 位图帧真源（3–8 帧）
- `storyboard/<slug>/frame-NN.svg` — 自绘矢量源（可编辑）；栅格化为 960×560 WebP（q97），改图后重出同名 `.webp` 再跑导出
  - 栅格化：用 Playwright 的 `channel="msedge"`（与 `bms-book/snapshot_visuals.py` 同款）打开同目录 SVG，视口 960×560、`device_scale_factor=1` 截图 PNG，再用 Pillow 存 WebP（q97，不缩放）。Git Bash 里直接调 `msedge --headless` 会报 `command not found`（PowerShell 调用会挂起），不要写进流程。
  - 字体：帧 SVG 用 `font-family="KaiTi"`，需本机装有 KaiTi（Windows `simkai.ttf`）。缺字体时会回退、字宽改变而可能压字——没有 KaiTi 就别重出帧。`tools/check_handraw_manifest.py` 的几何门按**源 SVG 的字号与坐标**判压字 / 压线 / 压曲线（`path` 曲线按段采样）/ 出界，属性沿 `<g>` 继承、旋转文本按四角包围盒；它查不出「字体回退把字变宽」这一类——门绿不等于换字体后还绿
- `exports/<slug>.webp` — 可暂停动画；`<slug>-start.webp` / `<slug>-end.webp` 打印首末帧
- `manifest.json` — 全量登记；校验见 `tools/check_handraw_manifest.py`

画风：FA-002 机制 / FA-029 信息结构。色：C-03 主色，C-15 仅危险。图注：原理示意 / 非实拍。
旧几何 SVG → `docs/circuits/assets/archive/`（`hppc-pulse` → `bms-book/assets/archive/`）。
过渡：未归档旧 SVG 仍守 `docs/circuits/动画画风规范.md`；handraw 产物守 `docs/visual-style-pack.md`。
