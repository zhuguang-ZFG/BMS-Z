#!/usr/bin/env python3
"""两卷装配层：manifest 驱动的站点、单文件 HTML 与公共构建助手。

渲染仍由两卷既有构建器承担；本模块只负责页序/介质调度与产物归位。
PDF 与 EPUB 分别见 book/pdf.py、book/epub.py。
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOOK = ROOT / "book"
DIST = BOOK / "dist"
PY = sys.executable

HTML_LIMITS_BYTES = {"I": 24 * 1024 * 1024, "II": 32 * 1024 * 1024}
MAX_PRINT_PAGES = 700

EXPECTED = {
    "I": ["book.html", "book-a4.pdf", "book-16k-1.pdf", "book-16k-2.pdf", "book.epub"],
    "II": ["book.html", "book-a4.pdf", "book-16k-1.pdf", "book.epub"],
}
VOLUME_DIR = {"I": DIST / "volume-1", "II": DIST / "volume-2"}


class BuildError(RuntimeError):
    """构建或审计失败。"""


def run(cmd: list[str], cwd: Path = ROOT) -> None:
    print("+", " ".join(cmd), f"(cwd={cwd.relative_to(ROOT)})")
    result = subprocess.run(cmd, cwd=cwd)
    if result.returncode != 0:
        raise BuildError(f"命令失败（exit {result.returncode}）：{' '.join(cmd)}")


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def copy_artifact(src: Path, dst: Path) -> Path:
    if not src.is_file():
        raise BuildError(f"构建器没有产出预期文件：{src}")
    ensure_dir(dst.parent)
    shutil.copy2(src, dst)
    return dst


def volumes(choice: str) -> list[str]:
    return ["I", "II"] if choice == "all" else [choice]


def copy_site_tree(src: Path, dst: Path) -> list[str]:
    skipped: list[str] = []

    def visit(source: Path, target: Path) -> None:
        target.mkdir(parents=True, exist_ok=True)
        try:
            entries = list(source.iterdir())
        except PermissionError:
            skipped.append(str(source.relative_to(src)))
            return
        for entry in entries:
            try:
                if entry.is_dir():
                    visit(entry, target / entry.name)
                elif entry.is_file():
                    shutil.copy2(entry, target / entry.name)
            except PermissionError:
                skipped.append(str(entry.relative_to(src)))

    visit(src, dst)
    return skipped


def build_site(no_build: bool) -> None:
    if not no_build:
        npm = shutil.which("npm") or "npm"
        run([npm, "run", "docs:build"], cwd=ROOT)
    src = ROOT / "docs/.vitepress/site-dist"
    if not src.is_dir():
        raise BuildError(f"站点产物不存在：{src}（先跑 python book/build.py site）")
    dst = DIST / "site"
    if dst.exists():
        shutil.rmtree(dst)
    skipped = copy_site_tree(src, dst)
    if skipped:
        print(f"警告：以下站点条目不可读，已跳过：{', '.join(skipped)}")
    print(f"site -> {dst} ({sum(p.stat().st_size for p in dst.rglob('*') if p.is_file())} bytes)")


def build_html(volume: str, no_build: bool) -> None:
    out = VOLUME_DIR[volume]
    if volume == "I":
        cmd = [PY, "analog-book/build_book.py"]
        if no_build:
            cmd.append("--no-build")
        run(cmd, cwd=ROOT / "analog")
        copy_artifact(ROOT / "analog/analog-book/dist/analog-circuit-book.html",
                      out / "book.html")
        return
    ensure_dir(out)
    run([PY, "bms-book/build_html.py", "--out-dir", str(out)])
    produced = out / "bms-book.html"
    if not produced.is_file():
        raise BuildError(f"构建器没有产出预期文件：{produced}")
    produced.replace(out / "book.html")
