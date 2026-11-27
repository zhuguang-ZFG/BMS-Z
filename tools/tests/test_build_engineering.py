"""The engineering assembly (P2.6) builds only from registries and manuscripts."""

import json
import shutil
import base64
from io import BytesIO
import re
import xml.etree.ElementTree as ET
import zipfile

import pytest

from tools.build_engineering import build, MANIFEST, ROOT

pytestmark = pytest.mark.skipif(
    shutil.which("node") is None, reason="装配需要 Node 渲染器"
)


def implemented_units() -> set[str]:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    return {
        u["id"]
        for u in manifest["units"]
        if u.get("status") == "locally_verified" and u.get("source")
    }


def test_build_outputs_single_book_assets_and_report(tmp_path):
    build(tmp_path)
    out = tmp_path
    book = out / "engineering-book.html"
    assert book.is_file(), "单文件书必须产出"
    text = book.read_text(encoding="utf-8")
    assert "<main>" in text and "</main>" in text
    assert '<span class="lang">text</span>' not in text and 'class="copy"' not in text
    assert '<pre ' in text and 'python code/engineering/identification/d13_ekf.py' in text
    expected = implemented_units()
    assert f"本版收录 {len(expected)} 个工程单元" in text
    assert not re.search(r"</h1>\s*<h1\b", text), "每章只排一次章名"
    for uid in ("conventions", "prerequisites", "sources", *(uid.lower() for uid in expected)):
        assert f'id="{uid}--toc"' in text, f"书内缺章节 {uid}"
    assert 'class="toc"' in text, "书内必须有目录导航"
    toc = text.split('<nav class="toc"', 1)[1].split("</nav>", 1)[0]
    assert len(re.findall(r'class="toc-entry" href="#[^"]+--toc"', toc)) == len(expected) + 3
    d13 = re.search(r'href="#d13--toc">.*?</a><details>.*?<ol>(.*?)</ol></details>', toc, re.S)
    assert d13
    assert set(re.findall(r'href="#([^"]+)"', d13[1])) == set(re.findall(r'<h2\b[^>]*id="(d13--[^"]+)"', text))
    with zipfile.ZipFile(out / "engineering.epub") as epub:
        package = ET.fromstring(epub.read("EPUB/package.opf"))
        covers = package.findall(".//{*}item[@properties='cover-image']")
        assert len(covers) == 1 and covers[0].get("media-type") == "image/jpeg"
        assert epub.read("EPUB/" + covers[0].get("href")) == (ROOT / "bms-book/engineering/cover.jpg").read_bytes()
        title = ET.fromstring(epub.read("EPUB/title.xhtml"))
        photo = title.find(".//{*}figure/{*}img")
        original = (ROOT / "docs/circuits/assets/photos/libresolar-bms-c1.jpg").read_bytes()
        assert photo is not None and epub.read("EPUB/" + photo.get("src")) == original
        assert base64.b64encode(original).decode("ascii") in text
        assert "CC BY-SA 4.0" in "".join(title.find(".//{*}figcaption").itertext())
        nav = ET.fromstring(epub.read("EPUB/nav.xhtml"))
        chapter = ET.fromstring(epub.read("EPUB/d13.xhtml"))
        targets = {a.get("href") for a in nav.findall(".//{*}a") if a.get("href").startswith("d13.xhtml#")}
        assert targets == {"d13.xhtml#" + h.get("id") for h in chapter.findall(".//{*}h2")}
    figures = sorted(
        p.relative_to(out).as_posix() for p in (out / "assets").glob("*/*")
    )
    assert "assets/s1-measurement/S1-F1-sense-chain.svg" in figures
    assert "assets/d01-cell/D01-F1-cross-section.svg" in figures
    assert "assets/d12-soc/D12-F1-three-errors.svg" in figures
    data = json.loads((out / "build-report.json").read_text(encoding="utf-8"))
    assert set(data["units"]) == expected
    assert len(data["units"]["S1"]["source_sha256"]) == 16


def test_reading_levels_become_data_level_attributes(tmp_path):
    build(tmp_path)
    book = (tmp_path / "engineering-book.html").read_text(encoding="utf-8")
    assert 'data-level="derivation"' in book, "断言锚点小节须带推导层级"
    assert 'data-level="lab"' in book, "S1.9 动手验证须带动手层级"


