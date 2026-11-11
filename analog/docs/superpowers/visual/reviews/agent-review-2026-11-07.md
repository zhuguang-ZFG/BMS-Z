# 代理审图报告（2026-11-07）

> **性质**：用户于 2026-11-07 选择「授权代理审图」。本报告是机器辅助评分，**不是人工签字**；manifest 逐条写明 `reviewed_by: agent-proxy`，用户保留抽检、否决和回退权。

- 待审 `generated`：**117** 张
- 可推进：**117** 张；阻断：**0** 张
- 逐图分数：`docs/superpowers/visual/reviews/agent-review-2026-11-07.csv`

## 评分口径

| 维度 | 5 分 | 4 分 | 阻断 |
|---|---|---|---|
| 教学必要性 | 所在章最长无图段 >1500 | 其余 | — |
| 事实精度 | 有 source_facts 与 prompt | 缺其一 | 缺 source_facts / prompt 文件 |
| 构图层级 | 版面 bounds=pass 且文本 ≥8（动画 ≥4 拍） | 文本 4–7 或动画 3 拍 | bounds 失败 / 文本 <4 / 缺 beats |
| 风格一致性 | style_id 在锁定集合且 layout/color 齐全 | 缺 layout 或 color | style_id 不在锁定集合 |
| 印刷可读性 | 最小字号 ≥9.0pt（动画有 print fallback 与 reduced_motion） | 8.5–9.0pt / 缺其一 | <8.5pt |
| 运动叙事 | ≥4 拍且结论帧有效 | 3 拍 | 缺结论帧 / <3 拍 |
| 交互节奏 | 6–20s 且 3–5 拍 | 4–30s 且 2–6 拍 | 超出范围 |

## 分章统计

| 章 | 静态 | 动画 | 小计 |
|---:|---:|---:|---:|
| 1 | 5 | 0 | 5 |
| 2 | 8 | 0 | 8 |
| 3 | 7 | 0 | 7 |
| 4 | 7 | 0 | 7 |
| 5 | 5 | 0 | 5 |
| 6 | 5 | 0 | 5 |
| 7 | 6 | 0 | 6 |
| 9 | 9 | 0 | 9 |
| 10 | 11 | 0 | 11 |
| 11 | 12 | 0 | 12 |
| 12 | 9 | 0 | 9 |
| 13 | 5 | 0 | 5 |
| 14 | 3 | 0 | 3 |
| 15 | 10 | 0 | 10 |
| 16 | 6 | 0 | 6 |
| 18 | 9 | 0 | 9 |

## 阻断项

无。

## 逐图分数

