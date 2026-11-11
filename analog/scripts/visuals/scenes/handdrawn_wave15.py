"""Wave 15 手绘草图：补五处既无插图又无候选图的小节。

每张图的数字只取对应 anchor 小节：ch2 取 2.10 例 2-1 的电压分账与导通角，
ch2 取 2.8 的三件套次序与布局军规，ch11 取 11.10 的三种税与 SNR 算例，
ch12 取 12.9 的三种反馈接法对照表，ch13 取 13.9 的四类功放效率与发热账。
"""
from __future__ import annotations

from scripts.visuals.scenes.handdrawn_wave2 import (
    AMBER, BLUE, GREEN, INK, INK2, PAPER, RED, RULE, arrow, box, header, text,
)


def _down_arrow(x: float, y1: float, y2: float, colour: str = INK2) -> list[str]:
    """竖直向下的箭头：arrow() 只画右向，向下须手写。"""
    return [
        f'<line x1="{x}" y1="{y1}" x2="{x}" y2="{y2 - 11}" '
        f'stroke="{colour}" stroke-width="2.5" stroke-linecap="round"/>',
        f'<polygon points="{x},{y2} {x - 6},{y2 - 12} {x + 6},{y2 - 12}" fill="{colour}"/>',
    ]


def rectifier_voltage_ledger():
    parts = [header('桥式整流：峰值到手里还剩多少',
                    '12 Vrms 不是 12 V 直流。峰值先扣两只管压降，再扣半个纹波，剩下的才归负载。')]

    parts.append(box(50, 130, 900, 150, fill=PAPER, stroke=BLUE))
    parts.append(text(76, 170, '空载：电流很小，管压降也小', 24, colour=BLUE, weight='700'))
    parts.append(text(76, 212, '副边峰值 12 × √2', 22, colour=INK2))
    parts.append(text(926, 214, '17.0 V', 26, colour=INK, anchor='end', weight='700'))
    parts.append(text(76, 252, '两只管子各约 0.6~0.7 V，串联扣 1.3 V，剩', 22, colour=INK2))
    parts.append(text(926, 254, '15.7 V', 26, colour=BLUE, anchor='end', weight='700'))

    parts.append(box(50, 300, 900, 186, fill=PAPER, stroke=GREEN))
    parts.append(text(76, 340, '带载 1 A：管压降升高，还要再扣半个纹波', 24, colour=GREEN, weight='700'))
    parts.append(text(76, 382, '管压降升到 0.9 V，两只串联扣', 22, colour=INK2))
    parts.append(text(926, 384, '1.8 V', 26, colour=INK, anchor='end', weight='700'))
    parts.append(text(76, 420, '现有 4700 µF、50 Hz，纹波 1 ÷ (2 × 50 × 4700 µF)', 22, colour=INK2))
    parts.append(text(926, 422, '2.13 V', 26, colour=AMBER, anchor='end', weight='700'))
    parts.append(f'<line x1="82" y1="444" x2="920" y2="444" stroke="{RULE}" stroke-width="2"/>')
    parts.append(text(76, 474, '17.0 − 1.8 − 半个纹波，平均输出', 22, colour=INK2))
    parts.append(text(926, 476, '14.1 V', 26, colour=GREEN, anchor='end', weight='700'))

    parts.append(box(50, 506, 430, 118, fill=PAPER, stroke=AMBER))
    parts.append(text(74, 546, '想把纹波压到 1 V', 24, colour=AMBER, weight='700'))
    parts.append(text(74, 584, '电容要 10,000 µF，耐压至少 25 V', 22, colour=INK2))

    parts.append(box(520, 506, 430, 118, fill=PAPER, stroke=RED))
    parts.append(text(544, 546, '平均 1 A 不等于管子只过 1 A', 24, colour=RED, weight='700'))
    parts.append(text(544, 584, '3 ms 内平均 3.3 A；峰值另查', 22, colour=INK2))
    return parts


