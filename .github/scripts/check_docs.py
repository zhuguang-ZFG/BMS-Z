#!/usr/bin/env python3
"""轻量文档一致性：SVG 数量、关键 code 路径、Markdown 相对链接与锚点存在性。"""
from __future__ import annotations

import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")

# GitHub 锚点算法（github-slugger）的等价实现：
#   小写 → 去掉标点（保留 字母/组合记号/数字/连接符/连字符/空格）→ 每个空格换一个 "-"。
# 注意是"每个空格换一个"，不是折叠——`AFE + MCU` 去掉 "+" 后剩两个空格，
# 必须得到 `afe--mcu`。折叠成单个 "-" 会把正确链接误报为失效。
# 一-鿿 是 CJK，̀-ͯ 是组合记号（\w 不含后者）。
_KEEP = re.compile(r"[^\w\s\-\u4e00-\u9fff\u0300-\u036f]", re.UNICODE)


def slugify(heading: str) -> str:
    s = unicodedata.normalize("NFC", heading).strip().lower()
    s = _KEEP.sub("", s)
    return s.replace(" ", "-")


def anchors_of(path: Path) -> set[str]:
    """收集一份 Markdown 里的全部锚点，含 GitHub 的重复标题去重后缀（-1/-2…）。"""
    out: set[str] = set()
    seen: dict[str, int] = {}
    in_fence = False
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        m = HEADING_RE.match(line)
        if not m:
            continue
        base = slugify(m.group(2))
        if not base:
            continue
        n = seen.get(base, 0)
        seen[base] = n + 1
        out.add(base if n == 0 else f"{base}-{n}")
    return out


# 动画数量只设下界：新增动画不该让 CI 变红，掉下来才是回退。
# 下界必须跟着实际发货量走——当前 36 个；停在旧值会让"删掉一半动画"
# 这种回退静默通过。
MIN_SVGS = 36


def main() -> int:
    assets = ROOT / "docs" / "circuits" / "assets"
    svgs = sorted(assets.glob("*.svg"))
    if len(svgs) < MIN_SVGS:
        print(f"FAIL: expected >= {MIN_SVGS} SVGs in {assets}, found {len(svgs)}")
        return 1

    # 每个动画的硬性约定：中文 <title>（可访问性）、SMIL 动画元素、深色模式覆盖块。
    bad_svgs: list[str] = []
    for svg in svgs:
        text = svg.read_text(encoding="utf-8")
        lacks = [
            name
            for name, ok in (
                ("<title>", "<title>" in text),
                ("SMIL 动画", "<animate" in text),
                ("深色模式块", "prefers-color-scheme: dark" in text),
            )
            if not ok
        ]
        if lacks:
            bad_svgs.append(f"{svg.name}: 缺 {'、'.join(lacks)}")
    if bad_svgs:
        print("FAIL: SVG 约定不满足:")
        print("\n".join(bad_svgs))
        return 1
    print(f"ok: {len(svgs)} SVGs（title / animate / 深色模式 齐全）")

    for rel in ("code/soc", "code/protocol", "code/firmware", "code/README.md"):
        if not (ROOT / rel).exists():
            print(f"FAIL: missing {rel}")
            return 1
    print("ok: code packages present")

    missing: list[str] = []
    bad_anchors: list[str] = []
    checked = 0
    anchor_cache: dict[Path, set[str]] = {}

    for md in ROOT.rglob("*.md"):
        if ".git" in md.parts:
            continue
        text = md.read_text(encoding="utf-8")
        for _label, raw in LINK_RE.findall(text):
            url = raw.strip().split()[0]
            if url.startswith(("http://", "https://", "mailto:")):
                continue
            path_part, _, frag = url.partition("#")
            if not path_part:
                continue  # 纯页内锚点：本仓库未使用，先不引入噪声
            target = (md.parent / path_part).resolve()
            try:
                target.relative_to(ROOT)
            except ValueError:
                continue
            checked += 1
            if not target.exists():
                missing.append(f"{md.relative_to(ROOT).as_posix()}: {url}")
                continue
            # 锚点校验：链接指向的章节被改名时，"文件存在"检查发现不了
            if frag and target.suffix == ".md":
                if target not in anchor_cache:
                    anchor_cache[target] = anchors_of(target)
                if frag not in anchor_cache[target]:
                    bad_anchors.append(f"{md.relative_to(ROOT).as_posix()}: {url}")

    if missing:
        print("FAIL: broken relative links:")
        print("\n".join(missing[:50]))
        return 1
    print(f"ok: {checked} relative file links exist")

    if bad_anchors:
        print("FAIL: anchors not found in target file:")
        print("\n".join(bad_anchors[:50]))
        return 1
    print(f"ok: anchors in {len(anchor_cache)} files resolve")
    return 0


if __name__ == "__main__":
    sys.exit(main())
