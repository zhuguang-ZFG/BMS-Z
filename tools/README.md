# 机制动画生成

`gen_mechanism_svgs.py` 重画下面表里的机制图。曲线点来自脚本里的公式，或来自 `code/soc/compare.py` 的 `run(seed=42)`。不改 `code/` 里的算法。色和版式见 [动画画风规范](../docs/circuits/动画画风规范.md)。

```bash
python3 tools/gen_mechanism_svgs.py
```

会覆盖：

| 文件 | 曲线从哪来 |
|---|---|
| `docs/circuits/assets/ocv-hysteresis.svg` | 平均开路电压 ± 20 mV。SOC 0.50 锚在 3.300 V，平台斜率 0.075 V/单位荷电 |
| `docs/circuits/assets/ocv-plateau-distrust.svg` | 同一条平均支，锚改到 3.295 V。底栏的 dV/dSOC 和「5 mV 盖住多少个百分点」是这条导数算的 |
| `docs/circuits/assets/sop-derating.svg` | 温度分段线性、荷电分段线性、电压墙 `(OCV−3.00)/0.015/40 A`，取最小后再限斜率 |
| `docs/circuits/assets/kalman-gain.svg` | `P←P+Q`，`K=P/(P+R)`，`P←(1−K)P`。P0=0.04，Q=0.0004，R 取 0.001 和 0.020 |
| `docs/circuits/assets/ekf-estimation.svg` | `compare.py` 全部 17000 步的 RMSE；折线等距抽点 |
| `docs/circuits/assets/second-order-rc.svg` | `U = 3.700 − 20·(0.002 + 0.004·(1−e^{−t/1}) + 0.006·(1−e^{−t/30}))`。一阶对照把 10 mΩ 合成 τ=12 s |
| `docs/circuits/assets/soh-aging.svg` | 容量 `100 − 20·(n/3000)^1.5`，内阻 `20 + 25·(n/3000)^0.45` mΩ。新电池按 5.0 Ah 起算 |
| `docs/circuits/assets/error-budget-waterfall.svg` | 2.0、1.5、0.8、0.3、0.9 mV 逐截累加。预算线在 5 mV，标定后剩约 1.8 mV |

数字是示意或仿真，不是电芯实测。单文件控制在大约 20 KB 以内。

另外几张示意图（DW01、短路时间轴等）是在原文件上加了移动的点或游标，不由这个脚本覆盖。DW01 底栏的检流直线是 `V = 0.40 + 1.20 t`（t 从 0 到 1），1.2 V 是这条直线上的阈值。

底栏横轴标题用 `axis_title_xy`：放在最后一个刻度的右侧，不要和刻度写在同一个点上。`tools/reskin_legacy_svgs.py` 按画风规范换旧图的色和字体时，也调用这个函数挪开已经叠住的标题。
