---
search: false
---

# P0.9：来源采用、责任与补证门

本表将[已完成取样](../2026-11-08-bms-open-source-research.md)分配到后续实现。日期2026-11-08；版本/许可/实际读取文件以[快照](../2026-11-08-bms-open-source-snapshot.json)为准。状态`read`只表示静态审读，`contract_applied`表示已用于规则/纠错，均不等于上游复现或独立硬件验证。

角色为后续执行者的文件责任，不假设已有真人专家。尚未取得的手册、数据和独立评审必须保留缺口。每项退出G02前把具体源路径/页节、版本、条件与断言ID记入单元任务卡；当前P0不创建虚假的产品登记或实验结果。

| 来源 | 当前采用状态 | 对应单元 / 实验 | 责任角色 | 后续应读/应交的具体内容 | 截止门 |
|---|---|---|---|---|---|
| OS01 PyBaMM | read；层级与事件边界进入合同；**reproduced-locally（2026-11-18，E12 轻量基准）**：pybamm 26.10.1.1 固定于 .venv-os01，证据 `code/research-closure/evidence/os01-closure.json`——SPMe 1C 至 2.5V 实解、事件终止、能量积分 17.2747Wh、x_n 5/20 网格对照 energy_diff 2.75mWh / v_end 差 1e-13；`compare_lithium_ion` 符号在 26.10.1.1 不存在记 unavailable。**2026-11-19 独立积分器锚点补上**（`os01_independent_reference.py`，证据 `evidence/os01-independent-reference.json`）：同一离散 SPMe RHS（Simulation 两段式管线 + EvaluatorPython，102 维）由 **scipy LSODA**（非 PyBaMM 求解器；短窗实测 RK45 45,399 步/26 s、Radau 34 步、LSODA 127 步——刚度主导选型）积分，与显式 IDAKLU(rtol=1e-9/atol=1e-11，与独立侧对称) 参考在 **751** 个参考时刻状态向量交叉核验 max_rel=**1.18e-8**、rel_l2=4.6e-10（纯相对判据 1e-4 通过，余量 ~8,400×；dense-output 采样无插值误差；nfev=6948，输出区间 750）。鉴别实验：Simulation 默认求解路径作参考时 max_rel=1.9e-4 且对积分器紧容差不敏感——差异在参考侧容差/输出插值，已换显式求解器。**边界如实**：非完全独立模型锚点——方程/事件独立（降阶单粒子+1RC ODE 与 2.5V dense-output 求根本脚本内定义），OCV 数据经 Chen2020 电极参数转写、R0/R1/C1 由参考前 60 s 辨识（如实登记）；**2026-11-19 独立模型锚点已补**（`os01_independent_model.py`，证据 `evidence/os01-independent-model.json`，all_pass）：窗口 Q=5.099 Ah 由 2.5V 下截止静置端标量根封闭（不含参考 t_end，纯预测），R0/R1/C1 前 60 s 辨识（RMSE 0.23 mV），预测全程放电 t_end/容量/能量相对偏差 **2.0%/2.0%/2.4%**（≤3% 保真度门）；**V(t) 轨迹核对补入**（advisory 防端点通过漏检；等时 1 s 物理网格——参考自适应输出点非均匀，751 点中 713 个落前半程，直接平均会稀释后段）：主窗 DOD 0–0.84（边界由 OCV 锚点梯度 dOCV/dz>2×中段中位数定，模型输入非误差数据）RMSE=**26.1 mV** ≤30 mV 门，holdout(t>60 s)=26.4 mV；膝区 DOD 0.84–1.0 RMSE=104 mV 单列不判（1RC ECM 膝区不保真，登记局限）；全程等时 RMSE=48.0 mV 与 v_max=254 mV（位于 t_end_ref，模型膝点滞后 72 s 的真实同刻电压预测误差）**如实保留不删**——初版 150 mV 平峰值门 FAILED 结果存于 evidence；途中否决：标称容量硬套窗口（电极容量 5.83/8.73 Ah 不一致暴露）、静置 2.5V 端 z 方向错置（非物理 4.6V 中窗）、正极计量方向写反（advisory 判符号错误属实，放电为正极嵌锂 sp↑） | D01/D02/D17/D18/D27，R01；E10–12 | 模型研究 | compare_lithium_ion、SPMe子模型、rate_capability对应依赖/参数/事件；冻结可运行版本，交网格/容差/独立参考和能量积分对照 | P6 G02–G05；E12轻量基准可P4先做 |
| OS02 PyBOP | read；拟合与验证分开进入合同；**2026-11-18 S2 标准库基准完成并定案为验收基线**（`code/research-closure/os02_ecm_benchmark.py`，证据 `evidence/os02-ecm-benchmark.json`，确定性种子可复跑）：合成 2RC 多脉冲，OCV 初值两组对照误差 ≤6e-4 V；**同时刻重复观测**对 SSE 为严格权重缩放——代价恰×5、argmin 逐位一致（drift=0.0，已按时间索引语义验证，非拉长轨迹）；NM+边界投影无越界（修复了回存未裁剪点的泄漏）；代价追踪 400 迭代单调非增；多初值实测**不**同代价（seed1 陷 tau1≈0 退化支路，seed2 近真值 60/600 s）——2RC 六参数可辨识性弱已实证；独立留出脉冲组 RMSE 1.26 mV（噪声底 0.1 mV）通过。PyBOP 26.10 加性探针（`os02_pybop_probe.py`）：**Thevenin/ECM 模型已移除**，固定 notebook(316b28d) 流程不可复现——探针降级为环境事实登记，不门控验收基线。**Mendeley 原数据许可已核（2026-11-19，pending 关闭）**：数据集标识经 2026-11-08 研究快照与 PyBOP notebook 双向确认 = Samsung INR21700 30T 3Ah Li-ion Battery Data（Kollmeyer & Skells 2020，Mendeley Data V1，DOI 10.17632/9xyvy2njj3.1；现存 V2/2023 更新，notebook 引 V1）；许可经版本专属页面 JSON-LD 双向确认：V1 页（`/1`，`"version":1`）与 V2 页（`/2`，`"version":2`）均载 `"license":{"url":"creativecommons.org/licenses/by/4.0","text":"CC BY 4.0"}`——许可声明覆盖快照锁定的 V1；允许再利用含商用，须署名并注明变更；**无 NC 限制**（检索中 ResearchGate 片段所示 CC BY-NC 系该论文自身许可，已排除；顶层 public-api 无版本尾缀时解析为 V2，已甄别）| D11/D13–16，R02；E02 | 辨识/估计 | multipulse notebook的OCV初值/时间去重/2RC边界；追代价和优化结果、独立留出 | P4 G02；S2标准库基准先做，不依赖安装该库 |
| OS03 liionpack | read；几何变化不能充老化真值；**2026-11-18 S3 轻量电路基准完成**（`code/research-closure/os03_circuit_benchmark.py`，证据 `evidence/os03-circuit-benchmark.json`，不依赖 liionpack）：可手算 2p1s/1p2s 电阻网络 numpy 节点分析——求解器对称特例对手算（<1e-12）、KCL 五节点残差 <1e-13、KVL 外环 <1e-9、支路电流和=负载、弱支路（cell2：低 OCV+高内阻）分流更少且端电压最低、**首次约束事件=最弱单节**（V_min=3.0V 阈值电流 34.2A vs 强节 35.7A，二分 60 位）；1p2s 串联支路电流处处相等、端电压对手算。途中修复：Norton 源在串联中点缺回流（1p2s 电压虚高至 12V）、r_bus 并地泄流误接（改 n_bus_hi→n_bus_mid→n_out 串联路径）、KVL 残差漏 −V_out、np.bool_ 不入 JSON | D03/D10/D16/D17/D24/D28，R03；E04 | 整包/热模型 | setup_circuit节点网络、两类拓扑、输入数组映射；冻结兼容依赖；逐节KCL/KVL与最弱项证据 | P3轻量电路G03；P6复杂模型G02–G05 |
| OS04 LibreSolar固件 | read；回填≠回读写入合同；**2026-11-18 S4 配置链路基准完成**（`code/research-closure/os04_bq_config_benchmark.py`，证据 `evidence/os04-bq-config-benchmark.json`，独立实现 14/14 全过）：量化往返 ≤step/2；限幅静默（20V 写入返回 success 但回填被改 12.903V）；**核心反例：NACK 重试后 success=True 而 committed=False，寄存器仍旧值、回填≠回读**；ready 超时耗尽返回失败；长度/校验和注入被拒；重试常数不作 WCET 声明 | D04/D05/D08/D10/D20/D26；E01/E05 | AFE/固件 | BQ配置编码、写入返回值、interface等待/校验；将模拟寄存器测试和真实回读分开；冻结west依赖SHA | P3 G02–G05；S1器件延时需先补SRC02 |
| OS05 LibreSolar C1 | read；硬件/固件版本分开 | D05–D07/D24–D26；E01/E05 | PCB/功率 | 导出/目视审查具体修订图纸、逐网连接、分流测点；对应BOM和制造条件；旧v0.3报告只能用于其DUT | P3 G02–G03，SRC02/03 |
| OS06 VESC | read；占位、位图、注释代码进入反例；**2026-11-18 S6 CAN/PEC/权限链基准完成**（`code/research-closure/os06_can_pec_benchmark.py`，证据 `evidence/os06-can-pec-benchmark.json`，独立实现不拷 GPL）：CAN 扩展帧位图打包/解包与上层有效性链分离（非法节点号打包可往返但被链拒绝）；CRC-15 PEC 检出单比特/双比特注入，**PEC 关闭时同一注入静默通过（注释开线反例实证）**；越权命令在授权段被拒并留审计日志、降额标志下同命令被钳制执行 | D05/D10/D15/D18–D21/D24；E05/E07 | 通信/均衡 | comm_can发送/接收位图与上层有效性链；bms_if权限/降额；LTC6813静默/PEC及被注释开线；独立实现反例而非拷GPL代码 | P3/P5对应G02–G05 |
| OS07 foxBMS | read；命令/反馈身份进入纠偏合同；**2026-11-18 S7 接触器 FSM 基准完成**（`code/research-closure/os07_contactor_fsm_benchmark.py`，证据 `evidence/os07-contactor-fsm-benchmark.json`，**11/11 全过**）：四态 FSM（OFF/PRECHARGE/ON/FAULT）+ 独立反馈 + 去抖 10ms + 反馈超时 50ms（均为教学参数，非 foxBMS 实测配置）；正常闭合时序、反馈粘连检出（cmd OFF 后恒 ON → FAULT 并撤许可）、去抖窗滤除 5ms 毛刺/采信 12ms 毛刺；**清旗/复位/重新许可三分**：清旗只清诊断、复位回 OFF 不给许可、重新许可只恢复许可位——三操作独立可测；**命令≠反馈**：无独立反馈源时物理粘连不可证伪 | D08/D20/D22–D26，R04；E03/E07 | 高压/安全 | 从registry/SPS/反馈/DIAG回调继续追完整状态机和去抖配置/测试；区分清旗、复位、重新许可 | P1/S3 G02核心语义；P5/P6完整链 |
| OS08 BLAST | read；条件域/外推限制进入合同；**2026-11-18 S8 老化模型基准完成**（`code/research-closure/os08_aging_model_benchmark.py`，证据 `evidence/os08-aging-model-benchmark.json`，10/10 全过，参数显式标注 TEACHING-SYNTHETIC）：日历项随 T/SOC/√t 单调、循环项随吞吐量线性、两分量可分离回归（参数复原误差 ≤0.19%，Ea/k_soc 等复原）；窗内外推显式标记 `extrapolation=true` 且**不给精度断言**；固定种子两次运行逐位一致。**R03 实证仍 pending**——合成基准只验算法语义，不验标定，无外部数据不得关闭 | D15–D18/D27，R03；E08 | 老化 | 250Ah LFP原论文/数据及条件组合、日历/循环分量补偿；Kokam快算另建模型身份；核独立数据可用性 | P4/P6 G02；无外部数据不得关闭R03实证 |
| OS09 Battery Data Toolkit | read；充放/单位/元数据边界进入合同；**2026-11-18 S9 数据 schema 基准完成**（`code/research-closure/os09_data_schema_benchmark.py`，证据 `evidence/os09-data-schema-benchmark.json`，全过）：必填字段缺失 fail-closed 拒收并列缺项；启发式三分支（恒正电流/容量-符号矛盾仅警告，时间戳非严格递增拒收）——**启发式≠判定**实证；显式转换（声明 discharge_negative）清除 (a) 类警告且与警告路径分离、带来源记录；CycleLevelData 聚合与手算残差 <1e-9（3 段吞吐/倍率/能量） | B05/D12/D21/D26；E09/E12 | 数据 | RawData与CycleLevelData单位、符号警告/不足数据分支；将启发式警告与显式转换分开；定义BMS必填源字段 | P1.0/P4/P5 G02–G05 |
| DATA01 NASA RW3 | 元数据复查；既有本地谱系审核；**2026-11-18 谱系审计本机核验**（证据 `code/research-closure/evidence/data01-lineage.json`：metadata 必填字段齐、25461 行零解析失败、充正放零违例、(series,source_step) 组 source_sample 全连续、CSV sha256 本地重算；上游 ZIP 归档摘要未重核记未核） | B05/D11–D14/D21；E06/E09 | 数据/估计 | 本地metadata与CSV原始step/行，OCV/capacity/pulse/validation隔离；重跑证据保存reference_soc与预测，不命名独立真值 | P0.7；后续P4/P5留出任务 |
| EDU01 UCCS/Plett | 本地导读已读；原站访问待复核 | B02/B03/D02/D11–D14，R02 | 数学/估计 | 核合法取得的讲义实际版本/页节，引用公式及其假设；原站恢复前标访问状态，不重发讲义 | 对应单元G02；可用其他可核原理源替代但记录理由 |
| CASE01 PyBaMM5072/5205 | 原问题/评论/补丁已读；**2026-11-18 解析基准双版本×双求解器对照完成**（`code/research-closure/case01_event_baseline.py`，证据 `evidence/case01-baseline-{25.6.0,26.10.1.1}-{casadi,idaklu}.json` 四份 + `case01-tight-tolerance-probe.json`）：模型树完整性探针确认重复 Heaviside 节点如实进入收集路径；修复版双求解器五例全过；修复前默认容差下——Casadi 重复例偏差 1.1e-6（刚过 1e-6 容差）、IDAKLU 区间内部切换例偏差 3.1e-4；**紧容差（rtol=atol≤1e-6）探针显示修复前 IDAKLU 收敛至 8e-10——差异归于求解器容差路径，不能归因 PR #5205 不连续缺陷，原故障在简化解析模型上未复现**。判定：**未复现（修复语义核验通过、缺陷未触达）**；原 MWE 的非物理不连续未重建（自定义 Yang/Basic DFN 半电池超出本地快照材料） | B02/D02/D18/D27，R01；E11 | 数值模型 | 固定修复提交及必要前版本，先建解析ODE端点/左右侧/重复事件基准；明确是否真的重现原MWE | P6 G04–G05 |

