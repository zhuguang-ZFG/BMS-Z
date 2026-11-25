# 执行计划

1. [x] **准备实现分支**：基于已包含 PR #114 的最新 `main` 创建 `zhuguang-ZFG/passive-balance-lab`，保留用户未提交的 `package-lock.json` 修改。
2. [x] **固定基线**：复核第 9 章算例、`balancing_energy.py`、`mountBookLab`、离线构建器和站点 directive；原始算例口径未变。
3. [x] **实现生成 SVG 实验**：在 §9.2 加入默认可读的内联 SVG 和电阻范围控件；`reader.js` 负责纯公式、同步 SVG/数值、重置和即时判题。
4. [x] **补内容边界**：标明波纹只表示功率、理想时间不含占空比/降额/控制限制；添加先猜后拖的学习提示。
5. [x] **测试交互与失败状态**：覆盖默认值、阻值边界、非法参数、答题反馈、重置、无脚本回退与打印状态。
6. [x] **验证交付面**：BMS 书测试及质量门通过；离线 HTML、PDF、EPUB 重建并校验；VitePress 站点测试、构建、浏览器交互与 375 px 视口检查通过。
7. [x] **完成 Papermorph 决策记录**：对照官方仓库、功能、Codex 流程、离线发布、依赖和费用；建议本轮暂不安装。
8. [ ] **提交与集成**：提交代码后推送分支、等待 CI 全绿、合并 PR；不纳入用户的锁文件改动。

## 审查点

- 内容审查：图、公式、读数和错误反馈的单位与算例一致；把静态/合成假设写清楚。
- 交互审查：鼠标、原生键盘和触摸控件均可完成输入与作答；更新只由一个状态驱动。
- 发布审查：站点版和单文件离线 HTML 都可用；打印版能读懂默认状态。
- 范围审查：没有 Papermorph 安装、模型调用或新增包；没有声称完成 PDF/EPUB 交互发布。

## 验证记录

- `node --test bms-book/tests/test_reader.mjs`：14 项通过。
- `python -m pytest bms-book/tests -q --basetemp .trellis/tasks/11-24-papermorph-svg-pilot/tmp/pytest-all`：328 项通过。
- `python bms-book/check.py`：通过。
- `npm run docs:build`：77 项站点测试和 VitePress 构建通过；静态包检查通过。
- 离线 HTML 浏览器抽查：交互、键盘、即时判分、375 px、打印和禁用 JavaScript 回退通过。
- VitePress 浏览器抽查：CSR 挂载、SVG/数值联动和 375 px 通过。
- `python bms-book/build_html.py --pdf`：HTML 与带目录、书签和元数据的 PDF 已生成。
- `python bms-book/build_epub.py --html bms-book/dist/bms-book.html --out-dir bms-book/dist` 与 `--check`：EPUB 已生成并通过 XML/资源/链接检查。
- `python bms-book/check_pdf.py bms-book/dist/bms-book.pdf`：发布契约通过。
- `python .trellis/scripts/task.py validate papermorph-svg-pilot`：通过。
