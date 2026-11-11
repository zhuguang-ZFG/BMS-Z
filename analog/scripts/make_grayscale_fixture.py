#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""16K 灰度印刷对照夹具。

为什么需要它：全书主风格定为 FF-015 纸雕微距（`reviews/pilot-decision.md`），而纸雕的
斜视角与纸层阴影在单色激光打印上会吃掉明度台阶。ch17 的 24 个点位里 V3 定量图 6 +
V5 流程图 5 = 11 个（46%）正是重灾区，所以批量生成前必须有一张可复跑的对照图。

口径：
- 色值取自上游 handraw-style 色卡的中位像素，不手抄 hex；
- 「16K 打印」近似为 BT.601 灰度 + 5 档量化（暗端并黑、亮端并白）；
- 判读句、坐标轴、刻度与中文一律由本脚本确定性绘制，不经生图模型（规格 §3.3）。

用法：python scripts/make_grayscale_fixture.py [--out DIR] [--check]
  --check 只打印实测对比度并按闸值退出码返回。
"""
from __future__ import annotations

import argparse
import math
import os
import statistics
import sys

from PIL import Image, ImageDraw, ImageFont

# 上游色卡相对路径由安装根解析，项目文件不写绝对路径。
COLOR_SWATCHES_REL = os.path.join("images", "colors")
CJK_FONT_CANDIDATES = [
    os.path.join("build", "fonts-src", "NotoSansCJKsc-Regular.otf"),
    os.path.join("build", "fonts-src", "NotoSansSC-VF.ttf"),
    r"C:/Windows/Fonts/msyh.ttc",
    r"C:/Windows/Fonts/NotoSansCJKsc-Regular.otf",
]

# 已拍板色族（2026-11-05）：纸 C-34 / 墨 C-32 / 阴影 C-35 / 重点 C-26。
PALETTES = {
    "approved": ("C-34", "C-32", "C-35", "C-26"),
    "rejected_slate_as_paper": ("C-35", "C-32", "C-35", "C-26"),
    "current_book": ("C-30", "C-31", "C-31", "C-29"),
}
LABELS = {
    "approved": "A · 已拍板：奶油白纸 / 炭黑墨 / 石板灰阴影 / 柿子橙重点",
    "rejected_slate_as_paper": "B · 石板灰当纸底（上一题字面写法，实测否决）",
    "current_book": "C · 现行全书：象牙白纸 / 佩恩灰墨 / 赭石重点",
}
# 闸值：纸墨必须拉开，否则 16K 印刷不可读。
MIN_PAPER_INK_RATIO = 4.0
MIN_PAPER_ACCENT_RATIO = 3.0

W, H = 640, 420
MARGIN = 56


def upstream_root() -> str:
    """从环境变量或常见安装位置解析 handraw-style 安装根；解析不到即报错，不猜色值。"""
    for env in ("HANDRAW_STYLE_ROOT", "HANDRAW_STYLE_DIR"):
        p = os.environ.get(env)
        if p and os.path.isdir(p):
            return p
    home = os.path.expanduser("~")
    for p in (
        os.path.join(home, ".agents", "skills", "handraw-style"),
        os.path.join(home, ".claude", "skills", "handraw-style"),
    ):
        if os.path.isdir(p):
            return p
    raise SystemExit(
        "找不到 handraw-style 安装根：请设 HANDRAW_STYLE_ROOT 环境变量指向安装目录，"
        "色值必须从上游色卡解析，不允许手抄 hex。"
    )


def swatch_rgb(color_id: str, root: str) -> tuple[int, int, int]:
    path = os.path.join(root, COLOR_SWATCHES_REL, color_id + ".webp")
    path = os.path.normpath(path)
    if not os.path.exists(path):
        raise SystemExit(f"上游色卡缺失：{color_id} -> {path}")
    im = Image.open(path).convert("RGB").resize((32, 32))
    px = list(im.get_flattened_data()) if hasattr(im, "get_flattened_data") else list(im.getdata())
    return tuple(int(statistics.median(c[i] for c in px)) for i in range(3))


def _lin(v: float) -> float:
    return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4


def rel_luminance(rgb) -> float:
    r, g, b = (_lin(c / 255) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def lightness(rgb) -> float:
    y = rel_luminance(rgb)
    return 116 * (y ** (1 / 3)) - 16 if y > 0.008856 else 903.3 * y


def contrast(a, b) -> float:
    ya, yb = rel_luminance(a), rel_luminance(b)
    hi, lo = max(ya, yb), min(ya, yb)
    return (hi + 0.05) / (lo + 0.05)


def cjk_font(size: int) -> tuple[ImageFont.ImageFont, str]:
    for cand in CJK_FONT_CANDIDATES:
        if os.path.exists(cand):
            try:
                return ImageFont.truetype(cand, size), cand
            except OSError:
                continue
    return ImageFont.load_default(), "ascii-fallback（中文会变方框，夹具不可用于判读）"


def draw_panel(rgb_by_role: dict, title: str, fonts) -> Image.Image:
    im = Image.new("RGB", (W, H), rgb_by_role["paper"])
    d = ImageDraw.Draw(im)
    paper, ink, shade, accent = (rgb_by_role[k] for k in ("paper", "ink", "shade", "accent"))
    d.text((MARGIN, 14), title, fill=ink, font=fonts[0][0])
    d.line([(MARGIN, 52), (MARGIN, H - 52), (W - MARGIN, H - 52)], fill=ink, width=3)
    for i in range(1, 9):
        x = MARGIN + (W - 2 * MARGIN) * i / 9
        d.line([(x, 52), (x, H - 52)], fill=shade, width=1)
    for j in range(1, 6):
        y = 52 + (H - 104) * j / 6
        d.line([(MARGIN, y), (W - MARGIN, y)], fill=shade, width=1)
    # 纸雕层阴影块：只做材质与注意力引导，高度不编码任何数值。
    d.polygon([(MARGIN + 40, H - 52), (MARGIN + 130, H - 52),
               (MARGIN + 130, H - 160), (MARGIN + 40, H - 138)], fill=shade)
    for k, (amp, ph) in enumerate([(110, 0.0), (70, 1.1), (40, 2.2)]):
        pts = [(MARGIN + (W - 2 * MARGIN) * t / 100,
                H - 52 - 44 - amp * (1 + math.sin(t / 100 * 2 * math.pi + ph)) / 2)
               for t in range(101)]
        d.line(pts, fill=accent if k == 0 else ink, width=5 if k == 0 else 3)
    d.text((MARGIN, H - 34),
           " ".join("#%02X%02X%02X" % rgb_by_role[r] for r in ("paper", "ink", "shade", "accent")),
           fill=ink, font=fonts[1][0])
    return im


def print16k(im: Image.Image) -> Image.Image:
    g = im.convert("L")
    return g.point(lambda v: min((v // 51) * 51, 255)).convert("RGB")


def build(out_dir: str) -> dict:
    root = upstream_root()
    os.makedirs(out_dir, exist_ok=True)
    fonts = (cjk_font(18), cjk_font(14))
    rows, results = [], {}
    for key, (paper, ink, shade, accent) in PALETTES.items():
        rgb = {r: swatch_rgb(c, root) for r, c in
               zip(("paper", "ink", "shade", "accent"), (paper, ink, shade, accent))}
        ids = dict(zip(("paper", "ink", "shade", "accent"), (paper, ink, shade, accent)))
        color = draw_panel(rgb, LABELS[key], fonts)
        gray = print16k(color)
        name = key.replace("_", "-")
        color.save(os.path.join(out_dir, f"fixture-{name}-color.png"))
        gray.save(os.path.join(out_dir, f"fixture-{name}-print16k.png"))
        rows.append((color, gray))
        results[key] = {
            "color_ids": ids,
            "hex": {r: "#%02X%02X%02X" % v for r, v in rgb.items()},
            "lightness": {r: round(lightness(v), 1) for r, v in rgb.items()},
            "paper_vs_ink": round(contrast(rgb["paper"], rgb["ink"]), 2),
            "paper_vs_shade": round(contrast(rgb["paper"], rgb["shade"]), 2),
            "paper_vs_accent": round(contrast(rgb["paper"], rgb["accent"]), 2),
            "ink_vs_accent": round(contrast(rgb["ink"], rgb["accent"]), 2),
            "shade_vs_accent": round(contrast(rgb["shade"], rgb["accent"]), 2),
        }
    sheet = Image.new("RGB", (W * 2 + 30, H * len(rows) + 90 + 10 * (len(rows) - 1)),
                      (255, 255, 255))
    d = ImageDraw.Draw(sheet)
    big, _ = cjk_font(22)
    d.text((MARGIN, 12), "16K 灰度印刷对照夹具 · 左=彩色原稿 右=单色打印模拟（同一图，确定性绘制）",
           fill=(0, 0, 0), font=big)
    for i, (color, gray) in enumerate(rows):
        y = 60 + i * (H + 10)
        sheet.paste(color, (0, y))
        sheet.paste(gray, (W + 30, y))
    sheet.save(os.path.join(out_dir, "grayscale-fixture-sheet.png"))
    results["_font"] = fonts[0][1]
    results["_out"] = out_dir
    return results


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=os.path.join(
        "docs", "superpowers", "visual", "reviews", "palette-2026-11-05"))
    ap.add_argument("--check", action="store_true", help="只跑闸值判定")
    ap.add_argument("--json", metavar="PATH", help="把实测结果写成 JSON")
    args = ap.parse_args(argv)

    res = build(args.out)
    print(f"字体：{res['_font']}")
    failed = []
    for key, data in res.items():
        if key.startswith("_"):
            continue
        ok = (data["paper_vs_ink"] >= MIN_PAPER_INK_RATIO
              and data["paper_vs_accent"] >= MIN_PAPER_ACCENT_RATIO)
        print(f"{key}: 纸墨 {data['paper_vs_ink']}:1  纸阴影 {data['paper_vs_shade']}:1  "
              f"纸重点 {data['paper_vs_accent']}:1  墨重点 {data['ink_vs_accent']}:1  "
              f"阴影重点 {data['shade_vs_accent']}:1  -> {'PASS' if ok else 'FAIL'}")
        if key == "approved" and not ok:
            failed.append(key)
    if args.json:
        import json
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(res, fh, ensure_ascii=False, indent=2)
        print("JSON:", args.json)
    if failed:
        print("闸值未过：已拍板色族在 16K 灰度下不可读，批量生产保持阻塞。")
        return 1
    print(f"夹具输出：{res['_out']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
