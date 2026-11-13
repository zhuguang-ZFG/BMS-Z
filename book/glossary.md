# 共享术语表

> 卷一与卷二的术语合并表；定义以正文为准，相关条目只做导航。

| 术语 | 英文 | 定义 | 所属卷 | 相关条目 |
|---|---|---|---|---|
| 虚短/虚断 | — | 深负反馈下，运放两输入端"电压相等、电流为零"——分析一切闭环运放电路的两公理 | 卷一 | 卷一·第 12 章《运放应用电路族：从节点方程到工作边界》 |
| 增益带宽积 GBW | GBW | 增益×带宽≈常数：要 100 倍增益，1MHz 运放只剩 10kHz 可用带宽 | 卷一 | 卷一·第 6 章《运算放大器：从内部结构到参数字典》 |
| 压摆率 SR | SR | 输出"每微秒最多爬几伏"——大信号正弦变三角波的元凶 | 卷一 | 卷一·第 6 章《运算放大器：从内部结构到参数字典》 |
| 轨到轨 Rail-to-Rail | Rail-to-Rail | 输入/输出能贴到电源轨（或几乎贴到）——单电源供电的救命参数 | 卷一 | 卷一·第 6 章《运算放大器：从内部结构到参数字典》 |
| 失调电压 V_OS | V_OS | 输入为 0 输出却不为 0——运放的"天生长歪"，µV 级是精密分水岭 | 卷一 | 卷一·第 6 章《运算放大器：从内部结构到参数字典》 |
| 共模抑制比 CMRR | CMRR | 两输入同涨同跌时输出纹丝不动的程度——差分对的看家本领 | 卷一 | 卷一·第 11 章《放大电路拓扑：三种组态与四大积木》 |
| PSRR | PSRR | 电源上的纹波被输出"吸走"多少 dB——电源脏了输出也脏 | 卷一 | 纹波 |
| 米勒效应 | — | 反馈电容被增益放大 A 倍——栅/集电极电容是设计者看不见的拖油瓶 | 卷一 | 卷一·第 4 章《MOSFET：电压控制的开关王者》 |
| 体二极管 | — | MOSFET 结构自带的寄生二极管，方向永远朝上——H 桥滑行全靠它 | 卷一 | 卷一·第 13 章《电源与信号产生电路》 |
| 上拉/下拉电阻 | — | 把悬空的线"请"到一个确定电平的电阻——I2C 4.7kΩ 的由来 | 卷一 | 卷一·第 5 章《输出结构彻底讲透：推挽、开漏、上拉下拉》 |
| 线与 Wired-AND | Wired-AND | 多个开漏输出并联：任何一家拉低线就是低——没有短路路径的安全并联 | 卷一 | 卷一·第 5 章《输出结构彻底讲透：推挽、开漏、上拉下拉》 |
| 死区时间 | — | 换向瞬间上下管"都别开"的空窗，1~2µs——没有它就是烧管倒计时 | 卷一 | 卷一·第 13 章《电源与信号产生电路》 |
| 迟滞/回差 | — | 比较器故意加宽的"模糊带"——噪声在门限附近抖也不误翻 | 卷一 | 卷一·第 7 章《比较器：专为"判决"而生》 |
| 伏秒平衡 | — | 开关电源稳态：电感一周期"充的伏秒=放的伏秒"——Buck 一切公式的根 | 卷一 | 卷一·第 13 章《电源与信号产生电路》 |
| 纹波 | — | 输出电压每周期的小锯齿——设计就是给它划红线 | 卷一 | 卷一·第 13 章《电源与信号产生电路》 |
| 温漂 ppm/°C | — | 每升温 1°C 变化百万分之几——基准与精密电阻的身价指标 | 卷一 | 卷一·第 9 章《电压基准与稳压器：系统的"定盘星"》 |
| 混叠 Aliasing | Aliasing | 采样不够快，高频信号伪装成低频假信号——软件救不回来的失真 | 卷一 | 卷一·第 13 章《电源与信号产生电路》 |
| 奈奎斯特 2 倍率 | — | 采样率必须 > 2×信号最高频率——混叠的第一道防线 | 卷一 | 卷一·第 13 章《电源与信号产生电路》 |
| LSB 量化台阶 | — | ADC 把连续电压切成 2^N 格，每格的高度——分辨率的天花板 | 卷一 | 卷一·第 13 章《电源与信号产生电路》 |
| 波特图 | — | 增益/相位随频率的"体检报告"——−20dB/dec 是一阶 RC 的指纹 | 卷一 | 卷一·第 12 章《运放应用电路族：从节点方程到工作边界》 |
| 戴维南等效 | — | 任何线性网络都能简化成一个电压源串一个电阻——化简万能钥匙 | 卷一 | 卷一·第 1 章《无源元件的真实面目》 |
| 寄生参数 | — | 元件"夹带"的 L/C/R——高频下反客为主的隐形元件 | 卷一 | 卷一·第 1 章《无源元件的真实面目》 |
| 回流路径/地弹 | — | 电流走环路：回流被切断，地电平就"跳"——数字电路让模拟失效的头号嫌犯 | 卷一 | 卷一·第 15 章《PCB 绘制注意事项》 |
| 自举 Bootstrap | Bootstrap | 一只电容把高侧管栅极"举"到比电源还高——否则高侧永远开不透 | 卷一 | 卷一·第 13 章《电源与信号产生电路》 |
| droop/电荷注入 | — | 保持电容漏电下垂 + 开关断开踢一脚——采样保持的两大天敌 | 卷一 | 卷一·第 8 章《模拟开关与多路复用器：CMOS 传输门》 |
| 巴克豪森判据 | — | 振荡的两个条件：环路增益=1、相移=0°——审视一切振荡电路的尺子 | 卷一 | 卷一·第 13 章《电源与信号产生电路》 |
| AFE（模拟前端） | Analog Front End | 多串电压/温度采样与均衡驱动 | 卷二 | — |
| BMS（电池管理系统） | Battery Management System | 本书主题 | 卷二 | — |
| BMU（电池管理单元） | Battery Management Unit | 有时指主控，有时指从控 | 卷二 | — |
| BCU（电池控制单元） | Battery Control Unit | 常指 pack 主控 | 卷二 | — |
| CMC（单体监测电路） | Cell Monitoring Circuit | 从控/采样板 | 卷二 | — |
| SOC（荷电状态） | State of Charge | 剩余电量百分比 | 卷二 | — |
| SOH（健康状态） | State of Health | 容量/功率衰减程度 | 卷二 | — |
| SOP（功率状态） | State of Power | 未来时间窗口的允许功率 | 卷二 | — |
| OCV（开路电压） | Open Circuit Voltage | 静置后端电压 | 卷二 | — |
| EKF（扩展卡尔曼滤波） | Extended Kalman Filter | 非线性状态估计 | 卷二 | — |
| UKF（无迹卡尔曼滤波） | Unscented Kalman Filter | 另一类非线性滤波 | 卷二 | — |
| RLS（递推最小二乘） | Recursive Least Squares | 在线参数辨识 | 卷二 | — |
| HPPC（混合脉冲功率特性） | Hybrid Pulse Power Characterization | 常用参数辨识工况 | 卷二 | — |
| IMD（绝缘监测装置） | Insulation Monitoring Device | 高压对机壳绝缘电阻监测 | 卷二 | — |
| EOL（下线检测） | End of Line | 生产末端测试 | 卷二 | — |
| HIL（硬件在环） | Hardware-in-the-Loop | 控制器接仿真模型测试 | 卷二 | — |
| SPM（单粒子模型） | Single Particle Model | 简化电化学模型 | 卷二 | — |
| SPMe（扩展单粒子模型） | SPMe | 增加电解液动力学 | 卷二 | — |
| DFN（全阶电化学模型） | Doyle-Fuller-Newman | 常用高精度基准 | 卷二 | — |
| SEI（固体电解质界面膜） | Solid Electrolyte Interphase | 与老化/产气相关 | 卷二 | — |
| C-rate（倍率） | C-rate | 1C = 1 小时放完额定容量 | 卷二 | — |
| DBC（CAN 数据库） | Database CAN | 信号定义文件 | 卷二 | — |
| E2E（端到端保护） | End-to-End | CRC/计数器/超时 | 卷二 | — |
| OSHWA（开源硬件协会） | Open Source Hardware Association | 开源硬件认证 | 卷二 | — |
| FMEA（失效模式与影响分析） | Failure Mode and Effects Analysis | 风险分析 | 卷二 | — |
| FTA（故障树分析） | Fault Tree Analysis | 自顶向下分析 | 卷二 | — |
| PCS（储能变流器） | Power Conversion System | 储能系统功率变换 | 卷二 | — |
| EMS（能量管理系统） | Energy Management System | 上层调度 | 卷二 | — |
| NIS（归一化新息平方） | Normalized Innovation Squared | 残差相对噪声的度量 | 卷二 | — |
| NEES（归一化估计误差平方） | Normalized Estimation Error Squared | 需要状态参考真值及误差协方差，不能只凭电压新息计算 | 卷二 | — |
| Joseph form（Joseph 协方差更新） | Joseph covariance update | 显式保留状态与测量协方差项，改善数值结构 | 卷二 | — |
| Observability（可观测性） | Observability | 状态能否由输入与输出区分；满秩不等于噪声下可准确估计 | 卷二 | — |
| OVP / UVP（过压 / 欠压保护） | Over / Under Voltage Protection | 通常连续 N 拍去抖后动作 | 卷二 | — |
| OCD / SCD（过流 / 短路放电保护） | Over Current Discharge / Short Circuit Discharge | SCD 常本拍锁存 | 卷二 | — |
| UT / OT（低温 / 过温保护） | Under / Over Temperature | 过温通常双断 | 卷二 | — |
| DTC（诊断故障码） | Diagnostic Trouble Code | ISO 15031-6 三字节格式 | 卷二 | — |
| DID（数据标识符） | Data Identifier | UDS 0x22/0x2E 读写的地址 | 卷二 | UDS（统一诊断服务） |
| NRC（负响应码） | Negative Response Code | UDS 负响应 0x7F + 服务 + NRC | 卷二 | UDS（统一诊断服务） |
| UDS（统一诊断服务） | Unified Diagnostic Services | ISO 14229，读写/故障/刷写 | 卷二 | — |
| FBL / SBL（出厂引导 / 刷写引导） | Factory / Secondary Bootloader | 31.5 刷写两阶段 | 卷二 | — |
| HVIL（高压互锁） | High Voltage Interlock Loop | 环路断线即禁止上高压 | 卷二 | — |
| HARA（危害分析与风险评估） | Hazard Analysis and Risk Assessment | 功能安全流程第一步 | 卷二 | — |
| ASIL（汽车安全完整性等级） | Automotive Safety Integrity Level | A–D 定级，须按场景评估 | 卷二 | — |
| FTTI（故障容忍时间间隔） | Fault Tolerant Time Interval | 检测+去抖+反应的口袋预算 | 卷二 | — |
| K 值（自放电率） | — | 产线常用 mV/h，注意时间窗口 | 卷二 | — |
| BCL（电池充电需求） | Battery Charge Limit | GB/T 27930 充电机报文 | 卷二 | — |
