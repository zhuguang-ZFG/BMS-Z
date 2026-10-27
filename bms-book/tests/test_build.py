"""Validate the artifact readers actually open, including offline math and links."""
from collections import Counter
from html.parser import HTMLParser
import importlib.util
import os
from pathlib import Path
import json
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
    assert len(motion) == 33
    assert all(img['data-motion-src'].startswith('data:image/svg+xml;base64,') for img in motion)
    assert 'data-mode="static"' in text
    assert 'beforeprint' in text
    for lab in ("ocv", "sop", "thermal", "protection"):
        assert f'data-book-lab="{lab}"' in text


def test_vector_print_snapshots_are_static_and_complete():
    entries = json.loads((ROOT / 'visuals.json').read_text(encoding='utf-8'))
    for entry in entries:
        svg = ET.parse(ROOT / 'assets/print' / entry['file']).getroot()
        assert svg.get('data-snapshot-time') == str(entry['time'])
        tags = [node.tag.split('}')[-1] for node in svg.iter()]
        assert 'text' in tags and 'title' in tags
        assert not {'animate', 'animateMotion', 'animateTransform', 'set'} & set(tags)


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
        "先看 §5.9 再回 §1.2–§1.5\n"
        "外部 §4.7b 与 §0.1.6 豁免\n"
        "技术协议 §3.2 豁免\n"
        "BMS-Z 阶段 4（§4.8 工程落地）",
    )
    assert len(checker.failures) == 1
    assert "§5.9" in checker.failures[0]


@pytest.mark.parametrize("name", ["cccv_charge.py", "thermal_lump.py"])
def test_demos_can_print_in_a_chinese_windows_console(name):
    result = subprocess.run(
        [sys.executable, str(ROOT / "code" / name)],
        capture_output=True, encoding="gbk", timeout=30,
        env={**os.environ, "PYTHONIOENCODING": "gbk:strict"},
    )
    assert result.returncode == 0, result.stdout + result.stderr
