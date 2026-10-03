# BMS 学习路线：从入门到精通

> 收录日期：2026-10-03。资料按学习阶段组织，每个阶段给出：学习目标 → 核心概念 → 推荐资料 → 实践任务。
> 周期为建议值，可根据基础增减。

```mermaid
flowchart LR
    A["0 前置知识"] --> B["1 入门：认识 BMS"]
    B --> C["2 基础：保护板实践"]
    C --> D["3 进阶：AFE + MCU 智能 BMS"]
    D --> E["4 核心：SOC/SOH 算法"]
    E --> F["5 系统：通信与集成"]
    F --> G["6 精通：工程化与前沿"]
```

---

## 阶段 0：前置知识（1–2 周）

**目标**：具备能看懂 BMS 电路和代码的最低基础。

**核心概念**：模拟/数字电路基础（ADC、MOS、运放、隔离）、C 语言与嵌入式开发（GPIO/I2C/SPI/UART）、锂电池化学基础。

**推荐资料**：

- [Battery University：BU-409 锂电充电](https://batteryuniversity.com/article/bu-409-charging-lithium-ion) — 充电特性（CC-CV、C 倍率）必读
- [Battery University：BU-808 延长锂电池寿命](https://batteryuniversity.com/article/bu-808-how-to-prolong-lithium-based-batteries/) — 电池为什么需要保护
- [瑞萨《Battery Management System Tutorial》](https://www.renesas.com/en/document/whp/battery-management-system-tutorial) — 最好的 BMS 扫盲白皮书，先读一遍

**验收**：能解释为什么锂电池不能过充/过放，什么是 CC-CV 充电曲线。

---

## 阶段 1：入门——认识 BMS（1 周）

**目标**：说清 BMS 是什么、解决什么问题、由哪些功能模块组成。

**核心概念**：过充/过放/过流/短路/温度五大保护；单体电压均衡；SOC/SOH/SOP 三大状态量；保护板 vs 智能 BMS 的区别。

**推荐资料**：

- [NXP BMS 应用页](https://www.nxp.com.cn/applications/BATTERY-MANAGEMENT-SYSTEM) — 功能安全视角的架构图
- [英飞凌 非堆叠式 BMS 方案](https://www.infineon.cn/application/non-stackable-bms-solutions) — 保护级设计视角
- [知乎：什么是 BMS / 学习路线讨论](https://www.zhihu.com/question/439467314)、[如何自学 BMS](https://www.zhihu.com/question/22491005)
- [B 站：BMS 项目实战视频课](https://www.bilibili.com/video/BV1pv4y1T7Xi/) — 视频入门

**验收**：能画出 BMS 的功能框图（采样 → 保护 → 均衡 → 估算 → 通信），说明每一块的输入输出。

---

## 阶段 2：基础实践——保护板（2–4 周）

**目标**：看懂并亲手调通一块多串保护板，掌握保护电路的硬件细节。

**核心概念**：保护 IC（DW01 / S-8254A / 中颖 SH367309）与 MOS 管协同架构；ID/NTC 检测；MOS 选型（VDS、RDS(on)、Qg）；静态功耗。

**推荐资料**：

- [CSDN：S-8254A 多串锂电池硬件保护方案深度解析](https://bbs.csdn.net/weixin_29169899/article/details/100241878) — 保护机制 + MOS 选型法则
- [21ic：基于中颖 SH367309 的 1-17 串 BMS 保护板设计全解析](https://bbs.21ic.com/icview-3531958-1-1.html) — 完整实战，含静态功耗/采样精度实测
- [EET-China：锂电池保护板的 ID、NTC 设计](https://www.eet-china.com/mp/a179929.html)
- [21ic BMS 标签页](https://www.21ic.com/tags/bms)、[EEWORLD BMS 全方位解析](https://bbs.eeworld.com.cn/thread-1309359-1-1.html) — 遇到具体问题时的检索入口

**实践任务**：

1. 拆解一块成品保护板（如 3S 三元锂保护板），反推电路。
2. 调试 [立创开源 BQ76920 5S BMS 工程](https://oshwhub.com/kaijun/mps-energy-station)，实测过充/过放保护阈值与静态功耗。

**验收**：能独立说明一块保护板上每个关键器件的作用，并实测验证保护动作。

---

## 阶段 3：进阶——AFE + MCU 的智能 BMS（1–2 个月）

**目标**：设计并实现一块"采样 + 均衡 + 保护 + 通信"的完整智能 BMS。这是从硬件爱好者到 BMS 工程师的分水岭。

**核心概念**：AFE（模拟前端）架构与寄存器；电压/电流/温度采样链路；被动/主动均衡电路；高边/低边 MOS 驱动；菊花链与电气隔离；EMC 设计。

**AFE 选型**：

- **TI BQ769x0 / BQ769x2**（≤16S，中文资料与开源生态最全，入门首选）
- **ADI LTC6811 / LTC6813**（车规高压，isoSPI 菊花链，EV 级）
- **瑞萨 ISL94202 / ISL94203**（平衡之选）

**推荐资料（按精读顺序）**：

1. [vamoirid/Battery-Management-System-LTC6811-STM32](https://github.com/vamoirid/Battery-Management-System-LTC6811-STM32)（55★）— 结构最清晰的入门工程：LTC6811 从板 + STM32F4
2. [LibreSolar/bms-firmware](https://github.com/LibreSolar/bms-firmware)（262★）+ [bms-c1 硬件](https://github.com/LibreSolar/bms-c1)（262★）— Zephyr 固件，同时支持 bq769x0/bq769x2/ISL94202，可直接烧录学习
3. [foxBMS 文档](https://foxbms.org/) — Fraunhofer 工业级平台，文档本身就是 BMS 架构教材；源码 [foxBMS/foxbms-2](https://github.com/foxBMS/foxbms-2)（479★）
4. [BotoX/xiaomi-m365-compatible-bms](https://github.com/BotoX/xiaomi-m365-compatible-bms)（219★）— 量产级固件（ATmega328P + BQ769x0），看真实产品怎么写
5. [TI ESS BMS 方案页](https://www.ti.com.cn/solution/zh-cn/ess-battery-management-system-bms) + [TI E2E 电源管理论坛](https://e2e.ti.com/support/power-management-group/power-management/f/power-management-forum) — 参考设计 + 实战答疑
6. [EEVblog：Learning Path for building my own BMS](https://www.eevblog.com/forum/beginners/learning-path-for-buiding-my-own-bms/)、[Seeking constructive criticism on BMS design](https://www.eevblog.com/forum/projects/seeking-constructive-criticism-on-bms-design/) — 设计评审类长帖

**实践任务**：

1. 抄一块 8–16S BMS 原理图（以 LibreSolar bms-c1 为蓝本），完成 PCB 设计。
2. 烧录 LibreSolar 固件跑通电压/温度采集与被动均衡；有余力则自写 bq769x2 驱动。

**验收**：自研板能稳定采集全部串电压（误差 <10mV）、实现被动均衡，并通过所有保护项实测。

---

## 阶段 4：核心——SOC / SOH / SOP 估算算法（1–3 个月）

**目标**：实现可用的 SOC 估算（误差 <5%），理解 SOH 与 SOP。这是 BMS 的软件核心。

**核心概念**：安时积分（库仑计）；OCV-SOC 曲线与静置修正；等效电路模型（Thevenin / 二阶 RC）；卡尔曼滤波 EKF/UKF；容量与内阻衰退模型。

**推荐资料（按顺序）**：

1. **Coursera 专项课：[Algorithms for Battery Management Systems](https://www.coursera.org/specializations/algorithms-for-battery-management-systems)**（Gregory Plett，科罗拉多大学博尔德分校）— 该领域最系统的公开课程：
   - [Introduction to Battery Management Systems](https://www.coursera.org/learn/battery-management-systems)
   - [Battery State-of-Charge (SOC) Estimation](https://www.coursera.org/learn/battery-state-of-charge)（重点）
   - [Battery Pack Balancing and Power Estimation](https://www.coursera.org/learn/battery-pack-balancing-power-estimation)
2. **Plett 三部曲**（Artech House，作者主页 http://mocha-java.uccs.edu/）：Vol. I *Battery Modeling*、Vol. II *Equivalent-Circuit Methods*、Vol. III *Physics-Based Methods*
3. [AlterWL/Battery_SOC_Estimation](https://github.com/AlterWL/Battery_SOC_Estimation)（437★）— 卡尔曼滤波 SOC 的 MATLAB 实现，上手最快
4. [ks-santosh/MiniBMS](https://github.com/ks-santosh/MiniBMS)（60★）— Simulink 完整模型（SOC + 故障检测 + 状态机），仿真入门
5. [raghuramshankar/soc-estimation-of-li-ion-batteries](https://github.com/raghuramshankar/soc-estimation-of-li-ion-batteries) — EKF + OCV-SOC 建模 + 公开数据集使用说明
6. [mohammadrezwankhan/matlab-simulink-energy-lab](https://github.com/mohammadrezwankhan/matlab-simulink-energy-lab)（317★）— SOC EKF、热管理、BESS 控制的可复现参考模型
7. 中文教材：谭晓军《电动汽车动力电池管理系统设计》、熊瑞《动力电池管理系统核心算法》（[知乎书籍推荐](https://www.zhihu.com/question/352224059)）

**实践任务**：

1. 用 [Battery Archive](https://www.batteryarchive.org/) 公开数据在 MATLAB/Simulink 复现 EKF SOC 估算。
2. 把安时积分 + OCV 修正的简化 SOC 算法移植到阶段 3 的 MCU 上运行。

**验收**：能讲清 EKF 的状态方程与观测方程；自实现的 SOC 在恒流放电工况下误差 <5%。

---

## 阶段 5：系统——通信与集成（2–4 周）

**目标**：让 BMS 接入真实系统——上位机、储能逆变器、整车 CAN。

**核心概念**：UART / RS485-Modbus / CAN / SMBus / BLE 帧协议；隔离与电平匹配；CRC 校验；商用 BMS 私有协议逆向。

**推荐资料**：

- [BMS Communication Architectures — batterydesign.net](https://www.batterydesign.net/battery-management-system/hardware/bms-communication-architectures/) — 架构综述
- [Battery BMS Communication: CAN vs RS485](https://liniotech.com/blog/battery-bms-communication-can-vs-rs485-explained/)、[BMS 通信协议与网关集成](https://www.come-star.com/blog/bms-communication-protocols/)
- **协议实战文档（syssi 系列，即各品牌协议的事实文档）**：
  - [esphome-jk-bms](https://github.com/syssi/esphome-jk-bms)（1026★，UART/BLE）
  - [esphome-jbd-bms](https://github.com/syssi/esphome-jbd-bms)（258★）
  - [esphome-seplos-bms](https://github.com/syssi/esphome-seplos-bms)（119★，RS485/Modbus）
  - [esphome-pace-bms](https://github.com/syssi/esphome-pace-bms)（92★）
- [fl4p/batmon-ha](https://github.com/fl4p/batmon-ha)（522★）— JK/JBD/Daly/ANT BLE 集成到 Home Assistant
- [dexterbg/Twizy-Virtual-BMS](https://github.com/dexterbg/Twizy-Virtual-BMS)（94★）— 车规 CAN 协议仿真
- 社区实战帖：[DIY Solar Forum](https://diysolarforum.com/forums/second-life-lithium-batteries.24/)、[ST Community BMS 通信讨论](https://community.st.com/others-hardware-and-software-57/communication-protocols-between-microcontrollers-for-a-bms-151918)

**实践任务**：用 ESP32 通过 UART 或 BLE 读取一块商用 BMS（如 JK 或小翔）的数据，解析帧格式并上传 Home Assistant。

**验收**：能独立逆向一段未知 BMS 协议（帧头/长度/数据域/CRC），并写出解析器。

---

## 阶段 6：精通——工程化与前沿（持续）

**目标**：达到产品级水准，能独立完成一个可发布的 BMS 产品或开源项目。

**方向与资料**：

- **储能系统级**：[stuartpittaway/diyBMSv4](https://github.com/stuartpittaway/diyBMSv4)（1136★）+ [Second Life Storage 社区](https://secondlifestorage.com/index.php) — 模块化/分布式 BMS 架构、实战项目最多的社区
- **EV 高压**： [EnnoidMe/ENNOID-BMS](https://github.com/EnnoidMe/ENNOID-BMS)（330★）— LTC68xx 菊花链、400V 电池包、接触器控制；配合功能安全标准 ISO 26262、国标 GB 38661（电动汽车 BMS 安全要求）研读
- **电化学建模**：[pybamm-team/PyBaMM](https://github.com/pybamm-team/PyBaMM)（1673★，Python 物理建模事实标准）+ [liionpack](https://github.com/pybamm-team/liionpack)（120★，电池包级仿真）
- **数据驱动前沿**：[MichaelBosello/battery-rul-estimation](https://github.com/MichaelBosello/battery-rul-estimation)（198★，LSTM 寿命预测）、[alexdatadesign/lfp_soc_ml](https://github.com/alexdatadesign/lfp_soc_ml)（39★）、数据集 [TBSI-Sunwoda](https://github.com/terencetaothucb/TBSI-Sunwoda-Battery-Dataset)（63★）、[awesome-battery-data](https://github.com/pauljgasper/awesome-battery-data)
- **逆向工程能力**：[tinfever/FW-Dyson-BMS](https://github.com/tinfever/FW-Dyson-BMS)（934★）、[omarKmekkawy/Reverse_Engineering_BQ20z70_Laptop_BMS](https://github.com/omarKmekkawy/Reverse_Engineering_BQ20z70_Laptop_BMS)（132★，笔记本 SBS/SMBus）
- **完整开源项目参考**：[Green-bms/SmartBMS](https://github.com/Green-bms/SmartBMS)（751★，[知乎中文解读](https://zhuanlan.zhihu.com/p/669013095)）、[LibreSolar 全家](https://github.com/LibreSolar/bms-15s80-sc)

**实践任务（毕业项目）**：完成一个完整开源 BMS 项目（原理图 + PCB + 固件 + SOC 算法 + 通信协议 + 文档），发布到 GitHub 或立创开源硬件平台，并接受社区评审（可发到 EEVblog / EEWORLD 求评）。

---

## 快速检索：按问题找资料

| 遇到问题 | 去哪里 |
|---|---|
| 芯片选型 / BQ 寄存器配置 | [TI E2E 论坛](https://e2e.ti.com/support/power-management-group/power-management/f/power-management-forum) + TI 方案页 |
| 保护板硬件细节 | [21ic BMS 板块](https://www.21ic.com/tags/bms)、CSDN S-8254A 解析 |
| 硬件设计求评审 | [EEVblog 论坛](https://www.eevblog.com/forum/)、EEWORLD |
| 储能系统实战 | [Second Life Storage](https://secondlifestorage.com/)、[DIY Solar Forum](https://diysolarforum.com/) |
| 算法公式推导 | Plett 课程与书、AlterWL 仓库 |
| 协议帧格式 | syssi 系列仓库 README / 源码 |
| 电池化学疑问 | [Battery University](https://batteryuniversity.com/) |
