#!/usr/bin/env python3
"""按小节度量中文正文的可读性，定位最该改写的段落。

只做度量与报告，不改文件、不做闸。阈值出处与改写规则见
docs/superpowers/specs/language-style.md。

用法：
    python scripts/audit_readability.py                     # 全书排行
    python scripts/audit_readability.py --top 20            # 最差 20 节
    python scripts/audit_readability.py --chapter 6         # 只看第 6 章
    python scripts/audit_readability.py --section 6.3       # 单节明细（列出超长句）
    python scripts/audit_readability.py --json out.json     # 导出
"""
from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass, field, asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"

# 一句话的收尾标点（中文句末 + 分号）
SENTENCE_END = "。！？；"
# 读到这些就算从句边界，用来数「一句里塞了几个转折」
CLAUSE_MARK = "，、：——…"

# 告警线：本书是硬核教材，60 字算「长」、90 字算「很长」，作为分流工作线。
LONG = 60
VERY_LONG = 90
# 硬限：含逗号长句 ≤100 字，出自 ruanyf/document-style-guide text.md。
# 见 docs/superpowers/specs/language-style.md。
HARD_LIMIT = 100
# 一句里超过这么多从句就难跟
MAX_CLAUSES = 5

HEADING = re.compile(r"^(#{2,4})\s+(.*?)\s*$")
SECTION_NO = re.compile(r"^(\d+\.\d+(?:\.\d+)?)\s")


