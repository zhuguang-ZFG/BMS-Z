---
id: ch17-oscillation-order
generator: deterministic-svg-v1
reference_policy: none
numbers:
- 50mΩ
- 1A
- 50mV
zh_prompt: |
  风格名称：几何图式叙事。主题色：象牙白（Ivory）、佩恩灰（Payne's grey）、赭石（Ochre）。
  画面主题：振荡类故障固定排查顺序图。左侧四层阶梯自上而下：①电源去耦（验证：看纹波谱，一块示波器就能验）→②环路相位裕度（验证：看阶跃响应的过冲）→③布线寄生耦合（验证：看布局）→④接地环路（验证：看多点之间的电压差，可能得动板），层间下连箭头。右侧上卡「动手前先分两刀」：刀①断开外部源做电池供电试（振荡消失=外来干扰，纹丝不动=电路自振）；刀②看频率随电源/负载/温度变不变（自激频率由环路参数决定）——「频率的户口在哪，嫌疑就在哪」。右侧下卡「地环路的量级感」：5cm 地铜 ≈ 50mΩ × 1A 开关电流 = 50mV 地弹垫进小信号放大器参考点，症状最像前三者所以放在最后查。中部赭石判读条：「顺序即排查顺序，照做不要跳——从外到内、从便宜到贵」。底部绿标边界条件卡：三个旋钮各扫一遍记起振/停振临界点，临界点离工作点越远裕度越大。底注："接上探头振荡消失"=测量动作治好了病，修电路不修现象。
en_prompt: |
  Style name: Geometric Diagrammatic Narrative. Theme color: Ivory, Payne's grey, Ochre.
  Subject: the fixed four-tier hunt order for circuits that oscillate when they shouldn't. Left ladder top-down: 1 supply decoupling (read the ripple spectrum, one scope is enough) → 2 loop phase margin (read step-response overshoot) → 3 layout parasitic coupling (read the layout) → 4 ground loop (read voltage between points, may need board work), arrows between tiers. Upper-right card "two cuts before you start": cut 1 disconnect the external source (battery test — oscillation vanishes = injected interference, persists = the circuit itself); cut 2 does frequency track supply/load/temperature (self-excited frequency belongs to the loop) — "where the frequency was born, the suspect lives". Lower-right card "a sense of scale for ground loops": 5cm of ground copper ≈ 50mΩ × 1A switching current = 50mV of ground bounce sitting on a small-signal reference — symptoms mimic the first three, hence checked last. Ochre verdict bar: "the order is the procedure — outside-in, cheap-to-expensive". Green boundary-condition card: sweep load, temperature and supply, note the start/stop oscillation thresholds; the farther the threshold from the operating point, the larger the margin. Footnote: "oscillation stops when the probe clips on" = the measurement cured the disease — fix the circuit, not the symptom.
---
