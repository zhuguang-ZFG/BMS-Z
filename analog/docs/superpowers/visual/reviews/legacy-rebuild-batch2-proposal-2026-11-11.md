# 画廊 legacy 动画批次2 rebuild 提案 · 2026-11-11

146 个 p5 画廊 legacy 动画（批次1已处置7个在外）的处置提案。
依据：accepted V2 池 118 个（含本日新签核 24 个）的主题/purpose 逐对匹配。

## 一、rebuild 候选 45 个

| legacy | demo 节 | 候选 V2 替代 | 信心 | 备注 |
|---|---|---|---|---|
| boost-converter.svg | 5.14 Boost 升压：电感叠罗汉 | ch13-boost-cycle-v2 | 高 |  |
| bridge-rectifier.svg | 5.2 桥式整流与滤波 | ch02-bridge-power-v2 | 高 | 桥堆功耗 |
| buck-converter.svg | 5.11 Buck 降压：伏秒平衡 | ch13-buck-cycle-v2 | 高 | 伏秒平衡同主题 |
| charge-pump.svg | 5.23 电荷泵：电容斗提机 | ch13-pump-load-v2 | 高 |  |
| class-b-crossover.svg | 5.9 乙类推挽与交越失真 | ch11-crossover-v2 | 高 | 预偏置死区 |
| comparator-hysteresis.svg | 5.4 比较器迟滞 | ch07-hysteresis-timing-v2 | 中 | 5.4 为抗噪演示 |
| compliance-voltage.svg | 5.80 恒流源的合规电压 | ch13-current-compliance-v2 | 高 |  |
| constant-current.svg | 5.26 恒流源：电压横扫，电流平躺 | ch13-current-compliance-v2 | 中 | 恒流源主题近，形态需看 |
| current-mirror.svg | 5.13 电流镜：共用 V_BE 的复印机 | ch11-mirror-beta-v2 | 高 | 电流镜 β 误差 |
| derive-buck.svg | 5.114 降压纹波六步推导：那个 8 是三角波的面积 | ch13-buck-cycle-v2 | 中 | 推导节，V2 为波形演示，形态需看 |
| diff-pair.svg | 5.8 差分对：差模放大、共模抑制 | ch11-diff-steer-v2 | 高 | 尾电流分配 |
| discrete-ldo.svg | 5.65 分立串联稳压：LDO 的祖爷爷 | ch09-dropout-ripple-v2 | 中 | LDO 主题，V2 为稳压余量 |
| exp-555-duty.svg | 5.141 555 占空比：充放两条路各管一段 | ch10-diode-duty-v2 | 高 | 占空比非对称 |
| exp-555-mono-train.svg | 5.140 单稳态触发链：一触发，亮一拍 | ch10-monostable-leakage-v2 | 高 | 单稳态漏电 |
| exp-beta-drift.svg | 5.127 β 漂移冲击工作点：偏置的失效边界 | ch11-beta-budget-v2 | 高 | β 与偏置预算 |
| exp-cload-isolate.svg | 5.145 容性负载自激与隔离电阻（失效边界） | ch12-riso-step-v2 | 高 | 隔离电阻阶跃 |
| exp-conduction-angle.svg | 5.125 导通角与峰值电流：窄窗里的猛冲 | ch02-charge-window-v2 | 中 | 电荷窗口/峰值 |
| exp-crystal-pull.svg | 5.147 晶振牵引灵敏度：3pF 偏差值多少秒 | ch13-crystal-pull-v2 | 高 |  |
| exp-dead-time.svg | 5.131 直通窗口与死区：换向瞬间谁在岗 | ch04-deadtime-energy-v2 | 高 | 死区能量 |
| exp-delay-budget.svg | 5.135 判决延迟预算：运放兼职的代价 | ch07-release-timing-v2 | 高 | 响应时间定义 |
| exp-droop-budget.svg | 5.137 采样保持的 droop 预算：时间维度的税 | ch08-sample-hold-v2 | 中 | 采样保持；V2 为四拍演示 |
| exp-esr-ripple-split.svg | 5.122 纹波的两本账：容性与 ESR 谁说了算 | ch17-esr-sweep | 高 | ESR 纹波扫描同主题 |
| exp-gate-charge.svg | 5.129 米勒平台的栅电荷账：驱动电流是挤压器 | ch04-gate-power-v2 | 中 | 栅电荷/驱动功率 |
| exp-hyst-window.svg | 5.134 迟滞窗口：抗噪护城河的宽与窄 | ch07-hysteresis-timing-v2 | 高 | 迟滞窗口 |
| exp-inject-harmonic.svg | 5.136 电荷注入的信号相关性：从台阶到谐波 | ch08-charge-injection-v2 | 中 | 电荷注入；V2 标注技术原型 |
| exp-integrator-drift.svg | 5.144 积分器漂移与泄放电阻（失效边界） | ch12-leaky-integrator-v2 | 中 | 泄放电阻——与 5.33 同形态顾虑，需用户看 |
| exp-miller-mult.svg | 5.142 米勒倍增：一只电容被增益放大 | ch11-miller-charge-v2 | 高 | 米勒电荷 |
| exp-noise-ladder.svg | 5.143 噪声三税：一张预算表收口 | ch11-noise-bandwidth-v2 | 中 | 噪声积分；V2 为带宽积分 |
| exp-psrr-roll.svg | 5.139 PSRR 随频率滚降：电源抑制是分段防守 | ch11-psrr-ripple-v2 | 高 | PSRR 随频率 |
| exp-pullup-trade.svg | 5.130 上拉取值：上升沿与功耗的双边权衡 | ch05-pullup-window-v2 | 高 | 上拉窗口 |
| exp-slew-wall.svg | 5.133 压摆率墙：大信号的失效边界 | ch06-speed-envelope-v2 | 高 | 大信号斜率边界 |
| exp-source-sag.svg | 5.119 源的两次测量法：内阻一笔算出（失效边界） | ch00-divider-loading-v2 | 中 | 内阻/输出电阻 |
| exp-volt-second.svg | 5.146 伏秒平衡：电感稳态的入场券 | ch13-buck-cycle-v2 | 中 | 伏秒平衡；5.146 推导形态 |
| h-bridge.svg | 5.29 H 桥：电流听指挥掉头 | ch13-hbridge-reverse-v2 | 高 |  |
| inverting-buckboost.svg | 5.28 反相 Buck-Boost：正进负出 | ch13-inverting-ratio-v2 | 高 |  |
| miller-effect.svg | 5.16 米勒效应：10pF 变身 1nF | ch11-miller-charge-v2 | 中 | 5.16 为频率响应演示 |
| ne555-astable.svg | 5.6 555 无稳态振荡 | ch10-astable-cycle-v2 | 高 |  |
| ne555-monostable.svg | 5.30 555 单稳态：一触发，亮一拍 | ch10-monostable-leakage-v2 | 高 |  |
| pushpull-opendrain.svg | 5.5 推挽 vs 开漏 | ch05-open-drain-sharing-v2 | 高 |  |
| rlc-resonance.svg | 5.18 LC 谐振：电场磁场荡秋千 | ch13-lc-energy-v2 | 高 |  |
| sallen-key.svg | 5.10 Sallen-Key 二阶低通 | ch12-filter-q-v2 | 高 | Q 与阶跃形状 |
| sar-adc.svg | 5.19 SAR ADC：四位天平 | ch13-sar-trials-v2 | 高 |  |
| tristate-bus.svg | 5.51 三态总线：谁说话，谁闭嘴 | ch05-tristate-timing-v2 | 高 |  |
| wien-bridge.svg | 5.12 文氏桥振荡器：起振与稳幅 | ch13-wien-select-v2 | 高 |  |
| zener-regulator.svg | 5.25 齐纳稳压：电压溢流阀 | ch13-zener-budget-v2 | 高 |  |

