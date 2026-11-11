#!/usr/bin/env python3
"""一次性迁移脚本：把单文件 README.md 拆分为 docs/ 源文件树。

拆分规则
--------
* ``# `` (H1) 开启一个新「篇」文件：H1 行 + 到第一个 H2 之前的内容
* ``## `` (H2) 开启一个新页面
* ``## 5.NN ...``（第五篇动画条目）例外：并入第五篇页面，避免 101 个碎文件
* 拆分后按 anchor -> page 映射，把 ``](#x)`` 改写为 ``](page.md#x)``，
  使 docs/ 可直接被 MkDocs 渲染成多页站点且跨页跳转依然有效

产物：docs/*.md（扁平命名，前缀 pN- 表示所属篇）
配套：scripts/build_readme.py 反向拼回 README.md
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
README = ROOT / "README.md"
DOCS = ROOT / "docs"

H1 = re.compile(r"^# ")
H2 = re.compile(r"^## ")
DEMO_H2 = re.compile(r"^## 5\.\d+ ")
ANCHOR_DEF = re.compile(r'<a\s+id="([^"]+)"')
MD_LINK = re.compile(r"\]\(([^)]*?)#([^)/]+)\)")
HTML_HREF = re.compile(r'href="(?:[^"]*/)?#([^"]+)"')
CHAP = re.compile(r"第\s*(\d+)\s*章")
SECT = re.compile(r"^(\d+)\.(\d+)(?:\.(\d+))?")
PART_RE = re.compile(r"^第\s*([一二三四五六七八九十]+)\s*篇")
CN_NUM = "一二三四五六七八九十"

SLUG_FALLBACK = {
    "前言": "preface",
    "如何使用本指南": "how-to-use",
    "读多久：三条时间线": "timeline",
    "按需求找电路（情景导航）": "by-need",
    "必读精选（编辑之选）": "picks",
    "学习路线图": "roadmap",
    "目录": "toc",
    "更新日志": "changelog",
    "致谢": "thanks",
}


def strip_emoji(text: str) -> str:
    return re.sub(r"[\U0001F000-\U0001FAFF\u2600-\u27BF\uFE0F]", "", text).strip()


def slug_for(heading: str, idx: int) -> str:
    body = re.sub(r"^#+\s*", "", heading).strip()
    body = re.sub(r"<a\s+id=[^>]*>.*", "", body).strip()
    m = CHAP.search(body)
    if m:
        return "ch" + m.group(1)
    m = SECT.match(body)
    if m:
        return "s" + "-".join(g for g in m.groups() if g)
    clean = strip_emoji(body)
    for k, v in SLUG_FALLBACK.items():
        if k in clean:
            return v
    m = PART_RE.search(clean)
    if m:
        return "part" + str(CN_NUM.index(m.group(1)) + 1)
    return "sec%02d" % idx


def split_sections(lines):
    sections = []
    cur_head = "__front__"
    cur_body = []

    def flush():
        # 文档若以 H1 开头，首个 front 段为空——丢弃，让标题块成为 index
        if cur_head == "__front__" and not sections and not any(
                ln.strip() for ln in cur_body):
            return
        sections.append((cur_head, cur_body))

    fence = None
    for line in lines:
        marker = re.match(r"^\s{0,3}(`{3,}|~{3,})", line)
        if marker:
            value = marker.group(1)
            if fence is None:
                fence = value
            elif value[0] == fence[0] and len(value) >= len(fence):
                fence = None
            cur_body.append(line)
            continue
        if fence is None and (H1.match(line) or (H2.match(line) and not DEMO_H2.match(line))):
            # Anchors immediately BEFORE a heading belong to the new section.
            # Keeping them in the previous body made valid links open the wrong page.
            boundary = len(cur_body)
            while boundary and (not cur_body[boundary - 1].strip() or
                    re.fullmatch(r'\s*<a\s+id="[^"]+"></a>\s*', cur_body[boundary - 1])):
                boundary -= 1
            anchors = [value for value in cur_body[boundary:] if value.strip()]
            if anchors:
                del cur_body[boundary:]
            flush()
            cur_head = line
            cur_body = anchors + ([""] if anchors else [])
        else:
            cur_body.append(line)
    flush()
    return sections


def build_filenames(sections):
    """首页（文档标题块）= index；正文前导小节归入 p0；各篇从 p1 起编号。"""
    names = []
    part = 0
    idx = 0
    for i, (head, _) in enumerate(sections):
        if i == 0:
            names.append("index")
            part = 0
            idx = 0
            continue
        if H1.match(head):
            part += 1
            idx = 0
            names.append("p%d-%02d-%s" % (part, idx, slug_for(head, idx)))
            continue
        idx += 1
        names.append("p%d-%02d-%s" % (part, idx, slug_for(head, idx)))
    return names


def main():
    if not README.exists():
        print("README.md not found", file=sys.stderr)
        return 1
    lines = README.read_text(encoding="utf-8").split("\n")
    if lines and lines[-1] == "":
        lines.pop()          # 去掉文件末尾换行产生的空项
    sections = split_sections(lines)
    names = build_filenames(sections)

    anchor_map = {}
    pages = {}
    for (head, body), name in zip(sections, names):
        lines_seg = ([head] + body) if head != "__front__" else body
        content = "\n".join(lines_seg)
        pages[name] = content + "\n"
        for a in ANCHOR_DEF.findall(content):
            anchor_map[a] = name

    missing = set()

    def repl_md(m):
        anchor = m.group(2)
        target = anchor_map.get(anchor)
        if target is None:
            missing.add(anchor)
            return m.group(0)
        return "](%s.md#%s)" % (target, anchor)

    def repl_html(m):
        anchor = m.group(1)
        target = anchor_map.get(anchor)
        if target is None:
            missing.add(anchor)
            return m.group(0)
        return 'href="%s.md#%s"' % (target, anchor)

    for name in list(pages):
        c = MD_LINK.sub(repl_md, pages[name])
        c = HTML_HREF.sub(repl_html, c)
        pages[name] = c

    DOCS.mkdir(exist_ok=True)
    for stale in DOCS.glob("*.md"):      # 重跑时清掉旧页面，避免文件名残留
        stale.unlink()
    for name, content in pages.items():
        (DOCS / (name + ".md")).write_text(content, encoding="utf-8", newline="\n")

    print("wrote %d pages to %s" % (len(pages), DOCS))
    if missing:
        print("WARN unresolved anchors: %s" % sorted(missing), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
