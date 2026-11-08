"""The engineering assembly (P2.6) builds only from registries and manuscripts."""

import json
import shutil

import pytest

from tools.build_engineering import build, ROOT

pytestmark = pytest.mark.skipif(
    shutil.which("node") is None, reason="装配需要 Node 渲染器"
)


def test_build_outputs_units_assets_and_report(tmp_path):
    build(tmp_path)
    out = tmp_path
    assert (out / "index.html").is_file()
    for unit in ("s1", "s2", "s3"):
        page = out / f"{unit}.html"
        assert page.is_file(), f"{unit}.html 缺失"
        text = page.read_text(encoding="utf-8")
        assert "<main>" in text and "</main>" in text
    figures = sorted(
        p.relative_to(out).as_posix() for p in (out / "assets").glob("*/*")
    )
    assert len(figures) == 15, figures
    assert "assets/s1-measurement/S1-F1-sense-chain.svg" in figures
    data = json.loads((out / "build-report.json").read_text(encoding="utf-8"))
    assert set(data["units"]) == {"S1", "S2", "S3"}
    assert len(data["units"]["S1"]["source_sha256"]) == 16
    # 目录页含先修与层级徽标
    index = (out / "index.html").read_text(encoding="utf-8")
    assert "badge" in index and "先修" in index


def test_reading_levels_become_data_level_attributes(tmp_path):
    build(tmp_path)
    s1 = (tmp_path / "s1.html").read_text(encoding="utf-8")
    assert 'data-level="derivation"' in s1, "断言锚点小节须带推导层级"
    assert 'data-level="lab"' in s1, "S1.9 动手验证须带动手层级"
    s2 = (tmp_path / "s2.html").read_text(encoding="utf-8")
    assert 'data-level="derivation"' in s2
    s3 = (tmp_path / "s3.html").read_text(encoding="utf-8")
    assert 'data-level="lab"' in s3


def test_semantic_blocks_become_asides(tmp_path):
    build(tmp_path)
    s1 = (tmp_path / "s1.html").read_text(encoding="utf-8")
    assert 'class="callout story"' in s1
    assert 'class="chapter-route"' in s1
    assert "::::" not in s1, "容器语法不得残留在产物里"
    assert "它不证明" in s1, "导读边界声明必须在产物中"


def test_math_renders_offline_for_s2(tmp_path):
    build(tmp_path)
    s2 = (tmp_path / "s2.html").read_text(encoding="utf-8")
    assert "mjx" in s2 or "MathJax" in s2, "S2 的 82 处数学式必须由 mathjax3 离线渲染"


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
        ROOT / "bms-book/engineering-manifest.json",
        fake / "bms-book/engineering-manifest.json",
    )
    shutil.copy2(
        ROOT / "bms-book/engineering-claims.json",
        fake / "bms-book/engineering-claims.json",
    )
    shutil.copy2(
        ROOT / "bms-book/engineering-figures.json",
        fake / "bms-book/engineering-figures.json",
    )
    shutil.copy2(
        ROOT / "bms-book/engineering-experiments.json",
        fake / "bms-book/engineering-experiments.json",
    )
    monkeypatch.setattr(build_engineering, "ROOT", fake)
    with pytest.raises(SystemExit, match="正文源缺失"):
        build(tmp_path / "out")
    monkeypatch.setattr(build_engineering, "ROOT", original)


def test_broken_spine_fails_loudly(tmp_path):
    from tools.build_engineering import verify_spine

    index_html = '<a href="s1.html">S1</a><a href="ghost.html">幽灵</a>'
    (tmp_path / "s1.html").write_text("x", encoding="utf-8")
    with pytest.raises(SystemExit, match="坏 spine"):
        verify_spine(index_html, tmp_path)


def test_spine_passes_when_every_target_exists(tmp_path):
    from tools.build_engineering import verify_spine

    index_html = '<a href="s1.html">S1</a><a href="#anchor">本页锚</a>'
    (tmp_path / "s1.html").write_text("x", encoding="utf-8")
    verify_spine(index_html, tmp_path)


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
        "engineering-manifest.json",
        "engineering-claims.json",
        "engineering-figures.json",
        "engineering-experiments.json",
    ):
        shutil.copy2(ROOT / "bms-book" / name, fake / "bms-book" / name)
    (fake / "bms-book/engineering").mkdir(parents=True, exist_ok=True)
    shutil.copy2(
        ROOT / "bms-book/engineering/render.mjs",
        fake / "bms-book/engineering/render.mjs",
    )
    for manuscript in (ROOT / "bms-book/engineering").glob("S*.md"):
        shutil.copy2(manuscript, fake / "bms-book/engineering" / manuscript.name)
    # 只拷 S2/S3 的图，S1 缺图 → 装配必须在复制阶段报错
    for pattern in ("s2-model", "s3-precharge"):
        for src in (ROOT / "bms-book/engineering/assets" / pattern).glob("*"):
            shutil.copy2(src, fake / "bms-book/engineering/assets" / pattern / src.name)
    monkeypatch.setattr(build_engineering, "ROOT", fake)
    with pytest.raises(SystemExit, match="S1-F1 的文件缺失"):
        build(tmp_path / "out2")
    monkeypatch.setattr(build_engineering, "ROOT", original)
