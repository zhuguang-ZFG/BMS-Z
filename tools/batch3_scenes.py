"""第 3 批机制图。曲线在这里用公式算，再交给 gen_mechanism_svgs.main 写盘。

不改 code/。教学数都标示意，不写成某一颗电芯或某一版国标的摘录。
"""
from __future__ import annotations

import sys

import numpy as np

from gen_mechanism_svgs import (
    ROOT,
    axis_box,
    dot,
    fade_labels,
    poly,
    segment_times,
    steps,
    wrap,
    xticks,
    yticks,
)

# 图区固定。刻度和曲线都用这一组，避免字压到轴外面。
X0, X1, YT, YB = 108.0, 720.0, 248.0, 400.0


def readout(*parts: str) -> str:
    """底栏只放带名字的数，示意写在句末一次。"""
    return " · ".join(parts) + "（示意）"


def band(x: float, y: float, w: float, h: float, cls: str) -> str:
    return (
        f'  <rect class="{cls}" x="{x:.1f}" y="{y:.1f}" width="{max(w, 0):.1f}" height="{max(h, 0):.1f}"/>'
    )


def moving(samples: list[tuple[float, float]], cls: str = "doty") -> tuple[str, str]:
    """金点跟读数走。红点同一条路径，begin 提前半圈。"""
    framed = list(samples) + [samples[-1]]
    kt = segment_times(len(samples))
    body = "\n".join(
        (
            dot(framed, cls=cls, kt=kt),
            dot(framed, cls="dotr", r=4, kt=kt, begin="-6s"),
        )
    )
    return kt, body


def scene(
    headline: str,
    step_lines: list[str],
    y_cap: str,
    x_cap: str,
    ticks: str,
    series: str,
    legend: str,
    labels: list[str],
    kt: str,
    foot: str,
    svg_title: str,
    svg_desc: str,
    formula: str,
) -> str:
    height = 590
    body = f"""  <rect class="bg" width="800" height="{height}"/>
  <text class="title" x="24" y="32">{headline}</text>
  <rect class="panel" x="24" y="44" width="752" height="124" rx="6"/>
{steps(step_lines, y0=68, dy=24)}
  <rect class="panel" x="24" y="180" width="752" height="268" rx="6"/>
  <text class="small" x="40" y="202">{y_cap}</text>
{legend}
{axis_box(X0, YT, X1, YB)}
{ticks}
  <text class="small" x="{X1:.0f}" y="444" text-anchor="end">{x_cap}</text>
{series}
  <rect class="panel" x="24" y="460" width="752" height="68" rx="6"/>
{fade_labels(labels, 40, 500, cls="small", kt=kt)}
  <text class="small" x="24" y="560">{foot}</text>
"""
    return wrap(svg_title, svg_desc, body, height, formula)


def _xy(x_of, y_of, xs, ys) -> list[tuple[float, float]]:
    return list(zip(x_of(xs), y_of(ys), strict=True))


def build_i2t() -> str:
    """矩形时窗：I²t = 500² × t。对数轴上是一条直线。"""
    current = 500.0
    t = np.logspace(-6, -2, 61)
    energy = current**2 * t
    tmin, tmax = 1e-6, 1e-2
    emin, emax = current**2 * tmin, current**2 * tmax

    def x_of(v):
        lv = np.log10(np.asarray(v, dtype=float))
        return X0 + (lv - np.log10(tmin)) / (np.log10(tmax) - np.log10(tmin)) * (X1 - X0)

    def y_of(v):
        lv = np.log10(np.asarray(v, dtype=float))
        return YT + (np.log10(emax) - lv) / (np.log10(emax) - np.log10(emin)) * (YB - YT)

    pts = _xy(x_of, y_of, t, energy)
    marks = (2e-6, 10e-6, 1e-4, 1e-3)
    stations = [(float(x_of(m)), float(y_of(current**2 * m))) for m in marks]
    kt, dots = moving(stations)
    labels = [
        readout("t = 2 μs", "I²t = 0.5 A²s"),
        readout("t = 10 μs", "I²t = 2.5 A²s"),
        readout("t = 100 μs", "I²t = 25 A²s"),
        readout("t = 1 ms", "I²t = 250 A²s"),
    ]
    callouts = []
    # 10 μs 的字放在点的右下方，短引线避开斜率 1 的红线。1 ms 仍在点的左上方。
    x10 = float(x_of(10e-6))
    y10 = float(y_of(current**2 * 10e-6))
    callouts.append(
        "\n".join(
            (
                f'  <circle class="doty" r="3.5" cx="{x10:.1f}" cy="{y10:.1f}"/>',
                f'  <line class="axis" x1="{x10 + 4:.1f}" y1="{y10 + 4:.1f}" x2="{x10 + 16:.1f}" y2="{y10 + 16:.1f}"/>',
                f'  <text class="small" x="{x10 + 18:.1f}" y="{y10 + 22:.1f}" text-anchor="start">10 μs · 2.5 A²s</text>',
            )
        )
    )
    x1 = float(x_of(1e-3))
    y1 = float(y_of(current**2 * 1e-3))
    callouts.append(
        f'  <circle class="doty" r="3.5" cx="{x1:.1f}" cy="{y1:.1f}"/>\n'
        f'  <text class="small" x="{x1 - 8:.1f}" y="{y1 - 10:.1f}" text-anchor="end">1 ms · 250 A²s</text>'
    )
    return scene(
        "同样 500 A，时窗乘 100，I²t 也乘 100（示意）",
        [
            "① 矩形时窗<tspan class=\"small\">　电流一直按 500 A 算，I²t = 500² × t。</tspan>",
            "② 10 μs<tspan class=\"small\">　硬件窗口约 2.5 A²s。2 μs 那档更小，仍是示意。</tspan>",
            "③ 1 ms<tspan class=\"small\">　约 250 A²s。和时间差同一个 100 倍。</tspan>",
            "④ 口诀<tspan class=\"small\">　短路交给硬件的微秒。软件的毫秒来不及。</tspan>",
        ],
        "I²t / A²s（对数，示意）",
        "接通时间（对数）",
        "\n".join(
            (
                xticks(x_of, YB, [(1e-6, "1μs"), (10e-6, "10μs"), (1e-3, "1ms"), (1e-2, "10ms")]),
                yticks(y_of, X0, [(0.5, "0.5"), (2.5, "2.5"), (250, "250")]),
            )
        ),
        poly(pts, "liner") + "\n" + "\n".join(callouts) + "\n" + dots,
        '  <text class="small" x="200" y="218">斜率 = 1：时间×10，I²t 也×10</text>',
        labels,
        kt,
        "500 A、2 μs、10 μs、1 ms 都是数量级示例，不是某颗 MOS 的安全工作区。",
        "短路示例：500 A 的矩形时窗里，I²t 与接通时间成正比。10 μs 约 2.5 A²s，1 ms 约 250 A²s。",
        "对数轴上这条线斜率是 1：时间乘 10，I²t 也乘 10。线上标出 10 μs 的 2.5 A²s 和 1 ms 的 250 A²s。示意，不是示波器。",
        "formula: I2t = 500^2 * t; log-log; marks at 2 us, 10 us, 100 us, 1 ms",
    )


def build_gate() -> str:
    """近环 10 μs 落完，远环 200 μs 才落完。累计 I²t 按线性下降积分。"""
    current = 500.0
    t = np.linspace(0.0, 40e-6, 81)
    near_tf, far_tf = 10e-6, 200e-6

    def i_of(tt, tf):
        return current * np.clip(1.0 - np.asarray(tt, dtype=float) / tf, 0.0, None)

    def acc(tt, tf):
        u = np.minimum(np.asarray(tt, dtype=float), tf)
        return current**2 * (u - u**2 / tf + u**3 / (3 * tf**2))

    def x_of(v):
        return X0 + np.asarray(v, dtype=float) / 40e-6 * (X1 - X0)

    def y_of(v):
        return YT + (current - np.asarray(v, dtype=float)) / current * (YB - YT)

    near = _xy(x_of, y_of, t, i_of(t, near_tf))
    far = _xy(x_of, y_of, t, i_of(t, far_tf))
    marks = (0.0, 5e-6, 10e-6, 40e-6)
    stations = [(float(x_of(m)), float(y_of(i_of(m, far_tf)))) for m in marks]
    kt, dots = moving(stations, cls="doty")
    labels = []
    for m in marks:
        labels.append(
            readout(
                f"t = {m * 1e6:.0f} μs",
                f"近环 {float(i_of(m, near_tf)):.0f} A",
                f"近环 I²t {float(acc(m, near_tf)):.2f} A²s",
                f"远环 {float(i_of(m, far_tf)):.0f} A",
                f"远环 I²t {float(acc(m, far_tf)):.2f} A²s",
            )
        )
    return scene(
        "环路绕远，500 A 落得更慢（示意）",
        [
            "① 近环<tspan class=\"small\">　示意 10 μs 线性落到 0。关断还在硬件窗口里。</tspan>",
            "② 远环<tspan class=\"small\">　示意 200 μs 才落完。10 μs 时电流几乎还在。</tspan>",
            "③ 累计<tspan class=\"small\">　I²t 按电流平方对时间积分。落得慢，积得多。</tspan>",
            "④ 口诀<tspan class=\"small\">　栅极电流从哪出去，就从源极旁边回来。</tspan>",
        ],
        "电流 A（示意线性下降）",
        "时间 μs",
        "\n".join(
            (
                xticks(x_of, YB, [(0, "0"), (10e-6, "10"), (40e-6, "40")]),
                yticks(y_of, X0, [(0, "0"), (250, "250"), (500, "500")]),
            )
        ),
        poly(near, "lineb") + "\n" + poly(far, "liner") + "\n" + dots,
        '  <text class="hi" x="200" y="218">蓝 近环</text>\n  <text class="warn" x="320" y="218">红 远环</text>',
        labels,
        kt,
        "10 μs 和 200 μs 是两条示意落点，不是从板图里抽出的电感。矩形时窗仍看 I²t 那张。",
        "栅极回流：近环示意 10 μs 把 500 A 降到 0，远环示意 200 μs。累计 I²t 来自线性下降的积分。",
        "金点沿远环电流走。底栏同时读出近环和远环在这一刻的电流和累计 I²t。示意，不是驱动器手册波形。",
        "formula: i=500*max(0,1-t/tf); tf=10us or 200us; I2t=I^2*(t-t^2/tf+t^3/(3 tf^2)) until tf",
    )


