# Wave 9 图库（7 张，待审）

评分入口：[`contact-wave9.html`](contact-wave9.html)（本地打开）。
本页图片路径相对仓库根，GitHub 可直接预览。

## ch6（1 张）

### 输入偏置电流与平衡电阻
`ch06-bias-balance` · V4 · `IG-013`

<img src="../../../../../assets/figures-v2/ch06-bias-balance.webp" width="720" alt="手绘两张误差卡：20 纳安流过 1 千欧只有 20 微伏；流过 100 千欧就是 2 毫伏。下方写平衡电阻法 R3 等于 R1 并联 R2，两输入端直流电阻相等时偏置电流压降对消，只剩失调电流；边界是偏流随温度漂，FET 输入偏置电流是皮安级。">

## ch10（2 张）

### 单稳态 1.1RC 的误差预算
`ch10-monostable-budget` · V4 · `IG-013`

<img src="../../../../../assets/figures-v2/ch10-monostable-budget.webp" width="720" alt="手绘左右两栏：左栏写 t 等于 1.1 乘 R 乘 C，100 千欧乘 10 微法约 1.1 秒；右栏逐项列电阻正负 1%、薄膜电容正负 5%、阈值散差正负 2 到 4%，最坏同向正负 8 到 10%。底部写要正负 1% 需 COG、0.1% 电阻与修调。">

### 单稳态恢复时间与连发触发
`ch10-recovery-gap` · V4 · `IG-013`

<img src="../../../../../assets/figures-v2/ch10-recovery-gap.webp" width="720" alt="手绘两行脉冲时序：正常行等电容归零后再触发，第二拍脉宽不变；太早行在恢复期内触发，第二拍从半满电容起算而变短。右侧写放电管把电容从三分之二电源放空需微秒到几十微秒，大于 10 微法可到百微秒，触发间隔要大于脉宽加恢复时间。">

## ch11（1 张）

### 电流镜的三笔误差
`ch11-mirror-three-errors` · V4 · `IG-013`

<img src="../../../../../assets/figures-v2/ch11-mirror-three-errors.webp" width="720" alt="手绘三张误差卡：第一张写贝塔分流，参考支路先被基极电流分走一份，贝塔越大越准；第二张写 Early 效应，输出管 VCE 一变复制电流跟着变，Wilson 镜改进；第三张写有源负载，用电流镜替 Rc 可把单级增益推到 100 分贝以上。">

## ch12（3 张）

### TIA 的增益带宽稳定三角
`ch12-tia-three-way` · V4 · `IG-013`

<img src="../../../../../assets/figures-v2/ch12-tia-three-way.webp" width="720" alt="手绘三角关系图：顶点是增益，10 兆欧乘 1 纳安等于 10 毫伏；左下是带宽，10 皮法加 1 兆欧得到 15.9 千赫；右下是稳定，补偿电容至少 0.4 皮法、实装 1 到 2 皮法；中心写三者互相拉扯。">

### 开关电容的等效电阻
`ch12-switch-cap` · V4 · `IG-013`

<img src="../../../../../assets/figures-v2/ch12-switch-cap.webp" width="720" alt="手绘左右两栏：左栏写等效电阻等于 1 除以时钟频率乘电容，1 皮法乘 100 千赫等于 10 兆欧；右栏写电容比值匹配到 0.1%、时钟准到 ppm、精度来源从元件转到时钟。底部写采样会混叠、开关会注入电荷，时钟取信号带宽 50 到 100 倍。">

### 按源阻抗选输入级
`ch12-input-types` · V4 · `IG-013`

<img src="../../../../../assets/figures-v2/ch12-input-types.webp" width="720" alt="手绘两张输入级卡片：BJT 输入 20 纳安乘 1 兆欧为 20 毫伏，且每升 10 摄氏度偏置电流约翻倍；CMOS 输入 1 皮安乘 1 兆欧为 1 微伏，差四个数量级。底部写低源阻抗小于 10 千欧挑 en 小的 BJT，高源阻抗大于 100 千欧挑 Ib 小的 CMOS 或 JFET。">
