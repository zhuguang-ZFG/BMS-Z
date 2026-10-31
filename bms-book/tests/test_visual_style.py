"""Dependency-free palette and authored SVG paint contracts."""
import ast
import copy
from itertools import combinations
import json
import math
from pathlib import Path
import re
import xml.etree.ElementTree as ET

import pytest


PALETTE_PATH = Path(__file__).resolve().parents[2] / "tools" / "visual_palette.json"
MODES = ("light", "dark")
SCALAR_TOKENS = (
    "paper", "surface", "soft", "ink", "muted", "line", "line_strong",
    "accent", "link",
)
GROUP_TOKENS = {
    "notes": ("yellow", "mint", "rose"),
    "technical": ("blue", "red", "green", "gold", "purple"),
    "parts": tuple(f"p{index}" for index in range(9)),
}


def load_palette():
    assert PALETTE_PATH.is_file(), f"Missing palette: {PALETTE_PATH}"
    return json.loads(PALETTE_PATH.read_text(encoding="utf-8"))


def linear_rgb(color):
    channels = [int(color[index:index + 2], 16) / 255 for index in (1, 3, 5)]
    return tuple(
        channel / 12.92 if channel <= 0.04045
        else ((channel + 0.055) / 1.055) ** 2.4
        for channel in channels
    )


def contrast_ratio(first, second):
    """WCAG relative luminance for opaque sRGB colors (no rounded pass/fail)."""
    def luminance(color):
        return sum(channel * weight for channel, weight in zip(
            linear_rgb(color), (0.2126, 0.7152, 0.0722), strict=True,
        ))

    low, high = sorted((luminance(first), luminance(second)))
    return (high + 0.05) / (low + 0.05)


def cielab(color):
    """sRGB -> CIE XYZ -> CIELAB, using the D65 reference white."""
    red, green, blue = linear_rgb(color)
    xyz = (
        (0.4124564 * red + 0.3575761 * green + 0.1804375 * blue) / 0.95047,
        0.2126729 * red + 0.7151522 * green + 0.0721750 * blue,
        (0.0193339 * red + 0.1191920 * green + 0.9503041 * blue) / 1.08883,
    )
    delta = 6 / 29
    x, y, z = (
        value ** (1 / 3) if value > delta ** 3
        else value / (3 * delta ** 2) + 4 / 29
        for value in xyz
    )
    return (116 * y - 16, 500 * (x - y), 200 * (y - z))


def assert_text_contrast(theme, background, mode):
    # Borders and note fills are not text. All other foreground roles may be
    # used as small text, including plot legends and chapter navigation labels.
    foregrounds = {name: theme[name] for name in ("ink", "muted", "accent", "link")}
    for group in ("technical", "parts"):
        foregrounds.update({f"{group}.{name}": color for name, color in theme[group].items()})
    for name, color in foregrounds.items():
        ratio = contrast_ratio(color, theme[background])
        assert ratio >= 4.5, (
            f"{mode}.{name} ({color}) on {background} ({theme[background]}): "
            f"{ratio:.6f}:1 < 4.5:1"
        )


def assert_distinct_parts(parts):
    assert len({color.lower() for color in parts.values()}) == 9, "Parts must have nine distinct colors"


def assert_distinguishable_series(series, mode):
    # Delta E*ab >= 20 is a conservative normal-vision separation guard, not a
    # color-vision-deficiency guarantee. Plots still need labels/dash patterns.
    # Parts are navigation accents, not a nine-series chart palette.
    for (first, first_color), (second, second_color) in combinations(series.items(), 2):
        distance = math.dist(cielab(first_color), cielab(second_color))
        assert distance >= 20, (
            f"{mode}.technical.{first}/{second}: Delta E*ab {distance:.3f} < 20"
        )


