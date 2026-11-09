#!/usr/bin/env python3
"""Generate D11 and D12 figures."""
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


d11 = load("d11_joint_hppc", "d11_joint_hppc.py")
d12 = load("d12_soc_baseline", "d12_soc_baseline.py")

ROOT = HERE.parents[2]
OUT11 = ROOT / "bms-book" / "engineering" / "assets" / "d11-hppc"
OUT12 = ROOT / "bms-book" / "engineering" / "assets" / "d12-soc"

STYLE = """<style>
  .bg { fill: #f6f1e3; }
  .title { fill: #003153; font: 700 20px 'KaiTi','STKaiti','Noto Serif SC',serif; }
  .sub { fill: #5c6d73; font: 13px 'Noto Sans SC','Microsoft YaHei',sans-serif; }
  .lbl { fill: #4d5d63; font: 13px 'Noto Sans SC','Microsoft YaHei',sans-serif; }
  .small { fill: #4d5d63; font: 12px 'Noto Sans SC','Microsoft YaHei',sans-serif; }
  .value { fill: #003153; font: 700 18px 'Noto Sans SC','Microsoft YaHei',sans-serif; }
  .sym { fill: #003153; font: 700 19px 'KaiTi','STKaiti','Noto Serif SC',serif; }
  .share { stroke: #176b64; stroke-width: 2.6; fill: none; stroke-linecap: round; }
  .free { stroke: #8a5019; stroke-width: 2.2; fill: none; stroke-dasharray: 6 4; }
  .bad { stroke: #a3322a; stroke-width: 2.6; fill: none; stroke-linecap: round; }
  .box { fill: #fbf8f1; stroke: #003153; stroke-width: 2; rx: 8; }
  .bar-ok { fill: #176b64; opacity: 0.3; }
  .bar-bad { fill: #a3322a; opacity: 0.3; }
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


def f11_1_sharing() -> str:
    w, h = 800, 420
    b = [text(40, 40, "图 D11-F1　参数共享合同：τ 共享，K 逐工况", "title")]
    b.append(text(40, 64, "绿实线=跨工况共享；棕虚线=逐脉冲自由；K 的局部性用 160 mV 的留出差计量", "sub"))
    # 两个脉冲节点
    for x, label in ((120, "脉冲 A（z=0.60）"), (520, "脉冲 B（z=0.40）")):
        b.append(f'<rect class="box" x="{x}" y="110" width="180" height="56"/>')
        b.append(text(x + 90, 134, label, "lbl", "middle"))
        b.append(text(x + 90, 154, "K/A 逐脉冲自由", "small", "middle"))
    # τ 共享
    b.append('<path class="share" d="M 210 166 V 240 M 610 166 V 240 M 210 240 H 610"/>')
    b.append(text(410, 232, "τ = 45 s（共享）", "sym", "middle"))
    # K 不可迁移警示
    b.append('<path class="bad" d="M 300 138 H 520"/>')
    b.append(text(410, 128, "K 直接迁移 → 留出 160 mV", "small", "middle"))
    b.append(text(40, 300, "参数共享合同：每个参数注明共享/自由及物理理由；写不出理由默认逐工况自由", "lbl"))
    b.append(text(40, 330, "边界命中报告：网格最优压在边缘 → 标记并扩网格确认，不静默当真值", "lbl"))
    return svg(w, h, "参数共享合同示意", "两脉冲联合拟合中共享参数与逐工况自由参数的边界", "\n".join(b))


def f11_2_loo() -> str:
    w, h = 800, 400
    b = [text(40, 40, "图 D11-F2　留出验证：K 不可迁移的计量", "title")]
    b.append(text(40, 64, "同一真值下：单脉冲参数跨 SOC 留出 160 mV；联合拟合（共享 τ、逐脉冲 K）留出 0 mV", "sub"))
    x0, scale = 220, 3.2
    rows = [("单脉冲（z=0.60）→ z=0.40", 160.0, "bar-bad", "160.0 mV = ΔOCV"),
            ("联合拟合 → z=0.40", 0.0, "bar-ok", "0.0 mV")]
    y = 130
    for name, mv, cls, note in rows:
        b.append(text(x0 - 12, y + 16, name, "lbl", "end"))
        width = max(mv * scale, 2)
        b.append(f'<rect class="{cls}" x="{x0}" y="{y}" width="{width:.1f}" height="30" rx="5"/>')
        b.append(text(x0 + width + 12, y + 20, note, "value"))
        y += 70
    b.append(text(220, 320, "读法：拟合残差只是拟合残差；留出残差才是可迁移性的证据（B05）", "lbl"))
    return svg(w, h, "留出验证对照", "单脉冲参数与联合拟合参数在留出 SOC 点上的 RMSE 对照", "\n".join(b))


def f12_1_three_errors() -> str:
    w, h = 800, 420
    b = [text(40, 40, "图 D12-F1　三种 SOC 误差的形状", "title")]
    b.append(text(40, 64, "偏置随时间线性放大；初值恒定跟随；容量是全程增益误差", "sub"))
    px0, py0 = 90, 110
    b.append(f'<line class="axis" x1="{px0}" y1="{py0 + 220}" x2="{px0 + 600}" y2="{py0 + 220}"/>')
    b.append(f'<line class="axis" x1="{px0}" y1="{py0}" x2="{px0}" y2="{py0 + 220}"/>')
    hours = 10
    for name, cls, fn in (
        ("偏置 50 mA：25 pp / 10 h", "bad", lambda t: 2.5 * t),
        ("初值错 10 pp", "free", lambda t: 10.0),
        ("容量错 5%", "share", lambda t: 0.476 * t),
    ):
        pts = " ".join(
            f"{px0 + t / hours * 560:.1f},{py0 + 220 - fn(t) * 7:.1f}" for t in range(hours + 1)
        )
        b.append(f'<polyline class="{cls}" points="{pts}"/>')
        b.append(text(px0 + 570, py0 + 220 - fn(hours) * 7 + 4, name, "small"))
    b.append(text(px0 + 300, py0 + 250, "时间（h）", "small", "middle"))
    b.append(text(px0 - 8, py0 - 8, "SOC 误差（pp）", "small", "end"))
    b.append(text(90, 385, "三种伤要不同的医生：偏置靠校准频次，初值靠 OCV 校准，容量靠重新标定", "lbl"))
    return svg(w, h, "三种 SOC 误差形状", "电流偏置/初值/容量三类误差随时间的不同传播形状", "\n".join(b))


def f12_2_calibration() -> str:
    w, h = 800, 420
    b = [text(40, 40, "图 D12-F2　OCV 校准的三个生效条件", "title")]
    b.append(text(40, 64, "静置够久 × 斜率够陡 × 迟滞同支；缺一，校准方向都可能错", "sub"))
    conds = [
        ("静置够久", "极化退场：电荷转移秒级、浓差十秒–分钟", "没等够 = 把病当健康读"),
        ("斜率够陡", "5 mV：陡区 0.8 → 0.62 pp；平坦区 0.08 → 6.25 pp", "平坦区近乎失明"),
        ("迟滞同支", "10 mV 迟滞 @ 0.8 斜率 = 1.25 pp 校准误差", "用错支，校准本身成误差源"),
    ]
    y = 120
    for name, fact, fail in conds:
        b.append(f'<rect class="box" x="60" y="{y}" width="160" height="56"/>')
        b.append(text(140, y + 26, name, "sym", "middle"))
        b.append(text(140, y + 46, "条件", "small", "middle"))
        b.append(text(240, y + 24, fact, "lbl"))
        b.append(text(240, y + 46, f"失效后果：{fail}", "small"))
        y += 84
    b.append(text(60, 400, "报告纪律：写“OCV 校准已执行”必须同页附三个条件的满足证据", "lbl"))
    return svg(w, h, "OCV 校准三条件", "静置时长、OCV 斜率与迟滞分支三个校准生效条件及其失效后果", "\n".join(b))


def main() -> None:
    OUT11.mkdir(parents=True, exist_ok=True)
    OUT12.mkdir(parents=True, exist_ok=True)
    for name, payload in {"D11-F1-sharing-contract.svg": f11_1_sharing(), "D11-F2-loo-validation.svg": f11_2_loo()}.items():
        (OUT11 / name).write_text(payload, encoding="utf-8")
        print(f"wrote {OUT11 / name}")
    for name, payload in {"D12-F1-three-errors.svg": f12_1_three_errors(), "D12-F2-calibration.svg": f12_2_calibration()}.items():
        (OUT12 / name).write_text(payload, encoding="utf-8")
        print(f"wrote {OUT12 / name}")


if __name__ == "__main__":
    main()
