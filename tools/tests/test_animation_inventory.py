"""Migration must preserve the inventory and must not resurrect archived SVGs."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import gen_mechanism_svgs as mechanism  # noqa: E402
import gen_social_card as social  # noqa: E402


def test_regeneration_leaves_archived_sources_and_outputs_untouched(tmp_path):
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"entries": [
        {"status": "archived", "source_svg": "docs/circuits/assets/archive/migrated.svg"},
        {"status": "archived", "source_svg": None},  # 新增手绘没有旧 SVG
    ]}), encoding="utf-8")
    (tmp_path / "migrated.svg").write_text("keep prior bytes", encoding="utf-8")

    def forbidden():
        raise AssertionError("An archived builder must not run")

    builders = {"migrated.svg": forbidden, "live.svg": lambda: "<svg/>\n"}
    mechanism.write_svgs(builders, tmp_path, manifest)
    assert (tmp_path / "migrated.svg").read_text(encoding="utf-8") == "keep prior bytes"
    assert (tmp_path / "live.svg").read_text(encoding="utf-8") == "<svg/>\n"
    fresh = tmp_path / "fresh"
    fresh.mkdir()
    mechanism.write_svgs(builders, fresh, manifest)
    assert not (fresh / "migrated.svg").exists()


def test_social_and_about_counts_include_exports_and_deduplicate_sources(tmp_path, monkeypatch):
    assets = tmp_path / "docs/circuits/assets"
    exports = tmp_path / "docs/circuits/handraw/exports"
    for path in (assets, exports, tmp_path / "docs/stages", tmp_path / "code"):
        path.mkdir(parents=True, exist_ok=True)
    for name in ("live.svg", "migrating.svg"):
        (assets / name).touch()
    for name in ("migrating.webp", "archived.webp", "archived-start.webp", "archived-end.webp"):
        (exports / name).touch()
    checks = social._docs_checks
    monkeypatch.setattr(social, "ROOT", tmp_path)
    monkeypatch.setattr(social, "ASSETS", assets)
    monkeypatch.setattr(checks, "ROOT", tmp_path)
    monkeypatch.setattr(checks, "HANDRAW_EXPORTS", exports)
    seen = []

    def about(total):
        seen.append(total)
        return [], None

    monkeypatch.setattr(checks, "check_about_truth", about)
    assert social.counts() == (0, 3, 0)
    assert checks.run_about_checks() == 0
    assert seen == [3]