def test_palette_has_complete_color_only_schema():
    palette = load_palette()
    assert isinstance(palette, dict)
    assert set(palette) == set(MODES)
    for mode in MODES:
        theme = palette[mode]
        assert isinstance(theme, dict), mode
        assert set(theme) == set(SCALAR_TOKENS) | set(GROUP_TOKENS), mode
        leaves = {name: theme[name] for name in SCALAR_TOKENS}
        for group, names in GROUP_TOKENS.items():
            assert isinstance(theme[group], dict), f"{mode}.{group}"
            assert set(theme[group]) == set(names), f"{mode}.{group}"
            leaves.update({f"{group}.{name}": color for name, color in theme[group].items()})
        for name, value in leaves.items():
            assert isinstance(value, str) and re.fullmatch(r"#[0-9a-fA-F]{6}", value), (
                f"{mode}.{name} must be an opaque six-digit sRGB color, got {value!r}"
            )


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("background", ("paper", "surface"))
def test_palette_text_is_readable_on_reading_surfaces(mode, background):
    assert_text_contrast(load_palette()[mode], background, mode)


@pytest.mark.parametrize("mode", MODES)
def test_palette_ink_is_readable_on_soft_and_note_fills(mode):
    theme = load_palette()[mode]
    backgrounds = {"soft": theme["soft"], **theme["notes"]}
    for name, color in backgrounds.items():
        ratio = contrast_ratio(theme["ink"], color)
        assert ratio >= 4.5, f"{mode}.ink on {name}: {ratio:.6f}:1 < 4.5:1"


@pytest.mark.parametrize("mode", MODES)
def test_palette_preserves_nine_distinct_part_accents(mode):
    assert_distinct_parts(load_palette()[mode]["parts"])


@pytest.mark.parametrize("mode", MODES)
def test_part_guard_rejects_duplicate_colors_with_different_case(mode):
    parts = copy.deepcopy(load_palette()[mode]["parts"])
    parts["p8"] = parts["p0"].upper()
    with pytest.raises(AssertionError, match="distinct"):
        assert_distinct_parts(parts)


@pytest.mark.parametrize("mode", MODES)
def test_palette_technical_series_are_perceptually_separated(mode):
    assert_distinguishable_series(load_palette()[mode]["technical"], mode)


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("background", ("paper", "surface"))
def test_contrast_guard_rejects_unreadable_real_palette_mutation(mode, background):
    theme = copy.deepcopy(load_palette()[mode])
    theme["muted"] = theme[background]
    with pytest.raises(AssertionError, match=rf"{mode}\.muted"):
        assert_text_contrast(theme, background, mode)


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("channel_step", (0, 1), ids=("duplicate", "near-duplicate"))
def test_series_guard_rejects_confusable_real_palette_mutation(mode, channel_step):
    series = copy.deepcopy(load_palette()[mode]["technical"])
    channels = [int(series["blue"][index:index + 2], 16) for index in (1, 3, 5)]
    # Change at most one 8-bit level per channel; even nonidentical colors must
    # fail when they would look like the same line in a multi-series plot.
    series["red"] = "#" + "".join(
        f"{channel + channel_step if channel < 255 else channel - channel_step:02x}"
        for channel in channels
    )
    with pytest.raises(AssertionError, match=rf"{mode}\.technical\.(blue/red|red/blue)"):
        assert_distinguishable_series(series, mode)


@pytest.mark.parametrize("first,second,expected", [
    ("#000000", "#ffffff", 21.0),
    ("#808080", "#808080", 1.0),
    ("#808080", "#ffffff", 3.94944),
])
def test_contrast_metric_matches_reference_ratios(first, second, expected):
    assert contrast_ratio(first, second) == pytest.approx(expected, abs=1e-5)
    assert contrast_ratio(second, first) == pytest.approx(expected, abs=1e-5)


@pytest.mark.parametrize("color,expected", [
    ("#000000", (0.0, 0.0, 0.0)),
    ("#ffffff", (100.0, 0.0, 0.0)),
    ("#ff0000", (53.2408, 80.0925, 67.2032)),
])
def test_cielab_metric_matches_d65_reference_coordinates(color, expected):
    assert cielab(color) == pytest.approx(expected, abs=1e-3)


