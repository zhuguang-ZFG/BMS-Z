# 连续课程手绘图源

这 24 张图覆盖连续课程全部 24 课，使用项目已有的自绘 SVG → WebP 流程，数字来自课程同一教学电池包。风格沿用 FA-002 连续墨线、C-03 普鲁士蓝与少量 C-15 危险标记；构图参考 IG-002 结构标注、IG-004 对照、IG-008 流程。图是原理示意，不是照片或实验读数。

`tools/generate_course_sketches.py` 保存公共图形原语与第 1–6 / 9 课布局；`tools/course_sketches_protection.py` 维护第 7–8 / 10–12 课，`tools/course_sketches_charge_comms.py` 维护第 13–18 课，`tools/course_sketches_engineering.py` 维护第 19–24 课。主命令统一生成并校验全部图。需要修改时先改对应生成模块，再生成 SVG：

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

正文引用 WebP，离线 HTML 内嵌同一图片，EPUB 打包时转成兼容性更好的 PNG。PDF 保留高分辨率图片；24 张静态图不进入动画数量，也不计作专项照片。字形边界与摘要通过不能替代图意和手机阅读检查。

课程清单 `docs/course/manifest.json` 的 `illustration` 指定每课的主图，`tools/check_course.py` 检查本课解释中实际引用且不重复。原七图验收见 `docs/superpowers/plans/2026-11-08-beginner-readability.md`；全程手绘的图意、物理关系和出版验收见 `docs/superpowers/plans/2026-11-08-course-illustrations.md`。正文每张图都配有具体观察题，不能提前给出独立题答案。
