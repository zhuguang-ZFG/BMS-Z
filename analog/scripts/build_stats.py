#!/usr/bin/env python3
"""打印内容规模：文档页、动画、题库、视频、公式与测试数。"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
BOOK = ROOT / "analog-book" / "dist" / "analog-circuit-book.html"


def count_formulas() -> int | None:
    if not BOOK.is_file():
        return None
    return BOOK.read_text(encoding="utf-8").count('class="arithmatex"')


def main() -> None:
    # Windows 管道默认 GBK，中文标签会直接抛 UnicodeEncodeError。
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    pages = [p for p in DOCS.glob("*.md") if p.name != "index.md"]
    svgs = list((ROOT / "assets" / "svg").glob("*.svg"))
    quiz_ids = set()
    quiz_chapters = set()
    quiz_extras = set()
    youtube = set()
    bilibili = set()
    for page in pages:
        text = page.read_text(encoding="utf-8")
        quiz_ids.update(re.findall(r'id="(q-[\w-]+)"', text))
        quiz_chapters.update(re.findall(r'id="(q-ch[\w-]+)"', text))
        quiz_extras.update(re.findall(r'id="(q-extra-[\w-]+)"', text))
        for video_id in re.findall(r'youtube\.com/(?:watch\?v=|embed/)([\w-]{11})', text):
            youtube.add(video_id)
        for video_id in re.findall(r'bilibili\.com/video/(BV[\w]+)', text):
            bilibili.add(video_id)
    videos = youtube | bilibili
    tests = list((ROOT / "scripts").glob("test_*.py"))
    tests += list((ROOT / "analog-book" / "tests").glob("test_*.py"))
    formulas = count_formulas()
    print(f"文档页       {len(pages)}")
    print(f"SVG 动画     {len(svgs)}")
    print(f"题库条目     {len(quiz_ids)}（章题 {len(quiz_chapters)} · 加练 {len(quiz_extras)}）")
    print(f"视频链接     {len(videos)}（B 站 {len(bilibili)} · YouTube {len(youtube)}）")
    print(f"测试文件     {len(tests)}")
    print("公式         "
          + (f"{formulas}（整书）" if formulas is not None
             else "未构建（先运行 make book）"))


if __name__ == "__main__":
    main()