def test_capacity_labels_are_readable_on_translucent_bars():
    import xml.etree.ElementTree as ET

    asset = PALETTE_PATH.parents[1] / "bms-book/assets/aging-two-clocks.svg"
    parser = ET.XMLParser(target=ET.TreeBuilder(insert_comments=True))
    svg = ET.parse(asset, parser=parser).getroot()
    ns = "{http://www.w3.org/2000/svg}"
    paper = load_palette()["light"]["paper"]
    bars = [node for node in svg.iter(ns + "path")
            if "opacity: 0.85" in node.get("style", "")]
    labels = [node for node in svg.iter(ns + "g")
              if any(child.tag is ET.Comment and re.fullmatch(r"\s*\d+%\s*", child.text or "")
                     for child in node)]
    assert bars and len(labels) == 5
    for label in labels:
        foreground = re.search(r"fill: (#[0-9a-f]{6})", label.find(ns + "g").get("style"))[1]
        for bar in bars:
            color = re.search(r"fill: (#[0-9a-f]{6})", bar.get("style"))[1]
            composite = "#" + "".join(
                f"{round(int(color[i:i+2], 16) * 0.85 + int(paper[i:i+2], 16) * 0.15):02x}"
                for i in (1, 3, 5)
            )
            assert contrast_ratio(foreground, composite) >= 4.5


def test_persistent_visual_contracts_have_no_browser_imports():
    # Site-build installs pytest, not the local browser QA dependencies.
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    forbidden = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            names = [node.module or ""]
        else:
            continue
        forbidden.extend(f"{name}:{node.lineno}" for name in names
                         if name.split(".")[0].lower() in {"playwright", "pil", "pillow"})
    assert not forbidden, f"Local-only browser imports in persistent tests: {forbidden}"


SVG_NS = "{http://www.w3.org/2000/svg}"
ROOT = PALETTE_PATH.parents[1]
GENERATED_NOTES = "docs/circuits/assets/overdischarge-copper.svg"
DTC_ASSET = "docs/circuits/assets/dtc-snapshot.svg"
NOTE_PAIRS = [
    ("docs/circuits/assets/balance-mwh-ledger.svg", "text.warn", "rect.boxr"),
    ("docs/circuits/assets/balance-mwh-ledger.svg", "text.ok", "rect.boxg"),
    ("docs/circuits/assets/hil-testbench.svg", 'text[x="272"][y="126"]', "rect.fault"),
    ("docs/circuits/assets/ref-heat-couple.svg", 'text[x="95"][y="169"]', "rect.fill-boxy"),
    ("bms-book/assets/22-layers.svg", 'text[x="84"][y="110"]', 'rect[x="60"][y="86"]'),
    ("bms-book/assets/22-layers.svg", 'text[x="84"][y="278"]', 'rect[x="60"][y="254"]'),
    ("bms-book/assets/22-layers.svg", 'text[x="847"][y="106"]', 'rect[x="772"][y="84"]'),
    ("bms-book/assets/22-layers.svg", 'text[x="847"][y="124"]', 'rect[x="772"][y="84"]'),
    ("bms-book/assets/22-layers.svg", 'text[x="739"][y="305"]', 'rect[x="556"][y="286"]'),
]
NOTE_ROLES = [("warn", "boxr"), ("ok", "boxb"), ("gold", "boxy"), ("small", "boxr")]
LEGACY_NOTE_COLORS = {
    "#ad4644": "#b84745", "#36775e": "#377b60", "#5f6a63": "#626d65",
    "#8e6518": "#926717", "#736085": "#7c648e",
}


def fixture_declarations(text):
    declarations = {}
    for item in text.split(";"):
        if not item.strip():
            continue
        name, colon, value = item.partition(":")
        assert colon and re.fullmatch(r"[a-z-]+", name.strip()), item
        assert value.strip() and "!" not in value, f"Unsupported fixture declaration: {item}"
        declarations[name.strip()] = value.strip()
    return declarations


