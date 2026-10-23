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

## 14.2 闭式公式为什么偏乐观

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
\Delta T(\omega) = \frac{\dot{Q}(\omega)}{1 + j\omega\tau_{\text{th}}}, \quad \tau_{\text{th}}=R_{\text{th}}C_{\text{th}}
$$

BMS-Z 的 `thermal_demo.py` 给出两个可记的结论：

- 正弦生热的幅值被压缩 $1/\sqrt{1+(\omega\tau)^2}$，相位滞后 $\arctan(\omega\tau)$；
- 生热纹波在 **2ω**（因为 $I^2$），所以电流频率翻倍后，温度才跟上。

::: principle 一句话
**功率限制要预测温升，而不是等温度到上限。** 温度慢半拍，等它到线，极化早就撞墙了。
:::

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
