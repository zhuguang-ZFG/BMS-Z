# 第 27 章 EKF 的六个矩阵

::: story 现场
同一段工况、同一个种子 42：纯库仑计的整段 RMSE 是 **10.6183%**，EKF 是 **0.2004%**。

但 BMS-Z 在同一页写了一句更重要的提醒：这个 0.20% 是“最好情形”——EKF 拿到的 R0/R1/C1 与 OCV 曲线和“真值电芯”完全相同，只有容量、初值和零漂是错的。真电池上参数未知还会变，**这个数不能当作真电池精度**。

看懂这句话，比记住 0.20% 更有价值。
:::

## 27.1 两个状态，两句话

状态：

$$
x = \begin{bmatrix} SOC \\\\ U_{rc} \end{bmatrix}
$$

预测：

$$
x^- = A x + B I, \quad P^- = A P A^T + Q
$$

更新：

$$
S = C P^- C^T + R, \quad K = P^- C^T S^{-1}
$$

$$
x = x^- + K(z - h(x^-)), \quad P = (I - KC)P^-
$$

其中：

$$
A = \begin{bmatrix} 1 & 0 \\\\ 0 & e^{-\Delta t/\tau} \end{bmatrix}, \quad
B = \begin{bmatrix} \frac{\Delta t}{3600 Q} \\\\ R_1(1-e^{-\Delta t/\tau}) \end{bmatrix}
$$

$$
C = \begin{bmatrix} \frac{\mathrm{dOCV}}{\mathrm{dSOC}} & 1 \end{bmatrix}
$$

<figure>
<img src="../assets/ekf-loop.svg" alt="EKF 预测与更新循环：预测状态与协方差，再用电压残差修正">
<figcaption>图 27-1　EKF 的一拍：预测把状态推进一步，更新用电压残差把它拉回；Q 与 R 决定更信谁。</figcaption>
</figure>

::: principle 一句话
**预测负责“跟着电流走”，更新负责“被电压拉回”。** Q 与 R 不是玄学，是“你更信谁”的两个旋钮。
:::

## 27.2 BMS-Z 的六个矩阵

它的 `EKFEstimator` 用的是这些值：

| 矩阵 | 值 | 含义 |
|---|---|---|
| $P_0$ | `diag(1e-2, 1e-4)` | 初始不确定度：SOC 约 ±10%，U_rc 很小 |
| $Q$ | `diag(2e-6, 1e-7)` | 每秒过程噪声 |
| $R$ | `2.5e-5` V² | 测量噪声，约 5 mV |
| $A$ | `diag(1, exp(-dt/τ))` | 状态转移 |
| $B$ | `[dt/(3600Q), R1(1-exp(-dt/τ))]` | 电流输入 |
| $C$ | `[dOCV/dSOC, 1]` | 观测敏感度 |

注意 $R$ 的单位：5 mV 是标准差，方差是 $(5\times10^{-3})^2=2.5\times10^{-5}$。若把以伏表示的标准差 `0.005` 直接填进 $R$，方差会被放大 200 倍，相当于约 70.7 mV 的标准差；滤波器会降低对测量的信任。单位与平方都要核对。

## 27.3 增益自己会走到一个平台

BMS-Z 的一维示例：

- $R=0.001$：第一步 $K=0.9758$，后来收到 **0.4633**；
- $R=0.020$：平台收到 **0.1318**；
- 把 $Q$ 从 0.0004 提到 0.0016：平台更高——过程更吵，就多听测量。

平台区的观测敏感度大约 **0.75 mV / 1% SOC**。测量越吵，或平台越平，$K$ 就应该越小；否则噪声会灌进 SOC。

## 27.4 自己跑一遍

`code/ekf_soc.py` 用同一套思路做了个最小实验：

- 真值电芯 9.5 Ah，模型 10 Ah；初值 0.70 vs 真值 0.80；电流偏置 +2 mA；
- 测量噪声为幅值 5 mV 的确定性正弦，RMS 约 3.54 mV；滤波器仍按 5 mV 标准差设置 R，便于复现；
- 结果：纯库仑 RMSE **9.4605%**，EKF **0.1382%**。

它和 BMS-Z 的 10.6183% / 0.2004% 不完全相同，因为工况与噪声不同；但结论一致：**同样的错误初值、容量误差与零漂，EKF 能把误差压到 1% 以内**——前提是模型参数与 OCV 曲线可信。

::: trap 坑
把 EKF 当成“自动修正一切”。它只能修正它“看得见”的状态；容量、R0、OCV 曲线如果错了，残差会一直偏，滤波器可能收敛到一个错误但自洽的 SOC。
:::

::: lab 动手
跑 `python code/ekf_soc.py`。然后把 `bias` 从 0.002 改成 0.02，观察 RMSE；再把 `q00` 从 2e-6 改成 2e-4，看曲线是更跟测量还是更抖。
:::

## 练习

1. 写出 $A$、$B$、$C$ 的维度，并解释为什么 $C$ 的第二项是 1。
2. $R=2.5e-5$ 对应多少 mV 的标准差？如果实际噪声是 20 mV，$R$ 应该填多少？
3. 为什么容量误差不会像初值误差那样被 EKF 很快修掉？

## 参考资料

- BMS-Z 阶段 4 §4.5：https://github.com/zhuguang-ZFG/BMS-Z/blob/main/docs/stages/stage-4-SOC-SOH算法.md
- BMS-Z `estimators.py`：https://github.com/zhuguang-ZFG/BMS-Z/blob/main/code/soc/estimators.py
- Plett ECE5720：http://mocha-java.uccs.edu/ECE5720/index.html
- Plett《Battery Management Systems》Vol. II（Artech House, 2016）：等效电路方法与 Kalman 滤波状态估计体系，本章 EKF 六个矩阵的理论出处
