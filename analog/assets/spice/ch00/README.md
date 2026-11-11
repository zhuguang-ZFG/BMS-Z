# 第 0 章 分压器带载

- 电路：12 V 直流源、R1 = R2 = 10 kΩ；1 ms 时开关接入 10 kΩ 负载。
- 期望：空载 6.0 V；带载 4.0 V；负载电流 0.4 mA（戴维南等效 6 V 串 5 kΩ）。
- 运行：`python scripts/run_spice.py --root assets/spice`
- 数据：`divider.dat` 由本 deck 的 `wrdata` 生成，不是手写或拟合数据。
- 模型边界：理想开关（Ron = 1 Ω）、理想电阻、无引线电感与公差；用于验证分压与带载关系，不代表实测。
