#!/usr/bin/env python3
"""轻量文档一致性：SVG 数量、阶段表张数、关键 code 路径、Markdown 相对链接与锚点存在性。"""
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
# 下界必须跟着实际发货量走——当前 147 张；
# 停在旧值会让"删掉一半动画"这种回退静默通过。
MIN_SVGS = 147

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

# 这些元素不写坐标时，缺省就在 (0,0)。延迟开始的 animateMotion 在 begin 之前
# 不会把它们放到路径上，于是圆点停在画布原点。
_MOTION_POS = {
    "circle": ("cx", "cy"),
    "ellipse": ("cx", "cy"),
    "rect": ("x", "y"),
    "image": ("x", "y"),
    "use": ("x", "y"),
    "text": ("x", "y"),
    "foreignObject": ("x", "y"),
}
_CLOCK_RE = re.compile(r"^([+-]?(?:\d+(?:\.\d+)?|\.\d+))(ms|s)?$")


def _clock_seconds(raw: str | None) -> float | None:
    """时钟值换成秒。事件触发（click、id.end）返回 None，不当成原点停留。"""
    if raw is None:
        return 0.0
    match = _CLOCK_RE.fullmatch(raw.strip())
    if not match:
        return None
    value = float(match.group(1))
    if match.group(2) == "ms":
        return value / 1000.0
    return value


def _opacity_at_start(el: ET.Element) -> float | None:
    """这个元素自己在 t=0 贡献的不透明度。None 表示不强制。"""
    shown: list[float] = []
    forced = False
    for child in list(el):
        tag = child.tag.replace(SVG_NS, "")
        if tag not in {"animate", "set"} or child.get("attributeName") != "opacity":
            continue
        begin = _clock_seconds(child.get("begin"))
        if begin is None or begin > 0:
            continue
        forced = True
        if tag == "set":
            raw = child.get("to")
        elif child.get("values"):
            raw = child.get("values", "").split(";", 1)[0]
        else:
            raw = child.get("from")
        if raw is None:
            continue
        try:
            shown.append(float(raw))
        except ValueError:
            continue
    if forced and shown:
        return max(shown)
    if forced:
        return 0.0
    raw = el.get("opacity")
    if raw is None:
        return None
    try:
        return float(raw)
    except ValueError:
        return None


def _hidden_before_motion(el: ET.Element, parent: dict[ET.Element, ET.Element]) -> bool:
    node: ET.Element | None = el
    while node is not None:
        if node.get("visibility") == "hidden" or node.get("display") == "none":
            return True
        opacity = _opacity_at_start(node)
        if opacity is not None and opacity <= 0:
            return True
        node = parent.get(node)
    return False


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

            if tag != "animateMotion":
                continue
            begin_s = _clock_seconds(el.get("begin"))
            if begin_s is None or begin_s <= 0:
                continue
            href = el.get(XLINK_HREF) or el.get("href")
            host = (
                by_id.get(href[1:])
                if href and href.startswith("#")
                else parent.get(el)
            )
            if host is None:
                continue
            htag = host.tag.replace(SVG_NS, "")
            if htag == "g":
                parked = not host.get("transform")
            elif htag in _MOTION_POS:
                parked = not any(host.get(name) for name in _MOTION_POS[htag])
            else:
                parked = False
            if not parked or _hidden_before_motion(host, parent):
                continue
            problems.append(
                f"{svg.name}: <animateMotion begin={el.get('begin')}> 的 <{htag}>"
                " 在开始前没有坐标，会停在原点"
            )
    return total, problems


# 画风检查的豁免清单。还没迁过来的旧图写在这里，第 2、3 批改完一张就删掉对应行。
# 本批改过的图和以后新增的图不进清单，四项都要自己通过。
STYLE_BASELINE = Path(__file__).with_name("svg_style_baseline.txt")
STYLE_KINDS = (
    "undefined-class",
    "inline-paint",
    "small-font",
    "missing-desc",
    "missing-role",
    "desc-eq-title",
    "bad-width",
)
_PAINT_OK = {"none", "transparent", "currentcolor", "inherit"}
_CLASS_RE = re.compile(r"\.(-?[_a-zA-Z]+[\w-]*)")
_FONT_CSS_RE = re.compile(r"font-size\s*:\s*([0-9.]+)\s*px", re.IGNORECASE)
_FONT_ATTR_RE = re.compile(r"""font-size\s*=\s*["']([0-9.]+)["']""", re.IGNORECASE)
_STYLE_ATTR_RE = re.compile(r"""\bstyle\s*=\s*(["'])(.*?)\1""", re.IGNORECASE | re.DOTALL)