def protection_order():
    parts = [header('接口保护三件套：顺序错了等于没装',
                    '每个伸到板外的脚都是挨打的通道。三件套不是并列的三个零件，是有先后的三道手续。')]

    parts.append(box(50, 126, 900, 90, fill=PAPER, stroke=RED))
    parts.append(text(76, 164, '打进来的是什么：人体模型 100 pF + 1.5 kΩ', 24, colour=RED, weight='700'))
    parts.append(text(76, 200, '2 kV 放电，峰值电流约 1.3 A，前沿小于 10 ns', 22, colour=INK2))
    parts.extend(_down_arrow(500, 216, 244, RED))

    parts.append(box(50, 244, 900, 90, fill=PAPER, stroke=GREEN))
    parts.append(text(76, 282, '① 先泄放大能量：TVS / ESD 阵列', 24, colour=GREEN, weight='700'))
    parts.append(text(76, 318, '把 kV 级脉冲钳到十几伏，能量从地走掉', 22, colour=INK2))
    parts.extend(_down_arrow(500, 334, 362, GREEN))

    parts.append(box(50, 362, 900, 90, fill=PAPER, stroke=BLUE))
    parts.append(text(76, 400, '② 再限流：串联电阻 / PTC', 24, colour=BLUE, weight='700'))
    parts.append(text(76, 436, '让钳位器件不必独自吃掉全部能量', 22, colour=INK2))
    parts.extend(_down_arrow(500, 452, 480, BLUE))

    parts.append(box(50, 480, 900, 90, fill=PAPER, stroke=AMBER))
    parts.append(text(76, 518, '③ 最后兜底：钳位二极管到电源轨', 24, colour=AMBER, weight='700'))
    parts.append(text(76, 554, '把残余过冲引到轨上，优先用芯片内部的那对', 22, colour=INK2))

    parts.append(box(50, 592, 900, 86, fill=PAPER))
    parts.append(text(76, 628, '三条军规', 24, colour=INK, weight='700'))
    parts.append(text(76, 664, 'TVS 贴着接口放；防护地短而粗；高速口选小于 0.5 pF 的阵列',
                      22, colour=INK2))
    return parts


def noise_three_taxes():
    parts = [header('噪声预算：三种税，一张表',
                    'datasheet 给的是每根号赫兹的密度，不是总噪声。先把单位、带宽、参考点这三件事摆正。')]

    parts.append(box(50, 130, 430, 260, fill=PAPER, stroke=BLUE))
    parts.append(text(74, 170, '三种税各自的来历', 24, colour=BLUE, weight='700'))
    parts.append(text(74, 212, '热噪声：任何电阻都有', 22, colour=INK2))
    parts.append(text(456, 248, '12.9 nV/√Hz', 24, colour=INK, anchor='end', weight='700'))
    parts.append(text(74, 250, '10 kΩ、300 K 给出', 22, colour=INK2))
    parts.append(text(74, 294, '散粒噪声：电流越过结', 22, colour=INK2))
    parts.append(text(456, 330, '17.9 pA/√Hz', 24, colour=INK, anchor='end', weight='700'))
    parts.append(text(74, 332, '1 mA 给出', 22, colour=INK2))
    parts.append(text(74, 376, '1/f 噪声：拐角处与白噪声相等', 22, colour=AMBER, weight='700'))

    parts.append(box(520, 130, 430, 260, fill=PAPER, stroke=GREEN))
    parts.append(text(544, 170, '算一笔：10 kΩ 源阻、1 mVrms 信号', 24, colour=GREEN, weight='700'))
    parts.append(text(544, 212, '噪声带宽 1 MHz，噪声', 22, colour=INK2))
    parts.append(text(926, 214, '12.9 µVrms', 24, colour=INK, anchor='end', weight='700'))
    parts.append(text(544, 250, '信噪比只有', 22, colour=INK2))
    parts.append(text(926, 252, '37.8 dB', 26, colour=RED, anchor='end', weight='700'))
    parts.append(f'<line x1="550" y1="274" x2="920" y2="274" stroke="{RULE}" stroke-width="2"/>')
    parts.append(text(544, 312, '带宽 10 kHz：1.29 µV', 22, colour=INK2))
    parts.append(text(926, 314, '57.8 dB', 24, colour=GREEN, anchor='end', weight='700'))
    parts.append(text(544, 352, '源阻 1 kΩ：4.07 µV', 22, colour=INK2))
    parts.append(text(926, 354, '47.8 dB', 24, colour=GREEN, anchor='end', weight='700'))

    parts.append(box(50, 412, 900, 104, fill=PAPER, stroke=AMBER))
    parts.append(text(76, 450, '噪声带宽不是信号带宽', 24, colour=AMBER, weight='700'))
    parts.append(text(76, 488, '一阶低通的等效噪声带宽是 1.57 倍截止频率，拿截止频率代入会低估',
                      22, colour=INK2))

    parts.append(box(50, 540, 900, 104, fill=PAPER, stroke=RED))
    parts.append(text(76, 578, '合账按均方值相加，不按电压相加', 24, colour=RED, weight='700'))
    parts.append(text(76, 616, '四个等量且互不相关的项，合起来是单项的 2 倍、约 6.02 dB，不是 4 倍',
                      22, colour=INK2))
    return parts