def test_storyboard_uses_completed_frame_in_static_editions(tmp_path):
    from PIL import Image, ImageChops, ImageStat

    build(tmp_path)
    image_path = "assets/d13-ekf/D13-F2-soc-routes.webp"
    payload = (tmp_path / image_path).read_bytes()
    with Image.open(BytesIO(payload)) as frames:
        first = frames.convert("RGB")
        frames.seek(frames.n_frames - 1)
        final = frames.convert("RGB")
    assert first.tobytes() != final.tobytes()

    html = (tmp_path / "engineering-book.html").read_text(encoding="utf-8")
    pictures = re.findall(r"<picture>(.*?)</picture>", html, flags=re.S)
    original = base64.b64encode(payload).decode("ascii")
    picture = next((p for p in pictures if original in p), "")
    assert picture, "纸面和减少动态效果模式需要使用画完的图"
    assert 'media="print, (prefers-reduced-motion: reduce)"' in picture
    poster = re.search(r'srcset="data:image/webp;base64,([^"]+)"', picture)
    assert poster
    with Image.open(BytesIO(base64.b64decode(poster[1]))) as still:
        assert not still.is_animated
        def error_to(frame):
            return sum(ImageStat.Stat(ImageChops.difference(still.convert("RGB"), frame)).mean)
        assert error_to(final) < error_to(first)

    with zipfile.ZipFile(tmp_path / "engineering.epub") as epub:
        chapter = ET.fromstring(epub.read("EPUB/d13.xhtml"))
        image = next(el for el in chapter.findall(".//{*}img") if "D13-F2" in el.get("alt", ""))
        with Image.open(BytesIO(epub.read("EPUB/" + image.attrib["src"]))) as still:
            assert still.convert("RGB").tobytes() == final.tobytes()


def test_semantic_blocks_become_asides(tmp_path):
    build(tmp_path)
    book = (tmp_path / "engineering-book.html").read_text(encoding="utf-8")
    assert 'class="callout story"' in book
    assert 'class="chapter-route"' in book
    assert "::::" not in book, "容器语法不得残留在产物里"


def test_math_renders_offline_for_s2(tmp_path):
    build(tmp_path)
    book = (tmp_path / "engineering-book.html").read_text(encoding="utf-8")
    assert "mjx" in book or "MathJax" in book, "S2 数学式必须由 mathjax3 离线渲染"


def test_build_is_deterministic(tmp_path):
    first = tmp_path / "a"
    second = tmp_path / "b"
    build(first)
    build(second)
    names = sorted(
        p.relative_to(first).as_posix() for p in first.rglob("*") if p.is_file()
    )
    assert names == sorted(
        p.relative_to(second).as_posix() for p in second.rglob("*") if p.is_file()
    )
    for name in names:
        assert (first / name).read_bytes() == (second / name).read_bytes(), (
            f"{name} 两次构建不一致"
        )


def test_missing_unit_source_fails_loudly(tmp_path, monkeypatch):
    from tools import build_engineering

    original = build_engineering.ROOT
    fake = tmp_path / "repo"
    fake.mkdir()
    (fake / "bms-book/engineering").mkdir(parents=True)
    shutil.copy2(
        ROOT / "bms-book/engineering/manifest.json",
        fake / "bms-book/engineering/manifest.json",
    )
    shutil.copy2(
        ROOT / "bms-book/engineering/claims.json",
        fake / "bms-book/engineering/claims.json",
    )
    shutil.copy2(
        ROOT / "bms-book/engineering/figures.json",
        fake / "bms-book/engineering/figures.json",
    )
    shutil.copy2(
        ROOT / "bms-book/engineering/experiments.json",
        fake / "bms-book/engineering/experiments.json",
    )
    monkeypatch.setattr(build_engineering, "ROOT", fake)
    with pytest.raises(SystemExit, match="正文源缺失"):
        build(tmp_path / "out")
    monkeypatch.setattr(build_engineering, "ROOT", original)


def test_broken_spine_fails_loudly(tmp_path):
    from tools.build_engineering import verify_spine

    book_html = '<h2 id="s1--toc">S1</h2><a href="#ghost--toc">幽灵</a>'
    with pytest.raises(SystemExit, match="坏 spine"):
        verify_spine(book_html, tmp_path)


def test_spine_passes_when_every_anchor_exists(tmp_path):
    from tools.build_engineering import verify_spine

    book_html = '<h2 id="s1--toc">S1</h2><a href="#s1--toc">本章</a>'
    verify_spine(book_html, tmp_path)


