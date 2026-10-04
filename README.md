# BMS-Z

一套**从入门到产品级**的电池管理系统（BMS）自学路线：7 篇阶段教程 + 3 篇电路详解（36 个动画）+ 可运行的配套代码 + 术语表与器材清单。全部中文，全部免费。

[![tests](https://github.com/zhuguang-ZFG/BMS-Z/actions/workflows/tests.yml/badge.svg)](https://github.com/zhuguang-ZFG/BMS-Z/actions/workflows/tests.yml)
[![links](https://github.com/zhuguang-ZFG/BMS-Z/actions/workflows/links.yml/badge.svg)](https://github.com/zhuguang-ZFG/BMS-Z/actions/workflows/links.yml)

⚠️ **锂电池实验有真实火灾风险。** 碰真电池前先备护目镜与防火垫；安全纪律与器材见 [预算清单](docs/budget.md) 与 [阶段 2](docs/stages/stage-2-保护板实践.md)。本仓库是学习材料，不构成安全认证依据；阈值为示例值，设计以电芯/芯片 datasheet 与强制标准为准。

## 从这里开始（零基础）

1. **前两周怎么走**：[docs/stages/getting-started.md](docs/stages/getting-started.md) — 第 0 天小实验 + 14 天中文路径 + 可跳过什么  
2. **打开教程**：[阶段 0 前置知识](docs/stages/stage-0-前置知识.md) — 先懂电池，再谈管理（§0.1 必读）  
3. **买东西前看**：[docs/budget.md](docs/budget.md) ｜ **生词**：[docs/glossary.md](docs/glossary.md)  
4. **全图导航**（别一上来当任务刷）：[docs/bms-resources.md](docs/bms-resources.md)

不会英文没关系：主线教程与推荐中文视频足够走完入门；英文资料在总纲里均标为可选。

## 阶段教程（逐节展开，自测题附折叠答案）

| 阶段 | 内容 | 建议用时 |
|---|---|---|
| [阶段 0 前置知识](docs/stages/stage-0-前置知识.md) | 电池化学 / 电路基础 / 嵌入式 | 1–2 周 |
| [阶段 1 认识 BMS](docs/stages/stage-1-认识BMS.md) | 功能模块 / 五大保护 / 均衡 | 1 周 |
| [阶段 2 保护板实践](docs/stages/stage-2-保护板实践.md) | DW01 / S-8254A / 保护实测 | 2–4 周 |
| [阶段 3 AFE+MCU 智能 BMS](docs/stages/stage-3-AFE-MCU智能BMS.md) | BQ769x2 / LTC6811 / 固件架构 / PCB | 1–2 月 |
| [阶段 4 SOC/SOH 算法](docs/stages/stage-4-SOC-SOH算法.md) | 安时积分 / OCV / EKF / 双卡尔曼 / SOP | 1–3 月 |
| [阶段 5 通信与集成](docs/stages/stage-5-通信与集成.md) | UART / Modbus / CAN / BLE / 协议逆向 | 2–4 周 |
| [阶段 6 精通与毕业项目](docs/stages/stage-6-精通与毕业项目.md) | 高压架构 / 功能安全 / 量产 / 毕业项目 | 持续 |

## 电路与芯片详解（含 36 个 SMIL 动画）

[docs/circuits/README.md](docs/circuits/README.md) — 功率回路 / 采样链与 AFE / 充电均衡计量三篇深度解析。GitHub 网页端打开动画自动播放。

## 用 Obsidian 打开（可选）

仓库根目录就是一个 Obsidian 库：Obsidian →「打开本地文件夹」选本仓库即可。共享配置已随仓库提交（`.obsidian/`）：新建链接走「相对路径 Markdown 链接」，与 GitHub 渲染规则一致；个人窗口布局按 [.gitignore](.gitignore) 约定不入库。

- 教程与详解正文**内嵌**的 SMIL 动画，在 Obsidian 阅读视图中直接播放；配色跟随**所在页面的**深浅主题：GitHub 与 Obsidian 都会把自身主题写入页面 `color-scheme`，SVG 按它取色（Chromium 实测：系统浅色 + 页面深色主题时，内嵌动画仍正确走深色分支），不依赖操作系统设置。
- [docs/circuits/README.md](docs/circuits/README.md) 收录的 36 个动画是**链接**而非内嵌：点击后由系统默认应用打开（Windows 上通常是浏览器，动画照常播放）。
- 跨文件小节锚点（如 `bms-resources.md#62-算法精通`）按 GitHub 规则生成并受 CI 校验：Obsidian 能打开目标文件，但小节跳转以 GitHub 网页端为准（两家锚点规则不同）。
- [BMS学习路径.html](BMS学习路径.html) 等 HTML 文件在 Obsidian 中点击会用默认浏览器打开。

## 配套代码（PC 即可运行，CI 守护）

[code/](code/README.md) — 可 PC 化动手任务的参考实现（不是全部硬件任务都有代码）：

- `code/soc/` — Thevenin 电池模型 + 三种 SOC 估算器对比（Python）
- `code/protocol/` — CRC 校验 + UART 帧状态机解析器（Python）
- `code/firmware/` — BMS 主状态机骨架：保护去抖/故障快照/均衡/休眠（C99）

## 其他资料

- 瑞萨 BMS 白皮书（2018）中文编译导读：[docs/renesas-bms-tutorial-中文导读.md](docs/renesas-bms-tutorial-中文导读.md)（非官方编译，原文版权见文件内声明）
- Plett ECE5710 Notes02《等效电路电芯模型》中文导读：[docs/ece5710-notes02-中文导读.md](docs/ece5710-notes02-中文导读.md)（非官方编译，原文 © Gregory L. Plett / UCCS）
- Plett ECE5720 Notes03《电池状态估计》中文导读：[docs/ece5720-notes03-中文导读.md](docs/ece5720-notes03-中文导读.md)（非官方编译，KF/EKF/SPKF/bar-delta，原文 © Gregory L. Plett / UCCS）
- BMS 书目与免费资源清单：[BMS书籍清单.md](BMS书籍清单.md)（22 条书目核实版 + UCCS 官方讲义/视频资源索引）
- BMS 学习路径视频页：[BMS学习路径.html](BMS学习路径.html)（内嵌 B 站/YouTube 播放器；[在线版](https://zhuguang-zfg.github.io/BMS-Z/)由 GitHub Pages 提供，本地双击文件亦可）

## 许可

- **文档**（docs/、README）：[CC BY-SA 4.0](LICENSE)
- **代码**（code/）：[MIT](LICENSE)

## 维护

外链由 [lychee 月度巡检](.github/workflows/links.yml)（反爬站点按 `.lychee.toml` 配置豁免）；代码测试、ruff 静态检查与文档相对链接/SVG 计数随 PR 运行。发现错误欢迎提 Issue。

月度复查时手动点一下 `nxp.com`、`analog.com`、`eet-china.com` 这三家：它们已被 `.lychee.toml` 整站排除（对 bot 一律 404，或 HTTP/2 与 lychee 客户端不合，上游 [issue #2264](https://github.com/lycheeverse/lychee/issues/2264) 尚无强制 HTTP/1.1 的开关），**不在巡检范围内**，真关停了 CI 不会报。

CI 只做"抓错误"的检查，不做格式化：Python 用 ruff 的 bug 类规则（见 [ruff.toml](ruff.toml)），C 用 `gcc -Wall -Wextra -Werror`。格式化工具会把代码里对齐的中文注释打散，反而更难读——理由写在 ruff.toml 顶部。