def fixture_rules(svg, mode):
    # Fail closed outside these fixtures' class rules and single dark media block.
    assert mode in MODES
    for style in svg.iter(SVG_NS + "style"):
        # 手帐注记层（bms-motion）只管装饰，不参与便签/夹具配色合同。
        if style.get("id") == "bms-motion":
            continue
        css = re.sub(r"/\*.*?\*/", "", style.text or "", flags=re.S)
        css = re.sub(
            r"@media\s*\(prefers-color-scheme:\s*dark\)\s*\{((?:[^{}]*\{[^{}]*\}\s*)*)\}",
            lambda match: match[1] if mode == "dark" else "", css,
        )
        while css.strip():
            rule = re.match(r"\s*\.([\w-]+)\s*\{([^{}]*)\}", css)
            assert rule, f"Unsupported fixture CSS: {css[:100]}"
            yield rule[1], fixture_declarations(rule[2])
            css = css[rule.end():]


def fixture_element(svg, selector):
    match = re.fullmatch(r'([a-z]+)(?:\.([\w-]+))?((?:\[[\w-]+="[^"]*"\])*)', selector)
    assert match, f"Unsupported fixture selector: {selector}"
    tag, cls, attributes = match.groups()
    attributes = re.findall(r'\[([\w-]+)="([^"]*)"\]', attributes)
    for node in svg.iter(SVG_NS + tag):
        if cls and cls not in node.get("class", "").split():
            continue
        if all(node.get(key) == value for key, value in attributes):
            return node
    raise AssertionError(f"Missing SVG element: {selector}")


def fixture_property(svg, node, name, mode):
    parents = {child: parent for parent in svg.iter() for child in parent}
    rules = list(fixture_rules(svg, mode))
    while node is not None:
        value = node.get(name)
        for cls, declarations in rules:
            if cls in node.get("class", "").split() and name in declarations:
                value = declarations[name]
        value = fixture_declarations(node.get("style", "")).get(name, value)
        if value is not None and value != "inherit":
            return value
        node = parents.get(node)
    raise AssertionError(f"Missing authored {name} in {mode}")


def opaque_fixture_color(value):
    assert re.fullmatch(r"#[0-9a-fA-F]{6}", value or ""), f"Non-opaque fixture color: {value}"
    return value.lower()


def note_pair_paints(svg, mode, foreground, background):
    label = fixture_element(svg, foreground)
    assert "".join(label.itertext()).strip(), f"Empty label: {foreground}"
    card = fixture_element(svg, background)
    return tuple(opaque_fixture_color(fixture_property(svg, node, "fill", mode))
                 for node in (label, card))


def generated_role_paints(svg, mode, label, box):
    roles = {}
    for cls, declarations in fixture_rules(svg, mode):
        roles.setdefault(cls, {}).update(declarations)
    assert label in roles and box in roles, f"Missing generated roles: {label}/{box}"
    return tuple(opaque_fixture_color(roles[cls].get("fill")) for cls in (label, box))


def assert_note_paints(paints, context):
    fg, bg = paints
    ratio = contrast_ratio(fg, bg)
    assert ratio >= 4.5, f"{context}: {fg} on {bg}: {ratio:.6f}:1 < 4.5:1"


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("asset,foreground,background", NOTE_PAIRS)
def test_declared_note_text_pairs(mode, asset, foreground, background):
    svg = ET.parse(ROOT / asset).getroot()
    assert_note_paints(note_pair_paints(svg, mode, foreground, background), f"{mode} {asset} {foreground}")


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("label,box", NOTE_ROLES)
def test_generated_note_label_roles(mode, label, box):
    svg = ET.parse(ROOT / GENERATED_NOTES).getroot()
    assert_note_paints(generated_role_paints(svg, mode, label, box), f"{mode} generated .{label} on .{box}")


