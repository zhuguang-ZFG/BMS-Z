# 第 14 章 SOP 与热：三约束取最小，温度慢半拍

::: story 现场
一辆车在 0 °C 的早晨请求 200 kW。BMS 看着 SOC 80%、电压正常，就放行；十秒后单体电压掉到下限，功率被硬切。司机感受到的是“突然没劲”，电芯感受到的是“一次不必要的深度极化”。

SOP 不是“当前能出多大电流”，而是“未来 N 秒内，在电压、电流、温度、SOC 四个墙都不撞的前提下，能出多大功率”。
:::

## 14.1 三个约束，取最紧

BMS-Z 的 `sop_demo.py` 把约束写成三条：

1. **电压墙**：端电压不能越过上/下限（含极化预测）；
2. **SOC 墙**：不能把 SOC 用到窗口外；
3. **电流帽**：电芯、连接器、熔断器、接触器的最大电流。

对每个候选电流，前向仿真整个时间窗，检查末态电压与 SOC；取满足所有约束的最大值。**三约束取最小，不是取平均。**

<figure class="book-motion" data-animation="sop-voltage-limit.svg" data-mode="static">
<img src="../assets/print/sop-voltage-limit.svg" alt="电压墙限制放电幅值：允许电流由 OCV 到 Vmin 的余量和等效阻抗决定。放电幅值取正，参数为示意。" data-motion-src="../../docs/circuits/assets/sop-voltage-limit.svg">
<button type="button" data-book-motion v-book-motion aria-pressed="false" hidden>播放动画</button>
<figcaption>图 14-1　电压墙限制放电幅值：允许电流由 OCV 到 Vmin 的余量和等效阻抗决定。放电幅值取正，参数为示意。</figcaption>
<p class="visual-guide"><strong>先看哪里：</strong>SOC 接近下限时，电压余量缩小，允许电流被压向零；高 SOC 也仍受电流帽限制。</p>
<p class="visual-question"><strong>看完追问：</strong>在相同 OCV 下把电阻加倍，电压墙允许电流会怎样变化？发热能否只看这个电流？</p>
</figure>

## 14.2 闭式公式为什么偏乐观

<section class="book-lab" data-book-lab="sop" v-book-lab aria-label="SOP 三约束交互实验">
<h4>三堵墙，谁最先挡住电流？</h4>
<p class="lab-note">10 Ah 合成电芯，Vmin=2.8 V、SOC 下限 0.10、电流帽 30 A；固定 OCV 与 Rint，未计 RC、OCV 随 SOC 变化或温升反馈，不能当产品功率承诺。功率为单电芯端口值。</p>
<div class="lab-controls">
<label>OCV / V：<span data-value="ocv">3.7</span><input type="range" data-param="ocv" min="3" max="4.2" step="0.05" value="3.7" disabled></label>
<label>R / mΩ：<span data-value="resistance">20</span><input type="range" data-param="resistance" min="10" max="100" step="5" value="20" disabled></label>
<label>SOC：<span data-value="soc">0.5</span><input type="range" data-param="soc" min="0.11" max="0.95" step="0.01" value="0.5" disabled></label>
<label>预测窗 / s：<span data-value="horizon">600</span><input type="range" data-param="horizon" min="10" max="1200" step="10" value="600" disabled></label>
</div>
<svg viewBox="0 0 720 240" role="img" aria-label="电压墙、SOC 墙与电流帽的允许电流条形比较">
<text x="20" y="45" fill="currentColor" font-size="17">电压墙</text><rect data-bar="0" x="130" y="20" width="211.5" height="35" rx="5" fill="#2563eb"/>
<text x="20" y="105" fill="currentColor" font-size="17">SOC 墙</text><rect data-bar="1" x="130" y="80" width="112.8" height="35" rx="5" fill="#0f766e"/>
<text x="20" y="165" fill="currentColor" font-size="17">电流帽</text><rect data-bar="2" x="130" y="140" width="141" height="35" rx="5" fill="#b45309"/>
<text x="130" y="215" fill="currentColor" font-size="13">条长按 0–100 A 显示，超过 100 A 截顶；精确值见下方。</text>
</svg>
<div class="lab-readouts"><span>电压：<output data-output="limit-0">45.0 A</output></span><span>SOC：<output data-output="limit-1">24.0 A</output></span><span>硬件：<output data-output="limit-2">30.0 A</output></span></div>
<div class="lab-readouts"><span>允许：<output data-output="current">24.0 A</output></span><span>主导：<output data-output="binding">SOC 墙</output></span><span>端电压：<output data-output="terminal">3.220 V</output></span></div>
<div class="lab-readouts"><span>端口功率：<output data-output="power">77.3 W</output></span><span>欧姆生热：<output data-output="heat">11.5 W</output></span></div>
<p class="visual-question"><strong>试三次：</strong>缩短预测窗，看主导约束如何切换；把 R 增到 60 mΩ，看电压墙如何收紧；再降低 SOC，检查发热是否仍按同样方向变化。解释“电流取最小”与“功率取平均”为什么不同。</p>
</section>

