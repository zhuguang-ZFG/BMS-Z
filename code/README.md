# code/ — 教程配套参考实现

> 按层进入：[能力地图](../docs/stages/bloom-map.md)。三个目录的主层级见下表；逐行走读和进阶实验入口都在本页。
>
> 教程里**可在 PC 上跑通的那几项**动手任务，这里有能跑、有测试的最小实现。
> 硬件抄板 / ESP32 联调 / 毕业项目等仍须动手，仓库不替代实物。

| 目录 | 主层级 | 内容 | 对应教程 | 运行 |
|---|---|---|---|---|
| `soc/` | 分析 | Thevenin 模型 + 三种估算器对比、合成 HPPC、SOP 双法（闭式 HPPC vs 二分 + ESC）、集总热模型（稳态 / τ / 可逆热 / 正弦低通），以及 NASA RW3 实测标定与独立工况回放 | [阶段 4](../docs/stages/stage-4-SOC-SOH算法.md) §4.7、§4.10 任务 1–2 · [真实数据实验](../docs/SOC真实数据专题.md) · [ECE5710 Notes07 中文导读](../docs/ece5710-notes07-中文导读.md) | `cd soc && python3 compare.py --plot`；`python3 hppc_demo.py`；`python3 sop_demo.py`；`python3 thermal_demo.py`；`python3 real_data.py --plot` |
| `protocol/` | 应用 | CRC-8/16 校验 + UART 帧状态机解析器（坏帧丢弃并计数、垃圾前缀重同步） | [阶段 5](../docs/stages/stage-5-通信与集成.md) §5.2 / §5.6 | `cd protocol && python3 -m pytest tests/ -q` |
| `firmware/` | 应用 | BMS 主状态机骨架（保护去抖 / 故障分级枚举 / 快照 / 锁存 / 均衡 / 休眠），另有不改保护逻辑的快照回放 | [阶段 3](../docs/stages/stage-3-AFE-MCU智能BMS.md) §3.4、[阶段 6](../docs/stages/stage-6-精通与毕业项目.md) §6.2 与 [§6.2.5](../docs/stages/stage-6-精通与毕业项目.md#625-故障注入与快照回放-应用) | `cd firmware && gcc -std=c99 -Wall -Wextra -Werror -o test_bms bms.c test_bms.c && ./test_bms`；回放再编 `hil_replay`，命令见固件 README |

**把模块接起来**：[PC 综合实验](../docs/PC综合实验专题.md)复用三个目录中的代码。在仓库根运行 `python code/firmware/pc_demo.py`，得到逐拍采样、遥测字节流、接收日志与验收报告；需要 gcc。

**未覆盖（刻意留白）**：阶段 0–2 实物实验；阶段 3 抄板/AFE 驱动；跨电芯与全温区参数标定、§4.10 任务 3（上板）；阶段 5 任务 1–2（ESP32 / Home Assistant）；阶段 6 实物毕业项目。`hil_replay` 和 PC 综合实验都不是硬件实验台，没有开线检测。固件骨架也未实现预充、充电过流 OCC、欠温 UT、WARN/LIMP 动作——见 `firmware/bms.h` 顶部说明。

## 本页目录

按层走先看 [能力地图](../docs/stages/bloom-map.md)。标题末尾的 `[记忆]` … `[创造]` 是布鲁姆层级。

- [code/ — 教程配套参考实现](README.md#code--教程配套参考实现)
- [环境](README.md#环境)
- [设计约定（与教程全文一致）](README.md#设计约定与教程全文一致)
- [给自学者的使用建议](README.md#给自学者的使用建议)
- [代码走读（带行号） [应用]](README.md#代码走读带行号-应用)
  - [soc/：三种估算器的分歧只有"怎么校正"（对应阶段 4） [分析]](README.md#soc三种估算器的分歧只有怎么校正对应阶段-4-分析)
  - [protocol/：五条军规逐条落（对应阶段 5） [应用]](README.md#protocol五条军规逐条落对应阶段-5-应用)
  - [firmware/：五条纪律的代码落点（对应阶段 3 / 6） [应用]](README.md#firmware五条纪律的代码落点对应阶段-3--6-应用)

## 环境

```bash
pip install -r requirements.txt   # numpy / matplotlib / pytest
```

- Python 3.10+；C 代码需要任意 C99 编译器（gcc/clang/MSVC 均可）。CI 只自动跑 gcc；clang 与 MSVC 是按标准 C99 写的、未用编译器扩展，但没有自动验证——在你的编译器上报错请开 Issue。
- Windows：可用 `py -3` 代替 `python3`；固件测试产物为 `test_bms.exe`，直接运行即可。
- 全部测试在 CI 运行（`.github/workflows/tests.yml`）。
- 实测 CSV 随仓库提供，日常回放不联网；只有从原始 MATLAB 归档重新导出时需要额外安装 scipy。PC 综合实验由协议测试门一并执行。

## 设计约定（与教程全文一致）

- **电流符号：充电为正**（I > 0 充、I < 0 放）；
- SOC 在代码里用 `[0, 1]`，显示时 ×100；
- 所有阈值均为**示例值**——真实产品以电芯 datasheet 与保护 IC 料号为准；
- 这些代码是**教学骨架**：刻意保持短小、每条纪律可直接对应教程章节。
  量产级参考请研究 [LibreSolar](https://github.com/LibreSolar/bms-firmware)
  与 [foxBMS](https://github.com/foxBMS/foxbms-2)。

## 给自学者的使用建议

1. **先跑后读**：跑通 `compare.py --plot`，再带着"为什么 EKF 贴得住"的问题去读 `estimators.py`；
2. **动手改**：把电流零漂改大、把 EKF 的 R 调大，看曲线怎么变——教程 §4.5 的调参直觉就是这么来的；
3. **逆向练习**：`protocol/frames.py` 的帧格式是教学抽象；学完去对照 [esphome-jk-bms](https://github.com/syssi/esphome-jk-bms) 源码读真实协议；
4. **扩展状态机**：给 `firmware/bms.c` 加"预充"状态（教程 6.1.2）或充电过流保护，并把场景测试补上。

## 代码走读（带行号） [应用]

> **先读/后读**：soc 走读的主层是 [分析]；protocol 和 firmware 是 [应用]。三节都是先跑通再对着行号读。

先按上节"先跑后读"跑通，再对照下面的行号读——每个走读点都标了它对应的教程小节。

> **原理**　先跑通对应示例，再按行号看校正、组帧和断口是在哪一行发生的。
> **证据**　三条走读分别落到 `code/soc`、`code/protocol`、`code/firmware` 的测试，CI 会跑。结构参考 [foxBMS 2](https://github.com/foxBMS/foxbms-2)（英文，可选）。
> **延伸阅读**　[foxBMS 2](https://github.com/foxBMS/foxbms-2)（英文，量产结构参考，可选）

### soc/：三种估算器的分歧只有"怎么校正"（对应阶段 4） [分析]

> **先读/后读**：先跑 `compare.py` 是 [应用]。读三条曲线为什么分叉是 [分析]，这一节的主层。

- **CoulombOnly**（`estimators.py:17-30`）：核心就是 `:28` 一行 `soc += I·dt/Q`；`:29` 的 clip 是它唯一的自我保护。零漂和容量误差**没有任何修正通道**——它必然漂移，这不是实现缺陷而是方案属性（§4.2）。
- **CoulombWithResets**（`:33-83`）：同一行积分（`:52`），加两个校准锚点：满充复位（`:54-57`：高压 + 电流衰减到截止值 → 必然满电）与静置 OCV 复位（`:59-68`）。静置计时是**双向去抖**：普通超限采样让计时 `-4·dt` 回退，避免传感器噪声每次都清零；但**满充校准明确说明仍在充电**，必须清掉旧静置计时（`:57`），撤流后重新等够窗口，不能一拍就用 OCV 覆盖满充结果。`:74-83` 用二分查找顶替真实产品的 OCV 查表插值。
- **EKFEstimator**（`estimators.py:88`）：状态 `[SOC, U_rc]`。`step()` 中先预测状态与协方差，再用 `C = [dOCV/dSOC, 1]` 线性化观测方程，依次算残差、增益和修正。默认仍用合成 OCV 曲线；真实数据可注入标定曲线和导数，并用 `voltage_current_a` 区分积分区间平均电流与电压观测瞬间的电流。默认调用方式与原合成实验兼容。
- 跑 `compare.py --plot` 时对照看：三条曲线分叉的位置，就是上面三段代码的差异点。`compare.run()` 的第 k 项统一取**第 k 步结束时**的真值与估计值，绘图时刻是 `(k+1)·DT_S`；先记真值再推进模型会错开一拍，把工况变化混进 RMSE。

- **hppc_demo.py**（§4.4 / §4.10 任务 2 合成演示）：`identify_one`（`hppc_demo.py:132`）用脉冲前后均值差算 R0；`fit_relaxation`（`:105`）网格扫 τ，二维最小二乘拟合 K 与 A；再修正短脉冲尚未达到稳态的幅值。默认网格与合成结果保持兼容，真实数据可传 `tau_grid` 扩展搜索范围。窗长不足和固定渐近线带来的辨识偏差见该函数说明，那里报告的是合成实验。
- **sop_demo.py**（§4.7 合成演示）：`hppc_current`（`sop_demo.py:60`）闭式除法只看此刻；`bisect_current`（`:81`）每猜一个电流就把 `TheveninCell` 前向仿真 ΔT 秒，电压、SOC 墙、电流帽三约束取最紧。表驱动打印 6 个 SOC 点 × 3 档时间窗，六项自验收当断言。单节放电侧；N 串取最小与充电侧留白。
- **real_data.py**：`load_data` 校验随库实测数据；`calibrate` 只读标定分组；`evaluate` 在后续随机负载上比较原教学模型与标定模型；`run` 导出计算参考、误差和电压残差。源记录与重建方法见 [真实数据实验](../docs/SOC真实数据专题.md)。
- **thermal_demo.py**（热五天合成演示，Notes07 导读配套）：`net_power_w` 把四项生热教成欧姆火 + 可逆熵热两项，`steady_temp_c` 给恒流稳态解析解，`sine_response` 量正弦生热的温度低通（幅值缩 1/√(1+(ωτ)²)、滞后 arctan(ωτ)——生热纹波在 2ω）。六项自验收当断言；R_th/C_th/熵斜率全为合成示例。`code/firmware/` 依然没有热模型——这里教的是"温度从哪儿来"，不是产品热管理。

> **原理**　纯积分没有校正通道，零漂会一直累加。复位靠满充和静置锚，EKF 靠电压残差，分叉只来自校正方式。
> **证据**　三种估算器的差别在校正通道。讲义 [Plett ECE5720](http://mocha-java.uccs.edu/ECE5720/index.html)（英文，可选）与 [Notes03 中文导读](../docs/ece5720-notes03-中文导读.md)。测试在 `code/soc`。
> **延伸阅读**　[foxBMS 2](https://github.com/foxBMS/foxbms-2)（英文，量产结构参考，可选）

### protocol/：五条军规逐条落（对应阶段 5） [应用]

- 帧格式抽象在文件头 docstring（`frames.py:8-9`）；组帧 `Frame.to_bytes`（`:34-46`）。
- **军规 1 逐字节状态机**：`feed()`（`:78`）收一个字节，`_extract_frame()`（`:83`）按「找帧头 → 收元信息 → 等数据和 CRC → 校验」推进；状态由缓冲内容与长度决定，待收缓冲小于最大帧长 70 字节。
- **军规 2 坏帧计数不静默**：`:72-76` 五个统计字段；长度非法 `:106`、CRC 错 `:118` 各自计数，明确超时或结束后的残帧计入 `frames_incomplete`，丢弃无效前缀的次数计入 `resyncs`。
- **军规 3 垃圾前缀重同步**：`:85-96` 保留末尾孤立的 0xAA；长度或 CRC 失败时只排除当前坏帧头，余下字节重新扫描。因此缺 CRC 的旧帧不会吞掉下一帧的 AA；已经误收进载荷的好帧也能找回。合法帧中的 AA 55，甚至完整的内嵌好帧，都按载荷保留。
- **军规 4 单字节喂入**：`feed` 每次至多返回一帧；长度被破坏但仍 ≤64 时，仅凭字节不能断言外层帧已坏。串口上层确认**帧间超时**或流结束后应调用 `flush()`（`:127`），处理它返回的所有帧；普通 `read()` 分块不能当作超时。`parse_stream()` 适用于已结束的整段数据，自动做末尾 flush。
- **军规 5 物理量换算**：`cell_voltage_mv`（`:49-58`），raw16 大端 ×1mV。
- 易漏点 `:109`：总帧长是 `6 + len`，len=0 仍有帧头、元信息与 CRC，数据切片为空。

> **原理**　字节流没有帧界。状态机靠帧头、长度和 CRC 找回边界，坏帧要计数，不能静默丢掉。
> **证据**　帧界和 CRC 的回归在 `code/protocol/tests/`。真实帧对照 [esphome-jk-bms](https://github.com/syssi/esphome-jk-bms)（英文，可选）。
> **延伸阅读**　[foxBMS 2](https://github.com/foxBMS/foxbms-2)（英文，量产结构参考，可选）

### firmware/：五条纪律的代码落点（对应阶段 3 / 6） [应用]

- **断口方向**：`enter_fault`（`bms.c:41`）依据 `fault_mask` 合并限制：OVP 禁充、UVP/OCD 禁放、SCD/OT 双断；OVP 与 UVP 同时存在也必须双断，不能为恢复其中一项而放任另一项。`active_fault` 仅按 SCD > OT > OVP > UVP > OCD 选显示主因；第一现场仍是上电以来首次故障（`:49-50`），后续升级不覆盖。
- **保护最先评估**：`bms_tick`（`:103`）每拍都调用 `eval_protections`，**故障态也不例外**。各项保护全部评估后再合并断口，不能命中 OVP 就跳过 OT。只有全部故障都恢复才回待机，下拍重新决策合闸。
- **去抖**：`debounced`（`:58`）对 OVP/UVP/OCD 独立计数，正常输入清零，连续超限时饱和在 255；配 0 表示首次超限即动作，不会因 `0 ≥ 0` 把正常输入误判。旧故障恢复时不清其他项尚在积累的计数。
- **恢复条件**：`update_fault`（`:68`）只更新对应故障位，触发与释放之间保留原状态；`eval_protections`（`:74`）逐项给出回差、充电器条件和短路解锁窗口。SCD 只有电流进入 `(-100, +100)mA` 才解锁，充电电流不能冒充已卸载；电流先扩为 int64 再取负，避免 INT32_MIN 溢出。
- **满充校准边界**：`ST_CHARGE`（`:147`）先检查电流方向与充电器状态，再判断均衡和满充。必须充电器在场且电流 `> 0`：负载把净电流拉反、拔枪后的残余正电流都不能触发满充校准；电流归零时等待恢复，不进入均衡。
- **均衡**：`ST_BALANCE`（`:167`）每拍先关旧输出，再确认充电器在场、净电流为正、最高串不低于 `balance_start_mv`，才给高于最低串 delta 的串开放电开关。电流反向立即转放电，拔枪回待机；即使同拍压差收敛，也不能抢先转回充电。零电流或电压跌破门槛同拍停均衡，等待重新满足入口条件。
- **可移植性细节**：`bms_state_name`（`:209`）和 `bms_fault_name`（`:222`）用无符号比较保证越界枚举落到 `"?"`，避免依赖 GCC/MSVC 对枚举底层类型的不同选择。
- **快照回放**：`hil_replay.c` 只调用 `bms_tick`。过充去抖满之前状态可以已经是均衡；第三拍冻结过充；随后的短路只改当前显示。0 mV 会被记成欠压，因为骨架没有开线标志。

> **原理**　每一拍先把全部保护评估完，再按故障掩码合并充电和放电断口。故障态也不能跳过评估。
> **证据**　保护评估顺序的回归在 `code/firmware` 的 `test_bms`。结构参考 [LibreSolar 固件](https://github.com/LibreSolar/bms-firmware)（英文，可选）与 [foxBMS 2](https://github.com/foxBMS/foxbms-2)（英文，可选）。
> **延伸阅读**　[foxBMS 2](https://github.com/foxBMS/foxbms-2)（英文，量产结构参考，可选）
