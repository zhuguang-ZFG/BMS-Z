from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from check_handraw_manifest import validate_manifest  # noqa: E402

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
