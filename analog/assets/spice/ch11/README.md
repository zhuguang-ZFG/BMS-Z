# 第 11 章 差分对与共模抑制

- 电路：±12 V 双电源，两只 NPN 差分对，尾电流 1 mA，集电极电阻 10 kΩ；尾电流源并联 $R_{EE}=1\text{ M}\Omega$，用来体现有限尾电阻对共模增益的影响。
- 输入：$v_{id}=2\text{ mV}$（两基极分别相对 $V_{CM}$ 加 ±1 mV），$V_{CM}$ 从 0 V 直流扫到 1 V，步长 10 mV。
- 期望：$V_{CM}=0$ 时两集电极约 6.8 V 与 7.2 V（差模分量约 ±0.19 V）；$V_{CM}$ 升到 1 V 时，两集电极一起下移约 5 mV，体现 $R_{EE}$ 有限导致的共模增益。具体容差见 `assert.json`。
- 运行：`python scripts/run_spice.py --root assets/spice`（需要 ngspice；缺失时用例跳过）。
- 数据：`diffpair.dat` 由本 deck 的 `wrdata` 生成，不是手写或拟合数据。
- 模型边界：`QN` 只用 `Is / BF / VAF` 三个参数，没有寄生电容、基极电阻和失配；这是理想化差分对的直流教学模型，不代表实测，也不覆盖高频 CMRR。