## 专项缺口与阻塞范围

| 缺口 | 负责人 | 所需证据与来源任务 | 哪些结论被阻塞 / 可独立推进 |
|---|---|---|---|
| SRC01 电芯 | 物理/电芯 | 选择一个具体电芯料号、手册修订和OCV/温度数据；将正常端点、保护阈值、绝对限值分开 | 阻塞产品限值；可做明示教学参数的电路/电量推导 |
| SRC02 AFE/PCB | 测量/PCB | 对OS04/05逐网查板型，实际读取AFE手册/勘误的建立、扫描、诊断及寄存器章节，引用页节 | 阻塞真实精度/延迟/EMC声明；S1独立理想RC/滤波算例可推进 |
| SRC03 功率 | 功率/高压 | 确定候选MOS/驱动/接触器/电阻/熔断器/IMD料号，逐条登记条件曲线、修订、回路假设和器件限制 | 阻塞器件选型签字和高压许可；S3理想能量/失败逻辑可推进 |
| SRC04 热/充电 | 热/充电 | 收集热容/换热/熵项标定及独立温度测点；充电许可回电芯手册，冻结温度/倍率/工况 | 阻塞温度精度/SOP/快充安全外推；合成热基准可推进 |
| SRC05 协议/刷写 | 通信/固件 | 继续审本仓实现；候选Zephyr/MCUboot/python-can/cantools/python-udsoncan中只选相关模块，固定SHA与许可再读实现/失败路径 | 阻塞端到端安全/刷写恢复结论；已有PC解析和会话示范可按边界维护 |
| SRC06 系统/生产 | 系统安全/交付 | 先确定应用和标准适用性，再读合法取得的具体版本/条款；需求/测试/配置链，EOL与在役原始记录 | 阻塞标准符合性、诊断覆盖、产品能力宣称；可交完整论证结构和缺证据表 |
| SRC07 研究/真人/实物 | 老化/数据牵头；读者/硬件各自责任 | 原数据许可、跨电芯/温度验证组；W5读者背景/作答/原话；7项专项镜头的对象和授权 | 阻塞真实泛化、真人阅读效果和专项实拍验收；软件/材料工作仍可推进 |

