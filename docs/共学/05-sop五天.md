# 共学：SOP 五天

> **本篇你会学到**　「此刻还能出多大的力」怎么算：多约束取最小、闭式除法为什么偏乐观、时间窗为什么越长越紧，以及 SOC 墙怎么让简单方法漏报。
> **预计用时**　5 天，每天大约 30–60 分钟。
> **前置**　做过 [SOC 五天](01-soc五天.md) 或读过阶段 4 §4.4–§4.5。装好 Python 3.10+，在仓库根执行过 `pip install -r code/requirements.txt`。不接电池。

⚠️ 表里的安培全是一颗合成教学电芯（3 Ah、R0 33 mΩ、R1 16 mΩ、τ≈35 s）的模型输出，不是任何真实电芯的峰值能力。闭式法与二分法的差别是**方法**差别，不是产品精度；产品 SOP 要拿规格书和实测参数算。

## 本页目录

- [第 1 天　三个约束，取最紧的那个](05-sop五天.md#第-1-天三个约束取最紧的那个)
- [第 2 天　闭式除法：一条代数式算到底](05-sop五天.md#第-2-天闭式除法一条代数式算到底)
- [第 3 天　闭式偏乐观：它看不见未来](05-sop五天.md#第-3-天闭式偏乐观它看不见未来)
- [第 4 天　SOC 墙：简单方法漏报的地方](05-sop五天.md#第-4-天soc-墙简单方法漏报的地方)
- [第 5 天　充电侧是同一道题](05-sop五天.md#第-5-天充电侧是同一道题)

## 第 1 天：三个约束，取最紧的那个

**读**　[阶段 4 §4.7](../stages/stage-4-SOC-SOH算法.md#47-sop电池此刻能出多大力-分析) 开头那条约束清单：电压、电流、SOC、温度——SOP 是它们取最小值，不是挑一个最好的。

**看**　[SOP 多约束降额动画](../circuits/assets/sop-derating.svg)。红线永远卡在最矮的柱子上：能出多大力，看最短的那条约束。

**跑**（在仓库根）：

```bash
python3 code/soc/sop_demo.py
```

PowerShell：

```powershell
python code/soc/sop_demo.py
```

2026-10-09 在本仓库跑通（Python 3.13、numpy 2.5，约 1 秒），表格是：

```text
  SOC |   HPPC 闭式 | 二分  2s | 二分 10s | 二分 30s
------------------------------------------------------------------------
 0.90 |    33.9 A |  15.00帽   |  15.00帽   |  15.00帽
 0.70 |    27.6 A |  15.00帽   |  15.00帽   |  15.00帽
 0.50 |    22.7 A |  15.00帽   |  15.00帽   |  15.00帽
 0.30 |    17.9 A |  15.00帽   |  15.00帽   |  13.29压
 0.15 |    14.2 A |  13.77压   |  12.41压   |  10.46压
 0.12 |    13.3 A |  12.91压   |  11.53压   |   7.19墙
```

记号含义：帽 = 系统电流帽先咬住；压 = 电压约束咬住；墙 = SOC 墙咬住。末尾还有六行自验收，应全部 `[PASS]`。

**交**　贴 0.90 和 0.12 两行原文，加一句：这两行各自被哪条约束咬住、闭式法分别报了多少。

**口诀**　多约束取最小。最矮的柱子说了算。

**今天你解锁了**　你在自己电脑上跑完了一次 SOP 双法对照，并能在表里指出每一行是谁在管着。

**短自测**　0.90 那行闭式报 33.9 A，为什么二分只给 15 A？

<details>
<summary>先自己答再展开</summary>

33.9 A 只过了电压这一关。系统电流帽 15 A 是另一条约束，SOP 取最小——闭式除法天生只看电压，别的柱子它不管。
</details>

## 第 2 天：闭式除法：一条代数式算到底

**读**　[§4.7](../stages/stage-4-SOC-SOH算法.md#47-sop电池此刻能出多大力-分析) 的电压约束公式：$|I_{\text{放}}| \le \dfrac{U_{oc} + U_{RC} - U_{min}}{R_0}$。静置出发时 $U_{RC}=0$，整条式子只剩一次除法。

**看**　[电压限位下的峰值电流](../circuits/assets/sop-voltage-limit.svg)。平台上电流几乎不动，快放空就掉到零——分子（OCV 减下限）决定一切。

**跑**（手算对账：SOC 0.50、OCV 3.75 V、下限 3.00 V、R0 33 mΩ）：

```bash
python3 -c "import sys; sys.path.insert(0,'code/soc'); import sop_demo; print(round(sop_demo.hppc_current(0.50),1),'A')"
```

PowerShell：

```powershell
python -c "import sys; sys.path.insert(0,'code/soc'); import sop_demo; print(round(sop_demo.hppc_current(0.50),1),'A')"
```

2026-10-09 输出：

```text
22.7 A
```

和第 1 天表格 0.50 行的闭式列一致。

**交**　先在纸上用公式算 0.50 点（3.75 − 3.00 再除以 0.033），再贴脚本输出，写一句两者差多少。

**口诀**　电压墙先算一截。平台上几乎不动，快放空掉到零。

**今天你解锁了**　你手算过一条闭式 SOP，并知道脚本和你用的是同一条代数式。

## 第 3 天：闭式偏乐观：它看不见未来

**读**　[§4.7](../stages/stage-4-SOC-SOH算法.md#47-sop电池此刻能出多大力-分析) 里新加的那段演示对照：闭式只看此刻的 OCV 和内阻；二分每猜一个电流，就把一阶 RC 模型向前仿真 ΔT 秒——极化还在积累，SOC 还在掉。

**看**　[阶跃 R0 与 RC 尾巴](../circuits/assets/rc-step-r0-tail.svg)。电流一加 R0 立刻压降，RC 慢慢跟上——闭式只算了第一下，没算尾巴。

**跑**（0.15 点、闭式 vs 三档时间窗的二分）：

```bash
python3 -c "import sys; sys.path.insert(0,'code/soc'); import sop_demo; h=sop_demo.hppc_current(0.15); [print(f'{int(t)}s: bisect {sop_demo.bisect_current(0.15,t)[0]:.2f} A, hppc 高 {100*(h/sop_demo.bisect_current(0.15,t)[0]-1):.1f}%') for t in sop_demo.WINDOWS_S]"
```

PowerShell：

```powershell
python -c "import sys; sys.path.insert(0,'code/soc'); import sop_demo; h=sop_demo.hppc_current(0.15); [print(f'{int(t)}s: bisect {sop_demo.bisect_current(0.15,t)[0]:.2f} A, hppc 高 {100*(h/sop_demo.bisect_current(0.15,t)[0]-1):.1f}%') for t in sop_demo.WINDOWS_S]"
```

2026-10-09 输出：

```text
2s: bisect 13.77 A, hppc 高 3.2%
10s: bisect 12.41 A, hppc 高 14.5%
30s: bisect 10.46 A, hppc 高 35.9%
```

**交**　贴三行输出，写一句：为什么窗越长，闭式高得越多。

**口诀**　闭式只看此刻。窗越长，尾巴越长。

**今天你解锁了**　你能把「偏乐观」从一句结论变成三个百分比，并指出乐观的来源是没算极化累积。

**短自测**　为什么 2 s 窗只高 3.2%？

<details>
<summary>先自己答再展开</summary>

τ≈35 s。2 s 里极化只来得及爬到稳态的 1−exp(−2/35)≈6%，闭式漏掉的那部分本来就小；30 s 爬到 63%，漏掉的就成了大头。
</details>

## 第 4 天：SOC 墙：简单方法漏报的地方

**读**　[ECE5720 Notes06 中文导读 §五](../ece5720-notes06-中文导读.md#五40-串的例子65)：二分法加了 SOC 边界，低 SOC 时简单法差得远；按乐观值放电，有的工况会过放。

**看**　[OCV–SOC 曲线](../circuits/assets/ocv-soc-curve.svg) 的左端：快放空时 OCV 掉头向下，跌破下限后闭式直接给 0——但墙其实更早就在那儿了（可用电荷除以窗长）。

**跑**（0.12 点、30 s 窗，闭式 vs 二分）：

```bash
python3 -c "import sys; sys.path.insert(0,'code/soc'); import sop_demo; print(f'hppc {sop_demo.hppc_current(0.12):.1f} A vs bisect {sop_demo.bisect_current(0.12,30.0)[0]:.2f} A ({sop_demo.bisect_current(0.12,30.0)[1]})')"
```

PowerShell：

```powershell
python -c "import sys; sys.path.insert(0,'code/soc'); import sop_demo; print(f'hppc {sop_demo.hppc_current(0.12):.1f} A vs bisect {sop_demo.bisect_current(0.12,30.0)[0]:.2f} A ({sop_demo.bisect_current(0.12,30.0)[1]})')"
```

2026-10-09 输出：

```text
hppc 13.3 A vs bisect 7.19 A (SOC墙)
```

墙的账：SOC 0.12 距墙 0.10 还有 0.02，3 Ah 电芯就是 216 库仑；30 s 窗最多放 216/30 = 7.2 A。闭式报 13.3 A——按它放电，窗还没走完就穿墙过放。

**交**　贴输出，再自己算一遍 0.12 点的墙电流（0.02 × 3 Ah × 3600 s/h ÷ 30 s），写一句你的数和脚本的差多少。

**口诀**　墙是可用电荷除以窗长。闭式看不见它。

**今天你解锁了**　你用一次手算复现了 SOC 墙，并知道「偏乐观」在最贴墙的地方会变成「漏报」。

## 第 5 天：充电侧是同一道题

**读**　[§4.7b 充电地图](../stages/stage-4-SOC-SOH算法.md#47b-充电地图把析锂温度sop-合成一条允许电流-应用) 的那张四行表：析锂边界、温度窗口、电压限幅、SOP 与老化——四个数取最小。充电侧的电压限幅是 $|I_{\text{充}}| \le (U_{max} - U_{oc}) / R_0$，和放电同型。

**看**　[充电电流随温度降额](../circuits/assets/temp-ichg-derate.svg)。低温硬充容易析锂，0 °C 以下直接归零——充电侧比放电侧多一堵电化学的墙。

**跑**（手算对账：SOC 0.90、上限 4.20 V、OCV 4.12 V、R0 33 mΩ；仓库演示刻意留白充电侧，这题你自己算）：

先在纸上算 $(4.20 - 4.12) / 0.033$，再用一条命令核对：

```bash
python3 -c "print(round((4.20-4.12)/0.033,1),'A')"
```

PowerShell：

```powershell
python -c "print(round((4.20-4.12)/0.033,1),'A')"
```

2026-10-09 输出：

```text
2.4 A
```

**交**　贴你的手算和命令输出，写一句：为什么 SOC 0.90 的充电上限（2.4 A）比放电上限（第 1 天表里 0.90 行的 15 A）小这么多。

**口诀**　充电侧同一道题，换个方向、换堵墙。

**今天你解锁了**　你把闭式 SOP 用到了充电侧，并知道真正的充电允许电流还要再和析锂、温度一起取最小。

**短自测**　为什么仓库演示不直接把充电侧写进 sop_demo.py？

<details>
<summary>先自己答再展开</summary>

它是留给学习者的同型习题：方法你已经会了（公式换方向、约束换析锂和温度），写进脚本反而把练习做掉了。N 串取最小同理，见 [Notes06 导读](../ece5720-notes06-中文导读.md) 的映射表。
</details>

**上一篇**　[真实数据五天](04-真实数据五天.md) ｜ **目录**　[导读索引](../导读索引.md) ｜ **下一篇**　[擂台](../擂台.md)
