# 手绘动画扩量选题表（Task 11b · 2026-11-03）

> 每行：`id | 章 | 一句话物理故事 | 节拍数 | 关键数值来源 | 优先级`。全部经 `scripts/generate_svgs.py` 产出（`derive_frame` 统一版式 + `handraw.apply` 纸墨皮肤），**禁止手改产物 SVG**。优先补低密度章与每章至少一张「失效边界」动态图；禁选题：无数值故事的装饰循环、卡通拟人元件。

| id（SVG 文件） | 章 | 一句话物理故事 | 节拍 | 关键数值来源 | 优先级 |
|---|---|---|---|---|---|
| exp-source-sag | ch0 | 两次测量反推电源内阻，2A 负载塌 3.4V | 4 | p1-01-ch0 §0.6 算一笔 | 高（失效边界） |
| exp-unit-guard | ch0 | 单位错档让 τ 差一千倍 | 4 | p1-01-ch0 §0.7 | 高 |
| exp-derate-chain | ch0 | 1/4W 电阻的降额链：85°C 七成再打五折 | 4 | ch0 §0.9 / ch14 军规 | 高（失效边界） |
| exp-esr-ripple-split | ch1 | 纹波两本账：22µF 陶瓷容性主导、100µF 电解 ESR 主导 | 4 | p1-02-ch1 §1.2 算一笔 | 高 |
| exp-cap-life | ch1 | 电解寿命 10°C 翻倍：2000h@105°C→65°C 得 3.7 年 | 4 | p1-02-ch1 §1.7 | 高（失效边界） |
| exp-avalanche-edge | ch1 | 感性负载关断尖峰数百伏，续流二极管钳位 | 4 | ch1 §1.3 反电动势 | 高（失效边界） |
| exp-conduction-angle | ch2 | 整流导通角：1A 平均挨 3.3A 峰值窄脉冲 | 4 | p1-03-ch2 §2.6 | 高 |
| exp-tvs-ladder | ch2 | TVS→电阻→钳位三级削减 8kV 浪涌 | 4 | ch2 §2.11 例 2-2 | 高 |
| exp-beta-drift | ch3 | β 从 100 漂到 600：固定偏置撞饱和、分压偏置只动 4% | 4 | ch03-bjt-bias-stability 图 | 高（失效边界） |
| exp-thermal-loop | ch3 | 热失控正反馈环：T↑→VBE↓→IC↑→更热 | 4 | p1-04-ch3 §3.7 | 高（失效边界） |
| exp-gate-charge | ch4 | 米勒平台时长=Qgd/Idrv：10mA→40mA 提速四倍 | 4 | p1-05-ch4 §4.6 | 高 |
| exp-pullup-trade | ch5 | 上拉双边权衡：1k 快而费电、4.7k 超 300ns 窗 | 4 | ch05-open-drain-wired-and 图 | 高 |
| exp-dead-time | ch5 | 推挽换向直通窗口与死区 | 4 | ch5 §5.1/§5.6 | 高（失效边界） |
| exp-gbw-swap | ch6 | GBW 守恒：增益 100 只剩 100kHz 带宽 | 4 | ch6 §6.3 | 高 |
| exp-slew-wall | ch6 | 压摆率墙：5Vpk@100kHz 需 3.14V/µs | 4 | ch6 §6.7 | 高（失效边界） |
| exp-hyst-window | ch7 | 迟滞窗口三电阻：免疫区挡 200mV 毛刺 | 4 | p1-08-ch7 §7.3 | 高 |
| exp-delay-budget | ch7 | LM358 兼职判决拖 50µs、LM393 仅 1.6µs | 4 | ch07-delay-budget 图 | 高 |
| exp-inject-harmonic | ch8 | 注入随信号走：0.4pC 峰谷差落 1nF 变 0.4mV | 4 | ch08-charge-injection 图 | 高（失效边界） |
| exp-droop-budget | ch8 | droop 预算：2nA/10nF=0.2V/s，1ms 掉 0.4LSB | 4 | ch8 §8.4 端到端例 | 高 |
| exp-ldo-zero | ch9 | 换 MLCC 丢 ESR 零点：裕度 58°→32° | 4 | ch16 案例 A / ch9 §9.3 | 高（失效边界） |
| exp-psrr-roll | ch9 | PSRR 滚降：70dB→40dB→20dB 分段防守 | 4 | p1-10-ch9 §9.3 | 高 |
| exp-555-mono-train | ch10 | 单稳态一触发亮一拍：t=1.1RC，漏电是敌人 | 4 | p1-11-ch10 §10.5 | 中 |
| exp-555-duty | ch10 | 555 占空比：充放两条路各管一段 | 4 | ch10 §10.2 | 中 |
| exp-miller-mult | ch11 | 米勒倍增 (1+A)C：10pF 变 1010pF | 4 | p2-01-ch11 §11.5 | 高（失效边界） |
| exp-noise-ladder | ch11 | 噪声三税：带宽→源阻→电流，预算表收口 | 4 | ch11 §11.6 | 高 |
| exp-integrator-drift | ch12 | 积分器漂移爬向轨，泄放电阻拉回 | 4 | p2-02-ch12 §12.4/12.11 | 高（失效边界） |
| exp-cload-isolate | ch12 | 容性负载自激，隔离电阻收敛振铃 | 4 | ch12 §12.9 | 高（失效边界） |
| exp-volt-second | ch13 | 伏秒平衡：充放两块面积相等→Vo=D·Vin | 4 | ch13-buck-ripple 图 | 高 |
| exp-crystal-pull | ch13 | 晶振牵引：CL 12→15pF，RTC 每天差 4.8s | 4 | ch13-crystal-load-cap 图 | 高（失效边界） |
| exp-wc-rss | ch14 | 误差预算两把尺：WC 上界 vs RSS 良率 | 4 | p3-01-ch14 §14.10 | 高 |
| exp-return-cut | ch15 | 回流被开槽割断：面积×30、辐射+30dB | 4 | ch15 §15.2/15.7 | 高（失效边界） |
| exp-via-stack | ch15 | 叠层定阻抗：四层 0.35mm vs 双层 3mm | 4 | ch15-impedance-geometry 图 | 高 |
| exp-log2-split | ch16 | 二分数学：⌈log₂6⌉=3，每刀砍半 | 4 | p4-01-ch16 §16.1/16.7 | 高 |
| exp-contact-creep | ch17 | 接触电阻蠕变：通断判据的漂移盲区 | 4 | ch17-contact-resistance-creep 图 | 高（失效边界） |
| exp-cost-ladder | ch18 | 1-10-100 法则：把故障往左推 | 4 | ch18-four-gates 图 | 高 |

统计：35 张新增，`assets/svg` 总数 118 → **153**（闸：≥150，`scripts/test_svg_count_floor.py`）。
