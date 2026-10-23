# 第 10 章 模型：一条 OCV 曲线的四项

::: story 现场
BMS-Z 的合成电芯只有一行 OCV 公式，却把“电压怎么变成 SOC”讲透了：

```python
3.2 + 0.8*soc + 0.20*tanh((soc-0.05)*30) + 0.05*tanh((soc-0.90)*15)
```

SOC 0.5 时手算 3.7500 V，代码也 3.7500 V；SOC 0.05 处斜率冲到 **6.800 V/SOC**，中段回落到 **0.800**。同一个 1 mV 噪声，在陡处只换到很少的 SOC，在合成电芯的平台区却能换走一大截——EKF 的观测矩阵 $C=\mathrm{dOCV}/\mathrm{dSOC}$ 要的就是这个数。
:::

## 10.1 四项各管一段

| 项 | 作用 | 在 SOC 0.5 的贡献 |
|---|---|---|
| `3.2` | 基准平台 | 3.2000 V |
| `0.8*soc` | 中段斜率 | 0.4000 V |
| `0.20*tanh((soc-0.05)*30)` | 低 SOC 抬头 | 0.2000 V（已饱和） |
| `0.05*tanh((soc-0.90)*15)` | 高 SOC 抬头 | −0.0500 V |

加起来 3.7500 V。注意 `3.2` 不是“0% 时的实际电压”：SOC=0 时低端 tanh 取到下限 −0.20，实际 OCV 是 2.9690 V。

::: principle 一句话
**常数是基准，斜率管中段，两个 tanh 管两头。** 一条曲线不是“拟合出来的”，是四个可解释的部分叠出来的。
:::

## 10.2 R0：电流一加就掉的那一下

<section class="book-lab" data-book-lab="ocv" v-book-lab aria-label="OCV 四项交互实验">
<h4>把曲线拆开：拖动 SOC 和中段斜率</h4>
<p class="lab-note">教学合成模型。改变斜率后，端点和中段都会改变；5 mV 换算只是局部敏感度，不是滤波器实际修正。</p>
<div class="lab-controls">
<label>SOC（0–1）：<span data-value="soc">0.50</span><input type="range" data-param="soc" min="0" max="1" step="0.01" value="0.50" disabled></label>
<label>中段斜率（V/SOC）：<span data-value="slope">0.8</span><input type="range" data-param="slope" min="0.05" max="1.2" step="0.05" value="0.8" disabled></label>
</div>
<svg viewBox="0 0 720 330" role="img" aria-label="合成 OCV 曲线与当前 SOC 游标">
<path d="M60 30V270H660" fill="none" stroke="currentColor" opacity="0.5"/>
<text x="18" y="26" fill="currentColor" font-size="14">OCV / V</text><text x="605" y="315" fill="currentColor" font-size="14">SOC →</text>
<text x="30" y="276" fill="currentColor" font-size="12">2.8</text><text x="30" y="90" fill="currentColor" font-size="12">4.2</text>
<text x="60" y="292" fill="currentColor" font-size="12">0</text><text x="355" y="292" fill="currentColor" font-size="12">0.5</text><text x="652" y="292" fill="currentColor" font-size="12">1</text>
<rect data-band x="60" y="142.5" width="600" height="8" fill="#d97706" opacity="0.18"/>
<polyline data-curve points="60,248 90,219 120,190 180,178 300,157 360,146.5 480,126 600,102 660,82" fill="none" stroke="#2563eb" stroke-width="3"/>
<circle data-cursor cx="360" cy="146.5" r="7" fill="#d97706"/>
</svg>
<div class="lab-readouts"><span>OCV：<output data-output="voltage">3.7500 V</output></span><span>斜率：<output data-output="derivative">0.800 V/SOC</output></span><span>5 mV 局部换算：<output data-output="error">0.63 个百分点</output></span></div>
<p>四项相加：<output data-output="terms">3.2000 + 0.4000 + 0.2000 − 0.0500 V</output></p>
<p class="visual-question"><strong>试着推翻直觉：</strong>把 SOC 移到 0.05，再移到 0.50；电压噪声没变，为什么换算的 SOC 区间变了？把斜率调小后，两端陡区是否也消失？</p>
</section>

端电压：

$$
U = \mathrm{OCV} + I R_0 + U_{rc}
$$

