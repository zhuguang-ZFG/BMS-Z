<a id="part9"></a>
# 第九篇：自测与练习

> 看完不等于会。这 19 组章节题共 90 问（第 0、11、14 章各 10 问，第 2、16 章各 9 问，其余章节 3~4 问）是给"我以为我懂了"准备的体检表；
> 文末另附 **34 道专题加练**，覆盖 v3.21~v3.23 新增的 LC 谐振四拍 / 相位裕度与极点分裂 / 噪声预算 / Sallen-Key 理论 / 开关电容；
> 同批新增的还有量化噪声与 ENOB / TIA / 电流检测 / 功放 / 热设计 / LTspice / 排故记录 / 设计评审与六节四拍动态分析；
> v3.28 再补六组：**§1.7 直流偏压降容与介质地图、§12.13 运放输入级三口味、§13.10 晶体振荡器、§13.11 光耦与隔离；§14.8 可制造性与可测试性、§16.5 排故实战三案例**。
> **用法**：先盖住答案在纸上算，算完再展开对答案；错一题就回对应章节把那一段重读一遍。
> 章节题用于定位需要复习的概念，专题题用于加练；答对题不等同于具备独立设计能力。接着选一个 [里程碑项目](p8-03-s8-3.md)，用仿真、接线和实测验证理解。
>
> **打印复习稿**：在线站按 Ctrl/⌘+P，19 章与文末专题组各从新页开始，长组可续页；打印版会显示答案，适合对照复习，不是隐藏答案的试卷。先在预览里选需要的页码。

| 章节题答对数（共 90 题，专题题另计） | 建议下一步 |
|---|---|
| 70~90 题 | 复习错题，再选符合自己基础的项目验证；不作为能力认证 |
| 47~69 题 | 补做错题对应章节的「算一笔」 |
| 0~46 题 | 按 [三条时间线](p0-03-timeline.md) 回顾基础，优先补错题集中的章节 |

---

<a id="quiz-ch0"></a>
## 第 0 章 电路直觉学前班

