# 更新日志

## v0.4.0 · 2026-10-23

### 新增

- **第 31 章《UDS 诊断与刷写》**：ISO 14229 会话与安全访问（0x27 seed-key，附暴力空间账）、0x22/0x2E/0x31 与 NRC 小表、ISO 15031-6 DTC 与快照、FBL/SBL 刷写与双分区回滚；配 `code/uds_demo.py`（迷你 UDS ECU+客户端，NRC 全家桶可跑）。
- **第 32 章《高压安全与绝缘检测》**：高压系统地图、不平衡桥绝缘检测原理（平衡桥漏检对称退化）、HVIL、预充浪涌账、主动放电与验电文化；配 `code/insulation_bridge.py`（两次测量解 R+/R−，11 项断言）。
- **第七部分"诊断与高压：两张量产准考证"** 承载以上两章。
- **5 份新 demo**：`balancing_energy.py`、`data_audit.py`、`insulation_bridge.py`、`pybamm_fit.py`、`uds_demo.py`，全部 stdlib/numpy-only、确定性输出、结尾自检。
- **附录 E 习题参考答案**：32 章全部练习（约 96 题）配答案——数值题给关键步骤，设计题给判分要点。
- **CITATION.cff**：引用格式入口。
- **在线版**：伴读书接入 BMS-Z 站点（`docs/book/` 动态路由 + 侧栏目录 + `reading.md` 阅读入口），支持全文搜索、深色模式与上一章/下一章导航；单文件 HTML/PDF 仍可用 `build_html.py` 生成。

### 重写升级（空心章补肉）

- **第 9 章 均衡**：换 story（假满充现场），新增占空比降额/16 路总热账、主动均衡效率账、何时不该均衡、三条验证路径。
- **第 21 章 数据准备**：新增数据卡八要素、行尾/编码陷阱、八项行级体检（配 `data_audit.py`）、切分与泄漏。
- **第 22 章 开源架构**：从 README 导览升级为架构决策分析（foxBMS 分层理由、diyBMS 取舍、许可证即架构、四步读法）。
- **第 23 章 PyBaMM**：从官方 README 转述升级为"用仿真当裁判"（合成 SPMe 味裁判 + 平台标定 ECM，分窗 RMSE 露馅账）。
- **第 24 章 BMS×AI**：换成 BMS-Z `challenges/03-ai-review` 真实对抗现场；新增数据驱动 SOH 节（NASA RW3 真实锚点）与 AI 审查四步流程。
- **第 26 章 从原型到产品**：12 周路线图改为"三道阶段门"（每周交付物+验收数字），新增追溯矩阵示例与 GB/T 34131、QC/T 897 对照表自建法。

### 修复与一致性

- LFP 平台斜率口径统一为 0.75 mV/%（0.075 V/SOC），涉及 01/03/05 章。
- 第 18↔29 章重复练习去重；第 8↔25 章安全状态/E-Gas 内容分工。
- 术语表补 14 条（UDS、DTC、HVIL、ASIL、FTTI、K 值等）；附录 A 阶段映射修正；附录 D 标准表补 9 项。
- 修复 `cccv_charge.py`、`thermal_lump.py`、`ic_dv.py` 在 GBK 控制台的 Unicode 崩溃。
- 章节参考资料补经典文献（Plett 三卷、Vetter 2005、Bernardi 1985、Chen & Rinçón-Mora 2006、Sulzer 2021、SAE J2464、GB/T 34131、QC/T 897 等）。

### 工程

- 章节/版本/demo 清单统一到 `manifest.json`；构建改用 VitePress 渲染管线（公式构建期渲染为 SVG，插图内嵌）。
- `check.py`：demo 清单对账 + **书 ↔ demo 钉死数字断言**（实现与正文不许多头漂移）；交叉引用边界动态化。
- demo 全量 7 → 12。

## v0.3.1 及更早

见主仓库 CHANGELOG 与 git 历史。