常见的 Rint 近似：

$$
P_{\text{dis}} \approx \frac{V_{\text{ocv}} - V_{\min}}{R} \cdot V_{\min}
$$

它只用了“此刻”的 OCV 与 R，忽略了：

- RC 极化的积累；
- OCV 随 SOC 下降；
- 温度变化导致 R 上升；
- 电流帽与线束压降。

所以闭式值通常偏乐观。BMS-Z 的对照是：闭式除法 vs 二分 + 前向仿真，后者更保守，也更接近真实可用功率。

## 14.3 热：温度是慢变量，但会否决一切

产热：

$$
\dot{Q} \approx I^2 R + I \cdot T \frac{\partial U_{\text{ocv}}}{\partial T}
$$

第一项是欧姆热，第二项是熵热（可正可负）。温度响应是一个低通：

$$
\Delta T(\omega) = \frac{R_{\text{th}}\dot{Q}(\omega)}{1 + j\omega\tau_{\text{th}}}, \quad \tau_{\text{th}}=R_{\text{th}}C_{\text{th}}
$$

BMS-Z 的 `thermal_demo.py` 给出两个可记的结论：

- 正弦生热的幅值被压缩 $1/\sqrt{1+(\omega\tau)^2}$，相位滞后 $\arctan(\omega\tau)$；
- 生热纹波在 **2ω**（因为 $I^2$），所以电流频率翻倍后，温度才跟上。

::: principle 一句话
**功率限制要预测温升，而不是等温度到上限。** 温度慢半拍，等它到线，极化早就撞墙了。
:::

<figure class="book-motion" data-animation="thermal-paths.svg" data-mode="static">
<img src="../assets/print/thermal-paths.svg" alt="从产热到散热：电芯、界面和冷却介质构成热路径；温度变化滞后于生热。示意结构不代表具体模组。" data-motion-src="../../docs/circuits/assets/thermal-paths.svg">
<button type="button" data-book-motion v-book-motion aria-pressed="false" hidden>播放动画</button>
<figcaption>图 14-2　从产热到散热：电芯、界面和冷却介质构成热路径；温度变化滞后于生热。示意结构不代表具体模组。</figcaption>
<p class="visual-guide"><strong>先看哪里：</strong>按路径看温差在哪里积累：传感器读到的是安装位置温度，未必是内部最高温度。</p>
<p class="visual-question"><strong>看完追问：</strong>热阻加大与热容加大分别改变稳态温升还是时间常数？</p>
</figure>

## 14.4 工程落地

- 10 秒峰值与持续功率是两张表，不能混用；
- 低温充电单独限流（析锂风险），必要时先加热；
- 温度传感器要覆盖最热与最冷点；
- SOP 要随 SOH 更新（内阻涨了，同样功率下压降更大）；
- 故障时 SOP 归零，而不是“降一点”。

::: trap 坑
只用单体电压算 SOP，忽略连接器与线束压降。pack 级 200 A 时，1 mΩ 的连接电阻就是 0.2 V——足以让“看起来还能放”的功率变成过放。
:::

::: lab 动手
跑 BMS-Z 的 `python code/soc/sop_demo.py` 与 `thermal_demo.py`。前者打印 6 个 SOC 点 × 3 档时间窗的对照；后者给出稳态温度、τ 与正弦低通。把时间窗从 10 秒改成 30 秒，观察 SOP 怎么变。
:::

## 练习

1. 用 Rint 公式算 25 °C、SOC 50%、R=1 mΩ 时的放电功率，再与“加 RC 极化”的结果比较，解释差异。
2. 为什么生热纹波在 2ω？如果电流是 1 Hz 方波，温度主要跟哪个频率走？
3. 设计一个低温充电策略：温度 < 5 °C 时，电流上限怎么随温度变化？

## 参考资料

- BMS-Z SOP 五天：https://github.com/zhuguang-ZFG/BMS-Z/blob/main/docs/共学/05-sop五天.md
- BMS-Z 热五天：https://github.com/zhuguang-ZFG/BMS-Z/blob/main/docs/共学/06-热五天.md
- BMS-Z `sop_demo.py` / `thermal_demo.py`：https://github.com/zhuguang-ZFG/BMS-Z/tree/main/code/soc