def assert_source_color_mutations_fail(source, mode, paints):
    fg, bg = paints(ET.fromstring(source))
    assert_note_paints((fg, bg), "Unmodified source")
    assert fg in source, f"Missing source color: {fg}"
    replacements = [bg] + ([LEGACY_NOTE_COLORS[fg]] if mode == "light" else [])
    for replacement in replacements:
        mutated = ET.fromstring(source.replace(fg, replacement))
        assert paints(mutated) == (replacement, bg), "Mutation must reach the actual label paint"
        with pytest.raises(AssertionError, match="< 4.5:1"):
            assert_note_paints(paints(mutated), f"{mode} source mutation")


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("asset,foreground,background", NOTE_PAIRS)
def test_note_pair_guard_rejects_source_color_mutations(mode, asset, foreground, background):
    source = (ROOT / asset).read_text(encoding="utf-8")
    assert_source_color_mutations_fail(
        source, mode, lambda svg: note_pair_paints(svg, mode, foreground, background),
    )


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("label,box", NOTE_ROLES)
def test_generated_role_guard_rejects_source_color_mutations(mode, label, box):
    source = (ROOT / GENERATED_NOTES).read_text(encoding="utf-8")
    assert_source_color_mutations_fail(
        source, mode, lambda svg: generated_role_paints(svg, mode, label, box),
    )


def assert_dtc_marker_wiring(svg, mode):
    arrow = fixture_element(svg, "path.arrow")
    assert arrow.get("d", "").strip(), "Empty marker shaft"
    opaque_fixture_color(fixture_property(svg, arrow, "stroke", mode))
    assert float(fixture_property(svg, arrow, "stroke-width", mode)) > 0, "Invisible marker shaft"
    reference = fixture_property(svg, arrow, "marker-end", mode)
    match = re.fullmatch(r"url\(#([\w-]+)\)", reference)
    assert match, f"Invalid marker reference: {reference}"
    targets = [node for node in svg.iter() if node.get("id") == match[1]]
    assert len(targets) == 1 and targets[0].tag == SVG_NS + "marker", "Broken marker target"
    marker = targets[0]
    assert marker in list(svg.iterfind(f".//{SVG_NS}defs/{SVG_NS}marker")), "Missing marker definition"
    assert marker.get("orient") == "auto", "Marker must follow shaft direction"
    assert marker.get("markerUnits", "strokeWidth") == "strokeWidth", "Marker must scale with shaft"
    for dimension, reference in (("markerWidth", "refX"), ("markerHeight", "refY")):
        size = float(marker.get(dimension, "0"))
        assert size > 0 and 0 <= float(marker.get(reference, "0")) <= size, "Invalid marker geometry"
    heads = list(marker.iter(SVG_NS + "path"))
    assert heads, "Missing marker head"
    for head in heads:
        assert head.get("d", "").strip(), "Empty marker head"
        assert fixture_property(svg, head, "fill", mode) == "context-stroke", "Marker must use context-stroke"


@pytest.mark.parametrize("mode", MODES)
def test_dtc_marker_declares_context_stroke_and_valid_wiring(mode):
    assert_dtc_marker_wiring(ET.parse(ROOT / DTC_ASSET).getroot(), mode)


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("mutation", ("fixed-fill", "missing-target", "non-marker-target", "empty-head"))
def test_dtc_marker_guard_rejects_source_mutations(mode, mutation):
    svg = ET.parse(ROOT / DTC_ASSET).getroot()
    assert_dtc_marker_wiring(svg, mode)
    marker = svg.find(f".//{SVG_NS}marker")
    head = marker.find(SVG_NS + "path")
    if mutation == "fixed-fill":
        head.set("fill", fixture_property(svg, fixture_element(svg, "path.arrow"), "stroke", mode))
    elif mutation == "missing-target":
        marker.set("id", "missing-marker")
    elif mutation == "non-marker-target":
        marker.tag = SVG_NS + "g"
    else:
        head.set("d", "")
    with pytest.raises(AssertionError, match="[Mm]arker"):
        assert_dtc_marker_wiring(svg, mode)


CUSTOM_CSS = ROOT / "docs/.vitepress/theme/custom.css"


def media_blocks(css, keyword):
    """Return the bodies of top-level @media blocks whose query contains keyword."""
    blocks = []
    for match in re.finditer(r"@media\s+([^{]+)\{", css):
        if keyword not in match[1]:
            continue
        depth = 1
        for end in range(match.end(), len(css)):
            if css[end] == "{":
                depth += 1
            elif css[end] == "}":
                depth -= 1
                if depth == 0:
                    blocks.append(css[match.end():end])
                    break
    return blocks


