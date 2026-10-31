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
import tempfile
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
        format_name = "离线 HTML" if kind == "HTML" else "出版 PDF"
        description = (
            "单文件封装公式与插图，下载后可断网阅读"
            if kind == "HTML"
            else "A4 出版版式，含书签、目录页码与奇偶页眉"
        )
        cards.append(
            '<article class="download-card">'
            '<div class="card-meta">'
            f'<p class="format">{kind}</p><p class="size">{size}</p>'
            "</div>"
            f"<h2>{format_name}</h2>"
            f'<p class="description">{html.escape(description)}</p>'
            f'<a class="primary" href="{latest}">下载当前版 {kind}<span aria-hidden="true">↓</span></a>'
            '<p class="version-copy"><span>固定版本</span>'
            f'<a href="{versioned}">{versioned}</a></p>'
            '<details class="hash"><summary><span>SHA-256</span><span>展开校验值</span></summary>'
            f"<code>{sha256}</code></details>"
            "</article>"
        )

    safe_title = html.escape(title)
    safe_version = html.escape(version)
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light dark">
<meta name="description" content="{safe_title} v{safe_version} 离线 HTML、出版 PDF 与 SHA-256 校验。">
<title>{safe_title} · 下载</title>
<style>
:root {{ --paper:#fffdf5; --ink:#293b3a; --muted:#626d65; --line:#cfc6b2; --accent:#176b73; --accent-hover:#12545b; --button:#176b73; --button-hover:#12545b; --button-ink:#fff; --panel:#f7f2e5; --code:#fffdf5; --note:#fbefc7; --shadow:#e4f0df; }}
* {{ box-sizing:border-box; }}
html {{ color-scheme:light dark; }}
body {{ margin:0; min-height:100vh; color:var(--ink); background:var(--paper); font:16px/1.7 "Punctuation SC","Inter",ui-sans-serif,system-ui,-apple-system,"Segoe UI","PingFang SC","HarmonyOS Sans SC","Source Han Sans SC","Noto Sans CJK SC","Microsoft YaHei UI","Microsoft YaHei",sans-serif; }}
a {{ color:var(--accent); text-underline-offset:.18em; }}
a:hover {{ color:var(--accent-hover); }}
a:focus-visible,summary:focus-visible {{ outline:3px solid var(--accent); outline-offset:3px; border-radius:5px; }}
.skip {{ position:fixed; z-index:2; top:.75rem; left:.75rem; padding:.45rem .75rem; border-radius:7px; background:var(--paper); transform:translateY(-180%); }}
.skip:focus {{ transform:none; }}
.page {{ width:min(100% - 2.5rem,960px); margin:0 auto; padding:4.5rem 0 3rem; }}
.hero {{ padding-bottom:2rem; border-bottom:1px solid var(--line); }}
.eyebrow,.format {{ margin:0; color:var(--accent); font-size:.75rem; font-weight:800; line-height:1.4; letter-spacing:.14em; }}
h1 {{ max-width:19ch; margin:.45rem 0 .8rem; font-size:clamp(2rem,5vw,3.05rem); line-height:1.16; letter-spacing:-.025em; text-wrap:balance; }}
.lead {{ max-width:50rem; margin:0; color:var(--muted); font-size:1.04rem; }}
.release-facts {{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); margin:1.75rem 0 0; border:1px solid var(--line); border-radius:4px 14px 6px 12px; background:var(--note); box-shadow:3px 4px 0 var(--shadow); }}
.release-facts div {{ min-width:0; padding:.9rem 1rem; border-left:1px solid var(--line); }}
.release-facts div:first-child {{ border-left:0; }}
.release-facts dt {{ color:var(--muted); font-size:.76rem; font-weight:700; letter-spacing:.08em; }}
.release-facts dd {{ margin:.12rem 0 0; font-weight:700; }}
.download-grid {{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:1rem; margin:2rem 0 1rem; }}
.download-card {{ display:flex; min-width:0; flex-direction:column; padding:1.35rem; border:1px solid var(--line); border-top:3px solid var(--accent); border-radius:5px 18px 7px 14px; background:var(--panel); box-shadow:4px 5px 0 var(--shadow); }}
.card-meta {{ display:flex; align-items:center; justify-content:space-between; gap:1rem; }}
.size {{ margin:0; color:var(--muted); font-size:.8rem; font-variant-numeric:tabular-nums; }}
.download-card h2 {{ margin:.42rem 0 .35rem; font-size:1.35rem; line-height:1.3; }}
.description {{ min-height:3.4em; margin:0 0 1rem; color:var(--muted); }}
.primary {{ display:flex; align-items:center; justify-content:space-between; gap:1rem; padding:.72rem .9rem; border:1px solid var(--button); border-radius:9px; color:var(--button-ink); background:var(--button); font-weight:750; text-decoration:none; }}
.primary:hover {{ border-color:var(--button-hover); color:var(--button-ink); background:var(--button-hover); }}
.primary span {{ font-size:1.12rem; }}
.version-copy {{ display:grid; gap:.12rem; margin:1rem 0; color:var(--muted); font-size:.83rem; }}
.version-copy span {{ font-size:.72rem; font-weight:700; letter-spacing:.06em; }}
.version-copy a {{ overflow-wrap:anywhere; }}
.hash {{ margin-top:auto; padding-top:.9rem; border-top:1px solid var(--line); }}
.hash summary {{ display:flex; justify-content:space-between; gap:1rem; color:var(--muted); cursor:pointer; font-size:.76rem; font-weight:700; list-style:none; }}
.hash summary::-webkit-details-marker {{ display:none; }}
.hash summary span:last-child {{ color:var(--accent); font-weight:600; }}
.hash[open] summary {{ margin-bottom:.55rem; }}
.hash code {{ display:block; padding:.65rem .7rem; border:1px solid var(--line); border-radius:7px; color:var(--ink); background:var(--code); font:12px/1.55 "JetBrains Mono",ui-monospace,"SFMono-Regular",Consolas,monospace; overflow-wrap:anywhere; user-select:all; }}
.toolbox {{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:1rem; margin-top:1rem; }}
.toolbox a {{ display:block; padding:.9rem 1rem; border:1px solid var(--line); border-radius:10px; background:var(--paper); text-decoration:none; }}
.toolbox strong {{ display:block; color:var(--ink); }}
.toolbox span {{ color:var(--muted); font-size:.82rem; }}
.footer {{ display:flex; justify-content:space-between; gap:1rem; margin-top:2.25rem; padding-top:1.25rem; border-top:1px solid var(--line); color:var(--muted); font-size:.86rem; }}
.footer p {{ margin:0; }}
.footer a {{ font-weight:650; }}
@media (max-width:640px) {{
  .page {{ width:min(100% - 2rem,960px); padding:2rem 0; }}
  h1 {{ font-size:2rem; }}
  .release-facts,.download-grid,.toolbox {{ grid-template-columns:1fr; }}
  .release-facts div {{ padding:.7rem .85rem; border-top:1px solid var(--line); border-left:0; }}
  .release-facts div:first-child {{ border-top:0; }}
  .description {{ min-height:0; }}
  .footer {{ flex-direction:column; }}
}}
@media (prefers-color-scheme:dark) {{
  :root {{ --paper:#192727; --ink:#edf0e5; --muted:#b0beb3; --line:#496160; --accent:#7ec5c5; --accent-hover:#a0dddd; --button:#7ec5c5; --button-hover:#a0dddd; --button-ink:#192727; --panel:#223333; --code:#192727; --note:#453e2b; --shadow:#293f35; }}
}}
@media print {{
  :root {{ color-scheme:light; --paper:#fff; --panel:#fff; --code:#fff; --note:#fff; --ink:#293b3a; --muted:#626d65; --accent:#176b73; --line:#cfc6b2; }}
  .release-facts,.download-card {{ box-shadow:none; break-inside:avoid; }}
}}
</style>
</head>
<body>
<a class="skip" href="#downloads">跳到下载选项</a>
<div class="page">
<header class="hero">
<p class="eyebrow">BMS-Z · OFFLINE BOOK</p>
<h1>{safe_title}</h1>
<p class="lead">当前稳定版提供单文件 HTML 与出版 PDF；两种格式来自同一次书稿构建，并附版本化副本和可复核摘要。</p>
<dl class="release-facts">
<div><dt>版本</dt><dd>v{safe_version}</dd></div>
<div><dt>构建</dt><dd>同一份书稿</dd></div>
<div><dt>门禁</dt><dd>PDF 出版契约通过</dd></div>
</dl>
</header>
<main id="downloads">
<section class="download-grid" aria-label="选择下载格式">{''.join(cards)}</section>
<nav class="toolbox" aria-label="校验与机器可读文件">
<a href="SHA256SUMS.txt"><strong>SHA256SUMS.txt</strong><span>批量核对版本化文件</span></a>
<a href="book-downloads.json"><strong>book-downloads.json</strong><span>机器可读的版本、大小与摘要</span></a>
</nav>
</main>
<footer class="footer">
<p><a href="../reading.html">← 返回书籍与阅读路线</a></p>
<p>文档 CC BY-SA 4.0 · 代码 MIT</p>
</footer>
</div>
</body>
</html>
"""


def package_downloads(
    source_dir: Path, output_dir: Path, manifest_path: Path
) -> DownloadManifest:
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

    if output_dir.exists() and (not output_dir.is_dir() or output_dir.is_symlink()):
        raise PublicationError(f"output path is not an owned directory: {output_dir}")
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    staging_dir = Path(
        tempfile.mkdtemp(prefix=f".{output_dir.name}-staging-", dir=output_dir.parent)
    )
    backup_dir: Path | None = None
    try:
        files: list[DownloadFile] = []
        sums: list[str] = []
        for kind, source in inputs:
            suffix = source.suffix
            latest = f"bms-book{suffix}"
            versioned = f"bms-book-v{version}{suffix}"
            shutil.copyfile(source, staging_dir / latest)
            shutil.copyfile(source, staging_dir / versioned)
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
            sums.append(f"{digest} *{versioned}")

        metadata: DownloadManifest = {"title": title, "version": version, "files": files}
        (staging_dir / "book-downloads.json").write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        (staging_dir / "SHA256SUMS.txt").write_text(
            "\n".join(sums) + "\n", encoding="utf-8", newline="\n"
        )
        (staging_dir / "index.html").write_text(
            _landing_page(title, version, files), encoding="utf-8", newline="\n"
        )

        if output_dir.exists():
            backup_dir = Path(
                tempfile.mkdtemp(prefix=f".{output_dir.name}-backup-", dir=output_dir.parent)
            )
            backup_dir.rmdir()
            output_dir.replace(backup_dir)
        try:
            staging_dir.replace(output_dir)
        except OSError:
            if backup_dir is not None and backup_dir.exists():
                backup_dir.replace(output_dir)
            raise
        if backup_dir is not None:
            shutil.rmtree(backup_dir, ignore_errors=True)
        return metadata
    finally:
        shutil.rmtree(staging_dir, ignore_errors=True)


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