def build_hvil() -> str:
    """0 断开，15 ms 下令，30 ms 母线开始掉。500 ms 去抖会让人先碰到端子。"""
    t = np.logspace(0, 3, 90)  # ms

    def x_of(v):
        return X0 + (np.log10(np.asarray(v, dtype=float)) - 0.0) / 3.0 * (X1 - X0)

    def y_of(v):
        return YT + (1.0 - np.asarray(v, dtype=float)) * (YB - YT)

    def hold(tt, edge):
        return np.where(np.asarray(tt, dtype=float) < edge, 1.0, 0.0)

    cmd = hold(t, 15.0)
    bus = hold(t, 30.0)
    slow = hold(t, 500.0)
    marks = (5.0, 15.0, 30.0, 500.0)
    stations = [(float(x_of(m)), float(y_of(hold(m, 30.0)))) for m in marks]
    kt, dots = moving(stations)
    labels = [
        readout("t = 5 ms", "环已断", "接触器仍合", "母线仍满"),
        readout("t = 15 ms", "环已断", "接触器下令开", "母线仍满"),
        readout("t = 30 ms", "环已断", "接触器已开", "母线开始掉"),
        readout("t = 500 ms", "慢去抖才动", "人可能已碰到端子"),
    ]
    return scene(
        "环先断，闸再开，母线最后才开始掉（示意）",
        [
            "① ≤1 ms<tspan class=\"small\">　环在 0 ms 已断。对数轴画不出 0，原点标成 ≤1 ms。</tspan>",
            "② 约 15 ms<tspan class=\"small\">　BMS 下令打开接触器。母线这一拍还在。</tspan>",
            "③ 约 30 ms<tspan class=\"small\">　母线开始掉。示例，不是某只插头的图纸。</tspan>",
            "④ 500 ms<tspan class=\"small\">　去抖拉到按键那么长，人可以先碰到还带包压的端子。</tspan>",
        ],
        "1 = 未动作，0 = 已动作",
        "时间 ms（对数，原点 ≤1）",
        "\n".join(
            (
                xticks(x_of, YB, [(1, "≤1"), (15, "15"), (30, "30"), (500, "500")]),
                yticks(y_of, X0, [(0, "0 已动"), (1, "1 未动")]),
            )
        ),
        "\n".join((poly(_xy(x_of, y_of, t, cmd), "lineb"), poly(_xy(x_of, y_of, t, bus), "lineg"), poly(_xy(x_of, y_of, t, slow), "liner"), dots)),
        '  <text class="hi" x="200" y="218">蓝 开闸命令</text>\n  <text class="ok" x="360" y="218">绿 母线仍满</text>\n  <text class="warn" x="520" y="218">红 慢去抖</text>',
        labels,
        kt,
        "0、15 ms、30 ms、500 ms 都是示例。针脚长短差是第一道，去抖是第二道。",
        "HVIL 时序示意：环在 0 断开，约 15 ms 下令开闸，约 30 ms 母线开始掉。去抖若到 500 ms，人可以先碰到端子。",
        "三条阶梯在对数时间上先后落下。原点是 ≤1 ms，因为 0 画不上去；环断发生在 0 ms。金点沿「母线仍满」走。",
        "formula: steps at 15 ms, 30 ms, 500 ms; log time from 1 ms labeled ≤1; illustrative, not a connector drawing",
    )


def build_copper() -> str:
    """深放风险从约 2.0 V 起离开 0，到约 1.5 V 记满。2.5–3.0 V 是预充带，不是溶解点。"""
    t = np.linspace(0.0, 10.0, 61)
    volt = 3.4 - 0.24 * t

    def x_of(v):
        return X0 + np.asarray(v, dtype=float) / 10.0 * (X1 - X0)

    def y_of(v):
        return YT + (3.6 - np.asarray(v, dtype=float)) / (3.6 - 0.8) * (YB - YT)

    def zone(v: float) -> str:
        if v < 1.99:
            return "深放危险带"
        if v < 2.01:
            return "深放带上沿"
        if v < 2.99:
            return "预充带"
        if v < 3.01:
            return "预充门槛"
        return "保护余量内"

    pts = _xy(x_of, y_of, t, volt)
    # 3.0 / 2.5 / 2.0 / 1.2 V
    marks = tuple((3.4 - v) / 0.24 for v in (3.0, 2.5, 2.0, 1.2))
    stations = [(float(x_of(m)), float(y_of(3.4 - 0.24 * m))) for m in marks]
    kt, dots = moving(stations, cls="dotb")
    labels = []
    for m in marks:
        v = 3.4 - 0.24 * m
        risk = float(np.clip((2.0 - v) / 0.5, 0.0, 1.0))
        labels.append(readout(f"进程 {m:.1f}", f"电压 {v:.2f} V", f"深放风险 {risk:.2f}", zone(v)))
    # 预充带约 2.0–3.0 V；深放危险带约 2.0 V 以下。2.8 V 仍是保护截止余量。
    shades = "\n".join(
        (
            band(X0, float(y_of(3.0)), X1 - X0, float(y_of(2.0) - y_of(3.0)), "boxy"),
            band(X0, float(y_of(2.0)), X1 - X0, float(YB - y_of(2.0)), "boxr"),
        )
    )
    lines = []
    for v, name, cls, x, anchor in (
        (3.0, "3.0 预充", "lineg", X1 - 4, "end"),
        (2.8, "2.8 截止", "liney", X0 + 8, "start"),
        (2.0, "2.0 深放", "liner", X1 - 4, "end"),
    ):
        y = float(y_of(v))
        lines.append(f'  <line class="{cls}" x1="{X0:.0f}" y1="{y:.1f}" x2="{X1:.0f}" y2="{y:.1f}" stroke-dasharray="6 4"/>')
        lines.append(
            f'  <text class="small" x="{x:.0f}" y="{y - 4:.1f}" text-anchor="{anchor}">{name} V</text>'
        )
    return scene(
        "深放才溶铜。大约 2.5 V 只是预充带（示意）",
        [
            "① 保护留余量<tspan class=\"small\">　示例动作约 2.8–3.0 V。这是截止，不是铜溶解点。</tspan>",
            "② 低于约 3.0 V<tspan class=\"small\">　若手册允许，只按很小电流预充。常见带约 2.5–3.0 V。</tspan>",
            "③ 低于约 1.5–2 V<tspan class=\"small\">　或在那里放很久：铜可能溶解。很多厂家要求报废。</tspan>",
            "④ 口诀<tspan class=\"small\">　深放优先报废。拿不准就报废。跟着这颗电芯的手册。</tspan>",
        ],
        "单体电压 V（示意进程，不是实测放电）",
        "示意进程",
        "\n".join(
            (
                xticks(x_of, YB, [(0, "0"), (5, "5"), (10, "10")]),
                yticks(y_of, X0, [(1.2, "1.2"), (2.0, "2.0"), (3.0, "3.0"), (3.4, "3.4")]),
            )
        ),
        shades + "\n" + poly(pts, "lineb") + "\n" + "\n".join(lines) + "\n" + dots,
        '  <text class="gold" x="200" y="218">浅黄 预充带</text>\n  <text class="warn" x="340" y="218">浅红 深放危险带</text>',
        labels,
        kt,
        "大约 2.5–3.0 V 是常见小电流预充带，不是铜溶解点。鼓包、漏液，或拿不准，直接报废。",
        "过放示意：保护余量约 2.8–3.0 V。低于约 3.0 V 只谈小电流预充。铜溶解一般要到大约 1.5 V 或更低。",
        "浅黄是预充带，到约 3.0 V。浅红是深放危险带，约 2.0 V 以下。风险指数在 2.0 V 以下才离开 0，到约 1.5 V 记满。不是实测放电。",
        "formula: V=3.4-0.24*progress; risk=clip((2.0-V)/0.5,0,1); precharge band to 3.0 V; deep band below 2.0 V",
    )


def build_afe() -> str:
    """示意校验是字节和的低 8 位，不是某一颗 AFE 的 CRC 多项式。"""
    d0, d1, flipped = 0x12, 0x34, 0x35
    good = (d0 + d1) & 0xFF
    bad = (d0 + flipped) & 0xFF
    idx = np.array([0, 1, 2])
    good_sum = np.array([d0, good, good], dtype=float)
    bad_sum = np.array([d0, bad, bad], dtype=float)

    def x_of(v):
        return X0 + np.asarray(v, dtype=float) / 2.0 * (X1 - X0)

    def y_of(v):
        return YT + (0x60 - np.asarray(v, dtype=float)) / 0x60 * (YB - YT)

    marks = (0, 1, 2)
    stations = [(float(x_of(m)), float(y_of(good_sum[m]))) for m in marks]
    kt, dots = moving(stations)
    labels = [
        readout("第 1 字节", f"好帧和 {int(good_sum[0]):#04x}", f"坏帧和 {int(bad_sum[0]):#04x}"),
        readout("第 2 字节", f"好帧和 {int(good_sum[1]):#04x}", f"坏帧和 {int(bad_sum[1]):#04x}"),
        readout("比对", f"好帧 {good:#04x} 对得上", f"坏帧 {bad:#04x} 丢掉重读"),
    ]
    y_chk = float(y_of(good))
    check_line = (
        f'  <line class="liney" x1="{X0:.0f}" y1="{y_chk:.1f}" x2="{X1:.0f}" y2="{y_chk:.1f}" stroke-dasharray="6 4"/>'
    )
    return scene(
        "校验对不上，这一帧丢掉重读（示意）",
        [
            "① 两字节到齐<tspan class=\"small\">　示意校验 = (字节和) 的低 8 位。</tspan>",
            f"② 好帧<tspan class=\"small\">　0x12+0x34 = {good:#04x}，和校验字节一样。</tspan>",
            f"③ 翻了一位<tspan class=\"small\">　第二字节变成 0x35，和变成 {bad:#04x}。</tspan>",
            "④ 口诀<tspan class=\"small\">　对不上就重读。不要拿坏帧去做保护决定。</tspan>",
        ],
        "累加和（示意，不是 AFE 多项式）",
        "第几个数据字节",
        "\n".join(
            (
                xticks(x_of, YB, [(0, "第1"), (1, "第2"), (2, "比对")]),
                yticks(y_of, X0, [(0x12, "0x12"), (0x46, "0x46")]),
            )
        ),
        "\n".join((poly(_xy(x_of, y_of, idx, good_sum), "lineb"), poly(_xy(x_of, y_of, idx, bad_sum), "liner"), check_line, dots)),
        '  <text class="hi" x="220" y="218">蓝 好帧</text>\n  <text class="warn" x="340" y="218">红 翻了一位</text>\n  <text class="gold" x="500" y="218">金虚线 校验字节</text>',
        labels,
        kt,
        "这个低 8 位和只说明「对不上就丢」。不是 BQ769x2 或任何一颗 AFE 手册里的 CRC。",
        "AFE 读数示意：两字节的低 8 位和与校验字节不一致时，这一帧丢掉重读，不拿去保护。",
        "蓝线是 0x12、0x34 的累加，红线把第二字节改成 0x35。金点沿好帧走。校验多项式不冒充芯片手册。",
        "formula: check=(0x12+0x34)&0xFF=0x46; flipped=(0x12+0x35)&0xFF=0x47; not a vendor CRC",
    )


