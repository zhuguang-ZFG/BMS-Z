# 技术设计

## 集成边界

试点属于现有 BMS 深读书的第 9 章，不另建 Papermorph 项目。章节 Markdown 是在线版与离线版共用的内容源；在线 VitePress 主题已经从 `bms-book/reader.js` 导入 `mountBookLab`，并通过 `v-book-lab` 指令挂载实验。`bms-book/build_html.py` 把同一个 `reader.js` 内联进离线整书 HTML。因此首选扩展当前 `data-book-lab` 渐进增强约定。

目标文件候选：

- `bms-book/book/09-均衡.md`：实验说明、可操作控件、默认 SVG、追问和静态回退。
- `bms-book/reader.js`：纯计算函数、SVG 状态绘制、重置和判分行为。
- `bms-book/tests/test_reader.mjs`：公式与边界值测试；可测试的状态更新和判题分支。
- `bms-book/tests/test_build.py`：在线/离线来源、默认静态数值、无脚本回退及控件结构合同。
- 必要时 `docs/.vitepress/theme/index.ts` 或站点测试：只在现有自动挂载未覆盖新内容时修改；优先沿用既有 directive。

## 状态与数据流

使用一个显式状态 `{ cellVoltageV, bleedResistanceOhm, chargeDeltaAh }`，默认分别为 `4`、`100`、`1`。纯函数对输入做有限数与正数校验，并返回电流（A）、功率（W）和理想时间（h）：

```text
I = U / R
P = U² / R
t = ΔQ / I
```

滑块事件先构造并校验完整状态，再通过同一个 `renderPassiveBalance(state)` 更新图中支路、电阻热量提示及数值。电流路径保持清楚可辨；视觉强度只映射功率，不映射温度。页面自带的 SVG 保存默认状态，故 JS 不可用时仍完整可读。避免在 SVG 的 `<img>` 子文档上尝试写 DOM；图必须以内联 SVG 节点呈现。

选择题读取同一计算结果，检查 `R=50 Ω` 时的定量关系。正确和错误选项分别给出简短解释；每次作答可重选，恢复算例只重置滑块与图，不持久化成绩或读者数据。使用原生 `<input type="range">` 和按钮/单选控件承接触摸、键盘和辅助技术输入，不要求读者必须拖 SVG 中的细小图元。

## 离线、打印与兼容

- 控件默认 `disabled`，只有挂载成功后启用，沿用当前渐进增强模式。
- 默认 SVG、公式和反馈提示文字在 HTML 源里可见；交互脚本无需网络、服务端或新依赖。
- 当前打印 CSS 会隐藏实验滑块，保留实验内容和默认静态图。视实现需要补充明确的打印布局规则，但不生成另一份图。
- 窄屏控制区单列，SVG 使用 `viewBox` 和自适应宽度，避免推动整页横向滚动。
- 在线版由现有 `v-book-lab` 指令自动挂载；离线版由 `build_html.py` 的 `mountBookLab` 扫描自动挂载。

## Papermorph 评估方法

不在本任务中安装或运行 Papermorph。对照官方当前的 Skill/README 与完成的本地试点，检查：

1. 是否有当前 BookLab 难以实现的学习收益（分拍旁白、可操控 SVG 状态、图内判分）。
2. 输出能否沿用当前在线与单文件离线发布链。
3. 官方安装流程对 Codex 的支持是否充分、可复现。
4. 新增运行依赖、设置步骤、模型费用是否被独特收益抵消。

评估必须注明官方资料的核对日期及仓库提交；输出一个具体的下一步建议，不据此自动安装。

## 验证与回滚

- 单元测试：默认、最小/最大电阻、无效输入；正确/错误判题路径与恢复默认。
- 构建测试：在线章节与离线单文件都含完整默认 SVG、可操作控件和脚本。
- 浏览器抽查：375 px/桌面、鼠标/触摸可用控件、Tab/方向键/空格、即时数值、答题反馈和打印静态回退。
- 运行 `python -m pytest bms-book/tests -q`、`python bms-book/check.py`、`node --test bms-book/tests/test_reader.mjs` 和相关 VitePress 构建/测试。
- 实验可通过删除章节实验区、移除 `reader.js` 中的 balance 分支与其测试回退；不触碰原有全局 SVG 播放器或其它实验公式。
