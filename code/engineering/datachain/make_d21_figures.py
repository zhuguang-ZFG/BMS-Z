#!/usr/bin/env python3
"""Generate D21 figures: record chain from raw identity to aligned, lineage-bound
output (concept, numbers read from d21_record_chain.py)."""

from __future__ import annotations

from html import escape
from pathlib import Path
import importlib.util
import sys

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "d21_record_chain", HERE / "d21_record_chain.py"
)
assert spec is not None and spec.loader is not None
d21 = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = d21
spec.loader.exec_module(d21)

ROOT = HERE.parents[2]
OUT = ROOT / "bms-book" / "engineering" / "assets" / "d21-datachain"

STYLE = """<style>
  .bg { fill: #f6f1e3; }
  .title { fill: #003153; font: 700 20px 'KaiTi','STKaiti','Noto Serif SC',serif; }
  .sub { fill: #5c6d73; font: 13px 'Noto Sans SC','Microsoft YaHei',sans-serif; }
  .lbl { fill: #4d5d63; font: 13px 'Noto Sans SC','Microsoft YaHei',sans-serif; }
  .small { fill: #4d5d63; font: 12px 'Noto Sans SC','Microsoft YaHei',sans-serif; }
  .value { fill: #003153; font: 700 18px 'Noto Sans SC','Microsoft YaHei',sans-serif; }
  .sym { fill: #003153; font: 700 17px 'KaiTi','STKaiti','Noto Serif SC',serif; }
  .chain { stroke: #003153; stroke-width: 2.4; fill: none; stroke-linecap: round; stroke-linejoin: round; }
  .reject { stroke: #a3322a; stroke-width: 2.6; fill: none; stroke-linecap: round; }
  .box { fill: #fbf8f1; stroke: #003153; stroke-width: 2; rx: 8; }
  .box-warn { fill: #fbf8f1; stroke: #a3322a; stroke-width: 2.2; rx: 8; }
  .band { fill: #efe8d8; stroke: #003153; stroke-width: 1.6; rx: 8; }
  .hash { fill: #fbf8f1; stroke: #5c6d73; stroke-width: 1.4; rx: 6; }
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


def f1_record_chain() -> str:
    w, h = 840, 470
    report = d21.build_report(d21.default_records())
    counts = report["counts"]
    raw_n = counts["raw_records"]
    quar_n = counts["quarantined_records"]

    aligned = report["aligned_series"]
    pv40 = next(
        (r for r in aligned if r["field"] == "pack_v" and r["t_ms"] == 40.0), None
    )
    pv200 = next(
        (r for r in aligned if r["field"] == "pack_v" and r["t_ms"] == 200.0), None
    )

    b = [text(40, 40, "图 D21-F1　记录链：从原始身份到可交付对齐", "title")]
    b.append(
        text(
            40,
            64,
            "一条记录先证明自己是哪一次采样，才允许进入曲线；谱系哈希绑定回放，不证明真实硬件",
            "sub",
        )
    )

    # 三站链：原始身份 → 变换/隔离 → 对齐交付
    y = 96
    bh = 132
    bw = 232
    gap = 46
    xs = [40, 40 + bw + gap, 40 + 2 * (bw + gap)]

    b.append(f'<rect class="box" x="{xs[0]}" y="{y}" width="{bw}" height="{bh}" rx="8"/>')
    b.append(text(xs[0] + bw / 2, y + 26, "① 原始身份", "sym", "middle"))
    b.append(text(xs[0] + bw / 2, y + 52, f"{raw_n} 条原始记录", "value", "middle"))
    b.append(text(xs[0] + bw / 2, y + 76, "afe 5 · estimator 3 · firmware 3", "small", "middle"))
    b.append(
        text(xs[0] + bw / 2, y + 100, "七列：source / seq / t / field / raw / unit / quality", "small", "middle")
    )
    b.append(text(xs[0] + bw / 2, y + 120, "缺列、重 seq、时间回退一律拒绝", "small", "middle"))

    b.append(f'<rect class="box" x="{xs[1]}" y="{y}" width="{bw}" height="{bh}" rx="8"/>')
    b.append(text(xs[1] + bw / 2, y + 26, "② 单位防火墙 + 质量隔离", "sym", "middle"))
    b.append(text(xs[1] + bw / 2, y + 52, "51200 mV → 51.2 V", "value", "middle"))
    b.append(text(xs[1] + bw / 2, y + 76, "120 dA → 12.0 A · 6000 pp → 0.60", "small", "middle"))
    b.append(
        text(
            xs[1] + bw / 2,
            y + 100,
            f"invalid {quar_n} 条 → quarantine（estimator seq 3）",
            "small",
            "middle",
        )
    )
    b.append(text(xs[1] + bw / 2, y + 120, "隔离留审计身份，不进对齐", "small", "middle"))

    b.append(f'<rect class="box" x="{xs[2]}" y="{y}" width="{bw}" height="{bh}" rx="8"/>')
    b.append(text(xs[2] + bw / 2, y + 26, "③ 20 ms 对齐网格", "sym", "middle"))
    if pv40:
        b.append(
            text(
                xs[2] + bw / 2,
                y + 52,
                f"pack_v @40 ms：age={pv40['age_ms']:.0f} → 可交付",
                "value",
                "middle",
            )
        )
    if pv200:
        b.append(
            text(
                xs[2] + bw / 2,
                y + 76,
                f"pack_v @200 ms：age={pv200['age_ms']:.0f} → 拒交付",
                "lbl",
                "middle",
            )
        )
    b.append(text(xs[2] + bw / 2, y + 100, "新鲜预算 100 ms；旧值留痕不洗成新值", "small", "middle"))
    b.append(text(xs[2] + bw / 2, y + 120, "degraded 可见但不可交付", "small", "middle"))

    for i in range(2):
        x1 = xs[i] + bw
        x2 = xs[i + 1]
        b.append(
            f'<line class="chain" x1="{x1}" y1="{y + bh / 2}" x2="{x2}" y2="{y + bh / 2}"/>'
        )
        b.append(
            f'<path class="chain" d="M {x2 - 8} {y + bh / 2 - 6} L {x2} {y + bh / 2} L {x2 - 8} {y + bh / 2 + 6}"/>'
        )

    # 谱系带：两个哈希 → 回放判定
    by = 286
    b.append(f'<rect class="band" x="40" y="{by}" width="760" height="140" rx="8"/>')
    b.append(text(60, by + 28, "谱系 lineage：同一份输入 + 同一份变换规则，才允许叫 replay", "sym"))

    hb_y = by + 44
    b.append(f'<rect class="hash" x="60" y="{hb_y}" width="330" height="72" rx="6"/>')
    b.append(text(78, hb_y + 24, "source_sha256", "value"))
    b.append(text(78, hb_y + 46, "= sha256(records.csv 原始字节)", "small"))
    b.append(text(78, hb_y + 64, "默认脚本 = 同一份 CSV 序列化字节", "small"))

    b.append(f'<rect class="hash" x="430" y="{hb_y}" width="330" height="72" rx="6"/>')
    b.append(text(448, hb_y + 24, "config_sha256", "value"))
    b.append(text(448, hb_y + 46, "= sha256(字段单位合同)", "small"))
    b.append(text(448, hb_y + 64, "单位表/范围/grid/预算任一改动即漂移", "small"))

    b.append(
        f'<line class="reject" x1="225" y1="{hb_y + 72}" x2="225" y2="{by + 128}"/>'
    )
    b.append(
        f'<line class="reject" x1="595" y1="{hb_y + 72}" x2="595" y2="{by + 128}"/>'
    )
    b.append(text(420, by + 126, "任一漂移 → 回放 exit 2", "value", "middle"))

    return svg(
        w,
        h,
        "记录链：从原始身份到可交付对齐",
        "原始记录经单位防火墙与质量隔离后进入 20 ms 对齐网格；谱系由 source/config 双哈希绑定回放",
        "\n".join(b),
    )


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    figures = {"D21-F1-record-chain.svg": f1_record_chain()}
    for name, payload in figures.items():
        (OUT / name).write_text(payload, encoding="utf-8")
        print(f"wrote {OUT / name}")


if __name__ == "__main__":
    main()
