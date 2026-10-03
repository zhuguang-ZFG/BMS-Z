# BMS（电池管理系统）学习资料汇总

> 收录日期：2026-10-03，GitHub 星数为当日快照。

## 目录

1. [开源 BMS 完整项目](#1-开源-bms-完整项目硬件--固件)
2. [AFE 驱动与参考设计](#2-afe-驱动与参考设计)
3. [商用 BMS 协议逆向与监控集成](#3-商用-bms-协议逆向与监控集成)
4. [SOC / SOH / RUL 算法](#4-soc--soh--rul-算法)
5. [电池建模与仿真](#5-电池建模与仿真)
6. [国外论坛与社区](#6-国外论坛与社区)
7. [国内论坛与社区](#7-国内论坛与社区)
8. [厂商官方资料](#8-厂商官方资料)
9. [课程与书籍](#9-课程与书籍)
10. [公开数据集](#10-公开数据集)
11. [通信协议资料](#11-通信协议资料)
12. [学习路径建议](#12-学习路径建议)

---

## 1. 开源 BMS 完整项目（硬件 + 固件）

| 项目 | Stars | 说明 |
|---|---|---|
| [stuartpittaway/diyBMSv4](https://github.com/stuartpittaway/diyBMSv4) | 1136 | DIY 储能（powerwall）领域最知名的 BMS，分压采集模块 + 主控架构；固件在 [diyBMSv4Code](https://github.com/stuartpittaway/diyBMSv4Code)（154★） |
| [syssi/esphome-jk-bms](https://github.com/syssi/esphome-jk-bms) | 1026 | ESPHome 组件，UART/BLE 监控控制 JK（极空）BMS，协议文档齐全 |
| [tinfever/FW-Dyson-BMS](https://github.com/tinfever/FW-Dyson-BMS) | 934 | 戴森 V6/V7 吸尘器 BMS 固件重写，逆向学习好材料 |
| [Green-bms/SmartBMS](https://github.com/Green-bms/SmartBMS) | 751 | 开源智能 BMS，支持 LiFePO4 / Li-ion / NCM 电池组 |
| [fl4p/batmon-ha](https://github.com/fl4p/batmon-ha) | 522 | Home Assistant 集成，支持 JK / JBD / Daly / ANT / SOK 等蓝牙 BMS |
| [foxBMS/foxbms-2](https://github.com/foxBMS/foxbms-2) | 479 | Fraunhofer 出品的工业级研发平台，代码规范极高，文档见 [docs.foxbms.org](https://foxbms.org/) |
| [EnnoidMe/ENNOID-BMS](https://github.com/EnnoidMe/ENNOID-BMS) | 330 | LTC68xx + STM32 模块化 BMS，面向最高 400V EV 电池包 |
| [LibreSolar/bms-firmware](https://github.com/LibreSolar/bms-firmware) | 262 | 通用 BMS 固件，支持 bq769x0 / bq769x2 / ISL94202 |
| [patman15/BMS_BLE-HA](https://github.com/patman15/BMS_BLE-HA) | 362 | BLE BMS 的 Home Assistant 集成（JBD / Daly / Renogy / Seplos 等） |
| [syssi/esphome-jbd-bms](https://github.com/syssi/esphome-jbd-bms) | 258 | JBD（小翔）BMS 的 ESPHome 组件 |
| [BotoX/xiaomi-m365-compatible-bms](https://github.com/BotoX/xiaomi-m365-compatible-bms) | 219 | 小米滑板车 M365 兼容固件（ATmega328P + BQ769x0） |
| [LibreSolar/bms-c1](https://github.com/LibreSolar/bms-c1) | 262 | 16S / 100A BMS 硬件，基于 BQ76952，KiCad 工程 |
| [Teslafly/Dead-OpenBMS-dead](https://github.com/Teslafly/Dead-OpenBMS-dead) | 248 | 可扩展开源 BMS（已停更，思路仍值得参考） |
| [rickygu/openBMS](https://github.com/rickygu/openBMS) | 228 | 电动汽车锂电池 BMS（Java） |
| [spmp/Low-Cost-BMS-STM32](https://github.com/spmp/Low-Cost-BMS-STM32) | 69 | 低成本 STM32 BMS |
| [LibreSolar/bms-15s80-sc](https://github.com/LibreSolar/bms-15s80-sc) | 77 | 15S BMS，bq76940 / bq76930 |
| [slintak/lto-bms](https://github.com/slintak/lto-bms) | 74 | 1S LTO 电池 BMS |
| [raphaelchang/battman-hardware](https://github.com/raphaelchang/battman-hardware) | 60 | Battman 锂电池 BMS PCB 设计，固件见 [battman-firmware](https://github.com/raphaelchang/battman-firmware)（39★） |
| [Tertiush/bmspace](https://github.com/Tertiush/bmspace) | 62 | Pace BMS（Python） |

## 2. AFE 驱动与参考设计

| 项目 | Stars | 说明 |
|---|---|---|
| [nseidle/BMS](https://github.com/nseidle/BMS) | 180 | BQ76940 监控分线板 |
| [omarKmekkawy/Reverse_Engineering_BQ20z70_Laptop_BMS](https://github.com/omarKmekkawy/Reverse_Engineering_BQ20z70_Laptop_BMS) | 132 | 笔记本电池 BQ20Z70 逆向（SBS / SMBus，EV2300） |
| [vamoirid/Battery-Management-System-LTC6811-STM32](https://github.com/vamoirid/Battery-Management-System-LTC6811-STM32) | 55 | LTC6811 从板 + STM32F446RE，结构清晰，适合入门仿制 |
| [scttnlsn/bms](https://github.com/scttnlsn/bms) | 65 | Zephyr RTOS + bq76920，4S 锂电池组 |
| [LibreSolar/bq769x0-arduino-library](https://github.com/LibreSolar/bq769x0-arduino-library) | 52 | bq76920/76930/76940 的 Arduino 库（已归档，仍可参考） |
| [Velli20/Li-Ion-Battery-Test-Bench](https://github.com/Velli20/Li-Ion-Battery-Test-Bench) | 24 | LTC6811（DC2259A）+ STM32F7 电池测试台 |

常用模拟前端（AFE）芯片：TI **BQ769x0 / BQ769x2** 系列（生态最全、中文资料多）、ADI **LTC6811 / LTC6813**（车规高压、菊花链）、瑞萨 **ISL94202/94203**。

## 3. 商用 BMS 协议逆向与监控集成

| 项目 | Stars | 说明 |
|---|---|---|
| [syssi/esphome-seplos-bms](https://github.com/syssi/esphome-seplos-bms) | 119 | Seplos BMS：UART / RS485 / BLE（Modbus） |
| [syssi/esphome-pace-bms](https://github.com/syssi/esphome-pace-bms) | 92 | PACE BMS：RS485 Modbus |
| [dexterbg/Twizy-Virtual-BMS](https://github.com/dexterbg/Twizy-Virtual-BMS) | 94 | 雷诺 Twizy BMS 的 CAN 协议仿真库 |

> 这一组仓库本身就是各品牌 BMS 私有协议的事实文档（帧格式、寄存器、CRC），做协议对接时优先查阅。

## 4. SOC / SOH / RUL 算法

| 项目 | Stars | 说明 |
|---|---|---|
| [AlterWL/Battery_SOC_Estimation](https://github.com/AlterWL/Battery_SOC_Estimation) | 437 | 卡尔曼滤波 SOC 估算（MATLAB） |
| [mohammadrezwankhan/matlab-simulink-energy-lab](https://github.com/mohammadrezwankhan/matlab-simulink-energy-lab) | 317 | SOC EKF、热管理、BESS 控制的可复现 Simulink 参考模型 |
| [MichaelBosello/battery-rul-estimation](https://github.com/MichaelBosello/battery-rul-estimation) | 198 | 深度 LSTM 电池剩余寿命（RUL）预测 |
| [KeiLongW/battery-state-estimation](https://github.com/KeiLongW/battery-state-estimation) | 192 | 深度 LSTM SOC 估算 |
| [ks-santosh/MiniBMS](https://github.com/ks-santosh/MiniBMS) | 60 | Simulink 全模型（SOC + 故障检测 + 状态机），适合仿真入门 |
| [raghuramshankar/soc-estimation-of-li-ion-batteries](https://github.com/raghuramshankar/soc-estimation-of-li-ion-batteries) | — | EKF SOC，含 OCV-SOC 建模与公开数据集说明 |
| [alexdatadesign/lfp_soc_ml](https://github.com/alexdatadesign/lfp_soc_ml) | 39 | 磷酸铁锂（LFP）SOC 机器学习估算（XGBoost） |

## 5. 电池建模与仿真

| 项目 | Stars | 说明 |
|---|---|---|
| [pybamm-team/PyBaMM](https://github.com/pybamm-team/PyBaMM) | 1673 | Python 物理电池建模事实标准（DFN / SPM 等电化学模型） |
| [pybamm-team/liionpack](https://github.com/pybamm-team/liionpack) | 120 | 基于 PyBaMM 的电池包级仿真 |
| [FrankSuperG/electrochemical-battery-model-atlas](https://github.com/FrankSuperG/electrochemical-battery-model-atlas) | 51 | 开源电化学电池模型（DFN/P2D、SPM、SPMe）精选索引 |

## 6. 国外论坛与社区

| 社区 | 链接 | 价值 |
|---|---|---|
| TI E2E 电源管理论坛 | [e2e.ti.com](https://e2e.ti.com/support/power-management-group/power-management/f/power-management-forum) | BQ 系列选型与实战问答，TI 工程师直接回复 |
| EEVblog 论坛 | [eevblog.com](https://www.eevblog.com/forum/) | 高质量长帖：[Open source smart BMS](https://www.eevblog.com/forum/oshw/open-source-smart-bms/)、[Learning Path for building my own BMS](https://www.eevblog.com/forum/beginners/learning-path-for-buiding-my-own-bms/)、[Intelligent BMS](<https://www.eevblog.com/forum/projects/intelligent-bms-(battery-management-system)/>) |
| Second Life Storage | [secondlifestorage.com](https://secondlifestorage.com/index.php) | DIY 储能 / 二手电芯社区，有专门 BMS 板块，diyBMS 用户聚集地 |
| DIY Solar Forum | [diysolarforum.com](https://diysolarforum.com/forums/second-life-lithium-batteries.24/) | 太阳能储能 DIY，RS485/CAN 协议实战讨论多 |
| Endless Sphere | [endless-sphere.com](https://endless-sphere.com/) | 电动自行车 / EV 电池包 |
| Reddit | r/batteries、r/AskElectronics、[r/embedded](https://www.reddit.com/r/embedded/comments/1gb6p5z/sources_to_make_bms_from_using_esp32_or_arduino/) | 快速答疑、选型讨论 |
| ST Community | [community.st.com](https://community.st.com/others-hardware-and-software-57/communication-protocols-between-microcontrollers-for-a-bms-151918) | STM32 + BMS 通信架构讨论 |

## 7. 国内论坛与社区

| 社区 | 链接 | 价值 |
|---|---|---|
| EEWORLD 论坛 | [BMS 全方位解析](https://bbs.eeworld.com.cn/thread-1309359-1-1.html) | "DIY/开源硬件专区"系列帖 |
| 21ic | [BMS 标签页](https://www.21ic.com/tags/bms)、[SH367309 保护板设计全解析](https://bbs.21ic.com/icview-3531958-1-1.html) | 保护板实战帖多 |
| 知乎 | [学习路线讨论](https://www.zhihu.com/question/439467314)、[书籍推荐](https://www.zhihu.com/question/352224059)、[如何自学 BMS](https://www.zhihu.com/question/22491005)、[SmartBMS 中文解读](https://zhuanlan.zhihu.com/p/669013095) | 入门路线、书单 |
| 立创开源硬件平台 | [oshwhub.com](https://oshwhub.com/kaijun/mps-energy-station) | 完整开源工程（如 BQ76920 5S BMS） |
| CSDN | [S-8254A 多串锂电池硬件保护方案解析](https://bbs.csdn.net/weixin_29169899/article/details/100241878) | 保护电路 / MOS 选型类文章 |
| 哔哩哔哩 | [BMS 项目实战视频课](https://www.bilibili.com/video/BV1pv4y1T7Xi/) | 视频入门 |

## 8. 厂商官方资料

| 厂商 | 链接 | 内容 |
|---|---|---|
| TI | [ESS BMS 方案页](https://www.ti.com.cn/solution/zh-cn/ess-battery-management-system-bms)、[Battery management unit](https://www.ti.com/solution/battery-management-unit) | BQ 系列参考设计、应用笔记 |
| NXP | [BMS 应用页](https://www.nxp.com.cn/applications/BATTERY-MANAGEMENT-SYSTEM) | 功能安全视角的架构文档 |
| 英飞凌 | [非堆叠式 BMS 方案](https://www.infineon.cn/application/non-stackable-bms-solutions) | MOS 保护级设计 |
| 瑞萨 | [Battery Management System Tutorial](https://www.renesas.com/en/document/whp/battery-management-system-tutorial) | 经典入门白皮书 |
| foxBMS | [foxbms.org](https://foxbms.org/) | 文档本身就是最好的 BMS 架构教材 |
| NLnet OpenBMS | [nlnet.nl/project/OpenBMS](https://nlnet.nl/project/OpenBMS/) | Li-ion/Li-Po 监控保护的开源软硬件项目 |
| Battery University | [BU-409 充电](https://batteryuniversity.com/article/bu-409-charging-lithium-ion)、[BU-808 延寿](https://batteryuniversity.com/article/bu-808-how-to-prolong-lithium-based-batteries/) | 电池化学基础必读 |

## 9. 课程与书籍

**国外**

- Coursera 专项课程 [Algorithms for Battery Management Systems](https://www.coursera.org/specializations/algorithms-for-battery-management-systems)（Gregory Plett，科罗拉多大学博尔德分校）：
  - [Introduction to Battery Management Systems](https://www.coursera.org/learn/battery-management-systems)
  - [Battery State-of-Charge (SOC) Estimation](https://www.coursera.org/learn/battery-state-of-charge)
  - [Battery Pack Balancing and Power Estimation](https://www.coursera.org/learn/battery-pack-balancing-power-estimation)
- Gregory Plett 三部曲（Artech House）：
  - Vol. I: *Battery Modeling*
  - Vol. II: *Equivalent-Circuit Methods*
  - Vol. III: *Physics-Based Methods*
  - 作者主页：http://mocha-java.uccs.edu/

**国内**

- 谭晓军《电动汽车动力电池管理系统设计》
- 熊瑞《动力电池管理系统核心算法》

## 10. 公开数据集

- [Battery Archive](https://www.batteryarchive.org/) — 公开电池循环数据聚合（[资源索引页](https://www.batteryarchive.org/resources.html)）
- [pauljgasper/awesome-battery-data](https://github.com/pauljgasper/awesome-battery-data) — 开源电池数据 / 建模 / 分析生态一站式清单
- [lappemic/open-source-battery-data](https://github.com/lappemic/open-source-battery-data) — 开源电池数据集目录
- [terencetaothucb/TBSI-Sunwoda-Battery-Dataset](https://github.com/terencetaothucb/TBSI-Sunwoda-Battery-Dataset)（63★）— 清华-伯克利 x 欣旺达公开数据集

## 11. 通信协议资料

- [BMS Communication Protocols: Types, Conversion & Gateway Integration](https://www.come-star.com/blog/bms-communication-protocols/)
- [Battery BMS Communication: CAN vs RS485](https://liniotech.com/blog/battery-bms-communication-can-vs-rs485-explained/)
- [BMS Communication Architectures — batterydesign.net](https://www.batterydesign.net/battery-management-system/hardware/bms-communication-architectures/)
- 实战协议样本：第 3 节 syssi 系列仓库（JK / JBD / Seplos / PACE 的 UART、BLE、Modbus、CAN 帧格式）

## 12. 学习路径建议

- **从零做硬件 + 固件** → 先读 [LibreSolar/bms-firmware](https://github.com/LibreSolar/bms-firmware) + [diyBMSv4](https://github.com/stuartpittaway/diyBMSv4)；AFE 选 BQ769x2（生态最全）或 LTC6811（车规高压、菊花链）。
- **储能 / 户用电池** → diyBMSv4 + Second Life Storage 社区。
- **学 SOC/SOH 算法** → Coursera Plett 专项课 → AlterWL（EKF）→ MiniBMS（Simulink）→ LSTM 类项目。
- **做监控 / 上位机** → syssi 全家桶（协议文档最全）。
- **电池本体建模** → PyBaMM。