BMS-Z 的电芯 $R_0=20\ \mathrm{m\Omega}$。2 A 充电，台阶 $2 \times 0.020 = 40\ \mathrm{mV}$，手算与代码逐位相同。

R0 不是“状态”，是型号与老化的属性。它随温度下降而上升，随老化而上升。参数表写错 R0，后果比写错 C1 严重得多——下一节有数字。

## 10.3 RC：拖尾巴的那一段

一阶 RC 的离散递推：

$$
U_{rc,k+1} = e^{-\Delta t/\tau} U_{rc,k} + R_1\left(1-e^{-\Delta t/\tau}\right) I_k, \quad \tau=R_1C_1
$$

这个 `exp(-dt/τ)` 不是经验公式，是连续方程在零阶保持下的精确解。它决定了“撤流后电压多久回弹”：工程上常说等 **3–4 个 τ** 才接近稳态。

<figure class="book-motion" data-animation="rc-step-r0-tail.svg" data-mode="static">
<img src="../assets/print/rc-step-r0-tail.svg" alt="电压阶跃分解：20 A、2 mΩ 产生 40 mV 立刻压降，RC 拖尾再发展；该动画参数与本章 2 A 示例不同。" data-motion-src="../../docs/circuits/assets/rc-step-r0-tail.svg">
<button type="button" data-book-motion v-book-motion aria-pressed="false" hidden>播放动画</button>
<figcaption>图 10-1　电压阶跃分解：20 A、2 mΩ 产生 40 mV 立刻压降，RC 拖尾再发展；该动画参数与本章 2 A 示例不同。</figcaption>
<p class="visual-guide"><strong>先看哪里：</strong>盯住开始和撤流两次竖直跳变，再看中间弯曲拖尾：R0 与 RC 不住在同一个时间位置。</p>
<p class="visual-question"><strong>看完追问：</strong>撤流后立刻跳回的幅值应如何与开始阶跃对账？为什么末端总压差不能全叫 R0？</p>
</figure>

## 10.4 参数写错，谁会当场崩

BMS-Z 的合成对照中，把 R0 写大 10 倍，SOC RMSE 为 **41.51%**；把 C1 写大 10 倍，为 **1.00%**。这些是该工况下的 SOC 估计误差，不是电压 RMSE。

| 参数 | 写大 10 倍后的 SOC RMSE | 说明 |
|---|---:|---|
| R0 | 41.51% | 每一拍的台阶都错，误差立刻显形 |
| C1 | 1.00% | 只改变弛豫时间，短窗内影响小 |

这不是说 C1 不重要，而是说：**先修 R0，再修 C1。** 调参要有优先级，否则你会在一堆等效的参数组合里迷路。

::: trap 坑
用一条“看起来很顺”的拟合曲线代替参数辨识。曲线能对上，参数可能全错；换一个工况，误差立刻爆炸。**拟合优度不是参数正确性。**
:::

::: lab 动手
去 BMS-Z 跑“电芯建模五天”第 1 天的命令，把 OCV 拆成四项；再把中段斜率从 0.8 改成 0.4，算 SOC 0.5 的 OCV。然后跑第 5 天“把模型改坏”，观察 R0 与 C1 的差异。
:::

## 练习

1. 写出 OCV 公式在 SOC=0、0.05、0.5、1.0 的值，并解释每一段的主导项。
2. 为什么 `exp(-dt/τ)` 能等价于连续世界？用一句话说明“零阶保持”。
3. R0 与 C1 各写大 10 倍，为什么误差差这么多？从“每一拍”与“时间常数”两个角度解释。

## 参考资料

- BMS-Z 电芯建模五天：https://github.com/zhuguang-ZFG/BMS-Z/blob/main/docs/共学/09-电芯建模五天.md
- BMS-Z `cell_model.py`：https://github.com/zhuguang-ZFG/BMS-Z/blob/main/code/soc/cell_model.py
- BMS-Z 阶段 4：https://github.com/zhuguang-ZFG/BMS-Z/blob/main/docs/stages/stage-4-SOC-SOH算法.md
- Chen & Rinçón-Mora《Accurate Electrical Battery Model Capable of Predicting Runtime and I–V Performance》（IEEE Transactions on Energy Conversion, 21(2), 2006）：能同时预测续航与 I–V 特性的电模型经典论文，本章模型四项的参考蓝本
