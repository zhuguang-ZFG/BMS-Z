#!/usr/bin/env python3
"""为每一章生成一张 3:4「一句话」结论卡（SPEC R4 的「每章 3:4 结论卡」）。

内容全部取自书稿本身，不新增事实：
- 章标题：H1 去掉「第 N 章」前缀；
- 一句话：本章第一个 `::: principle 一句话` 块里的第一句加粗结论；
  没有加粗时取该块第一句；第 30 章没有 principle 块，退回 `::: trap 坑`
  的第一句（同为书稿原文，不新写）；
- 三个小节：本章前三个 `## ` 标题，去掉「N.M」编号。

产物：docs/public/spread/cards/chapters/xhs-NN.png（1080×1440）

用法：
    python tools/spread/build_chapter_cards.py [--validate]
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from spread_css import TASK_CSS  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
BOOK = ROOT / "bms-book" / "book"
OUT_DIR = ROOT / "docs" / "public" / "spread" / "cards" / "chapters"
PAGE = ROOT / "docs" / "传播材料.md"
PAGE_BEGIN = "<!-- CHAPTER_CARDS:BEGIN -->"
PAGE_END = "<!-- CHAPTER_CARDS:END -->"
SKILL_DIR = Path(
    __import__("os").environ.get(
        "GUIZANG_SOCIAL_SKILL",
        Path.home() / ".agents" / "skills" / "guizang-social-card-skill",
    )
)

CHAPTER_RE = re.compile(r"^(\d{2})-(.+)\.md$")
PRINCIPLE_RE = re.compile(r"::: principle[^\n]*\n(.*?)\n:::", re.S)
TRAP_RE = re.compile(r"::: trap[^\n]*\n(.*?)\n:::", re.S)


def clean(text: str) -> str:
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    return re.sub(r"\s+", " ", text).strip()


def first_sentence(text: str) -> str:
    m = re.match(r"^(.*?[。！？])", text)
    return (m.group(1) if m else text).strip()


def parse_chapter(path: Path) -> dict | None:
    m = CHAPTER_RE.match(path.name)
    if not m:
        return None
    no = int(m.group(1))
    body = path.read_text(encoding="utf-8")

    h1 = re.search(r"^# (.+)$", body, re.M)
    if not h1:
        return None
    title = re.sub(r"^第\s*\d+\s*章\s*", "", h1.group(1)).strip()

    block = PRINCIPLE_RE.search(body)
    if block:
        text = block.group(1).strip()
        bold = re.search(r"\*\*(.+?)\*\*", text, re.S)
        line = clean(bold.group(1) if bold else first_sentence(clean(text)))
    else:
        trap = TRAP_RE.search(body)
        if not trap:
            return None
        line = first_sentence(clean(trap.group(1)))
    if not line:
        return None

    sections = []
    for h2 in re.findall(r"^## (.+)$", body, re.M):
        name = re.sub(r"^\d+(?:\.\d+)*\s*", "", h2).strip()
        if name and name not in {"练习", "参考资料", "本章练习", "小结"}:
            sections.append(name)
        if len(sections) == 3:
            break
    if len(sections) < 3:
        return None
    stats = {
        "sections": len(re.findall(r"^## ", body, re.M)),
        # 书稿不内联图片，图由构建期从图号注册表插入；这里数本章引用的不同图号。
        "figures": len(set(re.findall(rf"图\s*{no}-\d+", body))),
        "labs": len(re.findall(r"^::: lab", body, re.M)),
    }
    return {"no": no, "title": title, "line": line, "sections": sections, "stats": stats, "path": path}


def poster(ch: dict) -> str:
    tight = " bms-tight" if len(ch["title"]) > 14 else ""
    rows = "\n".join(
        f'          <div class="bms-row"><span class="bms-idx">0{i}</span>'
        f'<span class="bms-item">{s}</span></div>'
        for i, s in enumerate(ch["sections"], start=1)
    )
    return f"""    <section class="poster xhs" id="xhs-{ch['no']:02d}">
      <canvas class="mag-bg" data-bg="ink-flow"></canvas>
      <div class="grain"></div>
      <div class="content stack gap-3">
        <div class="issue-row">
          <span>BMS-Z · 第 {ch['no']} 章</span><span class="dot"></span><span>一句话</span>
        </div>
        <p class="kicker">这一章，只记一句</p>
        <h2 class="h-xl{tight}">{ch['title']}</h2>
        <p class="bms-line">{ch['line']}</p>
        <div class="bms-outline">
{rows}
        </div>
        <div class="bms-stats">
          <span><b>{ch['stats']['sections']}</b>小节</span>
          <span><b>{ch['stats']['figures']}</b>张图</span>
          <span><b>{ch['stats']['labs']}</b>个实验</span>
        </div>
      </div>
      <div class="issue-strip">
        <span>BMS-Z 电池管理系统</span>
        <span>第 {ch['no']} 章</span>
      </div>
    </section>
