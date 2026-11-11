#!/usr/bin/env python3
"""生成并校验《通往模拟电路之路》16K 印刷书的 OFL 字体子集。

用法::

    python scripts/subset_fonts.py --download
    python scripts/subset_fonts.py --build
    python scripts/subset_fonts.py --check

源字体（可变字体 TTF 与 OFL 许可）下载到 ``build/fonts-src/``，该目录在
.gitignore 中，不入仓。``analog-book/fonts/`` 只保存子集、印章字体、
许可文本、``sources.json`` 与说明，供后续单文件书内联。
"""

import argparse
import hashlib
import html
import json
import re
import shutil
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BOOK = ROOT / "analog-book"
SRC_DIR = ROOT / "build" / "fonts-src"
sys.path.insert(0, str(BOOK))

from book import config  # noqa: E402
from book.fonts import (EMOJI_RE, STAMP_FONT_NAME,  # noqa: E402
                        missing_glyphs, required_text)
from fontTools.pens.recordingPen import DecomposingRecordingPen  # noqa: E402
from fontTools.pens.ttGlyphPen import TTGlyphPen  # noqa: E402
from fontTools.subset import Subsetter  # noqa: E402
from fontTools.ttLib import TTFont  # noqa: E402
from fontTools.varLib.instancer import instantiateVariableFont  # noqa: E402

SOURCES = {
    "NotoSerifSC": ("https://raw.githubusercontent.com/google/fonts/main/ofl/notoserifsc/NotoSerifSC%5Bwght%5D.ttf",
                    "OFL-NotoSerifSC.txt"),
    "NotoSansSC": ("https://raw.githubusercontent.com/google/fonts/main/ofl/notosanssc/NotoSansSC%5Bwght%5D.ttf",
                   "OFL-NotoSansSC.txt"),
    "JetBrainsMono": ("https://raw.githubusercontent.com/google/fonts/main/ofl/jetbrainsmono/JetBrainsMono%5Bwght%5D.ttf",
                      "OFL-JetBrainsMono.txt"),
}
TARGETS = {
    ("NotoSerifSC", 400): "NotoSerifSC-Regular.woff2",
    ("NotoSerifSC", 700): "NotoSerifSC-Bold.woff2",
    ("NotoSansSC", 400): "NotoSansSC-Regular.woff2",
    ("NotoSansSC", 700): "NotoSansSC-Bold.woff2",
    ("JetBrainsMono", 400): "JetBrainsMono-Regular.woff2",
}
# Noto CJK 不含上/下标、⅓/⅔、组合上划线 U+0305 与 ◄（U+25C4）。这 13 个
# 字符确实出现在书稿与 SVG 中，因此从同为 OFL 的 Noto 拉丁/符号字体复制
# 真实轮廓补充，而不是删减 required_text()。
GLYPH_SOURCES = {
    "NotoSerif": ("https://raw.githubusercontent.com/google/fonts/main/ofl/notoserif/NotoSerif%5Bwdth,wght%5D.ttf",
                  "OFL-NotoSerif.txt"),
    "NotoSans": ("https://raw.githubusercontent.com/google/fonts/main/ofl/notosans/NotoSans%5Bwdth,wght%5D.ttf",
                 "OFL-NotoSans.txt"),
    "NotoSansSymbols2": ("https://raw.githubusercontent.com/google/fonts/main/ofl/notosanssymbols2/NotoSansSymbols2-Regular.ttf",
                         "OFL-NotoSansSymbols2.txt"),
}
GLYPH_DONORS = {
    "NotoSerifSC": ("NotoSerif", "NotoSansSymbols2"),
    "NotoSansSC": ("NotoSans", "NotoSansSymbols2"),
}
SOURCE_FILES = {
    "NotoSerifSC": "NotoSerifSC-VF.ttf",
    "NotoSansSC": "NotoSansSC-VF.ttf",
    "JetBrainsMono": "JetBrainsMono-VF.ttf",
    "NotoSerif": "NotoSerif-VF.ttf",
    "NotoSans": "NotoSans-VF.ttf",
    "NotoSansSymbols2": "NotoSansSymbols2-Regular.ttf",
}
ALL_SOURCES = {**SOURCES, **GLYPH_SOURCES}
STAMP_FAMILY = "NotoSansSC"
STAMP_WEIGHT = 700
ASCII = "".join(chr(c) for c in range(32, 127))
STAMP_FIXED = "目录索引参考文献版本记录"
# 页眉/页脚可能采用的短篇名（与正文章节标题不一定逐字相同）。
STAMP_RUNNING_TITLES = "第一篇基础第二篇器件第三篇拓扑第四篇设计第五篇调试"
# Task 11A 才把真实的 schema-2 manifest 落盘，当前清单仍是 schema 1。为了让
# 印章字体现在就能排最终结构的前置页、篇、单元、附录与后记标题，这里保留
# 与 `analog-book/tests/book_fixtures.py` 一致的 schema-2 书名结构；schema 2
# 落盘后 stamp_text() 还会从清单自动收集，两份标题取并集。
STAMP_SECTION_TITLES = (
    "前言", "怎样读这本书", "模拟电路简史", "排版、术语与引用约定",
    "符号与单位表",
    "基础", "器件", "拓扑", "设计", "调试",
    "电路直觉与无源世界", "分立器件", "模拟集成器件", "信号链与功率",
    "方法与实现", "方法与经验",
    "动画与图示索引", "公式与设计速查", "常用芯片速查", "视频课程与配套资源",
    "学习路线、选读与诊断", "习题答案与综合自测", "术语表",
    "模型、近似与适用边界",
    "版本记录", "致谢", "来源与许可",
)
STAMP_TEST_TITLES = "通往模拟电路之路目录索引参考文献第一篇基础第二篇器件第三篇拓扑第四篇设计第五篇调试"


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def source_path(family: str) -> Path:
    return SRC_DIR / SOURCE_FILES[family]


