# 更新日志（CHANGELOG）

本仓库内容以 [GitHub Releases](https://github.com/zhuguang-ZFG/BMS-Z/releases) 为版本基线；格式参考 [Keep a Changelog](https://keepachangelog.com/)（中文）。

## [Unreleased]

### 文档

- 新增 CHANGELOG.md 并在 README 维护节链接 Releases 与变更记录
- README「用 Obsidian 打开」节的实测口径升级为 Obsidian 1.13.7 实机验证（阅读视图 SMIL 在播、深色分支正确）
- 总纲「精通自检清单」与阶段 6 评审量规互链

- 新增 CODE_OF_CONDUCT.md（Contributor Covenant 2.1 中文版）并在 CONTRIBUTING 链接，社区健康度补齐

- FAQ Q7 的「阶段 1 §1.6」升级为精确锚点链接

## [v1.0.0] — 2026-10-04

首个「教学级 · 产品级」稳定基线。

### 内容

- 7 篇阶段教程：前置知识 → 认识 BMS → 保护板实践 → AFE+MCU → SOC/SOH 算法 → 通信与集成 → 精通与毕业项目；66 道自测题全部附折叠答案
- 3 篇电路详解（功率回路 / 采样链与 AFE / 充电均衡计量）+ 38 张 SMIL 动画与电路图（含 DW01 原理图、BMS 学习路线图）
- 术语表 90 条、书单 22 条、器材预算清单、里程碑时间线、关键论文骨架、旁系知识导航、芯片选型速查表
- 毕业项目三维六级评审量规（「优秀」列 = 产品级门槛）

### 配套代码（PC 可跑，CI 守护）

- `code/soc/` SOC 三估算器对比、`code/protocol/` UART 帧解析器、`code/firmware/` BMS 状态机骨架
- `code/README.md` 逐行走读（带行号，映射教程小节）

### 门户与社区

- GitHub Pages 门户页：愿景条 + 路线图动画 + 六大分区卡 + 内嵌视频教程；跟随系统深色；Open Graph 社交卡
- README：emoji 导航、FAQ ×8、参与共建指引；14 天打卡清单（getting-started）
- CONTRIBUTING.md + Issue 模板 ×2（内容纠错/内容建议）+ PR 自检模板；仓库 topics/description/homepage 就位

### 质量

- 双 workflow：`tests`（ruff / pytest×2 / gcc / check_docs）随推送运行，`links`（lychee）随文档推送 + 每月巡检
- 反爬假死站点豁免流程文档化（8 个域按成因分组，月度人工复查清单）
- 许可：文档 CC BY-SA 4.0、代码 MIT（单 LICENSE 文件双节）

[Unreleased]: https://github.com/zhuguang-ZFG/BMS-Z/compare/v1.0.0...HEAD
[v1.0.0]: https://github.com/zhuguang-ZFG/BMS-Z/releases/tag/v1.0.0
