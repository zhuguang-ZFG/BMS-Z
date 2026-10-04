# 参与共建（CONTRIBUTING）

感谢愿意出手。这个仓库是**中文自学路线**，一切改动以"后来的读者少走弯路"为判据。

## 两条轻量入口（不用写代码）

- **内容纠错**：[Issue 纠错模板](https://github.com/zhuguang-ZFG/BMS-Z/issues/new/choose) —— 写清文件+小节、原文、应为、依据（datasheet / 标准 / 实测）。错别字、死链也算。
- **内容建议**：同上入口选「内容建议」 —— 想看的主题、资料或呈现方式；能说清"它解答什么真实问题"的建议最容易被采纳。

## 直接提 PR

小改动（错别字、死链、表述歧义）直接提；**涉及结构、新增页面/动画、外链清单的改动，建议先开 Issue 对齐**。

### 内容约定（PR 会被按这些逐条看）

1. **全中文**：术语以 [docs/glossary.md](docs/glossary.md) 为准；新术语进表，定义 2–3 句 + 一句"什么时候会遇到它"。
2. **标题锚点是公共合同**：既有小节标题不改字（外部链接与交叉引用按 GitHub slug 规则指向它们）；新增小节标题避免与既有撞名。
3. **教程↔详解的"摘要+链接"螺旋结构是刻意设计**，不是重复内容，不要"顺手去重"。
4. **外链纪律**：新增链接必须实测可达；反爬站点报假死时，先按 [.lychee.toml](.lychee.toml) 头部注释的流程核实"链接本身活着"再放行——**只放行假死，不洗白真死链**；付费墙论文只引用、不链接。
5. **事实与数值**：阈值/参数标注"示例值，以 datasheet 为准"；厂商宣传口径写成"据厂商发布"，不写成既定事实。
6. **新动画 SVG 三约定**（CI 强制）：含 `<title>`；至少一个 `<animate` 元素；含 `prefers-color-scheme: dark` 样式块（从既有 SVG 复制）。新增后同步三处计数：根 README（两处）+ [docs/circuits/README.md](docs/circuits/README.md)，并按 `.github/scripts/check_docs.py` 注释要求更新 `MIN_SVGS` 下界。
7. **动画必须有独立文字描述**：不看动画也能读懂正文（视障与打印场景）。

### 提交前跑本地门禁

```powershell
powershell -NoProfile -File scripts/local-gates.ps1
```

六门全绿再推：check_docs（相对链接/锚点/SVG 约定）→ ruff → pytest soc → 算法对比冒烟 → pytest protocol → 固件 gcc 编译+运行。PR 推送后 CI 的 `tests` 与 `links` 两个 workflow 都应通过；`links` 对反爬站点的误报按第 4 条处理。

### 许可

提交即表示同意：文档（docs/、README 等）按 [CC BY-SA 4.0](LICENSE)，代码（code/）按 [MIT](LICENSE) 发布。引用的外部资料注明出处与版权归属（先例见各中文导读文件头部声明）。
