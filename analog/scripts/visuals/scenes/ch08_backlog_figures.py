"""§8 二十张静态图的统一登记；绘制函数分在 a/b 两个模块。"""
from __future__ import annotations

from scripts.visuals.scenes.ch08_figures_a import FIGURES as _A
from scripts.visuals.scenes.ch08_figures_b import FIGURES as _B

_ALTS = {
    'ch08-threshold-loss-gap': '左右两栏：左栏画单 N 管从 5V 供电传到 4V、体效应退到 3.5V、下游门限 2.5V 的三道水位线；右栏画 N/P 并联后 20→26.7→20Ω 的包络，并列出 I²C 与音频分流两个单管岗位。',
    'ch08-gain-error-thermal-noise': '五行误差账：120Ω 配 100kΩ 得 0.12%、平坦度 ±30Ω 得 0.03%、全温 ×1.4 得 0.17%、100Ω 开关热噪声 1.3µV、10nF 的 kT/C 0.64µV；右侧读数只做量级比较。',
    'ch08-three-generation-error-race': '四步对比：CD4066 百Ω级、74HC4066 三十Ω级、专用低阻 Ω 级，末步把“哪一格先撞线”作为判据，并指出 16 位或 100kSa/s 以上才轮到专用器件。',
    'ch08-bootstrap-flatness-derivation': '左栏三行缺口推导落到判据 VDD−Vin > VTH+VSB；右栏自举把 VGS 钉在 5V，R_ON=80/5=16Ω 成一条水平线，代价是一只电容与本地驱动。',
    'ch08-off-state-traps': '左右两栏：左栏超轨时 ESD 二极管在 0.6V 导通、5V 轨遇 6V 毛刺越界，对策是限流或钳位；右栏半导通停在阈区，R_ON 大几个量级且随温度漂，判据是跃迁时间与 VIL/VIH 余量。',
    'ch08-mux16-timing-leakage-ledger': '五行账：软件 1µs、τ=410ns、12 位建立 3.4µs、一帧 80µs、85°C 漏流约 1µA 在 10kΩ 上得 10mV；条带只表示相对量级。',
    'ch08-crosstalk-cascade-mismatch': '双对数频率轴上两条 20dB/十倍频泄漏线：10kΩ 在 100kHz 为 −50dB、600Ω 压到 −65dB 以下；另标差分失配 10Ω 得 60dB 与每十倍频 20dB 的斜率。',
    'ch08-audio-routing-4053-topology': '五步预算顺序：±2V/20kHz 的双极性、16 位比 12 位紧 16 倍、−80dB 串扰、50Ω 对 600Ω 的 0.08V/V 插入损耗，最后一步说明 4053 切的是反馈电阻与节点。',
    'ch08-path-through-tree-star': '左右两栏：星形一片 16 路、总漏流 16 路之和、COM 寄生最大；树形两片加一级、串联 500Ω、每片 8 路漏流；底部以 16/32 通道数分界。',
    'ch08-param-triangle-tradeoff': '中心是 R_ON、注入与寄生、带宽与串扰的三角矛盾，三支分别写大沟道与小沟道的代价；中心框先问负载、温度、信号幅度三个测试条件。',
    'ch08-five-param-budget-table': '五行误差账：0.2、0.04、0.4、0.2 LSB 与 kT/C 忽略，右侧 RSS 约 0.5LSB；说明 4066 加 10nF 与一级缓冲够 12 位。',
    'ch08-switch-capacitor-network': '左右两栏把开关拆成五只元件：导通态 R_ON 与两只 Cout 决定带宽和建立；关断态 Cds 与 Cin 决定隔离和馈通；供电从 5V 到 15V 使 R_ON 从百Ω级降到几十Ω级。',
    'ch08-acquisition-settle-time': '五步：τ=750ns、12 位 8.3τ≈6.2µs、加延时约 7µs、留 30% 余量后承诺 100kSa/s，末步提醒半 LSB 口径是 9τ。',
    'ch08-e2e-case-1ksa': '五步走查 1kSa/s 记录仪：单电源家族、1MΩ 负载下 0.005%、10nF C0G、8.3τ≈104µs 远小于 1ms、2nA 漏流 1ms 掉 0.4LSB；每步都标“过”。',
    'ch08-charge-sharing-back-to-back': '左右两栏：左栏闭合瞬间 100pF 对 Chold 重分配出约 10mV 尖峰、按 10τ 衰减；右栏背靠背两只开关先断外后断内，中间节点吸收电荷，代价是两相控制与 R_ON 翻倍。',
    'ch08-sh-field-tests': '五步：三条件判定门、三条都否就删掉分立 S/H、100nF/1V/1µs 的理想 100mA 与 R_ON 限流后的 4mA、100ms 掉 200µV 得 2pA 并把矛头指向板面。',
    'ch08-triage-record-three-lines': '五站排故路径：0.1mA 跳到 12mA 的签名、带电插必现、数十伏窄脉冲、钳位加 1kΩ 后复现 50 次、最后压成现象/根因/防线三行。',
    'ch08-lab-bench-setup': '中心是 2.000V 信号源、VDD=5V 传输门、干净 EN 方波、Ch=10pF 与高阻缓冲四个量；四支说明初始全关、EN 跳高同导、探头电容的双面性、示波器四段。',
    'ch08-fifth-beat-temperature': '五行温度动作：R_ON ×1.3~1.5、漏流每 10°C 翻倍、注入随 VTH 漂移、750Ω×10nF 得 21kHz、热噪声等于 kT/C；结论是加大 Chold 而非换低阻开关。',
    'ch08-scope-expected-beats': '示波器预期波形：拍①指数爬升、拍③沿上窄台阶、随后 droop 缓降、再采样；右上标控制摆幅 5V 与 3.3V 下馈通 0.5mV 与 0.33mV，屏角注明非实测。',
}

FIGURES = {}
for _group in (_A, _B):
    for _asset_id, (_draw, _title, _anchor, _layout, _kind) in _group.items():
        FIGURES[_asset_id] = {
            'draw': _draw, 'title': _title, 'anchor': _anchor,
            'layout': _layout, 'type': _kind, 'chapter': 8,
            'source': 'docs/p1-09-ch8.md', 'alt': _ALTS[_asset_id],
        }
