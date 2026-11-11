#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""视觉密度审计：统计每章正文内嵌视觉锚点与无图段长度，并按预算与间距闸判。

口径（与规格书 2026-11-04 基线对齐，冻结在
docs/superpowers/visual/baseline-2026-11-04.json）：
- 视觉锚点 = 正文里实际内嵌的 `<img src="assets/...">` 或 Markdown 图片
  `![alt](assets/...)`。链接、表格、公式、计算器不算锚点。
- 字符 = 章节文件原文的非空白字符（含图片标签、标记符、表格竖线）。
- 正文字符 = 再剥掉 `<figure>` 整块与独立 `<img>` 标签后的非空白字符；
  规格要压的是这一项，`chars` 会随插图增多而变大，两者分开报。
- 无图段 = 相邻两个锚点之间（含章首到首锚点、末锚点到章尾）的非空白字符；
  锚点标签本身不计——量的是读者要读的字，不是标签。

闸（`--gate`）：章视觉数 < 预算、最长无图段 > 1500、H2 段 > 800 字无图、
相邻锚点 < 400 字且中间无三级标题（堆图）→ 退出码 1。
> 1200 字的无图段只警告。报告模式永远退出 0。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
CHAPTER_GLOB = "p*-ch*.md"
# `docs/` 里还有 p0-08-cheatsheet.md、p9-12-changelog.md 这类同前缀非章节文件，
# glob 挡不住，用文件名正则把真正的 `-chNN.md` 挑出来。
CHAPTER_NAME = re.compile(r"-ch(\d+)\.md$")

HARD_MAX_GAP = 1500
WARN_MAX_GAP = 1200
MIN_SPACING = 400
H2_MAX_TEXT = 800

# 规格 §4 每章最低视觉锚点预算。
BUDGETS = {0: 18, 1: 18, 2: 22, 3: 24, 4: 18, 5: 18, 6: 18, 7: 20,
           8: 32, 9: 18, 10: 24, 11: 26, 12: 18, 13: 18, 14: 22,
           15: 24, 16: 18, 17: 18, 18: 18}

FENCE = re.compile(r"^(?:```|~~~).*?^(?:```|~~~)[ \t]*$", re.M | re.S)
COMMENT = re.compile(r"<!--.*?-->", re.S)
# 公式块只用于「不算锚点」的掩码：load() 的正文切片取自原文，所以公式字符照常
# 计入无图段长度，口径不变（`$$` 起于行首才是块级公式，行内 `$x$` 不动）。
FORMULA = re.compile(r"^\$\$.*?\$\$", re.M | re.S)
ANCHOR = re.compile(
    r'<img\b[^>]*\bsrc\s*=\s*["\'](assets/[^"\']+)["\'][^>]*>'
    r"|!\[[^\]]*\]\((assets/[^)]+)\)", re.I)
H2 = re.compile(r"^## ", re.M)
H3 = re.compile(r"^### ", re.M)
HEAD = re.compile(r"^#{2,3} [^\n]*", re.M)
FIGURE_BLOCK = re.compile(r"<figure\b.*?</figure>", re.S | re.I)
IMG_TAG = re.compile(r"<img\b[^>]*>", re.I)


def chapters() -> list[Path]:
    return sorted((p for p in DOCS.glob(CHAPTER_GLOB) if CHAPTER_NAME.search(p.name)),
                  key=chapter_no)


def chapter_no(path: Path) -> int:
    m = CHAPTER_NAME.search(path.name)
    if m is None:
        raise ValueError(f"不是章节文件名：{path.name}")
    return int(m.group(1))


def nonws(text: str) -> int:
    return sum(1 for ch in text if not ch.isspace())


def prose_chars(text: str) -> int:
    """读者要读的正文字符：剥掉 `<figure>` 整块与独立 `<img>` 标签。

    `chars` 含 alt、figcaption 与标签语法，插图越多它越大；规格要压的是正文，
    两个口径分开报，才不会出现「图替了文字、闸反而更红」。
    """
    return nonws(IMG_TAG.sub("", FIGURE_BLOCK.sub("", text)))


def _blank(match: re.Match) -> str:
    """等长空白替换：偏移不变，围栏/注释里的图片不再被当成锚点。"""
    return re.sub(r"\S", " ", match.group(0))


def anchor_matches(raw: str) -> list[tuple[int, int, str]]:
    """锚点在原文里的 (起, 止, 资源路径)。

    围栏、注释与公式块先等长空白化，只用于「不算锚点」的定位；返回的偏移始终是
    原文偏移，调用方可以直接拿去数行号。
    """
    masked = FORMULA.sub(_blank, COMMENT.sub(_blank, FENCE.sub(_blank, raw)))
    return [(m.start(), m.end(), m.group(1) or m.group(2))
            for m in ANCHOR.finditer(masked)]