def _gbt_end_ticks(x_of) -> str:
    """「超时」在 3.8 s 刻度左侧，「结束」在 4 s 刻度右侧，避免两个词挤在一起。"""
    x_to = float(x_of(3.8))
    x_end = float(x_of(4.0))
    y = YB + 22
    return "\n".join(
        (
            f'  <line class="grid" x1="{x_to:.1f}" y1="{YB:.1f}" x2="{x_to:.1f}" y2="{YB + 6:.1f}"/>',
            f'  <text class="small" x="{x_to - 8:.1f}" y="{y:.0f}" text-anchor="end">超时</text>',
            f'  <line class="grid" x1="{x_end:.1f}" y1="{YB:.1f}" x2="{x_end:.1f}" y2="{YB + 6:.1f}"/>',
            f'  <text class="small" x="{x_end + 10:.1f}" y="{y:.0f}" text-anchor="start">结束</text>',
        )
    )


def build_gbt() -> str:
    """四段骨架。秒和安培都是示意，不摘国标周期，也不写帧 ID。"""
    t = np.linspace(0.0, 4.5, 91)

    def i_bms(tt):
        tt = np.asarray(tt, dtype=float)
        out = np.zeros_like(tt)
        out[(tt >= 2.0) & (tt < 3.0)] = 40.0
        out[(tt >= 3.0) & (tt < 4.0)] = 10.0
        return out

    def i_ok(tt):
        tt = np.asarray(tt, dtype=float)
        followed = i_bms(tt - 0.25)
        # 超时放在 3.8 s，晚于 0.25 s 滞后，绿线才能先跟上 10 A 再停。
        return np.where(tt >= 3.8, 0.0, followed)

    def i_bad(tt):
        tt = np.asarray(tt, dtype=float)
        followed = i_bms(tt - 0.25)
        return np.where(tt >= 3.8, i_bms(3.8 - 0.25), followed)

    def x_of(v):
        return X0 + np.asarray(v, dtype=float) / 4.5 * (X1 - X0)

    def y_of(v):
        return YT + (50.0 - np.asarray(v, dtype=float)) / 50.0 * (YB - YT)

    marks = (2.4, 3.1, 3.5, 4.2)
    stations = [(float(x_of(m)), float(y_of(i_bms(m)))) for m in marks]
    kt, dots = moving(stations)
    labels = [
        readout(
            f"t = {m:.1f} s",
            f"BMS 需求 {float(i_bms(m)):.0f} A",
            f"正确桩 {float(i_ok(m)):.0f} A",
            f"错误桩 {float(i_bad(m)):.0f} A",
        )
        for m in marks
    ]
    return scene(
        "车先说要多少，超时就停（示意，不是国标摘录）",
        [
            "① 辨识和参数<tspan class=\"small\">　前两秒需求还是 0。先对暗号，再谈能力。</tspan>",
            "② 充电循环<tspan class=\"small\">　需求从 BMS 发出。这里示意 40 A，稍后改成 10 A。</tspan>",
            "③ 充电机跟随<tspan class=\"small\">　晚 0.25 s。需求降到 10 A 之后，绿线再跟着降。</tspan>",
            "④ 超时<tspan class=\"small\">　示意 3.8 s 起必须停。红线是错的：还停在 10 A。</tspan>",
        ],
        "电流 A（示意）",
        "示意阶段秒，不是报文周期",
        "\n".join(
            (
                xticks(x_of, YB, [(1, "辨识"), (2, "充电")]),
                _gbt_end_ticks(x_of),
                yticks(y_of, X0, [(0, "0"), (10, "10"), (40, "40")]),
            )
        ),
        "\n".join(
            (
                poly(_xy(x_of, y_of, t, i_bms(t)), "lineb"),
                poly(_xy(x_of, y_of, t, i_bad(t)), "liner"),
                # 跟随阶段红绿重合。绿线虚线、并上移 2 px，盖在红线上面。
                poly([(x, y - 2.0) for x, y in _xy(x_of, y_of, t, i_ok(t))], "lineg"),
                dots,
            )
        ),
        '  <text class="hi" x="180" y="218">蓝 BMS 需求</text>\n  <text class="ok" x="340" y="218">绿 超时就停</text>\n  <text class="warn" x="500" y="218">红 超时仍灌</text>',
        labels,
        kt,
        "不写帧 ID。通信正常也不等于可以合接触器，预充仍要单独走。",
        "GB/T 27930 的四段骨架示意：BMS 发需求，充电机跟随；超时必须停充。秒和安培都不是国标摘录。",
        "蓝线是需求。绿线晚 0.25 s 跟上，先从 40 A 降到 10 A，示意 3.8 s 再落到 0。红线超时后仍停在 10 A。细则以现行国标为准。",
        "formula: illustrative stages; Ibms 40 A then 10 A; charger lags 0.25 s; timeout at 3.8 s forces green to 0",
    )


def build_smbus() -> str:
    """Voltage()=0x09，低字节在前。3700 mV 是把两个字节换算出来的示意，不是一块电池的读数。"""
    lo, hi = 0x74, 0x0E
    mv = lo + hi * 256
    slot = np.array([0, 1, 2, 3, 4, 5, 6, 7], dtype=float)
    decoded = np.array([0, 0, 0, 0, 0, 0, mv, mv], dtype=float)

    def x_of(v):
        return X0 + np.asarray(v, dtype=float) / 7.0 * (X1 - X0)

    def y_of(v):
        return YT + (4000.0 - np.asarray(v, dtype=float)) / 4000.0 * (YB - YT)

    marks = (1, 2, 5, 6)
    stations = [(float(x_of(m)), float(y_of(decoded[m]))) for m in marks]
    kt, dots = moving(stations, cls="dotb")
    labels = [
        readout("槽 1", "地址 0x0B", "电压 0 mV"),
        readout("槽 2", "命令 0x09", "电压 0 mV"),
        readout("槽 5", "低字节 0x74", "电压 0 mV"),
        readout("槽 6", "高字节 0x0E", f"电压 {mv} mV", "不是 SOC"),
    ]
    return scene(
        "先写命令字，再读回两个字节（示意）",
        [
            "① 地址<tspan class=\"small\">　7 位常见 0x0B。先扫，不要上来就假定。</tspan>",
            "② 命令<tspan class=\"small\">　Voltage() 是 0x09。电量百分比是另一条命令。</tspan>",
            "③ 低字节在前<tspan class=\"small\">　示意 0x74 然后 0x0E。</tspan>",
            f"④ 换算<tspan class=\"small\">　{lo}+{hi}*256 = {mv} mV。不要把它当成 SOC。</tspan>",
        ],
        "解出来的毫伏（两个字节到齐才有）",
        "往返的槽",
        "\n".join(
            (
                xticks(x_of, YB, [(1, "地址"), (2, "命令"), (5, "低"), (6, "高")]),
                yticks(y_of, X0, [(0, "0"), (3700, "3700")]),
            )
        ),
        poly(_xy(x_of, y_of, slot, decoded), "lineb") + "\n" + dots,
        '  <text class="small" x="220" y="218">高字节到了，读数才从 0 跳到 3700</text>',
        labels,
        kt,
        "3700 mV 是 0x74、0x0E 按小端换出来的教学数，不是某一块笔记本电池的测量。",
        "SMBus 读电压示意：先写 Voltage()=0x09，再按低字节在前读回。0x74 与 0x0E 合成 3700 mV，不是 SOC。",
        "折线在两个数据字节到齐之前停在 0。金点走到高字节时，底栏给出毫伏。地址 0x0B 要先扫描再假定。",
        "formula: mV = 0x74 + 0x0E*256 = 3700; command 0x09; address 0x0B is common, scan first",
    )


def build_discharge_beside() -> str:
    """400 V、1 mF、200 Ω、60 V、800 W 都来自详解④的同一笔示例。"""
    tau = 0.001 * 200.0
    t = np.linspace(0.0, 1.0, 81)
    volt = 400.0 * np.exp(-t / tau)
    stuck = np.full_like(t, 400.0)

    def x_of(v):
        return X0 + np.asarray(v, dtype=float) / 1.0 * (X1 - X0)

    def y_of(v):
        return YT + (420.0 - np.asarray(v, dtype=float)) / 420.0 * (YB - YT)

    t60 = float(-tau * np.log(60.0 / 400.0))
    marks = (0.0, t60, 0.6, 1.0)
    stations = [(float(x_of(m)), float(y_of(400.0 * np.exp(-m / tau)))) for m in marks]
    kt, dots = moving(stations)
    labels = []
    for m in marks:
        v = 400.0 * np.exp(-m / tau)
        energy = 0.5 * 0.001 * v**2
        labels.append(
            readout(
                f"t = {m:.2f} s",
                f"已开母线 {v:.0f} V",
                f"电容剩余 {energy:.1f} J",
                "仍合 400 V / 800 W",
            )
        )
    y60 = float(y_of(60.0))
    line60 = f'  <line class="liney" x1="{X0:.0f}" y1="{y60:.1f}" x2="{X1:.0f}" y2="{y60:.1f}" stroke-dasharray="6 4"/>'
    return scene(
        "先确认触点已开，200 Ω 才拉得动母线（示意）",
        [
            "① 触点已经分开<tspan class=\"small\">　τ=RC=0.2 s。电压按 400·e^(−t/0.2) 往下掉。</tspan>",
            f"② 到 60 V<tspan class=\"small\">　大约 {t60:.2f} s。电容里还剩约 1.8 J。</tspan>",
            "③ 闸还合着<tspan class=\"small\">　母线停在 400 V，200 Ω 按 800 W 一直吃。</tspan>",
            "④ 口诀<tspan class=\"small\">　电阻在电容那一侧，而且要等接触器先断开。</tspan>",
        ],
        "母线电压 V（示意）",
        "时间 s",
        "\n".join(
            (
                xticks(x_of, YB, [(0, "0"), (round(t60, 2), f"{t60:.2f}"), (1, "1")]),
                yticks(y_of, X0, [(60, "60"), (400, "400")]),
            )
        ),
        "\n".join((poly(_xy(x_of, y_of, t, volt), "lineb"), poly(_xy(x_of, y_of, t, stuck), "liner"), line60, dots)),
        '  <text class="hi" x="200" y="218">蓝 触点已开</text>\n  <text class="warn" x="360" y="218">红 闸还合着</text>\n  <text class="gold" x="530" y="218">金虚线 60 V</text>',
        labels,
        kt,
        "400 V、1 mF、200 Ω、60 V、80 J 是详解④的同一笔示例。放电没完成之前不要碰母线。",
        "主动放电示意：接触器断开后 200 Ω 把 400 V、1 mF 的母线拉向 60 V。闸还合着时电阻按 800 W 持续吃功率。",
        "蓝线是 e 指数，红线停在包压。金点沿蓝线走，底栏读出功率和电容里还剩的焦耳。示意，不是示波器。",
        "formula: tau=0.2 s; V=400*exp(-t/tau); t60=-tau*ln(60/400); P=V^2/200; E=0.5*C*V^2",
    )


