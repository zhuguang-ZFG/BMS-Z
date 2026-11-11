#!/usr/bin/env python3
"""EPUB 装配：两卷各自沿用现有 EPUB 构建器并归位到统一产物名。"""
from __future__ import annotations

from assemble import PY, ROOT, VOLUME_DIR, BuildError, copy_artifact, ensure_dir, run


def build_epub(volume: str, no_build: bool) -> None:
    out = VOLUME_DIR[volume]
    if volume == "I":
        run([PY, "scripts/build_epub.py"], cwd=ROOT / "analog")
        copy_artifact(ROOT / "analog/analog-book/dist/analog-circuit-book.epub",
                      out / "book.epub")
        return
    ensure_dir(out)
    run([PY, "bms-book/build_epub.py", "--out-dir", str(out)])
    produced = out / "bms-book.epub"
    if not produced.is_file():
        raise BuildError(f"构建器没有产出预期文件：{produced}")
    produced.replace(out / "book.epub")