def mask(raw: str) -> str:
    """锚点标签换成「`\x00` + 等长空格」，其余原文一字不动。

    等长替换让哨兵偏移同时就是原文偏移——`\x00` 后面的空格不是非空白字符，分段计数
    不变（`gaps` 按 `\x00` 切开），但行号可以直接从原文数出来：跨行的 `<figure>`
    不会再把之后的断层行号往上顶。
    """
    out: list[str] = []
    pos = 0
    for start, end, _src in anchor_matches(raw):
        out.append(raw[pos:start])
        out.append("\x00" + re.sub(r"[^\n]", " ", raw[start + 1:end]))
        pos = end
    out.append(raw[pos:])
    return "".join(out)


def scan(raw: str) -> tuple[str, list[tuple[int, str]], int]:
    return (mask(raw), [(start, src) for start, _end, src in anchor_matches(raw)],
            nonws(raw))


def load(path: Path) -> tuple[str, list[tuple[int, str]], int]:
    """返回 (哨兵化原文, 锚点[(原文偏移, 资源路径)], 原文非空白字符数)。

    字符数另按整份原文统计，与 `baseline-2026-11-04.json` 的冻结口径一致。
    """
    return scan(path.read_text(encoding="utf-8"))


def gaps(text: str) -> list[int]:
    return [nonws(part) for part in text.split("\x00")]


def clusters(text: str) -> int:
    """相邻锚点 < 400 字且中间无三级标题 → 堆图。"""
    bad = 0
    for m1, m2 in zip(list(re.finditer(r"\x00", text)),
                      list(re.finditer(r"\x00", text))[1:]):
        middle = text[m1.end():m2.start()]
        if nonws(middle) < MIN_SPACING and not H3.search(middle):
            bad += 1
    return bad


def h2_gaps(text: str) -> list[dict]:
    """二级小节超过 800 字且零锚点 → 失败项。"""
    hits = []
    heads = [m.start() for m in H2.finditer(text)]
    if not heads:
        return hits
    heads.append(len(text))
    for i in range(len(heads) - 1):
        body = text[heads[i]:heads[i + 1]]
        if nonws(body) > H2_MAX_TEXT and "\x00" not in body:
            title = body.splitlines()[0].lstrip("# ").strip()[:40]
            hits.append({"title": title, "chars": nonws(body)})
    return hits


def label(path: Path) -> str:
    """树内文件报相对路径；夹具临时目录报文件名。"""
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.name


def gap_spans(text: str, anchors: list[tuple[int, str]],
              threshold: int = WARN_MAX_GAP) -> list[dict]:
    """超过阈值的无图段：非空白字数、起始行、所属小节、下一张图的资源路径。

    偏移按行号报，不报字符偏移——backlog 要的是「在正文哪一节下刀」，行号能直接
    在编辑器里跳过去，字符偏移不能。`section` 是断层起点之前最近的标题（读者已经
    读完的小节），`section_next` 是断层之内遇到的第一个标题（要下刀的小节）；
    `next_asset` 为 null 表示该段延伸到章尾。
    """
    offsets = [off for off, _src in anchors]
    srcs = [src for _off, src in anchors] + [None]
    lo_bounds = [0] + [off + 1 for off in offsets]
    hi_bounds = offsets + [len(text)]
    heads = [(m.start(), m.group(0).lstrip("#").strip()) for m in HEAD.finditer(text)]
    out = []
    for i, (lo, hi) in enumerate(zip(lo_bounds, hi_bounds)):
        body = text[lo:hi]
        chars = nonws(body)
        if chars <= threshold:
            continue
        section = ""
        section_next = ""
        for pos, title in heads:
            if pos < lo:
                section = title
            elif not section_next:
                section_next = title
                break
        out.append({"chars": chars, "at_line": text.count("\n", 0, lo) + 1,
                    "section": section[:60], "section_next": section_next[:60],
                    "next_asset": srcs[i]})
    return out


def by_kind(assets: list[str]) -> dict:
    """按资源目录分型计数：figures=分析图、photos=实物照片、svg=示意图/动画帧。"""
    kinds = {"figures": 0, "photos": 0, "svg": 0, "other": 0}
    for src in assets:
        parts = src.split("/")
        directory = parts[1].removesuffix("-v2") if len(parts) > 1 else "other"
        kinds[directory if directory in kinds else "other"] += 1
    return kinds


def cluster_spans(text: str, anchors: list[tuple[int, str]]) -> list[dict]:
    """堆图的两端位置与资源名；行号沿用原文，便于编辑定位。"""
    rows = []
    for (left, left_src), (right, right_src) in zip(anchors, anchors[1:]):
        middle = text[left + 1:right]
        if nonws(middle) < MIN_SPACING and not H3.search(middle):
            rows.append({"chars": nonws(middle),
                         "from_line": text.count("\n", 0, left) + 1,
                         "to_line": text.count("\n", 0, right) + 1,
                         "from_asset": left_src, "to_asset": right_src})
    return rows


