# 附录 C 术语表

**表 C-1**　全书 46 条缩写术语速查（定义以正文为准）

| 缩写 | 英文 | 中文 | 说明 |
|---|---|---|---|
| AFE | Analog Front End | 模拟前端 | 多串电压/温度采样与均衡驱动 |
| BMS | Battery Management System | 电池管理系统 | 本书主题 |
| BMU | Battery Management Unit | 电池管理单元 | 有时指主控，有时指从控 |
| BCU | Battery Control Unit | 电池控制单元 | 常指 pack 主控 |
| CMC | Cell Monitoring Circuit | 单体监测电路 | 从控/采样板 |
| SOC | State of Charge | 荷电状态 | 剩余电量百分比 |
| SOH | State of Health | 健康状态 | 容量/功率衰减程度 |
| SOP | State of Power | 功率状态 | 未来时间窗口的允许功率 |
| OCV | Open Circuit Voltage | 开路电压 | 静置后端电压 |
| EKF | Extended Kalman Filter | 扩展卡尔曼滤波 | 非线性状态估计 |
| UKF | Unscented Kalman Filter | 无迹卡尔曼滤波 | 另一类非线性滤波 |
| RLS | Recursive Least Squares | 递推最小二乘 | 在线参数辨识 |
| HPPC | Hybrid Pulse Power Characterization | 混合脉冲功率特性 | 常用参数辨识工况 |
| IMD | Insulation Monitoring Device | 绝缘监测装置 | 高压对机壳绝缘电阻监测 |
| EOL | End of Line | 下线检测 | 生产末端测试 |
| HIL | Hardware-in-the-Loop | 硬件在环 | 控制器接仿真模型测试 |
| SPM | Single Particle Model | 单粒子模型 | 简化电化学模型 |
| SPMe | SPMe | 扩展单粒子模型 | 增加电解液动力学 |
| DFN | Doyle-Fuller-Newman | 全阶电化学模型 | 常用高精度基准 |
| SEI | Solid Electrolyte Interphase | 固体电解质界面膜 | 与老化/产气相关 |
| C-rate | C-rate | 倍率 | 1C = 1 小时放完额定容量 |
| DBC | Database CAN | CAN 数据库 | 信号定义文件 |
| E2E | End-to-End | 端到端保护 | CRC/计数器/超时 |
| OSHWA | Open Source Hardware Association | 开源硬件协会 | 开源硬件认证 |
| FMEA | Failure Mode and Effects Analysis | 失效模式与影响分析 | 风险分析 |
| FTA | Fault Tree Analysis | 故障树分析 | 自顶向下分析 |
| PCS | Power Conversion System | 储能变流器 | 储能系统功率变换 |
| EMS | Energy Management System | 能量管理系统 | 上层调度 |
| NIS | Normalized Innovation Squared | 归一化新息平方 | 残差相对噪声的度量 |
| NEES | Normalized Estimation Error Squared | 归一化估计误差平方 | 需要状态参考真值及误差协方差，不能只凭电压新息计算 |
| Joseph form | Joseph covariance update | Joseph 协方差更新 | 显式保留状态与测量协方差项，改善数值结构 |
| Observability | Observability | 可观测性 | 状态能否由输入与输出区分；满秩不等于噪声下可准确估计 |
| OVP / UVP | Over / Under Voltage Protection | 过压 / 欠压保护 | 通常连续 N 拍去抖后动作 |
| OCD / SCD | Over Current Discharge / Short Circuit Discharge | 过流 / 短路放电保护 | SCD 常本拍锁存 |
| UT / OT | Under / Over Temperature | 低温 / 过温保护 | 过温通常双断 |
| DTC | Diagnostic Trouble Code | 诊断故障码 | ISO 15031-6 三字节格式 |
| DID | Data Identifier | 数据标识符 | UDS 0x22/0x2E 读写的地址 |
| NRC | Negative Response Code | 负响应码 | UDS 负响应 0x7F + 服务 + NRC |
| UDS | Unified Diagnostic Services | 统一诊断服务 | ISO 14229，读写/故障/刷写 |
| FBL / SBL | Factory / Secondary Bootloader | 出厂引导 / 刷写引导 | 31.5 刷写两阶段 |
| HVIL | High Voltage Interlock Loop | 高压互锁 | 环路断线即禁止上高压 |
| HARA | Hazard Analysis and Risk Assessment | 危害分析与风险评估 | 功能安全流程第一步 |
| ASIL | Automotive Safety Integrity Level | 汽车安全完整性等级 | A–D 定级，须按场景评估 |
| FTTI | Fault Tolerant Time Interval | 故障容忍时间间隔 | 检测+去抖+反应的口袋预算 |
| K 值 | （自放电率分选指标） | 自放电率 | 产线常用 mV/h，注意时间窗口 |
| BCL | Battery Charge Limit | 电池充电需求 | GB/T 27930 充电机报文 |