def riso_feedback_point():
    parts = [header('同一只隔离电阻，反馈接哪头决定稳不稳',
                    '容性负载不是靠加一只电阻就压住的。电阻加在哪、反馈从哪取，是两件事。')]

    parts.append(box(50, 126, 900, 86, fill=PAPER))
    parts.append(text(76, 164, '教学模型（可复核）', 24, colour=INK, weight='700'))
    parts.append(text(76, 200, '开环增益 10 的 5 次方、主极点 10 Hz、输出阻抗 50 Ω，驱动 100 nF，阶跃 10 mV',
                      22, colour=INK2))

    parts.append(box(50, 232, 900, 110, fill=PAPER, stroke=RED))
    parts.append(text(76, 272, '不加隔离电阻', 24, colour=RED, weight='700'))
    parts.append(text(76, 310, '明显欠阻尼，输出过冲超过 70%', 22, colour=INK2))
    parts.append(text(926, 300, '10.2°', 30, colour=RED, anchor='end', weight='700'))

    parts.append(box(50, 362, 900, 110, fill=PAPER, stroke=GREEN))
    parts.append(text(76, 402, '加 50 Ω，反馈取 A 点（电阻之前）', 24, colour=GREEN, weight='700'))
    parts.append(text(76, 440, '此模型中运放端与负载端过冲都小于 5%', 22, colour=INK2))
    parts.append(text(926, 430, '88.2°', 30, colour=GREEN, anchor='end', weight='700'))

    parts.append(box(50, 492, 900, 110, fill=PAPER, stroke=AMBER))
    parts.append(text(76, 532, '加 50 Ω，反馈取 B 点（负载端）', 24, colour=AMBER, weight='700'))
    parts.append(text(76, 570, '比不加电阻时振铃更严重：零点不再出现在反馈里', 22, colour=INK2))
    parts.append(text(926, 560, '7.2°', 30, colour=RED, anchor='end', weight='700'))

    parts.append(box(50, 622, 900, 62, fill=PAPER, stroke=BLUE))
    parts.append(text(76, 662, '50 Ω 配 100 nF 对应约 31.8 kHz 的极点，但稳不稳要在环路穿越 0 dB 处判',
                      22, colour=BLUE, weight='700'))
    return parts


