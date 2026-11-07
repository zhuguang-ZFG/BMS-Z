"""EPUB consumer contracts; new regression coverage requires review."""
import importlib.util
from pathlib import Path
import sys
import zipfile
import xml.etree.ElementTree as ET

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def epub_module():
    spec = importlib.util.spec_from_file_location("book_epub", ROOT / "build_epub.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_epub_preserves_text_math_images_and_navigation(tmp_path):
    module = epub_module()
    html = '''<html lang="zh-CN"><head><title>证据链</title></head><body>
    <nav><a href="#ch-01">前言</a><a href="#ch-02">第二章</a></nav>
    <section class="chapter"><h2 id="ch-01">前言</h2><p>条件不能删</p>
    <svg viewBox="0 0 20 20"><path id="curve" d="M0 0L20 20"/></svg>
    <mjx-container><svg viewBox="0 0 20 20"><path d="M0 1L20 1"/></svg></mjx-container>
    <button>播放</button><script>throw Error('must not run')</script></section>
    <section class="chapter"><h2 id="ch-02">第二章</h2><a href="https://example.org/map#kp-x-l3">任务</a></section>
    </body></html>'''
    output = tmp_path / "book.epub"
    module.package_html(html, output, {"title": "证据链", "author": "BMS-Z", "version": "0.6.10", "license": "CC BY-SA 4.0"})
    assert module.validate_epub(output) == []
    with zipfile.ZipFile(output) as archive:
        assert archive.infolist()[0].filename == "mimetype"
        assert archive.infolist()[0].compress_type == zipfile.ZIP_STORED
        package = ET.fromstring(archive.read("EPUB/package.opf"))
        ns = {"opf": "http://www.idpf.org/2007/opf"}
        assert package.find("opf:spine/opf:itemref", ns) is not None
        content = archive.read("EPUB/book.xhtml").decode()
        assert "条件不能删" in content and "https://example.org/map#kp-x-l3" in content
        assert "播放" not in content and "<script" not in content
        assert 'id="ch-01"' in content and 'id="ch-02"' in content
        assert len([name for name in archive.namelist() if name.endswith(".svg")]) == 2


def test_epub_rejects_broken_internal_fragment(tmp_path):
    module = epub_module()
    with pytest.raises(ValueError, match="missing"):
        module.package_html('<html><body><h2 id="ch-01">正文</h2><a href="#missing">回链</a></body></html>', tmp_path / "bad.epub", {"title": "Book", "version": "1.0.0"})
    assert not (tmp_path / "bad.epub").exists()


def test_epub_does_not_accept_network_images_as_offline_content(tmp_path):
    module = epub_module()
    with pytest.raises(ValueError, match="https://"):
        module.package_html('<html><body><h2 id="ch-01">正文</h2><img src="https://example.org/private.png" alt="图"/></body></html>', tmp_path / "bad.epub", {"title": "Book", "version": "1.0.0"})
    assert not (tmp_path / "bad.epub").exists()
