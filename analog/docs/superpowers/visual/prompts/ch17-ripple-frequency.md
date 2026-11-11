---
id: ch17-ripple-frequency
generator: deterministic-svg-v1
reference_policy: none
numbers:
- 100Hz
- 50Hz
- 400mV
- 3.1V
- 三成
zh_prompt: |
  风格名称：几何图式叙事。主题色：象牙白（Ivory）、佩恩灰（Payne's grey）、赭石（Ochre）。
  画面主题：纹波判读三栏对比图。标题「纹波判读：先问频率，再问幅度」，副题点出"同样的纹波大，频率指认的方向完全不同"。三栏波形卡：①100Hz 工频纹波（大摆幅正弦，红）——嫌疑：整流后的大电解干涸（ESR 升高），动作：换低 ESR 电解或并联陶瓷；②开关频率及其谐波（高频小纹波，蓝）——嫌疑：输出滤波不足（开关电源固有纹波），动作：看 SW 波形找谐波源、加 LC/磁珠；③LDO 输出上的 100Hz（小摆幅正弦，赭）——嫌疑：压差太小/PSRR 不够，动作：查压差与输入纹波、选高 PSRR 器件。中部赭石判读条：「先问频率，再问幅度——测量必须能区分候选假设，只答"大不大"等于没测」。底部教学示例链路四卡：症状（5V 只有 3.1V、纹波 400mV）→ 测量①量频率（100Hz 整流纹波→指向大电解）→ 测量②量大电解（烫手·ESR 升高，容量只剩标称三成）→ 根因落定（换低 ESR 电解，两次测量没拆一颗芯片）。底注：100Hz=全波整流、50Hz=半波——频率的"户口"指认整流与滤波。
en_prompt: |
  Style name: Geometric Diagrammatic Narrative. Theme color: Ivory, Payne's grey, Ochre.
  Subject: a three-column ripple-reading comparison sheet titled "read ripple frequency first, amplitude second". Column one: a large 100Hz mains sine (red) — suspect: dried bulk electrolytic after rectification (ESR risen); action: replace with low-ESR electrolytic or add ceramics. Column two: switching-frequency ripple plus harmonics (dense small ripple, blue) — suspect: insufficient output filtering (inherent switching ripple); action: inspect the SW waveform, add LC/ferrite. Column three: a small 100Hz sine on an LDO output (ochre) — suspect: leaked from the input (dropout too small / weak PSRR); action: check dropout and PSRR. An ochre verdict bar: "frequency first, amplitude second — a measurement must discriminate candidate hypotheses". Bottom worked-example chain of four cards: symptom (5V rail reads 3.1V, 400mV ripple) → measure frequency (100Hz rectification ripple → points to the bulk cap) → probe the bulk cap (hot, ESR risen, capacitance down to a third of rating) → root cause set (replace with low-ESR electrolytic; two measurements, zero chips removed). Footnote: 100Hz = full-wave, 50Hz = half-wave — where the frequency was born names the culprit.
---
