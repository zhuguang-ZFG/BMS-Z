<a id="part5"></a>
# 第五篇：动画演示中心

> 全部 SVG 原理动画（SMIL，浏览器直接播放）位于 `assets/svg/` 目录，由 `scripts/generate_svgs.py` 一键产出，数量以生成器输出为准（仓库铁律：两者始终同步，扩量闸见 `scripts/test_svg_count_floor.py`）。配套 Falstad 在线电路可实时交互。

<details markdown="1">
<summary>动画速查：按章节，全索引（点击展开）</summary>

| 章 | 动画（点击直达） |
|---|---|
| §0 第 0 章 电路直觉学前班：先上车，再赶路 | [5.39](p5-00-part5.md#demo39) · [5.78](p5-00-part5.md#demo78) · [5.87](p5-00-part5.md#demo87) · [5.89](p5-00-part5.md#demo89) · [5.109](p5-00-part5.md#demo109)  · [5.119](p5-00-part5.md#demo119) · [5.120](p5-00-part5.md#demo120) · [5.121](p5-00-part5.md#demo121) |
| §1 第 1 章 无源元件的真实面目 | [5.36](p5-00-part5.md#demo36) · [5.43](p5-00-part5.md#demo43) · [5.60](p5-00-part5.md#demo60) · [5.79](p5-00-part5.md#demo79) · [5.101](p5-00-part5.md#demo101) · [5.103](p5-00-part5.md#demo103)  · [5.122](p5-00-part5.md#demo122) · [5.123](p5-00-part5.md#demo123) · [5.124](p5-00-part5.md#demo124) |
| §2 第 2 章 二极管：单向导电的物理本质 | [5.2](p5-00-part5.md#demo2) · [5.31](p5-00-part5.md#demo31) · [5.46](p5-00-part5.md#demo46) · [5.56](p5-00-part5.md#demo56) · [5.61](p5-00-part5.md#demo61) · [5.83](p5-00-part5.md#demo83) · [5.110](p5-00-part5.md#demo110)  · [5.125](p5-00-part5.md#demo125) · [5.126](p5-00-part5.md#demo126) |
| §3 第 3 章 BJT 三极管：完整概念体系 | [5.3](p5-00-part5.md#demo3) · [5.40](p5-00-part5.md#demo40) · [5.41](p5-00-part5.md#demo41) · [5.66](p5-00-part5.md#demo66) · [5.67](p5-00-part5.md#demo67) · [5.70](p5-00-part5.md#demo70) · [5.74](p5-00-part5.md#demo74) · [5.81](p5-00-part5.md#demo81)  · [5.127](p5-00-part5.md#demo127) · [5.128](p5-00-part5.md#demo128) |
| §4 第 4 章 MOSFET：电压控制的开关王者 | [5.44](p5-00-part5.md#demo44) · [5.57](p5-00-part5.md#demo57) · [5.68](p5-00-part5.md#demo68) · [5.82](p5-00-part5.md#demo82) · [5.92](p5-00-part5.md#demo92)  · [5.129](p5-00-part5.md#demo129) |
| §5 第 5 章 输出结构彻底讲透：推挽、开漏、上拉下拉 | [5.5](p5-00-part5.md#demo5) · [5.51](p5-00-part5.md#demo51) · [5.53](p5-00-part5.md#demo53) · [5.62](p5-00-part5.md#demo62) · [5.117](p5-00-part5.md#demo117)  · [5.130](p5-00-part5.md#demo130) · [5.131](p5-00-part5.md#demo131) |
| §6 第 6 章 运算放大器：从内部结构到参数字典 | [5.37](p5-00-part5.md#demo37) · [5.45](p5-00-part5.md#demo45) · [5.63](p5-00-part5.md#demo63) · [5.71](p5-00-part5.md#demo71) · [5.72](p5-00-part5.md#demo72) · [5.75](p5-00-part5.md#demo75) · [5.93](p5-00-part5.md#demo93) · [5.112](p5-00-part5.md#demo112)  · [5.132](p5-00-part5.md#demo132) · [5.133](p5-00-part5.md#demo133) |
| §7 第 7 章 比较器：专为"判决"而生 | [5.4](p5-00-part5.md#demo4) · [5.35](p5-00-part5.md#demo35) · [5.47](p5-00-part5.md#demo47) · [5.54](p5-00-part5.md#demo54) · [5.76](p5-00-part5.md#demo76)  · [5.134](p5-00-part5.md#demo134) · [5.135](p5-00-part5.md#demo135) |
| §8 第 8 章 模拟开关与多路复用器：CMOS 传输门 | [5.22](p5-00-part5.md#demo22) · [5.50](p5-00-part5.md#demo50) · [5.69](p5-00-part5.md#demo69) · [5.84](p5-00-part5.md#demo84) · [5.94](p5-00-part5.md#demo94)  · [5.136](p5-00-part5.md#demo136) · [5.137](p5-00-part5.md#demo137) |
| §9 第 9 章 电压基准与稳压器：系统的"定盘星" | [5.20](p5-00-part5.md#demo20) · [5.21](p5-00-part5.md#demo21) · [5.25](p5-00-part5.md#demo25) · [5.55](p5-00-part5.md#demo55) · [5.73](p5-00-part5.md#demo73) · [5.85](p5-00-part5.md#demo85) · [5.95](p5-00-part5.md#demo95)  · [5.138](p5-00-part5.md#demo138) · [5.139](p5-00-part5.md#demo139) |
| §10 第 10 章 555 定时器：最经典的混合信号芯片 | [5.1](p5-00-part5.md#demo1) · [5.6](p5-00-part5.md#demo6) · [5.30](p5-00-part5.md#demo30) · [5.58](p5-00-part5.md#demo58) · [5.77](p5-00-part5.md#demo77) · [5.86](p5-00-part5.md#demo86)  · [5.140](p5-00-part5.md#demo140) · [5.141](p5-00-part5.md#demo141) |
| §11 第 11 章 放大电路拓扑：三种组态与四大积木 | [5.8](p5-00-part5.md#demo8) · [5.9](p5-00-part5.md#demo9) · [5.13](p5-00-part5.md#demo13) · [5.16](p5-00-part5.md#demo16) · [5.48](p5-00-part5.md#demo48) · [5.64](p5-00-part5.md#demo64) · [5.111](p5-00-part5.md#demo111) · [5.113](p5-00-part5.md#demo113)  · [5.142](p5-00-part5.md#demo142) · [5.143](p5-00-part5.md#demo143) |
| §12 第 12 章 运放应用电路族：两条公理推演一切 | [5.10](p5-00-part5.md#demo10) · [5.15](p5-00-part5.md#demo15) · [5.17](p5-00-part5.md#demo17) · [5.24](p5-00-part5.md#demo24) · [5.27](p5-00-part5.md#demo27) · [5.32](p5-00-part5.md#demo32) · [5.33](p5-00-part5.md#demo33) · [5.34](p5-00-part5.md#demo34) · [5.52](p5-00-part5.md#demo52) · [5.59](p5-00-part5.md#demo59) · [5.104](p5-00-part5.md#demo104)  · [5.144](p5-00-part5.md#demo144) · [5.145](p5-00-part5.md#demo145) |
| §13 第 13 章 电源与信号产生电路 | [5.11](p5-00-part5.md#demo11) · [5.12](p5-00-part5.md#demo12) · [5.14](p5-00-part5.md#demo14) · [5.18](p5-00-part5.md#demo18) · [5.19](p5-00-part5.md#demo19) · [5.23](p5-00-part5.md#demo23) · [5.26](p5-00-part5.md#demo26) · [5.28](p5-00-part5.md#demo28) · [5.29](p5-00-part5.md#demo29) · [5.65](p5-00-part5.md#demo65) · [5.80](p5-00-part5.md#demo80) · [5.105](p5-00-part5.md#demo105) · [5.106](p5-00-part5.md#demo106) · [5.114](p5-00-part5.md#demo114)  · [5.146](p5-00-part5.md#demo146) · [5.147](p5-00-part5.md#demo147) |
| §14 第 14 章 电路设计方法论 | [5.42](p5-00-part5.md#demo42) · [5.88](p5-00-part5.md#demo88) · [5.98](p5-00-part5.md#demo98) · [5.107](p5-00-part5.md#demo107) · [5.108](p5-00-part5.md#demo108)  · [5.148](p5-00-part5.md#demo148) |
| §15 第 15 章 PCB 绘制注意事项 | [5.7](p5-00-part5.md#demo7) · [5.90](p5-00-part5.md#demo90) · [5.96](p5-00-part5.md#demo96) · [5.100](p5-00-part5.md#demo100)  · [5.149](p5-00-part5.md#demo149) · [5.150](p5-00-part5.md#demo150) |
| §16 第 16 章 排故五步法 | [5.38](p5-00-part5.md#demo38) · [5.49](p5-00-part5.md#demo49) · [5.99](p5-00-part5.md#demo99)  · [5.151](p5-00-part5.md#demo151) |
| §17 第 17 章 故障模式速查总表 | [5.91](p5-00-part5.md#demo91) · [5.102](p5-00-part5.md#demo102) · [5.116](p5-00-part5.md#demo116)  · [5.152](p5-00-part5.md#demo152) |
| §18 第 18 章 大师的排故智慧 | [5.97](p5-00-part5.md#demo97) · [5.115](p5-00-part5.md#demo115) · [5.118](p5-00-part5.md#demo118)  · [5.153](p5-00-part5.md#demo153) |

</details>
## 5.1 RC 充电 <a id="demo1"></a>

<p align="center"><img src="assets/svg/rc-charge.svg" width="720" alt="RC 充电动画：水桶与细水管"></p>




**看点**：电流箭头随充电逐渐变慢（alpha 衰减），即 $i_C=(V_S-v_C)/R$ 随电容电压升高而减小，指数曲线的成因就在这里。τ 时刻恰好充到 63.2%。

Falstad 交互：`Circuits → Basics → RC Circuit`

## 5.2 桥式整流与滤波 <a id="demo2"></a>

<p align="center"><img src="assets/svg/bridge-rectifier.svg" width="720" alt="桥式整流滤波SVG动画"></p>

**看点**：负半周被"翻转"上来；滤波电容在峰值充电（跟随橙色）、谷值放电（绿色自由衰减）。纹波大小正比于负载电流、反比于电容。

Falstad 交互：`Circuits → Diodes → Full-Wave Rectifier`

## 5.3 共射放大器失真 <a id="demo3"></a>

<p align="center"><img src="assets/svg/bjt-amplify.svg" width="720" alt="共射放大器SVG动画"></p>

**看点**：绿线 Q 点居中，波形完好；红线摆幅过大，顶部被截止区"削平"、底部撞饱和压降。**静态工作点是放大器的第一设计。**

Falstad 交互：`Circuits → Transistors → Common-Emitter Amp`

## 5.4 比较器迟滞 <a id="demo4"></a>

<p align="center"><img src="assets/svg-v2/ch07-hysteresis-timing-v2.svg" width="720" alt="相对中点的延时，只跨半个对称窗口。无迟滞参考门限 2.5 V，输入在 200 s 到达。 迟滞上阈值 2.727 V，在约 427.3 s 才翻转。 相对 2.5 V 的推迟是 227.3 s，不是 454.5 s。 只有拿下阈值作起点，时间差才对应整个窗口。 初态输出高；输入由 2.3 V 以 1 mV/s 上行，忽略传播与 RC 延迟。"></p>

**看点**：相对中点的延时，只跨半个对称窗口。无迟滞参考门限 2.5 V，输入在 200 s 到达。迟滞上阈值 2.727 V，在约 427.3 s 才翻转。相对 2.5 V 的推迟是 227.3 s，不是 454.5 s。

Falstad 交互：`Circuits → Op-Amps → Comparator → Hysteresis`

## 5.5 推挽 vs 开漏 <a id="demo5"></a>

<p align="center"><img src="assets/svg-v2/ch05-open-drain-sharing-v2.svg" width="720" alt="一只上拉给两个开漏输出供电。第二个下拉导通后总电流约三点二六毫安，由两条相等支路分担；另并一只上拉时总电流才升至约六点四四毫安。"></p>

**看点**：一只上拉给两个开漏输出供电。第二个下拉导通后总电流约三点二六毫安，由两条相等支路分担；另并一只上拉时总电流才升至约六点四四毫安。

## 5.6 555 无稳态振荡 <a id="demo6"></a>

<p align="center"><img src="assets/svg-v2/ch10-astable-cycle-v2.svg" width="720" alt="电容连续变化，输出在门限处切换。稳态从 3 V 起，RA 与 RB 一起给电容充电。 约 540.65 µs 到 6 V，输出转低、放电管导通。 经 RB 放电约 471.34 µs 后回到 3 V。 周期约 1.012 ms；输出高占 53.42%，并非对称。 示意 9 V、RA=1 kΩ、RB=6.8 kΩ、C=100 nF，理想开关。"></p>

**看点**：电容连续变化，输出在门限处切换。稳态从 3 V 起，RA 与 RB 一起给电容充电。约 540.65 µs 到 6 V，输出转低、放电管导通。经 RB 放电约 471.34 µs 后回到 3 V。

Falstad 交互：`Circuits → 555 Timer Chip → Astable Multivibrator`

## 5.7 PCB 回流路径 <a id="demo7"></a>

<p align="center"><img src="assets/svg/pcb-return-path.svg" width="720" alt="回流路径SVG动画"></p>

**看点**：红色信号粒子向前、绿色回流粒子紧贴其正下方反向回家（环路面积≈0）；地平面开槽后，紫色回流被迫绕到槽底走大圈，阴影区域就是 EMI 天线。


## 5.8 差分对：差模放大、共模抑制 <a id="demo8"></a>

<p align="center"><img src="assets/svg-v2/ch11-diff-steer-v2.svg" width="720" alt="差分电压重新分配同一份尾电流。负差模把电流分给右管，总量仍是 1 mA。 零差模时两管各得 0.5 mA。 各输入 ±10 mV 对应差模 20 mV，已偏离直线近似。 大差模让一边接近独占，不能无限线性放大。 示意匹配 BJT，集电流和 1 mA，VT=26 mV；忽略基流与 Early 效应。"></p>

**看点**：差分电压重新分配同一份尾电流。负差模把电流分给右管，总量仍是 1 mA。零差模时两管各得 0.5 mA。各输入 ±10 mV 对应差模 20 mV，已偏离直线近似。大差模让一边接近独占，不能无限线性放大。→ 正文 [第 11 章](p2-01-ch11.md#ch11)

## 5.9 乙类推挽与交越失真 <a id="demo9"></a>

<p align="center"><img src="assets/svg-v2/ch11-crossover-v2.svg" width="720" alt="预偏置逐渐缩小理想推挽死区。无预偏置，过零附近两支路都不导通。 基极间加 0.6 V，剩余死区缩小。 偏置增至 1 V，过零缺口进一步缩小。 1.3 V 在此模型中恰好消除死区；实物须测静态电流与温漂。 示意固定 VBE=0.65 V、输入峰值 1 V；恒压降模型不计算静态电流。"></p>

**看点**：预偏置逐渐缩小理想推挽死区。无预偏置，过零附近两支路都不导通。基极间加 0.6 V，剩余死区缩小。偏置增至 1 V，过零缺口进一步缩小。1.3 V 在此模型中恰好消除死区；实物须测静态电流与温漂。→ 正文 [11.4 推挽输出级](p2-01-ch11.md#ch11)

## 5.10 Sallen-Key 二阶低通 <a id="demo10"></a>

<p align="center"><img src="assets/svg-v2/ch12-filter-q-v2.svg" width="720" alt="同一自然频率，阶跃形状随 Q 变化。临界阻尼单调到达终值。更高 Q 增加振铃；比较响应前须说明频率归一化。"></p>

**看点**：同一自然频率，阶跃形状随 Q 变化。临界阻尼单调到达终值。更高 Q 增加振铃；比较响应前须说明频率归一化。→ 正文 [12.5 有源滤波](p2-02-ch12.md#ch12)

## 5.11 Buck 降压：伏秒平衡 <a id="demo11"></a>

<p align="center"><img src="assets/svg-v2/ch13-buck-cycle-v2.svg" width="720" alt="同一电感电流，开关与二极管轮流接管；导通初段至周期回到谷值。"></p>

**看点**：同一电感电流，开关与二极管轮流接管；导通初段至周期回到谷值。→ 正文 [13.2 Buck](p2-03-ch13.md#ch13)

## 5.12 文氏桥振荡器：起振与稳幅 <a id="demo12"></a>

<p align="center"><img src="assets/svg-v2/ch13-wien-select-v2.svg" width="720" alt="文氏桥只在一个频率兼有零相位与三分之一增益；f=0.1f0至f=10f0。"></p>

**看点**：文氏桥只在一个频率兼有零相位与三分之一增益；f=0.1f0 到 f=10f0。→ 正文 [13.4 文氏桥](p2-03-ch13.md#ch13)

## 5.13 电流镜：共用 V_BE 的复印机 <a id="demo13"></a>

<p align="center"><img src="assets/svg-v2/ch11-mirror-beta-v2.svg" width="720" alt="参考电流还要供给两只管子的基流。β=20 时，参考支路的基流占比不可忽略。 β=50 时，忽略 Early 的复制比约 96.15%。 β=100 时，复制比为 100/102。 β 增大只缩小基流误差；VCE 差仍会改变复制比。 示意匹配 β、同 VBE；实线忽略 Early，虚线 VA=100 V、输出 5 V。"></p>

**看点**：参考电流还要供给两只管子的基流。β=20 时，参考支路的基流占比不可忽略。β=50 时，忽略 Early 的复制比约 96.15%。β=100 时，复制比为 100/102。β 增大只缩小基流误差。→ 正文 [11.3 电流镜](p2-01-ch11.md#ch11)

## 5.14 Boost 升压：电感叠罗汉 <a id="demo14"></a>

<p align="center"><img src="assets/svg-v2/ch13-boost-cycle-v2.svg" width="720" alt="升压的关断阶段才把电感电流送往输出；导通储能至回到周期起点。"></p>

**看点**：升压的关断阶段才把电感电流送往输出；导通储能至回到周期起点。→ 正文 [13.3 Boost](p2-03-ch13.md#ch13)

## 5.15 精密整流：借增益消灭 0.7V <a id="demo15"></a>

<p align="center"><img src="assets/svg/precision-rectifier.svg" width="720" alt="精密整流SVG动画"></p>

**看点**：±100mV 小信号，普通二极管整流输出一条死线；运放把二极管塞进反馈环，等效死区 0.7V÷10万=7µV，输出半波分毫毕现。→ 正文 [12.6 精密整流](p2-02-ch12.md#ch12)

## 5.16 米勒效应：10pF 变身 1nF <a id="demo16"></a>

<p align="center"><img src="assets/svg-v2/ch11-miller-charge-v2.svg" width="720" alt="电荷随两端压差变化，电容本身没变。A=0，电容输出端固定，电荷只随输入变化。 A=10，输出反相，电容两端摆幅增加。 A=50，同一输入需搬运更多电荷。 A=100，等效输入电容为 1.01 nF。 示意 Cbc=10 pF；输入 ±1 mV，输出增益为 −A；低频电压增益近似。"></p>

**看点**：电荷随两端压差变化，电容本身没变。A=0，电容输出端固定，电荷只随输入变化。A=10，输出反相，电容两端摆幅增加。A=50，同一输入需搬运更多电荷。A=100，等效输入电容为 1.01 nF。示意 Cbc=10 pF。→ 正文 [11.5 频率响应](p2-01-ch11.md#ch11)

## 5.17 仪表放大器：三道防线挡共模 <a id="demo17"></a>

<p align="center"><img src="assets/svg/instrumentation-amp.svg" width="720" alt="仪表放大器SVG动画"></p>

**看点**：差模时 R_G 有电流（红粒子下流）、v1/v2 反向拉大；共模时 R_G 两端同升同降、无电流、前级增益=1，共模在源头就被"放生"，再被减法器剪掉。→ 正文 [12.3 节三运放仪放](p2-02-ch12.md#ch12)

## 5.18 LC 谐振：电场磁场荡秋千 <a id="demo18"></a>

<p align="center"><img src="assets/svg-v2/ch13-lc-energy-v2.svg" width="720" alt="电场能与磁场能交替，理想总能量不变；电容全储能至能量返回电容。"></p>

**看点**：电场能与磁场能交替，理想总能量不变；电容全储能至能量返回电容。→ 正文 [13.4 的延伸阅读段](p2-03-ch13.md#ch13)

## 5.19 SAR ADC：四位天平 <a id="demo19"></a>

<p align="center"><img src="assets/svg-v2/ch13-sar-trials-v2.svg" width="720" alt="逐位试探时保持输入不变；试 0.5：保留至试 0.6875：撤回。"></p>

**看点**：逐位试探时保持输入不变；试 0.5：保留至试 0.6875：撤回。→ 正文 [13.6 ADC](p2-03-ch13.md#ch13)

## 5.20 带隙基准：一正一负凑直线 <a id="demo20"></a>

<p align="center"><img src="assets/svg-v2/ch09-bandgap-balance-v2.svg" width="720" alt="带隙的一阶补偿，要把电流密度比算进去。先看 VBE：温度上升时，示意电压线性下降。ΔVBE=(kT/q)ln8，乘合适比例后斜率相反。令两条斜率相消，本例总电压为 1.2463 V。一阶平直不等于实际零漂；曲率、修调和应力另计。"></p>

**看点**：V_BE 随温度线性下降（25°C 约 0.65 V、斜率 −2 mV/°C），ΔV_BE=(kT/q)·lnN 反向爬坡；配好权重令两斜率相消，总电压 1.2463 V 一阶平直。注意一阶平直 ≠ 实际零漂：曲率、修调和应力另计。→ 正文 [9.1 带隙基准](p1-10-ch9.md#ch9)

## 5.21 TL431：自带标尺的比较器 <a id="demo21"></a>

<p align="center"><img src="assets/svg-v2/ch09-tl431-bias-v2.svg" width="720" alt="TL431 偏流流入 REF，输出误差是加号。REF 节点：上电阻电流等于下电阻电流加偏流。Vout=Vref(1+R1/R2)+Iref·R1，符号为正。各 10 kΩ 时输出为 5.020 V，不是 4.980 V。各 100 kΩ 时输出为 5.200 V；阻值上限由预算反推。"></p>

**看点**：别忘偏流 I_ref 流入 REF 节点，输出误差是**加号**：Vout=Vref(1+R1/R2)+I_ref·R1。各 10 kΩ 时输出 5.020 V（不是 4.980 V）；各 100 kΩ 时 5.200 V：阻值上限由误差预算反推，不是越大越好。→ 正文 [9.2 TL431](p1-10-ch9.md#ch9)

## 5.22 采样保持：给 SAR 按下暂停键 <a id="demo22"></a>

<p align="center"><img src="assets/svg-v2/ch08-sample-hold-v2.svg" width="720" alt="采样相追踪 2.000V、保持相冻结、漏流按 I/C 下斜、再采样；加大 Chold 同时摊注入、压 kT/C、缓 droop，代价是采集时间。"></p>

**看点**：采样相追踪输入（2.000 V），保持相冻结记忆；漏流按 I/C 匀速下斜（droop），再采样时重新追上。加大 C_hold 能同时摊平注入电荷、压低 kT/C 噪声、减缓 droop：代价是采集时间变长。→ 正文 [8.4 采样保持](p1-09-ch8.md#ch8)

## 5.23 电荷泵：电容斗提机 <a id="demo23"></a>

<p align="center"><img src="assets/svg-v2/ch13-pump-load-v2.svg" width="720" alt="飞跨电容的搬运速率限制带载电压；空载至负载 20 mA。"></p>

**看点**：飞跨电容的搬运速率限制带载电压；空载至负载 20 mA。→ 正文 [13.3 电荷泵](p2-03-ch13.md#ch13)

## 5.24 一阶 RC 低通与波特图 <a id="demo24"></a>

<p align="center"><img src="assets/svg/rc-lowpass.svg" width="720" alt="RC低通SVG动画"></p>

**看点**：fc 竖线恰好穿过 −3dB 交点；高频正弦进、缩小且滞后的绿波出，一颗极点的全部人生也就是 −20dB/dec 与最多 −90°。→ 正文 [12.5 有源滤波](p2-02-ch12.md#ch12)

## 5.25 齐纳稳压：电压溢流阀 <a id="demo25"></a>

<p align="center"><img src="assets/svg-v2/ch13-zener-budget-v2.svg" width="720" alt="先扣基流，再看齐纳管还能否稳压；空载至负载 500 mA。"></p>

**看点**：先扣基流，再看齐纳管还能否稳压；空载至负载 500 mA。→ 正文 [9.1 齐纳](p1-10-ch9.md#ch9)

## 5.26 恒流源：电压横扫，电流平躺 <a id="demo26"></a>

<p align="center"><img src="assets/svg-v2/ch13-current-compliance-v2.svg" width="720" alt="负载电压用尽余量后，电流再也保持不了；供电 2.8 V至回查输出级边界。"></p>

**看点**：负载电压用尽余量后，电流再也保持不了；供电 2.8 V至回查输出级边界。→ 正文 [13.5 恒流源](p2-03-ch13.md#ch13)

## 5.27 峰值检测：单向记忆 <a id="demo27"></a>

<p align="center"><img src="assets/svg/peak-detector.svg" width="720" alt="峰值检测SVG动画"></p>

**看点**：灰波创新高，绿线立刻跳上跟住；灰波回落，绿线平台守住，泄放电阻让它缓缓遗忘。只许上不许下，这就是峰值表和 AGC 的心脏。→ 正文 [12.6 峰值检测](p2-02-ch12.md#ch12)

## 5.28 反相 Buck-Boost：正进负出 <a id="demo28"></a>

<p align="center"><img src="assets/svg-v2/ch13-inverting-ratio-v2.svg" width="720" alt="反相 Buck-Boost 的极性来自放电连接；D=0.2至D=0.7。"></p>

**看点**：反相 Buck-Boost 的极性来自放电连接；D=0.2至D=0.7。→ 正文 [13.3 Buck-Boost](p2-03-ch13.md#ch13)

## 5.29 H 桥：电流听指挥掉头 <a id="demo29"></a>

<p align="center"><img src="assets/svg-v2/ch13-hbridge-reverse-v2.svg" width="720" alt="电压可以换向，电感电流必须连续；刚换向至负电流逐步建立。"></p>

**看点**：电压可以换向，电感电流必须连续；刚换向至负电流逐步建立。→ 正文 [13.7 H 桥](p2-03-ch13.md#ch13)

## 5.30 555 单稳态：一触发，亮一拍 <a id="demo30"></a>

<p align="center"><img src="assets/svg-v2/ch10-monostable-leakage-v2.svg" width="720" alt="漏电先拉长脉宽，过大时永远达不到上阈。无漏电，从零充到 6 V 的脉宽约 28.92 s。 漏电 1 µA，目标变为 8.44 V，脉宽约 32.66 s。 漏电继续增大，末段充电电流越来越小。 达到约 5.357 µA 时，目标不高于上阈，不再结束。 示意 9 V、R=560 kΩ、C=47 µF；恒流漏电流出电容节点。"></p>

**看点**：漏电先拉长脉宽，过大时永远达不到上阈。无漏电，从零充到 6 V 的脉宽约 28.92 s。漏电 1 µA，目标变为 8.44 V，脉宽约 32.66 s。漏电继续增大，末段充电电流越来越小。→ 正文 [10.5 单稳态](p1-11-ch10.md#ch10)

## 5.31 削波与钳位：闸门与垫脚石 <a id="demo31"></a>

<p align="center"><img src="assets/svg/clipper-clamper.svg" width="720" alt="削波钳位SVG动画"></p>

**看点**：左边红粒子从二极管闸门泄流削平顶底，右边绿粒子把 C 充成"串联电池"。同一个 0.7V，限幅动幅度、钳位动直流，一张图分清。→ 正文 [2.7 限幅与钳位](p1-03-ch2.md#ch2)

## 5.32 负反馈：十万倍的蛮力，被一根线驯成 6 倍 <a id="demo32"></a>

<p align="center"><img src="assets/svg/neg-feedback.svg" width="720" alt="负反馈SVG动画"></p>

**看点**：输出的一小份经反馈线"押"回反相端，把十万倍的开环蛮力驯成稳稳的 6 倍。输入输出波形完全重合，只差幅度。→ 正文 [12.1 方法论](p2-02-ch12.md#ch12)

## 5.33 积分器：方波换三角波 <a id="demo33"></a>

<p align="center"><img src="assets/svg-v2/ch12-integrator-cycle-v2.svg" width="720" alt="恒流改变斜率，初值决定直流中心。正输入产生负的输出斜率。初值零给出零到负五伏；零均值时应为正负二点五伏。"></p>

**看点**：恒流改变斜率，初值决定直流中心。正输入产生负的输出斜率。初值零给出零到负五伏；零均值时应为正负二点五伏。→ 正文 [12.4 积分器与微分器](p2-02-ch12.md#ch12)

## 5.34 单电源虚地：给信号造一个假地 <a id="demo34"></a>

<p align="center"><img src="assets/svg/virtual-ground.svg" width="720" alt="单电源虚地SVG动画"></p>

**看点**：两枚 10k 电阻分压造出 6V 中点，耦合电容把信号"骑"上 6V。灰信号撞地削平 vs 绿信号全程完好。→ 正文 [12.8 单电源运放](p2-02-ch12.md#ch12)

## 5.35 迟滞振荡器：方波自己弹出来 <a id="demo35"></a>

<p align="center"><img src="assets/svg/schmitt-osc.svg" width="720" alt="迟滞振荡器SVG动画"></p>

**看点**：Vc 在 ±3V 门槛间指数弹跳、比较器翻转不停，迟滞比较器加一根 RC，输出方波自动循环。→ 正文 [7.3 迟滞](p1-08-ch7.md#ch7)

## 5.36 阻抗随频率：电容降价、电感涨价 <a id="demo36"></a>

<p align="center"><img src="assets/svg/impedance-freq.svg" width="720" alt="阻抗随频率SVG动画"></p>

**看点**：橙色扫线从左到右扫频，蓝色 Zc 一路降、红色 Zl 一路升，5kHz 交点就是 LC 谐振；一枚电容的"身份"随频率而变。→ 正文 [1.3 真实电感](p1-02-ch1.md#ch1)

## 5.37 运放内部：三级流水线攒出 20 万倍 <a id="demo37"></a>

<p align="center"><img src="assets/svg/opamp-internals.svg" width="720" alt="运放内部框图SVG动画"></p>

**看点**：粒子从 IN 流到 OUT，即 ① 只认差模 ② 扛下全部增益（密勒补偿）③ 输出低阻，④ 偏置镜供水；每个 datasheet 参数都对得上位置。→ 正文 [6.1 解剖一只 741](p1-07-ch6.md#ch6)

## 5.38 排故五步法：把玄学拆成实验 <a id="demo38"></a>

<p align="center"><img src="assets/svg/debug-flow.svg" width="720" alt="排故五步法SVG动画"></p>

**看点**：橙框巡游五步、粒子沿流程走一圈，先问后拆、二分砍半、单变量、修根因、回归验证。→ 正文 [16.1 五步法详解](p4-01-ch16.md#ch16)

## 5.39 分压器：带载就塌的三分之一 <a id="demo39"></a>

<p align="center"><img src="assets/svg-v2/ch00-divider-loading-v2.svg" width="720" alt="空载 6.000V、挂 10kΩ 后 4.000V、误差 −33.3%；输出电阻 5kΩ，后级输入至少高一个数量级"></p>

**看点**：空载 6.000 V，挂上 10 kΩ 后跌到 4.000 V（误差 −33.3%）。分压公式只在空载时成立：输出电阻 5 kΩ 与后级输入阻抗分压，后级输入至少高一个数量级才算"没 load 垮"。→ 正文 [0.3 分压器](p1-01-ch0.md#ch0)

## 5.40 BJT 三个工作区：负载线切过哪里 <a id="demo40"></a>

<p align="center"><img src="assets/svg/bjt-regions.svg" width="720" alt="BJT三个工作区SVG动画"></p>

**看点**：紫色圆点沿负载线来回扫，左端饱和（β 失效）、中段放大、右端截止。→ 正文 [3.2 三个工作区](p1-04-ch3.md#ch3)

## 5.41 热失控：自己给自己加速的正反馈 <a id="demo41"></a>

<p align="center"><img src="assets/svg/thermal-runaway.svg" width="720" alt="BJT热失控SVG动画"></p>

**看点**：红色转圈箭头绕着四个环节越转越快，结点越烧越大。唯一的刹车是射极电阻。→ 正文 [3.7 热失控](p1-04-ch3.md#ch3)

## 5.42 PT100 信号链：把信号顶到接近满量程 <a id="demo42"></a>

<p align="center"><img src="assets/svg/signal-chain.svg" width="720" alt="PT100信号链全链SVG动画"></p>

**看点**：绿色粒子逐级流过四环，蓝色线代表放大后的 1.54V（满量程 75%）。贴地红线是"不放大就看不见"。→ 正文 [14.4 信号链实例](p3-01-ch14.md#ch14)

## 5.43 真实电容阻抗频谱：谷底定去耦 <a id="demo43"></a>

<p align="center"><img src="assets/svg/capacitor-parasitics.svg" width="720" alt="真实电容阻抗频谱SVG动画"></p>

**看点**：蓝线（100nF MLCC）谷底 0.3Ω@22.5MHz，灰线（10µF 电解）谷底 1Ω@356kHz；过了自谐振，电容就变成了电感。→ 正文 [1.2 真实电容](p1-02-ch1.md#ch1)

## 5.44 米勒平台：开通那 700ns 里最贵的 410ns <a id="demo44"></a>

<p align="center"><img src="assets/svg/miller-plateau.svg" width="720" alt="MOSFET米勒平台SVG动画"></p>

**看点**：四条波形同屏，$V_{GS}$ 在 2.9V 被钉住 160ns，$V_{DS}$ 猛跌，$P=V·I$ 只在重叠区鼓包。→ 正文 [4.3 米勒平台](p1-05-ch4.md#ch4)

## 5.45 运放阶跃：直线爬坡，不是指数 <a id="demo45"></a>

<p align="center"><img src="assets/svg/opamp-slew.svg" width="720" alt="运放阶跃响应SVG动画"></p>

**看点**：蓝色实线先做 2µs 直线爬坡，把总建立时间从灰色虚线（纯指数）的约 1.1µs 拖到 **2.6µs**。差的这 1.5µs 全是压摆率买的。→ 正文 [6.7 阶跃响应](p1-07-ch6.md#ch6)

## 5.46 二极管伏安特性：60mV 换十倍电流 <a id="demo46"></a>

<p align="center"><img src="assets/svg/diode-iv.svg" width="720" alt="二极管伏安特性SVG动画"></p>

**看点**：红蓝两条指数曲线，60°C 那条整条左移 70mV。测温、稳压、温度传感全靠这条曲线。→ 正文 [2.2 伏安特性](p1-03-ch2.md#ch2)

## 5.47 运放 vs 比较器：快的不一定能用 <a id="demo47"></a>

<p align="center"><img src="assets/svg/comparator-opamp.svg" width="720" alt="运放与比较器对比SVG动画"></p>

**看点**：绿色游标 1.3µs 直接跳变，蓝色 4µs 慢慢爬；坑在开集电极输出的 2.2ms 上升沿。→ 正文 [7.1 为什么不能混用](p1-08-ch7.md#ch7)

## 5.48 噪声三税种：不能消灭，只能谈判 <a id="demo48"></a>

<p align="center"><img src="assets/svg/noise-budget.svg" width="720" alt="噪声谱与噪声预算SVG动画"></p>

**看点**：BJT 与 MOSFET 的 1/f 拐角差一个量级；1kΩ·1MHz 折算 4.1µV，×1000 后就是 4.1mV。→ 正文 [11.6 噪声](p2-01-ch11.md#ch11)

## 5.49 探头是负载：测量本身在改电路 <a id="demo49"></a>

<p align="center"><img src="assets/svg/probe-loading.svg" width="720" alt="探头负载与测量安全SVG动画"></p>

**看点**：×1 探头在 100kΩ 节点上造成 9% 分压误差并把 f_c 压到 16kHz；另附电流档短路与地夹短路的两个「一按就出事」。→ 正文 [16.3 测量铁律](p4-01-ch16.md#ch16)

## 5.50 传输门：一只管子总有一段使不上劲 <a id="demo50"></a>

<p align="center"><img src="assets/svg-v2/ch08-transfer-gate-v2.svg" width="720" alt="同一横轴 VIN 与线性电阻刻度下，N 管在 4V 截止、P 管接管高段；并联包络为 20→26.7→20Ω，在 1~4V 为平台。末拍分开单 N 的阈值损失与并联传输门的 0~5V 摆幅，下游逻辑门限示例为 2.5V；双头箭头表示双向。"></p>

**看点**：N 管在 4 V 截止、P 管接管高段，单管总有一段使不上劲；并联包络 20→26.7→20 Ω，1~4 V 平坦平台就是「N 管送低、P 管送高」。末拍对比单 N 管的阈值损失与并联后 0~5 V 满摆幅，下游逻辑门限 2.5 V 下裕量充足。双头箭头表示双向。→ 正文 [8.1 传输门原理](p1-09-ch8.md#ch8)

## 5.51 三态总线：谁说话，谁闭嘴 <a id="demo51"></a>

<p align="center"><img src="assets/svg-v2/ch05-tristate-timing-v2.svg" width="720" alt="三态驱动条共用纳秒轴。旧器件最晚三十纳秒释放，新器件使能最小十纳秒；指令间隔五纳秒可重叠十五纳秒，间隔三十纳秒则留十纳秒空档。"></p>

**看点**：三态驱动条共用纳秒轴。旧器件最晚三十纳秒释放，新器件使能最小十纳秒；指令间隔五纳秒可重叠十五纳秒，间隔三十纳秒则留十纳秒空档。→ 正文 [5.4 三态与高阻](p1-06-ch5.md#ch5)

## 5.52 三种基本拓扑：同一只运放的三条路 <a id="demo52"></a>

<p align="center"><img src="assets/svg/three-topologies.svg" width="720" alt="三种基本拓扑对比SVG动画"></p>

**看点**：反相/同相/差分并排，同一组电阻比例都是 10 倍增益。差别只在输入阻抗、共模与服务代价。→ 正文 [12.2 三个基本拓扑](p2-02-ch12.md#ch12)

## 5.53 推挽输出级：直通电流从哪来 <a id="demo53"></a>

<p align="center"><img src="assets/svg/pushpull-stage.svg" width="720" alt="推挽输出级SVG动画"></p>

**看点**：上管供流/下管吸流两个方向都主动；两个推挽直连 = 100mA 短路，换班瞬间还有直通电流。→ 正文 [5.1 推挽输出](p1-06-ch5.md#ch5)

## 5.54 解剖 LM393：开集电极输出的三个红利 <a id="demo54"></a>

<p align="center"><img src="assets/svg/lm393-inside.svg" width="720" alt="LM393内部解剖SVG动画"></p>

**看点**：粒子从 PNP 输入级流到开集电极输出管；上拉接任意电压 → 电平转换，多路并联 → 线与。→ 正文 [7.2 解剖 LM393](p1-08-ch7.md#ch7)

## 5.55 齐纳 vs 带隙：两套温漂账 <a id="demo55"></a>

<p align="center"><img src="assets/svg/ref-showdown.svg" width="720" alt="齐纳与带隙对比SVG动画"></p>

**看点**：齐纳的抛物线温漂（5.6V 才触底）对带隙的平直线（3ppm/°C）；配比 K=2/0.177≈11.3 的来龙去脉。→ 正文 [9.1 齐纳 vs 带隙](p1-10-ch9.md#ch9)

## 5.56 PN 结：一堵会自己调节高度的墙 <a id="demo56"></a>

<p align="center"><img src="assets/svg/pn-junction.svg" width="720" alt="PN结形成SVG动画"></p>

**看点**：载流子扩散进耗尽层、电场把后来的往回推；三步（复合→建墙→平衡）就是内建电势的由来。→ 正文 [2.1 PN 结的形成](p1-03-ch2.md#ch2)

## 5.57 MOSFET 输出特性：饱和反而是放大区 <a id="demo57"></a>

<p align="center"><img src="assets/svg/mosfet-curves.svg" width="720" alt="MOSFET输出特性SVG动画"></p>

**看点**：四条曲线（四个 V_GS）+ 夹断点虚线；左边可变电阻、右边恒流源，别与 BJT 的"饱和"混淆。→ 正文 [4.2 输出特性](p1-05-ch4.md#ch4)

## 5.58 555 三种模式：同一颗芯三副面孔 <a id="demo58"></a>

<p align="center"><img src="assets/svg/555-modes.svg" width="720" alt="555三种模式SVG动画"></p>

**看点**：无稳态连续方波 / 单稳态一个脉冲 / 双稳态保持。差异只在电容接哪只脚。→ 正文 [10.2 三种模式](p1-11-ch10.md#ch10)

## 5.59 负反馈四种拓扑：稳定什么就采样什么 <a id="demo59"></a>

<p align="center"><img src="assets/svg/feedback-topo.svg" width="720" alt="负反馈四拓扑SVG动画"></p>

**看点**：2×2 四格卡片把四种拓扑的「钉死的量 / 受控源身份 / 阻抗走向」一次摊开。→ 正文 [12.7 负反馈四种拓扑](p2-02-ch12.md#ch12)

## 5.60 真实电阻：高频时它不再是「一个电阻」 <a id="demo60"></a>

<p align="center"><img src="assets/svg/resistor-model.svg" width="720" alt="真实电阻等效模型SVG动画"></p>

**看点**：理想 1kΩ 与真实电阻在 0.8GHz 前几乎重合、之后下坠到 1GHz 的 575Ω、3.6GHz 探底 ≈49Ω。再被引线电感拉回上升，两个寄生夺权点 f₁/f₂。→ 正文 [1.1 真实电阻](p1-02-ch1.md#ch1)

## 5.61 特殊二极管家族：压降与速度的地图 <a id="demo61"></a>

<p align="center"><img src="assets/svg/diode-family.svg" width="720" alt="特殊二极管家族SVG动画"></p>

**看点**：六族按「压降 × 速度」定位，肖特基左上、LED 下方、TVS 右上，位置即岗位。→ 正文 [2.4 特殊二极管](p1-03-ch2.md#ch2)

## 5.62 上拉电阻：4.7k 是怎么算出来的 <a id="demo62"></a>

<p align="center"><img src="assets/svg/pullup-sizing.svg" width="720" alt="上拉电阻取值SVG动画"></p>

**看点**：t_r≈0.8473·R·C 与 I=V/R 两条约束交叉出 4.7k；标准/快速模式的上限一目了然。→ 正文 [5.3 上拉与下拉](p1-06-ch5.md#ch5)

## 5.63 LM358：单电源双运放的两条边界 <a id="demo63"></a>

<p align="center"><img src="assets/svg/lm358-dual.svg" width="720" alt="LM358双运放SVG动画"></p>

**看点**：输入共模范围包含负轨，输出不是轨到轨；图中 3.5V 为示意，实际摆幅要按型号、负载和温度核对。→ [6.2 LM358 可控样板与实物接线](p1-07-ch6.md#lm358-study)

## 5.64 三种组态：一只管子的三种人生 <a id="demo64"></a>

<p align="center"><img src="assets/svg/bjt-configs.svg" width="720" alt="BJT三种组态SVG动画"></p>

**看点**：共射/共集/共基并排，增益、阻抗、相位、用途四行对照；级联心法收在末行。→ 正文 [11.1 三种组态](p2-01-ch11.md#ch11)

## 5.65 分立串联稳压：LDO 的祖爷爷 <a id="demo65"></a>

<p align="center"><img src="assets/svg-v2/ch09-dropout-ripple-v2.svg" width="720" alt="稳压余量看输入谷值，不只看平均值。输入为 3.5 V 加 0.2 V 正弦，平均值看似足够。 最高点 3.7 V，目标输出仍为 3.3 V。 输入谷值 3.3 V，扣去 0.15 V 压差只能输出 3.15 V。 谷值须覆盖输出加压差；实际还查动态 PSRR 与温度。 准静态示意：目标 3.3 V，负载 0.5 A，Ron=0.3 Ω，输入正弦 1 kHz。"></p>

**看点**：稳压余量看输入谷值，不只看平均值。输入为 3.5 V 加 0.2 V 正弦，平均值看似足够。最高点 3.7 V，目标输出仍为 3.3 V。输入谷值 3.3 V，扣去 0.15 V 压差只能输出 3.15 V。→ 正文 [13.1 分立串联稳压](p2-03-ch13.md#ch13)

## 5.66 BJT 放大原理：99% 的电子成了 I_C <a id="demo66"></a>

<p align="center"><img src="assets/svg/bjt-transport.svg" width="720" alt="BJT载流子输运SVG动画"></p>

**看点**：电子从发射区注入基区、绝大多数被集电结扫走，只有 1% 复合形成 I_B。这就是 β 的物理来源。→ 正文 [3.1 载流子输运](p1-04-ch3.md#ch3)

## 5.67 BJT 开关：Rb 怎么算、二极管为什么不能省 <a id="demo67"></a>

<p align="center"><img src="assets/svg/bjt-switch.svg" width="720" alt="BJT驱动继电器SVG动画"></p>

**看点**：强制 β=10 → I_B=7mA → R_B≈371Ω（就近取 360Ω）三步账；线圈反电动势与续流回路。→ 正文 [3.5 BJT 作开关](p1-04-ch3.md#ch3)

## 5.68 体二极管与栅极保护：MOS 的两条命门 <a id="demo68"></a>

<p align="center"><img src="assets/svg/body-diode.svg" width="720" alt="MOSFET体二极管SVG动画"></p>

**看点**：体二极管既是死区续流的功臣、也断了「反向阻断」的路；栅氧层 ±20V 的脆弱与防护。→ 正文 [4.4 体二极管](p1-05-ch4.md#ch4)

## 5.69 CD4051：八路传感器共用一个 ADC <a id="demo69"></a>

<p align="center"><img src="assets/svg/mux-4051.svg" width="720" alt="CD4051多路复用SVG动画"></p>

**看点**：3 位地址选 8 路、通道双向、切换时的电荷注入与 Ron 变化。→ 正文 [8.2 CD4066 与 CD4051](p1-09-ch8.md#ch8)

## 5.70 达林顿管：β 相乘与三笔代价 <a id="demo70"></a>

<p align="center"><img src="assets/svg/darlington.svg" width="720" alt="达林顿管SVG动画"></p>

**看点**：前级发射极电流就是后级基极电流；β≈β₁β₂ 换来的三笔代价：1.4V / 0.9V / 慢。→ 正文 [3.6 达林顿管](p1-04-ch3.md#ch3)

## 5.71 Datasheet 六参数优先级 <a id="demo71"></a>

<p align="center"><img src="assets/svg/datasheet-params.svg" width="720" alt="Datasheet六参数SVG动画"></p>

**看点**：六个参数按「会咬人」排序，每个都标出咬点与选型公式，五十页只读这六行。→ 正文 [6.3 Datasheet 参数](p1-07-ch6.md#ch6)

## 5.72 运放选型地图：速度 × 精度 <a id="demo72"></a>

<p align="center"><img src="assets/svg/opamp-map.svg" width="720" alt="运放选型地图SVG动画"></p>

**看点**：七款常见运放按 GBW 与 V_OS 定位，斩波零漂在最高精度区、741/LM358 在左下角。→ 正文 [6.4 常用运放选型](p1-07-ch6.md#ch6)

## 5.73 7805/AMS1117 四种翻车 <a id="demo73"></a>

<p align="center"><img src="assets/svg/ldo-failures.svg" width="720" alt="线性稳压故障地图SVG动画"></p>

**看点**：热账 2.1W、纹波谷值、ESR 振荡、上电过冲，四种死法的账都在图里。→ 正文 [9.4 7805/AMS1117 故障](p1-10-ch9.md#ch9)

## 5.74 BJT 在线速判：三个电压定故障 <a id="demo74"></a>

<p align="center"><img src="assets/svg/bjt-diagnosis.svg" width="720" alt="BJT在线速判SVG动画"></p>

**看点**：正常态两条判据 + 六种异常读数各自的故障定位与下一步动作。→ 正文 [3.8 BJT 故障速查](p1-04-ch3.md#ch3)

## 5.75 运放的六个经典坑 <a id="demo75"></a>

<p align="center"><img src="assets/svg/opamp-pitfalls.svg" width="720" alt="运放六个坑SVG动画"></p>

**看点**：按现场频率排序的六个坑；诊断顺序「输出电平 → 输入端压差 → 最后才怀疑运放」。→ 正文 [6.6 运放故障案例](p1-07-ch6.md#ch6)

## 5.76 比较器的五个坑：忘接上拉排第一 <a id="demo76"></a>

<p align="center"><img src="assets/svg/comparator-pitfalls.svg" width="720" alt="比较器五个坑SVG动画"></p>

**看点**：开集电极的两个后果（没上拉就没高电平 / 上拉位置决定电平）与三条红利。→ 正文 [7.4 比较器故障案例](p1-08-ch7.md#ch7)

## 5.77 555 参数与三个坑 <a id="demo77"></a>

<p align="center"><img src="assets/svg/ne555-params.svg" width="720" alt="555参数与三个坑SVG动画"></p>

**看点**：双极版 vs CMOS 版参数对照；5 脚为什么必须接 10nF、容性负载振荡、电源毛刺。→ 正文 [10.3 参数与故障](p1-11-ch10.md#ch10)

## 5.78 恒压源与恒流源：看 V-I 曲线认性格 <a id="demo78"></a>

<p align="center"><img src="assets/svg-v2/ch00-source-types-v2.svg" width="720" alt="横轴电流 I、纵轴电压 V：恒压源水平线、恒流源竖线；真实源负斜率的绝对值对应输出阻抗；恒压并联、恒流串联"></p>

**看点**：横轴 I、纵轴 V：水平线是恒压源，竖直线是恒流源；真实源负斜率的绝对值就是输出阻抗：越平越接近理想恒压。恒压源并联、恒流源串联。→ 正文 [0.6 恒压源与恒流源](p1-01-ch0.md#ch0)

## 5.79 戴维南与诺顿：两个数定性格 <a id="demo79"></a>

<p align="center"><img src="assets/svg/thevenin-norton.svg" width="720" alt="戴维南与诺顿等效SVG动画"></p>

**看点**：12V/10k/10k 网络 → V_th=6V、I_N=1.2mA、R_th=5kΩ；带载误差只看 R_th 与 R_L 之比。→ 正文 [1.4 戴维南与诺顿](p1-02-ch1.md#ch1)

## 5.80 恒流源的合规电压 <a id="demo80"></a>

<p align="center"><img src="assets/svg-v2/ch13-current-compliance-v2.svg" width="720" alt="负载电压用尽余量后，电流再也保持不了；供电 2.8 V至回查输出级边界。"></p>

**看点**：负载电压用尽余量后，电流再也保持不了；供电 2.8 V至回查输出级边界。→ 正文 [13.5 恒流源家族](p2-03-ch13.md#ch13)

## 5.81 共射放大器四拍：输入升、输出降 <a id="demo81"></a>

<p align="center"><img src="assets/svg/ce-dynamic.svg" width="720" alt="共射放大器四拍拆解SVG动画"></p>

**看点**：一个正弦周期拆成四拍；上行余量 6V、下行余量 4V → 对称摆幅 8.0Vpp；Q 点偏置就是「余量分配器」。→ 正文 [3.9 动态分析](p1-04-ch3.md#ch3)

## 5.82 MOSFET 开通四拍：栅极电荷如何变成热 <a id="demo82"></a>

<p align="center"><img src="assets/svg/mosfet-four-beats.svg" width="720" alt="MOSFET开通四拍SVG动画"></p>

**看点**：① 延时只充 $C_{GS}$；② $I_D$ 上升而 $V_{DS}$ 仍是 20V；③ $Q_{gd}=1.6nC$ 搬出 Miller 平台；④ 完全增强后只剩 0.75W 导通损耗。→ 正文 [4.6 动态分析](p1-05-ch4.md#ch4)

## 5.83 整流滤波电源四拍：从空电容到稳态纹波 <a id="demo83"></a>

<p align="center"><img src="assets/svg/rectifier-filter-beats.svg" width="720" alt="整流滤波电源四拍拆解SVG动画"></p>

**看点**：① 初始态电容放空；② 浪涌充电 10~50A；③ 稳态峰值充电 5~10A、导通角~20%；④ 谷值放电电容独供负载。→ 正文 [2.6 动态分析](p1-03-ch2.md#ch2)


## 5.84 模拟开关开合四拍：电荷注入如何毁掉采样精度 <a id="demo84"></a>

<p align="center"><img src="assets/svg/analog-switch-beats.svg" width="720" alt="模拟开关开合四拍拆解SVG动画"></p>

**看点**：① 栅极驱动开启、$R_{on}$→45Ω；② 沟道存 $Q_{ch}=0.2pC$；③ 关断注入 $\Delta V=10mV$（=20 LSB）；④ dummy 管反向抵消。→ 正文 [8.6 动态分析](p1-09-ch8.md#ch8)

**怎么看**：沿竖直时间游标同时看蓝色 $V_C$ 与紫色 EN 圆点；EN 在 8ms 变低时，$V_C$ 同时跳低 10mV。下方字幕切到「保持」，此后缓慢下垂是保持期的另一种误差。波形展示未补偿情况，第四张卡片说明 dummy 管的改进思路。

## 5.85 LDO 负载瞬态四拍：一次唤醒为何把 MCU 打到复位 <a id="demo85"></a>

<p align="center"><img src="assets/svg/ldo-transient-beats.svg" width="720" alt="LDO负载瞬态四拍拆解SVG动画"></p>

**看点**：① ESR 瞬跳 25mV；② 电容放电 245mV；③ 环路接管回升；④ 重新锁定（可能过冲）。总跌落 270mV ＞ 3.3V 复位阈值 165mV。→ 正文 [9.5 动态分析](p1-10-ch9.md#ch9)

**怎么看**：竖游标上的两点对应同一时刻。5µs 时负载电流跳高，输出先因 ESR 跳低；5–10µs 电容继续供电，10µs 后环路接管，30µs 后进入新的稳态。字幕随这四段切换；恢复曲线用于说明因果，实际过冲与恢复时间要看所选 LDO 和外围参数。

## 5.86 555 无稳态四拍：电容荡秋千，输出跳方波 <a id="demo86"></a>

<p align="center"><img src="assets/svg/555-astable-beats.svg" width="720" alt="555无稳态四拍拆解SVG动画"></p>

**看点**：① 上电 OUT 高；② 充电 541µs（走 R1+R2）；③ 放电 471µs（只走 R2）；④ 循环 → ≈990Hz、占空比 53%。→ 正文 [10.4 动态分析](p1-11-ch10.md#ch10)

**怎么看**：竖游标同时指向电容电压和 OUT，充到 6V 的那一刻 OUT 翻低，降回 3V 后下一周期 OUT 翻高。字幕同步显示充电或放电；下方波形是稳态周期，上方第一张卡片单独说明从 0V 开始的首次上电。

## 5.87 水路 = 电路：全书通用比喻 <a id="demo87"></a>

<p align="center"><img src="assets/svg/water-analogy.svg" width="720" alt="水路=电路通用比喻SVG动画"></p>

**看点**：环形水路走一圈，八个词一次记住：电压、电流、电阻、电容、电感、二极管、MOSFET、地。→ 正文 [0.1](p1-01-ch0.md#ch0)

## 5.88 树状供电：逐级净化 <a id="demo88"></a>

<p align="center"><img src="assets/svg/power-tree.svg" width="720" alt="树状供电逐级净化SVG动画"></p>

**看点**：输入 → 储能 → 稳压 → 去耦，每一级替下一级挡脏；去耦电容就近放。→ 正文 [14.3](p3-01-ch14.md#ch14)

## 5.89 电压降：同一股电流，谁 R 大谁分得多 <a id="demo89"></a>

<p align="center"><img src="assets/svg/voltage-drop.svg" width="720" alt="电压降SVG动画"></p>

**看点**：串联 4kΩ+1kΩ 分 5V，各得 4V/1V；右侧电压剖面把「竖降=跨电阻、横走=沿导线」画清楚。→ 正文 [0.2 欧姆定律](p1-01-ch0.md#ch0)

## 5.90 PCB 布线四招：45° 拐角 / 过孔 / 差分对 / 包地 <a id="demo90"></a>

<p align="center"><img src="assets/svg/pcb-routing.svg" width="720" alt="PCB布线四招SVG动画"></p>

**看点**：90° 尖角 vs 45° 折角、过孔 1nH+0.5pF、差分对等长紧邻、敏感线包地，四条规则的物理来源一屏看懂。→ 正文 [15.3 布线规则](p3-02-ch15.md#ch15)




## 5.91 故障速查：症状 → 嫌疑 → 验证 <a id="demo91"></a>

<p align="center"><img src="assets/svg/fault-lookup.svg" width="720" alt="故障速查SVG动画：症状→嫌疑→验证三列链路"></p>

**看点**：四类故障四条链路，粒子从症状流向头号嫌疑再到验证手段；底部紫色条是「不该振荡却振荡」的固定排查顺序。**先量电源，近一半故障出在电源上。** → 正文 [17.1 电源类](p4-02-ch17.md#ch17)

## 5.92 MOSFET 开关：沟道形成与导通 <a id="demo92"></a>

<p align="center"><img src="assets/svg/mosfet-switch.svg" width="720" alt="MOSFET 开关动画：沟道形成与导通"></p>

**看点**：$V_{GS}=0$ 两个背靠背 PN 结挡路；$V_{GS}>V_{TH}$ 栅极电场召唤电子形成 N 型沟道，S-D 导通，沟道电阻随 $V_{GS}$ 连续可调。**电压控制，不取栅流。** → 正文 [4.1 沟道形成原理](p1-05-ch4.md#ch4)

## 5.93 反相放大器：虚短虚断 <a id="demo93"></a>

<p align="center"><img src="assets/svg/opamp-inverting.svg" width="720" alt="反相放大器动画：虚短虚断"></p>

**看点**：$V_+≈V_-$ 与输入端不取电流，两条公理把五个拓扑变成五个"不用背的形状"。**先讲清公理凭什么成立，再看电路。** → 正文 [6.5 经典应用电路原理](p1-07-ch6.md#ch6)

## 5.94 模拟开关：电荷注入 <a id="demo94"></a>

<p align="center"><img src="assets/svg/analog-switch.svg" width="720" alt="模拟开关动画：电荷注入"></p>

**看点**：关断瞬间沟道里攒的电荷"无家可归"，被挤进保持电容。$ΔV=Q/C$ 是采样电路里最隐蔽的误差源（Charge Injection）。**别在 ADC 转换中途切通道。** → 正文 [8.3 关键参数解析](p1-09-ch8.md#ch8)

## 5.95 LDO 负反馈：闭环控制 <a id="demo95"></a>

<p align="center"><img src="assets/svg/ldo-feedback.svg" width="720" alt="LDO负反馈动画"></p>

**看点**：LDO 不是"稳压元件"而是闭环控制系统，误差放大器每秒纠正几千次。**输出电容 ESR 为什么能把它逼疯（环路稳定性），一眼看懂。** → 正文 [9.3 LDO 线性稳压器剖析](p1-10-ch9.md#ch9)

## 5.96 去耦电容：本地水库 <a id="demo96"></a>

<p align="center"><img src="assets/svg/cap-decoupling.svg" width="720" alt="去耦电容动画：贴脸放的真正原因"></p>

**看点**：去耦电容不是"滤波"而是**本地水库**。ns 级电流尖峰面前，10cm 走线电感就是断路。**"100nF 贴脸 <3mm"不是建议，是铁律。** → 正文 [15.1 布局](p3-02-ch15.md#ch15)

## 5.97 大师的排故智慧：三份心法，一条军规 <a id="demo97"></a>

<p align="center"><img src="assets/svg/master-wisdom.svg" width="720" alt="大师排故智慧SVG动画：三份心法一条军规"></p>

**看点**：Pease（先量电源/怀疑仪器）、Williams（预测波形/最小化复现）、共通（慢观察/快假设/严验证）三栏金句；底部军规条粒子链。**排故不是体力活，是科学方法。** → 正文 [18.1 Bob Pease](p4-03-ch18.md#ch18)

## 5.98 从需求到打样：六步流程 <a id="demo98"></a>

<p align="center"><img src="assets/svg/design-flow.svg" width="720" alt="从需求到打样六步流程SVG动画：一链加回炉回环"></p>

**看点**：需求指标 → 拓扑选择 → 器件选型 → 仿真验证 → 降额与保护 → 打样测试六步一链，粒子从头走到尾；仿真不过沿橙色回环回炉。**流程是螺旋不是直线。** → 正文 [14.1 设计流程](p3-01-ch14.md#ch14)

## 5.99 思维工具箱：四暗器 <a id="demo99"></a>

<p align="center"><img src="assets/svg/thinking-toolbox.svg" width="720" alt="思维工具箱SVG动画：四暗器何时用"></p>

**看点**：内外归因 / 对比法 / 极限法 / 隔离法四色卡片，粒子沿外框环绕；「何时用」一行小字。**先内外、再对比、极限逼、隔离切。** → 正文 [16.2 思维工具箱](p4-01-ch16.md#ch16)

## 5.100 一点接地：让大电流别踩小信号的路 <a id="demo100"></a>

<p align="center"><img src="assets/svg/ground-star.svg" width="720" alt="一点接地SVG动画：共用地线vs星形接地"></p>

**看点**：左红「共用地线」负载地与信号地共用一段 AB，10A×0.01Ω=100mV 压降踩进信号基准；右绿「星形一点接地」各自到汇点互不污染。**地不是"0V 参考点"，是电流回家的路。** → 正文 [15.2 接地](p3-02-ch15.md#ch15)

## 5.101 变压器：电压换电流 <a id="demo101"></a>

<p align="center"><img src="assets/svg/transformer.svg" width="720" alt="变压器SVG动画：电压换电流"></p>

**看点**：变比 1:2 升压，紫色磁通粒子沿磁芯搬能量，红/绿电流粒子同步进出；电压翻倍处电流减半。**初次级只有磁通耦合，没有导线相连。** → 正文 [1.3 真实电感与变压器](p1-02-ch1.md#ch1)

## 5.102 排故决策树：从「上电无反应」到具体表项 <a id="demo102"></a>

<p align="center"><img src="assets/svg/diagnosis-tree.svg" width="720" alt="排故决策树SVG动画：从「上电无反应」一路走到具体表项"></p>

**看点**：决策脊柱一路向下，「输入电压？」「电源轨？」「复位/时钟？」每问一个「否」就横向落到一张速查表（17.1/17.3）；四问皆「是」却功能异常，则按表现分四叶，即完全不动→17.3、读数不对→17.2、时好时坏→17.6→17.4、发热异常→17.5。**先定方向、再查细节，顺序本身就是方法论。** → 正文 [17.8 分诊决策树](p4-02-ch17.md#ch17)

## 5.103 电容直流偏压：标称容量 ≠ 工作容量 <a id="demo103"></a>

<p align="center"><img src="assets/svg/cap-derating.svg" width="720" alt="电容直流偏压降容教学动画：5V 时 10µF × 26% = 2.6µF"></p>

**看点**：圆点匀速扫过偏压轴，红线和 5V 工作点来自同一组教学数据；假设保持率为 26%，10µF 就变为 2.6µF，同纹波电流且忽略 ESR 时容性纹波增至约 3.85 倍。**曲线不是实测值，X5R/X7R 也不是降容等级**；C0G 仅作归一化参考。→ 正文 [1.7 电容直流偏压降容](p1-02-ch1.md#cap-dc-bias)

## 5.104 运放输入级选型：源阻抗决定一切 <a id="demo104"></a>

<p align="center"><img src="assets/svg/opamp-input-stage.svg" width="720" alt="运放输入级选型教学动画：BJT / CMOS / JFET 按源阻抗分工"></p>

**看点**：三张卡片摊开 $I_b$、$e_n$、$i_n$，下面的横轴按**源阻抗**分段，低阻段比的是 $e_n$（BJT 赢 1.7 倍）。高阻段比的是 $I_b\cdot R_s$（1MΩ 下 BJT 20mV vs CMOS 1µV，**差四个数量级**）。**别看"低噪声"三个字，先看源阻抗。** → 正文 [12.13 运放输入级的三种口味](p2-02-ch12.md#sec1213)

## 5.105 晶体振荡器：Pierce 拓扑与负阻判据 <a id="demo105"></a>

<p align="center"><img src="assets/svg/crystal-pierce.svg" width="720" alt="晶体振荡器教学动画：Pierce 拓扑 + 负载电容 + 负阻判据"></p>

**看点**：左边把 Pierce 拓扑的四个元件各司其职画清楚（$R_f$ 偏置、晶体选频、$C_1/C_2$ 定 $C_L$）；右边给出唯一必须算的数 $C_L=C_1C_2/(C_1+C_2)+C_{stray}$，还有**起振判据 $R_{neg}\ge5\times ESR$**。32.768kHz 只要 **1.7 µA/V** 的跨导，这就是 RTC 能把功耗做到 µA 级的根因。→ 正文 [13.10 晶体振荡器](p2-03-ch13.md#sec1310)

## 5.106 光耦与隔离：CTR 是设计变量 <a id="demo106"></a>

<p align="center"><img src="assets/svg/optocoupler-ctr.svg" width="720" alt="光耦隔离教学动画：LED + 隔离栅 + 光敏三极管，CTR 的三个坑"></p>

**看点**：橙色光粒子穿过 kV 级隔离栅，**信号能过、电流不能过**；右边列出 CTR 的三个坑（同型号分档 50%~600%、随温与时间衰减、小电流非线性）。结论是**按档位最小值 × 2 倍老化余量**反算驱动电流（$R_{in}$ 从 1kΩ 改 470Ω）。→ 正文 [13.11 光耦与隔离](p2-03-ch13.md#sec1311)

## 5.107 误差预算：最坏情况 vs 统计叠加 <a id="demo107"></a>

<p align="center"><img src="assets/svg/error-budget.svg" width="720" alt="误差预算教学动画：WC ±2.7% 与 3σ ±1.35% 的对比"></p>

**看点**：左侧把 Buck 反馈分压的四项误差逐条列成预算表。右侧把 WC 与 3σ 画成两条同心带，**3σ 大约只有 WC 的一半**；再用 $2\Phi(k)-1$ 折良率，即规格 ±1% 时约 **97.5%**，每千块 25 块超规。→ 正文 [14.8 原型到量产 DFM/DFT](p3-01-ch14.md#sec148)

## 5.108 探头地线环：量到的纹波可能是假的 <a id="demo108"></a>

<p align="center"><img src="assets/svg/probe-ground-loop.svg" width="720" alt="探头地线环教学动画：长地线夹 vs 弹簧地针"></p>

**看点**：左右对照，**长地线夹**在探头与远端地之间围出一个大环路；开关电源的磁场在里面感应出假的 200mV 纹波。换成**弹簧地针**，环路面积缩十倍以上，读数立刻干净。**排故时先怀疑测量，再怀疑电路。** → 正文 [14.8 原型到量产 DFM/DFT](p3-01-ch14.md#sec148)

## 5.109 分压公式四步推导：I 先算出来，再乘下臂电阻 <a id="demo109"></a>

<p align="center"><img src="assets/svg/derive-divider.svg" width="720" alt="分压公式四步推导动画：串联电流、欧姆定律、代换、代入数字"></p>

**看点**：左边电路随拍点亮、右边算式逐行推进，游标按拍指向下框「此刻推到哪一行」。**串联同流 → 欧姆定律 → 代入消去 I → 只剩电阻比**，最后一步代 12V 与两只 10kΩ 验证 6V。**公式不是背下来的，是三步推出来的**；同一个式子换成 R2=5k 就是 4V。→ 正文 [0.3 分压器](p1-01-ch0.md#sec-0-3)

## 5.110 纹波公式五步推导：电荷 → 电压 → 整流补几次 <a id="demo110"></a>

<p align="center"><img src="assets/svg/derive-ripple.svg" width="720" alt="纹波公式五步推导动画：电荷账、电容定义、代换、整流补两次、代入数字"></p>

**看点**：$Q=I\cdot\Delta t$ 是账本，$\Delta V=Q/C$ 是水桶，合起来 $\Delta V=I\cdot\Delta t/C$；全波整流每周期补两次水，于是 $\Delta t=1/(2f)$，公式里凭空出现的那个 **2** 就是这么来的。代 1A、50Hz、4700µF 得 2.1V。**每个量都有出处**。→ 正文 [2.3 整流与滤波](p1-03-ch2.md#sec-2-3)

## 5.111 共射增益五步推导：gm 变电流，Rc 变回电压 <a id="demo111"></a>

<p align="center"><img src="assets/svg/derive-gain.svg" width="720" alt="共射增益五步推导动画：跨导定义、室温数值、电流转电压、串成增益、代入数字"></p>

**看点**：$g_m=\Delta I_c/\Delta V_{be}$ 把输入电压抖成电流，$\Delta V_{out}=-\Delta I_c R_c$ 再把它抖回电压：**负号是「电流涨、Rc 压降涨、输出跌」推出来的**，不是约定。左图输入正弦经 gm 盒、Rc 出来倒过来了，一眼可见。代 38mS×2kΩ ≈ −76（37.6dB）。→ 正文 [11.8 有源负载与共源共栅](p2-01-ch11.md#sec-11-8)

## 5.112 负反馈增益六步推导：从 Vout = A·Vd 到 Af ≈ 1/β <a id="demo112"></a>

<p align="center"><img src="assets/svg/derive-feedback.svg" width="720" alt="负反馈增益六步推导动画：开环、采样、净输入、联立、求商、深反馈极限"></p>

**看点**：开环 → 采样 → 净输入 → 联立 → 移项求商，六步落到 $A_f=A/(1+A\beta)$；再让 $A\beta\gg1$，得到 **$A_f\approx1/\beta$**：增益只由电阻比决定，与 A 无关。**这就是「虚短」的定量版本**：A 越大，输入端压差越趋近于零。→ 正文 [6 运算放大器](p1-07-ch6.md#ch6)

## 5.113 米勒电容六步推导：10pF 为什么看起来像 1nF <a id="demo113"></a>

<p align="center"><img src="assets/svg/derive-miller.svg" width="720" alt="米勒电容六步推导动画：跨接电容被增益撬大"></p>

**看点**：Cbc 一头挂输入、一头挂输出，输出反相摆 −A·Δv，于是电容两端往相反方向跑、压差被撬成 $(1+A)\cdot\Delta v$；充同一份电荷，输入源要多搬 (1+A) 倍：**等效电容就这么被放大**。代 10pF 与 A=100 得 1.01nF，与 10kΩ 源阻一配，低通拐点只剩 15.8kHz。**增益换带宽，是同一只电容在收账**。→ 正文 [11.5 频率响应与米勒效应](p2-01-ch11.md#sec-11-5)

## 5.114 降压纹波六步推导：那个 8 是三角波的面积 <a id="demo114"></a>

<p align="center"><img src="assets/svg-v2/ch13-buck-cycle-v2.svg" width="720" alt="同一电感电流，开关与二极管轮流接管；导通初段至周期回到谷值。"></p>

**看点**：同一电感电流，开关与二极管轮流接管；导通初段至周期回到谷值。→ 正文 [13.2 Buck 降压](p2-03-ch13.md#sec-13-2)

## 5.115 预测对实测：对不上的地方才是线索 <a id="demo115"></a>

<p align="center"><img src="assets/svg/predict-measure.svg" width="720" alt="预测对实测动画：纸上预测曲线与示波器实测曲线对照，偏差超线即停手改模型"></p>

**看点**：左蓝右红两条 RC 充电曲线：左边是下探头前写在纸上的预测（100kΩ×1µF，2.5V 阈值 @ 69ms），右边是实测（140ms，或 1τ 只读 2.2V）。终值减半加 τ 减半，两条线索同指节点上的 ~100kΩ 漏电阻。**超 20% 对账线就停手改模型，继续测只是给错误的模型收集噪声。** → 正文 [18.2 Jim Williams](p4-03-ch18.md#sec-18-2)

## 5.116 间歇故障：先逼它现身，再在窗口里等它 <a id="demo116"></a>

<p align="center"><img src="assets/svg/intermittent-forcing.svg" width="720" alt="间歇故障逼迫流程动画：机械热电三把扳手轮番上阵，复现率从一天一次逼到按一下就坏"></p>

**看点**：机械（按压扭转轻敲）、热（冷冻喷剂热风枪）、电（电压拉偏负载阶跃）三把扳手轮流入漏斗，每把单独用、记录哪把改变复现率；复现率从「一天一次」逼到「按一下就坏」后，单次/毛刺/欠幅触发挂着等。**蜂鸣档一声断续，抵得上十分钟盯屏。** → 正文 [17.6 间歇性故障](p4-02-ch17.md#sec-17-6)

## 5.117 地弹：8 路同翻，把"地"弹起来 <a id="demo117"></a>

<p align="center"><img src="assets/svg-v2/ch05-ground-bounce-v2.svg" width="720" alt="同一时间轴的总回流和地电压。五纳亨共用电感上，八路共一百六十毫安在两纳秒内上升产生零点四伏，单路零点零五伏；恒流段理想电感压降为零。"></p>

**看点**：8 路同翻（每路 20 mA、共 160 mA）在 2 ns 内挤过 5 nH 共用地电感，L·di/dt 顶出 0.4 V 地弹（单路折算 0.05 V），没翻转的那路输出照样跟着抖；恒流段理想电感压降为零，尖峰只在边沿。**对策：大电流翻转分散开、地脚多给几只、低速信号别配高档驱动。** → 正文 [5.1 推挽输出](p1-06-ch5.md#sec-5-1)

## 5.118 三触点对账：160mV 去了哪里 <a id="demo118"></a>

<p align="center"><img src="assets/svg/three-probe-audit.svg" width="720" alt="三触点对账动画：LDO 输出脚 5.02V、运放 VCC 脚 4.86V、去耦电容复核，160mV 折算 1.3Ω 路径电阻"></p>

**看点**：探头依次点向稳压器输出脚（5.02V）、运放 VCC 脚（4.86V）、去耦电容两端复核，160mV 差值 ÷ 120mA 负载 ≈ 1.3Ω 路径电阻：0.2mm×200mm 细走线约 1000 个方 ≈ 0.5Ω，再叠过孔与接插件。**病灶在走线，不在芯片。** → 正文 [18.1 Bob Pease：模拟排故的「老中医」](p4-03-ch18.md#sec-18-1)

## 旁注：Falstad 内置示例地图（全部带动画）

| 主题 | 菜单路径 |
|---|---|
| 欧姆定律/分压 | Circuits → Basics |
| RC/RLC 暂态与谐振 | Circuits → Basics → RLC |
| 二极管整流全家桶 | Circuits → Diodes |
| 晶体管放大器 | Circuits → Transistors |
| 运放全家桶（跟随/反相/积分/滤波） | Circuits → Op-Amps |
| 555 系列 | Circuits → 555 Timer Chip |
| 开关电源 Buck/Boost | Circuits → Power Converters |

---

## 5.119 源的两次测量法：内阻一笔算出（失效边界） <a id="demo119"></a>

<p align="center"><img src="assets/svg-v2/ch00-divider-loading-v2.svg" width="720" alt="空载 6.000V、挂 10kΩ 后 4.000V、误差 −33.3%；输出电阻 5kΩ，后级输入至少高一个数量级"></p>

**看点**：空载 6.000V、挂 10kΩ 后 4.000V、误差 −33.3%；输出电阻 5kΩ，后级输入至少高一个数量级。→ 正文 [0.6 恒压源与恒流源](p1-01-ch0.md#sec-0-6)


## 5.120 单位错档一千倍：数量级先钉死 <a id="demo120"></a>

<p align="center"><img src="assets/svg/exp-unit-guard.svg" width="720" alt="单位错档一千倍：数量级先钉死动画：四步节拍推导"></p>

**看点**：左侧图元随拍点亮、右侧算式逐行推进；每一步的数字都能回对正文。→ 正文 [0.7 量纲与数量级](p1-01-ch0.md#sec-0-7)


## 5.121 额定功率的降额链：标称值怎么缩水 <a id="demo121"></a>

<p align="center"><img src="assets/svg/exp-derate-chain.svg" width="720" alt="额定功率的降额链：标称值怎么缩水动画：四步节拍推导"></p>

**看点**：左侧图元随拍点亮、右侧算式逐行推进；每一步的数字都能回对正文。→ 正文 [0.9 功率与降额](p1-01-ch0.md#sec-0-9)


## 5.122 纹波的两本账：容性与 ESR 谁说了算 <a id="demo122"></a>

<p align="center"><img src="assets/svg-v2/ch17-esr-sweep.svg" width="720" alt="ESR 从 0.1Ω 扫到 3Ω（扫描端点为示意值）——先问纹波频率，再问幅度"></p>

**看点**：ESR 从 0.1Ω 扫到 3Ω（扫描端点为示意值）：先问纹波频率，再问幅度。→ 正文 [1.2 ESR 与纹波](p1-02-ch1.md#ch1)


## 5.123 电解电容寿命账：10°C 翻倍（失效边界） <a id="demo123"></a>

<p align="center"><img src="assets/svg/exp-cap-life.svg" width="720" alt="电解电容寿命账：10°C 翻倍（失效边界）动画：四步节拍推导"></p>

**看点**：左侧图元随拍点亮、右侧算式逐行推进；每一步的数字都能回对正文。→ 正文 [1.7 寿命公式](p1-02-ch1.md#cap-dc-bias)


## 5.124 感性负载的关断尖峰：电感物理的必然推论 <a id="demo124"></a>

<p align="center"><img src="assets/svg/exp-avalanche-edge.svg" width="720" alt="感性负载的关断尖峰：电感物理的必然推论动画：四步节拍推导"></p>

**看点**：左侧图元随拍点亮、右侧算式逐行推进；每一步的数字都能回对正文。→ 正文 [1.3 反电动势](p1-02-ch1.md#ch1)


## 5.125 导通角与峰值电流：窄窗里的猛冲 <a id="demo125"></a>

<p align="center"><img src="assets/svg-v2/ch02-charge-window-v2.svg" width="720" alt="相同坐标轴上的三种电流：1 安负载持续 10 毫秒耗电 10 毫库；3 毫秒矩形脉冲平均 3.3 安，三角脉冲峰值 6.7 安，两者补回同一份电荷。示意脉形，不能替代实际整流仿真。"></p>

**看点**：相同坐标轴上的三种电流：1 安负载持续 10 毫秒耗电 10 毫库；3 毫秒矩形脉冲平均 3.3 安，三角脉冲峰值 6.7 安，两者补回同一份电荷。示意脉形，不能替代实际整流仿真。→ 正文 [2.6 导通角](p1-03-ch2.md#ch2)


## 5.126 接口防护三级削减：TVS → 电阻 → 钳位 <a id="demo126"></a>

<p align="center"><img src="assets/svg/exp-tvs-ladder.svg" width="720" alt="接口防护三级削减：TVS → 电阻 → 钳位动画：四步节拍推导"></p>

**看点**：左侧图元随拍点亮、右侧算式逐行推进；每一步的数字都能回对正文。→ 正文 [2.11 例 2-2](p1-03-ch2.md#ch2)


## 5.127 β 漂移冲击工作点：偏置的失效边界 <a id="demo127"></a>

<p align="center"><img src="assets/svg-v2/ch11-beta-budget-v2.svg" width="720" alt="标称通过后，还要重算 β 与偏置。β=100，输入电阻约 8.76 kΩ，低于目标。 β=150 时输入电阻恢复，但还需看其他指标。 β=200 标称输入电阻约 13.13 kΩ。 β=300 输入电阻更高，带宽却下降；不能只挑一个指标。 修订候选按正文完整偏置模型，扫共同 β；温度与器件电容未扫描。"></p>

**看点**：标称通过后，还要重算 β 与偏置。β=100，输入电阻约 8.76 kΩ，低于目标。β=150 时输入电阻恢复，但还需看其他指标。β=200 标称输入电阻约 13.13 kΩ。β=300 输入电阻更高，带宽却下降。→ 正文 [3.4 分压偏置](p1-04-ch3.md#ch3)


## 5.128 热失控：一条闭合的正反馈环（失效边界） <a id="demo128"></a>

<p align="center"><img src="assets/svg/exp-thermal-loop.svg" width="720" alt="热失控：一条闭合的正反馈环（失效边界）动画：四步节拍推导"></p>

**看点**：左侧图元随拍点亮、右侧算式逐行推进；每一步的数字都能回对正文。→ 正文 [3.7 热失控](p1-04-ch3.md#ch3)


## 5.129 米勒平台的栅电荷账：驱动电流是挤压器 <a id="demo129"></a>

<p align="center"><img src="assets/svg-v2/ch04-gate-power-v2.svg" width="720" alt="每周期七纳库栅电荷，一百千赫时平均供电零点七毫安；十伏、十欧回路初始峰值约一安；平均驱动功率七毫瓦，分布在驱动器及栅极回路中，不全在 MOSFET 内。"></p>

**看点**：每周期七纳库栅电荷，一百千赫时平均供电零点七毫安；十伏、十欧回路初始峰值约一安；平均驱动功率七毫瓦，分布在驱动器及栅极回路中，不全在 MOSFET 内。→ 正文 [4.3 与 4.6 平台与四拍](p1-05-ch4.md#ch4)


## 5.130 上拉取值：上升沿与功耗的双边权衡 <a id="demo130"></a>

<p align="center"><img src="assets/svg-v2/ch05-pullup-window-v2.svg" width="720" alt="同一电阻坐标轴上求灌电流下限和上升时间上限的交集。三点三伏、一百皮法可取九百六十七至三千五百四十一欧；四百皮法时上限八百八十五欧，区间为空。"></p>

**看点**：同一电阻坐标轴上求灌电流下限和上升时间上限的交集。三点三伏、一百皮法可取九百六十七至三千五百四十一欧；四百皮法时上限八百八十五欧，区间为空。→ 正文 [5.3 上拉取值](p1-06-ch5.md#ch5)


## 5.131 直通窗口与死区：换向瞬间谁在岗 <a id="demo131"></a>

<p align="center"><img src="assets/svg-v2/ch04-deadtime-energy-v2.svg" width="720" alt="十微秒周期内两段死区各五十纳秒，体二极管承受零点八伏、五安；每周期零点四微焦，乘一百千赫为零点零四瓦，即四十毫瓦。放大的单次换流图标明独立尺度。"></p>

**看点**：十微秒周期内两段死区各五十纳秒，体二极管承受零点八伏、五安；每周期零点四微焦，乘一百千赫为零点零四瓦，即四十毫瓦。放大的单次换流图标明独立尺度。→ 正文 [5.1 推挽直通](p1-06-ch5.md#ch5)


## 5.132 增益带宽交换：GBW 是一笔守恒的预算 <a id="demo132"></a>

<p align="center"><img src="assets/svg/exp-gbw-swap.svg" width="720" alt="增益带宽交换：GBW 是一笔守恒的预算动画：四步节拍推导"></p>

**看点**：左侧图元随拍点亮、右侧算式逐行推进；每一步的数字都能回对正文。→ 正文 [6.3 GBW](p1-07-ch6.md#ch6)


## 5.133 压摆率墙：大信号的失效边界 <a id="demo133"></a>

<p align="center"><img src="assets/svg-v2/ch06-speed-envelope-v2.svg" width="720" alt="小信号幅频与大信号斜率分别核算。小信号闭环极点 7 kHz，直流增益 100。 10 kHz 增益约 57.35，已经明显衰减。 若要求输出仍达 5 V 峰值，另算正弦最大斜率。 15.9 kHz 时所需斜率达到 SR；供电摆幅也须满足。 独立教学参数 GBW 0.7 MHz、NG 100、SR 0.5 V/µs、Vp 5 V。"></p>

**看点**：小信号幅频与大信号斜率分别核算。小信号闭环极点 7 kHz，直流增益 100。10 kHz 增益约 57.35，已经明显衰减。若要求输出仍达 5 V 峰值，另算正弦最大斜率。15.9 kHz 时所需斜率达到 SR。→ 正文 [6.7 压摆率](p1-07-ch6.md#ch6)


## 5.134 迟滞窗口：抗噪护城河的宽与窄 <a id="demo134"></a>

<p align="center"><img src="assets/svg-v2/ch07-hysteresis-timing-v2.svg" width="720" alt="相对中点的延时，只跨半个对称窗口。无迟滞参考门限 2.5 V，输入在 200 s 到达。 迟滞上阈值 2.727 V，在约 427.3 s 才翻转。 相对 2.5 V 的推迟是 227.3 s，不是 454.5 s。 只有拿下阈值作起点，时间差才对应整个窗口。 初态输出高；输入由 2.3 V 以 1 mV/s 上行，忽略传播与 RC 延迟。"></p>

**看点**：相对中点的延时，只跨半个对称窗口。无迟滞参考门限 2.5 V，输入在 200 s 到达。迟滞上阈值 2.727 V，在约 427.3 s 才翻转。相对 2.5 V 的推迟是 227.3 s，不是 454.5 s。→ 正文 [7.3 迟滞](p1-08-ch7.md#ch7)


## 5.135 判决延迟预算：运放兼职的代价 <a id="demo135"></a>

<p align="center"><img src="assets/svg-v2/ch07-release-timing-v2.svg" width="720" alt="响应时间的终点，先看手册怎样定义。输出管在示意的 1 µs 释放，随后才按 RC 上升。 越过 1.4 V 约在 1.077 µs；不同于 50% 终点。 50% 约 1.163 µs，70% 约 1.283 µs。 10%→90% 耗 0.516 µs；不能重复加进已测响应。 独立 RC 示意：5 V、4.7 kΩ、50 pF，1 µs 时输出管释放。"></p>

**看点**：响应时间的终点，先看手册怎样定义。输出管在示意的 1 µs 释放，随后才按 RC 上升。越过 1.4 V 约在 1.077 µs；不同于 50% 终点。50% 约 1.163 µs，70% 约 1.283 µs。→ 正文 [7.5 延迟账](p1-08-ch7.md#ch7)


## 5.136 电荷注入的信号相关性：从台阶到谐波 <a id="demo136"></a>

<p align="center"><img src="assets/svg-v2/ch08-charge-injection-v2.svg" width="720" alt="沟道电荷 0.2pC 在关断瞬间分成源侧与 Chold 两路；一半落到 10pF 得 10mV，即 2.048V/12 位的 20 个 LSB。"></p>

**看点**：沟道电荷 0.2pC 在关断瞬间分成源侧与 Chold 两路；一半落到 10pF 得 10mV，即 2.048V/12 位的 20 个 LSB。→ 正文 [8.3 注入分账](p1-09-ch8.md#ch8)


## 5.137 采样保持的 droop 预算：时间维度的税 <a id="demo137"></a>

<p align="center"><img src="assets/svg-v2/ch08-sample-hold-v2.svg" width="720" alt="采样相追踪 2.000V、保持相冻结、漏流按 I/C 下斜、再采样；加大 Chold 同时摊注入、压 kT/C、缓 droop，代价是采集时间。"></p>

**看点**：采样相追踪 2.000V、保持相冻结、漏流按 I/C 下斜、再采样；加大 Chold 同时摊注入、压 kT/C、缓 droop，代价是采集时间。→ 正文 [8.4 端到端例](p1-09-ch8.md#ch8)


## 5.138 LDO 换料的隐性账：ESR 零点与稳定（失效边界） <a id="demo138"></a>

<p align="center"><img src="assets/svg/exp-ldo-zero.svg" width="720" alt="LDO 换料的隐性账：ESR 零点与稳定（失效边界）动画：四步节拍推导"></p>

**看点**：左侧图元随拍点亮、右侧算式逐行推进；每一步的数字都能回对正文。→ 正文 [9.3 稳定性](p1-10-ch9.md#ch9)


## 5.139 PSRR 随频率滚降：电源抑制是分段防守 <a id="demo139"></a>

<p align="center"><img src="assets/svg-v2/ch11-psrr-ripple-v2.svg" width="720" alt="同样的纹波，抑制比随频率变化。100 Hz 的 80 dB 抑制把纹波折为 10 µVrms。 1 kHz 仍在本例的低频平台。 100 kHz 已降到 40 dB，输入等效纹波为 1 mVrms。 1 MHz 时为 20 dB；不能拿 DC 数字外推。 示意电源纹波 100 mVrms；PSRR 在 1 kHz 前 80 dB，随后每十倍频降 20 dB。"></p>

**看点**：同样的纹波，抑制比随频率变化。100 Hz 的 80 dB 抑制把纹波折为 10 µVrms。1 kHz 仍在本例的低频平台。100 kHz 已降到 40 dB，输入等效纹波为 1 mVrms。→ 正文 [9.3 PSRR](p1-10-ch9.md#ch9)


## 5.140 单稳态触发链：一触发，亮一拍 <a id="demo140"></a>

<p align="center"><img src="assets/svg-v2/ch10-monostable-leakage-v2.svg" width="720" alt="漏电先拉长脉宽，过大时永远达不到上阈。无漏电，从零充到 6 V 的脉宽约 28.92 s。 漏电 1 µA，目标变为 8.44 V，脉宽约 32.66 s。 漏电继续增大，末段充电电流越来越小。 达到约 5.357 µA 时，目标不高于上阈，不再结束。 示意 9 V、R=560 kΩ、C=47 µF；恒流漏电流出电容节点。"></p>

**看点**：漏电先拉长脉宽，过大时永远达不到上阈。无漏电，从零充到 6 V 的脉宽约 28.92 s。漏电 1 µA，目标变为 8.44 V，脉宽约 32.66 s。漏电继续增大，末段充电电流越来越小。→ 正文 [10.5 单稳态](p1-11-ch10.md#ch10)


## 5.141 555 占空比：充放两条路各管一段 <a id="demo141"></a>

<p align="center"><img src="assets/svg-v2/ch10-diode-duty-v2.svg" width="720" alt="二极管有压降，等电阻也不等于 50%。理想二极管绕过 RB，等电阻给出对称充放时间。 VF=0.3 V 时，充电目标降到 4.7 V，高段变长。 VF=0.6 V 时，门限仍不变，充电目标只有 4.4 V。 这段扫描中二极管一直导通；压降更大需分段求解。 示意 5 V、RA=RB=10 kΩ、C=100 nF；VD=0、恒定 VF。"></p>

**看点**：二极管有压降，等电阻也不等于 50%。理想二极管绕过 RB，等电阻给出对称充放时间。VF=0.3 V 时，充电目标降到 4.7 V，高段变长。VF=0.6 V 时，门限仍不变，充电目标只有 4.4 V。→ 正文 [10.2 三种模式](p1-11-ch10.md#ch10)


## 5.142 米勒倍增：一只电容被增益放大 <a id="demo142"></a>

<p align="center"><img src="assets/svg-v2/ch11-miller-charge-v2.svg" width="720" alt="电荷随两端压差变化，电容本身没变。A=0，电容输出端固定，电荷只随输入变化。 A=10，输出反相，电容两端摆幅增加。 A=50，同一输入需搬运更多电荷。 A=100，等效输入电容为 1.01 nF。 示意 Cbc=10 pF；输入 ±1 mV，输出增益为 −A；低频电压增益近似。"></p>

**看点**：电荷随两端压差变化，电容本身没变。A=0，电容输出端固定，电荷只随输入变化。A=10，输出反相，电容两端摆幅增加。A=50，同一输入需搬运更多电荷。A=100，等效输入电容为 1.01 nF。示意 Cbc=10 pF。→ 正文 [11.5 米勒效应](p2-01-ch11.md#ch11)


## 5.143 噪声三税：一张预算表收口 <a id="demo143"></a>

<p align="center"><img src="assets/svg-v2/ch11-noise-bandwidth-v2.svg" width="720" alt="截止频率之外的噪声仍在积分。积分到 fH，只收齐全部白噪声均方值的一半。 到 2fH，累计约 70.48%。 到 5fH，仍未收齐高频尾部。 积分到无穷才得到等效噪声带宽 πfH/2。 示意白噪声经过一阶低通，fH 为 −3 dB 点；按均方值累计。"></p>

**看点**：截止频率之外的噪声仍在积分。积分到 fH，只收齐全部白噪声均方值的一半。到 2fH，累计约 70.48%。到 5fH，仍未收齐高频尾部。积分到无穷才得到等效噪声带宽 πfH/2。→ 正文 [11.6 噪声预算](p2-01-ch11.md#ch11)


## 5.144 积分器漂移与泄放电阻（失效边界） <a id="demo144"></a>

<p align="center"><img src="assets/svg-v2/ch12-leaky-integrator-v2.svg" width="720" alt="泄放把无限 DC 增益变成有限平台。低频输出趋向有限的负一百倍。虚线是理想积分幅值，高频真实环路仍有限制。"></p>

**看点**：泄放把无限 DC 增益变成有限平台。低频输出趋向有限的负一百倍。虚线是理想积分幅值，高频真实环路仍有限制。→ 正文 [12.4 与 12.11 积分器](p2-02-ch12.md#ch12)


## 5.145 容性负载自激与隔离电阻（失效边界） <a id="demo145"></a>

<p align="center"><img src="assets/svg-v2/ch12-riso-step-v2.svg" width="720" alt="隔离电阻前后取反馈，阶跃不同。无隔离电阻，输出强烈振铃但最终收敛。移到电阻之后取反馈会失去零点，振铃更大。"></p>

**看点**：隔离电阻前后取反馈，阶跃不同。无隔离电阻，输出强烈振铃但最终收敛。移到电阻之后取反馈会失去零点，振铃更大。→ 正文 [12.9 稳定性实战](p2-02-ch12.md#ch12)


## 5.146 伏秒平衡：电感稳态的入场券 <a id="demo146"></a>

<p align="center"><img src="assets/svg-v2/ch13-buck-cycle-v2.svg" width="720" alt="同一电感电流，开关与二极管轮流接管；导通初段至周期回到谷值。"></p>

**看点**：同一电感电流，开关与二极管轮流接管；导通初段至周期回到谷值。→ 正文 [13.2 Buck](p2-03-ch13.md#ch13)


## 5.147 晶振牵引灵敏度：3pF 偏差值多少秒 <a id="demo147"></a>

<p align="center"><img src="assets/svg-v2/ch13-crystal-pull-v2.svg" width="720" alt="大步长负载偏移要直接算两个谐振频率；CL=12 pF至CL=15 pF。"></p>

**看点**：大步长负载偏移要直接算两个谐振频率；CL 从 12 pF 扫到 15 pF。→ 正文 [13.10 晶振](p2-03-ch13.md#ch13)


## 5.148 最坏情况 vs RSS：误差预算的两把尺 <a id="demo148"></a>

<p align="center"><img src="assets/svg/exp-wc-rss.svg" width="720" alt="最坏情况 vs RSS：误差预算的两把尺动画：四步节拍推导"></p>

**看点**：左侧图元随拍点亮、右侧算式逐行推进；每一步的数字都能回对正文。→ 正文 [14.10 WC/RSS](p3-01-ch14.md#ch14)


## 5.149 回流路径被割断：开槽的代价（失效边界） <a id="demo149"></a>

<p align="center"><img src="assets/svg/exp-return-cut.svg" width="720" alt="回流路径被割断：开槽的代价（失效边界）动画：四步节拍推导"></p>

**看点**：左侧图元随拍点亮、右侧算式逐行推进；每一步的数字都能回对正文。→ 正文 [15.2 与 15.7 回流](p3-02-ch15.md#ch15)


## 5.150 叠层与阻抗：同一只 50Ω 两种命运 <a id="demo150"></a>

<p align="center"><img src="assets/svg/exp-via-stack.svg" width="720" alt="叠层与阻抗：同一只 50Ω 两种命运动画：四步节拍推导"></p>

**看点**：左侧图元随拍点亮、右侧算式逐行推进；每一步的数字都能回对正文。→ 正文 [15.3 叠层](p3-02-ch15.md#ch15)


## 5.151 二分定位的对数数学：6 节点 3 刀 <a id="demo151"></a>

<p align="center"><img src="assets/svg/exp-log2-split.svg" width="720" alt="二分定位的对数数学：6 节点 3 刀动画：四步节拍推导"></p>

**看点**：左侧图元随拍点亮、右侧算式逐行推进；每一步的数字都能回对正文。→ 正文 [16.1 二分](p4-01-ch16.md#ch16)


## 5.152 接触电阻蠕变：只量通断会漏掉的漂移窗（失效边界） <a id="demo152"></a>

<p align="center"><img src="assets/svg/exp-contact-creep.svg" width="720" alt="接触电阻蠕变：只量通断会漏掉的漂移窗（失效边界）动画：四步节拍推导"></p>

**看点**：左侧图元随拍点亮、右侧算式逐行推进；每一步的数字都能回对正文。→ 正文 [17.6 焊接连接](p4-02-ch17.md#ch17)


## 5.153 1-10-100 成本法则：把故障往左推 <a id="demo153"></a>

<p align="center"><img src="assets/svg/exp-cost-ladder.svg" width="720" alt="1-10-100 成本法则：把故障往左推动画：四步节拍推导"></p>

**看点**：左侧图元随拍点亮、右侧算式逐行推进；每一步的数字都能回对正文。→ 正文 [18.4 评审四闸](p4-03-ch18.md#ch18)

