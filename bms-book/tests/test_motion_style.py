"""手帐式动效注记层：插入式装饰的覆盖、可访问性与技术结构合同。"""
import hashlib
import json
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import motion_style  # noqa: E402

ASSETS = ROOT / "docs" / "circuits" / "assets"
PRINT = ROOT / "bms-book" / "assets" / "print"
FINGERPRINTS = Path(__file__).with_name("motion_fingerprints.json")
NS = "{http://www.w3.org/2000/svg}"
SVGS = sorted(ASSETS.glob("*.svg"))
STYLE_RE = re.compile(r'<style id="bms-motion">(.*?)</style>', re.S)
CLASS_RE = re.compile(r"\.([A-Za-z][\w-]*)")


def svg_texts():
    return {path.name: path.read_text(encoding="utf-8") for path in SVGS}


def motion_roots(root):
    """返回装饰元素集合；装饰以 bms- 类名标记，样式块按 id 标记。"""
    decorated = []
    for el in root.iter():
        classes = (el.get("class") or "").split()
        if any(name.startswith("bms-") for name in classes):
            decorated.append(el)
        elif el.tag == f"{NS}style" and el.get("id") == "bms-motion":
            decorated.append(el)
    return decorated


def ancestors(root):
    return {child: parent for parent in root.iter() for child in parent}


def in_motion(el, parents):
    current = el
    while current is not None:
        classes = (current.get("class") or "").split()
        if any(name.startswith("bms-") for name in classes):
            return True
        current = parents.get(current)
    return False


def test_every_circuit_animation_carries_one_motion_layer():
    assert len(SVGS) >= 150
    problems = []
    for name, text in svg_texts().items():
        count = text.count('id="bms-motion"')
        if count != 1:
            problems.append(f"{name}: {count}")
    assert not problems, "每张动画必须恰有一个 bms-motion 样式块：" + "、".join(problems)


def test_motion_layer_defines_every_class_it_uses():
    problems = []
    for name, text in svg_texts().items():
        block = STYLE_RE.search(text)
        if not block:
            problems.append(f"{name}: 缺 bms-motion 样式块")
            continue
        defined = set(CLASS_RE.findall(block.group(1)))
        used = set()
        for raw in re.findall(r'class="([^"]+)"', text):
            used.update(token for token in raw.split() if token.startswith("bms-"))
        missing = used - defined
        if missing:
            problems.append(f"{name}: 未定义 {'、'.join(sorted(missing))}")
    assert not problems, "\n".join(problems)


def test_motion_groups_are_decorative_only():
    problems = []
    for name, text in svg_texts().items():
        if "<!DOCTYPE" in text or "<script" in text:
            problems.append(f"{name}: 不允许脚本或文档类型声明")
        root = ET.fromstring(text)
        parents = ancestors(root)
        roots = {el for el in motion_roots(root) if el.tag != f"{NS}style"}
        for el in roots:
            tag = el.tag.replace(NS, "")
            hidden = el.get("aria-hidden") == "true"
            current = parents.get(el)
            while not hidden and current is not None:
                hidden = (
                    current in roots
                    and current.get("aria-hidden") == "true"
                )
                current = parents.get(current)
            if not hidden:
                problems.append(f"{name}: 装饰 <{tag}> 缺 aria-hidden 或不在装饰组内")
            for child in el.iter():
                ctag = child.tag.replace(NS, "")
                if ctag in {"text", "title", "desc", "script", "animateMotion"}:
                    problems.append(f"{name}: 装饰里混入 <{ctag}>")
    assert not problems, "\n".join(problems)


def declared_title_sizes(text):
    sizes = []
    for style in ET.fromstring(text).iter(f"{NS}style"):
        if style.get("id") == "bms-motion":
            continue
        for selector, body in re.findall(r"([^{}]+)\{([^{}]*)\}", style.text or ""):
            if not re.search(r"(?:^|,)\s*\.title\s*(?:,|$)", selector.strip()):
                continue
            found = re.search(r"font-size\s*:\s*([\d.]+)px", body)
            if found:
                sizes.append(float(found.group(1)))
    return sizes


def test_title_marker_follows_stylesheet_font_size():
    problems = []
    checked = 0
    for name, text in svg_texts().items():
        meta = motion_style.title_meta(ET.fromstring(text))
        if meta is None:
            continue
        checked += 1
        _x, y, size, _width = meta
        sizes = declared_title_sizes(text)
        expected = sizes[-1] if sizes else 16.0
        if abs(size - expected) > 1e-6:
            problems.append(f"{name}: 字号 {size:g} 与样式表 {expected:g} 不符")
        marker = re.search(
            r'<rect class="bms-marker"[^>]*\by="([-\d.]+)"[^>]*\bheight="([\d.]+)"',
            text,
        )
        if marker is None:
            problems.append(f"{name}: 缺标题荧光笔")
            continue
        marker_y, marker_h = (float(value) for value in marker.groups())
        if abs(marker_h - size * 1.08) > 0.11:
            problems.append(f"{name}: 荧光笔高度 {marker_h:g} 不随字号 {size:g}")
        if abs(marker_y - (y - size * 0.93)) > 0.11:
            problems.append(f"{name}: 荧光笔位置与字号 {size:g} 不匹配")
    assert checked >= 150, checked
    assert not problems, "\n".join(problems)


