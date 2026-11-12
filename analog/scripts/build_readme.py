#!/usr/bin/env python3
"""由 docs/ 生成 README.md 入口与 BOOK.md 全量单文件（docs 是唯一数据源）。

* 页面顺序：index.md → pN-MM-*.md，按 (篇, 序号) 升序
* ``BOOK.md`` 保持旧的单文件语义：跨页锚点链接 ``](page.md#anchor)``
  反写为 ``](#anchor)``，拼合后的锚点仍可跳转
* ``README.md`` 只保留首页与仓库入口：跨页链接改为 ``](docs/page.md#anchor)``，
  避免 GitHub 首页超过在线渲染阈值
* ``--check``：只比对不落盘（CI 用），任一文件不一致返回非零
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
README = ROOT / "README.md"
BOOK = ROOT / "BOOK.md"

PAGE_RE = re.compile(r"^p(\d+)-(\d+)-.+\.md$")
MD_LINK = re.compile(r"\]\(([\w\-]+\.md)#([^)/]+)\)")
HTML_HREF = re.compile(r'href="([\w\-]+\.md)#([^"]+)"')
PAGE_LINK = re.compile(r"\]\(([\w\-]+\.md)\)")
HTML_PAGE = re.compile(r'href="([\w\-]+\.md)"')

PORTAL = """
---

<a id="readme-portal"></a>
## 仓库入口

- [完整单文件版 BOOK.md](BOOK.md)（由 docs/ 全量拼合；文件较大，适合下载与本地检索）
- [分页源文件 docs/](docs/)（逐页阅读、编辑与审读的源头）
- [在线知识站](https://aliyun-hutuji.donglicao.com/analog-circuit-roadmap/)
- [16K 印刷构建说明](analog-book/README.md)
"""


def page_order(path: Path) -> tuple:
    name = path.name
    if name == "index.md":
        return (0, 0, name)
    m = PAGE_RE.match(name)
    if m:
        return (int(m.group(1)), int(m.group(2)), name)
    return (99, 99, name)


def collect_pages() -> list[Path]:
    if not DOCS.is_dir():
        print("docs/ not found — 先运行 scripts/split_readme.py", file=sys.stderr)
        raise SystemExit(1)
    return sorted(DOCS.glob("*.md"), key=page_order)


def _transform(text: str, page_names: set[str], *, single_file: bool) -> str:
    if single_file:
        text = MD_LINK.sub(lambda m: "](#%s)" % m.group(2), text)
        text = HTML_HREF.sub(lambda m: 'href="#%s"' % m.group(2), text)
    else:
        text = MD_LINK.sub(
            lambda m: "](docs/%s#%s)" % (m.group(1), m.group(2)), text)
        text = HTML_HREF.sub(
            lambda m: 'href="docs/%s#%s"' % (m.group(1), m.group(2)), text)
    # 无锚点的整页链接在 README/BOOK 两种形态下都指向 docs/ 源文件。
    text = PAGE_LINK.sub(
        lambda m: "](docs/%s)" % m.group(1) if m.group(1) in page_names else m.group(0),
        text)
    text = HTML_PAGE.sub(
        lambda m: 'href="docs/%s"' % m.group(1) if m.group(1) in page_names else m.group(0),
        text)
    # 跨卷链接：docs/ 在 analog/ 下一级，源里 ../../ 上溯到仓库根；BOOK.md 与
    # README.md 都在 analog/ 下，只需一级。原样保留会把链接指到仓库根之上
    # （lychee 判 file-not-found，run 43254167168 实证）。
    text = text.replace("](../../bms-book/", "](../bms-book/")
    return text


def build_book() -> str:
    """全量单文件：与旧的 README 单文件语义一致。"""
    page_names = {p.name for p in collect_pages()}
    all_lines: list[str] = []
    for path in collect_pages():
        raw = path.read_text(encoding="utf-8")
        lines = raw.split("\n")
        if lines and lines[-1] == "":
            lines.pop()          # 去掉文件末尾换行产生的空项
        text = "\n".join(lines)
        if not text.strip():
            continue
        all_lines.append(_transform(text, page_names, single_file=True))
    return "\n".join(all_lines) + "\n"


def build_readme() -> str:
    """短入口 README：只取 docs/index.md，并把跨页链接指回 docs/。"""
    page_names = {p.name for p in collect_pages()}
    text = (DOCS / "index.md").read_text(encoding="utf-8").strip("\n")
    text = _transform(text, page_names, single_file=False)
    first, sep, rest = text.partition("\n")
    if not sep:
        raise ValueError("docs/index.md 缺少标题后的正文")
    text = first + "\n\n[仓库入口](#readme-portal)\n" + sep + rest
    return text + PORTAL


def _write(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8", newline="\n")


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def main() -> int:
    # Windows 管道默认 GBK，中文与 ✔ 会直接抛 UnicodeEncodeError。
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="只检查 docs 与 README/BOOK 是否一致")
    args = ap.parse_args()

    outputs = ((README, build_readme()), (BOOK, build_book()))
    if args.check:
        mismatched = [path.name for path, content in outputs
                      if content.replace("\r\n", "\n") != _read(path).replace("\r\n", "\n")]
        if mismatched:
            print("与 docs/ 不同步：请运行 python scripts/build_readme.py -> "
                  + ", ".join(mismatched), file=sys.stderr)
            return 1
        print("docs/ ↔ README.md + BOOK.md 同步 ✔")
        return 0

    for path, content in outputs:
        _write(path, content)
        print(f"{path.name} 已由 docs/ 重建（{len(content)} 字符）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