def audio_class_heat():
    parts = [header('功放选类别，先算这笔热账',
                    '同样推 10 W，B 类散 6.7 W 的热，D 类只散 1.1 W。指甲盖大小和大散热器的差别就在这。')]

    parts.append(box(50, 130, 900, 150, fill=PAPER, stroke=BLUE))
    parts.append(text(76, 170, '先把 8 Ω 喇叭要的 10 W 换成电压电流', 24, colour=BLUE, weight='700'))
    parts.append(text(76, 212, '有效值 8.94 V、电流 1.12 A，峰值', 22, colour=INK2))
    parts.append(text(926, 214, '12.6 V', 26, colour=INK, anchor='end', weight='700'))
    parts.append(text(76, 252, '推挽要留管压降，所以电源至少', 22, colour=INK2))
    parts.append(text(926, 254, '±15 V', 26, colour=BLUE, anchor='end', weight='700'))

    parts.append(box(50, 300, 430, 196, fill=PAPER, stroke=RED))
    parts.append(text(74, 340, '用 B 类：理论 78.5%', 24, colour=RED, weight='700'))
    parts.append(text(74, 382, '实际按 60% 算', 22, colour=INK2))
    parts.append(text(74, 420, '电源要提供 16.7 W', 22, colour=INK2))
    parts.append(text(74, 464, '其余全变热', 22, colour=INK2))
    parts.append(text(456, 468, '6.7 W', 30, colour=RED, anchor='end', weight='700'))

    parts.append(box(520, 300, 430, 196, fill=PAPER, stroke=GREEN))
    parts.append(text(544, 340, '换 D 类：效率 90%', 24, colour=GREEN, weight='700'))
    parts.append(text(544, 382, '同样的音质', 22, colour=INK2))
    parts.append(text(544, 420, '指甲盖大的芯片就够', 22, colour=INK2))
    parts.append(text(544, 464, '只发热', 22, colour=INK2))
    parts.append(text(926, 468, '1.1 W', 30, colour=GREEN, anchor='end', weight='700'))

    parts.append(box(50, 522, 900, 76, fill=PAPER, stroke=AMBER))
    parts.append(text(76, 560, '省下的热不是白给的', 24, colour=AMBER, weight='700'))
    parts.append(text(76, 592, 'D 类的 PWM 边沿是强干扰源，输出要加 LC 滤波，必须过 EMI', 22, colour=INK2))

    parts.append(box(50, 618, 900, 66, fill=PAPER))
    parts.append(text(76, 656, '偏置管必须贴散热器与功率管热耦合，否则温升推高偏置电流，直接热失控',
                      22, colour=INK, weight='700'))
    return parts


