---
prev:
  text: '热五天'
  link: '/共学/06-热五天.html'
next:
  text: '仿真擂台'
  link: '/擂台.html'
---

# 共学：HPPC 五天

> **本篇你会学到**　§4.4 那句「参数从 HPPC 脉冲测试来」到底怎么来：一条电压曲线怎么被拆成 R0、R1、C1 三个数、渐近线为什么必须用两个点钉、什么窗口形状会让拟合当场骗人。
> **预计用时**　5 天，每天大约 30–60 分钟。
> **前置**　做过 [SOC 五天](01-soc五天.md) 或读过 [阶段 4 §4.4](../stages/stage-4-SOC-SOH算法.md)。装好 Python 3.10+，在仓库根执行过 `pip install -r code/requirements.txt`。不接电池。

⚠️ 本篇全部是**合成教学电芯**：脚本自己用一组「真值」R0/R1/C1 生成带噪声的电压采样，再用三步流程反推回来和真值对账（18650 NCM 的典型量级，但数值是合成的，不是任何真实电芯的参数；噪声 σ=1 mV/5 mA、随机种子写死）。它教的是「脉冲→反推→对账」这套流程本身；真电芯要按 [阶段 4 §4.10 动手任务](../stages/stage-4-SOC-SOH算法.md) 指的路径做真 HPPC 实验。

## 本页目录