def strip_noise(text: str) -> str:
    """去掉代码块、HTML、公式、表格、图片行——这些不该参与句长统计。"""
    text = re.sub(r"```.*?```", " ", text, flags=re.S)
    text = re.sub(r"~~~.*?~~~", " ", text, flags=re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\$\$.*?\$\$", " 公式 ", text, flags=re.S)
    text = re.sub(r"\$[^$\n]+\$", " 公式 ", text)
    text = re.sub(r"`[^`\n]+`", " 符号 ", text)
    out = []
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("|") or s.startswith(">") or s.startswith("!["):
            continue
        if re.match(r"^[-*+]\s", s) or re.match(r"^\d+[.)]\s", s):
            s = re.sub(r"^[-*+]\s|^\d+[.)]\s", "", s)
        out.append(s)
    return "\n".join(out)


def sentences(text: str) -> list[str]:
    buf, res = [], []
    for ch in text:
        if ch in "\n\r":
            if buf:
                res.append("".join(buf))
                buf = []
            continue
        buf.append(ch)
        if ch in SENTENCE_END:
            res.append("".join(buf))
            buf = []
    if buf:
        res.append("".join(buf))
    cleaned = []
    for s in res:
        s = re.sub(r"\s+", "", s)
        # 只统计含中文的句子；纯参数行/英文型号行不算
        if len(s) >= 8 and re.search(r"[\u4e00-\u9fff]", s):
            cleaned.append(s)
    return cleaned


def clause_count(s: str) -> int:
    return sum(1 for ch in s if ch in CLAUSE_MARK) + 1


@dataclass
class Section:
    file: str
    number: str
    title: str
    line: int
    chars: int = 0
    n_sent: int = 0
    long_sent: int = 0
    very_long: int = 0
    over_hard: int = 0
    multi_clause: int = 0
    max_len: int = 0
    mean_len: float = 0.0
    worst: list[str] = field(default_factory=list)

    @property
    def long_ratio(self) -> float:
        return self.long_sent / self.n_sent if self.n_sent else 0.0

    @property
    def score(self) -> float:
        """越高越该改。长句占比为主，很长句与多从句句加权。"""
        if not self.n_sent:
            return 0.0
        return round(
            100 * self.long_ratio
            + 60 * self.very_long / self.n_sent
            + 40 * self.multi_clause / self.n_sent,
            1,
        )


def parse_file(path: Path) -> list[Section]:
    raw = path.read_text(encoding="utf-8")
    lines = raw.splitlines()
    marks: list[tuple[int, str, str]] = []
    in_fence = False
    for i, line in enumerate(lines):
        if line.strip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        m = HEADING.match(line)
        if m and len(m.group(1)) == 3:
            title = m.group(2)
            num = SECTION_NO.match(title)
            marks.append((i, num.group(1) if num else "", title))
    out = []
    for idx, (start, num, title) in enumerate(marks):
        end = marks[idx + 1][0] if idx + 1 < len(marks) else len(lines)
        body = strip_noise("\n".join(lines[start + 1 : end]))
        sec = Section(file=path.name, number=num, title=title, line=start + 1)
        ss = sentences(body)
        sec.chars = sum(len(s) for s in ss)
        sec.n_sent = len(ss)
        if ss:
            lens = [len(s) for s in ss]
            sec.max_len = max(lens)
            sec.mean_len = round(sum(lens) / len(lens), 1)
            sec.long_sent = sum(1 for n in lens if n > LONG)
            sec.very_long = sum(1 for n in lens if n > VERY_LONG)
            sec.over_hard = sum(1 for n in lens if n > HARD_LIMIT)
            sec.multi_clause = sum(1 for s in ss if clause_count(s) > MAX_CLAUSES)
            sec.worst = sorted(ss, key=len, reverse=True)[:3]
        out.append(sec)
    return out


def chapter_files(chapter: int | None) -> list[Path]:
    files = sorted(DOCS.glob("p*-ch*.md"))
    if chapter is None:
        return files
    tag = f"ch{chapter}.md"
    return [f for f in files if f.name.endswith(tag)]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--top", type=int, default=15)
    ap.add_argument("--chapter", type=int)
    ap.add_argument("--section")
    ap.add_argument("--json", type=Path)
    ap.add_argument("--min-sentences", type=int, default=6,
                    help="句子太少的节不参与排行，默认 6")
    args = ap.parse_args(argv)

    secs: list[Section] = []
    for f in chapter_files(args.chapter):
        secs.extend(parse_file(f))

    if args.section:
        hit = [s for s in secs if s.number == args.section]
        if not hit:
            print(f"未找到小节 {args.section}")
            return 1
        for s in hit:
            print(f"{s.file}:{s.line}  §{s.number} {s.title}")
            print(f"  句数 {s.n_sent}  均长 {s.mean_len}  最长 {s.max_len}"
                  f"  >{LONG}字 {s.long_sent}  >{VERY_LONG}字 {s.very_long}"
                  f"  破硬限{HARD_LIMIT} {s.over_hard}"
                  f"  从句>{MAX_CLAUSES} {s.multi_clause}  分数 {s.score}")
            for w in s.worst:
                print(f"  [{len(w)}字/{clause_count(w)}从句] {w}")
        return 0

    rank = [s for s in secs if s.n_sent >= args.min_sentences]
    rank.sort(key=lambda s: s.score, reverse=True)

    tot_sent = sum(s.n_sent for s in secs)
    tot_long = sum(s.long_sent for s in secs)
    tot_vl = sum(s.very_long for s in secs)
    tot_hard = sum(s.over_hard for s in secs)
    tot_mc = sum(s.multi_clause for s in secs)
    print(f"小节 {len(secs)}（入排行 {len(rank)}）  句子 {tot_sent}")
    print(f"长句(>{LONG}字) {tot_long} = {100*tot_long/tot_sent:.1f}%   "
          f"很长(>{VERY_LONG}字) {tot_vl} = {100*tot_vl/tot_sent:.1f}%   "
          f"多从句(>{MAX_CLAUSES}) {tot_mc} = {100*tot_mc/tot_sent:.1f}%")
    print(f"破硬限(>{HARD_LIMIT}字，ruanyf 规范) {tot_hard} = "
          f"{100*tot_hard/tot_sent:.1f}%")
    print()
    print(f"{'分数':>6}  {'节':<9} {'句':>4} {'均长':>5} {'最长':>5} "
          f"{'长':>3} {'很长':>4} {'从句':>4}  标题")
    for s in rank[: args.top]:
        print(f"{s.score:>6}  {s.number or '-':<9} {s.n_sent:>4} {s.mean_len:>5} "
              f"{s.max_len:>5} {s.long_sent:>3} {s.very_long:>4} "
              f"{s.multi_clause:>4}  {s.title[:34]}")

    if args.json:
        payload = {
            "thresholds": {"long": LONG, "very_long": VERY_LONG,
                           "hard_limit": HARD_LIMIT,
                           "max_clauses": MAX_CLAUSES},
            "totals": {"sections": len(secs), "sentences": tot_sent,
                       "long": tot_long, "very_long": tot_vl,
                       "multi_clause": tot_mc, "over_hard": tot_hard},
            "sections": [asdict(s) | {"score": s.score,
                                      "long_ratio": round(s.long_ratio, 3)}
                         for s in secs],
        }
        args.json.write_text(json.dumps(payload, ensure_ascii=False, indent=2),
                             encoding="utf-8")
        print(f"\n→ {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
