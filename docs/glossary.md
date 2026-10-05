# BMS 术语表

> 中英对照 + 一句话解释 + 反向索引（点链接跳到讲透它的章节）。
> 按主题分组；查单个术语用 Ctrl+F 更快。

## 系统与架构

| 术语 | 全称 / 英文 | 一句话 | 详解 |
|---|---|---|---|
| BMS | Battery Management System | 电池管理系统：监测、保护、均衡、估算、通信五件事 | [阶段 1](stages/stage-1-认识BMS.md) |
| AFE | Analog Front End | 模拟前端：专职高精度采样与硬件保护的芯片（如 BQ769x2） | [详解 ②](circuits/02-采样链与AFE芯片.md) |
| BMU | Battery Management Unit | 主控板：对外通信、汇总决策、继电器驱动 | [阶段 6](stages/stage-6-精通与毕业项目.md#611-高压电池系统架构-分析) |
| CMU | Cell Monitoring Unit | 从板：每组 12–18 串的采样与均衡执行 | 同上 |
| BDU | Battery Disconnect Unit | 配电盒：主继电器、预充、熔断器、电流传感器 | 同上 |
| 并簇 / 环流 | Parallel strings / Circulating current | 多包并联时压差驱动的包间电流；合闸前须对齐 | [阶段 6 §6.1.5](stages/stage-6-精通与毕业项目.md) |
| TMS | Thermal Management System | 热管理：加热/制冷执行；与 BMS 分工见阶段 6 | [阶段 6 §6.1.6](stages/stage-6-精通与毕业项目.md) |
| 保护板 | Protection Board | 无 MCU 的纯硬件保护：阈值写死、不认识 SOC | [阶段 1 §1.6](stages/stage-1-认识BMS.md) |
| 菊花链 | Daisy Chain | 多颗 AFE 逐级"接收→再生→转发"的级联方式 | [详解 ② §7](circuits/02-采样链与AFE芯片.md) |
| 同口 / 分口 | Common / Separate Port | 充放电共用一个 MOS 组 / 充放电 MOS 分开 | [详解 ① §2.3](circuits/01-功率回路-MOS保护与预充.md) |

## 电池与状态量

| 术语 | 全称 / 英文 | 一句话 | 详解 |
|---|---|---|---|
| SOC | State of Charge | 荷电状态：还剩多少电（分母是**当前**满充容量） | [阶段 4](stages/stage-4-SOC-SOH算法.md) |
| SOH | State of Health | 健康状态：容量口径与内阻口径两种 | [阶段 4 §4.6](stages/stage-4-SOC-SOH算法.md) |
| SOP | State of Power | 此刻能出多大力：多约束取最小 | [阶段 4 §4.7](stages/stage-4-SOC-SOH算法.md) |
| OCV | Open Circuit Voltage | 开路电压：静置后与 SOC 单调对应 | [阶段 4 §4.3](stages/stage-4-SOC-SOH算法.md) |
| C 倍率 | C-rate | 1C = 一小时放完额定容量的电流 | [阶段 0 §0.1.5](stages/stage-0-前置知识.md) |
| CC-CV | Constant Current – Constant Voltage | 恒流转恒压充电法；满充看 CV 截止电流 | [详解 ③ §1](circuits/03-充电均衡与计量.md) |
| NCM / LFP / LCO | 三元 / 磷酸铁锂 / 钴酸锂 | 三种主流正极化学体系，性格迥异 | [阶段 0 §0.1.1](stages/stage-0-前置知识.md) |
| 固态电池 | Solid-state battery | 固体电解质代替液态电解液；阈值和 OCV 表要换，短路保护仍要留 | [阶段 0 §0.1.8](stages/stage-0-前置知识.md#018-固态电池固体电解质换掉了什么-理解) |
| 结构电池 | Structural battery | 碳纤维兼做电极和承力件。碳纤维外壳里的普通电芯不是这一类 | [阶段 0 §0.1.9](stages/stage-0-前置知识.md#019-碳纤维结构电池电极在承力外壳是另一件事-理解) |
| 析锂 / 锂枝晶 | Li Plating / Dendrite | 锂来不及嵌入石墨而析出金属锂，长成针可刺穿隔膜 | [阶段 0 §0.1.2](stages/stage-0-前置知识.md) |
| 热失控 | Thermal Runaway | 放热→升温→更放热的自我加速链式反应 | [阶段 1 §1.5](stages/stage-1-认识BMS.md) |
| dT/dt | 温升速率 | 比绝对温度更早的热失控信号 | [阶段 1 §1.5](stages/stage-1-认识BMS.md) |
| OCV 滞回 | OCV Hysteresis | 充放电方向 OCV 曲线不重合，差几十 mV | [阶段 4 §4.3](stages/stage-4-SOC-SOH算法.md) |
| 极化 | Polarization | 电流让端电压偏离 OCV 的压差分量；静置几分钟到几小时才消散，OCV 查表前必须等它 | [阶段 4 §4.3](stages/stage-4-SOC-SOH算法.md) |
| 木桶效应 | Barrel Effect | 串联可用容量被最弱单体锁死；Ah 不相加 | [阶段 1 §1.2](stages/stage-1-认识BMS.md) |

## 功率器件与保护

| 术语 | 全称 / 英文 | 一句话 | 详解 |
|---|---|---|---|
| MOSFET | 金属氧化物半导体场效应管 | 电控闸门：BMS 里最重要的器件 | [详解 ① §1](circuits/01-功率回路-MOS保护与预充.md) |
| 体二极管 | Body Diode | MOS 制造白送的并联单向阀，单颗永远关不死双向 | [详解 ① §1.2](circuits/01-功率回路-MOS保护与预充.md) |
| 背靠背 | Back-to-Back | 两颗 MOS 反向串联实现双向阻断（共漏/共源） | [详解 ① §1.2](circuits/01-功率回路-MOS保护与预充.md) |
| 高边 / 低边驱动 | High-/Low-side | 保护开关串在 B+ 或 B−；高边源极浮动需浮地驱动 | [阶段 3 §3.5](stages/stage-3-AFE-MCU智能BMS.md)、[详解 ① §1.4](circuits/01-功率回路-MOS保护与预充.md) |
| 自举（电容） | Bootstrap | 高边驱动的浮地「充电宝」：借开关节点摆动给上管栅泵电，不能常开 | [详解 ① §1.4](circuits/01-功率回路-MOS保护与预充.md)、[阶段 3 §3.5](stages/stage-3-AFE-MCU智能BMS.md) |
| VDS / RDS(on) / Qg | 耐压 / 导阻 / 栅电荷 | MOS 选型三参数 | [详解 ① §1.3](circuits/01-功率回路-MOS保护与预充.md) |
| EAS | 雪崩能量额定 | 关断感性负载时 MOS 承受高压尖峰的能力 | [详解 ① §1.3](circuits/01-功率回路-MOS保护与预充.md) |
| I²t | 电流平方×时间 | 热损伤的量度；MOS、线束、熔断器配合的标尺 | [阶段 2 §2.3](stages/stage-2-保护板实践.md) |
| 预充 | Pre-charge | 先串电阻给母线电容充电再合主闸，防数千安冲击 | [详解 ① §3](circuits/01-功率回路-MOS保护与预充.md) |
| 母线电容 | DC-link Capacitor | 逆变器入口的蓄水池：吸纹波稳母线；裸合闸等于短路，所以要预充 | [详解 ① §3](circuits/01-功率回路-MOS保护与预充.md) |
| 熔断器 | Fuse | 不可复位的最后手段，与 MOS 保护按 I²t 配合 | [阶段 6 §6.1.4](stages/stage-6-精通与毕业项目.md) |
| IMD | Insulation Monitoring Device | 绝缘检测：主流电桥法交替投切解两个未知量 | [阶段 6 §6.1.3](stages/stage-6-精通与毕业项目.md) |
| TVS / ESD | 瞬态抑制二极管 / 静电 | 采样口与通信口的浪涌防护 | [阶段 3 §3.5](stages/stage-3-AFE-MCU智能BMS.md) |
| EMC | 电磁兼容 | 小信号采样链与功率回路噪声的攻防 | [阶段 6 §6.1.4](stages/stage-6-精通与毕业项目.md) |

## 采样与芯片

| 术语 | 全称 / 英文 | 一句话 | 详解 |
|---|---|---|---|
| MUX | 多路选择器 | 一颗 ADC 巡逻测 16 串：串间一致性好的来源 | [详解 ② §2](circuits/02-采样链与AFE芯片.md) |
| INL | 积分非线性 | ADC 刻度自身的弯曲程度 | [阶段 0 §0.2.2](stages/stage-0-前置知识.md) |
| 基准源 | Voltage Reference | 误差预算的第一项；温漂是头号敌人 | [详解 ② §1](circuits/02-采样链与AFE芯片.md) |
| 开线检测 | Open-wire Detection | 采样线断线检测：电流源拉一下看电压动不动 | [详解 ② §4](circuits/02-采样链与AFE芯片.md) |
| 开尔文接法 | Kelvin (4-wire) | 电流走一对端子、采样走另一对，剔除引线压降 | [详解 ② §8](circuits/02-采样链与AFE芯片.md) |
| 共模 | Common Mode | 两根信号线「一起抬」的那部分电压；高压包顶上的采样点共模数百伏，直连烧芯片 | [详解 ②](circuits/02-采样链与AFE芯片.md)、[阶段 3](stages/stage-3-AFE-MCU智能BMS.md) |
| 库仑计 | Coulomb Counter | AFE 内独立高速通道，硬件替你安时积分 | [详解 ② §5](circuits/02-采样链与AFE芯片.md) |
| DW01 | — | 单节保护 IC：三道判断题的保安 | [详解 ① §2](circuits/01-功率回路-MOS保护与预充.md) |
| S-8254A | — | 3–4 串保护 IC，不可级联；部分延时由外置电容（CDT/CCT）设定 | [阶段 2 §2.3](stages/stage-2-保护板实践.md) |
| BQ769x0/x2 | TI | ≤16S AFE 家族，中文资料最全 | [阶段 3 §3.2](stages/stage-3-AFE-MCU智能BMS.md) |
| LTC6811 / ADBMS | ADI | 12 串 AFE，isoSPI 菊花链，车规 | [阶段 3 §3.3](stages/stage-3-AFE-MCU智能BMS.md) |
| isoSPI | Isolated SPI | 变压器耦合的差分 SPI：信号穿墙、电位差留下 | [详解 ② §7](circuits/02-采样链与AFE芯片.md) |
| NTC | 负温度系数热敏电阻 | 越热阻值越小；下臂接法中点电压随温降 | [详解 ② §6](circuits/02-采样链与AFE芯片.md) |
| REGOUT | — | AFE 内置 LDO 输出，给 MCU 供电 | [详解 ② §5](circuits/02-采样链与AFE芯片.md) |

## 算法

| 术语 | 全称 / 英文 | 一句话 | 详解 |
|---|---|---|---|
| 安时积分 | Coulomb Counting | `SOC += I·dt/Q`；零漂会被积进去，误差不收敛 | [阶段 4 §4.2](stages/stage-4-SOC-SOH算法.md)、[代码](../code/soc/) |
| 满充校准 | Full-charge Reset | CV 截止电流 → 必然 100% → 复位 | [阶段 4 §4.2](stages/stage-4-SOC-SOH算法.md) |
| Thevenin 模型 | 一阶 RC 等效电路 | R0 瞬时压降 + R1C1 慢回弹 | [阶段 4 §4.4](stages/stage-4-SOC-SOH算法.md) |
| HPPC | 混合脉冲功率特性测试 | 打电流脉冲辨识 R0/R1/C1 的标准方法 | [阶段 4 §4.4](stages/stage-4-SOC-SOH算法.md) |
| EKF / UKF | 扩展/无迹卡尔曼滤波 | 预测+修正，谁可信多听谁 | [阶段 4 §4.5](stages/stage-4-SOC-SOH算法.md) |
| 双卡尔曼 | Dual EKF | 快滤波器估 SOC、慢滤波器估容量/内阻 | [阶段 4 §4.6](stages/stage-4-SOC-SOH算法.md) |
| 可观测性 | Observability | 参数只有在电流激励下才"看得见" | [阶段 4 §4.6](stages/stage-4-SOC-SOH算法.md) |
| 残差 | Residual / Innovation | 实测−预测；持续偏大=模型错了不是滤波器错了 | [阶段 4 §4.5](stages/stage-4-SOC-SOH算法.md) |

## 通信

| 术语 | 全称 / 英文 | 一句话 | 详解 |
|---|---|---|---|
| UART | 通用异步收发 | 商用 BMS 调试口最常见接口；注意电平与共地 | [阶段 5 §5.2](stages/stage-5-通信与集成.md) |
| RS485 | — | 差分半双工总线；两端 120Ω 终端 + 方向切换是坑 | [阶段 5 §5.3](stages/stage-5-通信与集成.md) |
| Modbus RTU | — | 储能界老干部；帧界靠 3.5 字符静默 | [阶段 5 §5.3](stages/stage-5-通信与集成.md) |
| CAN / CAN FD | 控制器局域网 | 车上官话；显性 0 盖隐性 1 的非破坏仲裁 | [阶段 5 §5.4](stages/stage-5-通信与集成.md) |
| DBC | CAN Database | CAN 报文的"寄存器映射表"：factor/offset 换算 | [阶段 5 §5.4](stages/stage-5-通信与集成.md) |
| SMBus / SBS | 智能电池系统 | 笔记本电池的国际标准命令集 | [阶段 5 §5.5](stages/stage-5-通信与集成.md) |
| BLE / GATT / MTU | 低功耗蓝牙 | 手机 App 监控主流；长帧要协商 MTU+分包重组 | [阶段 5 §5.5](stages/stage-5-通信与集成.md) |
| MQTT | 消息队列遥测传输 | 物联网发布/订阅主力；TLS 与遗嘱消息是底线 | [ESP32 专题](esp32-bms专题.md) §4 |
| CRC | 循环冗余校验 | 五自由度：多项式/初值/反射×2/异或；先用已知帧验证程序 | [阶段 5 §5.6](stages/stage-5-通信与集成.md)、[代码](../code/protocol/) |

## 功能安全与标准

| 术语 | 全称 / 英文 | 一句话 | 详解 |
|---|---|---|---|
| ISO 26262 / GB/T 34590 | 道路车辆功能安全 | 车规功能安全母标准 | [阶段 6 §6.4](stages/stage-6-精通与毕业项目.md) |
| HARA | 危害分析与风险评估 | 定安全目标与 ASIL 的前置分析 | [bms-resources §6.3](bms-resources.md) |
| ASIL | 汽车安全完整性等级 | A→D 逐级严格；防过充常 C/D（由 HARA 定） | [阶段 6 §6.4](stages/stage-6-精通与毕业项目.md) |
| FMEA | 失效模式与影响分析 | 逐器件问"它坏了会怎样" | [bms-resources §6.3](bms-resources.md) |
| FTTI | 故障容忍时间间隔 | 约束诊断周期：检测+反应必须小于它 | [阶段 6 §6.4](stages/stage-6-精通与毕业项目.md) |
| IMD | 绝缘监测装置 | 高压包对壳绝缘的专职哨兵；电桥/注入/外置三路线 | [阶段 6 §6.1.3](stages/stage-6-精通与毕业项目.md) |
| Y 电容 | — | 母线对壳滤波电容；绝缘测量稳态窗的量化依据 | [阶段 6 §6.1.3](stages/stage-6-精通与毕业项目.md) |
| SPFM / LFM | 单点/潜伏故障度量 | ASIL 达标要算的两个覆盖率指标 | [bms-resources §6.3](bms-resources.md) |
| GB/T 38661 / 39086 | 车用 BMS 技术条件 / 功能安全要求 | 中国国标，38661 全文公开 | [bms-resources §6.3](bms-resources.md) |
| GB/T 27930 | 充电机-BMS 通信协议 | 直流桩握手：辨识→参数→周期需求→超时停充 | [阶段 5 §5.4.1](stages/stage-5-通信与集成.md) |
| UL 1973 / IEC 62619 / UN 38.3 | 储能 / 工业 / 运输安全标准 | 按目标市场选读 | [bms-resources §6.3](bms-resources.md) |

## 固件与量产

| 术语 | 全称 / 英文 | 一句话 | 详解 |
|---|---|---|---|
| 状态机 | State Machine | BMS 固件的灵魂：迁移集中一处 | [阶段 3 §3.4](stages/stage-3-AFE-MCU智能BMS.md)、[代码](../code/firmware/) |
| 去抖 | Debounce | 连续 N 拍超限才动作，躲开正常瞬态 | [阶段 3 §3.4](stages/stage-3-AFE-MCU智能BMS.md) |
| 锁存 | Latch | 严重故障保持断开，需明确条件才解锁 | [阶段 6 §6.2.2](stages/stage-6-精通与毕业项目.md) |
| DTC | 故障诊断码 + 快照 | 触发瞬间冻结现场；售后能力=快照质量 | [阶段 6 §6.2.2](stages/stage-6-精通与毕业项目.md) |
| UDS | 统一诊断服务 | 车规诊断协议，DTC 的对外格式 | [阶段 6 §6.2.2](stages/stage-6-精通与毕业项目.md) |
| 标定 | Calibration | 出厂写入电流零漂/电压增益等修正系数 | [阶段 6 §6.2.3](stages/stage-6-精通与毕业项目.md) |
| EOL | 下线测试 | 出厂前的全项检测清单 | [阶段 6 §6.5](stages/stage-6-精通与毕业项目.md) |
| HIL | 硬件在环 | 电芯模拟器 + 故障注入的测试台 | [阶段 6 §6.5](stages/stage-6-精通与毕业项目.md) |
| 电芯模拟器 | Cell Simulator/Emulator | 电阻分压链或多路隔离电源假装电池串 | [阶段 2 §2.6](stages/stage-2-保护板实践.md) |
| Bootloader / OTA / A/B 双区 | — | 永不被覆盖 + 断电可回滚，两条铁律 | [阶段 6 §6.2.4](stages/stage-6-精通与毕业项目.md) |
| 磨损均衡 | Wear Leveling | 参数区写次数均摊，防 Flash 写穿 | [阶段 6 §6.2.3](stages/stage-6-精通与毕业项目.md) |
| IWDG | 独立看门狗 | 自己带时钟：主时钟死了它还能复位 | [阶段 0 §0.3.1](stages/stage-0-前置知识.md) |
| FreeRTOS | — | MCU 上最主流的实时内核：任务/队列/事件组三件套 | [STM32 专题](stm32-bms专题.md)、[ESP32 专题](esp32-bms专题.md) |
| ESP-IDF | ESP32 IoT Development Framework | ESP32 原生开发框架；Arduino core 的底层就是它 | [ESP32 专题](esp32-bms专题.md) §3 |
| ADC 注入组 | Injected Channel Group | 定时器硬件触发的 ADC 通道组：I/V 同步采样的实现手段 | [STM32 专题](stm32-bms专题.md) §4 |
| PyBaMM | Python Battery Mathematical Modelling | 电化学机理建模的事实标准（前沿方向） | [bms-resources §6.5](bms-resources.md) |
| 无线 BMS | wBMS | 电芯数据经无线节点回传，省去菊花链线束 | [bms-resources §6.5](bms-resources.md) |

---

返回 [学习路线总纲](bms-resources.md) ｜ [器材与预算清单](budget.md)
