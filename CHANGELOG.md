# 更新日志（CHANGELOG）

本仓库内容以 [GitHub Releases](https://github.com/zhuguang-ZFG/BMS-Z/releases) 为版本基线；格式参考 [Keep a Changelog](https://keepachangelog.com/)（中文）。

## [Unreleased]

### 文档

- 新增 CHANGELOG.md 并在 README 维护节链接 Releases 与变更记录
- README「用 Obsidian 打开」节的实测口径升级为 Obsidian 1.13.7 实机验证（阅读视图 SMIL 在播、深色分支正确）
- 总纲「精通自检清单」与阶段 6 评审量规互链

- 新增 CODE_OF_CONDUCT.md（Contributor Covenant 2.1 中文版）并在 CONTRIBUTING 链接，社区健康度补齐

- 新增 code/soc/hppc_demo.py：HPPC 参数辨识合成演示（R0 跳变法 + 回弹网格拟合，含 40s 窗病态实测教训），阶段 4 §4.4/§4.10 任务 2 配套，附 2 个回归测试

- hppc_demo.py 增补真实数据适配说明（切段/窗长/温度/接触阻抗四坑，不代做任务 2）；bms.h 预充扩展练习补 5 个设计问题（只给问题不给答案）

- 新增 STM32/ESP32 两篇实战专题（选型/外设映射/框架/坑清单 + GitHub 参考工程各 4 个）+ 两张动画（ADC 注入组同步采样、ESP32 睡眠电流剖面），计数 38→40；stage-3/5、bms-resources mermaid、词表（MQTT/FreeRTOS/ESP-IDF/ADC 注入组）同步织网

- §6.1.3 绝缘检测深化（联立求解数学/低频注入法/外置 IMD/多点失效与 Y 电容 3–5τ 窗口量化、ISO 6469）；书单免费资源 +3（Mastering STM32 / FreeRTOS 官方手册 / ESP-IDF 中文指南，均实测可达）；题库 66→72（stage-3/5/6 各 +2，配折叠答案）；STM32 专题陈旧仓库条目标注更新日期

- 新增 3 张动画（计数 40→43）：SOH 老化双指标（阶段 4 §4.6）、MQTT 发布订阅与遗嘱（ESP32 专题 §4）、DTC 故障快照（阶段 6 §6.2.2），均嵌文配文字回退；候选 LFP 平台动画经查 ocv-soc-curve.svg 已覆盖而放弃

- 新增 4 张动画（计数 43→47）：一阶 vs 二阶 RC（阶段 4 §4.4）、被动均衡分时调度（阶段 6 §6.3）、HIL 测试台（阶段 6 §6.5）、采样链误差预算瀑布（详解② §1——评审指出的详解②核心论点视觉缺口），均嵌文配文字回退

- STM32/ESP32 两篇专题全文润色（叙事化开场钩子、记忆点金句、坑清单现场感，事实/编号/链接全部保持）；§6.1.3 电桥法数学补「称体重」直觉

- 门户 BMS学习路径.html 消漂移：计数 38→47 三处（og/nav/卡），新增 STM32/ESP32 两张专题卡（6→8 卡）

- 新增 2 张动画（计数 47→49）：OCV 滞回（阶段 4 §4.3 考点视觉化——游标同 SOC 两电压对照）、极化的物理图景（浓度梯度形成/回匀——「要等静置」的物理原因）；全入口面漂移扫描：无陈旧计数残留（CHANGELOG 历史记录除外）

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
