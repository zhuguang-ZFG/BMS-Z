---
search: false
slug: protection-proof-matrix
style: FA-029
colors: [C-03, C-15]
frames: 5
caption: 原理示意 / 非实拍
bans: [no-people, no-cartoon-IP, no-live-photo-claim]
kp_id: protection-debounce
source_svg: null
---

# 观察题

两路保护一起切断成功，能证明硬件路径与软件路径各自都能切断吗？

# 事实表

来源：[阶段 3 §3.7](../../../stages/stage-3-AFE-MCU智能BMS.md#37-调试先模拟后接电池-应用) 第 5 步要求「AFE 硬件保护与 MCU 软件保护各自独立生效（分别屏蔽一边测）」。本图画验证条件的区分，不画动作速度，不给阈值、延时或芯片寄存器设置。

| 条件 | 预期观测 | 能支持的结论 |
|---|---|---|
| 两条动作路径都允许 | 故障下切断 | 至少一路起了作用，不能单独归因 |
| 软件动作屏蔽、硬件动作保留 | 同一故障下应切断 | 所测条件下硬件路径可独立动作 |
| 硬件动作屏蔽、软件动作保留 | 同一故障下应切断 | 所测条件下软件路径可独立动作 |
| 两组分别成功 | 两组各自留证 | 不等于所有故障条件都被覆盖，也不等于有两个独立执行器 |

试验限制：隔离、限流的电芯模拟台架，故障条件可重复。图内是预期结果，不冒充实测记录。实际试验必须依芯片与台架规程确认可安全屏蔽的动作路径及恢复步骤；不得在真电池上停用保护。两条路径可能共用传感、供电、驱动或 MOS，不能因此声称双重硬件冗余。

# 帧大纲

1. 固定四列表头与三组试验位置；联合试验两条路径均允许，尚未施加故障。
2. 联合试验显示切断，但归因不明：有一路失效时，另一路仍可能掩盖它。
3. 展开仅测硬件一行：软件动作屏蔽、硬件动作允许，应切断；恢复后再换下一组。
4. 展开仅测软件一行：硬件动作屏蔽、软件动作允许，应切断；两组分别留证。
5. 保留完整矩阵，补充结论边界：仅支持已测条件下各自可动作；共用执行器不等于双重硬件冗余。

# Prompt（中文）

风格名称：几何叙事信息图。参考作者与风格名称：Chris Ware 几何叙事。普鲁士蓝结构线与文字，纸张颗粒，克制的几何对照。五帧固定同一布局：四列表头为试验条件、硬件路径、软件路径、预期观测。逐帧展开联合试验、仅测硬件、仅测软件三行。联合切断不标作两路均已验证；两组分别屏蔽的试验各自标预期切断。末帧仅用小段朱砂红强调共用执行器不等于双重硬件冗余。图注为原理示意 / 非实拍。限流模拟台架，所有结果均为预期结果，不表现为真实测量；无人、无卡通形象、无品牌标志。

# Prompt（EN）

Style name: geometric narrative information diagram. Reference author and style name: Chris Ware geometric narrative. Prussian-blue linework and lettering, paper grain, restrained geometric comparisons. Five frames keep a fixed four-column layout: test condition, hardware action path, software action path, expected observation. Reveal a joint test, hardware-only test and software-only test in sequence. A successful joint cutoff must not be presented as proof of both paths. Each single-path test expects a cutoff with the other action path inhibited. In the final frame, a small vermilion note identifies the boundary: a shared actuator is not dual hardware redundancy. Caption: 原理示意 / 非实拍. Use a current-limited cell-simulator bench and identify outcomes as expected, not measured. No people, cartoon characters or brand logos.
