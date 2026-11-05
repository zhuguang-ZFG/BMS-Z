from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from check_handraw_manifest import frame_geometry_problems, validate_manifest  # noqa: E402

MANIFEST = ROOT / "docs" / "circuits" / "handraw" / "manifest.json"
REQUIRED = {
    "slug", "source_svg", "kp_id", "style", "colors",
    "frames", "export", "caption_ok", "bans_ok", "status",
}
ALLOWED_STYLE = {"FA-002", "FA-029"}
ALLOWED_STATUS = {"prompts_only", "rendered", "exported", "linked", "archived"}


def test_manifest_exists_and_has_expected_entries():
    assert MANIFEST.is_file()
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    # 第一批 20 张 + 第二批新增（无旧几何源，source_svg 为 null）；#22 soc-routes §12.4、#23 pybamm-scales §23.1
    assert len(data["entries"]) == 23


def test_each_entry_has_required_fields_and_palette():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    for entry in data["entries"]:
        missing = REQUIRED - set(entry)
        assert not missing, f"{entry.get('slug')}: missing {missing}"
        assert entry["style"] in ALLOWED_STYLE
        assert entry["colors"]["primary"] == "C-03"
        assert entry["colors"]["danger"] == "C-15"
        assert entry["status"] in ALLOWED_STATUS
        if entry["source_svg"] is not None:
            src = ROOT / entry["source_svg"]
            assert src.is_file(), f"missing source {entry['source_svg']}"


def test_validate_manifest_clean_on_current_file():
    errors = validate_manifest(MANIFEST)
    assert errors == []


def test_geometry_gate_flags_text_over_text(tmp_path):
    """压字回归：本批 frame-01 把时间轴标签写在电流标签上，两条都在画布内，只有相交才抓得到。"""
    svg = tmp_path / "frame-01.svg"
    svg.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 560">'
        '<text x="600" y="442" text-anchor="middle" font-size="13">静置时间 t（min，示意）</text>'
        '<text x="640" y="448" font-size="12">I（放电，示意）</text>'
        "</svg>",
        encoding="utf-8",
    )
    problems = frame_geometry_problems(svg)
    assert any("压字" in p for p in problems), problems


def test_geometry_gate_flags_label_crossed_by_axis(tmp_path):
    """压线回归：电压标注左端落在 y 轴上，竖线从末位数字中间穿过。"""
    svg = tmp_path / "frame-01.svg"
    svg.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 560">'
        '<line x1="180" y1="400" x2="180" y2="170" stroke-width="1.6"/>'
        '<text x="150" y="226" font-size="13">3.620 V（放电支极限）</text>'
        "</svg>",
        encoding="utf-8",
    )
    problems = frame_geometry_problems(svg)
    assert any("压线" in p for p in problems), problems


def test_geometry_gate_flags_rotated_title_on_ticks(tmp_path):
    """旋转文本回归：y 轴标题 rotate(-90) 后压在刻度数字上，跳过旋转文本就整类放行。"""
    svg = tmp_path / "frame-01.svg"
    svg.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 560">'
        '<text x="172" y="293" text-anchor="end" font-size="12">3.56</text>'
        '<text x="146" y="290" text-anchor="middle" font-size="13" '
        'transform="rotate(-90 146 290)">端电压（V，示意）</text>'
        "</svg>",
        encoding="utf-8",
    )
    problems = frame_geometry_problems(svg)
    assert any("压字" in p for p in problems), problems


def test_geometry_gate_accepts_separated_labels(tmp_path):
    """修好之后同一批坐标必须判干净——否则这道门只会逼人往另一边挪。"""
    svg = tmp_path / "frame-01.svg"
    svg.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 560">'
        '<line x1="180" y1="400" x2="180" y2="170" stroke-width="1.6"/>'
        '<text x="172" y="293" text-anchor="end" font-size="12">3.56</text>'
        '<text x="130" y="290" text-anchor="middle" font-size="13" '
        'transform="rotate(-90 130 290)">端电压（V，示意）</text>'
        '<text x="200" y="226" font-size="13">3.620 V（放电支极限）</text>'
        "</svg>",
        encoding="utf-8",
    )
    assert frame_geometry_problems(svg) == []