def _svg_style_findings(text: str) -> list[tuple[str, str]]:
    """四项便宜检查：未定义的 class、内联 fill/color、字号 <12、缺 desc 或 role。"""
    findings: list[tuple[str, str]] = []
    styles = re.findall(r"<style[^>]*>(.*?)</style>", text, flags=re.IGNORECASE | re.DOTALL)
    defined = set(_CLASS_RE.findall("\n".join(styles)))
    missing: list[str] = []
    for raw in re.findall(r'class="([^"]+)"', text):
        for name in raw.split():
            if name not in defined and name not in missing:
                missing.append(name)
    if missing:
        findings.append(("undefined-class", "、".join(missing)))

    paints: list[str] = []
    for _quote, body in _STYLE_ATTR_RE.findall(text):
        for decl in body.split(";"):
            if ":" not in decl:
                continue
            prop, val = (part.strip().lower() for part in decl.split(":", 1))
            if prop in {"fill", "color"} and val not in _PAINT_OK:
                item = f"{prop}:{val}"
                if item not in paints:
                    paints.append(item)
    if paints:
        findings.append(("inline-paint", "、".join(paints[:6])))

    small = {n for n in _FONT_CSS_RE.findall(text) + _FONT_ATTR_RE.findall(text) if float(n) < 12}
    if small:
        shown = "、".join(f"{n}px" for n in sorted(small, key=float))
        findings.append(("small-font", shown))

    desc_m = re.search(r"<desc\b[^>]*>(.*?)</desc>", text, flags=re.IGNORECASE | re.DOTALL)
    desc_text = re.sub(r"<[^>]+>", "", desc_m.group(1)) if desc_m else ""
    desc_text = re.sub(r"\s+", "", desc_text)
    if len(desc_text) < 12:
        findings.append(("missing-desc", "缺有内容的 <desc>（至少一句机制说明）"))
    title_m = re.search(r"<title\b[^>]*>(.*?)</title>", text, flags=re.IGNORECASE | re.DOTALL)
    title_text = re.sub(r"\s+", "", title_m.group(1)) if title_m else ""
    if desc_text and title_text and desc_text == title_text:
        # 读屏先念 title 再念 desc，两遍同一个句子等于第二遍是噪声。
        findings.append(("desc-eq-title", "<desc> 不该是 <title> 的复读，写图上在动什么"))
    root = re.search(r"<svg\b[^>]*>", text)
    if root is None or 'role="img"' not in root.group(0):
        findings.append(("missing-role", '根 <svg> 缺 role="img"'))
    vb = re.search(r"""\bviewBox\s*=\s*["']([^"']+)["']""", text)
    if vb:
        parts = vb.group(1).split()
        try:
            width = float(parts[2]) if len(parts) == 4 else None
        except ValueError:
            width = None
        if width is None:
            findings.append(("bad-width", f"viewBox 要四位数字：{vb.group(1)!r}"))
        elif width != 800:
            findings.append(("bad-width", f"viewBox 宽 {parts[2]}，规范是 800"))
    return findings


def load_style_baseline() -> set[tuple[str, str]]:
    allowed: set[tuple[str, str]] = set()
    if not STYLE_BASELINE.exists():
        return allowed
    for raw in STYLE_BASELINE.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        name, _, kind = line.partition(" ")
        if name and kind:
            allowed.add((name, kind))
    return allowed


def check_svg_style(svgs: list[Path]) -> list[str]:
    """旧图可以留在豁免清单里。清单外的图（含本批改过的、新加的）必须通过。"""
    allowed = load_style_baseline()
    names = {svg.name for svg in svgs}
    problems: list[str] = []
    for name, kind in sorted(allowed):
        if name not in names:
            problems.append(f"豁免清单里的 {name} 已经不在 assets/，删掉这一行")
        elif kind not in STYLE_KINDS:
            problems.append(f"豁免清单的检查项不认识：{name} {kind}")
    for svg in svgs:
        for kind, detail in _svg_style_findings(svg.read_text(encoding="utf-8")):
            if (svg.name, kind) in allowed:
                continue
            problems.append(f"{svg.name}: {kind} {detail}")
    return problems


def check_markdown_hygiene() -> list[str]:
    """拦住两类会让公式在 GitHub 上坏掉的写法。

    - 控制字符：\\times 里的 \\t 曾被存成真正的 TAB，公式变成 ``imes``。
    - \\( \\)：GitHub 不渲染这对定界符，行内公式要用 $...$。
    """
    problems: list[str] = []
    delim = re.compile(r"\\\(|\\\)")
    for md in ROOT.rglob("*.md"):
        if ".git" in md.parts:
            continue
        rel = md.relative_to(ROOT).as_posix()
        text = md.read_text(encoding="utf-8")
        for n, line in enumerate(text.splitlines(), 1):
            bad = [ch for ch in line if ord(ch) < 32 and ch not in "\t"]
            # TAB 也算：它就是 \\times 被吃掉的那一种。
            if "\t" in line or bad:
                shown = "TAB" if "\t" in line else ",".join(f"U+{ord(ch):04X}" for ch in bad)
                problems.append(f"{rel}:{n}: 控制字符 {shown}")
        in_fence = False
        for n, line in enumerate(text.splitlines(), 1):
            if line.lstrip().startswith("```"):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            if delim.search(line):
                problems.append(f"{rel}:{n}: 仍用 \\( \\) 定界，GitHub 不渲染")
    return problems


