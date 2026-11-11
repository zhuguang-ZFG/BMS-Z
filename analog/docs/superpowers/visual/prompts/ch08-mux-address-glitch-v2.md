---
id: ch08-mux-address-glitch-v2
generator: svg-v2-scene
reference_policy: none
style_id: FA-029
layout_id: IG-012
color_ids:
- C-34
- C-32
- C-35
- C-26
numbers: []
zh_prompt: 风格名称：几何图式叙事。主题：4051 地址 011→100 的一种可能中间态是 111，未禁止时可能短暂接通通道 7。危险示例与保护时序分拍显示，不把错误通道已导通画进保护帧。保护帧先拉高 INH，再改地址；INH 高电平覆盖整个地址变化与最终稳定过程，所有通道全断。地址稳定后释放 INH，至少等 t_ON 接通并另留信号建立时间，再打开采样窗。用格雷码减少多位变化是另一种编码办法。图形、公式与数值均由确定性 SVG 绘制。动画引擎技术原型，尚未完成人工评分与主风格复评。
en_prompt: 'Style name: Geometric Diagrammatic Narrative. For a 4051 address change from 011 to 100, show 111 as one possible transient; without inhibition, channel 7 may briefly conduct. Keep the unsafe example separate from the protected timing. Assert INH before changing the address and keep it high until the final address is stable; all channels remain disconnected while INH is high. Release INH, allow at least t_ON for enabling and additional signal-settling time, then sample. Gray-code encoding is a separate way to reduce multi-bit transitions. Render geometry and labels deterministically in SVG. Engine prototype; human scoring and style review remain pending.'
---
