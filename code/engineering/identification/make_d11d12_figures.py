#!/usr/bin/env python3
"""Generate D11 and D12 figures."""
from __future__ import annotations

import argparse
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


D11_STYLE = """<style>
  .bg { fill:#f6f1e3; }
  .title { font-size:26px; }
  .lbl { font-size:19px; }
  .sub { font-size:17px; }
  .small { font-size:16px; }
  .value { font-size:26px; }
  .box { fill:#fffdf7; stroke:#254959; stroke-width:1.6; }
  .divider { stroke:#c8c1b2; stroke-width:1; }
  .flow { stroke:#176b64; stroke-width:2.5; fill:none; marker-end:url(#arrow); }
  .curve { stroke:#176b64; stroke-width:2.4; fill:none; }
  .mismatch { stroke:#a3322a; stroke-width:2.4; stroke-dasharray:7 4; fill:none; }
</style>
<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10" fill="none" stroke="#176b64" stroke-width="1.5"/></marker></defs>"""


def validation_contract(report: dict | None = None, *, engineering: bool = False) -> str:
    report = d11.build_report() if report is None else report
    fit = report["noisy"]["fit"]
    heading = "图 D11-F1　先分数据，再谈预测" if engineering else "把答案留到最后：一条可信的验证路径"
    b = [D11_STYLE, text(40, 48, heading, "title"),
         text(40, 79, "合成一阶 RC · 放电为正 · 初始极化为零 · 每条尾段 180 s", "sub")]
    cards = [(40, "01  训练 A / B", "电压进入拟合", "共享 R1 / τ", "K 逐脉冲自由"),
             (350, "02  独立标定", "OCV / 容量 Q / 初始 SOC", "协议给定电流和时长", "算脉冲后的 K"),
             (660, "03  验证 C / D", "先不看实测电压", "换 SOC、方向与脉冲时长", "整条脉冲留出")]
    for x, title, line1, line2, line3 in cards:
        b.append(f'<rect class="box" x="{x}" y="110" width="260" height="155" rx="10"/>')
        for y, label, cls in [(142, title, "sym"), (180, line1, "small"), (212, line2, "small"), (242, line3, "small")]:
            b.append(text(x + 18, y, label, cls))
    b.extend(['<path class="flow" d="M170 265 V310 H330"/>',
              '<path class="flow" d="M480 265 V310"/>',
              '<path class="flow" d="M790 265 V310 H630"/>',
              '<rect class="box" x="330" y="288" width="300" height="96" rx="10"/>',
              text(480, 322, "冻结模型 → 生成预测", "sym", "middle"),
              text(480, 352, f'τ̂={fit["tau"]:.1f} s · R̂1={fit["r1_ohm"]*1000:.3f} mΩ', "small", "middle"),
              '<path class="flow" d="M480 384 V429"/>',
              '<rect class="box" x="240" y="435" width="480" height="78" rx="10"/>',
              text(480, 467, "最后打开 C / D 电压，只做评分", "sym", "middle"),
              text(480, 495, "验证电压不回流到 R1、τ、K 或初态", "small", "middle"),
              text(40, 550, "检查办法：换掉验证电压，参数与预测应原样保留；只有分数改变。", "sub"),
              text(40, 581, "共享参数仅是本算例假设；跨温度、老化或真实电芯须重新验证。", "sub")])
    return svg(960, 615, heading, "训练A/B识别R1和时间常数；独立标定给OCV、容量和初态；冻结参数后预测未参与拟合的C/D，最后比较电压评分。", "\n".join(b))


def f11_1_sharing(report: dict | None = None) -> str:
    return validation_contract(report, engineering=True)