def test_geometry_gate_uses_inherited_font_size(tmp_path):
    """字号继承回归：<text> 没写 font-size、靠 <g font-size> 继承时必须按 20 量宽。

    早先按 12 兜底，两条文本的盒都缩窄 → 真交叠判不出来，正是要抓的压字被静默放过。
    """
    svg = tmp_path / "frame-01.svg"
    svg.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 560">'
        '<g font-size="20">'
        '<text x="100" y="100">端电压</text>'
        '<text x="150" y="100">示意</text>'
        "</g></svg>",
        encoding="utf-8",
    )
    problems = frame_geometry_problems(svg)
    assert any("压字" in p for p in problems), problems


def test_geometry_gate_flags_label_on_curve(tmp_path):
    """压曲线回归：标注压在手绘曲线上。

    只查 <line> 时这一类看不见——本批 polarization-physics f05 的「3.440 V」就压在
    松弛曲线上，靠放大目视才发现；曲线必须按 path 段采样进同一套判定。
    """
    svg = tmp_path / "frame-01.svg"
    svg.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 560">'
        '<path d="M100,200 C 150,120 200,120 250,200" fill="none"/>'
        '<text x="150" y="145" font-size="12">标注</text>'
        "</svg>",
        encoding="utf-8",
    )
    problems = frame_geometry_problems(svg)
    assert any("压曲线" in p for p in problems), problems


def test_all_rendered_frames_are_geometry_clean():
    """已渲染条目的每一帧都要过几何门——这是上面三条缺陷的最终防线。"""
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    problems = []
    for entry in data["entries"]:
        for rel in entry.get("frames") or []:
            svg = (ROOT / rel).with_suffix(".svg")
            if svg.is_file():
                problems.extend(frame_geometry_problems(svg))
    assert problems == [], problems


def test_archived_slugs_are_not_referenced_by_live_text():
    """归档后正文不得再指旧路径——包括 `<img data-motion-src>` 这类裸属性。

    `check_docs` 只对 Markdown 链接做存在性对账，裸属性它看不见；漏掉一处，
    站点上就是一张 404 的图而门是绿的。历史条目（CHANGELOG/更新动态/计划）不改写。
    """
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    archived = [e["slug"] for e in data["entries"] if e["status"] == "archived"]
    skip = ("CHANGELOG.md", "docs/更新动态.md", "docs/superpowers/",
            ".tmp-", ".local/", "node_modules/", "docs/.vitepress/", "bms-book/dist/")
    problems = []
    for path in ROOT.rglob("*.md"):
        rel = path.relative_to(ROOT).as_posix()
        if any(rel.startswith(prefix) for prefix in skip):
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for slug in archived:
            if f"circuits/assets/{slug}.svg" in text:
                problems.append(f"{rel}: 仍引用已归档的 {slug}.svg")
    assert problems == [], problems


def test_archived_entries_still_get_geometry_and_export_checks(tmp_path):
    """归档只放宽「源几何 SVG 还能不能找到」，不能顺带把帧与导出从门里摘掉。

    真回归：把 status 集合写成 {rendered,exported,linked} 时，六张已归档的活图
    既不跑几何门、也不查导出是否存在——改坏一帧，门还是绿的。
    """
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    entry = next(e for e in data["entries"] if e["status"] == "archived")
    broken = json.loads(json.dumps(entry))
    broken["slug"] = "archived-gate-probe"
    broken["frames"] = ["docs/circuits/handraw/storyboard/dfd-probe/frame-01.webp"]
    broken["export"] = "docs/circuits/handraw/exports/dfd-probe.webp"
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"entries": [broken] * 20}, ensure_ascii=False), encoding="utf-8")
    errors = validate_manifest(manifest)
    assert any("missing frame" in e for e in errors), errors
    assert any("missing export" in e for e in errors), errors
