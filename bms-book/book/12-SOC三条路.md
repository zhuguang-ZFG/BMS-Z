# 第 12 章 SOC：三条路与三个锚点

::: story 现场
同一段工况，三种 SOC 估算器跑出三条曲线：

- **纯库仑计**：短时最准，长时间必漂；
- **库仑 + 复位**：靠满充和静置 OCV 两个锚点把漂移拉回；
- **EKF**：每一拍用电压残差修正，不需要等静置。

它们的分歧不在“积分”，而在**怎么校正**。BMS-Z 的 `compare.py` 把这三条线画在同一张图上，分叉的位置就是答案。
:::

<figure>
<img src="../assets/soc-tradeoff.svg" alt="纯库仑、复位校正与 EKF 三条 SOC 曲线的对比示意">
<figcaption>图 12-1　三条 SOC 曲线。纯库仑越跑越偏；复位锚点把误差拉回；EKF 用每拍残差修正。</figcaption>
</figure>

## 12.1 库仑计数

$$
SOC_k = SOC_{k-1} + \frac{\eta I_k \Delta t}{3600 Q}
$$

充电为正，所以充电时 SOC 上升。$Q$ 用 Ah，$\Delta t$ 用秒；单位错一个，结果差几个数量级。

优点：短时精度高、动态响应快。

缺点：纯积分，误差累积。电流零点偏置、容量误差、采样丢失都会变成永久漂移。

一个 100 Ah pack，0.1 A 偏置，静置 10 天 → 24% 漂移。这不是实现缺陷，是方案属性：**纯积分没有校正通道。**

## 12.2 两个锚点

**满充复位**：高压 + 电流衰减到截止值 → 必然满电。

**静置 OCV 复位**：|I| 小于阈值持续 N 分钟 → 查 OCV–SOC 表。

BMS-Z 的实现里有两个容易漏的细节：

1. 静置计时是**双向去抖**：普通超限采样让计时回退，避免噪声每次都清零。
2. 满充校准明确说明“仍在充电”，必须清掉旧静置计时；撤流后重新等够窗口，不能一拍就用 OCV 覆盖满充结果。

## 12.3 EKF：用电压残差拉回

状态 $x=[SOC, U_{rc}]$，观测：

$$
z = \mathrm{OCV}(SOC) + I R_0 + U_{rc} + v
$$

每拍：

1. 用电流预测状态与协方差；
2. 用 $C=[\mathrm{dOCV}/\mathrm{dSOC}, 1]$ 线性化观测；
3. 算残差、增益、修正。

同一个 15 mV 残差，在 SOC 0.05 处 $C=6.8$ V/SOC，只对应 0.2% SOC；在合成电芯的平台区 $C=0.8$ V/SOC，就是 1.9%。**同一个电压差，在不同工作点含义完全不同。**

::: principle 一句话
**库仑计负责“连续”，锚点负责“不跑飞”，EKF 负责“每拍拉一把”。** 三者不是互斥，是分工。
:::

## 12.4 三条路的取舍

| 方案 | 优点 | 缺点 | 适用 |
|---|---|---|---|
| 纯库仑 | 简单、短时准 | 必漂 | 短时任务、受控充电 |
| 库仑 + 复位 | 可解释、可测试 | 依赖满充/静置 | 储能、可定期校准 |
| EKF | 动态好、无需静置 | 依赖模型与参数 | 车用、宽工况 |

BMS-Z 的结论很务实：先把库仑与锚点做对，再上 EKF。**没有好的 OCV 表和参数，EKF 只是把错误模型算得更平滑。**

::: trap 坑
把“参考 SOC”当成“真值”。如果参考值是用同一路电流积分出来的，它和你的估算器共享误差源；报告里必须标注 `independent_soc_truth: false`（JSON 报告字段；同名字段在 Python 代码里写作 `False`）。
:::

::: lab 动手
跑 `python code/soc_coulomb_ocv.py`，对比纯积分、OCV 校正、电流偏置、容量误差四组结果。再把偏置从 0.05 A 改成 0.2 A，观察漂移。最后去 BMS-Z 跑 `compare.py --plot`，看三条曲线的分叉点。
:::

## 练习

1. 推导库仑计在 0.1 A 偏置下 10 天的漂移，并解释为什么“静置校正”能救它。
2. 为什么满充复位后要清掉静置计时？如果不清，会发生什么？
3. 同一个 15 mV 残差，在 $C=6.8$ 与 $C=0.8$ 时各对应多少 SOC 误差？

## 参考资料

- BMS-Z 阶段 4：https://github.com/zhuguang-ZFG/BMS-Z/blob/main/docs/stages/stage-4-SOC-SOH算法.md
- BMS-Z `estimators.py`：https://github.com/zhuguang-ZFG/BMS-Z/blob/main/code/soc/estimators.py
- BMS-Z 无真值诊断：https://github.com/zhuguang-ZFG/BMS-Z/blob/main/docs/共学/10-无真值诊断五天.md
- Plett《Battery Management Systems》Vol. I（Artech House, 2015）：电芯建模与状态估计的完整体系，本章 SOC 三条路的理论框架出处