def check_stage_counts() -> list[str]:
    """README 阶段表的「本章动画」列必须等于对应正文里唯一嵌入的 SVG 张数。

    这组数字已经真实漂移过一次（108→110），而且每加一张动画都要人手同步；
    在这里对上账，漂移自己变红，不再靠人记。
    """
    problems: list[str] = []
    readme_path = ROOT / "README.md"
    readme = readme_path.read_text(encoding="utf-8")
    row_re = re.compile(
        r"^\|\s*\[[^\]]*\]\((docs/stages/[^)]+\.md)\)\s*\|[^|]*\|\s*(\d+)\s*\|",
        re.M,
    )
    rows = row_re.findall(readme)
    if not rows:
        return [f"{readme_path.name}: 阶段表一行都没匹配到，表格式变了吗？"]
    embed_re = re.compile(r"!\[[^\]]*\]\(([^)]+\.svg)\)")
    total = 0
    for rel, claimed in rows:
        doc = ROOT / rel
        if not doc.exists():
            problems.append(f"README 阶段表指向不存在的 {rel}")
            continue
        names = {Path(p).name for p in embed_re.findall(doc.read_text(encoding="utf-8"))}
        if len(names) != int(claimed):
            problems.append(
                f"README 说 {rel} 嵌 {claimed} 张动画，正文实际唯一嵌入 {len(names)} 张"
            )
        total += int(claimed)
    m = re.search(r"七篇合计\s*(\d+)", readme)
    if m and int(m.group(1)) != total:
        problems.append(f"README 说七篇合计 {m.group(1)}，表格各行加起来是 {total}")
    return problems


def anchors_of_html(path: Path) -> set[str]:
    """HTML 页的锚点就是 id 属性（门户页没有 GitHub 式标题 slug）。"""
    text = path.read_text(encoding="utf-8")
    return set(re.findall(r'\bid="([^"]+)"', text))


def check_svg_index(svgs: list[Path]) -> list[str]:
    """动画索引（docs/circuits/README.md）必须和 assets/ 的实际清单双向一致。

    索引行是 「[名称](assets/xxx.svg)」。assets 有而索引没有 → 新图忘了收录；
    索引有而 assets 没有 → 图删了没摘行。清单对上了，「147 张」这类手写数字
    就没有漂移的空间。
    """
    readme = ROOT / "docs" / "circuits" / "README.md"
    indexed = {
        Path(m).name
        for m in re.findall(r"\]\(assets/([^)]+\.svg)\)", readme.read_text(encoding="utf-8"))
    }
    actual = {s.name for s in svgs}
    problems = [f"assets 有但动画索引没收录：{n}" for n in sorted(actual - indexed)]
    problems += [f"动画索引有但 assets 没有（死行）：{n}" for n in sorted(indexed - actual)]
    return problems


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
        title_m = re.search(r"<title\b[^>]*>(.*?)</title>", text, flags=re.DOTALL)
        title_text = re.sub(r"\s+", "", title_m.group(1)) if title_m else ""
        root_tag = re.search(r"<svg\b[^>]*>", text)
        lacks = [
            name
            for name, ok in (
                ("有内容的 <title>", len(title_text) >= 4),
                ("SMIL 动画", "<animate" in text),
                ("深色模式块", "prefers-color-scheme: dark" in text),
                ('role="img"', root_tag is not None and 'role="img"' in root_tag.group(0)),
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

    style_problems = check_svg_style(svgs)
    if style_problems:
        print("FAIL: SVG 画风检查（未定义 class / 内联填色 / 字号 <12 / 缺 desc 或 role / desc 复读 title / 画布宽）:")
        print("\n".join(style_problems[:50]))
        return 1
    print("ok: SVG 画风检查通过（豁免清单之外的图）")

    stage_problems = check_stage_counts()
    if stage_problems:
        print("FAIL: README 阶段表的动画张数和正文对不上:")
        print("\n".join(stage_problems[:50]))
        return 1
    print("ok: README 阶段表的「本章动画」与各篇正文嵌入数一致")

    index_problems = check_svg_index(svgs)
    if index_problems:
        print("FAIL: 动画索引和 assets/ 清单对不上:")
        print("\n".join(index_problems[:50]))
        return 1
    print("ok: 动画索引与 assets/ 双向一致（无孤儿图、无死行）")

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
            # 锚点校验：链接指向的章节被改名时，"文件存在"检查发现不了。
            # .md 用 GitHub 标题 slug，.html 用 id 属性。
            if frag and target.suffix == ".md":
                if target not in anchor_cache:
                    anchor_cache[target] = anchors_of(target)
                if frag not in anchor_cache[target]:
                    bad_anchors.append(f"{md.relative_to(ROOT).as_posix()}: {url}")
            elif frag and target.suffix == ".html":
                if target not in anchor_cache:
                    anchor_cache[target] = anchors_of_html(target)
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

    hygiene = check_markdown_hygiene()
    if hygiene:
        print("FAIL: Markdown 公式里有控制字符，或仍用 \\( \\) 定界:")
        print("\n".join(hygiene[:50]))
        return 1
    print("ok: markdown has no control characters or \\( \\) math delimiters")
    return 0


if __name__ == "__main__":
    sys.exit(main())