def f11_2_loo(report: dict | None = None) -> str:
    report = d11.build_report() if report is None else report
    noisy, mismatch = report["noisy"], report["mismatch"]
    b = [D11_STYLE, text(40, 48, "图 D11-F2　训练很贴，换工况还准吗", "title"),
         text(40, 79, "固定种子 · 电压噪声 σ = 0.1 mV · 全部评分使用 180 s 尾段", "sub")]
    for x, title, value, note in [(40, "训练回代 A / B", noisy["fit"]["rms_mv"], "这些电压参与了拟合"),
                                 (350, "独立预测 C / D", noisy["validation_rmse_mv"], "参数和初态均未重拟"),
                                 (660, "失配验证 C / D", mismatch["validation_rmse_mv"], "验证真值 τ 改为 70 s")]:
        b.append(f'<rect class="box" x="{x}" y="105" width="260" height="124" rx="10"/>')
        b.extend([text(x+18, 137, title, "sym"), text(x+18, 177, f"{value:.3f} mV", "value"), text(x+18, 210, note, "small")])
    b.extend([text(40, 273, "看残差形状：验证脉冲 C（+1.5 A × 15 s）", "sym"),
              text(40, 301, "实测 − 预测；曲线每 5 s 取点展示，RMSE 用全部 0.5 s 采样计算。", "small")])
    x0, y0, pw, ph = 95, 330, 795, 205
    for value in (-.5, 0., 1., 2., 2.5):
        y = y0 + (2.5-value)/3 * ph
        b.append(f'<line class="divider" x1="{x0}" y1="{y}" x2="{x0+pw}" y2="{y}"/>')
        b.append(text(x0-12, y+5, f"{value:.1f}", "small", "end"))
    b.append(text(x0-12, y0-12, "mV", "small", "end"))
    for t in (0, 60, 120, 180):
        x = x0+t/180*pw
        b.append(text(x, y0+ph+26, str(t), "small", "middle"))
    for scene, cls in [(noisy,"curve"),(mismatch,"mismatch")]:
        pts=" ".join(f'{x0+r["t_s"]/180*pw:.2f},{y0+(2.5-r["residual_mv"])/3*ph:.2f}' for r in scene["validation"]["C"]["trace"])
        b.append(f'<polyline class="{cls}" points="{pts}"/>')
    b.extend([text(890, 585, "撤流后时间 / s", "small", "end"),
              '<path class="curve" d="M95 588 H140"/>',text(153,594,"同模型预测", "small"),
              '<path class="mismatch" d="M350 588 H395"/>',text(408,594,"失配后仍用原参数", "small"),
              '<line class="divider" x1="40" y1="620" x2="920" y2="620"/>',
              text(40, 653, f'另一个错误：搬用局部 K → {report["local_k_counterexample"]["transferred_k_rmse_mv"]:.1f} mV', "sym"),
              text(40, 683, "该反例是无噪、同协议、跨 SOC 的 OCV 差；不与上面的带噪实验混算。", "small")])
    return svg(960, 715, "独立预测与失配残差", "训练回代、独立预测与模型失配的RMSE分开列出。验证C的残差曲线显示失配产生系统偏差；旧160mV是单独的局部K搬用反例。", "\n".join(b))


def generate_d11(out: Path, report: dict | None = None) -> None:
    report = d11.build_report() if report is None else report
    out.mkdir(parents=True, exist_ok=True)
    for name, payload in {"D11-F1-sharing-contract.svg": f11_1_sharing(report),
                          "D11-F2-loo-validation.svg": f11_2_loo(report)}.items():
        (out / name).write_text(payload, encoding="utf-8")


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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--unit", choices=("d11", "d12", "all"), default="all")
    parser.add_argument("--out", type=Path, help="自选目录；all 模式分 d11/d12 子目录")
    parser.add_argument("--book-out", type=Path, help="可选主书 SVG 输出目录")
    args = parser.parse_args()
    if args.unit in ("d11", "all"):
        report = d11.build_report()
        out = OUT11 if args.out is None else args.out / "d11" if args.unit == "all" else args.out
        generate_d11(out, report)
        book_out = args.book_out or (ROOT / "bms-book/assets" if args.out is None else None)
        if book_out is not None:
            book_out.mkdir(parents=True, exist_ok=True)
            (book_out / "hppc-validation-contract.svg").write_text(validation_contract(report), encoding="utf-8")
        print(f"D11 figures -> {out}")
    if args.unit in ("d12", "all"):
        out = OUT12 if args.out is None else args.out / "d12" if args.unit == "all" else args.out
        out.mkdir(parents=True, exist_ok=True)
        for name, payload in {"D12-F1-three-errors.svg": f12_1_three_errors(), "D12-F2-calibration.svg": f12_2_calibration()}.items():
            (out / name).write_text(payload, encoding="utf-8")
        print(f"D12 figures -> {out}")


if __name__ == "__main__":
    main()