def build_solid() -> str:
    """界面更慢只是为了把差别画出来。不给固态电芯编一套保护阈值。"""
    t = np.linspace(0.0, 20.0, 81)
    i_amp = 1.0
    v_liquid = 3.70 - i_amp * 0.020 * (1.0 - np.exp(-t / 1.0))
    v_solid = 3.70 - i_amp * 0.080 * (1.0 - np.exp(-t / 8.0))

    def x_of(v):
        return X0 + np.asarray(v, dtype=float) / 20.0 * (X1 - X0)

    def y_of(v):
        return YT + (3.74 - np.asarray(v, dtype=float)) / (3.74 - 3.58) * (YB - YT)

    marks = (0.0, 1.0, 8.0, 20.0)
    stations = [(float(x_of(m)), float(y_of(3.70 - i_amp * 0.080 * (1.0 - np.exp(-m / 8.0))))) for m in marks]
    kt, dots = moving(stations)
    labels = []
    for m in marks:
        vl = 3.70 - i_amp * 0.020 * (1.0 - np.exp(-m / 1.0))
        vs = 3.70 - i_amp * 0.080 * (1.0 - np.exp(-m / 8.0))
        labels.append(readout(f"t = {m:.0f} s", f"液态界面 {vl:.3f} V", f"固体界面 {vs:.3f} V"))
    return scene(
        "换的是离子通道，保护不能跟着拆（示意）",
        [
            "① 电子仍走外电路<tspan class=\"small\">　1 A 示意。液体或固体都不取消这根回路。</tspan>",
            "② 液体界面<tspan class=\"small\">　20 mΩ、τ=1 s。压降很快坐实。</tspan>",
            "③ 固体界面<tspan class=\"small\">　80 mΩ、τ=8 s。更慢，只为把差别画出来。</tspan>",
            "④ 口诀<tspan class=\"small\">　听到「固态所以不用 BMS」，摇头。外壳碳纤维也不是结构电池。</tspan>",
        ],
        "端电压 V（示意）",
        "时间 s",
        "\n".join(
            (
                xticks(x_of, YB, [(0, "0"), (1, "1"), (8, "8"), (20, "20")]),
                yticks(y_of, X0, [(3.62, "3.62"), (3.68, "3.68"), (3.70, "3.70")]),
            )
        ),
        poly(_xy(x_of, y_of, t, v_liquid), "lineb") + "\n" + poly(_xy(x_of, y_of, t, v_solid), "liner") + "\n" + dots,
        '  <text class="hi" x="200" y="218">蓝 液体界面</text>\n  <text class="warn" x="380" y="218">红 固体界面</text>',
        labels,
        kt,
        "毫欧和秒不是氧化物、硫化物或聚合物的手册。短路时放热可以更大，这张图不画温度，也不改阈值。",
        "固态与液态的示意对照：离子通道变了，外电路里的电子还在。界面电阻和秒数是教学数，不能拿去改保护阈值。",
        "红线落得更低、更慢。金点沿红线走。碳纤维外壳里仍是普通电芯，按那些电芯的手册读，不要编一份包级阈值。",
        "formula: V=3.70-I*R*(1-exp(-t/tau)); liquid 0.020 ohm 1 s; solid interface 0.080 ohm 8 s; I=1 A",
    )


def build_isolation() -> str:
    """空槽是高通，铜桥在直流也是增益 1。400 V 是仓库里的示例包压。"""
    freq = np.logspace(1, 6, 61)
    f0 = 1.0e4
    ratio = freq / f0
    gain = ratio / np.sqrt(1.0 + ratio**2)
    v_slot = 400.0 * gain
    v_cu = np.full_like(freq, 400.0)

    def x_of(v):
        return X0 + (np.log10(np.asarray(v, dtype=float)) - 1.0) / 5.0 * (X1 - X0)

    def y_of(v):
        return YT + (420.0 - np.asarray(v, dtype=float)) / 420.0 * (YB - YT)

    marks = (10.0, 1.0e4, 1.0e5, 1.0e6)
    stations = [(float(x_of(m)), float(y_of(400.0 * (m / f0) / np.sqrt(1.0 + (m / f0) ** 2)))) for m in marks]
    kt, dots = moving(stations)
    labels = []
    for m in marks:
        g = (m / f0) / np.sqrt(1.0 + (m / f0) ** 2)
        slot_v = 400 * g
        shown = f"{slot_v:.2f}" if m < 100 else f"{slot_v:.1f}"
        if m >= 1e6:
            freq_label = "1 MHz"
        elif m >= 1e3:
            freq_label = f"{m / 1e3:.0f} kHz"
        else:
            freq_label = f"{m:.0f} Hz"
        labels.append(readout(f"f = {freq_label}", f"空槽 {shown} V", "铜桥 400 V"))
    return scene(
        "铜桥让直流过去，空槽让直流留在墙这边（示意）",
        [
            "① 空槽<tspan class=\"small\">　示意高通，拐角 10 kHz。直流增益走向 0。</tspan>",
            "② 铜桥<tspan class=\"small\">　从直流到高频增益都是 1。通信地被拉到包电位。</tspan>",
            "③ 10 Hz<tspan class=\"small\">　空槽这边几乎没有 400 V，铜桥这边就是 400 V。</tspan>",
            "④ 口诀<tspan class=\"small\">　隔离槽是开口。铜皮不能当桥。报文还在也不代表隔离还在。</tspan>",
        ],
        "通信侧看到的电压 V（示意包压 400）",
        "频率 Hz（对数）",
        "\n".join(
            (
                xticks(x_of, YB, [(10, "10"), (1e4, "10k"), (1e6, "1M")]),
                yticks(y_of, X0, [(0, "0"), (400, "400")]),
            )
        ),
        poly(_xy(x_of, y_of, freq, v_slot), "lineb") + "\n" + poly(_xy(x_of, y_of, freq, v_cu), "liner") + "\n" + dots,
        '  <text class="hi" x="200" y="218">蓝 空槽</text>\n  <text class="warn" x="320" y="218">红 铜桥</text>',
        labels,
        kt,
        "10 kHz 是为了把高通画出来，不是变压器手册。爬电距离查所选标准，这篇不写毫米数。",
        "隔离槽示意：空槽按高通挡住直流，一条铜桥让 400 V 的包电位出现在通信侧。报文还能发，不代表人手是安全的。",
        "蓝线随频率升起，红线贴着 400 V。金点沿蓝线走。人手摸到被铜桥接上的通信口，摸到的是电池电位。",
        "formula: H=f/f0/sqrt(1+(f/f0)^2); f0=10 kHz illustrative; copper gain=1; V=400*H",
    )


def build_cloud_dash() -> str:
    """正常存储最大 30 s，3 级报警最大 1 s。采集不低于 1 次/s。监控，不是切断。"""
    t = np.linspace(0.0, 60.0, 121)
    age = np.mod(t, 30.0)

    def x_of(v):
        return X0 + np.asarray(v, dtype=float) / 60.0 * (X1 - X0)

    def y_of(v):
        return YT + (32.0 - np.asarray(v, dtype=float)) / 32.0 * (YB - YT)

    marks = (15.0, 29.0, 30.0, 59.0)
    stations = [(float(x_of(m)), float(y_of(m % 30.0))) for m in marks]
    kt, dots = moving(stations)
    labels = [
        readout(f"t = {m:.0f} s", f"正常存储年龄 {m % 30:.0f} s", "报警存储上限 1 s") for m in marks
    ]
    y1 = float(y_of(1.0))
    ceiling = f'  <line class="lineg" x1="{X0:.0f}" y1="{y1:.1f}" x2="{X1:.0f}" y2="{y1:.1f}"/>'
    return scene(
        "屏幕上的数，可以比包里的样本老 30 秒（示意）",
        [
            "① 采集<tspan class=\"small\">　正文转述：不低于 1 次/s。包里可以很新。</tspan>",
            "② 正常存储<tspan class=\"small\">　间隔最大 30 s。年龄锯齿爬到 30 再回 0。</tspan>",
            "③ 3 级报警<tspan class=\"small\">　存储间隔最大 1 s。绿线是这道上限。</tspan>",
            "④ 口诀<tspan class=\"small\">　这是监控。过充过放和短路的切断不看这朵云。</tspan>",
        ],
        "屏幕上这条记录的年龄 s",
        "时间 s",
        "\n".join(
            (
                xticks(x_of, YB, [(0, "0"), (30, "30"), (60, "60")]),
                yticks(y_of, X0, [(1, "1"), (30, "30")]),
            )
        ),
        poly(_xy(x_of, y_of, t, age), "lineb") + "\n" + ceiling + "\n" + dots,
        '  <text class="hi" x="200" y="218">蓝 正常存储</text>\n  <text class="ok" x="380" y="218">绿 报警存储上限 1 s</text>',
        labels,
        kt,
        "间隔来自正文对 GB/T 32960.2—2016 的转述。上传周期另见 32960.3，这里不画。不是 FTTI。",
        "云仪表上的数：正常存储年龄按 30 s 打锯齿，3 级报警的存储年龄不超过 1 s。切断不靠这条记录。",
        "蓝线是 t 对 30 取余。绿线钉在 1 s。金点沿锯齿走。包上的比较器不等这 30 s。",
        "formula: age_normal = t mod 30; alarm storage age ceiling = 1 s; cited from the stage-6 paraphrase of GB/T 32960.2-2016",
    )


