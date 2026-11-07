---
search: false
---

# BMS v3：开源资源审读、实验合同与证据缺口

日期：2026-11-08。用途：给[总SPEC](../../BMS系统教材SPEC-v3.md)和[P0–P8执行计划](2026-11-08-bms-depth-rebuild.md)提供实际代码依据，使每一环有输入、作品和拒收条件。本轮完成的是**指定版本的源码/资料审读与实验设计**，没有安装或运行这些上游项目，没有复现其性能、验证实物或完成新版教材。

用户指定的Claude项目主要贡献教学和出版组织方法，见[单独审计](2026-11-08-claude-reference-audit.md)；本文件补充BMS专业证据。完整SHA、实际读取路径、许可与范围存于[开源取样快照](2026-11-08-bms-open-source-snapshot.json)。快照记录文件身份和观察，不收录上游整篇源码、插图或Notebook保存的图片。

## 1. 选择原则与已读取资源

选择资源围绕电芯模型、参数辨识、整包不一致、真实硬件/固件、系统反馈、老化和数据链。每个项目实际读README、许可及具体实现/例子；不是按热度罗列仓库。表中短SHA仅为阅读方便，永久文件链接与快照使用完整SHA。

| ID | 资源/固定版本 | 实际关注点 | 已核对的许可 | 进入单元 |
|---|---|---|---|---|
| OS01 | [PyBaMM](https://github.com/pybamm-team/PyBaMM/tree/7ad734e74b72b5c55a821bf0696921125a201138)，`7ad734e74b72` | SPM/SPMe/DFN对照、子模型、事件和倍率能量 | 软件BSD-3-Clause，外部参数/论文/数据另核 | D01/D02/D17/D18/D27，R01 |
| OS02 | [PyBOP](https://github.com/pybop-team/PyBOP/tree/316b28d0b456793b1e3cb3cf0c5c6d8fc65347b3)，`316b28d0b456` | 多脉冲2RC、代价/约束/优化与可辨识性 | BSD-3-Clause；示例外部数据许可未核完 | D11/D13–D16，R02 |
| OS03 | [liionpack](https://github.com/pybamm-team/liionpack/tree/02365eb2f2ae4ad413e80fcd0ee8079897159a37)，`02365eb2f2ae` | 逐电芯状态、串并拓扑、连接电阻、几何差异 | MIT；已进入维护模式，兼容环境另冻 | D03/D10/D15–D17/D24/D28，R03 |
| OS04 | [LibreSolar固件](https://github.com/LibreSolar/bms-firmware/tree/779d20199bff2666e01371ce2f562dcda4d6bda3)，`779d20199bff` | AFE、保护、均衡、硬件抽象与配置 | Apache-2.0；第三方组件仍分别登记 | D04/D05/D08/D10/D19/D20/D24 |
| OS05 | [LibreSolar bms-c1](https://github.com/LibreSolar/bms-c1/tree/0ca09706f49906bdc73f6ccf99635de349d47474)，`0ca09706f499` | 硬件源文件、功率/测量接口与设计约束 | 硬件CERN-OHL-W-2.0；文档CC-BY-SA-4.0 | D03/D05–D07/D10/D24/D26 |
| OS06 | [VESC BMS固件](https://github.com/vedderb/vesc_bms_fw/tree/591d57dadb14d4392d4cf859a5187264a8aafed8)，`591d57dadb14` | 净电流/充电/均衡、通信与保护责任；SOH占位 | 根GPLv3；所读实现头部GPL-3.0-or-later，第三方另核 | D07–D10/D15/D18–D20/D24 |
| OS07 | [foxBMS 2](https://github.com/foxBMS/foxbms-2/tree/73dbde670f7e9ec59afc33855bcf27576bd874de)，`73dbde670f7e` | 接触器反馈来源、按串诊断、清旗与恢复 | 软件BSD-3-Clause；硬件/文档CC-BY-4.0 | D08/D20/D22–D26，R04 |
| OS08 | [BLAST-Lite](https://github.com/NatLabRockies/BLAST-Lite/tree/991591726c07c74b5d8131e9090fee190d2e5d57)，`991591726c07` | 容量老化、条件有效域、长期外推、控制假设 | BSD-3-Clause；原论文/老化数据另核 | D15–D18/D21/D26/D27，R03 |
| OS09 | [Battery Data Toolkit](https://github.com/ROVI-org/battery-data-toolkit/tree/19961e6bbb2d0cfe0bff9c129144fcf8f3dd3be6)，`19961e6bbb2d` | 列schema、原始身份、单位、符号启发式检查 | Apache-2.0；可读数据集各有各的许可 | B05、D12/D21/D26 |

GitHub对OS05/OS07返回的许可标识为`NOASSERTION`，实际许可证文件已澄清资产分工，不能把它写成“无许可”。OS08的原`NREL/BLAST-Lite`地址已实查重定向到`NatLabRockies/BLAST-Lite`。不直接复制这些项目的图、代码或教学表达；未来确需复用时按具体资产完成署名、许可与变更记录。

## 2. 从具体代码中采用什么

### OS01：模型的名字不能代替适用范围

实读[模型对照例](https://github.com/pybamm-team/PyBaMM/blob/7ad734e74b72b5c55a821bf0696921125a201138/examples/scripts/compare_lithium_ion.py)、[SPMe实现](https://github.com/pybamm-team/PyBaMM/blob/7ad734e74b72b5c55a821bf0696921125a201138/packages/pybamm/src/pybamm/models/full_battery_models/lithium_ion/spme.py)和[倍率例](https://github.com/pybamm-team/PyBaMM/blob/7ad734e74b72b5c55a821bf0696921125a201138/examples/scripts/rate_capability.py)。SPMe的电解液/电势子模型提供从“忽略了什么物理过程”进入模型层级的方法；对照脚本本身没有完整冻结参数、网格与独立实测。

采用到E10的模型对照卡和E12能量审读：同一物理任务冻结初值、温度、参数集、工况、事件和容差；报告模型差异及运行成本。有实测才能报告验证误差。倍率例中的普通样本均值电压乘容量不能直接成为非均匀采样能量的标准答案；以`∫VI dt/3600`作独立核对。示例的3.2 V与倍率是其算例条件，不是通用电芯限值。

### OS02：拟合流程明确，独立验证还要补上

实读[多脉冲2RC笔记本](https://github.com/pybop-team/PyBOP/blob/316b28d0b456793b1e3cb3cf0c5c6d8fc65347b3/examples/notebooks/battery_parameterisation/ecm_multipulse_identification.ipynb)的全部正文/代码单元。它把`simulator → cost → problem → optimiser → result`分开，给出参数边界、随机种子和优化停止条件，适合D11逐步连接数学与程序。

也要教读者审查前提：默认OCV、以首个电压作初始OCV、时间戳去重和事件删除都需要理由；同数据拟合图不构成独立验证，后续驱动预测没有展示独立实测误差。本书E02先完成可手算1RC，再扩2RC；报告多初值、边界命中、时间常数交换等价、留出预测与温度参数证据。v25.10前后API发生重构，后续环境不得混用旧教程。

### OS03：整包平均值掩盖了哪些单节

实读[不同初始SOC](https://github.com/pybamm-team/liionpack/blob/02365eb2f2ae4ad413e80fcd0ee8079897159a37/examples/different_initial_soc.py)、[mixed_capacity](https://github.com/pybamm-team/liionpack/blob/02365eb2f2ae4ad413e80fcd0ee8079897159a37/examples/mixed_capacity.py)和[网络构造中的setup_circuit](https://github.com/pybamm-team/liionpack/blob/02365eb2f2ae4ad413e80fcd0ee8079897159a37/liionpack/netlist_utils.py)。后者区分电芯内阻、连接电阻、母排/端子电阻与两类串并拓扑。

E04从可手算2p1s电阻网络进入，再使用逐电芯输入；检查KCL/KVL、支路电流、最弱单节和首次约束事件。`mixed_capacity`通过电极宽度变化制造差异，不能称为只改变容量的实测老化模型。几何减半、可用容量衰减和内阻增加必须分成不同场景。复杂依赖留在研究环境，基础电路图不强制依赖LaTeX/Lcapy。

### OS04/OS05：把硬件路径、配置和算法连起来

实读固件的[BQ769x2配置](https://github.com/LibreSolar/bms-firmware/blob/779d20199bff2666e01371ce2f562dcda4d6bda3/drivers/bms_ic/bq769x2/bq769x2.c)、[通信接口](https://github.com/LibreSolar/bms-firmware/blob/779d20199bff2666e01371ce2f562dcda4d6bda3/drivers/bms_ic/bq769x2/bq769x2_interface.c)和[模拟寄存器测试](https://github.com/LibreSolar/bms-firmware/blob/779d20199bff2666e01371ce2f562dcda4d6bda3/tests/bms_ic/bq769x2/src/functions.c)相关区段。保护设置经历量化、限幅、写入与配置对象回填；**回填表征值不等于硬件寄存器回读**，也不证明写入成功。通信层的等待/重试、长度和校验和提供异常注入点，不能直接当作实测WCET。

硬件取样包括[BQ76952图纸源结构](https://github.com/LibreSolar/bms-c1/blob/0ca09706f49906bdc73f6ccf99635de349d47474/kicad/bq76952.kicad_sch)、[BOM](https://github.com/LibreSolar/bms-c1/blob/0ca09706f49906bdc73f6ccf99635de349d47474/build/bms-c1_bom.csv)和[v0.3测试记录](https://github.com/LibreSolar/bms-c1/blob/0ca09706f49906bdc73f6ccf99635de349d47474/testing/v0.3/README.md)。BOM中的300 µΩ分流器与固件板型声明吻合，只能说明这一标称值一致，不能证明两个版本兼容或精度达标。旧测试记录的DUT、要求、仪器、方法、结果值得采用，但结果只属于其注明的硬件/固件组合。

E01/E05必须交出“信号从何而来、哪个时间戳、哪个限值、谁请求动作、谁执行、怎样观察”的连续链，分别记录需求值、编码值、表征值、写入状态和独立回读状态；E04的小电路与后续OS05拓扑审读互相核对。固件的`west.yml`仍引用Zephyr可移动分支，复现时须另外冻结依赖提交。开源默认限值或延时不能移作所有化学体系的教材规则。本轮未完成整板连线/netlist或原理图目视审查、PCB布局评价、编译或实测；D06回流/EMC和D07 SOA须SRC02/SRC03补足。

### OS06：一项数值和一个功能不是同一回事

VESC README明确该设计不直接切断用电端，而要求用电端限流，并把短路处理责任交给熔断器。这是特定架构的责任分配，不能移植成通用安全策略。[bms_if.c](https://github.com/vedderb/vesc_bms_fw/blob/591d57dadb14d4392d4cf859a5187264a8aafed8/bms_if.c)的SOH仍是TODO并返回1.0；把该数值显示成100%不能证明估计了健康状态。

[comm_can.c](https://github.com/vedderb/vesc_bms_fw/blob/591d57dadb14d4392d4cf859a5187264a8aafed8/comm_can.c)实际发送/接收的bit2、bit3为`charge_allowed`、`charge_ok`，与旧说明存在漂移；接收时刻、特定值的过期和缓存ID回收有不同语义。[LTC6813驱动](https://github.com/vedderb/vesc_bms_fw/blob/591d57dadb14d4392d4cf859a5187264a8aafed8/drivers/ltc6813.c)有均衡静默采样及PEC校验，开线检查块却被注释；不能因代码里出现诊断名就计作执行覆盖。局部取样不构成对全部上层数据有效性处理的审计。

E07追踪通信请求、远端响应、本地保护与执行权限，加入“远端不配合/通信中断”的任务。D15把SOH占位字段作为审读题：定位其定义、更新来源、数据证据和未实现标记；不能把屏幕上的百分数当实测SOH。完整调用链、硬件分断和短路验证保持待执行。

### OS07：反馈的来源决定它能证明什么

实读[contactor.c](https://github.com/foxBMS/foxbms-2/blob/73dbde670f7e9ec59afc33855bcf27576bd874de/src/app/driver/contactor/contactor.c)、[诊断回调](https://github.com/foxBMS/foxbms-2/blob/73dbde670f7e9ec59afc33855bcf27576bd874de/src/app/engine/diag/cbs/diag_cbs_contactor.c)和[模块说明](https://github.com/foxBMS/foxbms-2/blob/73dbde670f7e9ec59afc33855bcf27576bd874de/docs/software/modules/driver/contactor/contactor.rst)。驱动按配置选无反馈、SPS电流或常开/常闭数字反馈；无反馈分支直接令`feedback=currentSet`。比较后按正/负/预充类型及串号产生诊断事件。回调`NOT_OK`置位、`RESET`清位，`OK`本身不清旗。

E03因此增加`feedback_source / evidence_kind / age / string_id`；命令回填不能通过物理触点验证，SPS电流、辅助触点、主路径电流各证明不同对象。恢复观测、清旗、复位和重新许可分别验。这里只审了驱动和回调，不宣称已追完上层状态机、去抖时间或整个安全论证；OSHWA开源硬件认证也不等于产品安全认证。

### OS08：模型有效域不能用一张最大最小值表代替

实读[250 Ah LFP老化模型](https://github.com/NatLabRockies/BLAST-Lite/blob/991591726c07c74b5d8131e9090fee190d2e5d57/blast/models/lfp_gr_250AhPrismatic_2019.py)、README与[快算例](https://github.com/NatLabRockies/BLAST-Lite/blob/991591726c07c74b5d8131e9090fee190d2e5d57/examples/example_fast_calculations.ipynb)。模型头部给出循环温度10–45℃、DoD 0.8–1，并限定10℃充电只有0.16C；通用字典上限0.65C不能覆盖该低温条件。日历与循环损失分别累加，容量输出为`1−qLoss_t−qLoss_EFC`。

E08要求条件组合的模型卡，区分容量SOH、电阻SOH、日历时间和EFC。原作者指出两损失分量存在补偿，训练总量拟合好不证明各机理正确；README对1–3年数据外推十年以上保留定性边界。快算Notebook使用另一Kokam模型且固定温度/SOC周期，不能与250 Ah LFP的参数/范围混用，不能用来预测变化气候。有效域声明是模型训练范围，不能生成电芯充电许可。

### OS09：数据格式正确仍可能得到错误结论

实读[列schema](https://github.com/ROVI-org/battery-data-toolkit/blob/19961e6bbb2d0cfe0bff9c129144fcf8f3dd3be6/battdat/schemas/column.py)、[符号检查实现](https://github.com/ROVI-org/battery-data-toolkit/blob/19961e6bbb2d0cfe0bff9c129144fcf8f3dd3be6/battdat/consistency/current.py)、[正负例测试](https://github.com/ROVI-org/battery-data-toolkit/blob/19961e6bbb2d0cfe0bff9c129144fcf8f3dd3be6/tests/consistency/test_sign.py)和来源元数据说明。原始电流约定充电为正；原始循环能量字段为J，循环统计的能量字段为Wh。验证字段类型/单调性并不证明量纲转换、校准或物理正确。

`SignConventionChecker`在近恒流窗口用电压随时间的趋势给潜在符号错误警告。E09保留这种“发现可疑输入”的方法，同时设计平坦电压、松弛、静置和数据不足案例；不得根据趋势偷偷翻转电流。本书适配器必须列原始单位/符号、每次变换与输出身份。源文件、转换与派生表可回溯，不能用schema通过替代校准和独立验证。

## 3. 数据、课程与社区证据

**DATA01 / NASA RW3。** 本库已有[数据说明](../../../code/soc/data/nasa_rw3/README.md)与`metadata.json`。本轮实际访问[Zenodo记录15277374 API](https://zenodo.org/api/records/15277374)，确认DOI、CC-BY-4.0、NASA机构作者及对应ZIP的120125009字节/MD5身份；本轮没有重新下载大ZIP。现有归档、MAT、CSV的SHA-256保留在快照，并明确它们来自已有本地元数据，未冒称本轮重算。

固定划分沿用OCV step 0、容量step 2、脉冲5/6/7、验证32…49；保留原采样间隔与组身份。现有转换为旧接口充正放负，新深研适配不得重复翻转。**没有独立实测SOC**：由电流和容量计算的参考SOC只能写reference。先按整段工况留出，后续跨电芯/温度验证必须另取合适数据；不能把同一RW3的随机逐行切分称为跨电芯验证。

**EDU01 / Plett公开课程。** 现有[UCCS中文导读](../../uccs-中文导读路径.md)对应ECE5710建模与ECE5720估计控制，作为B02/B03、D02/D11–D14/R02的理论补充。公开可读不等于开源许可；不重发本地讲义。原站此前2026-11-07有访问失败记录，本轮未复查原站，故不写“已恢复”。后续关键公式引用需核到实际讲义版本和页节。

**CASE01 / 社区故障闭环。** 实读[PyBaMM #5072](https://github.com/pybamm-team/PyBaMM/issues/5072)正文、4条评论、关联事件和[修复PR #5205](https://github.com/pybamm-team/PyBaMM/pull/5205)的补丁。用户报告25.6.0及自定义模型在时间切换附近出现非物理结果；修复合并提交为`eed82f4729d84a2eb4b7dbb25c907460a23de282`，涉及时间不连续点的收集、过滤与合入。

采用到E11：区间外、端点、重复事件及左右侧分别检验，用解析小ODE先审语义，再接复杂模型。补丁的文字描述与端点行为有表述差异，应以明确的代码/测试合同解释。该历史个案不证明当前库或全部求解器都有同样问题；本轮没有重跑原MWE，也未确定首个含修复的发行标签。社区问题用来形成反例，再由本地证据决定结论。

## 4. 十二项实验合同

全部状态为`planned`。E ID是实验族，可含多个带独立`scenario_id`的基准/反例；不等于用一个脚本覆盖所有单元。每项都要走总SPEC的G01–G10，输入/输出/判据随所属任务冻结。下面的“验收”是未来要求。

| ID / 阶段 / 单元 | 输入、推导与最小复现 | 必做反例或迁移 | 图和学员作品 | 验收及独立边界 |
|---|---|---|---|---|
| E01 测量到动作；P1/P3；D04–D08 | S1冻结误差/协方差、RC建立、N=1/5/9滤波；按OS04/OS05追需求→编码→表征→写入→独立回读 | 相关噪声、单点校准外推、量程内开线、过期值、写失败仍回填；换相位/通道数 | 信号路径手绘、误差与扫描共时轴；C1预算/校准表 | 对照S1解析值；完整物理链重算起止和重叠；配置值不证明写成功。手册缺失不编硬件延时；仿真通过不算AFE实测 |
| E02 脉冲辨识；P1/P4；D02/D11/D14、R02 | S2主1RC：K/A/τ联合拟合、有限脉冲修正、独立30 s验证；再按OS02扩2RC | 短窗/未知OCV、多初值、边界命中、2RC标签交换、未知偏置 | 手绘等效电路、极化分解、残差/目标函数、重合电压；C2参数报告 | 无噪解析容差按S2；带噪报告区间与敏感性。低训练RMSE不代表可辨识；实测数据许可/划分另验 |
| E03 预充及反馈；P1/P5；D07/D08/D23、C3 | S3含初始残压的RC/能量；OS07命令→反馈来源→诊断；冻结每类反馈时钟 | 单电压根因判断、命令回填、过期反馈、按串错归属、残压/回灌、重试热与锁存 | 分状态手绘回路、源/阻/容能量、五泳道时序；器件/故障矩阵 | 能量守恒与允许状态转移同时通过；清旗不等于重合许可；辅助触点不证明主路径断流；器件分断仍待实测 |
| E04 整包不一致；P3小电路/P6模型；D03/D10/D16/D17/D24/D28 | 先手算2p1s节点网络，再OS03的逐电芯SOC/连接电阻/拓扑；一次只改一项 | 同平均值但最弱单节不同；几何变化被误称老化；端子位置改变分流 | 大幅节点/流向手绘、逐支路波形、最弱项热图；网络与约束报告 | KCL/KVL残差按数值精度设容差；逐节首次约束可追溯。耦合热/寿命结论需相应实测依据 |
| E05 均衡、热与净电流；P3/P5；D07/D09/D10/D18 | 由OS04–OS06配置审读画旁路，算Ah/Wh/占空比/热和有效采样窗口 | 低压差≠已均衡；容量弱项无法修复；旁路净电流/充电器电流混用；停均衡后仍用旧样本 | 手绘分流/发热机制、采样窗口、能量账；两方案取舍 | 守恒、有效样本标记和动作权限一致；实际器件值/热限/独立保护由SRC02–04补齐 |
| E06 SOC与可观测性；P4；D12–D14、C2/R02 | DATA01先复核谱系和划分；合成真值基准做手算EKF一轮，再无真值实测诊断 | 初值/容量/偏置分别失配；小新息但SOC错；平坦OCV局部病态 | 状态身份手绘、预测/更新、新息/漂移图；参考/预测分栏 | 合成状态误差与真实数据诊断分别报告；未独立实测不得给SOC准确度结论；Q/R单位与整定数据登记 |
| E07 通信和责任边界；P3/P5/P6；D08/D19/D20/D24 | OS06请求/本地动作/外部限流职责；OS07反馈身份；按发送/接收实际位图追字段→所有者→动作 | SOH占位100%、旧文档位图、合法CRC旧帧、回绕/复位/过期、远端不响应、任务超时 | 端到端泳道、责任分区手绘；故障轨迹/安全默认值表 | CRC/时效/授权与缓存回收分开验；注释掉的诊断不计覆盖；命令有实际执行者和时间上界来源。没有执行证据不宣称保护成功 |
| E08 老化与外推；P4/P6；D15–D18/D27、R03 | OS08固定模型卡、日历/EFC/容量输出；比较固定能量/固定SOC窗口 | 10℃0.16C与通用0.65C混淆、分量抵消、变化气候误用快算、长期外推 | 老化机制手绘、二维条件域、分组/误差和容量曲线；模型限制报告 | 标定/验证按电芯或温度/工况隔离，范围组合可查；无独立数据则只交模型演示，R03实证部分保持pending |
| E09 数据变换与重放；P4/P5；B05/D21/D26 | OS09 schema与来源；DATA01原始→单位/符号→组→派生；重算电量/能量 | V/mV、J/Wh、双重翻转、重复/回退/缺失时间、空段、随机逐行泄漏、趋势误判 | 数据来源/时间轴图；输入摘要、变换日志、重放报告 | 不静默修输入；派生量可追到原始行/组；启发式只报警。以相同冻结输入独立重放并按算法容差比对 |
| E10 模型层级；P6；D01/D02/D27、R01 | OS01同目标下ECM/SPM/SPMe/DFN卡；解释保留的过程、参数、离散与成本 | 默认参数不同却直接排名、网格未收敛、模型互相接近被称真值 | 电芯尺度手绘、模型状态对照、统一工况曲线；选择与边界报告 | 冻结版本/参数/网格/求解器/事件；细化收敛单独检验。无独立实测仅称模型间差异 |
| E11 事件与分段输入；P6；B02/D02/D18/D27、R01 | CASE01启发；解析一阶ODE检验切换，随后固定环境比较求解器 | 区间前后/端点/重复事件，严格与非严格比较，输出时刻与积分时刻混用 | 分段输入与响应共时轴、左右极限标注；最小复现与版本记录 | 解析解、事件时间、终止原因都验；案例复现另设状态，关闭issue不能当本项目验证 |
| E12 能量及采样口径；P4/P6；B01/B05/D03/D17/D18/D27 | OS01倍率例与OS09单位；从积分计算Ah/Wh，先用解析分段轨迹 | 改采样密度导致普通均值变；把Ah当Wh；漏3600；只检查预测窗口末点 | 能量面积、重采样对照、SOP约束切换；单位/窗口报告 | 同一轨迹非均匀输出下按积分精度一致；电压/温度约束检查整个窗口，未建模约束显著列出 |

三样章的参数、公式、时间语义与容差以[执行计划S1–S3](2026-11-08-bms-depth-rebuild.md)为唯一合同，这里不维护第二套数值。E04/E10等分为轻量前置与高保真研究两部分，先修通过才进入后者；不得把复杂库安装变成初学者第一步。

## 5. 还缺什么来源，何时必须补齐

九仓并不能覆盖BMS全部专业事实。以下缺口必须由P0.9指派，相关单元的G02/G03退出前补证据。候选方向尚未在本轮实际审读，不计入“已参考”数量。

| ID | 待补证据 | 目标单元 / 阻塞环节 | 下一次必须交付 | 拒收条件 |
|---|---|---|---|---|
| SRC01 电芯原理/限值 | 具体化学体系的厂家手册、OCV/温度数据、公开电化学教材/论文 | D01/D03/D12/D18，G02/G03 | 料号/版本/页节、限值条件、OCV迟滞/静置证据、数据身份 | 开源例程3.2 V等默认值直接当通用电芯规则 |
| SRC02 AFE与板级测量 | OS04/OS05进一步逐网审图；所选AFE手册/勘误、布局/回流与EMC测量资料 | D04–D06/D10，E01/E05 | 配置→脚位→RC→采样→寄存器链；板型/修订；实际尺寸原理图审查与误差预算 | 只读KiCad文本就宣称PCB/EMC通过；未核扫描语义就加延时 |
| SRC03 功率与独立保护 | MOS/驱动/接触器/预充电阻/熔断器/IMD的具体手册和应用资料 | D07–D09/D23，S3与E05 | 带条件的SOA/脉冲/热/耐压/分断曲线，驱动与共因假设；具体器件再定验收阈值 | 单一额定功率或95%母线比例替代选型；熔断器名称替代保护配合 |
| SRC04 热和充电实证 | 独立温度测点、熵热/热容/换热标定、完整窗口限流与充电许可来源 | D16–D18，E06/E08/E12 | 可分离的标定/验证工况与测点身份；非真实数据则只交模型范围 | 电压拟合好就宣布温度/SOP/快充安全有效 |
| SRC05 通信/诊断/刷写 | 本仓protocol/firmware继续追踪；可再审Zephyr、MCUboot、python-can/cantools、python-udsoncan等对应模块 | D19–D22，P5 | 冻结采用项目/文件/许可，区分编解码、会话、授权、镜像签名/回滚与断电恢复；逐步故障实验 | 工具支持某协议就宣称端到端安全；CRC当认证；MCUboot等同完整UDS方案 |
| SRC06 系统安全/生产 | 目标应用适用标准及可合法取得条款；开源需求/测试/配置链，真实产线和在役实例 | D09/D24–D26、R04，P6 | 标准版本/适用性、需求—实现—验证对应、EOL/配置追溯及证据缺口 | 仿真或开源认证代替产品合规；无条款原文却编具体要求 |
| SRC07 研究与外部验证 | PyBOP数据原始许可、BLAST原论文/独立老化数据、跨电芯/温度组；W5与专项镜头 | R01–R03、D15/D27/D28，P6/P7 | 参数/数据/代码各自来源和实际取得状态；新分组的适用性；真人/硬件原始记录 | 同一数据拆行冒充跨域、模型代答、合成图顶替真实测量和专项实拍 |

SRC缺口未闭合时，可完成不依赖它的推导和教学合成基准，但不能把依赖结论标为已验证。数据确实无法取得时，交付范围缩至合成演示并记`gap/pending`；不得悄悄降低独立验证门槛。

## 6. 各环节如何恢复与收口

每次开工从P任务定位到D/B/R单元，读取该单元的G01–G10状态、来源ID和E实验族。先解决阻塞的先修、源证据或参数歧义，再制作源稿/实验/图。三样章完成后，根据实际返工修订后续批次工作量；完整实现前不宣布达到“从入门到精通”。

规划验收只核对来源、映射、依赖、公式合同、文件链接与未完成状态。之后每一批实现要有真实输出和审查记录；通过本轮文档检查不计入实验通过数。W5真人试读和7项专项照片保持待验收，当前没有新证据可关闭它们。