## 二、无 V2 对应 101 个

概念/总览类演示，处置需用户决策：retire（从 p5 删 demo 节）或排期新建 V2。

| legacy | demo 节 | 类别 |
|---|---|---|
| 555-astable-beats.svg | 5.86 555 无稳态四拍：电容荡秋千，输出跳方波 | 555 |
| 555-modes.svg | 5.58 555 三种模式：同一颗芯三副面孔 | 555 |
| analog-switch-beats.svg | 5.84 模拟开关开合四拍：电荷注入如何毁掉采样精度 | 总览/其他 |
| analog-switch.svg | 5.94 模拟开关：电荷注入 | 总览/其他 |
| bjt-amplify.svg | 5.3 共射放大器失真 | BJT 概念 |
| bjt-configs.svg | 5.64 三种组态：一只管子的三种人生 | BJT 概念 |
| bjt-diagnosis.svg | 5.74 BJT 在线速判：三个电压定故障 | BJT 概念 |
| bjt-regions.svg | 5.40 BJT 三个工作区：负载线切过哪里 | BJT 概念 |
| bjt-switch.svg | 5.67 BJT 开关：Rb 怎么算、二极管为什么不能省 | BJT 概念 |
| bjt-transport.svg | 5.66 BJT 放大原理：99% 的电子成了 I_C | BJT 概念 |
| body-diode.svg | 5.68 体二极管与栅极保护：MOS 的两条命门 | 总览/其他 |
| cap-decoupling.svg | 5.96 去耦电容：本地水库 | 电容 |
| cap-derating.svg | 5.103 电容直流偏压：标称容量 ≠ 工作容量 | 电容 |
| capacitor-parasitics.svg | 5.43 真实电容阻抗频谱：谷底定去耦 | 电容 |
| ce-dynamic.svg | 5.81 共射放大器四拍：输入升、输出降 | 总览/其他 |
| clipper-clamper.svg | 5.31 削波与钳位：闸门与垫脚石 | 总览/其他 |
| comparator-opamp.svg | 5.47 运放 vs 比较器：快的不一定能用 | 比较器 |
| comparator-pitfalls.svg | 5.76 比较器的五个坑：忘接上拉排第一 | 比较器 |
| crystal-pierce.svg | 5.105 晶体振荡器：Pierce 拓扑与负阻判据 | 总览/其他 |
| darlington.svg | 5.70 达林顿管：β 相乘与三笔代价 | 总览/其他 |
| datasheet-params.svg | 5.71 Datasheet 六参数优先级 | 总览/其他 |
| debug-flow.svg | 5.38 排故五步法：把玄学拆成实验 | 总览/其他 |
| derive-divider.svg | 5.109 分压公式四步推导：I 先算出来，再乘下臂电阻 | 推导 |
| derive-feedback.svg | 5.112 负反馈增益六步推导：从 Vout = A·Vd 到 Af ≈ 1/β | 推导 |
| derive-gain.svg | 5.111 共射增益五步推导：gm 变电流，Rc 变回电压 | 推导 |
| derive-miller.svg | 5.113 米勒电容六步推导：10pF 为什么看起来像 1nF | 推导 |
| derive-ripple.svg | 5.110 纹波公式五步推导：电荷 → 电压 → 整流补几次 | 推导 |
| design-flow.svg | 5.98 从需求到打样：六步流程 | 总览/其他 |
| diagnosis-tree.svg | 5.102 排故决策树：从「上电无反应」到具体表项 | 总览/其他 |
| diode-family.svg | 5.61 特殊二极管家族：压降与速度的地图 | 二极管 |
| diode-iv.svg | 5.46 二极管伏安特性：60mV 换十倍电流 | 二极管 |
| error-budget.svg | 5.107 误差预算：最坏情况 vs 统计叠加 | 总览/其他 |
| exp-avalanche-edge.svg | 5.124 感性负载的关断尖峰：电感物理的必然推论 | 实验边界 |
| exp-cap-life.svg | 5.123 电解电容寿命账：10°C 翻倍（失效边界） | 实验边界 |
| exp-contact-creep.svg | 5.152 接触电阻蠕变：只量通断会漏掉的漂移窗（失效边界） | 实验边界 |
| exp-cost-ladder.svg | 5.153 1-10-100 成本法则：把故障往左推 | 实验边界 |
| exp-derate-chain.svg | 5.121 额定功率的降额链：标称值怎么缩水 | 实验边界 |
| exp-gbw-swap.svg | 5.132 增益带宽交换：GBW 是一笔守恒的预算 | 实验边界 |
| exp-ldo-zero.svg | 5.138 LDO 换料的隐性账：ESR 零点与稳定（失效边界） | 实验边界 |
| exp-log2-split.svg | 5.151 二分定位的对数数学：6 节点 3 刀 | 实验边界 |
| exp-return-cut.svg | 5.149 回流路径被割断：开槽的代价（失效边界） | 实验边界 |
| exp-thermal-loop.svg | 5.128 热失控：一条闭合的正反馈环（失效边界） | 实验边界 |
| exp-tvs-ladder.svg | 5.126 接口防护三级削减：TVS → 电阻 → 钳位 | 实验边界 |
| exp-unit-guard.svg | 5.120 单位错档一千倍：数量级先钉死 | 实验边界 |
| exp-via-stack.svg | 5.150 叠层与阻抗：同一只 50Ω 两种命运 | 实验边界 |
| exp-wc-rss.svg | 5.148 最坏情况 vs RSS：误差预算的两把尺 | 实验边界 |
| fault-lookup.svg | 5.91 故障速查：症状 → 嫌疑 → 验证 | 总览/其他 |
| feedback-topo.svg | 5.59 负反馈四种拓扑：稳定什么就采样什么 | 总览/其他 |
| ground-star.svg | 5.100 一点接地：让大电流别踩小信号的路 | 总览/其他 |
| impedance-freq.svg | 5.36 阻抗随频率：电容降价、电感涨价 | 总览/其他 |
| instrumentation-amp.svg | 5.17 仪表放大器：三道防线挡共模 | 总览/其他 |
| integrator.svg | 5.33 积分器：方波换三角波 | 总览/其他 |
| intermittent-forcing.svg | 5.116 间歇故障：先逼它现身，再在窗口里等它 | 总览/其他 |
| ldo-failures.svg | 5.73 7805/AMS1117 四种翻车 | 电源 |
| ldo-feedback.svg | 5.95 LDO 负反馈：闭环控制 | 电源 |
| ldo-transient-beats.svg | 5.85 LDO 负载瞬态四拍：一次唤醒为何把 MCU 打到复位 | 电源 |
| lm358-dual.svg | 5.63 LM358：单电源双运放的两条边界 | 总览/其他 |
| lm393-inside.svg | 5.54 解剖 LM393：开集电极输出的三个红利 | 总览/其他 |
| master-wisdom.svg | 5.97 大师的排故智慧：三份心法，一条军规 | 总览/其他 |
| miller-plateau.svg | 5.44 米勒平台：开通那 700ns 里最贵的 410ns | 总览/其他 |
| mosfet-curves.svg | 5.57 MOSFET 输出特性：饱和反而是放大区 | FET 概念 |
| mosfet-four-beats.svg | 5.82 MOSFET 开通四拍：栅极电荷如何变成热 | FET 概念 |
| mosfet-switch.svg | 5.92 MOSFET 开关：沟道形成与导通 | FET 概念 |
| mux-4051.svg | 5.69 CD4051：八路传感器共用一个 ADC | 总览/其他 |
| ne555-params.svg | 5.77 555 参数与三个坑 | 总览/其他 |
| neg-feedback.svg | 5.32 负反馈：十万倍的蛮力，被一根线驯成 6 倍 | 总览/其他 |
| noise-budget.svg | 5.48 噪声三税种：不能消灭，只能谈判 | 总览/其他 |
| opamp-input-stage.svg | 5.104 运放输入级选型：源阻抗决定一切 | 运放概念 |
| opamp-internals.svg | 5.37 运放内部：三级流水线攒出 20 万倍 | 运放概念 |
| opamp-inverting.svg | 5.93 反相放大器：虚短虚断 | 运放概念 |
| opamp-map.svg | 5.72 运放选型地图：速度 × 精度 | 运放概念 |
| opamp-pitfalls.svg | 5.75 运放的六个经典坑 | 运放概念 |
| opamp-slew.svg | 5.45 运放阶跃：直线爬坡，不是指数 | 运放概念 |
| optocoupler-ctr.svg | 5.106 光耦与隔离：CTR 是设计变量 | 总览/其他 |
| pcb-return-path.svg | 5.7 PCB 回流路径 | Layout |
| pcb-routing.svg | 5.90 PCB 布线四招：45° 拐角 / 过孔 / 差分对 / 包地 | Layout |
| peak-detector.svg | 5.27 峰值检测：单向记忆 | 总览/其他 |
| pn-junction.svg | 5.56 PN 结：一堵会自己调节高度的墙 | 总览/其他 |
| power-tree.svg | 5.88 树状供电：逐级净化 | 总览/其他 |
| precision-rectifier.svg | 5.15 精密整流：借增益消灭 0.7V | 总览/其他 |
| predict-measure.svg | 5.115 预测对实测：对不上的地方才是线索 | 总览/其他 |
| probe-ground-loop.svg | 5.108 探头地线环：量到的纹波可能是假的 | 调试 |
| probe-loading.svg | 5.49 探头是负载：测量本身在改电路 | 调试 |
| pullup-sizing.svg | 5.62 上拉电阻：4.7k 是怎么算出来的 | 总览/其他 |
| pushpull-stage.svg | 5.53 推挽输出级：直通电流从哪来 | 总览/其他 |
| rc-charge.svg | 5.1 RC 充电 | 基础电路 |
| rc-lowpass.svg | 5.24 一阶 RC 低通与波特图 | 基础电路 |
| rectifier-filter-beats.svg | 5.83 整流滤波电源四拍：从空电容到稳态纹波 | 总览/其他 |
| ref-showdown.svg | 5.55 齐纳 vs 带隙：两套温漂账 | 总览/其他 |
| resistor-model.svg | 5.60 真实电阻：高频时它不再是「一个电阻」 | 总览/其他 |
| schmitt-osc.svg | 5.35 迟滞振荡器：方波自己弹出来 | 总览/其他 |
| signal-chain.svg | 5.42 PT100 信号链：把信号顶到接近满量程 | 总览/其他 |
| thermal-runaway.svg | 5.41 热失控：自己给自己加速的正反馈 | 总览/其他 |
| thevenin-norton.svg | 5.79 戴维南与诺顿：两个数定性格 | 总览/其他 |
| thinking-toolbox.svg | 5.99 思维工具箱：四暗器 | 总览/其他 |
| three-probe-audit.svg | 5.118 三触点对账：160mV 去了哪里 | 方法 |
| three-topologies.svg | 5.52 三种基本拓扑：同一只运放的三条路 | 方法 |
| transformer.svg | 5.101 变压器：电压换电流 | 总览/其他 |
| virtual-ground.svg | 5.34 单电源虚地：给信号造一个假地 | 总览/其他 |
| voltage-drop.svg | 5.89 电压降：同一股电流，谁 R 大谁分得多 | 总览/其他 |
| water-analogy.svg | 5.87 水路 = 电路：全书通用比喻 | 总览/其他 |