| id | 章 | 类型 | 必要性 | 事实 | 构图 | 风格 | 印刷 | 叙事 | 节奏 | 合计 |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `ch18-assumption-tree` | 18 | V4 | 4 | 5 | 5 | 5 | 4 | — | — | 23 |
| `ch18-fault-record` | 18 | V4 | 4 | 5 | 5 | 5 | 4 | — | — | 23 |
| `ch18-two-way-validation` | 18 | V4 | 4 | 5 | 5 | 5 | 4 | — | — | 23 |
| `ch14-derating-margin` | 14 | V4 | 5 | 5 | 5 | 5 | 4 | — | — | 24 |
| `ch15-trace-drop` | 15 | V4 | 5 | 5 | 5 | 5 | 4 | — | — | 24 |
| `ch18-predict-before-probe` | 18 | V4 | 4 | 5 | 5 | 5 | 4 | — | — | 23 |
| `ch18-first-minute` | 18 | V4 | 4 | 5 | 5 | 5 | 4 | — | — | 23 |
| `ch18-four-wire` | 18 | V4 | 4 | 5 | 5 | 5 | 4 | — | — | 23 |
| `ch14-arrhenius-ten-degree` | 14 | V4 | 5 | 5 | 5 | 5 | 4 | — | — | 24 |
| `ch18-swap-discipline` | 18 | V4 | 4 | 5 | 5 | 5 | 4 | — | — | 23 |
| `ch18-component-signatures` | 18 | V4 | 4 | 5 | 5 | 5 | 4 | — | — | 23 |
| `ch18-temp-spray` | 18 | V4 | 4 | 5 | 5 | 5 | 4 | — | — | 23 |
| `ch16-instrument-trust` | 16 | V4 | 5 | 5 | 5 | 5 | 4 | — | — | 24 |
| `ch16-postmortem-split` | 16 | V4 | 5 | 5 | 5 | 5 | 4 | — | — | 24 |
| `ch15-thermal-relief` | 15 | V4 | 5 | 5 | 5 | 5 | 4 | — | — | 24 |
| `ch16-first-question` | 16 | V4 | 5 | 5 | 5 | 5 | 4 | — | — | 24 |
| `ch16-probe-compensation` | 16 | V4 | 5 | 5 | 5 | 5 | 4 | — | — | 24 |
| `ch15-adc-straddle` | 15 | V4 | 5 | 5 | 5 | 5 | 4 | — | — | 24 |
| `ch15-return-review` | 15 | V4 | 5 | 5 | 5 | 5 | 4 | — | — | 24 |
| `ch15-ground-grid` | 15 | V4 | 5 | 5 | 5 | 5 | 4 | — | — | 24 |
| `ch16-bandwidth-five` | 16 | V4 | 5 | 5 | 5 | 5 | 4 | — | — | 24 |
| `ch01-e24-ladder` | 1 | V4 | 4 | 5 | 5 | 5 | 4 | — | — | 23 |
| `ch04-gate-window` | 4 | V4 | 4 | 5 | 5 | 5 | 4 | — | — | 23 |
| `ch04-deadtime-ledger` | 4 | V4 | 4 | 5 | 5 | 5 | 4 | — | — | 23 |
| `ch05-tristate-handover` | 5 | V4 | 4 | 5 | 5 | 5 | 4 | — | — | 23 |
| `ch07-hysteresis-window` | 7 | V4 | 4 | 5 | 5 | 5 | 4 | — | — | 23 |
| `ch09-esr-window` | 9 | V4 | 4 | 5 | 5 | 5 | 4 | — | — | 23 |
| `ch05-rp-power` | 5 | V4 | 4 | 5 | 5 | 5 | 4 | — | — | 23 |
| `ch09-reference-ladder` | 9 | V4 | 4 | 5 | 5 | 5 | 4 | — | — | 23 |
| `ch10-monostable-budget` | 10 | V4 | 4 | 5 | 5 | 5 | 4 | — | — | 23 |
| `ch10-recovery-gap` | 10 | V4 | 4 | 5 | 5 | 5 | 4 | — | — | 23 |
| `ch11-mirror-three-errors` | 11 | V4 | 4 | 5 | 5 | 5 | 4 | — | — | 23 |
| `ch12-tia-three-way` | 12 | V4 | 4 | 5 | 5 | 5 | 4 | — | — | 23 |
| `ch12-switch-cap` | 12 | V4 | 4 | 5 | 5 | 5 | 4 | — | — | 23 |
| `ch12-input-types` | 12 | V4 | 4 | 5 | 5 | 5 | 4 | — | — | 23 |
| `ch06-bias-balance` | 6 | V4 | 4 | 5 | 5 | 5 | 4 | — | — | 23 |
| `ch02-esd-chain` | 2 | V4 | 4 | 5 | 5 | 5 | 4 | — | — | 23 |
| `ch02-zener-budget` | 2 | V4 | 4 | 5 | 5 | 5 | 4 | — | — | 23 |
| `ch02-junction-margin` | 2 | V4 | 4 | 5 | 5 | 5 | 4 | — | — | 23 |
| `ch02-parallel-hog` | 2 | V4 | 4 | 5 | 5 | 5 | 4 | — | — | 23 |
| `ch03-switch-budget` | 3 | V4 | 4 | 5 | 5 | 5 | 4 | — | — | 23 |
| `ch03-low-high-side` | 3 | V4 | 4 | 5 | 5 | 5 | 4 | — | — | 23 |
| `ch03-reverse-beta` | 3 | V4 | 4 | 5 | 5 | 5 | 4 | — | — | 23 |
| `ch03-config-impedance` | 3 | V4 | 4 | 5 | 5 | 5 | 4 | — | — | 23 |
| `ch03-early-effect` | 3 | V4 | 4 | 5 | 5 | 5 | 4 | — | — | 23 |
| `ch11-miller-bandwidth` | 11 | V4 | 4 | 5 | 5 | 5 | 4 | — | — | 23 |
| `ch13-compliance-ceiling` | 13 | V4 | 5 | 5 | 5 | 5 | 4 | — | — | 24 |
| `ch13-current-sense-budget` | 13 | V4 | 5 | 5 | 5 | 5 | 4 | — | — | 24 |
| `ch01-electrolytic-life` | 1 | V4 | 4 | 5 | 5 | 5 | 4 | — | — | 23 |
| `ch01-derating-product` | 1 | V4 | 4 | 5 | 5 | 5 | 4 | — | — | 23 |
| `ch04-dvdt-false-turnon` | 4 | V4 | 4 | 5 | 5 | 5 | 4 | — | — | 23 |
| `ch06-slew-vs-gbw` | 6 | V4 | 4 | 5 | 5 | 5 | 4 | — | — | 23 |
| `ch07-pullup-three-accounts` | 7 | V4 | 4 | 5 | 5 | 5 | 4 | — | — | 23 |
| `ch07-threshold-budget` | 7 | V4 | 4 | 5 | 5 | 5 | 4 | — | — | 23 |
| `ch10-astable-reverse-design` | 10 | V4 | 4 | 5 | 5 | 5 | 4 | — | — | 23 |
| `ch10-duty-fifty-paths` | 10 | V4 | 4 | 5 | 5 | 5 | 4 | — | — | 23 |
| `ch05-shoot-through-ledger` | 5 | V4 | 4 | 5 | 5 | 5 | 4 | — | — | 23 |
| `ch05-ab-bias-thermal` | 5 | V4 | 4 | 5 | 5 | 5 | 4 | — | — | 23 |
| `ch09-ldo-four-accounts` | 9 | V4 | 4 | 5 | 5 | 5 | 4 | — | — | 23 |
| `ch11-two-stage-margin` | 11 | V4 | 4 | 5 | 5 | 5 | 4 | — | — | 23 |
| `ch12-switched-cap-equivalent` | 12 | V4 | 4 | 5 | 5 | 5 | 4 | — | — | 23 |
| `ch12-input-stage-source-z` | 12 | V4 | 4 | 5 | 5 | 5 | 4 | — | — | 23 |
| `ch11-phase-margin-table` | 11 | V4 | 4 | 5 | 5 | 5 | 4 | — | — | 23 |
| `ch06-741-four-blocks` | 6 | V4 | 4 | 5 | 5 | 5 | 4 | — | — | 23 |
| `ch01-thevenin-two-load` | 1 | V4 | 4 | 5 | 5 | 5 | 4 | — | — | 23 |
| `ch02-rectifier-voltage-ledger` | 2 | V4 | 4 | 5 | 5 | 5 | 4 | — | — | 23 |
| `ch02-protection-order` | 2 | V4 | 4 | 5 | 5 | 5 | 4 | — | — | 23 |
| `ch11-noise-three-taxes` | 11 | V4 | 4 | 5 | 5 | 5 | 4 | — | — | 23 |
| `ch12-riso-feedback-point` | 12 | V4 | 4 | 5 | 5 | 5 | 4 | — | — | 23 |
| `ch13-audio-class-heat` | 13 | V4 | 5 | 5 | 5 | 5 | 4 | — | — | 24 |
| `ch11-diffpair-four-beats` | 11 | V4 | 4 | 5 | 5 | 5 | 4 | — | — | 23 |
| `ch02-bridge-junction-ledger` | 2 | V4 | 4 | 5 | 5 | 5 | 4 | — | — | 23 |
| `ch04-thermal-chain-ledger` | 4 | V4 | 4 | 5 | 5 | 5 | 4 | — | — | 23 |
| `ch01-q-selectivity-map` | 1 | V4 | 4 | 5 | 5 | 5 | 4 | — | — | 23 |
| `ch02-diode-fault-order` | 2 | V4 | 4 | 5 | 5 | 5 | 4 | — | — | 23 |
| `ch15-radiated-loop-area` | 15 | V4 | 5 | 5 | 5 | 5 | 4 | — | — | 24 |
| `ch09-tl431-divider-floor` | 9 | V4 | 4 | 5 | 5 | 5 | 4 | — | — | 23 |
| `ch13-crystal-neg-resistance` | 13 | V4 | 5 | 5 | 5 | 5 | 4 | — | — | 24 |
| `ch13-sampling-quantization` | 13 | V4 | 5 | 5 | 5 | 5 | 4 | — | — | 24 |
| `ch14-pt100-error-budget` | 14 | V4 | 5 | 5 | 5 | 5 | 4 | — | — | 24 |
| `ch10-555-fault-tree` | 10 | V4 | 4 | 5 | 5 | 5 | 4 | — | — | 23 |
| `ch10-555-threshold-clamp` | 10 | V4 | 4 | 5 | 5 | 5 | 4 | — | — | 23 |
| `ch03-ce-swing-budget` | 3 | V4 | 4 | 5 | 5 | 5 | 4 | — | — | 23 |
| `ch15-return-mirror` | 15 | V4 | 5 | 5 | 5 | 5 | 4 | — | — | 24 |
| `ch15-ground-bounce-ledger` | 15 | V4 | 5 | 5 | 5 | 5 | 4 | — | — | 24 |
| `ch15-ground-freq-split` | 15 | V4 | 5 | 5 | 5 | 5 | 4 | — | — | 24 |
| `ch15-stackup-bridge` | 15 | V4 | 5 | 5 | 5 | 5 | 4 | — | — | 24 |
| `ch16-record-card` | 16 | V4 | 5 | 5 | 5 | 5 | 4 | — | — | 24 |
| `ch11-noise-identify` | 11 | V4 | 4 | 5 | 5 | 5 | 4 | — | — | 23 |
| `ch04-channel-formation` | 4 | V4 | 4 | 5 | 5 | 5 | 4 | — | — | 23 |
| `ch03-region-check` | 3 | V4 | 4 | 5 | 5 | 5 | 4 | — | — | 23 |
| `ch04-output-regions` | 4 | V4 | 4 | 5 | 5 | 5 | 4 | — | — | 23 |
| `ch04-switching-energy-ledger` | 4 | V4 | 4 | 5 | 5 | 5 | 4 | — | — | 23 |
| `ch05-open-drain-rise` | 5 | V4 | 4 | 5 | 5 | 5 | 4 | — | — | 23 |
| `ch06-opamp-conditions` | 6 | V4 | 4 | 5 | 5 | 5 | 4 | — | — | 23 |
| `ch06-fault-conditions` | 6 | V4 | 4 | 5 | 5 | 5 | 4 | — | — | 23 |
| `ch07-window-logic` | 7 | V4 | 4 | 5 | 5 | 5 | 4 | — | — | 23 |
| `ch07-delay-endpoints` | 7 | V4 | 4 | 5 | 5 | 5 | 4 | — | — | 23 |
| `ch07-glitch-margin` | 7 | V4 | 4 | 5 | 5 | 5 | 4 | — | — | 23 |
| `ch09-shunt-corners` | 9 | V4 | 4 | 5 | 5 | 5 | 4 | — | — | 23 |
| `ch09-reference-charge` | 9 | V4 | 4 | 5 | 5 | 5 | 4 | — | — | 23 |
| `ch09-thermal-path` | 9 | V4 | 4 | 5 | 5 | 5 | 4 | — | — | 23 |
| `ch09-load-transient` | 9 | V4 | 4 | 5 | 5 | 5 | 4 | — | — | 23 |
| `ch09-transient-budget` | 9 | V4 | 4 | 5 | 5 | 5 | 4 | — | — | 23 |
| `ch10-555-modes` | 10 | V4 | 4 | 5 | 5 | 5 | 4 | — | — | 23 |
| `ch10-discharge-current` | 10 | V4 | 4 | 5 | 5 | 5 | 4 | — | — | 23 |
| `ch10-logic-margin` | 10 | V4 | 4 | 5 | 5 | 5 | 4 | — | — | 23 |
| `ch10-timer-leakage` | 10 | V4 | 4 | 5 | 5 | 5 | 4 | — | — | 23 |
| `ch10-clock-gating` | 10 | V4 | 4 | 5 | 5 | 5 | 4 | — | — | 23 |
| `ch11-topology-ports` | 11 | V4 | 4 | 5 | 5 | 5 | 4 | — | — | 23 |
| `ch11-noise-input-budget` | 11 | V4 | 4 | 5 | 5 | 5 | 4 | — | — | 23 |
| `ch11-cascode-headroom` | 11 | V4 | 4 | 5 | 5 | 5 | 4 | — | — | 23 |
| `ch11-cmrr-definitions` | 11 | V4 | 4 | 5 | 5 | 5 | 4 | — | — | 23 |
| `ch11-design-dc` | 11 | V4 | 4 | 5 | 5 | 5 | 4 | — | — | 23 |
| `ch12-sallen-key-network` | 12 | V4 | 4 | 5 | 5 | 5 | 4 | — | — | 23 |
| `ch12-feedback-ports` | 12 | V4 | 4 | 5 | 5 | 5 | 4 | — | — | 23 |
| `ch12-phase-crossing` | 12 | V4 | 4 | 5 | 5 | 5 | 4 | — | — | 23 |
