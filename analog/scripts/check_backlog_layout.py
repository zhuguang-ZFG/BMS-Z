#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 chapter-backlog 的点位计划套回正文副本，交给审计闸判——验证「计划能落成合法布局」。

审计器只描述现状（哪些段超标、几张图、间距够不够）。backlog 是**尚未执行**的计划：
人写行号，会写错三种东西，而且错得很安静——

1. 插到被替代文字**之前**。审计器只掩掉 `<img>` 标签本身，`figcaption` 照常计入
   阅读字数并落在锚点之后那段里，所以插在前等于原文＋图注一起留在右段，白插。
2. 行号落在段落中间（例如 `<a id>` 占一行、列表连写多行），插进去把一段劈成两半。
3. 在太短的段里塞两张图：段长 571 字，两张图要各自 ≥400 字的间距，物理上不可能。

本脚本按 backlog 的 `insert_after_line` / `delete_lines` 生成占位图（图注固定
`CAPTION_CHARS` 字），写进 `build/tmp/backlog-layout/` 的同名章节文件，再用
`audit_visual_density` 的同一套闸判它。于是 backlog 从「读一遍有信心」变成
可回归的事实：`--check` 不绿就不许进入生成环节。

口径与审计器完全一致（复用 `avd.mask`），所以这里的数字可以直接和
`python scripts/audit_visual_density.py --chapter N --gaps` 对照。
"""
from __future__ import annotations

import argparse
import re
import sys
import tempfile
from pathlib import Path

import audit_visual_density as avd
import yaml

ROOT = Path(__file__).resolve().parents[1]
BACKLOG_DIR = ROOT / "docs" / "superpowers" / "visual" / "chapter-backlog"
CAPTION_CHARS = 120            # 占位图注字数：与真实图注同量级，宁可偏保守
CAPTION_TEXT = "图" * CAPTION_CHARS
RUN_NAME = re.compile(r"^(p\d+-\d+-ch\d+)\.md$")

TABLE_ROW = re.compile(r"^\s*\|")


# ---------------------------------------------------------------- 正文结构
def paragraphs(text: str) -> list[tuple[int, int]]:
    """非空白行的连续段，(起行, 止行)，1-based 含端点。"""
    blocks: list[list[int]] = []
    for i, line in enumerate(text.split("\n"), 1):
        if line.strip():
            if blocks and blocks[-1][1] == i - 1:
                blocks[-1][1] = i
            else:
                blocks.append([i, i])
    return [(b[0], b[1]) for b in blocks]


def anchor_spans(text: str) -> list[tuple[int, int, str]]:
    """既有锚点的 (起行, 止行, 资源路径)。"""
    out = []
    for start, end, src in avd.anchor_matches(text):
        out.append((text.count("\n", 0, start) + 1,
                    text.count("\n", 0, end) + 1, src))
    return out


def baseline_runs(text: str, anchors: list[tuple[int, str]],
                  origin: list[int] | None = None) -> list[dict]:
    """现状（或套用计划后）的无图段：字数、起行、止行、收尾它的锚点（`None` ＝ 章尾）。

    `text` 是 `avd.mask` 之后的哨兵文，偏移即原文偏移，所以行号可数。传入 `origin`
    （`apply_plan_mapped` 的行映射）时，起行/止行折回**正文原始行号**——否则报告里的
    行号是插了占位图之后的模拟行号，人拿去对不上 backlog。
    """
    offsets = [off for off, _src in anchors]
    srcs = [src for _off, src in anchors] + [None]
    n_lines = len(text.split("\n"))
    bounds = [0] + [o + 1 for o in offsets]
    hi = offsets + [len(text)]

    def src_line(off: int) -> int:
        at = min(text.count("\n", 0, off) + 1, n_lines)
        return origin[at - 1] if origin else at

    runs = []
    for i, (lo, top) in enumerate(zip(bounds, hi)):
        runs.append({
            "index": i,
            "chars": avd.nonws(text[lo:top]),
            "start_line": src_line(lo),
            "end_line": src_line(top),
            "next_asset": srcs[i],
        })
    return runs


def run_at(runs: list[dict], line: int) -> dict:
    """插在哪一行落在现状的哪一段里（`target_run` 就是这么算出来的）。"""
    hits = [r for r in runs if r["start_line"] <= line < r["end_line"]]
    return hits[0] if hits else runs[-1]


# ---------------------------------------------------------------- 套用计划
def figure(point_id: str) -> str:
    src = f"assets/figures/{point_id}.svg"
    return (f'<figure><img src="{src}" width="720" alt="{point_id} 占位">'
            f"<figcaption>{CAPTION_TEXT}</figcaption></figure>")


def apply_plan_mapped(text: str, points: list[dict]) -> tuple[str, list[int]]:
    """删掉被替代的行、在 `insert_after_line` 之后落下占位图。

    逐行一次成型（不是逐点位改写），所以点位之间不会互相顶掉行号。
    同时返回 `origin`：模拟文里每一行对应正文的哪一行，供报告折回真实行号。
    """
    lines = text.split("\n")
    deleted: set[int] = set()
    insert_at: dict[int, list[str]] = {}
    for pt in points:
        for rng in pt.get("delete_lines") or []:
            deleted.update(range(rng[0], rng[1] + 1))
        line = pt.get("insert_after_line") or pt.get("at_line")
        insert_at.setdefault(line, []).append(pt["id"])
    out: list[str] = []
    origin: list[int] = []
    for i, line in enumerate(lines, 1):
        if i not in deleted:
            out.append(line)
            origin.append(i)
        if i in insert_at:
            out.append("")
            origin.append(i)
            for pid in insert_at[i]:
                out.append(figure(pid))
                origin.append(i)
                out.append("")
                origin.append(i)
    return "\n".join(out), origin


def apply_plan(text: str, points: list[dict]) -> str:
    return apply_plan_mapped(text, points)[0]


def simulated_text(sim: str) -> str:
    """套用计划后的正文 → 审计器哨兵文（与 `avd.load` 同一口径）。"""
    return avd.mask(sim)


def spacing_conflicts(text: str, origin: list[int] | None = None) -> list[dict]:
    """哨兵文里相邻锚点间隔 < MIN_SPACING 且中间无三级标题 → 堆图，报出两侧行号。"""
    hits = []
    n_lines = len(text.split("\n"))

    def src_line(off: int) -> int:
        at = min(text.count("\n", 0, off) + 1, n_lines)
        return origin[at - 1] if origin else at

    marks = list(re.finditer("\x00", text))
    for m1, m2 in zip(marks, marks[1:]):
        middle = text[m1.end():m2.start()]
        if avd.nonws(middle) < avd.MIN_SPACING and not avd.H3.search(middle):
            hits.append({"between": avd.nonws(middle),
                         "line_a": src_line(m1.start()),
                         "line_b": src_line(m2.start())})
    return hits


# ---------------------------------------------------------------- 落点建议
def line_offsets(text: str) -> list[int]:
    """每一行（1-based）的行首偏移，索引 0 不用。"""
    offs = [0]
    for i, line in enumerate(text.split("\n")):
        offs.append(offs[-1] + len(line) + 1)
    return offs


def cut_candidates(blocks: list[tuple[int, int]], lo: int, hi: int) -> list[int]:
    """段内合法落点：段末行（空行等价于下一段末的前一格，这里只认段末，够用）。"""
    return sorted(e for _s, e in blocks if lo <= e < hi)


def plan_cuts(cum: list[int], lo: int, hi: int, cuts: list[int],
              spacing: int = avd.MIN_SPACING,
              target: int = avd.WARN_MAX_GAP,
              cap: int = CAPTION_CHARS) -> list[int]:
    """把 (lo, hi) 这一段劈成每块 ≤ target 且相邻 ≥ spacing 的落点序列，取最少刀。

    `cum[i]` 是第 i 行之前的累计字数，所以一层的字数＝`cum[b] - cum[a]`。
    图注 `cap` 会加进每一刀的右块，所以劈块时把它算进预算。
    """
    total = cum[hi] - cum[lo]
    for n in range(1, 8):
        step = (total + n * cap) / (n + 1)
        if step > target:
            continue
        chosen: list[int] = []
        prev = lo
        prev_chars = 0
        ok = True
        for k in range(1, n + 1):
            want = cum[lo] + step * k - cap
            pool = [c for c in cuts if c > prev
                    and cum[c] - cum[prev] >= spacing]
            if not pool:
                ok = False
                break
            c = min(pool, key=lambda x: abs(cum[x] - want))
            chosen.append(c)
            prev = c
        if not ok or cum[hi] - cum[prev] < spacing:
            continue
        if any(cum[b] - cum[a] > target for a, b in
               zip([lo] + chosen, chosen + [hi])):
            continue
        return chosen
    return []


def suggest(text: str, runs: list[dict], blocks: list[tuple[int, int]],
            source_lines: list[str],
            only: int = avd.HARD_MAX_GAP) -> list[dict]:
    """逐段给出建议落点（含该行的正文片段，按内容挑选用）。

    累计字数取自哨兵文（`\x00` 换成空格），所以 `<img>` 标签本身不计，而
    `<figure>`／`<figcaption>` 的标记照计——与审计器口径一致；行号仍与正文一一对应。
    """
    cum = [0]
    for line in text.replace("\x00", " ").split("\n"):
        cum.append(cum[-1] + avd.nonws(line))
    out = []
    for r in runs:
        if r["chars"] <= only:
            continue
        lo, hi = r["start_line"], r["end_line"]
        items = []
        for c in plan_cuts(cum, lo, hi, cut_candidates(blocks, lo + 1, hi)):
            snippet = source_lines[c - 1].strip()[:46] if 0 < c <= len(source_lines) else ""
            items.append({"line": c, "left": cum[c] - cum[lo],
                          "right": cum[hi] - cum[c], "text": snippet})
        out.append({"run": r, "cuts": items})
    return out


# ---------------------------------------------------------------- 合法性
def check_point(point: dict, blocks: list[tuple[int, int]], n_lines: int,
                anchors: list[tuple[int, int, str]] = ()) -> list[str]:
    pid = point.get("id", "?")
    problems: list[str] = []
    line = point.get("insert_after_line")
    ranges = [tuple(r) for r in point.get("delete_lines") or []]

    if line is None:
        return [f"{pid}: 缺 insert_after_line"]
    if not 1 <= line <= n_lines:
        problems.append(f"{pid}: insert_after_line {line} 越界（正文 {n_lines} 行）")
    elif not _is_boundary(line, blocks):
        problems.append(f"{pid}: 行 {line} 落在段落中间，插进去会把一段劈成两半")

    for s, e in ranges:
        if not (1 <= s <= e <= n_lines):
            problems.append(f"{pid}: delete_lines [{s},{e}] 越界")
            continue
        inside = [b for b in blocks if b[0] <= e and s <= b[1]]
        partial = [b for b in inside if not (s <= b[0] and b[1] <= e)]
        if partial:
            b = partial[0]
            problems.append(f"{pid}: delete_lines [{s},{e}] 切到段 {b[0]}–{b[1]} 中间")
        for ln in range(s, e + 1):
            for a0, a1, src in anchors:
                if a0 <= ln <= a1:
                    problems.append(f"{pid}: delete_lines [{s},{e}] 删掉了既有锚点 {src}")
                    break

    if ranges:
        last_end = max(e for _s, e in ranges)
        if line < last_end:
            problems.append(
                f"{pid}: 插在被替代文字之前（图注会把右段撑回去，见 gates."
                f"anchor_after_replaced_text）")
    return problems


def _is_boundary(line: int, blocks: list[tuple[int, int]]) -> bool:
    """段末或空行都算合法落点；段起与段中不算。"""
    if any(s <= line <= e for s, e in blocks):
        return any(e == line for _s, e in blocks)
    return True


def duplicate_inserts(points: list[dict]) -> list[tuple[int, list[str]]]:
    seen: dict[int, list[str]] = {}
    for pt in points:
        line = pt.get("insert_after_line")
        if line is not None:
            seen.setdefault(line, []).append(pt["id"])
    return [(line, ids) for line, ids in sorted(seen.items()) if len(ids) > 1]


def is_executable(point: dict) -> bool:
    """action: new 且 status 是 planned（省略即 planned）才套用；deferred 只登记不执行。"""
    return point.get("action") == "new" and point.get("status", "planned") == "planned"


def duplicate_deletes(points: list[dict]) -> list[tuple[int, list[str]]]:
    """同一正文行被两个点位当成「被本图替代的文字」——一段文字不能删两次。"""
    owner: dict[int, str] = {}
    pairs: dict[tuple[str, ...], int] = {}
    for pt in points:
        for s, e in pt.get("delete_lines") or []:
            for ln in range(s, e + 1):
                prev = owner.get(ln)
                if prev is not None and prev != pt["id"]:
                    key = tuple(sorted({prev, pt["id"]}))
                    pairs.setdefault(key, ln)
                owner.setdefault(ln, pt["id"])
    return [(ln, list(ids)) for ids, ln in sorted(pairs.items())]


# ---------------------------------------------------------------- 汇总
def load_backlog(path: Path) -> dict:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as e:
        where = getattr(e, "problem_mark", None)
        spot = f"（行 {where.line + 1}）" if where else ""
        raise SystemExit(f"{path.name}: YAML 解析失败{spot}——"
                         f"以「」或单引号包住以引号开头的条目") from e
    if "points" not in data:
        raise SystemExit(f"{path.name}: backlog 缺 points")
    return data


def verify(backlog_path: Path, source_path: Path | None = None) -> dict:
    data = load_backlog(backlog_path)
    source = source_path or ROOT / data["source"]
    raw = source.read_text(encoding="utf-8")
    blocks = paragraphs(raw)
    n_lines = len(raw.split("\n"))
    anchors = anchor_spans(raw)
    text, offs, _chars = avd.load(source)
    runs = baseline_runs(text, offs)

    planned: list[dict] = []
    problems: list[str] = []
    for pt in data["points"]:
        if pt.get("action") != "new":
            continue
        if not is_executable(pt):
            if not (pt.get("blocked_by") or pt.get("defer_reason")):
                problems.append(
                    f"{pt['id']}: status {pt.get('status')} 不套用，但没写 "
                    f"blocked_by / defer_reason 说明它为什么落不下")
            continue
        bad = check_point(pt, blocks, n_lines, anchors)
        if bad:
            problems.extend(bad)
            continue
        got = run_at(runs, pt["insert_after_line"])
        want = pt.get("target_run")
        if want is not None and abs(got["chars"] - int(want)) > 40:
            problems.append(f"{pt['id']}: target_run {want} 实为 {got['chars']}"
                            f"（行 {pt['insert_after_line']} 落在段 {got['index']}）")
        planned.append(pt)
    for line, ids in duplicate_inserts(planned):
        problems.append(f"{'/'.join(ids)}: 同一行 {line} 落两个点位（必判堆图）")
    for line, ids in duplicate_deletes(planned):
        problems.append(f"{'/'.join(ids)}: 行 {line} 被两个点位同时当作替代文字")

    sim, origin = apply_plan_mapped(raw, planned)
    tmp = Path(tempfile.mkdtemp()) / source.name
    tmp.write_text(sim, encoding="utf-8")
    audit = avd.audit(tmp, detailed=True)
    sim_text, sim_anchors, _ = avd.load(tmp)
    return {
        "backlog": backlog_path.name,
        "source": source.as_posix(),
        "chapter": data.get("chapter"),
        "baseline_runs": runs,
        "planned": len(planned),
        "planned_ids": [pt["id"] for pt in planned],
        "new_points": sum(1 for pt in data["points"] if pt.get("action") == "new"),
        "problems": problems,
        "spacing_conflicts": spacing_conflicts(sim_text, origin),
        "simulated_runs": baseline_runs(sim_text, sim_anchors, origin),
        "unplaced": [pt["id"] for pt in data["points"]
                     if is_executable(pt) and pt["id"] not in
                     {p["id"] for p in planned}],
        "deferred": [pt["id"] for pt in data["points"]
                     if pt.get("action") == "new" and not is_executable(pt)],
        "audit": audit,
        "failures": avd.failures([audit]),
    }


def suggestions(backlog_path: Path, source_path: Path | None = None,
                only: int = avd.HARD_MAX_GAP) -> list[dict]:
    """按现状断层给建议落点——backlog 的行号从这里来，不靠手算。"""
    data = load_backlog(backlog_path)
    source = source_path or ROOT / data["source"]
    raw = source.read_text(encoding="utf-8")
    text, offs, _ = avd.load(source)
    return suggest(text, baseline_runs(text, offs), paragraphs(raw),
                   raw.split("\n"), only)


# ---------------------------------------------------------------- CLI
def report(v: dict, show_all_runs: bool = False) -> None:
    print(f"\n=== {v['backlog']} → {v['source']}（新增点位 {v['planned']}"
          f"/{v['new_points']} 个套用"
          + (f"，{len(v['deferred'])} 个 deferred" if v["deferred"] else "") + "）")
    if v["problems"]:
        print("  计划本身:")
        for p in v["problems"]:
            print(f"    BAD {p}")
    if v["unplaced"]:
        print("    未套用（因上述 BAD）：" + "、".join(v["unplaced"]))
    if v["spacing_conflicts"]:
        print("  堆图:")
        for c in v["spacing_conflicts"]:
            print(f"    行 {c['line_a']}→{c['line_b']} 间隔 {c['between']} 字"
                  f"（< {avd.MIN_SPACING}）")
    a = v["audit"]
    print(f"  套用后: 视觉 {a['visuals']}/{a['budget']} 最长段 {a['longest_gap']}"
          f" 警告段 {a['warn_gaps']} 硬超 {a['hard_gaps']} 堆图 {a['clusters']}"
          f" H2无图 {len(a['h2_no_visual'])}")
    rows = v["simulated_runs"] if show_all_runs else [
        r for r in v["simulated_runs"] if r["chars"] > avd.WARN_MAX_GAP]
    for r in rows:
        flag = ("HARD" if r["chars"] > avd.HARD_MAX_GAP
                else "warn" if r["chars"] > avd.WARN_MAX_GAP else "ok  ")
        print(f"    {flag} {r['chars']:>5} 字 正文行 {r['start_line']:>4}"
              f"–{r['end_line']:>4} → {r['next_asset'] or '（章尾）'}")
    for f in v["failures"]:
        print("  FAIL " + f)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--backlog", type=Path, action="append",
                    help="指定 backlog yml（默认 chapter-backlog/ch*.yml 全部）")
    ap.add_argument("--check", action="store_true",
                    help="有任何计划问题或闸失败即退出 1（默认为报告模式，退出 0）")
    ap.add_argument("--suggest", action="store_true",
                    help="按现状断层打印建议落点与该行正文，用于修订 backlog 行号")
    ap.add_argument("--warn", action="store_true", help="--suggest 时也列 >1200 的段")
    ap.add_argument("--all", action="store_true", help="套用后逐段全列，不只超警告线的")
    args = ap.parse_args(argv)
    paths = args.backlog or sorted(BACKLOG_DIR.glob("ch*.yml"))
    if args.suggest:
        only = avd.WARN_MAX_GAP if args.warn else avd.HARD_MAX_GAP
        stuck = 0
        for p in paths:
            for s in suggestions(p, only=only):
                r = s["run"]
                print(f"\n{p.name} 段 {r['index']}：{r['chars']} 字 正文行 "
                      f"{r['start_line']}–{r['end_line']} → "
                      f"{r['next_asset'] or '（章尾）'}")
                if not s["cuts"]:
                    print("    无合法劈法（段里没有足够的合格段末落点）——登记 open_decision")
                    stuck += 1
                for c in s["cuts"]:
                    print(f"    插 行 {c['line']:>4}（左 {c['left']:>4} / 右 "
                          f"{c['right']:>4}＋{CAPTION_CHARS} 图注）｜{c['text']}")
        print(f"\n无解段 {stuck} 处")
        return 0
    bad = 0
    for p in paths:
        v = verify(p)
        report(v, show_all_runs=args.all)
        bad += len(v["problems"]) + len(v["failures"]) + len(v["spacing_conflicts"])
    print(f"\n合计 {len(paths)} 份 backlog，{bad} 项待修")
    return 1 if (args.check and bad) else 0


if __name__ == "__main__":
    sys.exit(main())
