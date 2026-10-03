# BMS-Z

一套**从入门到产品级**的电池管理系统（BMS）自学路线：7 篇阶段教程 + 3 篇电路详解（20 个动画）+ 可运行的配套代码 + 术语表与器材清单。全部中文，全部免费。

[![tests](https://github.com/zhuguang-ZFG/BMS-Z/actions/workflows/tests.yml/badge.svg)](https://github.com/zhuguang-ZFG/BMS-Z/actions/workflows/tests.yml)
[![links](https://github.com/zhuguang-ZFG/BMS-Z/actions/workflows/links.yml/badge.svg)](https://github.com/zhuguang-ZFG/BMS-Z/actions/workflows/links.yml)

## 从这里开始

1. **总纲**：[docs/bms-resources.md](docs/bms-resources.md) — 学习路线：每阶段给出 目标 → 核心概念 → 资料 → 实践任务 → 验收标准
2. **先看预算**：[docs/budget.md](docs/budget.md) — 全程器材清单：最低 ¥600 起步，什么该买、什么缓买、什么能借
3. **遇到生词**：[docs/glossary.md](docs/glossary.md) — 术语表：中英对照 + 一句话解释 + 反向索引

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

## 电路与芯片详解（含 20 个 SMIL 动画）

[docs/circuits/README.md](docs/circuits/README.md) — 功率回路 / 采样链与 AFE / 充电均衡计量三篇深度解析。GitHub 网页端打开动画自动播放。

## 配套代码（PC 即可运行，CI 守护）

[code/](code/README.md) — 教程动手任务的可运行参考实现：

- `code/soc/` — Thevenin 电池模型 + 三种 SOC 估算器对比（Python）
- `code/protocol/` — CRC 校验 + UART 帧状态机解析器（Python）
- `code/firmware/` — BMS 主状态机骨架：保护去抖/故障快照/均衡/休眠（C99）

## 其他资料

- 瑞萨 BMS 白皮书（2018）中文编译导读：[docs/renesas-bms-tutorial-中文导读.md](docs/renesas-bms-tutorial-中文导读.md)（非官方编译，原文版权见文件内声明）

## 许可

- **文档**（docs/、README）：[CC BY-SA 4.0](LICENSE)
- **代码**（code/）：[MIT](LICENSE)
- 本仓库是学习材料，不构成安全认证依据；所有阈值为示例值，实际设计以电芯/芯片 datasheet 与强制标准为准。锂电池实验有真实火灾风险，安全装备与实验纪律见 [阶段 2](docs/stages/stage-2-保护板实践.md)。

## 维护

外链由 [lychee 月度巡检](.github/workflows/links.yml)（反爬站点按 `.lychee.toml` 配置豁免）；代码测试与文档相对链接/SVG 计数随 PR 运行。发现错误欢迎提 Issue。
