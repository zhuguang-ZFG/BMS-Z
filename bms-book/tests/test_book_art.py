"""章徽/篇题插画装载契约（book_art.py）。

这些测试是接线功能的 RED/GREEN 证据：合法章徽以 data URI 内联、契约违例装载即报错、
缺文件默认告警不 fail 而 --strict-emblems 缺一枚即 fail。全部用 tmp 目录造 fixture，
不依赖插画 worker 交付的真实章徽文件。
"""
from __future__ import annotations

import base64
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
try:
    import build_html
    from book_art import EmblemError, EmblemLibrary, chapter_stem, part_stem
finally:
    sys.path.pop(0)


@pytest.fixture
def emblem_root() -> Path:
    """独立 tmp 目录：不走 pytest 的 tmp_path 工厂（本机 D:/temp/User/pytest-of-* 有坏 ACL 残留）。"""
    root = Path(tempfile.mkdtemp(prefix="book-art-test-"))
    try:
        yield root
    finally:
        shutil.rmtree(root, ignore_errors=True)

GOOD_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48" fill="none" '
    'stroke="currentColor" stroke-width="2">'
    '<circle cx="24" cy="24" r="16"/><path d="M24 8v32"/></svg>'
)
# 篇题按卷 I part_art 语言：纸底 + 三色 + 拉丁 <text> 标签。
PART_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 120">'
    '<rect width="320" height="120" fill="#fffdf8"/>'
    '<path d="M24 76h120" stroke="#5eead4" stroke-width="3"/>'
    '<path d="M160 76h60" stroke="#f2b84b" stroke-width="3"/>'
    '<text x="24" y="30" font-family="sans-serif" font-size="12" fill="#94a3b8">PART 01</text>'
    '<text x="24" y="50" font-family="sans-serif" font-size="12" fill="#94a3b8">READING LAYERS</text>'
    '</svg>'
)


def write_emblem(root: Path, stem: str, svg: str) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    path = root / f"{stem}.svg"
    path.write_text(svg, encoding="utf-8")
    return path


def test_chapter_stem_mapping_covers_numbered_and_appendix_chapters():
    assert chapter_stem("00-前言.md") == "ch00"
    assert chapter_stem("01-电池里在发生什么.md") == "ch01"
    assert chapter_stem("32-高压安全与绝缘检测.md") == "ch32"
    assert chapter_stem("附录A-BMS-Z地图.md") == "ch33"
    assert chapter_stem("附录E-习题参考答案.md") == "ch37"
    assert chapter_stem("README.md") is None


def test_part_stem_mapping_follows_manifest_ids():
    assert part_stem("p0") == "part-p0"
    assert part_stem("p8") == "part-p8"


def test_valid_emblem_is_inlined_as_data_uri_image(emblem_root):
    write_emblem(emblem_root, "ch01", GOOD_SVG)
    html = EmblemLibrary(root=emblem_root).chapter_html("01-电池里在发生什么.md", "电池里在发生什么")

    assert 'class="chapter-emblem"' in html
    assert 'alt="章徽线描：电池里在发生什么"' in html
    match = re.search(r'src="data:image/svg\+xml;base64,([^"]+)"', html)
    assert match, html
    assert base64.b64decode(match.group(1)).decode("utf-8") == GOOD_SVG
    assert 'width="48" height="48"' in html


def test_valid_part_art_is_inlined_as_data_uri_image(emblem_root):
    write_emblem(emblem_root, "part-p1", GOOD_SVG)
    html = EmblemLibrary(root=emblem_root).part_html("p1", "从电芯到证据链")

    assert 'class="part-art"' in html
    assert 'alt="篇题线描：从电芯到证据链"' in html
    assert "data:image/svg+xml;base64," in html
    assert re.search(r'width="\d+" height="\d+"', html), html


def test_colored_part_art_with_latin_text_is_accepted(emblem_root):
    write_emblem(emblem_root, "part-p1", PART_SVG)
    html = EmblemLibrary(root=emblem_root).part_html("p1", "从电芯到证据链")

    assert 'class="part-art"' in html
    assert 'width="320" height="120"' in html
    assert EmblemLibrary(root=emblem_root).warnings == []


def test_part_art_rejects_cjk_labels(emblem_root):
    write_emblem(emblem_root, "part-p2", PART_SVG.replace("PART 01", "第二篇"))

    with pytest.raises(EmblemError, match="CJK"):
        EmblemLibrary(root=emblem_root).part_html("p2", "测量与估计")


def test_part_art_still_rejects_shared_blacklist(emblem_root):
    write_emblem(emblem_root, "part-p3", PART_SVG.replace("<rect", '<rect id="paper"'))

    with pytest.raises(EmblemError, match="禁用内容"):
        EmblemLibrary(root=emblem_root).part_html("p3", "安全与验证")