def build_cert() -> str:
    """示意 FTTI 100 ms、反应 10 ms，和 ftti 那张是同一笔教学预算。不是认证结论。"""
    t = np.linspace(0.0, 100.0, 81)
    hardware = np.where(t >= 10.0, 1.0, 0.0)
    dead = np.zeros_like(t)

    def x_of(v):
        return X0 + np.asarray(v, dtype=float) / 100.0 * (X1 - X0)

    def y_of(v):
        return YT + (1.15 - np.asarray(v, dtype=float)) / 1.15 * (YB - YT)

    marks = (0.0, 10.0, 50.0, 100.0)
    stations = [(float(x_of(m)), float(y_of(1.0 if m >= 10.0 else 0.0))) for m in marks]
    kt, dots = moving(stations, cls="dotg")
    labels = []
    for m in marks:
        hw = "已切断" if m >= 10.0 else "未切断"
        labels.append(readout(f"t = {m:.0f} ms", f"硬件 {hw}", "软件 未切断", "FTTI 100 ms"))
    return scene(
        "注入之后，硬件通道自己切断（示意预算）",
        [
            "① 注入<tspan class=\"small\">　拔采样线或抬高模拟电压。不要对真电池做。</tspan>",
            "② 10 ms<tspan class=\"small\">　和 FTTI 那张一样，反应示意 10 ms。硬件落到已切断。</tspan>",
            "③ 软件停了<tspan class=\"small\">　红线一直是 0。比较器不经过这颗 MCU。</tspan>",
            "④ 口诀<tspan class=\"small\">　注入一次，独立切断一次，把时间写下来。这不是认证结论。</tspan>",
        ],
        "1 = 已切断，0 = 未切断",
        "时间 ms",
        "\n".join(
            (
                xticks(x_of, YB, [(0, "0"), (10, "10"), (100, "100")]),
                yticks(y_of, X0, [(0, "0"), (1, "1")]),
            )
        ),
        poly(_xy(x_of, y_of, t, hardware), "lineg") + "\n" + poly(_xy(x_of, y_of, t, dead), "liner") + "\n" + dots,
        '  <text class="ok" x="200" y="218">绿 硬件</text>\n  <text class="warn" x="320" y="218">红 MCU 已停</text>',
        labels,
        kt,
        "100 ms 和 10 ms 是教学预算，不是某个 ASIL 项目的 FTTI。现场实拍仍然没有。",
        "功能安全示意：硬件通道在教学反应时间 10 ms 切断，停掉的软件一直不断。100 ms 是同一笔示意 FTTI，不是认证结论。",
        "绿线在 10 ms 跳到已切断，红线停在 0。金点沿绿线走。记录里要能看出切断时间，不能只改软件阈值。",
        "formula: hardware steps to 1 at 10 ms; dead MCU stays 0; FTTI teaching budget 100 ms",
    )


def build_pack_manual() -> str:
    """阈值格留空。4.25 V 是阶段 1 的三元示例，不能填进未公开的包级手册。"""
    s = np.linspace(0.0, 1.0, 41)
    volt = 3.0 + 1.2 * s

    def x_of(v):
        return X0 + np.asarray(v, dtype=float) * (X1 - X0)

    def y_of(v):
        return YT + (4.4 - np.asarray(v, dtype=float)) / (4.4 - 2.8) * (YB - YT)

    marks = (0.0, 0.4, 0.7, 1.0)
    stations = [(float(x_of(m)), float(y_of(3.0 + 1.2 * m))) for m in marks]
    kt, dots = moving(stations)
    labels = []
    for m in marks:
        v = 3.0 + 1.2 * m
        labels.append(readout(f"示意电压 {v:.2f} V", "这本手册的阈值格 空"))
    y_borrow = float(y_of(4.25))
    borrowed = (
        f'  <line class="liner" x1="{X0:.0f}" y1="{y_borrow:.1f}" x2="{X1:.0f}" y2="{y_borrow:.1f}" stroke-dasharray="6 4"/>'
    )
    return scene(
        "格子空着，这页就不算这本包的手册（示意）",
        [
            "① 电压可以示意地爬<tspan class=\"small\">　从 3.0 V 到 4.2 V，只说明采样在动。</tspan>",
            "② 阈值不画实线<tspan class=\"small\">　钠离子、固态、结构电池的格子仍空着。</tspan>",
            "③ 别借用 4.25 V<tspan class=\"small\">　那是阶段 1 的三元示例，红虚线提醒你别填进去。</tspan>",
            "④ 口诀<tspan class=\"small\">　手册没写的数，就让格子空着。</tspan>",
        ],
        "示意电压 V",
        "示意进程",
        "\n".join(
            (
                xticks(x_of, YB, [(0, "0"), (1, "1")]),
                yticks(y_of, X0, [(3.0, "3.0"), (4.2, "4.2")]),
            )
        ),
        poly(_xy(x_of, y_of, s, volt), "lineb") + "\n" + borrowed + "\n" + dots,
        '  <text class="warn" x="200" y="218">红虚线 4.25 V 三元示例，不能填进空格</text>',
        labels,
        kt,
        "不编寄存器地址，也不编保护阈值。包级手册该缺的还缺。",
        "包级采样示意：电压可以沿一条教学直线走，但这本未公开手册的阈值格保持为空。4.25 V 只是别的体系的示例。",
        "蓝线从 3.0 V 走到 4.2 V。红虚线钉在 4.25 V，用来记住不要借用。底栏每一拍都写着阈值格是空的。",
        "formula: V=3.0+1.2*s illustrative; 4.25 V is the stage-1 ternary example and is not filled in as a threshold",
    )


def build_mqtt() -> str:
    """保活 15 s 只为把遗嘱的时刻画出来，不是某一家 broker 的默认值。"""
    t = np.linspace(0.0, 30.0, 61)
    age = t
    will = np.where(t >= 15.0, 1.0, 0.0)

    def x_of(v):
        return X0 + np.asarray(v, dtype=float) / 30.0 * (X1 - X0)

    def y_of(v):
        return YT + (32.0 - np.asarray(v, dtype=float)) / 32.0 * (YB - YT)

    marks = (0.0, 14.0, 15.0, 30.0)
    stations = [(float(x_of(m)), float(y_of(m))) for m in marks]
    kt, dots = moving(stations)
    labels = []
    for m in marks:
        flag = "已代发" if m >= 15.0 else "未代发"
        labels.append(readout(f"静默 {m:.0f} s", f"年龄 {m:.0f} s", f"遗嘱 {flag}", "保活 15 s"))
    return scene(
        "心跳断了，broker 代发遗嘱（示意保活）",
        [
            "① 网关还在<tspan class=\"small\">　年龄从 0 往上走。订阅者听到的是普通遥测。</tspan>",
            "② 示意保活 15 s<tspan class=\"small\">　不是某一家 broker 的出厂默认。</tspan>",
            "③ 越过 15 s<tspan class=\"small\">　broker 代发离线遗嘱。订阅者不要再把旧遥测当活的。</tspan>",
            "④ 口诀<tspan class=\"small\">　人掉线了，最后一句话由中间人来说。</tspan>",
        ],
        "距上一包的秒数",
        "静默时间 s",
        "\n".join(
            (
                xticks(x_of, YB, [(0, "0"), (15, "15"), (30, "30")]),
                yticks(y_of, X0, [(0, "0"), (15, "15"), (30, "30")]),
            )
        ),
        poly(_xy(x_of, y_of, t, age), "lineb")
        + "\n"
        + poly(_xy(x_of, y_of, t, will * 15.0), "liner")
        + "\n"
        + dots,
        '  <text class="hi" x="200" y="218">蓝 静默年龄</text>\n  <text class="warn" x="380" y="218">红 遗嘱（到点升到 15）</text>',
        labels,
        kt,
        "15 s 是这张图的教学保活，用来看「超时才代发」。保护切断不走这条 MQTT。",
        "MQTT 示意：网关静默超过教学保活 15 s 后，broker 代发遗嘱。15 s 不是厂商默认值。",
        "蓝线是静默秒数，红线在 15 s 升到保活线上，表示遗嘱已经代发。金点沿蓝线走。",
        "formula: age=t while silent; will steps at illustrative keepalive 15 s",
    )


def build_parallel() -> str:
    """并联只有一个端电压。电流按内阻反比分配。20 mΩ 起算和 SOH 图的新电池同一量级，仍是示意。"""
    k = np.linspace(1.0, 4.0, 41)
    total = 10.0
    i1 = total * k / (1.0 + k)
    i2 = total / (1.0 + k)

    def x_of(v):
        return X0 + (np.asarray(v, dtype=float) - 1.0) / 3.0 * (X1 - X0)

    def y_of(v):
        return YT + (10.0 - np.asarray(v, dtype=float)) / 10.0 * (YB - YT)

    marks = (1.0, 2.0, 3.0, 4.0)
    stations = [(float(x_of(m)), float(y_of(total * m / (1.0 + m)))) for m in marks]
    kt, dots = moving(stations)
    labels = []
    for m in marks:
        a = total * m / (1.0 + m)
        b = total - a
        labels.append(readout(f"R2/R1 = {m:.0f}", f"I1 = {a:.2f} A", f"I2 = {b:.2f} A", "端电压只有一个"))
    return scene(
        "并联只有一个电压，电流按内阻分（示意）",
        [
            "① 表笔只看得到一个电压<tspan class=\"small\">　两节并在一起，端电压是同一点。</tspan>",
            "② 总电流 10 A<tspan class=\"small\">　示意。I1 = 10·k/(1+k)，k 是 R2/R1。</tspan>",
            "③ k=2<tspan class=\"small\">　若 R1=20 mΩ、R2=40 mΩ，电流大约 6.67 A 和 3.33 A。</tspan>",
            "④ 口诀<tspan class=\"small\">　电压一样，不代表两节一样用力。</tspan>",
        ],
        "支路电流 A（示意总电流 10 A）",
        "R2 / R1",
        "\n".join(
            (
                xticks(x_of, YB, [(1, "1"), (2, "2"), (4, "4")]),
                yticks(y_of, X0, [(2, "2"), (5, "5"), (8, "8")]),
            )
        ),
        poly(_xy(x_of, y_of, k, i1), "lineb") + "\n" + poly(_xy(x_of, y_of, k, i2), "liner") + "\n" + dots,
        '  <text class="hi" x="200" y="218">蓝 支路 1</text>\n  <text class="warn" x="340" y="218">红 支路 2</text>',
        labels,
        kt,
        "20 mΩ 只是和 SOH 示意同一量级。不能从端电压看出哪一节在偷懒。",
        "并联示意：对外只有一个电压。总电流 10 A 时，两支路按内阻的反比分配，内阻大的那支电流更小。",
        "蓝线随阻值比升高，红线下降，两者之和保持 10 A。金点沿蓝线走。示意，不是两节电芯的实测内阻。",
        "formula: I1=10*k/(1+k); I2=10/(1+k); k=R2/R1; example k=2 is 20 mohm and 40 mohm",
    )


