# 设计

两图沿用 800 px 画布、手帐装饰与语义配色。被动画回路简图，主动用能量路径和电感电流示意图。常显的阶段提示承担静态阅读，播放层仅高亮当前状态。沿用 VitePress 的无 SMIL 派生图和滚动容器，从已有资产清单匹配图片。书籍使用各自的静态资产，不需要改打包逻辑。
New standalone SVG diagrams retain a readable static layer. In the site renderer, keep live and still filenames in REDUCED_MOTION_ASSETS. A generated still strips SMIL and hides the playback group. If a still needs one SVG state, give that element a meaningful base value outside playback and test the browser's reduced-motion setting.
