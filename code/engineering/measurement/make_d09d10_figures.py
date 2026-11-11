#!/usr/bin/env python3
"""Generate D09 and D10 figures."""

from __future__ import annotations

from html import escape
from pathlib import Path
import importlib.util
import sys

HERE = Path(__file__).resolve().parent


def load(name: str, path: str):
    spec = importlib.util.spec_from_file_location(name, HERE / path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


d09 = load("d09_independence", "d09_independence.py")
d10 = load("d10_balance", "d10_balance.py")

ROOT = HERE.parents[2]
OUT9 = ROOT / "bms-book" / "engineering" / "assets" / "d09-safety"
OUT10 = ROOT / "bms-book" / "engineering" / "assets" / "d10-balance"

STYLE = """<style>
  .bg { fill: #f6f1e3; }
  .title { fill: #003153; font: 700 20px 'KaiTi','STKaiti','Noto Serif SC',serif; }
  .sub { fill: #5c6d73; font: 13px 'Noto Sans SC','Microsoft YaHei',sans-serif; }
  .lbl { fill: #4d5d63; font: 13px 'Noto Sans SC','Microsoft YaHei',sans-serif; }
  .small { fill: #4d5d63; font: 12px 'Noto Sans SC','Microsoft YaHei',sans-serif; }
  .value { fill: #003153; font: 700 18px 'Noto Sans SC','Microsoft YaHei',sans-serif; }
  .sym { fill: #003153; font: 700 19px 'KaiTi','STKaiti','Noto Serif SC',serif; }
  .wire { stroke: #003153; stroke-width: 2.2; fill: none; stroke-linecap: round; stroke-linejoin: round; }
  .kill { stroke: #a3322a; stroke-width: 2.6; fill: none; stroke-linecap: round; stroke-dasharray: 7 5; }
  .ok { stroke: #176b64; stroke-width: 2.6; fill: none; stroke-linecap: round; }
  .box { fill: #fbf8f1; stroke: #003153; stroke-width: 2; rx: 8; }
  .cell-bad { fill: #a3322a; opacity: 0.14; }
  .cell-mid { fill: #8a5019; opacity: 0.16; }
  .cell-good { fill: #176b64; opacity: 0.18; }
  .axis { stroke: #5c6d73; stroke-width: 1.3; }
  .halo { paint-order: stroke; stroke: #f6f1e3; stroke-width: 4; stroke-linejoin: round; }
</style>"""


def svg(width: int, height: int, title: str, desc: str, body: str) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}" role="img" aria-label="{escape(title)}">\n'
        f"<title>{escape(title)}</title>\n<desc>{escape(desc)}</desc>\n{STYLE}\n"
        f'<rect class="bg" x="0" y="0" width="{width}" height="{height}"/>\n{body}\n</svg>\n'
    )


def text(x, y, value, cls="lbl", anchor="start") -> str:
    return (
        f'<text class="{cls}" x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}">'
        f"{escape(value, quote=False)}</text>"
    )


def f9_1_common_supply() -> str:
    w, h = 800, 420
    b = [text(40, 40, "图 D09-F1　共同供电：独立性声明的单点击穿", "title")]
    b.append(
        text(
            40,
            64,
            "“双 MCU 双算法”的账面冗余被一根电源轨归零；独立性按失效模式逐条审",
            "sub",
        )
    )
    # 供电轨
    b.append('<rect class="box" x="300" y="100" width="200" height="44"/>')
    b.append(text(400, 127, "共用 DC/DC 供电轨", "sym", "middle"))
    # 两条通道
    b.append('<path class="wire" x1="350" y1="144" x2="230" y2="200"/>')
    b.append('<path class="wire" x1="450" y1="144" x2="570" y2="200"/>')
    b.append('<rect class="box" x="150" y="200" width="160" height="60"/>')
    b.append(text(230, 228, "主 MCU 算法", "lbl", "middle"))
    b.append(text(230, 248, "阈值 + 模型", "small", "middle"))
    b.append('<rect class="box" x="490" y="200" width="160" height="60"/>')
    b.append(text(570, 228, "副 MCU 简化阈值", "lbl", "middle"))
    b.append(text(570, 248, "“备份”", "small", "middle"))
    # 失效路径
    b.append('<path class="kill" d="M 400 144 V 320 M 230 260 V 320 M 570 260 V 320"/>')
    b.append('<path class="kill" d="M 230 320 H 570"/>')
    b.append(
        '<circle class="cell-bad" cx="400" cy="340" r="6" fill="#a3322a" opacity="0.9"/>'
    )
    b.append(text(414, 346, "供电轨失效 → 备份概率 0", "value"))
    b.append(text(40, 320, "共享项逐项审：供电 / 基准源 / 传感链 / 时钟", "lbl"))
    return svg(
        w,
        h,
        "共同供电双杀示意",
        "双 MCU 账面冗余被共用供电轨单点击穿的故障树示意",
        "\n".join(b),
    )