"""


def write_page(chapters: list[dict]) -> None:
    """把 32 行表格写进 docs/传播材料.md 的标记块，页面其它部分保持人手写。"""
    if not PAGE.exists():
        print(f"  跳过页面表格：{PAGE.name} 不存在")
        return
    rows = ["| 章 | 标题 | 卡 |", "|---:|---|---|"]
    for ch in chapters:
        name = f"xhs-{ch['no']:02d}.png"
        rows.append(
            f"| {ch['no']} | {ch['title']} | "
            f"[{name}](/spread/cards/chapters/{name}) |"
        )
    text = PAGE.read_text(encoding="utf-8")
    start = text.index(PAGE_BEGIN) + len(PAGE_BEGIN)
    end = text.index(PAGE_END)
    PAGE.write_text(text[:start] + "\n" + "\n".join(rows) + "\n" + text[end:], encoding="utf-8")
    print(f"  {PAGE.relative_to(ROOT).as_posix()} 写入 {len(chapters)} 行")


def build(validate: bool) -> None:
    chapters = []
    for path in sorted(BOOK.glob("*.md")):
        ch = parse_chapter(path)
        if ch:
            chapters.append(ch)
    if len(chapters) < 32:
        raise SystemExit(f"只解析到 {len(chapters)} 章，应为 32 章")

    template = SKILL_DIR / "assets" / "template-editorial-card.html"
    if not template.exists():
        raise SystemExit(f"找不到 social-card 模板：{template}")

    work = ROOT / ".tmp-cardbuild" / "chapters"
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)

    html = template.read_text(encoding="utf-8")
    head, rest = html.rsplit("<!-- POSTERS_HERE -->", 1)
    _, _, tail = rest.partition("</main>")
    body = "".join(poster(ch) for ch in chapters)
    out = head + body + "\n  </main>" + tail
    out = out.replace("</head>", "  <style>" + TASK_CSS + "  </style>\n</head>", 1)
    out = out.replace('data-theme="ink-classic"', 'data-theme="forest-ink"', 1)
    (work / "index.html").write_text(out, encoding="utf-8")

    print(f"→ 渲染 {len(chapters)} 章结论卡")
    subprocess.run(
        ["node", str(SKILL_DIR / "scripts" / "render.mjs"), str(work)],
        cwd=str(SKILL_DIR),
        check=True,
    )

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    pngs = sorted((work / "output").glob("*.png"))
    if len(pngs) != len(chapters):
        raise SystemExit(f"渲染出 {len(pngs)} 张，应为 {len(chapters)} 张")
    total = 0
    for png in pngs:
        shutil.copy2(png, OUT_DIR / png.name)
        total += png.stat().st_size
    print(f"  docs/public/spread/cards/chapters/  {len(pngs)} 张，{total / 1048576:.1f} MB")

    write_page(chapters)

    if validate:
        print("→ 校验")
        subprocess.run(
            ["node", str(SKILL_DIR / "validate-social-deck.mjs"), str(work)],
            cwd=str(SKILL_DIR),
            check=True,
        )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--validate", action="store_true")
    args = ap.parse_args()
    build(args.validate)
    return 0


if __name__ == "__main__":
    sys.exit(main())