- [第 1 天　一条脉冲，三段曲线](07-hppc五天.md#第-1-天一条脉冲三段曲线)
- [第 2 天　渐近线要两个点钉](07-hppc五天.md#第-2-天渐近线要两个点钉)
- [第 3 天　两种当场骗人的拟合](07-hppc五天.md#第-3-天两种当场骗人的拟合)
- [第 4 天　扫全 SOC：画内阻的地图](07-hppc五天.md#第-4-天扫全-soc画内阻的地图)
- [第 5 天　你自己就是标定工程师](07-hppc五天.md#第-5-天你自己就是标定工程师)

## 第 1 天：一条脉冲，三段曲线

**读**　[阶段 4 §4.4](../stages/stage-4-SOC-SOH算法.md) 的「参数从哪来」段和 [术语表 HPPC 行](../glossary.md)：HPPC＝混合脉冲功率特性测试，在不同 SOC 点打电流脉冲，从电压响应拟合 R0、R1、C1。脉冲期间你看到的电压只有三段：跳变（欧姆瞬降）、爬升（RC 极化）、静置回弹（极化排掉）。

**看**　[内阻压降与回弹](../circuits/assets/internal-resistance.svg)。带载「腿软」I·R、卸载回弹：腿软那一下就是今天的跳变段，回弹那段就是静置段。图上是示意数，认形状不认数。

**看码**　`code/soc/hppc_demo.py` 顶部的模块文档——它把「三步反推法」写成了人话：R0 从跳变、τ 从回弹形状、R1 从回弹幅值。今天先用眼睛把这三段在数字上认出来。

**跑**（演示本体，仓库根）：

```bash
python3 code/soc/hppc_demo.py
```

PowerShell：

```powershell
python code/soc/hppc_demo.py
```

2026-10-09 在本仓库跑通（Python 3.13，约 1 秒），表格 8 行，每行「真值/估计」三对数加误差，末尾一行：

```text
最差相对误差：R0 1.6%（容差 10%）、R1 3.0%（容差 15%）、C1 1.3%（容差 20%）
PASS：全部 SOC 点在容差内——方法闭环成立；换真实数据时流程相同，只是数据源从 TheveninCell 换成你的采集文件
```

今天只看 SOC 0.5 那一行：R0 真 33.0 估 33.0 mΩ、R1 真 16.0 估 15.7 mΩ、C1 真 2200 估 2172 F。三个数都不是「拟合库变出来的」，是三步初等算术。

**交**（手算对账，先纸上算）：把 SOC 0.5 点的采样序列取出来，脉冲前 1 s 均值减脉冲开始后 0.3 s 均值，得跳变 **97.8 mV**。R0 = 跳变 ÷ |I|，脉冲 3 A——纸上是 32.6 mΩ，和表里的 33.0 差在噪声。核对命令：

```bash
python3 -c "import sys; sys.path.insert(0,'code/soc'); import numpy as np, hppc_demo as hp; t,u,i,n_pre,n_pulse=hp.simulate_pulse(0.5,33e-3,16e-3,2200); print('jump=%.1f mV -> R0=%.1f mΩ' % ((np.mean(u[n_pre-10:n_pre])-np.mean(u[n_pre:n_pre+3]))*1e3, (np.mean(u[n_pre-10:n_pre])-np.mean(u[n_pre:n_pre+3]))/3*1e3))"
```

PowerShell：

```powershell
python -c "import sys; sys.path.insert(0,'code/soc'); import numpy as np, hppc_demo as hp; t,u,i,n_pre,n_pulse=hp.simulate_pulse(0.5,33e-3,16e-3,2200); print('jump=%.1f mV -> R0=%.1f mΩ' % ((np.mean(u[n_pre-10:n_pre])-np.mean(u[n_pre:n_pre+3]))*1e3, (np.mean(u[n_pre-10:n_pre])-np.mean(u[n_pre:n_pre+3]))/3*1e3))"
```

2026-10-09 输出：

```text
jump=97.8 mV -> R0=32.6 mΩ
```

**口诀**　跳变除电流，就是 R0。快得来不及极化的那一段。

**今天你解锁了**　你能在一条带噪声的电压曲线上认出跳变段，并用一条减法把它变成欧姆数。

**短自测**　为什么跳变取「脉冲前 1 s 均值 − 脉冲后 0.3 s 均值」，而不是取单个采样点相减？

<details>
<summary>先自己答再展开</summary>

噪声。电压噪声 σ=1 mV，单点相减把两份噪声原封不动带进 R0（÷3 A 就是 0.67 mΩ 的抖动）；几个采样的均值把噪声压下去，而 0.3 s 相对 τ≈35 s 短到极化几乎没长——既稳又没污染。
</details>

## 第 2 天：渐近线要两个点钉

**读**　[ECE5710 Notes02 中文导读「脉冲估参数」段](../ece5710-notes02-中文导读.md)：单 R–C 支路的粗标定——瞬时压降给 R0、稳态压降给 R0+R1、约 4 个时间常数收敛给 C1。原文实例 i=5 A、|v0|=41 mV、|v∞|=120 mV → R0≈8.2 mΩ、R1≈15.8 mΩ。今天的演示是它的「带噪声、要钉渐近线」版。

**看**　[阶跃 R0 与 RC 尾巴](../circuits/assets/rc-step-r0-tail.svg)。20 A、2 mΩ：先掉 40 mV 的是 R0，再按示意 τ=8 s 拖尾的是 RC——尾巴拖平了，渐近线才露头。

**看码**　`hppc_demo.py` 文档第 2 步：静置回弹 $U(t)=K+A\,e^{-t/\tau}$ 里有三个未知数，其中 K（渐近线）和 A（幅值）**成对搬家**：只截一段窗拟合，τ 一变形状就变，K 和 A 谁都不肯单独让步——所以渐近线必须「至少两个远离的点」钉住。演示脚本的做法：网格搜 τ（3–120 s 步长 0.5 s），τ 一钉死 exp 项就已知，K、A 退化成线性最小二乘。

**跑**（对 SOC 0.5 的静置段做拟合，仓库根）：

```bash
python3 -c "import sys; sys.path.insert(0,'code/soc'); import hppc_demo as hp; t,u,i,n_pre,n_pulse=hp.simulate_pulse(0.5,33e-3,16e-3,2200); tau,amp,K=hp.fit_relaxation(t[n_pre+n_pulse:]-t[n_pre+n_pulse],u[n_pre+n_pulse:]); print('tau=%.1f s | amp=%.2f mV | K=%.4f V' % (tau,amp*1e3,K))"
```

PowerShell：

```powershell
python -c "import sys; sys.path.insert(0,'code/soc'); import hppc_demo as hp; t,u,i,n_pre,n_pulse=hp.simulate_pulse(0.5,33e-3,16e-3,2200); tau,amp,K=hp.fit_relaxation(t[n_pre+n_pulse:]-t[n_pre+n_pulse],u[n_pre+n_pulse:]); print('tau=%.1f s | amp=%.2f mV | K=%.4f V' % (tau,amp*1e3,K))"
```

2026-10-09 输出：

```text
tau=35.5 s | amp=-11.80 mV | K=3.7478 V
```

τ 真值 = R1×C1 = 16 mΩ × 2200 F = 35.2 s，拟合 35.5 s——差的是网格 0.5 s 的分辨率零头。

**交**（手算对账）：脉冲只有 10 s，τ≈35 s，所以 RC 支路只充到 $1-e^{-10/35.2}$ ≈ **24.7%**——U_rc(10 s) = 3 A × 16 mΩ × 0.247 ≈ **11.9 mV**。反算回去：|amp| ÷ |I| ÷ 0.2473 = 11.80 ÷ 3 ÷ 0.2473 ≈ 15.9 mΩ ≈ R1。核对命令（纯算术，不含拟合）：

```bash
python3 -c "import math; f=1-math.exp(-10/35.2); print('charge_factor=%.4f | amp_pred=%.2f mV | R1_back=%.2f mΩ' % (f, 3*0.016*f*1e3, 0.0118/3/f*1e3))"
```

PowerShell：

```powershell
python -c "import math; f=1-math.exp(-10/35.2); print('charge_factor=%.4f | amp_pred=%.2f mV | R1_back=%.2f mΩ' % (f, 3*0.016*f*1e3, 0.0118/3/f*1e3))"
```

2026-10-09 输出：

```text
charge_factor=0.2473 | amp_pred=11.87 mV | R1_back=15.90 mΩ
```

**口诀**　τ 定形状，两角钉渐近线：左上角是幅值，右平线是终值。

**今天你解锁了**　你能分清 amp 与 K 谁是谁：拿 24.7% 这个折扣把幅值还原成 R1，而不是拿尾巴上看着平的那段当 R1。

## 第 3 天：两种当场骗人的拟合

**读**　`code/soc/hppc_demo.py` 模块文档「真实数据适配说明」第 2、3 条：静置窗长 ≥3–4 倍你预期的 τ，否则回到脚本注释里那个 40 s 病态（窗长不够时 K 与 A 分不开）；温度漂移会拟合出假 τ。这一条是 [SOC 五天](01-soc五天.md)「拟合不是越漂亮越好」的辨识版。

**看**　[极化的物理图景](../circuits/assets/polarization-physics.svg)。表面被抽空、离子再扩散回匀，底栏那条示意回弹电压就是今天要拟合的形状——它慢，是因为扩散慢，不是仪器慢。

**跑**（坑①，把静置窗从 120 s 砍到车规 HPPC 的 40 s，仓库根）：

```bash
python3 -c "import sys; sys.path.insert(0,'code/soc'); import numpy as np, hppc_demo as hp; t,u,i,n_pre,n_pulse=hp.simulate_pulse(0.5,33e-3,16e-3,2200); tr=t[n_pre+n_pulse:]-t[n_pre+n_pulse]; ur=u[n_pre+n_pulse:]; m=tr<=40.0; tau,amp,K=hp.fit_relaxation(tr[m],ur[m]); print('40s窗: tau=%.1f s | R1est=%.2f mΩ | 误差=%.0f%%' % (tau,abs(amp)/3*1e3,abs(abs(amp)/3-16e-3)/16e-3*100))"
```

PowerShell：

```powershell
python -c "import sys; sys.path.insert(0,'code/soc'); import numpy as np, hppc_demo as hp; t,u,i,n_pre,n_pulse=hp.simulate_pulse(0.5,33e-3,16e-3,2200); tr=t[n_pre+n_pulse:]-t[n_pre+n_pulse]; ur=u[n_pre+n_pulse:]; m=tr<=40.0; tau,amp,K=hp.fit_relaxation(tr[m],ur[m]); print('40s窗: tau=%.1f s | R1est=%.2f mΩ | 误差=%.0f%%' % (tau,abs(amp)/3*1e3,abs(abs(amp)/3-16e-3)/16e-3*100))"
```

2026-10-09 输出：

```text
40s窗: tau=30.5 s | R1est=3.61 mΩ | 误差=77%
```

同一个脚本、同一份数据，只砍窗口：R1 从差 2% 烂到差 **77%**——40 s 只够 1.1 个 τ，回弹没走完，渐近线没露面，τ 和 R1 一起塌。这就是演示用 120 s（≈3.4 个 τ）静置的原因。

**跑**（坑②，偷懒用「末段均值」当渐近线——不搜 τ、把 30 s 附近一段的均值直接当 K）：

```bash
python3 -c "import sys; sys.path.insert(0,'code/soc'); import numpy as np, hppc_demo as hp; t,u,i,n_pre,n_pulse=hp.simulate_pulse(0.5,33e-3,16e-3,2200); tr=t[n_pre+n_pulse:]-t[n_pre+n_pulse]; ur=u[n_pre+n_pulse:]; tail=np.mean(ur[(tr>=25)&(tr<=30)]); print('30s末均值=%.4f V | 比真K低%.1f mV | 幅值只剩%.2f mV（真11.8）' % (tail,(3.7478-tail)*1e3,(tail-ur[0])*1e3))"
```

PowerShell：

```powershell
python -c "import sys; sys.path.insert(0,'code/soc'); import numpy as np, hppc_demo as hp; t,u,i,n_pre,n_pulse=hp.simulate_pulse(0.5,33e-3,16e-3,2200); tr=t[n_pre+n_pulse:]-t[n_pre+n_pulse]; ur=u[n_pre+n_pulse:]; tail=np.mean(ur[(tr>=25)&(tr<=30)]); print('30s末均值=%.4f V | 比真K低%.1f mV | 幅值只剩%.2f mV（真11.8）' % (tail,(3.7478-tail)*1e3,(tail-ur[0])*1e3))"
```

2026-10-09 输出：

```text
30s末均值=3.7425 V | 比真K低5.3 mV | 幅值只剩5.84 mV（真11.8）
```

第 2 天说渐近线要「远离脉冲的两个点」钉——30 s 才 0.85 个 τ，指数还差 41% 没走完，末段均值把 K 拉低 5.3 mV，回弹幅值一下从 11.8 mV 缩到 5.8 mV。R1 靠幅值吃饭，跟着腰斩。

**交**　贴两行输出，写一句人话：为什么「截一段看着平的电压当渐近线」比「多等到 120 s」便宜却贵得多。

**口诀**　静置不够长，K 和 A 抢账；末段当渐近，幅值腰斩。

**今天你解锁了**　你亲手复现了「窗口病态」和「末段均值偷懒」两种拟合骗局，并且知道识别它们的信号：τ 和参数对窗口长度过敏、τ 顶网格边界、幅值对不上第 2 天的预测。

**短自测**　第 3 天 40 s 窗的 R1 差 77%，第 1 天的 R0 却几乎没受影响（两个窗口下都一样算）——为什么 R0 免疫？

<details>
<summary>先自己答再展开</summary>

R0 只吃「跳变」：两个 0.3 s 均值一减，τ≈35 s 的极化在 0.3 s 里才长了不到 1%，静置窗怎么截都动不了它。R1 恰恰整个住在回弹的**形状和终值**里——形状由 τ 定、终值就是渐近线 K，所以窗口和噪声专杀 R1、C1。
</details>

## 第 4 天：扫全 SOC：画内阻的地图

**读**　[阶段 4 §4.4b 开头](../stages/stage-4-SOC-SOH算法.md)：HPPC 离线标定给的是「出厂那一刻」的参数地图；再回看 [ECE5710 Notes02 中文导读](../ece5710-notes02-中文导读.md) 的参数段——R0 随温度升高指数下降，随 SOC 降低抬头。今天演示把「随 SOC」这一维扫给你看。

**看**　[内阻随温度](../circuits/assets/rint-arrhenius.svg)。示意 R(T) 随 1/T 指数变：冷天内阻抬头。今天扫 SOC 这张地图，第 5 天你会看到温度也来抢同一支笔。

**看码**　演示表头的「真值」数组：R0 从 SOC 0.9 的 26 mΩ 一路涨到 0.2 的 48 mΩ（1.85 倍）、R1 从 12 涨到 24 mΩ，而 C1 从 3000 降到 1600 F——R 涨 C 降，τ=R1·C1 反而稳。这一串是脚本为了让 τ 落在网格中段挑的合成教学值，不是任何真实电芯的标定结果，别抄进你的 BOM。

**跑**（τ 真值手算，仓库根）：

```bash
python3 -c "print('tau真值 @SOC0.9=%.1f s  @SOC0.2=%.1f s' % (12e-3*3000, 24e-3*1600))"
```

PowerShell：

```powershell
python -c "print('tau真值 @SOC0.9=%.1f s  @SOC0.2=%.1f s' % (12e-3*3000, 24e-3*1600))"
```

2026-10-09 输出：

```text
tau真值 @SOC0.9=36.0 s  @SOC0.2=38.4 s
```

对照演示表格里 8 行的 τ 估计（都落在 34–38 s 附近）：一条几乎平的线。第 2 天那笔「10 s 脉冲只充到 24.7%」的账因此全 SOC 通用。

**交**　把演示表格誊到纸上，画 R0(SOC) 一条曲线，标出 33 mΩ（0.5）和 48 mΩ（0.2）两点。再写一句：拿 SOC 0.5 标出来的 R0 去算 SOC 0.2 的电压降，会往哪边错、错多少毫伏（3 A × 15 mΩ）？这题的「错多少」正好是 [SOP 五天](05-sop五天.md) 里闭式法翻车账的同款单位。

**口诀**　一张表不是三个参数，是三个函数——横轴都是 SOC。

**今天你解锁了**　你看懂了 HPPC 为什么要「在不同 SOC 点打脉冲」：标定产出的不是参数点，是参数随 SOC 的地图；τ 稳、R 陡，所以极化账不能跨 SOC 挪用。

## 第 5 天：你自己就是标定工程师

**读**　[ECE5710 Notes02 中文导读](../ece5710-notes02-中文导读.md)「脉冲估参数」的原文实例，和 [阶段 4 §4.4b](../stages/stage-4-SOC-SOH算法.md)：离线 HPPC 管出厂，RLS 在线辨识让参数跟着电池走——边界是「HPPC 给地图，在线辨识修地图」。

**看**　[卸流回弹时间轴](../circuits/assets/ocv-rest-timeline.svg)。立刻回来的是内阻，慢慢回来的是极化，滞回缝还在——真数据比演示脏的地方全在这条时间轴上。

**看码**　`identify_one()` 的 20 行：第 1 天减法、第 2 天 fit_relaxation + charge_factor 修正、第 3 天的 120 s 纪律，三步全在里面。它吃 `(soc0, r0, r1, c1)` 四个数，其中三个其实只是「电池」的代称——换成你的采集文件，只有数据源变。

**跑**（今天先纸上标定一颗假电池——[SOC 五天](01-soc五天.md) 同款纸笔流程）：某电芯打 **2 A** 放电脉冲，瞬时压降 **50 mV**，脉冲末总压降 **110 mV**，静置后约 **200 s** 走完（≈4 个 τ）。求 R0、R1、τ、C1。提示：瞬时那笔是 R0；多出来的是 R1；4τ=200 s；C1=τ/R1。核对命令（只核对，先自己算）：

```bash
python3 -c "print('R0=%.1f mΩ R1=%.1f mΩ tau=%.0f s C1=%.0f F' % (50/2, (110-50)/2, 200/4, (200/4)/((110-50)/2*1e-3)))"
```

PowerShell：

```powershell
python -c "print('R0=%.1f mΩ R1=%.1f mΩ tau=%.0f s C1=%.0f F' % (50/2, (110-50)/2, 200/4, (200/4)/((110-50)/2*1e-3)))"
```

2026-10-09 输出：

```text
R0=25.0 mΩ R1=30.0 mΩ tau=50 s C1=1667 F
```

**再跑**（机器版单点全流程，和演示表格 SOC 0.5 行对账）：

```bash
python3 -c "import sys; sys.path.insert(0,'code/soc'); import hppc_demo as hp; r=hp.identify_one(0.5, 33e-3, 16e-3, 2200); print('R0=%.1f mΩ R1=%.1f mΩ C1=%.0f F tau=%.1f s' % (r[0]*1e3, r[1]*1e3, r[2], r[3]))"
```

PowerShell：

```powershell
python -c "import sys; sys.path.insert(0,'code/soc'); import hppc_demo as hp; r=hp.identify_one(0.5, 33e-3, 16e-3, 2200); print('R0=%.1f mΩ R1=%.1f mΩ C1=%.0f F tau=%.1f s' % (r[0]*1e3, r[1]*1e3, r[2], r[3]))"
```

2026-10-09 输出：

```text
R0=32.6 mΩ R1=16.0 mΩ C1=2216 F tau=35.5 s
```

**再跑一遍**（真数据第一条警告：温度漂移。假想你的记录上叠了 0.1 mV/s 的慢漂——实验中途电芯升温就会这样——再拟合一次，仓库根）：

```bash
python3 -c "import sys; sys.path.insert(0,'code/soc'); import numpy as np, hppc_demo as hp; t,u,i,n_pre,n_pulse=hp.simulate_pulse(0.5,33e-3,16e-3,2200); tr=t[n_pre+n_pulse:]-t[n_pre+n_pulse]; ur=u[n_pre+n_pulse:]; tau,_,_=hp.fit_relaxation(tr,ur-0.1e-3*tr); print('加 0.1 mV/s 假想漂移：tau=%.1f s（真 35.5，网格顶 120）' % tau)"
```

PowerShell：

```powershell
python -c "import sys; sys.path.insert(0,'code/soc'); import numpy as np, hppc_demo as hp; t,u,i,n_pre,n_pulse=hp.simulate_pulse(0.5,33e-3,16e-3,2200); tr=t[n_pre+n_pulse:]-t[n_pre+n_pulse]; ur=u[n_pre+n_pulse:]; tau,_,_=hp.fit_relaxation(tr,ur-0.1e-3*tr); print('加 0.1 mV/s 假想漂移：tau=%.1f s（真 35.5，网格顶 120）' % tau)"
```

2026-10-09 输出：

```text
加 0.1 mV/s 假想漂移：tau=119.5 s（真 35.5，网格顶 120）
```

τ 被直接吸到网格顶。渐近线自己还在爬，任何指数都追不上它——这就是脚本「适配说明」第 3 条要求每段独立估 offset、记录每段温度做 sanity check 的原因。

**交**　二选一提交：① 纸笔题四个数 + 这条命令的输出，写一句「你的三步和第 1/2/3 天各对应哪一步」；② 真刀真枪——手边有任何带时间戳的 V/I 记录（NASA 数据集的脉冲段也算，见 [阶段 4 §4.10](../stages/stage-4-SOC-SOH算法.md)），整理成 `t, u, i` 三个数组后把 `identify_one` 的第 1、2 步原样搬过去（`fit_relaxation(t_rel, u_rel)` 接口就是 (t, u) → (τ, amp, K)），贴你的 τ 和 R1。**注意**：真实长脉冲（如 NASA 的约 600 s 段）不是标准 10 s HPPC，charge_factor 那一步的 T_PULSE 要换成你自己的脉冲宽度。

**口诀**　减法给 R0，形状给 τ，幅值给 R1——三步都是初等算术，拟合库只是省纸。

**今天你解锁了**　你能不用任何拟合库、三步从一条脉冲里挖出 R0/R1/C1，知道离线 HPPC 与在线辨识（§4.4b 的 RLS）各管哪段，也知道自己数据的脉冲宽度该怎么进公式。

**短自测**　演示里 C1 的容差（20%）为什么比 R0（10%）宽一倍？

<details>
<summary>先自己答再展开</summary>

C1 = τ/R1，是两个误差相除：τ 带网格 0.5 s 的分辨率（约 1.4%）和窗口病态风险，R1 已经吃了 charge_factor 放大（÷0.247 把幅值噪声放大 4 倍）——除法再把相对误差叠加。R0 只有跳变一处噪声，最干净，所以容差最紧。
</details>

**上一篇**　[热五天](06-热五天.md) ｜ **目录**　[导读索引](../导读索引.md) ｜ **下一篇**　[擂台](../擂台.md)
