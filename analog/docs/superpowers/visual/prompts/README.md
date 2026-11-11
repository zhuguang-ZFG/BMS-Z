# 提示词记录

每张新图保存 `<id>.md`，YAML front matter 至少含 `id`、`generator`、`reference_policy`、
`numbers`、`zh_prompt`、`en_prompt`。主 manifest 保存 style/layout/color、source_facts 与输出路径。
生图底图记录也保留这些 ID、来源和预期输出；尚未调用模型时用 `generator: pending`、
`status: planned`，不要填写实际模型或生成时间。

`numbers` 的普通字符串须在来源小节出现。示意数值逐项记录：

```yaml
numbers:
  - 100Hz
  - value: 0.1Ω
    label: 示意
    reason: 扫描起点用于演示变化，不是器件保证值或实测值。
```

示意标签必须出现在图内可见文字中。检查器还会扫描 SVG 的可见数字，避免只检查已声明的子集。
模型只画无文字底图，公式、电路、数值和中文由技术图层绘制。参考资源使用上游相对路径，
不记录本机绝对路径。

`pilot/` 保存已生成的三种风格历史试片；`quant-pilot/` 保存主风格确定后的三张定量风险试片，
当前处于待生图状态。完整双层合成契约见上一级 `technical-overlay-contract.md`。