def test_missing_figure_file_fails_loudly(tmp_path, monkeypatch):
    from tools import build_engineering

    original = build_engineering.ROOT
    fake = tmp_path / "repo"
    for rel in (
        "bms-book/engineering/assets/s1-measurement",
        "bms-book/engineering/assets/s2-model",
        "bms-book/engineering/assets/s3-precharge",
    ):
        (fake / rel).mkdir(parents=True, exist_ok=True)
    for name in (
        "manifest.json",
        "claims.json",
        "figures.json",
        "experiments.json",
    ):
        shutil.copy2(
            ROOT / "bms-book/engineering" / name, fake / "bms-book/engineering" / name
        )
    (fake / "bms-book/engineering").mkdir(parents=True, exist_ok=True)
    shutil.copy2(
        ROOT / "bms-book/engineering/render.mjs",
        fake / "bms-book/engineering/render.mjs",
    )
    manifest = json.loads((ROOT / "bms-book/engineering/manifest.json").read_text(encoding="utf-8"))
    for unit in manifest["units"]:
        if unit.get("status") != "locally_verified" or not unit.get("source"):
            continue
        manuscript = ROOT / unit["source"]
        destination = fake / unit["source"]
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(manuscript, destination)
    # S1 缺图，其他已装配源齐全，须在复制阶段报错。
    for pattern in ("s2-model", "s3-precharge"):
        for src in (ROOT / "bms-book/engineering/assets" / pattern).glob("*"):
            shutil.copy2(src, fake / "bms-book/engineering/assets" / pattern / src.name)
    monkeypatch.setattr(build_engineering, "ROOT", fake)
    with pytest.raises(SystemExit, match="S1-F1 的文件缺失"):
        build(tmp_path / "out2")
    monkeypatch.setattr(build_engineering, "ROOT", original)


def test_epub_present_and_valid(tmp_path):
    import xml.etree.ElementTree as ET
    import zipfile

    build(tmp_path)
    epub = tmp_path / "engineering.epub"
    assert epub.is_file(), "EPUB 必须随构建产出"
    build_epub = _load_epub_module()
    assert build_epub.validate_epub(epub) == []
    with zipfile.ZipFile(epub) as archive:
        for name in archive.namelist():
            if not name.endswith(".xhtml"):
                continue
            document = ET.fromstring(archive.read(name))
            xhtml = "{http://www.w3.org/1999/xhtml}"
            for parent in document.iter():
                for child in parent:
                    if child.tag == xhtml + "figcaption":
                        assert parent.tag == xhtml + "figure", (name, "orphan caption")
                    if child.tag == xhtml + "figure":
                        assert parent.tag != xhtml + "p", (name, "figure inside paragraph")


def test_epub_is_deterministic(tmp_path):
    first = tmp_path / "a"
    second = tmp_path / "b"
    build(first)
    build(second)
    assert (first / "engineering.epub").read_bytes() == (
        second / "engineering.epub"
    ).read_bytes(), "EPUB 两次构建必须逐字节一致"


def test_epub_bad_spine_is_rejected(tmp_path):
    """坏 spine 负例：内容文档缺席 spine、断 idref 都必须被合同抓住。"""
    build_epub = _load_epub_module()
    opf_bad = """<?xml version="1.0" encoding="utf-8"?>
    <package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="book-id">
      <metadata><dc:identifier xmlns:dc="http://purl.org/dc/elements/1.1/" id="book-id">urn:x</dc:identifier></metadata>
      <manifest>
        <item id="a" href="a.xhtml" media-type="application/xhtml+xml"/>
        <item id="b" href="b.xhtml" media-type="application/xhtml+xml"/>
      </manifest>
      <spine><itemref idref="a"/><itemref idref="ghost"/></spine>
    </package>"""
    xhtml = (
        b'<html xmlns="http://www.w3.org/1999/xhtml"><head><title>t</title></head>'
        b"<body><p>x</p></body></html>"
    )
    files = {
        "EPUB/package.opf": opf_bad.encode(),
        "EPUB/a.xhtml": xhtml,
        "EPUB/b.xhtml": xhtml,
    }
    problems = build_epub.validate_files(files)
    assert any("unknown spine idref" in p for p in problems), problems
    assert any("content missing from spine" in p for p in problems), problems


def _load_epub_module():
    from tools import build_engineering

    return build_engineering._epub_module()
