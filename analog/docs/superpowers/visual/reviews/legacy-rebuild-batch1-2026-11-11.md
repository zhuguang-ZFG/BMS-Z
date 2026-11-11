# Legacy 动画 rebuild 批次 1（2026-11-11）

7 个 legacy 动画由 **已签核 accepted 的 V2 资产**替代。第 5 部分动画索引页（p5-00-part5.md）对应 demo 节已换图，看点句按 V2 签核 alt 重写（数字逐项来自 manifest alt，未新增事实）。

| legacy | demo 节 | replacement（accepted） |
|---|---|---|
| assets/svg/bandgap.svg | 5.20 | assets/svg-v2/ch09-bandgap-balance-v2.svg |
| assets/svg/tl431.svg | 5.21 | assets/svg-v2/ch09-tl431-bias-v2.svg |
| assets/svg/sample-hold.svg | 5.22 | assets/svg-v2/ch08-sample-hold-v2.svg |
| assets/svg/divider-loading.svg | 5.39 | assets/svg-v2/ch00-divider-loading-v2.svg |
| assets/svg/transfer-gate.svg | 5.50 | assets/svg-v2/ch08-transfer-gate-v2.svg |
| assets/svg/source-types.svg | 5.78 | assets/svg-v2/ch00-source-types-v2.svg |
| assets/svg/ground-bounce.svg | 5.117 | assets/svg-v2/ch05-ground-bounce-v2.svg |

排除项：assets/svg/integrator.svg（5.33）——候选替代 ch12-leaky-integrator-v2 为频域幅频特性图，与原"方波换三角波"时域演示内容形态不同，留人工重组节标题与叙述。

验证：check_visual_manifest PASS；check_visual_release 闸 legacy disposition 153→146。