def license_url(font_url: str) -> str:
    return font_url.rsplit("/", 1)[0] + "/OFL.txt"


def _download(url: str, dest: Path) -> None:
    print(f"下载 {url}")
    request = urllib.request.Request(
        url, headers={"User-Agent": "analog-book-subset-fonts/1.0"})
    with urllib.request.urlopen(request, timeout=300) as response:
        data = response.read()
    if not data:
        raise RuntimeError(f"下载内容为空: {url}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    print(f"  -> {dest}  {len(data):,} 字节  sha256={hashlib.sha256(data).hexdigest()}")


def download_sources() -> None:
    for family, (url, license_name) in ALL_SOURCES.items():
        _download(url, source_path(family))
        _download(license_url(url), SRC_DIR / license_name)


def _font_cmap(font: TTFont) -> set[int]:
    cmap = set()
    for table in font["cmap"].tables:
        if table.isUnicode():
            cmap.update(table.cmap.keys())
    return cmap


def _instance(font: TTFont, axes: dict[str, float]) -> TTFont:
    if "fvar" not in font:
        return font
    available = {axis.axisTag for axis in font["fvar"].axes}
    limits = {tag: value for tag, value in axes.items() if tag in available}
    return instantiateVariableFont(font, limits)


def _donor_axes(family: str, weight: int) -> dict[str, float]:
    axes = {"wght": weight}
    if family in ("NotoSerif", "NotoSans"):
        axes["wdth"] = 100
    return axes


def _copy_glyphs(target: TTFont, donor: TTFont, codepoints: set[int]) -> set[int]:
    """把 donor 的真实字形轮廓复制进 target，并补 cmap/hmtx/vmtx。"""
    donor_cmap = donor.getBestCmap()
    donor_glyphset = donor.getGlyphSet()
    target_order = target.getGlyphOrder()
    target_glyphs = target["glyf"]
    target_hmtx = target["hmtx"]
    target_vmtx = target["vmtx"] if "vmtx" in target else None
    target_cmaps = [table for table in target["cmap"].tables if table.isUnicode()]
    upem = target["head"].unitsPerEm
    if donor["head"].unitsPerEm != upem:
        raise RuntimeError(
            f"donor unitsPerEm {donor['head'].unitsPerEm} != target {upem}，"
            "需先缩放字形")
    copied = set()
    for codepoint in sorted(codepoints):
        donor_name = donor_cmap.get(codepoint)
        if donor_name is None:
            continue
        pen = TTGlyphPen(None)
        recording = DecomposingRecordingPen(donor_glyphset)
        donor_glyphset[donor_name].draw(recording)
        recording.replay(pen)
        glyph = pen.glyph()
        if glyph.numberOfContours == 0:
            raise RuntimeError(
                f"donor 字形为空: U+{codepoint:04X} ({donor_name})")
        name = f"book_uni{codepoint:04X}"
        target_glyphs.glyphs[name] = glyph
        target_hmtx.metrics[name] = donor["hmtx"][donor_name]
        if target_vmtx is not None:
            target_vmtx.metrics[name] = (upem, 0)
        target_order.append(name)
        for table in target_cmaps:
            table.cmap[codepoint] = name
        copied.add(codepoint)
    target.setGlyphOrder(target_order)
    target["maxp"].numGlyphs = len(target_order)
    return copied


def _add_donor_glyphs(target: TTFont, family: str, weight: int,
                      missing: set[int]) -> set[int]:
    remaining = set(missing)
    for donor_family in GLYPH_DONORS.get(family, ()):
        if not remaining:
            break
        donor = TTFont(source_path(donor_family))
        donor = _instance(donor, _donor_axes(donor_family, weight))
        wanted = remaining & _font_cmap(donor)
        if wanted:
            copied = _copy_glyphs(target, donor, wanted)
            print(f"  从 {donor_family} 补充 {len(copied)} 个字形: "
                  + " ".join(f"U+{cp:04X}" for cp in sorted(copied)))
            remaining -= copied
        del donor
    return remaining


def build_subset(family: str, weight: int, chars: set[str], target: Path) -> None:
    font = TTFont(source_path(family))
    font = _instance(font, {"wght": weight})
    wanted = {ord(ch) for ch in chars if ch not in "\r\n\t"}
    missing = wanted - _font_cmap(font)
    subsetter = Subsetter()
    subsetter.populate(unicodes=wanted - missing)
    subsetter.subset(font)
    if missing:
        leftover = _add_donor_glyphs(font, family, weight, missing)
        if leftover:
            print("  警告: 源字体与补字字体都缺: "
                  + " ".join(f"U+{cp:04X}" for cp in sorted(leftover)))
    font.recalcTimestamp = False  # 固定 head.modified，保证重建哈希稳定
    font.flavor = "woff2"
    target.parent.mkdir(parents=True, exist_ok=True)
    font.save(target)


def _plain_heading(line: str) -> str:
    text = html.unescape(re.sub(r"<[^>]+>", " ", line))
    return EMOJI_RE.sub("", text).strip()


def _entry_titles(entries) -> list[str]:
    """清单段内所有带 title 的条目（兼容 schema 2 的列表结构）。"""
    if not isinstance(entries, list):
        return []
    return [str(entry["title"]) for entry in entries
            if isinstance(entry, dict) and entry.get("title")]


def stamp_text() -> str:
    """页眉/页脚可能出现的全部文字：书名、篇名、单元名、章名、附录与固定词。"""
    chunks = [STAMP_FIXED, STAMP_RUNNING_TITLES, *STAMP_SECTION_TITLES]
    manifest = json.loads(config.MANIFEST_PATH.read_text(encoding="utf-8"))
    chunks.append(str(manifest.get("title", "")))
    chunks.append(str(manifest.get("subtitle", "")))
    # schema 1 的单一附录标题。
    appendix = manifest.get("appendix")
    if isinstance(appendix, dict):
        chunks.append(str(appendix.get("title", "")))
    # schema 2 的四个清单段（Task 11A 起）；schema 1 下这些键缺省。
    chunks.extend(_entry_titles(manifest.get("front_matter")))
    for part in manifest.get("parts") or []:
        if not isinstance(part, dict):
            continue
        chunks.append(str(part.get("title", "")))
        chunks.extend(_entry_titles(part.get("units")))
    chunks.extend(_entry_titles(manifest.get("appendices")))
    chunks.extend(_entry_titles(manifest.get("back_matter")))
    for path in sorted(Path(config.DOCS).glob("*.md")):
        for line in path.read_text(encoding="utf-8").splitlines():
            match = re.match(r"^#{1,3}\s+(.*)$", line)
            if match:
                chunks.append(_plain_heading(match.group(1)))
    return "\n".join(chunks) + ASCII


def build_stamp(target: Path) -> None:
    font = TTFont(source_path(STAMP_FAMILY))
    font = _instance(font, {"wght": STAMP_WEIGHT})
    subsetter = Subsetter()
    subsetter.populate(
        unicodes={ord(ch) for ch in set(stamp_text()) if ch not in "\r\n\t"})
    subsetter.subset(font)
    font.recalcTimestamp = False  # 固定 head.modified，保证重建哈希稳定
    target.parent.mkdir(parents=True, exist_ok=True)
    font.save(target)


def _write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")


def build_all(out_dir: Path) -> None:
    missing = [str(path) for family in ALL_SOURCES for path in
               (source_path(family), SRC_DIR / ALL_SOURCES[family][1])
               if not path.is_file()]
    if missing:
        raise RuntimeError(
            "缺少源字体/许可文件，请先运行 --download:\n  " + "\n  ".join(missing))

    text_chars = {ch for ch in required_text() if ch not in "\r\n\t"}
    print(f"required_text: {len(text_chars)} 个唯一字符")
    out_dir.mkdir(parents=True, exist_ok=True)

    subsets = []
    for (family, weight), name in TARGETS.items():
        chars = set(ASCII) if family == "JetBrainsMono" else text_chars
        target = out_dir / name
        print(f"生成 {name} <- {source_path(family).name} @ wght={weight} "
              f"({len(chars)} 字符)")
        build_subset(family, weight, chars, target)
        subsets.append({
            "name": name,
            "family": family,
            "weight": weight,
            "characters": len(chars),
            "bytes": target.stat().st_size,
            "sha256": sha256_of(target),
        })

    stamp_target = out_dir / STAMP_FONT_NAME
    stamp_chars = set(stamp_text())
    print(f"生成 {STAMP_FONT_NAME} <- {source_path(STAMP_FAMILY).name} "
          f"@ wght={STAMP_WEIGHT} ({len(stamp_chars)} 字符)")
    build_stamp(stamp_target)

    licenses = []
    for family, (_url, license_name) in ALL_SOURCES.items():
        src = SRC_DIR / license_name
        dst = out_dir / license_name
        shutil.copyfile(src, dst)
        licenses.append({
            "name": license_name,
            "family": family,
            "url": license_url(ALL_SOURCES[family][0]),
            "bytes": dst.stat().st_size,
            "sha256": sha256_of(dst),
        })

    data = {
        "schema": 1,
        "generated_by": "scripts/subset_fonts.py",
        "required_text_characters": len(text_chars),
        "sources": [
            {
                "family": family,
                "role": ("glyph-donor" if family in GLYPH_SOURCES
                         else "primary"),
                "file": SOURCE_FILES[family],
                "url": url,
                "sha256": sha256_of(source_path(family)),
                "bytes": source_path(family).stat().st_size,
            }
            for family, (url, _license) in ALL_SOURCES.items()
        ],
        "subsets": subsets,
        "stamp": {
            "name": STAMP_FONT_NAME,
            "family": STAMP_FAMILY,
            "weight": STAMP_WEIGHT,
            "characters": len(stamp_chars),
            "bytes": stamp_target.stat().st_size,
            "sha256": sha256_of(stamp_target),
        },
        "licenses": licenses,
    }
    _write_json(out_dir / "sources.json", data)
    write_readme(out_dir / "README.md", data)
    print(f"写入 {out_dir / 'sources.json'} 与 {out_dir / 'README.md'}")


def _table(headers: list[str], rows: list[list[str]]) -> list[str]:
    lines = ["| " + " | ".join(headers) + " |",
             "|" + "|".join(" --- " for _ in headers) + "|"]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    return lines


def write_readme(path: Path, data: dict) -> None:
    subset_rows = [
        [f"`{entry['name']}`", entry["family"], str(entry["weight"]),
         str(entry["characters"]), f"{entry['bytes']:,}", f"`{entry['sha256']}`"]
        for entry in data["subsets"]
    ]
    stamp = data["stamp"]
    source_rows = [
        [entry["family"], entry["role"], f"`{entry['file']}`",
         f"<{entry['url']}>", f"{entry['bytes']:,}", f"`{entry['sha256']}`"]
        for entry in data["sources"]
    ]
    lines = [
        "# 书内字体子集",
        "",
        "《通往模拟电路之路》16K 印刷书使用的 OFL 字体子集。后续构建把它们以",
        "data URI 内联进单文件 HTML，因此本目录不需要任何系统字体或网络字体。",
        "",
        "## WOFF2 子集",
        "",
    ]
    lines += _table(
        ["文件", "家族", "字重", "请求字符数", "字节", "SHA-256"], subset_rows)
    lines += [
        "",
        "## 印章字体",
        "",
    ]
    lines += _table(
        ["文件", "家族", "字重", "请求字符数", "字节", "SHA-256"],
        [[f"`{stamp['name']}`", stamp["family"], str(stamp["weight"]),
          str(stamp["characters"]), f"{stamp['bytes']:,}",
          f"`{stamp['sha256']}`"]])
    lines += [
        "",
        "印章字体由 Noto Sans SC 在 wght=700 实例化后，子集到 ASCII、书名、",
        "前置页/篇/单元/附录/后记标题、章名与页脚固定词，用于页眉/页脚印章。",
        "",
        "## 源字体",
        "",
        "源文件缓存在仓库外的 `build/fonts-src/`（`.gitignore` 已忽略），",
        "重新生成时可凭 `sources.json` 中的 URL 与 SHA-256 校验。",
        "",
    ]
    lines += _table(
        ["家族", "角色", "文件", "URL", "字节", "SHA-256"], source_rows)
    lines += [
        "",
        "## 缺字补充",
        "",
        "Noto Serif SC 与 Noto Sans SC 的可变字体都不含书稿实际使用的 14 个",
        "字符：上标 `U+2070 U+2075 U+2076 U+2077 U+2078 U+2079`、下标",
        "`U+2080 U+2081 U+2082`、分数 `U+2153 U+2154`、组合上划线 `U+0305`、",
        "实心左指三角 `U+25C4` 与叉号 `U+2717`。子集脚本从同为 OFL 的 Noto Serif /",
        "Noto Sans（拉丁）复制前 12 个字符的真实轮廓，并从 Noto Sans Symbols 2 复制",
        "`U+25C4` 与 `U+2717`，再写入子集的 cmap/hmtx/vmtx；没有删减覆盖测试的字符。",
        "",
        "对勾 `U+2713` 原生存在于 Noto SC 中。`EMOJI_RE` 会剥掉 `✓✗`，而 Task 5",
        "把 ✅/❌ 映射为 `✓/✗` 输出，因此 `required_text()` 在剥离 emoji 后显式",
        "补入这两个字形，四个正文子集都必须覆盖它们。",
        "",
        "## 许可",
        "",
        "全部字体按 SIL Open Font License 1.1 发布，许可全文见同目录",
        "`OFL-*.txt`；源字体版权与保留字体名以对应文件为准。",
        "",
        "## 复现",
        "",
        "```bash",
        "python scripts/subset_fonts.py --download",
        "python scripts/subset_fonts.py --build",
        "python scripts/subset_fonts.py --check",
        "```",
        "",
        "`--build` 只读取 `build/fonts-src/`，不访问网络；`--check` 校验哈希、",
        "许可文件与 `required_text()` 覆盖率。`build/fonts-src/` 中的源 TTF/OTF",
        "与下载的许可文件不入仓。",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def _format_codepoints(chars: set[str]) -> str:
    return " ".join(f"U+{ord(ch):04X} {ch!r}" for ch in sorted(chars))


def _verify_file(out_dir: Path, entry: dict, errors: list[str]) -> Path | None:
    name = entry.get("name", "")
    path = out_dir / name
    if not name or Path(name).name != name:
        errors.append(f"sources.json 中的文件名无效: {name!r}")
        return None
    if not path.is_file():
        errors.append(f"缺少文件: {path}")
        return None
    size = path.stat().st_size
    if size != entry.get("bytes"):
        errors.append(f"{name} 字节数不符: {size} != {entry.get('bytes')}")
    digest = sha256_of(path)
    if digest != entry.get("sha256"):
        errors.append(f"{name} sha256 不符: {digest} != {entry.get('sha256')}")
    return path


def check(out_dir: Path) -> int:
    errors: list[str] = []
    manifest_path = out_dir / "sources.json"
    if not manifest_path.is_file():
        print(f"错误: 缺少 {manifest_path}，请先运行 --build", file=sys.stderr)
        return 1
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    if data.get("schema") != 1:
        errors.append(f"sources.json schema 应为 1: {data.get('schema')!r}")

    entries = {entry.get("name"): entry for entry in data.get("subsets", [])}
    if len(data.get("subsets", [])) != len(TARGETS):
        errors.append(
            f"sources.json 子集数量应为 {len(TARGETS)}: {len(data.get('subsets', []))}")
    for (family, weight), name in TARGETS.items():
        entry = entries.get(name)
        if entry is None:
            errors.append(f"sources.json 缺少子集: {name}")
            continue
        if entry.get("family") != family or entry.get("weight") != weight:
            errors.append(f"{name} 的 family/weight 记录不符")
        _verify_file(out_dir, entry, errors)

    stamp_entry = data.get("stamp") or {}
    if stamp_entry.get("name") != STAMP_FONT_NAME:
        errors.append(f"sources.json 缺少印章字体记录: {STAMP_FONT_NAME}")
    else:
        _verify_file(out_dir, stamp_entry, errors)

    licenses = {entry.get("name"): entry for entry in data.get("licenses", [])}
    for family, (_url, license_name) in ALL_SOURCES.items():
        entry = licenses.get(license_name)
        if entry is None:
            errors.append(f"sources.json 缺少许可记录: {license_name}")
            continue
        if entry.get("family") != family:
            errors.append(f"{license_name} 的 family 记录不符")
        _verify_file(out_dir, entry, errors)

    unique = {ch for ch in required_text() if ch not in "\r\n\t"}
    print(f"required_text: {len(unique)} 个唯一字符")
    for (family, weight), name in TARGETS.items():
        if family == "JetBrainsMono":
            continue
        missing = missing_glyphs(out_dir / name, "".join(sorted(unique)))
        print(f"覆盖 {name}: {len(unique) - len(missing)}/{len(unique)}")
        if missing:
            errors.append(f"{name} 缺字: {_format_codepoints(missing)}")

    mono_name = TARGETS[("JetBrainsMono", 400)]
    mono_missing = missing_glyphs(out_dir / mono_name, ASCII)
    print(f"覆盖 {mono_name}: ASCII {len(ASCII) - len(mono_missing)}/{len(ASCII)}")
    if mono_missing:
        errors.append(f"{mono_name} 缺字: {_format_codepoints(mono_missing)}")

    stamp_chars = set(stamp_text())
    stamp_missing = missing_glyphs(out_dir / STAMP_FONT_NAME, "".join(sorted(stamp_chars)))
    print(f"覆盖 {STAMP_FONT_NAME}: {len(stamp_chars) - len(stamp_missing)}/{len(stamp_chars)}")
    if stamp_missing:
        errors.append(
            f"{STAMP_FONT_NAME} 缺字: {_format_codepoints(stamp_missing)}")

    for title in (STAMP_TEST_TITLES,):
        title_missing = missing_glyphs(out_dir / STAMP_FONT_NAME, title)
        if title_missing:
            errors.append(
                f"{STAMP_FONT_NAME} 页眉标题缺字: {_format_codepoints(title_missing)}")

    if errors:
        for error in errors:
            print(f"错误: {error}", file=sys.stderr)
        return 1
    print(f"OK: {len(TARGETS)} 个 WOFF2 子集 + 印章字体 + "
          f"{len(ALL_SOURCES)} 份 OFL 许可均已校验")
    return 0


def main(argv=None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(
        description="下载、生成并校验 OFL 字体子集（build/fonts-src 不入仓）")
    parser.add_argument("--download", action="store_true",
                        help="从 raw.githubusercontent.com 下载源可变字体与 OFL.txt")
    parser.add_argument("--build", action="store_true",
                        help="从 build/fonts-src/ 重新生成 WOFF2 子集与印章 TTF")
    parser.add_argument("--check", action="store_true",
                        help="校验子集哈希、许可与 required_text() 覆盖率")
    parser.add_argument("--out", type=Path, default=config.FONTS_DIR,
                        help="子集输出目录（默认 analog-book/fonts）")
    args = parser.parse_args(argv)
    if not (args.download or args.build or args.check):
        parser.error("至少指定 --download、--build、--check 之一")
    out_dir = args.out.resolve()
    try:
        if args.download:
            download_sources()
        if args.build:
            build_all(out_dir)
        if args.build or args.check:
            return check(out_dir)
    except (OSError, RuntimeError, urllib.error.URLError) as exc:
        print(f"错误: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
