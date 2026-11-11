# Wave 8 图库（8 张，待审）

评分入口：[`contact-wave8.html`](contact-wave8.html)（本地打开）。
本页图片路径相对仓库根，GitHub 可直接预览。

## ch1（1 张）

### E24 档位与 3.3k 的来历
`ch01-e24-ladder` · V4 · `IG-013`

<img src="../../../../../assets/figures-v2/ch01-e24-ladder.webp" width="720" alt="手绘左右两栏：左栏算出 3.285k，落到 E24 货架档 3.3k，误差落在正负 5% 窗内；右栏列出 24 档、约 1.1 倍档比、正负 5% 容差与 E96 的正负 1%。底部写先选系列再选值，货架上没有 3.285k。">

## ch4（2 张）

### 栅极保护的电压窗
`ch04-gate-window` · V4 · `IG-013`

<img src="../../../../../assets/figures-v2/ch04-gate-window.webp" width="720" alt="手绘三条电压带：栅氧额定正负 20 伏、钳位 13 到 16 伏、驱动 12 伏；右栏写明钳位高于驱动且低于额定、栅源并 10 千欧下拉、开尔文源脚。底部写 12 伏驱动选 13 到 16 伏钳位。">

### 死区损耗的明账
`ch04-deadtime-ledger` · V4 · `IG-013`

<img src="../../../../../assets/figures-v2/ch04-deadtime-ledger.webp" width="720" alt="手绘公式与对照：死区损耗约等于 0.8 伏乘 5 安乘 100 纳秒乘 100 千赫，约 0.4 瓦；同一只管子沟道压降 5 安乘 30 毫欧为 0.15 伏，体二极管为 0.8 伏。底部写死区压到几十纳秒但不能压到零。">

## ch5（2 张）

### 上拉电阻自己的功耗
`ch05-rp-power` · V4 · `IG-013`

<img src="../../../../../assets/figures-v2/ch05-rp-power.webp" width="720" alt="手绘左右两张功率卡：3.3 伏乘 1 千欧为 11 毫瓦，0603 随便扛；5 伏乘 100 欧为 250 毫瓦，0402 已超 1/16 瓦。底部写总线被拉低时全部电压落在电阻上，强上拉先核封装功率。">

### 三态总线的交接时序
`ch05-tristate-handover` · V4 · `IG-013`

<img src="../../../../../assets/figures-v2/ch05-tristate-handover.webp" width="720" alt="手绘三段时间轴：驱动器 A 释放进入高阻，空档 tDIS 为 10 到 30 纳秒，驱动器 B 使能开始驱动；下方写重叠 10 纳秒会让两个驱动器同时开口，产生微秒级电流尖峰。底部写先撤销 OE 再转身后开口。">

## ch7（1 张）

### 迟滞窗口与两个阈值
`ch07-hysteresis-window` · V4 · `IG-013`

<img src="../../../../../assets/figures-v2/ch07-hysteresis-window.webp" width="720" alt="手绘迟滞回环：上行阈值 6.15 伏、下行阈值 5.85 伏，窗口 305 毫伏，覆盖现场 120 毫伏噪声；右侧列出窗口至少为噪声峰峰两倍、R2 比 R1 为 100 比 1、窗口约电源 1%。底部写先量噪声再定电阻。">

## ch9（2 张）

### LDO 的 ESR 稳定窗口
`ch09-esr-window` · V4 · `IG-013`

<img src="../../../../../assets/figures-v2/ch09-esr-window.webp" width="720" alt="手绘 ESR 数轴：老式 NPN 准 LDO 的稳定区是 0.3 到 22 欧；左侧 5 毫欧的 MLCC 因零点太远而振荡，右侧大于 22 欧因零点太近而响应慢。底部写容量一样不等于环路还稳。">

### 基准选型的精度阶梯
`ch09-reference-ladder` · V4 · `IG-013`

<img src="../../../../../assets/figures-v2/ch09-reference-ladder.webp" width="720" alt="手绘五级精度阶梯：稳压二极管 5% 级、LM385 带隙 1 到 3%、TL431 0.5 到 2%、REF50xx 或 ADR45xx 0.05 到 0.1% 且 3 到 10 ppm 每摄氏度、LM399 埋入齐纳 0.3 到 2 ppm 每摄氏度。底部写 12 位配 REF50xx 是浪费，20 位配 TL431 是事故。">