def build_isospi_cm() -> str:
    """共模大约按每节 3.7 V 抬。3.7 V 来自讲义里的大约值，不是评估板实测。"""
    n = np.linspace(0.0, 16.0, 33)
    vcm = n * 3.7
    vsig = np.full_like(n, 2.0)

    def x_of(v):
        return X0 + np.asarray(v, dtype=float) / 16.0 * (X1 - X0)

    def y_of(v):
        return YT + (70.0 - np.asarray(v, dtype=float)) / 70.0 * (YB - YT)

    marks = (0.0, 6.0, 12.0, 16.0)
    stations = [(float(x_of(m)), float(y_of(m * 3.7))) for m in marks]
    kt, dots = moving(stations)
    labels = [readout(f"n = {m:.0f}", f"共模 {m * 3.7:.1f} V", "差分 2 V") for m in marks]
    return scene(
        "数据包过去，几十伏的共模留在墙这边（示意）",
        [
            "① 每多一节<tspan class=\"small\">　共模大约再抬 3.7 V。这是讲义里的大约值。</tspan>",
            "② 十二到十六节<tspan class=\"small\">　相邻从板之间就是几十伏，不是一根普通排线。</tspan>",
            "③ 差分不过这条斜线<tspan class=\"small\">　示意 2 V。变压器让它过去，共模留下。</tspan>",
            "④ 口诀<tspan class=\"small\">　数据穿过变压器，高压电位差留在墙那边。</tspan>",
        ],
        "电压 V（示意）",
        "隔开的节数",
        "\n".join(
            (
                xticks(x_of, YB, [(0, "0"), (12, "12"), (16, "16")]),
                yticks(y_of, X0, [(2, "2"), (44.4, "44"), (59.2, "59")]),
            )
        ),
        poly(_xy(x_of, y_of, n, vcm), "liner") + "\n" + poly(_xy(x_of, y_of, n, vsig), "lineb") + "\n" + dots,
        '  <text class="warn" x="200" y="218">红 共模</text>\n  <text class="hi" x="320" y="218">蓝 差分示意</text>',
        labels,
        kt,
        "3.7 V 是锂离子大约的工作电压，不是 BQ769 评估板测到的共模，也不是 isoSPI 的时序。",
        "菊花链示意：共模按节数乘大约 3.7 V 升高，穿过变压器的差分不跟着这根斜线走。",
        "红线是 n×3.7 V，蓝线停在示意 2 V。金点沿红线走。评估板照片仍然没有，这张不代替实拍。",
        "formula: Vcm=n*3.7 V; Vdiff=2 V flat; 3.7 V is the lecture approximation, not an EVB measurement",
    )


def build_balance_topo() -> str:
    """被动 4.2 V、100 Ω。主动一拍 ½LI²=20 μJ。不写效率百分数。"""
    t = np.linspace(0.5, 10.0, 40)
    power = 4.2**2 / 100.0
    e_pass = power * t
    e_act = 20e-6 * t  # 每秒一拍的示意

    def x_of(v):
        return X0 + (np.asarray(v, dtype=float) - 0.5) / 9.5 * (X1 - X0)

    def y_of(v):
        lv = np.log10(np.asarray(v, dtype=float))
        return YT + (1.0 - lv) / (1.0 - (-6.0)) * (YB - YT)

    marks = (1.0, 2.0, 5.0, 10.0)
    stations = [(float(x_of(m)), float(y_of(power * m))) for m in marks]
    kt, dots = moving(stations)
    labels = []
    for m in marks:
        labels.append(
            readout(
                f"t = {m:.0f} s",
                f"被动热 {power * m:.3f} J",
                f"主动输入 {20e-6 * m * 1e6:.0f} μJ",
                "效率不写",
            )
        )
    return scene(
        "被动的热是焦耳，主动搬到低节的那一截留空（示意）",
        [
            f"① 被动<tspan class=\"small\">　4.2²/100 = {power:.3f} W。热按这个功率乘时间。</tspan>",
            "② 主动一拍<tspan class=\"small\">　½×10 μH×(2 A)² = 20 μJ。每秒一拍是示意节拍。</tspan>",
            "③ 纵轴是对数<tspan class=\"small\">　否则 20 μJ 会贴在 0 上看不见。</tspan>",
            "④ 口诀<tspan class=\"small\">　热可以口算。效率百分数留空，任务板还没收这份数。</tspan>",
        ],
        "能量 J（对数，示意）",
        "时间 s",
        "\n".join(
            (
                xticks(x_of, YB, [(1, "1"), (5, "5"), (10, "10")]),
                yticks(y_of, X0, [(1e-5, "10μJ"), (1e-3, "1mJ"), (1.0, "1J")]),
            )
        ),
        poly(_xy(x_of, y_of, t, e_pass), "liner") + "\n" + poly(_xy(x_of, y_of, t, e_act), "lineb") + "\n" + dots,
        '  <text class="warn" x="200" y="218">红 被动变成热</text>\n  <text class="hi" x="400" y="218">蓝 主动每拍输入</text>',
        labels,
        kt,
        "4.2 V、100 Ω、10 μH、2 A 是详解里的示例。不写效率百分数。",
        "均衡拓扑示意：被动按 4.2 V、100 Ω 把能量变成热；主动一拍输入 20 μJ。搬到低节的效率不在这张图上填。",
        "对数轴上红线是热量，蓝线是主动侧已经花掉的输入。金点沿红线走。输出那一截留空。",
        "formula: P=4.2^2/100; Epass=P*t; Eact=20e-6*t; 20 uJ = 0.5*10e-6*2^2",
    )


def build_balance_blank() -> str:
    """输入能量已知，输出未知，所以效率格留空。"""
    n = np.arange(1, 11, dtype=float)
    e_in_uj = 20.0 * n

    def x_of(v):
        return X0 + (np.asarray(v, dtype=float) - 1.0) / 9.0 * (X1 - X0)

    def y_of(v):
        return YT + (220.0 - np.asarray(v, dtype=float)) / 220.0 * (YB - YT)

    marks = (1, 4, 7, 10)
    stations = [(float(x_of(m)), float(y_of(20.0 * m))) for m in marks]
    kt, dots = moving(stations)
    labels = [readout(f"拍数 {m:.0f}", f"输入 {20 * m:.0f} μJ", "输出 留空") for m in marks]
    return scene(
        "分母有了，分子没有，效率格就空着（示意）",
        [
            "① 一拍输入<tspan class=\"small\">　仍是 ½LI² = 20 μJ。这一头可以口算。</tspan>",
            "② 累加<tspan class=\"small\">　十拍 200 μJ。直线，斜率每拍 20 μJ。</tspan>",
            "③ 输出<tspan class=\"small\">　低节实际收到多少，仓库里没有这份测量。</tspan>",
            "④ 口诀<tspan class=\"small\">　没有分子就不要写百分数。空着是诚实。</tspan>",
        ],
        "累计输入 μJ（示意）",
        "拍数",
        "\n".join(
            (
                xticks(x_of, YB, [(1, "1"), (4, "4"), (10, "10")]),
                yticks(y_of, X0, [(20, "20"), (100, "100"), (200, "200")]),
            )
        ),
        poly(_xy(x_of, y_of, n, e_in_uj), "lineb") + "\n" + dots,
        '  <text class="small" x="200" y="218">只有输入。输出不画，避免编出一个效率。</text>',
        labels,
        kt,
        "拓扑效率的定量对比仍见任务板。这张图故意不填那一格。",
        "均衡效率空表示意：主动一拍的输入按 20 μJ 累加，输出未知，所以不写效率百分数。",
        "直线斜率是每拍 20 μJ。金点沿输入走，底栏每一拍都写着输出留空。",
        "formula: Ein=20 uJ * n; Eout left blank; eta not plotted",
    )


