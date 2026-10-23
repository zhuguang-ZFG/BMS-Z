"""Validate the artifact readers actually open, including offline math and links."""
from collections import Counter
from html.parser import HTMLParser
import importlib.util
import os
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]


class Document(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.fragments = []
        self.images = []
        self.scripts = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.append(attrs["id"])
        if tag == "a" and attrs.get("href", "").startswith("#"):
            self.fragments.append(attrs["href"][1:])
        if tag == "img":
            self.images.append(attrs)
        if tag == "script" and "src" in attrs:
            self.scripts.append(attrs["src"])


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


@pytest.mark.parametrize("name", ["cccv_charge.py", "thermal_lump.py"])
def test_demos_can_print_in_a_chinese_windows_console(name):
    result = subprocess.run(
        [sys.executable, str(ROOT / "code" / name)],
        capture_output=True, encoding="gbk", timeout=30,
        env={**os.environ, "PYTHONIOENCODING": "gbk:strict"},
    )
    assert result.returncode == 0, result.stdout + result.stderr
