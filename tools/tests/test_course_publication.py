"""Portable-book contracts, independent of Chrome or installed Node modules."""
import importlib.util
import base64
from pathlib import Path
import shutil
import zipfile
import xml.etree.ElementTree as ET

import pytest


ROOT = Path(__file__).resolve().parents[2]


def builder():
    spec = importlib.util.spec_from_file_location('course_builder', ROOT / 'tools/build_course.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def lesson_html(extra=''):
    return ('<html><body><h2 id="lesson-01">01 · 第一课</h2>'
            '<details open class="course-check"><summary>核对</summary>保留条件</details>'
            f'{extra}</body></html>')


def test_offline_course_rejects_unresolved_links_and_duplicate_ids():
    module = builder()
    manifest = {'lessons': [{'id': '01'}]}
    module.validate_html(lesson_html('<a href="#lesson-01">回链</a>'), manifest)
    for broken in ('<a href="02-pack.md">下一课</a>', '<a href="#missing">题目</a>',
                   '<span id="lesson-01">重复 ID</span>', '<img src="https://example.org/plot.png">'):
        with pytest.raises(ValueError):
            module.validate_html(lesson_html(broken), manifest)


def test_pdf_contract_requires_the_answer_body_not_only_a_heading():
    module = builder()
    source = lesson_html()
    assert module.missing_pdf_answers(source, '01 · 第一课 核对') == [1]
    assert module.missing_pdf_answers(source, '01 · 第一课 核对 保留条件') == []


def test_epub_course_identity_style_and_answers_are_preserved(tmp_path):
    module = builder().load_epub_module()
    output = tmp_path / 'course.epub'
    metadata = {'title': '连续学习版', 'version': '1.0.0',
                'identifier': 'urn:bms-z:course:1.0.0', 'modified': '2026-11-08T00:00:00Z'}
    css = 'body { color: #293b3a; } .course-check { border: 1px solid #176b73; }'
    module.package_html(lesson_html('<a href="#lesson-01">上一课</a>'), output,
                        metadata, stylesheet=css)
    assert module.validate_epub(output) == []
    with zipfile.ZipFile(output) as archive:
        package = ET.fromstring(archive.read('EPUB/package.opf'))
        namespaces = {'dc': module.DC, 'opf': module.OPF}
        assert package.find('opf:metadata/dc:identifier', namespaces).text == metadata['identifier']
        assert package.find('opf:metadata/opf:meta', namespaces).text == metadata['modified']
        assert archive.read('EPUB/book.css').decode() == css
        content = archive.read('EPUB/book.xhtml').decode()
        assert '保留条件' in content and 'class="course-check"' in content
        assert 'open="' not in content and 'epub-summary' in content
        assert 'href="#lesson-01"' in content


def test_default_book_epub_identity_is_unchanged(tmp_path):
    module = builder().load_epub_module()
    output = tmp_path / 'book.epub'
    module.package_html(lesson_html(), output, {'title': '完整本', 'version': '0.6.10'})
    with zipfile.ZipFile(output) as archive:
        package = ET.fromstring(archive.read('EPUB/package.opf'))
        namespaces = {'dc': module.DC, 'opf': module.OPF}
        assert package.find('opf:metadata/dc:identifier', namespaces).text == 'urn:bms-z:book:0.6.10'
        assert archive.read('EPUB/book.css').decode() == module.CSS


@pytest.mark.skipif(not shutil.which('node') or not (ROOT / 'node_modules/vitepress').exists(),
                    reason='full course render requires the site Node dependencies')
def test_real_course_render_keeps_lesson_navigation_offline():
    source, manifest, report = builder().render_html()
    assert report['lessons'] == 24 and report['answers'] == 24
    assert source.count('data-course-lesson=') == 24
    assert '<details class="course-check">' in source
    assert '<details open' not in source
    for row in manifest['lessons']:
        assert f'href="#lesson-{row["id"]}"' in source
    assert 'https://zhuguang-zfg.github.io/BMS-Z/book/27-EKF的六个矩阵.html' in source
    assert 'class="header-anchor"' not in source and '<button' not in source
    # The build identity must include the actual embedded images, so changing a
    # diagram without editing a lesson cannot leave the provenance report stale.
    assert len(report['image_sources']) == report['images']
    expected_sketches = {f"docs/course/{row['illustration']}" for row in manifest['lessons']}
    assert len(expected_sketches) == 24
    assert expected_sketches <= set(report['image_sources'])
    for asset in report['image_sources']:
        assert base64.b64encode((ROOT / asset).read_bytes()).decode() in source
