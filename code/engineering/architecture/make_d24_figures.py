#!/usr/bin/env python3
"""Generate D24 figure: who checks what — audit coverage layers.

Static responsibility map (no numeric inputs): the four layers are disjoint by
design, which is the chapter's core teaching point — D24 never re-checks what
the gate or the builder already proves, it covers what they cannot see.
"""

from __future__ import annotations

from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE.parents[2] / "bms-book" / "engineering" / "assets" / "d24-architecture"

STYLE = """<style>
  .bg { fill: #f6f1e3; }
  .title { fill: #003153; font: 700 20px 'KaiTi','STKaiti','Noto Serif SC',serif; }
  .sub { fill: #5c6d73; font: 13px 'Noto Sans SC','Microsoft YaHei',sans-serif; }
  .layer { fill: #fbf8f1; stroke: #003153; stroke-width: 1.8; }
  .layername { fill: #003153; font: 700 15px 'Noto Sans SC','Microsoft YaHei',sans-serif; }
  .scope { fill: #a3322a; font: 700 12px 'Noto Sans SC','Microsoft YaHei',sans-serif; }
  .item { fill: #4d5d63; font: 13px 'Noto Sans SC','Microsoft YaHei',sans-serif; }
  .out { fill: #fbf8f1; stroke: #a3322a; stroke-width: 1.8; }
  .outname { fill: #a3322a; font: 700 14px 'Noto Sans SC','Microsoft YaHei',sans-serif; }
  .arrow { stroke: #003153; stroke-width: 1.8; fill: none; marker-end: url(#head); }
  .foot { fill: #5c6d73; font: 12px 'Noto Sans SC','Microsoft YaHei',sans-serif; }
</style>"""

LAYERS = [
    ("check_engineering 门", "逐条 · 每次提交", [
        "证据名解析（evidence → 测试 def）",
        "锚点指纹 / 单元源指纹",
        "source_id 必须在采用表",
        "图版文件存在且在教学区可见",
    ]),
    ("build_engineering 装配", "装配子集 · 构建时", [
        "装配单元拓扑排序 + 无环",
        "登记回写（指纹/计数）",
        "计划态单元不阻塞装配",
    ]),
    ("D24 audit_registry", "全图含计划态 · R1–R6", [
        "R1 先修引用闭合 / R2 全图无环",
        "R3 证据与来源双空 = ungrounded",
        "R4/R5 实验与图版工件独立复算",
        "R6 planned 阻塞 verified = warning",
    ]),
    ("protocol_self_check", "对外方法 · 六问", [
        "每问 path + must_contain 真核验",
        "冻结开源快照 SHA-256 钉住",
        "空目录 / 篡改 / 换快照 = fail",
    ]),
]


def build_svg() -> str:
    width, height = 960, 620
    band_x, band_w = 60, 560
    out_x, out_w = 700, 220
    top = 92
    band_h, gap = 96, 26
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" font-family="sans-serif">',
        "<title>审读分层：谁证明什么，谁看不见什么</title>",
        "<desc>四层职责图：check_engineering 门逐条校验、build 装配只看装配子集、D24 审计器查全图 R1-R6、协议核验六问加快照钉；输出 findings/verdict 与前向追溯矩阵；全绿不授予产品资质。</desc>",
        '<defs><marker id="head" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto">'
        '<path d="M0,0 L8,4 L0,8 z" fill="#003153"/></marker></defs>',
        STYLE,
        f'<rect class="bg" x="0" y="0" width="{width}" height="{height}"/>',
        '<text class="title" x="60" y="42">审读分层：谁证明什么，谁看不见什么</text>',
        '<text class="sub" x="60" y="66">四层各司其职、互不重复；D24 只补门与构建器视野之外的洞。数字出处：E17 冻结（D24.6）。</text>',
    ]
    for i, (name, scope, items) in enumerate(LAYERS):
        y = top + i * (band_h + gap)
        parts.append(f'<rect class="layer" x="{band_x}" y="{y}" width="{band_w}" height="{band_h}" rx="8"/>')
        parts.append(f'<text class="layername" x="{band_x + 16}" y="{y + 24}">{name}</text>')
        parts.append(f'<text class="scope" x="{band_x + band_w - 190}" y="{y + 24}">{scope}</text>')
        for j, item in enumerate(items):
            col = j % 2
            row = j // 2
            parts.append(
                f'<text class="item" x="{band_x + 16 + col * 276}" y="{y + 50 + row * 22}">· {item}</text>'
            )
        mid = y + band_h / 2
        parts.append(f'<path class="arrow" d="M{band_x + band_w + 4},{mid:.0f} L{out_x - 8},{mid:.0f}"/>')
    # right output column
    outs = [("findings + verdict", "审计报告：0 error 才算 pass"), ("traceability_matrix.json", "每条 active claim 一行，缺口不藏")]
    for k, (name, desc) in enumerate(outs):
        y = top + 60 + k * 150
        parts.append(f'<rect class="out" x="{out_x}" y="{y}" width="{out_w}" height="64" rx="8"/>')
        parts.append(f'<text class="outname" x="{out_x + 14}" y="{y + 26}">{name}</text>')
        parts.append(f'<text class="item" x="{out_x + 14}" y="{y + 48}">{desc}</text>')
    parts.append(
        '<text class="foot" x="60" y="568">边界：四层全部通过也只证明登记自洽，不授予产品资质；SRC01/SRC06（待补）与 UDS/HIL 实车验收各自闭合前无产品结论。</text>'
    )
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    target = OUT / "D24-F1-audit-layers.svg"
    target.write_text(build_svg(), encoding="utf-8")
    print(f"wrote {target}")


if __name__ == "__main__":
    main()