SCENES = {
    'ch02-rectifier-voltage-ledger': {
        'draw': rectifier_voltage_ledger, 'title': '桥式整流的电压分账与峰值电流',
        'anchor': '2.10', 'chapter': 2, 'source': 'docs/p1-03-ch2.md',
        'alt': '手绘桥式整流电压分账。上面蓝框空载：副边峰值 12 乘根号 2 得 17.0 伏，'
               '两只管子各约 0.6 到 0.7 伏、串联扣 1.3 伏，剩 15.7 伏。'
               '中间绿框带载 1 安：管压降升到 0.9 伏、两只串联扣 1.8 伏，'
               '现有 4700 微法配 50 赫兹，纹波等于 1 除以 2 乘 50 乘 4700 微法得 2.13 伏，'
               '17.0 减 1.8 再减半个纹波，平均输出 14.1 伏。'
               '左下琥珀框写想把纹波压到 1 伏，电容要 10,000 微法、耐压至少 25 伏；'
               '右下红框写负载平均 1 安不等于管子只过 1 安，导通只占 3 毫秒，窗口平均 3.3 安；实际峰值须另查脉形。',
    },
    'ch02-protection-order': {
        'draw': protection_order, 'title': '接口保护三件套的先后次序',
        'anchor': '2.8', 'chapter': 2, 'source': 'docs/p1-03-ch2.md',
        'alt': '手绘接口保护三件套自上而下的次序图，四块之间用实心向下箭头相连。'
               '顶部红框写打进来的是什么：人体模型 100 皮法加 1.5 千欧，'
               '2 千伏放电的峰值电流约 1.3 安、前沿小于 10 纳秒。'
               '第一步绿框先泄放大能量，用 TVS 或 ESD 阵列把千伏级脉冲钳到十几伏，能量从地走掉；'
               '第二步蓝框再限流，用串联电阻或 PTC，让钳位器件不必独自吃掉全部能量；'
               '第三步琥珀框最后兜底，用钳位二极管到电源轨把残余过冲引到轨上，优先用芯片内部的那对。'
               '底部写三条军规：TVS 贴着接口放，防护地短而粗，高速口选小于 0.5 皮法的阵列。',
    },
    'ch11-noise-three-taxes': {
        'draw': noise_three_taxes, 'title': '三种噪声税与信噪比算例',
        'anchor': '11.10', 'chapter': 11, 'source': 'docs/p2-01-ch11.md',
        'alt': '手绘噪声预算两栏。左侧蓝框三种税的来历：热噪声任何电阻都有，'
               '10 千欧配 300 开给出 12.9 纳伏每根号赫兹；散粒噪声是电流越过结，'
               '1 毫安给出 17.9 皮安每根号赫兹；1 比 f 噪声在拐角处与白噪声相等。'
               '右侧绿框算一笔，源阻 10 千欧、信号 1 毫伏有效值：噪声带宽 1 兆赫时噪声 12.9 微伏有效值，'
               '信噪比只有 37.8 分贝；带宽压到 10 千赫、噪声 1.29 微伏，信噪比 57.8 分贝；'
               '源阻降到 1 千欧、噪声 4.07 微伏，信噪比 47.8 分贝。'
               '中段琥珀框写噪声带宽不是信号带宽，一阶低通的等效噪声带宽是 1.57 倍截止频率，'
               '拿截止频率代入会低估。底部红框写合账按均方值相加、不按电压相加，'
               '四个等量且互不相关的项合起来是单项的 2 倍、约 6.02 分贝，不是 4 倍。',
    },
    'ch12-riso-feedback-point': {
        'draw': riso_feedback_point, 'title': '隔离电阻的反馈取点与相位裕度',
        'anchor': '12.9', 'chapter': 12, 'source': 'docs/p2-02-ch12.md',
        'alt': '手绘三行对照表，同一只隔离电阻换反馈取点。顶部写教学模型：'
               '开环增益 10 的 5 次方、主极点 10 赫兹、输出阻抗 50 欧，驱动 100 纳法，阶跃 10 毫伏。'
               '第一行红框不加隔离电阻，相位裕度 10.2 度，明显欠阻尼、输出过冲超过 70%；'
               '第二行绿框加 50 欧并把反馈取在 A 点也就是电阻之前，相位裕度 88.2 度，'
               '此模型中运放端与负载端过冲都小于 5%；'
               '第三行琥珀框加 50 欧但反馈取在 B 点也就是负载端，相位裕度只剩 7.2 度，'
               '比不加电阻时振铃更严重，因为零点不再出现在反馈里。'
               '底部蓝框写 50 欧配 100 纳法对应约 31.8 千赫的极点，'
               '但稳不稳要在环路穿越 0 分贝处判。',
    },
    'ch13-audio-class-heat': {
        'draw': audio_class_heat, 'title': 'B 类与 D 类推同一只喇叭的热账',
        'anchor': '13.9', 'chapter': 13, 'source': 'docs/p2-03-ch13.md',
        'alt': '手绘功放热账。顶部蓝框先把 8 欧喇叭要的 10 瓦换成电压电流：'
               '有效值 8.94 伏、电流 1.12 安，峰值 12.6 伏；推挽要留管压降，所以电源至少正负 15 伏。'
               '左下红框用 B 类，理论效率 78.5%、实际按 60% 算，电源要提供 16.7 瓦，'
               '其余全变热 6.7 瓦；右下绿框换 D 类，效率 90%，同样的音质，'
               '指甲盖大的芯片就够，只发热 1.1 瓦。'
               '琥珀框写省下的热不是白给的：D 类的 PWM 边沿是强干扰源，输出要加 LC 滤波、必须过 EMI。'
               '底部写偏置管必须贴散热器与功率管热耦合，否则温升推高偏置电流，直接热失控。',
    },
}

# Corrected chapter 11 model and visual contract.
from scripts.visuals.scenes.ch11_reference_figures import SCENES as _ch11_corrected
SCENES['ch11-noise-three-taxes'] = _ch11_corrected['ch11-noise-three-taxes']

# Corrected chapter 12 models and source conditions.
from scripts.visuals.scenes.ch12_reference_figures import SCENES as _ch12_corrected
SCENES['ch12-riso-feedback-point'] = _ch12_corrected['ch12-riso-feedback-point']

# Chapter 13 reviewed model overrides.
from scripts.visuals.scenes.ch13_reference_figures import SCENES as _CH13_REVIEWED
for _aid in ['ch13-audio-class-heat']:
    SCENES[_aid] = _CH13_REVIEWED[_aid]