def build_cloud_pack() -> str:
    """包上的阶梯用文档里的时间：10 μs 示例、DW01 过充 80–200 ms、云上 1 s 与 30 s。"""
    t = np.logspace(-6, 2, 140)

    def x_of(v):
        return X0 + (np.log10(np.asarray(v, dtype=float)) - (-6)) / 8.0 * (X1 - X0)

    def y_of(v):
        return YT + (1.15 - np.asarray(v, dtype=float)) / 1.15 * (YB - YT)

    short = np.where(t < 10e-6, 1.0, 0.0)
    ov = np.where(t < 0.080, 1.0, 0.0)
    cloud = np.where(t < 30.0, 1.0, 0.0)
    marks = (10e-6, 0.080, 0.200, 30.0)
    stations = [(float(x_of(m)), float(y_of(0.0 if m >= 0.080 else 1.0))) for m in marks]
    kt, dots = moving(stations)
    labels = [
        readout("t = 10 μs", "短路通道 已动作", "过充通道 未动作", "云记录 未到点"),
        readout("t = 80 ms", "短路通道 已动作", "过充通道 已动作", "云记录 未到点"),
        readout("t = 200 ms", "短路通道 已动作", "过充延时上沿", "云记录 未到点"),
        readout("t = 30 s", "短路通道 已动作", "过充通道 已动作", "云记录 到点"),
    ]
    return scene(
        "切断在包上，云上的 30 秒是记录（示意）",
        [
            "① 短路窗口<tspan class=\"small\">　示例 10 μs。蓝线在这里落到已动作。</tspan>",
            "② 过充延时<tspan class=\"small\">　DW01 的 80–200 ms。绿线画在 80 ms 这道下沿。</tspan>",
            "③ 云上的记录<tspan class=\"small\">　报警存储最大 1 s，正常存储最大 30 s。</tspan>",
            "④ 口诀<tspan class=\"small\">　热失控切断不能等云端下令。晚到的报文用来复盘。</tspan>",
        ],
        "1 = 未动作，0 = 已动作",
        "时间 s（对数）",
        "\n".join(
            (
                xticks(x_of, YB, [(10e-6, "10μs"), (0.08, "80ms"), (1, "1s"), (30, "30s")]),
                yticks(y_of, X0, [(0, "0 已动"), (1, "1 未动")]),
            )
        ),
        "\n".join(
            (
                poly(_xy(x_of, y_of, t, short), "lineb"),
                poly(_xy(x_of, y_of, t, ov), "lineg"),
                poly(_xy(x_of, y_of, t, cloud), "liner"),
                dots,
            )
        ),
        '  <text class="hi" x="160" y="218">蓝 10 μs</text>\n  <text class="ok" x="280" y="218">绿 80 ms</text>\n  <text class="warn" x="420" y="218">红 30 s</text>',
        labels,
        kt,
        "10 μs 是短路示例。80–200 ms 是 DW01 过充延时。1 s 和 30 s 是正文对 GB/T 32960.2 的转述。都不是 FTTI。",
        "包端与云端的时间差：短路示例 10 μs、DW01 过充 80–200 ms，都早于云上正常存储最多 30 s 的记录。",
        "三条阶梯在对数时间上先后落下。金点沿 80 ms 那条走。切断留在包上，云端报文用来复盘。",
        "formula: steps at 10 us, 80 ms, 30 s; DW01 OV delay band 80-200 ms; GB/T 32960.2 storage ceilings as paraphrased in stage 6",
    )


def build_precharge() -> str:
    """400 V、1 mF、170 Ω。把 RC 示例里的 2.35 A 和 80 J 收进同一根时间轴。"""
    r_ohm, c_farad, u_pack = 170.0, 0.001, 400.0
    tau = r_ohm * c_farad
    t = np.linspace(0.0, 0.8, 81)
    volt = u_pack * (1.0 - np.exp(-t / tau))

    def x_of(v):
        return X0 + np.asarray(v, dtype=float) / 0.8 * (X1 - X0)

    def y_of(v):
        return YT + (420.0 - np.asarray(v, dtype=float)) / 420.0 * (YB - YT)

    marks = (0.0, tau, 3 * tau, 0.8)
    stations = [(float(x_of(m)), float(y_of(u_pack * (1.0 - np.exp(-m / tau))))) for m in marks]
    kt, dots = moving(stations, cls="dotb")
    labels = []
    for m in marks:
        v = u_pack * (1.0 - np.exp(-m / tau))
        current = (u_pack - v) / r_ohm
        gate = "可合" if m + 1e-9 >= 3 * tau and v > 100 else "仍开"
        labels.append(
            readout(
                f"t = {m:.2f} s",
                f"母线 {v:.0f} V",
                f"预充电流 {current:.2f} A",
                f"主闸 {gate}",
            )
        )
    y40 = float(y_of(40.0))
    yk = float(x_of(3 * tau))
    extra = "\n".join(
        (
            f'  <line class="liner" x1="{X0:.0f}" y1="{y40:.1f}" x2="{X1:.0f}" y2="{y40:.1f}" stroke-dasharray="6 4"/>',
            f'  <line class="lineg" x1="{yk:.1f}" y1="{YT:.0f}" x2="{yk:.1f}" y2="{YB:.0f}"/>',
            '  <text class="warn" x="200" y="430">故障示意：停在约 40 V，K1 仍开</text>',
        )
    )
    return scene(
        "电压先爬。大约 0.51 s 才合主闸（示意）",
        [
            f"① t=0<tspan class=\"small\">　只合预充闸。I0=400/170={u_pack / r_ohm:.2f} A。</tspan>",
            f"② 一个 τ<tspan class=\"small\">　{tau:.2f} s，约 63%，253 V 上下。主闸仍开。</tspan>",
            "③ 约 3τ<tspan class=\"small\">　0.51 s，约 95%，380 V。这时才合 K1，再打开预充闸。</tspan>",
            "④ 口诀<tspan class=\"small\">　爬不到就不合主闸。充到 400 V 的储能是 80 J。</tspan>",
        ],
        "母线电压 V（示意）",
        "时间 s",
        "\n".join(
            (
                xticks(x_of, YB, [(0, "0"), (0.17, "0.17"), (0.51, "0.51"), (0.8, "0.8")]),
                yticks(y_of, X0, [(40, "40"), (253, "253"), (380, "380")]),
            )
        ),
        poly(_xy(x_of, y_of, t, volt), "lineb") + "\n" + extra + "\n" + dots,
        '  <text class="ok" x="480" y="230">绿线 合 K1</text>',
        labels,
        kt,
        "400 V、1 mF、170 Ω、80 J 是同一笔口算。½CU²=80 J 几乎全变成电阻上的热。不是示波器。",
        "预充示意：400 V、1 mF、170 Ω。约 0.17 s 到 253 V，约 0.51 s 到 380 V 才合主闸。刚接通约 2.35 A，储能 80 J。",
        "蓝线是 400(1−e^{−t/0.17})。绿竖线在约 0.51 s。故障若停在约 40 V，主闸保持打开。示意，不是示波器。",
        "formula: V=400*(1-exp(-t/0.17)); I=(400-V)/170; E=0.5*0.001*400^2=80 J; close K1 near 3 tau",
    )


def build_weld() -> str:
    """τ=1 s 来自 10 μF 与 100 kΩ。粘连侧不跟着掉。"""
    tau = 10e-6 * 100e3
    t = np.linspace(0.0, 5.0, 81)
    volt = 400.0 * np.exp(-t / tau)
    stuck = np.full_like(t, 400.0)

    def x_of(v):
        return X0 + np.asarray(v, dtype=float) / 5.0 * (X1 - X0)

    def y_of(v):
        return YT + (420.0 - np.asarray(v, dtype=float)) / 420.0 * (YB - YT)

    marks = (0.1, 1.0, 2.0, 5.0)
    stations = [(float(x_of(m)), float(y_of(400.0 * np.exp(-m / tau)))) for m in marks]
    kt, dots = moving(stations)
    labels = []
    for m in marks:
        v = 400.0 * np.exp(-m / tau)
        shown = f"{v:.0f}" if v >= 10 else f"{v:.1f}"
        labels.append(readout(f"t = {m:.1f} s", f"正常侧 {shown} V", "粘连侧 400 V"))
    return scene(
        "100 ms 还很高，5 s 才落到个位数（示意）",
        [
            "① 命令已经断开<tspan class=\"small\">　正常侧 V=400·e^(−t/τ)，τ=RC=1 s。</tspan>",
            "② 100 ms<tspan class=\"small\">　还剩大约 90%，三百六十伏上下。这时采样会误判。</tspan>",
            "③ 5 s<tspan class=\"small\">　大约 2.7 V。仍停在包压附近，才像粘连。</tspan>",
            "④ 口诀<tspan class=\"small\">　命令已经断开，负载侧电压还不掉，就是粘连。</tspan>",
        ],
        "负载侧电压 V（示意包压 400）",
        "时间 s",
        "\n".join(
            (
                xticks(x_of, YB, [(0.1, "0.1"), (1, "1"), (5, "5")]),
                yticks(y_of, X0, [(2.7, "2.7"), (362, "362"), (400, "400")]),
            )
        ),
        poly(_xy(x_of, y_of, t, volt), "lineb") + "\n" + poly(_xy(x_of, y_of, t, stuck), "liner") + "\n" + dots,
        '  <text class="hi" x="200" y="218">蓝 正常断开</text>\n  <text class="warn" x="380" y="218">红 粘连，停在 400 V</text>',
        labels,
        kt,
        "10 μF、100 kΩ、τ=1 s 是示例。真实窗口用本包的 Y 电容和泄放电阻重算。",
        "粘连检测示意：正常侧按 400·e^(−t) 衰减，0.1 s 约 362 V，5 s 约 2.7 V。粘连侧停在 400 V。",
        "金点沿正常衰减走。粘连是那条不掉的红线。100 ms 就采样，会把正常断开判成粘连。",
        "formula: tau=10e-6*100e3=1 s; V=400*exp(-t/tau); weld stays at 400 V",
    )