> 还不知道从哪章测起？先做 3 分钟 [入场诊断](p0-09-diagnostic.md#diagnostic) 定路线。

[← 返回第 0 章复习](p1-01-ch0.md#ch0) · [卡住先查公式：速查表·直流基础](p0-08-cheatsheet.md#dc)

1. <a id="q-ch0-01" data-quiz-question="true"></a>12V 电源串 3kΩ（上臂）与 6kΩ（下臂）分压，空载输出是多少？在下臂并联一个 6kΩ 负载后又变成多少？

    <details markdown="1">
    <summary>答案</summary>

    空载 8V（12×6/9）；并 6kΩ 后下臂等效变成 3kΩ → 12×3/6 = **6V**，塌陷 25%。这就是"带载就塌"。见 [0.3 分压器](p1-01-ch0.md#sec-0-3)。

    </details>

2. <a id="q-ch0-02" data-quiz-question="true"></a>「地」到底是什么？为什么说它不是下水道？

    <details markdown="1">
    <summary>答案</summary>

    地是**人为选定的电压参考点**，所有"某点电压"都是相对它的差值；它同时也是回流路径的一部分，电流真的从里面流，所以它既有参考意义又有物理意义。当它是回流路径时，它上面的阻抗会产生真实压降（共阻抗耦合）。见 [0.4](p1-01-ch0.md#sec-0-4)。

    </details>

3. <a id="q-ch0-03" data-quiz-question="true"></a>理想恒压源与恒流源的内阻分别是多少？现实里的近似物是啥？

    <details markdown="1">
    <summary>答案</summary>

    恒压源内阻 **0**（输出电压不随负载变），恒流源内阻 **∞**（输出电流不随负载变）。近似：稳压电源/大电容 ≈ 恒压源；电流镜/电感中的储能电流 ≈ 恒流源。见 [0.6](p1-01-ch0.md#sec-0-6)。

    </details>

4. <a id="q-ch0-04" data-quiz-question="true"></a>10kΩ 电阻与 100µF 电容组成 RC 电路，时间常数是多少？请用基本单位算一遍。

    <details markdown="1">
    <summary>答案</summary>

    $\tau=RC=10^4\,\Omega\times100\times10^{-6}\,\text{F}=10^4\times10^{-4}=1\,\text{s}$。先把 kΩ 换成 $10^4\,\Omega$、µF 换成 $10^{-4}\,\text{F}$，再相乘；单位是秒。见 [0.7](p1-01-ch0.md#sec-0-7)。

    </details>

5. <a id="q-ch0-05" data-quiz-question="true"></a>12V 加在 1kΩ、1/4W 电阻上，功耗多少？按 50% 降额，这只电阻合格吗？应该换多大？

    <details markdown="1">
    <summary>答案</summary>

    $I=12\text{V}/1\text{k}\Omega=12\,\text{mA}$，$P=12\times0.012=144\,\text{mW}$。1/4W 的 50% 降额限值是 125mW，144mW 超限，**不合格**；换 1/2W（降额后 250mW，144mW 占 57.6%）才合格。见 [0.9](p1-01-ch0.md#sec-0-9)。

    </details>

6. <a id="q-ch0-06" data-quiz-question="true"></a>一只 VCCS 的跨导为 2mS，控制电压 1V，输出接 3kΩ 负载。输出电流和负载电压各是多少？

    <details markdown="1">
    <summary>答案</summary>

    $I_{out}=g_mV_{in}=2\,\text{mS}\times1\,\text{V}=2\,\text{mA}$；负载电压 $2\,\text{mA}\times3\,\text{k}\Omega=6\,\text{V}$。注意输出电压 6V 由负载决定，换负载电压就变。见 [0.8](p1-01-ch0.md#sec-0-8)。

    </details>

7. <a id="q-ch0-07" data-quiz-question="true"></a>一段地线电阻 0.1Ω，流过 1A 电流，两端产生多大压差？这对毫伏级测量意味着什么？

    <details markdown="1">
    <summary>答案</summary>

    $V=IR=1\,\text{A}\times0.1\,\Omega=0.1\,\text{V}=100\,\text{mV}$。如果模拟电路以这段地线为参考，100mV 的误差足以淹没毫伏级信号；大电流回路与小信号回路要分开走地，最后单点汇合。见 [0.4](p1-01-ch0.md#sec-0-4)。

    </details>

8. <a id="q-ch0-08" data-quiz-question="true"></a>5V 电源内阻 50Ω，接 1kΩ 负载，负载上的实际电压是多少？

    <details markdown="1">
    <summary>答案</summary>

    负载与内阻串联分压：$V_L=5\times1\text{k}/(1\text{k}+50)=4.76\,\text{V}$。内阻只占 5%，却吃掉了 0.24V；负载越重，塌得越多。见 [0.6](p1-01-ch0.md#sec-0-6)。

    </details>

9. <a id="q-ch0-09" data-quiz-question="true"></a>9V、500mAh 电池供 10mA 负载，理想续航多少小时？按 80% 可用容量呢？

    <details markdown="1">
    <summary>答案</summary>

    理想：$500\,\text{mAh}/10\,\text{mA}=50\,\text{h}$；按 80% 可用容量：$50\times0.8=40\,\text{h}$。电池容量是电荷量，算能量还要乘电压：$9\times0.5=4.5\,\text{Wh}$。见 [0.9](p1-01-ch0.md#sec-0-9)。

    </details>

10. <a id="q-ch0-10" data-quiz-question="true"></a>从 0.10 节的十个误区里任选一个，说明它错在哪个隐含假设，以及你会用什么测量或计算动作纠正它。

    <details markdown="1">
    <summary>答案</summary>

    示例：选"分压公式永远成立"。隐含假设是后级负载无穷大；纠正动作是先算分压器输出电阻 $R_1\parallel R_2$，再与负载比较，必要时实测带载后的输出。其他误区只要点出隐含假设并给出可执行的检查动作即可。见 [0.10](p1-01-ch0.md#sec-0-10)。

    </details>

<a id="quiz-ch1"></a>
## 第 1 章 无源元件

[← 返回第 1 章复习](p1-02-ch1.md#ch1) · [卡住先查公式：速查表·无源与频域](p0-08-cheatsheet.md#passive)

1. <a id="q-ch1-01" data-quiz-question="true"></a>10µF 电解电容在 1MHz 为什么"不像电容"？

    <details markdown="1">
    <summary>答案</summary>

    自谐振频率（通常 0.1~1MHz）以上 **ESL 接管**，阻抗随频率上升，它变成了电感。所以高频去耦要靠小容量陶瓷电容并联，见 [1.2](p1-02-ch1.md#sec-1-2)。

    </details>

2. <a id="q-ch1-02" data-quiz-question="true"></a>真实电阻的高频等效模型是什么？三个元件分别在什么频率段说话？

    <details markdown="1">
    <summary>答案</summary>

    $j\omega L + (R \parallel C)$：低频是 R；中频并联电容 C 让阻抗略降；高频引线电感 L 接管、阻抗回升。见 [1.1](p1-02-ch1.md#sec-1-1)。

    </details>

3. <a id="q-ch1-03" data-quiz-question="true"></a>品质因数 Q 怎么定义？Q 越高越好吗？

    <details markdown="1">
    <summary>答案</summary>

    $Q = f_c/BW$（也等于谐振时电抗/电阻）。Q 高 = 选频尖锐、损耗小，但带宽窄、对元件容差敏感、瞬态 ringing 更久——**Q 高不等于更好**，见 [1.5](p1-02-ch1.md#sec-1-5)。

    </details>

<a id="quiz-ch2"></a>
## 第 2 章 二极管

[← 返回第 2 章复习](p1-03-ch2.md#ch2) · [卡住先查公式：速查表·二极管](p0-08-cheatsheet.md#diode)

1. <a id="q-ch2-01" data-quiz-question="true"></a>室温下硅二极管电流增大 10 倍，正向压降变化多少？

    <details markdown="1">
    <summary>答案</summary>

    约 **60mV**（一个 decade 对应 $nV_T \ln 10$，n≈1 时 60mV）。这是"60mV 换十倍电流"的由来，见 [2.2](p1-03-ch2.md#sec-2-2)。

    </details>

2. <a id="q-ch2-02" data-quiz-question="true"></a>12V 交流经桥式整流 + 4700µF 滤波、1A 负载，纹波峰峰值大概多少？

    <details markdown="1">
    <summary>答案</summary>

    $\Delta V \approx I/(2fC) = 1/(2\times50\times4700\mu) \approx$ **2.1Vpp**（全波整流纹波频率 100Hz）。见 [2.6 四拍拆解](p1-03-ch2.md#sec-2-6)。

    </details>

3. <a id="q-ch2-03" data-quiz-question="true"></a>限幅与钳位的本质区别是什么？

    <details markdown="1">
    <summary>答案</summary>

    **限幅动幅度**（削掉超过门限的部分），**钳位动直流分量**（整条波形被垫高/压低，形状不变）。同一个 0.7V，一个是闸门一个是垫脚石。见 [2.7](p1-03-ch2.md#sec-2-7)。

    </details>

4. <a id="q-ch2-04" data-quiz-question="true"></a>接口保护为什么"TVS 必须贴着接口放"？

    <details markdown="1">
    <summary>答案</summary>

    引线电感在 ns 级 ESD 前沿上会抬升钳位电压（1nH 在 1A/ns 下就是 1V），离接口 8cm 的 TVS 形同虚设。见 [2.8](p1-03-ch2.md#sec28)。

    </details>

5. <a id="q-ch2-05" data-quiz-question="true"></a>硅二极管的正向压降温度系数约 −2 mV/°C，结温升高 60°C 时，同样电流下的正向压降变化多少？

    <details markdown="1">
    <summary>答案</summary>

    约 **−120 mV**（$ -2\text{ mV/°C}\times60\text{°C}$）。压降随温度升高而下降，所以不能用“恒压 0.7V”模型算高温工作点；同理，温度传感器和热失控都从这条系数来。见 [2.9.1](p1-03-ch2.md#sec-2-9-1)。

    </details>

6. <a id="q-ch2-06" data-quiz-question="true"></a>把一只 5.1 V 稳压管直接并在 12 V 电源两端，会发生什么？正确接法是什么？

    <details markdown="1">
    <summary>答案</summary>

    直接并在 12 V 上会瞬间流过很大的击穿电流，稳压管过热损坏，电源也可能被拖垮。正确接法是串限流电阻（或恒流源），让击穿电流落在额定范围，例如 $R=(12-5.1)/I_Z$，同时校核 $P_Z=V_Z I_Z$。击穿本身可逆，**没有限流就不可逆**。见 [2.9.2](p1-03-ch2.md#sec-2-9-2)。

    </details>

7. <a id="q-ch2-07" data-quiz-question="true"></a>全波整流、1 A 负载、纹波频率 100 Hz，要求纹波峰峰值不超过 1 V，滤波电容至少多大？

    <details markdown="1">
    <summary>答案</summary>

    $C \ge I/(2f\Delta V)=1/(2\times50\times1)=\mathbf{10\,000\ \mu F}$。还要选耐压至少为峰值电压 1.5 倍以上、纹波电流额定足够的电容；容量够但 ESR 太大，纹波仍会超标。见 [2.10.2](p1-03-ch2.md#sec-2-10-2)。

    </details>

8. <a id="q-ch2-08" data-quiz-question="true"></a>5 V 信号口的 TVS，$V_{RWM}$、$V_C$ 和 $I_{PP}$ 各看什么？为什么 $V_C$ 常常大于芯片绝对最大值？

    <details markdown="1">
    <summary>答案</summary>

    $V_{RWM}$ 要高于正常信号峰值（如 5.5 V），否则正常信号就被钳；$V_C$ 是在规定浪涌电流下的钳位电压，要结合后级限流电阻/钳位二极管一起看；$I_{PP}$ 与 $P_{PP}$ 要覆盖目标浪涌波形（ESD 与 8/20 µs 不能混用）。TVS 在大电流下钳到 9~15 V 很常见，**它负责泄放大能量，残压靠电阻和芯片内部钳位压到毫安级**。见 [2.11](p1-03-ch2.md#sec-2-11)。

    </details>

9. <a id="q-ch2-09" data-quiz-question="true"></a>一只二极管通过 1 A 平均电流，正向压降 0.9 V，$R_{\theta JA}=40$ °C/W，环境 40°C，结温多少？

    <details markdown="1">
    <summary>答案</summary>

    $P=1\times0.9=0.9\text{ W}$，$T_j=40+0.9\times40=\mathbf{76°C}$。若封装热阻更大、或环境温度更高，结温会迅速逼近 125°C/150°C 上限；桥堆里多只二极管共用散热路径，还要按总损耗重新算。见 [2.12.3](p1-03-ch2.md#sec-2-12-3)。

    </details>

<a id="quiz-ch3"></a>
## 第 3 章 BJT

[← 返回第 3 章复习](p1-04-ch3.md#ch3) · [卡住先查公式：速查表·BJT](p0-08-cheatsheet.md#bjt)

1. <a id="q-ch3-01" data-quiz-question="true"></a>判断 BJT 三个工作区，看什么？

    <details markdown="1">
    <summary>答案</summary>

    看两个 PN 结偏置：**放大**=发射结正偏/集电结反偏；**饱和**=都正偏（$V_{CE}\approx0.1\sim0.3V$）；**截止**=都反偏。见 [3.2](p1-04-ch3.md#sec-3-2)。

    </details>

2. <a id="q-ch3-02" data-quiz-question="true"></a>为什么必须用分压偏置而不是单电阻基极偏置？

    <details markdown="1">
    <summary>答案</summary>

    单电阻偏置的 $I_C$ 正比于 β，而 β 在同类器件间能差 3 倍、随温度漂移；分压偏置 + $R_E$ 负反馈让工作点由电阻比决定，**与 β 基本脱钩**。见 [3.4](p1-04-ch3.md#sec-3-4)。

    </details>

3. <a id="q-ch3-03" data-quiz-question="true"></a>热失控的正反馈链条怎么写？

    <details markdown="1">
    <summary>答案</summary>

    $T\uparrow \Rightarrow V_{BE}\downarrow(-2mV/°C) \Rightarrow I_C\uparrow \Rightarrow P\uparrow \Rightarrow T\uparrow$，闭环增益 >1 就跑飞。破解：$R_E$ 负反馈、散热、温度补偿。见 [3.7](p1-04-ch3.md#sec-3-7)。

    </details>

<a id="quiz-ch4"></a>
## 第 4 章 MOSFET

[← 返回第 4 章复习](p1-05-ch4.md#ch4) · [卡住先查公式：速查表·MOSFET](p0-08-cheatsheet.md#mos)

1. <a id="q-ch4-01" data-quiz-question="true"></a>米勒平台期间 MOSFET 工作在哪个区？为什么这是"最贵的几百纳秒"？

    <details markdown="1">
    <summary>答案</summary>

    **不能把整个平台都叫欧姆区**。感性负载硬开通时，平台主要处于器件的饱和/有源区，接近结束才转向欧姆区；功率器件资料也把高耗散放大状态称为 linear mode。此时 $V_{DS}$ 下降而 $I_D$ 约为负载电流，电压电流同时大，开关损耗集中在平台期间。见 [4.3](p1-05-ch4.md#sec-4-3) / [4.6](p1-05-ch4.md#sec-4-6)。

    </details>

2. <a id="q-ch4-02" data-quiz-question="true"></a>栅极为什么绝不能悬空？

    <details markdown="1">
    <summary>答案</summary>

    栅氧仅几十 nm、耐压通常 **±20V**，而栅极输入电阻近乎 ∞：感应电荷/ESD 无泄放路径，直接击穿。未用栅极要下拉。见 [4.4](p1-05-ch4.md#sec-4-4)。

    </details>

3. <a id="q-ch4-03" data-quiz-question="true"></a>体二极管在什么场合是"救命"的，什么场合是"麻烦"的？

    <details markdown="1">
    <summary>答案</summary>

    救命：感性负载续流、H 桥死区期间的电流通路；麻烦：它不能快恢复，桥式/同步整流中反向恢复带来损耗与尖峰。见 [4.4](p1-05-ch4.md#sec-4-4)。

    </details>

<a id="quiz-ch5"></a>
## 第 5 章 推挽与开漏

[← 返回第 5 章复习](p1-06-ch5.md#ch5) · [卡住先查公式：速查表·输出级](p0-08-cheatsheet.md#outstage)

1. <a id="q-ch5-01" data-quiz-question="true"></a>I²C 为什么规定开漏 + 上拉？

    <details markdown="1">
    <summary>答案</summary>

    **线与**：任何设备都能把总线拉低，谁都不拉时上拉为高。这样天然实现多主仲裁与时钟同步，且不打架（推挽会因一高一低直通）。见 [5.2](p1-06-ch5.md#sec-5-2)。

    </details>

2. <a id="q-ch5-02" data-quiz-question="true"></a>上拉电阻 4.7kΩ 是怎么权衡出来的？

    <details markdown="1">
    <summary>答案</summary>

    下限由灌电流决定 $R \ge (V_{DD}-V_{OL})/I_{OL}$（3.3V/3mA → ≥1.1kΩ）；上限由上升时间决定 $t_r \approx 0.847RC$，400pF 满载时 4.7k 给 1.6µs（超过标准模式 1µs 上限）→ 长总线要降到 2.2kΩ；短板子 4.7k 是速度与功耗的折中。见 [5.3](p1-06-ch5.md#sec-5-3)。

    </details>

3. <a id="q-ch5-03" data-quiz-question="true"></a>推挽输出上下管同时导通叫什么？怎么防？

    <details markdown="1">
    <summary>答案</summary>

    **直通 / shoot-through**：电源到地的低阻通路，瞬间大电流。靠**死区时间**（先关后开）与栅极驱动时序防。见 [5.1](p1-06-ch5.md#sec-5-1) / [13.7](p2-03-ch13.md#sec-13-7)。

    </details>

<a id="quiz-ch6"></a>
## 第 6 章 运算放大器

[← 返回第 6 章复习](p1-07-ch6.md#ch6) · [卡住先查公式：速查表·运放](p0-08-cheatsheet.md#opamp)

1. <a id="q-ch6-01" data-quiz-question="true"></a>「虚短虚断」成立的前提是什么？

    <details markdown="1">
    <summary>答案</summary>

    **深负反馈 + 开环增益足够大**（$A_{OL}\beta \gg 1$）。开环、正反馈、比较器状态下都不成立。见 [12.1](p2-02-ch12.md#sec-12-1)。

    </details>

2. <a id="q-ch6-02" data-quiz-question="true"></a>GBW = 1MHz 的运放做 100 倍同相放大，-3dB 带宽是多少？

    <details markdown="1">
    <summary>答案</summary>

    **10kHz**（增益带宽积为常数：$f_{-3dB}=GBW/G$）。见 [6.3](p1-07-ch6.md#sec-6-3)。

    </details>

3. <a id="q-ch6-03" data-quiz-question="true"></a>压摆率 0.5V/µs 的运放输出 10V 阶跃，最快需要多久？还缺什么参数？

    <details markdown="1">
    <summary>答案</summary>

    $t = 10V / 0.5V/µs =$ **20µs**（还可能有线性建立段）；工程上还要看**建立时间**（到 0.01% 所需时间，含热效应尾巴）。见 [6.7](p1-07-ch6.md#sec-6-7)。

    </details>

<a id="quiz-ch7"></a>
## 第 7 章 比较器

[← 返回第 7 章复习](p1-08-ch7.md#ch7) · [卡住先查公式：速查表·比较器](p0-08-cheatsheet.md#cmp)

1. <a id="q-ch7-01" data-quiz-question="true"></a>为什么"拿运放当比较器"是坏习惯（至少三条理由）？

    <details markdown="1">
    <summary>答案</summary>

    ① 运放为线性区做了相位补偿，饱和后**退出饱和慢**；② 输入端常有保护二极管/背靠背结构，大差分输入会出问题；③ 输出摆幅不干净、恢复时间长；④ 没有专为判决优化的输出级。见 [7.1](p1-08-ch7.md#sec-7-1)。

    </details>

2. <a id="q-ch7-02" data-quiz-question="true"></a>迟滞的两个门限由什么决定？

    <details markdown="1">
    <summary>答案</summary>

    由**正反馈电阻比**与**输出高低电平**决定。把输出的一部分反馈到同相端，使上门限与下门限分离，间距即迟滞带宽。迟滞带宽须大于噪声峰峰值。见 [7.3](p1-08-ch7.md#sec-7-3)。

    </details>

3. <a id="q-ch7-03" data-quiz-question="true"></a>LM393 输出必须接什么？忘了会怎样？

    <details markdown="1">
    <summary>答案</summary>

    **上拉电阻**：经典 LM393 是 NPN **开集电极**输出，只能主动拉低。没有上拉时，输出管截止后的电位不受保证，可能悬浮，不能把它认作有效高电平。见 [7.2](p1-08-ch7.md#sec-7-2)。

    </details>

<a id="quiz-ch8"></a>
## 第 8 章 模拟开关

[← 返回第 8 章复习](p1-09-ch8.md#ch8) · [卡住先查公式：速查表·模拟开关](p0-08-cheatsheet.md#switch)

1. <a id="q-ch8-01" data-quiz-question="true"></a>传输门为什么必须 NMOS 与 PMOS 并联？

    <details markdown="1">
    <summary>答案</summary>

    NMOS 传低电平好、传高电平差（$V_{GS}$ 不够）；PMOS 反之。并联后**全程导通电阻平坦**，实现轨到轨。见 [8.1](p1-09-ch8.md#sec-8-1)。

    </details>

2. <a id="q-ch8-02" data-quiz-question="true"></a>采样保持电路的两大误差源是什么？各自怎么缓解？

    <details markdown="1">
    <summary>答案</summary>

    **droop**（保持电容漏电导致电压下垂）→ 加大电容/低漏电介质/缩短保持时间；**电荷注入**（开关断开时沟道电荷踢进电容，$\Delta V = Q_{ch}/C_H$）→ 加大 $C_H$、用互补dummy 开关、减小开关尺寸。见 [8.4](p1-09-ch8.md#sec-8-4)。

    </details>

3. <a id="q-ch8-03" data-quiz-question="true"></a>CD4051 是干什么用的？用它做多路采集要注意什么？

    <details markdown="1">
    <summary>答案</summary>

    8 选 1 模拟多路复用器。注意：导通电阻（几百欧）与信号源/采样电容构成的时间常数决定**切换后的建立时间**。通道间还有串扰与漏电流。见 [8.2](p1-09-ch8.md#sec-8-2)。

    </details>

<a id="quiz-ch9"></a>
## 第 9 章 基准与稳压

[← 返回第 9 章复习](p1-10-ch9.md#ch9) · [卡住先查公式：速查表·基准与稳压](p0-08-cheatsheet.md#ref)

1. <a id="q-ch9-01" data-quiz-question="true"></a>齐纳与带隙基准的温漂本质差别是什么？

    <details markdown="1">
    <summary>答案</summary>

    齐纳 <5V 是齐纳击穿（负温漂）、>5V 是雪崩（正温漂）；**带隙**把 $V_{BE}$ 的负温漂与 $\Delta V_{BE}$（PTAT）的正温漂按权重相加 → 得到 ≈1.25V 的零温漂电压。见 [9.1](p1-10-ch9.md#sec-9-1)。

    </details>

2. <a id="q-ch9-02" data-quiz-question="true"></a>LDO 的 dropout 电压是什么？为什么它决定电池能用到多低？

    <details markdown="1">
    <summary>答案</summary>

    维持稳压所需的**最小 $V_{IN}-V_{OUT}$**（由调整管的导通电阻/饱和压降决定）。电池电压掉到 $V_{OUT}+V_{DO}$ 以下，输出就跟着掉。所以低压差 LDO 能延长电池寿命。见 [9.3](p1-10-ch9.md#sec-9-3)。

    </details>

3. <a id="q-ch9-03" data-quiz-question="true"></a>线性稳压输出端最容易忽视的一个参数是什么？

    <details markdown="1">
    <summary>答案</summary>

    **输出电容的 ESR**：老式 LDO（如 1117 系列）的稳定性依赖 ESR 落在某个窗口内（太大→瞬态差，太小→环路失稳振荡）；换用陶瓷电容时要确认 datasheet。见 [9.3](p1-10-ch9.md#sec-9-3)。

    </details>

<a id="quiz-ch10"></a>
## 第 10 章 555 定时器

[← 返回第 10 章复习](p1-11-ch10.md#ch10) · [卡住先查公式：速查表·555](p0-08-cheatsheet.md#timer)

1. <a id="q-ch10-01" data-quiz-question="true"></a>555 无稳态振荡的频率公式？

    <details markdown="1">
    <summary>答案</summary>

    $f \approx 1.44/((R_1+2R_2)C)$，占空比 $>50\%$（$t_H$ 含 $R_1+R_2$、$t_L$ 只有 $R_2$）。要 50% 需二极管旁路 $R_2$。见 [10.2](p1-11-ch10.md#sec-10-2)。

    </details>

2. <a id="q-ch10-02" data-quiz-question="true"></a>单稳态模式的输出脉宽？

    <details markdown="1">
    <summary>答案</summary>

    $t \approx 1.1RC$：电容从 0 充到 $\frac{2}{3}V_{CC}$ 的时间（$\ln 3 \times RC$）。见 [10.5](p1-11-ch10.md#sec-10-5)。

    </details>

3. <a id="q-ch10-03" data-quiz-question="true"></a>555 内部那三个 5kΩ 电阻是干嘛的？（名字的由来）

    <details markdown="1">
    <summary>答案</summary>

    串联分压给两个比较器提供 **$\frac{1}{3}V_{CC}$** 与 **$\frac{2}{3}V_{CC}$** 两个门限——一切公式的源头，也是 555 这个名字的来源。见 [10.1](p1-11-ch10.md#sec-10-1)。

    </details>

<a id="quiz-ch11"></a>
## 第 11 章 放大电路拓扑

[← 返回第 11 章复习](p2-01-ch11.md#ch11) · [卡住先查公式：速查表·拓扑·噪声·稳定](p0-08-cheatsheet.md#topo)

1. <a id="q-ch11-01" data-quiz-question="true"></a>三种组态里，哪个电压增益≈1、哪个高频特性最好、哪个既能放大又反相？

    <details markdown="1">
    <summary>答案</summary>

    **共集（射随）**增益≈1、输入高输出低；**共基**高频最好（无米勒效应）；**共射**电压增益大且**反相**。见 [11.1](p2-01-ch11.md#sec-11-1)。

    </details>

2. <a id="q-ch11-02" data-quiz-question="true"></a>电流镜在模拟 IC 里的两个作用？

    <details markdown="1">
    <summary>答案</summary>

    ① **复制偏置电流**（一处生成、多处镜像）；② 作为**有源负载**（直流压降小、交流阻抗极高 → 单级高增益）。见 [11.3](p2-01-ch11.md#sec-11-3)。

    </details>

3. <a id="q-ch11-03" data-quiz-question="true"></a>米勒效应把 $C_{gd}$ 等效放大多少倍？后果是什么？

    <details markdown="1">
    <summary>答案</summary>

    $(1+|A_v|)$ 倍。10pF 在 100 倍增益下等效 1nF 跨接在输入输出之间，直接把带宽吃掉（并可能在反馈环路里制造极点）。见 [11.5](p2-01-ch11.md#sec-11-5)。

    </details>

4. <a id="q-ch11-04" data-quiz-question="true"></a>为什么电流源可以做“有源负载”，而电阻不行？

    <details markdown="1">
    <summary>答案</summary>

    电流源**直流电阻小**（几百欧到几千欧，只吃掉少量电压余量），**交流输出电阻 $r_o$ 大**（几十千欧到兆欧）。增益看的是交流负载 $R_{out}=r_{o,n}\parallel r_{o,p}$，所以同样一条电源轨，电流源负载能把单级增益做到 $g_m r_o$ 量级；电阻负载要更高的增益就得加大 $R_C$，直流压降和摆幅先受不了。见 [11.8](p2-01-ch11.md#sec-11-8)。

    </details>

5. <a id="q-ch11-05" data-quiz-question="true"></a>cascode 为什么能把输出电阻抬到 $g_m r_o^2$ 量级？代价是什么？

    <details markdown="1">
    <summary>答案</summary>

    共基管把输入管的 $r_o$ 串进自己的发射极。输出端看到的是“共基管的 $r_o$ 再加上被 $(g_m r_o)$ 放大的发射极电阻”，量级变成 $g_m r_o^2$。但多叠一只管子就多要一个 $V_{CE}$ 余量，输出摆幅变小。见 [11.8](p2-01-ch11.md#sec-11-8)。

    </details>

6. <a id="q-ch11-06" data-quiz-question="true"></a>差分对 $A_{vd}=200$、单端 $A_{cm}=0.01$，CMRR 是多少 dB？

    <details markdown="1">
    <summary>答案</summary>

    $CMRR=200/0.01=20{,}000$，即 $20\log_{10}(20{,}000)\approx86\text{ dB}$。注意这是**单端**共模增益下的值；换成差分输出，$A_{cm}$ 不同，CMRR 不能直接比较。见 [11.9](p2-01-ch11.md#sec-11-9)。

    </details>

7. <a id="q-ch11-07" data-quiz-question="true"></a>PSRR = 60 dB 时，电源上 100 mV 的纹波等效到输入端是多少？

    <details markdown="1">
    <summary>答案</summary>

    $60\text{ dB}=1000$ 倍，$100\text{ mV}/1000=0.1\text{ mV}$。但这是低频值；高频下结电容和封装电感会给纹波开新路，PSRR 常掉到 40~60 dB，不能拿 DC 值预测开关纹波。见 [11.9](p2-01-ch11.md#sec-11-9)。

    </details>

8. <a id="q-ch11-08" data-quiz-question="true"></a>10 kΩ 电阻、300 K、1 MHz 带宽，热噪声有效值约多少？

    <details markdown="1">
    <summary>答案</summary>

    $V_n=\sqrt{4kTRB}=\sqrt{4(1.38\times10^{-23})(300)(10^4)(10^6)}\approx12.9\ \mu\text{Vrms}$。带宽每降 100 倍，噪声降 10 倍；源阻每降 100 倍也降 10 倍。见 [11.10](p2-01-ch11.md#sec-11-10)。

    </details>

9. <a id="q-ch11-09" data-quiz-question="true"></a>要 60 dB 增益，第一级 40 倍、第二级 25 倍够不够？为什么不能只靠一级？

    <details markdown="1">
    <summary>答案</summary>

    $40\times25=1000$，正好 60 dB。一级共射要做到 1000 倍，需要 $R_C$ 与 $r_o$ 并联后约 $25\text{ k}\Omega$（按 $g_m=40\text{ mS}$ 算），12 V 电源给不起这个直流压降；分成两级后每级只要几十倍，偏置和摆幅都留得下余量。实际还要扣掉后级负载分流和射随器的 0.97。见 [11.11](p2-01-ch11.md#sec-11-11)。

    </details>

10. <a id="q-ch11-10" data-quiz-question="true"></a>$C_{bc}=5\text{ pF}$、第一级增益 50，输入等效电容是多少？源阻 10 kΩ 时输入极点约多少？

    <details markdown="1">
    <summary>答案</summary>

    $C_{in}=(1+50)\times5\text{ pF}=255\text{ pF}$；$f_p=1/[2\pi(10\text{ k})(255\text{ p})]\approx62\text{ kHz}$。要 100 kHz，得降增益、降源阻或上 cascode 拆掉米勒桥。见 [11.11](p2-01-ch11.md#sec-11-11)。

    </details>

<a id="quiz-ch12"></a>
## 第 12 章 运放应用电路族

[← 返回第 12 章复习](p2-02-ch12.md#ch12) · [卡住先查公式：速查表·运放](p0-08-cheatsheet.md#opamp)

1. <a id="q-ch12-01" data-quiz-question="true"></a>反相放大器的增益公式？输入阻抗由什么决定？

    <details markdown="1">
    <summary>答案</summary>

    $A_v = -R_f/R_i$；输入阻抗 ≈ **$R_i$**（虚地把输入端钉在 0V）。这是反相组态的固有代价。见 [12.2](p2-02-ch12.md#sec-12-2)。

    </details>

2. <a id="q-ch12-02" data-quiz-question="true"></a>相位裕度的工程底线与舒适区分别是多少度？

    <details markdown="1">
    <summary>答案</summary>

    底线 **45°**、舒适区 **60°**。低于 45° 会出现明显过冲/振铃，低于 0° 直接振荡。见 [12.7](p2-02-ch12.md#sec-12-7)。

    </details>

3. <a id="q-ch12-03" data-quiz-question="true"></a>运放跟随器驱动 100nF 长电缆就振荡，最省事的两招是什么？

    <details markdown="1">
    <summary>答案</summary>

    ① 输出串隔离电阻，**反馈取隔离电阻前的运放输出端**，阻值按运放、负载与环路分析选择；代价是负载电流造成直流压降。要从负载端校正直流误差，需另设计高频反馈补偿，不能只移动反馈线。② 适当提高**噪声增益**、降低交越频率，并验证稳定性。见 [12.9](p2-02-ch12.md#sec129)。

    </details>

<a id="quiz-ch13"></a>
## 第 13 章 电源与信号产生

[← 返回第 13 章复习](p2-03-ch13.md#ch13) · [卡住先查公式：速查表·电源与信号](p0-08-cheatsheet.md#power)

1. <a id="q-ch13-01" data-quiz-question="true"></a>Buck 的伏秒平衡怎么写？由此得到占空比？

    <details markdown="1">
    <summary>答案</summary>

    $(V_{IN}-V_{OUT})t_{on} = V_{OUT}t_{off}$ → $D = V_{OUT}/V_{IN}$（CCM 理想）。这是所有 Buck 计算的源头。见 [13.2](p2-03-ch13.md#sec-13-2)。

    </details>

2. <a id="q-ch13-02" data-quiz-question="true"></a>电荷泵相对电感的 DC-DC 有什么优缺点？

    <details markdown="1">
    <summary>答案</summary>

    优点：无磁件、**EMI 小**、体积小、可做负压/倍压；缺点：带载能力弱（几十 mA）、输出阻抗较高、效率随压差下降。见 [13.3](p2-03-ch13.md#sec-13-3)。

    </details>

3. <a id="q-ch13-03" data-quiz-question="true"></a>H 桥为什么要设死区时间？恒流源的"合规电压"又是什么？

    <details markdown="1">
    <summary>答案</summary>

    死区防止上下管**直通**（先关后开）；恒流源的合规电压是**它能维持恒流的最大输出电压**，超过就退出恒流区（4~20mA 环路要留足裕量）。见 [13.7](p2-03-ch13.md#sec-13-7) / [13.5.1](p2-03-ch13.md#sec-13-5-1)。

    </details>

<a id="quiz-ch14"></a>
## 第 14 章 设计方法论

[← 返回第 14 章复习](p3-01-ch14.md#ch14) · [卡住先查公式：速查表·设计与可靠性](p0-08-cheatsheet.md#design)

1. <a id="q-ch14-01" data-quiz-question="true"></a>从需求到打样的六步是什么？哪一步最容易被跳过？

    <details markdown="1">
    <summary>答案</summary>

    需求指标 → 拓扑选择 → 器件选型 → 仿真验证 → **降额与保护** → 打样测试。最容易跳过的是"降额与保护"：常温典型值能跑，极限工况却会烧。仿真不过就回炉，别硬着头皮打样。见 [14.1](p3-01-ch14.md#sec-14-1)。

    </details>

2. <a id="q-ch14-02" data-quiz-question="true"></a>PT100 为什么要三线/四线制？

    <details markdown="1">
    <summary>答案</summary>

    PT100 只有 ~0.385Ω/°C，引线电阻（几欧）会带来十几度的误差；三线/四线用**开尔文接法**把引线电阻抵消掉。见 [14.4](p3-01-ch14.md#sec-14-4)。

    </details>

3. <a id="q-ch14-03" data-quiz-question="true"></a>十条军规里"最坏情况分析（WCCA）：参数全取极限仍要工作"为什么排得上号？

    <details markdown="1">
    <summary>答案</summary>

    原型在常温、典型值下通过，不代表批次和极限工况同样过关；WCCA 把所有参数同向推到极限，是对"概率尾巴"的兜底。消费类再用 RSS 的 $3\sigma$ 估良率，车规/医疗则直接按 WC 验收。见 [14.2 军规 10](p3-01-ch14.md#sec-14-2) / [14.10](p3-01-ch14.md#sec-14-10)。

    </details>

4. <a id="q-ch14-04" data-quiz-question="true"></a>三个独立误差项各 ±1%，按均匀分布。最坏情况、RSS 的 $1\sigma$ 与 $3\sigma$ 各是多少？

    <details markdown="1">
    <summary>答案</summary>

    WC $=1\%+1\%+1\%=\mathbf{3\%}$；单项 $\sigma=1\%/\sqrt{3}=0.577\%$，RSS 的 $1\sigma=\sqrt{3}\times0.577\%=\mathbf{1.0\%}$，$3\sigma=\mathbf{3.0\%}$。**别把 ±1% 的极限当成 $1\sigma$**，那样 $3\sigma$ 会算成 5.2%，凭空多出 73% 的悲观。见 [14.10](p3-01-ch14.md#sec-14-10)。

    </details>

5. <a id="q-ch14-05" data-quiz-question="true"></a>一颗器件 $\theta_{JC}=2$、$\theta_{CS}=1$、$\theta_{SA}=17$（°C/W），$T_A=50$°C，$P=2$W，结温多少？若上限 125°C，余量多少？

    <details markdown="1">
    <summary>答案</summary>

    $T_J=50+2\times(2+1+17)=\mathbf{90°C}$；余量 $125-90=\mathbf{35°C}$。热设计就是这条串联链：先把总热阻算出来，再逐项扣封装、界面、散热器。见 [14.5](p3-01-ch14.md#sec145)。

    </details>

6. <a id="q-ch14-06" data-quiz-question="true"></a>同一只基准同时给激励和 ADC 供电时，为什么不能把两项误差直接平方和开根？

    <details markdown="1">
    <summary>答案</summary>

    这两项**相关**：基准一涨，激励和 ADC 刻度同向变化，必须先合并成一个等效项，再参与 RSS；直接当独立项会把总误差算小。比率测量正是利用这种相关性，把大部分误差约掉。见 [14.9](p3-01-ch14.md#sec-14-9) / [14.10](p3-01-ch14.md#sec-14-10)。

    </details>

7. <a id="q-ch14-07" data-quiz-question="true"></a>测试计划里只写"测 5V 轨"为什么不够？一条完整测试至少写清哪五件事？

    <details markdown="1">
    <summary>答案</summary>

    没有判据的测试只是围观。一条完整测试要写清**目的、条件、仪器、判据、失败动作**：失败时先查哪、换什么。见 [14.11](p3-01-ch14.md#sec-14-11)。

    </details>

8. <a id="q-ch14-08" data-quiz-question="true"></a>PT100 在 0~100°C 的输出是 38.5mV，ADC 满量程 2.048V 并留 25% 余量，目标信号 1.54V，增益取多少？

    <details markdown="1">
    <summary>答案</summary>

    $1.54\text{V}\div38.5\text{mV}=\mathbf{40}$。顺序是**从后往前推**：先定 ADC 满量程与余量，再分配增益，最后算噪声预算。见 [14.4](p3-01-ch14.md#sec-14-4)。

    </details>

9. <a id="q-ch14-09" data-quiz-question="true"></a>把仪放增益电阻从 1% 换成 0.1%，增益误差理论上从 1% 降到 0.1%。为什么不能无条件换？

    <details markdown="1">
    <summary>答案</summary>

    成本与可得性会上升，而且**温漂不匹配**时比例精度仍会漂；更该先看这一项在预算里占多少方差、是否已有校准。预算里放大只占一部分时，把钱花在更长的条上收益更大。见 [14.9](p3-01-ch14.md#sec-14-9) / [14.10](p3-01-ch14.md#sec-14-10)。

    </details>

10. <a id="q-ch14-10" data-quiz-question="true"></a>为什么在 >100MHz 的高速节点上随便加测试点，可能把信号压坏？该怎么替代？

    <details markdown="1">
    <summary>答案</summary>

    测试点本身是**寄生电容**，加在高速节点上会造成负载与阻抗不连续；这类节点改用**测试过孔**、把 TP 放在缓冲之后，或靠**内建自测（BIST）**。见 [14.8](p3-01-ch14.md#sec148)。

    </details>

**错题回查（先回方法，再重算）**

- 第 1、3 题错 → 回 [14.1](p3-01-ch14.md#sec-14-1) / [14.2](p3-01-ch14.md#sec-14-2)：默写六步与十条军规，并写出每一步的交付物。
- 第 2、8 题错 → 回 [14.4](p3-01-ch14.md#sec-14-4)：从 ADC 满量程反推增益，把信号链重画一遍。
- 第 4、5、6 题错 → 回 [14.9](p3-01-ch14.md#sec-14-9) / [14.10](p3-01-ch14.md#sec-14-10)：重算 RSS 与 WC，先合并相关项。
- 第 7、10 题错 → 回 [14.11](p3-01-ch14.md#sec-14-11) / [14.8](p3-01-ch14.md#sec148)：给每条测试补判据、失败动作与测试点。
- 第 9 题错 → 回 [14.9](p3-01-ch14.md#sec-14-9)：按方差份额排序，先砍最长的那一条。

**能用自己的话讲清"为什么"，比记住答案更重要。**

<a id="quiz-ch15"></a>
## 第 15 章 PCB

[← 返回第 15 章复习](p3-02-ch15.md#ch15) · [卡住先查公式：速查表·PCB](p0-08-cheatsheet.md#pcb)

1. <a id="q-ch15-01" data-quiz-question="true"></a>去耦电容为什么必须贴着电源引脚放？

    <details markdown="1">
    <summary>答案</summary>

    去耦有效性取决于**环路电感**而非容量：每 1mm 走线约 1nH，距离一远，高频电流就先去别处要。见 [15.1](p3-02-ch15.md#sec-15-1)。

    </details>

2. <a id="q-ch15-02" data-quiz-question="true"></a>高速信号的回流电流走哪里？地平面开槽会怎样？

    <details markdown="1">
    <summary>答案</summary>

    回流在**信号线正下方的地平面**上（最小环路=最小电感）；开槽迫使回流绕路 → 环路面积暴增 → 变成**缝隙天线**辐射 EMI。见 [15.2](p3-02-ch15.md#sec-15-2) / [15.6](p3-02-ch15.md#sec156)。

    </details>

3. <a id="q-ch15-03" data-quiz-question="true"></a>星形接地适用于什么场合？高频为什么反而不推荐分割地？

    <details markdown="1">
    <summary>答案</summary>

    星形接地适合**低频/小信号**（避免公共阻抗耦合）；高频时回流必须紧贴信号线，分割地会破坏回流路径 → 应优先用**完整地平面**。只在必要时（如隔离/大功率）分割并桥接。见 [15.2](p3-02-ch15.md#sec-15-2)。

    </details>

<a id="quiz-ch16"></a>
## 第 16 章 排故五步法

[← 返回第 16 章复习](p4-01-ch16.md#ch16) · [卡住先查公式：速查表·排故](p0-08-cheatsheet.md#debug)

1. <a id="q-ch16-01" data-quiz-question="true"></a>排故五步是哪五步？

    <details markdown="1">
    <summary>答案</summary>

    复现现象 → 划分范围（对半切） → 提出假设 → 测量验证 → 修复并确认根因；核心是**单变量对照**与**先电源后信号**。见 [16.1](p4-01-ch16.md#sec-16-1)。

    </details>

2. <a id="q-ch16-02" data-quiz-question="true"></a>示波器探头对被测电路意味着什么？

    <details markdown="1">
    <summary>答案</summary>

    它是**并联负载**：×1 档约 1MΩ∥100pF，×10 档约 10MΩ∥十几 pF。在高频/高阻节点上，接上探头就改变了电路（"接上探头振荡消失"= 本来就在临界稳定）。见 [16.3](p4-01-ch16.md#sec163)。

    </details>

3. <a id="q-ch16-03" data-quiz-question="true"></a>「对数切半法」适用于什么？

    <details markdown="1">
    <summary>答案</summary>

    长链路（传感器→放大→滤波→ADC→软件）定位：在链路中点测一次，判断故障在前半还是后半。**每测一次砍掉一半**，n 次测量定位 $2^n$ 个节点。见 [16.2](p4-01-ch16.md#sec-16-2)。

    </details>

4. <a id="q-ch16-04" data-quiz-question="true"></a>×10 探头为什么比 ×1 更适合测高阻节点？

    <details markdown="1">
    <summary>答案</summary>

    ×10 档约 10MΩ∥10~15pF，×1 档约 1MΩ∥100pF。以 100kΩ 源阻为例，×10 的直流分压误差约 1%，×1 约 9%；输入电容小十倍，时间常数也从约 9µs 降到约 1µs，带宽提高约九倍。见 [16.6](p4-01-ch16.md#sec-16-6)。

    </details>

5. <a id="q-ch16-05" data-quiz-question="true"></a>16 个可测节点的链路，每次只能判断正常/异常，最少几次能锁定故障级？

    <details markdown="1">
    <summary>答案</summary>

    4 次。每次二选一，4 次最多区分 $2^4=16$ 种情况；按中点优先，16→8→4→2→1。前提是测量点本身可信，探头不能把节点改坏。见 [16.7](p4-01-ch16.md#sec-16-7)。

    </details>

6. <a id="q-ch16-06" data-quiz-question="true"></a>往链路里注入测试信号，先要确认哪三件事？

    <details markdown="1">
    <summary>答案</summary>

    节点是否允许外加电压（会不会改变直流工作点）；注入源阻抗会不会拖住节点；地夹是否接在同一回流路径上。幅度从小到大，先 10mV 量级，避免把后级打进饱和。见 [16.7](p4-01-ch16.md#sec-16-7)。

    </details>

7. <a id="q-ch16-07" data-quiz-question="true"></a>用长鳄鱼夹地线测电源纹波，为什么可能看到"假纹波"？

    <details markdown="1">
    <summary>答案</summary>

    长地线有几十到一百多纳亨电感，开关电流的 $di/dt$ 会在地线上感应出尖峰。示波器把它和真实信号一起画出来。改用弹簧地针缩短地回路，或用差分探头；测市电相关电路还要先隔离。见 [16.6](p4-01-ch16.md#sec-16-6)。

    </details>

8. <a id="q-ch16-08" data-quiz-question="true"></a>一份可复用的排故记录，至少要能回答哪些问题？

    <details markdown="1">
    <summary>答案</summary>

    现象与复现条件、环境和版本、电源/静态与动态测量、假设链（含已证伪）、单变量实验；根因的物理机制、修复动作、回归条件与样本数、防呆动作。根因和回归不能空，"已修好"不算回归结论。见 [16.9](p4-01-ch16.md#sec-16-9)。

    </details>

9. <a id="q-ch16-09" data-quiz-question="true"></a>「根因」和「触发条件」为什么要分开写？

    <details markdown="1">
    <summary>答案</summary>

    根因是设计或工艺里本来就存在的缺陷，触发条件只是把它暴露出来的那阵风。只改触发条件（降测试温度、加风扇、粘住 BGA），缺陷还在，换个批次或季节就会复发；修根因并用回归与防呆锁住，才算闭环。见 [16.8](p4-01-ch16.md#sec-16-8)。

    </details>

<a id="quiz-ch17"></a>
## 第 17 章 故障速查

[← 返回第 17 章复习](p4-02-ch17.md#ch17) · [卡住先查公式：速查表·排故](p0-08-cheatsheet.md#debug)

1. <a id="q-ch17-01" data-quiz-question="true"></a>故障排查永远第一步查什么？为什么？

    <details markdown="1">
    <summary>答案</summary>

    **电源与时序**：电压值、纹波、上电顺序、复位与时钟。经验上七成"芯片坏了"出自电源/连接问题。见 [17.1](p4-02-ch17.md#sec-17-1)。

    </details>

2. <a id="q-ch17-02" data-quiz-question="true"></a>"不该振荡却振荡"的排查顺序是什么？

    <details markdown="1">
    <summary>答案</summary>

    电源去耦 → 环路**相位裕度** → 布线寄生耦合 → 接地环路；别忘了探头本身是负载。见 [17.3](p4-02-ch17.md#sec-17-3)。

    </details>

3. <a id="q-ch17-03" data-quiz-question="true"></a>真实故障中占比最高的一类是什么？

    <details markdown="1">
    <summary>答案</summary>

    **焊接与连接**（虚焊、冷焊、接插件松动、线束断），远高于器件损坏。所以"先摇一摇、按一按、看焊点"永远值得先做。见 [17.5](p4-02-ch17.md#sec-17-5)。

    </details>

<a id="quiz-ch18"></a>
## 第 18 章 大师的排故智慧

[← 返回第 18 章复习](p4-03-ch18.md#ch18) · [卡住先查公式：速查表·排故](p0-08-cheatsheet.md#debug)

1. <a id="q-ch18-01" data-quiz-question="true"></a>Bob Pease 那条最该记住的态度是什么？

    <details markdown="1">
    <summary>答案</summary>

    **相信测量、怀疑直觉**——"仪器从不说谎，人会"（先复现、按序记录、把假设写成可证伪的实验）。见 [18.1](p4-03-ch18.md#sec-18-1)。

    </details>

2. <a id="q-ch18-02" data-quiz-question="true"></a>Jim Williams 的测量铁律是什么？

    <details markdown="1">
    <summary>答案</summary>

    **测量本身不能破坏被测电路**：探头地线要短、用接地弹簧而非长鳄鱼夹、注意探头电容与带宽限制。否则你看到的是"探头+电路"而不是电路。见 [18.2](p4-03-ch18.md#sec-18-2)。

    </details>

3. <a id="q-ch18-03" data-quiz-question="true"></a>两位大师的共通心法是哪三条？

    <details markdown="1">
    <summary>答案</summary>

    ① 先复现并按序记录症状；② 一次只改一个变量；③ 找到**根因**而不只是让它"看起来好了"。见 [18.3](p4-03-ch18.md#sec-18-3)。

    </details>

---

## 专题加练（新增小节 · 34 题）

> 这 34 题对应 v3.21~v3.23 补入的小节与加深内容：§1.6 LC 谐振四拍、§12.10 TIA、§13.8 电流检测、§13.9 功放与 THD；
> 另含 §14.5 热设计、§14.6 LTspice、§16.4 排故记录与复盘、§18.4 设计评审清单，连同六节「四拍动态分析」与第 17 章故障总表；
> v3.23 再加 **§11.5 相位裕度/极点分裂、§11.6 噪声预算、§12.5 Sallen-Key 理论、§12.12 开关电容、§13.6 量化噪声与 ENOB** 五组；
> v3.28 再加六组：**§1.7 直流偏压降容与铝电解寿命、§12.13 运放输入级三口味与 RRIO、§13.10 晶体振荡器（$C_L$/牵引/负阻）、§13.11 光耦 CTR；§14.8 误差预算与良率、§16.5 排故实战三案例**。全部是能算的题。

1. <a id="q-extra-01" data-quiz-question="true"></a>**§13.8** 12V 电机额定 5A，用 10mΩ 分流电阻做高侧检测、要求 1% 精度——放大器至少要多大的 CMRR？

    <details markdown="1">
    <summary>答案</summary>

    满量程 $5A\times10m\Omega=50mV$，1% 即 0.5mV 误差预算；分给放大器 0.2mV → $CMRR > 12V/0.2mV = 60000 \approx$ **96dB**。LM358 只有 70dB（12V 共模直接产生 3.8mV ≈ 7.6% 误差），必须用 INA181/INA240 这类电流检测放大器。见 [13.8](p2-03-ch13.md#sec138)。

    </details>

2. <a id="q-extra-02" data-quiz-question="true"></a>**§13.8** 负载与系统共地，且要求能测"负载对地短路"——低侧还是高侧？为什么？

    <details markdown="1">
    <summary>答案</summary>

    **高侧**。低侧检测会把负载的"地"抬高 $V_{shunt}$（破坏共地参考），而且短路时电流绕过电阻直接走地、**测不到**；高侧地完整、短路电流仍经过分流电阻。见 [13.8](p2-03-ch13.md#sec138)。

    </details>

3. <a id="q-extra-03" data-quiz-question="true"></a>**§13.9** 8Ω 喇叭输出 10W，B 类功放（实际效率 60%）电源要供多少瓦？有多少变热？

    <details markdown="1">
    <summary>答案</summary>

    $P_{supply}=10/0.6=\mathbf{16.7W}$，其中 10W 出声、**6.7W 全变热**。换 D 类（90%）→ 只发热 1.1W，这就是便携音箱用 D 类的原因。见 [13.9](p2-03-ch13.md#sec139)。

    </details>

4. <a id="q-extra-04" data-quiz-question="true"></a>**§13.9** 输出级为什么要加 $V_{BE}$ 倍增偏置？为什么偏置管必须贴在散热器上？

    <details markdown="1">
    <summary>答案</summary>

    加偏置是为了让两管在过零点都微微导通，消除**交越失真**（平肩）；贴散热器是为了**热补偿**：功率管温升使 $V_{BE}$ 下降、偏置电流增大、更热，会正反馈成**热失控**。偏置管与之热耦合，才能反向抵消。见 [13.9](p2-03-ch13.md#sec139)。

    </details>

5. <a id="q-extra-05" data-quiz-question="true"></a>**§14.5** LDO 12V→5V、1A；TO-220 的 $\theta_{JC}=2$、硅脂 $\theta_{CS}=1$、$T_A=40°C$、要求 $T_J\le125°C$——散热器热阻最多多大？

    <details markdown="1">
    <summary>答案</summary>

    $P=(12-5)\times1=7W$；允许总热阻 $=(125-40)/7=12.1$ °C/W → $\theta_{SA}\le12.1-2-1=\mathbf{9.1}$ °C/W（巴掌大铝片即可）。换成 90% 效率的 Buck：$P=0.56W$ → 允许 152 °C/W，**什么都不用加**。见 [14.5](p3-01-ch14.md#sec145)。

    </details>

6. <a id="q-extra-06" data-quiz-question="true"></a>**§14.5** 为什么同一颗 SOT-23 的 $\theta_{JA}$，在不同板子上能差一倍？

    <details markdown="1">
    <summary>答案</summary>

    因为不加散热器时，散热几乎全靠 **PCB 铜皮**（面积、热过孔、内层地平面）；datasheet 的 $\theta_{JA}$ 基于 JEDEC 标准测试板。**脱离板条件谈 $\theta_{JA}$ 没有意义**。见 [14.5](p3-01-ch14.md#sec145)。

    </details>

7. <a id="q-extra-07" data-quiz-question="true"></a>**§14.6** 为什么不能用"理想运放"模型验证压摆率与相位裕度？

    <details markdown="1">
    <summary>答案</summary>

    理想运放没有带宽限制、没有压摆率、输出无限快 → 仿真永远"完美"，看不见真实效应。**必须用厂商 SPICE 模型**（LT1012 / OPA192 等）才看得到 GBW、SR、输出限幅。见 [14.6](p3-01-ch14.md#sec146)。

    </details>

8. <a id="q-extra-08" data-quiz-question="true"></a>**§14.6** `.tran` 跑出来看不到开关尖峰，最可能是哪两处设置？

    <details markdown="1">
    <summary>答案</summary>

    ① **时间步长太粗**：加 `maxstep`：`.tran 0 10m 0 100n`；② **波形压缩**：`.options plotwinsize=0`。见 [14.6](p3-01-ch14.md#sec146)。

    </details>

9. <a id="q-extra-09" data-quiz-question="true"></a>**§5.6** ±12V、8Ω 的推挽若上下管同时导通（直通），电流和瞬时功耗约多少？为什么毫秒级烧管？

    <details markdown="1">
    <summary>答案</summary>

    两管 $R_{CE(sat)}$ 之和按 1Ω → $I=24/1=\mathbf{24A}$，瞬时功耗 $24^2\times0.5=\mathbf{288W}$，远超 TO-220 的 60W 极限。见 [5.6](p1-06-ch5.md#sec-5-6)。

    </details>

10. <a id="q-extra-10" data-quiz-question="true"></a>**§7.5** $R_1=10k$（同相端到基准）、$R_2=100k$（输出反馈）、$V_{ref}=2.5V$、$V_{OH}=5V$、$V_{OL}=0V$——迟滞宽度多少？能免疫多大幅度的毛刺？

    <details markdown="1">
    <summary>答案</summary>

    $V_{TH+}=(100k\times2.5+10k\times5)/110k=2.73V$，$V_{TH-}=2.27V$ → 宽度 **0.45V**；幅度小于 0.45V 的毛刺全部免疫。想更宽就把 $R_2$ 改小（但输入可用范围也被吃掉）。见 [7.5](p1-08-ch7.md#sec-7-5)。

    </details>

11. <a id="q-extra-11" data-quiz-question="true"></a>**§11.7** 差分对为什么在共模输入时输出差几乎为零？靠什么抑制共模？

    <details markdown="1">
    <summary>答案</summary>

    尾电流源把两管总电流钉死（$I_1+I_2=I_{tail}$）：共模想让两管同时多导电，但**总电流拿不到额外的**。于是两管电流不变、输出差为零。抑制共模靠的是那只**恒流尾巴**（$R_{tail}$ 越大 CMRR 越高），不是管子本身。见 [11.7](p2-01-ch11.md#sec-11-7)。

    </details>

12. <a id="q-extra-12" data-quiz-question="true"></a>**§12.11** 积分器 $R=10k$、$C=10n$，输入 ±1V 方波（半周期 500µs）——输出三角波峰峰值多少？

    <details markdown="1">
    <summary>答案</summary>

    斜率 $=v_{in}/RC=1V/100\mu s$ → 500µs 走 5V → 峰峰值 **10V**。注意是**直线**不是指数（恒流充电容）。见 [12.11](p2-02-ch12.md#sec-12-11)。

    </details>

13. <a id="q-extra-13" data-quiz-question="true"></a>**§14.7** 为什么"Buck + 后级 LDO"是常用组合？代价是什么？

    <details markdown="1">
    <summary>答案</summary>

    Buck 效率高但开关纹波大（几十~几百 kHz），LDO 低频 PSRR 60~80dB 把纹波再压两个数量级——**效率交给 Buck、噪声交给 LDO**。代价是 LDO 上的压差功耗（要过 [14.5 热设计](p3-01-ch14.md#sec145) 这笔账）。见 [14.7](p3-01-ch14.md#sec-14-7)。

    </details>

14. <a id="q-extra-14" data-quiz-question="true"></a>**§15.7** 地平面被切开后回程绕远，回路面积从 0.5cm² 变成 15cm²——辐射大约涨多少？

    <details markdown="1">
    <summary>答案</summary>

    面积放大 30 倍 → 辐射约 **+30dB**（辐射正比于回路面积 × $di/dt$）。所以 EMC 整改第一刀永远是**检查关键信号的回流面是否完整**。见 [15.7](p3-02-ch15.md#sec-15-7)。

    </details>

15. <a id="q-extra-15" data-quiz-question="true"></a>**§17** 拿到"上电无反应"，决策树的前两问是什么？各自的"否"落到哪张表？

    <details markdown="1">
    <summary>答案</summary>

    ① **输入电压在不在？** 否 → 17.1 电源类（保险 / 极性 / 连接）；② **关键电源轨都对吗？** 否 → 17.1（带载跌落 / 纹波 / 使能）。再往下是复位/时钟 → 17.3。见 [17.8 决策树](p4-02-ch17.md#sec-17-8) 与 [动画 5.102](p5-00-part5.md#demo102)。

    </details>

16. <a id="q-extra-16" data-quiz-question="true"></a>**§1.6** 串联回路 $R=1\Omega$、$L=1mH$、$C=10\mu F$，谐振频率多少？谐振时电感/电容上的电压是多少（电源 1V）？

    <details markdown="1">
    <summary>答案</summary>

    $f_0=\dfrac{1}{2\pi\sqrt{LC}}=\dfrac{1}{2\pi\times10^{-4}}\approx\mathbf{1592Hz}$；谐振时 $X_L=X_C=\sqrt{L/C}=10\Omega$、电流 $I=1V/1\Omega=1A$ → $V_L=V_C=1A\times10\Omega=\mathbf{10V}$——**电源只有 1V，元件上却有 10V**（电压放大 $Q=X_L/R=10$ 倍）。带宽 $BW=f_0/Q\approx159Hz$。见 [1.6](p1-02-ch1.md#sec-1-6)。

    </details>

17. <a id="q-extra-17" data-quiz-question="true"></a>**§16.4** 排故记录表里"根因"一栏最容易写成什么？正确的写法应该落到哪一层？

    <details markdown="1">
    <summary>答案</summary>

    最容易写成**症状复述**（"换了个芯片就好了"）；正确写法要落到**物理机制**（"晶振焊点虚焊，热胀后接触电阻变大导致起振失败"）。根因 ≠ 症状，必须能反推出可执行的设计约束。见 [16.4](p4-01-ch16.md#sec164)。

    </details>

18. <a id="q-extra-18" data-quiz-question="true"></a>**§18.4** 设计评审四道关口是哪四道？每条评审项要配一句什么问句？

    <details markdown="1">
    <summary>答案</summary>

    **原理图 → 布局 → 首板上电前 → 出货回归**；每条打勾前问"**如果不做，17 章哪一行会中招**"。把排故清单倒过来写，就是设计约束清单。见 [18.4](p4-03-ch18.md#sec-18-4)。

    </details>

19. <a id="q-extra-19" data-quiz-question="true"></a>**§11.5** 两级运放跨接补偿电容 $C_c$ 后，主极点和次极点分别往哪个方向走？为什么？

    <details markdown="1">
    <summary>答案</summary>

    主极点**左移变低**：$C_c$ 被第二级增益 $g_{m2}R_2$ 米勒放大成大电容，压住第一级输出。次极点**右移变高**：$C_c$ 给第二级输入开了低阻通路。这叫**极点分裂**。两个极点一分开，增益交点前的相位损耗减少 → 相位裕度回升。代价是单位增益带宽被钉成 $g_{m1}/(2\pi C_c)$。见 [11.5](p2-01-ch11.md#sec-11-5)。

    </details>

20. <a id="q-extra-20" data-quiz-question="true"></a>**§11.6** 源阻抗 1MΩ、信号带宽 10kHz——源电阻热噪声多大？为什么换"低噪声运放"没用？

    <details markdown="1">
    <summary>答案</summary>

    噪声带宽 $BW_n=1.57\times10\text{kHz}=15.7\text{kHz}$ → $\sqrt{4kTRB}\approx\mathbf{16.1\mu V}$。而运放电压噪声（$e_n=10\text{nV}/\sqrt{\text{Hz}}$）只有 1.25µV。**源电阻热噪声占了约 99%**，把 $e_n$ 换到 3nV 总噪声几乎不变。要么降源阻、要么压带宽。见 [11.6](p2-01-ch11.md#sec-11-6)。

    </details>

21. <a id="q-extra-21" data-quiz-question="true"></a>**§11.6** 一阶低通 −3dB 带宽 10kHz，白噪声的等效噪声带宽是多少？

    <details markdown="1">
    <summary>答案</summary>

    $BW_n=\dfrac{\pi}{2}f_H\approx1.57\times10\text{kHz}=\mathbf{15.7kHz}$。滚降段的噪声也被算进去了，**别拿 −3dB 带宽直接乘**。见 [11.6](p2-01-ch11.md#sec-11-6)。

    </details>

22. <a id="q-extra-22" data-quiz-question="true"></a>**§13.6** 满量程正弦输入时，12 位理想 ADC 的理论 SNR 是多少 dB？实际 ADC 在相同条件下测得 SINAD 为 68dB，ENOB 是多少？仅知道不含谐波的 SNR 为 68dB，能否确定 ENOB？

    <details markdown="1">
    <summary>答案</summary>

    $\text{SNR}=6.02N+1.76=6.02\times12+1.76=\mathbf{74.0dB}$；$\text{ENOB}=(68-1.76)/6.02\approx\mathbf{11.0}$ 位；此处代入的是 **SINAD**。仅有 SNR 时不能确定实际 ENOB，除非已知失真可忽略；输入不满幅还需幅度修正。见 [13.6](p2-03-ch13.md#sec136)。

    </details>

23. <a id="q-extra-23" data-quiz-question="true"></a>**§13.6** SAR ADC：$f_s=1\text{Msps}$、$C_{in}=20\text{pF}$、12 位——源阻抗上限大约多少？

    <details markdown="1">
    <summary>答案</summary>

    半周期 $500\text{ns}$，建立到 0.012%（半 LSB，$1/2^{N+1}$）需 $(N+1)\ln2\approx9$ 个 $\tau$ → $\tau\approx55\text{ns}$ → $R_{max}=\tau/C_{in}\approx\mathbf{2.75k\Omega}$。超过就掉码，所以 ADC 前必须加运放缓冲。见 [13.6](p2-03-ch13.md#sec136)。

    </details>

24. <a id="q-extra-24" data-quiz-question="true"></a>**§12.5** 等值元件的 Sallen-Key 低通（$R_1{=}R_2$、$C_1{=}C_2$）Q 是多少？要 Butterworth 怎么改？

    <details markdown="1">
    <summary>答案</summary>

    $Q=\sqrt{C_1/C_2}/2=0.5$（临界阻尼，滚降偏软）。要 $Q=0.707$（Butterworth），等值电阻下取**反馈电容 $C_1=2C_2$**（接输出那只取接地那只的 2 倍）。见 [12.5](p2-02-ch12.md#sec-12-5)。

    </details>

25. <a id="q-extra-25" data-quiz-question="true"></a>**§12.12** 1pF 电容 + 100kHz 时钟等效多大电阻？为什么开关电容滤波器前面必须加抗混叠？

    <details markdown="1">
    <summary>答案</summary>

    $R_{eq}=\dfrac{1}{f_{clk}C}=\dfrac{1}{10^5\times10^{-12}}=\mathbf{10M\Omega}$。因为开关电容对输入是**采样系统**，$f_{clk}$ 就是采样率。带外信号会混叠进来且无法事后剔除，所以前面必须加抗混叠滤波器。时钟通常取信号带宽的 50~100 倍。见 [12.12](p2-02-ch12.md#sec-12-12)。

    </details>

26. <a id="q-extra-26" data-quiz-question="true"></a>**§1.7** 只知道电容标称 10µF / 6.3V、0805、X5R，能确定它在 5V 偏压下的容量吗？若某具体料号在指定测试条件下的曲线显示保持率为 26%，有效容量是多少？若下降的是 50～70%，又剩多少？

    <details markdown="1">
    <summary>答案</summary>

    不能仅凭封装、耐压或 X5R 确定偏压降容；要查具体料号在相应温度、频率和交流幅度下的 DC-bias 曲线，必要时带偏压测量。给定保持率 26% 时，$C_{eff}=10\mu F\times26\%=\mathbf{2.6\mu F}$；下降 50～70% 则剩 $10\times(1-0.7)$ 到 $10\times(1-0.5)$，即 **3～5µF**。26% 是本题的假设条件，不是所有 X5R 的通性。见 [1.7](p1-02-ch1.md#cap-dc-bias)。

    </details>

27. <a id="q-extra-27" data-quiz-question="true"></a>**§1.7** 105°C/2000h 的铝电解实际工作在 65°C——预期寿命多少？对"设计寿命 10 年、24h 连续运行"的设备够不够？

    <details markdown="1">
    <summary>答案</summary>

    $L=2000\times2^{(105-65)/10}=2000\times2^4=\mathbf{32000h}\approx3.7$ 年（24h×365）。**不够**。对策：换 105°C/5000h 以上、降低纹波电流（减少内部温升）、或改用固态/聚合物电容。顺带记住失效模式：**钽电容是短路（急性病），铝电解是干涸（慢性病）**。见 [1.7](p1-02-ch1.md#cap-dc-bias)。

    </details>

28. <a id="q-extra-28" data-quiz-question="true"></a>**§12.13** 源阻抗 1MΩ、信号只有 0~10mV。BJT 输入运放 $I_b=20\text{nA}$、CMOS 输入 $I_b=1\text{pA}$——各引入多大偏置误差？选谁？

    <details markdown="1">
    <summary>答案</summary>

    $V_{err}=I_bR_s$：BJT $=20\text{nA}\times1\text{M}\Omega=\mathbf{20mV}$（比满量程信号还大一倍！）；CMOS $=1\text{pA}\times1\text{M}\Omega=\mathbf{1\mu V}$。**必须选 CMOS/JFET**。而且 $I_b$ 每升 10°C 约翻一倍，高温下 BJT 更糟。选型判据只有一条：**看源阻抗**。低阻挑 $e_n$ 小的 BJT，高阻挑 $I_b$ 小的 CMOS/JFET。见 [12.13](p2-02-ch12.md#sec1213)。

    </details>

29. <a id="q-extra-29" data-quiz-question="true"></a>**§12.13** 轨到轨输入（RRIO）运放的互补输入对，为什么会在共模中点附近出现交越失真与失调台阶？

    <details markdown="1">
    <summary>答案</summary>

    RRIO 用 **PMOS 对 + NMOS 对**并联覆盖全共模范围，在中点附近两组对管**交接**。交接处总跨导 $g_m$ 出现凹陷（掉 20~30%），闭环增益随之波动 → **交越失真**；两组对管的 $V_{os}$ 不同 → 共模扫过中点时 $V_{os}$ 出现**台阶**。对策：① 让信号避开中点；② 选**电荷泵输入级**的真轨到轨器件（内部抬压，全程只用一组对管）；③ 用非 RRIO 但共模留足裕量的精密运放。见 [12.13](p2-02-ch12.md#sec1213)。

    </details>

30. <a id="q-extra-30" data-quiz-question="true"></a>**§13.10** 32.768kHz 的 RTC 晶体标称 $C_L=12\text{pF}$，随手焊了两只 22pF（实际 $C_L\approx15\text{pF}$，$C_0=1.5\text{pF}$、$C_1=10\text{fF}$）——每天快慢多少秒？

    <details markdown="1">
    <summary>答案</summary>

    牵引灵敏度 $S=\dfrac{C_1}{2(C_0+C_L)^2}=\dfrac{10\text{fF}}{2\times(16.5\text{p})^2}\approx\mathbf{18\ ppm/pF}$；$\Delta C_L=3\text{pF}$ → $\Delta f/f\approx55\text{ppm}$ → 每天 $55\times10^{-6}\times86400\approx\mathbf{4.8\ 秒}$。所以 $C_L$ 必须按晶体标称值反算：$C_L=\frac{C_1C_2}{C_1+C_2}+C_{stray}$，$C_{stray}\approx3\sim5\text{pF}$。见 [13.10](p2-03-ch13.md#sec1310)。

    </details>

31. <a id="q-extra-31" data-quiz-question="true"></a>**§13.10** 8MHz 晶体 $ESR=80\Omega$、$C_0=3\text{pF}$、$C_L=15\text{pF}$——起振需要的临界跨导 $g_{m,crit}$ 多少？为什么 32.768kHz 的 RTC 振荡器反而能做进 µA 级？

    <details markdown="1">
    <summary>答案</summary>

    $g_{m,crit}=4\cdot ESR\cdot(2\pi f_0)^2\cdot(C_0+C_L)^2=4\times80\times(2\pi\times8\text{M})^2\times(18\text{p})^2\approx\mathbf{0.26\ mA/V}$。32.768kHz 晶体 $ESR$ 虽高达 35~90kΩ，但 $\omega^2$ 小了约 6 万倍 → $g_{m,crit}\approx\mathbf{1.7\ \mu A/V}$——**它需要的 $g_m$ 本来就极小**，这就是 RTC 省电的根本原因。工程上还要留 **$R_{neg}\ge5\times ESR_{max}$** 的裕度。见 [13.10](p2-03-ch13.md#sec1310)。

    </details>

32. <a id="q-extra-32" data-quiz-question="true"></a>**§13.11** 3.3V 逻辑经 PC817 光耦驱动（$V_F=1.2\text{V}$、$R_{in}=1\text{k}\Omega$、该档 CTR 最小 50%、下拉 4.7kΩ 需 $I_C\ge0.7\text{mA}$）——够不够？为什么最终该选 470Ω？

    <details markdown="1">
    <summary>答案</summary>

    $I_F=(3.3-1.2)/1\text{k}=2.1\text{mA}$，按 CTR 50% → $I_C\ge1.05\text{mA}$ 有余量。但 **CTR 会随时间和温度衰减**（100°C、$I_F=20\text{mA}$ 跑 10 年可能掉一半）：若降到 25% → $I_C=0.53\text{mA}$ 拉不动。所以按"**档位最小值 × 老化余量**"设计，选 470Ω（$I_F=4.5\text{mA}$）。另：隔离侧电源必须来自隔离侧，爬电距离要看安规（250V 加强绝缘常要求 ≥5mm + 宽体封装 + 隔离槽）。见 [13.11](p2-03-ch13.md#sec1311)。

    </details>

33. <a id="q-extra-33" data-quiz-question="true"></a>**§14.8** Buck 反馈分压 $V_{out}=V_{ref}(1+R_1/R_2)$、$R_1=R_2$：电阻容差 ±1%、$V_{ref}$ 初始 ±1%、温漂 ±0.2%、负载调整率 ±0.5%——最坏情况与 RSS $3\sigma$ 各多少？规格定 ±1% 时良率大约多少？

    <details markdown="1">
    <summary>答案</summary>

    最坏情况 $=1.0+1.0+0.2+0.5=\mathbf{\pm2.7\%}$；RSS $1\sigma=\sqrt{0.24^2+0.33^2+0.07^2+0.17^2}\approx0.45\%$ → $3\sigma\approx\mathbf{\pm1.35\%}$。规格 ±1% 时需 $1/0.45=2.24\sigma$ → 良率 $=2\Phi(2.24)-1\approx\mathbf{97.5\%}$（每 1000 块约 25 块超规）；想上 99.7% 必须把某项贡献压下来（0.1% 电阻 / 更准基准）。**RSS 的 $3\sigma$ 大约只有 WC 的一半。** 见 [14.8](p3-01-ch14.md#sec148)。

    </details>

34. <a id="q-extra-34" data-quiz-question="true"></a>**§16.5** 一块板"台架上好好的、装进机箱 2 小时就复位"，开盖正常——五步法怎么走？为什么说"温度"和"耦合"缺一不可？

    <details markdown="1">
    <summary>答案</summary>

    ① 问：开盖/关盖差在**温度 + 屏蔽**，热像仪量到 45°C→68°C；② 看：复位瞬间 3.3V 有 400mV/20ns 的**尖峰**（不是塌陷）→ 是耦合不是供电不足；③ 二分：π 滤波只减半，**铜箔罩住晶振 → 尖峰消失**；④ 单变量：晶振线 12mm、与 SW 节点平行 6mm；⑤ 根因：**温度升 23°C 让晶振负阻裕度下降（起振变勉强）+ SW 的高 dV/dt 经平行走线耦合进来把振荡打停一拍**。两者缺一不可。修复：晶振贴 MCU、走线 <5mm、下方开地、四周地环；SW 面积最小化 + snubber。见 [16.5](p4-01-ch16.md#sec165)。

    </details>

---

> **做完 19 组**：把错题对应的章节重读一遍，然后挑一个 [里程碑项目](p8-03-s8-3.md) 动手。模拟电路的直觉，只从烙铁和示波器里长出来——不从阅读里长出来。
