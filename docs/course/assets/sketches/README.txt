# 连续课程手绘图源

这七张图使用项目已有的自绘 SVG → WebP 流程，数字来自课程同一教学电池包。风格沿用 FA-002 连续墨线、C-03 普鲁士蓝与少量 C-15 危险标记；构图参考 IG-002 结构标注、IG-004 对照、IG-008 流程。图是原理示意，不是照片或实验读数。

`tools/generate_course_sketches.py` 保存可编辑图形、布局和标注。需要修改时先改生成器，再生成 SVG：

```sh
python tools/generate_course_sketches.py
python tools/generate_course_sketches.py --check
```

确认图中连接、方向、单位与课文一致后，用本机已有的 Playwright、Edge/Chrome、Pillow 和 KaiTi 字体导出高清静态 WebP：

```sh
python tools/render_course_sketches.py --browser-channel msedge
python tools/render_course_sketches.py --check
```

SVG 画布为 1440×1080，正文 WebP 为 2880×2160。渲染器确认实际 KaiTi 字体和文字边界；没有字体时停止，不自动换字体。`manifest.json` 记录 SVG、渲染器、字体和输出文件的摘要，`--check` 只用标准库，可在没有浏览器或 KaiTi 的 CI 中校验已入库产物。

正文引用 WebP，离线 HTML 内嵌同一图片，EPUB 打包时转成兼容性更好的 PNG。PDF 保留高分辨率图片；七张图不进入动画数量，也不计作专项照片。字形边界与摘要通过不能替代图意和手机阅读检查。

本轮逐图审阅包括：串联极性与闭合路径、电流箭头方向、带载两端读数、函数数据流与接线的区别、校正位移方向、样本年龄端点、命令与反馈时序。正文每张图都配有具体观察题。验收记录见 `docs/superpowers/plans/2026-11-08-beginner-readability.md`。