def test_technical_fingerprint_includes_visible_tail_text():
    text = (ASSETS / "state-machine.svg").read_text(encoding="utf-8")
    phrase = "示意门槛见保护去抖：4.25 V 触发，4.15 V 才谈恢复。"
    canonical = motion_style.technical_canonical(text)
    assert canonical.count(phrase) == 2, "紧跟 <animate> 的可见尾随文字没有被指纹收录"


def test_refresh_rebuilds_the_same_layer():
    text = (ASSETS / "state-machine.svg").read_text(encoding="utf-8")
    assert motion_style.decorate(text) == text, "无 refresh 时必须幂等"
    refreshed = motion_style.decorate(text, refresh=True)
    assert refreshed == text, "strip + re-decorate 必须逐字节还原同一装饰层"
    assert refreshed.count('id="bms-motion"') == 1


def test_motion_smil_is_checker_safe():
    problems = []
    for name, text in svg_texts().items():
        root = ET.fromstring(text)
        parents = ancestors(root)
        for el in root.iter():
            if el.tag.replace(NS, "") not in {
                "animate", "animateTransform", "animateMotion", "set",
            }:
                continue
            if not in_motion(el, parents):
                continue
            key_times = el.get("keyTimes")
            if key_times is None:
                continue
            times = [float(part) for part in key_times.split(";")]
            values = el.get("values")
            if values is not None and len(values.split(";")) != len(times):
                problems.append(f"{name}: values 与 keyTimes 不等长")
            if times[0] != 0.0 or times[-1] != 1.0:
                problems.append(f"{name}: keyTimes 必须 0 开头 1 结尾")
            if any(b < a for a, b in zip(times, times[1:], strict=False)):
                problems.append(f"{name}: keyTimes 必须单调不减")
            splines = el.get("keySplines")
            if splines is not None and len(splines.split(";")) != len(times) - 1:
                problems.append(f"{name}: keySplines 数量不对")
    assert not problems, "\n".join(problems)


def test_motion_layer_has_dark_and_reduced_motion_contract():
    for name, text in svg_texts().items():
        block = STYLE_RE.search(text)
        assert block, f"{name}: 缺 bms-motion 样式块"
        css = block.group(1)
        assert "@media (prefers-color-scheme: dark)" in css, name
        assert ".bms-marker" in css and ".bms-sticker" in css, name
        assert "@media (prefers-reduced-motion: reduce)" in css, name
        assert re.search(r"\.bms-doodle\s*\{\s*display:\s*none", css), name


def test_motion_layer_reaches_titles_headers_and_stickers():
    # 提示框贴纸只落在「有出现时刻」的大提示框上，单元格小标签加框会变成噪声；
    # 因此按贴纸总数和覆盖文件数设下限，而不是要求 15 个文件各贴一张。
    stats = {"title": 0, "doodle": 0, "sticker": 0, "sticker_files": 0, "success": 0}
    for text in svg_texts().values():
        stats["title"] += 'class="bms-marker"' in text
        stats["doodle"] += 'class="bms-doodle"' in text
        stats["sticker"] += text.count('class="bms-sticker"')
        stats["sticker_files"] += 'class="bms-sticker"' in text
        stats["success"] += 'class="bms-success"' in text
    assert stats["title"] >= 150, stats
    assert stats["doodle"] >= 140, stats
    assert stats["sticker"] >= 20 and stats["sticker_files"] >= 10, stats
    assert stats["success"] >= 1, stats


def test_motion_layer_preserves_technical_structure():
    assert FINGERPRINTS.is_file(), "缺少技术结构指纹：先按 HEAD 原图生成 motion_fingerprints.json"
    expected = json.loads(FINGERPRINTS.read_text(encoding="utf-8"))
    current = svg_texts()
    assert set(expected) == set(current), "指纹清单必须覆盖全部动画"
    problems = []
    for name, text in sorted(current.items()):
        digest = hashlib.sha256(
            motion_style.technical_canonical(text).encode("utf-8")
        ).hexdigest()
        if digest != expected[name]:
            problems.append(name)
    assert not problems, "这些动画的技术节点或既有 SMIL 被改动：" + "、".join(problems)


def test_print_snapshots_freeze_the_motion_layer_without_animation():
    snapshots = sorted(PRINT.glob("*.svg"))
    assert snapshots, "缺少打印快照"
    problems = []
    for path in snapshots:
        text = path.read_text(encoding="utf-8")
        if "<animate" in text:
            problems.append(f"{path.name}: 仍有 SMIL")
        if 'id="bms-motion"' not in text:
            problems.append(f"{path.name}: 未冻结装饰层")
        if b"\r\n" in path.read_bytes():
            problems.append(f"{path.name}: 含 CRLF，快照必须写 LF")
    assert not problems, "\n".join(problems)


def test_circuit_assets_use_lf():
    offenders = [
        path.name
        for path in SVGS
        if b"\r\n" in path.read_bytes()
    ]
    assert not offenders, "动画源文件必须写 LF：" + "、".join(offenders)