本表每项均有任务归属和退出门，P0.9可以作为“已分配”完成；`read`和`pending`不会因此改成`reproduced/verified`。后续实际采用新源时补具体版本和文件，停止使用旧结论时保留撤回原因，不以来源数量增加代替证据缺口关闭。


## 2026-11-26 D11 独立预测专项

本节新增证据身份，不改变 OS02 历史基准或 NASA 数据谱系结论。

- PyBOP 固定 `5b615fdac40a91761d224db7f48b887845a32d15`，BSD-3-Clause，已读 `examples/notebooks/battery_parameterisation/ecm_multipulse_identification.ipynb` 与 `lgm50_pulse_validation.ipynb`。采用训练后冻结参数、在第二数据集预测的流程；验证笔记还将初始SOC改为 `0.8-0.0075`，不能宣传成完全盲测。未执行完整上游笔记。
- SciPy 固定 `e4e854eaa8f18d807cd3496028e257e36caa93cc`，BSD-3-Clause；`d11_joint_hppc.py --scipy` 直接复用 `scipy.optimize.least_squares`，与网格同一训练集、同一SSE和物理边界。局部运行通过，另有62.3s/23mΩ合成数据的密网格对照测试。
- Boyd & Vandenberghe 作者公开教材 *Introduction to Applied Linear Algebra*，§13.2，印刷261–264页已读，来源 <https://web.stanford.edu/~boyd/vmls/vmls.pdf>。采用训练/验证分离原则，按整脉冲分组；不复制教材图片或段落。
- Plett BMS1 官网配套页已读取，只核实课程与工具箱入口，未读取商业书正文。Z-Library 对 Plett/Ljung 两次检索均返回 Access denied，未取得正文，不能计为书籍证据。
- E02c/D11 报告升级 schema 2：原“联合留出0mV”撤回，其数据曾参与拟合。新固定带噪场景训练0.101542mV、独立预测0.104042mV；只改验证τ为70s后0.552790mV，训练参数不变。全部为合成实验，不改变真实电芯精度证据状态。
