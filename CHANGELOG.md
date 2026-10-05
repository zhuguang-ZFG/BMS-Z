# 更新日志（CHANGELOG）

本仓库内容以 [GitHub Releases](https://github.com/zhuguang-ZFG/BMS-Z/releases) 为版本基线；格式参考 [Keep a Changelog](https://keepachangelog.com/)（中文）。

## [Unreleased]

## [1.1.0] — 2026-10-05

教学深化大版本：详解④ + 16 张新动画（38→54）+ 两篇 MCU 实战专题 + 题库/书单/词表扩编 + 门户消漂移。

### 文档

- 详解④《系统安全与量产》：HVIL/IMD/主动放电三件套、接触器管理（PWM 保持/粘连检测/分断纪律/上下电时序表）、E-Gas 三层监控与看门狗安全态、EOL 产线测试与追溯
- 新增 STM32/ESP32 两篇实战专题（选型/外设映射/框架/坑清单 + GitHub 参考工程各 4 个），全文叙事化润色（事实/编号/链接保持）
- 新增 16 张动画（计数 38→54，均嵌文配文字回退）：ADC 注入组同步采样、ESP32 睡眠电流剖面、SOH 老化双指标、MQTT 发布订阅与遗嘱、DTC 故障快照、一阶 vs 二阶 RC、被动均衡分时调度、HIL 测试台、采样链误差预算瀑布、OCV 滞回、极化的物理图景、最弱单体反极、热管理三路线、接触器粘连检测、看门狗与安全态、采样线断线检测；check_docs 动画下界同步至 54
- 题库 66→72（stage-3/5/6 各 +2，配折叠答案）；书单免费资源 +3（均实测可达）；术语表 +8（MQTT/FreeRTOS/ESP-IDF/ADC 注入组/IMD/Y 电容等）
- §6.1.3 绝缘检测深化（联立求解数学/低频注入法/外置 IMD/多点失效与 Y 电容 3–5τ 窗口量化、ISO 6469、称体重直觉）
- 新增 code/soc/hppc_demo.py：HPPC 参数辨识合成演示（R0 跳变法 + 回弹网格拟合），阶段 4 §4.10 任务 2 配套，附 2 个回归测试；增补真实数据适配说明（不代做任务）
- 门户 BMS学习路径.html 消漂移（计数同步 + STM32/ESP32 两张专题卡，6→8 卡）；资源总纲 mermaid 补专题与详解④节点
- 新增 CODE_OF_CONDUCT.md（Contributor Covenant 2.1 中文版）；README「用 Obsidian 打开」节升级为 1.13.7 实机验证口径；FAQ Q7 精确锚点；书单头日期修正与题库问答全库对齐审计

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

[Unreleased]: https://github.com/zhuguang-ZFG/BMS-Z/compare/v1.1.0...HEAD
[1.1.0]: https://github.com/zhuguang-ZFG/BMS-Z/compare/v1.0.0...v1.1.0
[v1.0.0]: https://github.com/zhuguang-ZFG/BMS-Z/releases/tag/v1.0.0
