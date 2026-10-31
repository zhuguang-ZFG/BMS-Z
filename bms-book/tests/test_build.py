"""Validate the artifact readers actually open, including offline math and links."""
from collections import Counter
from html.parser import HTMLParser
import importlib.util
import os
from pathlib import Path
import json
import re
import xml.etree.ElementTree as ET
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]


class Document(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.labelledby = []
        self.fragments = []
        self.images = []
        self.scripts = []
        self.routes = []
        self.chapters = []
        self.chapter_navigation = 0
        self.chapter_compasses = []
        self._inside_compass = False
        self._capture_compass_term = False
        self._compass_term = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.append(attrs["id"])
        if "aria-labelledby" in attrs:
            self.labelledby.extend(attrs["aria-labelledby"].split())
        if tag == "a" and attrs.get("href", "").startswith("#"):
            self.fragments.append(attrs["href"][1:])
        if tag == "img":
            self.images.append(attrs)
        if tag == "script" and "src" in attrs:
            self.scripts.append(attrs["src"])
        if tag == "a" and attrs.get("class") == "route-card":
            self.routes.append(attrs["href"])
        if tag == "section" and attrs.get("class") == "chapter":
            self.chapters.append(attrs)
            self.chapter_compasses.append([])
        if tag == "nav" and attrs.get("class") == "chapter-nav":
            self.chapter_navigation += 1
        if tag == "aside" and "chapter-compass" in attrs.get("class", "").split():
            self._inside_compass = True
            self.chapter_compasses[-1].append({"attrs": attrs, "terms": []})
        if tag == "dt" and self._inside_compass:
            self._capture_compass_term = True
            self._compass_term = []

    def handle_data(self, data):
        if self._capture_compass_term:
            self._compass_term.append(data)

    def handle_endtag(self, tag):
        if tag == "dt" and self._capture_compass_term:
            self.chapter_compasses[-1][-1]["terms"].append(
                "".join(self._compass_term).strip()
            )
            self._capture_compass_term = False
            self._compass_term = []
        if tag == "aside" and self._inside_compass:
            self._inside_compass = False


@pytest.fixture(scope="module")
def artifact(tmp_path_factory):
    out = tmp_path_factory.mktemp("book-artifact")
    result = subprocess.run(
        [sys.executable, str(ROOT / "build_html.py"), "--out-dir", str(out)],
        capture_output=True, encoding="utf-8", timeout=120,
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
    )
    assert result.returncode == 0, result.stdout + result.stderr
    text = (out / "bms-book.html").read_text(encoding="utf-8")
    doc = Document()
    doc.feed(text)
    return doc, text


def test_chapter_links_and_svg_ids_are_unique(artifact):
    doc, _ = artifact
    duplicates = [id for id, count in Counter(doc.ids).items() if count > 1]
    assert not duplicates, duplicates[:10]
    assert set(doc.fragments) <= set(doc.ids)
    assert len([id for id in doc.ids if id.startswith("ch-") and len(id) == 5]) == len(load_checker().EXPECTED_FILES)

def test_aria_labelledby_targets_exist(artifact):
    doc, _ = artifact
    assert set(doc.labelledby) <= set(doc.ids)


def test_numbered_chapters_have_one_editorial_compass(artifact):
    doc, _ = artifact
    manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    files = [file for part in manifest["parts"] for file in part["files"]]
    assert len(doc.chapter_compasses) == len(files)
    for file, compasses in zip(files, doc.chapter_compasses, strict=True):
        if file[:2].isdigit() and not file.startswith("00-"):
            assert len(compasses) == 1, file
            assert compasses[0]["attrs"].get("aria-label") == "本章罗盘"
            assert compasses[0]["terms"] == ["本章要回答", "读完应交出", "这一章不证明"]
        else:
            assert compasses == [], file

@pytest.mark.parametrize("name", [
    "hppc-identifiability", "innovation-evidence", "kalman-observation-weight",
    "hppc-pulse", "ocv-four-terms", "aging-two-clocks", "residual-fingerprints",
    "voltage-red-lines", "thermal-horizon", "discharge-energy-budget",
])
def test_scientific_figure_canvas_uses_shared_paper(name):
    palette = json.loads((ROOT.parent / "tools/visual_palette.json").read_text(encoding="utf-8"))["light"]
    image = ET.parse(ROOT / "assets" / f"{name}.svg").getroot()
    background = image.find(".//*[@id='patch_1']/{http://www.w3.org/2000/svg}path")
    fill = re.search(r"fill:\s*(#[0-9a-f]{6})", background.get("style", ""))
    assert fill and fill[1] in {palette["paper"], palette["surface"]}


@pytest.mark.parametrize("name", ["hppc-pulse", "ocv-four-terms", "aging-two-clocks", "residual-fingerprints"])
def test_numerical_step_captions_use_ink_on_series_tints(name):
    from test_visual_style import contrast_ratio

    palette = json.loads((ROOT.parent / "tools/visual_palette.json").read_text(encoding="utf-8"))["light"]
    ns = "{http://www.w3.org/2000/svg}"
    svg = ET.parse(ROOT / "assets" / f"{name}.svg").getroot()
    steps = svg.find(".//*[@id='axes_1']")
    captions = [node for node in steps.findall(ns + "g") if node.get("id", "").startswith("text_")]
    panels = [node for node in steps.iter(ns + "path") if "opacity: 0.14" in node.get("style", "")]
    assert captions and len(captions) == len(panels)
    for caption, panel in zip(captions, panels, strict=True):
        foreground = re.search(r"fill: (#[0-9a-f]{6})", caption.find(ns + "g").get("style"))[1]
        tint = re.search(r"fill: (#[0-9a-f]{6})", panel.get("style"))[1]
        background = "#" + "".join(
            f"{round(int(tint[i:i + 2], 16) * 0.14 + int(palette['surface'][i:i + 2], 16) * 0.86):02x}"
            for i in (1, 3, 5)
        )
        assert foreground == palette["ink"]
        assert contrast_ratio(foreground, background) >= 4.5


@pytest.mark.parametrize("name,digest", [
    ("hppc-identifiability", "9474fb24a39c4a328ae296efbce934b1108bd7c0daea18c02f078bd685ccf964"),
    ("innovation-evidence", "9bee8a02c228f45ade7346b02297ee49af6fc78f7fa9f55241b2f2dacfa6dd3b"),
    ("kalman-observation-weight", "d4e957f8b071df3bf1b3eb49cf0fe0910194e32c72d977e7d7568ea59fb9a52c"),
    ("hppc-pulse", "d2adb976de2c37063e96e66cdddb9df4ce045d5821920657f4799ed0c665ea13"),
    ("ocv-four-terms", "20e800bf94f2270fabcd88485ec7dc57440dd434bcc96152d3c2a148964b88ec"),
    ("aging-two-clocks", "418919c92fee14e7f018163c3e145541dde79a8f06d9ec0438770a92baee9903"),
    ("residual-fingerprints", "b235c1866d3180427ab247b775cbde7385cbe5802e6767821916f80db849a4f3"),
    ("voltage-red-lines", "a0c4f5d9b0ee84e4e468ce06524a4f63944f4769a7e28e9298ec07bfbda9b93d"),
    ("thermal-horizon", "7588c32a2dda597c1998f30dbf54dfc3fbf651cce950759ae34d6c3a68e70645"),
    ("discharge-energy-budget", "f6a18182343a9ec6391fe2b4bd3db4dc8d92be2f944edcae35d12c1dfb5d7d8d"),
])
def test_numerical_svg_ids_and_references_are_stable(name, digest):
    import hashlib

    source = (ROOT / "assets" / f"{name}.svg").read_text(encoding="utf-8")
    references = re.findall(r'(?:\bid="[^"]+"|(?:xlink:)?href="#[^"]+"|url\(#[^)]+\))', source)
    assert hashlib.sha256("\n".join(references).encode()).hexdigest() == digest


def test_generated_animation_theme_matches_shared_palette():
    sys.path.insert(0, str(ROOT.parent / "tools"))
    try:
        import gen_mechanism_svgs
    finally:
        sys.path.pop(0)
    palette = json.loads((ROOT.parent / "tools/visual_palette.json").read_text(encoding="utf-8"))
    svg = ET.fromstring(gen_mechanism_svgs.wrap("title", "description", "", 400, "test"))
    style = svg.findtext("{http://www.w3.org/2000/svg}style")
    backgrounds = re.findall(r"\.bg\s*\{\s*fill:\s*(#[0-9a-f]{6})", style)
    assert backgrounds == [palette[mode]["paper"] for mode in ("light", "dark")]
    for mode in ("light", "dark"):
        for name in ("blue", "red", "green", "gold"):
            assert palette[mode]["technical"][name] in style


def test_portal_uses_shared_illustration_with_reserved_layout_space():
    doc = Document()
    doc.feed((ROOT.parent / "BMS学习路径.html").read_text(encoding="utf-8"))
    image = next((image for image in doc.images
                  if image.get("class") == "portal-illustration"), None)
    assert image is not None
    assert image["src"] == "docs/public/illustrations/bms-scrapbook.svg"
    assert image.get("alt") and image.get("width") and image.get("height")
    assert all(image.get("loading") == "lazy" for image in doc.images[1:])


def test_copied_portal_resolves_public_illustrations_without_rewriting_external_urls(tmp_path):
    vitepress = tmp_path / "docs/.vitepress"
    vitepress.mkdir(parents=True)
    (vitepress / "dist").mkdir()
    script = vitepress / "copy-site-assets.mjs"
    script.write_bytes((ROOT.parent / "docs/.vitepress/copy-site-assets.mjs").read_bytes())
    (vitepress / "site-assets.json").write_text(
        json.dumps({"assets": {"portal.html": "portal.html"}}), encoding="utf-8",
    )
    (tmp_path / "portal.html").write_text(
        '<img src="docs/public/illustrations/cover.svg">'
        '<img src="docs/circuits/assets/plot.svg">'
        '<a href="https://example.org/docs/public/illustrations/cover.svg">source</a>',
        encoding="utf-8",
    )
    subprocess.run(["node", str(script)], check=True, capture_output=True)
    result = (vitepress / "dist/portal.html").read_text(encoding="utf-8")
    assert '<img src="illustrations/cover.svg">' in result
    assert '<img src="circuits/assets/plot.svg">' in result
    assert 'href="https://example.org/docs/public/illustrations/cover.svg"' in result


def test_cover_illustration_is_embedded_and_accessible_offline(artifact):
    import base64

    doc, _ = artifact
    covers = [image for image in doc.images if image.get("class") == "cover-illustration"]
    assert len(covers) == 1
    cover = covers[0]
    assert cover.get("alt") and cover.get("width") and cover.get("height")
    assert cover["src"].startswith("data:image/svg+xml;base64,")
    svg = ET.fromstring(base64.b64decode(cover["src"].split(",", 1)[1]))
    ns = {"svg": "http://www.w3.org/2000/svg"}
    assert svg.get("role") == "img"
    assert svg.findtext("svg:title", namespaces=ns)
    assert svg.findtext("svg:desc", namespaces=ns)
    assert not svg.findall(".//svg:script", ns)
    assert not any(node.get("href", "").startswith(("http:", "https:")) for node in svg.iter())


def test_formulas_and_figures_work_offline(artifact):
    doc, text = artifact
    assert "mjx-container" in text
    assert 'data-mml-node="merror"' not in text
    assert not doc.scripts
    assert doc.images
    assert all(img["src"].startswith("data:image/svg+xml;base64,") for img in doc.images)
    assert all(img.get("width") and img.get("height") for img in doc.images)
    assert "<!--CALLOUT:" not in text
    assert "::: story" not in text


def test_each_main_part_has_one_opening_bet(artifact):
    _, text = artifact
    manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    assert text.count('class="reading-bet"') == 7
    for part in manifest["parts"]:
        if part["id"] not in {"p1", "p2", "p3", "p4", "p5", "p6", "p7"}:
            continue
        count = sum(
            'class="reading-bet"' in (ROOT / "book" / name).read_text(encoding="utf-8")
            for name in part["files"]
        )
        assert count == 1, part["id"]


def test_motion_has_offline_sources_and_static_fallbacks(artifact):
    doc, text = artifact
    motion = [img for img in doc.images if 'data-motion-src' in img]
    assert len(motion) == 34
    assert all(img['data-motion-src'].startswith('data:image/svg+xml;base64,') for img in motion)
    assert 'data-mode="static"' in text
    assert 'beforeprint' in text
    for lab in ("ocv", "sop", "thermal", "protection"):
        assert f'data-book-lab="{lab}"' in text
    assert "mountCalmReader(document)" in text
    assert "reader-tools" in text
    assert "reader-progress" in text


def test_reader_preferences_apply_before_first_paint(artifact):
    """静读与字号必须在 <head> 里、首次绘制前落到 <html>。

    放到 </body> 前的整书脚本里才应用的话，存了偏好的读者每次打开都会先看到
    默认版式、再被跳一下（实测字号差 2.6 px、正文左缘差 187 px、侧栏闪现一次）。
    """
    _, text = artifact
    head = text[: text.index("</head>")]
    # 取 <head> 里的内联脚本本身来判断，不能只 grep "book-calm"——样式表里也有
    # html.book-calm 规则，拿它当凭据会把「脚本被挪走了」这件事漏过去。
    scripts = re.findall(r"<script>(.*?)</script>", head, re.S)
    boot = [s for s in scripts if "--book-reader-scale" in s and "localStorage" in s]
    assert boot, f"<head> 里没有首屏偏好脚本（找到 {len(scripts)} 段内联脚本）"
    assert "book-calm" in boot[0], "首屏脚本没有落静读类"
    # 必须排在样式表之前：先落类与变量，再让样式表按最终状态算第一帧。
    assert head.index(boot[0]) < head.index("<style>"), "首屏偏好脚本应排在 <style> 之前"
    assert "</script" not in boot[0].lower(), "内联脚本含 </script 会截断文档"


def _css_text() -> str:
    """离线整书的样式表：CSS 与 VISUAL_CSS 拼起来就是浏览器拿到的那份。

    build_html 顶层 import index_terms（同目录模块），所以先把 ROOT 放进 sys.path，
    与下面 check.py 的加载方式一致。
    """
    sys.path.insert(0, str(ROOT))
    try:
        spec = importlib.util.spec_from_file_location("build_html", ROOT / "build_html.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.CSS + module.VISUAL_CSS
    finally:
        sys.path.pop(0)


def _block(css: str, header: str) -> str:
    """取出某个 @media 块的花括号内容（按括号配平扫，嵌套的 @page 也能带出来）。

    header 本身已经带上了那个 `{`，所以深度从 1 起算：从 0 起算时，块内第一条
    规则的 `}` 就会把深度带回 0、当场收尾，只截到第一条规则。
    """
    start = css.index(header) + len(header)
    depth, end = 1, len(css)
    for i in range(start, len(css)):
        if css[i] == "{":
            depth += 1
        elif css[i] == "}":
            depth -= 1
            if depth == 0:
                end = i
                break
    return css[start:end]


# 颜色相关的变量：深色模式必须逐个重报。--page 以外还有卷首/分部页自己那组
# --feature-*，漏掉任何一个，深底正文里就会留着一块奶白（上一轮正是封面与
# 九张分部页整片发白，实测 15.4:1）。
_COLOR_TOKENS = (
    "--ink", "--muted", "--border", "--border-strong", "--paper", "--surface",
    "--soft", "--page", "--accent", "--link",
    "--feature-paper", "--feature-ink", "--feature-muted", "--feature-border",
)


def test_dark_mode_overrides_every_colour_token():
    css = _css_text()
    root = _block(css, ":root {")
    dark = _block(css, "@media screen and (prefers-color-scheme:dark) {")
    declared = {t for t in _COLOR_TOKENS if f"{t}:" in root}
    assert declared == set(_COLOR_TOKENS), f"色板漏声明：{set(_COLOR_TOKENS) - declared}"
    missing = [t for t in _COLOR_TOKENS if f"{t}:" not in dark]
    assert not missing, f"深色模式没重报这些颜色变量：{missing}"


def test_every_part_has_its_own_accent_in_screen_and_dark():
    """九个分部（含导读 p0）各有一档主题色，章与分部页共用，深色模式同样逐个重报。

    钉两件事：一是 p0 不能沿用默认值（否则导读与第一部分同色），二是深色模式
    必须重报八个编号分部 + p0——`.dark`/`@media dark` 里只写一个 --accent 时，
    分部色会在深色模式下一起塌成同一个颜色。
    """
    css = _css_text()
    manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    parts = [p["id"] for p in manifest["parts"]]
    assert parts[0] == "p0" and len(parts) == 9
    dark = _block(css, "@media screen and (prefers-color-scheme:dark) {")
    screen_colours, dark_colours = {}, {}
    for part in parts:
        pattern = re.compile(
            re.escape(f'[data-part="{part}"] {{ --accent:') + r"(#[0-9a-f]{6})",
        )
        for label, scope, store in (
            ("屏幕", css, screen_colours), ("深色", dark, dark_colours),
        ):
            match = pattern.search(scope)
            assert match, f"{part} 在{label}模式没有主题色"
            store[part] = match.group(1)
    for label, colours in (("屏幕", screen_colours), ("深色", dark_colours)):
        assert len(set(colours.values())) == 9, f"{label}模式分部色有重复：{colours}"
    palette = json.loads((ROOT.parent / "tools/visual_palette.json").read_text(encoding="utf-8"))
    assert screen_colours == palette["light"]["parts"]
    assert dark_colours == palette["dark"]["parts"]


def test_dark_screen_palette_cannot_leak_into_print():
    """系统偏好深色时，打印仍须使用浅色墨色与九个分部色。"""
    headers = re.findall(r"@media\s+([^{}]+)\{", _css_text())
    dark = [header.strip() for header in headers if "prefers-color-scheme" in header]
    assert dark == ["screen and (prefers-color-scheme:dark)"], \
        f"深色变量必须限于屏幕，不能套到白纸上：{dark}"


def test_print_forces_light_svg_theme():
    """Printing from a dark OS must not send dark SVG figures to paper."""
    printed = _block(_css_text(), "@media print {")
    root = re.search(r":root\s*\{([^}]*)\}", printed)
    assert root and re.search(r"color-scheme\s*:\s*light", root[1])


def test_print_keeps_one_palette_with_the_screen_edition():
    """打印只换纸色，不换色板：墨色与分部色沿用共享 LIGHT 那一套。

    上一轮打印块把 :root 重置成一整套冷色（--ink/--accent 等），却没有同时改
    分部页的暖色规则，于是印出来「暖色分部页 + 冷色章内强调」同页混排。
    """
    css = _css_text()
    root = _block(css, ":root {")
    printed = _block(css, "@media print {")
    light = json.loads((ROOT.parent / "tools/visual_palette.json").read_text(encoding="utf-8"))["light"]
    roles = {f"--{name}": light[name] for name in ("ink", "muted", "accent", "link")}
    roles.update({
        "--border": light["line"], "--border-strong": light["line_strong"],
        "--feature-ink": light["ink"], "--feature-muted": light["muted"],
        "--feature-border": light["line"],
        "--good": light["technical"]["green"], "--danger": light["technical"]["red"],
        "--ochre": light["technical"]["gold"], "--purple": light["technical"]["purple"],
    })
    for token, colour in roles.items():
        assert f"{token}:{colour};" in root, f"{token} 未沿用共享 LIGHT 色板"
        assert f"{token}:" not in printed, f"打印块不该重置 {token}：它会和分部色脱节"
    assert "--paper:#ffffff" in printed, "打印应退成白纸（纸色底满版铺油墨）"
    assert "--page:#ffffff" in printed, "纸面外背景也应退成白色"
    assert "--feature-paper:#ffffff" in printed, "卷首与分部页同样退成白纸"
    assert "box-shadow:none" in _block(printed, "body {"), "打印不应留下纸面投影"
    assert not re.search(r'\[data-part="p\d"\] \{ --accent:', printed), \
        "打印块不该再单独定义分部色"


def test_site_print_preserves_light_semantics_and_part_colours():
    css = (ROOT.parent / "docs/.vitepress/theme/custom.css").read_text(encoding="utf-8")
    palette = json.loads((ROOT.parent / "tools/visual_palette.json").read_text(encoding="utf-8"))
    screen_blocks = re.findall(r"@media screen\s*\{", css)
    assert len(screen_blocks) == 2, "深色基础色与分部色都应限于屏幕"
    printed = _block(css[css.index("/* —— 全站打印"):], "@media print {")
    for role in ("ink", "muted", "accent", "link", "red", "green", "gold", "purple"):
        assert f"--bms-{role}:" not in printed, f"打印不应改写浅色语义色 {role}"
    assert "color: #000 !important" not in printed
    for part, colour in palette["light"]["parts"].items():
        assert f".book-reading.book-part-{part} {{ --book-accent: {colour}; }}" in css
    assert "--bms-paper: #fff;" in printed
    for selector in (".timing-phase", ".timing-legend span:not(.timing-limit)::before", ".pack-cell__fill"):
        assert selector in printed, f"打印必须保留承载数据的图形 {selector}"
    assert "background-color: var(--vp-c-brand-1) !important" in printed
    assert "print-color-adjust: exact" in printed


def test_reader_teardown_leaves_persisted_preferences_on_html():
    """拆挂载只能拆自己建的东西：静读类与字号变量是读者偏好，不是本次挂载的副作用。

    逐章路由每次切页都「先 cleanup 再重挂」，cleanup 里顺手重置这两项的话，
    重挂前那几帧会按默认版式渲染——实测静读读者的 CLS 从 0.019 涨到 0.605
    （Google 的「差」线是 0.25），正文左缘跳 187 px、字号跳 2.6 px、侧栏闪现。
    这是源码级看门：钉住 cleanup 的形状，真实行为另有浏览器实测。
    """
    source = (ROOT / "reader.js").read_text(encoding="utf-8")
    teardown = source[source.index("/**\n   * 只拆监听"):]
    assert "classList.remove('book-calm')" not in teardown, "cleanup 不应摘掉静读类"
    assert "removeProperty('--book-reader-scale')" not in teardown, "cleanup 不应清掉字号变量"
    # 自己加的监听必须逐个摘干净（少摘一个就会在切页时越积越多）。
    for listener in ("toggleCalm", "onSmaller", "onLarger", "updateProgress"):
        assert f"removeEventListener('click', {listener})" in teardown \
            or f"removeEventListener('scroll', {listener})" in teardown \
            or f"removeEventListener('resize', {listener})" in teardown, \
            f"cleanup 漏摘 {listener}"


def test_calm_toggle_reports_state_not_the_next_action(artifact):
    """静读开关键的文字必须固定，状态只由 aria-pressed 表达。

    按状态把文字换成「退出静读」会同时坏两件事：读屏念出「退出静读，已按下」
    ——标签说下一步动作、aria-pressed 说当前状态，两句自相矛盾；四字比两字宽，
    一点就把工具条撑宽 23 px、右边三个控件一起右移 23 px，想接着点「字＋」
    会发现它已经从指针下挪走了（两者都在浏览器里实测过）。
    """
    source = (ROOT / "reader.js").read_text(encoding="utf-8")
    assert "'退出静读'" not in source and '"退出静读"' not in source, \
        "静读键不应按状态改文字：读屏会自相矛盾，工具条还会跳宽"
    assert "calmButton.setAttribute('aria-pressed'" in source, "静读键必须报 aria-pressed"
    # 文字不变之后，状态全靠这一档样式——两份样式表都得有实底的按下态。
    _, text = artifact
    assert '.reader-tools button[aria-pressed="true"]' in text, "离线版缺按下态样式"
    site_css = (ROOT.parent / "docs" / ".vitepress" / "theme" / "custom.css").read_text(encoding="utf-8")
    assert ".reader-tools button[aria-pressed='true']" in site_css, "线上版缺按下态样式"


def test_reader_toolbar_is_a_group_not_a_landmark(artifact):
    """四个按钮的设置条是控件组，不该占一个页面地标。

    带 aria-label 的 <aside> 会映射成 complementary 地标（HTML-AAM），而整书
    本来就有 160 个地标（逐章导读卡、来源锚点、翻页导航，都是读者真会跳的目标）。
    再塞一个设置条只是噪声。无障碍树实测：改成 role="group" 后地标 161→160。
    """
    source = (ROOT / "reader.js").read_text(encoding="utf-8")
    block = source[source.index("tools.id = 'book-reader-tools'"):source.index("doc.body.append")]
    assert "createElement('aside')" not in source[source.index("const tools ="):source.index("tools.innerHTML")], \
        "工具条不应用 <aside>（会变成 complementary 地标）"
    assert "setAttribute('role', 'group')" in block, "工具条应声明 role=group"
    # 工具条是运行时建的，所以产物里查的是内嵌脚本本身，不是静态标签。
    _, text = artifact
    assert "setAttribute('role', 'group')" in text, "内嵌脚本里没有 role=group"


def test_theme_entry_cancels_the_pending_mount_frame():
    """切页比两帧更快时，未兑现的那一帧必须取消，否则漏监听。

    旧写法先把 cleanupReader 置空、再排 rAF：第二次调用时句柄已是 undefined，
    拆不掉第一次挂的 scroll/resize，那一对就永久留在 window 上对着已摘除的
    进度条节点做无用功（实测连挂 3 次漏 4 个监听）。
    """
    entry = (ROOT.parent / "docs" / ".vitepress" / "theme" / "index.ts").read_text(encoding="utf-8")
    assert "cancelAnimationFrame" in entry, "没有取消未兑现的挂载帧"
    mount = entry[entry.index("const mountReader"):entry.index("const previousAfterRouteChange")]
    # 取消必须发生在 cleanup 与置空之前，否则等于没取消。
    assert mount.index("cancelAnimationFrame") < mount.index("cleanupReader?.()"), \
        "取消挂载帧要排在 cleanup 之前"


def test_vector_print_snapshots_are_static_and_complete():
    entries = json.loads((ROOT / 'visuals.json').read_text(encoding='utf-8'))
    for entry in entries:
        svg = ET.parse(ROOT / 'assets/print' / entry['file']).getroot()
        assert svg.get('data-snapshot-time') == str(entry['time'])
        tags = [node.tag.split('}')[-1] for node in svg.iter()]
        assert 'text' in tags and 'title' in tags
        assert not {'animate', 'animateMotion', 'animateTransform', 'set'} & set(tags)


def test_ocv_print_does_not_freeze_a_partially_drawn_relaxation_curve():
    svg = ET.parse(ROOT / 'assets/print/ocv-rest-timeline.svg').getroot()
    curves = [path for path in svg.iter('{http://www.w3.org/2000/svg}path')
              if path.get('id') == 'relaxation-curve'
              or (path.get('pathLength') and path.get('stroke-dasharray') == path.get('pathLength'))]
    assert curves, '印刷图必须保留松弛曲线'
    for path in curves:
        assert path.get('d'), '松弛曲线不能是空路径'
        offset = float(path.get('stroke-dashoffset', '0').removesuffix('px'))
        assert offset <= 0, '印刷图的松弛曲线必须完整，不能在动画绘制中途定格'


def test_reading_routes_and_chapter_labels_reach_real_content(artifact):
    doc, text = artifact
    assert len(doc.routes) >= 3
    assert all(route[1:] in doc.ids for route in doc.routes)
    assert all(chapter["aria-labelledby"] in doc.ids for chapter in doc.chapters)
    assert len(doc.chapters) == len(load_checker().EXPECTED_FILES)
    assert "把越限变成有时间预算的动作" in text
    assert "4.50 mV" in text
    assert doc.chapter_navigation == len(doc.chapters)


def test_source_anchors_render_and_match_manifest(artifact):
    from html import escape as html_escape
    doc, text = artifact
    manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    expected_cards = len(manifest["chapter_sources"])
    assert text.count('class="source-anchors"') == expected_cards
    assert 'id="ch-38-sources"' in text
    for sid, entry in manifest["sources"].items():
        assert html_escape(entry["title"]) in text, f"来源登记表缺少条目 {sid}"
    assert "73dbde670f7e9ec59afc33855bcf27576bd874de" in text  # foxBMS 快照钉死
    assert "779d20199bff2666e01371ce2f562dcda4d6bda3" in text  # LibreSolar 快照钉死


def test_oshwa_it000007_maps_to_greenbms():
    manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    source = manifest["sources"]["oshwa-it000007"]
    assert "GreenBMS" in source["title"]
    assert "SmartBMS" in source["title"]
    assert "LibreSolar" not in source["title"]
    appendix = (ROOT / "book" / "附录D-参考资料.md").read_text(encoding="utf-8")
    assert "OSHWA IT000007（GreenBMS / SmartBMS）" in appendix

def load_checker():
    sys.path.insert(0, str(ROOT))
    try:
        spec = importlib.util.spec_from_file_location("book_checker", ROOT / "check.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        sys.path.pop(0)


def test_missing_chapter_reports_failure_without_traceback(tmp_path, monkeypatch):
    checker = load_checker()
    monkeypatch.setattr(checker, "BOOK", tmp_path)
    monkeypatch.setattr(checker, "check_assets", lambda: None)
    monkeypatch.setattr(checker, "check_demos", lambda: None)
    monkeypatch.setattr(checker, "check_version", lambda: None)
    with pytest.raises(SystemExit) as failure:
        checker.main()
    assert failure.value.code == 1
    assert any("缺少" in msg for msg in checker.failures)


def test_section_refs_catch_bad_refs_and_exempt_external_contexts():
    """§ 小节引用门：坏引用报红；同章合法引用与外部文档语境（字母后缀、三级编号、协议、阶段）放行。"""
    checker = load_checker()
    checker.failures.clear()
    checker.build_section_map()
    checker.check_refs(
        "05-测量链.md",
        "先看 §5.10 再回 §1.2–§1.5\n"
        "外部 §4.7b 与 §0.1.6 豁免\n"
        "技术协议 §3.2 豁免\n"
        "BMS-Z 阶段 4（§4.8 工程落地）",
    )
    assert len(checker.failures) == 1
    assert "§5.10" in checker.failures[0]


@pytest.mark.parametrize("name", ["cccv_charge.py", "thermal_lump.py"])
def test_demos_can_print_in_a_chinese_windows_console(name):
    result = subprocess.run(
        [sys.executable, str(ROOT / "code" / name)],
        capture_output=True, encoding="gbk", timeout=30,
        env={**os.environ, "PYTHONIOENCODING": "gbk:strict"},
    )
    assert result.returncode == 0, result.stdout + result.stderr
