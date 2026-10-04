#!/usr/bin/env python3
"""轻量文档一致性：SVG 数量、关键 code 路径、Markdown 相对链接与锚点存在性。"""
from __future__ import annotations

import re
import sys
import unicodedata
import xml.etree.ElementTree as ET
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
# 下界必须跟着实际发货量走——当前 37 张（36 个 SMIL 动画 + 1 张 DW01 电路图）；
# 停在旧值会让"删掉一半动画"这种回退静默通过。
MIN_SVGS = 37

SVG_NS = "{http://www.w3.org/2000/svg}"
XLINK_HREF = "{http://www.w3.org/1999/xlink}href"
ANIM_TAGS = {"animate", "animateTransform", "animateMotion", "set"}

# 各元素真正拥有的几何属性。动画写了元素没有的属性（最典型：给 <line> animate "y"，
# 而 <line> 的几何是 y1/y2）不会报错，只是**静默不动**——所以必须静态拦住。
GEOM_ATTRS = {
    "rect": {"x", "y", "width", "height", "rx", "ry"},
    "circle": {"cx", "cy", "r"},
    "ellipse": {"cx", "cy", "rx", "ry"},
    "line": {"x1", "y1", "x2", "y2"},
    "polyline": {"points"},
    "polygon": {"points"},
    "path": {"d"},
    "text": {"x", "y", "dx", "dy", "rotate", "textLength"},
    "tspan": {"x", "y", "dx", "dy"},
    "image": {"x", "y", "width", "height"},
    "use": {"x", "y", "width", "height"},
    "foreignObject": {"x", "y", "width", "height"},
    "svg": {"x", "y", "width", "height"},
    "g": set(),  # <g> 完全没有几何属性
}
ALL_GEOM = set().union(*GEOM_ATTRS.values())


def check_smil(svgs: list[Path]) -> tuple[int, list[str]]:
    """校验 SMIL 动画的硬性规范。

    SMIL 对 keyTimes 的要求是"不满足即文档有错"，而浏览器处理"有错"的方式是
    **整条动画不执行**：元素停在初始值上，页面不报错、CI 也看不出来，只有人眼
    盯着动画才会发现某一幕从来没出现过。本函数把这些规则变成红灯。
    """
    problems: list[str] = []
    total = 0
    for svg in svgs:
        try:
            root = ET.parse(svg).getroot()
        except ET.ParseError as exc:
            problems.append(f"{svg.name}: XML 解析失败：{exc}")
            continue
        parent = {child: p for p in root.iter() for child in p}
        by_id = {el.get("id"): el for el in root.iter() if el.get("id")}

        for el in root.iter():
            tag = el.tag.replace(SVG_NS, "")
            if tag not in ANIM_TAGS:
                continue
            total += 1
            attr = el.get("attributeName")
            where = f"{svg.name}: <{tag} attributeName={attr}>"

            key_times = el.get("keyTimes")
            if key_times is not None:
                parts = key_times.split(";")
                try:
                    nums = [float(p) for p in parts]
                except ValueError:
                    problems.append(f"{where} keyTimes 不是数字列表：{key_times}")
                    nums = []
                if nums:
                    # 规范：首值必须 0；calcMode 非 discrete 时末值必须 1。
                    if nums[0] != 0.0:
                        problems.append(f"{where} keyTimes 必须以 0 开头：{key_times}")
                    if el.get("calcMode") != "discrete" and nums[-1] != 1.0:
                        problems.append(
                            f"{where} keyTimes 必须以 1 结尾（calcMode 非 discrete）：{key_times}"
                        )
                    if any(b < a for a, b in zip(nums, nums[1:], strict=False)):
                        problems.append(f"{where} keyTimes 必须单调不减：{key_times}")
                    if any(x < 0.0 or x > 1.0 for x in nums):
                        problems.append(f"{where} keyTimes 必须落在 [0,1]：{key_times}")
                for name in ("values", "keyPoints"):
                    lst = el.get(name)
                    if lst is not None and len(lst.split(";")) != len(parts):
                        problems.append(
                            f"{where} {name} 有 {len(lst.split(';'))} 项、"
                            f"keyTimes 有 {len(parts)} 项，必须等长"
                        )

            if attr:
                href = el.get(XLINK_HREF) or el.get("href")
                target = (
                    by_id.get(href[1:])
                    if href and href.startswith("#")
                    else parent.get(el)
                )
                if target is not None:
                    ttag = target.tag.replace(SVG_NS, "")
                    if ttag in GEOM_ATTRS and attr in ALL_GEOM and attr not in GEOM_ATTRS[ttag]:
                        owns = "/".join(sorted(GEOM_ATTRS[ttag])) or "无几何属性"
                        problems.append(
                            f"{where} <{ttag}> 没有 {attr} 属性（它的几何属性是 {owns}）"
                        )
    return total, problems


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

    anim_count, smil_problems = check_smil(svgs)
    if smil_problems:
        print("FAIL: SMIL 动画不合规（浏览器会直接不执行这条动画）:")
        print("\n".join(smil_problems[:50]))
        return 1
    print(f"ok: {anim_count} 个动画元素的 keyTimes/values/attributeName 合规")

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
