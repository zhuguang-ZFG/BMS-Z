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


def test_manifest_exists_and_has_20_entries():
    assert MANIFEST.is_file()
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert len(data["entries"]) == 20


def test_each_entry_has_required_fields_and_palette():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    for entry in data["entries"]:
        missing = REQUIRED - set(entry)
        assert not missing, f"{entry.get('slug')}: missing {missing}"
        assert entry["style"] in ALLOWED_STYLE
        assert entry["colors"]["primary"] == "C-03"
        assert entry["colors"]["danger"] == "C-15"
        assert entry["status"] in ALLOWED_STATUS
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

