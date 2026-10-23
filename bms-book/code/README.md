# code/ — 十四个可运行的迷你实验

支持 Python 3.10+；`hppc_fit.py`、`pybamm_fit.py` 需要 `numpy`，其余仅用标准库。在仓库根安装 `bms-book/requirements.txt`；本页表格命令从 `bms-book/` 目录运行。

| 文件 | 验证什么 | 运行 |
|---|---|---|
| `soc_coulomb_ocv.py` | 库仑计数、OCV 校正、电流偏置、容量误差 | `python code/soc_coulomb_ocv.py` |
| `ekf_soc.py` | 两状态 EKF 与纯库仑的 RMSE 对比 | `python code/ekf_soc.py` |
| `hppc_fit.py` | 从脉冲反推 R0/R1/C1；40 s 窗的偏差 | `python code/hppc_fit.py` |
| `frame_parser.py` | CRC-8、坏帧丢弃、重同步、残帧 flush | `python code/frame_parser.py` |
| `thermal_lump.py` | 集总热模型：稳态、τ、熵热、充放不对称、低通 | `python code/thermal_lump.py` |
| `cccv_charge.py` | CC-CV：安时账、充电地图、判满判据 | `python code/cccv_charge.py` |
| `ic_dv.py` | dQ/dV 两座峰：老化指纹、欧姆位移、窗口容量 | `python code/ic_dv.py` |
| `balancing_energy.py` | 均衡能量账：被动烧掉 vs 主动搬运 | `python code/balancing_energy.py` |
| `data_audit.py` | 行级体检：8 项检查抓注入瑕疵 | `python code/data_audit.py` |
| `insulation_bridge.py` | 不平衡桥解绝缘电阻；平衡桥漏检对称退化 | `python code/insulation_bridge.py` |
| `pybamm_fit.py` | 仿真当裁判：平台标定 ECM，两端露馅（合成） | `python code/pybamm_fit.py` |
| `uds_demo.py` | 迷你 UDS：会话、seed-key、DID、NRC 全家桶 | `python code/uds_demo.py` |
| `measurement_budget.py` | 绝对上界、随机噪声、偏置与同步误差、保护裕量 | `python code/measurement_budget.py` |
| `estimator_evidence.py` | 观测权重、同分布不同时间结构、SOH 端点误差 | `python code/estimator_evidence.py` |

参考输出（2026-10，Windows / Python 3.13；`check.py` 会把这些数字与书中引用对账）：

```text
soc_coulomb_ocv: bias 51.90% vs OCV-corrected 46.15%（真值 40%）
ekf_soc:         coulomb 9.4605% vs EKF 0.1382%
hppc_fit:        R0 0.47%、R1 0.44%、C1 0.41%；40 s 窗 R1 17.5%
frame_parser:    2 好帧、1 坏 CRC、1 残帧、5 次重同步
thermal_lump:    29.9→31.117 °C（熵 +1.217 K）、τ=120 s、充放差 2.424 K
cccv_charge:     恒流 48 min 收 1.60 Ah；恒压 29 min 才 0.30 Ah（占总时间 37%）
ic_dv:           峰 (3.400 V, 1.200)/(3.680 V, 0.700)；老化 ×0.65、+30 mV；1.80 Ah → SOH 90%
balancing_energy: passive 25.0 h / 4.0 Wh vs active 0.5 h / 0.7 Wh（50× 快、省 5.7×）
data_audit:      3/3 defects caught（越界 1、卡死 5、时间戳 1），0 false positives
insulation_bridge: 40 kΩ 临界判 FAULT；对称退化被平衡桥漏检、被不平衡桥检出
pybamm_fit:      R0 est 30.20 mΩ；分窗 RMSE 3.08 / 14.32 / 19.87 mV（两端 5.5× 平台）
uds_demo:        0x27 错钥匙 7F 27 35 → 对钥匙 67 02；编程会话门禁与锁死全覆盖
measurement_budget: 4.50 mV → 6.00 个百分点；7 天偏置 8.40 个百分点；同步 100.0 mV；触发裕量 3643.50 mV
```

约定与正文一致：**充电为正**，SOC 用 0–1，所有阈值为教学示例。
这些脚本是"最小可复现实验"，不是量产实现；量产参考见 BMS-Z、foxBMS 2 与 LibreSolar。