def test_site_svg_theme_follows_manual_toggle_not_os():
    """Embedded SVGs read prefers-color-scheme from the parent's color-scheme.

    Without an explicit light root, a manually light site on a dark OS still
    paints every animation and snapshot dark. VitePress only supplies the dark
    half in its base stylesheet.
    """
    css = re.sub(r"/\*.*?\*/", "", CUSTOM_CSS.read_text(encoding="utf-8"), flags=re.S)
    light = re.findall(r"(?m)^\s*:root\s*\{([^}]*)\}", css)
    dark = re.findall(r"(?m)^\s*html\.dark\s*\{([^}]*)\}", css)
    assert any(re.search(r"color-scheme:\s*light\b", block) for block in light)
    assert any(re.search(r"color-scheme:\s*dark\b", block) for block in dark)


def test_site_print_forces_light_svg_theme():
    css = re.sub(r"/\*.*?\*/", "", CUSTOM_CSS.read_text(encoding="utf-8"), flags=re.S)
    printed = media_blocks(css, "print")
    assert any(
        re.search(r"html\.dark[^{}]*\{[^}]*color-scheme:\s*light\b", block)
        for block in printed
    ), "Print must override html.dark's color-scheme so SVG figures stay on paper"


def test_scrapbook_svg_is_accessible_sized_and_self_contained():
    """Catch missing art, broken accessible references, layout shifts and dependencies."""
    import xml.etree.ElementTree as ET

    asset = PALETTE_PATH.parents[1] / "docs/public/illustrations/bms-scrapbook.svg"
    assert asset.is_file(), f"Missing scrapbook illustration: {asset}"
    svg = ET.parse(asset).getroot()
    ns = "{http://www.w3.org/2000/svg}"
    assert svg.tag == ns + "svg"
    assert svg.get("role") == "img"
    ids = [node.get("id") for node in svg.iter() if node.get("id")]
    assert len(ids) == len(set(ids)), "SVG IDs must be unique"
    for tag, attribute in (("title", "aria-labelledby"), ("desc", "aria-describedby")):
        node = svg.find(ns + tag)
        assert node is not None and "".join(node.itertext()).strip(), f"Missing {tag}"
        assert node.get("id") in svg.get(attribute, "").split(), f"Broken {attribute}"
    for attribute in ("aria-labelledby", "aria-describedby"):
        assert set(svg.get(attribute, "").split()) <= set(ids)

    width, height = (float(svg.get(key, "0")) for key in ("width", "height"))
    viewbox = tuple(float(value) for value in svg.get("viewBox", "").split())
    assert width > 0 and height > 0, "Reserve intrinsic dimensions before loading"
    assert len(viewbox) == 4 and viewbox[:2] == (0, 0)
    assert viewbox[2:] == (width, height), "Intrinsic size and viewBox must agree"

    forbidden = {"text", "image", "foreignObject", "script", "style", "animate",
                 "animateMotion", "animateTransform", "set"}
    palette = load_palette()["light"]
    allowed_colors = {palette[key] for key in SCALAR_TOKENS}
    for group in GROUP_TOKENS:
        allowed_colors.update(palette[group].values())
    used_colors = set()
    for node in svg.iter():
        assert node.tag.removeprefix(ns) not in forbidden, node.tag
        for attribute, value in node.attrib.items():
            name = attribute.split("}")[-1]
            assert not name.startswith("on") and name != "style", attribute
            if name == "href":
                assert value.startswith("#") and value[1:] in ids, "External SVG dependency"
            for target in re.findall(r"url\((.*?)\)", value):
                assert target.startswith("#") and target[1:] in ids, "External SVG resource"
            used_colors.update(re.findall(r"#[0-9a-fA-F]{6}\b", value))
    assert used_colors <= allowed_colors, "Illustration must use the shared palette"
    assert set(palette["notes"].values()) <= used_colors
    assert any(node.get("d", "").strip() for node in svg.iter(ns + "path")), "Empty art"
