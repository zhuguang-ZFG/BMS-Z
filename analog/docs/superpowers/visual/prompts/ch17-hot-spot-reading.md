---
id: ch17-hot-spot-reading
generator: deterministic-svg-v1
reference_policy: none
numbers:
- 60°C
- 10°C
zh_prompt: |
  风格名称：几何图式叙事。主题色：象牙白（Ivory）、佩恩灰（Payne's grey）、赭石（Ochre）。
  画面主题：热类故障定位流程图。顶部两步流程卡：第一步蓝卡「先扫：红外热像仪/指尖点触」——扫出整板温度分布图，异常热点自己站出来，指尖只在安全电压下快速点触、超过约 60°C 就别摸；第二步赭卡「后喷：冷冻喷剂逐器件降温」——看故障何时消失，消失的那只就是嫌疑，喷过会结露、回温干燥再下结论。中部左卡「分布还是单点」：单个器件热→它功耗大（红条）；一片区域一起热→热源在别处、这里只是散热路径（绿条）。中部右卡「红外两条纪律」：裸金属与光亮表面发射率低读数系统性偏低→贴哑光胶带再测；热像仪看到的是表面温度不是结温→按热阻链折算。中部赭石判读条：「温度测量永远先看分布，再看单点——先喷后扫，整板喷冷，线索全灭」。底部教学示例三卡链：电容鼓包的位置本身就是一张热源地图（旁边往往坐着散热器或功率管）→ 换电容时顺手降温（挪位/隔热/改善风道）→ 收益比换更大容值的电容大得多。底注：结温每降 10°C 寿命约翻一倍——修好"坏"之后，降额管的是"不再坏"。
en_prompt: |
  Style name: Geometric Diagrammatic Narrative. Theme color: Ivory, Payne's grey, Ochre.
  Subject: a two-step heat-fault localization sheet. Step one (blue): scan first — IR camera or careful fingertip taps (safe voltage only, never touch above about 60°C) to map the board's temperature distribution; abnormal hot spots announce themselves. Step two (ochre): spray second — freeze suspect devices one by one and watch when the fault disappears; sprayed areas condense moisture, so let them warm and dry before concluding. Middle-left card "distribution or single point": one device hot → its own dissipation (red strip); a whole region warm → the heat source is elsewhere, this is just the thermal path (green strip). Middle-right card "two IR disciplines": bare metal and shiny surfaces read systematically low — stick a matte tape patch; thermal cameras see surface temperature, not junction — fold down the thermal-resistance chain. Ochre verdict bar: "always read the distribution before the single point — spray-first kills every clue". Bottom worked-example chain of three cards: a bulged capacitor's location is itself a heat-source map (a heatsink or power transistor usually sits next door) → when replacing it, cool its environment too (relocate, shield, improve airflow) → that pays more than a bigger capacitor. Footnote: every 10°C off the junction roughly doubles lifetime — fixing "broken" is the repair, derating is "never breaks again".
---
