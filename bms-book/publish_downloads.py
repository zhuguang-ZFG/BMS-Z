#!/usr/bin/env python3
"""Package the generated BMS book as deterministic GitHub Pages downloads."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
from pathlib import Path
import re
import shutil
from typing import TypedDict


class DownloadFile(TypedDict):
    kind: str
    latest: str
    versioned: str
    bytes: int
    sha256: str


class DownloadManifest(TypedDict):
    title: str
    version: str
    files: list[DownloadFile]

ROOT = Path(__file__).resolve().parent


class PublicationError(RuntimeError):
    """The downloadable book package cannot be produced safely."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _display_size(size: int) -> str:
    if size >= 1024 * 1024:
        return f"{size / (1024 * 1024):.1f} MiB"
    if size >= 1024:
        return f"{size / 1024:.1f} KiB"
    return f"{size} B"


def _landing_page(title: str, version: str, files: list[DownloadFile]) -> str:
    cards = []
    for item in files:
        kind = item["kind"].upper()
        latest = html.escape(item["latest"])
        versioned = html.escape(item["versioned"])
        size = _display_size(item["bytes"])
        sha256 = html.escape(item["sha256"])
        description = "单文件、公式与插图内嵌，可断网阅读" if kind == "HTML" else "A4 出版版式，含书签、目录页码与奇偶页眉"
        cards.append(
            '<article class="download-card">'
            f'<p class="kind">{kind}</p><h2><a href="{latest}">下载 {kind}</a></h2>'
            f'<p>{html.escape(description)} · {size}</p>'
            f'<p class="file">版本化文件：<a href="{versioned}">{versioned}</a></p>'
            f'<p class="hash"><span>SHA-256</span><code>{sha256}</code></p>'
            "</article>"
        )
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light dark">
<title>{html.escape(title)} · 下载</title>
<style>
:root {{ --paper:#fff; --ink:#0f172a; --muted:#475569; --line:#d8dee9; --accent:#0f766e; --panel:#f8fafc; }}
* {{ box-sizing:border-box; }}
body {{ margin:0 auto; max-width:900px; padding:3rem 1.25rem 5rem; color:var(--ink); background:var(--paper); font:16px/1.7 system-ui,"Noto Sans SC","Microsoft YaHei",sans-serif; }}
a {{ color:var(--accent); }}
.eyebrow,.kind {{ color:var(--accent); font-size:.78rem; font-weight:800; letter-spacing:.14em; }}
h1 {{ margin:.25rem 0; line-height:1.25; }}
.lead {{ color:var(--muted); }}
.download-grid {{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:1rem; margin:2rem 0; }}
.download-card {{ min-width:0; padding:1.25rem; border:1px solid var(--line); border-top:4px solid var(--accent); border-radius:14px; background:var(--panel); }}
.download-card h2 {{ margin:.15rem 0 .4rem; }}
.download-card p {{ margin:.35rem 0; }}
.file,.hash {{ color:var(--muted); font-size:.86rem; overflow-wrap:anywhere; }}
.hash span {{ display:block; font-weight:700; }}
.hash code {{ display:block; padding:.5rem; border:1px solid var(--line); border-radius:7px; background:var(--paper); overflow-wrap:anywhere; user-select:all; }}
.back {{ display:inline-block; margin-top:1rem; }}
@media (max-width:640px) {{ body {{ padding-top:1.5rem; }} .download-grid {{ grid-template-columns:1fr; }} }}
@media (prefers-color-scheme:dark) {{ :root {{ --paper:#0f172a; --ink:#e2e8f0; --muted:#a8b4c5; --line:#475569; --accent:#5eead4; --panel:#172033; }} }}
</style>
</head>
<body>
<p class="eyebrow">BMS-Z · OFFLINE BOOK</p>
<h1>{html.escape(title)}</h1>
<p class="lead">v{html.escape(version)} · 当前稳定版下载。文件由同一份书稿自动构建并通过 PDF 出版契约检查。</p>
<div class="download-grid">{''.join(cards)}</div>
<p><a href="SHA256SUMS.txt">下载 SHA256SUMS.txt</a> · <a href="book-downloads.json">查看机器可读清单</a></p>
<a class="back" href="../reading.html">← 返回在线阅读与路线</a>
</body>
</html>
"""


def package_downloads(source_dir: Path, output_dir: Path, manifest_path: Path) -> DownloadManifest:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    title = manifest.get("title")
    version = manifest.get("version")
    if not isinstance(title, str) or not title.strip():
        raise PublicationError("manifest title is missing")
    if not isinstance(version, str) or not re.fullmatch(r"\d+\.\d+\.\d+", version):
        raise PublicationError(f"invalid manifest version: {version!r}")

    inputs = [("html", source_dir / "bms-book.html"), ("pdf", source_dir / "bms-book.pdf")]
    missing = [path.name for _, path in inputs if not path.is_file()]
    if missing:
        raise PublicationError(f"missing generated book artifact: {', '.join(missing)}")

    output_dir.mkdir(parents=True, exist_ok=True)
    files: list[DownloadFile] = []
    sums: list[str] = []
    for kind, source in inputs:
        suffix = source.suffix
        latest = f"bms-book{suffix}"
        versioned = f"bms-book-v{version}{suffix}"
        shutil.copyfile(source, output_dir / latest)
        shutil.copyfile(source, output_dir / versioned)
        digest = _sha256(source)
        size = source.stat().st_size
        files.append(
            {
                "kind": kind,
                "latest": latest,
                "versioned": versioned,
                "bytes": size,
                "sha256": digest,
            }
        )
        sums.append(f"{digest}  {versioned}")

    metadata: DownloadManifest = {"title": title, "version": version, "files": files}
    (output_dir / "book-downloads.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    (output_dir / "SHA256SUMS.txt").write_text("\n".join(sums) + "\n", encoding="utf-8", newline="\n")
    (output_dir / "index.html").write_text(
        _landing_page(title, version, files), encoding="utf-8", newline="\n"
    )
    return metadata


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, default=ROOT / "dist")
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, default=ROOT / "manifest.json")
    args = parser.parse_args()
    try:
        result = package_downloads(args.source_dir, args.out_dir, args.manifest)
    except (OSError, json.JSONDecodeError, PublicationError) as exc:
        parser.error(str(exc))
    print(f"packaged book v{result['version']} in {args.out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