def h2_coverage(text: str) -> list[dict]:
    """逐 H2 的字数与锚点数，含零视觉的段——报告用，不只报失败项。"""
    heads = [m.start() for m in H2.finditer(text)]
    if not heads:
        return []
    bounds = heads + [len(text)]
    rows = []
    for i in range(len(heads)):
        body = text[bounds[i]:bounds[i + 1]]
        rows.append({"title": body.splitlines()[0].lstrip("# ").strip()[:60],
                     "chars": nonws(body), "visuals": body.count("\x00")})
    return rows


def audit(path: Path, detailed: bool = False) -> dict:
    """detailed=False 保持冻结基线口径逐位一致；断层偏移等只在需要时附加。"""
    raw = path.read_text(encoding="utf-8")
    text, anchors, chars = scan(raw)
    seg = gaps(text)
    n = chapter_no(path)
    out = {
        "file": label(path),
        "chapter": n,
        "chars": chars,
        "prose_chars": prose_chars(raw),
        "visuals": len(anchors),
        "budget": BUDGETS[n],
        "longest_gap": max(seg) if seg else 0,
        "warn_gaps": sum(1 for g in seg if g > WARN_MAX_GAP),
        "hard_gaps": sum(1 for g in seg if g > HARD_MAX_GAP),
        "gaps": seg,
        "clusters": clusters(text),
        "h2_no_visual": h2_gaps(text),
        "assets": [src for _off, src in anchors],
    }
    if detailed:
        out["gap_spans"] = gap_spans(text, anchors)
        out["cluster_spans"] = cluster_spans(text, anchors)
        out["by_kind"] = by_kind([src for _off, src in anchors])
        out["h2_coverage"] = h2_coverage(text)
    return out


def row(r: dict) -> str:
    return (f"ch{r['chapter']:<2} 字符={r['chars']:>6} 视觉={r['visuals']:>3}/"
            f"{r['budget']:<3} 最长无图段={r['longest_gap']:>5} "
            f"警告={r['warn_gaps']:<2} 堆图={r['clusters']:<2} "
            f"H2无图={len(r['h2_no_visual'])}")


def failures(rows: list[dict]) -> list[str]:
    bad = []
    for r in rows:
        tag = r["file"]
        if r["visuals"] < r["budget"]:
            bad.append(f"{tag}: 视觉 {r['visuals']} < 预算 {r['budget']}")
        if r["longest_gap"] > HARD_MAX_GAP:
            bad.append(f"{tag}: 最长无图段 {r['longest_gap']} > {HARD_MAX_GAP}")
        if r["clusters"]:
            bad.append(f"{tag}: {r['clusters']} 处堆图（相邻 < {MIN_SPACING} 字）")
        for h in r["h2_no_visual"]:
            bad.append(f"{tag}: H2「{h['title']}」{h['chars']} 字零视觉")
    return bad


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--gate", action="store_true", help="按预算与间距闸判失败")
    ap.add_argument("--json", type=Path, help="写出完整统计 JSON")
    ap.add_argument("--chapter", type=int, action="append", help="只看某章")
    ap.add_argument("--gaps", action="store_true",
                    help="列出 >1500 字断层的位置、所属小节与下一张图（backlog 定位用）")
    args = ap.parse_args(argv)
    files = chapters()
    if args.chapter:
        files = [f for f in files if chapter_no(f) in set(args.chapter)]
    rows = [audit(f, detailed=args.json is not None or args.gaps) for f in files]
    for r in rows:
        print(row(r))
    if args.gaps:
        for r in rows:
            print(f"\n{r['file']}  ch{r['chapter']}  视觉 {r['visuals']}/{r['budget']}"
                  f"  分型 {r['by_kind']}")
            for g in r["gap_spans"]:
                if g["chars"] <= HARD_MAX_GAP:
                    continue
                nxt = g["next_asset"] or "（章尾）"
                where = g["section_next"] or g["section"]
                print(f"  {g['chars']:>6} 字  行 {g['at_line']:>5}  「{where}」→ {nxt}")
            for c in r["cluster_spans"]:
                print(f"  堆图 {c['chars']} 字  行 {c['from_line']}→{c['to_line']}"
                      f"  {c['from_asset']} → {c['to_asset']}")
    total = sum(r["visuals"] for r in rows)
    print(f"合计：{len(rows)} 章 视觉 {total} 字符 "
          f"{sum(r['chars'] for r in rows)} 正文 "
          f"{sum(r['prose_chars'] for r in rows)}")
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps({"chapters": rows}, ensure_ascii=False,
                                        indent=1) + "\n", encoding="utf-8")
        print(f"JSON → {args.json}")
    if args.gate:
        bad = failures(rows)
        for line in bad:
            print("FAIL " + line)
        print(f"闸：{'FAIL' if bad else 'PASS'}（{len(bad)} 项）")
        return 1 if bad else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