def test_part_art_allows_presentation_role_like_volume_one(emblem_root):
    svg = PART_SVG.replace("<svg ", '<svg role="presentation" ')
    write_emblem(emblem_root, "part-p4", svg)

    html = EmblemLibrary(root=emblem_root).part_html("p4", "把数据接到现场")
    assert 'class="part-art"' in html


def test_chapter_emblem_rejects_hex_colors_even_with_currentColor(emblem_root):
    write_emblem(emblem_root, "ch04", GOOD_SVG.replace("<circle", '<circle fill="#fffdf8"'))

    with pytest.raises(EmblemError, match="颜色字面量"):
        EmblemLibrary(root=emblem_root).chapter_html("04-保护板解剖.md", "保护板解剖")


@pytest.mark.parametrize("stem,name", [
    ("ch01", "01-电池里在发生什么.md"),
    ("ch34", "附录B-项目清单.md"),
])
def test_missing_emblem_warns_and_keeps_chapter_head_untouched(emblem_root, stem, name):
    library = EmblemLibrary(root=emblem_root)

    assert library.chapter_html(name, "任一章") == ""
    assert library.warnings and stem in library.warnings[0] and name in library.warnings[0]


def test_missing_part_art_warns_and_keeps_divider_untouched(emblem_root):
    library = EmblemLibrary(root=emblem_root)

    assert library.part_html("p0", "导读") == ""
    assert library.warnings and "part-p0.svg" in library.warnings[0]


def test_missing_emblem_dir_behaves_like_missing_files(emblem_root):
    library = EmblemLibrary(root=emblem_root / "absent")

    assert library.chapter_html("05-测量链.md", "测量链") == ""
    assert library.part_html("p2", "测量与估计") == ""
    assert len(library.warnings) == 2


def test_strict_mode_fails_on_missing_chapter_emblem(emblem_root):
    with pytest.raises(EmblemError, match="ch03"):
        EmblemLibrary(root=emblem_root, strict=True).chapter_html("03-电芯化学家族.md", "电芯化学家族")


def test_strict_mode_fails_on_missing_part_art(emblem_root):
    with pytest.raises(EmblemError, match="part-p5"):
        EmblemLibrary(root=emblem_root, strict=True).part_html("p5", "安全与验证")


def test_contract_violations_fail_even_outside_strict_mode(emblem_root):
    broken = {
        "no-viewBox": GOOD_SVG.replace('viewBox="0 0 48 48" ', ""),
        "no-currentColor": GOOD_SVG.replace("currentColor", "#176b73"),
        "id-attr": GOOD_SVG.replace("<circle", '<circle id="dot"'),
        "href-attr": GOOD_SVG.replace("</svg>", '<use href="#x"/></svg>'),
        "css-url": GOOD_SVG.replace("<circle", '<circle fill="url(#g)"'),
        "script-tag": GOOD_SVG.replace("</svg>", "<script>alert(1)</script></svg>"),
        "text-element": GOOD_SVG.replace("</svg>", "<text>48</text></svg>"),
        "role-attr": GOOD_SVG.replace("<svg ", '<svg role="img" '),
        "aria-label": GOOD_SVG.replace("<svg ", '<svg aria-label="章徽" '),
        "data-uri-attr": GOOD_SVG.replace("<circle", '<circle fill="data:image/png;base64,AAA"'),
        "event-attr": GOOD_SVG.replace("<circle", '<circle onload="x()"'),
        "xlink": GOOD_SVG.replace("</svg>", '<use xlink:href="#x"/></svg>'),
        "double-root": GOOD_SVG + GOOD_SVG,
    }
    library = EmblemLibrary(root=emblem_root)
    for label, svg in broken.items():
        write_emblem(emblem_root, "ch02", svg)
        with pytest.raises(EmblemError) as exc:
            library.chapter_html("02-BMS的六件事.md", "BMS的六件事")
        assert "ch02.svg" in str(exc.value), label
        assert library.warnings == [], label


def test_oversize_emblem_is_rejected(emblem_root):
    write_emblem(emblem_root, "ch09", GOOD_SVG.replace("</svg>", "<!--" + "x" * 6000 + "--></svg>"))
    assert len((emblem_root / "ch09.svg").read_bytes()) > 6000
    with pytest.raises(EmblemError, match="6000"):
        EmblemLibrary(root=emblem_root).chapter_html("09-均衡.md", "均衡")


def test_build_defaults_to_non_strict_and_ships_display_css():
    assert build_html.STRICT_EMBLEMS is False
    for fragment in (".chapter-head", ".chapter-emblem", ".part-art"):
        assert fragment in build_html.CSS


def test_cli_advertises_strict_emblems_flag():
    result = subprocess.run(
        [sys.executable, str(ROOT / "build_html.py"), "--help"],
        capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0
    assert "--strict-emblems" in result.stdout