def f9_2_matrix_fmea() -> str:
    w, h = 800, 600
    b = [text(40, 40, "图 D09-F2　覆盖与隔离：按失效模式审证据", "title")]
    b.append(text(40, 66, "矩阵是检查提示，不是安全等级；高覆盖与隔离也不能替代残余风险论证", "sub"))
    cells = [
        (0, 0, "cell-bad", ("漏诊风险", "共因风险仍在")),
        (1, 0, "cell-mid", ("已有诊断覆盖", "共因仍可使两路同时失效")),
        (0, 1, "cell-mid", ("已识别共因有隔离", "未检出的随机失效仍需控制")),
        (1, 1, "cell-good", ("已分析模式有覆盖与隔离证据", "仍需核查遗漏模式与残余风险")),
    ]
    x0, y0, cw, ch = 90, 116, 340, 84
    for cx, cy, cls, notes in cells:
        x, y = x0 + cx * cw, y0 + cy * ch
        b.append(f'<rect class="{cls}" x="{x}" y="{y}" width="{cw - 12}" height="{ch - 10}" rx="8"/>')
        for line, note in enumerate(notes):
            b.append(text(x + (cw - 12) / 2, y + 30 + line * 24, note, "lbl", "middle"))
    for k, label in enumerate(("覆盖低", "覆盖高")):
        b.append(text(x0 + k * cw + (cw - 12) / 2, y0 - 12, label, "lbl", "middle"))
    for k, label in enumerate(("不隔离", "隔离")):
        b.append(text(x0 - 10, y0 + k * ch + 42, label, "lbl", "end"))
    b.append(text(40, 330, "教学 FMEA：控制、证据与残余风险逐项列", "sym"))
    for i, row in enumerate(d09.fmea_rows()):
        x, y = 40 + (i % 2) * 370, 352 + (i // 2) * 88
        b.append(f'<rect class="box" x="{x}" y="{y}" width="350" height="76"/>')
        b.append(text(x + 12, y + 23, row["mode"], "lbl"))
        control = row["control"]
        for line, start in enumerate(range(0, len(control), 22)):
            b.append(text(x + 12, y + 44 + line * 16, control[start : start + 22], "small"))
    b.append(text(40, 552, "本例保留一项共因缺口；真实项目不要求固定留一行“无”。", "lbl"))
    b.append(text(40, 578, "表格全绿本身不证明安全；每项控制仍需有效性证据。", "lbl"))
    return svg(
        w,
        h,
        "覆盖与隔离审查矩阵及教学 FMEA",
        "按已分析失效模式核查诊断覆盖、共因隔离和残余风险；教学FMEA展示一项未闭合共因缺口，不代替安全论证。",
        "\n".join(b),
    )


def f10_1_bleed() -> str:
    w, h = 800, 420
    b = [text(40, 40, "图 D10-F1　旁路三笔账与分时窗口", "title")]
    b.append(
        text(
            40,
            64,
            "35 mA / 0.122 W / 拉平 50 mAh 要 85.7 min；均衡与测量分时，有效样本 50%",
            "sub",
        )
    )
    # 左：旁路电流路径
    b.append('<rect class="box" x="60" y="120" width="130" height="60"/>')
    b.append(text(125, 150, "电芯 3.5 V", "lbl", "middle"))
    b.append('<path class="ok" d="M 190 150 H 260 V 130 H 300 V 170 H 260"/>')
    b.append(text(245, 118, "R 100 Ω → 35 mA", "small", "middle"))
    b.append(text(245, 190, "P = 0.122 W/通道", "small", "middle"))
    b.append(text(60, 250, "50 mAh ÷ 35 mA = 85.7 min", "value"))
    b.append(
        text(
            60,
            280,
            "需求写 30 min → 只能处理 17.5 mAh：改需求、改电阻，或写明只处理一半",
            "lbl",
        )
    )
    # 右：分时窗口
    tx = 470
    for i in range(3):
        x = tx + i * 90
        b.append(
            f'<rect x="{x}" y="140" width="45" height="30" fill="#a3322a" opacity="0.3" rx="4"/>'
        )
        b.append(
            f'<rect x="{x + 45}" y="140" width="45" height="30" fill="#176b64" opacity="0.3" rx="4"/>'
        )
    b.append(text(tx, 130, "均衡开（样本无效）| 恢复+采样（有效）", "small"))
    b.append(text(tx, 200, "40 ms 周期：有效样本 50%", "value"))
    b.append(text(tx, 230, "用脏样本判均衡 = 正反馈", "lbl"))
    return svg(
        w,
        h,
        "旁路三笔账与分时窗口",
        "100 Ω 旁路的电流/热/时间三笔账与均衡测量分时窗口",
        "\n".join(b),
    )


def f10_2_three_diffs() -> str:
    w, h = 800, 420
    b = [text(40, 40, "图 D10-F2　电压差 / SOC 差 / 容量差不可互换", "title")]
    b.append(
        text(
            40,
            64,
            "20 mV 在平坦区 = 25 pp SOC 差；容量弱节 0.2 Ah 永远在，均衡救不了",
            "sub",
        )
    )
    rows = [
        ("电压差", "20 mV", "随 OCV 斜率变：0.08 区 = 25 pp，0.8 区 = 2.5 pp", "amber"),
        ("SOC 差", "25 pp", "可均衡（拉齐到同一 SOC）", "teal"),
        ("容量差", "0.2 Ah", "不可均衡：满充弱节先到上限，放电先到下限", "red"),
    ]
    y = 120
    for name, magnitude, reading, tone in rows:
        color = {"amber": "#8a5019", "teal": "#176b64", "red": "#a3322a"}[tone]
        b.append(
            f'<rect x="60" y="{y}" width="120" height="52" fill="{color}" opacity="0.22" rx="8"/>'
        )
        b.append(text(120, y + 24, name, "sym", "middle"))
        b.append(text(120, y + 44, magnitude, "small", "middle"))
        b.append(text(200, y + 32, reading, "lbl"))
        y += 76
    b.append('<path class="kill" d="M 120 350 H 680"/>')
    b.append(
        text(400, 374, "先按容量归档弱节，再对非弱节做 SOC 均衡", "value", "middle")
    )
    return svg(
        w,
        h,
        "三种差不可互换",
        "电压差、SOC 差、容量差的换算关系与弱节判据流程",
        "\n".join(b),
    )


def main() -> None:
    OUT9.mkdir(parents=True, exist_ok=True)
    OUT10.mkdir(parents=True, exist_ok=True)
    for name, payload in {
        "D09-F1-common-supply.svg": f9_1_common_supply(),
        "D09-F2-matrix-fmea.svg": f9_2_matrix_fmea(),
    }.items():
        (OUT9 / name).write_text(payload, encoding="utf-8")
        print(f"wrote {OUT9 / name}")
    for name, payload in {
        "D10-F1-bleed-window.svg": f10_1_bleed(),
        "D10-F2-three-diffs.svg": f10_2_three_diffs(),
    }.items():
        (OUT10 / name).write_text(payload, encoding="utf-8")
        print(f"wrote {OUT10 / name}")


if __name__ == "__main__":
    main()
