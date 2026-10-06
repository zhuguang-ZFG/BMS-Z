# 用 Obsidian 打开

> **本篇你会学到**　这个仓库怎么当成一个 Obsidian 库打开，动画在阅读视图里怎么播。
> **预计用时**　五分钟。
> **前置**　已经装好 Obsidian。不用它也不影响在 GitHub 上学习。

仓库根目录就是一个 Obsidian 库：Obsidian →「打开本地文件夹」选本仓库即可。共享配置已随仓库提交（`.obsidian/`）：新建链接走「相对路径 Markdown 链接」，与 GitHub 渲染规则一致；个人窗口布局按 [.gitignore](../.gitignore) 约定不入库。

- 教程与详解正文**内嵌**的 SMIL 动画，在 Obsidian 阅读视图中直接播放；配色跟随**所在页面的**深浅主题：GitHub 与 Obsidian 都会把自身主题写入页面 `color-scheme`，SVG 按它取色（Obsidian 1.13.7 实机验证：BMS-Z vault 打开 stage-0，阅读视图内动画实测在播、深色主题下 SVG 正确走深色分支），不依赖操作系统设置。
- [docs/circuits/README.md](circuits/README.md) 收录的 147 张动画与电路图是**链接**而非内嵌：点击后由系统默认应用打开（Windows 上通常是浏览器，动画照常播放）。
- 跨文件小节锚点（如 `bms-resources.md#62-算法精通`）按 GitHub 规则生成并受 CI 校验：Obsidian 能打开目标文件，但小节跳转以 GitHub 网页端为准（两家锚点规则不同）。
- [BMS学习路径.html](../BMS学习路径.html) 等 HTML 文件在 Obsidian 中点击会用默认浏览器打开。

**上一篇**　[README](../README.md) ｜ **目录**　[阶段教程](../README.md#阶段教程) ｜ **下一篇**　[动画索引](circuits/README.md)
