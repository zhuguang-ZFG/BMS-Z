import hashlib
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
try:
    from publish_downloads import PublicationError, package_downloads
finally:
    sys.path.pop(0)


def _manifest(path: Path, version: str = "0.6.1") -> Path:
    path.write_text(
        json.dumps(
            {
                "title": "BMS 实战：从一颗电芯到一套证据链",
                "version": version,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return path


def test_package_downloads_emits_stable_and_versioned_artifacts(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    html_bytes = b"<!doctype html><title>BMS</title>"
    pdf_bytes = b"%PDF-1.4\nbook"
    (source / "bms-book.html").write_bytes(html_bytes)
    (source / "bms-book.pdf").write_bytes(pdf_bytes)
    output = tmp_path / "downloads"

    result = package_downloads(source, output, _manifest(tmp_path / "manifest.json"))

    expected = {
        "bms-book.html",
        "bms-book.pdf",
        "bms-book-v0.6.1.html",
        "bms-book-v0.6.1.pdf",
        "book-downloads.json",
        "SHA256SUMS.txt",
        "index.html",
    }
    assert {path.name for path in output.iterdir()} == expected
    assert (output / "bms-book.html").read_bytes() == html_bytes
    assert (output / "bms-book-v0.6.1.html").read_bytes() == html_bytes
    assert (output / "bms-book.pdf").read_bytes() == pdf_bytes
    assert (output / "bms-book-v0.6.1.pdf").read_bytes() == pdf_bytes

    metadata = json.loads((output / "book-downloads.json").read_text(encoding="utf-8"))
    assert metadata == result
    assert metadata["version"] == "0.6.1"
    assert [item["kind"] for item in metadata["files"]] == ["html", "pdf"]
    assert metadata["files"][0]["bytes"] == len(html_bytes)
    assert metadata["files"][0]["sha256"] == hashlib.sha256(html_bytes).hexdigest()
    assert metadata["files"][1]["sha256"] == hashlib.sha256(pdf_bytes).hexdigest()

    sums = (output / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines()
    assert sums == [
        f"{hashlib.sha256(html_bytes).hexdigest()}  bms-book-v0.6.1.html",
        f"{hashlib.sha256(pdf_bytes).hexdigest()}  bms-book-v0.6.1.pdf",
    ]
    landing = (output / "index.html").read_text(encoding="utf-8")
    assert "BMS 实战：从一颗电芯到一套证据链" in landing
    assert "v0.6.1" in landing
    assert 'href="bms-book.html"' in landing
    assert 'href="bms-book.pdf"' in landing
    assert 'href="SHA256SUMS.txt"' in landing


def test_package_downloads_refuses_partial_source_without_output(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "bms-book.html").write_text("ok", encoding="utf-8")
    output = tmp_path / "downloads"

    with pytest.raises(PublicationError, match="bms-book.pdf"):
        package_downloads(source, output, _manifest(tmp_path / "manifest.json"))

    assert not output.exists()