def build_protocol() -> str:
    """用仓库自己的教学帧和 CRC-8/ATM。垃圾前缀之后能重新同步。"""
    proto = str(ROOT / "code" / "protocol")
    if proto not in sys.path:
        sys.path.insert(0, proto)
    from frames import Frame, FrameParser

    good = Frame(0x01, 0x03, bytes([0x0E, 0x74])).to_bytes()
    garbage = bytes([0x00, 0x11, 0x22])
    stream = garbage + good
    bad = bytearray(stream)
    bad[-2] ^= 0x01  # 数据末字节翻一位，CRC 不再匹配

    def trace(blob: bytes) -> tuple[list[int], list[int]]:
        parser = FrameParser()
        ok, crc_bad = [], []
        for byte in blob:
            parser.feed(byte)
            ok.append(parser.frames_ok)
            crc_bad.append(parser.frames_bad_crc)
        return ok, crc_bad

    ok = trace(stream)[0]
    crc_bad = trace(bytes(bad))[1]
    idx = np.arange(len(stream), dtype=float)

    def x_of(v):
        return X0 + np.asarray(v, dtype=float) / (len(stream) - 1) * (X1 - X0)

    def y_of(v):
        return YT + (1.2 - np.asarray(v, dtype=float)) / 1.2 * (YB - YT)

    marks = (2, 3, len(stream) - 2, len(stream) - 1)
    stations = [(float(x_of(m)), float(y_of(ok[m]))) for m in marks]
    kt, dots = moving(stations, cls="dotg")
    labels = []
    for m in marks:
        labels.append(
            readout(
                f"字节 {m}",
                f"值 0x{stream[m]:02X}",
                f"好帧 {ok[m]}",
                f"坏 CRC {crc_bad[m]}",
            )
        )
    mv = (0x0E << 8) | 0x74
    return scene(
        "垃圾前缀后面，好帧还找得回来（示意）",
        [
            "① 帧头<tspan class=\"small\">　教学帧是 AA 55。前面三个垃圾字节先被让开。</tspan>",
            f"② 数据<tspan class=\"small\">　命令 0x03，大端毫伏。这里是 0x0E74 = {mv} mV。</tspan>",
            "③ CRC-8/ATM<tspan class=\"small\">　盖住地址到数据。对得上，解析器交还一帧。</tspan>",
            "④ 口诀<tspan class=\"small\">　坏帧要计数。翻一位就对不上，不许静默吞掉。</tspan>",
        ],
        "完成的好帧数",
        "字节序号",
        "\n".join(
            (
                xticks(x_of, YB, [(0, "0"), (3, "帧头"), (len(stream) - 1, "末字节")]),
                yticks(y_of, X0, [(0, "0"), (1, "1")]),
            )
        ),
        poly(_xy(x_of, y_of, idx, np.array(ok, dtype=float)), "lineg")
        + "\n"
        + poly(_xy(x_of, y_of, idx, np.array(crc_bad, dtype=float)), "liner")
        + "\n"
        + dots,
        '  <text class="ok" x="180" y="218">绿 好流</text>\n  <text class="warn" x="300" y="218">红 翻位后的坏 CRC 计数</text>',
        labels,
        kt,
        "帧格式是仓库教学帧，不是某家 BMS。3700 mV 按 code/protocol 的大端约定换算，不是抓包。",
        "协议重同步示意：三个垃圾字节之后，教学帧 AA 55 仍能被 code/protocol 的解析器认出来。翻一位则坏 CRC 计数加一。",
        "绿线在最后一个好字节跳到 1。红线是同一位置翻位后的坏 CRC 计数。金点沿好流走。坏帧要计数，不能把程序打死。",
        "formula: Frame(0x01,0x03,bytes([0x0E,0x74])) via code/protocol; garbage 00 11 22; CRC-8/ATM; one bit flip",
    )


def build_uv() -> str:
    """预充带才画 0.05C。深放带电流是 0：优先报废，不鼓励激活。"""
    cap = 5.0
    i_small = 0.05 * cap

    def x_of(v):
        return X0 + (np.asarray(v, dtype=float) - 1.0) / 2.6 * (X1 - X0)

    def y_of(v):
        return YT + (6.0 - np.asarray(v, dtype=float)) / 6.0 * (YB - YT)

    def allow(v: float) -> float:
        # 大约 2.0–3.0 V 才是小电流预充。再低不画成可以充。
        return i_small if 2.0 <= v <= 3.0 else 0.0

    v_marks = (1.2, 2.5, 2.8, 3.0)
    stations = [(float(x_of(v)), float(y_of(allow(v)))) for v in v_marks]
    kt, dots = moving(stations)
    labels = [
        readout("V = 1.2 V", "深放危险带", "允许电流 0 A", "优先报废"),
        readout("V = 2.5 V", "预充带", f"允许电流 {i_small:.2f} A", "1C = 5 A，不要"),
        readout("V = 2.8 V", "预充带", f"允许电流 {i_small:.2f} A", "1C = 5 A，不要"),
        readout("V = 3.0 V", "预充门槛", f"允许电流 {i_small:.2f} A", "以上按手册"),
    ]
    v_pre = np.linspace(2.0, 3.0, 17)
    i_pre = np.full_like(v_pre, i_small)
    y_big = float(y_of(cap))
    x_lo, x_hi = float(x_of(2.0)), float(x_of(3.0))
    shades = "\n".join(
        (
            band(X0, YT, float(x_of(2.0)) - X0, YB - YT, "boxr"),
            band(x_lo, YT, x_hi - x_lo, YB - YT, "boxy"),
        )
    )
    dont = (
        f'  <line class="liner" x1="{x_lo:.1f}" y1="{y_big:.1f}" x2="{x_hi:.1f}" y2="{y_big:.1f}" stroke-dasharray="6 4"/>'
    )
    return scene(
        "低于约 3 V 只走小电流；深放优先报废（示意）",
        [
            "① 低于约 3.0 V<tspan class=\"small\">　或手册的预充门槛：只许小电流，直到回到门槛以上。</tspan>",
            "② 大约 2.0–3.0 V<tspan class=\"small\">　教学 5 Ah 的 0.05C = 0.25 A。红虚线 1C 不要走。</tspan>",
            "③ 低于约 1.5–2 V<tspan class=\"small\">　或放很久：铜枝晶、内短路。很多厂家要求报废。</tspan>",
            "④ 口诀<tspan class=\"small\">　跟着手册。拿不准就报废。鼓包漏液也报废。不要激活。</tspan>",
        ],
        "允许电流 A（示意）",
        "单体电压 V",
        "\n".join(
            (
                xticks(x_of, YB, [(1.2, "1.2"), (2.0, "2.0"), (2.5, "2.5"), (3.0, "3.0")]),
                yticks(y_of, X0, [(0.25, "0.25"), (5, "5")]),
            )
        ),
        shades
        + "\n"
        + poly(_xy(x_of, y_of, v_pre, i_pre), "lineb")
        + "\n"
        + dont
        + "\n"
        + dots,
        '  <text class="warn" x="160" y="218">浅红 深放，优先报废</text>\n  <text class="gold" x="360" y="218">浅黄 预充带</text>\n  <text class="hi" x="500" y="218">蓝 0.05C</text>',
        labels,
        kt,
        "大约 2.5–3.0 V 是常见小电流预充带，不是铜溶解点。5 Ah 是教学容量。拿不准就报废。",
        "亏电示意：低于约 3.0 V 只允许小电流。教学 5 Ah 的 0.05C 是 0.25 A，只画在大约 2.0–3.0 V。更深的优先报废。",
        "浅红是深放危险带，允许电流画成 0。浅黄预充带里蓝线是 0.25 A，红虚线 5 A 标成不要。正常充电电流以手册为准。",
        "formula: I=0.05*5 Ah=0.25 A only for about 2.0..3.0 V; I=0 below 2.0 V; 1C=5 A marked do-not-use",
    )


def build_balance_speed() -> str:
    """1 个百分点、示意 5 Ah。被动电流用阶段 1 的 50–200 mA。"""
    cap_ah = 5.0
    delta_ah = 0.01 * cap_ah
    current = np.linspace(0.05, 0.20, 41)
    hours = delta_ah / current

    def x_of(v):
        return X0 + (np.asarray(v, dtype=float) - 0.05) / 0.15 * (X1 - X0)

    def y_of(v):
        return YT + (1.2 - np.asarray(v, dtype=float)) / 1.2 * (YB - YT)

    marks = (0.05, 0.10, 0.15, 0.20)
    stations = [(float(x_of(m)), float(y_of(delta_ah / m))) for m in marks]
    kt, dots = moving(stations)
    labels = []
    for m in marks:
        hours_i = delta_ah / m
        sec_1c = delta_ah / cap_ah * 3600.0
        labels.append(
            readout(
                f"I = {m * 1000:.0f} mA",
                f"修 1 个百分点 {hours_i:.2f} h",
                f"对照 1C 要 {sec_1c:.0f} s",
            )
        )
    return scene(
        "均衡比充放电小两个数量级，所以很慢（示意）",
        [
            "① 差 1 个百分点<tspan class=\"small\">　示意 5 Ah 就是 0.05 Ah，50 mAh。</tspan>",
            "② 50 mA<tspan class=\"small\">　要 1 小时。200 mA 要 0.25 小时。都在阶段 1 的示例范围里。</tspan>",
            "③ 1C<tspan class=\"small\">　5 A 只要 36 s。50 mA 的 100 倍，大约两个数量级。</tspan>",
            "④ 口诀<tspan class=\"small\">　均衡治不了根本。配组、热、均衡，三件事一起做。</tspan>",
        ],
        "修掉 1 个百分点要几小时",
        "均衡电流 A",
        "\n".join(
            (
                xticks(x_of, YB, [(0.05, "0.05"), (0.10, "0.10"), (0.20, "0.20")]),
                yticks(y_of, X0, [(0.25, "0.25"), (1, "1")]),
            )
        ),
        poly(_xy(x_of, y_of, current, hours), "lineb") + "\n" + dots,
        '  <text class="small" x="200" y="218">t = 0.05 Ah / I。更大的充放电电流会到三个数量级。</text>',
        labels,
        kt,
        "50–200 mA 是阶段 1 写的示例范围。5 Ah 是教学容量。不能拿这张图代替配组。",
        "均衡有多慢：示意 5 Ah 的 1 个百分点，50 mA 要 1 小时，200 mA 要 0.25 小时。1C 只要 36 秒。",
        "时间与电流成反比。金点沿曲线走，底栏把毫安和小时换出来。均衡电流比充放电小得多，只能慢慢修。",
        "formula: t_h=0.05/I for I in 0.05..0.20 A; 1C reference 5 A takes 36 s; 5 Ah and 50-200 mA are teaching figures",
    )


BUILDERS = {
    "afe-register-read.svg": build_afe,
    "gbt-27930-handshake.svg": build_gbt,
    "gate-return-loop.svg": build_gate,
    "hvil-loop.svg": build_hvil,
    "overdischarge-copper.svg": build_copper,
    "short-i2t-window.svg": build_i2t,
    "smbus-sbs-roundtrip.svg": build_smbus,
    "active-discharge-beside-contactor.svg": build_discharge_beside,
    "solid-vs-structural-cell.svg": build_solid,
    "isolation-copper-bridge.svg": build_isolation,
    "cloud-bms-dashboard.svg": build_cloud_dash,
    "cert-floor-scene.svg": build_cert,
    "pack-manual-sampling.svg": build_pack_manual,
    "mqtt-pubsub-will.svg": build_mqtt,
    "parallel-tap-boundary.svg": build_parallel,
    "bq769-evb-isospi.svg": build_isospi_cm,
    "balance-topology-compare.svg": build_balance_topo,
    "cloud-vs-pack-protection.svg": build_cloud_pack,
    "balance-efficiency-blank.svg": build_balance_blank,
    "precharge-sequence-curve.svg": build_precharge,
    "contactor-weld-check.svg": build_weld,
    "protocol-resync.svg": build_protocol,
    "uv-recovery-005c.svg": build_uv,
    "balance-vs-pack-current.svg": build_balance_speed,
}
