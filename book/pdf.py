#!/usr/bin/env python3
"""PDF 装配：A4 单卷与 16K 分册（卷 I 两册、卷 II 一册）。"""
from __future__ import annotations

from assemble import (PY, ROOT, VOLUME_DIR, BuildError, copy_artifact,
                      ensure_dir, run)


def build_pdf(volume: str, fmt: str, no_build: bool) -> None:
    out = VOLUME_DIR[volume]
    if fmt == "a4":
        if volume == "I":
            cmd = [PY, "analog-book/build_book.py", "--pdf"]
            if no_build:
                cmd.append("--no-build")
            run(cmd, cwd=ROOT / "analog")
            copy_artifact(ROOT / "analog/analog-book/dist/analog-circuit-book.pdf",
                          out / "book-a4.pdf")
            return
        ensure_dir(out)
        run([PY, "bms-book/build_html.py", "--pdf", "--out-dir", str(out)])
        produced = out / "bms-book.pdf"
        if not produced.is_file():
            raise BuildError(f"构建器没有产出预期文件：{produced}")
        produced.replace(out / "book-a4.pdf")
        rebuilt_html = out / "bms-book.html"
        if rebuilt_html.is_file():
            rebuilt_html.replace(out / "book.html")
        return

    if volume == "II":
        ensure_dir(out)
        run([PY, "bms-book/build_print_book.py", "--out-dir", str(out)])
        produced = out / "bms-book.pdf"
        if not produced.is_file():
            raise BuildError(f"构建器没有产出预期文件：{produced}")
        produced.replace(out / "book-16k-1.pdf")
        for extra in ("bms-book.html", "bms-book.md"):
            (out / extra).unlink(missing_ok=True)
        return
    run([PY, "analog-book/build_print_book.py", *(["--no-build"] if no_build else [])],
        cwd=ROOT / "analog")
    run([PY, "analog-book/build_print_book.py", "--volumes", "--pdf",
         *(["--no-build"] if no_build else [])], cwd=ROOT / "analog")
    print_dir = ROOT / "analog/analog-book/dist/print"
    for index, name in ((1, "volume-1"), (2, "volume-2")):
        copy_artifact(print_dir / name / "analog-circuit-book.pdf",
                      out / f"book-16k-{index}.pdf")
